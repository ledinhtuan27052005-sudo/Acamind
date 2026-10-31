from typing import Optional
import time
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, field_validator
from uuid import UUID
from app.db.postgres import get_db
from app.core.security import get_optional_user
from app.core.document_access import readable_document_ids
from app.services.retriever import (
    retrieve,
    _vector_search_task,
    _bm25_task,
    get_cross_lingual_query_bundle,
)
from app.services.generator import generate_answer, evaluate_rag
from app.services.scientific_appraiser import (
    verify_atomic_claims_entailment,
    strip_academic_header_and_boilerplate,
)

router = APIRouter()


class ScopedEvaluationRequest(BaseModel):
    document_ids: Optional[list[str]] = None

    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, values):
        if values is None:
            return None
        return [str(UUID(value)) for value in values]


class EvalRequest(ScopedEvaluationRequest):
    question: str


def _compute_chunk_metrics(
    query: str,
    expanded_terms: list[str],
    chunks: list[dict],
    mode: str,
) -> dict:
    # Same observable metric for every architecture; no mode-specific floors.
    words = set(re.findall(r"[^\W_]+", (query + " " + " ".join(expanded_terms or [])).lower()))
    tokens = set(re.findall(r"[^\W_]+", " ".join(c.get("content") or "" for c in chunks).lower()))
    coverage = len(words & tokens) / len(words) if words else 0.0
    return {"keyword_coverage_pct": round(coverage * 100, 1),
            "semantic_alignment_pct": None, "authority_score_pct": None,
            "citation_precision_pct": None, "overall_composite_pct": None}


@router.post("/run")
def run_evaluation(req: EvalRequest, db: Session = Depends(get_db), user=Depends(get_optional_user)):
    if not req.question.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")

    search_ids = readable_document_ids(db, user, req.document_ids if req.document_ids else None)
    chunks = retrieve(req.question, search_ids, db, top_k=5)
    if not chunks:
        raise HTTPException(400, "Không tìm thấy context liên quan trong tài liệu đã chọn")

    answer = generate_answer(req.question, chunks)
    contexts = [c["content"] for c in chunks]
    scores = evaluate_rag(req.question, answer, contexts)
    claim_verification = verify_atomic_claims_entailment(req.question, answer, chunks, db=db)

    return {
        **scores,
        "answer": answer,
        "claim_verification": claim_verification,
        "sources": [
            {
                "document_id": c.get("document_id", ""),
                "filename": c.get("doc_filename") or c.get("doc_title") or "Document.pdf",
                "page": c["page_number"],
                "preview": strip_academic_header_and_boilerplate(c["content"])[:240],
            }
            for c in chunks
        ],
    }


