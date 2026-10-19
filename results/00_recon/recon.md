# Stage 0: Codebase Reconnaissance Report (`recon.md`)

## Metadata & Environment Snapshot
- **Timestamp:** `2026-10-16T00:15:00+07:00`
- **Git Commit:** `f188a03afec1e3d0840dbb00f9d32fb4cb022e9c` (32 modified/untracked working tree files)
- **OS & Hardware:** Windows 11 (`Windows-11-10.0.26200-SP0`), AMD 6-Core / 12-Thread Processor (`AMD64 Family 25 Model 117 Stepping 2, AuthenticAMD`), `15.31 GB` physical RAM (16 GB nominal). *(Note: Paper Section 4.1 inaccurately described the machine as "Intel Core i7, 32GB RAM DDR5".)*
- **Python & Core Packages:**
  - Python: `3.14.7` (`backend/.venv/Scripts/python.exe`)
  - PyTorch: `2.14.1+cpu` (`CUDA available: False`)
  - `sentence-transformers`: `6.1.0` (`intfloat/multilingual-e5-base`, 768-d)
  - `FlagEmbedding`: installed (`BAAI/bge-reranker-v2-m3`)
  - `rank_bm25`: installed (`BM25Okapi`)
  - `PyMuPDF` (`fitz`): `1.28.2`
- **PostgreSQL & pgvector Instances on Host:**
  - **Port 5433 (`localhost:5433/rag_db`, Docker container `insight-pgvector`):** `PostgreSQL 16.15 (Debian 16.15-1.pgdg12+2)` with `pgvector 0.8.7`. Contains **504 documents** (`499` arXiv PDFs matching `26%.pdf` with `12,411` pages and **`70,825` chunks**, 100% embedded + `5` extra documents with `39` pages and `234` chunks = **`71,059` total chunks**, 100% embedded).
  - **Port 5432 (`localhost:5432/rag_db`, Windows local service `postgresql-x64-16`):** `PostgreSQL 16.15 (Visual C++ build 1944)`. Contains `551` documents (`499` in category `arxiv_benchmark_500` with **`2,994` chunks** — i.e., 6 chunks/doc from `run_500_pdf_1000_benchmark.py` — plus `52` other documents with `6,767` chunks = `9,761` total chunks).

---

## (a) Source Code Architecture Map

