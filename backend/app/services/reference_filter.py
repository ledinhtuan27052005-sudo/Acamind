"""
Module lọc bỏ nội dung mục Tài liệu tham khảo (References / Bibliography)
trong các bài báo khoa học PDF, đảm bảo hệ thống chỉ trích xuất và trích dẫn
từ nội dung chính (Mở đầu, Phương pháp, Kết quả, Thảo luận, Kết luận).
"""
import re
import logging

logger = logging.getLogger(__name__)

# Các tiêu đề bắt đầu mục tài liệu tham khảo (hỗ trợ đánh số chương như '7. References', '## References', v.v.)
_REF_HEADER_REGEX = re.compile(
    r'(?:^|\n)\s*(?:\[Trang\s+\d+\]\s*\n\s*)?(?:#{1,4}\s*|\d{1,2}\.?\s+)?'
    r'(?:references?|tài liệu tham khảo|bibliography|literature cited|works cited)\b\s*(?::|\n|$)',
    re.IGNORECASE
)

# Các tiêu đề phần phụ lục hành chính cuối bài (Acknowledgements, Funding, Ethics, Affiliations, Disclosures, Open Access)
_BACKMATTER_HEADER_REGEX = re.compile(
    r'(?:^|\n)\s*(?:#{1,4}\s*|\d{1,2}\.?\s+)?'
    r'(?:acknowledgements?|acknowledgments?|lời cảm ơn|funding(?:\s+information|\s+statement)?|'
    r'ethics\s+(?:approval|statement|declarations?)(?:\s+and\s+(?:informed\s+)?consent(?:\s+to\s+participate)?)?|'
    r'compliance\s+with\s+ethical\s+standards|disclosures?|'
    r'competing\s+interests?|conflicts?\s+of\s+interest|(?:credit\s+)?author(?:ship)?\s+contributions?(?:\s+statement)?|'
    r'affiliations?|author\s+information|authors?\s+and\s+affiliations?|'
    r'data\s+availability(?:\s+statement)?|code\s+availability|publisher[\'’]?s\s+note|open\s+access)\b',
    re.IGNORECASE
)

# Các cụm câu đặc trưng của phần Đóng góp tác giả / Xung đột lợi ích / Giấy phép bản quyền cuối bài
_BOILERPLATE_PHRASE_REGEX = re.compile(
    r'(?:agreement\s+to\s+be\s+accountable\s+for\s+all\s+aspects\s+of\s+the\s+work|'
    r'final\s+approval\s+of\s+the\s+version\s+to\s+be\s+published|'
    r'critical\s+revision\s+for\s+important\s+intellectual\s+content|'
    r'have\s+nothing\s+to\s+disclose|reports?\s+personal\s+fees\s+from|'
    r'licensed\s+under\s+a\s+creative\s+commons\s+attribution|'
    r'credit\s+authorship\s+contribution\s+statement|'
    r'if\s+material\s+is\s+not\s+included\s+in\s+the\s+article[\'’]?s\s+creative\s+commons\s+licence)',
    re.IGNORECASE
)

# Bản quyền / chân trang nhà xuất bản bị tách rời từng ký tự hoặc nguyên dòng
_COPYRIGHT_NOISE_REGEX = re.compile(
    r'(?:all\s+rights\s+reserved|macmillan\s+publishers|springer\s+nature|'
    r'©\s*\d{4}|m\s+a\s+c\s+m\s+i\s+l\s+l\s+a\s+n|s\s+p\s+r\s+i\s+n\s+g\s+e\s+r)',
    re.IGNORECASE
)

# Năm xuất bản: (18xx), (19xx), (20xx) hoặc dạng số năm đứng sau dấu chấm/phẩy/khoảng trắng
_YEAR_REGEX = re.compile(r'(?:\((?:18|19|20)\d{2}[a-z]?\)|\b(?:18|19|20)\d{2}[a-z]?(?=[.,;\s\)]))')

# Định dạng đánh số trích dẫn trong ngoặc vuông: [1], [2], [10]
_BRACKET_NUM_REGEX = re.compile(r'(?:^|[\n\t]|\s{2,})\[\d{1,3}\]\s+[A-Z]')

# Định dạng đánh số trích dẫn kèm tác giả (hỗ trợ cả dấu tab \t và Vancouver style '16. Sterne J, Hernán M')
_NUM_REF_ENTRY_REGEX = re.compile(
    r'(?:^|[\n\t]|\s{2,})\d{1,3}\.\s+[A-Z][a-zA-Z\u00C0-\u017F\'-]+(?:,\s+[A-Z]|\s+[A-Z]{1,3}(?:[.,\s\(]|\b))'
)

