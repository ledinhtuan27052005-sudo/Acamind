import uuid, os, shutil, sys, time, logging, re, io
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Depends, HTTPException, Body, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.db.postgres import get_db
from app.models.document import Document, Chunk
from app.services.parser import parse_pdf
from app.services.chunking import chunk_text
from app.services.embedder import embed_and_store
from app.core.config import settings
from app.core.security import get_optional_user, get_current_user
from app.core.plan_utils import get_limits, count_user_docs, count_monthly_docs, count_annual_docs

logger = logging.getLogger(__name__)

# Đảm bảo stdout dùng UTF-8 (fix lỗi UnicodeEncodeError trên Windows khi in path có dấu)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

router = APIRouter()


import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# Dedicated worker pool cho xử lý PDF nền để KHÔNG BAO GIỜ làm nghẽn HTTP thread pool của FastAPI
_PIPELINE_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pdf_pipeline")
_MEMORY_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="doc_memory")
_QUEUED_DOC_IDS: set[str] = set()
_QUEUED_LOCK = threading.Lock()
_NEO4J_DOWN_UNTIL: float = 0.0


def _is_neo4j_reachable() -> bool:
    global _NEO4J_DOWN_UNTIL
    now = time.time()
    if now < _NEO4J_DOWN_UNTIL:
        return False
    try:
        parsed = urlparse(settings.NEO4J_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port or 7687
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        _NEO4J_DOWN_UNTIL = now + 60.0
        return False


def _enqueue_pipeline(file_path: str, document_id: str, db_url: str) -> None:
    with _QUEUED_LOCK:
        if document_id in _QUEUED_DOC_IDS:
            return
        _QUEUED_DOC_IDS.add(document_id)
    try:
        _PIPELINE_EXECUTOR.submit(_run_pipeline, file_path, document_id, db_url)
    except Exception:
        with _QUEUED_LOCK:
            _QUEUED_DOC_IDS.discard(document_id)
        raise


def resume_pending_documents() -> None:
    """Khôi phục các tài liệu đang ở trạng thái 'processing' khi server khởi động lại."""
    from sqlalchemy import text as sql_text
    from app.db.postgres import SessionLocal
    db = SessionLocal()
    try:
        # Preserve distinct versions, including PDFs sharing a filename.
        pending_docs = (
            db.query(Document)
            .filter(Document.status.in_(["processing", "cancel_requested"]))
            .order_by(Document.created_at.asc())
            .all()
        )
        resumed = 0
        for d in pending_docs:
            if d.file_path and os.path.exists(d.file_path):
                _enqueue_pipeline(d.file_path, str(d.id), settings.POSTGRES_URL)
                resumed += 1
            else:
                d.status = "cancelled" if d.status == "cancel_requested" else "error"
        db.commit()
        if resumed > 0:
            logger.info("Resumed %d pending PDF documents in background pipeline queue.", resumed)
    except Exception as e:
        logger.warning("Failed to resume pending documents: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


def _run_pipeline(file_path: str, document_id: str, db_url: str):
    """Xử lý PDF upload trong background: parse, chunk, embed."""
    from sqlalchemy import text as sql_text
    from app.db.postgres import SessionLocal, _resolve_postgres_url
    from app.services.processing_jobs import checkpoint, ProcessingCancelled

    db_url = _resolve_postgres_url(db_url)
    db = SessionLocal()
    error_msg = None

    try:
        checkpoint(db, document_id, 'parsing')
        # Restart indexing for this document without accumulating partial chunks.
        from app.models.document import DocumentFigure
        db.query(Chunk).filter(Chunk.document_id == document_id).delete(synchronize_session=False)
        db.query(DocumentFigure).filter(DocumentFigure.document_id == document_id).delete(synchronize_session=False)
        db.execute(sql_text('DELETE FROM page_texts WHERE document_id = :did'), {'did': document_id})
        db.commit()
        # 1. Parse PDF
        parsed = parse_pdf(file_path)
        checkpoint(db, document_id, 'chunking')

        # 2. Cập nhật metadata document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.title = parsed["metadata"].get("title") or os.path.splitext(doc.filename)[0]
            doc.authors = parsed["metadata"].get("author", "")
            doc.total_pages = parsed["total_pages"]
            db.commit()
        else:
            raise ValueError(f"Document {document_id} not found in DB")

        # 3. Chunk text
        if parsed.get("ocr_recovered_count", 0) > 0:
            logger.info("Document %s: Phục hồi thành công %d trang scan qua Gemini Vision OCR", document_id, parsed["ocr_recovered_count"])

        chunks = chunk_text(parsed["full_text"], document_id, parsed["pages"])
        if not chunks:
            raise ValueError("PDF không có văn bản hợp lệ (đã kiểm tra qua PyMuPDF và Vision OCR). Vui lòng kiểm tra lại tài liệu.")

        # 4. Lưu full text từng trang vào page_texts (Mục 3: kho bộ nhớ toàn văn)
        try:
            for page_info in parsed["pages"]:
                raw_page_text = (page_info.get("text", "") or "").replace("\x00", "").strip()
                if raw_page_text:
                    db.execute(sql_text("""
                        INSERT INTO page_texts (document_id, page_number, content)
                        VALUES (:doc_id, :page, :content)
                        ON CONFLICT (document_id, page_number) DO UPDATE SET content = EXCLUDED.content
                    """), {
                        "doc_id": document_id,
                        "page": page_info["page"],
                        "content": raw_page_text,
                    })
            db.commit()
        except Exception as pt_err:
            logger.warning("Lưu page_texts thất bại cho %s: %s", document_id, pt_err)
            try:
                db.rollback()
            except Exception:
                pass

        # 5. Embed and store chunks
        checkpoint(db, document_id, 'embedding')
        embed_and_store(chunks, db)
        checkpoint(db, document_id, 'figures')

        # 7. Update Neo4j graph (optional - chỉ gọi khi Neo4j đang chạy để tránh treo 5s mỗi file)
        if _is_neo4j_reachable():
            from app.db.neo4j import insert_document_graph
            try:
                insert_document_graph(document_id, doc.title or doc.filename, doc.authors or "", doc.year or 0)
            except Exception as e:
                logger.warning("Neo4j insert failed for %s: %s", document_id, e)

        # 8. Trích xuất sơ đồ, hình ảnh & bảng biểu (Multimodal Figure Extraction)
        try:
            from app.services.figure_extractor import extract_and_save_figures
            extract_and_save_figures(file_path, document_id, db)
        except Exception as fig_err:
            logger.warning("Trích xuất sơ đồ thất bại cho %s: %s", document_id, fig_err)
            try:
                db.rollback()
            except Exception:
                pass

        # 9. Mark as ready
        checkpoint(db, document_id, 'ready')
        print(f"[INFO] [OK] Pipeline done: {document_id} - {len(chunks)} chunks")

        # 10. Chỉ tự động gọi LLM sinh L1 Memory nền khi ENABLE_AUTO_MEMORY=1 (mặc định tắt trên Ollama cục bộ
        # để không làm đầy hàng đợi Ollama gây chậm phản hồi Chatbot)
        if os.getenv("ENABLE_AUTO_MEMORY", "0") == "1":
            try:
                from app.services.memory_builder import build_memory_for_doc
                _MEMORY_EXECUTOR.submit(build_memory_for_doc, document_id, db_url)
            except Exception as mem_err:
                logger.warning("Không thể xếp hàng build_memory_for_doc cho %s: %s", document_id, mem_err)

        # 11. Nhường CPU/GIL 100ms giữa các file để HTTP server luôn phản hồi tức thì
        time.sleep(0.1)

    except ProcessingCancelled:
        logger.info('Processing cancelled or no longer active: %s', document_id)
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        print(f"[ERROR] Pipeline failed for {document_id}: {error_msg}")

        try:
            db.rollback()
        except Exception:
            pass
        db.close()

        try:
            fresh_db = SessionLocal()
            try:
                checkpoint(fresh_db, document_id, 'error')
            except ProcessingCancelled:
                pass
            finally:
                fresh_db.close()
        except Exception as cleanup_err:
            print(f"[ERROR] Failed to update error status: {cleanup_err}")
    finally:
        with _QUEUED_LOCK:
            _QUEUED_DOC_IDS.discard(document_id)
        try:
            db.close()
        except Exception:
            pass


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_docs = db.query(func.count(Document.id)).scalar() or 0
    ready_docs = db.query(func.count(Document.id)).filter(Document.status == "ready").scalar() or 0
    processing_docs = db.query(func.count(Document.id)).filter(Document.status == "processing").scalar() or 0
    total_chunks = db.query(func.count(Chunk.id)).scalar() or 0
    return {
        "total_documents": total_docs,
        "ready_documents": ready_docs,
        "processing_documents": processing_docs,
        "total_chunks": total_chunks,
    }


def _enforce_upload_quota(current_user, db: Session) -> None:
    """Kiểm tra hạn mức tải tài liệu của người dùng (nếu đã đăng nhập và không phải admin)."""
    if current_user is None or current_user.role == "admin":
        return
    limits = get_limits(current_user)
    plan = getattr(current_user, "plan", "free") or "free"

    if limits["max_docs"] is not None:
        if count_user_docs(current_user.id, db) >= limits["max_docs"]:
            raise HTTPException(
                403,
                f"❌ Gói {limits['label']} chỉ cho phép tối đa {limits['max_docs']} tài liệu. "
                "Nâng cấp để tải thêm."
            )
    elif limits["max_monthly_docs"] is not None:
        monthly = count_monthly_docs(current_user.id, db)
        if monthly >= limits["max_monthly_docs"]:
            raise HTTPException(
                403,
                f"❌ Gói {limits['label']} chỉ cho phép tối đa {limits['max_monthly_docs']} tài liệu/tháng. "
                "Bạn đã đạt giới hạn tháng này."
            )
    elif plan == "enterprise":
        from app.models.document import Organization, OrgMember
        org_as_owner = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
        if org_as_owner:
            if org_as_owner.package_type == "annual" and org_as_owner.max_annual_docs_owner:
                annual = count_annual_docs(current_user.id, db)
                if annual >= org_as_owner.max_annual_docs_owner:
                    raise HTTPException(
                        403,
                        f"❌ Gói trường giới hạn {org_as_owner.max_annual_docs_owner} tài liệu/năm. "
                        "Bạn đã đạt giới hạn năm nay."
                    )
            elif org_as_owner.max_monthly_docs_owner:
                monthly = count_monthly_docs(current_user.id, db)
                if monthly >= org_as_owner.max_monthly_docs_owner:
                    raise HTTPException(
                        403,
                        f"❌ Gói trường giới hạn {org_as_owner.max_monthly_docs_owner} tài liệu/tháng. "
                        "Bạn đã đạt giới hạn tháng này."
                    )
        else:
            member = db.query(OrgMember).filter(
                OrgMember.user_id == current_user.id, OrgMember.status == "active"
            ).first()
            if member:
                org = db.query(Organization).filter(Organization.id == member.org_id).first()
                if org and org.max_monthly_docs is not None:
                    monthly = count_monthly_docs(current_user.id, db)
                    if monthly >= org.max_monthly_docs:
                        raise HTTPException(
                            403,
                            f"❌ Tổ chức giới hạn {org.max_monthly_docs} tài liệu/tháng. "
                            "Bạn đã đạt giới hạn tháng này."
                        )


async def _save_and_enqueue_single_pdf(
    file: UploadFile,
    category: Optional[str],
    current_user,
    db: Session,
    background_tasks: BackgroundTasks,
) -> dict:
    """Lưu 1 file PDF (non-blocking) và đưa vào hàng đợi xử lý nền (_run_pipeline)."""
    import hashlib
    from starlette.concurrency import run_in_threadpool

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, f"❌ Chỉ chấp nhận file PDF ({file.filename})")

    await run_in_threadpool(_enforce_upload_quota, current_user, db)

    document_id = str(uuid.uuid4())
    safe_filename = file.filename.replace(" ", "_").replace("/", "_").replace("\\", "_")

    try:
        upload_dir = settings.get_pdf_upload_dir()
    except Exception as e:
        raise HTTPException(500, f"❌ Không thể tạo thư mục upload: {e}")

    file_path = os.path.join(upload_dir, f"{document_id}_{safe_filename}")

    max_bytes = 200 * 1024 * 1024  # 200MB
    total = 0
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    f.close()
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                    raise HTTPException(413, f"❌ File '{file.filename}' vượt quá 200MB")
                sha256.update(chunk)
                await run_in_threadpool(f.write, chunk)
    except HTTPException:
        raise
    except Exception as e:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(500, f"❌ Không thể lưu file '{file.filename}': {e}")

    if total == 0:
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(400, f"❌ File PDF trống: {file.filename}")

    content_hash = sha256.hexdigest()

    def _check_dup_and_insert_sync() -> dict:
        from app.services.study_duplicates import find_upload_duplicate
        existing_doc = find_upload_duplicate(db, content_hash, current_user.id if current_user else None)
        if existing_doc:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                pass
            if existing_doc.status == "processing" and existing_doc.file_path and os.path.exists(existing_doc.file_path):
                _enqueue_pipeline(existing_doc.file_path, str(existing_doc.id), settings.POSTGRES_URL)
            return {
                "document_id": str(existing_doc.id),
                "filename": existing_doc.filename,
                "status": existing_doc.status,
                "title": existing_doc.title,
                "has_memory": existing_doc.has_memory,
                "message": f"✓ File đã tồn tại (doc cũ: {existing_doc.title or existing_doc.filename}). Trả về document cũ.",
                "duplicate": True,
            }

        try:
            user_id = current_user.id if current_user else None
            doc = Document(
                id=document_id,
                filename=file.filename,
                file_path=file_path,
                status="processing",
                user_id=user_id,
                category=category,
                content_hash=content_hash,
            )
            db.add(doc)
            db.commit()
        except Exception as e:
            db.rollback()
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                pass
            raise HTTPException(500, f"❌ Lỗi lưu database cho '{file.filename}': {e}")

        _enqueue_pipeline(file_path, document_id, settings.POSTGRES_URL)
        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "processing",
            "duplicate": False,
            "message": "✓ File uploaded. Processing in background...",
        }

    return await run_in_threadpool(_check_dup_and_insert_sync)


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    files: Optional[list[UploadFile]] = File(None),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Upload 1 hoặc nhiều file PDF và xử lý trong background."""
    upload_list: list[UploadFile] = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)
    if not upload_list:
        raise HTTPException(400, "❌ Vui lòng chọn ít nhất 1 file PDF để tải lên")

    if len(upload_list) == 1:
        return await _save_and_enqueue_single_pdf(upload_list[0], category, current_user, db, background_tasks)

    results = []
    errors = []
    for item in upload_list:
        try:
            res = await _save_and_enqueue_single_pdf(item, category, current_user, db, background_tasks)
            results.append(res)
        except HTTPException as he:
            errors.append({"filename": item.filename, "error": he.detail, "status": "error"})
        except Exception as exc:
            errors.append({"filename": item.filename, "error": str(exc), "status": "error"})

    if not results and errors:
        raise HTTPException(400, errors[0]["error"])

    first = results[0]
    return {
        "document_id": first["document_id"],
        "filename": first["filename"],
        "status": first["status"],
        "total_uploaded": len(results),
        "total_errors": len(errors),
        "documents": results,
        "errors": errors,
        "message": f"✓ Đã tải lên {len(results)}/{len(upload_list)} tài liệu. Đang xử lý nền...",
    }


@router.post("/upload-multiple")
async def upload_multiple_documents(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Upload đồng thời nhiều tài liệu PDF (Batch Upload) và xử lý trong background."""
    if not files:
        raise HTTPException(400, "❌ Vui lòng chọn ít nhất 1 file PDF để tải lên")

    results = []
    errors = []
    for item in files:
        try:
            res = await _save_and_enqueue_single_pdf(item, category, current_user, db, background_tasks)
            results.append(res)
        except HTTPException as he:
            errors.append({"filename": item.filename, "error": he.detail, "status": "error"})
        except Exception as exc:
            errors.append({"filename": item.filename, "error": str(exc), "status": "error"})

    if not results and errors:
        raise HTTPException(400, errors[0]["error"])

    return {
        "total_uploaded": len(results),
        "total_errors": len(errors),
        "documents": results,
        "errors": errors,
        "message": f"✓ Đã tải lên {len(results)}/{len(files)} tài liệu. Đang xử lý nền...",
    }