| Pipeline Stage | Production Implementation (File & Function) | Benchmark Script Implementation (`run_50_real_questions_benchmark.py`) |
| :--- | :--- | :--- |
| **1. PDF Ingestion & Scan Circuit Breaker** | `backend/app/services/parser.py::parse_pdf` (L217–325), `backend/app/services/file_parser.py::_parse_pdf` (L128–244), `backend/app/api/v1/document.py::_run_pipeline` (L91–215), and batch script `backend/scripts/ingest_all_500_pdfs.py` (L100–272). Computes `char_density = total_chars / total_pages`; if `< 50` chars/page (`_MIN_CHAR_DENSITY = 50`), sets `is_scanned = True`. | In `run_50_real_questions_benchmark.py` (L117–148): extracted only up to the first 10 pages per PDF and selected at most 20 chunks per PDF into port 5432; in `run_500_pdf_1000_benchmark.py` (L114–124): extracted only first 6 pages and capped at 6 chunks/doc (`2,994` chunks). By contrast, `ingest_all_500_pdfs.py` ingested all `12,411` pages (`70,825` chunks) into port 5433. |
| **2. Text Chunking (L1 / L2)** | `backend/app/services/chunking.py::chunk_text` (L75–183): uses `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200, length_function=len)` (character-based, ~150–200 words/chunk), prepending `[Document: title \| Section: section_title]` to `content`. L1 document summary is built in `backend/app/services/memory_builder.py::build_document_memory`. | `run_50_real_questions_benchmark.py` called `chunk_text()`, whereas `run_500_pdf_1000_benchmark.py` (L151) truncated `sc["content"][:600]`. |
| **3. Dense Embedding** | `backend/app/services/embedder.py`: loads `intfloat/multilingual-e5-base` (768-d), applies `DOC_PREFIX = "passage: "` in `embed_texts()` (L76–101, `batch_size=64`, `normalize_embeddings=True`) and `QUERY_PREFIX = "query: "` in `embed_query()` (L104–129, with MD5 cache `_query_embed_cache`, max 256). | Calls `_get_model().encode(QUERY_PREFIX + q, normalize_embeddings=True)` directly without `_query_embed_cache`. |
| **4. HNSW Vector Search** | `backend/app/services/retriever.py::_vector_search_task` (L151–204): opens a new `SessionLocal()`, runs `SET LOCAL hnsw.ef_search = 100`, and executes `SELECT ... (1 - (c.embedding <=> :vec::vector)) AS score FROM chunks c JOIN documents d ... ORDER BY c.embedding <=> :vec::vector LIMIT :lim` (`candidate_k = min(max(top_k * 8, 40), 60)` = 40). | `run_50_real_questions_benchmark.py` (L259–266): ran `SELECT ... FROM chunks c JOIN documents d ... WHERE c.document_id IN %s ORDER BY c.embedding <=> %s::vector LIMIT 6` — **oracle-filtered to `target_ids` (`WHERE c.document_id IN target_ids`)** instead of searching the 499-doc corpus! |
| **5. Sparse Lexical (GIN / BM25) Search** | `backend/app/services/retriever.py::_bm25_task` (L206–215) $\to$ `_bm25_via_fts` (L50–96): queries `page_texts.tsv` (GIN index on `to_tsvector('simple', content)`) using `ts_rank_cd(tsv, to_tsquery('simple', :q))`, then joins `chunks` on `(document_id, page_number)`. Falls back to `_bm25_in_memory` (`rank_bm25.BM25Okapi` on `LIMIT 500` arbitrary chunks) if FTS returns 0 hits. | `run_50_real_questions_benchmark.py` (L271–279): ran `ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s))` directly on `chunks` table **with `WHERE c.document_id IN target_ids`** (oracle document filter, sequential, not parallel). |
| **6. RRF Fusion** | `backend/app/services/retriever.py::_compute_rrf` (L99–148): fuses `dense_results` and `bm25_results` using `1.0 / (k + rank + 1)` with `_RRF_K = 60` (`0`-indexed `rank`, so top-1 has `1/(60+1)`). Also adds a heuristic bonus `+0.008` if query words overlap with `section_title`. | `run_50_real_questions_benchmark.py` (L283–291): computed `1.0 / (60 + r + 1)` in Python over the 6 dense + 6 sparse oracle-filtered chunks. |
| **7. DCSR (Dynamic Confident-Skip Reranking)** | `backend/app/services/retriever.py` (L254–262): checks only `ratio = top_rrf[0]["rrf_score"] / max(top_rrf[1]["rrf_score"], 1e-6) >= 2.5` (`_RRF_CONFIDENT_RATIO = 2.5`). Does **not** compute `Conf(q, C)` (Eq. 7). | `run_50_real_questions_benchmark.py` (L294–300): computed `s1 / max(0.01, s2)` on **Dense cosine scores** (not RRF!), and hardcoded `dcsr_skipped = (delta_rrf >= 1.30 or q_item["type"] == "Literature Synthesis")`. Then **hardcoded retrieval latency**: `t_acamind_ret_ms = max(t_dense, t_bm25) + t_fusion + (0.08 if dcsr_skipped else 185.0)` without ever calling the reranker! |
| **8. Cross-Encoder Reranker** | `backend/app/services/reranker.py::rerank` (L98–187): uses `BAAI/bge-reranker-v2-m3` (`FlagReranker` or `CrossEncoder`, `batch_size=16`), normalizes scores via sigmoid `1/(1+exp(-s))`, caches in `_rerank_cache` (max 256). | **Never called** in `run_50_real_questions_benchmark.py` or `run_500_pdf_1000_benchmark.py` (replaced by constant `185.0` ms or `random.uniform(170.0, 240.0)` ms). |
| **9. CRAG Refusal Gate** | `backend/app/services/retriever.py::evaluate_retrieval_confidence` (L331–368): computes `min(1.0, (top_rrf * 15.0) * 0.5 + overlap_ratio * 0.5)` against `_CRAG_MIN_CONFIDENCE = 0.25`. **Dead code: never imported or called anywhere in `chat.py`, `retriever.py`, or any script.** | In `run_50_real_questions_benchmark.py` (L303): used ground-truth label `is_ooc` (`acamind_chunks if not is_ooc else []`) to pass empty context `[]` to Acamind while passing non-empty chunks to Naive Dense and BM25. |
| **10. LLM Generation** | `backend/app/services/generator.py::generate_answer` / `generate_stream` $\to$ `backend/app/services/llm_client.py::LLMClient` calling `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions` (`gemini-2.5-flash-lite`, `temperature=0.2`). | `run_50_real_questions_benchmark.py::call_gemini_safe` (L51–91): called `gemini-2.5-flash-lite` via REST API (`temperature=0.1`, `maxOutputTokens=650`). Only called LLM for Naive Dense and BM25 on **8 out of 50** queries (`comparative_indices = {0, 4, 8, 20, 22, 35, 37, 45}`). |
| **11. Evaluation Metrics (Faithfulness & Citation Accuracy)** | Not part of runtime backend; implemented in `run_50_real_questions_benchmark.py::verify_grounding_and_citations` (L93–115). | `verify_grounding_and_citations`: parses `[filename - Trang X]`, checks if `(filename, page)` is in the **retrieved `chunks` passed to the LLM** (Citation-in-Context, NOT ground truth!), and computes `faith = min(0.98, 0.60 + overlap * 0.25 + cite_acc * 0.15)` (with a hardcoded floor of `0.60`, disagreeing with Eq. 11 in the paper!). |

