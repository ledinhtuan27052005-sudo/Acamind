"""
Hệ thống Đánh giá Độ uy tín Học thuật và Mật độ Thông tin Trọng tâm của Tài liệu
(Academic Authority & Topical Information Density Scorer)

Module này chịu trách nhiệm:
1. Đánh giá cấp độ uy tín học thuật (Level of Evidence / Academic Authority) của từng tài liệu
   dựa trên metadata (title, authors, filename, year) và nội dung (RCT, DSM, Meta-analysis, TS, BS, GS,...).
2. Đánh giá mật độ thông tin trọng tâm (Topical Information Density) của từng chunk đối với câu hỏi
   (độ phủ thuật ngữ chủ đề, dữ liệu định lượng số liệu %, cơ chế, phác đồ).
3. Tích hợp vào quá trình Reranking để ưu tiên đưa các tài liệu uy tín nhất và dày dặn thông tin nhất
   lên đầu Context, đồng thời dán nhãn để LLM ưu tiên trích dẫn.
"""
from __future__ import annotations

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── 1. Từ khóa nhận diện cấp độ uy tín học thuật ──────────────────────────────

# Cấp 1: Tiêu chuẩn vàng lâm sàng & Hướng dẫn chính thức (Gold Standard / Level 1 Evidence)
_TIER_1_KEYWORDS = [
    # Thử nghiệm lâm sàng / RCT
    "randomized controlled trial", "randomised controlled trial", "rct",
    "thử nghiệm lâm sàng", "thu nghiem lam sang", "thực thi lâm sàng", "thuc thi lam sang",
    "báo cáo thực thi lâm sàng", "bao cao thuc thi lam sang", "báo cáo lâm sàng",
    "controlled clinical trial", "clinical trial", "thực nghiệm lâm sàng",
    # Chuẩn chẩn đoán & Hướng dẫn chính thức
    "dsm-5", "dsm-iv", "dsm-5-tr", "icd-11", "icd-10",
    "clinical practice guideline", "hướng dẫn lâm sàng", "hướng dẫn chẩn đoán",
    "phác đồ", "phac do", "phac-do", "hướng dẫn điều trị", "huong dan dieu tri",
    "meta-analysis", "phân tích gộp", "phan tich gop",
    "systematic review", "tổng quan hệ thống", "tong quan he thong",
    # Cơ quan quản lý & Viện chuyên môn hàng đầu
    "bộ y tế", "bo y te", "american psychological association", "apa",
    "viện sức khỏe tâm thần", "vien suc khoe tam than", "who", "world health organization",
]

# Cấp 2: Công trình nghiên cứu có phản biện / Chuyên gia y khoa y tế
_TIER_2_KEYWORDS = [
    # Học vị / Chức danh chuyên môn
    "ts. bs.", "ts.", "bs.", "gs. ts.", "pgs. ts.", "phd", "m.d.", "md", "prof.",
    "bác sĩ chuyên khoa", "chuyên gia lâm sàng", "bệnh viện", "khoa tâm thần",
    # Tạp chí & Nhà xuất bản uy tín
    "journal", "lancet", "jama", "psychiatry", "springer", "elsevier", "nature",
    "clinical psychology", "psychological medicine", "bmc psychiatry",
    # Dấu hiệu phương pháp nghiên cứu thực nghiệm chặt chẽ
    "cỡ mẫu", "sample size", "bdi-ii", "phq-9", "gad-7", "p-value", "kiểm định f",
    "thang đo", "nhóm đối chứng", "control group", "can thiệp", "intervention arm",
]

# Cấp 3: Tài liệu học thuật tổng quan / Giáo trình
_TIER_3_KEYWORDS = [
    "scoping review", "literature review", "tổng quan tài liệu",
    "textbook", "giáo trình", "chuyên khảo", "luận án", "luận văn",
    "kỷ yếu hội thảo", "conference proceedings", "nghiên cứu định tính",
]


