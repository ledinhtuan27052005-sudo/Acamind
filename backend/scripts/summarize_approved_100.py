"""Summarize observable outcomes of the frozen 100-question experiment.

These are mechanical indicators, not judgments of factual correctness or human
inter-rater agreement. Gold document IDs are used only after generation.
"""
from __future__ import annotations

import json
import math
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_ROOT = ROOT / "backend" / "data" / "raw_pdfs_500"


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    if total == 0:
        return None
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return [round(center - margin, 4), round(center + margin, 4)]


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lo, hi = math.floor(index), math.ceil(index)
    return round(ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo), 2)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results" / "experiment_100_approved_results_postfix_v2_20261021.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = sorted(data["rows"], key=lambda row: row["id"])
    completed = [r for r in rows if r.get("status") == "completed"]
    answerable = [r for r in completed if not r["is_refusal"]]
    refusal = [r for r in completed if r["is_refusal"]]
    full_retrieval = [r for r in answerable if set(r["source_ids"]) <= set(r.get("retrieved_target_source_ids", []))]
    multi = [r for r in answerable if len(r["source_ids"]) > 1]
    multi_full = [r for r in multi if set(r["source_ids"]) <= set(r.get("retrieved_target_source_ids", []))]
    false_refusals = [r["id"] for r in answerable if (r.get("answer") or "").lstrip().startswith("__NO_CONTEXT__")]
    correct_refusals = [r["id"] for r in refusal if (r.get("answer") or "").lstrip().startswith("__NO_CONTEXT__")]
    cited_all = []
    no_citation = []
    cited_files = Counter()
    invalid_page_labels = []
    for row in answerable:
        answer = row.get("answer") or ""
        labels = re.findall(r"([\w.\-]+\.pdf)\s*[-–]\s*(?:Trang|Page)\s*(\d+)", answer, re.I)
        names = {name.removesuffix(".pdf") for name, _ in labels}
        cited_files.update(names)
        if not labels:
            no_citation.append(row["id"])
        if set(row["source_ids"]) <= names:
            cited_all.append(row["id"])
        for name, page in labels:
            pdf = PDF_ROOT / name
            if not pdf.exists():
                invalid_page_labels.append({"id": row["id"], "label": f"{name}:p{page}", "reason": "missing PDF"})
                continue
            try:
                import pymupdf
                page_count = len(pymupdf.open(pdf))
            except Exception:
                continue
            if not 1 <= int(page) <= page_count:
                invalid_page_labels.append({"id": row["id"], "label": f"{name}:p{page}", "reason": f"page outside 1–{page_count}"})
    latency = [float(r.get("elapsed_seconds") or 0) for r in completed]
    result = {
        "experiment_file": path.name,
        "evaluation_status": data.get("evaluation_status", "unspecified"),
        "model": data.get("model"),
        "question_file_sha256": data.get("question_file_sha256"),
        "code_sha256": data.get("code_sha256"),
        "completed": len(completed), "expected": 100,
        "errors": [{"id": r["id"], "status": r.get("status"), "error": r.get("error")} for r in rows if r.get("status") != "completed"],
        "answerable_completed": len(answerable), "refusal_completed": len(refusal),
        "all_target_docs_retrieved": {"numerator": len(full_retrieval), "denominator": len(answerable), "wilson_95": wilson(len(full_retrieval), len(answerable))},
        "multi_source_all_targets_retrieved": {"numerator": len(multi_full), "denominator": len(multi), "wilson_95": wilson(len(multi_full), len(multi))},
        "all_target_docs_cited": {"numerator": len(cited_all), "denominator": len(answerable), "wilson_95": wilson(len(cited_all), len(answerable))},
        "answerable_false_refusals": {"numerator": len(false_refusals), "denominator": len(answerable), "ids": false_refusals, "wilson_95": wilson(len(false_refusals), len(answerable))},
        "designed_refusals_with_marker": {"numerator": len(correct_refusals), "denominator": len(refusal), "ids": correct_refusals, "wilson_95": wilson(len(correct_refusals), len(refusal))},
        "answerable_without_citation_ids": no_citation,
        "invalid_cited_pdf_pages": invalid_page_labels,
        "latency_seconds": {"mean": round(statistics.mean(latency), 2) if latency else None,
                            "p50": percentile(latency, .5), "p95": percentile(latency, .95)},
        "important_limit": "Document retrieval and citation-label validity do not establish answer correctness or claim-level PDF support. This is an iterative post-feedback run, not an untouched holdout.",
    }
    output = path.with_name(path.stem + "_metrics.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"SAVED {output}")


if __name__ == "__main__":
    main()
