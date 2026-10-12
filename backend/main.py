from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy import text
from pathlib import Path
from contextlib import asynccontextmanager
from app.api.v1 import api_router
from app.db.postgres import engine
from app.models.document import Base
# Import để Base.metadata.create_all biết về DocumentSummary
from app.models import document_summary  # noqa: F401
import logging

_logger = logging.getLogger(__name__)

# ── Tăng giới hạn body size cho upload file PDF lớn ──────────────────────────────
# Starlette mặc định giới hạn ~1MB. Tăng lên 200MB để upload file PDF lớn.
# Middleware này ép starlette.http.request.max_size cho mỗi request.
class LargeUploadMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int = 200 * 1024 * 1024):
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        # Cập nhật max_size cho mỗi request để upload lớn không bị reject
        # starlette.django multipart parser đọc từ request.max_size (mặc định ~1MB)
        try:
            request._max_size = self.max_upload_size
        except AttributeError:
            pass
        # Một số phiên bản starlette lưu ở _stream.max_size
        try:
            if hasattr(request, "_receive") and request._receive is not None:
                pass
        except Exception:
            pass
        return await call_next(request)

Base.metadata.create_all(bind=engine)

# Add new columns to existing tables if missing
try:
    _conn = engine.connect()
    _conn.execute(text("SET lock_timeout = '2s'"))
    _conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(1000)"))
    _conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_oauth BOOLEAN DEFAULT FALSE"))
    _conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(50) DEFAULT 'free'"))
    _conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_expires_at TIMESTAMP"))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS organizations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            max_slots INTEGER,
            max_monthly_docs INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    _conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS max_monthly_docs INTEGER"))
    _conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS max_monthly_docs_owner INTEGER"))
    _conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS max_annual_docs_owner INTEGER"))
    _conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS package_type VARCHAR(20) DEFAULT 'monthly'"))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS enterprise_tickets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            school_name VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            message TEXT,
            status VARCHAR(20) DEFAULT 'open',
            admin_note TEXT,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS enterprise_offers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ticket_id UUID REFERENCES enterprise_tickets(id) ON DELETE SET NULL,
            token VARCHAR(32) UNIQUE NOT NULL,
            school_name VARCHAR(255) NOT NULL,
            contact_email VARCHAR(255) NOT NULL,
            amount INTEGER NOT NULL,
            duration_months INTEGER DEFAULT 12,
            package_type VARCHAR(20) DEFAULT 'monthly',
            max_slots INTEGER,
            max_monthly_docs_member INTEGER,
            max_monthly_docs_owner INTEGER,
            max_annual_docs_owner INTEGER,
            ref_code VARCHAR(30) UNIQUE NOT NULL,
            status VARCHAR(20) DEFAULT 'draft',
            activated_email VARCHAR(255),
            activated_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP
        )
    """))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS org_invite_codes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            code VARCHAR(20) UNIQUE NOT NULL,
            duration_months INTEGER NOT NULL,
            max_uses INTEGER,
            used_count INTEGER DEFAULT 0,
            valid_until TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS org_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            invite_code_id UUID REFERENCES org_invite_codes(id),
            duration_months INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            UNIQUE(org_id, user_id)
        )
    """))
    _conn.execute(text("CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON org_members(user_id)"))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            plan VARCHAR(50) NOT NULL,
            amount INTEGER NOT NULL,
            ref_code VARCHAR(30) UNIQUE NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
    """))
    _conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_ref_code ON payments(ref_code)"))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            body TEXT,
            type VARCHAR(20) DEFAULT 'info',
            is_read BOOLEAN DEFAULT FALSE,
            link VARCHAR(500),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    _conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)"))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS email_otps (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL,
            otp VARCHAR(6) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            query TEXT NOT NULL,
            answer TEXT NOT NULL,
            document_ids JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ai_insights (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            insight_type VARCHAR(100) DEFAULT 'health_summary',
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS document_categories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) UNIQUE NOT NULL,
            color VARCHAR(20) DEFAULT '#6366f1',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    # Bảng lưu full text từng trang (cho retrieval chính xác Mục 3)
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS page_texts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            page_number INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(document_id, page_number)
        )
    """))
    _conn.execute(text("CREATE INDEX IF NOT EXISTS idx_page_texts_doc_id ON page_texts(document_id)"))

    # ── Phase A: Compressed memory cho mỗi document (build 1 lần lúc upload) ──
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS document_summaries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
            abstract TEXT,
            abstract_embedding VECTOR(768),
            topic_index JSONB DEFAULT '[]'::jsonb,
            key_facts JSONB DEFAULT '[]'::jsonb,
            entities JSONB DEFAULT '[]'::jsonb,
            memory_status VARCHAR(20) DEFAULT 'pending',
            memory_tokens_used INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """))
    # Defensive: nếu CREATE TABLE trên không pick up DEFAULT (vd thiếu pgcrypto),
    # ép ALTER thêm default. Idempotent.
    _conn.execute(text("ALTER TABLE document_summaries ALTER COLUMN id SET DEFAULT gen_random_uuid()"))
    _conn.execute(text("CREATE INDEX IF NOT EXISTS idx_doc_sum_status ON document_summaries(memory_status)"))
    _conn.execute(text("CREATE INDEX IF NOT EXISTS idx_doc_sum_doc_id ON document_summaries(document_id)"))

    # ── Phase C #1: FTS column + GIN index cho page_texts (thay in-memory BM25) ──
    # Generated column dùng 'simple' config (lowercase + tokenize) — không stem tiếng Việt,
    # nhưng recall vẫn ổn nhờ vector path. Phase 2 có thể thay 'unaccent' hoặc custom VN tokenizer.
    _conn.execute(text("""
        ALTER TABLE page_texts ADD COLUMN IF NOT EXISTS tsv tsvector
        GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED
    """))
    _conn.execute(text("CREATE INDEX IF NOT EXISTS idx_page_texts_tsv ON page_texts USING GIN(tsv)"))

    # ── Phase A: cờ memory đã build xong chưa (cho UI badge + filter nhanh) ──
    _conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS has_memory BOOLEAN DEFAULT FALSE"))
    _conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS memory_status VARCHAR(20) DEFAULT 'pending'"))
    _conn.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_memory ON documents(memory_status)"))

    # ── Dedup: content_hash column để detect duplicate file khi upload ──────────
    _conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64)"))
    # Partial unique index: chỉ enforce unique cho non-null hashes
    _conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_content_hash_unique
        ON documents(content_hash) WHERE content_hash IS NOT NULL
    """))

    # ── Paywall flag cho tài liệu trả phí ──────────────────────────────────────
    _conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS is_paywall BOOLEAN DEFAULT FALSE"))

    # ── Migrate old Vietnamese category names to English ──
    _vi_to_en_cats = {
        "Tâm lý lâm sàng": "Clinical Psychology",
        "Tâm lý nhận thức": "Cognitive Psychology",
        "Tâm lý hành vi": "Behavioral Psychology",
        "Tâm lý phát triển": "Developmental Psychology",
        "Tâm lý xã hội": "Social Psychology",
        "Thần kinh tâm lý": "Neuropsychology",
        "Tâm lý trị liệu": "Psychotherapy",
        "DSM / ICD / Chẩn đoán": "DSM / ICD / Diagnosis",
        "Phân tâm học": "Psychoanalysis",
        "Tâm lý sức khỏe": "Health Psychology",
        "Tâm lý học đường": "Educational Psychology",
        "Nghiên cứu & Thống kê": "Research & Statistics",
    }
    for _old, _new in _vi_to_en_cats.items():
        _conn.execute(
            text("UPDATE document_categories SET name = :new WHERE name = :old"),
            {"old": _old, "new": _new},
        )
        _conn.execute(
            text("UPDATE documents SET category = :new WHERE category = :old"),
            {"old": _old, "new": _new},
        )

    for _name, _color in [
        ("Clinical Psychology",              "#6366f1"),
        ("Cognitive Psychology",              "#3b82f6"),
        ("Behavioral Psychology",            "#10b981"),
        ("Developmental Psychology",         "#f59e0b"),
        ("Social Psychology",                "#ec4899"),
        ("Neuropsychology",                  "#06b6d4"),
        ("Psychotherapy",                    "#8b5cf6"),
        ("DSM / ICD / Diagnosis",            "#ef4444"),
        ("Psychoanalysis",                   "#e11d48"),
        ("Health Psychology",                "#0ea5e9"),
        ("Educational Psychology",           "#84cc16"),
        ("Research & Statistics",            "#6b7280"),
    ]:
        _conn.execute(
            text("INSERT INTO document_categories (id, name, color) VALUES (gen_random_uuid(), :n, :c) ON CONFLICT (name) DO NOTHING"),
            {"n": _name, "c": _color},
        )
    _conn.execute(text("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key         VARCHAR(100) PRIMARY KEY,
            value       TEXT NOT NULL DEFAULT '',
            description TEXT,
            updated_at  TIMESTAMP DEFAULT NOW()
        )
    """))
    for _k, _v, _d in [
        ("site_name",           "Acamind — AI Psychology",         "Display name of the system"),
        ("registration_open",   "true",                          "Allow new account registration"),
        ("maintenance_mode",    "false",                         "Enable maintenance mode"),
        ("maintenance_message", "",                              "Message shown during maintenance"),
        ("max_upload_mb",       "200",                           "Max upload file size (MB)"),
        ("default_plan",        "free",                          "Default plan for new accounts"),
        ("allow_google_auth",   "true",                          "Allow Google OAuth login"),
        ("ai_model",            "llama-3.3-70b-versatile",       "AI model in use (Groq)"),
        ("ai_temperature",      "0.3",                           "AI model temperature (0.0–1.0)"),
        ("max_context_chunks",  "5",                             "Max context chunks per question"),
    ]:
        _conn.execute(
            text("INSERT INTO system_settings (key, value, description) VALUES (:k,:v,:d) ON CONFLICT (key) DO NOTHING"),
            {"k": _k, "v": _v, "d": _d},
        )
    _conn.commit()
    _conn.close()
except Exception as _e:
    _logger.warning("Startup schema migration notice: %s", _e)

app = FastAPI(
    title="Acamind — Academic RAG System",
    description="Hệ thống hỏi đáp học thuật với RAG + Hybrid Search",
    version="1.0.0",
)

# ── Pre-warm ML models lúc startup để query đầu tiên không cold start 10-30s ─
# - sentence-transformers (E5): tải weights + load vào RAM (~10-30s)
# - FlagReranker (BGE): tải weights (~3-5s)
# Failures ở đây KHÔNG block server ready — model sẽ load lazy khi cần.
@app.on_event("startup")
def _warm_models_at_startup():
    import threading

    def _warm_worker():
        try:
            from app.services.embedder import _get_model
            model = _get_model()
            _ = model.encode(
                ["query: warmup", "passage: warmup"],
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            _logger.info(
                "Embedding model warmed OK (dim=%d)", model.get_sentence_embedding_dimension()
            )
        except Exception as e:
            _logger.warning("Embedding warmup failed (non-fatal, will load lazily): %s", e)

        try:
            import os as _os
            if _os.getenv("RERANK_BACKEND", "flag").lower() != "llm":
                from app.services.reranker import get_reranker
                reranker = get_reranker()
                _logger.info("Reranker warmed OK: %s", type(reranker._model).__name__ if hasattr(reranker, "_model") and reranker._model else "lazy")
        except Exception as e:
            _logger.warning("Reranker warmup failed (non-fatal, will load lazily): %s", e)

    threading.Thread(target=_warm_worker, daemon=True, name="model-warmup").start()

# Middleware phải được add theo thứ tự ngược: add cuối cùng = chạy đầu tiên
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Context-Pages", "X-Document-IDs"],
)
# Thêm middleware tăng giới hạn upload 200MB
app.add_middleware(LargeUploadMiddleware, max_upload_size=200 * 1024 * 1024)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "ok", "app": "Acamind", "docs": "/docs"}

@app.get("/health/db")
def db_health():
    from app.db.postgres import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"postgres": "ok"}
    except Exception as e:
        return {"postgres": "error", "detail": str(e)}
    finally:
        db.close()


@app.get("/health/readiness")
def readiness_health():
    """Expose non-sensitive prerequisites for the RAG workflow."""
    from sqlalchemy import func
    from app.core.config import settings
    from app.db.postgres import SessionLocal
    from app.models.document import Chunk, Document

    db = SessionLocal()
    try:
        ready_documents = db.query(func.count(Document.id)).filter(Document.status == "ready").scalar() or 0
        total_chunks = db.query(func.count(Chunk.id)).scalar() or 0
        llm_configured = bool(settings.GEMINI_API_KEY.strip())
        issues = []
        if not llm_configured:
            issues.append("Chưa cấu hình GEMINI_API_KEY cho dịch vụ tạo câu trả lời.")
        if ready_documents == 0:
            issues.append("Chưa có tài liệu ở trạng thái ready.")
        if total_chunks == 0:
            issues.append("Chưa có chunk đã lập chỉ mục để truy xuất RAG.")
        return {
            "ready_for_rag": not issues,
            "llm_configured": llm_configured,
            "llm_model": settings.LLM_MODEL,
            "ready_documents": ready_documents,
            "total_chunks": total_chunks,
            "issues": issues,
        }
    except Exception as e:
        return {
            "ready_for_rag": False,
            "llm_configured": False,
            "llm_model": "unknown",
            "ready_documents": 0,
            "total_chunks": 0,
            "issues": [f"Không thể kiểm tra trạng thái RAG: {str(e)}"],
        }
    finally:
        db.close()
