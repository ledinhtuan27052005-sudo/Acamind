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
from app.services.reference_filter import is_reference_content, filter_reference_chunks, clean_reference_boundary
from app.services.cross_lingual import get_cross_lingual_query_bundle

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
_PARALLEL_TIMEOUT = 45.0  # giây — fallback sequential nếu 1 query quá lâu


def _vector_search_task(query: str, trans_query: str | None = None, doc_ids_str: str | None = None):
    """Vector search chạy trong thread riêng với session riêng.
    Hỗ trợ truy xuất đa ngữ (Dual-Vector Search): tìm đồng thời vector câu hỏi gốc và vector đã dịch
    để quét trúng cả tài liệu tiếng Anh lẫn tiếng Việt.
    SET LOCAL hnsw.ef_search = 100 cải thiện recall ~5-10% (chậm thêm ~30ms).
    """
    with SessionLocal() as s:
        s.execute(text("SET LOCAL hnsw.ef_search = 100"))
        query_vector = embed_query_cached(query)
        vec_str = "[" + ",".join(map(str, query_vector)) + "]"
        doc_filter = f"WHERE document_id IN ({doc_ids_str})" if doc_ids_str else "WHERE 1=1"
        rows = s.execute(text(f"""
            SELECT id, content, page_number, document_id,
                   1 - (embedding <=> '{vec_str}'::vector) AS score
            FROM chunks
            {doc_filter} AND embedding IS NOT NULL
            ORDER BY embedding <=> '{vec_str}'::vector ASC LIMIT {_CANDIDATE_LIMIT * 2}
        """)).fetchall()

        if trans_query and trans_query.strip().lower() != query.strip().lower():
            try:
                trans_vector = embed_query_cached(trans_query)
                trans_vec_str = "[" + ",".join(map(str, trans_vector)) + "]"
                trans_rows = s.execute(text(f"""
                    SELECT id, content, page_number, document_id,
                           1 - (embedding <=> '{trans_vec_str}'::vector) AS score
                    FROM chunks
                    {doc_filter} AND embedding IS NOT NULL
                    ORDER BY embedding <=> '{trans_vec_str}'::vector ASC LIMIT {_CANDIDATE_LIMIT * 2}
                """)).fetchall()
                # Hợp nhất các ứng viên từ 2 vector, chọn điểm tương đồng cao nhất cho mỗi chunk
                candidate_map = {}
                for r in rows:
                    candidate_map[r.id] = r
                for tr in trans_rows:
                    if tr.id not in candidate_map or tr.score > candidate_map[tr.id].score:
                        candidate_map[tr.id] = tr

                # Sắp xếp giảm dần theo điểm vector tương đồng
                rows = sorted(candidate_map.values(), key=lambda x: x.score, reverse=True)
            except Exception as e:
                logger.warning("Translated vector search failed: %s", e)

        # Lọc bỏ các chunk thuộc mục tài liệu tham khảo (References)
        clean_rows = [r for r in rows if not is_reference_content(r.content)]
        return clean_rows[:_CANDIDATE_LIMIT * 2]


