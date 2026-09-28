"""Run a reproducible Acamind operational test and save raw evidence.

The input is a JSON array with question, ground_truth and document_ids fields.
Use --repeat 100 with the supplied 10 independent questions to make 1,000
executions. Those executions measure operational stability, not 1,000
independent scientific QA samples; report that distinction in the paper.
"""

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data" / "eval_questions.json"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "operational_test_results"
CITATION_RE = re.compile(r"\[[^\]]+\s-\sPage\s+\d+\]", re.IGNORECASE)


def load_cases(path: Path) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("Input phải là JSON array không rỗng.")
    for index, case in enumerate(cases, 1):
        missing = {"question", "ground_truth", "document_ids"} - case.keys()
        if missing or not case["ground_truth"].strip() or not case["document_ids"]:
            raise ValueError(f"Ca {index} thiếu dữ liệu bắt buộc: {sorted(missing)}")
    return cases


def run_case(api_url: str, case: dict, test_id: str, source_case_id: int) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    timer = time.perf_counter()
    row = {
        "test_id": test_id,
        "source_case_id": source_case_id,
        "started_at_utc": started,
        "question": case["question"],
        "document_ids": case["document_ids"],
        "ground_truth": case["ground_truth"],
    }
    try:
        response = requests.post(
            f"{api_url.rstrip('/')}/chat/answer",
            json={"query": case["question"], "document_ids": case["document_ids"]},
            timeout=90,
        )
        row["http_status"] = response.status_code
        response.raise_for_status()
        body = response.json()
        answer = body.get("answer", "")
        no_context = "__NO_CONTEXT__" in answer
        citations = CITATION_RE.findall(answer)
        row.update({
            "outcome": "no_context" if no_context else "success",
            "answer": answer,
            "context_count": len(body.get("contexts", [])),
            "citation_count": len(citations),
            "has_page_citation": bool(citations),
            "error": "",
        })
    except Exception as exc:  # Evidence must include failures, not hide them.
        row.update({
            "http_status": getattr(getattr(exc, "response", None), "status_code", None),
            "outcome": "error",
            "answer": "",
            "context_count": 0,
            "citation_count": 0,
            "has_page_citation": False,
            "error": str(exc),
        })
    row["latency_seconds"] = round(time.perf_counter() - timer, 4)
    return row


def main() -> int:
    # Windows terminals may default to cp1252, which cannot display Vietnamese
    # help and progress text. Keep the evidence runner usable from PowerShell.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    parser = argparse.ArgumentParser(description="Run and record Acamind operational tests.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--repeat", type=int, default=100, help="Lần lặp toàn bộ tập test (mặc định 100).")
    parser.add_argument("--api-url", default="http://localhost:8000/api/v1")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat phải >= 1")

    cases = load_cases(args.input)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = args.output_dir / f"operational_test_{timestamp}.jsonl"
    csv_path = args.output_dir / f"operational_test_{timestamp}_summary.csv"
    manifest_path = args.output_dir / f"operational_test_{timestamp}_manifest.json"
    total = len(cases) * args.repeat
    print(f"Chạy {total} lượt ({len(cases)} ca độc lập × {args.repeat} lần lặp).")

    fieldnames = ["test_id", "source_case_id", "started_at_utc", "outcome", "http_status", "latency_seconds", "context_count", "citation_count", "has_page_citation", "error"]
    outcomes, latencies = [], []
    with jsonl_path.open("w", encoding="utf-8") as jsonl, csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for run in range(1, args.repeat + 1):
            for source_case_id, case in enumerate(cases, 1):
                test_number = (run - 1) * len(cases) + source_case_id
                row = run_case(args.api_url, case, f"OP-{test_number:04d}", source_case_id)
                jsonl.write(json.dumps(row, ensure_ascii=False) + "\n")
                writer.writerow({key: row.get(key, "") for key in fieldnames})
                outcomes.append(row["outcome"])
                latencies.append(row["latency_seconds"])
                print(f"{row['test_id']}: {row['outcome']} ({row['latency_seconds']:.2f}s)")

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(args.input),
        "independent_cases": len(cases),
        "repeat_count": args.repeat,
        "total_executions": total,
        "api_url": args.api_url,
        "summary": {
            "success": outcomes.count("success"),
            "no_context": outcomes.count("no_context"),
            "error": outcomes.count("error"),
            "mean_latency_seconds": round(sum(latencies) / len(latencies), 4),
        },
        "raw_results_jsonl": str(jsonl_path),
        "summary_csv": str(csv_path),
        "interpretation": "Repeated runs assess operational stability only. They are not additional independent QA examples.",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã lưu evidence: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
