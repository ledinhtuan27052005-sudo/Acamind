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


def _run_pipeline(file_path: str, document_id: str, db_url: str):
    """Xử lý PDF upload trong background: parse, chunk, embed."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    error_msg = None
    
    try:
        # 1. Parse PDF
        parsed = parse_pdf(file_path)
        
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
        from sqlalchemy import text as sql_text
        for page_info in parsed["pages"]:
            if page_info.get("text", "").strip():
                db.execute(sql_text("""
                    INSERT INTO page_texts (document_id, page_number, content)
                    VALUES (:doc_id, :page, :content)
                    ON CONFLICT (document_id, page_number) DO UPDATE SET content = EXCLUDED.content
                """), {
                    "doc_id": document_id,
                    "page": page_info["page"],
                    "content": page_info["text"],
                })
        db.commit()

        # 5. Embed and store chunks
        embed_and_store(chunks, db)

        # 7. Update Neo4j graph (optional - non-blocking, retry 1 lần nếu fail)
        from app.db.neo4j import insert_document_graph
        neo4j_ok = False
        for attempt in (1, 2):
            try:
                insert_document_graph(document_id, doc.title or doc.filename, doc.authors or "", doc.year or 0)
                neo4j_ok = True
                break
            except Exception as e:
                logger.warning("Neo4j insert attempt %d failed for %s: %s", attempt, document_id, e)
                if attempt == 1:
                    time.sleep(1.0)  # chờ 1s rồi retry 1 lần
        if not neo4j_ok:
            # Ghi log đầy đủ + đánh dấu trong document để admin có thể retry thủ công sau.
            logger.error("Neo4j insert FAILED permanently for document %s. Graph node sẽ bị thiếu.", document_id)
            try:
                from sqlalchemy import text as sql_text
                db.execute(sql_text("UPDATE documents SET neo4j_synced = false WHERE id = :id"), {"id": document_id})
                db.commit()
            except Exception:
                pass  # Nếu cột neo4j_synced chưa tồn tại, bỏ qua — không chặn pipeline.

        # 8. Trích xuất sơ đồ, hình ảnh & bảng biểu (Multimodal Figure Extraction)
        try:
            from app.services.figure_extractor import extract_and_save_figures
            extract_and_save_figures(file_path, document_id, db)
        except Exception as fig_err:
            logger.warning("Trích xuất sơ đồ thất bại cho %s: %s", document_id, fig_err)

        # 9. Mark as ready
        doc.status = "ready"
        db.commit()
        print(f"[INFO] [OK] Pipeline done: {document_id} - {len(chunks)} chunks")

        # 9. Build compressed memory (Phase A) — best-effort, không chặn pipeline.
        # Nếu fail, document vẫn ở status='ready', RAG path vẫn hoạt động bình thường.
        try:
            from app.services.memory_builder import build_memory_for_doc
            build_memory_for_doc(document_id, db_url)
        except Exception as mem_err:
            logger.warning("Memory build skip cho %s: %s", document_id, mem_err)
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        print(f"[ERROR] Pipeline failed for {document_id}: {error_msg}")
        
        # Rollback current session
        try:
            db.rollback()
        except:
            pass
        db.close()
        
        # Create fresh connection to update status to error
        try:
            fresh_engine = create_engine(db_url, isolation_level="READ_COMMITTED")
            fresh_db = sessionmaker(bind=fresh_engine)()
            error_doc = fresh_db.query(Document).filter(Document.id == document_id).first()
            if error_doc:
                error_doc.status = "error"
                fresh_db.commit()
                print(f"[INFO] Document {document_id} status updated to 'error'")
            fresh_db.close()
            fresh_engine.dispose()
        except Exception as cleanup_err:
            print(f"[ERROR] Failed to update error status: {cleanup_err}")
    finally:
        try:
            db.close()
        except:
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


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload PDF và xử lý trong background."""
    # 0. Enforce plan upload limit
    if current_user.role != "admin":
        limits = get_limits(current_user)
        plan = getattr(current_user, "plan", "free") or "free"

        # Free: tổng tài liệu
        if limits["max_docs"] is not None:
            if count_user_docs(current_user.id, db) >= limits["max_docs"]:
                raise HTTPException(
                    403,
                    f"❌ Gói {limits['label']} chỉ cho phép tối đa {limits['max_docs']} tài liệu. "
                    "Nâng cấp để tải thêm."
                )

        # Pro / Researcher: giới hạn tháng
        elif limits["max_monthly_docs"] is not None:
            monthly = count_monthly_docs(current_user.id, db)
            if monthly >= limits["max_monthly_docs"]:
                raise HTTPException(
                    403,
                    f"❌ Gói {limits['label']} chỉ cho phép tối đa {limits['max_monthly_docs']} tài liệu/tháng. "
                    "Bạn đã đạt giới hạn tháng này."
                )

        # Enterprise: chủ tài khoản hoặc thành viên
        elif plan == "enterprise":
            from app.models.document import Organization, OrgMember
            # Chủ tài khoản trường
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
                # Thành viên (học sinh)
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

    # 1. Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "❌ Chỉ chấp nhận file PDF")

    # 1.5. Dedup: tính SHA-256 hash của nội dung file để check duplicate
    #     (cùng user HOẶC công khai). Nếu đã tồn tại → trả về doc cũ.
    from app.services.dedup_utils import compute_file_hash
    content_hash = compute_file_hash(file.file)
    existing_doc = db.query(Document).filter(
        Document.content_hash == content_hash,
        or_(
            Document.user_id == current_user.id,
            Document.user_id.is_(None),  # công khai
            # Admin/researcher upload: chia sẻ giữa users
            Document.user_id.isnot(None),
        )
    ).first()
    if existing_doc:
        return {
            "document_id": str(existing_doc.id),
            "filename": existing_doc.filename,
            "status": existing_doc.status,
            "title": existing_doc.title,
            "has_memory": existing_doc.has_memory,
            "message": f"✓ File đã tồn tại (doc cũ: {existing_doc.title or existing_doc.filename}). Trả về document cũ.",
            "duplicate": True,
        }

    # 2. Validate file size — tăng giới hạn lên 200MB và dùng streaming write
    #    để tránh load toàn bộ file vào RAM (gây OOM với file lớn)
    document_id = str(uuid.uuid4())
    safe_filename = file.filename.replace(" ", "_").replace("/", "_").replace("\\", "_")

    # 3. Prepare upload directory (absolute path)
    try:
        upload_dir = settings.get_pdf_upload_dir()
    except Exception as e:
        raise HTTPException(500, f"❌ Không thể tạo thư mục upload: {e}")

    file_path = os.path.join(upload_dir, f"{document_id}_{safe_filename}")

    # 4. Stream file ra disk từng chunk 1MB — tránh OOM và cho phép file lớn
    max_bytes = 200 * 1024 * 1024  # 200MB
    total = 0
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
                    raise HTTPException(413, "❌ File vượt quá 200MB")
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(500, f"❌ Không thể lưu file: {e}")

    if total == 0:
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(400, "❌ File PDF trống")

    print(f"[INFO] File saved: {file_path} ({total} bytes)")

    # 6. Create document record in DB
    try:
        user_id = current_user.id if current_user else None
        doc = Document(
            id=document_id,
            filename=file.filename,
            file_path=file_path,
            status="processing",
            user_id=user_id,
            category=category,
            content_hash=content_hash,  # Dedup: lưu hash để check duplicate lần sau
        )
        db.add(doc)
        db.commit()
        print(f"[INFO] Document record created: {document_id}")
    except Exception as e:
        raise HTTPException(500, f"❌ Lỗi lưu database: {e}")

    # 7. Schedule background processing
    background_tasks.add_task(_run_pipeline, file_path, document_id, settings.POSTGRES_URL)
    
    return {
        "document_id": document_id,
        "filename": file.filename,
        "status": "processing",
        "message": "✓ File uploaded. Processing in background..."
    }