@router.get("/categories")
def list_categories_public(db: Session = Depends(get_db)):
    """Public endpoint — trả về danh sách phân loại từ DB."""
    from app.models.document import DocumentCategory
    cats = db.query(DocumentCategory).order_by(DocumentCategory.name).all()
    return [{"id": str(c.id), "name": c.name, "color": c.color} for c in cats]


@router.get("/list")
def list_documents(db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    from app.core.document_access import visible_documents
    query = visible_documents(db.query(Document), current_user)

    docs = query.order_by(Document.created_at.desc()).all()
    return {
        "total": len(docs),
        "documents": [
            {
                "id": str(d.id),
                "filename": d.filename,
                "title": d.title,
                "authors": d.authors,
                "year": d.year,
                "total_pages": d.total_pages,
                "status": d.status,
                "category": d.category,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "user_id": str(d.user_id) if d.user_id else None,
                # Cho frontend biết user có quyền sửa/xóa tài liệu này không
                "is_owner": (
                    current_user is not None and (
                        current_user.role == "admin" or
                        (d.user_id is not None and str(d.user_id) == str(current_user.id))
                    )
                ),
                # Phase A: cờ memory đã build xong chưa (cho UI badge + filter nhanh)
                "has_memory": bool(getattr(d, "has_memory", False)),
                "memory_status": getattr(d, "memory_status", "pending"),
            }
            for d in docs
        ],
    }


@router.get("/lookup")
def lookup_document(
    q: Optional[str] = Query(None),
    filename: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Tìm nhanh document theo filename/title phục vụ việc nhảy trang citation (Nhóm 4)."""
    target = (q or filename or title or "").strip()
    if not target:
        raise HTTPException(400, "Vui lòng nhập từ khóa tìm kiếm")

    # Loại bỏ đuôi .pdf nếu có để so sánh linh hoạt
    clean_target = re.sub(r'\.pdf$', '', target, flags=re.IGNORECASE).strip()

    from app.core.document_access import visible_documents
    query = visible_documents(db.query(Document), current_user)

    doc = query.filter(
        or_(
            Document.filename == target,
            Document.filename.ilike(f"%{clean_target}%"),
            Document.title.ilike(f"%{clean_target}%"),
        )
    ).first()

    if not doc:
        raise HTTPException(404, f"Không tìm thấy tài liệu phù hợp với '{target}'")

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "title": doc.title,
        "total_pages": doc.total_pages,
        "authors": doc.authors,
        "year": doc.year,
        "has_file": bool(doc.file_path and os.path.exists(doc.file_path)),
    }


def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def _enforce_doc_read_access(doc: Document, current_user, db: Session) -> None:
    from app.core.document_access import enforce_document_read
    enforce_document_read(doc, current_user, db)


@router.get("/{document_id}/file")
def get_document_file(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Serve PDF file — inline for viewing, supports download via browser."""
    if not _is_valid_uuid(document_id):
        raise HTTPException(404, "Mã tài liệu không hợp lệ")
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    _enforce_doc_read_access(doc, current_user, db)

    if not os.path.exists(doc.file_path):
        logger.error(f"Document file not found: {doc.file_path} for doc_id={document_id}")
        raise HTTPException(404, f"File không còn tồn tại trên server: {doc.filename}")

    from urllib.parse import quote
    encoded_filename = quote(doc.filename)
    return FileResponse(
        doc.file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"},
    )


@router.get("/{document_id}/highlighted-file")
def get_highlighted_document_file(
    document_id: str,
    page: Optional[int] = Query(None, description="Trang cần highlight (1-indexed)"),
    highlight: Optional[str] = Query(None, description="Đoạn văn trích dẫn hoặc từ khóa cần highlight"),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Serve PDF file đã được nhúng lớp highlight màu vàng trực tiếp tại đoạn văn trích dẫn."""
    if not _is_valid_uuid(document_id):
        raise HTTPException(404, "Mã tài liệu không hợp lệ")
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    _enforce_doc_read_access(doc, current_user, db)

    if not os.path.exists(doc.file_path):
        raise HTTPException(404, f"File không còn tồn tại trên server: {doc.filename}")

    from urllib.parse import quote
    encoded_filename = quote(doc.filename)

    return FileResponse(
        doc.file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"},
    )


@router.get("/{document_id}/highlight-meta")
def get_document_highlight_meta(
    document_id: str,
    page: int = Query(..., description="Trang cần kiểm tra (1-indexed)"),
    query: str = Query("", description="Từ khóa hoặc đoạn văn cần tìm tọa độ"),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Đã tắt tính năng highlight theo yêu cầu: chỉ điều hướng đúng trang trích dẫn."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    _enforce_doc_read_access(doc, current_user, db)
    return {"page": page, "rects": [], "terms": [], "grounded_sentence": ""}


@router.get("/{document_id}/figures")
def list_document_figures(document_id: str, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    """Lấy danh sách các sơ đồ, biểu đồ và bảng biểu đã trích xuất của tài liệu."""
    from app.models.document import DocumentFigure
    if not _is_valid_uuid(document_id):
        raise HTTPException(404, "Mã tài liệu không hợp lệ")
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    _enforce_doc_read_access(doc, current_user, db)
    figs = db.query(DocumentFigure).filter(DocumentFigure.document_id == document_id).order_by(DocumentFigure.page_number).all()
    return [
        {
            "id": str(f.id),
            "page_number": f.page_number,
            "figure_type": f.figure_type,
            "caption": f.caption,
            "image_filename": f.image_filename,
            "url": f"/api/v1/document/{document_id}/figures/{f.image_filename}",
        }
        for f in figs
    ]


@router.get("/{document_id}/figures/{figure_name}")
def get_document_figure(document_id: str, figure_name: str, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    """Phục vụ ảnh sơ đồ / biểu đồ / bảng biểu trích xuất từ tài liệu."""
    from app.services.figure_extractor import FIGURES_STORAGE_DIR
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    _enforce_doc_read_access(doc, current_user, db)
    safe_name = os.path.basename(figure_name)
    file_path = os.path.join(FIGURES_STORAGE_DIR, str(document_id), safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(404, f"Không tìm thấy sơ đồ: {safe_name}")
    return FileResponse(file_path, media_type="image/png")


@router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    if not _is_valid_uuid(document_id):
        raise HTTPException(404, "Mã tài liệu không hợp lệ")
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    _enforce_doc_read_access(doc, current_user, db)
    return {
        "id": str(doc.id), "filename": doc.filename, "title": doc.title,
        "authors": doc.authors, "year": doc.year, "status": doc.status,
        "total_pages": doc.total_pages, "category": doc.category,
    }


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not _is_valid_uuid(document_id):
        raise HTTPException(404, "Mã tài liệu không hợp lệ")
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    # Kiểm tra quyền: chỉ admin hoặc chủ sở hữu mới được xóa tài liệu
    if current_user.role != "admin":
        if doc.user_id is None or str(doc.user_id) != str(current_user.id):
            raise HTTPException(403, "Bạn không có quyền xóa tài liệu này")

    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    try:
        from app.db.neo4j import delete_document_graph
        delete_document_graph(document_id)
    except Exception:
        pass
    db.delete(doc)
    db.commit()
    return {"message": "Đã xóa tài liệu"}


@router.patch("/{document_id}/category")
def update_category(
    document_id: str,
    category: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    if not current_user:
        raise HTTPException(401, "Cần đăng nhập để thực hiện thao tác này")
    # Admin có thể sửa mọi tài liệu
    # Người khác chỉ sửa được tài liệu của mình (doc.user_id phải khớp)
    if current_user.role != "admin":
        if doc.user_id is None or str(doc.user_id) != str(current_user.id):
            raise HTTPException(403, "Bạn không có quyền chỉnh sửa tài liệu này")
    doc.category = category
    db.commit()
    return {"message": "Đã cập nhật phân loại", "category": category}


@router.patch("/{document_id}/metadata")
def update_metadata(
    document_id: str,
    title: Optional[str] = Body(None, embed=True),
    authors: Optional[str] = Body(None, embed=True),
    year: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Sửa metadata tài liệu (title, authors, year). Chỉ owner hoặc admin mới có quyền."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    if not current_user:
        raise HTTPException(401, "Cần đăng nhập để thực hiện thao tác này")
    if current_user.role != "admin":
        if doc.user_id is None or str(doc.user_id) != str(current_user.id):
            raise HTTPException(403, "Bạn không có quyền chỉnh sửa tài liệu này")
    if title is not None:
        doc.title = title.strip() or None
    if authors is not None:
        doc.authors = authors.strip() or None
    if year is not None:
        try:
            doc.year = int(year) if year else None
        except (ValueError, TypeError):
            raise HTTPException(400, "Năm xuất bản phải là số nguyên")
    db.commit()
    # Đồng bộ sang Neo4j nếu có
    try:
        from app.db.neo4j import insert_document_graph
        insert_document_graph(
            document_id,
            doc.title or doc.filename,
            doc.authors or "",
            doc.year or 0,
        )
    except Exception as e:
        logger.warning("Neo4j sync sau update metadata thất bại: %s", e)
    return {
        "message": "Đã cập nhật metadata",
        "title":   doc.title,
        "authors": doc.authors,
        "year":    doc.year,
    }


@router.post("/{document_id}/summarize")
def summarize_document_endpoint(document_id: str, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    _enforce_doc_read_access(doc, current_user, db)
    if doc.status != "ready":
        raise HTTPException(400, f"Tài liệu chưa sẵn sàng (status: {doc.status})")
    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.chunk_index).all()
    full_text = " ".join([c.content for c in chunks])
    from app.services.generator import summarize_document
    return {"document_id": document_id, "summary": summarize_document(full_text)}


# ── Phase A: Admin rebuild memory endpoint ─────────────────────────────────────

@router.post("/{document_id}/rebuild-memory")
def rebuild_memory_endpoint(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Trigger lại memory build cho 1 document đã upload trước đó.

    Dùng khi:
    - Document upload trước khi có memory builder → cần rebuild để có memory ready
    - Memory build bị failed → retry
    - Muốn dùng model tốt hơn (vd qwen2.5:7b thay vì 1.5B) → rebuild với env mới

    Auth: chỉ admin hoặc owner của document.
    Status: 200 nếu trigger OK, document.memory_status chuyển sang 'building'.
    Memory build chạy background → poll GET /document/{id} để check memory_status.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    # Auth: admin hoặc owner
    if current_user is None or (
        current_user.role != "admin"
        and (doc.user_id is None or str(doc.user_id) != str(current_user.id))
    ):
        raise HTTPException(403, "Chỉ admin hoặc chủ sở hữu mới được rebuild memory")

    if doc.status != "ready":
        raise HTTPException(400, f"Document chưa sẵn sàng (status: {doc.status}) — không có page_texts để build memory")

    # Reset memory_status trước khi rebuild
    from sqlalchemy import text as sql_text
    db.execute(sql_text("""
        UPDATE document_summaries SET memory_status = 'pending', error_message = NULL
        WHERE document_id = :did
    """), {"did": document_id})
    db.execute(sql_text("""
        UPDATE documents SET has_memory = FALSE, memory_status = 'pending'
        WHERE id = :did
    """), {"did": document_id})
    db.commit()

    # Schedule background rebuild
    from app.services.memory_builder import build_memory_for_doc
    from app.db.postgres import _resolve_postgres_url
    background_tasks.add_task(build_memory_for_doc, document_id, _resolve_postgres_url(settings.POSTGRES_URL))

    return {
        "message": "Memory rebuild đã được trigger (chạy background).",
        "document_id": document_id,
        "memory_status": "pending",
        "tip": "Poll GET /api/v1/document/{id} để check memory_status → 'ready' khi xong.",
    }


@router.get("/{document_id}/memory-status")
def memory_status_endpoint(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Check trạng thái memory build cho 1 document.

    Trả về memory_status + số facts/entities + abstract length.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    _enforce_doc_read_access(doc, current_user, db)

    from sqlalchemy import text as sql_text
    row = db.execute(sql_text("""
        SELECT memory_status, error_message, abstract IS NOT NULL as has_abstract,
               jsonb_array_length(COALESCE(key_facts, '[]'::jsonb)) as n_facts,
               jsonb_array_length(COALESCE(entities, '[]'::jsonb)) as n_entities,
               abstract_embedding IS NOT NULL as has_embedding,
               memory_tokens_used, updated_at
        FROM document_summaries WHERE document_id = :did
    """), {"did": document_id}).first()

    if not row:
        return {
            "document_id": document_id,
            "has_memory": doc.has_memory,
            "memory_status": doc.memory_status or "pending",
            "summary_row": None,
        }

    return {
        "document_id": document_id,
        "has_memory": doc.has_memory,
        "memory_status": doc.memory_status,
        "summary": {
            "memory_status": row.memory_status,
            "error_message": row.error_message,
            "has_abstract": row.has_abstract,
            "n_facts": row.n_facts,
            "n_entities": row.n_entities,
            "has_embedding": row.has_embedding,
            "tokens_used": row.memory_tokens_used,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        },
    }
