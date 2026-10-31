"""
Extract text from uploaded files (PDF, DOCX, XLSX, images).
Used for inline file upload in chat — files are parsed and fed as context
into the chat LLM without being permanently stored.
"""
import io
import logging
import re
from typing import Literal

import datetime
import fitz  # PyMuPDF
import pdfplumber
import docx
import openpyxl

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 50
MAX_TEXT_CHARS = 100_000  # cap to avoid token overflow


def _clean(text: str) -> str:
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    return text.strip()


def _pdf_to_text(data: bytes) -> str:
    """Extract text from PDF using PyMuPDF (fast, handles embedded images and scanned pages with Vision OCR)."""
    parts = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip() and len(text.strip()) >= 50:
                parts.append(f"[Trang {page_num + 1}]\n{text}")
            else:
                # Trang scan hoặc text quá ngắn (< 50 chars) -> thử chạy Vision OCR
                ocr_success = False
                try:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("jpeg")
                    ocr_res = _image_to_text(img_bytes, "jpeg")
                    if ocr_res and not ocr_res.startswith("[Hình ảnh — không thể") and not ocr_res.startswith("[Hình ảnh — API lỗi"):
                        parts.append(f"[Trang {page_num + 1}] (OCR Tự động)\n{ocr_res}")
                        ocr_success = True
                except Exception as e:
                    logger.warning("Auto OCR failed in inline chat for page %d: %s", page_num + 1, e)

                if not ocr_success:
                    if text.strip():
                        parts.append(f"[Trang {page_num + 1}]\n{text}")
                    else:
                        images = page.get_images(full=True)
                        if images:
                            parts.append(f"[Trang {page_num + 1}] [Hình ảnh — không thể trích xuất văn bản tự động]")

    text = '\n\n'.join(parts)
    return _clean(text)


def _pdfplumber_fallback(data: bytes) -> str:
    """Fallback PDF parser using pdfplumber (better for tables)."""
    parts = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            tables = page.extract_tables()
            if tables:
                for t in tables:
                    if t:
                        text += "\n\n[Bảng]\n"
                        for row in t:
                            text += " | ".join(str(c or "") for c in row) + "\n"
            if text.strip():
                parts.append(f"[Trang {i}]\n{text}")

    text = '\n\n'.join(parts)
    return _clean(text)


def _docx_to_text(data: bytes) -> str:
    """Extract text from DOCX."""
    try:
        doc = docx.Document(io.BytesIO(data))
        parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                parts.append(para.text)
        text = '\n\n'.join(parts)
        return _clean(text)
    except Exception as e:
        logger.warning("docx parse error: %s", e)
        return "[Không thể đọc file DOCX]"


def _format_cell_value(val) -> str:
    """Định dạng giá trị ô Excel thành chuỗi sạch cho Markdown table."""
    if val is None:
        return ""
    if isinstance(val, (datetime.datetime, datetime.date)):
        if isinstance(val, datetime.datetime):
            if val.hour == 0 and val.minute == 0 and val.second == 0:
                return val.strftime("%Y-%m-%d")
            return val.strftime("%Y-%m-%d %H:%M")
        return val.strftime("%Y-%m-%d")
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return f"{val:.4f}".rstrip("0").rstrip(".")
    return str(val).replace("\n", " ").replace("|", "\\|").strip()


