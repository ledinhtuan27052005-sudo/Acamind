"""Measure retrieval coverage for approved questions without passing gold sources to retrieval."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.postgres import SessionLocal
from app.services.retriever import retrieve
from run_approved_100_eval import parse_questions, QUESTION_FILE


def main() -> None:
    questions = parse_questions(QUESTION_FILE.read_text(encoding="utf-8"))
    requested = os.getenv("ACAMIND_DIAGNOSTIC_IDS", "").strip()
    selected = {int(v) for v in requested.split(",") if v.strip()} if requested else None
    output = ROOT / "results" / os.getenv("ACAMIND_DIAGNOSTIC_FILE", "retrieval_diagnostic_100.json")
    previous = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {"rows": []}
    done = {row["id"] for row in previous["rows"]}
    for q in questions:
        if q["id"] in done or (selected is not None and q["id"] not in selected):
            continue
        started = time.perf_counter()
        with SessionLocal() as db:
            chunks = retrieve(q["question"], None, db, top_k=12)
        names = [str(c.get("doc_filename") or "") for c in chunks]
        hit = [sid for sid in q["source_ids"] if any(sid in name for name in names)]
        row = {
            "id": q["id"], "question": q["question"],
            "target_sources": q["source_ids"], "target_hits": hit,
            "target_source_recall": len(hit) / len(q["source_ids"]) if q["source_ids"] else None,
            "retrieved": [{"filename": names[i], "page": c.get("page_number"),
                           "content_start": (c.get("parent_context") or c.get("content") or "")[:220]}
                          for i, c in enumerate(chunks)],
            "route": chunks[0].get("_telemetry", {}).get("route") if chunks else None,
            "seconds": round(time.perf_counter() - started, 2),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        previous["rows"].append(row)
        temp = output.with_suffix(".json.tmp")
        temp.write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(output)
        print(f"{q['id']}: {len(hit)}/{len(q['source_ids'])} target PDFs, route={row['route']}, {row['seconds']}s", flush=True)
    print(f"SAVED {output}", flush=True)


if __name__ == "__main__":
    main()
