"""Read-only local comparison smoke against two indexed documents."""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import text
from app.core.config import settings
from app.db.postgres import SessionLocal
from app.services.evidence_policy import assess_evidence, evidence_packet
from app.services.retriever import retrieve

if len(sys.argv) > 1:
    settings.EVIDENCE_LOCAL_MODEL = sys.argv[1]

with SessionLocal() as session:
    rows = session.execute(text(
        "SELECT id::text, title FROM documents WHERE status='ready' AND title IS NOT NULL "
        "ORDER BY title LIMIT 2"
    )).fetchall()
    assert len(rows) == 2
    targets = [row.title for row in rows]
    ids = [row.id for row in rows]
    question = 'Compare ' + ' and '.join('"' + title + '"' for title in targets) + ' on methods and findings'
    start = time.perf_counter()
    chunks = retrieve(question, ids, session, top_k=12, rerank_top_n=30)
    retrieval_ms = round((time.perf_counter() - start) * 1000, 1)
    assert {c.get("sub_query_target") for c in chunks} == set(targets)
    packet = evidence_packet(targets, chunks)
    start = time.perf_counter()
    result = assess_evidence(question, targets, chunks)
    print(json.dumps({
        "model": settings.EVIDENCE_LOCAL_MODEL,
        "targets": len(targets), "chunks": len(chunks),
        "packet_chars": sum(len(p["text"]) for p in packet),
        "retrieval_ms": retrieval_ms,
        "verification_ms": round((time.perf_counter() - start) * 1000, 1),
        "action": result["action"],
        "supported_cells": result.get("supported_cells"),
        "total_cells": result.get("total_cells"),
    }, ensure_ascii=True))
    assert result["action"] != "unavailable", "Verifier failed on real indexed passages"