def score_document_authority(doc_info: dict[str, Any], sample_content: str = "") -> tuple[float, str, str]:
    """Tính điểm uy tín học thuật của tài liệu.
    
    Returns:
        (bonus_score, tier_name, label_description)
        - bonus_score: từ 0.0 đến 0.50
        - tier_name: "tier_1" | "tier_2" | "tier_3" | "tier_4"
        - label_description: Mô tả cấp độ uy tín học thuật để đưa vào prompt
    """
    title = (doc_info.get("title") or doc_info.get("doc_title") or "").lower()
    filename = (doc_info.get("filename") or doc_info.get("doc_filename") or "").lower()
    authors = (doc_info.get("authors") or doc_info.get("doc_authors") or "").lower()
    content_sample = sample_content[:1500].lower() if sample_content else ""

    combined_text = f"{title} {filename} {authors} {content_sample}"

    # Kiểm tra Cấp 1 (Độ uy tín cao nhất)
    for kw in _TIER_1_KEYWORDS:
        if kw in combined_text:
            label = "Bằng chứng Cấp 1 (Thử nghiệm lâm sàng ngẫu nhiên có đối chứng RCT / Báo cáo thực thi lâm sàng / Hướng dẫn chẩn đoán chuẩn mực)"
            return 0.45, "tier_1", label

    # Kiểm tra Cấp 2 (Nghiên cứu có phản biện / Chuyên gia uy tín)
    for kw in _TIER_2_KEYWORDS:
        if kw in combined_text:
            label = "Bằng chứng Cấp 2 (Công trình nghiên cứu có thẩm định y khoa / Chuyên gia TS. BS. thực hiện)"
            return 0.28, "tier_2", label

    # Kiểm tra Cấp 3 (Học thuật tổng quan)
    for kw in _TIER_3_KEYWORDS:
        if kw in combined_text:
            label = "Bằng chứng Cấp 3 (Tài liệu tổng quan học thuật / Chuyên khảo khoa học)"
            return 0.15, "tier_3", label

    # Cấp 4: Tham khảo chuẩn
    return 0.05, "tier_4", "Tài liệu tham khảo chuyên ngành"


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
    matched_words = [w for w in query_words if w in clean_content]
    overlap_ratio = len(matched_words) / max(len(query_words), 1)

    # Nếu có trans_query (hỗ trợ cross-lingual) -> tính thêm overlap từ câu hỏi đối chiếu
    if trans_query and trans_query.strip().lower() != clean_query:
        en_stop = {"what", "is", "are", "how", "why", "when", "where", "who", "which", "the", "and", "for", "with", "that", "this", "from"}
        vi_stop = {"la", "gi", "nhu", "the", "nao", "cua", "trong", "va", "cac", "nhung"}
        trans_words = [w for w in re.findall(r'\b\w{2,}\b', trans_query.lower()) if len(w) > 2 and w not in en_stop and w not in vi_stop]
        if trans_words:
            matched_trans = [w for w in trans_words if w in clean_content]
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
        density_label = "Rất cao (Đầy đủ số liệu thực nghiệm & phân tích trọng tâm)"
    elif total_density >= 0.15:
        density_label = "Cao (Nhiều dữ liệu liên quan trực tiếp đến câu hỏi)"
    else:
        density_label = "Trung bình (Thông tin bổ trợ tổng quát)"

    return total_density, density_label, overlap_ratio


# ── 3. Rerank tổng hợp dựa trên Uy tín & Mật độ thông tin ────────────────────

