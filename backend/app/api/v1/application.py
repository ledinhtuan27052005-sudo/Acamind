import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.postgres import get_db
from app.models.document import User, ResearcherApplication
from app.core.security import get_current_user

router = APIRouter()


def _app_out(app: ResearcherApplication) -> dict:
    return {
        "id": str(app.id),
        "user_id": str(app.user_id),
        "reason": app.reason,
        "status": app.status,
        "admin_note": app.admin_note,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
    }


class ApplicationRequest(BaseModel):
    reason: str = ""


@router.post("/researcher")
def apply_researcher(
    body: ApplicationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sinh viên gửi đơn đăng ký tài khoản Researcher."""
    if current_user.role in ("researcher", "admin"):
        raise HTTPException(400, "Bạn đã có quyền Researcher hoặc Admin")

    # Chỉ cho phép gửi lại nếu đơn trước bị từ chối
    pending = db.query(ResearcherApplication).filter(
        ResearcherApplication.user_id == current_user.id,
        ResearcherApplication.status == "pending",
    ).first()
    if pending:
        raise HTTPException(400, "Bạn đã có đơn đăng ký đang chờ xét duyệt")

    app = ResearcherApplication(
        id=uuid.uuid4(),
        user_id=current_user.id,
        reason=body.reason.strip(),
        status="pending",
    )
    db.add(app)
    db.commit()
    return {
        "message": "Đã gửi đơn đăng ký thành công. Admin sẽ xét duyệt sớm.",
        "application": _app_out(app),
    }


@router.get("/researcher/status")
def get_application_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xem trạng thái đơn đăng ký Researcher mới nhất của bản thân."""
    app = (
        db.query(ResearcherApplication)
        .filter(ResearcherApplication.user_id == current_user.id)
        .order_by(ResearcherApplication.created_at.desc())
        .first()
    )
    return {
        "current_role": current_user.role,
        "status": app.status if app else "none",
        "application": _app_out(app) if app else None,
    }
