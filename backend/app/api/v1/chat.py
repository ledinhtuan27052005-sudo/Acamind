from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import unicodedata
import re
import json
import logging
import uuid
from urllib.parse import urlparse
from app.db.postgres import get_db
from app.services.retriever import (
    retrieve,
    retrieve_via_memory,
    classify_and_decompose_query,
    _resolve_explicit_title_scope,
    _sanitize_uuid_list,
)
from app.services.comparison_coverage import assess_target_coverage
from app.services.scientific_appraiser import (
    harmonize_cross_study_metrics,
    compute_cross_study_concordance,
)
from app.services.evidence_policy import (assess_and_repair, needs_verification, policy_prompt,
                                          qualify_missing_evidence, render_verified_matrix)
from app.services.generator import (
    generate_stream, generate_answer, classify_query_domain,
    generate_stream_web_search, generate_stream_direct,
)
from app.services.web_scraper import duckduckgo_search, fetch_public_source
from app.services.file_parser import parse_file, parse_file_chunks
from app.services.llm_client import llm_configuration_error
from app.core.security import get_optional_user, get_current_user
from app.core.document_access import readable_document_ids
from app.core.plan_utils import get_limits, count_today_chats, count_monthly_chats

logger = logging.getLogger(__name__)


from app.services.cross_lingual import detect_language


PREDEFINED_QA = {
    # Tiếng Việt
    "hi": "Xin chào bạn, bắt đầu ngay thôi!",
    "chao": "Xin chào bạn, bắt đầu ngay thôi!",
    "xin chao": "Xin chào bạn, bắt đầu ngay thôi!",
    "hello": "Xin chào bạn, bắt đầu ngay thôi!",
    "tram cam la gi": "Trầm cảm là một rối loạn tâm trạng phổ biến, đặc trưng bởi cảm giác buồn bã, mất hứng thú kéo dài và mệt mỏi, ảnh hưởng sâu sắc đến sinh hoạt và suy nghĩ.",
    "lo au la gi": "Lo âu là phản ứng tự nhiên của cơ thể trước căng thẳng, nhưng rối loạn lo âu xảy ra khi sự sợ hãi và lo lắng quá mức, kéo dài và gây cản trước cuộc sống hàng ngày.",
    "cbt la gi": "CBT (Cognitive Behavioral Therapy - Liệu pháp nhận thức hành vi) là phương pháp trị liệu giúp nhận diện và thay đổi các suy nghĩ, hành vi tiêu cực nhằm cải thiện sức khỏe tâm thần.",
    "stress co loi hay co hai": "Stress có thể có lợi (stress tích cực - eustress) giúp tập trung và hành động, nhưng stress kéo dài (distress) sẽ gây hại nghiêm trọng cho thể chất và tinh thần.",
    "lam sao de giam stress nhanh": "Bạn có thể áp dụng các kỹ thuật như hít thở sâu, thiền định, tập thể dục nhẹ, nghe nhạc, hoặc viết nhật ký để giải tỏa căng thẳng nhanh chóng.",
    "roi loan luong cuc la gi": "Rối loạn lưỡng cực là tình trạng sức khỏe tâm thần gây ra sự biến động nghiêm trọng về tâm trạng, năng lượng và khả năng hoạt động, chuyển đổi giữa hưng cảm và trầm cảm.",
    "tam ly hoc hanh vi la gi": "Tâm lý học hành vi tập trung vào việc nghiên cứu các hành vi có thể quan sát được và cách hành vi được hình thành, thay đổi thông qua quá trình tương tác với môi trường.",
    "co che tu ve cua cai toi la gi": "Cơ chế tự vệ là các chiến lược tâm lý vô thức (như dồn nén, phóng chiếu, hợp lý hóa) được tâm trí sử dụng để tự bảo vệ khỏi lo âu và xung đột nội tâm.",
    "ocd la gi": "OCD (Rối loạn ám ảnh cưỡng chế) là một rối loạn tâm thần kéo dài, đặc trưng bởi các ý nghĩ ám ảnh lặp đi lặp lại không mong muốn (ám ảnh) và các hành vi nghi thức để giảm lo âu (cưỡng chế).",
    "tri tue cam xuc la gi": "EQ (Trí tuệ cảm xúc) là khả năng nhận biết, hiểu, quản lý và biểu đạt cảm xúc của bản thân cũng như nhận biết, thấu hiểu cảm xúc của người khác.",

    # Tiếng Anh (English)
    "what is depression": "Depression is a common mental health disorder characterized by persistent sadness, loss of interest in activities, and fatigue, significantly affecting daily life.",
    "what is anxiety": "Anxiety is a natural response to stress, but anxiety disorders involve excessive, persistent fear and worry that interfere with daily activities.",
    "what is cbt": "CBT (Cognitive Behavioral Therapy) is a treatment method that helps identify and change negative thoughts and behaviors to improve mental health.",
    "is stress good or bad": "Stress can be beneficial (positive stress - eustress) by helping you focus and act, but prolonged stress (distress) is highly harmful to physical and mental health.",
    "how to reduce stress quickly": "You can apply techniques like deep breathing, meditation, light exercise, listening to music, or journaling to relieve stress quickly.",
    "what is bipolar disorder": "Bipolar disorder is a mental health condition that causes extreme shifts in mood, energy, activity levels, and concentration, fluctuating between mania and depression.",
    "what is behavioral psychology": "Behavioral psychology focuses on studying observable behaviors and how behaviors are learned and modified through interactions with the environment.",
    "what are ego defense mechanisms": "Defense mechanisms are unconscious psychological strategies (like repression, projection, rationalization) used to protect the mind from anxiety and internal conflict.",
    "what is ocd": "OCD (Obsessive-Compulsive Disorder) is a long-lasting mental disorder where a person has uncontrollable, reoccurring thoughts (obsessions) and/or behaviors (compulsions) that he or she feels the urge to repeat.",
    "what is emotional intelligence": "EQ (Emotional Intelligence) is the ability to recognize, understand, manage, and express one's own emotions, as well as recognize and understand the emotions of others."
}

def get_predefined_answer(query: str, lang: str, ready_count: int = 0) -> str | None:
    # Chuẩn hóa query: lower, không dấu, bỏ ký tự đặc biệt
    q = query.lower().strip()
    q = re.sub(r'[?!.,;:\-\s]+$', '', q)
    q = q.strip()
    # Loại bỏ chỉ dẫn chế độ của hệ thống (nếu có từ frontend)
    q = re.sub(r'^\[he\s+thong:[^\]]+\]', '', q).strip()
    q = re.sub(r'^\[system:[^\]]+\]', '', q).strip()
    
    # Bỏ dấu tiếng Việt
    q_normalized = unicodedata.normalize('NFKD', q)
    q_normalized = ''.join([c for c in q_normalized if not unicodedata.combining(c)])
    q_normalized = q_normalized.replace('đ', 'd').strip()

    # Xử lý câu chào hỏi riêng dựa trên ngôn ngữ phát hiện
    if q_normalized in ("hi", "hello"):
        if lang == "en":
            return "Hello! Let's get started!"
        return "Xin chào bạn, bắt đầu ngay thôi!"
        
    if q_normalized in ("chao", "xin chao"):
        return "Xin chào bạn, bắt đầu ngay thôi!"

    # Khi hệ thống đã có tài liệu PDF sẵn sàng (ready_count > 0), ưu tiên truy vấn RAG
    # để trả lời kèm trích dẫn [ten_file.pdf - Trang X] và highlight trên tài liệu gốc.
    if ready_count > 0:
        return None

    # Thử khớp chính xác các key định nghĩa sẵn (chỉ khi kho chưa có tài liệu)
    if q in PREDEFINED_QA:
        return PREDEFINED_QA[q]
        
    if q_normalized in PREDEFINED_QA:
        return PREDEFINED_QA[q_normalized]
        
    # Thử khớp tương đối
    for key, value in PREDEFINED_QA.items():
        if key in q and len(q) - len(key) < 5:
            return value
        if key in q_normalized and len(q_normalized) - len(key) < 5:
            return value
    return None


def _deep_mode_instruction(raw_query: str, lang: str) -> str:
    """Chỉ dẫn chế độ Chuyên sâu, phân nhánh theo loại câu hỏi.

    - Câu so sánh (bộ định tuyến trả >= 2 đối tượng): bảng Tiêu chí × Đối tượng, hàng = tiêu chí người dùng hỏi.
    - Câu thường: trả lời đủ từng ý; bảng tổng hợp chỉ gồm tài liệu thực sự liên quan.
    Không áp đặt số hàng cố định hay giới hạn số từ cứng (trước đây: "3 hàng", "dưới 150 từ"
    khiến LLM nhồi tài liệu không liên quan và bỏ sót ý ở câu hỏi dài).
    """
    body = re.sub(r'^\[(?:he\s+thong|system):[^\]]+\]\s*', '', raw_query, flags=re.IGNORECASE).strip()
    try:
        route = classify_and_decompose_query(body)
    except Exception:
        route = {"num_targets": 1, "sub_queries": [body]}
    targets = [t for t in (route.get("sub_queries") or []) if t][:4]
    focus = (route.get("comparison_focus") or "").strip()
    if lang == "en":
        if int(route.get("num_targets") or 1) > 1 and len(targets) >= 2:
            cols = " | ".join(targets)
            crit = focus or "the dimensions the user asked about"
            return (
                "[System: DEEP MODE (MODE=DEEP), COMPARISON question. Write 1-2 short synthesis paragraphs with "
                "[filename.pdf - Page X] citations, then draw a Criterion x Target comparison matrix: "
                f"| Criterion | {cols} | Agreement & differences |. Each row is one criterion the user asked about ({crit}); "
                "each cell states the evidence for THAT target with its own citation, or 'Not found in retrieved passages'. "
                "Never put unrelated documents in the table or references. Length follows the number of requested points.] "
            )
        return (
            "[System: DEEP MODE (MODE=DEEP). Synthesize all aspects of the question that have evidence in the retrieved "
            "passages with [filename.pdf - Page X] citations, including PICO facts (population, intervention, comparison, "
            "outcomes; N, effect sizes) when reported, and then clearly state which requested aspects are 'not found in "
            "retrieved passages' (do NOT output __NO_CONTEXT__ if at least one aspect of the question is supported). "
            "If 2 or more relevant documents exist, add a short agreement/difference paragraph and an Evidence Synthesis Matrix "
            "| Study / Document | Design & Sample | Key Findings | Citation | with one row per TRULY relevant document "
            "(never add unrelated documents to fill rows).] "
        )
    if int(route.get("num_targets") or 1) > 1 and len(targets) >= 2:
        cols = " | ".join(targets)
        crit = focus or "các tiêu chí người dùng hỏi"
        return (
            "[He thong: Chế độ CHUYÊN SÂU (MODE=DEEP), câu hỏi SO SÁNH. Viết 1-2 đoạn tổng hợp ngắn kèm nhãn "
            "[ten_file.pdf - Trang X], rồi vẽ Bảng Ma trận Đối chiếu theo Tiêu chí: "
            f"| Tiêu chí | {cols} | Nhận định đồng thuận & khác biệt |. Mỗi hàng là một tiêu chí người dùng hỏi ({crit}); "
            "mỗi ô ghi dữ kiện của ĐÚNG đối tượng đó kèm nhãn trích dẫn riêng, nếu không có thì ghi "
            "'Chưa tìm thấy trong các đoạn được truy xuất'. TUYỆT ĐỐI không đưa tài liệu không liên quan vào bảng hoặc "
            "danh mục tham khảo. Độ dài tùy theo số ý cần trả lời.] "
        )
    return (
        "[He thong: Chế độ CHUYÊN SÂU (MODE=DEEP). Trình bày CÔ ĐỌNG từng ý trong câu hỏi có bằng chứng trong DOCUMENT CONTEXT "
        "(mỗi ý 1-2 câu súc tích, không lặp lại ý; nêu khái niệm, phân loại, biểu hiện, quy trình đánh giá, can thiệp và dữ kiện "
        "PICO như cỡ mẫu N, cỡ hiệu ứng nếu có) kèm nhãn [ten_file.pdf - Trang X] ở cuối mỗi câu; KHÔNG xuất __NO_CONTEXT__ khi "
        "ngữ cảnh đã có bằng chứng cho một phần câu hỏi, mà hãy trả lời phần có bằng chứng rồi nêu gọn trong 1 câu những ý còn lại "
        "'chưa tìm thấy trong các đoạn được truy xuất'. Sau đó nếu có từ 2 tài liệu liên quan trở lên, nêu ngắn gọn điểm Đồng thuận & Khác biệt (Dong thuan & Khac biet) và lập ngay Bảng Tổng hợp Bằng chứng "
        "(Evidence Synthesis Matrix) | Nghiên cứu / Tài liệu | Thiết kế & Đối tượng | Phát hiện chính | Nguồn trích dẫn | "
        "(mỗi ô ngắn gọn dưới 20 từ) chỉ gồm những tài liệu THỰC SỰ liên quan (không thêm tài liệu không liên quan cho đủ hàng).] "
    )


