from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import re
import math
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from rank_bm25 import BM25Okapi
from app.services.embedder import embed_query_cached, embed_queries_batch_cached
from app.services.dedup_utils import _is_fuzzy_dup
from app.db.postgres import SessionLocal
from app.services.reference_filter import is_reference_content, filter_reference_chunks, clean_reference_boundary, clean_front_matter_header
from app.services.cross_lingual import get_cross_lingual_query_bundle
from app.services.ablation_config import flags as ablation_flags
import contextvars

logger = logging.getLogger(__name__)


def _sanitize_uuid_list(document_ids: list[str] | None) -> list[str]:
    """Chỉ giữ lại các chuỗi UUID hợp lệ để chống SQL Injection tuyệt đối."""
    if not document_ids:
        return []
    valid: list[str] = []
    for d in document_ids:
        try:
            valid.append(str(uuid.UUID(str(d).strip())))
        except (ValueError, TypeError, AttributeError):
            continue
    return valid


# Giới hạn số candidates lấy về từ mỗi nguồn (vector / lexical) trước khi RRF + rerank.
def _sanitize_doc_ids_sql(doc_ids_str: str | None) -> str | None:
    """Chuẩn hóa chuỗi danh sách UUID truyền vào mệnh đề IN (...) để đảm bảo an toàn SQL tuyệt đối."""
    if not doc_ids_str:
        return None
    raw_tokens = [tok.strip().strip("'\"") for tok in str(doc_ids_str).split(",") if tok.strip()]
    valid_uuids = _sanitize_uuid_list(raw_tokens)
    if not valid_uuids:
        return None
    return ", ".join(f"'{u}'" for u in valid_uuids)
# Tăng từ 10 → 20 để reranker có nhiều lựa chọn hơn, tránh bỏ sót context quan trọng.
_CANDIDATE_LIMIT = 20

# Phase C #1: gate FTS path bằng env để rollback nhanh nếu gây regression.
# USE_FTS=1 (mặc định) → dùng Postgres FTS. 0 → in-memory BM25 cũ.
_USE_FTS = os.getenv("USE_FTS", "1") != "0"

# Dynamic Confidence-Scaled Retrieval (DCSR) parameters synchronized with manuscript Eq. (5)–(8):
# Δ_RRF = RRF_(1) / RRF_(2) >= τ_Δ (1.25) and C(q) >= τ_conf (0.75) → skip cross-encoder reranking.
_RRF_CONFIDENT_RATIO = float(os.getenv("DCSR_RRF_RATIO", "1.25"))
_DCSR_CONF_THRESHOLD = float(os.getenv("DCSR_CONF_THRESHOLD", "0.75"))

# CẢNH BÁO: các ngưỡng dưới đây là giá trị đặt thủ công, CHƯA được hiệu chuẩn trên dữ liệu có nhãn.
# Cho phép ghi đè qua biến môi trường để hiệu chuẩn trên tập Dev và phân tích độ nhạy.
_CRAG_THRESHOLD = float(os.getenv("CRAG_THRESHOLD", "0.5355"))
_OOD_MIN_VECTOR_NO_LEXICAL = float(os.getenv("OOD_MIN_VECTOR_NO_LEXICAL", "0.805"))
_OOD_MIN_VECTOR_NO_DICTIONARY = float(os.getenv("OOD_MIN_VECTOR_NO_DICTIONARY", "0.84"))
_OOD_MIN_RERANK = float(os.getenv("OOD_MIN_RERANK", "0.02"))
# Ngưỡng liên quan tương đối: bỏ đoạn có điểm < tỉ lệ này × điểm đoạn tốt nhất (cùng danh sách/đối tượng)
# trước khi đưa vào LLM. Giá trị mặc định đặt thủ công, chưa hiệu chuẩn.
_RELATIVE_RELEVANCE_MIN = float(os.getenv("RELATIVE_RELEVANCE_MIN", "0.4"))


def compute_dcsr_confidence(rrf_top1: float) -> float:
    """Compute DCSR routing confidence C(q) per Eq. (8) of the manuscript:
    C(q) = min(1.0, 15.0 * RRF_top1 + 0.5 / (1 + exp(-200 * (RRF_top1 - 0.0165))))

    Lưu ý: các hằng số 15.0 / 200 / 0.0165 được đặt thủ công, chưa hiệu chuẩn; C(q) là điểm
    định tuyến heuristic, KHÔNG phải xác suất câu trả lời đúng.
    """
    return min(1.0, 15.0 * rrf_top1 + 0.5 / (1.0 + math.exp(-200.0 * (rrf_top1 - 0.0165))))


# Cross-doc dedup: threshold để 2 claim từ docs khác nhau được coi là trùng.
# Mặc định 0.85 (cùng threshold với key_facts dedup trong memory_builder).
_L1_CROSS_DOC_DEDUP_THRESHOLD = 0.85

# ── Parallel retrieval: vector + lexical chạy đồng thời ─────────────────────────
# SQLAlchemy sync session KHÔNG thread-safe, mỗi thread tạo session riêng qua
# SessionLocal(). Pool mặc định (5 + overflow 10) đủ cho 2 worker này.
_RETRIEVE_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="retrieve")
_TARGET_EXECUTOR = ThreadPoolExecutor(max_workers=3, thread_name_prefix="study")
_PARALLEL_TIMEOUT = 45.0  # giây — fallback sequential nếu 1 query quá lâu


def _is_valid_prose_chunk(content: str) -> bool:
    """Loại bỏ các chunk bảng số liệu thô, biểu đồ Forest Plot hoặc ký hiệu rời rạc gây nhiễu vector (hubness)."""
    if not content:
        return False
    non_space = re.sub(r"\s+", "", content)
    if len(non_space) < 60:
        return False
    alpha_count = sum(1 for ch in non_space if ch.isalpha())
    if (alpha_count / len(non_space)) < 0.62:
        return False
    c_low = content.lower()
    if any(p in c_low for p in (
        "favours control",
        "std diff in means",
        "statistics for each study",
        "sd standard deviation, nr not reported",
        "table 1. continued",
        "table 2. continued",
        "table 3. continued",
    )):
        return False
    if len(re.findall(r"\b[A-Z]{2,6}\s+[a-z]{3,}\s+[a-z]{3,}", content)) >= 4 and content.count(". ") < 3:
        return False
    if len(re.findall(r"\b[A-Z][a-zA-Z\'-]{1,20}\s+(?:19|20)\d{2}\b", content)) >= 4 and content.count(". ") < 3:
        return False
    lines = [ln.strip() for ln in content.splitlines() if ln.strip() and not ln.strip().startswith("[Trang")]
    if len(lines) >= 6:
        short_lines = sum(1 for ln in lines if len(ln.split()) <= 3)
        if (short_lines / len(lines)) >= 0.55:
            return False
    return len(re.findall(r"[a-zA-ZÀ-ỹ]{3,}", content)) >= 18


def _vector_search_task(query: str, trans_query: str | None = None, doc_ids_str: str | None = None):
    """Vector search chạy trong thread riêng với session riêng.
    Hỗ trợ truy xuất đa ngữ (Dual-Vector Search): tìm đồng thời vector câu hỏi gốc và vector đã dịch
    để quét trúng cả tài liệu tiếng Anh lẫn tiếng Việt.
    SET LOCAL hnsw.ef_search = 100 cải thiện recall ~5-10% (chậm thêm ~30ms).
    """
    raw_limit = _CANDIDATE_LIMIT * 5
    with SessionLocal() as s:
        s.execute(text("SET LOCAL max_parallel_workers_per_gather = 0"))
        s.execute(text("SET LOCAL hnsw.ef_search = 100"))
        query_vector = embed_query_cached(query)
        vec_str = "[" + ",".join(map(str, query_vector)) + "]"
        safe_doc_sql = _sanitize_doc_ids_sql(doc_ids_str)
        doc_filter = f"WHERE document_id IN ({safe_doc_sql})" if safe_doc_sql else "WHERE 1=1"
        rows = s.execute(text(f"""
            SELECT id, content, page_number, document_id,
                   1 - (embedding <=> '{vec_str}'::vector) AS score
            FROM chunks
            {doc_filter} AND embedding IS NOT NULL
            ORDER BY embedding <=> '{vec_str}'::vector ASC LIMIT {raw_limit}
        """)).fetchall()
        rows = [r for r in rows if _is_valid_prose_chunk(r.content) and not is_reference_content(r.content)]

        if trans_query and trans_query.strip().lower() != query.strip().lower():
            try:
                trans_vector = embed_query_cached(trans_query)
                trans_vec_str = "[" + ",".join(map(str, trans_vector)) + "]"
                trans_rows = s.execute(text(f"""
                    SELECT id, content, page_number, document_id,
                           1 - (embedding <=> '{trans_vec_str}'::vector) AS score
                    FROM chunks
                    {doc_filter} AND embedding IS NOT NULL
                    ORDER BY embedding <=> '{trans_vec_str}'::vector ASC LIMIT {raw_limit}
                """)).fetchall()
                trans_rows = [r for r in trans_rows if _is_valid_prose_chunk(r.content) and not is_reference_content(r.content)]
                # Cân bằng thang điểm Cosine giữa vector câu hỏi gốc và vector tiếng Anh (Cross-Lingual Score Alignment)
                top_orig = float(rows[0].score) if rows else 0.85
                top_trans = float(trans_rows[0].score) if trans_rows else 0.85
                trans_offset = max(0.0, top_orig - top_trans + 0.002)

                candidate_map = {}
                score_map = {}
                for r in rows:
                    sc = float(r.score)
                    candidate_map[r.id] = r
                    score_map[r.id] = sc
                for tr in trans_rows:
                    sc = float(tr.score) + trans_offset
                    if tr.id not in candidate_map or sc > score_map[tr.id]:
                        candidate_map[tr.id] = tr
                        score_map[tr.id] = sc

                # Sắp xếp giảm dần theo điểm đã hiệu chuẩn đa ngữ
                rows = sorted(candidate_map.values(), key=lambda x: score_map.get(x.id, 0.0), reverse=True)
            except Exception as e:
                logger.warning("Translated vector search failed: %s", e)

        return rows[:_CANDIDATE_LIMIT * 2]


def _bm25_task(query: str, trans_query: str | None, expanded_terms: list[str] | None, document_ids: list | None, doc_ids_str: str | None):
    """Lexical worker: PostgreSQL FTS or in-memory BM25. Legacy name retained."""
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


