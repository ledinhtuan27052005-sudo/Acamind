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
def explain_term(body: ExplainRequest, db: Session = Depends(get_db)):
    if not body.term.strip():
        raise HTTPException(400, "Thuật ngữ không được để trống")

    lang_map = {"vi": "tiếng Việt", "en": "English"}
    lang = lang_map.get(body.language, "tiếng Việt")

    # ── Bước 1: Tìm trong kho tài liệu lâm sàng (L1 Fast Memory + L2 Deep Hybrid RAG) ──
    doc_chunks = ""
    doc_sources = []
    telemetry_info = None
    try:
        from app.services.retriever import retrieve, retrieve_via_memory
        from app.services.authority_scorer import score_document_authority
        from app.services.scientific_appraiser import (
            evaluate_cebm_evidence_level,
            generate_apa7_citation,
            generate_bibtex_entry,
            strip_academic_header_and_boilerplate,
        )

        search_ids = body.document_ids if (body.document_ids and len(body.document_ids) <= 15) else None
        chunks = None
        if search_ids and len(search_ids) <= 5:
            try:
                chunks = retrieve_via_memory(body.term, search_ids, db, top_k=5)
            except Exception:
                try:
                    db.rollback()
                except Exception:
                    pass
                chunks = None

        if not chunks:
            chunks = retrieve(body.term, search_ids, db, top_k=6)

        if chunks:
            telemetry_info = chunks[0].get("_telemetry")
            doc_chunks = "\n\n---\nTÀI LIỆU LÂM SÀNG LIÊN QUAN TRONG KHO (ưu tiên trích dẫn nguồn này):\n"
            seen_doc_page: set[tuple[str, int]] = set()
            for i, ch in enumerate(chunks[:6], 1):
                did = str(ch.get("document_id") or "")
                page = int(ch.get("page_number") or 1)
                if (did, page) in seen_doc_page:
                    continue
                seen_doc_page.add((did, page))
                raw_txt = ch.get("parent_context") or ch.get("content") or ""
                title = ch.get("doc_title") or ch.get("doc_filename") or f"Tài liệu {i}"
                fname = ch.get("doc_filename") or title
                authors = ch.get("doc_authors") or ""
                clean_txt = strip_academic_header_and_boilerplate(raw_txt, paper_title=title)[:650]
                if not clean_txt:
                    clean_txt = (ch.get("content") or "")[:600]

                doc_dict = {
                    "id": did,
                    "filename": fname,
                    "title": title,
                    "authors": authors,
                    "year": 2024,
                }
                _, tier_name, tier_label = score_document_authority(doc_dict, clean_txt)
                cebm_info = evaluate_cebm_evidence_level([doc_dict], [ch])
                apa7_str = generate_apa7_citation(doc_dict).rstrip(".") + f" (p. {page})."
                bibtex_str = generate_bibtex_entry(doc_dict)

                doc_chunks += f"\n[{len(doc_sources) + 1}] [{fname} - Page {page}] (Tiêu đề: {title} | Tác giả: {authors or 'N/A'}):\n{clean_txt}\n"
                doc_sources.append({
                    "document_id": did,
                    "doc_title": title,
                    "doc_filename": fname,
                    "doc_authors": authors,
                    "page_number": page,
                    "text": clean_txt,
                    "authority_tier": tier_name,
                    "authority_label": tier_label,
                    "cebm_level": cebm_info.get("level", "2b"),
                    "cebm_label": cebm_info.get("level_label", "Cấp 2B"),
                    "apa7": apa7_str,
                    "bibtex": bibtex_str,
                })
                if len(doc_sources) >= 5:
                    break
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass

    # ── Bước 2: Build prompt — RAG-first, fallback web ──────────────────────
    ctx_part = f"\n\nNgữ cảnh sử dụng:\n\"{body.context}\"" if body.context else ""
    rag_part = doc_chunks if doc_chunks else ""

    if doc_chunks:
        source_intro = (
            "Dựa CHÍNH XÁC trên các đoạn trích từ kho tài liệu lâm sàng dưới đây (ưu tiên cao nhất), "
            "hãy giải thích thuật ngữ và GẮN NHÃN TRÍCH DẪN SỐ TRANG theo đúng định dạng `[Tên_file.pdf - Trang X]` "
            "(hoặc `[Tên_file.pdf - Page X]`) ngay sau câu giải thích:"
        )
    else:
        source_intro = "Không tìm thấy trong tài liệu upload. Hãy dùng kiến thức chuẩn từ giáo trình tâm lý học uy tín (APA, WHO, ICD-11, DSM-5-TR, NIH) để giải thích:"

    prompt = f"""Giải thích thuật ngữ chuyên ngành tâm lý học sau đây bằng {lang}, **đúng chuẩn chuyên ngành nhất**.

{source_intro}{rag_part}{ctx_part}

YÊU CẦU BẮT BUỘC:
- Dùng định nghĩa chuẩn từ APA Dictionary of Psychology, DSM-5-TR, ICD-11, hoặc các bài báo thực nghiệm trong kho tài liệu.
- Nếu có đoạn trích từ kho tài liệu ở trên, BẮT BUỘC trích dẫn rõ `[Tên_file.pdf - Trang X]` ngay trong bài giải thích.
- Nếu thuật ngữ có nhiều nghĩa theo trường phái khác nhau (Phân tâm học, CBT, Nhân văn, Sinh học thần kinh...), nêu rõ từng trường phái.
- KHÔNG đoán mò nếu không chắc chắn.

Trả lời theo cấu trúc:
1. **Định nghĩa học thuật** (1-3 câu chuẩn xác kèm trích dẫn `[Tên_file.pdf - Trang X]` nếu có)
2. **Lĩnh vực & Bối cảnh lâm sàng / nghiên cứu**
3. **Ví dụ thực nghiệm hoặc tiêu chuẩn đo lường cụ thể** (nêu rõ thang đo, cỡ mẫu hoặc cơ chế trong tài liệu)
4. **Thuật ngữ liên quan**

Thuật ngữ: **{body.term}**"""

    result = _call_llm(prompt, temperature=0.2, max_tokens=1200)
    return {
        "term": body.term,
        "explanation": result.strip(),
        "language": body.language,
        "source_type": "uploaded_docs" if doc_chunks else "web_fallback",
        "sources": doc_sources,
        "telemetry": telemetry_info,
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


# ── Literature Review (4-Attribute Clinical Evidence Matrix + Synthesis) ─────

class LiteratureRequest(BaseModel):
    document_ids: List[str]
    focus: Optional[str] = None  # câu hỏi nghiên cứu tập trung


def _build_literature_matrix_and_summaries(
    docs: list[Document],
    focus: Optional[str],
    db: Session,
) -> tuple[list[dict], list[str]]:
    """Trích xuất Ma trận Bằng chứng 4 Thuộc tính (Methodology/Intervention, Psychometric Scale/Metric,
    Key Finding/Effect Size, Page Citation) kèm Cấp độ Bằng chứng CEBM và APA 7th cho từng tài liệu.
    """
    from sqlalchemy import text as sql_text
    from app.services.retriever import retrieve
    from app.services.authority_scorer import score_document_authority
    from app.services.scientific_appraiser import (
        evaluate_cebm_evidence_level,
        extract_structured_study_cells,
        generate_apa7_citation,
        generate_bibtex_entry,
        strip_academic_header_and_boilerplate,
    )

    matrix_rows: list[dict] = []
    doc_summaries: list[str] = []

    for doc in docs:
        did = str(doc.id)
        fname = doc.filename or "Document.pdf"
        title = doc.title or fname
        authors = doc.authors or "N/A"
        year = doc.year or 2024

        # 1. Lấy các chunk liên quan theo focus query (nếu có) + các chunk đầu bài báo (trang 1-3)
        matching_chunks: list[dict] = []
        if focus and focus.strip():
            try:
                retrieved = retrieve(focus.strip(), [did], db, top_k=5)
                matching_chunks.extend(retrieved)
            except Exception:
                try:
                    db.rollback()
                except Exception:
                    pass

        early_db_chunks = (
            db.query(Chunk)
            .filter(Chunk.document_id == doc.id)
            .order_by(Chunk.page_number.asc())
            .limit(8)
            .all()
        )
        seen_cids = {str(c.get("id")) for c in matching_chunks if c.get("id")}
        for idx_c, ch in enumerate(early_db_chunks):
            if str(ch.id) not in seen_cids:
                matching_chunks.append({
                    "id": str(ch.id),
                    "content": ch.content or "",
                    "page_number": ch.page_number or 1,
                    "document_id": did,
                    "rrf_score": round(0.025 - idx_c * 0.002, 4),
                    "doc_title": title,
                    "doc_authors": authors,
                    "doc_filename": fname,
                })

        # 2. Lấy page_texts của các trang xuất hiện để bóc tách câu đầy đủ không bị cụt
        page_nums = sorted({int(c.get("page_number") or 1) for c in matching_chunks} | {1, 2})
        page_texts_map: dict[tuple[str, int], str] = {}
        try:
            p_rows = db.execute(
                sql_text("""
                    SELECT page_number, content
                    FROM page_texts
                    WHERE document_id = :did AND page_number = ANY(:pnos)
                """),
                {"did": did, "pnos": page_nums},
            ).fetchall()
            for pr in p_rows:
                page_texts_map[(fname, int(pr.page_number))] = pr.content or ""
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

        # 3. Bóc tách 4 thuộc tính thực chứng bằng Structure-Aware Disjoint Slot Extractor
        cells = extract_structured_study_cells(
            paper_title=title,
            filename=fname,
            matching_chunks=matching_chunks,
            page_texts_map=page_texts_map,
        )

        raw_cite = cells.get("page_citation", f"[{fname} - Page 1]")
        p_match = re.search(r"(?:Page|Trang)\s*(\d+)", raw_cite, re.IGNORECASE)
        primary_page = int(p_match.group(1)) if p_match else 1

        sample_content = " ".join((c.get("content") or "")[:400] for c in matching_chunks[:4])
        doc_dict = {
            "id": did,
            "filename": fname,
            "title": title,
            "authors": authors if authors != "N/A" else "",
            "year": year,
        }
        _, tier_name, tier_label = score_document_authority(doc_dict, sample_content)
        cebm_info = evaluate_cebm_evidence_level([doc_dict], matching_chunks)
        apa7_str = generate_apa7_citation(doc_dict).rstrip(".") + f" (p. {primary_page})."
        bibtex_str = generate_bibtex_entry(doc_dict)

        row_item = {
            "document_id": did,
            "filename": fname,
            "title": title,
            "authors": authors,
            "year": year,
            "authority_tier": tier_name,
            "authority_label": tier_label,
            "cebm_level": cebm_info.get("level", "2b"),
            "cebm_label": cebm_info.get("level_label", "Cấp 2B"),
            "study_design": cebm_info.get("study_design", ""),
            "methodology": cells.get("methodology", ""),
            "scale_or_metric": cells.get("scale_or_metric", ""),
            "finding": cells.get("finding", ""),
            "page_citation": raw_cite,
            "primary_page": primary_page,
            "supporting_pages": cells.get("all_supporting_pages", [primary_page]),
            "apa7": apa7_str,
            "bibtex": bibtex_str,
        }
        matrix_rows.append(row_item)

        clean_excerpts = []
        for ch in matching_chunks[:4]:
            pno = int(ch.get("page_number") or 1)
            cleaned_c = strip_academic_header_and_boilerplate(ch.get("content") or "", paper_title=title)[:400]
            if cleaned_c:
                clean_excerpts.append(f"  • [Trang {pno}]: {cleaned_c}")

        doc_summaries.append(
            f"=== TÀI LIỆU: [{fname}] ===\n"
            f"- Tiêu đề: {title}\n"
            f"- Tác giả: {authors} ({year}) | Cấp độ bằng chứng: {cebm_info.get('level_label', '')} ({cebm_info.get('study_design', '')})\n"
            f"- Phương pháp & Can thiệp (Methodology): {cells.get('methodology', '')}\n"
            f"- Thang đo / Tập dữ liệu / Chỉ số (Scale & Metric): {cells.get('scale_or_metric', '')}\n"
            f"- Phát hiện chính & Cỡ hiệu ứng (Key Finding): {cells.get('finding', '')}\n"
            f"- Nhãn trích dẫn chuẩn: {raw_cite}\n"
            f"- Đoạn trích chi tiết:\n" + "\n".join(clean_excerpts)
        )

    return matrix_rows, doc_summaries


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

    matrix_rows, doc_summaries = _build_literature_matrix_and_summaries(docs, body.focus, db)

    focus_part = f"\nChủ đề / Câu hỏi nghiên cứu trọng tâm: **{body.focus}**" if body.focus else ""
    prompt = f"""Bạn là chuyên gia viết tổng quan tài liệu nghiên cứu học thuật (Systematic Literature Review). Hãy viết một bài Tổng quan Tài liệu chuyên sâu tổng hợp từ {len(docs)} công trình nghiên cứu sau:{focus_part}

{chr(10).join(doc_summaries)}

QUY TẮC BẮT BUỘC:
1. Mọi số liệu, phương pháp, thang đo và kết quả nêu ra BẮT BUỘC phải gắn nhãn trích dẫn chính xác theo định dạng `[Tên_file.pdf - Trang X]` (ví dụ: `[{docs[0].filename} - Trang 1]`).
2. So sánh đối chiếu trực tiếp sự tương đồng và khác biệt về Phương pháp luận (Methodology), Thang đo / Công cụ đo lường (Psychometric Scales / Metrics) và Kết quả thực nghiệm (Key Findings / Effect Sizes) giữa các nghiên cứu.
3. Viết theo cấu trúc chuẩn học thuật:
## 1. Bối cảnh & Mục tiêu Tổng quan
## 2. Đối sánh Thiết kế Nghiên cứu & Công cụ Đo lường
## 3. Tổng hợp Kết quả Thực nghiệm & Cỡ Hiệu ứng
## 4. Phân tích Điểm Đồng thuận, Khác biệt & Khoảng trống Nghiên cứu (Research Gaps)
## 5. Kết luận & Khuyến nghị Lâm sàng / Học thuật"""

    import base64
    import json as json_lib
    from app.services.scientific_appraiser import analyze_cebm_contradiction_radar
    matrix_b64 = ""
    radar_b64 = ""
    try:
        matrix_json = json_lib.dumps(matrix_rows, ensure_ascii=False)
        matrix_b64 = base64.b64encode(matrix_json.encode("utf-8")).decode("ascii")
        radar_obj = analyze_cebm_contradiction_radar(matrix_rows, body.focus, llm_callable=None)
        radar_json = json_lib.dumps(radar_obj, ensure_ascii=False)
        radar_b64 = base64.b64encode(radar_json.encode("utf-8")).decode("ascii")
    except Exception:
        pass

    def stream_response():
        messages = [{"role": "user", "content": prompt}]
        yield from _stream_llm(messages, temperature=0.3, max_tokens=8192)

    return StreamingResponse(
        stream_response(),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Literature-Matrix": matrix_b64,
            "X-Literature-Radar": radar_b64,
            "Access-Control-Expose-Headers": "X-Literature-Matrix, X-Literature-Radar",
        },
    )


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