def _normalize_mode_instruction(raw_query: str, lang: str) -> str:
    """Chuẩn hóa chỉ dẫn hệ thống (MODE=BRIEF / MODE=DEEP) theo đúng ngôn ngữ câu hỏi."""
    sent_query = raw_query
    mode_marker = re.search(r'\bmode\s*=\s*(brief|deep)\b', raw_query, flags=re.IGNORECASE)
    is_brief_mode = (
        mode_marker.group(1).lower() == "brief"
        if mode_marker
        else any(kw in raw_query.lower() for kw in ["ngan gon", "suc tich", "briefly", "concisely"])
    )
    if "[he thong:" not in raw_query.lower() and "[system:" not in raw_query.lower():
        return sent_query
    if is_brief_mode:
        brief = ('[System: Reply concisely in about 2-4 sentences. Answer only the question and avoid unasked topics.] '
                 if lang == "en" else
                 '[He thong: Hay tra loi ngan gon trong khoang 2-4 cau, dung trong tam cau hoi va khong mo rong sang chu de khac.] ')
        return re.sub(r'^\[(?:he\s+thong|system):[^\]]+\]\s*', lambda _m: brief, raw_query, flags=re.IGNORECASE)
    deep = _deep_mode_instruction(raw_query, lang)
    return re.sub(r'^\[(?:he\s+thong|system):[^\]]+\]\s*', lambda _m: deep, raw_query, flags=re.IGNORECASE)


_CJK_PUNCT_MAP = str.maketrans({
    "。": ". ",
    "，": ", ",
    "：": ": ",
    "；": "; ",
    "（": " (",
    "）": ") ",
    "【": "[",
    "】": "]",
    "、": ", ",
    "“": '"',
    "”": '"',
})
_CJK_CHAR_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")


