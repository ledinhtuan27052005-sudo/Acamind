"""Criterion-specific retrieval ordering; relevance is not verified support."""
from copy import deepcopy
import hashlib

from app.services.evidence_policy import requested_facets

FACET_PROMPTS = {
    "sample": "Cỡ mẫu, quần thể và người tham gia / sample size, population, participants",
    "method": "Phương pháp, thiết kế và can thiệp / methods, study design, intervention",
    "measure": "Thang đo, công cụ và chỉ số / measures, instruments, evaluation metrics",
    "finding": "Kết quả và cỡ hiệu ứng / findings, outcomes and effect sizes",
    "limitation": "Hạn chế và giới hạn nghiên cứu / limitations and caveats",
}


def chunk_key(chunk):
    # IDs alone can be missing, or collide between sources. Never merge studies.
    fields = [str(chunk.get(k) or "") for k in
              ("document_id", "doc_filename", "id", "page_number", "content")]
    return hashlib.sha256("\0".join(fields).encode()).hexdigest()


def rerank_by_facets(groups, facets, top_n):
    """Batch original + criterion queries, then fairly select unique passages.

    Base relevance scores remain attached to their original query. Criterion
    scores only populate facet_scores and ordering; they never certify a cell.
    A failed scorer preserves the base ordering without invented facet scores.
    """
    from app.services.reranker import rerank_groups

    facets = list(dict.fromkeys(f for f in facets if f in FACET_PROMPTS))
    if not facets or top_n <= 0:
        return rerank_groups(groups, top_n=top_n)
    expanded = []
    for query, chunks in groups:
        expanded.append((query, chunks))
        for facet in facets:
            expanded.append((f"{query}\nTiêu chí cần tìm / requested criterion: {FACET_PROMPTS[facet]}", chunks))
    # Keep the candidate pool until facet allocation; scorer enforces its budget.
    results = rerank_groups(expanded, top_n=max((len(c) for _, c in groups), default=0))
    output = []
    stride = len(facets) + 1
    for group_index, (_, candidates) in enumerate(groups):
        base = results[group_index * stride]
        by_key = {chunk_key(c): deepcopy(c) for c in base}
        for c in by_key.values():
            c["facet_scores"] = {f: None for f in facets}
            c["facet_queries"] = {f: FACET_PROMPTS[f] for f in facets}
            c["facet_selection"] = []
        queues = {}
        for offset, facet in enumerate(facets, 1):
            ranked = results[group_index * stride + offset]
            scored = [c for c in ranked if c.get("rerank_score_available") and chunk_key(c) in by_key]
            scored.sort(key=lambda c: c["rerank_score"], reverse=True)
            queues[facet] = [chunk_key(c) for c in scored]
            for c in scored:
                by_key[chunk_key(c)]["facet_scores"][facet] = c["rerank_score"]
        selected, seen = [], set()
        while len(selected) < top_n:
            progressed = False
            for facet in facets:
                queue = queues[facet]
                while queue and queue[0] in seen:
                    queue.pop(0)
                if queue and len(selected) < top_n:
                    key = queue.pop(0)
                    seen.add(key)
                    by_key[key]["facet_selection"].append(facet)
                    selected.append(by_key[key])
                    progressed = True
            if not progressed:
                break
        for c in base:
            key = chunk_key(c)
            if key not in seen and len(selected) < top_n:
                seen.add(key)
                selected.append(by_key[key])
        for c in selected:
            c["facet_rerank_status"] = "scored" if any(v is not None for v in c["facet_scores"].values()) else "unavailable"
        output.append(selected)
    return output