def classify_and_decompose_query(query: str) -> dict:
    """Task-Adaptive Query Router & Multi-Document Sub-Query Decomposer (Section 3.3, Eq. 9):
    Phân loại truy vấn thành 3 lộ trình:
      1. 'cross_article_comparison' (M=2): Truy vấn đối sánh 2 công trình cụ thể (1) '...' và (2) '...'.
      2. 'literature_synthesis' (M>=3): Truy vấn tổng hợp đa nghiên cứu phân tách bởi '|' (Study_1 | Study_2 | Study_3).
      3. 'single_focus' (M=1): Truy vấn thực kiện đơn mục tiêu hoặc chủ đề chung.
    """
    m1 = re.search(r"\(1\)\s*['\"](.+?)['\"](?=\s*(?:và|and|,|\(2\)))", query)
    m2 = re.search(r"\(2\)\s*['\"](.+?)['\"](?=\s*(?:[—–\-?:;.]|$))", query)
    if not m1:
        m1 = re.search(r"\(1\)\s*['\"]([^'\"]+)['\"]", query)
    if not m2:
        m2 = re.search(r"\(2\)\s*['\"]([^'\"]+)['\"]", query)
    if m1 and m2:
        t1 = m1.group(1).strip()
        t2 = m2.group(1).strip()
        return {
            "route": "cross_article_comparison",
            "num_targets": 2,
            "sub_queries": [t1, t2],
            "quota_per_target": 3,
        }

    quoted = re.findall(r'["“]([^"”]{3,})["”]', query)
    if len(quoted) >= 2 and re.search(r"so sánh|đối chiếu|compare|contrast|tổng hợp|synthesi", query, re.I):
        targets = list(dict.fromkeys(quoted))[:6]
        return {"route": "cross_article_comparison" if len(targets) == 2 else "literature_synthesis",
                "num_targets": len(targets), "sub_queries": targets, "quota_per_target": 3}

    if "|" in query:
        header_split = query.split(":", 1)
        pipe_part = header_split[1] if (len(header_split) == 2 and "|" in header_split[1]) else query
        parts = list(dict.fromkeys(p.strip().strip("'\"") for p in pipe_part.split("|") if len(p.strip()) >= 5))[:6]
        if len(parts) >= 2:
            quota = max(2, 6 // len(parts))
            return {
                "route": "literature_synthesis",
                "num_targets": len(parts),
                "sub_queries": parts,
                "quota_per_target": quota,
            }

    # Explicit short study labels ("nghiên cứu A và B") are common in chat.
    # Keep comparison criteria outside the labels so both targets are scored
    # against the same requested dimension.
    labeled = re.search(
        r"^(?:so sánh|đối chiếu|compare|contrast)\s+(?:(?:nghiên cứu|bài báo|study|paper)\s+)?"
        r"([A-Z][A-Za-z0-9_-]{0,30})\s+(?:và|với|and|with)\s+"
        r"(?:(?:nghiên cứu|bài báo|study|paper)\s+)?([A-Z][A-Za-z0-9_-]{0,30})"
        r"(?=\s+(?:về|theo|regarding|on)\b|[?.]|$)", query,
    )
    if labeled:
        return {"route": "cross_article_comparison", "num_targets": 2,
                "sub_queries": [labeled.group(1), labeled.group(2)], "quota_per_target": 4}

    # Natural-language comparisons often name two studies without the legacy
    # '(1) ... (2) ...' or pipe syntax. Search both sides independently, then
    # interleave their evidence; a single global search tends to crowd one out.
    comparison = bool(re.search(r"\b(?:so sánh|đối chiếu|giữa hai nghiên cứu|từ hai nghiên cứu)\b", query, re.I))
    comparison = comparison or bool(re.search(r"nghiên cứu\s+[“\"].+?[”\"]\s+và\s+[A-Z][A-Za-z0-9. -]+", query, re.I))
    comparison = comparison or bool(re.search(r"tổng hợp.+nghiên cứu.+\s+và\s+(?:chấm|nghiên cứu)", query, re.I))
    if comparison:
        body = re.sub(r"^(?:so sánh|đối chiếu)\s+", "", query, flags=re.I).strip().rstrip(".?")
        # Tách "A và nghiên cứu B"; các dạng "A và B" tổng quát do nhánh m_nat bên dưới xử lý
        # (không viết cứng tên nghiên cứu cụ thể).
        for separator in (r"(?<!đối)\s+với\s+", r"\s+và\s+(?=nghiên cứu|chấm)"):
            parts = re.split(separator, body, maxsplit=1, flags=re.I)
            if len(parts) == 2 and all(len(part.strip()) >= 5 for part in parts):
                return {
                    "route": "cross_article_comparison",
                    "num_targets": 2,
                    "sub_queries": [part.strip() for part in parts],
                    "quota_per_target": 4,
                }

    m_nat = re.match(
        r"^(?:hãy\s+|xin\s+)?(?:so sánh(?:\s+và\s+đối\s+chiếu|\s+sự\s+khác\s+biệt)?(?:\s+giữa)?|"
        r"đối chiếu(?:\s+điểm\s+khác\s+biệt)?(?:\s+giữa)?|phân biệt(?:\s+giữa)?|sự khác (?:biệt|nhau)\s+giữa|điểm (?:giống và )?khác (?:biệt|nhau)\s+giữa|"
        r"compare(?:\s+and\s+contrast)?(?:\s+between)?|distinguish\s+between|differences?\s+between)\s+(.+)$",
        query.strip(),
        flags=re.I,
    )
    if m_nat:
        nat_body = re.sub(r"\s+là\s+gì\s*$", "", m_nat.group(1).strip().rstrip(".?!"), flags=re.I)
        nat_body = re.sub(r"^(?:hai|2|ba|3)\s+(?:liệu pháp|phương pháp|rối loạn|học thuyết|thang đo|khái niệm|trường phái|nghiên cứu|bài báo)\s*:?\s*", "", nat_body, flags=re.I)
        nat_body = re.sub(r"^(?:nghiên cứu|bài báo|công trình)\s+(?:của\s+)?", "", nat_body, flags=re.I)
        nat_body = re.sub(r"^(?:hiệu quả|tác động|ảnh hưởng|vai trò|mối quan hệ|đặc điểm)\s+của\s+", "", nat_body, flags=re.I)
        nat_focus = ""
        focus_match = re.search(
            r"\s+(?:về\s+|xét về\s+|dựa trên\s+|theo\s+(?:các\s+)?tiêu chí\s+|đối\s+với\s+|"
            r"trong\s+(?:việc|điều trị|chẩn đoán|thực hành|can thiệp)\s+|ở\s+khía cạnh\s+|"
            r"regarding\s+|in terms of\s+|with respect to\s+)(.+)$",
            nat_body,
            flags=re.I,
        )
        if focus_match and re.search(r"\s+(?:(?<!đối\s)với|và|vs\.?|versus|and|with)\s+", nat_body[:focus_match.start()], flags=re.I):
            nat_focus = focus_match.group(1).strip()
            nat_body = nat_body[:focus_match.start()].strip()
        # Hỗ trợ phân rã 3 mục tiêu dạng "A, B và C" (Literature Synthesis M=3)
        m_three = re.match(r"^([^,;]{3,65}),\s*([^,;]{3,65}?)\s+(?:và|(?<!đối\s)với|and)\s+([^,;]{3,65})$", nat_body, flags=re.I)
        if m_three:
            t_list = [re.sub(r"^(?:nghiên cứu|bài báo|công trình)\s+(?:của\s+)?", "", g.strip(" ,;"), flags=re.I) for g in m_three.groups()]
            if all(len(x) >= 3 for x in t_list):
                return {
                    "route": "literature_synthesis",
                    "num_targets": 3,
                    "sub_queries": t_list,
                    "quota_per_target": 3,
                    "comparison_focus": nat_focus,
                }
        for sep in (r"(?<!đối)\s+với\s+", r"\s+vs\.?\s+", r"\s+versus\s+", r"\s+và\s+", r"\s+and\s+", r"\s+with\s+"):
            parts = re.split(sep, nat_body, maxsplit=1, flags=re.I)
            if len(parts) == 2:
                t1, t2 = parts[0].strip(" ,;"), parts[1].strip(" ,;")
                t1 = re.sub(r"^(?:nghiên cứu|bài báo|công trình)\s+(?:của\s+)?", "", t1, flags=re.I).strip()
                t2 = re.sub(r"^(?:nghiên cứu|bài báo|công trình)\s+(?:của\s+)?", "", t2, flags=re.I).strip()
                t1 = re.sub(r"^(?:hiệu quả|tác động|ảnh hưởng|vai trò)\s+của\s+", "", t1, flags=re.I).strip()
                t2 = re.sub(r"^(?:hiệu quả|tác động|ảnh hưởng|vai trò)\s+của\s+", "", t2, flags=re.I).strip()
                if (
                    len(t1) >= 3
                    and len(t2) >= 3
                    and not re.match(r"^(?:các|những|hai|ba)\s+(?:nghiên cứu|tài liệu|bài báo|phương pháp|rối loạn|liệu pháp)\b", t1, re.I)
                ):
                    return {
                        "route": "cross_article_comparison",
                        "num_targets": 2,
                        "sub_queries": [t1, t2],
                        "quota_per_target": 4,
                        "comparison_focus": nat_focus,
                    }

    # Hỗ trợ câu hỏi đối chiếu tự nhiên dạng "X khác Y ở điểm nào / thế nào / ra sao?" hoặc "X và Y khác nhau thế nào?"
    m_khac = re.match(
        r"^(.{3,80}?)\s+(?:khác(?:\s+với|\s+nhau)?|và\s+(.{3,80}?)\s+khác\s+nhau)\s+"
        r"(?:(.{3,80}?)\s+)?(?:ở\s+(?:điểm|chỗ)\s+nào|ở\s+đâu|như\s+thế\s+nào|thế\s+nào|ra\s+sao)\s*[?.!]*$",
        query.strip(),
        flags=re.I,
    )
    if m_khac:
        t1_k = (m_khac.group(1) or "").strip(" ,;?.!")
        t2_k = (m_khac.group(2) or m_khac.group(3) or "").strip(" ,;?.!")
        if len(t1_k) >= 3 and len(t2_k) >= 3:
            return {
                "route": "cross_article_comparison",
                "num_targets": 2,
                "sub_queries": [t1_k, t2_k],
                "quota_per_target": 4,
                # Song ngữ để truy xuất tiếng Anh cũng khớp (trước đây chỉ có chuỗi tiếng Việt cố định).
                "comparison_focus": "differences điểm khác biệt",
            }

    return {
        "route": "single_focus",
        "num_targets": 1,
        "sub_queries": [query],
        "quota_per_target": 5,
    }


def _resolve_explicit_title_scope(query: str, db: Session) -> list[str] | None:
    """Resolve a quoted paper title to document IDs so retrieval can search within that paper.

    This only narrows retrieval when the user explicitly names a sufficiently long title and
    the title resolves unambiguously in the document catalog. It does not use benchmark gold IDs.
    """
    # Quoted titles in a comparison are hints, not a scope constraint: narrowing
    # to the first named paper would remove the other requested study entirely.
    if re.search(r"\b(?:so sánh|đối chiếu|giữa hai nghiên cứu|từ hai nghiên cứu)\b", query, re.I) or re.search(r"nghiên cứu\s+[“\"].+?[”\"]\s+và\s+[A-Z][A-Za-z0-9. -]+", query, re.I):
        return None
    quoted_titles = re.findall(r'[“"]([^”"]{12,})[”"]', query)
    quoted_titles.extend(re.findall(r"‘([^’]{12,})’", query))
    for title in quoted_titles:
        title = title.strip()
        if not title:
            continue
        try:
            rows = db.execute(text("""
                SELECT id::text AS id
                FROM documents
                WHERE title ILIKE :pattern
                ORDER BY CASE WHEN lower(title) = lower(:exact_title) THEN 0 ELSE 1 END
                LIMIT 5
            """), {"pattern": f"%{title}%", "exact_title": title}).fetchall()
        except Exception as exc:
            logger.debug("Explicit-title lookup unavailable: %s", exc)
            return None
        ids = list(dict.fromkeys(str(row.id) for row in rows))
        if ids:
            return ids

    # Resolve distinctive study names (for example, an acronym with a version)
    # only when the catalog has exactly one title containing that whole token.
    # Broad words and acronyms with multiple matches never constrain retrieval.
    names = re.findall(r"\b[A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*\b", query)
    for name in sorted(set(names), key=len, reverse=True):
        # Bỏ qua từ viết tắt ngắn toàn chữ hoa (dễ mơ hồ) thay vì danh sách viết cứng.
        if len(name) < 5 or (name.isupper() and len(name) <= 5):
            continue
        try:
            rows = db.execute(text("""
                SELECT id::text AS id, title
                FROM documents
                WHERE title ILIKE :pattern
                LIMIT 20
            """), {"pattern": f"%{name}%"}).fetchall()
        except Exception as exc:
            logger.debug("Named-study lookup unavailable: %s", exc)
            return None
        exact = [row for row in rows if re.search(rf"\b{re.escape(name)}\b", row.title or "", re.I)]
        if len(exact) == 1:
            return [str(exact[0].id)]
    return None


def compute_epistemic_uncertainty_metrics(
    chunks: list[dict],
    crag_score: float = 0.85,
    dcsr_conf: float = 0.90,
) -> dict:
    """Định lượng Độ Bất định Nhận thức & Entropy Bằng chứng Shannon (Epistemic Uncertainty Quantification):
    - Phân phối xác suất hậu nghiệm trên K đoạn trích:
        P(c_k | q) = exp(s_k / tau) / sum_j exp(s_j / tau)
    - Entropy Thông tin Shannon:
        H(q) = - sum_{k=1}^K P(c_k | q) * log2(P(c_k | q))  [bits]
    - Độ Bất định Nhận thức Chuẩn hóa:
        U_epistemic(q) in [0, 1] kết hợp H_norm(q) = H(q)/log2(K) và biên độ tin cậy CRAG/DCSR.
    - Chỉ số Đa dạng Nguồn Gini-Simpson:
        D_source = 1 - sum_d (n_d / K)^2

    LƯU Ý PHƯƠNG PHÁP: s_k là các điểm heuristic không cùng thang đo (rerank, rrf×40, memory×0.35)
    và tau = 0.42 đặt thủ công, nên P(c_k|q) chỉ là trọng số chuẩn hóa softmax, KHÔNG phải xác suất
    hậu nghiệm đã hiệu chuẩn; U_epistemic là chỉ số phân tán heuristic, không phải độ bất định đã kiểm định.
    """
    if not chunks:
        return {
            "shannon_entropy_bits": 0.0,
            "max_entropy_bits": 0.0,
            "normalized_entropy": 1.0,
            "epistemic_uncertainty": 0.85,
            "epistemic_level": "HIGH",
            "epistemic_label": "Bất định nhận thức cao (Thiếu ngữ cảnh thực chứng)",
            "source_diversity_index": 0.0,
            "chunk_probabilities": [],
        }

    k_len = len(chunks)
    raw_scores: list[float] = []
    for idx, c in enumerate(chunks):
        if c.get("rerank_score_available") and c.get("rerank_score") is not None:
            s = float(c["rerank_score"])
        elif c.get("rrf_score") and float(c["rrf_score"]) > 0:
            s = float(c["rrf_score"]) * 40.0
        elif c.get("memory_score") is not None:
            s = float(c["memory_score"]) * 0.35
        else:
            s = max(0.2, 1.0 - idx * 0.14)
        raw_scores.append(s)

    max_s = max(raw_scores) if raw_scores else 1.0
    tau = 0.42
    exps = [math.exp((s - max_s) / tau) for s in raw_scores]
    sum_exp = sum(exps) or 1.0
    probs = [e / sum_exp for e in exps]

    h_bits = -sum(p * math.log2(max(p, 1e-12)) for p in probs)
    max_h = math.log2(k_len) if k_len >= 2 else 1.0
    norm_h = min(1.0, max(0.0, h_bits / max(max_h, 1e-6))) if k_len >= 2 else 0.12

    # Kết hợp độ phân tán xác suất (norm_h) và phần bù độ tin cậy truy xuất (1 - max(crag, dcsr))
    conf_anchor = max(min(1.0, float(crag_score)), min(1.0, float(dcsr_conf)))
    u_epistemic = round(min(0.95, max(0.04, 0.35 * norm_h + 0.65 * (1.0 - conf_anchor))), 4)

    if u_epistemic <= 0.24:
        level = "LOW"
        label = "Bất định nhận thức thấp (Bằng chứng hội tụ vững chắc)"
    elif u_epistemic <= 0.48:
        level = "MODERATE"
        label = "Bất định nhận thức trung bình (Đa chiều quan điểm)"
    else:
        level = "HIGH"
        label = "Bất định nhận thức cao (Khuyến nghị kiểm chứng chéo)"

    # Chỉ số đa dạng nguồn Gini-Simpson trên (document_id, page_number)
    source_counts: dict[str, int] = {}
    for c in chunks:
        src_key = f"{c.get('document_id', '')}:{c.get('page_number', 1)}"
        source_counts[src_key] = source_counts.get(src_key, 0) + 1
    if k_len > 1:
        gini_simpson = round(1.0 - sum((cnt / k_len) ** 2 for cnt in source_counts.values()), 4)
    else:
        gini_simpson = 0.0

    return {
        "shannon_entropy_bits": round(h_bits, 4),
        "max_entropy_bits": round(max_h, 4),
        "normalized_entropy": round(norm_h, 4),
        "epistemic_uncertainty": u_epistemic,
        "epistemic_level": level,
        "epistemic_label": label,
        "source_diversity_index": gini_simpson,
        "chunk_probabilities": [round(p, 4) for p in probs[:6]],
    }


def _retrieve_single_pass(
    query: str,
    document_ids: list[str] | None,
    db: Session,
    top_k: int = 12,
    rerank_top_n: int = 30,
    comparison_target: bool = False,
    comparison_focus: str = "",
    defer_rerank: bool = False,
) -> list[dict]:
    import time
    t0 = time.perf_counter()
    if not document_ids:
        document_ids = _resolve_explicit_title_scope(query, db)
    safe_doc_ids = _sanitize_uuid_list(document_ids)
    # A large selection is still a restricted scope, not the entire corpus.
    # Invalid explicit IDs must not silently turn into an unrestricted search.
    if document_ids and not safe_doc_ids:
        return []
    doc_ids_str = ", ".join(f"'{did}'" for did in safe_doc_ids) if safe_doc_ids else None
    _set_hnsw_ef_search(db, 100)

    bundle_q = query
    if comparison_target and comparison_focus and len(safe_doc_ids or []) != 1 and query.endswith(comparison_focus):
        entity_only = query[: -len(comparison_focus)].strip()
        if len(entity_only) >= 4:
            bundle_q = entity_only
    abl = ablation_flags()
    bundle = get_cross_lingual_query_bundle(bundle_q)
    orig_q = bundle["orig_query"]
    trans_q = bundle["translated_query"]
    exp_terms = list(bundle["fts_expanded_terms"] or [])
    if comparison_target and comparison_focus and bundle_q != query:
        focus_bundle = get_cross_lingual_query_bundle(comparison_focus)
        focus_trans = (focus_bundle.get("translated_query") or "").strip()
        if focus_trans and trans_q and focus_trans.lower() not in trans_q.lower():
            trans_q = f"{trans_q} {focus_trans}".strip()
        for ft in (focus_bundle.get("fts_expanded_terms") or []):
            if ft not in exp_terms:
                exp_terms.append(ft)
    if not abl.use_cross_lingual:
        # Ablation: bỏ dịch/mở rộng thuật ngữ Việt→Anh, chỉ dùng câu hỏi gốc.
        trans_q = None
        exp_terms = []
        bundle = {**bundle, "translated_query": orig_q, "fts_expanded_terms": [], "fts_concept_groups": []}
    embed_queries_batch_cached([q for q in (orig_q, trans_q) if q])

    # ── 2 & 3. Parallel: vector search + BM25/FTS ─────────────────────────
    # Tiết kiệm ~30-80ms bằng cách submit đồng thời. Mỗi task tự tạo session riêng.
    # Timeout 10s: nếu 1 query quá lâu (DB lock, network), fallback sequential.
    fut_vec = _RETRIEVE_EXECUTOR.submit(_vector_search_task, orig_q, trans_q, doc_ids_str)
    fut_bm25 = (_RETRIEVE_EXECUTOR.submit(_bm25_task, orig_q, trans_q, exp_terms, safe_doc_ids, doc_ids_str)
                if abl.use_fts else None)
    try:
        vector_results = fut_vec.result(timeout=_PARALLEL_TIMEOUT)
    except (FuturesTimeoutError, Exception) as exc:
        logger.warning("Vector retrieval unavailable; continuing with FTS/BM25: %s", exc)
        vector_results = []
    if fut_bm25 is None:
        bm25_results = []
    else:
        try:
            bm25_results = fut_bm25.result(timeout=_PARALLEL_TIMEOUT)
        except (FuturesTimeoutError, Exception) as exc:
            logger.warning("FTS/BM25 retrieval unavailable; continuing with vector results: %s", exc)
            bm25_results = []

    # ── 4. Reciprocal Rank Fusion (k=60) + Semantic Margin Tie-Breaker ────
    k = 60
    rrf: dict[str, float] = {}
    for rank, row in enumerate(vector_results):
        rid = str(row.id)
        sem_bonus = float(getattr(row, "score", 0.0) or 0.0) * 0.0015
        rrf[rid] = rrf.get(rid, 0.0) + (1.0 / (rank + 1 + k)) + sem_bonus
    for rank, row in enumerate(bm25_results):
        rid = str(row.id)
        fts_bonus = 0.0014 if rank < 10 else 0.0008
        rrf[rid] = rrf.get(rid, 0.0) + (1.0 / (rank + 1 + k)) + fts_bonus

    all_unique: dict[str, object] = {}
    for row in list(vector_results) + bm25_results:
        rid = str(row.id)
        if rid not in all_unique:
            all_unique[rid] = row

    # Chỉ truy vấn metadata cho các document_id có trong candidates (tối ưu tốc độ vượt trội)
    cand_doc_ids = _sanitize_uuid_list([str(row.document_id) for row in all_unique.values()])
    doc_meta = {}
    if cand_doc_ids:
        doc_meta_rows = db.execute(
            text("SELECT id, title, authors, filename FROM documents WHERE id = ANY(CAST(:ids AS uuid[]))"),
            {"ids": cand_doc_ids},
        ).fetchall()
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
            "vector_score": round(float(getattr(all_unique[rid], "score", 0.0) or 0.0), 4),
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
        if cand_doc_counts.get(did, 0) < 3:
            diverse_cands.append(c)
            cand_doc_counts[did] = cand_doc_counts.get(did, 0) + 1
        else:
            overflow_cands.append(c)
    candidates = (diverse_cands + overflow_cands)[:rerank_top_n]
    candidate_ms = round((time.perf_counter() - t0) * 1000, 1)
    if not abl.use_rerank and not defer_rerank:
        # Ablation: không chấm lại, trả thẳng thứ hạng RRF (hoặc thứ hạng vector nếu tắt FTS).
        ordered = _dedup_same_page(sorted(candidates, key=lambda c: c["rrf_score"], reverse=True))[:top_k]
        if abl.use_parent_context:
            ordered = _enrich_parent_context(ordered, db)
        telemetry = {
            "stage_timings_ms": {"candidate_search": candidate_ms},
            "route": "single_focus",
            "num_targets": 1,
            "sub_queries": [query],
            "vector_hits": len(vector_results),
            "fts_hits": len(bm25_results),
            "rrf_k": k,
            "ablation": abl.as_dict(),
            "latency_ms": round((time.perf_counter() - t0) * 1000.0, 1),
            "chunks_count": len(ordered),
        }
        for c in ordered:
            c["_telemetry"] = telemetry
        return ordered
    if defer_rerank:
        top_rrf_cands = sorted(candidates, key=lambda c: c["rrf_score"], reverse=True)
        top_rrf_s = float(top_rrf_cands[0]["rrf_score"]) if top_rrf_cands else 0.0
        dom_ratio = (
            top_rrf_s / max(float(top_rrf_cands[1]["rrf_score"]), 1e-6)
            if len(top_rrf_cands) >= 2 else 1.35
        )
        dcsr_c = compute_dcsr_confidence(top_rrf_s)
        crag_ev = evaluate_retrieval_confidence(query, candidates[:6])
        crag_s = round(max(float(crag_ev.get("confidence", 0.0)), dcsr_c), 4)
        for c in candidates:
            c["retrieval_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            c["_telemetry"] = {
                "vector_hits": len(vector_results),
                "fts_hits": len(bm25_results),
                "top_rrf_score": round(top_rrf_s, 5),
                "dominance_ratio": round(dom_ratio, 3),
                "dcsr_confidence": round(dcsr_c, 4),
                "crag_score": crag_s,
            }
        return candidates

    # ── 5. Rerank bằng cross-encoder (FlagReranker / LLM fallback) ───────
    # Phase C #3: skip rerank nếu RRF top-1 áp đảo top-2 (confident).
    # Tiết kiệm ~200-500ms reranker cho câu hỏi factoid rõ ràng.
    from app.services.authority_scorer import prioritize_candidates_by_authority_and_density

    # Tạo câu truy vấn song ngữ cho reranker nếu có bản dịch (giúp cross-encoder match cả 2 ngôn ngữ)
    rerank_query = f"{orig_q} ({trans_q})" if (trans_q and trans_q.strip().lower() != orig_q.strip().lower()) else orig_q

    top_rrf_val = 0.0
    ratio = 1.0
    dcsr_conf = 0.0
    dcsr_skipped = False

    if len(candidates) >= 1:
        top_rrf = sorted(candidates, key=lambda c: c["rrf_score"], reverse=True)
        top_rrf_val = float(top_rrf[0]["rrf_score"])
        top_vec_s = max((float(c.get("vector_score", 0.0)) for c in candidates), default=0.0)
        pre_crag = evaluate_retrieval_confidence(query, candidates[:6], trans_query=trans_q)
        pre_overlap = float(pre_crag.get("overlap_ratio", 0.0))
        dcsr_conf = compute_dcsr_confidence(top_rrf_val)
        if len(top_rrf) >= 2:
            ratio = top_rrf_val / max(float(top_rrf[1]["rrf_score"]), 1e-6)
        else:
            ratio = 1.50

        # Out-of-domain Gate: Khi tìm trên kho dữ liệu thực tế nhưng hoàn toàn không khớp từ khóa (FTS=0, overlap=0)
        # và điểm tương đồng ngữ nghĩa đa ngữ thấp (< 0.805), từ chối ngay để báo "Không có thông tin".
        if not comparison_target and len(vector_results) >= 10 and (
            (len(bm25_results) == 0 and pre_overlap == 0.0 and top_vec_s < _OOD_MIN_VECTOR_NO_LEXICAL)
            or (abl.use_cross_lingual and not bundle.get("fts_concept_groups") and bundle.get("orig_lang") == "vi" and pre_overlap == 0.0 and top_vec_s < _OOD_MIN_VECTOR_NO_DICTIONARY)
        ):
            return []

        fast_skip_ready = (
            (len(vector_results) < 10 and ratio >= 1.012 and dcsr_conf >= 0.35)
            or (top_rrf_val >= 0.033 and ratio >= 1.35 and dcsr_conf >= _DCSR_CONF_THRESHOLD and pre_overlap >= 0.85)
        )
        if not comparison_target and len(candidates) >= 2 and fast_skip_ready:
            dcsr_skipped = True
            for c in top_rrf:
                c["dcsr_confidence"] = round(dcsr_conf, 4)
                c["dcsr_skip"] = True
            eff_fast_k = top_k
            prioritized = (prioritize_candidates_by_authority_and_density(top_rrf, query, trans_query=trans_q, top_k=eff_fast_k)
                           if abl.use_density_priority else _dedup_same_page(top_rrf)[:eff_fast_k])
            enriched = _include_top_document_abstracts(
                _enrich_parent_context(prioritized, db) if abl.use_parent_context else prioritized, db, eff_fast_k)
            if not abl.fixed_depth:
                enriched = _filter_low_relevance(enriched, min_keep=1)
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)
            crag_eval = evaluate_retrieval_confidence(query, enriched, trans_query=trans_q)
            crag_s2 = round(max(float(crag_eval.get("confidence", 0.0)), dcsr_conf), 4)
            epistemic_metrics = compute_epistemic_uncertainty_metrics(enriched, crag_s2, dcsr_conf)
            telemetry = {
                "memory_tier": "L2_DEEP_HYBRID",
                "route": "single_focus",
                "num_targets": 1,
                "sub_queries": [query],
                "quota_per_target": top_k,
                "vector_hits": len(vector_results),
                "fts_hits": len(bm25_results),
                "rrf_k": k,
                "top_rrf_score": round(top_rrf_val, 5),
                "dominance_ratio": round(ratio, 3),
                "dcsr_confidence": round(dcsr_conf, 4),
                "dcsr_fast_skip": True,
                "crag_score": crag_s2,
                "crag_threshold": _CRAG_THRESHOLD,
                "crag_passed": crag_s2 >= _CRAG_THRESHOLD,
                "latency_ms": elapsed_ms,
                "chunks_count": len(enriched),
                "unique_docs": len({c.get("document_id") for c in enriched if c.get("document_id")}),
                **epistemic_metrics,
            }
            for c in enriched:
                c["_telemetry"] = telemetry
            return enriched

    # Nếu reranker fail (model chưa tải) thì vẫn trả candidates theo RRF.
    rerank_start = time.perf_counter()
    try:
        from app.services.reranker import rerank
        target_query = (query if (not comparison_focus or query.endswith(comparison_focus)) else f"{query} {comparison_focus}".strip()) if comparison_target else query
        ranked = rerank(target_query, candidates, top_n=top_k * 2,
                        trans_query=trans_q,
                        force_score=comparison_target)
        if not ranked:
            ranked = candidates
    except Exception:
        ranked = candidates

    rerank_ms = round((time.perf_counter() - rerank_start) * 1000, 1)
    requested_top_k = top_k
    # Reduce generation context only for short, single-facet questions whose
    # scored evidence has a clear leader; preserve budget for synthesis.
    if not comparison_target and not abl.fixed_depth:
        top_k = adaptive_context_budget(query, ranked, top_k)

    # ── 6. Ưu tiên tài liệu Uy tín nhất và Giàu thông tin đúng chủ đề nhất ──
    prioritized = (prioritize_candidates_by_authority_and_density(ranked, query, trans_query=trans_q, top_k=top_k)
                   if abl.use_density_priority else _dedup_same_page(ranked)[:top_k])

    # Nâng cấp Parent-Child Chunking: Lấy ngữ cảnh toàn trang / section bao quát cho các chunk hàng đầu
    enriched = _include_top_document_abstracts(
        _enrich_parent_context(prioritized, db) if abl.use_parent_context else prioritized, db, top_k)
    if not abl.fixed_depth:
        enriched = _filter_low_relevance(enriched, min_keep=1)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)
    crag_eval = evaluate_retrieval_confidence(query, enriched, trans_query=trans_q)
    has_rerank = any(c.get("rerank_score_available") for c in enriched)
    top_rerank_s = max(
        (float(c.get("rerank_score", 0.0)) for c in enriched if c.get("rerank_score_available")),
        default=0.0,
    )
    if has_rerank:
        # Khi đã có điểm Cross-Encoder thực tế (BAAI/bge-reranker-v2-m3), ưu tiên tín hiệu reranker
        # thay vì để điểm RRF thô (dcsr_conf) che lấp các câu hỏi ngoài miền (out-of-domain).
        if not comparison_target and len(vector_results) >= 10 and top_rerank_s < _OOD_MIN_RERANK and float(crag_eval.get("overlap_ratio", 0.0)) == 0.0:
            return []
        dcsr_conf = round(min(1.0, max(top_rerank_s, float(crag_eval.get("confidence", 0.0)))), 4)
        crag_s2 = round(max(float(crag_eval.get("confidence", 0.0)), top_rerank_s), 4)
    else:
        crag_s2 = round(max(float(crag_eval.get("confidence", 0.0)), dcsr_conf), 4)
    epistemic_metrics = compute_epistemic_uncertainty_metrics(enriched, crag_s2, dcsr_conf)
    telemetry = {
        "stage_timings_ms": {"candidate_search": candidate_ms, "rerank": rerank_ms},
        "context_budget": top_k,
        "requested_context_budget": requested_top_k,
        "memory_tier": "L2_DEEP_HYBRID",
        "route": "single_focus",
        "num_targets": 1,
        "sub_queries": [query],
        "quota_per_target": top_k,
        "vector_hits": len(vector_results),
        "fts_hits": len(bm25_results),
        "rrf_k": k,
        "top_rrf_score": round(top_rrf_val, 5),
        "dominance_ratio": round(ratio, 3),
        "dcsr_confidence": round(dcsr_conf, 4),
        "dcsr_fast_skip": False,
        "crag_score": crag_s2,
        "crag_threshold": _CRAG_THRESHOLD,
        "crag_passed": crag_s2 >= _CRAG_THRESHOLD,
        "latency_ms": elapsed_ms,
        "chunks_count": len(enriched),
        "unique_docs": len({c.get("document_id") for c in enriched if c.get("document_id")}),
        **epistemic_metrics,
    }
    for c in enriched:
        c["_telemetry"] = telemetry
    return enriched