def _excel_to_sheets(data: bytes, ext: str, filename: str = "Tập tin") -> list[dict]:
    """Trích xuất từng sheet thành danh sách các dictionary:
    [{"sheet_name": str, "sheet_index": int, "text": str, "row_count": int, "col_count": int}, ...]
    Hỗ trợ xử lý thông minh:
    - Merged cells (ô gộp): lan truyền giá trị để không làm mất dữ liệu các ô con.
    - Fallback công thức: nếu data_only=True trả về None, lấy chuỗi công thức từ data_only=False.
    - Smart header: phát hiện dòng banner/tiêu đề bảng riêng biệt với dòng header các cột.
    - Multi-level header: kết hợp phân cấp nếu có nhiều tầng tiêu đề.
    """
    clean_ext = ext.lower().lstrip(".")
    sheets_out = []

    # 1. Thử đọc .xlsx bằng openpyxl
    if clean_ext == "xlsx":
        try:
            wb_val = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
            wb_form = None
            try:
                wb_form = openpyxl.load_workbook(io.BytesIO(data), data_only=False)
            except Exception:
                pass

            for sidx, sheet_name in enumerate(wb_val.sheetnames, 1):
                ws = wb_val[sheet_name]
                ws_f = wb_form[sheet_name] if wb_form and sheet_name in wb_form.sheetnames else None

                # 1.1 Unmerge & propagate values cho các ô gộp
                for rng in list(ws.merged_cells.ranges):
                    top_val = ws.cell(row=rng.min_row, column=rng.min_col).value
                    ws.unmerge_cells(str(rng))
                    for r in range(rng.min_row, rng.max_row + 1):
                        for c in range(rng.min_col, rng.max_col + 1):
                            ws.cell(row=r, column=c, value=top_val)

                # 1.2 Trích xuất toàn bộ hàng và bù đắp công thức nếu có
                all_rows = []
                for r_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
                    row_vals = []
                    for c_idx, val in enumerate(row, 1):
                        if val is None and ws_f is not None:
                            try:
                                f_val = ws_f.cell(row=r_idx, column=c_idx).value
                                if f_val is not None and str(f_val).startswith("="):
                                    val = f"[{f_val}]"
                            except Exception:
                                pass
                        row_vals.append(val)
                    all_rows.append(row_vals)

                # Lọc bỏ các hàng hoàn toàn rỗng
                non_empty_rows = [r for r in all_rows if any(c is not None and str(c).strip() != "" for c in r)]
                if not non_empty_rows:
                    continue

                # Xác định số cột tối đa thực sự có dữ liệu
                max_col = 0
                for r in non_empty_rows:
                    for c_idx in range(len(r) - 1, -1, -1):
                        if r[c_idx] is not None and str(r[c_idx]).strip() != "":
                            max_col = max(max_col, c_idx)
                            break
                col_count = max_col + 1
                if col_count == 0:
                    continue

                # Nhận diện banner tiêu đề và hàng header
                banners = []
                header_idx = 0
                for idx, r in enumerate(non_empty_rows):
                    cells = [r[c] for c in range(min(col_count, len(r)))]
                    non_empty_cells = [c for c in cells if c is not None and str(c).strip() != ""]
                    unique_vals = set(str(c).strip() for c in non_empty_cells)
                    if len(unique_vals) == 1 and col_count > 1:
                        banners.append(list(unique_vals)[0])
                    elif len(non_empty_cells) >= 2:
                        header_idx = idx
                        break

                lines = [f"### [Sheet: {sheet_name}] (Tổng số {len(non_empty_rows)} hàng, {col_count} cột)"]
                for b in banners:
                    lines.append(f"> **Tiêu đề nội dung:** {b}")

                # Kiểm tra kết hợp multi-level headers (nếu header_idx + 1 cũng toàn chuỗi)
                raw_header = non_empty_rows[header_idx] if header_idx < len(non_empty_rows) else []
                header_cells = [
                    _format_cell_value(raw_header[c] if c < len(raw_header) and raw_header[c] is not None and str(raw_header[c]).strip() != "" else f"Cột {c+1}")
                    for c in range(col_count)
                ]

                # Nếu hàng kế tiếp cũng là chữ và không phải số dữ liệu -> gộp tiêu đề phân cấp
                data_start_idx = header_idx + 1
                if header_idx + 1 < len(non_empty_rows):
                    next_row = non_empty_rows[header_idx + 1]
                    next_cells = [next_row[c] if c < len(next_row) else None for c in range(col_count)]
                    if all(isinstance(c, str) and not c.replace(".", "", 1).isdigit() for c in next_cells if c is not None):
                        combined_headers = []
                        for h1, h2 in zip(header_cells, next_cells):
                            h2_clean = _format_cell_value(h2)
                            if h1 and h2_clean and h1 != h2_clean and not h1.startswith("Cột "):
                                combined_headers.append(f"{h1} - {h2_clean}")
                            elif h2_clean:
                                combined_headers.append(h2_clean)
                            else:
                                combined_headers.append(h1)
                        header_cells = combined_headers
                        data_start_idx = header_idx + 2

                lines.append("| " + " | ".join(header_cells) + " |")
                lines.append("| " + " | ".join(["---"] * col_count) + " |")

                # Dữ liệu các hàng (giới hạn tối đa 200 hàng/sheet)
                data_rows = non_empty_rows[data_start_idx:]
                for r in data_rows[:200]:
                    cells = [
                        _format_cell_value(r[c] if c < len(r) else "")
                        for c in range(col_count)
                    ]
                    lines.append("| " + " | ".join(cells) + " |")

                if len(data_rows) > 200:
                    lines.append(f"... (Đã hiển thị 200/{len(data_rows)} hàng dữ liệu của sheet '{sheet_name}')")

                sheets_out.append({
                    "sheet_name": sheet_name,
                    "sheet_index": sidx,
                    "text": "\n".join(lines),
                    "row_count": len(non_empty_rows),
                    "col_count": col_count,
                })

            if sheets_out:
                return sheets_out
        except Exception as e:
            logger.warning("openpyxl parse error: %s. Thử fallback pandas/xlrd...", e)

    # 2. Fallback pandas hoặc xlrd cho .xls hoặc khi openpyxl gặp lỗi
    try:
        import pandas as pd
        excel_dict = pd.read_excel(io.BytesIO(data), sheet_name=None)
        sidx = 0
        for sheet_name, df in excel_dict.items():
            sidx += 1
            if df.empty:
                continue

            col_count = len(df.columns)
            row_count = len(df)
            lines = [f"### [Sheet: {sheet_name}] (Tổng số {row_count} hàng, {col_count} cột)"]

            cols = [_format_cell_value(c) for c in df.columns]
            lines.append("| " + " | ".join(cols) + " |")
            lines.append("| " + " | ".join(["---"] * col_count) + " |")

            for _, row in df.iloc[:200].iterrows():
                cells = [_format_cell_value(row[c] if pd.notna(row[c]) else "") for c in df.columns]
                lines.append("| " + " | ".join(cells) + " |")

            if row_count > 200:
                lines.append(f"... (Đã hiển thị 200/{row_count} hàng dữ liệu của sheet '{sheet_name}')")

            sheets_out.append({
                "sheet_name": str(sheet_name),
                "sheet_index": sidx,
                "text": "\n".join(lines),
                "row_count": row_count,
                "col_count": col_count,
            })

        if sheets_out:
            return sheets_out
    except Exception as e:
        logger.warning("pandas excel fallback parse error: %s", e)

    # 3. Fallback cuối cùng bằng xlrd thuần
    try:
        import xlrd
        book = xlrd.open_workbook(file_contents=data)
        for sidx, sheet_name in enumerate(book.sheet_names(), 1):
            sh = book.sheet_by_name(sheet_name)
            if sh.nrows == 0 or sh.ncols == 0:
                continue

            lines = [f"### [Sheet: {sheet_name}] (Tổng số {sh.nrows} hàng, {sh.ncols} cột)"]
            col_count = sh.ncols

            header_cells = [
                _format_cell_value(sh.cell_value(0, c) if sh.cell_value(0, c) != "" else f"Cột {c+1}")
                for c in range(col_count)
            ]
            lines.append("| " + " | ".join(header_cells) + " |")
            lines.append("| " + " | ".join(["---"] * col_count) + " |")

            for r_idx in range(1, min(sh.nrows, 201)):
                cells = [
                    _format_cell_value(sh.cell_value(r_idx, c) if sh.cell_value(r_idx, c) is not None else "")
                    for c in range(col_count)
                ]
                lines.append("| " + " | ".join(cells) + " |")

            if sh.nrows > 201:
                lines.append(f"... (Đã hiển thị 200/{sh.nrows} hàng của sheet '{sheet_name}')")

            sheets_out.append({
                "sheet_name": str(sheet_name),
                "sheet_index": sidx,
                "text": "\n".join(lines),
                "row_count": sh.nrows,
                "col_count": col_count,
            })
        if sheets_out:
            return sheets_out
    except Exception as e:
        logger.warning("xlrd direct parse error: %s", e)

    return []