@router.post("/ablation")
def run_ablation_benchmark(req: EvalRequest, db: Session = Depends(get_db), user=Depends(get_optional_user)):
    """Thực nghiệm Đối chứng Thuật toán Trực tiếp (Live A/B/C Ablation Benchmark):
    So sánh định lượng trên cùng truy vấn giữa 3 cấu hình:
      1. Baseline A: Naive Dense RAG (Single-Vector Cosine Search Only)
      2. Baseline B: Hybrid RRF (Dense + lexical search (PostgreSQL FTS / in-memory BM25), k=60, No Cross-Encoder / No Authority)
      3. Acamind Pipeline (Proposed: Cross-Lingual + Hybrid RRF + DCSR/Cross-Encoder + Authority + Parent-Context + CRAG)
    """
    if not req.question.strip():
        raise HTTPException(400, "Vui lòng nhập câu hỏi thực nghiệm")

    search_ids = readable_document_ids(db, user, req.document_ids if req.document_ids else None)
    doc_ids_str = ", ".join([f"'{did}'" for did in search_ids]) if search_ids else None

    bundle = get_cross_lingual_query_bundle(req.question)
    exp_terms = bundle.get("fts_expanded_terms") or []

    # ── 1. Chạy Baseline A: Naive Dense RAG (chỉ dùng vector gốc, không dịch, không truy xuất từ khóa) ──
    t_a0 = time.perf_counter()
    try:
        vec_rows = _vector_search_task(req.question, None, doc_ids_str)
    except Exception:
        vec_rows = []
    lat_a = round((time.perf_counter() - t_a0) * 1000.0, 1)

    cand_doc_ids = list({str(r.document_id) for r in vec_rows[:10]})
    doc_meta: dict[str, dict] = {}
    if cand_doc_ids:
        try:
            c_str = ", ".join([f"'{d}'" for d in cand_doc_ids])
            m_rows = db.execute(text(f"SELECT id, title, filename FROM documents WHERE id IN ({c_str})")).fetchall()
            doc_meta = {str(r.id): {"title": r.title or r.filename, "filename": r.filename or ""} for r in m_rows}
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

    naive_chunks = [
        {
            "id": str(r.id),
            "document_id": str(r.document_id),
            "doc_filename": doc_meta.get(str(r.document_id), {}).get("filename", "Document.pdf"),
            "doc_title": doc_meta.get(str(r.document_id), {}).get("title", "Document"),
            "page_number": int(r.page_number or 1),
            "content": r.content or "",
            "score": round(float(getattr(r, "score", 0.7)), 4),
        }
        for r in vec_rows[:5]
    ]
    metrics_a = _compute_chunk_metrics(req.question, exp_terms, naive_chunks, "naive_dense")

    # ── 2. Chạy Baseline B: Hybrid RRF (Vector + lexical, k=60, không Rerank / không Parent Context) ──
    t_b0 = time.perf_counter()
    try:
        bm25_rows = _bm25_task(req.question, None, None, search_ids, doc_ids_str)
    except Exception:
        bm25_rows = []

    k_rrf = 60
    rrf_scores: dict[str, float] = {}
    row_lookup: dict[str, object] = {}
    for rank, r in enumerate(vec_rows[:15]):
        rid = str(r.id)
        rrf_scores[rid] = rrf_scores.get(rid, 0.0) + 1.0 / (rank + 1 + k_rrf)
        row_lookup[rid] = r
    for rank, r in enumerate(bm25_rows[:15]):
        rid = str(r.id)
        rrf_scores[rid] = rrf_scores.get(rid, 0.0) + 1.0 / (rank + 1 + k_rrf)
        if rid not in row_lookup:
            row_lookup[rid] = r

    top_rrf_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:5]
    lat_b = round(lat_a + (time.perf_counter() - t_b0) * 1000.0, 1)

    hybrid_chunks = []
    for rid in top_rrf_ids:
        r_obj = row_lookup[rid]
        did = str(r_obj.document_id)
        hybrid_chunks.append({
            "id": rid,
            "document_id": did,
            "doc_filename": doc_meta.get(did, {}).get("filename", "Document.pdf"),
            "doc_title": doc_meta.get(did, {}).get("title", "Document"),
            "page_number": int(r_obj.page_number or 1),
            "content": r_obj.content or "",
            "score": round(rrf_scores[rid], 5),
        })
    metrics_b = _compute_chunk_metrics(req.question, exp_terms, hybrid_chunks, "hybrid_rrf")

    # ── 3. Chạy Acamind Full Pipeline (Proposed Architecture) ──
    t_c0 = time.perf_counter()
    acamind_chunks = retrieve(req.question, search_ids, db, top_k=5)
    lat_c = round((time.perf_counter() - t_c0) * 1000.0, 1)
    if not acamind_chunks:
        raise HTTPException(400, "Không tìm thấy ngữ cảnh phù hợp để chạy đối chứng.")

    metrics_c = _compute_chunk_metrics(req.question, exp_terms, acamind_chunks, "acamind_full")
    telemetry_c = acamind_chunks[0].get("_telemetry") or {}

    # Tạo câu trả lời & kiểm chứng mệnh đề trên Acamind Pipeline
    answer = generate_answer(req.question, acamind_chunks[:5])
    claim_shield = verify_atomic_claims_entailment(req.question, answer, acamind_chunks, db=db)

    def _format_preview_list(c_list: list[dict]) -> list[dict]:
        out = []
        for idx, ch in enumerate(c_list[:4], 1):
            fname = ch.get("doc_filename") or ch.get("doc_title") or "Document.pdf"
            title = ch.get("doc_title") or fname
            pno = int(ch.get("page_number") or 1)
            raw_t = ch.get("content") or ""
            clean_t = strip_academic_header_and_boilerplate(raw_t, paper_title=title)[:220]
            out.append({
                "rank": idx,
                "document_id": str(ch.get("document_id") or ""),
                "filename": fname,
                "title": title,
                "page": pno,
                "score": round(float(ch.get("rerank_score") or ch.get("rrf_score") or ch.get("score") or 0.0), 4),
                "snippet": clean_t or (ch.get("content") or "")[:200],
            })
        return out

    naive_faithfulness = hybrid_faithfulness = acamind_faithfulness = None

    pipelines = [
        {
            "id": "naive_dense",
            "name": "1. Baseline A: Naive Dense RAG",
            "architecture": "Single-Vector Cosine Similarity (HNSW 384-d Only)",
            "latency_ms": lat_a,
            "keyword_coverage_pct": metrics_a["keyword_coverage_pct"],
            "semantic_alignment_pct": metrics_a["semantic_alignment_pct"],
            "citation_precision_pct": metrics_a["citation_precision_pct"],
            "faithfulness_pct": naive_faithfulness,
            "overall_score_pct": metrics_a["overall_composite_pct"],
            "dcsr_active": False,
            "crag_verified": False,
            "top_chunks": _format_preview_list(naive_chunks),
        },
        {
            "id": "hybrid_rrf",
            "name": "2. Baseline B: Standard Hybrid RRF",
            "architecture": "Dense HNSW + lexical (PostgreSQL FTS / in-memory BM25) + RRF (k=60)",
            "latency_ms": lat_b,
            "keyword_coverage_pct": metrics_b["keyword_coverage_pct"],
            "semantic_alignment_pct": metrics_b["semantic_alignment_pct"],
            "citation_precision_pct": metrics_b["citation_precision_pct"],
            "faithfulness_pct": hybrid_faithfulness,
            "overall_score_pct": metrics_b["overall_composite_pct"],
            "dcsr_active": False,
            "crag_verified": False,
            "top_chunks": _format_preview_list(hybrid_chunks),
        },
        {
            "id": "acamind_full",
            "name": "3. Acamind Proposed Pipeline (Ours)",
            "architecture": "Dual-Memory L1/L2 + Cross-Lingual RRF + DCSR/Cross-Encoder + Authority + CRAG",
            "latency_ms": lat_c,
            "keyword_coverage_pct": metrics_c["keyword_coverage_pct"],
            "semantic_alignment_pct": metrics_c["semantic_alignment_pct"],
            "citation_precision_pct": metrics_c["citation_precision_pct"],
            "faithfulness_pct": acamind_faithfulness,
            "overall_score_pct": metrics_c["overall_composite_pct"],
            "dcsr_active": True,
            "dcsr_fast_skip": bool(telemetry_c.get("dcsr_fast_skip", False)),
            "crag_verified": bool(telemetry_c.get("crag_passed", False)),
            "top_chunks": _format_preview_list(acamind_chunks),
        },
    ]

    gains = {
        "faithfulness_gain_vs_naive": None,
        "recall_gain_vs_naive": None,
        "keyword_coverage_delta_vs_naive": round(metrics_c["keyword_coverage_pct"] - metrics_a["keyword_coverage_pct"], 1),
        "citation_gain_vs_naive": None,
        "overall_gain_vs_naive": None,
    }

    return {
        "question": req.question,
        "expanded_bilingual_terms": exp_terms,
        "pipelines": pipelines,
        "gains": gains,
        "telemetry": telemetry_c,
        "answer": answer,
        "claim_verification": claim_shield,
    }


# ── Multi-Query Statistical Significance Benchmark Suite & Pareto Frontier ────

class AblationSuiteRequest(ScopedEvaluationRequest):
    custom_question: Optional[str] = None
    document_ids: Optional[list[str]] = None


@router.post("/ablation-suite")
def run_statistical_ablation_suite(req: AblationSuiteRequest, db: Session = Depends(get_db)):
    raise HTTPException(422, "Chưa có bộ nhãn độc lập và các lượt chạy đối chứng thực đo để kiểm định thống kê. Không tạo p-value, phần trăm độ đúng hoặc đường Pareto từ điểm giả lập. Dùng đối chiếu một câu hỏi để xem độ phủ từ khóa và thời gian truy xuất; đây chưa phải benchmark độ chính xác.")
