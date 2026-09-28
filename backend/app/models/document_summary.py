"""Model cho bảng document_summaries — compressed memory của mỗi document.

Mỗi document có tối đa 1 row. Build 1 lần lúc upload bằng `memory_builder.build_memory_for_doc`.
Sau đó được dùng bởi `retriever.retrieve_via_memory` (L1 fast path).
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.db.postgres import Base


class DocumentSummary(Base):
    __tablename__ = "document_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # UNIQUE: mỗi document chỉ có 1 memory
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Abstract 200-400 từ tóm tắt tài liệu
    abstract = Column(Text)

    # Embed của abstract — dùng cho L1 cosine match để chọn top 3 docs
    abstract_embedding = Column(Vector(768))

    # Mục lục semantic: [{"topic": "...", "page_start": 1, "page_end": 5}, ...]
    topic_index = Column(JSONB, default=list)

    # Key facts: [{"claim": "...", "page": 5, "confidence": 0.9}, ...]
    # 20-200 facts tuỳ kích thước doc. Cap 200 trong memory_builder.
    key_facts = Column(JSONB, default=list)

    # Entities: [{"name": "Freud", "type": "person", "page": 12}, ...]
    # type ∈ {"person", "theory", "term", "formula"}
    entities = Column(JSONB, default=list)

    # pending → building → ready | failed
    memory_status = Column(String(20), default="pending")

    # Track token usage để estimate cost
    memory_tokens_used = Column(Integer, default=0)

    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
