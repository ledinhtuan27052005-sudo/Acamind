import re
import fitz  # PyMuPDF
import pdfplumber

# Ngưỡng phát hiện heading dựa trên font size (points).
# Text có size >= ngưỡng này được coi là heading. 13.0 là mặc định hợp lý cho
# phần lớn tài liệu học thuật (body thường 10-12pt, heading thường 14-18pt).
_HEADING_MIN_SIZE = 13.0

# Ngưỡng phát hiện trang scan: text quá ngắn → có thể là PDF scan (cần OCR).
_SCAN_PAGE_MIN_CHARS = 50


def clean_text(text: str) -> str:
    """Lọc ký tự nguy hiểm khỏi text PDF trước khi lưu vào PostgreSQL.
    - Xóa NUL bytes (0x00) — nguyên nhân gây crash DB
    - Xóa control characters (0x01-0x08, 0x0B, 0x0C, 0x0E-0x1F)
    - Giữ lại \t \n \r vì cần cho quá trình chunking
    - Chuẩn hóa newline thừa và khoảng trắng cuối dòng
    """
    # Xóa NUL và control chars không hợp lệ (giữ \t=0x09, \n=0x0A, \r=0x0D)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # Chuẩn hóa nhiều newline liên tiếp → tối đa 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Xóa khoảng trắng thừa cuối mỗi dòng
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    return text.strip()


def extract_structure(file_path: str) -> dict:
    """Trích xuất cấu trúc tài liệu: TOC, headings, tables.

    Dùng làm input cho memory_builder (Step 6) — LLM dựa vào headings + TOC
    để sinh abstract & key_facts chính xác hơn (biết phân chia chương/section).

    Returns:
        dict với keys:
          - toc: list[dict] — table of contents [[level, title, page], ...] từ fitz
          - headings: list[dict] — [{text, page, size}, ...] text có font >= ngưỡng
          - tables: list[dict] — [{page, rows, cols}, ...] chỉ metadata, không dump data
    """
    doc = fitz.open(file_path)

    # TOC từ PDF metadata (nếu có)
    try:
        raw_toc = doc.get_toc(simple=True) or []
    except Exception:
        raw_toc = []
    toc = [
        {"level": int(item[0]), "title": str(item[1]), "page": int(item[2])}
        for item in raw_toc
        if len(item) >= 3
    ]

    # Headings: scan tất cả spans, lấy text có font size >= threshold
    headings: list[dict] = []
    for page_num in range(len(doc)):
        try:
            page_dict = doc[page_num].get_text("dict")
        except Exception:
            continue
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:  # chỉ text blocks
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = span.get("size", 0)
                    if size >= _HEADING_MIN_SIZE:
                        text = span.get("text", "").strip()
                        # Heading hợp lệ: 5-200 ký tự, có chữ (không phải số/space thuần)
                        if 5 < len(text) < 200 and re.search(r"\w", text):
                            headings.append({
                                "text": text,
                                "page": page_num + 1,
                                "size": round(size, 1),
                            })

    # Tables: pdfplumber (giữ cùng code cũ, chỉ lấy metadata để tiết kiệm memory)
    tables: list[dict] = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    for t in page.extract_tables() or []:
                        if t and len(t) > 1 and t[0]:
                            tables.append({
                                "page": page_num + 1,
                                "rows": len(t),
                                "cols": len(t[0]),
                            })
                except Exception:
                    continue
    except Exception:
        pass

    return {"toc": toc, "headings": headings, "tables": tables}


def parse_pdf(file_path: str) -> dict:
    """Parse PDF — trả về full text + per-page text + structure (TOC/headings/tables).

    Step 5 mở rộng: thêm `is_scanned` flag cho mỗi page (text < 50 chars = scanned).
    OCR thật sự (pytesseract) là phase 2; hiện tại chỉ log warning để admin biết.
    """
    doc = fitz.open(file_path)
    pages_text = []
    full_text = ""
    scanned_page_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = clean_text(page.get_text("text"))
        is_scanned = len(text.strip()) < _SCAN_PAGE_MIN_CHARS
        if is_scanned:
            scanned_page_count += 1
        pages_text.append({
            "page": page_num + 1,
            "text": text,
            "is_scanned": is_scanned,
        })
        full_text += f"\n[Trang {page_num + 1}]\n{text}"

    metadata = doc.metadata or {}

    # Cảnh báo nếu quá nhiều trang scan (chưa OCR → memory sẽ nghèo)
    total = len(doc)
    if total > 0 and scanned_page_count / total > 0.3:
        import logging
        logging.getLogger(__name__).warning(
            "PDF %s có %d/%d trang scan (>30%%). Nên chạy OCR trước khi upload.",
            file_path, scanned_page_count, total,
        )

    # Trích xuất cấu trúc (TOC + headings + tables metadata)
    try:
        structure = extract_structure(file_path)
    except Exception:
        structure = {"toc": [], "headings": [], "tables": []}

    return {
        "full_text": full_text.strip(),
        "pages": pages_text,
        "total_pages": total,
        "structure": structure,
        "scanned_page_count": scanned_page_count,
        "metadata": {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "creation_date": metadata.get("creationDate", ""),
        }
    }


def extract_tables(file_path: str) -> list:
    """Backward-compat: dump full table data (dùng cho export/debug)."""
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            for table in page.extract_tables():
                if table and len(table) > 1:
                    tables.append({"page": page_num + 1, "data": table})
    return tables