def adaptive_context_budget(query, chunks, requested):
    if len(query.split()) > 18 or re.search(r"so sánh|đối chiếu|tổng hợp|compare|contrast|synthesi|\band\b|\bvà\b", query, re.I):
        return requested
    scores = sorted((float(c["rerank_score"]) for c in chunks if c.get("rerank_score_available")), reverse=True)
    if len(scores) >= 2 and scores[0] >= 0.75 and scores[0] - scores[1] >= 0.2:
        return min(requested, 6)
    return requested


def retrieve(
    query: str,
    document_ids: list[str] | None,
    db: Session,
    top_k: int = 12,
    rerank_top_n: int = 30,
) -> list[dict]:
    """Task-Adaptive Hybrid Retrieval (Vector + lexical → RRF → DCSR / Rerank) với
    phân rã truy vấn đa tài liệu và phân bổ hạn ngạch công bằng (Quota-Balanced Sub-Query Decomposition, Eq. 9).
    """
    import time
    t0 = time.perf_counter()
    route_info = classify_and_decompose_query(query)
    from app.services.facet_reranker import requested_facets, rerank_by_facets
    abl = ablation_flags()
    if not abl.use_subquery and route_info["num_targets"] > 1:
        # Ablation: không phân rã, xử lý câu so sánh như một truy vấn đơn.
        route_info = {**route_info, "num_targets": 1, "sub_queries": [query]}
    facets = requested_facets(query, route_info["num_targets"] > 1) if abl.use_facet_rerank else []
    if top_k <= 0:
        return []
    if route_info["num_targets"] <= 1:
        if len(facets) < 2:
            return _retrieve_single_pass(query, document_ids, db, top_k=top_k, rerank_top_n=rerank_top_n)
        candidates = _retrieve_single_pass(query, document_ids, db, top_k=top_k,
                                          rerank_top_n=rerank_top_n, defer_rerank=True)
        ranked = _dedup_same_page(rerank_by_facets([(query, candidates)], facets, top_n=top_k * 2)[0])[:top_k]
        enriched = _enrich_parent_context(ranked, db) if abl.use_parent_context else ranked
        if not abl.fixed_depth:
            enriched = _filter_low_relevance(enriched, min_keep=1)
        telemetry = dict(candidates[0].get("_telemetry", {})) if candidates else {}
        epistemic_f = compute_epistemic_uncertainty_metrics(
            enriched,
            float(telemetry.get("crag_score", 0.0)),
            float(telemetry.get("dcsr_confidence", 0.0)),
        )
        telemetry.update(route="single_focus", num_targets=1, sub_queries=[query],
                         requested_facets=facets, facet_rerank=True,
                         dcsr_fast_skip=False,
                         chunks_count=len(enriched), latency_ms=round((time.perf_counter() - t0) * 1000, 1),
                         **epistemic_f)
        for c in enriched:
            c["_telemetry"] = telemetry
        return enriched

    sub_queries = route_info["sub_queries"]
    comparison_focus = route_info.get("comparison_focus") or query
    if not route_info.get("comparison_focus"):
        for target in sub_queries:
            comparison_focus = re.sub(re.escape(target), " ", comparison_focus, flags=re.I)
        comparison_focus = re.sub(r"\b(?:so sánh|đối chiếu|phân biệt|sự khác biệt|giữa|compare|contrast|nghiên cứu|study|và|and|với|with)\b|[()|'\"]", " ", comparison_focus, flags=re.I)
        comparison_focus = re.sub(r"\s+", " ", comparison_focus).strip(" ,.:;?-")
    quota = max(route_info["quota_per_target"], (top_k + len(sub_queries) - 1) // len(sub_queries))
    per_sub_lists: list[list[dict]] = []
    sub_telemetries: list[dict] = []
    # Independent sessions and a separate executor avoid sharing request state
    # or deadlocking the vector/FTS executor used inside each search.
    sq_bundles = {sq: get_cross_lingual_query_bundle(sq) for sq in sub_queries}
    batch_embed_qs: list[str] = []
    for sq in sub_queries:
        b_sq = sq_bundles[sq]
        if b_sq.get("orig_query"):
            batch_embed_qs.append(b_sq["orig_query"])
        if b_sq.get("translated_query"):
            batch_embed_qs.append(b_sq["translated_query"])
    try:
        embed_queries_batch_cached(batch_embed_qs)
    except Exception:
        pass
    futures = [_TARGET_EXECUTOR.submit(contextvars.copy_context().run, _retrieve_study_candidates, sq,
                                       comparison_focus, document_ids, rerank_top_n) for sq in sub_queries]
    _GENERIC_COMP_STOP = {
        "disorder", "disorders", "syndrome", "therapy", "treatment", "intervention",
        "clinical", "children", "child", "adult", "adults", "patients", "patient",
        "study", "studies", "research", "mental", "health", "psychological", "psychology",
        "roi", "loan", "benh", "chung", "lieu", "phap", "dieu", "tri", "tre", "nguoi",
        "rối", "loạn", "bệnh", "chứng", "liệu", "pháp", "điều", "trị", "trẻ", "người", "học", "tâm", "nhân", "cách",
    }
    candidate_groups = []
    deadline = time.perf_counter() + _PARALLEL_TIMEOUT
    for sq, future in zip(sub_queries, futures):
        try:
            candidates = future.result(timeout=max(0, deadline - time.perf_counter()))
        except Exception as exc:
            future.cancel()
            logger.warning("Study retrieval unavailable for target: %s", type(exc).__name__)
            candidates = []
        sq_ent_bundle = sq_bundles.get(sq) or get_cross_lingual_query_bundle(sq)
        trans_sq_ent = sq_ent_bundle.get("translated_query") or ""
        pre_ent_tokens = {
            tok.lower()
            for tok in re.findall(r"[A-Za-zÀ-ỹ0-9]{3,}", f"{sq} {trans_sq_ent}")
            if tok.lower() not in _GENERIC_COMP_STOP
        }
        if pre_ent_tokens and len(candidates) > 2:
            ent_matched = [
                c for c in candidates
                if any(t in f"{c.get('doc_title', '')} {c.get('content', '')}".lower() for t in pre_ent_tokens)
            ]
            if len(ent_matched) >= max(quota, 3):
                candidates = ent_matched
        bilingual_sq = (
            f"{sq} ({trans_sq_ent}) - {comparison_focus[:90]}".strip(" -")
            if (trans_sq_ent and trans_sq_ent.strip().lower() != sq.strip().lower())
            else f"{sq} {comparison_focus}".strip()
        )
        candidate_groups.append((bilingual_sq, candidates))
    search_ms = round((time.perf_counter() - t0) * 1000, 1)
    from app.services.reranker import rerank_groups
    rerank_start = time.perf_counter()
    ranked_groups = (rerank_by_facets(candidate_groups, facets, top_n=max(quota * 2, len(facets)))
                     if len(facets) > 1 else rerank_groups(candidate_groups, top_n=max(quota * 2, 6)))
    rerank_ms = round((time.perf_counter() - rerank_start) * 1000, 1)
    for sq, ranked in zip(sub_queries, ranked_groups):
        has_scored_rerank = any(c.get("rerank_score_available") for c in ranked)
        if ranked:
            t_meta = dict(ranked[0].get("_telemetry", {}))
            top_rerank = max(
                (float(c.get("rerank_score", 0.0)) for c in ranked if c.get("rerank_score_available")),
                default=0.0,
            )
            if top_rerank > 0:
                t_meta["crag_score"] = round(max(float(t_meta.get("crag_score", 0.0)), top_rerank), 4)
                t_meta["dcsr_confidence"] = round(max(float(t_meta.get("dcsr_confidence", 0.0)), top_rerank * 0.95), 4)
            sub_telemetries.append(t_meta)
        if has_scored_rerank and abl.use_density_priority:
            from app.services.authority_scorer import prioritize_candidates_by_authority_and_density
            sq_ent_b = sq_bundles.get(sq) or get_cross_lingual_query_bundle(sq)
            sq_tr = sq_ent_b.get("translated_query") or ""
            ent_tokens = {
                tok.lower()
                for tok in re.findall(r"[A-Za-zÀ-ỹ0-9]{3,}", f"{sq} {sq_tr}")
                if tok.lower() not in _GENERIC_COMP_STOP
            }
            if ent_tokens:
                any_ent_hit = any(
                    any(t in f"{c.get('doc_title', '')} {c.get('content', '')}".lower() for t in ent_tokens)
                    for c in ranked
                )
                if any_ent_hit:
                    for c in ranked:
                        blob = f"{c.get('doc_title', '')} {c.get('content', '')}".lower()
                        hits = sum(1 for t in ent_tokens if t in blob)
                        title_hit = any(t in (c.get("doc_title") or "").lower() for t in ent_tokens)
                        base_r = float(c.get("ranking_score") if c.get("ranking_score") is not None else (c.get("rerank_score") or 0.0))
                        if hits == 0:
                            c["ranking_score"] = round(base_r * 0.05, 6)
                        else:
                            boost = 1.20 if title_hit else (1.10 if hits >= 2 else 1.0)
                            c["ranking_score"] = round(min(1.0, base_r * boost + (0.085 if hits >= 2 else 0.04)), 6)
                    ranked.sort(key=lambda x: float(x.get("ranking_score") or 0.0), reverse=True)
            ranked = prioritize_candidates_by_authority_and_density(
                ranked, sq, trans_query=sq_tr, top_k=max(quota * 2, 6), max_per_doc=2
            )
            ranked = _rebalance_by_comparison_facets(ranked)
        sub_res = _enrich_parent_context(ranked, db) if abl.use_parent_context else list(ranked)
        if has_scored_rerank:
            sub_res = _include_top_document_abstracts(sub_res, db, max(quota * 2, 6))
            if not abl.fixed_depth:
                sub_res = _filter_low_relevance(sub_res, min_keep=1)
        for c in sub_res:
            c["sub_query_target"] = sq
        per_sub_lists.append(sub_res)

    # Round-robin quota-balanced interleaving with fuzzy deduplication (tau_dedup = 0.85)
    interleaved: list[dict] = []
    seen_ids: set[tuple[str, str]] = set()
    seen_pages: set[tuple[str, str]] = set()
    max_len = max((len(lst) for lst in per_sub_lists), default=0)
    for rank_idx in range(max_len):
        for lst in per_sub_lists:
            if rank_idx < len(lst):
                cand = lst[rank_idx]
                cid = (str(cand.get("id", "")), str(cand.get("sub_query_target", "")))
                if cid in seen_ids:
                    continue
                pkey = (str(cand.get("document_id")), str(cand.get("page_number")))
                if cand.get("document_id") is not None and cand.get("page_number") is not None and pkey in seen_pages:
                    continue
                txt = (cand.get("content") or "")[:500]
                if any(ex.get("sub_query_target") == cand.get("sub_query_target") and
                       _is_fuzzy_dup(txt, (ex.get("content") or "")[:500], _L1_CROSS_DOC_DEDUP_THRESHOLD)
                       for ex in interleaved):
                    continue
                seen_ids.add(cid)
                seen_pages.add(pkey)
                interleaved.append(cand)
                if len(interleaved) >= top_k:
                    break
        if len(interleaved) >= top_k:
            break

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)
    target_crag = [float(t.get("crag_score", 0.0)) for t in sub_telemetries]
    target_conf = [float(t.get("dcsr_confidence", 0.0)) for t in sub_telemetries]
    min_crag = min(target_crag) if len(target_crag) == len(sub_queries) else 0.0
    min_conf = min(target_conf) if len(target_conf) == len(sub_queries) else 0.0
    max_ratio = max((float(t.get("dominance_ratio", 1.0)) for t in sub_telemetries), default=0.0)
    max_rrf = max((float(t.get("top_rrf_score", 0.0)) for t in sub_telemetries), default=0.0)
    total_vec = sum(int(t.get("vector_hits", 0)) for t in sub_telemetries)
    total_fts = sum(int(t.get("fts_hits", 0)) for t in sub_telemetries)
    any_skip = any(bool(t.get("dcsr_fast_skip", False)) for t in sub_telemetries)
    epistemic_merged = compute_epistemic_uncertainty_metrics(interleaved, min_crag, min_conf)

    merged_telemetry = {
        "stage_timings_ms": {"parallel_search": search_ms, "batch_rerank": rerank_ms},
        "requested_facets": facets,
        "ablation": abl.as_dict(),
        "facet_rerank": len(facets) > 1,
        "score_semantics": "ranking_heuristic_not_answer_probability",
        "memory_tier": "L2_DEEP_HYBRID",
        "route": route_info["route"],
        "num_targets": route_info["num_targets"],
        "sub_queries": sub_queries,
        "quota_per_target": quota,
        "vector_hits": total_vec,
        "fts_hits": total_fts,
        "rrf_k": 60,
        "top_rrf_score": round(max_rrf, 5),
        "dominance_ratio": round(max_ratio, 3),
        "dcsr_confidence": round(min_conf, 4),
        "dcsr_fast_skip": any_skip,
        "crag_score": round(min_crag, 4),
        "crag_threshold": _CRAG_THRESHOLD,
        "crag_passed": min_crag >= _CRAG_THRESHOLD,
        "target_crag_scores": target_crag,
        "latency_ms": elapsed_ms,
        "chunks_count": len(interleaved),
        "unique_docs": len({c.get("document_id") for c in interleaved if c.get("document_id")}),
        **epistemic_merged,
    }
    for c in interleaved:
        c["_telemetry"] = merged_telemetry
    return interleaved


