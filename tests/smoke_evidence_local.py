"""Opt-in integration test using synthetic passages and loopback Ollama only."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services.evidence_policy import assess_evidence

targets = ['Study Alpha', 'Study Beta']
question = 'Compare the sample sizes of Study Alpha and Study Beta.'
chunks = [dict(id='a', document_id='a', doc_title='Study Alpha', doc_filename='alpha.pdf',
               page_number=2, sub_query_target=targets[0], content='Study Alpha enrolled 120 participants in a randomized trial.'),
          dict(id='b', document_id='b', doc_title='Study Beta', doc_filename='beta.pdf',
               page_number=3, sub_query_target=targets[1], content='Study Beta enrolled 80 participants in a randomized trial.')]
results = []
for expected, passages in [('answer', chunks), ('partial', chunks[:1]), ('answer', chunks)]:
    result = assess_evidence(question, targets, passages)
    results.append({k: result.get(k) for k in ['action', 'supported_cells', 'total_cells', 'verification_ms', 'cache_hit']})
    assert result['action'] == expected, json.dumps(result)
assert results[-1]['cache_hit']
print(json.dumps(results))
