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
    r'(?:^|\n)\s*(?:#{1,4}\s*|\d{1,2}\.?\s+)?(?:references?|tài liệu tham khảo|bibliography|literature cited|works cited)\s*(?::|\n|$)',
    re.IGNORECASE
)

# Năm xuất bản: (18xx), (19xx), (20xx) hoặc dạng số năm đứng sau dấu chấm/phẩy/khoảng trắng
_YEAR_REGEX = re.compile(r'(?:\((?:18|19|20)\d{2}[a-z]?\)|\b(?:18|19|20)\d{2}[a-z]?(?=[.,;\s]))')

# Định dạng đánh số trích dẫn trong ngoặc vuông: [1], [2], [10]
_BRACKET_NUM_REGEX = re.compile(r'(?:^|\n)\s*\[\d{1,3}\]\s+[A-Z]')

# Định dạng đánh số trích dẫn kèm tác giả: 21. Mobbs D..., 25. Dong X..., 1. Smith, J.
_NUM_REF_ENTRY_REGEX = re.compile(r'(?:^|\n)\s*\d{1,3}\.\s+[A-Z][a-z]+(?:,\s+[A-Z]\.?|\s+[A-Z]{1,2}(?:\.|\b|\())')

# DOI / URL thư mục
_DOI_URL_REGEX = re.compile(r'\b(?:doi(?::|\.org)|arxiv:\d|isbn|issn|https?://(?:doi\.org|arxiv\.org|dx\.doi\.org))\b', re.IGNORECASE)

# Tên tác giả dạng học thuật: LastName, F. M.
_AUTHOR_NAME_REGEX = re.compile(r'\b[A-Z][a-zA-Z\'-]+,\s+[A-Z]\.(?:\s*[A-Z]\.)?')

# Tập, số trang: 56(7), 1268 hoặc pp. 101-124
_VOL_PAGE_REGEX = re.compile(r'\b\d{1,4}\s*\(\s*\d{1,4}\s*\)\s*,\s*\d+(?:[–\-]\d+)?\b|\b(?:pp|pages)\.?\s*\d+(?:[–\-]\d+)?\b', re.IGNORECASE)

# Nhà xuất bản học thuật phổ biến
_PUBLISHER_REGEX = re.compile(r'\b(?:press|proceedings|springer|elsevier|ieee|acm|routledge|wiley|mit press|university press|conference on|symposium on|sage|journal of|plos|nature|science)\b', re.IGNORECASE)


def is_reference_content(text: str) -> bool:
    """Kiểm tra xem một đoạn văn bản (chunk/snippet) có phải là mục References hay không.
    
    Returns:
        True nếu đoạn văn bản là danh sách tài liệu tham khảo.
    """
    if not text or len(text.strip()) < 30:
        return False

    clean_text = text.strip()

    # 1. Bắt đầu bằng tiêu đề References / Tài liệu tham khảo
    if _REF_HEADER_REGEX.search(clean_text[:120]):
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

    # Định dạng đánh số 1. Smith, J. / 21. Mobbs D kết hợp với năm
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
    """Nếu đoạn văn bản chứa điểm giao thoa (phần đầu là nội dung, phần sau là References),
    cắt bỏ phần References phía sau để giữ lại nội dung chính."""
    if not text:
        return ""
    match = _REF_HEADER_REGEX.search(text)
    if match:
        idx = match.start()
        # Nếu tiêu đề References nằm sau ít nhất 50 ký tự nội dung chính
        if idx >= 50:
            return text[:idx].strip()
        # Nếu tiêu đề nằm ngay đầu -> bỏ toàn bộ
        return ""
    return text


def filter_reference_chunks(chunks: list[dict]) -> list[dict]:
    """Lọc danh sách chunks, loại bỏ toàn bộ các chunk thuộc mục References.
    Đồng thời làm sạch các chunk chứa điểm giao thoa với mục References."""
    if not chunks:
        return []

    filtered = []
    for c in chunks:
        content = c.get("content", "")
        if not content:
            continue

        # 1. Thử cắt bỏ References nếu nằm ở cuối chunk
        cleaned = clean_reference_boundary(content)
        if cleaned and len(cleaned) < len(content):
            if not is_reference_content(cleaned):
                c_copy = dict(c)
                c_copy["content"] = cleaned
                filtered.append(c_copy)
            continue

        # 2. Nếu không có header giao thoa, kiểm tra toàn bộ chunk có phải là References không
        if is_reference_content(content):
            logger.debug("Filtered reference chunk: doc=%s, page=%s", c.get("document_id"), c.get("page_number"))
            continue

        filtered.append(c)

    return filtered
