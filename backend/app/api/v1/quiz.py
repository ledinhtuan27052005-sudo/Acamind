import uuid, json, re
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.db.postgres import get_db
from app.services.llm_client import get_default_client

router = APIRouter()
llm_client = get_default_client()

# ── Pydantic models ────────────────────────────────────────────────

class GenerateQuizRequest(BaseModel):
    document_id: str
    num_questions: int = 10
    question_type: str = "mixed" # mcq | true_false | mixed
    language: str = "vi"
    user_id: Optional[str] = None

class SubmitAnswerRequest(BaseModel):
    attempt_id: str
    question_id: str
    user_answer: str
    is_flagged: bool = False

class SubmitQuizRequest(BaseModel):
    attempt_id: str
    time_spent_seconds: int


# ── Helper ─────────────────────────────────────────────────────────

def _parse_quiz_json(raw: str) -> list[dict]:
    """Parse LLM output thành list[dict]. Robust với output bị cắt giữa chừng.

    Thử tuần tự:
    1. Strip markdown code block → parse toàn bộ.
    2. Nếu parse lỗi (bị cắt), tìm các object {...} hoàn chỉnh cuối cùng.
    3. Nếu vẫn không được, raise ValueError.
    """
    if not raw or not raw.strip():
        raise ValueError("LLM trả về rỗng")

    text = raw.strip()

    # Bỏ code fences nếu có
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)

    # Thử parse toàn bộ trước
    start = text.find("[")
    if start == -1:
        raise ValueError("LLM không trả về JSON array")
    snippet = text[start:]

    # Cách 1: parse thẳng
    try:
        data = json.loads(snippet)
        if isinstance(data, list):
            return [q for q in data if isinstance(q, dict)]
    except json.JSONDecodeError:
        pass

    # Cách 2: tìm từng object {...} hoàn chỉnh (cứu khi bị cắt giữa array)
    questions = []
    # Tìm tất cả cặp { ... } cân bằng bằng regex non-greedy + đếm brace
    i = 0
    while i < len(snippet):
        if snippet[i] == "{":
            depth = 0
            in_string = False
            escape = False
            for j in range(i, len(snippet)):
                ch = snippet[j]
                if escape:
                    escape = False
                    continue
                if ch == "\\":
                    escape = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        # Thử parse object này
                        candidate = snippet[i:j + 1]
                        try:
                            obj = json.loads(candidate)
                            if isinstance(obj, dict) and ("question_text" in obj or "question" in obj):
                                questions.append(obj)
                        except json.JSONDecodeError:
                            pass
                        i = j
                        break
            else:
                # Hết string mà chưa đóng brace → bỏ qua
                break
        i += 1

    if questions:
        return questions
    raise ValueError("LLM không trả về JSON array hợp lệ")


# ── 1. Tạo quiz ────────────────────────────────────────────────────