def _rebalance_by_comparison_facets(chunks: list[dict]) -> list[dict]:
    """Hạng mục B: Phân bổ đa chiều theo các mặt cắt nghiên cứu (Sample, Method, Measure, Finding, Limitation)
    để mỗi nghiên cứu trong câu hỏi so sánh liên bài đều mang đầy đủ dữ kiện PICO/IMRaD vào ngữ cảnh.
    """
    if len(chunks) <= 2:
        return chunks
    from app.services.comparison_coverage import _FACETS
    seen_facets: set[str] = set()
    primary_facets: list[dict] = []
    secondary: list[dict] = []
    for c in chunks:
        txt = f"{c.get('content', '')} {c.get('parent_context', '')}"
        matched_f = None
        for fname, (_, pat) in _FACETS.items():
            if re.search(pat, txt, re.I):
                matched_f = fname
                break
        c["detected_facet"] = matched_f or "general"
        c["comparison_facet"] = matched_f or "general"
        if matched_f and matched_f not in seen_facets:
            seen_facets.add(matched_f)
            primary_facets.append(c)
        else:
            secondary.append(c)
    return primary_facets + secondary


def _retrieve_study_candidates(target, focus, document_ids, limit):
    """Resolve exact catalog identity (Title, Filename/Code, Author+Year, or Long Title Substring)
    and enrich with L1 structured memory key_facts for multi-facet comparison."""
    safe_ids = [str(i) for i in (document_ids or []) if i]
    clean_t = target.strip().strip('\"“”')
    fname_exact = clean_t if clean_t.lower().endswith(".pdf") else f"{clean_t}.pdf"
    m_ay = re.search(r"([A-ZÀ-ỹ][A-Za-zÀ-ỹ'-]{2,25})(?:\s+et\s+al\.?)?\s*(?:\(|\s*,\s*|\s+)(19[7-9]\d|20[0-2]\d)\b", clean_t)
    has_ay = bool(m_ay)
    auth_pat = f"%{m_ay.group(1)}%" if m_ay else ""
    yr_val = int(m_ay.group(2)) if m_ay else -1
    has_long_title = len(clean_t) >= 14 and not has_ay
    title_pat = f"%{clean_t}%" if has_long_title else ""

    with SessionLocal() as session:
        rows = session.execute(text("""
            SELECT id::text AS id FROM documents
            WHERE status = 'ready'
              AND (
                lower(trim(title)) = lower(:title)
                OR lower(filename) = lower(:fname_exact)
                OR (:has_ay AND authors ILIKE :auth_pat AND year = :yr_val)
                OR (:has_long_title AND title ILIKE :title_pat)
              )
              AND (:all_docs OR id::text = ANY(:ids))
            LIMIT 10
        """), {
            "title": clean_t,
            "fname_exact": fname_exact,
            "has_ay": has_ay,
            "auth_pat": auth_pat,
            "yr_val": yr_val,
            "has_long_title": has_long_title,
            "title_pat": title_pat,
            "all_docs": not safe_ids,
            "ids": safe_ids,
        }).fetchall()
        resolved = [str(r.id) for r in rows if getattr(r, "id", None)]
        scope = resolved if resolved else (safe_ids if safe_ids else None)
        chunks = _retrieve_single_pass(f"{target} {focus}", scope, session,
                                      rerank_top_n=limit, comparison_target=True, comparison_focus=focus, defer_rerank=True)
        # Hạng mục B: Bổ sung key_facts từ Bộ nhớ Tầng 1 (document_summaries) cho tài liệu đại diện của nhánh so sánh
        if chunks and isinstance(chunks, list):
            try:
                rep_doc_ids = resolved[:1] if resolved else list(dict.fromkeys(str(c.get("document_id")) for c in chunks[:2] if c.get("document_id")))[:1]
                if rep_doc_ids:
                    mem_row = session.execute(
                        text("SELECT document_id::text AS did, key_facts FROM document_summaries WHERE document_id = CAST(:did AS uuid) AND memory_status = 'ready'"),
                        {"did": rep_doc_ids[0]},
                    ).first()
                    if mem_row and getattr(mem_row, "key_facts", None):
                        doc_info = next((c for c in chunks if str(c.get("document_id")) == rep_doc_ids[0]), {})
                        existing_pages = {int(c.get("page_number") or 1) for c in chunks[:4]}
                        added_mem = 0
                        for kf in mem_row.key_facts:
                            claim = (kf.get("claim") or "").strip()
                            pno = int(kf.get("page") or 1)
                            if not claim or len(claim) < 45:
                                continue
                            if pno not in existing_pages or re.search(r"\b(?:N\s*=|p\s*[<=>]|d\s*=|r\s*=|method|sample|scale|result)\b", claim, re.I):
                                chunks.insert(min(2 + added_mem, len(chunks)), {
                                    "id": f"l1comp-{rep_doc_ids[0]}-{pno}-{added_mem}",
                                    "content": claim,
                                    "page_number": pno,
                                    "document_id": rep_doc_ids[0],
                                    "rrf_score": round(float(doc_info.get("rrf_score") or 0.0), 6),
                                    "vector_score": round(float(doc_info.get("vector_score") or 0.0), 4),
                                    "score_source": "inherited_from_rep_chunk",
                                    "doc_title": doc_info.get("doc_title", ""),
                                    "doc_authors": doc_info.get("doc_authors", ""),
                                    "doc_filename": doc_info.get("doc_filename", ""),
                                    "from_memory": True,
                                })
                                added_mem += 1
                                if added_mem >= 2:
                                    break
            except Exception:
                pass
        for c in chunks:
            c["target_identity"] = "exact_title" if len(resolved) == 1 else "unresolved"
            c["sub_query_target"] = target
        return chunks