@router.get("/categories")
def list_categories_public(db: Session = Depends(get_db)):
    """Public endpoint — trả về danh sách phân loại từ DB."""
    from app.models.document import DocumentCategory
    cats = db.query(DocumentCategory).order_by(DocumentCategory.name).all()
    return [{"id": str(c.id), "name": c.name, "color": c.color} for c in cats]


@router.get("/list")
def list_documents(db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    from sqlalchemy.orm import aliased
    from sqlalchemy import or_
    from app.models.document import User as UserModel

    UploaderAlias = aliased(UserModel)
    base = db.query(Document).outerjoin(UploaderAlias, Document.user_id == UploaderAlias.id)

    if current_user and current_user.role == "admin":
        # Admin thấy tất cả
        query = base
    elif current_user:
        # Researcher / student: tài liệu của mình + tài liệu công khai (admin/researcher/legacy)
        # Legacy "user" role được coi như student (private)
        query = base.filter(
            or_(
                Document.user_id == current_user.id,
                Document.user_id == None,
                UploaderAlias.role.in_(["admin", "researcher"]),
            )
        )
    else:
        # Chưa đăng nhập: chỉ thấy tài liệu công khai
        query = base.filter(
            or_(
                Document.user_id == None,
                UploaderAlias.role.in_(["admin", "researcher"]),
            )
        )

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

    doc = db.query(Document).filter(
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


import uuid

def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


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

    # Access control: same visibility rules as list_documents
    if current_user and current_user.role == "admin":
        pass  # admin sees all
    elif current_user:
        if doc.user_id and str(doc.user_id) != str(current_user.id):
            from app.models.document import User as UserModel
            uploader = db.query(UserModel).filter(UserModel.id == doc.user_id).first()
            if not uploader or uploader.role not in ("admin", "researcher"):
                raise HTTPException(403, f"Không có quyền xem tài liệu này (uploaded by: {uploader.role if uploader else 'unknown'})")
    else:
        if doc.user_id:
            from app.models.document import User as UserModel
            uploader = db.query(UserModel).filter(UserModel.id == doc.user_id).first()
            if not uploader or uploader.role not in ("admin", "researcher"):
                raise HTTPException(403, "Vui lòng đăng nhập để xem tài liệu này")

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

    # Access control: same visibility rules as list_documents
    if current_user and current_user.role == "admin":
        pass
    elif current_user:
        if doc.user_id and str(doc.user_id) != str(current_user.id):
            from app.models.document import User as UserModel
            uploader = db.query(UserModel).filter(UserModel.id == doc.user_id).first()
            if not uploader or uploader.role not in ("admin", "researcher"):
                raise HTTPException(403, "Không có quyền xem tài liệu này")
    else:
        if doc.user_id:
            from app.models.document import User as UserModel
            uploader = db.query(UserModel).filter(UserModel.id == doc.user_id).first()
            if not uploader or uploader.role not in ("admin", "researcher"):
                raise HTTPException(403, "Vui lòng đăng nhập để xem tài liệu này")

    if not os.path.exists(doc.file_path):
        raise HTTPException(404, f"File không còn tồn tại trên server: {doc.filename}")

    from urllib.parse import quote
    encoded_filename = quote(doc.filename)

    # Nếu không có yêu cầu highlight hoặc trang, fallback trả về file gốc
    if not highlight or not page:
        return FileResponse(
            doc.file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"},
        )

    try:
        from app.services.pdf_highlighter import generate_highlighted_pdf_stream
        pdf_bytes = generate_highlighted_pdf_stream(doc.file_path, page, highlight)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}",
                "Cache-Control": "private, max-age=300",
            },
        )
    except Exception as e:
        logger.warning(f"Failed to generate highlighted PDF for doc {document_id}: {e}")
        return FileResponse(
            doc.file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"},
        )


