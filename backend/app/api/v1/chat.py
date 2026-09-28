from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import unicodedata
import re
import json
import logging
import uuid
from app.db.postgres import get_db
from app.services.retriever import retrieve, retrieve_via_memory
from app.services.generator import (
    generate_stream, generate_answer, classify_query_domain,
    generate_stream_web_search, generate_stream_direct,
)
from app.services.web_scraper import duckduckgo_search
from app.services.file_parser import parse_file
from app.services.llm_client import llm_configuration_error
from app.core.security import get_optional_user
from app.core.plan_utils import get_limits, count_today_chats

logger = logging.getLogger(__name__)


def detect_language(query: str) -> str:
    # Loại bỏ chỉ dẫn chế độ của hệ thống (nếu có từ frontend)
    clean_q = re.sub(r'^\[he\s+thong:[^\]]+\]', '', query, flags=re.IGNORECASE).strip()
    clean_q = re.sub(r'^\[system:[^\]]+\]', '', clean_q, flags=re.IGNORECASE).strip()

    # Kiểm tra các ký tự có dấu đặc trưng tiếng Việt
    vi_chars = set("áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
                   "ÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ")
    if any(c in vi_chars for c in clean_q):
        return "vi"
    # Kiểm tra từ vựng tiếng Anh phổ biến
    en_words = {"what", "is", "how", "to", "the", "in", "of", "and", "a", "an", "depression", "anxiety", "cbt", "ocd", "bipolar", "stress", "hello", "hi", "who", "why", "where", "affect", "people", "psychology"}
    words = set(clean_q.lower().split())
    if words.intersection(en_words):
        return "en"
    return "vi"


PREDEFINED_QA = {
    # Tiếng Việt
    "hi": "Xin chào bạn, bắt đầu ngay thôi!",
    "chao": "Xin chào bạn, bắt đầu ngay thôi!",
    "xin chao": "Xin chào bạn, bắt đầu ngay thôi!",
    "hello": "Xin chào bạn, bắt đầu ngay thôi!",
    "tram cam la gi": "Trầm cảm là một rối loạn tâm trạng phổ biến, đặc trưng bởi cảm giác buồn bã, mất hứng thú kéo dài và mệt mỏi, ảnh hưởng sâu sắc đến sinh hoạt và suy nghĩ.",
    "lo au la gi": "Lo âu là phản ứng tự nhiên của cơ thể trước căng thẳng, nhưng rối loạn lo âu xảy ra khi sự sợ hãi và lo lắng quá mức, kéo dài và gây cản trước cuộc sống hàng ngày.",
    "cbt la gi": "CBT (Cognitive Behavioral Therapy - Liệu pháp nhận thức hành vi) là phương pháp trị liệu giúp nhận diện và thay đổi các suy nghĩ, hành vi tiêu cực nhằm cải thiện sức khỏe tâm thần.",
    "stress co loi hay co hai": "Stress có thể có lợi (stress tích cực - eustress) giúp tập trung và hành động, nhưng stress kéo dài (distress) sẽ gây hại nghiêm trọng cho thể chất và tinh thần.",
    "lam sao de giam stress nhanh": "Bạn có thể áp dụng các kỹ thuật như hít thở sâu, thiền định, tập thể dục nhẹ, nghe nhạc, hoặc viết nhật ký để giải tỏa căng thẳng nhanh chóng.",
    "roi loan luong cuc la gi": "Rối loạn lưỡng cực là tình trạng sức khỏe tâm thần gây ra sự biến động nghiêm trọng về tâm trạng, năng lượng và khả năng hoạt động, chuyển đổi giữa hưng cảm và trầm cảm.",
    "tam ly hoc hanh vi la gi": "Tâm lý học hành vi tập trung vào việc nghiên cứu các hành vi có thể quan sát được và cách hành vi được hình thành, thay đổi thông qua quá trình tương tác với môi trường.",
    "co che tu ve cua cai toi la gi": "Cơ chế tự vệ là các chiến lược tâm lý vô thức (như dồn nén, phóng chiếu, hợp lý hóa) được tâm trí sử dụng để tự bảo vệ khỏi lo âu và xung đột nội tâm.",
    "ocd la gi": "OCD (Rối loạn ám ảnh cưỡng chế) là một rối loạn tâm thần kéo dài, đặc trưng bởi các ý nghĩ ám ảnh lặp đi lặp lại không mong muốn (ám ảnh) và các hành vi nghi thức để giảm lo âu (cưỡng chế).",
    "tri tue cam xuc la gi": "EQ (Trí tuệ cảm xúc) là khả năng nhận biết, hiểu, quản lý và biểu đạt cảm xúc của bản thân cũng như nhận biết, thấu hiểu cảm xúc của người khác.",

    # Tiếng Anh (English)
    "what is depression": "Depression is a common mental health disorder characterized by persistent sadness, loss of interest in activities, and fatigue, significantly affecting daily life.",
    "what is anxiety": "Anxiety is a natural response to stress, but anxiety disorders involve excessive, persistent fear and worry that interfere with daily activities.",
    "what is cbt": "CBT (Cognitive Behavioral Therapy) is a treatment method that helps identify and change negative thoughts and behaviors to improve mental health.",
    "is stress good or bad": "Stress can be beneficial (positive stress - eustress) by helping you focus and act, but prolonged stress (distress) is highly harmful to physical and mental health.",
    "how to reduce stress quickly": "You can apply techniques like deep breathing, meditation, light exercise, listening to music, or journaling to relieve stress quickly.",
    "what is bipolar disorder": "Bipolar disorder is a mental health condition that causes extreme shifts in mood, energy, activity levels, and concentration, fluctuating between mania and depression.",
    "what is behavioral psychology": "Behavioral psychology focuses on studying observable behaviors and how behaviors are learned and modified through interactions with the environment.",
    "what are ego defense mechanisms": "Defense mechanisms are unconscious psychological strategies (like repression, projection, rationalization) used to protect the mind from anxiety and internal conflict.",
    "what is ocd": "OCD (Obsessive-Compulsive Disorder) is a long-lasting mental disorder where a person has uncontrollable, reoccurring thoughts (obsessions) and/or behaviors (compulsions) that he or she feels the urge to repeat.",
    "what is emotional intelligence": "EQ (Emotional Intelligence) is the ability to recognize, understand, manage, and express one's own emotions, as well as recognize and understand the emotions of others."
}