---

## (b) How Is BM25 Actually Implemented?
1. **In Production (`backend/app/services/retriever.py`):**
   - Primary path (`_bm25_via_fts`, L50–96): Uses **PostgreSQL native Full-Text Search** `ts_rank_cd(tsv, to_tsquery('simple', :q))` over table `page_texts` (indexed by GIN index `idx_page_texts_tsv` on `to_tsvector('simple', content)`), then maps matching pages back to rows in `chunks`.
   - Fallback path (`_bm25_in_memory`, L218–252): Only triggered if FTS returns `0` rows. Loads an arbitrary `LIMIT 500` rows from `chunks` into Python and runs `rank_bm25.BM25Okapi(tokenized)` (default $k_1=1.5, b=0.75$).
2. **In Benchmark Scripts (`run_50_real_questions_benchmark.py` L272, `run_500_pdf_1000_benchmark.py` L336):**
   - Uses PostgreSQL `ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s))` directly on `chunks.content`.
3. **Are $k_1 = 1.2, b = 0.75$ (Eq. 5 in the paper) implemented anywhere?**
   - **NO.** PostgreSQL's `ts_rank_cd` computes cover-density ranking (not Okapi BM25 and has no $k_1, b$ parameters). No BM25 extension (`pg_search` / `ParadeDB`) is installed in PostgreSQL.

---

## (c) What Is the "Vision OCR" Engine in Table 2?
- Implemented in `backend/app/services/parser.py::ocr_page_image` (L39–111) and `backend/app/services/file_parser.py::_image_to_text` (L88–125).
- It renders the PDF page to a PNG image at 150 DPI using PyMuPDF (`page.get_pixmap(dpi=150)`) and sends the base64-encoded PNG to an **external commercial cloud API** (`client.complete_image` $\to$ Google Gemini Multimodal API `gemini-2.5-flash-lite` / OpenAI Vision API), caching responses by image SHA-256 in `data/ocr_cache.json`.
- It is **not** an on-premise/local OCR engine (no Tesseract, PaddleOCR, or EasyOCR is used), which directly contradicts Table 8's claim of *"100% On-premise Database (Zero raw literature leakage)"* whenever OCR fallback is triggered.

---

## (d) Refusal Queries, LLM Invocation, and Active Caches
1. **Does the current code call the LLM on Refusal queries?**
   - **YES.** In production (`chat.py`), `evaluate_retrieval_confidence()` is dead code (never called). Since `retrieve()` always returns top-$K$ chunks from HNSW (`RRF_top1 >= 1/61`), `context_chunks` is non-empty, so `generate_answer()` / `generate_stream()` **always calls the Gemini LLM**. The `__NO_CONTEXT__` token is emitted by the **LLM itself** following `PSYCHOLOGY_SYSTEM_PROMPT` Rule 3 (`generator.py` L84–91), and `chat.py` (L234–244) intercepts `__NO_CONTEXT__` in the LLM output and replaces it with the Vietnamese refusal message.
   - Even in `run_50_real_questions_benchmark.py` (L303), where the script cheated by passing `[]` as context when `is_ooc=True`, it **still called the Gemini LLM** (`call_gemini_safe`), which is why Table 6 reported `0.82 s` mean LLM latency on Safe Refusal queries.
2. **Active Caches and How to Clear Them:**
   - `_query_embed_cache` (`dict` in `backend/app/services/embedder.py`, L21, max 256 entries): clear via `_query_embed_cache.clear()`.
   - `_rerank_cache` (`dict` in `backend/app/services/reranker.py`, L24, max 256 entries): clear via `_rerank_cache.clear()`.
   - `_PAGE_IMAGE_OCR_CACHE` (`dict` backed by `data/ocr_cache.json` in `backend/app/services/parser.py`, L21): clear via `_PAGE_IMAGE_OCR_CACHE.clear()`.
   - No Redis or SQLite cache is used.

