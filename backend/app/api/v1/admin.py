import uuid
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from pydantic import BaseModel
from app.db.postgres import get_db
from app.models.document import User, Document, Chunk, ResearcherApplication, DocumentCategory
from app.core.security import require_admin
from app.core.plan_utils import PLAN_LIMITS

router = APIRouter()

VALID_ROLES = {"student", "researcher", "admin"}


class RoleUpdate(BaseModel):
    role: str  # "student" | "researcher" | "admin"


class ReviewApplication(BaseModel):
    action: str   # "approve" | "reject"
    note: str = ""


class CategoryCreate(BaseModel):
    name: str
    color: str = "#6366f1"


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


def _user_out(u: User, doc_count: int = 0) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role,
        "plan": getattr(u, "plan", None) or "free",
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "document_count": doc_count,
    }


def _app_out(app: ResearcherApplication, user: User) -> dict:
    return {
        "id": str(app.id),
        "user_id": str(app.user_id),
        "user_email": user.email,
        "user_name": user.full_name or "",
        "reason": app.reason or "",
        "status": app.status,
        "admin_note": app.admin_note,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
    }


# ── User management ───────────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    search: Optional[str] = Query(None),
    role:   Optional[str] = Query(None),
    plan:   Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    q = db.query(User)
    if search:
        term = f"%{search}%"
        q = q.filter(User.email.ilike(term) | User.full_name.ilike(term))
    if role and role in VALID_ROLES:
        q = q.filter(User.role == role)
    if plan:
        q = q.filter(User.plan == plan)
    users = q.order_by(User.created_at.desc()).all()
    doc_counts = dict(
        db.query(Document.user_id, func.count(Document.id))
        .group_by(Document.user_id)
        .all()
    )
    return {
        "total": len(users),
        "users": [_user_out(u, doc_counts.get(u.id, 0)) for u in users],
    }


@router.patch("/users/{user_id}/role")
def update_role(
    user_id: str,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    if body.role not in VALID_ROLES:
        raise HTTPException(400, f"role phải là một trong: {', '.join(VALID_ROLES)}")
    if user_id == str(current_admin.id):
        raise HTTPException(400, "Không thể thay đổi role của chính mình")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Không tìm thấy user")

    old_role = user.role
    user.role = body.role

    # Nếu nâng lên researcher → tự động duyệt đơn đang pending (nếu có)
    if body.role == "researcher" and old_role != "researcher":
        pending_app = db.query(ResearcherApplication).filter(
            ResearcherApplication.user_id == user.id,
            ResearcherApplication.status == "pending",
        ).first()
        if pending_app:
            pending_app.status = "approved"
            pending_app.reviewed_at = datetime.now()
            pending_app.reviewed_by = current_admin.id

    db.commit()
    return {"message": f"Đã cập nhật role thành '{body.role}'", "user": _user_out(user)}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    if user_id == str(current_admin.id):
        raise HTTPException(400, "Không thể xóa tài khoản của chính mình")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Không tìm thấy user")

    db.delete(user)
    db.commit()
    return {"message": f"Đã xóa user {user.email}"}


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), _=Depends(require_admin)):
    total_users      = db.query(func.count(User.id)).scalar() or 0
    admin_count      = db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0
    researcher_count = db.query(func.count(User.id)).filter(User.role == "researcher").scalar() or 0
    student_count    = db.query(func.count(User.id)).filter(User.role.in_(["student", "user"])).scalar() or 0
    pending_apps     = db.query(func.count(ResearcherApplication.id)).filter(
        ResearcherApplication.status == "pending"
    ).scalar() or 0
    total_docs   = db.query(func.count(Document.id)).scalar() or 0
    total_chunks = db.query(func.count(Chunk.id)).scalar() or 0
    return {
        "total_users": total_users,
        "admin_count": admin_count,
        "researcher_count": researcher_count,
        "student_count": student_count,
        "pending_applications": pending_apps,
        "total_documents": total_docs,
        "total_chunks": total_chunks,
    }


# ── Researcher applications ───────────────────────────────────────────────────