def get_predefined_answer(query: str, lang: str) -> str | None:
    # Chuẩn hóa query: lower, không dấu, bỏ ký tự đặc biệt
    q = query.lower().strip()
    q = re.sub(r'[?!.,;:\-\s]+$', '', q)
    q = q.strip()
    # Loại bỏ chỉ dẫn chế độ của hệ thống (nếu có từ frontend)
    q = re.sub(r'^\[he\s+thong:[^\]]+\]', '', q).strip()
    q = re.sub(r'^\[system:[^\]]+\]', '', q).strip()
    
    # Bỏ dấu tiếng Việt
    q_normalized = unicodedata.normalize('NFKD', q)
    q_normalized = ''.join([c for c in q_normalized if not unicodedata.combining(c)])
    q_normalized = q_normalized.replace('đ', 'd').strip()

    # Xử lý câu chào hỏi riêng dựa trên ngôn ngữ phát hiện
    if q_normalized in ("hi", "hello"):
        if lang == "en":
            return "Hello! Let's get started!"
        return "Xin chào bạn, bắt đầu ngay thôi!"
        
    if q_normalized in ("chao", "xin chao"):
        return "Xin chào bạn, bắt đầu ngay thôi!"

    # Thử khớp chính xác các key định nghĩa sẵn
    if q in PREDEFINED_QA:
        return PREDEFINED_QA[q]
        
    if q_normalized in PREDEFINED_QA:
        return PREDEFINED_QA[q_normalized]
        
    # Thử khớp tương đối
    for key, value in PREDEFINED_QA.items():
        if key in q and len(q) - len(key) < 5:
            return value
        if key in q_normalized and len(q_normalized) - len(key) < 5:
            return value
    return None