# DOI / URL thư mục (không đặt \b sau dấu ':' vì 'doi: 10.1016' có khoảng trắng sau ':')
_DOI_URL_REGEX = re.compile(
    r'(?:\bdoi\s*:|\bdoi\.org/|\barxiv\s*:\s*\d|\bisbn\b|\bissn\b|https?://\s*(?:dx\.)?doi\.org/|https?://\s*arxiv\.org/)',
    re.IGNORECASE
)

# Tên tác giả dạng học thuật: LastName, F. M. | FirstName M. LastName | Vancouver: LastName FM, LastName2 GH | BibTeX/ACL: FirstName LastName, (and) FirstName2 LastName2
_AUTHOR_NAME_REGEX = re.compile(
    r'(?:\b[A-Z][a-zA-Z\u00C0-\u017F\'-]+,\s+[A-Z]\.(?:\s*[A-Z]\.)?'
    r'|\b[A-Z][a-zA-Z\u00C0-\u017F\'-]+\s+(?:[A-Z]\.\s+)+[A-Z][a-zA-Z\u00C0-\u017F\'-]+'
    r'|\b[A-Z][a-zA-Z\u00C0-\u017F\'-]+\s+[A-Z]{1,2},\s+[A-Z][a-zA-Z\u00C0-\u017F\'-]+\s+[A-Z]{1,2}\b'
    r'|\b[A-Z][a-z]{1,15}\s+(?:[A-Z][a-zA-Z.]*\s+)?[A-Z][a-zA-Z\u00C0-\u017F\'-]{1,20},\s+(?:and\s+)?[A-Z][a-z]{1,15}\s+(?:[A-Z][a-zA-Z.]*\s+)?[A-Z][a-zA-Z\u00C0-\u017F\'-]{1,20}\b)'
)

# Tập, số trang: 56(7), 1268 hoặc 31(3):236-257 hoặc 41:85-97 hoặc pp. 101-124
_VOL_PAGE_REGEX = re.compile(
    r'\b\d{1,4}\s*(?:\(\s*\d{1,4}\s*\)\s*[,:]\s*\d+(?:[–\-]\d+)?|:\s*\d{1,5}[–\-]\d{1,5})\b|\b(?:pp|pages)\.?\s*\d+(?:[–\-]\d+)?\b',
    re.IGNORECASE
)

# Nhà xuất bản học thuật phổ biến
_PUBLISHER_REGEX = re.compile(
    r'\b(?:press|proceedings|springer|elsevier|ieee|acm|routledge|wiley|mit press|university press|'
    r'conference on|symposium on|transactions on|arxiv preprint|computational linguistics|'
    r'neural information processing|sage|journal of|plos|nature|science|bmj|lancet|jama|ann\s+surg|obes\s+surg)\b',
    re.IGNORECASE
)

_ABSTRACT_START_REGEX = re.compile(
    r'(?:^|\n)\s*(?:abstract|tóm\s+tắt|summary)\s*(?::|\n)',
    re.IGNORECASE
)

_AFFILIATION_LINE_REGEX = re.compile(
    r'\b(?:department\s+of|division\s+of|faculty\s+of|school\s+of|institute\s+of|key\s+laboratory|'
    r'center\s+for|centre\s+for|university|hospital|medical\s+center|medical\s+centre|klinika|'
    r'nhs\s+foundation\s+trust|correspondence|corresponding\s+author|'
    r'contributed\s+equally|e-?mail\(?s?\)?:|@[a-z0-9.-]+\.[a-z]{2,})\b',
    re.IGNORECASE
)

# Dòng đánh số đơn vị công tác (Affiliations): "18 Division of General Surgery...", "1 Department of Surgical Sciences..."
_NUMBERED_AFFIL_REGEX = re.compile(
    r'(?:^|[\n\t])\s*\d{1,2}\s+(?:Department|Division|Institute|Center|Centre|School|Faculty|Hospital|University|Laboratory|Clinic|Section|Unit|Ministry|National)\b',
    re.IGNORECASE
)


def _normalize_zero_width(text: str) -> str:
    """Loại bỏ zero-width space (\\u200b) và chuẩn hóa khoảng trắng đặc biệt trong PDF."""
    if not text:
        return ""
    text = re.sub(r'[\u200b-\u200f\ufeff\xad]', '', text)
    text = re.sub(r'[\xa0\u2000-\u200a]', ' ', text)
    return text


