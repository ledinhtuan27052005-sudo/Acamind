from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import re
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from rank_bm25 import BM25Okapi
from app.services.embedder import embed_query_cached
from app.services.dedup_utils import _is_fuzzy_dup
from app.db.postgres import SessionLocal

logger = logging.getLogger(__name__)

# Giới hạn số candidates lấy về từ mỗi nguồn (vector / BM25) trước khi RRF + rerank.
# Tăng từ 10 → 20 để reranker có nhiều lựa chọn hơn, tránh bỏ sót context quan trọng.
_CANDIDATE_LIMIT = 20

# Phase C #1: gate FTS path bằng env để rollback nhanh nếu gây regression.
# USE_FTS=1 (mặc định) → dùng Postgres FTS. 0 → in-memory BM25 cũ.
_USE_FTS = os.getenv("USE_FTS", "1") != "0"

# Phase C #3: ngưỡng RRF ratio để skip rerank. Top-1 RRF score / Top-2 RRF score.
# ≥ _RRF_CONFIDENT_RATIO → top-1 áp đảo → confident, không cần rerank.
_RRF_CONFIDENT_RATIO = 2.5

# Cross-doc dedup: threshold để 2 claim từ docs khác nhau được coi là trùng.
# Mặc định 0.85 (cùng threshold với key_facts dedup trong memory_builder).
_L1_CROSS_DOC_DEDUP_THRESHOLD = 0.85

# ── Parallel retrieval: vector + BM25 chạy đồng thời ─────────────────────────
# SQLAlchemy sync session KHÔNG thread-safe, mỗi thread tạo session riêng qua
# SessionLocal(). Pool mặc định (5 + overflow 10) đủ cho 2 worker này.
_RETRIEVE_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="retrieve")
_PARALLEL_TIMEOUT = 10.0  # giây — fallback sequential nếu 1 query quá lâu


def _vector_search_task(query: str, doc_ids_str: str):
    """Vector search chạy trong thread riêng với session riêng.

    SET LOCAL hnsw.ef_search = 100 cải thiện recall ~5-10% (chậm thêm ~30ms).
    """
    with SessionLocal() as s:
        s.execute(text("SET LOCAL hnsw.ef_search = 100"))
        query_vector = embed_query_cached(query)
        vec_str = "[" + ",".join(map(str, query_vector)) + "]"
        return s.execute(text(f"""
            SELECT id, content, page_number, document_id,
                   1 - (embedding <=> '{vec_str}'::vector) AS score
            FROM chunks
            WHERE document_id IN ({doc_ids_str}) AND embedding IS NOT NULL
            ORDER BY score DESC LIMIT {_CANDIDATE_LIMIT}
        """)).fetchall()


def _bm25_task(query: str, document_ids: list, doc_ids_str: str):
    """BM25/FTS search chạy trong thread riêng với session riêng."""
    with SessionLocal() as s:
        return _bm25_search(query, document_ids, doc_ids_str, s)


def _cross_doc_dedup(chunks: list[dict]) -> list[dict]:
    """Bỏ chunk trùng giữa các docs trong L1 retrieval.

    Khi user upload cùng 1 file 2 lần (2 docs khác nhau nhưng cùng content), hoặc
    2 docs khác nhau có cùng 1 fact (vd cùng trích dẫn từ sách), L1 sẽ trả về
    cùng 1 fact 2 lần gây noise. Hàm này giữ 1 chunk có memory_score cao nhất.

    Args:
        chunks: list đã được sort theo memory_score giảm dần.

    Returns:
        list đã dedup, giữ nguyên thứ tự memory_score.
    """
    if not chunks:
        return []
    out = []
    seen_claims: list[str] = []  # normalized claim text đã thấy
    for c in chunks:
        content = c.get("content", "")
        if not content:
            continue
        # Check fuzzy match với các claims đã thấy
        is_dup = any(_is_fuzzy_dup(content, seen, _L1_CROSS_DOC_DEDUP_THRESHOLD) for seen in seen_claims)
        if is_dup:
            continue
        seen_claims.append(content)
        out.append(c)
    return out


def _set_hnsw_ef_search(db: Session, ef: int = 100) -> None:
    """Tăng độ chính xác tìm vector gần đúng của HNSW index.

    Mặc định pgvector HNSW dùng ef_search=40 (đổi recall/latency).
    Tăng lên 100 cho retrieval chính xác hơn ~5–10% (chậm thêm ~30ms).
    """
    try:
        db.execute(text(f"SET LOCAL hnsw.ef_search = {int(ef)}"))
    except Exception:
        pass