def _save_chat_history(db: Session, user_id: str, query: str, answer: str, document_ids: list) -> None:
    """Best-effort lưu chat vào bảng chat_history. Không raise nếu fail."""
    try:
        db.execute(
            text("""
                INSERT INTO chat_history (id, user_id, query, answer, document_ids)
                VALUES (:id, :uid, :query, :answer, cast(:docs AS jsonb))
            """),
            {
                "id": str(uuid.uuid4()),
                "uid": user_id,
                "query": query[:4000],
                "answer": answer[:5000],
                "docs": json.dumps(document_ids or []),
            },
        )
        db.commit()
    except Exception as e:
        logger.warning("Failed to auto-save chat_history for user %s: %s", user_id, e)
        try:
            db.rollback()
        except Exception:
            pass

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    document_ids: list[str]
    mode: Optional[str] = "single"
    force_web_search: Optional[bool] = False  # nếu True: bỏ qua RAG, dùng web search luôn


class AnswerRequest(BaseModel):
    query: str
    document_ids: list[str]


class ExportRequest(BaseModel):
    messages: list[dict]
    title: str = "Báo cáo Hỏi Đáp Tâm Lý Học"


class DomainCheckRequest(BaseModel):
    query: str


class GeneralSearchRequest(BaseModel):
    query: str


# ── Main chat (RAG + psychology) ───────────────────────────────────────────────