# ── Feature 1: Kiểm chứng Chống Ảo giác Cấp độ Mệnh đề (Claim-Level Entailment Shield) ──

class VerifyClaimsRequest(BaseModel):
    query: str = ""
    answer: str
    document_ids: Optional[List[str]] = None


@router.post("/verify-claims")
def verify_claims_endpoint(
    body: VerifyClaimsRequest,
    db: Session = Depends(get_db),
):
    from app.services.retriever import retrieve, retrieve_via_memory
    from app.services.scientific_appraiser import verify_atomic_claims_entailment

    if not body.answer or not body.answer.strip():
        raise HTTPException(400, "Nội dung câu trả lời cần kiểm chứng không được để trống")

    search_ids = body.document_ids if (body.document_ids and len(body.document_ids) > 0) else None
    search_q = (body.query or body.answer[:240]).strip()
    chunks: list[dict] = []

    try:
        if search_ids and len(search_ids) <= 5:
            mem = retrieve_via_memory(search_q, search_ids, db, top_k=6)
            if mem:
                chunks = mem
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    if not chunks:
        try:
            chunks = retrieve(search_q, search_ids, db, top_k=10)
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
            chunks = []

    return verify_atomic_claims_entailment(
        query=body.query,
        answer=body.answer,
        context_chunks=chunks,
        db=db,
    )