def _bm25_task(query: str, trans_query: str | None, expanded_terms: list[str] | None, document_ids: list | None, doc_ids_str: str | None):
    """BM25/FTS search chạy trong thread riêng với session riêng, hỗ trợ từ khóa song ngữ."""
    with SessionLocal() as s:
        return _bm25_search(query, trans_query, expanded_terms, document_ids, doc_ids_str, s)


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
    document_ids: list[str] | None,
    db: Session,
    top_k: int = 12,
    rerank_top_n: int = 30,
) -> list[dict]:
    """Hybrid retrieval (vector + BM25 → RRF → rerank) trả về top_k chunks đa dạng từ nhiều tài liệu.

    Args:
        query: Câu hỏi gốc.
        document_ids: Danh sách doc_id user chọn. Nếu None hoặc rỗng: tìm toàn bộ kho.
        db: SQLAlchemy session.
        top_k: Số chunks trả về cuối cùng (sau rerank). Mặc định 12 (hỗ trợ tổng hợp từ 2-4 tài liệu).
        rerank_top_n: Số candidates đưa vào reranker. Mặc định 30.

    Returns:
        List chunks đã rerank, mỗi chunk chứa content/page_number/document_id/...
    """
    doc_ids_str = ", ".join([f"'{did}'" for did in document_ids]) if document_ids else None

    # Tăng ef_search cho HNSW (cải thiện recall)
    _set_hnsw_ef_search(db, 100)

    # ── 1. Đóng gói truy vấn song ngữ (Bilingual Cross-Lingual Bundle) ─────────
    bundle = get_cross_lingual_query_bundle(query)
    orig_q = bundle["orig_query"]
    trans_q = bundle["translated_query"]
    exp_terms = bundle["fts_expanded_terms"]

    # ── 2 & 3. Parallel: vector search + BM25/FTS ─────────────────────────
    # Tiết kiệm ~30-80ms bằng cách submit đồng thời. Mỗi task tự tạo session riêng.
    # Timeout 10s: nếu 1 query quá lâu (DB lock, network), fallback sequential.
    fut_vec = _RETRIEVE_EXECUTOR.submit(_vector_search_task, orig_q, trans_q, doc_ids_str)
    fut_bm25 = _RETRIEVE_EXECUTOR.submit(_bm25_task, orig_q, trans_q, exp_terms, document_ids, doc_ids_str)
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

    # Chỉ truy vấn metadata cho các document_id có trong candidates (tối ưu tốc độ vượt trội)
    cand_doc_ids = list({str(row.document_id) for row in all_unique.values()})
    doc_meta = {}
    if cand_doc_ids:
        cand_ids_str = ", ".join([f"'{d}'" for d in cand_doc_ids])
        doc_meta_rows = db.execute(text(f"""
            SELECT id, title, authors, filename
            FROM documents
            WHERE id IN ({cand_ids_str})
        """)).fetchall()
        doc_meta = {
            str(r.id): {
                "title": r.title or r.filename,
                "authors": r.authors or "",
                "filename": r.filename or "",
            }
            for r in doc_meta_rows
        }

    # Lấy rerank_top_n candidates theo RRF (lấy dư để sau khi lọc References vẫn đủ số lượng)
    top_ids = sorted(rrf.keys(), key=lambda x: rrf[x], reverse=True)[:rerank_top_n * 2]
    raw_candidates = [
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
    # Lọc bỏ hoàn toàn các chunk thuộc mục Tài liệu tham khảo (References)
    filtered_cands = filter_reference_chunks(raw_candidates)
    # Đảm bảo tính đa dạng tài liệu: Mỗi tài liệu lấy tối đa 6 chunks vào tập ứng viên đưa vào Reranker
    cand_doc_counts: dict[str, int] = {}
    diverse_cands = []
    overflow_cands = []
    for c in filtered_cands:
        did = c.get("document_id", "")
        if cand_doc_counts.get(did, 0) < 6:
            diverse_cands.append(c)
            cand_doc_counts[did] = cand_doc_counts.get(did, 0) + 1
        else:
            overflow_cands.append(c)
    candidates = (diverse_cands + overflow_cands)[:rerank_top_n]

    # ── 5. Rerank bằng cross-encoder (FlagReranker / LLM fallback) ───────
    # Phase C #3: skip rerank nếu RRF top-1 áp đảo top-2 (confident).
    # Tiết kiệm ~200-500ms reranker cho câu hỏi factoid rõ ràng.
    from app.services.authority_scorer import prioritize_candidates_by_authority_and_density

    # Tạo câu truy vấn song ngữ cho reranker nếu có bản dịch (giúp cross-encoder match cả 2 ngôn ngữ)
    rerank_query = f"{orig_q} ({trans_q})" if (trans_q and trans_q.strip().lower() != orig_q.strip().lower()) else orig_q

    if len(candidates) >= 2:
        top_rrf = sorted(candidates, key=lambda c: c["rrf_score"], reverse=True)
        ratio = top_rrf[0]["rrf_score"] / max(top_rrf[1]["rrf_score"], 1e-6)
        if ratio >= _RRF_CONFIDENT_RATIO:
            prioritized = prioritize_candidates_by_authority_and_density(top_rrf, query, trans_query=trans_q, top_k=top_k)
            return _enrich_parent_context(prioritized, db)

    # Nếu reranker fail (model chưa tải) thì vẫn trả candidates theo RRF.
    try:
        from app.services.reranker import rerank
        ranked = rerank(query, candidates, top_n=top_k * 2, trans_query=trans_q)
        if not ranked:
            ranked = candidates
    except Exception:
        ranked = candidates

    # ── 6. Ưu tiên tài liệu Uy tín nhất và Giàu thông tin đúng chủ đề nhất ──
    prioritized = prioritize_candidates_by_authority_and_density(ranked, query, trans_query=trans_q, top_k=top_k)

    # Nâng cấp Parent-Child Chunking: Lấy ngữ cảnh toàn trang / section bao quát cho các chunk hàng đầu
    return _enrich_parent_context(prioritized, db)


def _enrich_parent_context(chunks: list[dict], db: Session) -> list[dict]:
    """Parent-Child Hierarchical Context Enrichment:
    Đối với các chunk được xếp hạng cao nhất (Child Chunks - dùng để tìm kiếm chính xác),
    truy vấn kho văn bản toàn trang (page_texts) để mở rộng ngữ cảnh bao quát (Parent Context).
    Giúp LLM nắm trọn vẹn luận điểm khoa học xung quanh mà không bị đứt đoạn câu từ.
    """
    if not chunks:
        return chunks

    doc_page_pairs = {(c["document_id"], c["page_number"]) for c in chunks if c.get("page_number")}
    if not doc_page_pairs:
        return chunks

    conditions = " OR ".join([f"(document_id = '{d}' AND page_number = {p})" for d, p in doc_page_pairs])
    try:
        rows = db.execute(text(f"""
            SELECT document_id, page_number, content 
            FROM page_texts 
            WHERE {conditions}
        """)).fetchall()
        page_map = {(str(r.document_id), r.page_number): r.content for r in rows}

        for c in chunks:
            key = (c["document_id"], c.get("page_number"))
            parent_text = page_map.get(key)
            if parent_text:
                if is_reference_content(parent_text):
                    c["parent_context"] = c["content"]
                    continue
                # Làm sạch phần References nếu xuất hiện trên trang
                cleaned_parent = clean_reference_boundary(parent_text)
                if not cleaned_parent:
                    c["parent_context"] = c["content"]
                    continue
                # Cắt gọn parent_context quanh vị trí chunk để không tràn prompt token (tối đa 1500 chars)
                c_snippet = c.get("content", "")[:100]
                pos = cleaned_parent.find(c_snippet) if c_snippet else -1
                if pos >= 0:
                    start_pos = max(0, pos - 250)
                    end_pos = min(len(cleaned_parent), pos + len(c.get("content", "")) + 250)
                    c["parent_context"] = cleaned_parent[start_pos:end_pos].strip()
                else:
                    c["parent_context"] = cleaned_parent[:1500].strip()
            else:
                c["parent_context"] = c["content"]
    except Exception as e:
        logger.warning("Parent context enrichment failed: %s", e)
        for c in chunks:
            c["parent_context"] = c["content"]

    return chunks


def evaluate_retrieval_confidence(query: str, chunks: list[dict]) -> dict:
    """Corrective RAG (CRAG) Evaluator:
    Đánh giá độ tin cậy và chất lượng thông tin của các chunks trích xuất được.
    - score >= 0.60: High confidence (Correct) -> Sử dụng trực tiếp ngữ cảnh tài liệu
    - 0.35 <= score < 0.60: Ambiguous -> Cần bổ sung ngữ cảnh / web search nếu cho phép
    - score < 0.35: Incorrect / Out-of-domain -> Kích hoạt Safe Refusal hoặc Web Fallback
    """
    if not chunks:
        return {"confidence": 0.0, "status": "incorrect", "action": "refusal"}

    top_rrf = chunks[0].get("rrf_score", 0.0)
    q_words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
    context_text = " ".join([c.get("content", "").lower() for c in chunks[:3]])

    matched_words = [w for w in q_words if w in context_text]
    overlap_ratio = len(matched_words) / max(len(q_words), 1)

    # Kết hợp điểm xếp hạng RRF và tỷ lệ trùng khớp từ khóa
    confidence = round(min(1.0, (top_rrf * 15.0) * 0.5 + overlap_ratio * 0.5), 3)

    if confidence >= 0.6:
        status = "correct"
        action = "proceed"
    elif confidence >= 0.35:
        status = "ambiguous"
        action = "expand_or_web"
    else:
        status = "incorrect"
        action = "refusal"

    return {
        "confidence": confidence,
        "status": status,
        "action": action,
        "matched_terms": matched_words,
        "query_terms_count": len(q_words),
    }


def _bm25_search(
    query: str,
    trans_query: str | None,
    expanded_terms: list[str] | None,
    document_ids: list[str],
    doc_ids_str: str,
    db: Session,
) -> list:
    """BM25-style search thay thế in-memory BM25Okapi.
    Hỗ trợ truy xuất từ khóa song ngữ cho Postgres FTS.
    """
    words = re.findall(r"\w+", query.lower())
    fts_terms = [w for w in words if len(w) > 1]
    if not fts_terms and not expanded_terms and not trans_query:
        return []

    if _USE_FTS:
        try:
            fts_results = _bm25_via_fts(fts_terms, trans_query, expanded_terms, doc_ids_str, db)
            if fts_results:
                return fts_results
            logger.info("FTS returned no page hits; falling back to chunk BM25")
        except Exception as e:
            logger.warning("FTS BM25 failed, falling back to in-memory BM25: %s", e)

    # Fallback: in-memory BM25Okapi
    return _bm25_in_memory(query, doc_ids_str, db)


def _bm25_via_fts(fts_terms: list[str], trans_query: str | None, expanded_terms: list[str] | None, doc_ids_str: str | None, db: Session) -> list:
    """FTS path: query page_texts.tsv → lấy page hits → map về chunks.
    Xây dựng câu truy vấn song ngữ (Bilingual FTS): kết hợp từ khóa gốc và từ khóa đối chiếu.
    """
    orig_clause = " & ".join(fts_terms[:4]) if fts_terms else ""

    trans_clause = ""
    if trans_query and trans_query.strip().lower() != " ".join(fts_terms).lower():
        en_stop = {"what", "is", "are", "how", "why", "when", "where", "who", "which", "the", "and", "for", "with", "that", "this", "from", "define", "definition"}
        vi_stop = {"la", "gi", "nhu", "the", "nao", "cua", "trong", "va", "cac", "nhung"}
        trans_words = [w for w in re.findall(r'\b\w{2,}\b', trans_query.lower()) if w not in en_stop and w not in vi_stop]
        if trans_words:
            trans_clause = " & ".join(trans_words[:3])

    exp_clause = " | ".join(expanded_terms[:4]) if expanded_terms else ""

    clauses = [c for c in [orig_clause, trans_clause, exp_clause] if c]
    if len(clauses) > 1:
        fts_query = " | ".join(f"({c})" for c in clauses)
    elif clauses:
        fts_query = clauses[0]
    else:
        fts_query = orig_clause

    doc_filter = f"AND document_id IN ({doc_ids_str})" if doc_ids_str else ""
    try:
        fts_rows = db.execute(text(f"""
            SELECT document_id, page_number,
                   ts_rank_cd(tsv, to_tsquery('simple', :q)) AS rank
            FROM page_texts
            WHERE tsv @@ to_tsquery('simple', :q) {doc_filter}
            ORDER BY rank DESC
            LIMIT 20
        """), {"q": fts_query}).fetchall()
    except Exception as e:
        logger.warning("FTS search error: %s", e)
        return []

    if not fts_rows:
        return []

    # Map CHỈ các chunks thuộc về top matching pages thay vì tải toàn bộ DB vào RAM
    page_conditions = " OR ".join([f"(document_id = '{r.document_id}' AND page_number = {r.page_number})" for r in fts_rows])
    matching_chunks = db.execute(text(f"""
        SELECT id, content, page_number, document_id
        FROM chunks WHERE {page_conditions}
    """)).fetchall()

    if not matching_chunks:
        return []

    # Map (doc_id_str, page) → list chunks
    chunks_by_page: dict[tuple[str, int], list] = {}
    for r in matching_chunks:
        key = (str(r.document_id), r.page_number)
        chunks_by_page.setdefault(key, []).append(r)

    # Trả chunks theo thứ tự rank (bỏ qua các chunk thuộc mục References)
    out: list = []
    for r in fts_rows:
        page_chunks = chunks_by_page.get((str(r.document_id), r.page_number), [])
        valid_chunks = [c for c in page_chunks if not is_reference_content(c.content)]
        out.extend(valid_chunks)
    return out[:_CANDIDATE_LIMIT]


def _bm25_in_memory(query: str, doc_ids_str: str | None, db: Session) -> list:
    """Fallback in-memory BM25Okapi — code gốc giữ nguyên để rollback nhanh."""
    doc_filter = f"WHERE document_id IN ({doc_ids_str})" if doc_ids_str else ""
    all_chunks = db.execute(text(f"""
        SELECT id, content, page_number, document_id
        FROM chunks {doc_filter}
        LIMIT 500
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

    out_chunks = filter_reference_chunks(out_chunks)
    if not out_chunks:
        return None

    out_chunks.sort(key=lambda c: c["memory_score"], reverse=True)

    # Cross-doc dedup: nếu 2 chunks từ docs khác nhau có claim giống nhau
    # (fuzzy match), giữ 1 (cao nhất theo memory_score).
    # Tránh trả về cùng 1 fact 2 lần khi user upload cùng file vào 2 docs.
    out_chunks = _cross_doc_dedup(out_chunks)

    return out_chunks[:top_k]
