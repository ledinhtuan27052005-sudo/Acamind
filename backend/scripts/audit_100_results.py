"""Create an explicitly AI-assisted, provisional audit of the 100 approved runs.

Content scores are a model-assisted review against the gold anchors. They are not
independent human ratings and should not be presented as such in a paper.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
SOURCE = RESULTS / "experiment_100_approved_results.json"
OUT_JSON = RESULTS / "experiment_100_ai_assisted_audit.json"
OUT_CSV = RESULTS / "experiment_100_ai_assisted_audit.csv"

# 0 = incorrect/absent; 1 = partly correct, incomplete, or under-supported;
# 2 = expected core answer appears correct. Conservative provisional review.
CONTENT = {
 1:0,2:0,3:2,4:2,5:1,6:2,7:0,8:0,9:0,10:2,
 11:2,12:1,13:2,14:2,15:2,16:2,17:2,18:1,19:2,20:2,
 21:1,22:2,23:2,24:2,25:2,26:2,27:1,28:2,29:2,30:2,
 31:2,32:2,33:2,34:2,35:2,36:2,37:1,38:2,39:2,40:2,
 41:2,42:2,43:2,44:0,45:1,46:2,47:2,48:2,49:1,50:2,
 51:0,52:2,53:2,54:2,55:2,56:2,57:2,58:2,59:2,60:2,
 61:2,62:2,63:1,64:1,65:2,66:1,67:2,68:1,69:2,70:2,
 71:1,72:2,73:2,74:2,75:2,76:2,77:2,78:2,79:2,80:2,
 81:2,82:2,83:2,84:2,85:1,86:1,87:2,88:2,89:2,90:2,
 91:2,92:2,93:2,94:1,95:2,96:2,97:2,98:2,99:1,100:2,
}
NOTES = {
 1: "False abstention: target PDF and abstract were retrieved, but answer returned __NO_CONTEXT__.",
 2: "Wrong paper and wrong size range (8–12B/27–31B instead of 1B–671B); target paper absent from top 12.",
 5: "Core topic appears relevant, but response expands beyond the requested difficulty; full factual entailment needs adjudication.",
 7: "Numerical answer conflicts with anchor (26.2%/13.0% vs 30.0%/10.5%).",
 8: "Reports 18%, conflicting with the approved answer anchor of 40%.",
 9: "False abstention: answerable calibration question; target paper was not retrieved.",
 12: "Partly aligned, but the expected negative language/tone/conflict indicators are not clearly established in the answer excerpt.",
 18: "Reports human sample sizes but omits the five LLMs requested by the gold anchor.",
 21: "Discusses retaining more self-generated ideas, but does not clearly establish the requested low-quality-idea comparison.",
 27: "Discusses spatial alignment; temporal lag/flattening and failure to reproduce reversals are not clearly established.",
 37: "Reports the interview sample, but the longitudinal 673-user / six-month component is incomplete or missing.",
 44: "False abstention/incomplete synthesis: only one of two target papers retrieved; answer gives no comparison.",
 45: "Partial synthesis; one target source is absent from retrieved context and the second study is incompletely represented.",
 49: "Abstains from a comparison even though both target PDFs appear in the retrieved top 12; answer is incomplete.",
 51: "Abstains after retrieving one target paper; comparison is not answered.",
 63: "Names Normality Paradox in place of the requested Cognitive Destabilization; Truthfulness Paradox is present.",
 64: "Only the VLM paper appears in retrieved targets; human-reasoning paper and its method are not covered.",
 66: "Three-paper synthesis is incomplete: one of three target PDFs is missing from retrieved context.",
 68: "Only the loneliness paper is retrieved; the LLM depression-rater evidence is not covered, and unrelated sources appear.",
 71: "Only the relational-AI target is retrieved; self-efficacy findings from the other two target studies are missing.",
 85: "Uses Normality Paradox in place of Cognitive Destabilization; requested Truthfulness Paradox is discussed.",
 86: "Effect size is reported; both requested sample sizes need confirmation in full answer.",
 94: "Main performance metrics are present; the second-ranked predictor requires confirmation in the full answer.",
 99: "Safe generic abstention, but does not explain that the source is observational/simulation-based rather than a causal human experiment.",
}


def citation_audit(row: dict) -> dict:
    retrieved = {(str(x.get("filename", "")).lower(), str(x.get("page", ""))) for x in row.get("retrieved", [])}
    labels = row.get("citation_labels", [])
    exact = 0
    target = 0
    malformed = 0
    unresolved = 0
    target_ids = set(row.get("source_ids", []))
    for label in labels:
        m = re.search(r"([^\s\[\]]+\.pdf)\s*[-–]\s*(?:Page|Trang)\s*(\d+)(.*)$", label, re.I)
        if not m:
            unresolved += 1
            continue
        filename, page, suffix = m.group(1).lower(), m.group(2), m.group(3)
        if "," in suffix:
            malformed += 1
        if (filename, page) in retrieved:
            exact += 1
            if any(sid.lower() in filename for sid in target_ids):
                target += 1
        else:
            unresolved += 1
    if not labels:
        status = "no_citation"
    elif exact == len(labels):
        status = "all_labels_match_retrieved_filename_page"
    elif exact:
        status = "some_labels_unverified_against_saved_retrieval"
    else:
        status = "citation_labels_unverified"
    return {"citation_labels_total": len(labels), "citation_labels_matching_saved_retrieval": exact,
            "target_source_citation_labels_matching_saved_retrieval": target,
            "unverified_citation_labels": unresolved, "combined_page_labels": malformed,
            "citation_traceability_status": status}


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = []
    for result in sorted(data["rows"], key=lambda x: x["id"]):
        audited = {k: result.get(k) for k in ("id", "question", "expected_answer", "source_ids", "status", "answer", "retrieved_target_source_ids", "target_source_recall", "elapsed_seconds", "is_refusal")}
        audited["ai_assisted_content_score_0_to_2"] = CONTENT[result["id"]]
        audited["score_interpretation"] = {0:"incorrect_or_no_answer", 1:"partial_or_needs_adjudication", 2:"core_answer_appears_correct"}[CONTENT[result["id"]]]
        audited["provisional_review_note"] = NOTES.get(result["id"], "Core answer appears to match the expected anchor; this provisional model-assisted judgment is not an independent human score.")
        audited.update(citation_audit(result))
        rows.append(audited)
    scores = Counter(r["ai_assisted_content_score_0_to_2"] for r in rows)
    summary = {
        "review_type":"AI-assisted provisional rubric review by Codex; not independent human annotation",
        "rubric":{"content_score":"0 incorrect/absent; 1 partial/incomplete/needs adjudication; 2 expected core answer appears correct",
                  "citation_traceability":"machine checks whether cited PDF/page labels occur in the saved top-12 evidence; this does not establish semantic entailment"},
        "rows_reviewed":len(rows), "content_score_counts":dict(sorted(scores.items())),
        "core_answer_apparent_correct_rate":round(scores[2]/len(rows),4) if rows else None,
        "citation_labels_total":sum(r["citation_labels_total"] for r in rows),
        "citation_labels_matching_saved_retrieval":sum(r["citation_labels_matching_saved_retrieval"] for r in rows),
        "citation_labels_unverified":sum(r["unverified_citation_labels"] for r in rows),
        "combined_page_labels":sum(r["combined_page_labels"] for r in rows),
        "critical_cases":[1,2,7,8,9,44,49,51,63,64,68,71,85],
        "limitations":["Scores are an AI-assisted review against the supplied expected-answer anchors, not human judgments.",
                        "No second independent rater or adjudication was performed; no inter-rater reliability can be reported.",
                        "Citation filename/page matching is syntactic only; entailment and page-level support require reading the PDF passages.",
                        "The expected anchors themselves have not been independently verified against every PDF in this audit."],
        "created_at":datetime.now(timezone.utc).isoformat(),
    }
    OUT_JSON.write_text(json.dumps({"summary":summary,"rows":rows},ensure_ascii=False,indent=2),encoding="utf-8")
    fields=["id","status","question","expected_answer","source_ids","retrieved_target_source_ids","target_source_recall","ai_assisted_content_score_0_to_2","score_interpretation","provisional_review_note","citation_labels_total","citation_labels_matching_saved_retrieval","target_source_citation_labels_matching_saved_retrieval","unverified_citation_labels","combined_page_labels","citation_traceability_status","is_refusal","elapsed_seconds"]
    with OUT_CSV.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");writer.writeheader();writer.writerows(rows)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print(f"AUDIT_JSON={OUT_JSON}\nAUDIT_CSV={OUT_CSV}")


if __name__ == "__main__":
    main()
