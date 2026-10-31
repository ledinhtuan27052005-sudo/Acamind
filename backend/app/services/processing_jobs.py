from datetime import datetime, timezone
from uuid import UUID
from app.models.document import Document
from app.models.processing_job import ProcessingJob

STAGES = {'queued': 'Đang chờ xử lý', 'parsing': 'Đọc PDF / OCR', 'chunking': 'Chia đoạn văn bản',
          'embedding': 'Tạo chỉ mục tìm kiếm', 'figures': 'Trích xuất hình và bảng',
          'ready': 'Hoàn tất', 'cancelled': 'Đã hủy', 'error': 'Xử lý thất bại'}


class ProcessingCancelled(Exception):
    pass


def record_stage(db, document_id, stage):
    did = UUID(str(document_id))
    job = db.get(ProcessingJob, did)
    if job is None:
        job = ProcessingJob(document_id=did)
        db.add(job)
    job.stage = stage
    job.updated_at = datetime.now(timezone.utc)


def checkpoint(db, document_id, stage):
    doc = db.query(Document).filter(Document.id == UUID(str(document_id))).populate_existing().with_for_update().first()
    if doc is None or doc.status not in ('processing', 'cancel_requested'):
        db.rollback()
        raise ProcessingCancelled()
    if doc.status == 'cancel_requested':
        doc.status = 'cancelled'
        record_stage(db, document_id, 'cancelled')
        db.commit()
        raise ProcessingCancelled()
    record_stage(db, document_id, stage)
    if stage in ('ready', 'error'):
        doc.status = stage
    db.commit()