# ── Feature 2: Radar Phát hiện Mâu thuẫn & Đồng thuận Trọng số CEBM ──────────

@router.post("/contradiction-radar")
def contradiction_radar_endpoint(
    body: LiteratureRequest,
    db: Session = Depends(get_db),
):
    from app.services.scientific_appraiser import analyze_cebm_contradiction_radar

    if not body.document_ids:
        raise HTTPException(400, "Cần chọn ít nhất 1 tài liệu")
    docs = db.query(Document).filter(Document.id.in_(body.document_ids[:10])).all()
    if not docs:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    matrix_rows, _ = _build_literature_matrix_and_summaries(docs, body.focus, db)
    radar = analyze_cebm_contradiction_radar(matrix_rows, body.focus, llm_callable=_call_llm)
    return {
        "matrix_rows": matrix_rows,
        "radar": radar,
    }


# ── Feature 3: Đồ thị Tri thức Thần kinh – Tâm lý Liên kết Não 3D ────────────

class NeuroGraphRequest(BaseModel):
    query: str
    answer: Optional[str] = ""
    document_ids: Optional[List[str]] = None


@router.post("/neuro-graph")
def neuro_graph_endpoint(
    body: NeuroGraphRequest,
    db: Session = Depends(get_db),
):
    from app.services.retriever import retrieve
    from app.services.scientific_appraiser import extract_neuro_clinical_3d_graph

    search_ids = body.document_ids if (body.document_ids and len(body.document_ids) > 0) else None
    search_q = (body.query or body.answer or "Tâm lý thần kinh não bộ").strip()[:300]
    chunks: list[dict] = []
    try:
        chunks = retrieve(search_q, search_ids, db, top_k=6)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    return extract_neuro_clinical_3d_graph(
        query=body.query,
        answer=body.answer or "",
        context_chunks=chunks,
    )