def _clean_cjk_leakage(text_line: str) -> str:
    """Loại bỏ triệt để hiện tượng rò rỉ chữ Hán (CJK) từ mô hình đa ngữ qwen2.5."""
    if not text_line or not _CJK_CHAR_RE.search(text_line):
        return text_line
    cleaned = text_line.translate(_CJK_PUNCT_MAP)
    cleaned = re.sub(
        r"[^.!?\n\[\]]*[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]{2,}[^.!?\n\[\]]*(?:[.!?]\s*)?",
        " ",
        cleaned,
    )
    cleaned = _CJK_CHAR_RE.sub("", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned


def _normalize_stream_citations(text_line: str) -> str:
    """Chuẩn hóa định dạng trích dẫn trên từng dòng stream để UI luôn render nút bấm được."""
    if not text_line:
        return text_line
    text_line = _clean_cjk_leakage(text_line)
    # Đóng ngoặc vuông bị thiếu ở cuối dòng nếu thẻ trích dẫn dạng [file.pdf - Trang X bị cắt cuối stream
    text_line = re.sub(
        r"(\[[^\[\]\n]+?\.(?:pdf|docx|xlsx)\s*[-–—,:]\s*(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)\s*\d+)\s*$",
        r"\1]",
        text_line,
        flags=re.IGNORECASE,
    )
    # Chuyển (file.pdf - Trang 1) -> [file.pdf - Trang 1]
    text_line = re.sub(
        r'\(([^\(\)\[\]\n]+?\.pdf\s*[-–—,:]\s*(?:Page|Trang|tr\.?|p\.?|pp\.?)\s*\d+(?:\s*,\s*\d+)*)\)',
        r'[\1]',
        text_line,
        flags=re.IGNORECASE,
    )
    # Tách [file.pdf - Trang 1, 2] -> [file.pdf - Trang 1] [file.pdf - Trang 2]
    def _split_pages(m: re.Match[str]) -> str:
        fname, marker, page_list = m.groups()
        pages = re.findall(r'\d+', page_list)
        return " ".join(f"[{fname.strip()} - {marker} {p}]" for p in pages)

    text_line = re.sub(
        r'\[([^\[\]\n]+?\.pdf)\s*[-–—,:]\s*(Trang|Page|tr\.?|p\.?|pp\.?)\s*(\d+(?:\s*,\s*(?:(?:Trang|Page|tr\.?|p\.?|pp\.?)\s*)?\d+)+)\]',
        _split_pages,
        text_line,
        flags=re.IGNORECASE,
    )
    # Đưa nhãn trích dẫn bị đặt nhầm sau dấu chấm câu (. [file.pdf - Trang X]) vào trước dấu chấm
    text_line = re.sub(
        r"\.\s*((?:\[[^\[\]\n]+?\.(?:pdf|docx|xlsx)\s*[-–—,:]\s*(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)[^\[\]\n]*\]\s*)+)",
        lambda m: " " + m.group(1).strip() + ".",
        text_line,
        flags=re.IGNORECASE,
    )
    # Gộp các nhãn trích dẫn giống hệt nhau đứng liền kề (vd. [A.pdf - Trang 4] [A.pdf - Trang 4])
    text_line = re.sub(
        r"(\[[^\[\]\n]+?\.(?:pdf|docx|xlsx)\s*[-–—,:]\s*(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)[^\[\]\n]*\])(?:\s*\1)+",
        r"\1",
        text_line,
        flags=re.IGNORECASE,
    )
    text_line = re.sub(r"(?i)((?:chưa|không)\s+được\s+đề\s+cập\s+(?:trực\s+tiếp|chi\s+tiết|cụ\s+thể)\s+trong\s+các\s+(?:tài\s+liệu|đoạn\s+trích)(?:\s+được\s+truy\s+xuất)?)(?:\s*\[[^\[\]\n]+?\.(?:pdf|docx|xlsx)\s*[-–—,:]\s*(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)[^\[\]\n]*\])+", r"\1", text_line)
    if len(re.sub(r"\[[^\]]+\]", "", text_line).strip()) < 95 and not re.search(r"\b\d+(?:[.,]\d+)?\b", re.sub(r"\[[^\]]+\]", "", text_line)) and re.search(r"(?i)^(?:\s*[-•*]\s*)?(?:trong các đoạn|các đoạn được truy xuất|tài liệu|hiện tại)?[^.!?\n]{0,30}(?:không có thông tin|không tìm thấy thông tin|chưa tìm thấy thông tin|chưa tìm thấy đủ bằng chứng|dựa vào kiến thức chung|kiến thức bên ngoài|no sufficient evidence|no relevant information|not found in retrieved passages)", text_line): text_line = re.sub(r"\s*\[[^\[\]\n]+?\.(?:pdf|docx|xlsx)\s*[-–—,:]\s*(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)[^\[\]\n]*\]", "", text_line, flags=re.I)
    return text_line


_CITATION_TAG_RE = re.compile(r"\s*\[([^\[\]\n]+?\.(?:pdf|docx|xlsx))\s*[-–—,:]\s*(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)\s*([^\[\]\n]*)\]", re.I)
_ABSENCE_SENTENCE_RE = re.compile(
    r"(?i)(?:không|chưa)\s+(?:có|tìm\s+thấy)\s+(?:thông\s+tin|dữ\s+kiện|dữ\s+liệu|bằng\s+chứng|số\s+liệu)"
    r"|(?:không|chưa)\s+(?:được\s+)?(?:đề\s+cập|cung\s+cấp|báo\s+cáo)|không\s+đề\s+cập|không\s+thể\s+xác\s+định|chưa\s+thể\s+xác\s+định"
    r"|not\s+found\s+in\s+(?:the\s+)?retrieved|no\s+(?:relevant\s+)?information|not\s+(?:reported|mentioned|provided)"
)
_CONTRAST_RE = re.compile(r"(?i)\b(?:nhưng|tuy\s+nhiên|trong\s+khi|còn|ngược\s+lại|however|but|whereas|while)\b")
_LEADING_PREFIX_RE = re.compile(
    r"(?i)^(?:[\s•\-*\d.)]+|(?:đồng\s+thuận|khác\s+biệt)\s*:\s*|(?:tuy\s+nhiên|nhưng|mặt\s+khác|ngoài\s+ra|do\s+đó|vì\s+vậy|however|but)\s*,?\s*)+"
)


def _strip_absence_sentence_citations(text_line: str) -> str:
    """Xóa nhãn trích dẫn khỏi CÂU khẳng định thiếu thông tin (xét từng câu, không chỉ dòng ngắn).

    Một trang được truy xuất không thể là bằng chứng cho việc "không có thông tin". Câu có từ nối đối lập
    ở giữa câu (nhưng/tuy nhiên/...) chỉ giữ lại phần trích dẫn thuộc vế khẳng định trước từ nối.
    """
    if "[" not in text_line or text_line.lstrip().startswith("|") or not _ABSENCE_SENTENCE_RE.search(text_line):
        return text_line
    parts = re.split(r"(?<=[.!?])(\s+)", text_line)
    out = []
    for part in parts:
        if part and not part.isspace() and _ABSENCE_SENTENCE_RE.search(part):
            trimmed = _LEADING_PREFIX_RE.sub("", part)
            mid_contrasts = [m for m in _CONTRAST_RE.finditer(trimmed) if m.start() > 0]
            if not mid_contrasts:
                part = _CITATION_TAG_RE.sub("", part)
            else:
                # Nếu mệnh đề thiếu thông tin nằm sau từ nối đối lập ở giữa câu, chỉ xóa trích dẫn ở mệnh đề đó
                last_c = mid_contrasts[-1]
                offset = len(part) - len(trimmed) + last_c.start()
                head, tail = part[:offset], part[offset:]
                if _ABSENCE_SENTENCE_RE.search(tail):
                    part = head + _CITATION_TAG_RE.sub("", tail)
        out.append(part)
    return "".join(out)


_NUM_TOKEN_RE = re.compile(r"(?<![\w.,])(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)(?![\w])")
_FILENAME_OR_ID_RE = re.compile(
    r"\b(?:\S+\.(?:pdf|docx|xlsx)|(?:PMC|ERIC_E[JD]|PsyArXiv_)\w+|\d{4}\.\d{4,5}(?:v\d+)?|(?:DSM|ICD|AIS|PHQ|GAD|BDI|SCL|DASS)\s*[-–]?\s*[IVX\d]+)\b",
    re.I,
)


def _numeric_variants(tok: str) -> set[str]:
    raw = tok.strip()
    variants = {raw, raw.replace(",", "."), raw.replace(".", ","), raw.replace(",", "").replace(".", "")}
    if re.fullmatch(r"\d+[.,]\d+", raw):
        variants.add(raw.replace(",", ".").lstrip("0") or "0")
    return {v for v in variants if v}


def _repair_citation_filenames(text_line: str, context_chunks: list[dict]) -> str:
    """Sửa lỗi chính tả tên file hoặc tên tiêu đề trong nhãn trích dẫn [xxx - Trang N] về đúng doc_filename thực tế."""
    if "[" not in text_line or not context_chunks:
        return text_line
    from difflib import SequenceMatcher
    valid_docs: list[tuple[str, str, set[int]]] = []
    seen_fn: set[str] = set()
    doc_pages: dict[str, set[int]] = {}
    for c in context_chunks:
        fn = str(c.get("doc_filename") or c.get("filename") or "").strip()
        if not fn:
            continue
        fn_low = fn.lower()
        try:
            doc_pages.setdefault(fn_low, set()).add(int(c.get("page_number") or 1))
        except (ValueError, TypeError):
            pass
        if fn_low not in seen_fn:
            seen_fn.add(fn_low)
            valid_docs.append((fn, str(c.get("doc_title") or "").strip().lower(), doc_pages[fn_low]))
    if not valid_docs:
        return text_line

    def _fix_tag(m: re.Match[str]) -> str:
        raw_name, marker, pg_str = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        raw_low = raw_name.lower()
        for fn, _, _ in valid_docs:
            if raw_low == fn.lower():
                return m.group(0)
        try:
            pg_int = int(re.findall(r"\d+", pg_str)[0])
        except Exception:
            pg_int = -1
        best_fn = None
        best_score = 0.0
        for fn, title_low, pages in valid_docs:
            fn_low = fn.lower()
            sim_fn = SequenceMatcher(None, raw_low, fn_low).ratio()
            if raw_low.endswith(".pdf") and fn_low.endswith(".pdf"):
                sim_stem = SequenceMatcher(None, raw_low[:-4], fn_low[:-4]).ratio()
                sim_fn = max(sim_fn, sim_stem)
            sim_title = 0.85 if (title_low and len(raw_low) >= 6 and (raw_low in title_low or title_low in raw_low)) else 0.0
            score = max(sim_fn, sim_title)
            if pg_int in pages:
                score += 0.08
            if score > best_score:
                best_score = score
                best_fn = fn
        if best_fn and best_score >= 0.74:
            return f"[{best_fn} - {marker} {pg_str}]"
        return m.group(0)

    return re.sub(
        r"\[([^\[\]\n]+?)\s*[-–—,:]\s*(Trang|Page|Sheet|tr\.?|p\.?|pp\.?)\s*(\d+[^\[\]\n]*)\]",
        _fix_tag,
        text_line,
        flags=re.I,
    )


def _verify_numeric_citations(text_line: str, context_chunks: list[dict]) -> str:
    """Đánh dấu câu có con số không xuất hiện trong bất kỳ trang nào mà chính câu đó trích dẫn.

    Chỉ xét số có >= 2 chữ số hoặc số thập phân (bỏ năm 1900–2099, số trang, mã tên file PDF/arXiv). Không gọi LLM.
    """
    if "[" not in text_line or not context_chunks:
        return text_line
    page_text: dict[tuple[str, str], str] = {}
    doc_text: dict[str, str] = {}
    for c in context_chunks:
        fn = str(c.get("doc_filename") or c.get("filename") or "").strip().lower()
        pg = str(c.get("page_number") or "").strip()
        if fn:
            chunk_blob = " " + str(c.get("parent_context") or "") + " " + str(c.get("content") or "")
            key = (fn, pg)
            page_text[key] = page_text.get(key, "") + chunk_blob
            doc_text[fn] = doc_text.get(fn, "") + chunk_blob
    is_table_row = text_line.lstrip().startswith("|") and text_line.rstrip().endswith("|")
    parts = [text_line] if is_table_row else re.split(r"(?<=[.!?])(\s+)", text_line)
    out = []
    for part in parts:
        tags = _CITATION_TAG_RE.findall(part or "")
        if not tags:
            out.append(part)
            continue
        body = _FILENAME_OR_ID_RE.sub(" ", _CITATION_TAG_RE.sub(" ", part))
        nums = []
        for tok in _NUM_TOKEN_RE.findall(body):
            digits = re.sub(r"\D", "", tok)
            if len(digits) < 2 and not re.search(r"[.,]", tok):
                continue
            if re.fullmatch(r"(?:19|20)\d{2}", tok):
                continue
            nums.append(tok)
        if not nums:
            out.append(part)
            continue
        cited_texts = []
        for fn, pg in tags:
            fn_key = fn.strip().lower()
            pg_num = (re.findall(r"\d+", pg) or [""])[0]
            cited_texts.append(page_text.get((fn_key, pg_num), "") + " " + doc_text.get(fn_key, ""))
        cited_blob = " ".join(cited_texts)
        if not cited_blob.strip():
            out.append(part)  # không có văn bản trang để đối chiếu → không kết luận
            continue
        missing = [n for n in nums if not any(v in cited_blob for v in _numeric_variants(n))]
        if missing:
            note = " (chưa xác minh được số liệu " + ", ".join(dict.fromkeys(missing)) + " trong trang được trích)"
            stripped = part.rstrip()
            trail = part[len(stripped):]
            if is_table_row and stripped.endswith("|"):
                part = stripped[:-1].rstrip() + note + " |" + trail
            else:
                end_punct = stripped[-1] if stripped and stripped[-1] in ".!?" else ""
                core = stripped[:-1] if end_punct else stripped
                part = core + note + end_punct + trail
        out.append(part)
    return "".join(out)



def _build_references_block(full_answer: str, context_chunks: list[dict], lang: str) -> str:
    """Trích xuất citations trong câu trả lời và tạo mục Tài liệu tham khảo / References."""
    if len(re.sub(r"\[[^\]]+\]", "", full_answer).strip()) < 95 and re.search(r"(?i)^(?:\s*[-•*]\s*)?(?:trong các đoạn|các đoạn được truy xuất|tài liệu|hiện tại)?[^.!?\n]{0,30}(?:không có thông tin|không tìm thấy thông tin|chưa tìm thấy thông tin|chưa tìm thấy đủ bằng chứng|dựa vào kiến thức chung|kiến thức bên ngoài|no sufficient evidence|no relevant information|not found in retrieved passages)", full_answer): return ""
    citation_pattern = re.compile(r'\[([^\]]+)\]')
    raw_citations = citation_pattern.findall(full_answer)

    doc_map: dict[str, dict] = {}
    for c in context_chunks:
        doc_id = str(c.get("document_id") or "")
        doc_key = str(c.get("doc_filename") or c.get("filename") or doc_id) if doc_id == "inline_file" else doc_id
        if doc_key and doc_key not in doc_map:
            doc_map[doc_key] = {
                "filename": c.get("doc_filename") or c.get("filename") or c.get("doc_title") or "Tài liệu",
                "title": c.get("doc_title") or "",
                "authors": c.get("doc_authors") or "",
            }

    seen_keys: set[str] = set()
    refs_lines: list[str] = []
    ref_idx = 1
    for raw in raw_citations:
        sub_parts = re.split(r'[;,]', raw) if raw.lower().count('.pdf') > 1 else raw.split(';')
        for sub in sub_parts:
            key = sub.strip()
            if not key or key in seen_keys:
                continue
            page_match = re.search(
                r'([^\[]+?)\s*[-–—,:|]\s*(?:Page|Trang|tr\.?|p\.?|pp\.?)\s*(\d+)',
                key,
                re.IGNORECASE,
            )
            sheet_match = re.search(
                r'([^\[]+?)\s*[-–—,:|]\s*Sheet\s*:?\s*([^\]]+)',
                key,
                re.IGNORECASE,
            ) if not page_match else None
            if page_match or sheet_match:
                seen_keys.add(key)
                if page_match:
                    fname = page_match.group(1).strip()
                    loc_label = f"Page {page_match.group(2).strip()}" if lang == "en" else f"Trang {page_match.group(2).strip()}"
                else:
                    fname = sheet_match.group(1).strip()
                    loc_label = f"Sheet: {sheet_match.group(2).strip()}"
                found_doc = None
                for _, doc_info in doc_map.items():
                    if (
                        fname.lower() == doc_info["filename"].lower()
                        or (doc_info["title"] and fname.lower() == doc_info["title"].lower())
                        or fname.lower() in doc_info["filename"].lower()
                    ):
                        found_doc = doc_info
                        break
                if found_doc:
                    canonical_fn = found_doc["filename"] or fname
                    title_part = found_doc["title"] or canonical_fn
                    authors_part = f" — *{found_doc['authors']}*" if found_doc["authors"] else ""
                    refs_lines.append(f"{ref_idx}. [{canonical_fn} - {loc_label}] **{title_part}**{authors_part}")
                    ref_idx += 1

    if not refs_lines:
        return ""
    heading = "## References\n\n" if lang == "en" else "## Tài liệu tham khảo\n\n"
    return "\n\n---\n" + heading + "\n".join(refs_lines)


def _enforce_chat_limits(current_user, db: Session) -> None:
    """Kiểm tra giới hạn câu hỏi theo ngày và theo tháng của gói cước."""
    if current_user is None:
        return
    limits = get_limits(current_user)
    if limits.get("max_daily_chat") is not None:
        today_count = count_today_chats(current_user.id, db)
        if today_count >= limits["max_daily_chat"]:
            raise HTTPException(
                429,
                f"❌ Gói {limits['label']} chỉ cho phép {limits['max_daily_chat']} câu hỏi/ngày. "
                "Nâng cấp lên Pro để mở rộng giới hạn."
            )
    if limits.get("max_monthly_chat") is not None:
        monthly_count = count_monthly_chats(current_user.id, db)
        if monthly_count >= limits["max_monthly_chat"]:
            raise HTTPException(
                429,
                f"❌ Gói {limits['label']} chỉ cho phép {limits['max_monthly_chat']} câu hỏi/tháng. "
                "Vui lòng nâng cấp gói cước để tiếp tục sử dụng."
            )


def _save_chat_history(db: Session, user_id: str, query: str, answer: str, document_ids: list) -> None:
    """Best-effort lưu chat vào bảng chat_history. Không raise nếu fail."""
    try:
        db.execute(
            text("""
                INSERT INTO chat_history (id, user_id, query, answer, document_ids)
                VALUES (:id, :uid, :query, :answer, cast(:docs AS jsonb))
            """),
            {
                "id": str(uuid.uuid4()),
                "uid": user_id,
                "query": query[:4000],
                "answer": answer[:5000],
                "docs": json.dumps(document_ids or []),
            },
        )
        db.commit()
    except Exception as e:
        logger.warning("Failed to auto-save chat_history for user %s: %s", user_id, e)
        try:
            db.rollback()
        except Exception:
            pass

router = APIRouter()

MAX_ANALYSIS_FILES = 20
MAX_ANALYSIS_URLS = 6
_URL_PATTERN = re.compile(r"https?://[^\s<>\]\[(){}\"']+", re.IGNORECASE)


def _urls_in_query(query: str) -> list[str]:
    found = []
    for raw in _URL_PATTERN.findall(query or ""):
        candidate = raw.rstrip(".,;:!?。！，；：")
        if candidate and candidate not in found:
            found.append(candidate)
    if len(found) > MAX_ANALYSIS_URLS:
        raise HTTPException(400, f"Tối đa {MAX_ANALYSIS_URLS} URL trong một lượt phân tích.")
    return found


def _source_kind(url: str, title: str = "", content_type: str = "") -> str:
    host = (urlparse(url).hostname or "").lower()
    if any(marker in host for marker in ("arxiv.org", "biorxiv.org", "medrxiv.org", "psyarxiv.com")):
        return "preprint"
    if host.endswith((".gov", ".edu")) or any(token in host for token in ("who.int", "nih.gov", "apa.org", "institution")):
        return "institutional or organization source"
    if "doi.org/" in url.lower() or any(token in host for token in ("springer.com", "sciencedirect.com", "wiley.com", "sagepub.com", "tandfonline.com", "frontiersin.org", "nature.com", "jamanetwork.com", "apa.org")):
        return "scholarly article or publisher page"
    if content_type == "application/pdf":
        return "PDF document (publication type unverified)"
    return "website (publication type unverified)"


def _fetch_url_sources(query: str, explicit_urls: list[str] | None = None, search_if_empty: bool = False) -> tuple[list[dict], list[str]]:
    """Get readable public web/PDF sources without forwarding browser cookies."""
    urls = list(explicit_urls or [])
    search_results: list[dict] = []
    errors: list[str] = []
    if not urls and search_if_empty:
        try:
            search_results = duckduckgo_search(query, max_results=3)
            urls = [str(item.get("href") or item.get("url") or "") for item in search_results]
            urls = [url for url in urls if url.startswith(("https://", "http://"))][:5]
        except Exception as exc:
            logger.warning("Public web search failed: %s", exc)

    results: list[dict] = []
    for index, url in enumerate(urls[:MAX_ANALYSIS_URLS]):
        try:
            fetched = fetch_public_source(url)
            if fetched.get("content_type") == "application/pdf":
                name = fetched["url"].split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1] or f"source_{index + 1}.pdf"
                if not name.lower().endswith(".pdf"):
                    name += ".pdf"
                visual_request = bool(re.search(
                    r"\b(chart|graph|plot|figure|visual|table|diagram|biểu đồ|đồ thị|hình|sơ đồ|bảng số liệu|ước lượng số liệu)\b",
                    query,
                    re.IGNORECASE,
                ))
                page_chunks = parse_file_chunks(
                    fetched["data"], name, analyze_visuals=visual_request, max_visual_pages=3
                )
                page_chunks = _select_inline_chunks(page_chunks, query, per_document=6, max_total=6)
                body = "\n\n".join(
                    f"[PDF page {chunk.get('page_number', '?')}]\n{chunk.get('content', '')}"
                    for chunk in page_chunks
                )
                if not body.strip():
                    raise ValueError("Không trích xuất được nội dung PDF.")
                results.append({
                    "title": name,
                    "url": fetched["url"],
                    "body": body[:12000],
                    "source_type": _source_kind(fetched["url"], name, "application/pdf"),
                })
            else:
                results.append({
                    "title": fetched.get("title") or fetched["url"],
                    "url": fetched["url"],
                    "body": fetched.get("content", ""),
                    "source_type": _source_kind(fetched["url"], fetched.get("title", ""), "text/html"),
                })
        except Exception as exc:
            logger.info("Could not fetch public source %s: %s", url, exc)
            errors.append(f"{url}: {str(exc)}")
            # Search snippets remain attributable, but are explicitly marked
            # as snippets so generation cannot present them as full-text review.
            match = next((item for item in search_results if (item.get("href") or item.get("url")) == url), None)
            if match and (match.get("body") or "").strip():
                results.append({
                    "title": match.get("title") or url,
                    "url": url,
                    "body": f"[SEARCH SNIPPET ONLY — full page could not be accessed]\n{match.get('body', '')}",
                    "source_type": f"{_source_kind(url, match.get('title', ''))}; search snippet only (full text unavailable)",
                })
            elif explicit_urls:
                results.append({
                    "title": url,
                    "url": url,
                    "body": f"[SOURCE NOT ACCESSED — do not use as evidence] {str(exc)[:500]}",
                    "source_type": "not accessible; no source content retrieved",
                })
    return results, errors


