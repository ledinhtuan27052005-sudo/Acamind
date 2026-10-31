"""Re-run the revised standalone Q1/Q9 benchmark items without overwriting the original 100-item run."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
QUESTION_FILE = ROOT / "results" / "question_set_vi_100_for_approval.md"
OUT = ROOT / "results" / "experiment_100_q1_q9_retest.json"


def main() -> None:
    from app.db.postgres import SessionLocal
    from app.services import generator, retriever
    from app.services.llm_client import get_default_client
    from run_approved_100_eval import parse_questions

    selected = [q for q in parse_questions(QUESTION_FILE.read_text(encoding="utf-8")) if q["id"] in {1, 9}]
    if len(selected) != 2:
        raise SystemExit("Could not load revised Q1 and Q9 from the approved question set.")

    client = get_default_client()
    original_complete = client.complete
    last_call = [0.0]

    def throttled_complete(*args, **kwargs):
        delay = 4.2 - (time.monotonic() - last_call[0])
        if delay > 0:
            time.sleep(delay)
        last_call[0] = time.monotonic()
        return original_complete(*args, **kwargs)

    client.complete = throttled_complete
    generator.llm_client = client
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    attempts = previous.get("attempts", [])
    if previous.get("rows"):
        attempts.append({"started_at": previous.get("started_at"), "model": previous.get("model"), "rows": previous["rows"]})
    run = {"started_at": datetime.now(timezone.utc).isoformat(), "model": client.model, "rows": []}
    attempts.append(run)
    output = {
        "experiment": "approved_100_q1_q9_retest",
        "model": client.model,
        "source_question_file": QUESTION_FILE.name,
        "note": "Targeted retest; original 100-item run is preserved unchanged.",
        "attempts": attempts,
    }

    try:
        for q in selected:
            row = {**q, "status": "running"}
            run["rows"].append(row)
            print(f"START Q{q['id']}", flush=True)
            try:
                with SessionLocal() as db:
                    chunks = retriever.retrieve(q["question"], None, db, top_k=12)
                    telemetry = chunks[0].get("_telemetry") if chunks else None
                    for chunk in chunks:
                        chunk.pop("_telemetry", None)
                    answer = generator.generate_answer(q["question"], chunks, lang="vi")
                retrieved = [
                    {
                        "filename": c.get("doc_filename") or c.get("filename") or c.get("doc_title"),
                        "page": c.get("page_number"),
                        "content": (c.get("parent_context") or c.get("content") or "")[:1800],
                    }
                    for c in chunks
                ]
                names = " ".join(str(c.get("filename") or "") for c in retrieved)
                row.update({
                    "status": "completed",
                    "answer": answer,
                    "retrieved": retrieved,
                    "retrieved_target_source_ids": [s for s in q["source_ids"] if s in names],
                    "telemetry": telemetry,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
                print(f"DONE Q{q['id']} | target_hits={row['retrieved_target_source_ids']}", flush=True)
            except Exception as exc:
                row.update({"status": "error", "error": str(exc)[:1000]})
                print(f"ERROR Q{q['id']} | {str(exc)[:250]}", flush=True)
            OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        client.complete = original_complete

    print(f"RESULTS={OUT}", flush=True)


if __name__ == "__main__":
    main()