# ── Feature 4: Phòng Mô phỏng Ca Lâm sàng Ảo DSM-5/ICD-11 (OSCE Sandbox) ─────

class OsceChatRequest(BaseModel):
    case_id: str
    messages: List[dict]
    administer_scale: Optional[str] = None
    document_ids: Optional[List[str]] = None


class OsceEvaluateRequest(BaseModel):
    case_id: str
    messages: List[dict]
    administered_scales: List[str] = []
    user_diagnosis: str
    user_differential: str = ""
    user_treatment: str
    document_ids: Optional[List[str]] = None


@router.get("/osce/cases")
def list_osce_cases():
    from app.services.scientific_appraiser import OSCE_CLINICAL_CASES

    public_cases = []
    for c in OSCE_CLINICAL_CASES:
        public_cases.append({
            "case_id": c["case_id"],
            "title": c["title"],
            "difficulty": c["difficulty"],
            "patient_name": c["patient_name"],
            "patient_age": c["patient_age"],
            "occupation": c["occupation"],
            "avatar_emoji": c["avatar_emoji"],
            "chief_complaint": c["chief_complaint"],
            "initial_demeanor": c["initial_demeanor"],
            "available_scales": list(c["ground_truth"]["simulated_scale_results"].keys()),
        })
    return {"cases": public_cases}