def _excel_to_text(data: bytes, ext: str, filename: str = "Tập tin") -> str:
    """Trích xuất dữ liệu đa sheet từ tệp Excel (hỗ trợ cả .xlsx và .xls cũ).
    Đính kèm mục lục cấu trúc tất cả Sheet ở đầu để LLM nắm được bản đồ tổng thể.
    """
    sheets = _excel_to_sheets(data, ext, filename)
    if not sheets:
        return "[Không thể đọc dữ liệu từ file Excel này]"

    parts = []
    # Nếu file có nhiều sheet, bổ sung bản mục lục tổng quan
    if len(sheets) > 1:
        overview_lines = [
            f"### 📑 TỔNG QUAN TÀI LIỆU EXCEL (Gồm {len(sheets)} Sheet):"
        ]
        for s in sheets:
            overview_lines.append(f"- Sheet {s['sheet_index']}: **{s['sheet_name']}** ({s['row_count']} hàng, {s['col_count']} cột)")
        parts.append("\n".join(overview_lines))

    for s in sheets:
        parts.append(s["text"])

    return _clean("\n\n---\n\n".join(parts))


def _image_to_text(data: bytes, ext: str) -> str:
    """Trích xuất chi tiết hình ảnh bằng nhà cung cấp OCR/vision đã cấu hình.
    Hỗ trợ OCR văn bản, phân tích bảng biểu Markdown, giải thích sơ đồ, đồ thị nghiên cứu.
    """
    try:
        from app.services.llm_client import get_ocr_client
        client = get_ocr_client()
        clean_ext = ext.lower().lstrip(".")
        mime_map = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "gif": "image/gif",
            "bmp": "image/bmp",
        }
        mime_type = mime_map.get(clean_ext, "image/jpeg")

        description = client.complete_image(
            image_data=data,
            prompt=(
                "Bạn là chuyên gia phân tích tài liệu học thuật, số liệu nghiên cứu và hình ảnh y tế / tâm lý học. "
                "Hãy phân tích hình ảnh tài liệu học thuật bằng tiếng Việt và chỉ nêu nội dung nhìn thấy được:\n"
                "1. Trích nguyên văn tiêu đề, nhãn, chú thích và các số liệu đọc rõ ràng; đánh dấu phần mờ/không đọc được thay vì tự đoán.\n"
                "2. Với bảng, tái hiện cấu trúc và số liệu đọc được dưới dạng Markdown; không tự điền ô thiếu.\n"
                "3. Với biểu đồ, nêu loại biểu đồ, trục, đơn vị, nhãn, xu hướng. Nếu ước lượng giá trị từ vị trí/độ cao của điểm trên hình, ghi rõ là ƯỚC LƯỢNG và không trình bày như số liệu trích xuất chính xác.\n"
                "4. Phân biệt quan sát trực tiếp với diễn giải; nếu hình không đủ rõ để kết luận, nói rõ giới hạn đó."
            ),
            max_tokens=4096,
            temperature=0.1,
            mime_type=mime_type,
        )
        return f"[Hình ảnh: {ext.upper()}]\n{description}"
    except Exception as e:
        logger.warning("vision parse error (%s): %s", ext, e)
        return "[Hình ảnh — không thể trích xuất nội dung tự động. Vui lòng mô tả nội dung ảnh trong câu hỏi của bạn để tôi có thể hỗ trợ tốt hơn.]"