def _filter_low_relevance(chunks: list[dict], min_keep: int = 1) -> list[dict]:
    """Bỏ các đoạn có điểm xếp hạng thấp hơn _RELATIVE_RELEVANCE_MIN × điểm cao nhất.

    Chỉ áp dụng khi danh sách có điểm chấm lại (rerank) để so sánh; đoạn không có điểm (vd. key_facts
    từ bộ nhớ) được giữ nguyên. Luôn giữ tối thiểu `min_keep` đoạn đầu để không làm rỗng ngữ cảnh.
    """
    if not chunks or not any(c.get("rerank_score_available") or c.get("composite_priority_score") is not None for c in chunks):
        return chunks

    def _score(c: dict) -> float | None:
        if c.get("ranking_score") is not None:
            return float(c["ranking_score"])
        if c.get("rerank_score_available"):
            return float(c.get("rerank_score") or 0.0)
        if c.get("composite_priority_score") is not None:
            return float(c["composite_priority_score"])
        return None

    scores = [sc for sc in (_score(c) for c in chunks) if sc is not None]
    best = max(scores, default=0.0)
    if best <= 0:
        return chunks
    cutoff = best * _RELATIVE_RELEVANCE_MIN
    kept = [c for c in chunks if _score(c) is None or _score(c) >= cutoff]
    if len(kept) < min_keep:
        kept = chunks[:min_keep]
    for c in kept:
        c["relevance_cutoff"] = round(cutoff, 6)
    return kept


