import uuid
import json
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.db.postgres import get_db
from app.models.document import User
from app.core.security import get_current_user, verify_password, hash_password
from app.services.profile_analyzer import analyze_symptoms, analyze_chat_patterns
from app.services.llm_client import llm_configuration_error

router = APIRouter()

AVATAR_DIR = Path("../data/avatars")


# ── Me / Edit profile ──────────────────────────────────────────────────────────

class UpdateNameRequest(BaseModel):
    full_name: str

class UpdatePasswordRequest(BaseModel):
    current_password: str = ""
    new_password: str

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "plan": getattr(user, "plan", None) or "free",
        "avatar_url": user.avatar_url,
        "is_oauth": bool(user.is_oauth),
    }

@router.patch("/me")
def update_me(req: UpdateNameRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = req.full_name.strip()
    if not name:
        raise HTTPException(400, "Tên không được để trống")
    user.full_name = name
    db.commit()
    return {"message": "Đã cập nhật tên", "full_name": user.full_name}

@router.patch("/password")
def update_password(req: UpdatePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.is_oauth:
        if not verify_password(req.current_password, user.hashed_password):
            raise HTTPException(400, "Mật khẩu hiện tại không đúng")
    if len(req.new_password) < 6:
        raise HTTPException(400, "Mật khẩu mới phải có ít nhất 6 ký tự")
    user.hashed_password = hash_password(req.new_password)
    user.is_oauth = False
    db.commit()
    return {"message": "Đã đổi mật khẩu thành công"}

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in {"jpg", "jpeg", "png", "webp", "gif"}:
        raise HTTPException(400, "Chỉ chấp nhận JPG, PNG, WebP")
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    for old_ext in ["jpg", "jpeg", "png", "webp", "gif"]:
        old = AVATAR_DIR / f"{user.id}.{old_ext}"
        if old.exists():
            old.unlink()
    content = await file.read()
    with open(AVATAR_DIR / f"{user.id}.{ext}", "wb") as f:
        f.write(content)
    user.avatar_url = f"/api/v1/profile/avatar/{user.id}"
    db.commit()
    return {"avatar_url": user.avatar_url}

@router.get("/avatar/{user_id}")
def get_avatar(user_id: str):
    for ext in ["jpg", "jpeg", "png", "webp", "gif"]:
        p = AVATAR_DIR / f"{user_id}.{ext}"
        if p.exists():
            return FileResponse(str(p))
    raise HTTPException(404, "Avatar không tìm thấy")


class SaveChatRequest(BaseModel):
    user_id: Optional[str] = None
    query: str
    answer: str
    document_ids: list[str] = []


# ── Chat History ───────────────────────────────────────────────────────────────

@router.post("/chat-history")
def save_chat(req: SaveChatRequest, db: Session = Depends(get_db)):
    if not req.user_id:
        return {"ok": True, "message": "Không lưu — chưa đăng nhập"}
    record_id = str(uuid.uuid4())
    db.execute(
        text("""
            INSERT INTO chat_history (id, user_id, query, answer, document_ids)
            VALUES (:id, :uid, :query, :answer, cast(:docs AS jsonb))
        """),
        {
            "id": record_id,
            "uid": req.user_id,
            "query": req.query,
            "answer": req.answer[:5000],
            "docs": json.dumps(req.document_ids),
        },
    )
    db.commit()
    return {"ok": True, "id": record_id}


@router.get("/chat-history/{user_id}")
def get_chat_history(user_id: str, limit: int = 20, db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT id, query, answer, document_ids, created_at
            FROM chat_history
            WHERE user_id = :uid
            ORDER BY created_at DESC
            LIMIT :lim
        """),
        {"uid": user_id, "lim": limit},
    ).fetchall()
    return {
        "total": len(rows),
        "history": [
            {
                "id": str(r.id),
                "query": r.query,
                "answer": r.answer[:300] + ("..." if len(r.answer) > 300 else ""),
                "document_ids": r.document_ids if r.document_ids else [],
                "created_at": str(r.created_at) if r.created_at else None,
            }
            for r in rows
        ],
    }


# ── Symptoms & Insights ────────────────────────────────────────────────────────

@router.get("/symptoms/{user_id}")
def get_symptoms(user_id: str, db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT id, region_id, region_name, description, pain_level, duration, reported_at
            FROM body_symptoms WHERE user_id = :uid ORDER BY reported_at DESC
        """),
        {"uid": user_id},
    ).fetchall()
    symptoms = [
        {
            "id": str(r.id),
            "region_id": r.region_id,
            "region_name": r.region_name,
            "description": r.description,
            "pain_level": r.pain_level,
            "duration": r.duration,
            "reported_at": str(r.reported_at) if r.reported_at else None,
        }
        for r in rows
    ]
    # Simple stats
    avg_pain = round(sum(s["pain_level"] for s in symptoms) / len(symptoms), 1) if symptoms else 0
    region_counts: dict = {}
    for s in symptoms:
        region_counts[s["region_name"]] = region_counts.get(s["region_name"], 0) + 1

    return {
        "total": len(symptoms),
        "avg_pain": avg_pain,
        "region_counts": region_counts,
        "symptoms": symptoms,
    }


@router.post("/insights/{user_id}")
def generate_insights(user_id: str, db: Session = Depends(get_db)):
    """Generate and cache AI health insights from symptom history."""
    rows = db.execute(
        text("""
            SELECT region_name, description, pain_level, duration, reported_at
            FROM body_symptoms WHERE user_id = :uid ORDER BY reported_at DESC LIMIT 20
        """),
        {"uid": user_id},
    ).fetchall()
    symptoms = [
        {
            "region_name": r.region_name,
            "description": r.description,
            "pain_level": r.pain_level,
            "duration": r.duration,
            "reported_at": r.reported_at,
        }
        for r in rows
    ]

    chat_rows = db.execute(
        text("SELECT query FROM chat_history WHERE user_id = :uid ORDER BY created_at DESC LIMIT 10"),
        {"uid": user_id},
    ).fetchall()
    chats = [{"query": r.query} for r in chat_rows]

    config_error = llm_configuration_error()
    if config_error and (symptoms or chats):
        raise HTTPException(status_code=503, detail=config_error)

    health_insight = analyze_symptoms(symptoms)
    learning_insight = analyze_chat_patterns(chats) if chats else None

    # Cache insight
    insight_id = str(uuid.uuid4())
    db.execute(
        text("""
            INSERT INTO ai_insights (id, user_id, insight_type, content, metadata)
            VALUES (:id, :uid, 'health_summary', :content, cast(:meta AS jsonb))
        """),
        {
            "id": insight_id,
            "uid": user_id,
            "content": health_insight,
            "meta": json.dumps({"symptom_count": len(symptoms), "chat_count": len(chats)}),
        },
    )
    db.commit()

    return {
        "health_insight": health_insight,
        "learning_insight": learning_insight,
        "symptom_count": len(symptoms),
        "chat_count": len(chats),
    }


@router.get("/insights/{user_id}/latest")
def get_latest_insight(user_id: str, db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT content, metadata, created_at
            FROM ai_insights WHERE user_id = :uid
            ORDER BY created_at DESC LIMIT 1
        """),
        {"uid": user_id},
    ).first()
    if not row:
        return {"insight": None}
    return {
        "insight": row.content,
        "metadata": row.metadata,
        "created_at": str(row.created_at) if row.created_at else None,
    }


@router.get("/summary/{user_id}")
def get_profile_summary(user_id: str, db: Session = Depends(get_db)):
    """Dashboard-style summary for profile page."""
    sym_count = db.execute(
        text("SELECT COUNT(*) FROM body_symptoms WHERE user_id = :uid"), {"uid": user_id}
    ).scalar() or 0
    chat_count = db.execute(
        text("SELECT COUNT(*) FROM chat_history WHERE user_id = :uid"), {"uid": user_id}
    ).scalar() or 0
    profile_row = db.execute(
        text("SELECT user_type, onboarding_done FROM user_profiles WHERE user_id = :uid"),
        {"uid": user_id},
    ).first()
    return {
        "symptom_count": sym_count,
        "chat_count": chat_count,
        "user_type": profile_row.user_type if profile_row else "patient",
        "onboarding_done": profile_row.onboarding_done if profile_row else False,
    }