@router.post("/generate")
def generate_quiz(req: GenerateQuizRequest, db: Session = Depends(get_db)):
    """Tạo bộ câu hỏi từ nội dung PDF bằng AI, lưu vào DB.

    Ràng buộc:
    - num_questions: 1..20
    """
    # Validate số câu (tối thiểu 1, tối đa 20)
    if req.num_questions < 1 or req.num_questions > 20:
        raise HTTPException(400, "Số câu hỏi phải từ 1 đến 20")

    chunks_rows = db.execute(
        text("SELECT content FROM chunks WHERE document_id = :doc_id ORDER BY chunk_index LIMIT 30"),
        {"doc_id": req.document_id},
    ).fetchall()

    if not chunks_rows:
        raise HTTPException(404, "Không có nội dung. Document chưa xử lý xong.")

    # Giảm context xuống 10000 chars: thực nghiệm cho thấy context quá lớn (>20K)
    # khiến LLM viết explanation quá dài → max_tokens không đủ → bị cắt JSON.
    # 10K chars ~ 3-4K tokens, đủ dữ liệu cho 10-30 câu nếu chunks chất lượng.
    context = "\n\n".join([c.content for c in chunks_rows])[:10000]

    lang_instr = "Tạo câu hỏi bằng tiếng Việt" if req.language == "vi" else "Generate questions in English"
    qtype_desc = (
        "Trắc nghiệm 4 đáp án" if req.question_type == "mcq"
        else "Đúng/Sai" if req.question_type == "true_false"
        else "Hỗn hợp trắc nghiệm và đúng/sai"
    )

    prompt = f"""Dựa trên nội dung tài liệu sau, {lang_instr}.
Tạo chính xác {req.num_questions} câu hỏi.
Loại câu hỏi: {qtype_desc}.

Trả về JSON array THUẦN TÚY (không markdown, không text bên ngoài):
[
  {{
    "question_text": "Câu hỏi?",
    "question_type": "mcq",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_answer": "A",
    "explanation": "Giải thích tại sao A đúng",
    "source_text": "Đoạn văn gốc trong tài liệu"
  }}
]
Với câu true_false: options = ["Đúng", "Sai"], correct_answer = "Đúng" hoặc "Sai"

NỘI DUNG TÀI LIỆU:
{context}"""

    # Tính max_tokens theo số câu: 1 câu ~1500, 20 câu ~14000, cap 16384.
    # Tăng lên ~700 tokens/câu để tránh LLM bị cắt JSON.
    max_tok = min(1024 + req.num_questions * 700, 16384)

    raw = llm_client.complete(
        messages=[{"role": "user", "content": prompt}],
        system="Bạn là chuyên gia tạo đề kiểm tra học thuật. CHỈ trả về JSON array thuần túy, KHÔNG markdown, KHÔNG ```json, KHÔNG giải thích bên ngoài.",
        max_tokens=max_tok,
        temperature=0.3,
    )

    # Thử parse, nếu fail (do LLM cắt JSON) thì retry tối đa 3 lần với số câu giảm dần.
    questions_data = None
    last_error: Exception | None = None
    target_n = req.num_questions

    for attempt in range(4):  # 1 lần đầu + 3 retry
        try:
            if attempt == 0:
                data = _parse_quiz_json(raw)
            else:
                # Retry: giảm 1/3 số câu mỗi lần
                target_n = max(1, req.num_questions - (req.num_questions // 3) * attempt)
                retry_prompt = prompt.replace(
                    f"Tạo chính xác {req.num_questions} câu hỏi",
                    f"Tạo chính xác {target_n} câu hỏi",
                )
                raw2 = llm_client.complete(
                    messages=[{"role": "user", "content": retry_prompt}],
                    system="Bạn là chuyên gia tạo đề kiểm tra học thuật. CHỈ trả về JSON array thuần túy, KHÔNG markdown, KHÔNG ```json, KHÔNG giải thích bên ngoài.",
                    max_tokens=min(1024 + target_n * 1200, 16384),
                    temperature=0.3 + attempt * 0.1,  # tăng diversity
                )
                data = _parse_quiz_json(raw2)
            # Nếu parse OK và có >= 1 câu → thành công
            if data and len(data) > 0:
                questions_data = data
                req.num_questions = target_n if attempt > 0 else len(data)
                break
            last_error = ValueError("LLM trả về array rỗng")
        except (ValueError, json.JSONDecodeError) as e:
            last_error = e
            continue

    if not questions_data:
        raise HTTPException(
            500,
            f"LLM trả về format không hợp lệ sau 4 lần thử. Lỗi: {last_error}. "
            f"Vui lòng thử lại hoặc giảm số câu hỏi."
        )

    # Lấy tên document
    doc_row = db.execute(
        text("SELECT filename, title FROM documents WHERE id = :id"),
        {"id": req.document_id},
    ).first()
    doc_title = (doc_row.title or doc_row.filename) if doc_row else "Unknown"

    # Lưu quiz_set
    quiz_set_id = str(uuid.uuid4())
    db.execute(
        text("""
            INSERT INTO quiz_sets (id, document_id, user_id, title, question_type, difficulty, language, total_questions)
            VALUES (:id, :doc_id, :user_id, :title, :qtype, :diff, :lang, :total)
        """),
        {
            "id":      quiz_set_id,
            "doc_id":  req.document_id,
            "user_id": req.user_id,
            "title":   f"Kiểm tra: {doc_title[:100]}",
            "qtype":   req.question_type,
            "diff":    "medium",
            "lang":    req.language,
            "total":   len(questions_data),
        },
    )

    # Lưu từng câu hỏi
    for idx, q in enumerate(questions_data):
        db.execute(
            text("""
                INSERT INTO quiz_questions
                    (id, quiz_set_id, question_index, question_text, question_type, options, correct_answer, explanation, source_text)
                VALUES (:id, :qset, :idx, :qtext, :qtype, cast(:opts AS jsonb), :correct, :expl, :src)
            """),
            {
                "id":      str(uuid.uuid4()),
                "qset":    quiz_set_id,
                "idx":     idx,
                "qtext":   q.get("question_text", ""),
                "qtype":   q.get("question_type", "mcq"),
                "opts":    json.dumps(q.get("options", []), ensure_ascii=False),
                "correct": q.get("correct_answer", ""),
                "expl":    q.get("explanation", ""),
                "src":     q.get("source_text", "")[:500],
            },
        )
    db.commit()

    return {
        "quiz_set_id":     quiz_set_id,
        "total_questions": len(questions_data),
        "title":           f"Kiểm tra: {doc_title[:60]}",
        "difficulty":      "medium",
    }


# ── 2. Lấy câu hỏi (không có đáp án) ─────────────────────────────

@router.get("/{quiz_set_id}")
def get_quiz(quiz_set_id: str, db: Session = Depends(get_db)):
    """Lấy bộ câu hỏi để làm bài (không trả về đáp án đúng)."""
    quiz = db.execute(
        text("SELECT * FROM quiz_sets WHERE id = :id"), {"id": quiz_set_id}
    ).first()
    if not quiz:
        raise HTTPException(404, "Không tìm thấy quiz")

    questions = db.execute(
        text("""
            SELECT id, question_index, question_text, question_type, options
            FROM quiz_questions WHERE quiz_set_id = :id ORDER BY question_index
        """),
        {"id": quiz_set_id},
    ).fetchall()

    return {
        "quiz_set_id":     quiz_set_id,
        "title":           quiz.title,
        "difficulty":      quiz.difficulty,
        "total_questions": quiz.total_questions,
        "questions": [
            {
                "id":      str(q.id),
                "index":   q.question_index,
                "text":    q.question_text,
                "type":    q.question_type,
                "options": q.options if q.options else [],  # JSONB trả về list trực tiếp, không cần json.loads()
            }
            for q in questions
        ],
    }


# ── 3. Bắt đầu attempt ────────────────────────────────────────────

@router.post("/attempt/start")
def start_attempt(
    quiz_set_id: str = Query(...),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Tạo attempt record khi user bắt đầu làm bài."""
    attempt_id = str(uuid.uuid4())
    deadline   = datetime.now() + timedelta(hours=5)
    db.execute(
        text("""
            INSERT INTO quiz_attempts (id, quiz_set_id, user_id, deadline)
            VALUES (:id, :qset, :user_id, :deadline)
        """),
        {"id": attempt_id, "qset": quiz_set_id, "user_id": user_id, "deadline": deadline},
    )
    db.commit()
    return {"attempt_id": attempt_id, "deadline": deadline.isoformat()}


# ── 4. Lưu đáp án từng câu ────────────────────────────────────────

@router.post("/answer")
def save_answer(req: SubmitAnswerRequest, db: Session = Depends(get_db)):
    """Lưu đáp án của 1 câu (có thể gọi nhiều lần, upsert theo attempt+question)."""
    existing = db.execute(
        text("SELECT id FROM quiz_answers WHERE attempt_id = :aid AND question_id = :qid"),
        {"aid": req.attempt_id, "qid": req.question_id},
    ).first()

    if existing:
        db.execute(
            text("""
                UPDATE quiz_answers
                SET user_answer = :ans, is_flagged = :flag, answered_at = :now
                WHERE attempt_id = :aid AND question_id = :qid
            """),
            {
                "ans": req.user_answer, "flag": req.is_flagged,
                "now": datetime.now(), "aid": req.attempt_id, "qid": req.question_id,
            },
        )
    else:
        db.execute(
            text("""
                INSERT INTO quiz_answers (id, attempt_id, question_id, user_answer, is_flagged, answered_at)
                VALUES (:id, :aid, :qid, :ans, :flag, :now)
            """),
            {
                "id":   str(uuid.uuid4()),
                "aid":  req.attempt_id,
                "qid":  req.question_id,
                "ans":  req.user_answer,
                "flag": req.is_flagged,
                "now":  datetime.now(),
            },
        )
    db.commit()
    return {"ok": True}


# ── 5. Nộp bài + chấm điểm ────────────────────────────────────────

@router.post("/attempt/submit")
def submit_quiz(req: SubmitQuizRequest, db: Session = Depends(get_db)):
    """Nộp bài — chấm điểm, lưu kết quả, trả về điểm số và giải thích."""
    attempt = db.execute(
        text("SELECT quiz_set_id FROM quiz_attempts WHERE id = :id"), {"id": req.attempt_id}
    ).first()
    if not attempt:
        raise HTTPException(404, "Attempt không tồn tại")

    # Đáp án user
    user_answers = db.execute(
        text("SELECT question_id, user_answer FROM quiz_answers WHERE attempt_id = :id"),
        {"id": req.attempt_id},
    ).fetchall()

    # Đáp án đúng + explanation
    correct_rows = db.execute(
        text("SELECT id, question_text, correct_answer, explanation FROM quiz_questions WHERE quiz_set_id = :qset"),
        {"qset": attempt.quiz_set_id},
    ).fetchall()
    correct_map = {str(r.id): r for r in correct_rows}

    # Chấm điểm
    total_correct = 0
    review = []
    answered_map = {str(a.question_id): a.user_answer for a in user_answers}

    for row in correct_rows:
        qid       = str(row.id)
        user_ans  = (answered_map.get(qid) or "").strip().upper()
        correct   = row.correct_answer.strip().upper()
        is_right  = user_ans == correct
        if is_right:
            total_correct += 1
        if qid in answered_map:
            db.execute(
                text("UPDATE quiz_answers SET is_correct = :c WHERE attempt_id = :aid AND question_id = :qid"),
                {"c": is_right, "aid": req.attempt_id, "qid": qid},
            )
        review.append({
            "question":       row.question_text,
            "user_answer":    answered_map.get(qid, "(Chưa trả lời)"),
            "correct_answer": row.correct_answer,
            "is_correct":     is_right,
            "explanation":    row.explanation,
        })

    total = len(correct_rows)
    score = round((total_correct / total) * 100, 2) if total > 0 else 0.0

    db.execute(
        text("""
            UPDATE quiz_attempts
            SET status='submitted', submitted_at=:now, score=:score,
                total_correct=:tc, time_spent_seconds=:time
            WHERE id=:id
        """),
        {
            "now":  datetime.now(),
            "score": score,
            "tc":   total_correct,
            "time": req.time_spent_seconds,
            "id":   req.attempt_id,
        },
    )
    db.commit()

    grade = (
        "Xuất sắc"   if score >= 90 else
        "Tốt"        if score >= 75 else
        "Trung bình" if score >= 50 else
        "Chưa đạt"
    )
    return {
        "score":              score,
        "total_correct":      total_correct,
        "total_questions":    total,
        "grade":              grade,
        "time_spent_seconds": req.time_spent_seconds,
        "review":             review,
    }
