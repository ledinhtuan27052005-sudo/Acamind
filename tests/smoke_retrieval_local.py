"""Read-only integration smoke; requires the existing local DB and cached models."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.db.postgres import SessionLocal
from app.services.retriever import retrieve
from sqlalchemy import text

with SessionLocal() as session:
    rows = session.execute(text("SELECT id::text, title FROM documents WHERE status='ready' AND title IS NOT NULL ORDER BY title LIMIT 2")).fetchall()
    assert len(rows) == 2
    ids = [row.id for row in rows]
    question = 'Compare ' + ' and '.join('"' + row.title + '"' for row in rows) + ' on methods'
    start = time.perf_counter()
    chunks = retrieve(question, ids, session, top_k=8, rerank_top_n=12)
    targets = {c.get('sub_query_target') for c in chunks}
    assert targets == {r.title for r in rows}, 'One study lost during retrieval'
    assert all(c['document_id'] in ids for c in chunks), 'Document scope widened'
    assert all(c.get('target_identity') == 'exact_title' for c in chunks)
    print(json.dumps({'chunks': len(chunks), 'targets': len(targets),
                      'elapsed_ms': round((time.perf_counter()-start)*1000, 1),
                      'timings': chunks[0]['_telemetry'].get('stage_timings_ms'),
                      'scored': sum(bool(c.get('rerank_score_available')) for c in chunks)}))