def _cap_context_documents(chunks: list[dict], max_documents: int = MAX_ANALYSIS_FILES) -> list[dict]:
    """Keep retrieved context within the user-facing six-source analysis cap."""
    allowed: list[str] = []
    selected: list[dict] = []
    for chunk in chunks:
        document_id = str(chunk.get("document_id") or "")
        # Inline files share one synthetic id; their filenames are the identity.
        key = str(chunk.get("doc_filename") or chunk.get("filename") or document_id) if document_id == "inline_file" else document_id
        if not key:
            key = str(chunk.get("doc_filename") or chunk.get("filename") or "unknown")
        if key not in allowed:
            if len(allowed) >= max(0, max_documents):
                continue
            allowed.append(key)
        selected.append(chunk)
    return selected


def _select_inline_chunks(chunks: list[dict], query: str, per_document: int = 4, max_total: int = 24) -> list[dict]:
    """Choose query-relevant pages from temporary files while preserving each source."""
    stop = {"the", "and", "for", "with", "from", "what", "which", "that", "this", "these", "those", "about", "into", "của", "trong", "với", "cho", "những", "các", "nào", "được", "là", "và", "theo", "giữa", "về", "như", "hãy", "phân", "tích", "so", "sánh", "bài", "nghiên", "cứu"}
    terms = {word.casefold() for word in re.findall(r"[\wÀ-ỹ]{3,}", query) if word.casefold() not in stop}
    source_chunks: dict[str, list[dict]] = {}
    for chunk in chunks:
        source = str(chunk.get("doc_filename") or chunk.get("filename") or chunk.get("document_id") or "source")
        source_chunks.setdefault(source, []).append(chunk)

    ranked: dict[str, list[dict]] = {}
    for source, items in source_chunks.items():
        def score(item: dict) -> tuple[int, int]:
            content = str(item.get("content", "")).casefold()
            lexical = sum(1 for term in terms if term in content)
            findings_bonus = 2 if re.search(r"\b(results?|findings?|outcomes?|discussion|conclusion|kết quả|phát hiện|thảo luận|kết luận)\b", content) else 0
            return lexical + findings_bonus, -int(item.get("page_number") or 1)
        ranked[source] = sorted(items, key=score, reverse=True)[:per_document]

    # Round-robin across files keeps comparisons from being dominated by one long PDF.
    selected: list[dict] = []
    for rank in range(per_document):
        for source_items in ranked.values():
            if rank < len(source_items) and len(selected) < max_total:
                item = dict(source_items[rank])
                item["content"] = str(item.get("content", ""))[:5000]
                selected.append(item)
    return selected


class ChatRequest(BaseModel):
    query: str
    document_ids: Optional[list[str]] = []
    mode: Optional[str] = "single"
    force_web_search: Optional[bool] = False  # nếu True: bỏ qua RAG, dùng web search luôn


class AnswerRequest(BaseModel):
    query: str
    document_ids: Optional[list[str]] = []


class ExportRequest(BaseModel):
    messages: list[dict]
    title: str = "Báo cáo Hỏi Đáp Tâm Lý Học"


class DomainCheckRequest(BaseModel):
    query: str


class GeneralSearchRequest(BaseModel):
    query: str


# ── Main chat (RAG + psychology) ───────────────────────────────────────────────

