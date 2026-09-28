import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Optional
from app.db.postgres import get_db

router = APIRouter()


class SymptomReport(BaseModel):
    user_id: Optional[str] = None
    region_id: str
    region_name: str
    description: str
    pain_level: int = Field(..., ge=1, le=10)
    duration: Optional[str] = None


@router.post("/symptoms")
def report_symptom(report: SymptomReport, db: Session = Depends(get_db)):
    """Lưu khai báo triệu chứng của người dùng."""
    symptom_id = str(uuid.uuid4())
    db.execute(
        text("""
            INSERT INTO body_symptoms
                (id, user_id, region_id, region_name, description, pain_level, duration)
            VALUES
                (:id, :user_id, :region_id, :region_name, :description, :pain_level, :duration)
        """),
        {
            "id": symptom_id,
            "user_id": report.user_id,
            "region_id": report.region_id,
            "region_name": report.region_name,
            "description": report.description,
            "pain_level": report.pain_level,
            "duration": report.duration,
        },
    )
    db.commit()
    return {"id": symptom_id, "message": "Đã lưu triệu chứng thành công"}


@router.get("/symptoms/{user_id}")
def get_symptoms(user_id: str, db: Session = Depends(get_db)):
    """Lấy lịch sử triệu chứng của một người dùng."""
    rows = db.execute(
        text("""
            SELECT id, region_id, region_name, description, pain_level, duration, reported_at
            FROM body_symptoms
            WHERE user_id = :user_id
            ORDER BY reported_at DESC
        """),
        {"user_id": user_id},
    ).fetchall()
    return {
        "total": len(rows),
        "symptoms": [
            {
                "id": str(r.id),
                "region_id": r.region_id,
                "region_name": r.region_name,
                "description": r.description,
                "pain_level": r.pain_level,
                "duration": r.duration,
                "reported_at": r.reported_at.isoformat() if r.reported_at else None,
            }
            for r in rows
        ],
    }


@router.delete("/symptoms/{symptom_id}")
def delete_symptom(symptom_id: str, db: Session = Depends(get_db)):
    """Xóa một khai báo triệu chứng."""
    result = db.execute(
        text("DELETE FROM body_symptoms WHERE id = :id"), {"id": symptom_id}
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(404, "Không tìm thấy triệu chứng")
    return {"message": "Đã xóa triệu chứng"}


@router.get("/symptoms")
def get_all_symptoms(limit: int = 50, db: Session = Depends(get_db)):
    """Lấy tất cả triệu chứng gần đây (admin/debug)."""
    rows = db.execute(
        text("""
            SELECT id, user_id, region_id, region_name, description, pain_level, duration, reported_at
            FROM body_symptoms
            ORDER BY reported_at DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).fetchall()
    return {
        "total": len(rows),
        "symptoms": [
            {
                "id": str(r.id),
                "user_id": str(r.user_id) if r.user_id else None,
                "region_id": r.region_id,
                "region_name": r.region_name,
                "description": r.description,
                "pain_level": r.pain_level,
                "duration": r.duration,
                "reported_at": r.reported_at.isoformat() if r.reported_at else None,
            }
            for r in rows
        ],
    }
