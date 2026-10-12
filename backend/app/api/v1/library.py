"""
Thư viện bài báo — đọc trực tiếp từ bảng `documents` (user upload qua /document/upload).
Không còn dùng folder DOCUMENT/ hay bảng library_articles.
Mỗi document upload lên → tự động xuất hiện trong thư viện.
"""
import re
import os
from typing import Optional, List
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from app.db.postgres import get_db
from app.models.document import Document, User, Chunk
from app.core.security import get_current_user, get_optional_user

router = APIRouter()

PAID_PLANS = {"pro", "researcher", "enterprise"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _can_access_paywall(user: Optional[User]) -> bool:
    if user is None:
        return False
    if user.role == "admin":
        return True
    return (getattr(user, "plan", "free") or "free") in PAID_PLANS


def _detect_language(filename: str) -> str:
    vi_chars = "àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
    if any(c in filename for c in vi_chars):
        return "vi"
    lower = filename.lower()
    vi_keywords = ["vietnamese", "viet", "việt", "văn bản", "bai", "bào", "báo", "trang",
                   "phac do", "phác đồ", "sổ tay", "roiloan", "tran", "cvv", "anxiety-and-worry",
                   "mot-so", "dieu-tri", "wpview"]
    return "vi" if any(k in lower for k in vi_keywords) else "en"


def _doc_to_article(doc: Document, user: Optional[User]) -> dict:
    """Convert Document row → dict format giống LibraryArticle để frontend không cần sửa."""
    title = (doc.title or "").strip() or (doc.filename or "Tài liệu không tên")
    is_paywall = bool(getattr(doc, "is_paywall", False))
    locked = is_paywall and not _can_access_paywall(user)
    return {
        "id":               str(doc.id),
        "document_id":      str(doc.id),
        "filename":         doc.filename,
        "file_path":        doc.file_path,
        "title_original":   title,
        "title_vi":         None,
        "authors":          doc.authors or "",
        "year":             doc.year,
        "journal":          None,
        "doi":              None,
        "language":         _detect_language(doc.filename or ""),
        "abstract_original": None,
        "abstract_vi":      None,
        "translation_vi":   None,
        "tags":             None,
        "is_paywall":       is_paywall,
        "cover_emoji":      "📄",
        "order_index":      0,
        "created_at":       doc.created_at.isoformat() if doc.created_at else None,
        "translation_locked": False,
        "pdf_locked":       locked,
        "total_pages":      doc.total_pages,
        "status":           doc.status,
        # Phase A: cờ memory đã build xong chưa (cho UI badge + filter nhanh)
        "has_memory":       bool(getattr(doc, "has_memory", False)),
        "memory_status":    getattr(doc, "memory_status", "pending"),
    }


def _query_ready_docs(db: Session, user: Optional[User]):
    """Lấy danh sách documents mà user có quyền xem (sẵn sàng + công khai/owner)."""
    from app.models.document import User as UserModel
    from sqlalchemy.orm import aliased

    UploaderAlias = aliased(UserModel)
    base = db.query(Document).outerjoin(UploaderAlias, Document.user_id == UploaderAlias.id)

    if user and user.role == "admin":
        return base
    if user:
        return base.filter(
            or_(
                Document.user_id == user.id,
                Document.user_id == None,
                UploaderAlias.role.in_(["admin", "researcher"]),
            )
        )
    return base.filter(
        or_(
            Document.user_id == None,
            UploaderAlias.role.in_(["admin", "researcher"]),
        )
    )


# ── Public endpoints ──────────────────────────────────────────────────────────

@router.get("/articles")
def list_articles(
    search: Optional[str] = Query(None),
    lang:   Optional[str] = Query(None),
    db:     Session = Depends(get_db),
    user:   Optional[User] = Depends(get_optional_user),
):
    """Liệt kê tài liệu trong thư viện (= các document đã upload + ready)."""
    q = _query_ready_docs(db, user).filter(Document.status == "ready")
    if search:
        t = f"%{search}%"
        q = q.filter(
            Document.title.ilike(t) |
            Document.filename.ilike(t) |
            Document.authors.ilike(t)
        )
    docs = q.order_by(Document.created_at.desc()).all()
    if lang in ("en", "vi"):
        docs = [d for d in docs if _detect_language(d.filename or "") == lang]
    return [_doc_to_article(d, user) for d in docs]


@router.get("/articles/{article_id}")
def get_article(
    article_id: str,
    db:   Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Chi tiết 1 tài liệu (article_id = document_id)."""
    doc = db.query(Document).filter(Document.id == article_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    return _doc_to_article(doc, user)


@router.get("/articles/{article_id}/pdf")
def get_article_pdf(
    article_id: str,
    db:   Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Trả về file PDF của document. Paywall: chỉ Pro+ mới xem được (admin luôn pass)."""
    doc = db.query(Document).filter(Document.id == article_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(404, "File PDF không tồn tại trên server")
    # Check paywall
    if getattr(doc, "is_paywall", False) and not _can_access_paywall(user):
        raise HTTPException(403, "Tài liệu paywall. Nâng cấp gói Pro trở lên để truy cập.")
    return FileResponse(
        path=doc.file_path,
        media_type="application/pdf",
        filename=doc.filename,
        headers={"Content-Disposition": "inline"},
    )


# ── Admin endpoints ───────────────────────────────────────────────────────────

class ArticleUpdate(BaseModel):
    title_original:   Optional[str]  = None
    title_vi:         Optional[str]  = None
    authors:          Optional[str]  = None
    year:             Optional[int]  = None
    journal:          Optional[str]  = None
    doi:              Optional[str]  = None
    language:         Optional[str]  = None
    abstract_original: Optional[str] = None
    abstract_vi:      Optional[str]  = None
    translation_vi:   Optional[str]  = None
    tags:             Optional[str]  = None
    is_paywall:       Optional[bool] = None
    cover_emoji:      Optional[str]  = None
    order_index:      Optional[int]  = None


@router.patch("/admin/articles/{article_id}")
def update_article(
    article_id: str,
    body: ArticleUpdate,
    db:   Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cập nhật metadata tài liệu (chỉ admin)."""
    if user.role != "admin":
        raise HTTPException(403, "Chỉ admin mới được cập nhật")
    doc = db.query(Document).filter(Document.id == article_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    # Map từ schema LibraryArticle cũ → Document fields
    field_map = {
        "title_original": "title",
        "authors":        "authors",
        "year":           "year",
        "is_paywall":     "is_paywall",
    }
    for src, dst in field_map.items():
        value = getattr(body, src, None)
        if value is not None:
            setattr(doc, dst, value)

    db.commit()
    db.refresh(doc)
    return _doc_to_article(doc, user)


@router.delete("/admin/articles/{article_id}")
def delete_article(
    article_id: str,
    db:   Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Xoá tài liệu (chỉ admin)."""
    if user.role != "admin":
        raise HTTPException(403, "Chỉ admin mới được xoá")
    doc = db.query(Document).filter(Document.id == article_id).first()
    if not doc:
        raise HTTPException(404)
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass
    db.delete(doc)
    db.commit()
    return {"ok": True}


# ── Authors ───────────────────────────────────────────────────────────────────

def _parse_authors(raw: Optional[str]) -> List[str]:
    """Split 'Author A, Author B; Author C' → ['Author A', 'Author B', 'Author C']"""
    if not raw:
        return []
    parts = re.split(r"[,;]", raw)
    return [p.strip() for p in parts if p.strip()]


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.get("/authors")
def list_authors(
    search: Optional[str] = Query(None),
    db:     Session = Depends(get_db),
):
    """Danh sách tác giả tổng hợp từ documents."""
    docs = _query_ready_docs(db, None).filter(Document.status == "ready").all()

    author_map: dict = defaultdict(list)
    for doc in docs:
        for author in _parse_authors(doc.authors):
            author_map[author].append({
                "id":             str(doc.id),
                "title_original": doc.title or doc.filename,
                "title_vi":       None,
                "year":           doc.year,
                "journal":        None,
                "language":       _detect_language(doc.filename or ""),
                "is_paywall":     False,
                "cover_emoji":    "📄",
            })

    results = []
    for name, arts in author_map.items():
        if search and search.lower() not in name.lower():
            continue
        years = [a["year"] for a in arts if a["year"]]
        results.append({
            "name":          name,
            "slug":          _slug(name),
            "article_count": len(arts),
            "articles":      arts,
            "year_range":    [min(years), max(years)] if years else None,
            "languages":     list({a["language"] for a in arts}),
        })

    results.sort(key=lambda x: -x["article_count"])
    return {"total": len(results), "authors": results}


@router.get("/authors/{slug}")
def get_author(
    slug: str,
    db:   Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Get author details by slug."""
    docs = _query_ready_docs(db, user).filter(Document.status == "ready").all()
    name = None
    author_articles = []
    for doc in docs:
        for author in _parse_authors(doc.authors):
            if _slug(author) == slug:
                if name is None:
                    name = author
                author_articles.append(_doc_to_article(doc, user))
    if not name:
        raise HTTPException(404, "Author not found")
    return {
        "name":     name,
        "slug":     slug,
        "articles": author_articles,
    }


# ── Cross-article analysis ────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    article_ids: List[str]


@router.post("/analysis")
def analyze_articles(
    body: AnalysisRequest,
    db:   Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Compare multiple documents using AI."""
    if len(body.article_ids) < 2:
        raise HTTPException(400, "At least 2 documents are required for comparison")
    if len(body.article_ids) > 8:
        raise HTTPException(400, "Maximum 8 documents per analysis")

    docs = db.query(Document).filter(Document.id.in_(body.article_ids)).all()
    if len(docs) < 2:
        raise HTTPException(404, "Could not find enough requested documents")

    context_lines = []
    for i, doc in enumerate(docs, 1):
        # Use actual indexed passages, not metadata alone.  This makes the
        # cross-article synthesis grounded in the uploaded sources and allows
        # the model to compare findings/methods rather than merely titles.
        chunks = (
            db.query(Chunk)
            .filter(Chunk.document_id == doc.id)
            .order_by(Chunk.chunk_index)
            .limit(8)
            .all()
        )
        excerpts = "\n".join(
            f"[Page {chunk.page_number or '?'}] {chunk.content[:700]}"
            for chunk in chunks
            if chunk.content
        )
        context_lines.append(
            f"[Document {i}] {doc.title or doc.filename}"
            + (f"\nAuthors: {doc.authors}" if doc.authors else "")
            + (f"\nYear: {doc.year}" if doc.year else "")
            + (f"\nSource excerpts:\n{excerpts}" if excerpts else "\nSource excerpts: unavailable")
        )
    context = "\n\n".join(context_lines)

    prompt = f"""You are an expert academic research analyst. Compare the following {len(docs)} documents:

{context}

Respond EXACTLY in the following JSON format (no markdown, no extra explanation):
{{
  "summary": "A 2-3 sentence comparative overview",
  "common_themes": [{{"theme": "theme name", "explanation": "brief explanation"}}],
  "differences": [{{"aspect": "aspect name", "difference": "brief description"}}],
  "comparison_table": [
    {{"factor": "Factor name", "values": ["value for document 1", "value for document 2", ...]}}
  ],
  "research_gaps": [{{"gap": "research gap name", "implication": "brief implication"}}],
  "recommendation": "Suggestions for further reading or research directions"
}}

IMPORTANT: Always respond in English. Do NOT use any markdown formatting in any of the values.
"""

    try:
        from app.services.llm_client import get_default_client
        client = get_default_client()
        raw = client.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096,
        )
        json_match = re.search(r"\{[\s\S]+\}", raw)
        if json_match:
            import json
            analysis = json.loads(json_match.group())
        else:
            analysis = {"summary": raw, "common_themes": [], "differences": [], "comparison_table": [], "research_gaps": [], "recommendation": ""}
    except Exception as e:
        analysis = {
            "summary": f"AI analysis failed: {str(e)}",
            "common_themes": [],
            "differences": [],
            "comparison_table": [],
            "research_gaps": [],
            "recommendation": "",
        }

    return {
        "articles": [_doc_to_article(d, user) for d in docs],
        "analysis": analysis,
    }
