from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


def _normalize_ws(text: str) -> str:
    """Chuẩn hoá khoảng trắng + xuống dòng để so sánh fuzzy."""
    return re.sub(r"\s+", " ", text or "").strip()


def _char_overlap(a: str, b: str) -> int:
    """Đếm số ký tự (đã chuẩn hoá) của a xuất hiện trong b.

    Dùng sliding window để tìm vị trí a khớp nhiều nhất với b.
    Trả về số ký tự khớp (≈0 nếu không khớp).
    """
    a = _normalize_ws(a)
    b = _normalize_ws(b)
    if not a or not b:
        return 0
    # Lấy đoạn đầu của a (tối đa 120 ký tự) làm đại diện
    head = a[:120]
    if not head:
        return 0
    # Tìm vị trí head trong b
    pos = b.find(head)
    if pos >= 0:
        return len(head)
    # Không khớp nguyên: đếm prefix dài nhất khớp
    best = 0
    for n in range(min(len(head), 80), 10, -5):
        if head[:n] in b:
            best = n
            break
    return best


def _find_page(chunk_content: str, pages_data: list) -> int:
    """Gán trang cho chunk bằng cách tìm trang có nhiều ký tự chung nhất
    với phần đầu của chunk (cải thiện đáng kể so với `in` đơn thuần).

    Trước đây: so sánh 80 ký tự đầu chunk với `in page_text` — chunk cắt
    ngang trang sẽ gán sai. Giờ: chuẩn hoá whitespace + dùng sliding overlap.
    """
    if not pages_data:
        return 1
    head = chunk_content[:120]
    best_page = 1
    best_score = 0
    for page in pages_data:
        text = page.get("text", "")
        if not text:
            continue
        score = _char_overlap(head, text)
        if score > best_score:
            best_score = score
            best_page = page["page"]
    return best_page


def chunk_text(text: str, document_id: str, pages_data: list) -> list[dict]:
    """Chunk văn bản PDF thành các đoạn nhỏ tập trung 1 chủ đề.

    Cải thiện so với phiên bản cũ:
    - chunk_size 1500 → 800 (mỗi chunk tập trung hơn)
    - chunk_overlap 150 → 200 (~25%, tránh rớt thông tin ở biên)
    - _find_page dùng fuzzy match thay vì `in` đơn thuần
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    raw_chunks = splitter.split_text(text)
    chunks = []
    for idx, content in enumerate(raw_chunks):
        if not content.strip():
            continue
        chunks.append({
            "content": content,
            "chunk_index": idx,
            "document_id": document_id,
            "page_number": _find_page(content, pages_data),
        })
    return chunks
