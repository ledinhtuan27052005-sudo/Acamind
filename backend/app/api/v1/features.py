"""
Features: translate, explain, trends, literature review, slides
"""
import os
import re
from typing import List, Optional
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.postgres import get_db
from app.models.document import Document, Chunk
from app.core.security import get_optional_user, get_current_user
from app.services.llm_client import get_default_client
from app.services.llm_client import llm_configuration_error

router = APIRouter()
llm_client = get_default_client()


def _call_llm(prompt: str, temperature: float = 0.3, max_tokens: int = 4096) -> str:
    return llm_client.complete(
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _stream_llm(messages: list, temperature: float = 0.3, max_tokens: int = 8192):
    # Tách system message (nếu có) ra khỏi messages — Gemini OpenAI-compat cần system là field riêng.
    system_content = None
    user_messages: list = []
    for m in messages:
        if m.get("role") == "system":
            system_content = m.get("content", "")
        else:
            user_messages.append(m)
    yield from llm_client.stream(
        messages=user_messages,
        system=system_content,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ── Translate ────────────────────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"   # "en" | "vi" | "auto"
    target_lang: str = "vi"     # "en" | "vi"


@router.post("/translate")
def translate_text(body: TranslateRequest):
    if not body.text.strip():
        raise HTTPException(400, "Văn bản không được để trống")
    if len(body.text) > 5000:
        raise HTTPException(400, "Văn bản tối đa 5.000 ký tự")

    lang_labels = {"en": "tiếng Anh", "vi": "tiếng Việt"}
    target_label = lang_labels.get(body.target_lang, "tiếng Việt")

    prompt = f"""Dịch đoạn văn sau sang {target_label}.

QUY TẮC BẮT BUỘC về thuật ngữ chuyên ngành:
- Nếu một từ/cụm từ là THUẬT NGỮ CHUYÊN NGÀNH (đặc biệt tâm lý học, y học, khoa học), hãy giữ nguyên thuật ngữ gốc tiếng Anh trong dấu ngoặc đơn ngay sau bản dịch tiếng Việt.
- Ví dụ: "rối loạn lo âu lan tỏa (Generalized Anxiety Disorder)", "hành vi tránh né (avoidance behavior)", "thiên kiến nhận thức (cognitive bias)".
- Các từ vựng thông thường thì dịch tự nhiên, KHÔNG cần thêm ngoặc.
- Giữ nguyên định dạng và cấu trúc câu gốc.
- CHỈ trả về bản dịch, không giải thích thêm.

Đoạn văn cần dịch:
{body.text}"""

    result = _call_llm(prompt, temperature=0.1, max_tokens=4096)
    return {"original": body.text, "translation": result.strip(), "target_lang": body.target_lang}


# ── Explain term ─────────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    term: str
    context: Optional[str] = None   # đoạn văn xung quanh từ đó
    language: str = "vi"            # ngôn ngữ trả lời
    document_ids: Optional[list[str]] = None  # ưu tiên RAG từ tài liệu upload


@router.post("/explain")
def explain_term(body: ExplainRequest):
    if not body.term.strip():
        raise HTTPException(400, "Thuật ngữ không được để trống")

    lang_map = {"vi": "tiếng Việt", "en": "English"}
    lang = lang_map.get(body.language, "tiếng Việt")

    # ── Bước 1: Tìm trong tài liệu upload (ưu tiên cao nhất) ────────────────
    doc_chunks = ""
    doc_sources = []
    if body.document_ids:
        try:
            from app.services.rag import retrieve_relevant_chunks
            chunks = retrieve_relevant_chunks(body.term, body.document_ids, top_k=5)
            if chunks:
                doc_chunks = "\n\n---\nTÀI LIỆU UPLOAD LIÊN QUAN (ưu tiên dùng nguồn này):\n"
                for i, ch in enumerate(chunks[:5], 1):
                    text = ch.get("text", "")[:600]
                    title = ch.get("doc_title") or ch.get("filename") or f"Tài liệu {i}"
                    page = ch.get("page_number", "?")
                    doc_chunks += f"\n[{i}] ({title}, trang {page}): {text}\n"
                    doc_sources.append({"doc_title": title, "page_number": page, "text": text})
        except Exception:
            pass

    # ── Bước 2: Build prompt — RAG-first, fallback web ──────────────────────
    ctx_part = f"\n\nNgữ cảnh sử dụng:\n\"{body.context}\"" if body.context else ""
    rag_part = doc_chunks if doc_chunks else ""

    if doc_chunks:
        # Có RAG → dùng nguồn từ tài liệu upload
        source_intro = "Dựa CHÍNH trên các đoạn trích từ tài liệu upload dưới đây (ưu tiên cao nhất), hãy giải thích:"
    else:
        # Không có RAG → dùng web search thông qua kiến thức của bạn
        source_intro = "Không tìm thấy trong tài liệu upload. Hãy dùng kiến thức chuẩn từ web/giáo trình tâm lý học uy tín (APA, WHO, ICD-11, DSM-5-TR, NIH) để giải thích:"

    prompt = f"""Giải thích thuật ngữ chuyên ngành tâm lý học sau đây bằng {lang}, **đúng chuẩn chuyên ngành nhất**.

{source_intro}{rag_part}{ctx_part}

YÊU CẦU BẮT BUỘC:
- Dùng định nghĩa chuẩn từ APA Dictionary of Psychology, DSM-5-TR, ICD-11, hoặc các giáo trình tâm lý học uy tín.
- Nếu thuật ngữ có nhiều nghĩa theo trường phái khác nhau (Phân tâm học, CBT, Nhân văn, Sinh học...), nêu rõ từng trường phái.
- KHÔNG đoán mò nếu không chắc chắn.

Trả lời theo cấu trúc:
1. **Định nghĩa** (1-2 câu, dùng ngôn ngữ học thuật)
2. **Lĩnh vực & bối cảnh** sử dụng
3. **Ví dụ cụ thể** trong nghiên cứu hoặc lâm sàng
4. **Thuật ngữ liên quan** (nếu có)

Thuật ngữ: **{body.term}**"""

    result = _call_llm(prompt, temperature=0.2, max_tokens=1024)
    return {
        "term": body.term,
        "explanation": result.strip(),
        "language": body.language,
        "source_type": "uploaded_docs" if doc_chunks else "web_fallback",
        "sources": doc_sources,
    }


# ── Trending Topics ──────────────────────────────────────────────────────────

STOP_WORDS_VI = {
    "và", "của", "trong", "với", "là", "các", "có", "một", "được", "này",
    "đến", "tại", "từ", "cho", "về", "bởi", "qua", "theo", "khi", "như",
    "không", "những", "hay", "nhưng", "mà", "thì", "đã", "sẽ", "đang",
    "vào", "ra", "lên", "xuống", "đây", "đó", "nào", "gì", "ai", "tôi",
    "bạn", "họ", "chúng", "hơn", "nhất", "rất", "cũng", "đều", "còn",
}

STOP_WORDS_EN = {
    "the", "a", "an", "in", "of", "to", "and", "for", "on", "with",
    "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "can", "this", "that", "these", "those", "it",
    "its", "by", "from", "at", "as", "or", "but", "not", "no", "so",
    "if", "than", "then", "their", "they", "we", "our", "your", "my",
    "he", "she", "his", "her", "which", "who", "what", "when", "where",
    "how", "all", "also", "into", "through", "during", "each",
}


def _extract_keywords(text: str, top_n: int = 50) -> list:
    words = re.findall(r"[a-zA-ZÀ-ỹ]{3,}", text.lower())
    stop = STOP_WORDS_VI | STOP_WORDS_EN
    filtered = [w for w in words if w not in stop and len(w) >= 4]
    counts = Counter(filtered)
    return [{"word": w, "count": c} for w, c in counts.most_common(top_n)]


@router.get("/trends")
def get_trends(db: Session = Depends(get_db)):
    """Trending keywords + topic distribution từ toàn bộ tài liệu."""
    docs = db.query(Document).filter(Document.status == "ready").all()

    all_text = " ".join(
        f"{d.title or ''} {d.authors or ''} {d.category or ''}"
        for d in docs
    )
    keywords = _extract_keywords(all_text, top_n=60)

    # Category breakdown
    cat_counts: Counter = Counter()
    year_counts: Counter = Counter()
    for d in docs:
        if d.category:
            cat_counts[d.category] += 1
        if d.year:
            year_counts[str(d.year)] += 1

    return {
        "total_documents": len(docs),
        "keywords": keywords,
        "categories": [{"name": k, "count": v} for k, v in cat_counts.most_common()],
        "years": sorted(
            [{"year": y, "count": c} for y, c in year_counts.items()],
            key=lambda x: x["year"],
        ),
    }


# ── Literature Review ────────────────────────────────────────────────────────

class LiteratureRequest(BaseModel):
    document_ids: List[str]
    focus: Optional[str] = None  # câu hỏi nghiên cứu tập trung


@router.post("/literature-review")
def literature_review(
    body: LiteratureRequest,
    db:   Session = Depends(get_db),
    user = Depends(get_current_user),
):
    if len(body.document_ids) < 1:
        raise HTTPException(400, "Cần ít nhất 1 tài liệu")
    if len(body.document_ids) > 10:
        raise HTTPException(400, "Tối đa 10 tài liệu")

    config_error = llm_configuration_error()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    docs = db.query(Document).filter(Document.id.in_(body.document_ids)).all()
    if not docs:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    # Get top chunks from each doc
    doc_summaries = []
    for doc in docs:
        chunks = db.query(Chunk).filter(Chunk.document_id == doc.id).limit(5).all()
        chunk_text = " ".join(c.content[:300] for c in chunks)
        doc_summaries.append(
            f"[{doc.title or doc.filename}] (Tác giả: {doc.authors or 'N/A'}, Năm: {doc.year or 'N/A'})\n{chunk_text}"
        )

    focus_part = f"\nCâu hỏi nghiên cứu: {body.focus}" if body.focus else ""
    prompt = f"""Bạn là chuyên gia viết tổng quan tài liệu nghiên cứu học thuật. Hãy viết một bài Literature Review tổng hợp từ {len(docs)} tài liệu sau:{focus_part}

{chr(10).join(doc_summaries)}

Viết theo cấu trúc:
## 1. Giới thiệu
## 2. Các chủ đề chính
## 3. Phương pháp nghiên cứu
## 4. Kết quả và phát hiện
## 5. Khoảng trống nghiên cứu
## 6. Kết luận

Viết bằng tiếng Việt, học thuật, có trích dẫn tên tác giả/năm trong ngoặc."""

    def stream_response():
        messages = [{"role": "user", "content": prompt}]
        yield from _stream_llm(messages, temperature=0.4, max_tokens=8192)

    return StreamingResponse(stream_response(), media_type="text/plain")


# ── AI Slides ────────────────────────────────────────────────────────────────

class SlidesRequest(BaseModel):
    document_id: str
    num_slides: int = 8
    style: str = "academic"  # "academic" | "simple" | "detailed"


@router.post("/slides")
def generate_slides(
    body: SlidesRequest,
    db:   Session = Depends(get_db),
    user = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == body.document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    chunks = db.query(Chunk).filter(Chunk.document_id == doc.id).limit(10).all()
    content = "\n".join(c.content[:400] for c in chunks)

    style_desc = {
        "academic": "học thuật, chuyên nghiệp, phù hợp hội thảo khoa học",
        "simple":   "đơn giản, dễ hiểu, phù hợp sinh viên",
        "detailed": "chi tiết, đầy đủ số liệu và trích dẫn",
    }.get(body.style, "học thuật")

    prompt = f"""Tạo outline bài thuyết trình {style_desc} gồm {body.num_slides} slides từ tài liệu:

Tiêu đề: {doc.title or doc.filename}
Tác giả: {doc.authors or "N/A"}
Năm: {doc.year or "N/A"}

Nội dung tài liệu:
{content}

Trả về JSON theo định dạng sau (không thêm markdown):
{{
  "title": "Tiêu đề bài thuyết trình",
  "subtitle": "Phụ đề",
  "slides": [
    {{
      "number": 1,
      "title": "Tiêu đề slide",
      "type": "title|content|chart|summary",
      "bullets": ["điểm 1", "điểm 2", "điểm 3"],
      "speaker_note": "Ghi chú cho người thuyết trình"
    }}
  ]
}}"""

    raw = _call_llm(prompt, temperature=0.4, max_tokens=8192)
    json_match = re.search(r"\{[\s\S]+\}", raw)
    if json_match:
        import json as json_lib
        try:
            slides_data = json_lib.loads(json_match.group())
        except Exception:
            slides_data = {"title": doc.title or doc.filename, "subtitle": "", "slides": [], "raw": raw}
    else:
        slides_data = {"title": doc.title or doc.filename, "subtitle": "", "slides": [], "raw": raw}

    return {"document": {"id": str(doc.id), "title": doc.title or doc.filename}, **slides_data}
