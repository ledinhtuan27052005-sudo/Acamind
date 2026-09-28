import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.db.postgres import get_db

router = APIRouter()

ONBOARDING_QUESTIONS = [
    {
        "id": "q1",
        "question": "Bạn là ai trong lĩnh vực y tế?",
        "options": [
            {"value": "patient", "label": "Bệnh nhân / Người quan tâm sức khỏe"},
            {"value": "student", "label": "Sinh viên y khoa / Điều dưỡng"},
            {"value": "expert", "label": "Bác sĩ / Chuyên gia y tế"},
        ],
    },
    {
        "id": "q2",
        "question": "Mục đích chính khi sử dụng hệ thống?",
        "options": [
            {"value": "symptom_check", "label": "Tìm hiểu triệu chứng & bệnh lý"},
            {"value": "study", "label": "Học tập / Nghiên cứu tài liệu y khoa"},
            {"value": "clinical", "label": "Hỗ trợ công việc lâm sàng"},
        ],
    },
    {
        "id": "q3",
        "question": "Trình độ kiến thức y khoa của bạn?",
        "options": [
            {"value": "basic", "label": "Cơ bản — chỉ biết các kiến thức phổ thông"},
            {"value": "intermediate", "label": "Trung bình — đang học hoặc mới tốt nghiệp"},
            {"value": "advanced", "label": "Nâng cao — có kinh nghiệm lâm sàng"},
        ],
    },
]

USER_TYPE_MAP = {
    ("patient", "symptom_check", "basic"): "patient",
    ("patient", "symptom_check", "intermediate"): "patient",
    ("student", "study", "intermediate"): "student",
    ("student", "study", "basic"): "student",
    ("expert", "clinical", "advanced"): "expert",
}


def _infer_user_type(answers: dict) -> str:
    q1 = answers.get("q1", "patient")
    if q1 == "expert":
        return "expert"
    if q1 == "student":
        return "student"
    return "patient"


class OnboardingSubmit(BaseModel):
    user_id: Optional[str] = None
    answers: dict


@router.get("/questions")
def get_questions():
    return {"questions": ONBOARDING_QUESTIONS}


@router.post("/submit")
def submit_onboarding(req: OnboardingSubmit, db: Session = Depends(get_db)):
    user_type = _infer_user_type(req.answers)

    if req.user_id:
        existing = db.execute(
            text("SELECT id FROM user_profiles WHERE user_id = :uid"),
            {"uid": req.user_id},
        ).first()
        import json
        if existing:
            db.execute(
                text("""
                    UPDATE user_profiles
                    SET user_type = :utype, onboarding_done = TRUE, answers = cast(:ans AS jsonb)
                    WHERE user_id = :uid
                """),
                {"utype": user_type, "ans": json.dumps(req.answers), "uid": req.user_id},
            )
        else:
            db.execute(
                text("""
                    INSERT INTO user_profiles (id, user_id, user_type, onboarding_done, answers)
                    VALUES (:id, :uid, :utype, TRUE, cast(:ans AS jsonb))
                """),
                {
                    "id": str(uuid.uuid4()),
                    "uid": req.user_id,
                    "utype": user_type,
                    "ans": json.dumps(req.answers),
                },
            )
        db.commit()

    return {"user_type": user_type, "message": "Phân loại thành công"}


@router.get("/status/{user_id}")
def get_status(user_id: str, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT user_type, onboarding_done FROM user_profiles WHERE user_id = :uid"),
        {"uid": user_id},
    ).first()
    if not row:
        return {"onboarding_done": False, "user_type": "patient"}
    return {"onboarding_done": row.onboarding_done, "user_type": row.user_type}