@router.get("/{document_id}/highlight-meta")
def get_document_highlight_meta(
    document_id: str,
    page: int = Query(..., description="Trang cần kiểm tra (1-indexed)"),
    query: str = Query(..., description="Từ khóa hoặc đoạn văn cần tìm tọa độ"),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Lấy danh sách bounding boxes và terms khớp trên trang."""
    if not _is_valid_uuid(document_id):
        raise HTTPException(404, "Mã tài liệu không hợp lệ")
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(404, "Không tìm thấy tài liệu")

    try:
        from app.services.pdf_highlighter import get_highlight_metadata
        meta = get_highlight_metadata(doc.file_path, page, query)
        return meta
    except Exception as e:
        logger.error(f"Error getting highlight meta: {e}")
        return {"page": page, "rects": [], "terms": [], "grounded_sentence": ""}


@router.get("/{document_id}/figures")
def list_document_figures(document_id: str, db: Session = Depends(get_db)):
    """Lấy danh sách các sơ đồ, biểu đồ và bảng biểu đã trích xuất của tài liệu."""
    from app.models.document import DocumentFigure
    if not _is_valid_uuid(document_id):
        raise HTTPException(404, "Mã tài liệu không hợp lệ")
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
def get_document_figure(document_id: str, figure_name: str, db: Session = Depends(get_db)):
    """Phục vụ ảnh sơ đồ / biểu đồ / bảng biểu trích xuất từ tài liệu."""
    from app.services.figure_extractor import FIGURES_STORAGE_DIR
    safe_name = os.path.basename(figure_name)
    file_path = os.path.join(FIGURES_STORAGE_DIR, str(document_id), safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(404, f"Không tìm thấy sơ đồ: {safe_name}")
    return FileResponse(file_path, media_type="image/png")


@router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    if not _is_valid_uuid(document_id):
        raise HTTPException(404, "Mã tài liệu không hợp lệ")
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    return {
        "id": str(doc.id), "filename": doc.filename, "title": doc.title,
        "authors": doc.authors, "year": doc.year, "status": doc.status,
        "total_pages": doc.total_pages, "category": doc.category,
    }


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    # Kiểm tra quyền: user đăng nhập chỉ xóa được tài liệu của mình (trừ admin)
    if current_user and current_user.role != "admin":
        if doc.user_id and str(doc.user_id) != str(current_user.id):
            raise HTTPException(403, "Bạn không có quyền xóa tài liệu này")

    if os.path.exists(doc.file_path):
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
def summarize_document_endpoint(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
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
    background_tasks.add_task(build_memory_for_doc, document_id, settings.POSTGRES_URL)

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
