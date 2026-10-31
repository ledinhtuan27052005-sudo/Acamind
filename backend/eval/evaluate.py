"""Tính chỉ số + kiểm định thống kê từ ablation_runs.jsonl và xuất Excel.

Nguồn nhãn (qrels):
- `--qrels <file.tsv>` : nhãn NGƯỜI CHẤM (sau bước B3). Định dạng TSV, có header:
      question_id  file  page  grade  entities
  grade ∈ {0,1,2}; entities = các vế liên quan, phân tách bằng ';' (có thể trống).
- Không truyền `--qrels` : dùng nhãn TỰ ĐỘNG (silver) từ cột Auto_Candidate_Pages /
  Gold_Candidate_Pages của bộ câu hỏi. Nhãn này do chính từ điển + FTS của hệ thống sinh ra
  nên có thiên lệch vòng lặp — KẾT QUẢ CHỈ DÙNG ĐỂ GỠ LỖI, KHÔNG DÙNG ĐỂ NỘP BÁO.

Cách chạy:
    backend\\.venv\\Scripts\\python.exe -X utf8 backend\\eval\\evaluate.py
    backend\\.venv\\Scripts\\python.exe -X utf8 backend\\eval\\evaluate.py --qrels "Query and result\\qrels_human.tsv"
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "eval"))

import openpyxl  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402

from metrics import facet_coverage, retrieval_metrics, target_coverage  # noqa: E402
from stats import bootstrap_ci, fmt_p, holm, mcnemar_exact_p, wilcoxon_p  # noqa: E402

QUESTIONS = ROOT / "Query and result" / "300_cau_hoi_tam_ly_hoc.csv"
RUNS = ROOT / "Query and result" / "ablation_runs.jsonl"
REFERENCE = "M7_Acamind_Full"
CONTINUOUS = ["doc_recall@5", "doc_recall@10", "doc_mrr@10", "doc_ndcg@10", "page_recall@10", "page_ndcg@10"]
BINARY = ["doc_hit@5", "doc_hit@10", "page_hit@5"]


def col(row: dict, *names: str) -> str:
    for n in names:
        if n in row and row[n] is not None:
            return row[n]
    return ""


def load_silver_qrels(questions: list[dict]):
    qrels, ent = {}, {}
    for r in questions:
        q = {}
        for tag in col(r, "Auto_Candidate_Pages", "Gold_Candidate_Pages").split(";"):
            tag = tag.strip()
            if ":p" in tag:
                fn, pg = tag.rsplit(":p", 1)
                if pg.isdigit():
                    q[(fn.strip(), int(pg))] = 1
        qrels[r["Question_ID"]] = q
        ent[r["Question_ID"]] = {}
    return qrels, ent


def load_human_qrels(path: Path):
    qrels, ent = defaultdict(dict), defaultdict(dict)
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            key = (r["file"].strip(), int(r["page"]))
            qrels[r["question_id"]][key] = int(r["grade"])
            es = {e.strip() for e in (r.get("entities") or "").split(";") if e.strip()}
            if es and int(r["grade"]) >= 1:
                ent[r["question_id"]][key] = es
    return dict(qrels), dict(ent)


def mean(vals):
    v = [x for x in vals if x is not None]
    return (round(100 * statistics.mean(v), 2), len(v)) if v else (None, 0)


def pct(vals, q):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return None
    idx = min(len(v) - 1, max(0, int(round(q * (len(v) - 1)))))
    return round(v[idx], 1)


def style_header(ws):
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F4E78")
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for column in ws.columns:
        ws.column_dimensions[column[0].column_letter].width = 18


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", type=Path, default=QUESTIONS)
    ap.add_argument("--runs", type=Path, default=RUNS)
    ap.add_argument("--qrels", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--split", default="", help="Lọc theo Dataset_Split (vd. Test_Untouched)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    with open(args.questions, encoding="utf-8-sig", newline="") as f:
        questions = list(csv.DictReader(f))
    if args.split:
        questions = [q for q in questions if q.get("Dataset_Split") == args.split]
    qmeta = {q["Question_ID"]: q for q in questions}

    label_source = "HUMAN" if args.qrels else "SILVER_AUTO (chỉ để gỡ lỗi, KHÔNG dùng nộp báo)"
    qrels, ent = load_human_qrels(args.qrels) if args.qrels else load_silver_qrels(questions)
    out = args.out or args.runs.with_name(
        "ket_qua_ablation_" + ("human" if args.qrels else "silver") + (f"_{args.split}" if args.split else "") + ".xlsx")

    runs = defaultdict(dict)  # runs[config][qid] = record
    for line in args.runs.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["question_id"] in qmeta:
            runs[r["config"]][r["question_id"]] = r
    configs = [c for c in ["M1_Dense", "M2_Hybrid_RRF", "M3_Rerank", "M4_Cross_Lingual",
                           "M5_SubQuery", "M6_Facet_Rerank", "M7_Acamind_Full"] if c in runs]
    qids = [q for q in qmeta if all(q in runs[c] for c in configs)]

    per_q = defaultdict(dict)  # per_q[config][qid] = metrics
    for c in configs:
        for qid in qids:
            r = runs[c][qid]
            ranked = [(x["file"], x["page"]) for x in r["ranked"]]
            answerable = col(qmeta[qid], "Human_Answerability", "Corpus_Answerability", "Auto_Answerability") != "Unanswerable_In_Corpus"
            m = retrieval_metrics(ranked, qrels.get(qid, {})) if answerable else {}
            targets = [t.strip() for t in qmeta[qid].get("Target_Entities", "").split("|") if t.strip()]
            m["target_coverage@10"] = target_coverage(ranked, ent.get(qid, {}), targets) if ent.get(qid) else None
            m["facet_coverage"] = facet_coverage([x["content"] for x in r["ranked"]],
                                                 [f.strip() for f in qmeta[qid].get("Requested_Facets", "").split(",")])
            m["route_correct"] = 1.0 if r.get("route") == qmeta[qid].get("Expected_Route") else 0.0
            m["empty_result"] = 1.0 if not r["ranked"] else 0.0
            m["answerable"] = answerable
            m["latency_ms"] = r["latency_ms"]
            per_q[c][qid] = m

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "README"
    for line in [
        ["Nguồn nhãn", label_source],
        ["Số câu đánh giá", len(qids)],
        ["Split", args.split or "Tất cả"],
        ["Cấu hình tham chiếu", REFERENCE],
        ["Kiểm định", "Wilcoxon signed-rank (chỉ số liên tục), McNemar exact (Hit@k); hiệu chỉnh Holm cho các so sánh với tham chiếu; bootstrap 95% CI (10.000 lần, seed 42)"],
        ["Câu Unanswerable", "Loại khỏi chỉ số truy xuất; đánh giá riêng ở sheet Abstention"],
        ["Độ trễ", "Đo sau khi xóa toàn bộ cache trước mỗi lượt (trạng thái lạnh), thứ tự cấu hình xáo trộn"],
        ["Target coverage", "Chỉ có khi dùng nhãn người (cột entities)"],
    ]:
        ws.append(line)
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 120

    metric_cols = BINARY + CONTINUOUS + ["target_coverage@10", "facet_coverage"]
    ws = wb.create_sheet("Ablation")
    ws.append(["Cấu hình", "N (answerable)"] + [f"{m} (%)" for m in metric_cols]
              + ["Latency p50 (ms)", "Latency p95 (ms)"])
    for c in configs:
        vals = per_q[c]
        row = [c, sum(1 for q in qids if vals[q]["answerable"])]
        row += [mean([vals[q].get(m) for q in qids])[0] for m in metric_cols]
        lat = [vals[q]["latency_ms"] for q in qids]
        row += [pct(lat, 0.5), pct(lat, 0.95)]
        ws.append(row)
    style_header(ws)

    ws = wb.create_sheet("Significance_vs_Full")
    ws.append(["Chỉ số", "Cấu hình", "Δ (Full − cấu hình), điểm %", "95% CI thấp", "95% CI cao",
               "Kiểm định", "p (thô)", "p (Holm)", "Trình bày"])
    for m in ["doc_hit@10", "doc_mrr@10", "doc_ndcg@10", "page_hit@5", "page_ndcg@10"]:
        others = [c for c in configs if c != REFERENCE]
        ref = [per_q[REFERENCE][q].get(m) for q in qids]
        raw, cis = [], []
        for c in others:
            cur = [per_q[c][q].get(m) for q in qids]
            raw.append(mcnemar_exact_p(ref, cur) if m in BINARY else wilcoxon_p(ref, cur))
            cis.append(bootstrap_ci(ref, cur))
        adj = holm(raw)
        for c, p, pa, ci in zip(others, raw, adj, cis):
            test = "McNemar exact" if m in BINARY else "Wilcoxon"
            d = [round(100 * x, 2) for x in ci] if ci else [None, None, None]
            shown = f"Δ = {d[0]:+.2f} [{d[1]:.2f}, {d[2]:.2f}], {fmt_p(pa)}" if ci else "n/a"
            ws.append([m, c, d[0], d[1], d[2], test, p, pa, shown])
    style_header(ws)

    ws = wb.create_sheet("By_Group_Full")
    ws.append(["Nhóm câu hỏi", "Độ dài", "N", "Router accuracy (%)", "doc_hit@5 (%)", "doc_hit@10 (%)",
               "doc_mrr@10 (%)", "doc_ndcg@10 (%)", "page_hit@5 (%)", "Latency p50 (ms)"])
    groups = defaultdict(list)
    for q in qids:
        groups[(qmeta[q]["Nhóm câu hỏi"], qmeta[q]["Độ dài"])].append(q)
    for (g, l), qs in groups.items():
        v = per_q[REFERENCE]
        ws.append([g, l, len(qs), mean([v[q]["route_correct"] for q in qs])[0]]
                  + [mean([v[q].get(m) for q in qs])[0] for m in ["doc_hit@5", "doc_hit@10", "doc_mrr@10", "doc_ndcg@10", "page_hit@5"]]
                  + [pct([v[q]["latency_ms"] for q in qs], 0.5)])
    style_header(ws)

    ws = wb.create_sheet("Abstention")
    ws.append(["Cấu hình", "N unanswerable", "Tỉ lệ trả rỗng ở câu unanswerable (%)",
               "N answerable", "Tỉ lệ trả rỗng sai ở câu answerable (%)"])
    for c in configs:
        v = per_q[c]
        un = [q for q in qids if not v[q]["answerable"]]
        an = [q for q in qids if v[q]["answerable"]]
        ws.append([c, len(un), mean([v[q]["empty_result"] for q in un])[0],
                   len(an), mean([v[q]["empty_result"] for q in an])[0]])
    style_header(ws)

    ws = wb.create_sheet("Per_Question")
    ws.append(["Question_ID", "Câu hỏi", "Nhóm", "Độ dài", "Split", "Cấu hình", "Route", "Latency (ms)",
               "Top-10 (file:trang)"] + metric_cols)
    for c in configs:
        for q in qids:
            r, m = runs[c][q], per_q[c][q]
            ws.append([q, qmeta[q]["Câu hỏi"], qmeta[q]["Nhóm câu hỏi"], qmeta[q]["Độ dài"],
                       qmeta[q].get("Dataset_Split"), c, r.get("route"), r["latency_ms"],
                       "; ".join(f"{x['file']}:p{x['page']}" for x in r["ranked"][:10])]
                      + [m.get(k) for k in metric_cols])
    style_header(ws)

    wb.save(out)
    print(f"Nguồn nhãn: {label_source}")
    print(f"Đã ghi: {out}")


if __name__ == "__main__":
    main()
