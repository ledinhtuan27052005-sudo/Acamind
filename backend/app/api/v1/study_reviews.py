from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.postgres import get_db
from app.core.security import get_current_user
from app.models.document import Document, Chunk, User
from app.models.study_review import StudyFieldReview
from app.services.study_profile import FIELDS

router = APIRouter()


class ReviewInput(BaseModel):
    expected_revision: int = Field(ge=0)
    status: Literal['draft', 'confirmed']
    value: str = Field(min_length=1, max_length=4000)
    note: str = Field(default='', max_length=1000)
    chunk_id: UUID
    quote: str = Field(min_length=15, max_length=50000)


def check_document(document_id, criterion, db, user):
    from app.api.v1.document import _enforce_doc_read_access
    if criterion not in FIELDS:
        raise HTTPException(422, 'Tiêu chí không hợp lệ')
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc is None:
        raise HTTPException(404, 'Không tìm thấy tài liệu')
    _enforce_doc_read_access(doc, user, db)


def serialize(row):
    return {key: getattr(row, key) for key in ('revision', 'status', 'value', 'note', 'quote', 'page', 'created_at', 'reviewer_name')} | {
        'chunk_id': str(row.chunk_id)}


def scoped_reviews(db, document_id, criterion, user):
    return db.query(StudyFieldReview).filter(StudyFieldReview.document_id == document_id,
        StudyFieldReview.user_id == user.id, StudyFieldReview.criterion == criterion)


@router.get('/study-profile/{document_id}/reviews/{criterion}')
def review_history(document_id: UUID, criterion: str, before: int | None = Query(default=None, ge=1),
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_document(document_id, criterion, db, user)
    query = scoped_reviews(db, document_id, criterion, user)
    if before is not None:
        query = query.filter(StudyFieldReview.revision < before)
    rows = query.order_by(StudyFieldReview.revision.desc()).limit(21).all()
    return {'items': [serialize(r) for r in rows[:20]],
            'next_before': rows[19].revision if len(rows) > 20 else None}


@router.post('/study-profile/{document_id}/reviews/{criterion}')
def save_review(document_id: UUID, criterion: str, body: ReviewInput,
                db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_document(document_id, criterion, db, user)
    if not body.value.strip() or len(body.quote.strip()) < 15:
        raise HTTPException(422, 'Nội dung và đoạn nguồn không được để trống')
    chunk = db.query(Chunk).filter(Chunk.id == body.chunk_id, Chunk.document_id == document_id).first()
    if chunk is None or body.quote not in chunk.content or type(chunk.page_number) is not int or chunk.page_number < 1:
        raise HTTPException(422, 'Đoạn trích phải khớp nguồn gốc của đúng tài liệu. Hãy tải lại nguồn.')
    # Serializes first writes too; optimistic revision detects stale browser tabs.
    db.query(User).filter(User.id == user.id).with_for_update().one()
    latest = scoped_reviews(db, document_id, criterion, user).order_by(StudyFieldReview.revision.desc()).first()
    revision = latest.revision if latest else 0
    if body.expected_revision != revision:
        db.rollback()
        raise HTTPException(409, 'Dữ liệu đã thay đổi. Tải lại lịch sử trước khi lưu.')
    row = StudyFieldReview(document_id=document_id, user_id=user.id, criterion=criterion,
        revision=revision + 1, status=body.status, value=body.value.strip(), note=body.note.strip(),
        chunk_id=body.chunk_id, quote=body.quote, page=chunk.page_number,
        reviewer_name=(user.full_name or 'Người dùng')[:255])
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Có thay đổi đồng thời. Tải lại lịch sử trước khi lưu.')
    db.refresh(row)
    return serialize(row)
