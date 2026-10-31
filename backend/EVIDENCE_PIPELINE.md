# Evidence-aware retrieval

## Lexical retrieval terminology

The default lexical branch is PostgreSQL Full-Text Search using `ts_rank_cd`
with a GIN index. This is not Okapi BM25. Setting `USE_FTS=0` selects the
in-memory `rank_bm25.BM25Okapi` implementation. An exception that reaches the
lexical router may also trigger that fallback; empty FTS results alone do not.
Some FTS helpers handle their own errors and return no results instead.

The internal `_bm25_task`, `_bm25_search`, and `_bm25_via_fts` names are retained
for caller compatibility, not as descriptions of the active scoring algorithm.
Benchmark reports must record the configuration and any fallback events; do not
describe a run as BM25 merely because it calls one of these legacy functions.

## Pipeline

Multi-criterion questions now batch the original query and separate criterion
queries (sample, method, measure, finding, limitation). Criteria share the bounded
candidate pool and model cache. Within each study, unique passages are selected
round-robin by criterion before the existing cross-study allocation. Original
query scores stay unchanged; `facet_scores` and `facet_selection` describe only
retrieval relevance, not verified support. Failed scoring preserves base order
with null criterion scores. Single-criterion queries keep the existing path.
When context slots are fewer than requested study/criterion combinations, full
coverage is not guaranteed. This step does not retrieve new candidates for each
criterion; targeted repair remains the evidence verifier's responsibility.

Rerank caches are scoped to the scorer/model instance, model name, backend,
available model revision, scoring schema and token limit. Replacing a model
invalidates reuse. LLM fallback rankings are not cached as cross-encoder results.
For in-place changes to model weights or tokenizer state, recreate the wrapper
or restart the process; cache identity does not hash all weight tensors.

Implemented in indexed-document chat. URL/file-only analysis retains its existing
pipeline. Existing DCSR scores remain routing heuristics, not answer probabilities.

- Comparison targets (maximum six) retrieve concurrently on a separate three-worker
  executor. Each target owns a DB session; vector/FTS workers retain their own
  sessions. Exact catalog title resolution respects the requested document IDs.
- Cross-encoder pairs from all targets are scored in one batch, then interleaved
  with per-target quotas. Model failure means unavailable scores, not negative
  evidence. The CrossEncoder fallback now explicitly uses sigmoid normalization.
- Short, single-focus questions may reduce context from 12 to 6 only with a strong
  scored leader (0.75 score and 0.20 margin). These are conservative routing
  defaults, not calibrated thresholds; evaluate them before claiming gains.
- Comparisons and uncertain single-focus retrieval run a local evidence assessment.
  The assessor returns one cell per target/criterion, with a contiguous quote.
  Code checks source ID, target identity, document/page presence and quote membership
  in the original chunk (not a multi-page parent). Semantic support is still a model
  judgment. This is not an independent NLI certificate.
- Verifier output tokens scale with the required target-by-facet matrix (512–3,000
  tokens). All retrieved excerpts and required cells remain unchanged; only unused
  generation allowance is reduced. Numeric logs expose verifier input size, work
  counts and latency without recording passage text.
- Missing cells trigger at most one repair round for at most two targets, then one
  reassessment. Partial support produces a partial answer. Zero support produces a
  bounded refusal. An unavailable verifier returns 503, not a false absence claim.
- Verification uses only Ollama on loopback, ignores HTTP proxy variables, rejects
  redirects and remote hosts, and has no external fallback. Configure
  `EVIDENCE_LOCAL_MODEL` (default `qwen2.5:7b`) and local `OLLAMA_BASE_URL`.
- A five-minute, 128-entry in-memory cache includes model, question, document IDs,
  pages and content. Changing source text invalidates the result. Nothing is written
  to a shared evidence store. Logs record outcome/counts/timing, not passage text.
- The chat evidence table shows model-assessed cells and original citation links.
  The full matrix guides generation; excerpts in HTTP telemetry are shortened.

## Validation

From repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m unittest discover -s tests -p test_evidence_pipeline.py -v
```

From frontend: `npx tsc --noEmit --incremental false`.

For a real evaluation, label answerable, partially answerable and unanswerable
questions independently of retrieval. Include incorrect study identities, mixed
languages, omitted results, conflicting outcomes, different metrics/time points and
reranker/verifier failures. Split by study (including versions/duplicates), not only
by question. Keep a separate calibration split and untouched test split.

Measure p50/p95 total latency and time to first token; retrieval, rerank,
verification and generation timings separately; wrong-answer rate among answered
questions; false-refusal rate among answerable questions; per-study/facet coverage;
citation correctness and comparability judgments. Report cold/warm cache separately.
Local verification adds latency on cache misses; faster retrieval does not guarantee
faster end-to-end answers. No accuracy or speedup percentage has been established.

No trained answerability model or statistical risk guarantee is shipped: it requires
human-labeled calibration data. Ingestion-time structured study extraction, DOI
resolution and automatic quantitative effect conversion are follow-up work.

## Scientific integrity corrections (2026-10-27)

- Authority bonuses are zero until a real appraisal workflow exists. Metadata or
  mentions of WHO, APA, RCT, journals or degrees cannot certify evidence tiers.
  CEBM and recommendation grades return `unverified`, with zero rating stars.
- PICO uses source-specific candidate excerpts, never the generated answer or
  default patient/treatment/outcome templates. Structured study fields are
  heuristic candidates; parent-context pages are not assigned to a chunk page.
- Legacy consensus/radar routes return null percentages and no invented conflicts,
  dominant study or causal verdict. Research-gap templates have been removed;
  missing retrieved text does not demonstrate a gap in the literature.
- Post-generation similarity search returns candidate passages with UNVERIFIED
  status and null entailment/faithfulness scores. A citation without a retrieved
  passage cannot serve as its own evidence. This is separate from the local
  pre-generation evidence-matrix verifier described above, which remains active.
- Meta-analysis accepts reviewed `meta_analysis_input` records only. Each record
  needs finite `hedges_g`, positive finite `variance`, integer `sample_n > 1`,
  `reviewed: true`, a nonempty `reviewer`, `independent_study_id`, `analysis_group`,
  and `source` with matching document_id, positive page and quote. At least two
  independent records must share a reviewed population/outcome/timepoint/contrast/
  direction group. The contract validates fields, not the truth of human review.
  Current UI extraction does not populate this contract: its forest plot reports
  insufficient data until a reviewed-data workflow is implemented.
- DL weights and pooling use unrounded numbers; normal-approximation p-values are
  computed with erfc. I-squared is not artificially capped at 96%. Forest axes
  include negative effects and all confidence intervals. No inference from total
  N to an equal-arm variance, automatic d conversion, or fixed nonsignificant p.
- Bibliographic exports omit absent metadata and mark missing year n.d.; no fake
  authors, journals, publishers or years. APA output is a draft, not a metadata
  validation or complete style-conformance certificate.
- Rerank rejects malformed/nonfinite/out-of-range model scores without caching;
  LLM fallback deduplicates indices and preserves remaining candidates as unscored.
  Diversity quotas do not silently relax per-document limits.

Remaining research work: independent annotated evaluation, calibrated relevance
thresholds, validated claim-level entailment/contradiction with comparability,
reviewed structured study ingestion and an appraisal UI. Unit tests cannot supply
accuracy, novelty, clinical validity or statistical risk guarantees. Health/OSCE
and neuro-anatomy teaching templates are outside this retrieval/scientific-synthesis
repair and have not been clinically validated by these tests.

## Evaluation integrity

The single-query ablation page reports observed keyword coverage using exactly
one formula for all architectures and retrieval-stage wall time. Keyword coverage
is not recall. Citation precision, semantic correctness, faithfulness and overall
accuracy remain null without independent judgments. All variants use top_k=5.
Sequential runs/cache state still prevent a controlled latency comparison.

The old statistical suite generated architecture-specific score floors, derived
baseline faithfulness from Acamind and fabricated a no-DCSR Pareto point. That
implementation has been removed. The endpoint returns 422 explaining that a
labeled dataset and genuine paired runs are required; it cannot export artificial
p-values or significance stars. Evaluation request document IDs are validated as
UUIDs before any legacy SQL string construction.

## Long-passage reranking

Bundled FlagEmbedding/CrossEncoder tokenizers now split long formatted passages
into overlapping windows within RERANK_MAX_LENGTH, including query and special
tokens. Exact character slices preserve passage text. Each pair is length-checked
again after slicing. The maximum window score ranks the original chunk; this is
an uncalibrated relevance aggregation, not answer confidence. Long documents may
benefit from more scoring opportunities; accuracy gains have not been established.

RERANK_WINDOW_OVERLAP defaults to 64 tokens (capped at one quarter of the actual
window); RERANK_MAX_WINDOWS defaults to 32 per passage (configurable 1–128).
Queries leaving insufficient passage space, unusable offsets or passages exceeding
that budget fail scoring and use the existing explicitly unscored fallback.
Inference batches contain at most 16 windows, shared across input pairs. Original
chunk content, document ID and page remain unchanged. Window offsets refer to the
formatted scoring passage, not PDF coordinates. Custom backends without a tokenizer
retain their previous scoring path; window coverage is not guaranteed for them.
The scoring schema and cache namespace include window settings. Changed aggregation
requires fresh relevance-threshold calibration before any accuracy claims.

## Claim ownership hints

Original chunk sentences now carry exact character offsets, quoted text and one
of current_study_candidate, cited_study_candidate, or unclear. Explicit first-person
/current-study language and external-attribution language provide lexical hints.
Mixed sources, quoted first-person claims, questions, qualified ownership, bare
citations, section headings and statistics do not certify original findings.
All classifications remain unverified. These hints reach generation and the local
evidence verifier; the verifier must still check study identity and the subject.
No statement is promoted to verified evidence or removed solely by these rules.
Parent context is not used to assign a source/page to ownership spans. This is a
conservative bilingual rule-based aid, not a trained authorship-resolution model;
implicit attribution and complex clauses can remain unclear or be misclassified.

## Study profiles

Literature matrix rows now offer an on-demand study profile with seven fields:
objective, method, sample, data, measure, finding and limitation. The authenticated
GET /features/study-profile/{UUID} endpoint enforces the existing document-read
policy before loading original chunks belonging to that document. It scans at most
2,000 chunks / 2,000,000 characters and reports truncation explicitly. Profiles are
computed fresh, with up to three deduplicated source candidates per field, original
chunk-relative offsets and page numbers. The UI opens the existing PDF verifier at
the candidate's source page and supports rebuilding the profile after data changes.

Fields and ownership are unverified lexical candidates, not complete semantic
extraction. Missing fields mean no matching candidate in scanned indexed text;
this does not assert absence in the complete PDF. Invalid source pages are excluded.
No profile is persisted or automatically approved for quantitative pooling.

## Pairwise comparability

Literature now offers a two-study conditions check for selected documents. The
POST /features/study-comparability endpoint enforces both document read policies,
then sends a bounded, source-linked profile subset only to loopback Ollama (no
proxy or remote fallback). The six dimensions are population, outcome, measurement
and units, time point, intervention/comparator, and effect coding direction.

Matched/different judgments require literal quotes from BOTH distinct documents.
Invalid, duplicated or missing criterion evidence becomes unknown. All six matched
criteria yield model-assessed comparable; any evidenced difference yields conditions
_differ; otherwise the result is insufficient_data. These are semantic judgments
of a local model, not independently verified equivalence or authorization to pool.
Model/network failures return 503, never false incompatibility. The UI shows each
criterion, explanations, both source quotes and links to their PDF pages. Changing
the selected pair or focus hides the old result. New profile fields for time point,
comparator and effect coding support this check. Accuracy on real studies remains
unmeasured; provenance checks cannot establish the truth of model reasoning.

## Source-linked agreement and contradiction

The Literature pair panel now offers a findings comparison for an explicit focus.
POST /features/study-relations checks both document permissions and runs the six
comparability criteria before requesting claim-level relations from loopback
Ollama. Unknown or different conditions stop the relation stage. Each accepted
agreement/contradiction needs both complete source passages, distinct document IDs,
explicit model flags for matching outcome/timepoint/contrast/coding, and an
explanation. Conflicting labels on the same source pair are discarded. Empty output
means no supported relation was established, not universal agreement or no conflict.

Profile passage selection now preserves complete quotes (up to 12 passages and
8,000 characters per study), avoiding truncation of trailing qualifiers. Relation
labels remain model judgments; literal-source and schema checks cannot establish
semantic truth. No consensus percentages, automatic meta-analysis, causal diagnosis
or study superiority are inferred. API failures return 503. The UI shows sources
side by side and opens the existing PDF verifier. Changes to pair or focus hide
previous results. Real-model accuracy and browser interaction remain to be tested.
# Targeted missing-cell retrieval

The evidence matrix offers an on-demand search for each missing criterion in one
authorized document, with optional topic text. It uses the existing hybrid
retrieval/reranking pipeline and returns at most five suggestions. Retrieved IDs
are reloaded from document-scoped original chunks; synthetic IDs are excluded.
Suggestions retain complete chunk text and page links, remain unverified, and do
not overwrite the extracted profile or establish that a criterion is satisfied.
An empty search is not proof of absence. Request failures remain distinct from
empty results. The UI permits one search at a time, retry, and cancellation of
client waiting (server computation may continue). Live retrieval quality and
browser interactions have not been evaluated by the mocked unit tests.

