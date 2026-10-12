import re
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
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
    # TOC từ PDF metadata (nếu có)
    raw_toc = []
    headings: list[dict] = []
    with fitz.open(file_path) as doc:
        try:
            raw_toc = doc.get_toc(simple=True) or []
        except Exception:
            raw_toc = []

        # Headings: scan tất cả spans, lấy text có font size >= threshold
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

    toc = [
        {"level": int(item[0]), "title": str(item[1]), "page": int(item[2])}
        for item in raw_toc
        if len(item) >= 3
    ]

    # Tables: pdfplumber (giữ cùng code cũ, chỉ lấy metadata để tiết kiệm memory, tối đa 30 trang đầu)
    tables: list[dict] = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages[:30]):
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


# Prompt chuyên dụng cho số hóa tài liệu học thuật qua Vision OCR
ACADEMIC_OCR_PROMPT = """Bạn là một chuyên gia số hóa tài liệu học thuật và bài báo y văn tâm lý học.
Nhiệm vụ của bạn là chuyển đổi hình ảnh trang tài liệu này thành văn bản Markdown chuẩn xác 100%:

1. BỐ CỤC: Nếu tài liệu trình bày dạng 2 cột hoặc nhiều cột, hãy đọc tuần tự trọn vẹn từng cột từ trên xuống dưới (đọc hết cột 1 rồi mới sang cột 2), tuyệt đối không đọc tràn ngang làm lẫn lộn câu từ giữa hai cột.
2. ĐỀ MỤC: Nhận diện và giữ đúng phân cấp tiêu đề (# cho Tiêu đề chính, ## cho Mục lớn, ### cho Tiểu mục).
3. BẢNG BIỂU: Chuyển đổi chính xác các bảng dữ liệu thành bảng Markdown (| Cột 1 | Cột 2 |), giữ nguyên toàn bộ số liệu thống kê (p, F, t, N, r, độ lệch chuẩn SD, giá trị p-value).
4. THUẬT NGỮ & CÔNG THỨC: Giữ nguyên thuật ngữ khoa học/tâm lý học song ngữ và các công thức toán học/thống kê.
5. TRUNG THỰC: Trích xuất nguyên văn, không tự ý tóm tắt, không thêm suy đoán, không bổ sung lời dẫn hay bình luận."""


import json
from pathlib import Path

# Bộ nhớ đệm SHA-256 cấp trang: băm ảnh -> văn bản Markdown OCR (0.01ms truy xuất, chống lặp API)
_PAGE_IMAGE_OCR_CACHE: dict[str, str] = {}
_OCR_CACHE_FILE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ocr_cache.json"


def _load_ocr_cache():
    global _PAGE_IMAGE_OCR_CACHE
    try:
        if _OCR_CACHE_FILE.exists():
            with open(_OCR_CACHE_FILE, "r", encoding="utf-8") as f:
                _PAGE_IMAGE_OCR_CACHE.update(json.load(f))
    except Exception:
        pass


def _save_ocr_cache():
    try:
        _OCR_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_OCR_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_PAGE_IMAGE_OCR_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


_load_ocr_cache()


def ocr_page_image(page, dpi: int = 150) -> tuple[str, float, bool]:
    """Render trang PDF thành ảnh và thực hiện nhận dạng quang học qua Gemini Vision API.
    
    Returns:
        tuple (ocr_text, latency_ms, is_cache_hit)
    """
    t0 = time.perf_counter()
    try:
        from app.services.llm_client import get_default_client
        client = get_default_client()
        if not client.api_key:
            return "", round((time.perf_counter() - t0) * 1000, 2), False

        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("jpeg")
        img_hash = hashlib.sha256(img_bytes).hexdigest()

        # Kiểm tra Cache băm ảnh
        if img_hash in _PAGE_IMAGE_OCR_CACHE:
            cached_text = _PAGE_IMAGE_OCR_CACHE[img_hash]
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            return cached_text, latency_ms, True

        ocr_result = client.complete_image(
            image_data=img_bytes,
            prompt=ACADEMIC_OCR_PROMPT,
            max_tokens=2048,
            temperature=0.1,
        )
        res_text = ocr_result.strip() if ocr_result else ""
        if res_text and not res_text.startswith("[Hình ảnh — API lỗi") and not res_text.startswith("[Hình ảnh — không thể"):
            _PAGE_IMAGE_OCR_CACHE[img_hash] = res_text
            _save_ocr_cache()
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            return res_text, latency_ms, False
        else:
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            return "", latency_ms, False
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("OCR failed for page %s: %s", getattr(page, "number", "?"), e)
        return "", round((time.perf_counter() - t0) * 1000, 2), False


