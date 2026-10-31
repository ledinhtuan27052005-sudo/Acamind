"""Candidate evidence coverage for questions comparing named studies.

Reranker scores are relevance signals, not proof that a requested result is
reported. The generator must still verify claims against the cited passages.
"""
from __future__ import annotations

import os
import re


_FACETS = {
    "sample": (r"\b(mẫu|cỡ mẫu|người tham gia|sample|participants?|subjects?)\b",
               r"\b(mẫu|người tham gia|đối tượng|sample|participants?|subjects?|n\s*=)\b"),
    "method": (r"\b(phương pháp|thiết kế|can thiệp|methods?|designs?|interventions?)\b",
               r"\b(phương pháp|thiết kế|can thiệp|methods?|designs?|interventions?|procedures?)\b"),
    "measure": (r"\b(thang đo|công cụ đo|measures?|scales?|instruments?)\b",
                r"\b(thang đo|đo lường|measures?|scales?|instruments?|questionnaires?)\b"),
    "finding": (r"\b(kết quả|phát hiện|hiệu quả|cỡ hiệu ứng|results?|findings?|outcomes?|effects?)\b",
                r"\b(kết quả|phát hiện|hiệu quả|results?|findings?|outcomes?|effects?|p\s*[<=>])\b"),
    "limitation": (r"\b(giới hạn|hạn chế|limitations?|caveats?)\b",
                   r"\b(giới hạn|hạn chế|limitations?|caveats?)\b"),
}


def assess_target_coverage(targets: list[str], chunks: list[dict], question: str = "") -> dict:
    """Keep each study independent; never let one high score cover another."""
    threshold = float(os.getenv("COMPARISON_RERANK_MIN_SCORE", "0.08"))
    requested_facets = [name for name, (question_pattern, _) in _FACETS.items()
                        if re.search(question_pattern, question, re.I)]
    rows = []
    claimed_documents: set[str] = set()
    for target in targets:
        own = [c for c in chunks if str(c.get("sub_query_target") or "").casefold() == target.casefold()]
        target_was_scored = any(c.get("rerank_score_available") for c in own)
        if target_was_scored:
            eligible = [c for c in own if c.get("rerank_score_available") and
                        float(c.get("rerank_score") or 0.0) >= threshold]
        else:
            eligible = list(own)
        distinct = [c for c in eligible if str(c.get("document_id") or "") not in claimed_documents]
        if not distinct and eligible and not any(c.get("target_identity") == "exact_title" for c in eligible):
            distinct = eligible
        chosen = max(distinct, key=lambda c: float(c.get("rerank_score") or 0.0), default=None)
        if chosen and chosen.get("document_id"):
            claimed_documents.add(str(chosen["document_id"]))
        scored = [float(c["rerank_score"]) for c in own if c.get("rerank_score_available")]
        best = max(scored) if scored else None
        # An unavailable reranker is not a negative score. Pass candidates to
        # the generator with an explicit uncertainty label instead.
        status = ("missing" if chosen is None
                  else "candidate" if chosen.get("rerank_score_available") else "unscored")
        facet_candidates = {
            name: [str(c.get("id") or "") for c in own
                   if re.search(_FACETS[name][1], str(c.get("parent_context") or c.get("content") or ""), re.I)]
            for name in requested_facets
        }
        rows.append({"target": target, "status": status,
                     "best_relevance_score": best, "candidate_count": len(own),
                     "representative_document_id": str(chosen.get("document_id") or "") if chosen else None,
                     "facet_candidates": facet_candidates})
    supported = [row for row in rows if row["status"] != "missing"]
    return {"targets": rows, "status": "none" if not supported else
            "complete_candidates" if len(supported) == len(rows) else "partial_candidates",
            "threshold": threshold, "requested_facets": requested_facets,
            "note": "Facet keywords locate candidates; they do not verify factual support."}