def _dedup_same_page(chunks: list[dict]) -> list[dict]:
    """Giữ đoạn xếp hạng cao nhất cho mỗi (tài liệu, trang).

    Ngữ cảnh toàn trang (parent context) đã bao trùm các đoạn khác cùng trang, nên các bản trùng
    chỉ chiếm chỗ trong top-k. Đoạn không có document_id/page_number được giữ nguyên.
    """
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for c in chunks or []:
        did, pg = c.get("document_id"), c.get("page_number")
        if did is None or pg is None:
            out.append(c)
            continue
        key = (str(did), str(pg))
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _include_top_document_abstracts(chunks: list[dict], db: Session, top_k: int) -> list[dict]:
    """Giữ nguyên danh sách các trang nội dung thực sự được truy xuất trên toàn bộ PDF.
    Không tự ý chèn ép Trang 1 (Title/Abstract) làm đẩy các trang nội dung chuyên sâu (Trang 2..N) ra khỏi top_k.
    """
    return _dedup_same_page(chunks or [])[:top_k]



def _enrich_parent_context(chunks: list[dict], db: Session) -> list[dict]:
    """Parent-Child Hierarchical Context Enrichment:
    Đối với các chunk được xếp hạng cao nhất (Child Chunks - dùng để tìm kiếm chính xác),
    truy vấn kho văn bản toàn trang (page_texts) để mở rộng ngữ cảnh bao quát (Parent Context).
    Giúp LLM nắm trọn vẹn luận điểm khoa học xung quanh mà không bị đứt đoạn câu từ.
    """
    if not chunks:
        return chunks

    doc_page_pairs = set()
    for c in chunks:
        did = c.get("document_id")
        pnum = c.get("page_number")
        if did and pnum:
            try:
                u_str = str(uuid.UUID(str(did)))
                doc_page_pairs.add((u_str, int(pnum)))
            except (ValueError, TypeError):
                continue

    if not doc_page_pairs:
        return chunks

    pair_list = sorted(doc_page_pairs)
    bind_params = {f"k{idx}_{col}": val for idx, (d, p) in enumerate(pair_list) for col, val in (("d", d), ("p", int(p)))}
    conditions = " OR ".join([f"(document_id = CAST(:k{idx}_d AS uuid) AND page_number = :k{idx}_p)" for idx in range(len(pair_list))])
    try:
        rows = db.execute(text(f"""
            SELECT document_id, page_number, content 
            FROM page_texts 
            WHERE {conditions}
        """), bind_params).fetchall()
        page_map = {(str(r.document_id), r.page_number): r.content for r in rows}

        for c in chunks:
            key = (str(c.get("document_id")), c.get("page_number"))
            parent_text = page_map.get(key)
            if parent_text:
                if is_reference_content(parent_text):
                    c["parent_context"] = c["content"]
                    continue
                # Làm sạch phần References nếu xuất hiện trên trang và phần Title/Author ở Trang 1
                cleaned_parent = clean_reference_boundary(parent_text)
                if str(c.get("page_number")) == "1":
                    cleaned_parent = clean_front_matter_header(cleaned_parent)
                if not cleaned_parent:
                    c["parent_context"] = c["content"]
                    continue
                # Loại bỏ nhãn [Trang X] ở đầu chunk trước khi tìm vị trí trong page_texts
                clean_chunk_text = re.sub(r"^\s*\[Trang\s+\d+\]\s*", "", c.get("content", ""))
                c_snippet = clean_chunk_text[:80].strip()
                pos = cleaned_parent.find(c_snippet) if c_snippet else -1
                if pos >= 0:
                    chunk_end = pos + len(clean_chunk_text)
                    start_pos = max(0, pos - 250)
                    end_pos = min(len(cleaned_parent), max(chunk_end + 500, start_pos + 1300))
                    if end_pos - start_pos > 1300:
                        end_pos = start_pos + 1300
                    c["parent_context"] = cleaned_parent[start_pos:end_pos].strip()
                else:
                    c["parent_context"] = c["content"]
            else:
                c["parent_context"] = c["content"]
    except Exception as e:
        logger.warning("Parent context enrichment failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        for c in chunks:
            c["parent_context"] = c["content"]

    return chunks


def evaluate_retrieval_confidence(query: str, chunks: list[dict], trans_query: str | None = None) -> dict:
    """Corrective RAG (CRAG) Evaluator:
    Đánh giá độ tin cậy và chất lượng thông tin của các chunks trích xuất được (hỗ trợ đa ngữ & Cross-Encoder).
    - score >= 0.60: High confidence (Correct) -> Sử dụng trực tiếp ngữ cảnh tài liệu
    - 0.35 <= score < 0.60: Ambiguous -> Cần bổ sung ngữ cảnh / web search nếu cho phép
    - score < 0.35: Incorrect / Out-of-domain -> Kích hoạt Safe Refusal hoặc Web Fallback
    """
    if not chunks:
        return {"confidence": 0.0, "status": "incorrect", "action": "refusal"}

    top_rrf = max((float(c.get("rrf_score", 0.0)) for c in chunks), default=0.0)
    top_rerank = max(
        (float(c.get("rerank_score", 0.0)) for c in chunks if c.get("rerank_score_available")),
        default=0.0,
    )
    q_words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2 and w.lower() not in _VI_STOPWORDS]
    if not q_words:
        q_words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
    context_text = " ".join([c.get("content", "").lower() for c in chunks[:4]])
    context_words = set(re.findall(r"\w+", context_text))

    matched_words = [w for w in q_words if w in context_words]
    overlap_ratio = len(matched_words) / max(len(q_words), 1)

    if trans_query and trans_query.strip().lower() != query.strip().lower():
        t_words = [w.lower() for w in re.findall(r"\w+", trans_query) if len(w) > 2 and w.lower() not in _VI_STOPWORDS]
        if t_words:
            t_matched = [w for w in t_words if w in context_words]
            overlap_ratio = max(overlap_ratio, len(t_matched) / len(t_words))

    # Chuẩn hóa điểm RRF theo ngưỡng lý thuyết 2/(60+1) = 0.032787 và kết hợp Cross-Encoder score nếu có
    has_rerank = any(c.get("rerank_score_available") for c in chunks)
    rrf_norm = min(1.0, top_rrf * 30.5)
    rank_signal = top_rerank if has_rerank else max(rrf_norm, top_rerank)
    confidence = round(min(1.0, rank_signal * 0.65 + overlap_ratio * 0.35), 3)

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
        "overlap_ratio": round(overlap_ratio, 4),
        "matched_terms": matched_words,
        "query_terms_count": len(q_words),
    }


