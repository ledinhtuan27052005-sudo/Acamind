from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.postgres import get_db
from app.services.retriever import retrieve
from app.services.generator import generate_answer, evaluate_rag

router = APIRouter()


class EvalRequest(BaseModel):
    question: str
    document_ids: list[str]


@router.post("/run")
def run_evaluation(req: EvalRequest, db: Session = Depends(get_db)):
    if not req.document_ids:
        raise HTTPException(400, "Cần chọn ít nhất một tài liệu")

    chunks = retrieve(req.question, req.document_ids, db, top_k=5)
    if not chunks:
        raise HTTPException(400, "Không tìm thấy context liên quan trong tài liệu đã chọn")

    answer = generate_answer(req.question, chunks)
    contexts = [c["content"] for c in chunks]
    scores = evaluate_rag(req.question, answer, contexts)

    return {
        **scores,
        "answer": answer,
        "sources": [{"page": c["page_number"], "preview": c["content"][:200]} for c in chunks],
    }
