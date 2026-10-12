import os
import re
import uuid
import logging
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from sqlalchemy.orm import Session
from app.models.document import DocumentFigure
from app.core.config import settings

logger = logging.getLogger(__name__)

# Thư mục lưu trữ hình ảnh/sơ đồ trích xuất
FIGURES_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage", "figures")
os.makedirs(FIGURES_STORAGE_DIR, exist_ok=True)

CAPTION_REGEX = re.compile(
    r'^(?:Figure|Fig\.|Hình|Sơ đồ|Table|Bảng)\s*([0-9A-Za-z.-]+)[\s.:\-–—]',
    re.IGNORECASE
)


def extract_and_save_figures(file_path: str, document_id: str, db: Session, max_pages: int = 60) -> List[Dict[str, Any]]:
    """Trích xuất tự động toàn bộ sơ đồ, biểu đồ, hình ảnh và bảng biểu từ tài liệu PDF.
    
    Thuật toán:
    1. Quét từng trang PDF, tìm các Caption đề mục (Figure 1, Hình 1, Sơ đồ 1, Table 1, Bảng 1).
    2. Xác định vùng bounding box chứa vector drawings hoặc raster images tương ứng với Caption.
    3. Render vùng ảnh với DPI cao (160 DPI) và lưu file ảnh PNG/WebP vào backend/storage/figures/{document_id}/.
    4. Lưu metadata vào bảng document_figures trong PostgreSQL.
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found for figure extraction: {file_path}")
        return []

    doc_storage_dir = os.path.join(FIGURES_STORAGE_DIR, str(document_id))
    os.makedirs(doc_storage_dir, exist_ok=True)

    extracted_figures = []

    try:
        with fitz.open(file_path) as doc:
            total_pages = min(len(doc), max_pages)

            for page_idx in range(total_pages):
                page_num = page_idx + 1
                page = doc[page_idx]
                page_rect = page.rect
                blocks = page.get_text("dict").get("blocks", [])

                # 1. Thu thập tất cả các Caption blocks trên trang
                captions = []
                for b in blocks:
                    if b.get("type") == 0:  # Text block
                        text = " ".join(
                            span.get("text", "")
                            for line in b.get("lines", [])
                            for span in line.get("spans", [])
                        ).strip()
                        m = CAPTION_REGEX.match(text)
                        if m:
                            fig_type = "table" if text.lower().startswith(("table", "bảng")) else "figure"
                            captions.append({
                                "text": text,
                                "type": fig_type,
                                "bbox": fitz.Rect(b["bbox"]),
                            })

                # 2. Thu thập vector drawings và raster images
                drawings = page.get_drawings() or []
                img_blocks = [
                    fitz.Rect(b["bbox"])
                    for b in blocks
                    if b.get("type") == 1 and (b["bbox"][2] - b["bbox"][0] > 70 and b["bbox"][3] - b["bbox"][1] > 70)
                ]

                # 3. Kết hợp Caption với khối hình ảnh/đồ họa tương ứng
                used_rects = set()
                fig_counter = 1

                for cap in captions:
                    cap_rect = cap["bbox"]
                    is_table = cap["type"] == "table"

                    # Tìm các drawings hoặc images nằm lân cận caption
                    candidate_rects = []

                    # Thông thường:
                    # - Figure: Ảnh nằm TRÊN caption (trong khoảng cách 450pt)
                    # - Table: Bảng nằm DƯỚI caption (trong khoảng cách 450pt)
                    for d in drawings:
                        r = fitz.Rect(d["rect"])
                        if r.width < 15 or r.height < 15:
                            continue
                        if is_table:
                            # Table nằm phía dưới caption
                            if cap_rect.y1 - 5 <= r.y0 <= cap_rect.y1 + 450:
                                if not (r.x1 < cap_rect.x0 - 60 or r.x0 > cap_rect.x1 + 60):
                                    candidate_rects.append(r)
                        else:
                            # Figure nằm phía trên caption
                            if cap_rect.y0 - 450 <= r.y1 <= cap_rect.y0 + 10:
                                if not (r.x1 < cap_rect.x0 - 60 or r.x0 > cap_rect.x1 + 60):
                                    candidate_rects.append(r)

                    for ir in img_blocks:
                        if is_table:
                            if cap_rect.y1 - 5 <= ir.y0 <= cap_rect.y1 + 450:
                                candidate_rects.append(ir)
                        else:
                            if cap_rect.y0 - 450 <= ir.y1 <= cap_rect.y0 + 10:
                                candidate_rects.append(ir)

                    if candidate_rects:
                        # Gom nhóm bounding box của toàn bộ sơ đồ/hình ảnh
                        fig_rect = candidate_rects[0]
                        for cr in candidate_rects[1:]:
                            fig_rect = fig_rect | cr

                        # Thêm margin 6pt xung quanh
                        fig_rect = fitz.Rect(
                            max(page_rect.x0, fig_rect.x0 - 6),
                            max(page_rect.y0, fig_rect.y0 - 6),
                            min(page_rect.x1, fig_rect.x1 + 6),
                            min(page_rect.y1, fig_rect.y1 + 6),
                        )

                        if fig_rect.width >= 60 and fig_rect.height >= 50:
                            rect_key = (round(fig_rect.x0), round(fig_rect.y0), round(fig_rect.x1), round(fig_rect.y1))
                            if rect_key not in used_rects:
                                used_rects.add(rect_key)
                                img_filename = f"p{page_num}_{cap['type']}_{fig_counter}.png"
                                img_path = os.path.join(doc_storage_dir, img_filename)

                                pix = page.get_pixmap(clip=fig_rect, dpi=160)
                                pix.save(img_path)

                                # Lưu record vào DB
                                clean_caption = cap["text"][:300].strip()
                                fig_record = DocumentFigure(
                                    document_id=uuid.UUID(str(document_id)),
                                    page_number=page_num,
                                    figure_type=cap["type"],
                                    caption=clean_caption,
                                    image_filename=img_filename,
                                    bbox=f"{fig_rect.x0:.1f},{fig_rect.y0:.1f},{fig_rect.x1:.1f},{fig_rect.y1:.1f}",
                                )
                                db.add(fig_record)
                                db.flush()

                                extracted_figures.append({
                                    "id": str(fig_record.id),
                                    "page_number": page_num,
                                    "figure_type": cap["type"],
                                    "caption": clean_caption,
                                    "image_filename": img_filename,
                                    "url": f"/api/v1/document/{document_id}/figures/{img_filename}",
                                })
                                fig_counter += 1

                # 4. Fallback: Nếu trang có ảnh raster độc lập kích thước lớn (không kèm caption)
                for ir in img_blocks:
                    if ir.width >= 160 and ir.height >= 120:
                        rect_key = (round(ir.x0), round(ir.y0), round(ir.x1), round(ir.y1))
                        if rect_key not in used_rects:
                            used_rects.add(rect_key)
                            img_filename = f"p{page_num}_diagram_{fig_counter}.png"
                            img_path = os.path.join(doc_storage_dir, img_filename)

                            pix = page.get_pixmap(clip=ir, dpi=160)
                            pix.save(img_path)

                            fig_record = DocumentFigure(
                                document_id=uuid.UUID(str(document_id)),
                                page_number=page_num,
                                figure_type="figure",
                                caption=f"Hình ảnh / Sơ đồ tại Trang {page_num}",
                                image_filename=img_filename,
                                bbox=f"{ir.x0:.1f},{ir.y0:.1f},{ir.x1:.1f},{ir.y1:.1f}",
                            )
                            db.add(fig_record)
                            db.flush()

                            extracted_figures.append({
                                "id": str(fig_record.id),
                                "page_number": page_num,
                                "figure_type": "figure",
                                "caption": f"Hình ảnh / Sơ đồ tại Trang {page_num}",
                                "image_filename": img_filename,
                                "url": f"/api/v1/document/{document_id}/figures/{img_filename}",
                            })
                            fig_counter += 1

            db.commit()
            logger.info(f"Successfully extracted {len(extracted_figures)} figures for document {document_id}")
    except Exception as e:
        logger.error(f"Error extracting figures for doc {document_id}: {e}", exc_info=True)
        db.rollback()

    return extracted_figures


def get_figures_for_chunks(chunks: List[Dict[str, Any]], db: Session) -> List[Dict[str, Any]]:
    """Tìm tất cả các hình ảnh / sơ đồ / bảng biểu tương ứng với danh sách chunks được truy xuất."""
    if not chunks:
        return []

    doc_page_pairs = set()
    doc_id_map = {}

    for c in chunks:
        doc_id = c.get("doc_id") or c.get("document_id")
        page_num = c.get("page_number")
        if doc_id and page_num:
            try:
                u_id = uuid.UUID(str(doc_id))
                doc_page_pairs.add((u_id, int(page_num)))
                doc_id_map[u_id] = c.get("doc_filename") or c.get("doc_title") or "tài liệu"
            except Exception:
                continue

    if not doc_page_pairs:
        return []

    # Truy vấn DB các hình ảnh trên đúng trang hoặc trang liền kề (page ± 1)
    results = []
    seen_ids = set()

    for u_id, p_num in doc_page_pairs:
        figures = db.query(DocumentFigure).filter(
            DocumentFigure.document_id == u_id,
            DocumentFigure.page_number.in_([p_num, p_num - 1, p_num + 1])
        ).all()

        for f in figures:
            if str(f.id) not in seen_ids:
                seen_ids.add(str(f.id))
                results.append({
                    "id": str(f.id),
                    "document_id": str(f.document_id),
                    "doc_filename": doc_id_map.get(f.document_id, "Tài liệu"),
                    "page_number": f.page_number,
                    "figure_type": f.figure_type,
                    "caption": f.caption or f"Sơ đồ trang {f.page_number}",
                    "image_filename": f.image_filename,
                    "url": f"/api/v1/document/{f.document_id}/figures/{f.image_filename}",
                })

    return results
