"""
Memory builder — Phase A core.

Khi user upload PDF, sau khi parse + chunk + embed xong, gọi module này để build
"compressed memory" cho document. Memory gồm:
  - abstract: tóm tắt 200-400 từ
  - abstract_embedding: vector của abstract (dùng cho L1 cosine match)
  - topic_index: mục lục semantic
  - key_facts: 20-200 facts quan trọng, mỗi fact có page number
  - entities: tác giả/khái niệm/lý thuyết

Memory được lưu vào bảng document_summaries và được dùng bởi
`retriever.retrieve_via_memory()` (L1 fast path) → trả lời < 500ms cho câu hỏi
factoid mà không cần gọi LLM rerank hay load toàn bộ chunks.

DESIGN PRINCIPLES:
  - 1-4 LLM calls / document tuỳ kích thước PDF (cap 4 để tránh bill cao)
  - Best-effort: nếu LLM fail, set memory_status='failed', document vẫn 'ready'
  - RAG path vẫn hoạt động bình thường nếu memory build fail
  - Idempotent: nếu memory đã ready, skip
"""
from __future__ import annotations

import json
import logging
import re
import time
import traceback
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.dedup_utils import dedup_facts, dedup_entities

logger = logging.getLogger(__name__)

# ── Cấu hình ─────────────────────────────────────────────────────────────────
_MAX_FACTS = 200  # cap số key_facts để tránh memory row quá lớn
_MAX_FACTS_PER_CHUNK = 50  # cap khi gọi LLM cho PDF > 100 trang
_LARGE_PDF_PAGE_THRESHOLD = 100  # ngưỡng chia chunk
_TOTAL_PAGES_SAMPLE_FOR_ABSTRACT = 12  # lấy N trang đầu + cuối + giữa làm sample
_TIMEOUT_S = 120  # timeout cho mỗi LLM call

# Max tokens cho LLM call. Cao để chứa JSON lớn (200 facts × ~50 chars = 10KB ≈ 2500 tokens).
# Với local model 1.5B, cần ≥ 4000 để không bị truncate.
# Gemini cần nhiều hơn để tránh bị truncate giữa JSON.
_MAX_TOKENS_STANDARD = 4500
_MAX_TOKENS_LARGE_ABSTRACT = 2000
_MAX_TOKENS_LARGE_FACT = 4500

# Khi dùng Gemini, tăng max_tokens để đảm bảo output JSON không bị cắt.
_MAX_TOKENS_GEMINI = 14000

# Số facts tối đa khi build với Gemini
_MAX_FACTS_PER_CHUNK_GEMINI = 25


# ── Prompts ───────────────────────────────────────────────────────────────────

_PROMPT_ABSTRACT_AND_FACTS = """Bạn là chuyên gia đọc tài liệu học thuật. Dựa vào TIÊU ĐỀ, TÁC GIẢ, MỤC LỤC, HEADINGS, và ĐOẠN TRÍCH dưới đây, hãy sinh JSON với schema chính xác:

{{
  "abstract": "Tóm tắt 200-400 từ về nội dung chính, mục tiêu, phương pháp, kết luận quan trọng.",
  "key_facts": [
    {{"claim": "Mệnh đề ngắn (1-2 câu) về 1 fact/định nghĩa/kết luận quan trọng", "page": <số trang trong tài liệu>}},
    ...{n_facts} facts
  ],
  "entities": [
    {{"name": "Tên tác giả/khái niệm/lý thuyết/công thức", "type": "person|theory|term|formula", "page": <số trang>}}
  ]
}}

QUY TẮC BẮT BUỘC:
- CHỈ dùng thông tin có trong CONTEXT. KHÔNG bịa, KHÔNG dùng kiến thức ngoài.
- Số trang PHẢI là trang THẬT có trong CONTEXT được cung cấp. Nếu không chắc → BỎ qua fact đó.
- Ưu tiên facts: định nghĩa, kết luận nghiên cứu, dữ liệu quan trọng, lý thuyết cốt lõi.
- Trả về CHÍNH XÁC JSON, KHÔNG thêm markdown, KHÔNG giải thích.
"""