@router.post("/osce/chat")
def osce_patient_chat(
    body: OsceChatRequest,
    db: Session = Depends(get_db),
):
    from app.services.scientific_appraiser import OSCE_CLINICAL_CASES

    case_obj = next((c for c in OSCE_CLINICAL_CASES if c["case_id"] == body.case_id), OSCE_CLINICAL_CASES[0])
    gt = case_obj["ground_truth"]

    # Nếu nhà lâm sàng chỉ định thang đo tâm lý (PHQ-9, GAD-7, BDI-II, DASS-21)
    if body.administer_scale:
        scale_code = body.administer_scale.strip().upper()
        sim_scales = gt["simulated_scale_results"]
        scale_res = sim_scales.get(scale_code) or next(iter(sim_scales.values()))
        return {
            "type": "scale_result",
            "scale_code": scale_code,
            "total_score": scale_res["total_score"],
            "severity": scale_res["severity"],
            "breakdown": scale_res["breakdown"],
            "patient_reply": (
                f"(Đã hoàn thành phiếu đánh giá {scale_code}) Kết quả tổng điểm: {scale_res['total_score']} — "
                f"Mức độ: {scale_res['severity']}. Chi tiết: {scale_res['breakdown']}"
            ),
        }

    history_lines = []
    for m in body.messages[-8:]:
        role_label = "Bác sĩ / Nhà lâm sàng" if m.get("role") == "user" else f"Bệnh nhân ({case_obj['patient_name']})"
        history_lines.append(f"{role_label}: {m.get('content', '')}")

    prompt = f"""{case_obj['hidden_persona_prompt']}

QUY TẮC ĐÓNG VAI BỆNH NHÂN (BẮT BUỘC):
- Chỉ trả lời ở ngôi thứ nhất (xưng "em" hoặc "tôi" với "bác sĩ/chuyên gia") đúng tâm lý của bệnh nhân.
- KHÔNG tự nói tên bệnh lý y khoa hay tiêu chuẩn DSM-5. Chỉ mô tả cảm giác, giấc ngủ, suy nghĩ và sinh hoạt đời thường.
- Thể hiện cử chỉ/cảm xúc ngắn gọn trong ngoặc vuông ở đầu câu, ví dụ: [Thở dài, nhìn xuống] hoặc [Đan chặt hai bàn tay].
- Chỉ tiết lộ triệu chứng nhạy cảm (như ý nghĩ muốn biến mất, kết quả xét nghiệm tuyến giáp, hoặc chi tiết vụ tai nạn) KHI bác sĩ hỏi đúng khía cạnh đó.
- Trả lời tự nhiên trong 2-4 câu, KHÔNG dùng ký tự markdown ** hay ###.

Lịch sử cuộc trò chuyện:
{chr(10).join(history_lines)}

Bệnh nhân ({case_obj['patient_name']}) trả lời:"""

    try:
        reply = _call_llm(prompt, temperature=0.35, max_tokens=350).strip()
        reply = re.sub(r"\*{1,3}|#{1,4}", "", reply).strip()
    except Exception:
        reply = "[Thở dài] Dạ thưa bác sĩ, triệu chứng này làm em rất mệt mỏi và ảnh hưởng nhiều đến công việc hàng ngày ạ."

    return {
        "type": "patient_reply",
        "patient_reply": reply,
    }


