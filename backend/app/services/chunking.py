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
    """Gán trang cho chunk bằng cách ưu tiên nhãn [Trang X] và phần thân chính của chunk.

    Khắc phục lỗi cũ:
    - Khi chunk cắt qua ranh giới trang (overlap 200 ký tự đầu thuộc cuối trang trước,
      sau đó là [Trang X] và 600 ký tự thuộc trang X), hoặc khi 120 ký tự đầu trùng với
      running header/footer lặp lại ở Trang 1, thuật toán cũ gán nhầm về Trang 1.
    """
    if not pages_data:
        return 1

    # 1. Nếu trong chunk có nhãn [Trang X], tính chính xác số ký tự thuộc về từng trang
    markers = list(re.finditer(r"\[Trang\s+(\d+)\]", chunk_content))
    if markers:
        page_char_counts: dict[int, int] = {}
        first_pos = markers[0].start()
        first_page = int(markers[0].group(1))
        if first_pos > 0:
            prev_page = max(1, first_page - 1)
            page_char_counts[prev_page] = page_char_counts.get(prev_page, 0) + first_pos
        for idx_m, m in enumerate(markers):
            p_num = int(m.group(1))
            seg_start = m.end()
            seg_end = markers[idx_m + 1].start() if idx_m + 1 < len(markers) else len(chunk_content)
            seg_len = max(0, seg_end - seg_start)
            page_char_counts[p_num] = page_char_counts.get(p_num, 0) + seg_len
        if page_char_counts:
            return max(page_char_counts.items(), key=lambda kv: (kv[1], kv[0]))[0]

    # 3. Nếu không có nhãn [Trang X] trong chunk, lấy đoạn giữa của chunk (bỏ qua 80 ký tự đầu/cuối dễ dính running header/footer)
    cleaned_content = re.sub(r"\[Trang\s+\d+\]\s*", "", chunk_content).strip()
    mid_start = 80 if len(cleaned_content) > 260 else 0
    probe = cleaned_content[mid_start:mid_start + 160]
    best_page = 1
    best_score = 0
    for page in pages_data:
        text = page.get("text", "")
        if not text:
            continue
        score = _char_overlap(probe, text)
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
    try:
        from app.services.reference_filter import filter_reference_chunks
        chunks = filter_reference_chunks(chunks)
    except Exception:
        pass
    return chunks