def retrieve(
    query: str,
    document_ids: list[str],
    db: Session,
    top_k: int = 8,
    rerank_top_n: int = 20,
) -> list[dict]:
    """Hybrid retrieval (vector + BM25 → RRF → rerank) trả về top_k chunks.

    Args:
        query: Câu hỏi gốc.
        document_ids: Danh sách doc_id user chọn.
        db: SQLAlchemy session.
        top_k: Số chunks trả về cuối cùng (sau rerank). Mặc định 8 (tăng từ 5).
        rerank_top_n: Số candidates đưa vào reranker. Mặc định 20.

    Returns:
        List chunks đã rerank, mỗi chunk chứa content/page_number/document_id/...
    """
    if not document_ids:
        return []

    doc_ids_str = ", ".join([f"'{did}'" for did in document_ids])

    # Tăng ef_search cho HNSW (cải thiện recall)
    _set_hnsw_ef_search(db, 100)

    # ── 1. Document metadata for citations ──────────────────────────────
    doc_meta_rows = db.execute(text(f"""
        SELECT id, title, authors, filename
        FROM documents
        WHERE id IN ({doc_ids_str})
    """)).fetchall()
    doc_meta = {
        str(r.id): {
            "title": r.title or r.filename,
            "authors": r.authors or "",
            "filename": r.filename or "",
        }
        for r in doc_meta_rows
    }

    # ── 2 & 3. Parallel: vector search + BM25/FTS ─────────────────────────
    # Tiết kiệm ~30-80ms bằng cách submit đồng thời. Mỗi task tự tạo session riêng.
    # Timeout 10s: nếu 1 query quá lâu (DB lock, network), fallback sequential.
    # Dense retrieval is an enhancement, not a single point of failure.  In
    # particular, Windows application-control policies can block the local ML
    # DLL while Postgres FTS remains fully usable.  Resolve both workers
    # independently so lexical retrieval still produces grounded context.
    fut_vec = _RETRIEVE_EXECUTOR.submit(_vector_search_task, query, doc_ids_str)
    fut_bm25 = _RETRIEVE_EXECUTOR.submit(_bm25_task, query, document_ids, doc_ids_str)
    try:
        vector_results = fut_vec.result(timeout=_PARALLEL_TIMEOUT)
    except (FuturesTimeoutError, Exception) as exc:
        logger.warning("Vector retrieval unavailable; continuing with FTS/BM25: %s", exc)
        vector_results = []
    try:
        bm25_results = fut_bm25.result(timeout=_PARALLEL_TIMEOUT)
    except (FuturesTimeoutError, Exception) as exc:
        logger.warning("FTS/BM25 retrieval unavailable; continuing with vector results: %s", exc)
        bm25_results = []

    # ── 4. Reciprocal Rank Fusion (k=60) ─────────────────────────────────
    k = 60
    rrf: dict[str, float] = {}
    for rank, row in enumerate(vector_results):
        rid = str(row.id)
        rrf[rid] = rrf.get(rid, 0.0) + 1.0 / (rank + 1 + k)
    for rank, row in enumerate(bm25_results):
        rid = str(row.id)
        rrf[rid] = rrf.get(rid, 0.0) + 1.0 / (rank + 1 + k)

    all_unique: dict[str, object] = {}
    for row in list(vector_results) + bm25_results:
        rid = str(row.id)
        if rid not in all_unique:
            all_unique[rid] = row

    # Lấy rerank_top_n candidates theo RRF
    top_ids = sorted(rrf.keys(), key=lambda x: rrf[x], reverse=True)[:rerank_top_n]
    candidates = [
        {
            "id": rid,
            "content": all_unique[rid].content,
            "page_number": all_unique[rid].page_number,
            "document_id": str(all_unique[rid].document_id),
            "rrf_score": round(rrf[rid], 6),
            "doc_title": doc_meta.get(str(all_unique[rid].document_id), {}).get("title", ""),
            "doc_authors": doc_meta.get(str(all_unique[rid].document_id), {}).get("authors", ""),
            "doc_filename": doc_meta.get(str(all_unique[rid].document_id), {}).get("filename", ""),
        }
        for rid in top_ids
        if rid in all_unique
    ]

    # ── 5. Rerank bằng cross-encoder (FlagReranker / LLM fallback) ───────
    # Phase C #3: skip rerank nếu RRF top-1 áp đảo top-2 (confident).
    # Tiết kiệm ~200-500ms reranker cho câu hỏi factoid rõ ràng.
    if len(candidates) >= 2:
        top_rrf = sorted(candidates, key=lambda c: c["rrf_score"], reverse=True)
        ratio = top_rrf[0]["rrf_score"] / max(top_rrf[1]["rrf_score"], 1e-6)
        if ratio >= _RRF_CONFIDENT_RATIO:
            return top_rrf[:top_k]

    # Nếu reranker fail (model chưa tải) thì vẫn trả candidates theo RRF.
    try:
        from app.services.reranker import rerank
        ranked = rerank(query, candidates, top_n=top_k)
        if not ranked:
            ranked = candidates[:top_k]
    except Exception:
        ranked = candidates[:top_k]

    return ranked