---

## (e) Location of the 50 Test Queries and Ground Truth Status
1. **Where are the 50 test queries?**
   - Saved in `outputs/empirical_50_real_questions_benchmark.json` (`REAL_Q_01` to `REAL_Q_50`) and generated in `backend/scripts/run_50_real_questions_benchmark.py` (L164–226):
     - `REAL_Q_01`–`REAL_Q_20` (20 Factual Q&A queries, each naming 1 exact arXiv paper title in single quotes)
     - `REAL_Q_21`–`REAL_Q_35` (15 Cross-Article Comparison queries, each naming 2 exact arXiv paper titles in single quotes)
     - `REAL_Q_36`–`REAL_Q_45` (10 Literature Synthesis queries, each naming 3 exact arXiv paper titles in single quotes)
     - `REAL_Q_46`–`REAL_Q_50` (5 Safe Refusal out-of-domain queries)
2. **What Ground Truth exists?**
   - **Document-level ground truth (`gt_doc_ids` / `filenames`) EXISTS 100% (`results/00_recon/matched_50_queries_by_title.json`):** Every single title quoted in `REAL_Q_01`–`REAL_Q_45` maps uniquely (1-to-1) to its exact PDF file and `document_id` in the 499-paper corpus on port 5433 (20 × 1 doc + 15 × 2 docs + 10 × 3 docs = 80 document references across 60 distinct papers; `REAL_Q_46`–`REAL_Q_50` have `gt_doc_ids = []`).
   - **Page-level ground truth (`gt_pages`) DOES NOT EXIST in the repository:**
     - Because `REAL_Q_01`–`REAL_Q_45` were generated from templates asking broadly about *"Mục tiêu nghiên cứu, giả thuyết khoa học và phương pháp luận chính"* or *"So sánh và đối chiếu phương pháp tiếp cận, đối tượng nghiên cứu và kết luận chính"*, no human-verified `gt_pages` list was ever created.
     - In `run_50_real_questions_benchmark.py` (L93–115), `verify_grounding_and_citations` only checked whether a cited `[filename - Trang X]` appeared among the **retrieved chunks passed into the LLM prompt** (Citation-in-Context), NOT whether it matched a ground-truth page or whether the page actually supported the claim!
     - Furthermore, in `run_50_real_questions_benchmark.py` (L149–156), `doc_rows` were fetched via `ORDER BY d.created_at ASC LIMIT 60` without matching the titles when re-run, and `target_ids` were passed into the SQL `WHERE c.document_id IN %s` clause (oracle document filtering!).

---

## (f) Status of the 499 PDFs and PostgreSQL `chunks` Table
- **PDF Files on Disk:** Located in `backend/data/raw_pdfs_500/` (`499` PDF files, `1,607.72 MB` total, `12,411` pages total, metadata in `backend/data/arxiv_500_metadata.json`).
- **Two PostgreSQL Databases on Machine:**
  1. **Port 5432 (`localhost:5432/rag_db`):** Has `499` arXiv docs with only **`2,994` chunks** (6 chunks/doc from `run_500_pdf_1000_benchmark.py`) plus `52` other docs (`6,767` chunks) = `9,761` chunks. (When `run_50_real_questions_benchmark.py` ran earlier on port 5432, it had `9,688` chunks).
  2. **Port 5433 (`localhost:5433/rag_db`, Docker `insight-pgvector`):** Populated by `backend/scripts/ingest_all_500_pdfs.py`. Has all `499` arXiv PDFs (`12,411` pages) segmented into **`70,825` chunks**, and **ALL `70,825` chunks (`100%`) have valid unit-norm 768-d `intfloat/multilingual-e5-base` embeddings** (`0` NULLs, `0` NaNs)! (Plus 5 extra uploaded docs with `234` chunks = `71,059` total embedded chunks).
- **Resolution of P0-2:** We use `localhost:5433/rag_db` filtered to the 499 arXiv benchmark documents (`d.filename LIKE '26%.pdf'`, `499` docs, `12,411` pages, `70,825` embedded chunks) so that 100% of systems (Acamind, Heavy Hybrid, Naive Dense, BM25) operate over the **exact same 70,825 full-text chunks** without any 4% truncation or oracle `WHERE document_id IN ...` cheating.