@router.post("")
def chat(request: ChatRequest, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    if not request.query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    query_urls = _urls_in_query(request.query)
    search_doc_ids = _sanitize_uuid_list(request.document_ids) if request.document_ids else None
    if search_doc_ids and len(search_doc_ids) + len(query_urls) > MAX_ANALYSIS_FILES:
        raise HTTPException(400, f"Tổng số tài liệu đã chọn và URL không được vượt quá {MAX_ANALYSIS_FILES}.")
    search_doc_ids = readable_document_ids(db, current_user, search_doc_ids)
    from app.models.document import Document
    ready_count = db.query(Document.id).filter(Document.status == "ready").count()
    if search_doc_ids is None:
        # When no indexed library exists, the request can still use public web.
        pass

    # Bóc tách câu hỏi thực tế của người dùng (loại bỏ chỉ dẫn hệ thống)
    clean_q = re.sub(r'^\[he\s+thong:[^\]]+\]', '', request.query, flags=re.IGNORECASE).strip()
    clean_q = re.sub(r'^\[system:[^\]]+\]', '', clean_q, flags=re.IGNORECASE).strip()
    clean_q = _URL_PATTERN.sub("", clean_q).strip() or request.query.strip()
    comparison_route = classify_and_decompose_query(clean_q)
    is_multi_target = comparison_route["num_targets"] > 1

    # Phát hiện ngôn ngữ thực sự của câu hỏi (tiếng Anh hay tiếng Việt)
    lang = detect_language(clean_q)

    # Chuẩn hóa chỉ dẫn hệ thống theo đúng ngôn ngữ của câu hỏi và giới hạn đúng trọng tâm
    sent_query = _normalize_mode_instruction(request.query, lang)

    # 1. Kiểm tra Q&A định nghĩa sẵn trước
    predefined = get_predefined_answer(clean_q, lang, ready_count=ready_count) if not query_urls else None
    if predefined:
        def stream_predefined():
            yield predefined
            if current_user is not None:
                _save_chat_history(db, str(current_user.id), clean_q, predefined, request.document_ids)
        return StreamingResponse(
            stream_predefined(),
            media_type="text/plain; charset=utf-8"
        )

    # 2. Kiểm tra giới hạn gói cước (ngày & tháng)
    _enforce_chat_limits(current_user, db)

    # Prefer the user's chosen/indexed corpus for comparative questions. Search
    # public web only when requested, when URLs were pasted, or when no library
    # corpus is available; comparison intent alone must not silently add sources.
    explicit_web_request = bool(re.search(
        r"\b(search|find sources|look up|web search|on the web|online)\b|tìm (?:trên )?web|tìm nguồn công khai|tìm tài liệu công khai|tra cứu web",
        clean_q,
        re.IGNORECASE,
    ))
    web_requested = bool(request.force_web_search or query_urls or ready_count == 0 or explicit_web_request)
    web_sources, web_errors = _fetch_url_sources(
        clean_q,
        explicit_urls=query_urls,
        search_if_empty=web_requested and not query_urls,
    )
    # Explicit URLs are the source boundary unless the user also selected
    # indexed document IDs. Otherwise continue using the local library.
    retrieve_local = not query_urls or bool(search_doc_ids)

    # ── Phase A: thử L1 memory TRƯỚC (khi có danh sách tài liệu mục tiêu <= 6) ──
    used_memory = False
    context_chunks: list[dict] = []
    effective_mem_ids = search_doc_ids
    if retrieve_local and not request.force_web_search and not is_multi_target and not effective_mem_ids:
        try:
            scoped_ids = _resolve_explicit_title_scope(clean_q, db)
            if scoped_ids and len(scoped_ids) <= MAX_ANALYSIS_FILES:
                effective_mem_ids = scoped_ids
            elif 0 < ready_count <= MAX_ANALYSIS_FILES:
                ready_rows = db.query(Document.id).filter(Document.status == "ready").limit(MAX_ANALYSIS_FILES).all()
                effective_mem_ids = [str(r.id) for r in ready_rows]
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

    if (retrieve_local and not request.force_web_search and not is_multi_target
            and effective_mem_ids and len(effective_mem_ids) <= MAX_ANALYSIS_FILES):
        try:
            # Dùng clean_q để tìm kiếm L1 memory tránh bị nhiễu bởi system prompt
            memory_chunks = retrieve_via_memory(clean_q, effective_mem_ids, db)
            if memory_chunks:
                # Enrich doc_title/authors từ bảng documents
                doc_meta_rows = db.execute(
                    text("SELECT id, title, authors, filename FROM documents WHERE id = ANY(CAST(:ids AS uuid[]))"),
                    {"ids": effective_mem_ids},
                ).fetchall()
                meta_map = {str(r.id): r for r in doc_meta_rows}
                for c in memory_chunks:
                    m = meta_map.get(c["document_id"])
                    if m:
                        c["doc_title"] = m.title or ""
                        c["doc_authors"] = m.authors or ""
                        c["doc_filename"] = m.filename or ""
                context_chunks = memory_chunks
                used_memory = True
                logger.info("chat: L1 memory hit, %d chunks (skipped L2 RAG)", len(memory_chunks))
        except Exception as mem_err:
            logger.warning("L1 memory lookup failed: %s", mem_err)
            try:
                db.rollback()  # Bảo vệ giao dịch tránh bị abort
            except Exception:
                pass

    # ── Phase B: L2 RAG chỉ chạy khi L1 không hit ──
    if retrieve_local and not context_chunks and not request.force_web_search:
        try:
            # Dùng clean_q để retrieve L2 RAG chính xác hơn
            # Tối ưu top_k=6 cho câu hỏi đơn mục tiêu (10 cho so sánh đa bài) để giảm 50% thời gian LLM đọc ngữ cảnh
            eff_top_k = 6
            context_chunks = retrieve(clean_q, search_doc_ids, db, top_k=eff_top_k)
        except Exception as ret_err:
            logger.warning("L2 retrieve failed: %s", ret_err)
            try:
                db.rollback()
            except Exception:
                pass

    context_chunks = _cap_context_documents(context_chunks, MAX_ANALYSIS_FILES - len(web_sources))
    comparison_coverage = None
    if is_multi_target and retrieve_local and not web_sources and not request.force_web_search:
        comparison_coverage = assess_target_coverage(comparison_route["sub_queries"], context_chunks, clean_q)
        if comparison_coverage["status"] == "none" and not context_chunks:
            message = ("No relevant evidence was found for any requested study." if lang == "en" else
                       "Không tìm thấy bằng chứng liên quan cho các nghiên cứu được yêu cầu.")
            return StreamingResponse(iter([message]), media_type="text/plain; charset=utf-8",
                                     headers={"X-No-Context": "true", "Access-Control-Expose-Headers": "X-No-Context"})

    # Nếu RAG hoàn toàn không tìm được context → Trả về ngay "Không có thông tin..." hoặc tiếng Anh tương ứng
    usable_web_sources = [
        source for source in web_sources
        if "no source content retrieved" not in str(source.get("source_type", ""))
    ]
    if not context_chunks and not usable_web_sources:
        if query_urls and web_errors:
            explanation = "Không đọc được nội dung từ các URL đã gửi. Hãy kiểm tra liên kết hoặc tải PDF mà bạn có quyền sử dụng lên.\n" + "\n".join(web_errors)
            return StreamingResponse(iter([explanation]), media_type="text/plain; charset=utf-8")
        if web_requested:
            message = "Không truy cập được nguồn công khai phù hợp ở lượt này. Hãy thử URL khác hoặc tải tài liệu bạn có quyền sử dụng lên." if lang != "en" else "No suitable public source could be accessed for this request. Try another URL or upload a document you are authorized to use."
            return StreamingResponse(iter([message]), media_type="text/plain; charset=utf-8")
        no_ctx_msg_en = "This information is not available in the uploaded documents."
        no_ctx_msg = ("This information is not available in the uploaded documents." if lang == "en" else "Không có thông tin về nội dung này trong các tài liệu đã tải lên.")
        def no_context_stream():
            yield no_ctx_msg
            if current_user is not None:
                _save_chat_history(db, str(current_user.id), clean_q, no_ctx_msg, request.document_ids)
        return StreamingResponse(
            no_context_stream(),
            media_type="text/plain; charset=utf-8",
            headers={"X-No-Context": "true", "Access-Control-Expose-Headers": "X-No-Context"},
        )

    import os as _os
    evidence_matrix = None
    _enable_verifier = _os.getenv("ENABLE_PRE_VERIFIER", "0") == "1"
    if _enable_verifier and context_chunks and not web_sources and (is_multi_target or needs_verification(context_chunks)):
        targets = comparison_route["sub_queries"] if is_multi_target else [clean_q]
        evidence_matrix, context_chunks = assess_and_repair(clean_q, targets, context_chunks, search_doc_ids, db)
        if is_multi_target:
            comparison_coverage = assess_target_coverage(targets, context_chunks, clean_q)
        logger.info("evidence_policy action=%s supported=%s total=%s verification_ms=%s repair_targets=%s",
                    evidence_matrix["action"], evidence_matrix.get("supported_cells"),
                    evidence_matrix.get("total_cells"), evidence_matrix.get("verification_ms"),
                    evidence_matrix.get("repair_targets", 0))
        if evidence_matrix["action"] == "unavailable":
            logger.warning("Local evidence verifier (Ollama) unavailable; falling back to main LLM generation check.")
            evidence_matrix = None
        elif evidence_matrix["action"] == "refuse":
            message = ("The retrieved passages do not provide sufficient evidence to answer this question. "
                       "This does not establish that the information is absent from the full papers."
                       if lang == "en" else "Các đoạn truy xuất chưa cung cấp đủ bằng chứng để trả lời câu hỏi này. "
                       "Điều này không có nghĩa là thông tin không tồn tại trong toàn bộ tài liệu.")
            return StreamingResponse(iter([message]), media_type="text/plain; charset=utf-8",
                headers={"X-No-Context": "true", "X-Evidence-Decision": "refuse",
                         "Access-Control-Expose-Headers": "X-No-Context,X-Evidence-Decision"})
        elif is_multi_target and evidence_matrix["action"] == "partial":
            # A free-form generator can turn partial evidence into uncited claims.
            # Render only verifier-approved literal excerpts for this case.
            answer = render_verified_matrix(evidence_matrix, lang)
            if current_user is not None:
                _save_chat_history(db, str(current_user.id), request.query, answer, request.document_ids)
            return StreamingResponse(iter([answer]), media_type="text/plain; charset=utf-8",
                headers={"X-No-Context": "false", "X-Evidence-Decision": "partial",
                         "X-Context-Pages": ",".join(str(c["page_number"]) for c in context_chunks),
                         "X-Document-IDs": ",".join(c["document_id"] for c in context_chunks),
                         "Access-Control-Expose-Headers": "X-No-Context,X-Evidence-Decision,X-Context-Pages,X-Document-IDs"})

    config_error = llm_configuration_error()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    # Tìm các hình ảnh / sơ đồ / bảng biểu liên quan đến các chunks được trích xuất
    available_figures = []
    try:
        from app.services.figure_extractor import get_figures_for_chunks
        available_figures = get_figures_for_chunks(context_chunks, db)
    except Exception as fig_err:
        logger.warning("Không thể lấy figures cho context_chunks: %s", fig_err)

    answer_query = _URL_PATTERN.sub("", sent_query).strip() or clean_q
    raw_tel_check = (context_chunks[0].get("_telemetry") if context_chunks else None) or {}
    if raw_tel_check.get("crag_passed") is False:
        answer_query += (
            "\n[CRAG Gate Warning: Retrieval confidence is below the verification threshold. "
            "Only report claims directly and explicitly stated in the retrieved passages, and state clearly if specific aspects are not supported.]"
            if lang == "en"
            else "\n[Cảnh báo Cổng kiểm định CRAG: Độ tin cậy truy hồi dưới ngưỡng chuẩn. "
            "Chỉ trình bày các dữ kiện có mặt trực tiếp trong đoạn trích và nêu rõ nếu khía cạnh được hỏi chưa có bằng chứng trực tiếp.]"
        )
    if evidence_matrix:
        answer_query += policy_prompt(evidence_matrix)
    if comparison_coverage:
        answer_query += ("\n[For every requested study and criterion, verify the reported fact in its own passage before comparing. "
                         "A relevant passage or a matching keyword alone is not factual support. Cite the exact source and page for each claim.]") if lang == "en" else (
                         "\n[Chỉ dẫn đối chiếu đa tài liệu: BẮT BUỘC khai thác và trình bày ĐẦY ĐỦ mọi dữ kiện liên quan đến từng đối tượng có trong từng đoạn trích (bao gồm công cụ/thang đo đánh giá, hệ thống phân loại DSM/ICD, đặc điểm đồng mắc, hoặc đáp ứng điều trị/thuốc...) kèm nhãn [ten_file.pdf - Trang X] ở cuối mỗi câu; "
                         "chỉ sau khi đã nêu hết các dữ kiện có mặt trong tài liệu mới ghi chú ngắn gọn những khía cạnh chưa được đề cập chi tiết.]")
    if comparison_coverage and comparison_coverage["status"] == "partial_candidates":
        missing = [row["target"] for row in comparison_coverage["targets"] if row["status"] == "missing"]
        answer_query += ("\n[Evidence coverage: no sufficiently relevant passage was retrieved for "
                         + "; ".join(missing) + ". Answer only supported parts; do not claim a complete comparison.]"
                         if lang == "en" else
                         "\n[Độ phủ bằng chứng: chưa truy hồi được đoạn đủ liên quan cho "
                         + "; ".join(missing) + ". Chỉ trả lời phần có nguồn và không kết luận đã so sánh đầy đủ.]")
    raw_stream = (
        generate_stream_web_search(answer_query, web_sources, context_chunks=context_chunks, lang=lang)
        if web_sources else generate_stream(answer_query, context_chunks, lang, available_figures)
    )

    def stream_with_saving():
        collected: list[str] = []; stream_unlocked = bool(web_sources); speculative_buffer: list[str] = []
        no_ctx_marker = "__NO_CONTEXT__"
        pending = ""
        for chunk in raw_stream:
            pending += chunk
            while True:
                if "\n" in pending:
                    line, pending = pending.split("\n", 1)
                    sep_char = "\n"
                elif not pending.lstrip().startswith("|") and (m_sent := re.search(r"\]\s*[.;]\s+", pending)):
                    cut_idx = m_sent.end()
                    line, pending = pending[:cut_idx], pending[cut_idx:]
                    sep_char = ""
                else:
                    break
                safe_line = _verify_numeric_citations(_strip_absence_sentence_citations(_repair_citation_filenames(_normalize_stream_citations(qualify_missing_evidence(line + sep_char)), context_chunks)), context_chunks)
                if re.search(r"(?i)(?:tài liệu không đề cập trực tiếp|dựa vào kiến thức chung)", safe_line) and not collected and not bool(_build_references_block(safe_line, context_chunks, lang)): safe_line = no_ctx_marker
                if not stream_unlocked and no_ctx_marker not in safe_line and not any(no_ctx_marker in c for c in collected) and bool(_build_references_block(safe_line, context_chunks, lang)): stream_unlocked = True; yield "".join(speculative_buffer); speculative_buffer.clear()
                if stream_unlocked and no_ctx_marker not in safe_line and not any(no_ctx_marker in c for c in collected) and not re.search(r"(?i)(?:dựa\s+(?:trên|vào)\s+kiến\s+thức\s+chung|kiến\s+thức\s+bên\s+ngoài)", safe_line):
                    yield safe_line
                elif not stream_unlocked: speculative_buffer.append(safe_line)
                collected.append(safe_line)
        if pending:
            safe_line = _verify_numeric_citations(_strip_absence_sentence_citations(_repair_citation_filenames(_normalize_stream_citations(qualify_missing_evidence(pending)), context_chunks)), context_chunks)
            if not stream_unlocked and no_ctx_marker not in safe_line and not any(no_ctx_marker in c for c in collected) and bool(_build_references_block(safe_line, context_chunks, lang)): stream_unlocked = True; yield "".join(speculative_buffer); speculative_buffer.clear()
            if stream_unlocked and no_ctx_marker not in safe_line and not any(no_ctx_marker in c for c in collected) and not re.search(r"(?i)(?:dựa\s+(?:trên|vào)\s+kiến\s+thức\s+chung|kiến\s+thức\s+bên\s+ngoài)", safe_line):
                yield safe_line
            collected.append(safe_line)
        full_answer = _clean_cjk_leakage(re.split(r'\n+[^\n]*(?:dựa\s+(?:trên|vào)\s+kiến\s+thức\s+chung|kiến\s+thức\s+bên\s+ngoài)[^\n]*', "".join(collected), maxsplit=1, flags=re.I)[0]).strip() + "\n"

        # Nếu LLM trả về __NO_CONTEXT__ (do chunks không chứa thông tin thực sự)
        if no_ctx_marker in full_answer:
            _unused_en = "No sufficient evidence was found in the retrieved passages."
            final_answer = ("This information is not available in the uploaded documents." if lang == "en" else "Không có thông tin về nội dung này trong các tài liệu đã tải lên.")
            yield final_answer
            if current_user is not None:
                _save_chat_history(db, str(current_user.id), request.query, final_answer, request.document_ids)
            return

        references_block = _build_references_block(full_answer, context_chunks, lang)
        if not web_sources and not references_block:
            final_answer = ("This information is not available in the uploaded documents." if lang == "en" else "Không có thông tin về nội dung này trong các tài liệu đã tải lên.")
            yield final_answer
            if current_user is not None and hasattr(locals().get("request", None), "query"): _save_chat_history(db, str(current_user.id), request.query, final_answer, request.document_ids)
            return
        if not web_sources and not stream_unlocked:
            yield full_answer
        final_answer = full_answer + references_block

        if references_block:
            yield references_block

        if current_user is not None:
            _save_chat_history(db, str(current_user.id), request.query, final_answer, request.document_ids)

    # Build Pipeline Telemetry & Clinical Authority / APA 7th Citation Metadata Header
    import base64
    telemetry_header_b64 = ""
    try:
        from app.services.authority_scorer import score_document_authority
        from app.services.scientific_appraiser import (
            evaluate_cebm_evidence_level,
            generate_apa7_citation,
            generate_bibtex_entry,
        )

        raw_telemetry = (context_chunks[0].get("_telemetry") if context_chunks else None)
        if not raw_telemetry:
            # Đường trả lời không có telemetry đo được (vd. bộ nhớ L1): KHÔNG điền số giả.
            # Chỉ tính những gì tính được từ chính các đoạn ngữ cảnh; phần không đo được để 0
            # và đánh dấu telemetry_source để giao diện/nhật ký biết đây là giá trị ước lượng.
            from app.services.retriever import evaluate_retrieval_confidence, _CRAG_THRESHOLD
            _crag_fb = evaluate_retrieval_confidence(clean_q, context_chunks) if context_chunks else {"confidence": 0.0}
            _rrfs = sorted((float(c.get("rrf_score") or 0.0) for c in context_chunks), reverse=True)
            raw_telemetry = {
                "telemetry_source": "fallback_estimated",
                "memory_tier": "L1_FAST_MEMORY" if used_memory else "L2_DEEP_HYBRID",
                "route": "single_focus",
                "num_targets": 1,
                "sub_queries": [clean_q],
                "quota_per_target": len(context_chunks),
                "vector_hits": 0,
                "fts_hits": 0,
                "rrf_k": 60,
                "top_rrf_score": round(_rrfs[0], 5) if _rrfs else 0.0,
                "dominance_ratio": round(_rrfs[0] / max(_rrfs[1], 1e-6), 3) if len(_rrfs) >= 2 and _rrfs[1] > 0 else 0.0,
                "dcsr_confidence": round(float(context_chunks[0].get("dcsr_confidence") or 0.0), 4) if context_chunks else 0.0,
                "dcsr_fast_skip": bool(context_chunks[0].get("dcsr_skip", False)) if context_chunks else False,
                "crag_score": float(_crag_fb.get("confidence", 0.0)),
                "crag_threshold": _CRAG_THRESHOLD,
                "crag_passed": float(_crag_fb.get("confidence", 0.0)) >= _CRAG_THRESHOLD,
                "latency_ms": 0.0,
                "chunks_count": len(context_chunks),
                "unique_docs": len({c.get("document_id") for c in context_chunks if c.get("document_id")}),
            }

        unique_doc_ids = _sanitize_uuid_list(
            list({str(c.get("document_id")) for c in context_chunks if c.get("document_id")})
        )
        doc_year_map: dict[str, int] = {}
        if unique_doc_ids:
            try:
                y_rows = db.execute(
                    text("SELECT id, year FROM documents WHERE id = ANY(CAST(:ids AS uuid[]))"),
                    {"ids": unique_doc_ids},
                ).fetchall()
                doc_year_map = {str(r.id): r.year for r in y_rows}
            except Exception:
                try:
                    db.rollback()
                except Exception:
                    pass

        grouped_by_doc: dict[str, list[dict]] = {}
        for c in context_chunks:
            did = str(c.get("document_id") or "")
            if did:
                grouped_by_doc.setdefault(did, []).append(c)

        sources_meta: list[dict] = []
        for did, d_chunks in grouped_by_doc.items():
            c0 = d_chunks[0]
            fname = c0.get("doc_filename") or c0.get("doc_title") or "Document.pdf"
            title = c0.get("doc_title") or fname
            authors = c0.get("doc_authors") or ""
            year = doc_year_map.get(did)
            pages = sorted({int(m.group(1)) if (m := re.search(r'(\d+)', str(ch.get("page_number") or "1"))) else 1 for ch in d_chunks})
            sample_txt = " ".join((ch.get("content") or "")[:400] for ch in d_chunks[:3])
            doc_dict = {
                "id": did,
                "filename": fname,
                "title": title,
                "authors": authors,
                "year": year,
            }
            _, tier_name, tier_label = score_document_authority(doc_dict, sample_txt)
            cebm_info = evaluate_cebm_evidence_level([doc_dict], d_chunks)
            apa7_str = generate_apa7_citation(doc_dict)
            if pages:
                page_suffix = f" (p. {pages[0]})" if len(pages) == 1 else f" (pp. {', '.join(map(str, pages[:4]))})"
                apa7_str = apa7_str.rstrip(".") + f"{page_suffix}."
            bibtex_str = generate_bibtex_entry(doc_dict)
            page_excerpts: dict[str, str] = {}
            for ch in d_chunks:
                p_key = str(int(m.group(1)) if (m := re.search(r'(\d+)', str(ch.get("page_number") or "1"))) else str(ch.get("page_number") or "1"))
                if ch.get("content") and len(page_excerpts.get(p_key, "")) < 1500:
                    page_excerpts[p_key] = ((page_excerpts.get(p_key, "") + "\n" + re.sub(r'^\[Trang\s+\d+\]\s*', '', str(ch.get("content") or "")).strip()).strip())[:3500]
            sources_meta.append({
                "document_id": did,
                "filename": fname,
                "title": title,
                "authors": authors,
                "year": year,
                "pages": pages[:6],
                "page_excerpts": page_excerpts,
                "authority_tier": tier_name,
                "authority_label": tier_label,
                "cebm_level": cebm_info.get("level", "2b"),
                "cebm_label": cebm_info.get("level_label", "Cấp 2B"),
                "study_design": cebm_info.get("study_design", ""),
                "apa7": apa7_str,
                "bibtex": bibtex_str,
            })

        sub_queries = raw_telemetry.get("sub_queries") or [clean_q]
        is_multi_target = len(sub_queries) > 1
        evidence_targets = []
        for sub_query in sub_queries:
            if is_multi_target:
                target_chunks = [
                    c for c in context_chunks
                    if str(c.get("sub_query_target") or "").strip().casefold()
                    == str(sub_query).strip().casefold()
                ]
            else:
                target_chunks = context_chunks
            evidence_targets.append({
                "sub_query": sub_query,
                "retrieved_count": len(target_chunks),
                "has_retrieved_evidence": bool(target_chunks),
                "coverage_status": next((row["status"] for row in (comparison_coverage or {}).get("targets", [])
                                         if row["target"] == sub_query), "unverified"),
                "evidence": [
                    {
                        "document_id": str(c.get("document_id") or ""),
                        "filename": c.get("doc_filename") or c.get("doc_title") or "Tài liệu",
                        "title": c.get("doc_title") or c.get("doc_filename") or "Tài liệu",
                        "page": int(m.group(1)) if (m := re.search(r'(\d+)', str(c.get("page_number") or "1"))) else 1,
                        "excerpt": (c.get("content") or "")[:900],
                    }
                    for c in target_chunks[:4]
                ],
            })

        payload_json = json.dumps(
            {"telemetry": raw_telemetry, "sources": sources_meta,
             "evidence_targets": evidence_targets,
             "comparison_coverage": comparison_coverage,
             "cross_study_concordance": compute_cross_study_concordance(context_chunks),
             "metric_harmonization": harmonize_cross_study_metrics(context_chunks),
             "evidence_matrix": ({**evidence_matrix, "cells": [
                 {**cell, "evidence": [{**e, "quote": e["quote"][:240]} for e in cell["evidence"]]}
                 for cell in evidence_matrix["cells"]]} if evidence_matrix else None)},
            ensure_ascii=False,
        )
        telemetry_header_b64 = base64.b64encode(payload_json.encode("utf-8")).decode("ascii")
    except Exception as tel_err:
        logger.warning("Failed to build telemetry header: %s", tel_err)

    # The experimental pipeline telemetry describes indexed RAG stages and is
    # not meaningful for URL/temporary-file analysis.
    if web_sources:
        telemetry_header_b64 = ""

    return StreamingResponse(
        stream_with_saving(),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Context-Pages": ",".join(str(c["page_number"]) for c in context_chunks),
            "X-Document-IDs": ",".join(c["document_id"] for c in context_chunks),
            "X-No-Context": "false",
            "X-Evidence-Decision": evidence_matrix["action"] if evidence_matrix else "generation_check",
            "X-Memory-Hit": "true" if used_memory else "false",
            "X-Pipeline-Telemetry": telemetry_header_b64,
            "Access-Control-Expose-Headers": "X-Context-Pages,X-Document-IDs,X-No-Context,X-Memory-Hit,X-Pipeline-Telemetry,X-Evidence-Decision",
        }
    )