def extract_headings_from_markdown(text: str, page_num: int) -> list[dict]:
    """Trích xuất các đề mục từ văn bản Markdown thu được qua OCR (#, ##, ###)."""
    headings = []
    for line in text.splitlines():
        line = line.strip()
        match = re.match(r'^(#{1,3})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            h_text = match.group(2).strip()
            simulated_size = 18.0 if level == 1 else (15.0 if level == 2 else 13.5)
            if 3 < len(h_text) < 200:
                headings.append({
                    "text": h_text,
                    "page": page_num,
                    "size": simulated_size,
                })
    return headings


def parse_pdf(file_path: str, enable_ocr: bool = True, max_ocr_workers: int = 5) -> dict:
    """Parse PDF — trả về full text + per-page text + structure (TOC/headings/tables).

    Tích hợp Multi-Engine Auto-Recovery Ingestion chuẩn xác từng mili giây:
    - Bóc tách siêu tốc với PyMuPDF (fast text layer).
    - Tự động kích hoạt Multimodal Vision OCR song song đa luồng (ThreadPoolExecutor) cho trang scan.
    - Caching trang cấp SHA-256 (truy xuất < 0.1ms).
    - Đo lường độ trễ chuẩn xác cao bằng time.perf_counter().
    """
    t_start = time.perf_counter()
    pages_text = []
    scanned_indices = []
    metadata = {}
    total = 0

    with fitz.open(file_path) as doc:
        total = len(doc)
        metadata = doc.metadata or {}

        # Giai đoạn 1: Quét nhanh văn bản số trên toàn bộ tài liệu (Fast-path)
        for page_num in range(total):
            page = doc[page_num]
            text = clean_text(page.get_text("text"))
            is_scanned = len(text.strip()) < _SCAN_PAGE_MIN_CHARS
            if is_scanned:
                scanned_indices.append(page_num)

            pages_text.append({
                "page": page_num + 1,
                "text": text,
                "is_scanned": is_scanned,
                "ocr_applied": False,
                "ocr_latency_ms": 0.0,
                "cache_hit": False,
            })

        scanned_page_count = len(scanned_indices)
        ocr_recovered_count = 0
        cache_hits = 0
        ocr_headings = []
        t_ocr_start = time.perf_counter()

        # Giai đoạn 2: Phục hồi song song các trang scan qua Multimodal Vision OCR (Parallel Auto-Recovery)
        if scanned_indices and enable_ocr:
            def _process_single_page(idx: int):
                # Render pixmap trực tiếp từ trang
                with fitz.open(file_path) as sub_doc:
                    p = sub_doc[idx]
                    return idx, ocr_page_image(p)

            # Thực thi đa luồng đồng thời tối đa 5 workers
            workers = min(max_ocr_workers, len(scanned_indices))
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(_process_single_page, p_idx) for p_idx in scanned_indices]
                for future in futures:
                    idx, (ocr_text, lat_ms, is_hit) = future.result()
                    if is_hit:
                        cache_hits += 1
                    if ocr_text and len(ocr_text.strip()) >= _SCAN_PAGE_MIN_CHARS:
                        cleaned = clean_text(ocr_text)
                        pages_text[idx]["text"] = cleaned
                        pages_text[idx]["ocr_applied"] = True
                        pages_text[idx]["ocr_latency_ms"] = lat_ms
                        pages_text[idx]["cache_hit"] = is_hit
                        ocr_recovered_count += 1
                        ocr_headings.extend(extract_headings_from_markdown(cleaned, idx + 1))

        t_ocr_duration_ms = round((time.perf_counter() - t_ocr_start) * 1000, 2)

    # Ghép toàn văn tài liệu
    full_text = "\n".join(f"[Trang {p['page']}]\n{p['text']}" for p in pages_text).strip()

    # Trích xuất cấu trúc (TOC + headings + tables metadata)
    try:
        structure = extract_structure(file_path)
    except Exception:
        structure = {"toc": [], "headings": [], "tables": []}

    # Bổ sung các đề mục nhận diện được từ OCR
    if ocr_headings:
        structure.setdefault("headings", []).extend(ocr_headings)

    total_duration_ms = round((time.perf_counter() - t_start) * 1000, 2)

    # Cảnh báo nếu số trang scan chưa thể phục hồi qua OCR quá lớn (>30%)
    unrecovered_scanned = scanned_page_count - ocr_recovered_count
    if total > 0 and unrecovered_scanned / total > 0.3:
        import logging
        logging.getLogger(__name__).warning(
            "PDF %s có %d/%d trang scan chưa thể phục hồi qua OCR (>30%%).",
            file_path, unrecovered_scanned, total,
        )

    return {
        "full_text": full_text,
        "pages": pages_text,
        "total_pages": total,
        "structure": structure,
        "scanned_page_count": scanned_page_count,
        "ocr_recovered_count": ocr_recovered_count,
        "ocr_cache_hits": cache_hits,
        "telemetry": {
            "total_duration_ms": total_duration_ms,
            "ocr_duration_ms": t_ocr_duration_ms,
            "parallel_workers": min(max_ocr_workers, len(scanned_indices)) if scanned_indices else 0,
        },
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