def clean_front_matter_header(text: str) -> str:
    """Làm sạch phần Tiêu đề bài báo, Tác giả, Đơn vị công tác (Affiliation) và Email liên hệ
    ở đầu Trang 1 để hệ thống không trích dẫn/highlight nhầm vào tiêu đề hoặc tên tác giả."""
    if not text:
        return ""
    page_tag = ""
    body = text
    m_tag = re.match(r'^(\s*\[Trang\s+\d+\]\s*\n?)', body)
    if m_tag:
        page_tag = m_tag.group(1)
        body = body[m_tag.end():]

    # Nếu có chữ Abstract / Tóm tắt trong 1200 ký tự đầu tiên -> cắt bỏ phần Title/Author/Affiliation phía trên
    m_abs = _ABSTRACT_START_REGEX.search(body[:1200])
    if m_abs:
        body = body[m_abs.start():].lstrip()

    # Loại bỏ các dòng chú thích tác giả / email liên hệ (correspondence footnotes)
    clean_lines = []
    for line in body.splitlines():
        s = line.strip()
        if not s:
            clean_lines.append(line)
            continue
        if re.search(r'(?:these\s+authors\s+contributed\s+equally|co-?corresponding\s+authors?|e-?mail\(?s?\)?:|@[a-z0-9.-]+\.[a-z]{2,})', s, re.I):
            continue
        clean_lines.append(line)

    result = "\n".join(clean_lines).strip()
    if not result:
        return ""
    return f"{page_tag}{result}" if page_tag else result


def is_front_matter_only(text: str) -> bool:
    """Kiểm tra xem một chunk ở Trang 1 có phải CHỈ chứa tiêu đề, tên tác giả và đơn vị công tác
    (hoặc quá ngắn sau khi cắt tiêu đề) hay không."""
    if not text:
        return True
    body = re.sub(r'^\s*\[Trang\s+\d+\]\s*', '', text).strip()
    if len(body) < 120:
        return True
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return True
    affil_hits = sum(1 for ln in lines if _AFFILIATION_LINE_REGEX.search(ln))
    if affil_hits >= 2 and len(body) < 550 and not _ABSTRACT_START_REGEX.search(body):
        return True
    return False


def is_reference_content(text: str) -> bool:
    """Kiểm tra xem một đoạn văn bản (chunk/snippet) có phải là mục References,
    danh sách Đơn vị công tác (Affiliations), Đóng góp tác giả (Author Contributions),
    Xung đột lợi ích (Disclosures) hoặc phụ lục hành chính cuối bài hay không.
    
    Returns:
        True nếu đoạn văn bản là danh sách tài liệu tham khảo hoặc phụ lục hành chính/tác giả.
    """
    if not text or len(text.strip()) < 30:
        return False

    clean_text = _normalize_zero_width(re.sub(r'^\s*\[Trang\s+\d+\]\s*', '', text.strip()).strip())

    # 1. Bắt đầu bằng tiêu đề References / Tài liệu tham khảo hoặc Back-matter / Affiliations
    if _REF_HEADER_REGEX.search(clean_text[:200]):
        return True
    if _BACKMATTER_HEADER_REGEX.search(clean_text[:200]):
        return True

    # Nếu đoạn văn chứa từ 2 tiêu đề hành chính cuối bài trở lên
    if len(_BACKMATTER_HEADER_REGEX.findall(clean_text)) >= 2:
        return True

    # Kiểm tra các mẫu câu đóng góp tác giả / xung đột lợi ích / giấy phép bản quyền cuối bài
    if _BOILERPLATE_PHRASE_REGEX.search(clean_text):
        return True

    # Kiểm tra danh sách đơn vị công tác (Affiliations) ở bất kỳ trang nào (kể cả trang cuối Springer/Nature)
    if len(_NUMBERED_AFFIL_REGEX.findall(clean_text)) >= 2:
        return True
    affil_matches = len(_AFFILIATION_LINE_REGEX.findall(clean_text))
    if affil_matches >= 3 and not _ABSTRACT_START_REGEX.search(clean_text):
        return True

    # 2. Kiểm tra mật độ định dạng trích dẫn thư mục
    num_years = len(_YEAR_REGEX.findall(clean_text))
    num_brackets = len(_BRACKET_NUM_REGEX.findall(clean_text))
    num_num_entries = len(_NUM_REF_ENTRY_REGEX.findall(clean_text))
    num_authors = len(_AUTHOR_NAME_REGEX.findall(clean_text))
    num_doi = len(_DOI_URL_REGEX.findall(clean_text))
    num_vol_page = len(_VOL_PAGE_REGEX.findall(clean_text))
    num_pub = len(_PUBLISHER_REGEX.findall(clean_text))

    # Nếu có nhiều mục đánh số dạng [1], [2] -> danh mục trích dẫn
    if num_brackets >= 2:
        return True

    # Định dạng đánh số 1. Smith, J. / 16. Sterne J kết hợp với năm
    if num_num_entries >= 2 and num_years >= 1:
        return True

    # Chứa từ 2 DOI trở lên (chỉ xuất hiện trong danh mục tài liệu tham khảo)
    if num_doi >= 2:
        return True

    # Năm xuất bản kết hợp với DOI và/hoặc tập san
    if num_years >= 2 and num_doi >= 1:
        return True

    # Có ít nhất 1 tác giả theo format chuẩn thư mục kèm năm và đặc trưng xuất bản
    if num_years >= 2 and num_authors >= 1 and (num_pub >= 1 or num_vol_page >= 1 or num_doi >= 1):
        return True

    if num_years >= 1 and num_authors >= 1 and num_doi >= 1:
        return True

    if num_authors >= 3 and num_years >= 1:
        return True

    if num_vol_page >= 2 and num_years >= 1:
        return True

    if num_authors >= 2 and num_years >= 2:
        return True

    return False


