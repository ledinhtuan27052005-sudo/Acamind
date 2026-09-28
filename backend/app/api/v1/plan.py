from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.postgres import get_db
from app.models.document import User
from app.core.security import get_current_user
from app.core.plan_utils import PLAN_LIMITS, get_limits, count_user_docs, count_today_chats

router = APIRouter()


@router.get("/pricing")
def get_pricing():
    """Public: return all plan tiers and their features/prices."""
    return [
        {
            "key": key,
            "label": info["label"],
            "price_vnd": info["price_vnd"],
            "max_docs": info["max_docs"],
            "max_daily_chat": info["max_daily_chat"],
            "features": info["features"],
        }
        for key, info in PLAN_LIMITS.items()
    ]


@router.get("/me")
def get_my_usage(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Authenticated: return current plan + usage stats."""
    limits = get_limits(current_user)
    plan = getattr(current_user, "plan", None) or "free"
    if current_user.role == "admin":
        plan = "enterprise"
    elif current_user.role == "researcher" and plan == "free":
        plan = "researcher"

    doc_count = count_user_docs(current_user.id, db)
    chat_count = count_today_chats(current_user.id, db)

    return {
        "plan": plan,
        "plan_label": limits["label"],
        "max_docs": limits["max_docs"],
        "max_daily_chat": limits["max_daily_chat"],
        "used_docs": doc_count,
        "used_today_chat": chat_count,
    }


class UpgradePlanRequest(BaseModel):
    plan: str


@router.patch("/users/{user_id}")
def upgrade_user_plan(
    user_id: str,
    req: UpgradePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin only: upgrade or downgrade a user's plan."""
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin mới có thể thay đổi gói dịch vụ")
    if req.plan not in PLAN_LIMITS:
        raise HTTPException(400, f"Gói không hợp lệ. Chọn: {list(PLAN_LIMITS.keys())}")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(404, "Không tìm thấy người dùng")
    target.plan = req.plan
    db.commit()
    return {"message": f"Đã cập nhật gói cho {target.email} → {req.plan}"}