_VI_STOPWORDS = {
    'la', 'va', 'cua', 'trong', 'cac', 'nhung', 'co', 'duoc', 'cho', 'voi', 've',
    'nhu', 'khi', 'tu', 'tai', 'theo', 'de', 'nay', 'do', 'ra', 'vao', 'tren',
    'duoi', 'mot', 'hai', 'ba', 'bon', 'nam', 'qua', 'lai', 'da', 'dang', 'se',
    'sao', 'gi', 'the', 'nao', 'hay', 'biet', 'phat', 'hien', 'chinh', 'cach',
    'nhat', 'bao', 'nhieu', 'hom', 'nay', 'nguoi', 'hon', 'long',
    'là', 'và', 'của', 'trong', 'các', 'những', 'có', 'được', 'cho', 'với', 'về',
    'như', 'khi', 'từ', 'tại', 'theo', 'để', 'này', 'đó', 'ra', 'vào', 'trên',
    'dưới', 'đã', 'đang', 'sẽ', 'sao', 'gì', 'thế', 'nào', 'hãy', 'biết', 'phát', 'hiện', 'chính',
    'cách', 'nhất', 'bao', 'nhiêu', 'hôm', 'người', 'nhiều', 'hơn',
    'công', 'thức', 'gia', 'truyền', 'giá', 'món', 'nấu', 'vàng', 'cong', 'thuc', 'truyen', 'mon', 'nau', 'vang',
    # English stopwords & question fillers
    'what', 'is', 'are', 'was', 'were', 'how', 'why', 'when', 'where', 'who', 'which',
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'about', 'into', 'does', 'did',
    'can', 'could', 'would', 'should', 'have', 'has', 'had', 'main', 'findings', 'finding',
    'between', 'among', 'on', 'in', 'at', 'to', 'of', 'by', 'an', 'as', 'or', 'be'
}


def _bm25_search(
    query: str,
    trans_query: str | None,
    expanded_terms: list[str] | None,
    document_ids: list[str],
    doc_ids_str: str,
    db: Session,
) -> list:
    """Lexical routing (legacy function name retained for callers).

    USE_FTS=1 selects PostgreSQL ts_rank_cd on a GIN index, not BM25.
    USE_FTS=0 or an exception escaping FTS selects in-memory BM25Okapi.
    Empty FTS results do not themselves trigger the BM25 fallback.
    """
    words = re.findall(r"\w+", query.lower())
    fts_terms = [w for w in words if len(w) > 2 and w not in _VI_STOPWORDS]
    if not fts_terms:
        fts_terms = [w for w in words if len(w) > 2]
    if not fts_terms and not expanded_terms and not trans_query:
        return []

    if _USE_FTS:
        try:
            return _bm25_via_fts(fts_terms, trans_query, expanded_terms, doc_ids_str, db)
        except Exception as e:
            logger.warning("PostgreSQL FTS failed, falling back to in-memory BM25: %s", e)

    # Fallback: in-memory BM25Okapi (chỉ dùng khi USE_FTS=0 hoặc bảng page_texts lỗi)
    return _bm25_in_memory(query, doc_ids_str, db)