_PROMPT_TOPIC_INDEX = """Cho MỤC LỤC (TOC) và HEADINGS của tài liệu, sinh JSON array mô tả cấu trúc chủ đề:

[{{"topic": "Tên chủ đề/chương", "page_start": <số trang bắt đầu>, "page_end": <số trang kết thúc>}}]

QUY TẮC:
- Giữ thứ tự xuất hiện trong tài liệu.
- page_start/page_end dựa trên headings/TOC. Nếu không rõ page_end, dùng next-1.
- Tối đa 30 topics. Trả về CHÍNH XÁC JSON array, KHÔNG thêm text.
"""


# ── JSON parsing utilities ───────────────────────────────────────────────────

def _parse_json_object(raw: str) -> Optional[dict]:
    """Robust parse JSON object từ LLM output. Tìm {...} đầu tiên.

    LLM thỉnh thoảng wrap JSON trong ```json ... ``` hoặc thêm text trước/sau.
    Strategy: tìm '{' đầu tiên, dùng stack counting để tìm '}' tương ứng.
    Trả về None nếu không parse được.
    """
    if not raw:
        return None
    # Strip markdown code fences nếu có
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())

    # Tìm '{' đầu tiên
    start = raw.find("{")
    if start < 0:
        return None

    # Stack counting tìm '}' tương ứng
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(raw)):
        c = raw[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _parse_json_array(raw: str) -> Optional[list]:
    """Tương tự _parse_json_object nhưng cho array. Tìm [...] đầu tiên."""
    if not raw:
        return None
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())

    start = raw.find("[")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(raw)):
        c = raw[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


# ── LLM call wrapper ─────────────────────────────────────────────────────────

def _llm_complete(messages: list[dict], system: str, max_tokens: int = 3000) -> str:
    """Wrapper gọi Gemini (qua llm_client) cho memory extraction task.

    Chỉ hỗ trợ backend Gemini. Nếu env flag
    `MEMORY_LLM_BACKEND` khác 'gemini', log warning và fallback về Gemini.

    Tự động bump max_tokens lên _MAX_TOKENS_GEMINI (14000) vì 
    hay bị truncate giữa JSON.
    Caller có thể pass max_tokens cao hơn nếu cần.

    Trả về '' nếu fail (không raise) — caller sẽ fallback.
    """
    from app.core.config import settings
    backend = (settings.MEMORY_LLM_BACKEND or "gemini").lower()
    if backend != "gemini":
        logger.warning(
            "MEMORY_LLM_BACKEND=%r không còn hỗ trợ — chỉ Gemini. Fallback về Gemini.",
            backend,
        )

    # Đảm bảo Gemini có đủ tokens
    effective_max = max(max_tokens, _MAX_TOKENS_GEMINI)
    try:
        from app.services.llm_client import get_default_client
        client = get_default_client()
        return client.complete(
            messages=messages,
            system=system,
            max_tokens=effective_max,
            temperature=0.1,
        ) or ""
    except Exception as e:
        logger.warning("Gemini LLM call failed: %s", e)
        return ""


# ── Sample pages logic ───────────────────────────────────────────────────────

def _sample_pages(pages: list[dict], n: int) -> list[dict]:
    """Lấy n trang đại diện: đầu + cuối + giữa. Tránh load full text vào prompt."""
    if len(pages) <= n:
        return pages
    step = max(1, len(pages) // n)
    sampled = []
    seen_pages = set()
    for i in range(0, len(pages), step):
        if len(sampled) >= n:
            break
        p = pages[i]
        if p["page"] not in seen_pages:
            sampled.append(p)
            seen_pages.add(p["page"])
    return sampled


# ── Public entrypoint ────────────────────────────────────────────────────────

def build_memory_for_doc(document_id: str, db_url: str) -> bool:
    """Build compressed memory cho 1 document. Idempotent.

    Args:
        document_id: UUID string của document.
        db_url: Postgres connection URL.

    Returns:
        True nếu memory_status='ready', False nếu fail.
        Document vẫn ở status='ready' cho dù memory build fail.
    """
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 1. Load document + pages
        doc = db.execute(
            text("SELECT id, title, authors, year, filename, file_path, total_pages "
                 "FROM documents WHERE id = :id"),
            {"id": document_id},
        ).first()
        if not doc:
            logger.error("build_memory: document %s not found", document_id)
            return False

        # Idempotent: nếu memory đã ready, skip
        existing = db.execute(
            text("SELECT memory_status FROM document_summaries WHERE document_id = :id"),
            {"id": document_id},
        ).first()
        if existing and existing.memory_status == "ready":
            logger.info("build_memory: %s already ready, skip", document_id)
            return True

        # Mark building
        _upsert_summary(db, document_id, memory_status="building", error_message=None)
        db.commit()

        # Load pages từ page_texts
        pages_rows = db.execute(
            text("SELECT page_number, content FROM page_texts "
                 "WHERE document_id = :id ORDER BY page_number"),
            {"id": document_id},
        ).fetchall()
        if not pages_rows:
            logger.warning("build_memory: %s has no pages in page_texts", document_id)
            _upsert_summary(db, document_id, memory_status="failed",
                            error_message="No page text found")
            db.commit()
            return False

        pages = [{"page": r.page_number, "text": r.content or ""} for r in pages_rows]

        # Load hoặc build structure (TOC + headings)
        structure = _load_or_build_structure(doc, pages, db)

        # 2. Build abstract + key_facts + entities
        is_large = len(pages) > _LARGE_PDF_PAGE_THRESHOLD
        if is_large:
            ok = _build_memory_large(doc, pages, structure, db)
        else:
            ok = _build_memory_standard(doc, pages, structure, db)

        if not ok:
            _upsert_summary(db, document_id, memory_status="failed",
                            error_message="LLM returned empty/invalid JSON")
            db.commit()
            return False

        # 3. Build topic_index (dùng structure từ PDF nếu có, fallback LLM)
        topics = _build_topic_index(structure)
        if topics:
            db.execute(
                text("UPDATE document_summaries SET topic_index = :t WHERE document_id = :did"),
                {"t": json.dumps(topics), "did": document_id},
            )
            db.commit()

        # 4. Embed abstract
        abs_row = db.execute(
            text("SELECT abstract FROM document_summaries WHERE document_id = :did"),
            {"did": document_id},
        ).first()
        if abs_row and abs_row.abstract:
            try:
                from app.services.embedder import embed_text
                vec = embed_text(abs_row.abstract, is_query=False)
                # Dùng CAST thay vì :: để tránh conflict với SQLAlchemy named param.
                # Vector string phải được build thành literal trong Python (escape an toàn vì toàn số).
                vec_literal = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
                db.execute(
                    text("UPDATE document_summaries SET abstract_embedding = CAST(:v AS vector) "
                         "WHERE document_id = :did"),
                    {"v": vec_literal, "did": document_id},
                )
                db.commit()
            except Exception as e:
                # Embed fail không critical — vẫn có thể dùng memory (chỉ L1 cosine fail)
                logger.warning("embed abstract failed for %s: %s", document_id, e)

        # 5. Mark ready + update documents.has_memory
        db.execute(
            text("UPDATE document_summaries SET memory_status = 'ready' "
                 "WHERE document_id = :did"),
            {"did": document_id},
        )
        db.execute(
            text("UPDATE documents SET has_memory = TRUE, memory_status = 'ready' "
                 "WHERE id = :did"),
            {"did": document_id},
        )
        db.commit()
        logger.info("build_memory: %s DONE", document_id)
        return True

    except Exception as e:
        logger.error("build_memory FATAL for %s: %s\n%s", document_id, e, traceback.format_exc())
        try:
            _upsert_summary(db, document_id, memory_status="failed",
                            error_message=str(e)[:500])
            db.execute(
                text("UPDATE documents SET memory_status = 'failed' WHERE id = :id"),
                {"id": document_id},
            )
            db.commit()
        except Exception:
            pass
        return False
    finally:
        try:
            db.close()
        except Exception:
            pass


# ── Internal builders ────────────────────────────────────────────────────────

def _upsert_summary(db, document_id: str, **fields) -> None:
    """Insert hoặc update 1 row trong document_summaries.

    Cột `id` có default gen_random_uuid() nên KHÔNG truyền vào.
    Cột `document_id` được truyền riêng qua placeholder :document_id (không nằm trong fields).
    """
    existing = db.execute(
        text("SELECT id FROM document_summaries WHERE document_id = :did"),
        {"did": document_id},
    ).first()
    if existing:
        if fields:
            set_clause = ", ".join(f"{k} = :{k}" for k in fields)
            db.execute(
                text(f"UPDATE document_summaries SET {set_clause} WHERE document_id = :did"),
                {**fields, "did": document_id},
            )
    else:
        fields.setdefault("memory_status", "pending")
        cols = ", ".join(f"{k}" for k in fields)
        placeholders = ", ".join(f":{k}" for k in fields)
        db.execute(
            text(f"INSERT INTO document_summaries (document_id, {cols}) "
                 f"VALUES (:did, {placeholders})"),
            {**fields, "did": document_id},
        )


def _load_or_build_structure(doc, pages: list[dict], db) -> dict:
    """Load structure đã cache, hoặc build mới bằng extract_structure()."""
    # Hiện tại structure không lưu DB (chỉ dùng 1 lần cho memory build).
    # Nếu sau này cần reuse, có thể lưu JSON vào 1 cột mới.
    from app.services.parser import extract_structure
    file_path = doc.file_path if hasattr(doc, "file_path") else None
    if not file_path:
        return {"toc": [], "headings": [], "tables": []}
    try:
        return extract_structure(file_path)
    except Exception as e:
        logger.warning("extract_structure failed: %s", e)
        return {"toc": [], "headings": [], "tables": []}


def _format_pages_for_prompt(pages: list[dict], max_chars: int = 12000) -> str:
    """Format pages thành text đưa vào prompt. Cap tổng chars."""
    parts = []
    total = 0
    for p in pages:
        snippet = (p.get("text") or "").strip()
        if not snippet:
            continue
        chunk = f"[Trang {p['page']}]\n{snippet}\n"
        if total + len(chunk) > max_chars:
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n".join(parts)


def _format_structure_for_prompt(structure: dict, max_items: int = 30) -> str:
    """Format TOC + headings thành text ngắn cho prompt."""
    lines = []
    if structure.get("toc"):
        lines.append("MỤC LỤC (TOC):")
        for i, item in enumerate(structure["toc"][:max_items]):
            indent = "  " * (item.get("level", 1) - 1)
            lines.append(f"{indent}- {item.get('title', '')} (trang {item.get('page', '?')})")
    if structure.get("headings"):
        lines.append("\nHEADINGS (theo trang):")
        for h in structure["headings"][:max_items]:
            lines.append(f"- p.{h['page']}: {h['text']}")
    if structure.get("tables"):
        lines.append(f"\nBẢNG: {len(structure['tables'])} bảng trong tài liệu")
    return "\n".join(lines) if lines else "(Không có cấu trúc rõ ràng)"


def _build_memory_standard(doc, pages: list[dict], structure: dict, db) -> bool:
    """Build memory cho PDF ≤ 100 trang: 1 LLM call."""
    from app.core.config import settings
    is_gemini = settings.MEMORY_LLM_BACKEND.lower() == "gemini"
    n_facts = _MAX_FACTS_PER_CHUNK_GEMINI if is_gemini else _MAX_FACTS_PER_CHUNK

    sample = _sample_pages(pages, _TOTAL_PAGES_SAMPLE_FOR_ABSTRACT)
    pages_text = _format_pages_for_prompt(sample)
    structure_text = _format_structure_for_prompt(structure)

    title = (getattr(doc, "title", None) or "").strip() or getattr(doc, "filename", "Tài liệu")
    authors = (getattr(doc, "authors", None) or "").strip() or "Không rõ"

    user_msg = (
        f"TIÊU ĐỀ: {title}\n"
        f"TÁC GIẢ: {authors}\n\n"
        f"{structure_text}\n\n"
        f"ĐOẠN TRÍCH ({(len(pages))} trang tổng, lấy mẫu {len(sample)} trang đại diện):\n"
        f"{pages_text}\n\n"
        f"Hãy sinh JSON với {n_facts} key_facts, abstract 200-400 từ, "
        f"và entities (tác giả, khái niệm, lý thuyết)."
    )

    raw = _llm_complete(
        messages=[{"role": "user", "content": user_msg}],
        system=_PROMPT_ABSTRACT_AND_FACTS.format(n_facts=n_facts),
        max_tokens=_MAX_TOKENS_STANDARD,
    )
    parsed = _parse_json_object(raw)
    if not parsed:
        logger.warning("_build_memory_standard: parse JSON fail. raw[:200]=%s", raw[:200])
        return False

    abstract = str(parsed.get("abstract", "")).strip()[:3000]
    key_facts = parsed.get("key_facts") or []
    entities = parsed.get("entities") or []

    # Validate + cap + dedup
    key_facts = _validate_facts(key_facts, max_pages=len(pages))
    key_facts = dedup_facts(key_facts)[:_MAX_FACTS]
    entities = _validate_entities(entities)
    entities = dedup_entities(entities)[:100]

    # Estimate tokens used (rough: 1 token ~ 4 chars)
    tokens_used = (len(user_msg) + len(raw)) // 4

    _upsert_summary(
        db, str(doc.id),
        abstract=abstract,
        key_facts=json.dumps(key_facts),
        entities=json.dumps(entities),
        memory_tokens_used=tokens_used,
    )
    db.commit()
    return True


def _build_memory_large(doc, pages: list[dict], structure: dict, db) -> bool:
    """Build memory cho PDF > 100 trang: 1 abstract call + 3 fact-extraction calls (4 chunks)."""
    title = (getattr(doc, "title", None) or "").strip() or getattr(doc, "filename", "Tài liệu")
    authors = (getattr(doc, "authors", None) or "").strip() or "Không rõ"
    structure_text = _format_structure_for_prompt(structure)

    # ── 1. Abstract từ sample đầu/cuối/giữa ──
    sample = _sample_pages(pages, _TOTAL_PAGES_SAMPLE_FOR_ABSTRACT)
    sample_text = _format_pages_for_prompt(sample)

    abstract_raw = _llm_complete(
        messages=[{"role": "user", "content":
            f"TIÊU ĐỀ: {title}\nTÁC GIẢ: {authors}\n\n"
            f"{structure_text}\n\nĐOẠN TRÍCH:\n{sample_text}\n\n"
            f"Viết abstract 200-400 từ tóm tắt nội dung chính của tài liệu. "
            f"Chỉ dùng thông tin từ CONTEXT. Trả về CHÍNH XÁC JSON: {{\"abstract\": \"...\"}}"
        }],
        system="Bạn là chuyên gia tóm tắt tài liệu. CHỈ trả về JSON, không thêm text.",
        max_tokens=_MAX_TOKENS_LARGE_ABSTRACT,
    )
    abstract_parsed = _parse_json_object(abstract_raw)
    abstract = str((abstract_parsed or {}).get("abstract", "")).strip()[:3000]
    if not abstract:
        # Fallback: dùng 1000 ký tự đầu của full_text
        abstract = (pages[0].get("text", "") + pages[-1].get("text", ""))[:1500].strip()

    # ── 2. Key_facts: chia 3 phần, mỗi phần ~40 facts ──
    all_facts: list = []
    all_entities: list = []
    n_chunks = 3
    chunk_size = len(pages) // n_chunks
    facts_per_chunk = _MAX_FACTS_PER_CHUNK

    for i in range(n_chunks):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < n_chunks - 1 else len(pages)
        chunk_pages = pages[start:end]
        if not chunk_pages:
            continue
        chunk_text = _format_pages_for_prompt(chunk_pages, max_chars=15000)
        if not chunk_text.strip():
            continue

        raw = _llm_complete(
            messages=[{"role": "user", "content":
                f"PHẦN {i+1}/{n_chunks} của tài liệu '{title}'.\n"
                f"Trang {chunk_pages[0]['page']}-{chunk_pages[-1]['page']}:\n{chunk_text}\n\n"
                f"Sinh JSON {{\"key_facts\": [{{claim, page}}], \"entities\": [{{name, type, page}}]}} "
                f"với tối đa {facts_per_chunk} facts. CHỈ dùng thông tin từ CONTEXT."
            }],
            system=_PROMPT_ABSTRACT_AND_FACTS.format(n_facts=facts_per_chunk),
            max_tokens=_MAX_TOKENS_LARGE_FACT,
        )
        parsed = _parse_json_object(raw)
        if parsed:
            all_facts.extend(parsed.get("key_facts") or [])
            all_entities.extend(parsed.get("entities") or [])

    # Validate + cap + dedup
    all_facts = _validate_facts(all_facts, max_pages=len(pages))
    all_facts = dedup_facts(all_facts)[:_MAX_FACTS]
    all_entities = _validate_entities(all_entities)
    all_entities = dedup_entities(all_entities)[:100]

    # Estimate tokens
    tokens_used = len(abstract) // 4 + len(all_facts) * 30 + len(all_entities) * 15

    _upsert_summary(
        db, str(doc.id),
        abstract=abstract,
        key_facts=json.dumps(all_facts),
        entities=json.dumps(all_entities),
        memory_tokens_used=tokens_used,
    )
    db.commit()
    return True


def _build_topic_index(structure: dict) -> list:
    """Dùng structure có sẵn (TOC + headings) để build topic_index.

    Nếu structure có TOC → dùng trực tiếp. Nếu không → gọi LLM.
    """
    toc = structure.get("toc") or []
    headings = structure.get("headings") or []

    if toc:
        # Ưu tiên TOC. Mỗi entry trở thành 1 topic. page_end = next_start - 1.
        out = []
        for i, item in enumerate(toc):
            page_start = int(item.get("page", 0))
            if i + 1 < len(toc):
                page_end = int(toc[i + 1].get("page", page_start)) - 1
            else:
                page_end = page_start + 9  # default 10 pages
            out.append({
                "topic": str(item.get("title", "")).strip(),
                "page_start": page_start,
                "page_end": max(page_end, page_start),
            })
        # Cap 30 topics
        return out[:30]

    if headings:
        # Group headings theo size lớn nhất (level 1)
        out = []
        for h in headings[:30]:
            out.append({
                "topic": str(h.get("text", "")).strip(),
                "page_start": int(h.get("page", 1)),
                "page_end": int(h.get("page", 1)) + 4,  # estimate
            })
        return out

    return []


def _validate_facts(facts: list, max_pages: int) -> list:
    """Validate + clean key_facts. Bỏ fact không có claim hoặc page invalid."""
    out = []
    for f in facts:
        if not isinstance(f, dict):
            continue
        claim = str(f.get("claim", "")).strip()
        if not claim or len(claim) < 5 or len(claim) > 500:
            continue
        try:
            page = int(f.get("page", 0))
        except (TypeError, ValueError):
            continue
        if page < 1 or page > max_pages:
            continue
        out.append({
            "claim": claim,
            "page": page,
            "confidence": float(f.get("confidence", 0.8)),
        })
    return out


def _validate_entities(entities: list) -> list:
    """Validate entities. Type phải ∈ {person, theory, term, formula}."""
    valid_types = {"person", "theory", "term", "formula"}
    out = []
    seen = set()
    for e in entities:
        if not isinstance(e, dict):
            continue
        name = str(e.get("name", "")).strip()
        if not name or len(name) < 2 or len(name) > 100:
            continue
        if name.lower() in seen:
            continue
        etype = str(e.get("type", "term")).lower().strip()
        if etype not in valid_types:
            etype = "term"
        try:
            page = int(e.get("page", 0))
        except (TypeError, ValueError):
            page = 0
        out.append({"name": name, "type": etype, "page": page})
        seen.add(name.lower())
    return out