def _bm25_search(
    query: str,
    document_ids: list[str],
    doc_ids_str: str,
    db: Session,
) -> list:
    """BM25-style search thay thế in-memory BM25Okapi.

    Phase C #1: query FTS trên page_texts.tsv (GIN-indexed) → lấy top pages by rank
    → map về chunks. Best-effort: nếu FTS fail (chưa migrate schema, hoặc USE_FTS=0),
    fallback in-memory BM25 cũ.

    Returns:
        List SQLAlchemy rows giống format BM25Okapi cũ: có .id, .content, .page_number, .document_id
    """
    # Build FTS query: tách từ, AND chúng, chỉ giữ từ len > 1
    # to_tsquery('simple', 'word1 & word2 & ...') — escape ký tự đặc biệt bằng cách
    # chỉ giữ alphanumeric + underscore.
    words = re.findall(r"\w+", query.lower())
    fts_terms = [w for w in words if len(w) > 1]
    if not fts_terms:
        return []

    if _USE_FTS:
        try:
            fts_results = _bm25_via_fts(fts_terms, doc_ids_str, db)
            if fts_results:
                return fts_results
            # Older uploads may have chunks but no page_texts rows yet.  They
            # remain searchable through the legacy lexical index.
            logger.info("FTS returned no page hits; falling back to chunk BM25")
        except Exception as e:
            # FTS có thể fail nếu chưa migrate schema (chưa có cột tsv).
            # Fallback về in-memory BM25 để RAG không chết.
            import logging
            logging.getLogger(__name__).warning(
                "FTS BM25 failed, falling back to in-memory BM25: %s", e
            )

    # Fallback: in-memory BM25Okapi (code cũ, giữ nguyên để rollback an toàn)
    return _bm25_in_memory(query, doc_ids_str, db)


def _bm25_via_fts(fts_terms: list[str], doc_ids_str: str, db: Session) -> list:
    """FTS path: query page_texts.tsv → lấy page hits → map về chunks.

    1. ts_rank_cd tìm top 20 pages có từ khoá xuất hiện
    2. Lấy chunks trong các page đó (cùng document_id, page_number)
    """
    fts_query = " & ".join(fts_terms)  # AND giữa các từ
    fts_rows = db.execute(text("""
        SELECT document_id, page_number,
               ts_rank_cd(tsv, to_tsquery('simple', :q)) AS rank
        FROM page_texts
        WHERE document_id IN ({doc_ids_str})
          AND tsv @@ to_tsquery('simple', :q)
        ORDER BY rank DESC
        LIMIT 20
    """.format(doc_ids_str=doc_ids_str)), {"q": fts_query}).fetchall()

    if not fts_rows:
        return []

    # Lấy TẤT CẢ chunks (chỉ trong selected docs) rồi group theo (doc_id, page)
    # Lưu ý: nếu kho lớn (>100k chunks) có thể tối ưu bằng cách dùng subquery
    # IN (SELECT page_number FROM page_texts WHERE ...) — nhưng cho MVP giữ đơn giản.
    all_chunks = db.execute(text(f"""
        SELECT id, content, page_number, document_id
        FROM chunks WHERE document_id IN ({doc_ids_str})
    """)).fetchall()

    if not all_chunks:
        return []

    # Map (doc_id_str, page) → list chunks
    chunks_by_page: dict[tuple[str, int], list] = {}
    for r in all_chunks:
        key = (str(r.document_id), r.page_number)
        chunks_by_page.setdefault(key, []).append(r)

    # Trả chunks theo thứ tự rank (chunks trong page nào trước → trước)
    out: list = []
    for r in fts_rows:
        out.extend(chunks_by_page.get((str(r.document_id), r.page_number), []))
    return out[:_CANDIDATE_LIMIT]


def _bm25_in_memory(query: str, doc_ids_str: str, db: Session) -> list:
    """Fallback in-memory BM25Okapi — code gốc giữ nguyên để rollback nhanh."""
    all_chunks = db.execute(text(f"""
        SELECT id, content, page_number, document_id
        FROM chunks WHERE document_id IN ({doc_ids_str})
    """)).fetchall()
    if not all_chunks:
        return []
    corpus = [r.content.lower().split() for r in all_chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query.lower().split())
    top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
        :_CANDIDATE_LIMIT
    ]
    return [all_chunks[i] for i in top_idx]


def retrieve_full_page(document_id: str, page_number: int, db: Session) -> str:
    """Truy xuất toàn bộ text của một trang từ bảng page_texts."""
    row = db.execute(text("""
        SELECT content FROM page_texts
        WHERE document_id = :doc_id AND page_number = :page
    """), {"doc_id": document_id, "page": page_number}).first()
    return row.content if row else ""


