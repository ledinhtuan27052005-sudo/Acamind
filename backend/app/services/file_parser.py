"""
Extract text from uploaded files (PDF, DOCX, XLSX, images).
Used for inline file upload in chat — files are parsed and fed as context
into the chat LLM without being permanently stored.
"""
import io
import logging
import re
from typing import Literal

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
    """Extract text from PDF using PyMuPDF (fast, handles embedded images too)."""
    parts = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                parts.append(f"[Trang {page_num + 1}]\n{text}")
            else:
                # Page may be a scan — try to get images
                images = page.get_images(full=True)
                if images:
                    parts.append(f"[Trang {page_num + 1}] [Hình ảnh — không thể trích xuất văn bản]")

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


def _xlsx_to_text(data: bytes) -> str:
    """Extract text from XLSX — dump all sheets."""
    try:
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
        parts = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            parts.append(f"[Sheet: {sheet_name}]")
            for row in ws.iter_rows(values_only=True):
                row_text = " | ".join(str(c or "") for c in row if c is not None)
                if row_text.strip():
                    parts.append(row_text)
        text = '\n'.join(parts)
        return _clean(text)
    except Exception as e:
        logger.warning("xlsx parse error: %s", e)
        return "[Không thể đọc file Excel]"


def _image_to_text(data: bytes, ext: str) -> str:
    """Extract text from image files using Gemini Vision API (graceful fallback)."""
    try:
        from app.services.llm_client import get_default_client
        client = get_default_client()
        description = client.complete_image(
            image_data=data,
            prompt=(
                "Mô tả ngắn gọn và chi tiết nội dung của hình ảnh này bằng tiếng Việt. "
                "Trích xuất tất cả văn bản hiển thị trong ảnh (nếu có). "
                "Nếu ảnh là biểu đồ, bảng, sơ đồ, hãy mô tả chi tiết nội dung."
            ),
            max_tokens=1024,
            temperature=0.1,
        )
        return f"[Hình ảnh]\n{description}"
    except Exception as e:
        logger.warning("vision parse error (%s): %s", ext, e)
        # Graceful: trả placeholder thay vì crash
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
            return _xlsx_to_text(file_data)[:MAX_TEXT_CHARS]

        elif ext in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'):
            return _image_to_text(file_data, ext)[:MAX_TEXT_CHARS]

        else:
            return f"[Định dạng '{ext}' không được hỗ trợ. Vui lòng upload PDF, DOCX, XLSX hoặc ảnh (JPG, PNG).]"
    except Exception as e:
        logger.error("parse_file error for %s: %s", filename, e)
        return f"[Lỗi khi đọc file: {filename}]"