# ── Domain classification ──────────────────────────────────────────────────────

@router.post("/detect-domain")
def detect_domain(request: DomainCheckRequest):
    """Phân loại câu hỏi: 'psychology' hoặc 'general'."""
    if not request.query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    domain = classify_query_domain(request.query)
    return {"domain": domain, "query": request.query}


# ── General web search fallback ────────────────────────────────────────────────

@router.post("/general")
def chat_general(
    request: GeneralSearchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Trả lời câu hỏi bằng kiến thức của AI, không kết nối internet."""
    if not request.query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")

    _enforce_chat_limits(current_user, db)

    config_error = llm_configuration_error()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    def stream_direct_saving():
        collected = []
        for chunk in generate_stream_direct(request.query):
            collected.append(chunk)
            yield chunk
        if current_user is not None:
            full_answer = _clean_cjk_leakage(re.split(r'\n+[^\n]*(?:dựa\s+(?:trên|vào)\s+kiến\s+thức\s+chung|kiến\s+thức\s+bên\s+ngoài)[^\n]*', "".join(collected), maxsplit=1, flags=re.I)[0]).strip() + "\n"
            _save_chat_history(db, str(current_user.id), request.query, full_answer, [])

    return StreamingResponse(
        stream_direct_saving(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Access-Control-Expose-Headers": "X-Context-Pages,X-Document-IDs,X-Doc-Authors",
        }
    )


# ── Non-streaming answer ───────────────────────────────────────────────────────

@router.post("/answer")
def chat_answer(request: AnswerRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Non-streaming: trả về câu trả lời + context chunks (dùng cho RAGAS)."""
    if not request.query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    request.document_ids = readable_document_ids(db, current_user, request.document_ids or None)
    if not request.document_ids:
        raise HTTPException(400, "Hệ thống chưa có tài liệu nào sẵn sàng. Vui lòng tải tài liệu lên.")

    context_chunks = retrieve(request.query, request.document_ids, db)
    if not context_chunks:
        return {
            "answer": "Chưa tìm thấy thông tin liên quan trong các đoạn được truy xuất từ tài liệu đã chọn.",
            "contexts": [],
        }

    available_figures = []
    try:
        from app.services.figure_extractor import get_figures_for_chunks
        available_figures = get_figures_for_chunks(context_chunks, db)
    except Exception:
        pass

    import os as _os
    route = classify_and_decompose_query(request.query)
    evidence_matrix = None
    answer_query = request.query
    _enable_verifier = _os.getenv("ENABLE_PRE_VERIFIER", "0") == "1"
    if _enable_verifier and (route["num_targets"] > 1 or needs_verification(context_chunks)):
        evidence_matrix, context_chunks = assess_and_repair(
            request.query, route["sub_queries"], context_chunks, request.document_ids, db)
        if evidence_matrix["action"] == "unavailable":
            logger.warning("Local evidence verifier (Ollama) unavailable in chat_answer; skipping strict matrix check.")
            evidence_matrix = None
        elif evidence_matrix["action"] == "refuse":
            return {"answer": "Chưa tìm thấy đủ bằng chứng trong các đoạn truy xuất.",
                    "contexts": [], "evidence_matrix": evidence_matrix}
        else:
            answer_query += policy_prompt(evidence_matrix)
    answer = generate_answer(answer_query, context_chunks, available_figures=available_figures)
    return {
        "answer": answer,
        "evidence_matrix": evidence_matrix,
        "contexts": [
            {
                "content": c["content"],
                "page_number": c["page_number"],
                "document_id": c["document_id"],
                "doc_title": c.get("doc_title", ""),
                "doc_authors": c.get("doc_authors", ""),
                "rrf_score": c.get("rrf_score", 0),
            }
            for c in context_chunks
        ],
    }


# ── Export ─────────────────────────────────────────────────────────────────────

@router.post("/export")
def export_chat(req: ExportRequest):
    from app.utils.export import export_chat_to_docx
    if not req.messages:
        raise HTTPException(400, "Không có tin nhắn để xuất")
    docx_bytes = export_chat_to_docx(req.messages, req.title)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="chat_{datetime.now().strftime("%Y%m%d")}.docx"'}
    )