def clean_reference_boundary(text: str) -> str:
    """Nếu đoạn văn bản chứa điểm giao thoa (phần đầu là nội dung, phần sau là References/Acknowledgements/Affiliations),
    cắt bỏ phần References/Back-matter phía sau để giữ lại nội dung chính."""
    if not text:
        return ""
    norm_text = _normalize_zero_width(text)
    cut_idx = len(norm_text)
    for pattern in (_REF_HEADER_REGEX, _BACKMATTER_HEADER_REGEX):
        match = pattern.search(norm_text)
        if match and match.start() < cut_idx:
            cut_idx = match.start()

    if cut_idx < len(norm_text):
        if cut_idx >= 180:
            candidate = norm_text[:cut_idx].strip()
            if _COPYRIGHT_NOISE_REGEX.search(candidate) and len(candidate) < 500:
                return ""
            return candidate
        return ""
    return norm_text


def filter_reference_chunks(chunks: list[dict]) -> list[dict]:
    """Lọc danh sách chunks, loại bỏ toàn bộ các chunk thuộc mục References, Back-matter, Affiliations
    và làm sạch phần Tiêu đề/Tác giả ở đầu Trang 1."""
    if not chunks:
        return []

    filtered = []
    for c in chunks:
        # File đính kèm tải lên trong chat (Excel, Word, Ảnh...) không phải là tài liệu thư mục để lọc bỏ
        if c.get("document_id") == "inline_file" or (c.get("from_memory") and not is_reference_content(c.get("content", ""))):
            filtered.append(c)
            continue

        content = c.get("content", "")
        if not content:
            continue

        # Xử lý Trang 1: Cắt bỏ phần Tiêu đề bài báo / Tên tác giả / Đơn vị công tác phía trên Abstract
        if str(c.get("page_number")) == "1":
            cleaned_p1 = clean_front_matter_header(content)
            if is_front_matter_only(cleaned_p1) or is_reference_content(cleaned_p1):
                continue
            c_copy = dict(c)
            c_copy["content"] = cleaned_p1
            filtered.append(c_copy)
            continue

        # 1. Thử cắt bỏ References / Back-matter / Affiliations nếu nằm ở cuối chunk
        cleaned = clean_reference_boundary(content)
        if not cleaned:
            continue
        if len(cleaned) < len(_normalize_zero_width(content)):
            if len(cleaned.strip()) >= 320 and not is_reference_content(cleaned):
                c_copy = dict(c)
                c_copy["content"] = cleaned
                filtered.append(c_copy)
            continue

        # 2. Nếu không có header giao thoa, kiểm tra toàn bộ chunk có phải là References / Back-matter / Affiliations không
        if is_reference_content(content):
            logger.debug("Filtered reference chunk: doc=%s, page=%s", c.get("document_id"), c.get("page_number"))
            continue

        filtered.append(c)

    return filtered
