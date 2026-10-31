"""Chỉ số truy xuất chuẩn cho thực nghiệm Acamind.

Quy ước:
- `ranked`: danh sách (filename, page) theo thứ tự hệ thống trả về (có thể trùng file).
- `qrels`: dict {(filename, page): grade} với grade ∈ {0, 1, 2}; grade >= 1 là liên quan.
- Câu hỏi KHÔNG có mục liên quan nào → trả về None (bị loại khỏi trung bình, đánh giá
  riêng ở phần "từ chối trả lời"). Bản cũ gán Recall = MRR = 1 cho trường hợp này.

Sửa so với bản cũ (run_300q_full_experiment.py):
- Page@5 trước đây cắt `[:6]` → nay cắt đúng `[:k]`.
- Recall@k nay là tỉ lệ mục liên quan được tìm thấy (Recall chuẩn); Hit@k tách riêng.
- Bổ sung nDCG@10 dùng nhãn phân bậc 0/1/2.
- Facet "answer" (khớp mọi từ ≥ 4 ký tự) bị loại khỏi Facet Coverage.
"""
from __future__ import annotations

import math
import re
from typing import Iterable

Ranked = list[tuple[str, int]]
Qrels = dict[tuple[str, int], int]


def _dedup(seq: Iterable) -> list:
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def doc_qrels(qrels: Qrels) -> dict[str, int]:
    """Nhãn mức tài liệu = nhãn cao nhất trong các trang của tài liệu đó."""
    out: dict[str, int] = {}
    for (fn, _pg), g in qrels.items():
        out[fn] = max(out.get(fn, 0), int(g))
    return out


def _rel_set(labels: dict, min_grade: int = 1) -> set:
    return {k for k, g in labels.items() if g >= min_grade}


def hit_at_k(ranked_ids: list, labels: dict, k: int) -> float | None:
    rel = _rel_set(labels)
    if not rel:
        return None
    return 1.0 if any(x in rel for x in ranked_ids[:k]) else 0.0


def recall_at_k(ranked_ids: list, labels: dict, k: int) -> float | None:
    rel = _rel_set(labels)
    if not rel:
        return None
    return len(rel & set(ranked_ids[:k])) / len(rel)


def mrr_at_k(ranked_ids: list, labels: dict, k: int = 10) -> float | None:
    rel = _rel_set(labels)
    if not rel:
        return None
    for i, x in enumerate(ranked_ids[:k], 1):
        if x in rel:
            return 1.0 / i
    return 0.0


def ndcg_at_k(ranked_ids: list, labels: dict, k: int = 10) -> float | None:
    if not _rel_set(labels):
        return None
    dcg = sum((2 ** labels.get(x, 0) - 1) / math.log2(i + 1) for i, x in enumerate(ranked_ids[:k], 1))
    ideal = sorted(labels.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(i + 1) for i, g in enumerate(ideal, 1))
    return dcg / idcg if idcg > 0 else None


def retrieval_metrics(ranked: Ranked, qrels: Qrels) -> dict:
    """Tính toàn bộ chỉ số mức tài liệu và mức trang cho một câu hỏi."""
    pages = _dedup((fn, int(pg)) for fn, pg in ranked if fn)
    docs = _dedup(fn for fn, _ in pages)
    dq = doc_qrels(qrels)
    return {
        "doc_hit@5": hit_at_k(docs, dq, 5),
        "doc_hit@10": hit_at_k(docs, dq, 10),
        "doc_recall@5": recall_at_k(docs, dq, 5),
        "doc_recall@10": recall_at_k(docs, dq, 10),
        "doc_mrr@10": mrr_at_k(docs, dq, 10),
        "doc_ndcg@10": ndcg_at_k(docs, dq, 10),
        "page_hit@5": hit_at_k(pages, qrels, 5),
        "page_recall@10": recall_at_k(pages, qrels, 10),
        "page_ndcg@10": ndcg_at_k(pages, qrels, 10),
        "n_relevant_docs": len(_rel_set(dq)),
        "n_relevant_pages": len(_rel_set(qrels)),
    }


def target_coverage(ranked: Ranked, entity_labels: dict[tuple[str, int], set[str]],
                    targets: list[str], k: int = 10) -> float | None:
    """Tỉ lệ thực thể (vế so sánh) có ít nhất một trang liên quan trong top-k.

    `entity_labels` lấy từ cột "Vế liên quan" do người chấm gán (B3), KHÔNG dùng trùng token.
    """
    if len(targets) < 2:
        return None
    pages = _dedup((fn, int(pg)) for fn, pg in ranked if fn)[:k]
    covered = set()
    for p in pages:
        covered |= entity_labels.get(p, set())
    norm = {t.strip().lower() for t in targets}
    return len(norm & {c.strip().lower() for c in covered}) / len(norm)


# Facet heuristic: chỉ dùng làm chỉ số phụ, ghi rõ là heuristic trong bài báo.
FACET_PATTERNS = {
    "sample": r"\b(?:n\s*=\s*\d+|participants?|patients?|students?|adolescents?|children|adults?|sample|cohort)\b",
    "method": r"\b(?:method|design|trial|rct|survey|cross-sectional|longitudinal|intervention|program|protocol)\b",
    "measure": r"\b(?:scale|inventory|questionnaire|score|phq|gad|bdi|dass|dsm|index|measure|assessment)\b",
    "finding": r"\b(?:result|finding|showed|indicated|significant|effect|correlation|associated|reduced|improved)\b",
    "limitation": r"\b(?:limitation|caveat|future research|generalizability|bias|self-report|small sample)\b",
}


def facet_coverage(contents: list[str], requested: list[str]) -> float | None:
    req = [f for f in requested if f in FACET_PATTERNS]
    if not req:
        return None
    blob = " ".join(contents).lower()
    return sum(1 for f in req if re.search(FACET_PATTERNS[f], blob, re.I)) / len(req)
