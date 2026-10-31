# Local verification results

## Running services

- Acamind frontend: http://localhost:3001
- Acamind backend: http://127.0.0.1:8001
- Port 8000 was occupied by another project and was left untouched.
- Runtime processes were started for this verification, not installed as services.

## Verified

- 228 automated tests passed (all `test_*.py` except the live PDF highlight suite).
- TypeScript: `npx tsc --noEmit --incremental false` passed.
- Real local PostgreSQL: new processing and review tables available.
- Dedicated synthetic test account: login API and browser login succeeded.
- Two generated PDFs with the same filename but different bytes retained separate document IDs.
- Identical PDF bytes under another filename reused the existing document ID.
- Cancellation request persisted; worker reached `cancelled`, not `ready`.
- Retry reused the stored PDF and document ID; both PDFs reached `ready` using actual embeddings.
- Study profiles returned original-source candidates.
- Confirmed review persisted; history returned it; a stale revision was rejected with HTTP 409.
- Similar-title PDFs were returned as possible version candidates.
- Targeted retrieval returned source passages and ranking-explanation objects.
- Actual local-model comparability and relations endpoints returned `conditions_differ`.
  This verifies execution and conservative gating, not scientific judgment accuracy.

## Unresolved / not verified

- Retrieved smoke-test passages had `score_source=unavailable`. Successful retrieval
  does not establish that Cross-Encoder reranking worked. Direct model diagnostics
  were not executed because automatic approval review failed on a usage limit.
- Browser verification reached successful login. Subsequent browser access failed
  with `browser.user is unavailable`; matrix editing, PDF highlighting, duplicate
  selection, and processing controls have not been verified by browser interaction.
- The PDF highlight suite, chat generation/streaming, translation, terminology,
  slides, exports, contradiction radar, claim verification, neuro graph, OSCE,
  account/organization/payment/admin workflows, load testing and production build
  were not exercised end to end in this run.
- No independent scientific accuracy benchmark was performed.

## Reproduction

`backend/scripts/local_feature_smoke.py` performs the local API integration path.
It creates a labelled test account and two synthetic PDFs each time it runs.
It retains those records for inspection. The temporary file
`acamind-local-smoke.json` in the execution account's temp directory holds that
test account's session state; it is not part of the repository.

The script checks retrieval availability separately from model score provenance;
its retrieval PASS line must not be interpreted as Cross-Encoder validation.
