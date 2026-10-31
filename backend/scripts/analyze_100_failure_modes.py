"""Create an auditable failure-mode table from the saved 100-question run.

This script does not make new correctness judgments. It carries forward the
existing AI-assisted notes and labels them as provisional for human review.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
RUN = RESULTS / "experiment_100_approved_results_retest_20261021.json"
AUDIT = RESULTS / "experiment_100_ai_assisted_audit.json"
OUT_CSV = RESULTS / "experiment_100_failure_mode_review.csv"
OUT_JSON = RESULTS / "experiment_100_failure_mode_summary.json"


def classify(note: str, is_refusal: bool, false_refusal: bool, missing_targets: bool) -> list[str]:
    text = note.casefold()
    labels: list[str] = []
    if false_refusal:
        labels.append("false_refusal")
    if missing_targets:
        labels.append("target_document_retrieval_gap")
    if re.search(r"numerical|number|size range|conflict|reports \d+%|wrong paper", text):
        labels.append("factual_or_numeric_mismatch_flag")
    if re.search(r"incomplete|omits|missing|only one|only the|one of|not clearly|does not clearly|does not establish", text):
        labels.append("incomplete_answer_or_evidence_flag")
    if re.search(r"citation|no_citation|no citation", text):
        labels.append("citation_review_needed")
    if is_refusal and "explain" in text:
        labels.append("refusal_explanation_review_needed")
    if not labels:
        labels.append("no_flag_in_provisional_note")
    return labels


def main() -> None:
    run = json.loads(RUN.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    run_by_id = {r["id"]: r for r in run["rows"]}
    audit_by_id = {r["id"]: r for r in audit["rows"]}
    out_rows = []
    label_counts: Counter[str] = Counter()
    for qid in sorted(run_by_id):
        r, a = run_by_id[qid], audit_by_id[qid]
        is_refusal = bool(r.get("is_refusal"))
        false_refusal = not is_refusal and bool(r.get("refusal_marker_detected"))
        source_ids = r.get("source_ids") or []
        found_ids = r.get("retrieved_target_source_ids") or []
        missing_targets = bool(source_ids) and len(set(source_ids) - set(found_ids)) > 0
        labels = classify(a.get("provisional_review_note", ""), is_refusal, false_refusal, missing_targets)
        label_counts.update(labels)
        out_rows.append({
            "id": qid,
            "question": r.get("question", ""),
            "answerable_or_refusal": "designed_refusal" if is_refusal else "answerable",
            "provisional_ai_content_score_0_to_2": a.get("ai_assisted_content_score_0_to_2"),
            "target_pdf_count": len(source_ids),
            "retrieved_target_pdf_count": len(set(source_ids) & set(found_ids)),
            "missing_target_pdf_ids": ";".join(sorted(set(source_ids) - set(found_ids))),
            "false_refusal_marker": false_refusal,
            "citation_traceability_status": a.get("citation_traceability_status", ""),
            "issue_flags": ";".join(labels),
            "provisional_review_note": a.get("provisional_review_note", ""),
            "answer": r.get("answer", ""),
            "retrieved_evidence": json.dumps(r.get("retrieved", []), ensure_ascii=False),
            "human_rater_1_score": "",
            "human_rater_1_page_support": "",
            "human_rater_2_score": "",
            "human_rater_2_page_support": "",
            "adjudication": "",
        })

    fieldnames = list(out_rows[0])
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    summary = {
        "source_run": RUN.name,
        "source_ai_assisted_audit": AUDIT.name,
        "rows": len(out_rows),
        "completed_rows": sum(r.get("status") == "completed" for r in run["rows"]),
        "provisional_ai_content_score_counts": audit.get("summary", {}).get("content_score_counts", {}),
        "provisional_issue_flag_counts_nonexclusive": dict(sorted(label_counts.items())),
        "critical_review_ids_from_prior_audit": audit.get("summary", {}).get("critical_cases", []),
        "interpretation": "Flags and scores are inherited from a single AI-assisted preliminary audit plus deterministic source-coverage checks. They are not independent human ratings, and citation-label matching does not prove claim-level support.",
        "outputs": [OUT_CSV.name, OUT_JSON.name],
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
