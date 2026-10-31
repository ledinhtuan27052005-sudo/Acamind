"""Retrieval ordering and lexical-density diagnostics.

Authority remains unverified; keyword mentions never award evidence tiers.
"""
from __future__ import annotations

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

def score_document_authority(doc_info: dict[str, Any], sample_content: str = "") -> tuple[float, str, str]:
    """Do not infer authority, peer review or evidence level from mentions.

    The current ingestion schema has no independently reviewed appraisal record.
    Preserve the public tuple contract without awarding an unverified bonus.
    """
    return 0.0, "unverified", "Chưa thẩm định chất lượng nguồn và cấp độ bằng chứng"


# ── 2. Đánh giá Mật độ Thông tin Đúng Trọng tâm Câu hỏi ────────────────────────

def score_topical_information_density(content: str, query: str, trans_query: str | None = None) -> tuple[float, str, float]:
    """Đánh giá mật độ thông tin và mức độ giải quyết trực tiếp câu hỏi của chunk.
    
    Tiêu chí:
    1. Độ phủ từ khóa của câu hỏi trong đoạn văn (Topic Coverage), xét cả câu gốc và câu dịch (Cross-Lingual).
    2. Sự hiện diện của thông tin định lượng thực chất (Số liệu %, cỡ mẫu, p-value, điểm thang đo).
    3. Sự hiện diện của các giải pháp/kỹ thuật/phác đồ hành động cụ thể.
    
    Returns:
        (density_bonus, density_label, overlap_ratio)
        - density_bonus: từ 0.0 đến 0.40
        - density_label: "Rất cao (Đầy đủ số liệu & giải pháp)" | "Cao" | "Trung bình"
        - overlap_ratio: mức độ phủ từ khóa câu hỏi
    """
    if not content or len(content.strip()) < 80:
        return 0.0, "Thấp (Nội dung ngắn hoặc khái quát)", 0.0

    clean_content = content.lower()
    clean_query = query.lower()

    # Bóc tách các từ khóa có ý nghĩa từ câu hỏi (>= 2 ký tự)
    query_words = [w for w in re.findall(r'\b\w{2,}\b', clean_query) if len(w) > 2]
    content_words = set(re.findall(r"\b\w+\b", clean_content))
    query_words = sorted(set(query_words))
    matched_words = [w for w in query_words if w in content_words]
    overlap_ratio = len(matched_words) / max(len(query_words), 1)

    # Nếu có trans_query (hỗ trợ cross-lingual) -> tính thêm overlap từ câu hỏi đối chiếu
    if trans_query and trans_query.strip().lower() != clean_query:
        en_stop = {"what", "is", "are", "how", "why", "when", "where", "who", "which", "the", "and", "for", "with", "that", "this", "from"}
        vi_stop = {"la", "gi", "nhu", "the", "nao", "cua", "trong", "va", "cac", "nhung"}
        trans_words = [w for w in re.findall(r'\b\w{2,}\b', trans_query.lower()) if len(w) > 2 and w not in en_stop and w not in vi_stop]
        if trans_words:
            trans_words = sorted(set(trans_words))
            matched_trans = [w for w in trans_words if w in content_words]
            trans_ratio = len(matched_trans) / max(len(trans_words), 1)
            overlap_ratio = max(overlap_ratio, trans_ratio)

    # 1. Điểm phủ từ khóa chủ đề (0.0 -> 0.20)
    topic_score = min(0.20, overlap_ratio * 0.20)

    # 2. Điểm dữ liệu định lượng (Quantitative Evidence): số liệu %, p-value, số bệnh nhân,...
    has_percent = bool(re.search(r'\b\d+(?:\.\d+)?%', content))
    has_sample_or_p = bool(re.search(r'\b(?:n\s*=\s*\d+|p\s*<\s*0\.\d+|p\s*=\s*0\.\d+|\b\d+\s*bệnh nhân|\b\d+\s*patients)\b', content, re.IGNORECASE))
    has_measure = bool(re.search(r'\b(?:bdi|phq|gad|dsm|thang đo|điểm số|scale|score)\b', content, re.IGNORECASE))

    evidence_bonus = 0.0
    if has_percent:
        evidence_bonus += 0.08
    if has_sample_or_p:
        evidence_bonus += 0.07
    if has_measure:
        evidence_bonus += 0.05
    evidence_bonus = min(0.15, evidence_bonus)

    # 3. Điểm kỹ thuật/quy trình hành động cụ thể (Actionable Information)
    action_words = ["kỹ thuật", "can thiệp", "phác đồ", "quy trình", "bước", "liệu pháp", "technique", "protocol", "intervention", "treatment", "method"]
    action_hits = sum(1 for w in action_words if w in clean_content)
    action_bonus = min(0.08, action_hits * 0.02)

    total_density = round(topic_score + evidence_bonus + action_bonus, 3)

    if total_density >= 0.25:
        density_label = "Nhiều dấu hiệu từ vựng/số liệu (chưa xác minh)"
    elif total_density >= 0.15:
        density_label = "Có dấu hiệu từ vựng/số liệu (chưa xác minh)"
    else:
        density_label = "Ít dấu hiệu từ vựng/số liệu"

    return total_density, density_label, overlap_ratio


