"""Opt-in local verifier probe for comparing Ollama models on fixed passages."""
import argparse
import json
from pathlib import Path
import sys
import time

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.core.config import settings
from app.services import evidence_policy as policy
from app.services.evidence_policy import (
    _local_complete, evidence_packet, requested_facets, validate_matrix,
    verification_output_budget,
)

parser = argparse.ArgumentParser()
parser.add_argument("model")
args = parser.parse_args()
settings.EVIDENCE_LOCAL_MODEL = args.model

targets = ["Study Alpha", "Study Beta"]
question = "Compare the sample sizes of Study Alpha and Study Beta."
chunks = [
    {"document_id": "a", "doc_title": "Study Alpha", "doc_filename": "alpha.pdf",
     "page_number": 2, "sub_query_target": targets[0],
     "content": "Study Alpha enrolled 120 participants in a randomized trial."},
    {"document_id": "b", "doc_title": "Study Beta", "doc_filename": "beta.pdf",
     "page_number": 3, "sub_query_target": targets[1],
     "content": "Study Beta enrolled 80 participants in a randomized trial."},
]
facets = requested_facets(question, True)
packet = evidence_packet(targets, chunks)
payload = {"question": question, "targets": targets, "facets": facets, "passages": packet}
start = time.perf_counter()
try:
    raw = _local_complete(payload, num_predict=verification_output_budget(targets, facets))
except httpx.HTTPStatusError as exc:
    print(json.dumps({"model": args.model, "status": exc.response.status_code,
                      "error": exc.response.text[:1000]}, ensure_ascii=True))
    raise SystemExit(1)
matrix = validate_matrix(raw, targets, facets, packet)
print(json.dumps({"model": args.model, "elapsed_ms": round((time.perf_counter() - start) * 1000, 1),
                  "action": matrix["action"], "supported_cells": matrix["supported_cells"],
                  "total_cells": matrix["total_cells"], "raw": raw}, ensure_ascii=True))

original_complete = policy._local_complete
def diagnostic_complete(payload, **kwargs):
    try:
        return original_complete(payload, **kwargs)
    except httpx.HTTPStatusError as exc:
        print(json.dumps({"model": args.model, "status": exc.response.status_code,
                          "error": exc.response.text[:1000]}, ensure_ascii=True))
        raise

policy._local_complete = diagnostic_complete
for label, passages in [("full", chunks), ("partial", chunks[:1])]:
    result = policy.assess_evidence(question, targets, passages)
    print(json.dumps({"case": label, "action": result["action"],
                      "supported_cells": result.get("supported_cells"),
                      "total_cells": result.get("total_cells"),
                      "verification_ms": result.get("verification_ms")}, ensure_ascii=True))