@router.get("/applications")
def list_applications(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Lấy danh sách đơn đăng ký Researcher. Mặc định: chỉ pending."""
    query = (
        db.query(ResearcherApplication, User)
        .join(User, ResearcherApplication.user_id == User.id)
    )
    filter_status = status if status in ("pending", "approved", "rejected") else "pending"
    query = query.filter(ResearcherApplication.status == filter_status)
    results = query.order_by(ResearcherApplication.created_at.desc()).all()
    return {
        "total": len(results),
        "status_filter": filter_status,
        "applications": [_app_out(app, user) for app, user in results],
    }


@router.patch("/applications/{app_id}/review")
def review_application(
    app_id: str,
    body: ReviewApplication,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    """Admin duyệt hoặc từ chối đơn đăng ký Researcher."""
    app = db.query(ResearcherApplication).filter(ResearcherApplication.id == app_id).first()
    if not app:
        raise HTTPException(404, "Không tìm thấy đơn đăng ký")
    if app.status != "pending":
        raise HTTPException(400, "Đơn đăng ký này đã được xử lý rồi")
    if body.action not in ("approve", "reject"):
        raise HTTPException(400, "action phải là 'approve' hoặc 'reject'")

    app.status = "approved" if body.action == "approve" else "rejected"
    app.admin_note = body.note.strip() or None
    app.reviewed_at = datetime.now()
    app.reviewed_by = current_admin.id

    if body.action == "approve":
        user = db.query(User).filter(User.id == app.user_id).first()
        if user:
            user.role = "researcher"

    db.commit()
    msg = "Đã duyệt. Tài khoản Researcher đã được kích hoạt." if body.action == "approve" else "Đã từ chối đơn đăng ký."
    return {"message": msg, "status": app.status}


# ── Category management ───────────────────────────────────────────────────────

def _cat_out(c: DocumentCategory) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "color": c.color,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("/categories")
def list_categories(db: Session = Depends(get_db), _=Depends(require_admin)):
    cats = db.query(DocumentCategory).order_by(DocumentCategory.name).all()
    # Đếm số tài liệu dùng mỗi phân loại
    counts = dict(
        db.query(Document.category, func.count(Document.id))
        .filter(Document.category.isnot(None))
        .group_by(Document.category)
        .all()
    )
    result = [dict(**_cat_out(c), doc_count=counts.get(c.name, 0)) for c in cats]
    return {"total": len(result), "categories": result}


@router.post("/categories", status_code=201)
def create_category(
    body: CategoryCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Tên phân loại không được để trống")
    if db.query(DocumentCategory).filter(DocumentCategory.name == name).first():
        raise HTTPException(400, "Phân loại này đã tồn tại")
    cat = DocumentCategory(id=uuid.uuid4(), name=name, color=body.color or "#6366f1")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return _cat_out(cat)


@router.patch("/categories/{cat_id}")
def update_category(
    cat_id: str,
    body: CategoryUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    cat = db.query(DocumentCategory).filter(DocumentCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(404, "Không tìm thấy phân loại")
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(400, "Tên không được để trống")
        conflict = db.query(DocumentCategory).filter(
            DocumentCategory.name == name,
            DocumentCategory.id != cat.id,
        ).first()
        if conflict:
            raise HTTPException(400, "Tên phân loại đã được dùng")
        # Cập nhật tên trong bảng documents luôn
        db.execute(
            text("UPDATE documents SET category = :new WHERE category = :old"),
            {"new": name, "old": cat.name},
        )
        cat.name = name
    if body.color is not None:
        cat.color = body.color
    db.commit()
    return _cat_out(cat)


@router.delete("/categories/{cat_id}")
def delete_category(
    cat_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    cat = db.query(DocumentCategory).filter(DocumentCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(404, "Không tìm thấy phân loại")
    # Bỏ phân loại khỏi các tài liệu đang dùng
    db.execute(
        text("UPDATE documents SET category = NULL WHERE category = :n"),
        {"n": cat.name},
    )
    db.delete(cat)
    db.commit()
    return {"message": f"Đã xóa phân loại '{cat.name}'"}


# ── System settings ───────────────────────────────────────────────────────────

class SettingsBatch(BaseModel):
    settings: Dict[str, str]


@router.get("/settings")
def get_settings(db: Session = Depends(get_db), _=Depends(require_admin)):
    rows = db.execute(
        text("SELECT key, value, description, updated_at FROM system_settings ORDER BY key")
    ).fetchall()
    return {
        "settings": {
            r[0]: {"value": r[1], "description": r[2], "updated_at": r[3].isoformat() if r[3] else None}
            for r in rows
        }
    }


@router.patch("/settings")
def update_settings(
    body: SettingsBatch,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    for k, v in body.settings.items():
        db.execute(
            text("""
                INSERT INTO system_settings (key, value, updated_at)
                VALUES (:k, :v, NOW())
                ON CONFLICT (key) DO UPDATE SET value = :v, updated_at = NOW()
            """),
            {"k": k, "v": v},
        )
    db.commit()
    return {"message": f"Đã cập nhật {len(body.settings)} cài đặt"}


# ── System info ───────────────────────────────────────────────────────────────

@router.get("/system-info")
def system_info(db: Session = Depends(get_db), _=Depends(require_admin)):
    from pathlib import Path
    total_users      = db.query(func.count(User.id)).scalar() or 0
    total_docs       = db.query(func.count(Document.id)).scalar() or 0
    total_chunks     = db.query(func.count(Chunk.id)).scalar() or 0
    enterprise_users = db.query(func.count(User.id)).filter(User.plan == "enterprise").scalar() or 0
    pro_users        = db.query(func.count(User.id)).filter(User.plan == "pro").scalar() or 0
    researcher_users = db.query(func.count(User.id)).filter(User.plan == "researcher").scalar() or 0

    # Check DB connection
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Disk usage of raw_pdfs folder
    pdf_dir = Path("data/raw_pdfs")
    pdf_files  = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    pdf_size_mb = sum(f.stat().st_size for f in pdf_files) / (1024 * 1024) if pdf_files else 0

    return {
        "version": "1.0.0",
        "db_status": "ok" if db_ok else "error",
        "total_users": total_users,
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "plan_breakdown": {
            "free": total_users - pro_users - researcher_users - enterprise_users,
            "pro": pro_users,
            "researcher": researcher_users,
            "enterprise": enterprise_users,
        },
        "storage": {
            "user_pdf_count": len(pdf_files),
            "user_pdf_size_mb": round(pdf_size_mb, 2),
        },
    }


# ── Plan limits (read-only) ───────────────────────────────────────────────────

@router.get("/plan-limits")
def get_plan_limits(_=Depends(require_admin)):
    return {"plans": PLAN_LIMITS}


# ── Test email ────────────────────────────────────────────────────────────────

class TestEmailRequest(BaseModel):
    to_email: str


@router.post("/test-email")
def send_test_email(body: TestEmailRequest, _=Depends(require_admin)):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        raise HTTPException(400, "Chưa cấu hình SMTP (SMTP_USER / SMTP_PASS trong .env)")

    try:
        msg = MIMEText(
            "Đây là email kiểm tra từ hệ thống Acamind.\n\nNếu bạn nhận được email này, cấu hình SMTP đang hoạt động đúng.",
            "plain", "utf-8"
        )
        msg["Subject"] = "[Acamind] Test Email"
        msg["From"]    = smtp_user
        msg["To"]      = body.to_email

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [body.to_email], msg.as_string())

        return {"sent": True, "to": body.to_email}
    except Exception as e:
        raise HTTPException(500, f"Gửi email thất bại: {str(e)}")


# ── Document categories management ──────────────────────────────────────────────

# Keep only psychology-related categories + Other
KEEP_CATEGORIES = {
    "DSM / ICD / Diagnosis",
    "Research & Statistics",
    "Psychoanalysis",
    "Behavioral Psychology",
    "Educational Psychology",
    "Clinical Psychology",
    "Cognitive Psychology",
    "Developmental Psychology",
    "Health Psychology",
    "Psychotherapy",
    "Social Psychology",
    "Neuropsychology",
    "Other",
}

DEFAULT_CATEGORIES = [
    ("DSM / ICD / Diagnosis", "#ef4444"),
    ("Research & Statistics", "#6b7280"),
    ("Psychoanalysis", "#e11d48"),
    ("Behavioral Psychology", "#10b981"),
    ("Educational Psychology", "#84cc16"),
    ("Clinical Psychology", "#6366f1"),
    ("Cognitive Psychology", "#3b82f6"),
    ("Developmental Psychology", "#f59e0b"),
    ("Health Psychology", "#0ea5e9"),
    ("Psychotherapy", "#8b5cf6"),
    ("Social Psychology", "#ec4899"),
    ("Neuropsychology", "#06b6d4"),
    ("Other", "#6b7280"),
]


@router.get("/categories/audit")
def audit_categories(
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Liệt kê categories hiện có + đếm documents theo từng category."""
    rows = (
        db.query(DocumentCategory, func.count(Document.id).label("doc_count"))
        .outerjoin(Document, Document.category == DocumentCategory.name)
        .group_by(DocumentCategory.id, DocumentCategory.name, DocumentCategory.color)
        .order_by(DocumentCategory.name)
        .all()
    )
    out = []
    for cat, cnt in rows:
        out.append({
            "id": str(cat.id),
            "name": cat.name,
            "color": cat.color,
            "doc_count": cnt or 0,
            "will_keep": cat.name in KEEP_CATEGORIES,
        })
    return {"categories": out, "keep_set": sorted(KEEP_CATEGORIES)}


@router.post("/categories/clean")
def clean_categories(
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Xóa các category không nằm trong KEEP_CATEGORIES. Documents trỏ tới
    category bị xóa sẽ được set category = NULL (giữ document, mất nhãn)."""
    deleted = 0
    reparented = 0
    try:
        # 1. Set category = NULL cho documents thuộc category sẽ bị xóa
        to_delete = (
            db.query(DocumentCategory.name)
            .filter(~DocumentCategory.name.in_(KEEP_CATEGORIES))
            .all()
        )
        delete_names = [r[0] for r in to_delete]
        if delete_names:
            reparented = (
                db.query(Document)
                .filter(Document.category.in_(delete_names))
                .update({"category": None}, synchronize_session=False)
            )
        # 2. Xóa các category không nằm trong KEEP_CATEGORIES
        if delete_names:
            deleted = (
                db.query(DocumentCategory)
                .filter(~DocumentCategory.name.in_(KEEP_CATEGORIES))
                .delete(synchronize_session=False)
            )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Lỗi khi xóa category: {str(e)}")

    # 3. Đảm bảo đủ categories chuẩn (insert missing ones)
    inserted = 0
    existing = {r[0] for r in db.query(DocumentCategory.name).all()}
    for name, color in DEFAULT_CATEGORIES:
        if name not in existing:
            db.add(DocumentCategory(name=name, color=color))
            inserted += 1
    db.commit()

    return {
        "deleted_categories": deleted,
        "reparented_documents": reparented,
        "inserted_categories": inserted,
        "kept_categories": sorted(KEEP_CATEGORIES),
    }