# ── File chat (inline upload) ─────────────────────────────────────────────────

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB per file
SUPPORTED_TYPES = {"pdf", "docx", "doc", "xlsx", "xls", "jpg", "jpeg", "png", "gif", "bmp", "webp"}


@router.post("/file-chat")
def chat_with_files(
    query: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    document_ids: str = Form("[]"),  # JSON array string
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Chat with inline uploaded files (PDF, DOCX, XLSX, images).
    Files are parsed on-the-fly and their text is injected as context for the LLM.
    Nothing is stored permanently.
    """
    if not query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    if len(files) > MAX_ANALYSIS_FILES:
        raise HTTPException(400, f"Tối đa {MAX_ANALYSIS_FILES} file mỗi lượt phân tích")
    _enforce_chat_limits(current_user, db)
    query_urls = _urls_in_query(query)

    # Bóc tách câu hỏi thực tế (loại bỏ chỉ dẫn chế độ [He thong: ...]) trước khi truy xuất
    clean_q = re.sub(r'^\[(?:he\s+thong|system):[^\]]+\]', '', query, flags=re.IGNORECASE).strip()
    clean_q = _URL_PATTERN.sub("", clean_q).strip() or clean_q or query.strip()
    lang = detect_language(clean_q)
    sent_query = _normalize_mode_instruction(query, lang)
    answer_query = _URL_PATTERN.sub("", sent_query).strip() or clean_q

    # Parse document_ids
    try:
        raw_doc_ids = json.loads(document_ids) if document_ids and document_ids != "[]" else []
    except json.JSONDecodeError:
        raw_doc_ids = []
    if not isinstance(raw_doc_ids, list):
        raw_doc_ids = []
    doc_ids = _sanitize_uuid_list(raw_doc_ids) if raw_doc_ids else []
    if len(doc_ids) + len(files) + len(query_urls) > MAX_ANALYSIS_FILES:
        raise HTTPException(400, f"Tổng số file đính kèm và tài liệu đã chọn không được vượt quá {MAX_ANALYSIS_FILES}.")
    if doc_ids:
        doc_ids = readable_document_ids(db, current_user, doc_ids)

    # Chỉ fallback lấy tất cả tài liệu nếu KHÔNG CÓ file đính kèm nào được gửi lên
    if not doc_ids and not files:
        doc_ids = readable_document_ids(db, current_user)

    # Validate & parse each file into structured chunks (per sheet for Excel)
    import os
    all_file_chunks: list[dict] = []
    for f in files:
        # Handle both 'photo.png' and 'C:\Users\HP\Pictures\photo.png' paths
        raw_name = f.filename or ""
        ext = os.path.splitext(raw_name)[1].lstrip(".").lower()
        if ext not in SUPPORTED_TYPES:
            raise HTTPException(400, f"Định dạng '{ext}' không được hỗ trợ: {f.filename}")
        size = 0
        data = b""
        while True:
            chunk = f.file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                raise HTTPException(400, f"File '{f.filename}' vượt 50MB")
            data += chunk

        # Phân tách file thành các chunk có cấu trúc rõ ràng (tách từng Sheet cho Excel)
        visual_request = bool(re.search(
            r"\b(chart|graph|plot|figure|visual|table|diagram|biểu đồ|đồ thị|hình|sơ đồ|bảng số liệu|ước lượng số liệu)\b",
            clean_q,
            re.IGNORECASE,
        ))
        f_chunks = parse_file_chunks(data, f.filename, analyze_visuals=visual_request, max_visual_pages=3)
        unreadable_markers = ("[Lỗi khi đọc file:", "[File PDF trống]", "[Không thể đọc file")
        if (
            not f_chunks
            or all(not (chunk.get("content") or "").strip() for chunk in f_chunks)
            or all(any(marker in (chunk.get("content") or "") for marker in unreadable_markers) for chunk in f_chunks)
        ):
            raise HTTPException(422, f"Không trích xuất được nội dung từ '{f.filename}'. Hãy thử PDF có thể tìm kiếm hoặc DOCX.")
        all_file_chunks.extend(f_chunks)

    web_sources, web_errors = _fetch_url_sources(
        clean_q,
        explicit_urls=query_urls,
        search_if_empty=not doc_ids and not files and not query_urls,
    )

    # Fallback: if no doc_ids and no files → general web search
    if not doc_ids and not all_file_chunks and not web_sources:
        if not query_urls:
            def no_results():
                yield "❌ Không tìm thấy kết quả tìm kiếm. Vui lòng thử lại."
            return StreamingResponse(no_results(), media_type="text/plain; charset=utf-8")
        message = "Không truy cập được các URL đã gửi. Hãy kiểm tra lại liên kết hoặc tải PDF mà bạn có quyền sử dụng lên.\n" + "\n".join(web_errors)
        return StreamingResponse(iter([message]), media_type="text/plain; charset=utf-8")

    # Use RAG with document_ids + inline file context (dùng clean_q không chứa [He thong: ...])
    context_chunks = retrieve(clean_q, doc_ids, db) if doc_ids else []

    # Luôn đưa nội dung file đính kèm (các sheet Excel, ảnh, tài liệu...) vào ngữ cảnh ưu tiên cao nhất
    if all_file_chunks:
        selected_inline = _select_inline_chunks(all_file_chunks, clean_q, per_document=4, max_total=24)
        context_chunks = selected_inline + context_chunks
    context_chunks = _cap_context_documents(context_chunks, MAX_ANALYSIS_FILES - len(web_sources))

    if not context_chunks and not web_sources:
        no_ctx_msg = ("No relevant information was found in the attached or retrieved documents."
                      if lang == "en" else "Chưa tìm thấy thông tin liên quan trong tài liệu đính kèm hoặc kho tài liệu.")
        return StreamingResponse(
            iter([no_ctx_msg]),
            media_type="text/plain; charset=utf-8",
            headers={"X-No-Context": "true", "Access-Control-Expose-Headers": "X-No-Context"},
        )

    config_error = llm_configuration_error()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    available_figures = []
    if doc_ids:
        try:
            from app.services.figure_extractor import get_figures_for_chunks
            available_figures = get_figures_for_chunks(context_chunks, db)
        except Exception as fig_err:
            logger.warning("Không thể lấy figures trong file-chat: %s", fig_err)

    raw_stream = (
        generate_stream_web_search(answer_query, web_sources, context_chunks=context_chunks, lang=lang)
        if web_sources else generate_stream(answer_query, context_chunks, lang=lang, available_figures=available_figures)
    )

    def stream_with_saving():
        collected: list[str] = []; stream_unlocked = bool(web_sources); speculative_buffer: list[str] = []
        no_ctx_marker = "__NO_CONTEXT__"
        pending = ""
        for chunk in raw_stream:
            pending += chunk
            while "\n" in pending:
                line, pending = pending.split("\n", 1)
                safe_line = _verify_numeric_citations(_strip_absence_sentence_citations(_normalize_stream_citations(qualify_missing_evidence(line + "\n"))), context_chunks)
                if re.search(r"(?i)(?:tài liệu không đề cập trực tiếp|dựa vào kiến thức chung)", safe_line) and not collected and not bool(_build_references_block(safe_line, context_chunks, lang)): safe_line = no_ctx_marker
                if not stream_unlocked and no_ctx_marker not in safe_line and not any(no_ctx_marker in c for c in collected) and bool(_build_references_block(safe_line, context_chunks, lang)): stream_unlocked = True; yield "".join(speculative_buffer); speculative_buffer.clear()
                if stream_unlocked and no_ctx_marker not in safe_line and not any(no_ctx_marker in c for c in collected) and not re.search(r"(?i)(?:dựa\s+(?:trên|vào)\s+kiến\s+thức\s+chung|kiến\s+thức\s+bên\s+ngoài)", safe_line):
                    yield safe_line
                elif not stream_unlocked: speculative_buffer.append(safe_line)
                collected.append(safe_line)
        if pending:
            safe_line = _verify_numeric_citations(_strip_absence_sentence_citations(_normalize_stream_citations(qualify_missing_evidence(pending))), context_chunks)
            if not stream_unlocked and no_ctx_marker not in safe_line and not any(no_ctx_marker in c for c in collected) and bool(_build_references_block(safe_line, context_chunks, lang)): stream_unlocked = True; yield "".join(speculative_buffer); speculative_buffer.clear()
            if stream_unlocked and no_ctx_marker not in safe_line and not any(no_ctx_marker in c for c in collected) and not re.search(r"(?i)(?:dựa\s+(?:trên|vào)\s+kiến\s+thức\s+chung|kiến\s+thức\s+bên\s+ngoài)", safe_line):
                yield safe_line
            collected.append(safe_line)
        full_answer = _clean_cjk_leakage(re.split(r'\n+[^\n]*(?:dựa\s+(?:trên|vào)\s+kiến\s+thức\s+chung|kiến\s+thức\s+bên\s+ngoài)[^\n]*', "".join(collected), maxsplit=1, flags=re.I)[0]).strip() + "\n"

        if no_ctx_marker in full_answer:
            final_answer = ("No sufficient evidence was found in the provided documents."
                            if lang == "en" else "Chưa tìm thấy đủ bằng chứng trong tài liệu được cung cấp.")
            yield final_answer
            if current_user is not None:
                _save_chat_history(db, str(current_user.id), clean_q, final_answer, doc_ids)
            return

        references_block = _build_references_block(full_answer, context_chunks, lang)
        if not web_sources and not references_block:
            final_answer = ("This information is not available in the uploaded documents." if lang == "en" else "Không có thông tin về nội dung này trong các tài liệu đã tải lên.")
            yield final_answer
            if current_user is not None and hasattr(locals().get("request", None), "query"): _save_chat_history(db, str(current_user.id), request.query, final_answer, request.document_ids)
            return
        if not web_sources and not stream_unlocked:
            yield full_answer
        final_answer = full_answer + references_block
        if references_block:
            yield references_block

        if current_user is not None:
            _save_chat_history(db, str(current_user.id), clean_q, final_answer, doc_ids)

    return StreamingResponse(
        stream_with_saving(),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Context-Pages": ",".join(str(c.get("page_number", 1)) for c in context_chunks),
            "X-Document-IDs": ",".join(str(c.get("document_id", "")) for c in context_chunks if c.get("document_id")),
            "X-No-Context": "false",
            "Access-Control-Expose-Headers": "X-Context-Pages,X-Document-IDs,X-No-Context",
        },
    )


# ── Scientific & Evidence-Based Research Appraisal Endpoints ────────────────

class AppraiseRequest(BaseModel):
    query: str
    answer: str
    document_ids: Optional[list[str]] = []


@router.post("/appraise")
def appraise_answer(
    req: AppraiseRequest,
    db: Session = Depends(get_db)
):
    """
    Thẩm định khoa học toàn diện cho câu trả lời theo 7 tiêu chuẩn học thuật:
    1. Oxford CEBM Evidence Level Grading & Recommendation Grade
    2. PICO Framework Extraction Card
    3. Consensus & Scientific Debate Matrix
    4. Peer-Review Socratic Questions (Devil's Advocate)
    5. Psychometric Scale Inspector & Cut-Offs (BDI-II, PHQ-9, GAD-7, DASS-21, HAM-D)
    6. International Citations (BibTeX, RIS, APA 7th)
    7. Interactive Semantic Knowledge Graph
    """
    from app.services.scientific_appraiser import appraise_scientific_context

    context_chunks = []
    # Nếu client truyền document_ids, chỉ lấy metadata hoặc chunks của các tài liệu đó
    safe_ids = _sanitize_uuid_list(req.document_ids) if req.document_ids else []
    if safe_ids:
        try:
            rows = db.execute(
                text("""
                    SELECT id, title, authors, year, filename
                    FROM documents
                    WHERE id = ANY(CAST(:ids AS uuid[]))
                """),
                {"ids": safe_ids},
            ).fetchall()
            for r in rows:
                context_chunks.append({
                    "document_id": str(r.id),
                    "doc_title": r.title or r.filename,
                    "doc_authors": r.authors or "",
                    "doc_filename": r.filename or "Tài liệu.pdf",
                    "content": ""
                })
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

    appraisal = appraise_scientific_context(req.query, req.answer, context_chunks, db)
    return appraisal



class CitationExportRequest(BaseModel):
    document_ids: Optional[list[str]] = []
    format: str = "bibtex"  # "bibtex", "ris", "apa7"
    custom_docs: Optional[list[dict]] = []


@router.post("/export-citation")
def export_citation(req: CitationExportRequest, db: Session = Depends(get_db)):
    from app.services.scientific_appraiser import (
        generate_bibtex_entry, generate_ris_entry, generate_apa7_citation
    )
    docs = []
    safe_ids = _sanitize_uuid_list(req.document_ids) if req.document_ids else []
    if safe_ids:
        rows = db.execute(
            text("""
                SELECT id, title, authors, year, filename
                FROM documents
                WHERE id = ANY(CAST(:ids AS uuid[]))
            """),
            {"ids": safe_ids},
        ).fetchall()
        for r in rows:
            docs.append({
                "id": str(r.id),
                "title": r.title or r.filename,
                "authors": r.authors or "",
                "year": r.year,
                "filename": r.filename or "Tài liệu.pdf"
            })
    if not docs and req.custom_docs:
        docs = req.custom_docs

    fmt = req.format.lower()
    if fmt == "bibtex":
        content = "\n\n".join([generate_bibtex_entry(d) for d in docs])
        filename = "citations.bib"
        media_type = "application/x-bibtex"
    elif fmt == "ris":
        content = "\n\n".join([generate_ris_entry(d) for d in docs])
        filename = "citations.ris"
        media_type = "application/x-research-info-systems"
    else:
        content = "\n\n".join([generate_apa7_citation(d) for d in docs])
        filename = "citations_apa7.txt"
        media_type = "text/plain; charset=utf-8"

    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