# ── Phase A: L1 memory retrieval ──────────────────────────────────────────────

def retrieve_via_memory(
    query: str,
    document_ids: list[str],
    db: Session,
    top_k: int = 8,
) -> list[dict] | None:
    """L1 lookup dựa trên compressed memory.

    Strategy:
    1. Check tất cả document_ids đều có memory_status='ready'. Nếu thiếu 1 → None.
    2. Cosine similarity query vs abstract_embedding → chọn top 3 docs liên quan nhất.
    3. Trong top 3 docs: scan key_facts, score bằng word overlap + phrase match.
    4. Trả top 5-8 facts dạng chunks (content + page + document_id + from_memory=True).

    Returns:
        - None nếu không hit (caller fallback L2 RAG)
        - List chunks nếu hit (caller dùng luôn, KHÔNG cần embed/vector search/rerank)
    """
    if not document_ids:
        return None

    # 1. Memory availability check
    doc_ids_str = ", ".join(f"'{d}'" for d in document_ids)
    try:
        mem_rows = db.execute(text(f"""
            SELECT document_id, abstract, key_facts
            FROM document_summaries
            WHERE document_id IN ({doc_ids_str})
              AND memory_status = 'ready'
        """)).fetchall()
    except Exception as e:
        logger.warning("L1 memory availability check failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return None

    if not mem_rows or len(mem_rows) != len(document_ids):
        return None  # ít nhất 1 doc thiếu memory → skip L1

    # 2. Cosine query vs abstract để chọn top 3 docs (best-effort)
    try:
        query_vector = embed_query_cached(query)
    except Exception:
        query_vector = None

    top_docs = []

    if query_vector is not None:
        q_str = "[" + ",".join(f"{x:.6f}" for x in query_vector) + "]"
        try:
            # Tính similarity trực tiếp trong DB!
            sim_rows = db.execute(text(f"""
                SELECT document_id, abstract, key_facts,
                       1 - (abstract_embedding <=> :q) AS similarity
                FROM document_summaries
                WHERE document_id IN ({doc_ids_str})
                  AND memory_status = 'ready'
                  AND abstract_embedding IS NOT NULL
            """), {"q": q_str}).fetchall()
            
            doc_scored = [(float(r.similarity or 0.0), r) for r in sim_rows]
            doc_scored.sort(key=lambda x: x[0], reverse=True)
            top_docs = doc_scored[:3]
        except Exception as e:
            logger.warning("L1 similarity SQL query failed: %s", e)
            try:
                db.rollback()
            except Exception:
                pass
            query_vector = None  # Force fallback below

    # Fallback nếu không có query_vector hoặc query similarity bị lỗi
    if query_vector is None or not top_docs:
        top_docs = [(0.0, r) for r in mem_rows]  # dùng tất cả mem_rows có sẵn


    if not top_docs:
        return None

    # 3. Scan key_facts trong top 3 docs, score bằng word overlap
    query_lower = query.lower()
    q_tokens = set(re.findall(r"\w+", query_lower))
    if not q_tokens:
        return None

    out_chunks: list[dict] = []
    for _, r in top_docs:
        facts = r.key_facts or []
        for f in facts:
            claim = (f.get("claim") or "").strip()
            if not claim:
                continue
            claim_lower = claim.lower()
            claim_tokens = set(re.findall(r"\w+", claim_lower))
            # Score = số từ query xuất hiện trong claim + bonus nếu cả phrase khớp
            overlap = len(q_tokens & claim_tokens)
            if overlap == 0:
                continue
            score = overlap
            # Bonus: nếu toàn bộ query phrase xuất hiện trong claim → boost mạnh
            if len(query_lower) > 5 and query_lower in claim_lower:
                score += 5
            # Bonus: confidence từ LLM
            try:
                conf = float(f.get("confidence", 0.8))
                score += conf
            except (TypeError, ValueError):
                pass

            out_chunks.append({
                "id": f"mem-{r.document_id}-{f.get('page', 0)}-{hash(claim) % 10000}",
                "content": claim,
                "page_number": int(f.get("page", 1)),
                "document_id": str(r.document_id),
                "rrf_score": 0.0,  # không dùng cho L1
                "doc_title": "",   # enriched by caller
                "doc_authors": "",
                "from_memory": True,
                "memory_score": score,
            })

    if not out_chunks:
        return None

    out_chunks.sort(key=lambda c: c["memory_score"], reverse=True)

    # Cross-doc dedup: nếu 2 chunks từ docs khác nhau có claim giống nhau
    # (fuzzy match), giữ 1 (cao nhất theo memory_score).
    # Tránh trả về cùng 1 fact 2 lần khi user upload cùng file vào 2 docs.
    out_chunks = _cross_doc_dedup(out_chunks)

    return out_chunks[:top_k]
