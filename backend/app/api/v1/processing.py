import os
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.core.security import get_current_user
from app.services.processing_jobs import STAGES, record_stage
from app.core.config import settings

router = APIRouter()


def owned_document(db, document_id, user, lock=False):
    query = db.query(Document).filter(Document.id == document_id)
    if lock:
        query = query.with_for_update()
    doc = query.first()
    if doc is None:
        raise HTTPException(404, 'Không tìm thấy tài liệu')
    if doc.user_id != user.id and user.role != 'admin':
        raise HTTPException(403, 'Chỉ chủ tài liệu hoặc quản trị viên được quản lý tác vụ')
    return doc


@router.get('/{document_id}/processing')
def processing_status(document_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    doc = owned_document(db, document_id, user)
    job = db.get(ProcessingJob, document_id)
    stage = doc.status if doc.status in ('ready', 'error', 'cancelled') else (job.stage if job else 'queued')
    return {'status': doc.status, 'stage': stage, 'label': 'Đã yêu cầu hủy; chờ kết thúc công đoạn hiện tại' if doc.status == 'cancel_requested' else STAGES.get(stage, stage),
            'updated_at': job.updated_at if job else None}


@router.post('/{document_id}/cancel-processing')
def cancel_processing(document_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    doc = owned_document(db, document_id, user, lock=True)
    if doc.status not in ('processing', 'cancel_requested', 'cancelled'):
        raise HTTPException(409, 'Tác vụ đã kết thúc; không thể hủy')
    if doc.status == 'processing':
        doc.status = 'cancel_requested'
    db.commit()
    return {'status': doc.status}


@router.post('/{document_id}/retry-processing')
def retry_processing(document_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from app.api.v1.document import _enqueue_pipeline, _QUEUED_LOCK, _QUEUED_DOC_IDS
    doc = owned_document(db, document_id, user, lock=True)
    with _QUEUED_LOCK:
        running = str(document_id) in _QUEUED_DOC_IDS
    if running or doc.status not in ('error', 'cancelled'):
        raise HTTPException(409, 'Tác vụ chưa dừng hoặc không cần thử lại')
    if not doc.file_path or not os.path.isfile(doc.file_path):
        raise HTTPException(409, 'Không còn PDF gốc; cần tải lại tệp')
    doc.status = 'processing'
    record_stage(db, document_id, 'queued')
    db.commit()
    try:
        _enqueue_pipeline(doc.file_path, str(document_id), settings.POSTGRES_URL)
    except Exception:
        doc.status = 'error'
        record_stage(db, document_id, 'error'); db.commit()
        raise HTTPException(503, 'Không thể đưa tác vụ vào hàng đợi. Hãy thử lại.')
    return {'status': 'processing'}