@router.post("/osce/evaluate")
def osce_evaluate_session(
    body: OsceEvaluateRequest,
    db: Session = Depends(get_db),
):
    from app.services.retriever import retrieve
    from app.services.scientific_appraiser import OSCE_CLINICAL_CASES, grade_osce_clinical_submission

    case_obj = next((c for c in OSCE_CLINICAL_CASES if c["case_id"] == body.case_id), OSCE_CLINICAL_CASES[0])
    cited_ev = ""
    try:
        search_ids = body.document_ids if (body.document_ids and len(body.document_ids) > 0) else None
        q_ev = f"{case_obj['ground_truth']['primary_diagnosis']} {case_obj['ground_truth']['evidence_treatment']}"
        chunks = retrieve(q_ev[:200], search_ids, db, top_k=3)
        if chunks:
            c0 = chunks[0]
            fn = c0.get("doc_filename") or c0.get("doc_title") or "Tài liệu.pdf"
            pg = int(c0.get("page_number") or 1)
            cited_ev = f"[{fn} - Page {pg}]"
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    return grade_osce_clinical_submission(
        case_id=body.case_id,
        interview_messages=body.messages,
        administered_scales=body.administered_scales,
        user_diagnosis=body.user_diagnosis,
        user_differential=body.user_differential,
        user_treatment=body.user_treatment,
        cited_evidence=cited_ev,
    )

