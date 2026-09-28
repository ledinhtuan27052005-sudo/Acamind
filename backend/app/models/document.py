import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.postgres import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="student")  # "student" | "researcher" | "admin"
    plan = Column(String(50), default="free")     # "free" | "pro" | "researcher" | "enterprise"
    plan_expires_at = Column(DateTime, nullable=True)  # set for org members
    avatar_url = Column(String(1000), nullable=True)
    is_oauth = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    title = Column(String(1000))
    authors = Column(Text)
    year = Column(Integer)
    total_pages = Column(Integer)
    status = Column(String(50), default="processing")
    category = Column(String(100), nullable=True)
    is_paywall = Column(Boolean, default=False)
    # Phase A: cờ memory đã build xong (cho UI badge + filter nhanh)
    has_memory = Column(Boolean, default=False)
    memory_status = Column(String(50), default="pending")
    # Dedup: SHA-256 hex của file content, dùng để detect duplicate upload
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))
    page_number = Column(Integer)
    chunk_index = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)


class DocumentCategory(Base):
    __tablename__ = "document_categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(20), default="#6366f1")
    created_at = Column(DateTime, default=datetime.now)


class ResearcherApplication(Base):
    __tablename__ = "researcher_applications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # "pending" | "approved" | "rejected"
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    reviewed_at = Column(DateTime, nullable=True)


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    max_slots = Column(Integer, nullable=True)
    max_monthly_docs = Column(Integer, nullable=True)          # giới hạn tài liệu/tháng cho thành viên (student)
    max_monthly_docs_owner = Column(Integer, nullable=True)    # giới hạn tài liệu/tháng cho chủ tài khoản trường
    max_annual_docs_owner = Column(Integer, nullable=True)     # giới hạn tài liệu/năm cho chủ tài khoản (gói năm)
    package_type = Column(String(20), default="monthly")       # "monthly" | "annual"
    created_at = Column(DateTime, default=datetime.now)


class OrgInviteCode(Base):
    __tablename__ = "org_invite_codes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    duration_months = Column(Integer, nullable=False)   # 1 | 3 | 12 | 48
    max_uses = Column(Integer, nullable=True)            # None = unlimited
    used_count = Column(Integer, default=0)
    valid_until = Column(DateTime, nullable=True)        # None = forever
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class OrgMember(Base):
    __tablename__ = "org_members"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invite_code_id = Column(UUID(as_uuid=True), ForeignKey("org_invite_codes.id"), nullable=True)
    duration_months = Column(Integer, nullable=False)
    joined_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(20), default="active")       # active | expired | revoked


class EnterpriseTicket(Base):
    __tablename__ = "enterprise_tickets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    school_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String(20), default="open")   # open | in_progress | closed
    admin_note = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class EnterpriseOffer(Base):
    __tablename__ = "enterprise_offers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("enterprise_tickets.id", ondelete="SET NULL"), nullable=True)
    token = Column(String(32), unique=True, nullable=False)     # URL token
    school_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    amount = Column(Integer, nullable=False)                    # VNĐ tuỳ chỉnh
    duration_months = Column(Integer, default=12)
    package_type = Column(String(20), default="monthly")        # monthly | annual
    max_slots = Column(Integer, nullable=True)
    max_monthly_docs_member = Column(Integer, nullable=True)    # giới hạn /tháng cho học sinh
    max_monthly_docs_owner = Column(Integer, nullable=True)     # 550 (gói tháng)
    max_annual_docs_owner = Column(Integer, nullable=True)      # 7000 (gói năm)
    ref_code = Column(String(30), unique=True, nullable=False)  # ENT + random
    status = Column(String(20), default="draft")                # draft | active | paid | expired
    activated_email = Column(String(255), nullable=True)        # email user đã claim
    activated_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    type = Column(String(20), default="info")   # info | success | warning | system
    is_read = Column(Boolean, default=False)
    link = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan = Column(String(50), nullable=False)        # target plan: "pro" | "researcher"
    amount = Column(Integer, nullable=False)         # VNĐ
    ref_code = Column(String(30), unique=True, nullable=False)  # e.g. ACM3X9KF2
    status = Column(String(20), default="pending")  # "pending" | "completed" | "expired"
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