@router.post("")
def chat(request: ChatRequest, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    if not request.query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    if not request.document_ids:
        raise HTTPException(400, "Phải chọn ít nhất 1 tài liệu")

    # Bóc tách câu hỏi thực tế của người dùng (loại bỏ chỉ dẫn hệ thống)
    clean_q = re.sub(r'^\[he\s+thong:[^\]]+\]', '', request.query, flags=re.IGNORECASE).strip()
    clean_q = re.sub(r'^\[system:[^\]]+\]', '', clean_q, flags=re.IGNORECASE).strip()

    # Phát hiện ngôn ngữ thực sự của câu hỏi (tiếng Anh hay tiếng Việt)
    lang = detect_language(clean_q)

    # Chuẩn hóa chỉ dẫn hệ thống theo đúng ngôn ngữ của câu hỏi
    sent_query = request.query
    if lang == "en":
        if "[he thong:" in request.query.lower():
            if "ngan gon" in request.query.lower() or "suc tich" in request.query.lower():
                sent_query = re.sub(
                    r'^\[he\s+thong:[^\]]+\]',
                    '[System: Please reply briefly and concisely in about 2-4 sentences. Avoid long listings.] ',
                    request.query,
                    flags=re.IGNORECASE
                )
            else:
                sent_query = re.sub(
                    r'^\[he\s+thong:[^\]]+\]',
                    '[System: Please reply in detail, fully, and deeply. Include plenty of information, concrete examples, expert analysis, and related factors. If possible, cite references. Use markdown formatting with clear headings and bullet points. You can write longer if needed.] ',
                    request.query,
                    flags=re.IGNORECASE
                )
    else:
        if "[system:" in request.query.lower():
            if "briefly" in request.query.lower() or "concisely" in request.query.lower():
                sent_query = re.sub(
                    r'^\[system:[^\]]+\]',
                    '[He thong: Hay tra loi ngan gon, suc tich trong khoang 2-4 cau. Tranh liet ke dai.] ',
                    request.query,
                    flags=re.IGNORECASE
                )
            else:
                sent_query = re.sub(
                    r'^\[system:[^\]]+\]',
                    '[He thong: Hay tra loi chi tiet, day du, sau sac. Bao gom nhieu thong tin, vi du cu the, phan tich chuyen su, va cac yeu to lien quan. Neu co the, hay trich dan nguon tham khao. Dung format markdown nhung nen co cau truc ro rang voi muc lon va muc nho. Co the tra loi dai hon neu can.] ',
                    request.query,
                    flags=re.IGNORECASE
                )

    # 1. Kiểm tra Q&A định nghĩa sẵn trước
    predefined = get_predefined_answer(clean_q, lang)
    if predefined:
        def stream_predefined():
            yield predefined
            if current_user is not None:
                _save_chat_history(db, str(current_user.id), clean_q, predefined, request.document_ids)
        return StreamingResponse(
            stream_predefined(),
            media_type="text/plain; charset=utf-8"
        )

    # 2. Kiểm tra giới hạn gói cước
    limits = get_limits(current_user)
    if limits["max_daily_chat"] is not None and current_user is not None:
        today_count = count_today_chats(current_user.id, db)
        if today_count >= limits["max_daily_chat"]:
            raise HTTPException(
                429,
                f"❌ Gói {limits['label']} chỉ cho phép {limits['max_daily_chat']} câu hỏi/ngày. "
                "Nâng cấp lên Pro để không giới hạn."
            )

    # ── Phase A: thử L1 memory TRƯỚC ──
    used_memory = False
    context_chunks: list[dict] = []
    if not request.force_web_search:
        try:
            # Dùng clean_q để tìm kiếm L1 memory tránh bị nhiễu bởi system prompt
            memory_chunks = retrieve_via_memory(clean_q, request.document_ids, db)
            if memory_chunks:
                # Enrich doc_title/authors từ bảng documents
                doc_meta_rows = db.execute(
                    text("SELECT id, title, authors, filename FROM documents WHERE id = ANY(CAST(:ids AS uuid[]))"),
                    {"ids": request.document_ids},
                ).fetchall()
                meta_map = {str(r.id): r for r in doc_meta_rows}
                for c in memory_chunks:
                    m = meta_map.get(c["document_id"])
                    if m:
                        c["doc_title"] = m.title or ""
                        c["doc_authors"] = m.authors or ""
                        c["doc_filename"] = m.filename or ""
                context_chunks = memory_chunks
                used_memory = True
                logger.info("chat: L1 memory hit, %d chunks (skipped L2 RAG)", len(memory_chunks))
        except Exception as mem_err:
            logger.warning("L1 memory lookup failed: %s", mem_err)
            try:
                db.rollback()  # Bảo vệ giao dịch tránh bị abort
            except Exception:
                pass

    # ── Phase B: L2 RAG chỉ chạy khi L1 không hit ──
    if not context_chunks:
        try:
            # Dùng clean_q để retrieve L2 RAG chính xác hơn
            context_chunks = retrieve(clean_q, request.document_ids, db)
        except Exception as ret_err:
            logger.warning("L2 retrieve failed: %s", ret_err)
            try:
                db.rollback()
            except Exception:
                pass

    # Nếu RAG hoàn toàn không tìm được context → Trả về ngay "Không có thông tin..." hoặc tiếng Anh tương ứng
    if not context_chunks:
        no_ctx_msg = "No information found in the related documents." if lang == "en" else "Không có thông tin trong tài liệu liên quan."
        def no_context_stream():
            yield no_ctx_msg
            if current_user is not None:
                _save_chat_history(db, str(current_user.id), clean_q, no_ctx_msg, request.document_ids)
        return StreamingResponse(
            no_context_stream(),
            media_type="text/plain; charset=utf-8",
            headers={"X-No-Context": "true", "Access-Control-Expose-Headers": "X-No-Context"},
        )

    config_error = llm_configuration_error()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    raw_stream = generate_stream(sent_query, context_chunks, lang)

    def stream_with_saving():
        collected: list[str] = []
        no_ctx_marker = "__NO_CONTEXT__"
        for chunk in raw_stream:
            collected.append(chunk)
            yield chunk
        full_answer = "".join(collected)

        # Nếu LLM trả về __NO_CONTEXT__ (do chunks không chứa thông tin thực sự)
        if full_answer.strip().startswith(no_ctx_marker):
            final_answer = "No information found in the related documents." if lang == "en" else "Không có thông tin trong tài liệu liên quan."
            yield f"\n\n{final_answer}"
            if current_user is not None:
                _save_chat_history(db, str(current_user.id), request.query, final_answer, request.document_ids)
            return

        # Trích xuất citations và build tài liệu tham khảo
        import re
        citation_pattern = re.compile(r'\[([^\]]+)\]')
        raw_citations = citation_pattern.findall(full_answer)

        # Đọc document metadata
        doc_map: dict[str, dict] = {}
        for c in context_chunks:
            doc_id = c.get("document_id", "")
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "filename": c.get("doc_filename") or c.get("doc_title") or "Tài liệu",
                    "title": c.get("doc_title") or "",
                    "authors": c.get("doc_authors") or "",
                }

        # Build danh sách references
        seen_keys: set[str] = set()
        refs_lines: list[str] = []
        for raw in raw_citations:
            key = raw.strip()
            if not key or key in seen_keys:
                continue
            seen_keys.add(key)
            match = re.search(r'([^\[]+?)\s*-\s*Trang\s+(\d+)', key)
            if match:
                fname = match.group(1).strip()
                page = match.group(2).strip()
                found_doc = None
                for doc_id, doc_info in doc_map.items():
                    if fname == doc_info["filename"] or fname == doc_info["title"]:
                        found_doc = doc_info
                        break
                if found_doc:
                    title_part = found_doc["title"] or found_doc["filename"]
                    authors_part = f" ({found_doc['authors']})" if found_doc["authors"] else ""
                    refs_lines.append(f"- {title_part}{authors_part} — Trang {page}")
                else:
                    refs_lines.append(f"- {fname} — Trang {page}")

        clean_answer = citation_pattern.sub('', full_answer)

        references_block = ""
        if refs_lines:
            references_block = (
                "\n\n---\n"
                "## Tài liệu tham khảo\n\n"
                + "\n".join(refs_lines)
            )

        final_answer = clean_answer + references_block

        if references_block:
            yield references_block

        if current_user is not None:
            _save_chat_history(db, str(current_user.id), request.query, final_answer, request.document_ids)

    return StreamingResponse(
        stream_with_saving(),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Context-Pages": ",".join(str(c["page_number"]) for c in context_chunks),
            "X-Document-IDs": ",".join(c["document_id"] for c in context_chunks),
            "X-No-Context": "false",
            "X-Memory-Hit": "true" if used_memory else "false",
            "Access-Control-Expose-Headers": "X-Context-Pages,X-Document-IDs,X-No-Context,X-Memory-Hit",
        }
    )