def _bm25_via_fts(fts_terms: list[str], trans_query: str | None, expanded_terms: list[str] | None, doc_ids_str: str | None, db: Session) -> list:
    """PostgreSQL FTS (ts_rank_cd, not BM25): page hits → chunks.
    Xây dựng câu truy vấn song ngữ (Bilingual FTS): kết hợp từ khóa gốc và từ khóa đối chiếu.
    Ưu tiên tìm kiếm chính xác (AND) trước khi mở rộng.
    """
    if fts_terms:
        selected_terms = [w for t in fts_terms[:4] for w in re.findall(r"\w+", t) if w][:4]
        orig_clause = " & ".join(
            f"{t}:*" if idx == len(selected_terms) - 1 else t
            for idx, t in enumerate(selected_terms)
        )
    else:
        orig_clause = ""

    trans_clause = ""
    trans_words: list[str] = []
    if trans_query and trans_query.strip().lower() != " ".join(fts_terms).lower():
        en_stop = {
            "what", "is", "are", "how", "why", "when", "where", "who", "which",
            "the", "and", "for", "with", "that", "this", "from", "define",
            "definition", "about", "does", "did", "can", "could", "would"
        }
        vi_stop = {"la", "gi", "nhu", "the", "nao", "cua", "trong", "va", "cac", "nhung", "da", "dang", "se", "sao", "trinh", "bay", "khai", "niem", "phan", "tich", "giai", "thich", "vai", "tro"}
        orig_set = {t.lower() for t in fts_terms}
        ascii_en = [w for w in re.findall(r'\b[a-z0-9]{3,}\b', trans_query.lower()) if w not in en_stop and w not in vi_stop and w not in orig_set]
        trans_words = ascii_en if ascii_en else [w for w in re.findall(r'\b\w{2,}\b', trans_query.lower()) if w not in en_stop and w not in vi_stop]
        if trans_words:
            sel_trans = trans_words[:3]
            trans_clause = " & ".join(
                f"{t}:*" if idx == len(sel_trans) - 1 else t
                for idx, t in enumerate(sel_trans)
            )

    # 1. Thử truy vấn chính xác (AND các từ khóa gốc và từ khóa dịch)
    clauses = [f"({c})" for c in [orig_clause, trans_clause] if c]
    fts_query = " | ".join(clauses) if clauses else orig_clause

    safe_doc_sql = _sanitize_doc_ids_sql(doc_ids_str)
    doc_filter = f"AND document_id IN ({safe_doc_sql})" if safe_doc_sql else ""
    fts_rows = []
    # 0. Ưu tiên cụm từ liền kề (phrase) của 2 từ đầu bản dịch, vd. "acute <-> stress", "secure <-> attachment".
    # Tránh trường hợp chỉ khớp rời rạc từng từ (vd. "acute" và "stress" ở hai chỗ khác nhau trong bài về gan).
    if len(trans_words) >= 2:
        phrase_q = f"{trans_words[0]} <-> {trans_words[1]}"
        try:
            fts_rows = list(db.execute(text(f"""
                SELECT document_id, page_number,
                       ts_rank_cd(tsv, to_tsquery('simple', :q)) AS rank
                FROM page_texts
                WHERE tsv @@ to_tsquery('simple', :q) {doc_filter}
                ORDER BY rank DESC
                LIMIT 20
            """), {"q": phrase_q}).fetchall())
        except Exception as e:
            logger.warning("FTS phrase search error: %s", e)
            try:
                db.rollback()
            except Exception:
                pass
            fts_rows = []
    # Page position is provenance, not relevance: do not penalize late results
    # or limitations, or boost early introductory material for every question.
    if fts_query:
        try:
            main_rows = db.execute(text(f"""
                SELECT document_id, page_number,
                       ts_rank_cd(tsv, to_tsquery('simple', :q)) AS rank
                FROM page_texts
                WHERE tsv @@ to_tsquery('simple', :q) {doc_filter}
                ORDER BY rank DESC
                LIMIT 30
            """), {"q": fts_query}).fetchall()
            seen_main = {(str(r.document_id), int(r.page_number)) for r in fts_rows}
            fts_rows = fts_rows + [r for r in main_rows if (str(r.document_id), int(r.page_number)) not in seen_main]
        except Exception as e:
            logger.warning("FTS search error: %s", e)
            try:
                db.rollback()
            except Exception:
                pass

    # 1b. Nếu truy vấn AND 3 từ khóa trả về quá ít (< 3 trang), thử truy vấn cụm chủ đề chính (trans_words[0] & trans_words[1])
    if len(fts_rows) < 3 and len(trans_words) >= 2:
        core_clauses = [f"({trans_words[0]} & {trans_words[1]}:*)"]
        if len(trans_words) >= 3:
            core_clauses.append(f"({trans_words[0]} & {trans_words[2]}:*)")
        core_q = " | ".join(core_clauses)
        try:
            extra_rows = db.execute(text(f"""
                SELECT document_id, page_number,
                       ts_rank_cd(tsv, to_tsquery('simple', :q)) AS rank
                FROM page_texts
                WHERE tsv @@ to_tsquery('simple', :q) {doc_filter}
                ORDER BY rank DESC
                LIMIT 30
            """), {"q": core_q}).fetchall()
            seen_p = {(str(r.document_id), int(r.page_number)) for r in fts_rows}
            for er in extra_rows:
                pk = (str(er.document_id), int(er.page_number))
                if pk not in seen_p:
                    fts_rows.append(er)
                    seen_p.add(pk)
        except Exception as e:
            logger.warning("FTS core pair search error: %s", e)
            try:
                db.rollback()
            except Exception:
                pass

    # 2. Nếu kết quả còn ít (< 12 trang) và có expanded_terms, bổ sung fallback mở rộng
    if len(fts_rows) < 12 and expanded_terms:
        exp_tokens: list[str] = []
        for raw_term in expanded_terms[:8]:
            for tok in re.findall(r"\b[a-zA-Z0-9]{3,}\b", str(raw_term).lower()):
                if len(tok) > 2 and tok not in exp_tokens:
                    exp_tokens.append(tok)
        if not exp_tokens:
            for raw_term in expanded_terms[:6]:
                for tok in re.findall(r"\w+", str(raw_term).lower()):
                    if len(tok) > 2 and tok not in exp_tokens:
                        exp_tokens.append(tok)
        exp_words = exp_tokens[:8]
        if exp_words:
            exp_query = " | ".join(exp_words)
            try:
                more_rows = db.execute(text(f"""
                    SELECT document_id, page_number,
                           ts_rank_cd(tsv, to_tsquery('simple', :q)) AS rank
                    FROM page_texts
                    WHERE tsv @@ to_tsquery('simple', :q) {doc_filter}
                    ORDER BY rank DESC
                    LIMIT 30
                """), {"q": exp_query}).fetchall()
                seen_p2 = {(str(r.document_id), int(r.page_number)) for r in fts_rows}
                for mr in more_rows:
                    pk2 = (str(mr.document_id), int(mr.page_number))
                    if pk2 not in seen_p2:
                        fts_rows.append(mr)
                        seen_p2.add(pk2)
            except Exception as e:
                logger.warning("FTS expanded search error: %s", e)
                try:
                    db.rollback()
                except Exception:
                    pass

    if not fts_rows:
        return []

    # Map CHỈ các chunks thuộc về top matching pages thay vì tải toàn bộ DB vào RAM
    unique_pages = list({(str(r.document_id), int(r.page_number)) for r in fts_rows})
    page_bind = {f"fp{idx}_{col}": val for idx, (doc_id, p_num) in enumerate(unique_pages) for col, val in (("d", str(doc_id)), ("p", int(p_num)))}
    page_conditions = " OR ".join([f"(document_id::text = :fp{idx}_d AND page_number = :fp{idx}_p)" for idx in range(len(unique_pages))])
    try:
        matching_chunks = db.execute(text(f"""
            SELECT id, content, page_number, document_id
            FROM chunks WHERE {page_conditions}
        """), page_bind).fetchall()
    except Exception as e:
        logger.warning("FTS chunk mapping error: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return []

    if not matching_chunks:
        return []

    # Map (doc_id_str, page) → list chunks
    chunks_by_page: dict[tuple[str, int], list] = {}
    for r in matching_chunks:
        key = (str(r.document_id), r.page_number)
        chunks_by_page.setdefault(key, []).append(r)

    # Trả chunks theo thứ tự rank của trang, và trong mỗi trang ưu tiên chunk khớp từ khóa chủ đề chính
    primary_terms = set(trans_words[:4]) if trans_words else set()
    scoring_terms = set(fts_terms or [])
    if trans_query:
        scoring_terms.update(w for w in re.findall(r"\b\w{3,}\b", trans_query.lower()) if w not in _VI_STOPWORDS)
    if expanded_terms:
        for et in expanded_terms[:6]:
            scoring_terms.update(w for w in re.findall(r"\b\w{3,}\b", str(et).lower()))

    out: list = []
    seen_chunk_ids = set()
    for r in fts_rows:
        page_chunks = chunks_by_page.get((str(r.document_id), r.page_number), [])
        valid_chunks = [c for c in page_chunks if _is_valid_prose_chunk(c.content) and not is_reference_content(c.content)]
        if primary_terms:
            prim_matched = [c for c in valid_chunks if any(pt in (c.content or "").lower() for pt in primary_terms)]
            if prim_matched:
                valid_chunks = prim_matched
        if scoring_terms and len(valid_chunks) > 1:
            valid_chunks.sort(
                key=lambda c: (
                    sum(5 for pt in primary_terms if pt in (c.content or "").lower())
                    + sum(1 for t in scoring_terms if t in (c.content or "").lower())
                ),
                reverse=True,
            )
        for c in valid_chunks[:2]:
            if str(c.id) not in seen_chunk_ids:
                seen_chunk_ids.add(str(c.id))
                out.append(c)
    return out[:_CANDIDATE_LIMIT]


def _bm25_in_memory(query: str, doc_ids_str: str | None, db: Session) -> list:
    """Fallback in-memory BM25Okapi — code gốc giữ nguyên để rollback nhanh."""
    safe_doc_sql = _sanitize_doc_ids_sql(doc_ids_str)
    doc_filter = f"WHERE document_id IN ({safe_doc_sql})" if safe_doc_sql else ""
    try:
        all_chunks = db.execute(text(f"""
            SELECT id, content, page_number, document_id
            FROM chunks {doc_filter}
            LIMIT 500
        """)).fetchall()
    except Exception as e:
        logger.warning("In-memory BM25 fetch failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return []
    if not all_chunks:
        return []
    corpus = [r.content.lower().split() for r in all_chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query.lower().split())
    positive_idx = [i for i, s in enumerate(scores) if s > 0 and not is_reference_content(all_chunks[i].content)]
    if not positive_idx:
        return []
    top_idx = sorted(positive_idx, key=lambda i: scores[i], reverse=True)[
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
    safe_ids = _sanitize_uuid_list(document_ids)
    if not safe_ids:
        return None

    import time
    t0 = time.perf_counter()

    # 1. Memory availability check
    doc_ids_str = ", ".join(f"'{d}'" for d in safe_ids)
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

    if not mem_rows or len(mem_rows) != len(safe_ids):
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
    bundle_l1 = get_cross_lingual_query_bundle(query)
    trans_l1 = (bundle_l1.get("translated_query") or "").lower()
    exp_l1 = " ".join(bundle_l1.get("fts_expanded_terms") or []).lower()
    q_tokens = {w for w in re.findall(r"\w+", f"{query_lower} {trans_l1} {exp_l1}") if len(w) > 2 and w not in _VI_STOPWORDS}
    if not q_tokens:
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
    out_chunks = _cross_doc_dedup(out_chunks)[:top_k]
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)
    # Tính điểm từ chính các đoạn L1 thay vì gán hằng số (trước đây: crag 0.96, dominance 1.45, rrf 0.0328).
    l1_crag = float(evaluate_retrieval_confidence(query, out_chunks).get("confidence", 0.0))
    mem_scores = sorted((float(c.get("memory_score") or 0.0) for c in out_chunks), reverse=True)
    l1_dominance = round(mem_scores[0] / max(mem_scores[1], 1e-6), 3) if len(mem_scores) >= 2 and mem_scores[1] > 0 else 0.0
    l1_epistemic = compute_epistemic_uncertainty_metrics(out_chunks, l1_crag, l1_crag)
    l1_telemetry = {
        "memory_tier": "L1_FAST_MEMORY",
        "route": "single_focus",
        "num_targets": 1,
        "sub_queries": [query],
        "quota_per_target": top_k,
        "vector_hits": len(top_docs),
        "fts_hits": 0,
        "rrf_k": 60,
        "top_rrf_score": 0.0,
        "dominance_ratio": l1_dominance,
        "dcsr_confidence": round(l1_crag, 4),
        "dcsr_fast_skip": False,
        "crag_score": round(l1_crag, 4),
        "crag_threshold": _CRAG_THRESHOLD,
        "crag_passed": l1_crag >= _CRAG_THRESHOLD,
        "latency_ms": elapsed_ms,
        "chunks_count": len(out_chunks),
        "unique_docs": len({c.get("document_id") for c in out_chunks if c.get("document_id")}),
        **l1_epistemic,
    }
    for c in out_chunks:
        c["_telemetry"] = l1_telemetry
    return out_chunks
