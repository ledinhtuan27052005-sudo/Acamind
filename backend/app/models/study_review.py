"""Append-only personal reviews of extracted study fields."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base


class StudyFieldReview(Base):
    __tablename__ = 'study_field_reviews'
    __table_args__ = (UniqueConstraint('document_id', 'user_id', 'criterion', 'revision', name='uq_study_review_revision'),)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reviewer_name = Column(String(255), nullable=False)
    criterion = Column(String(30), nullable=False)
    revision = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    value = Column(Text, nullable=False)
    note = Column(Text, nullable=False)
    # Snapshot retained even if indexing replaces the chunk later.
    chunk_id = Column(UUID(as_uuid=True), nullable=False)
    quote = Column(Text, nullable=False)
    page = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