# ── Domain classification ──────────────────────────────────────────────────────

@router.post("/detect-domain")
def detect_domain(request: DomainCheckRequest):
    """Phân loại câu hỏi: 'psychology' hoặc 'general'."""
    if not request.query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    domain = classify_query_domain(request.query)
    return {"domain": domain, "query": request.query}


# ── General web search fallback ────────────────────────────────────────────────

@router.post("/general")
def chat_general(
 request: GeneralSearchRequest,
 db: Session = Depends(get_db),
 current_user=Depends(get_optional_user),
):
    """Trả lời câu hỏi bằng kiến thức của AI, không kết nối internet."""
    if not request.query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")

    config_error = llm_configuration_error()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    def stream_direct_saving():
        collected = []
        for chunk in generate_stream_direct(request.query):
            collected.append(chunk)
            yield chunk
        if current_user is not None:
            full_answer = "".join(collected)
            _save_chat_history(db, str(current_user.id), request.query, full_answer, [])

    return StreamingResponse(
        stream_direct_saving(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Access-Control-Expose-Headers": "X-Context-Pages,X-Document-IDs,X-Doc-Authors",
        }
    )


# ── Non-streaming answer ───────────────────────────────────────────────────────

@router.post("/answer")
def chat_answer(request: AnswerRequest, db: Session = Depends(get_db)):
    """Non-streaming: trả về câu trả lời + context chunks (dùng cho RAGAS)."""
    if not request.query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    if not request.document_ids:
        raise HTTPException(400, "Phải chọn ít nhất 1 tài liệu")

    context_chunks = retrieve(request.query, request.document_ids, db)
    if not context_chunks:
        return {
            "answer": "Không tìm thấy thông tin liên quan trong tài liệu đã chọn.",
            "contexts": [],
        }

    answer = generate_answer(request.query, context_chunks)
    return {
        "answer": answer,
        "contexts": [
            {
                "content": c["content"],
                "page_number": c["page_number"],
                "document_id": c["document_id"],
                "doc_title": c.get("doc_title", ""),
                "doc_authors": c.get("doc_authors", ""),
                "rrf_score": c.get("rrf_score", 0),
            }
            for c in context_chunks
        ],
    }


