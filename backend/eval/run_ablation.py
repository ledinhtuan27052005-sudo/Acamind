"""Chạy thực nghiệm loại bỏ thành phần (ablation) M1–M7 bằng CHÍNH hàm retrieve() của hệ thống.

Khác bản cũ (scratch/run_300q_full_experiment.py):
- Mỗi cấu hình chạy độc lập qua cờ AblationFlags (không ghép kết quả của cấu hình khác,
  không viết lại pipeline riêng trong script).
- Xóa toàn bộ cache trước MỖI lượt (câu hỏi × cấu hình) → độ trễ đo ở trạng thái lạnh.
- Thứ tự cấu hình được xáo trộn theo từng câu (seed cố định) để tránh thiên lệch thứ tự.
- Độ sâu danh sách cố định (top_k = 10, fixed_depth) để Recall@10/nDCG@10 so sánh được.
- Ghi JSONL từng dòng → chạy tiếp được nếu bị gián đoạn (--resume mặc định).

Cách chạy (từ thư mục gốc dự án):
    backend\\.venv\\Scripts\\python.exe -X utf8 backend\\eval\\run_ablation.py
    backend\\.venv\\Scripts\\python.exe -X utf8 backend\\eval\\run_ablation.py --limit 10   # chạy thử
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import platform
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.postgres import SessionLocal  # noqa: E402
from app.services.ablation_config import CONFIGS, clear_all_caches, use_flags  # noqa: E402
from app.services.retriever import retrieve  # noqa: E402

DEFAULT_QUESTIONS = ROOT / "Query and result" / "300_cau_hoi_tam_ly_hoc.csv"
DEFAULT_OUT = ROOT / "Query and result" / "ablation_runs.jsonl"
SEED = 42
TOP_K = 10
RERANK_TOP_N = 24
WARMUP_QUERIES = ["Tâm lý học là gì?", "Trầm cảm là gì?", "So sánh CBT và SSRI",
                  "Rối loạn lo âu lan tỏa", "Liệu pháp hành vi biện chứng"]


def load_questions(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_done(out: Path) -> set[tuple[str, str]]:
    done = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                done.add((r["question_id"], r["config"]))
            except Exception:
                continue
    return done


def run_one(db, query: str, cfg_name: str) -> dict:
    flags = dataclasses.replace(CONFIGS[cfg_name], fixed_depth=True)
    clear_all_caches()
    t0 = time.perf_counter()
    error = None
    try:
        with use_flags(flags):
            chunks = retrieve(query, None, db, top_k=TOP_K, rerank_top_n=RERANK_TOP_N)
    except Exception as exc:  # ghi lỗi thay vì dừng cả lượt chạy
        chunks, error = [], f"{type(exc).__name__}: {exc}"
        try:
            db.rollback()
        except Exception:
            pass
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
    tel = chunks[0].get("_telemetry", {}) if chunks else {}
    return {
        "latency_ms": latency_ms,
        "error": error,
        "route": tel.get("route"),
        "num_targets": tel.get("num_targets"),
        "fts_hits": tel.get("fts_hits"),
        "vector_hits": tel.get("vector_hits"),
        "ranked": [
            {
                "file": c.get("doc_filename") or "",
                "page": int(c.get("page_number") or 0),
                "sub_query_target": c.get("sub_query_target"),
                "content": (c.get("content") or "")[:600],
            }
            for c in chunks
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=0, help="Chỉ chạy N câu đầu (chạy thử)")
    ap.add_argument("--configs", default=",".join(CONFIGS), help="Danh sách cấu hình, phân tách bằng dấu phẩy")
    ap.add_argument("--fresh", action="store_true", help="Xóa file kết quả cũ, chạy lại từ đầu")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    cfg_names = [c.strip() for c in args.configs.split(",") if c.strip()]
    questions = load_questions(args.questions)
    if args.limit:
        questions = questions[: args.limit]
    if args.fresh and args.out.exists():
        args.out.unlink()
    done = load_done(args.out)
    rng = random.Random(SEED)

    meta_path = args.out.with_suffix(".meta.json")
    meta_path.write_text(json.dumps({
        "seed": SEED, "top_k": TOP_K, "rerank_top_n": RERANK_TOP_N,
        "configs": {n: dataclasses.asdict(CONFIGS[n]) for n in cfg_names},
        "python": sys.version, "platform": platform.platform(), "processor": platform.processor(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cache_policy": "clear_all_caches() before every (question, config) run",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    with SessionLocal() as db:
        print(f"Warm-up {len(WARMUP_QUERIES)} truy vấn (không tính kết quả)...")
        for q in WARMUP_QUERIES:
            for n in cfg_names:
                run_one(db, q, n)

        t_start = time.perf_counter()
        with open(args.out, "a", encoding="utf-8") as fout:
            for i, row in enumerate(questions, 1):
                qid, query = row["Question_ID"], row["Câu hỏi"]
                order = cfg_names[:]
                rng.shuffle(order)  # luôn xáo để chuỗi ngẫu nhiên không đổi khi resume
                for n in order:
                    if (qid, n) in done:
                        continue
                    res = run_one(db, query, n)
                    rec = {"question_id": qid, "config": n, "query": query, **res}
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    fout.flush()
                elapsed = time.perf_counter() - t_start
                print(f"[{i}/{len(questions)}] {qid} xong — {elapsed:.0f}s")
    print(f"Hoàn tất. Kết quả: {args.out}")


if __name__ == "__main__":
    main()
