from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base


class ProcessingJob(Base):
    __tablename__ = 'document_processing_jobs'
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True)
    stage = Column(String(40), nullable=False, default='queued')
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