def prioritize_candidates_by_authority_and_density(
    candidates: list[dict[str, Any]],
    query: str,
    trans_query: str | None = None,
    top_k: int = 12,
    max_per_doc: int = 4
) -> list[dict[str, Any]]:
    """Tái sắp xếp và gắn nhãn các chunk ứng viên sao cho:
    - Các tài liệu có ĐỘ UY TÍN CAO NHẤT (Tier 1: RCT, Thử nghiệm lâm sàng, DSM, Phác đồ Bộ Y Tế)
    - Và NHIỀU THÔNG TIN ĐÚNG CHỦ ĐỀ NHẤT (Topical & Quantitative Density)
    được ưu tiên xếp hạng lên các vị trí đầu tiên trong danh sách Context.
    
    ĐẶC BIỆT (Multi-Document Diversity & Cross-Source Synthesis):
    - Đảm bảo trích xuất từ NHIỀU TÀI LIỆU KHÁC NHAU (tối thiểu 2 - 4 tài liệu nếu ứng viên có nhiều nguồn).
    - Giới hạn mỗi tài liệu tối đa max_per_doc chunks (mặc định 4) để tránh 1 tài liệu duy nhất chiếm hết context.
    - Phân bổ slot theo vòng để tài liệu lý thuyết, tài liệu lâm sàng, phác đồ điều trị đều có cơ hội xuất hiện.
    """
    if not candidates:
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

        # 3. Điểm gốc: Rerank score nếu có, hoặc RRF score
        base_score = float(chunk_dict.get("rerank_score") or chunk_dict.get("rrf_score") or 0.01)

        # 4. Công thức kết hợp:
        # Nếu đoạn văn hoàn toàn không liên quan đến chủ đề câu hỏi (overlap_ratio < 0.1),
        # triệt tiêu bớt điểm cộng uy tín để tránh tài liệu uy tín khác chủ đề
        # chèn ép tài liệu trả lời đúng định nghĩa/khái niệm được hỏi.
        effective_auth = auth_score if overlap_ratio >= 0.1 else auth_score * 0.1
        composite_score = base_score * (1.0 + effective_auth * 0.7 + density_score * 0.5)
        chunk_dict["composite_priority_score"] = round(composite_score, 6)

        scored_chunks.append(chunk_dict)

    # Sắp xếp giảm dần theo composite_priority_score
    scored_chunks.sort(key=lambda x: x["composite_priority_score"], reverse=True)

    # Nhóm các chunks theo document_id
    docs_chunks: dict[str, list[dict[str, Any]]] = {}
    for c in scored_chunks:
        doc_key = c.get("document_id") or c.get("doc_filename") or "unknown"
        docs_chunks.setdefault(doc_key, []).append(c)

    # Nếu ứng viên chỉ có 1 tài liệu duy nhất (hoặc người dùng chỉ chọn 1 tài liệu)
    if len(docs_chunks) <= 1:
        return scored_chunks[:top_k]

    # Nếu có từ 2 tài liệu trở lên: Triển khai thuật toán Đa dạng hóa Đa tài liệu (Multi-Document Diversity)
    selected_chunks: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    doc_counts: dict[str, int] = {k: 0 for k in docs_chunks}

    # Sắp xếp thứ tự ưu tiên của các tài liệu theo điểm chunk cao nhất của mỗi tài liệu
    doc_order = sorted(docs_chunks.keys(), key=lambda dk: docs_chunks[dk][0]["composite_priority_score"], reverse=True)

    # Vòng 1: Chọn chunk tốt nhất (Top 1) của TỪNG tài liệu liên quan
    for dk in doc_order:
        if len(selected_chunks) >= top_k:
            break
        best_chunk = docs_chunks[dk][0]
        cid = str(best_chunk.get("id"))
        if cid not in selected_ids:
            selected_chunks.append(best_chunk)
            selected_ids.add(cid)
            doc_counts[dk] += 1

    # Vòng 2: Lấy thêm chunk tốt thứ 2 của mỗi tài liệu (nếu còn slot)
    for dk in doc_order:
        if len(selected_chunks) >= top_k:
            break
        if len(docs_chunks[dk]) > 1:
            second_chunk = docs_chunks[dk][1]
            cid = str(second_chunk.get("id"))
            if cid not in selected_ids and doc_counts[dk] < max_per_doc:
                selected_chunks.append(second_chunk)
                selected_ids.add(cid)
                doc_counts[dk] += 1

    # Vòng 3: Điền các slot còn lại từ các chunk có composite_priority_score cao nhất
    # (giới hạn mỗi tài liệu tối đa max_per_doc chunks)
    for c in scored_chunks:
        if len(selected_chunks) >= top_k:
            break
        cid = str(c.get("id"))
        doc_key = c.get("document_id") or c.get("doc_filename") or "unknown"
        if cid not in selected_ids and doc_counts.get(doc_key, 0) < max_per_doc:
            selected_chunks.append(c)
            selected_ids.add(cid)
            doc_counts[doc_key] = doc_counts.get(doc_key, 0) + 1

    # Nếu vẫn chưa đủ top_k, nới lỏng giới hạn max_per_doc để điền đủ top_k
    if len(selected_chunks) < top_k:
        for c in scored_chunks:
            if len(selected_chunks) >= top_k:
                break
            cid = str(c.get("id"))
            if cid not in selected_ids:
                selected_chunks.append(c)
                selected_ids.add(cid)

    # Sắp xếp các chunks được chọn theo composite_priority_score giảm dần
    selected_chunks.sort(key=lambda x: x["composite_priority_score"], reverse=True)
    return selected_chunks
