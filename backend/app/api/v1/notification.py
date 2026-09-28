from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.postgres import get_db
from app.models.document import Notification, User

router = APIRouter()


def _out(n: Notification) -> dict:
    return {
        "id": str(n.id),
        "title": n.title,
        "body": n.body,
        "type": n.type,
        "is_read": n.is_read,
        "link": n.link,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


# ── User endpoints ────────────────────────────────────────────────────────────

@router.get("")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return [_out(n) for n in rows]


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .count()
    )
    return {"count": count}


@router.patch("/{notif_id}/read")
def mark_read(
    notif_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(404, "Không tìm thấy thông báo")
    n.is_read = True
    db.commit()
    return _out(n)


@router.patch("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}


@router.delete("/{notif_id}")
def delete_notification(
    notif_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(404, "Không tìm thấy thông báo")
    db.delete(n)
    db.commit()
    return {"ok": True}


# ── Admin endpoints ───────────────────────────────────────────────────────────

class SendNotifRequest(BaseModel):
    title: str
    body: Optional[str] = None
    type: str = "info"              # info | success | warning | system
    link: Optional[str] = None
    target_email: Optional[str] = None   # None = broadcast to all users


@router.post("/admin/send")
def admin_send(
    req: SendNotifRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin")
    if req.type not in ("info", "success", "warning", "system"):
        raise HTTPException(400, "type không hợp lệ")

    if req.target_email:
        target = db.query(User).filter(User.email == req.target_email.strip().lower()).first()
        if not target:
            raise HTTPException(404, f"Không tìm thấy user {req.target_email}")
        n = Notification(
            user_id=target.id,
            title=req.title,
            body=req.body,
            type=req.type,
            link=req.link,
        )
        db.add(n)
        db.commit()
        return {"ok": True, "sent_to": 1}
    else:
        # Broadcast: fan-out to all non-admin users
        users = db.query(User).all()
        notifs = [
            Notification(
                user_id=u.id,
                title=req.title,
                body=req.body,
                type=req.type,
                link=req.link,
            )
            for u in users
        ]
        db.bulk_save_objects(notifs)
        db.commit()
        return {"ok": True, "sent_to": len(notifs)}