def parse_file(file_data: bytes, filename: str) -> str:
    """Parse a file and return its text content."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    try:
        if ext == 'pdf':
            text = _pdf_to_text(file_data)
            if not text.strip():
                text = _pdfplumber_fallback(file_data)
            return text[:MAX_TEXT_CHARS] if text else "[File PDF trống]"

        elif ext in ('docx', 'doc'):
            return _docx_to_text(file_data)[:MAX_TEXT_CHARS]

        elif ext in ('xlsx', 'xls'):
            return _excel_to_text(file_data, ext, filename)[:MAX_TEXT_CHARS]

        elif ext in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'):
            return _image_to_text(file_data, ext)[:MAX_TEXT_CHARS]

        else:
            return f"[Định dạng '{ext}' không được hỗ trợ. Vui lòng upload PDF, DOCX, XLSX, XLS hoặc ảnh (JPG, PNG, WEBP).]"
    except Exception as e:
        logger.error("parse_file error for %s: %s", filename, e)
        return f"[Lỗi khi đọc file: {filename}]"


def parse_file_chunks(file_data: bytes, filename: str, analyze_visuals: bool = False, max_visual_pages: int = 1) -> list[dict]:
    """Phân tách file tải lên thành các chunk có cấu trúc (đặc biệt tách từng Sheet cho Excel),
    giúp LLM trích dẫn chính xác theo từng Sheet/trang và bao quát toàn bộ dữ liệu.
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if ext in ('xlsx', 'xls'):
        sheets = _excel_to_sheets(file_data, ext, filename)
        if not sheets:
            return [{
                "content": f"[Tệp Excel: {filename}]\n[Không thể đọc dữ liệu từ file Excel này]",
                "document_id": "inline_file",
                "doc_filename": filename,
                "doc_title": filename,
                "page_number": "Sheet 1",
                "sheet_name": "Sheet 1",
            }]

        chunks = []
        # Nếu có từ 2 sheet trở lên, tạo thêm 1 chunk tổng quan mục lục
        if len(sheets) > 1:
            overview_lines = [
                f"### 📑 TỔNG QUAN CẤU TRÚC TỆP EXCEL: '{filename}' (Gồm {len(sheets)} Sheet):"
            ]
            for s in sheets:
                overview_lines.append(f"- Sheet {s['sheet_index']}: **{s['sheet_name']}** ({s['row_count']} hàng, {s['col_count']} cột)")
            overview_lines.append("\n*Lưu ý: Dữ liệu chi tiết của từng Sheet được phân bổ ở các phần tương ứng bên dưới.*")
            chunks.append({
                "content": f"[Tệp Excel: {filename} | Mục lục Sheet]\n" + "\n".join(overview_lines),
                "document_id": "inline_file",
                "doc_filename": filename,
                "doc_title": filename,
                "page_number": "Mục lục Sheet",
                "sheet_name": "Mục lục Sheet",
            })

        for s in sheets:
            chunks.append({
                "content": f"[Tệp Excel: {filename} | Sheet: {s['sheet_name']}]\n{s['text']}",
                "document_id": "inline_file",
                "doc_filename": filename,
                "doc_title": filename,
                "page_number": f"Sheet: {s['sheet_name']}",
                "sheet_name": s['sheet_name'],
            })
        return chunks

    if ext == 'pdf':
        # Keep page provenance for inline PDFs so citations can identify the
        # page that actually supplied each fact.
        chunks = []
        visual_pages_used = 0
        try:
            with fitz.open(stream=file_data, filetype="pdf") as pdf:
                for page_index, page in enumerate(pdf):
                    text = _clean(page.get_text() or "")
                    if len(text) < 50:
                        try:
                            pix = page.get_pixmap(dpi=150)
                            ocr = _image_to_text(pix.tobytes("jpeg"), "jpeg")
                            if ocr and not ocr.startswith(("[Hình ảnh — không thể", "[Hình ảnh — API lỗi")):
                                text = _clean(ocr)
                        except Exception as exc:
                            logger.warning("Inline PDF OCR failed on page %s: %s", page_index + 1, exc)
                    if text:
                        has_visual_content = bool(page.get_images(full=True)) or bool(re.search(
                            r"\b(?:figure|fig\.?|chart|graph|plot|hình|biểu đồ|bảng)\s*\d*\b",
                            text,
                            re.IGNORECASE,
                        ))
                        if analyze_visuals and has_visual_content and visual_pages_used < max_visual_pages:
                            try:
                                pix = page.get_pixmap(dpi=130, alpha=False)
                                visual_text = _image_to_text(pix.tobytes("jpeg"), "jpeg")
                                if visual_text and not visual_text.startswith(("[Hình ảnh — không thể", "[Hình ảnh — API lỗi")):
                                    text += "\n\n[Vision analysis of figure/table/graphic on this PDF page; verify any visually estimated values]\n" + _clean(visual_text)
                                visual_pages_used += 1
                            except Exception as exc:
                                logger.warning("Inline PDF visual analysis failed on page %s: %s", page_index + 1, exc)
                        chunks.append({
                            "content": text[:MAX_TEXT_CHARS],
                            "document_id": "inline_file",
                            "doc_filename": filename,
                            "doc_title": filename,
                            "page_number": page_index + 1,
                        })
            # Add machine-readable table cells to their original page context;
            # this improves comparison and chart-ready numeric extraction.
            try:
                with pdfplumber.open(io.BytesIO(file_data)) as pdf_text:
                    page_chunks = {int(c["page_number"]): c for c in chunks}
                    for page_index, page in enumerate(pdf_text.pages, start=1):
                        target = page_chunks.get(page_index)
                        if not target:
                            continue
                        rendered_tables = []
                        for table_index, table in enumerate(page.extract_tables() or [], start=1):
                            if not table or len(table) < 2:
                                continue
                            rows = [[re.sub(r"\s+", " ", str(cell or "")).strip() for cell in row] for row in table]
                            width = max((len(row) for row in rows), default=0)
                            if width < 2:
                                continue
                            rows = [row + [""] * (width - len(row)) for row in rows]
                            rendered_tables.append(
                                f"[Extracted table {table_index}, PDF page {page_index}]\n"
                                + "| " + " | ".join(rows[0]) + " |\n"
                                + "| " + " | ".join(["---"] * width) + " |\n"
                                + "\n".join("| " + " | ".join(row) + " |" for row in rows[1:])
                            )
                        if rendered_tables:
                            target["content"] += "\n\n" + "\n\n".join(rendered_tables)
            except Exception as exc:
                logger.info("Inline PDF table extraction skipped for %s: %s", filename, exc)
        except Exception as exc:
            logger.warning("Inline PDF page parsing failed for %s: %s", filename, exc)
        if chunks:
            try:
                from app.services.reference_filter import filter_reference_chunks
                filtered_inline = filter_reference_chunks(chunks)
                if filtered_inline:
                    chunks = filtered_inline
            except Exception:
                pass
            return chunks

    # Other DOCX and image files are returned as one chunk.
    text = parse_file(file_data, filename)
    return [{
        "content": f"[File: {filename}]\n{text}",
        "document_id": "inline_file",
        "doc_filename": filename,
        "doc_title": filename,
        "page_number": 1,
    }]

