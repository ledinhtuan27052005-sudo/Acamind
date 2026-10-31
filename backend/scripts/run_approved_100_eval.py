"""Run the user-approved 100-question psychology evaluation through Acamind."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

QUESTION_FILE = ROOT / "results" / "question_set_vi_100_for_approval.md"
OUTPUT_SUFFIX = os.getenv("ACAMIND_EVAL_OUTPUT_SUFFIX", "")
OUT_JSON = ROOT / "results" / f"experiment_100_approved_results{OUTPUT_SUFFIX}.json"
OUT_CSV = ROOT / "results" / f"experiment_100_approved_summary{OUTPUT_SUFFIX}.csv"
OUT_SUMMARY = ROOT / "results" / f"experiment_100_approved_summary{OUTPUT_SUFFIX}.json"
MIN_CALL_INTERVAL = float(os.getenv("ACAMIND_EVAL_MIN_CALL_INTERVAL", "4.2"))


def parse_questions(text: str) -> list[dict]:
    starts = list(re.finditer(r"(?m)^(\d+)\. (.+)$", text))
    rows = []
    for i, match in enumerate(starts):
        block = text[match.start(): starts[i + 1].start() if i + 1 < len(starts) else len(text)]
        qnum = int(match.group(1))
        source_ids = sorted(set(re.findall(r"`([0-9]{4}\.[0-9]{5}v[0-9]+)\.pdf`", block)))
        # Accept revised anchors such as "Đáp án chuẩn đã đối chiếu lại PDF";
        # otherwise a corrected question can silently lose its gold answer.
        anchor = re.search(r"\*\*Đáp án[^:]*:\*\*\s*(.*?)(?=\s*\*\*Nguồn|\n\s*\d+\.|\Z)", block, re.S)
        rows.append({"id": qnum, "question": match.group(2).strip(), "source_ids": source_ids,
                     "expected_answer": re.sub(r"\s+", " ", anchor.group(1)).strip() if anchor else "",
                     "is_refusal": qnum >= 96})
    return rows


def safe_json(path: Path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    temp.replace(path)


def main():
    questions = parse_questions(QUESTION_FILE.read_text(encoding="utf-8"))
    if len(questions) != 100 or [q["id"] for q in questions] != list(range(1, 101)):
        raise SystemExit(f"Approved question set parse failed: {len(questions)} questions")
    if sum(q["is_refusal"] for q in questions) != 5:
        raise SystemExit("Refusal set must contain exactly five questions (96-100).")
    empty_anchors = [q["id"] for q in questions if not q["expected_answer"]]
    if empty_anchors:
        raise SystemExit(f"Question set has missing expected-answer anchors: {empty_anchors}")
    raw_pdf_stems = {p.stem for p in (ROOT / "backend" / "data" / "raw_pdfs_500").glob("*.pdf")}
    missing_gold_pdfs = sorted({sid for q in questions for sid in q["source_ids"] if sid not in raw_pdf_stems})
    if missing_gold_pdfs:
        raise SystemExit(f"Question source PDFs are absent from the benchmark corpus: {missing_gold_pdfs}")
    errata_file = ROOT / "results" / "experiment_100_gold_errata.json"
    if errata_file.exists():
        corrections = {item["question_id"]: item for item in json.loads(errata_file.read_text(encoding="utf-8")).get("corrections", [])}
        for question in questions:
            if question["id"] in corrections and corrections[question["id"]].get("gold_answer"):
                question["corrected_expected_answer"] = corrections[question["id"]]["gold_answer"]

    # A rerun must use the same approved questions and PDFs. The historical
    # completed run lacks a code hash, but today's manifest freezes input data
    # for the post-fix cohort without touching answer keys during retrieval.
    manifest_file = ROOT / "results" / "experiment_100_repro_manifest_20261021.json"
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        if hashlib.sha256(QUESTION_FILE.read_bytes()).hexdigest() != manifest["question_sha256"]:
            raise SystemExit("Approved question file changed since the frozen manifest.")
        pdf_root = ROOT / "backend" / "data" / "raw_pdfs_500"
        current_pdf_names = {path.name for path in pdf_root.glob("*.pdf")}
        if current_pdf_names != set(manifest["pdfs"]):
            raise SystemExit("PDF corpus file list changed since the frozen manifest.")
        for filename, expected_hash in manifest["pdfs"].items():
            digest = hashlib.sha256((pdf_root / filename).read_bytes()).hexdigest()
            if digest != expected_hash:
                raise SystemExit(f"PDF corpus changed since the frozen manifest: {filename}")

    results = json.loads(OUT_JSON.read_text(encoding="utf-8")) if OUT_JSON.exists() else {
        "experiment": "approved_100_psychology_questions", "model": None, "started_at": datetime.now(timezone.utc).isoformat(),
        "source_question_file": QUESTION_FILE.name,
        "question_file_sha256": hashlib.sha256(QUESTION_FILE.read_bytes()).hexdigest(),
        "code_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
            BACKEND / "app/services/retriever.py", BACKEND / "app/services/generator.py",
            BACKEND / "app/services/cross_lingual.py", Path(__file__)]},
        "evaluation_status": "iterative_post_feedback_diagnostic_not_held_out",
        "rows": []}
    done = {r["id"] for r in results["rows"] if r.get("status") == "completed"}

    from app.db.postgres import SessionLocal
    from app.services import retriever, generator
    from app.services.llm_client import get_default_client
    client = get_default_client()
    # backend/.env is loaded with override=True, so an ordinary shell LLM_MODEL
    # setting is overwritten. A dedicated experiment override keeps .env and
    # application deployment untouched while fixing one model for this run.
    experiment_model = os.getenv("ACAMIND_EVAL_MODEL", "").strip()
    if experiment_model:
        client.model = experiment_model
    results["provider"] = client.provider
    results["model"] = client.model
    results["min_llm_call_interval_seconds"] = MIN_CALL_INTERVAL

    # Rate-limit every LLM call (query translation and answer generation); no paid fallback.
    original_complete = client.complete
    last_call = [0.0]
    call_stats = {"count": 0}
    def throttled_complete(*args, **kwargs):
        delay = MIN_CALL_INTERVAL - (time.monotonic() - last_call[0])
        if delay > 0:
            time.sleep(delay)
        last_call[0] = time.monotonic()
        call_stats["count"] += 1
        return original_complete(*args, **kwargs)
    client.complete = throttled_complete
    generator.llm_client = client

    try:
        for q in questions:
            if q["id"] in done:
                continue
            print(f"START {q['id']}/100", flush=True)
            started = time.time()
            row = {**q, "status": "running", "model": client.model,
                   "started_at": datetime.now(timezone.utc).isoformat(), "llm_calls_before": call_stats["count"]}
            try:
                with SessionLocal() as db:
                    chunks = retriever.retrieve(q["question"], None, db, top_k=12)
                    retrieval_seconds = round(time.time() - started, 2)
                    telemetry = chunks[0].get("_telemetry") if chunks else None
                    for chunk in chunks:
                        chunk.pop("_telemetry", None)
                    answer = generator.generate_answer(q["question"], chunks, lang="vi")
                    if not answer.strip():
                        raise RuntimeError("Configured LLM returned an empty answer; item must be retried")
                    generation_seconds = round(time.time() - started - retrieval_seconds, 2)
                retrieved = []
                for c in chunks:
                    retrieved.append({"filename": c.get("doc_filename") or c.get("filename") or c.get("doc_title"),
                                      "document_id": c.get("document_id"), "page": c.get("page_number"),
                                      "score": c.get("score"), "abstract_context_added": bool(c.get("abstract_context_added")),
                                      "content": (c.get("content") or "")[:1200],
                                      "parent_context": (c.get("parent_context") or "")[:2600]})
                retrieved_names = " ".join(str(x.get("filename") or "") for x in retrieved)
                citations = re.findall(r"\[([^\]\n]+\.pdf\s*[-–]\s*(?:Page|Trang)\s*\d+[^\]]*)\]", answer, re.I)
                row.update({"status": "completed", "answer": answer, "retrieved": retrieved,
                            "retrieved_target_source_ids": [sid for sid in q["source_ids"] if sid in retrieved_names],
                            "target_source_recall": (sum(sid in retrieved_names for sid in q["source_ids"]) / len(q["source_ids"])) if q["source_ids"] else None,
                            "citation_count": len(citations), "citation_labels": citations,
                            "refusal_marker_detected": "__NO_CONTEXT__" in answer,
                            "telemetry": telemetry,
                            "retrieval_seconds": retrieval_seconds,
                            "generation_seconds": generation_seconds,
                            "elapsed_seconds": round(time.time() - started, 2),
                            "llm_calls": call_stats["count"] - row["llm_calls_before"],
                            "completed_at": datetime.now(timezone.utc).isoformat()})
                old_index = next((i for i, old in enumerate(results["rows"]) if old.get("id") == row["id"]), None)
                if old_index is None:
                    results["rows"].append(row)
                else:
                    old = results["rows"][old_index]
                    row["attempt_history"] = old.get("attempt_history", []) + ([{"status": old.get("status"), "error": old.get("error")} ] if old.get("error") else [])
                    results["rows"][old_index] = row
                safe_json(OUT_JSON, results)
                print(f"DONE {q['id']}/100 | retrieved={len(chunks)} | target_hits={row['retrieved_target_source_ids']} | {row['elapsed_seconds']}s", flush=True)
            except Exception as e:
                message = str(e)
                code = getattr(getattr(e, "response", None), "status_code", None)
                status = ("api_quota_or_runtime_error" if code == 429 or "429" in message else
                          "api_unavailable" if code == 503 or "503" in message else
                          "empty_answer" if "empty answer" in message else "runtime_error")
                row.update({"status": status,
                            "error": message[:1000], "http_status": code,
                            "elapsed_seconds": round(time.time() - started, 2),
                            "completed_at": datetime.now(timezone.utc).isoformat()})
                old_index = next((i for i, old in enumerate(results["rows"]) if old.get("id") == row["id"]), None)
                if old_index is None:
                    results["rows"].append(row)
                else:
                    old = results["rows"][old_index]
                    row["attempt_history"] = old.get("attempt_history", []) + ([{"status": old.get("status"), "error": old.get("error")} ] if old.get("error") else [])
                    results["rows"][old_index] = row
                safe_json(OUT_JSON, results)
                print(f"STOP {q['id']}/100 | {row['status']} | {message[:250]}", flush=True)
                if row["status"] in {"api_quota_or_runtime_error", "api_unavailable", "empty_answer"}:
                    print("Checkpoint saved; rerun after the API is available.", flush=True)
                    break

    finally:
        client.complete = original_complete

    rows = results["rows"]
    completed = [r for r in rows if r.get("status") == "completed"]
    summary = {"experiment": results["experiment"], "provider": client.provider, "model": client.model,
               "min_llm_call_interval_seconds": MIN_CALL_INTERVAL,
               "completed_count": len(completed), "error_count": len([r for r in rows if r.get("status") != "completed"]),
               "approved_total": 100, "refusal_questions_completed": sum(r.get("status") == "completed" and r.get("is_refusal") for r in rows),
               "mean_latency_seconds": round(sum(r.get("elapsed_seconds", 0) for r in completed) / len(completed), 2) if completed else None,
               "note": "Automatic retrieval/citation/refusal indicators only; answer factual correctness requires independent human assessment.",
               "updated_at": datetime.now(timezone.utc).isoformat()}
    safe_json(OUT_SUMMARY, summary)
    fields = ["id", "status", "question", "source_ids", "retrieved_target_source_ids", "target_source_recall", "citation_count", "refusal_marker_detected", "elapsed_seconds", "error"]
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({**r, "source_ids": ";".join(r.get("source_ids", [])), "retrieved_target_source_ids": ";".join(r.get("retrieved_target_source_ids", []))})
    print(f"SUMMARY {json.dumps(summary, ensure_ascii=False)}", flush=True)
    print(f"RESULTS={OUT_JSON}", flush=True)


if __name__ == "__main__":
    main()