# ── 3. Rerank tổng hợp dựa trên Uy tín & Mật độ thông tin ────────────────────

def prioritize_candidates_by_authority_and_density(
    candidates: list[dict[str, Any]],
    query: str,
    trans_query: str | None = None,
    top_k: int = 12,
    max_per_doc: int = 4
) -> list[dict[str, Any]]:
    """Tái sắp xếp các chunk ứng viên theo điểm tổng hợp và đảm bảo đa dạng tài liệu.

    LƯU Ý (đã kiểm chứng): score_document_authority() luôn trả về 0 vì hệ thống chưa có dữ liệu
    thẩm định chất lượng nguồn, nên hàm này KHÔNG ưu tiên RCT/meta-analysis/độ uy tín. Thành phần
    thực sự tác động tới thứ hạng là:
    - Điểm mật độ heuristic (score_topical_information_density): độ phủ từ khóa câu hỏi, có số liệu
      (%, n=, p=), có thang đo, có từ chỉ can thiệp/kỹ thuật; nhân với rel_gate từ điểm rerank.
    - Đa dạng tài liệu: giới hạn max_per_doc chunk/tài liệu, chọn vòng trang tốt nhất của các tài liệu đầu.
    Tên hàm được giữ nguyên để không phá vỡ giao diện gọi hiện có.
    """
    if not candidates or top_k <= 0 or max_per_doc <= 0:
        return []

    scored_chunks = []
    for c in candidates:
        chunk_dict = dict(c)

        # 1. Chấm điểm uy tín tài liệu
        auth_score, auth_tier, auth_label = score_document_authority(chunk_dict, chunk_dict.get("content", ""))
        chunk_dict["authority_score"] = auth_score
        chunk_dict["authority_tier"] = auth_tier
        chunk_dict["authority_label"] = auth_label

        # 2. Chấm điểm mật độ thông tin trọng tâm của đoạn văn (xét cả câu hỏi gốc và câu hỏi dịch)
        density_score, density_label, overlap_ratio = score_topical_information_density(
            chunk_dict.get("content", ""), query, trans_query
        )
        chunk_dict["density_score"] = density_score
        chunk_dict["density_label"] = density_label
        chunk_dict["overlap_ratio"] = overlap_ratio

        # Ordering may include heuristics; relevance gates use only model scores.
        if chunk_dict.get("ranking_score") is not None:
            base_score = float(chunk_dict["ranking_score"])
        elif chunk_dict.get("rerank_score_available"):
            base_score = float(chunk_dict.get("rerank_score") or 0.0)
        else:
            base_score = float(chunk_dict.get("rrf_score") or 0.005) * 0.25
            min_eval_score = min(
                (float(x.get("rerank_score") or 0.0) for x in candidates if x.get("rerank_score_available")),
                default=None,
            )
            if min_eval_score is not None:
                base_score = min(base_score, min_eval_score * 0.25)

        # 4. Công thức kết hợp:
        # Nếu đoạn văn hoàn toàn không liên quan đến chủ đề câu hỏi (overlap_ratio < 0.1),
        # triệt tiêu bớt điểm cộng uy tín để tránh tài liệu uy tín khác chủ đề
        # chèn ép tài liệu trả lời đúng định nghĩa/khái niệm được hỏi.
        rel_gate = min(1.0, float(chunk_dict.get("rerank_score") or 0.0) / 0.08) if chunk_dict.get("rerank_score_available") else 0.0
        effective_auth = (auth_score if overlap_ratio >= 0.1 else auth_score * 0.1) * rel_gate
        composite_score = base_score * (1.0 + effective_auth * 0.65 + density_score * 0.45 * rel_gate) + overlap_ratio * 0.015 * rel_gate
        chunk_dict["composite_priority_score"] = round(composite_score, 6)

        scored_chunks.append(chunk_dict)

    # Sắp xếp giảm dần theo composite_priority_score
    scored_chunks.sort(key=lambda x: x["composite_priority_score"], reverse=True)

    # Nhóm các chunks theo document_id và ưu tiên đa dạng số trang (page_number) trong cùng 1 PDF
    docs_chunks_raw: dict[str, list[dict[str, Any]]] = {}
    for c in scored_chunks:
        doc_key = c.get("document_id") or c.get("doc_filename") or "unknown"
        docs_chunks_raw.setdefault(doc_key, []).append(c)

    docs_chunks: dict[str, list[dict[str, Any]]] = {}
    for dk, ch_list in docs_chunks_raw.items():
        seen_pages: set[Any] = set()
        unique_page_chunks = []
        same_page_overflow = []
        for ch in ch_list:
            pnum = ch.get("page_number")
            if pnum not in seen_pages:
                seen_pages.add(pnum)
                unique_page_chunks.append(ch)
            else:
                same_page_overflow.append(ch)
        docs_chunks[dk] = unique_page_chunks + same_page_overflow

    # Nếu ứng viên chỉ có 1 tài liệu duy nhất (hoặc người dùng chỉ chọn 1 tài liệu)
    if len(docs_chunks) <= 1:
        only_key = next(iter(docs_chunks))
        return docs_chunks[only_key][:min(top_k, max_per_doc)]

    # Nếu có từ 2 tài liệu trở lên: Tập trung vào Top 3 tài liệu liên quan nhất trước
    # để lấy được NHIỀU TRANG khác nhau của mỗi PDF thực sự chứa thông tin (vd: Trang 3, Trang 7, Trang 12)
    selected_chunks: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    doc_counts: dict[str, int] = {k: 0 for k in docs_chunks}

    is_comp_query = bool(re.search(r"\b(so sánh|đối chiếu|phân biệt|khác biệt|giống và khác|compare|contrast|versus|vs\.?|giữa .+ và)\b", query, re.I))
    doc_order = sorted(docs_chunks.keys(), key=lambda dk: docs_chunks[dk][0]["composite_priority_score"], reverse=True)
    top_doc_score = docs_chunks[doc_order[0]][0]["composite_priority_score"] if doc_order else 0.0
    primary_docs = [doc_order[0]] if doc_order else []
    max_primary = 4 if is_comp_query else 3
    score_ratio_min = 0.12 if is_comp_query else 0.35
    for dk in doc_order[1:max_primary]:
        top_ch = docs_chunks[dk][0]
        if (
            top_ch["composite_priority_score"] >= top_doc_score * score_ratio_min
            and (top_ch.get("overlap_ratio", 0.0) >= 0.12 or float(top_ch.get("rerank_score") or top_ch.get("ranking_score") or 0.0) >= 0.45)
        ):
            primary_docs.append(dk)

    if is_comp_query or (len(primary_docs) >= 3 and top_k <= 8):
        max_per_doc = min(max_per_doc, 2)

    # Vòng 1: Chọn trang tốt nhất (Top 1) của các tài liệu thực sự liên quan (primary_docs)
    for dk in primary_docs:
        if len(selected_chunks) >= top_k:
            break
        best_chunk = docs_chunks[dk][0]
        cid = str(best_chunk.get("id") or id(best_chunk))
        if cid not in selected_ids:
            selected_chunks.append(best_chunk)
            selected_ids.add(cid)
            doc_counts[dk] += 1

    # Vòng 2: Lấy trang tốt thứ 2 (khác số trang) của các tài liệu trong primary_docs
    for dk in primary_docs:
        if len(selected_chunks) >= top_k:
            break
        if len(docs_chunks[dk]) > 1:
            second_chunk = docs_chunks[dk][1]
            if second_chunk["composite_priority_score"] >= top_doc_score * score_ratio_min:
                cid = str(second_chunk.get("id") or id(second_chunk))
                if cid not in selected_ids and doc_counts[dk] < max_per_doc:
                    selected_chunks.append(second_chunk)
                    selected_ids.add(cid)
                    doc_counts[dk] += 1

    # Vòng 3: Điền các slot còn lại NHƯNG chỉ lấy các đoạn đạt ngưỡng liên quan tối thiểu
    # (không nhét tài liệu lạc đề vào ngữ cảnh chỉ để lấp đầy top_k)
    for c in scored_chunks:
        if len(selected_chunks) >= top_k:
            break
        if c["composite_priority_score"] < top_doc_score * score_ratio_min:
            continue
        cid = str(c.get("id") or id(c))
        doc_key = c.get("document_id") or c.get("doc_filename") or "unknown"
        if doc_key not in primary_docs and c.get("overlap_ratio", 0.0) < 0.15 and float(c.get("rerank_score") or c.get("ranking_score") or 0.0) < 0.48:
            continue
        page_key = (doc_key, c.get("page_number"))
        if page_key in {(x.get("document_id") or x.get("doc_filename") or "unknown", x.get("page_number")) for x in selected_chunks}:
            continue
        if cid not in selected_ids and doc_counts.get(doc_key, 0) < max_per_doc:
            selected_chunks.append(c)
            selected_ids.add(cid)
            doc_counts[doc_key] = doc_counts.get(doc_key, 0) + 1

    # Sắp xếp các chunks được chọn theo composite_priority_score giảm dần
    selected_chunks.sort(key=lambda x: x["composite_priority_score"], reverse=True)
    return selected_chunks
