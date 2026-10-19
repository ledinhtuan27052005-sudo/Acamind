# Stage 0: Explicit Protocol Assumptions (`assumptions.md`)

In accordance with Inviolable Principle 9 (*"Nếu một yêu cầu không thực hiện được từ mã nguồn hiện có, nói rõ thay vì đoán. Chỉ hỏi tôi khi thật sự bị chặn; ngược lại tự đưa ra giả định hợp lý và ghi vào assumptions.md"*), we record the following explicit, verifiable assumptions:

## 1. Database Selection (`Port 5433` vs `Port 5432`)
- **Context:** The host machine runs two PostgreSQL 16 instances:
  - `localhost:5432/rag_db` (Windows local service): contains only `2,994` chunks for the 499 arXiv PDFs (`~4.2%` of the corpus, capped at 6 chunks/doc by `run_500_pdf_1000_benchmark.py`).
  - `localhost:5433/rag_db` (Docker container `insight-pgvector`, configured in `docker/docker-compose.yml` and populated by `backend/scripts/ingest_all_500_pdfs.py`): contains all `499` arXiv PDFs (`12,411` pages) segmented into **`70,825` chunks**, 100% embedded with `intfloat/multilingual-e5-base` (unit L2 norm = `1.0`, `0` NULL/NaN).
- **Assumption A-01:** All experiments in Stages 1–11 execute against **`localhost:5433/rag_db`** filtered to the 499 arXiv benchmark documents (`d.filename LIKE '26%.pdf'`, `499` docs, `12,411` pages, `70,825` chunks), excluding the 5 extra non-arXiv PDFs (`234` chunks) so the benchmark corpus strictly matches the 499-paper arXiv collection (`12,411` pages). Note that `70,825` chunks differs from the manuscript's reported `70,794` chunks by `+31` chunks (`+0.044%`), which is documented in `results/01_embedding/stats.json`.

## 2. Corpus-Wide Retrieval (Removing Oracle `WHERE document_id IN ...` Filter)
- **Context:** In `run_50_real_questions_benchmark.py` (L261, L274), SQL queries restricted search to `WHERE c.document_id IN target_ids` (passing the ground-truth document UUIDs into the query filter).
- **Assumption A-02:** In all new retrieval and generation experiments (Stages 3–10), **no oracle `document_id` filter** is passed to any system. Every query searches across the entire 499-document corpus (`70,825` chunks).

## 3. Ground Truth on the 50 Test Queries (`REAL_Q_01`–`REAL_Q_50`)
- **Context:**
  - Document-level ground truth (`gt_doc_ids`) is 100% deterministic for all 50 test queries (`matched_50_queries_by_title.json`), because `REAL_Q_01`–`REAL_Q_45` explicitly quote the exact paper title(s) (1 paper for Factual Q&A, 2 for Cross-Article, 3 for Literature Synthesis), and `REAL_Q_46`–`REAL_Q_50` are out-of-domain (`gt_doc_ids = []`).
  - However, human-annotated page-level ground truth (`gt_pages`) was never created for `REAL_Q_01`–`REAL_Q_45` (because the template questions ask broadly about *"Mục tiêu nghiên cứu, giả thuyết khoa học và phương pháp luận chính"* across the whole paper).
- **Assumption A-03:**
  - We preserve `test_50.json` (`REAL_Q_01`–`REAL_Q_50`) completely unmodified (Principle 3).
  - Alongside `results/02_split/dev_candidates.xlsx`, we also export `results/02_split/test_50_candidate_pages.xlsx` containing candidate pages (`page 1`..`3` where Abstract, Introduction, and Methodology appear, plus exact text snippets) so that at the Stage 2 human checkpoint, the user can confirm/adjust `gt_pages` for `test_50.json` if page-level Recall@10/MRR@10/NDCG@10 on `test_50` is desired in addition to document-level Recall@10/MRR@10/NDCG@10.

## 4. Sparse Lexical Retrieval Standardization
- **Context:** `retriever.py::_bm25_via_fts` uses `page_texts.tsv` (`to_tsvector('simple', content)`), while `run_50_real_questions_benchmark.py` used `to_tsvector('english', c.content)` on `chunks`.
- **Assumption A-04:** We build GIN indexes on **both** `chunks` (`idx_chunks_content_english_gin` on `to_tsvector('english', content)`) and `page_texts` (`idx_page_texts_tsv` on `tsv`), and in Stage 3b / Stage 6 we measure and report chunk-level GIN FTS (`ts_rank_cd`) directly on the `70,825` chunks so that Dense and Sparse operate at the exact same chunk granularity (`70,825` chunks).

## 5. CPU Inference Iteration Count in Stage 3a (`BAAI/bge-reranker-v2-m3`)
- **Context:** Stage 3a specifies measuring `BAAI/bge-reranker-v2-m3` (`568M` parameters, 24-layer XLM-RoBERTa-Large Cross-Encoder, FP32 on CPU) across $K \in \{10, 20, 30, 40, 50\}$ to test the manuscript's claim of `185 ms` for 50 candidates. On `AMD Ryzen 5 8645HS` CPU (FP32), a single forward pass takes `~13.3 s` at $K=10$ (`N=50` cold queries measured in Stage 3b) and `~65–150 s` at $K=50$ (**`350x–800x` slower than `185 ms`**). Running 100 repetitions across $K \in \{10, 20, 30, 40, 50\}$ for two token-length regimes would require >12 hours of continuous CPU compute.
- **Assumption A-05:** Because deterministic CPU transformer forward passes on fixed-length inputs have very low run-to-run variance ($\text{CV} < 5\%$), Stage 3a reports the full $N=50$ cold-query latency distribution at $K=10$ alongside $N=3..5$ repeated runs at each $K \in \{10, 20, 30, 40, 50\}$ for both production chunks (`~185` tokens) and `~512`-token passages, checkpointing after every $K$.

## 6. Disjunctive Bilingual/English FTS for Mixed Vietnamese-English Queries
- **Context:** As documented in `ISSUE-GT-05`, `plainto_tsquery('english', query)` joins all tokens with `&` (AND), which yields `0` hits whenever a query mixes Vietnamese question words with English terminology against an English corpus.
- **Assumption A-06:** In Stage 3e and Stages 4–7, we evaluate and report both the literal `plainto_tsquery` behavior and a disjunctive (`|`, boolean OR) English/bilingual `to_tsquery('english', ...)` constructed from `get_cross_lingual_query_bundle(query)` + ASCII technical terms so that Sparse GIN FTS genuinely retrieves matching English chunks.
