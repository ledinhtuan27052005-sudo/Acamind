from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.postgres import get_db
from app.services.retriever import retrieve
from app.services.generator import (
    analyze_symptoms_dsm,
    analyze_symptoms_with_fallback,
    synthesize_treatment_protocol,
    compare_psychology_schools,
    summarize_topic_research,
    classify_query_domain,
)
from app.services.web_scraper import duckduckgo_search
from app.services.llm_client import llm_configuration_error

router = APIRouter()


class SymptomRequest(BaseModel):
    symptom_description: str
    document_ids: list[str] = []
    top_k: Optional[int] = 8


class TreatmentRequest(BaseModel):
    condition: str
    document_ids: list[str]
    top_k: Optional[int] = 8


class CompareSchoolsRequest(BaseModel):
    topic: str
    document_ids: list[str]
    top_k: Optional[int] = 10


class TopicSummaryRequest(BaseModel):
    topic: str
    document_ids: list[str]
    top_k: Optional[int] = 15


# Minimum number of document chunks considered "sufficient"
MIN_SUFFICIENT_CHUNKS = 3

# ── 1. DSM/ICD Symptom Analysis ──────────────────────────────────────────

@router.post("/symptom-analysis")
def symptom_analysis(req: SymptomRequest, db: Session = Depends(get_db)):
    """Analyze symptoms against DSM/ICD from documents, with internet fallback."""
    if not req.symptom_description.strip():
        raise HTTPException(400, "Symptom description cannot be empty")

    # Try to retrieve from uploaded documents
    chunks = []
    if req.document_ids:
        chunks = retrieve(req.symptom_description, req.document_ids, db, top_k=req.top_k)

    # If document chunks are sufficient, use document-only analysis
    if len(chunks) >= MIN_SUFFICIENT_CHUNKS:
        config_error = llm_configuration_error()
        if config_error:
            raise HTTPException(status_code=503, detail=config_error)
        result = analyze_symptoms_dsm(req.symptom_description, chunks)
        sources = [
            {
                "doc_title": c.get("doc_title", ""),
                "doc_authors": c.get("doc_authors", ""),
                "page_number": c.get("page_number"),
                "document_id": c.get("document_id"),
            }
            for c in chunks
        ]
        return {
            "analysis": result,
            "sources": sources,
            "chunks_used": len(chunks),
        }

    # Insufficient document info — supplement with web search
    web_results = []
    try:
        search_query = f"mental health psychology symptoms {req.symptom_description[:200]}"
        web_results = duckduckgo_search(search_query, max_results=8)
    except Exception:
        pass  # Web search failure is non-fatal

    # If we have neither documents nor web results, inform the user
    if not chunks and not web_results:
        raise HTTPException(
            404,
            "No relevant information found from documents or internet. "
            "Please try adding psychology documents to the library or check your internet connection."
        )

    config_error = llm_configuration_error()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    # Use the combined fallback analyzer
    result = analyze_symptoms_with_fallback(req.symptom_description, chunks, web_results)

    # Build sources list (documents + web)
    sources = [
        {
            "doc_title": c.get("doc_title", ""),
            "doc_authors": c.get("doc_authors", ""),
            "page_number": c.get("page_number"),
            "document_id": c.get("document_id"),
        }
        for c in chunks
    ]
    # Add web sources
    for wr in web_results:
        sources.append({
            "doc_title": wr.get("title", "Web Source"),
            "doc_authors": wr.get("href", wr.get("url", "")),
            "page_number": None,
            "document_id": None,
        })

    return {
        "analysis": result,
        "sources": sources,
        "chunks_used": len(chunks),
        "web_sources_used": len(web_results),
    }


# ── 2. Treatment Protocol ────────────────────────────────────────────────────────

@router.post("/treatment-protocol")
def treatment_protocol(req: TreatmentRequest, db: Session = Depends(get_db)):
    """Synthesize treatment protocols from multiple scientific documents."""
    if not req.condition.strip():
        raise HTTPException(400, "Condition name cannot be empty")
    if not req.document_ids:
        raise HTTPException(400, "At least 1 document must be selected")

    chunks = retrieve(req.condition, req.document_ids, db, top_k=req.top_k)
    if not chunks:
        raise HTTPException(
            404,
            "No treatment information found in the selected documents."
        )

    config_error = llm_configuration_error()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    result = synthesize_treatment_protocol(req.condition, chunks)
    sources = [
        {
            "doc_title": c.get("doc_title", ""),
            "doc_authors": c.get("doc_authors", ""),
            "page_number": c.get("page_number"),
            "document_id": c.get("document_id"),
        }
        for c in chunks
    ]
    return {
        "protocol": result,
        "sources": sources,
        "chunks_used": len(chunks),
    }


# ── 3. Compare Psychology Schools ──────────────────────────────────────────

@router.post("/compare-schools")
def compare_schools(req: CompareSchoolsRequest, db: Session = Depends(get_db)):
    """Compare perspectives of multiple psychology schools on a topic."""
    if not req.topic.strip():
        raise HTTPException(400, "Topic cannot be empty")
    if not req.document_ids:
        raise HTTPException(400, "At least 2 documents must be selected for school comparison")

    chunks = retrieve(req.topic, req.document_ids, db, top_k=req.top_k)
    if not chunks:
        raise HTTPException(
            404,
            "No relevant content found in the selected documents."
        )

    config_error = llm_configuration_error()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    result = compare_psychology_schools(req.topic, chunks)
    sources = [
        {
            "doc_title": c.get("doc_title", ""),
            "doc_authors": c.get("doc_authors", ""),
            "page_number": c.get("page_number"),
            "document_id": c.get("document_id"),
        }
        for c in chunks
    ]
    return {
        "comparison": result,
        "sources": sources,
        "chunks_used": len(chunks),
    }


# ── 4. Topic Research Summary ────────────────────────────────────────

@router.post("/topic-summary")
def topic_summary(req: TopicSummaryRequest, db: Session = Depends(get_db)):
    """Synthesize all research on a psychology topic from the document repository."""
    if not req.topic.strip():
        raise HTTPException(400, "Topic cannot be empty")
    if not req.document_ids:
        raise HTTPException(400, "At least 1 document must be selected")

    chunks = retrieve(req.topic, req.document_ids, db, top_k=req.top_k)
    if not chunks:
        raise HTTPException(
            404,
            "No research found on this topic in the document repository."
        )

    config_error = llm_configuration_error()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    result = summarize_topic_research(req.topic, chunks)
    sources = [
        {
            "doc_title": c.get("doc_title", ""),
            "doc_authors": c.get("doc_authors", ""),
            "page_number": c.get("page_number"),
            "document_id": c.get("document_id"),
        }
        for c in chunks
    ]
    return {
        "summary": result,
        "sources": sources,
        "chunks_used": len(chunks),
        "topic": req.topic,
    }