# ── Export ─────────────────────────────────────────────────────────────────────

@router.post("/export")
def export_chat(req: ExportRequest):
    from app.utils.export import export_chat_to_docx
    if not req.messages:
        raise HTTPException(400, "Không có tin nhắn để xuất")
    docx_bytes = export_chat_to_docx(req.messages, req.title)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="chat_{datetime.now().strftime("%Y%m%d")}.docx"'}
    )


# ── File chat (inline upload) ─────────────────────────────────────────────────

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB per file
SUPPORTED_TYPES = {"pdf", "docx", "doc", "xlsx", "xls", "jpg", "jpeg", "png", "gif", "bmp", "webp"}


@router.post("/file-chat")
def chat_with_files(
    query: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    document_ids: str = Form("[]"),  # JSON array string
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Chat with inline uploaded files (PDF, DOCX, XLSX, images).
    Files are parsed on-the-fly and their text is injected as context for the LLM.
    Nothing is stored permanently.
    """
    if not query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    if len(files) > 10:
        raise HTTPException(400, "Tối đa 10 file mỗi lần gửi")

    # Parse document_ids
    try:
        doc_ids = json.loads(document_ids) if document_ids and document_ids != "[]" else []
    except json.JSONDecodeError:
        doc_ids = []

    # Validate & parse each file
    import os
    file_contexts: list[str] = []
    for f in files:
        # Handle both 'photo.png' and 'C:\Users\HP\Pictures\photo.png' paths
        raw_name = f.filename or ""
        ext = os.path.splitext(raw_name)[1].lstrip(".").lower()
        if ext not in SUPPORTED_TYPES:
            raise HTTPException(400, f"Định dạng '{ext}' không được hỗ trợ: {f.filename}")
        size = 0
        data = b""
        while True:
            chunk = f.file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                raise HTTPException(400, f"File '{f.filename}' vượt 50MB")
            data += chunk
        text = parse_file(data, f.filename)
        file_contexts.append(f"[File: {f.filename}]\n{text}\n")

    # Build context block from files
    file_context_block = ""
    if file_contexts:
        file_context_block = (
            "\n\n===== TAI LIEU DINH KEM =====\n"
            + "\n\n---\n\n".join(file_contexts)
            + "\n===== KET THUC TAI LIEU =====\n\n"
        )

    # Build full prompt with file context
    if file_context_block:
        enriched_query = (
            f"{file_context_block}"
            f"Cau hoi nguoi dung:\n{query}"
        )
    else:
        enriched_query = query

    # Fallback: if no doc_ids and no files → general web search
    if not doc_ids and not file_contexts:
        web_results = duckduckgo_search(query, max_results=5)
        if not web_results:
            def no_results():
                yield "❌ Không tìm thấy kết quả tìm kiếm. Vui lòng thử lại."
            return StreamingResponse(no_results(), media_type="text/plain; charset=utf-8")

        def stream():
            for chunk in generate_stream_web_search(query, web_results):
                yield chunk
        return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")

    # Use RAG with document_ids + inline file context
    context_chunks = retrieve(enriched_query, doc_ids, db) if doc_ids else []

    # If we have file context but no doc chunks, still use file context
    if file_contexts and not context_chunks:
        # Build synthetic chunks from file text
        for fc in file_contexts:
            context_chunks.append({
                "content": fc,
                "document_id": "inline_file",
                "page_number": 1,
                "doc_filename": "File dinh kem",
                "doc_title": "File dinh kem",
                "doc_authors": "",
            })

    if not context_chunks and not file_contexts:
        def no_ctx():
            yield "__NO_CONTEXT__"
        return StreamingResponse(no_ctx(), media_type="text/plain; charset=utf-8")

    raw_stream = generate_stream(enriched_query, context_chunks)

    def stream_with_saving():
        collected: list[str] = []
        for chunk in raw_stream:
            collected.append(chunk)
            yield chunk
        if current_user is not None:
            full = "".join(collected)
            _save_chat_history(db, str(current_user.id), query, full, doc_ids)

    return StreamingResponse(
        stream_with_saving(),
        media_type="text/plain; charset=utf-8",
    )
