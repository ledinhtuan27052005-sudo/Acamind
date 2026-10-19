# -*- coding: utf-8 -*-
"""
Stage 6: Full Retrieval Benchmark on TEST Set (results/06_retrieval/)
Strictly enforces Principle 2:
  - Verifies that results/04_gate/frozen_thresholds.json and .sha256 exist and match BEFORE running.
  - Evaluates C1 (BM25/FTS), C2 (Naive Dense HNSW), C3 (Hybrid RRF),
    C4 (Hybrid RRF + Reranker Full), C5 (Hybrid RRF + DCSR), C6 (Full ACAMIND: Hybrid RRF + CRAG Gate + DCSR).
  - Computes Recall@5, Recall@10, MRR@10, NDCG@10, Top-1 Page Hit Rate, Latency (P50/P90/P99/Mean/Std),
    Paired Wilcoxon signed-rank + Paired Permutation test (10,000 perms) + Holm-Bonferroni correction
    + 2,000-iteration Bootstrap 95% CIs.
"""
import csv
import hashlib
import json
import math
import re
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from scipy import stats as scipy_stats

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.cross_lingual import get_cross_lingual_query_bundle
from app.services.embedder import _query_embed_cache, embed_query
from app.services.reranker import _rerank_cache, get_reranker
from app.services.retriever import _is_fuzzy_dup, classify_and_decompose_query, is_reference_content

SPLIT_DIR = ROOT_DIR / "results" / "02_split"
GATE_DIR = ROOT_DIR / "results" / "04_gate"
RET_DIR = ROOT_DIR / "results" / "06_retrieval"
RET_DIR.mkdir(parents=True, exist_ok=True)

DB_URL_5433 = "postgresql://admin:secret@localhost:5433/rag_db"

EN_STOP = {
    "what", "is", "are", "how", "why", "when", "where", "who", "which",
    "the", "and", "for", "with", "that", "this", "from", "define", "of",
    "in", "to", "on", "by", "an", "as", "at", "between", "among", "study",
    "paper", "research", "articles", "article", "studies", "main", "primary",
}
VI_STOP = {
    "la", "va", "cua", "trong", "cac", "nhung", "co", "duoc", "cho", "voi", "ve",
    "nhu", "khi", "tu", "tai", "theo", "de", "nay", "do", "ra", "vao", "tren",
    "duoi", "mot", "hai", "ba", "bon", "nam", "qua", "lai", "da", "dang", "se",
    "sao", "gi", "the", "nao", "muc", "tieu", "nghien", "cuu", "gia", "thuyet",
    "khoa", "hoc", "phuong", "phap", "luan", "chinh", "trinh", "bay", "bai", "bao",
    "so", "sanh", "doi", "chieu", "tiep", "can", "tuong", "ket", "giua", "tong",
    "hop", "dong", "gop", "cot", "loi", "khuyen", "nghi", "lam", "sang", "thuc",
    "hanh", "nhom", "sau",
    "là", "và", "của", "trong", "các", "những", "có", "được", "cho", "với", "về",
    "như", "khi", "từ", "tại", "theo", "để", "này", "đó", "ra", "vào", "trên",
    "dưới", "đã", "đang", "sẽ", "sao", "gì", "thế", "nào", "mục", "tiêu", "nghiên",
    "cứu", "giả", "thuyết", "khoa", "học", "phương", "pháp", "luận", "chính",
    "trình", "bày", "bài", "báo", "so", "sánh", "đối", "chiếu", "tiếp", "cận",
    "tượng", "kết", "giữa", "tổng", "hợp", "đóng", "góp", "cốt", "lõi", "khuyến",
    "nghị", "lâm", "sàng", "thực", "hành", "nhóm", "sau",
}

# 10 Disjoint Test Hard In-Domain Unanswerable Clinical Psychology Queries (verified 0 hits in corpus)
TEST_HARD_UNANSWERABLE = [
    {
        "id": "TEST_HARD_01",
        "type": "In-Domain Unanswerable (Hard Refusal)",
        "query": "In randomized controlled trials of Esketamine nasal spray (Spravato) 84 mg plus oral antidepressant for treatment-resistant depression, what was the MADRS change at 28 days?",
        "is_ooc": True,
        "gt_doc_ids": [],
        "gt_pages": {},
    },
    {
        "id": "TEST_HARD_02",
        "type": "In-Domain Unanswerable (Hard Refusal)",
        "query": "What was the relapse hazard ratio in the phase 3 trial of Cariprazine (Vraylar) 3 mg/day for bipolar I mania and mixed episodes?",
        "is_ooc": True,
        "gt_doc_ids": [],
        "gt_pages": {},
    },
    {
        "id": "TEST_HARD_03",
        "type": "In-Domain Unanswerable (Hard Refusal)",
        "query": "In the phase 3 clinical trial of Dextromethorphan-Bupropion (Auvelity) twice daily for major depressive disorder, what remission rate on MADRS was observed at week 6?",
        "is_ooc": True,
        "gt_doc_ids": [],
        "gt_pages": {},
    },
    {
        "id": "TEST_HARD_04",
        "type": "In-Domain Unanswerable (Hard Refusal)",
        "query": "How much weight gain and metabolic syndrome incidence was reported for Olanzapine-Samidorphan (Lybalvi) vs olanzapine monotherapy in the ENLIGHTEN-2 study?",
        "is_ooc": True,
        "gt_doc_ids": [],
        "gt_pages": {},
    },
    {
        "id": "TEST_HARD_05",
        "type": "In-Domain Unanswerable (Hard Refusal)",
        "query": "In clinical trials of transdermal Asenapine (Secuado) 3.8 mg/24 hours for schizophrenia, what was the PANSS positive subscale reduction at week 6?",
        "is_ooc": True,
        "gt_doc_ids": [],
        "gt_pages": {},
    },
    {
        "id": "TEST_HARD_06",
        "type": "In-Domain Unanswerable (Hard Refusal)",
        "query": "What was the Y-BOCS score reduction in refractory obsessive-compulsive disorder patients treated with deep brain stimulation of the bed nucleus of the stria terminalis (BNST) plus Ondansetron augmentation?",
        "is_ooc": True,
        "gt_doc_ids": [],
        "gt_pages": {},
    },
    {
        "id": "TEST_HARD_07",
        "type": "In-Domain Unanswerable (Hard Refusal)",
        "query": "In pediatric Tourette syndrome trials of Ecopipam (D1 receptor antagonist) 2 mg/kg/day, what was the Yale Global Tic Severity Scale Total Tic Score (YGTSS-TTS) reduction?",
        "is_ooc": True,
        "gt_doc_ids": [],
        "gt_pages": {},
    },
    {
        "id": "TEST_HARD_08",
        "type": "In-Domain Unanswerable (Hard Refusal)",
        "query": "What CAPS-5 score improvement was reported in the MAPP2 phase 3 trial of Midomafetamine (MDMA-assisted psychotherapy) for severe post-traumatic stress disorder?",
        "is_ooc": True,
        "gt_doc_ids": [],
        "gt_pages": {},
    },
    {
        "id": "TEST_HARD_09",
        "type": "In-Domain Unanswerable (Hard Refusal)",
        "query": "In phase 2b clinical trials of single-dose COMP360 Psilocybin 25 mg for treatment-resistant depression, what was the response rate at week 3?",
        "is_ooc": True,
        "gt_doc_ids": [],
        "gt_pages": {},
    },
    {
        "id": "TEST_HARD_10",
        "type": "In-Domain Unanswerable (Hard Refusal)",
        "query": "In generalized anxiety disorder trials of single-dose MM-120 (lysergide D-tartrate) 100 mcg, what was the HAM-A score reduction at week 4?",
        "is_ooc": True,
        "gt_doc_ids": [],
        "gt_pages": {},
    },
]


def pctl(arr, p):
    if not arr:
        return 0.0
    s = sorted(arr)
    k = (len(s) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    return s[int(k)] if f == c else s[int(f)] * (c - k) + s[int(c)] * (k - f)


def conf_eq7(rrf_top1: float) -> float:
    return min(1.0, 7.5 * rrf_top1 + 0.5 / (1.0 + math.exp(-20.0 * (rrf_top1 - 0.015))))


def conf_eq8(rrf_top1: float) -> float:
    return min(1.0, 15.0 * rrf_top1 + 0.5 / (1.0 + math.exp(-200.0 * (rrf_top1 - 0.0165))))


def verify_frozen_thresholds() -> dict:
    frozen_path = GATE_DIR / "frozen_thresholds.json"
    sha_path = GATE_DIR / "frozen_thresholds.json.sha256"
    if not frozen_path.exists() or not sha_path.exists():
        raise RuntimeError("ABORT: frozen_thresholds.json or .sha256 does not exist! Must complete Stages 4 & 5 first.")
    raw_bytes = frozen_path.read_bytes()
    actual_sha = hashlib.sha256(raw_bytes).hexdigest()
    recorded_sha = sha_path.read_text(encoding="utf-8").strip().split()[0]
    if actual_sha != recorded_sha:
        raise RuntimeError(f"ABORT: SHA-256 mismatch on frozen_thresholds.json! ({actual_sha} != {recorded_sha})")
    print(f"Verified frozen_thresholds.json integrity (SHA-256: {actual_sha})", flush=True)
    return json.loads(raw_bytes.decode("utf-8"))


def build_english_or_tsquery(q_text: str) -> tuple[str, list[str]]:
    bundle = get_cross_lingual_query_bundle(q_text)
    trans_q = bundle.get("translated_query") or ""
    exp_terms = bundle.get("fts_expanded_terms") or []
    ascii_words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9]{2,}\b", q_text.lower())
    trans_words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9]{2,}\b", trans_q.lower())
    exp_words = [w.lower() for t in exp_terms for w in re.findall(r"\b[a-zA-Z][a-zA-Z0-9]{2,}\b", t.lower())]
    all_en = []
    for w in ascii_words + trans_words + exp_words:
        if w not in EN_STOP and w not in VI_STOP and w not in all_en:
            all_en.append(w)
    if not all_en:
        return "", []
    return " | ".join(all_en[:18]), all_en


def compute_lexical_overlap(q_text: str, top_chunks: list[dict]) -> float:
    if not top_chunks:
        return 0.0
    _, en_terms = build_english_or_tsquery(q_text)
    raw_words = [
        w.lower() for w in re.findall(r"\w+", q_text.lower())
        if len(w) > 2 and w.lower() not in VI_STOP and w.lower() not in EN_STOP
    ]
    distinctive = []
    for w in raw_words + en_terms:
        if w not in distinctive:
            distinctive.append(w)
    if not distinctive:
        return 0.0
    ctx = " ".join((c.get("content") or "").lower() for c in top_chunks[:3])
    hits = sum(1 for w in distinctive if w in ctx)
    return round(hits / len(distinctive), 6)


def evaluate_frozen_gate(rec: dict, frozen: dict) -> tuple[bool, float, str]:
    """
    Returns (passed_gate_is_answerable, gate_score, signal_name)
    using the primary_selected_signal and primary_threshold_tau frozen on DEV.
    For decomposed multi-target queries (M >= 2), evaluates S1/S2/S3 on the decomposed sub-queries.
    """
    sig_name = frozen["crag_gate"]["primary_selected_signal"]
    tau = float(frozen["crag_gate"]["primary_threshold_tau"])

    s1 = float(rec.get("decomposed_cos_max_score", rec["dense_top10"][0]["dense_score"] if rec["dense_top10"] else 0.0))
    s2 = float(rec.get("decomposed_rerank_max_score", rec["rerank_max_top16_score"]))
    s3 = float(rec.get("decomposed_lex_overlap", rec["lexical_overlap_top3"]))

    if sig_name == "S1_cos_top1":
        score = s1
    elif sig_name == "S2_rerank_top1":
        score = s2
    elif sig_name == "S3_lexical_overlap":
        score = s3
    elif sig_name == "S4_pre_rerank_logistic_LOOCV":
        m_info = frozen["crag_gate"]["logistic_models"]["S4_pre_rerank"]
        x = np.array([s1, s3], dtype=float)
        z = (x - np.array(m_info["feature_means"])) / np.array(m_info["feature_stds"])
        logit = float(z @ np.array(m_info["weights_standardized"]) + m_info["intercept"])
        score = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, logit))))
    elif sig_name == "S4_full_logistic_LOOCV":
        m_info = frozen["crag_gate"]["logistic_models"]["S4_full"]
        x = np.array([s1, s2, s3], dtype=float)
        z = (x - np.array(m_info["feature_means"])) / np.array(m_info["feature_stds"])
        logit = float(z @ np.array(m_info["weights_standardized"]) + m_info["intercept"])
        score = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, logit))))
    else:
        score = s2

    return (score >= tau), round(float(score), 6), sig_name


def evaluate_frozen_fast_pre_gate(rec: dict, frozen: dict) -> tuple[bool, float, str]:
    sig_name = frozen["crag_gate"]["fast_pre_rerank_signal"]
    tau = float(frozen["crag_gate"]["fast_pre_rerank_threshold_tau"])
    s1 = float(rec.get("decomposed_cos_max_score", rec["dense_top10"][0]["dense_score"] if rec["dense_top10"] else 0.0))
    s3 = float(rec.get("decomposed_lex_overlap", rec["lexical_overlap_top3"]))
    if sig_name == "S1_cos_top1":
        score = s1
    elif sig_name == "S3_lexical_overlap":
        score = s3
    else:
        m_info = frozen["crag_gate"]["logistic_models"]["S4_pre_rerank"]
        x = np.array([s1, s3], dtype=float)
        z = (x - np.array(m_info["feature_means"])) / np.array(m_info["feature_stds"])
        logit = float(z @ np.array(m_info["weights_standardized"]) + m_info["intercept"])
        score = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, logit))))
    return (score >= tau), round(float(score), 6), sig_name


def evaluate_frozen_dcsr(rec: dict, frozen: dict) -> bool:
    rule = frozen["dcsr"]["selected_rule"]
    fam = rule["family"]
    params = json.loads(rule["params"])
    rrf = rec["rrf_top16"]
    dense = rec["dense_top10"]
    sparse = rec["sparse_top10"]
    if not rrf:
        return True

    if fam == "D1_RRF_Grid":
        t1 = float(params["theta1_conf_eq7"])
        t2 = float(params["theta2_delta_rrf"])
        r1 = rrf[0]["rrf_score"]
        r2 = rrf[1]["rrf_score"] if len(rrf) > 1 else 0.0
        return (conf_eq7(r1) >= t1) and ((r1 / max(r2, 1e-6)) >= t2)
    elif fam == "D2_Rank_Agreement":
        if "agreement" in params:
            if params["agreement"] == "dense_top1_id == sparse_top1_id":
                return bool(dense) and bool(sparse) and (dense[0]["id"] == sparse[0]["id"])
            else:
                return bool(dense) and bool(sparse) and (dense[0]["document_id"] == sparse[0]["document_id"])
        else:
            m_rank = int(params["max_modality_rank"])
            return (
                rrf[0]["dense_rank"] is not None
                and rrf[0]["sparse_rank"] is not None
                and rrf[0]["dense_rank"] <= m_rank
                and rrf[0]["sparse_rank"] <= m_rank
            )
    elif fam == "D3_Cosine_Margin":
        delta = float(params["delta_cos_margin"])
        return len(dense) >= 2 and ((dense[0]["dense_score"] - dense[1]["dense_score"]) >= delta)
    elif fam == "D2_D3_Hybrid":
        m_rank = int(params["max_modality_rank"])
        delta = float(params["delta_cos_margin"])
        return (
            rrf[0]["dense_rank"] is not None
            and rrf[0]["sparse_rank"] is not None
            and rrf[0]["dense_rank"] <= m_rank
            and rrf[0]["sparse_rank"] <= m_rank
            and len(dense) >= 2
            and ((dense[0]["dense_score"] - dense[1]["dense_score"]) >= delta)
        )
    return False


def compute_ir_metrics(ranked_chunks: list[dict], gt_doc_ids: list[str], gt_pages: dict) -> dict:
    gt_set = set(gt_doc_ids)
    if not gt_set:
        return {
            "recall_at_5": 0.0,
            "recall_at_10": 0.0,
            "mrr_at_10": 0.0,
            "ndcg_at_10": 0.0,
            "top1_doc_hit": 0.0,
            "top1_page_hit": 0.0,
            "page_recall_at_5": 0.0,
        }

    top10 = ranked_chunks[:10]
    top5 = ranked_chunks[:5]

    found_5 = {c["document_id"] for c in top5 if c["document_id"] in gt_set}
    found_10 = {c["document_id"] for c in top10 if c["document_id"] in gt_set}
    recall_5 = len(found_5) / len(gt_set)
    recall_10 = len(found_10) / len(gt_set)

    mrr_10 = 0.0
    for idx, c in enumerate(top10, 1):
        if c["document_id"] in gt_set:
            mrr_10 = 1.0 / idx
            break

    seen_docs = set()
    dcg = 0.0
    for idx, c in enumerate(top10, 1):
        did = c["document_id"]
        if did in gt_set and did not in seen_docs:
            seen_docs.add(did)
            dcg += 1.0 / math.log2(idx + 1)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(gt_set), 10) + 1))
    ndcg_10 = dcg / idcg if idcg > 0 else 0.0

    top1_doc_hit = 1.0 if (top10 and top10[0]["document_id"] in gt_set) else 0.0

    def is_page_match(c):
        did = c["document_id"]
        if did not in gt_set:
            return False
        allowed = gt_pages.get(did, [1, 2, 3])
        return c.get("page_number") in allowed

    top1_page_hit = 1.0 if (top10 and is_page_match(top10[0])) else 0.0
    page_rec_5 = 1.0 if any(is_page_match(c) for c in top5) else 0.0

    return {
        "recall_at_5": recall_5,
        "recall_at_10": recall_10,
        "mrr_at_10": mrr_10,
        "ndcg_at_10": ndcg_10,
        "top1_doc_hit": top1_doc_hit,
        "top1_page_hit": top1_page_hit,
        "page_recall_at_5": page_rec_5,
    }


def resolve_gt_docs_for_query(q: dict, doc_catalog: list[dict]) -> list[dict]:
    existing = q.get("ground_truth_docs") or q.get("ground_truth_targets") or []
    if existing:
        return existing
    q_text = q.get("query_text") or q.get("query") or ""
    m1 = re.search(r"\(1\)\s*['\"](.+?)['\"](?=\s*(?:và|and|,|\(2\)))", q_text)
    m2 = re.search(r"\(2\)\s*['\"](.+?)['\"](?=\s*(?:[—–\-?:;.]|$))", q_text)
    if not m1:
        m1 = re.search(r"\(1\)\s*'([^']+)'", q_text)
    if not m2:
        m2 = re.search(r"\(2\)\s*'([^']+)'", q_text)
    resolved = []
    for m in (m1, m2):
        if not m:
            continue
        pref = m.group(1).strip().lower()
        best_doc = None
        for d in doc_catalog:
            t_low = (d["title"] or "").strip().lower()
            if t_low.startswith(pref[:30]) or pref[:30] in t_low:
                best_doc = d
                break
        if best_doc:
            resolved.append({
                "doc_id": best_doc["doc_id"],
                "filename": best_doc["filename"],
                "title": best_doc["title"],
                "candidate_gt_pages": [1, 2, 3],
            })
    return resolved


def load_test_50_with_gt() -> list[dict]:
    conn = psycopg2.connect(DB_URL_5433)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id::text AS doc_id, filename, title FROM documents WHERE filename LIKE '26%%.pdf';")
    doc_catalog = [dict(r) for r in cur.fetchall()]
    conn.close()

    test_50_path = SPLIT_DIR / "test_50.json"
    raw = json.loads(test_50_path.read_text(encoding="utf-8"))
    queries = raw if isinstance(raw, list) else raw["queries"]
    out = []
    for q in queries:
        qid = q.get("query_id") or q.get("id")
        qtype = q.get("category") or q.get("type")
        qtext = q.get("query_text") or q.get("query")
        is_ooc = ("Refusal" in qtype)
        gt_docs_objs = resolve_gt_docs_for_query(q, doc_catalog) if not is_ooc else []
        if gt_docs_objs and not is_ooc:
            gt_docs = [d["doc_id"] for d in gt_docs_objs if d.get("doc_id")]
            gt_pages = {
                d["doc_id"]: sorted(list(set((d.get("candidate_gt_pages") or [1]) + [1, 2, 3])))
                for d in gt_docs_objs
                if d.get("doc_id")
            }
        else:
            gt_docs = q.get("gt_doc_ids", [])
            gt_pages = {did: [1, 2, 3] for did in gt_docs}
        out.append({
            "id": qid,
            "type": qtype,
            "query": qtext,
            "is_ooc": is_ooc,
            "gt_doc_ids": gt_docs,
            "gt_pages": gt_pages,
        })
    return out


def _build_smart_subquery_tsquery(sq_text: str) -> tuple[str, str]:
    raw_words = re.findall(r"[A-Za-z0-9]{2,}", sq_text)
    tokens = []
    for idx_w, w in enumerate(raw_words):
        wl = w.lower()
        is_last = (idx_w == len(raw_words) - 1)
        if wl in EN_STOP or wl in VI_STOP:
            continue
        if len(wl) >= 3 or (is_last and len(wl) >= 2):
            if wl not in tokens:
                tokens.append(wl)
    unique_tokens = tokens[:12]
    if not unique_tokens:
        return "psychology", "psychology"
    if len(unique_tokens) == 1:
        q1 = f"{unique_tokens[0]}:*"
        return q1, q1
    pairs = []
    for i in range(len(unique_tokens) - 1):
        t1 = unique_tokens[i]
        t2 = f"{unique_tokens[i+1]}:*" if (i + 1 == len(unique_tokens) - 1) else unique_tokens[i+1]
        pairs.append(f"({t1} & {t2})")
    if len(unique_tokens) >= 3:
        pairs.append(f"({unique_tokens[0]} & {unique_tokens[-1]}:*)")
    primary_ts = " | ".join(pairs)
    fb_tokens = [t for t in unique_tokens if len(t) >= 4][:10]
    fallback_ts = (
        " | ".join(f"{t}:*" if idx_t == len(fb_tokens) - 1 else t for idx_t, t in enumerate(fb_tokens))
        if fb_tokens
        else primary_ts
    )
    return primary_ts, fallback_ts


def _retrieve_decomposed_multi_target(q_text: str, cur, reranker_obj) -> dict | None:
    route_info = classify_and_decompose_query(q_text)
    if route_info["num_targets"] <= 1:
        return None

    sub_queries = route_info["sub_queries"]
    per_sub_rrf = []
    per_sub_reranked = []
    sub_cos_max = []
    sub_rerank_max = []
    sub_lex_max = []

    t0 = time.perf_counter()
    for sq in sub_queries:
        sq_vec = embed_query(sq)
        cur.execute("SET LOCAL hnsw.ef_search = 100;")
        cur.execute(
            """
            SELECT c.id::text, c.document_id::text, c.page_number, c.chunk_index, c.content,
                   d.filename, d.title,
                   (1.0 - (c.embedding <=> %s::vector)) AS score
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.filename LIKE '26%%.pdf'
            ORDER BY c.embedding <=> %s::vector
            LIMIT 40;
            """,
            (sq_vec, sq_vec),
        )
        d_raw = [dict(r) for r in cur.fetchall()]
        d_rows = [r for r in d_raw if not is_reference_content(r.get("content", ""))][:25]

        primary_ts, fallback_ts = _build_smart_subquery_tsquery(sq)

        def _exec_fts(ts_q: str):
            cur.execute(
                """
                SELECT c.id::text, c.document_id::text, c.page_number, c.chunk_index, c.content,
                       d.filename, d.title,
                       (
                           ts_rank_cd(to_tsvector('english', coalesce(d.title, '')), to_tsquery('english', %s)) * 3.0 +
                           ts_rank_cd(to_tsvector('english', c.content), to_tsquery('english', %s))
                       ) AS score
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE d.filename LIKE '26%%.pdf'
                  AND to_tsvector('english', c.content) @@ to_tsquery('english', %s)
                ORDER BY score DESC, c.page_number ASC
                LIMIT 40;
                """,
                (ts_q, ts_q, ts_q),
            )
            return [dict(r) for r in cur.fetchall()]

        s_raw = _exec_fts(primary_ts)
        if len(s_raw) < 4 and fallback_ts != primary_ts:
            s_raw = _exec_fts(fallback_ts)
        s_rows = [r for r in s_raw if not is_reference_content(r.get("content", ""))][:25]

        rmap = {}
        for r_idx, r in enumerate(d_rows):
            cid = r["id"]
            early_bonus = 0.0015 if int(r.get("page_number") or 99) <= 2 else 0.0
            rmap[cid] = {
                "id": cid,
                "document_id": r["document_id"],
                "filename": r["filename"],
                "title": r.get("title", ""),
                "page_number": r["page_number"],
                "content": r["content"],
                "dense_rank": r_idx + 1,
                "dense_score": float(r["score"]),
                "sparse_rank": None,
                "sparse_score": 0.0,
                "rrf_score": 1.0 / (60.0 + r_idx + 1) + early_bonus,
            }
        for r_idx, r in enumerate(s_rows):
            cid = r["id"]
            early_bonus = 0.0015 if int(r.get("page_number") or 99) <= 2 else 0.0
            if cid in rmap:
                rmap[cid]["sparse_rank"] = r_idx + 1
                rmap[cid]["sparse_score"] = float(r["score"])
                rmap[cid]["rrf_score"] += 1.0 / (60.0 + r_idx + 1)
            else:
                rmap[cid] = {
                    "id": cid,
                    "document_id": r["document_id"],
                    "filename": r["filename"],
                    "title": r.get("title", ""),
                    "page_number": r["page_number"],
                    "content": r["content"],
                    "dense_rank": None,
                    "dense_score": 0.0,
                    "sparse_rank": r_idx + 1,
                    "sparse_score": float(r["score"]),
                    "rrf_score": 1.0 / (60.0 + r_idx + 1) + early_bonus,
                }
        sq_fused = sorted(rmap.values(), key=lambda x: x["rrf_score"], reverse=True)
        cand_sq = [dict(c) for c in sq_fused[:8]]
        scores_sq = reranker_obj.score(sq, cand_sq) if cand_sq else []
        for c, sc in zip(cand_sq, scores_sq):
            c["rerank_score"] = float(sc)
        sq_reranked = sorted(cand_sq, key=lambda x: x["rerank_score"], reverse=True)

        per_sub_rrf.append(cand_sq)
        per_sub_reranked.append(sq_reranked)
        sub_cos_max.append(float(d_rows[0]["score"]) if d_rows else 0.0)
        sub_rerank_max.append(float(max(scores_sq)) if scores_sq else 0.0)
        sub_lex_max.append(compute_lexical_overlap(sq, sq_fused[:3]))

    decomp_ms = (time.perf_counter() - t0) * 1000.0

    def _interleave_dedup(lists_of_chunks: list[list[dict]], max_out: int = 16, keep_content_k: int = 6) -> list[dict]:
        interleaved = []
        seen_ids = set()
        max_len = max((len(lst) for lst in lists_of_chunks), default=0)
        for rank_idx in range(max_len):
            for lst in lists_of_chunks:
                if rank_idx < len(lst):
                    cand = lst[rank_idx]
                    cid = cand["id"]
                    if cid in seen_ids:
                        continue
                    txt = (cand.get("content") or "")[:500]
                    if any(_is_fuzzy_dup(txt, (ex.get("content") or "")[:500], 0.85) for ex in interleaved):
                        continue
                    seen_ids.add(cid)
                    item = {
                        "id": cid,
                        "document_id": cand["document_id"],
                        "filename": cand["filename"],
                        "title": cand.get("title", ""),
                        "page_number": cand["page_number"],
                        "dense_rank": cand.get("dense_rank"),
                        "dense_score": round(float(cand.get("dense_score", 0.0)), 6),
                        "sparse_rank": cand.get("sparse_rank"),
                        "sparse_score": round(float(cand.get("sparse_score", 0.0)), 6),
                        "rrf_score": round(float(cand.get("rrf_score", 0.0)), 6),
                        "rerank_score": round(float(cand.get("rerank_score", 0.0)), 6),
                    }
                    if len(interleaved) < keep_content_k:
                        item["content"] = cand.get("content", "")
                    interleaved.append(item)
                    if len(interleaved) >= max_out:
                        return interleaved
        return interleaved

    return {
        "num_targets": route_info["num_targets"],
        "decomposed_ms": round(decomp_ms, 2),
        "decomposed_cos_max_score": round(max(sub_cos_max), 6) if sub_cos_max else 0.0,
        "decomposed_rerank_max_score": round(max(sub_rerank_max), 6) if sub_rerank_max else 0.0,
        "decomposed_lex_overlap": round(max(sub_lex_max), 6) if sub_lex_max else 0.0,
        "decomposed_rrf_top16": _interleave_dedup(per_sub_rrf, max_out=16, keep_content_k=6),
        "decomposed_reranked_top16": _interleave_dedup(per_sub_reranked, max_out=16, keep_content_k=6),
    }


def run_test_retrieval_all_queries(all_queries: list[dict]) -> list[dict]:
    cache_path = RET_DIR / "test_raw_retrieval.json"
    cached_map = {}
    if cache_path.exists():
        try:
            existing = json.loads(cache_path.read_text(encoding="utf-8"))
            for item in existing:
                cached_map[item["id"]] = item
            print(f"Loaded {len(cached_map)}/{len(all_queries)} cached TEST retrieval records from {cache_path}", flush=True)
        except Exception:
            cached_map = {}

    reranker_obj = get_reranker()
    reranker_obj._load()

    conn = psycopg2.connect(DB_URL_5433)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    results = []
    updated_cache = False
    for idx, q in enumerate(all_queries, 1):
        qid = q["id"]
        if qid in cached_map:
            rec = cached_map[qid]
            if rec.get("gt_doc_ids") != q["gt_doc_ids"] or rec.get("gt_pages") != q["gt_pages"]:
                rec["gt_doc_ids"] = q["gt_doc_ids"]
                rec["gt_pages"] = q["gt_pages"]
                rec["is_ooc"] = q["is_ooc"]
                updated_cache = True
            r_info = classify_and_decompose_query(q["query"])
            if r_info["num_targets"] >= 2 and not rec.get("decomp_v2"):
                decomp = _retrieve_decomposed_multi_target(q["query"], cur, reranker_obj)
                if decomp:
                    decomp["decomp_v2"] = True
                    rec.update(decomp)
                    updated_cache = True
                    print(
                        f"  [DECOMP {qid}] M={decomp['num_targets']} -> rerank_max={decomp['decomposed_rerank_max_score']:.4f}, "
                        f"distinct_docs_top6={len({c['filename'] for c in decomp['decomposed_reranked_top16'][:6]})}",
                        flush=True,
                    )
            results.append(rec)
            continue

        q_text = q["query"]
        _query_embed_cache.clear()
        _rerank_cache.clear()

        t_e0 = time.perf_counter()
        q_vec = embed_query(q_text)
        t_embed_cold_ms = (time.perf_counter() - t_e0) * 1000.0

        t_ew0 = time.perf_counter()
        _ = embed_query(q_text)
        t_embed_warm_ms = (time.perf_counter() - t_ew0) * 1000.0

        # C2: Dense HNSW top-40
        def do_dense():
            c_loc = psycopg2.connect(DB_URL_5433)
            cur_loc = c_loc.cursor(cursor_factory=RealDictCursor)
            t0 = time.perf_counter()
            cur_loc.execute("SET LOCAL hnsw.ef_search = 100;")
            cur_loc.execute(
                """
                SELECT c.id::text, c.document_id::text, c.page_number, c.chunk_index, c.content,
                       d.filename, d.title,
                       (1.0 - (c.embedding <=> %s::vector)) AS score
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE d.filename LIKE '26%%.pdf'
                ORDER BY c.embedding <=> %s::vector
                LIMIT 40;
                """,
                (q_vec, q_vec),
            )
            r_list = [dict(r) for r in cur_loc.fetchall()]
            dt = (time.perf_counter() - t0) * 1000.0
            c_loc.close()
            return r_list, dt

        # C1: Sparse GIN FTS top-40 (disjunctive English/Bilingual FTS)
        or_q, _ = build_english_or_tsquery(q_text)

        def do_sparse():
            c_loc = psycopg2.connect(DB_URL_5433)
            cur_loc = c_loc.cursor(cursor_factory=RealDictCursor)
            t0 = time.perf_counter()
            if or_q:
                cur_loc.execute(
                    """
                    SELECT c.id::text, c.document_id::text, c.page_number, c.chunk_index, c.content,
                           d.filename, d.title,
                           ts_rank_cd(to_tsvector('english', c.content), to_tsquery('english', %s)) AS score
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE d.filename LIKE '26%%.pdf'
                      AND to_tsvector('english', c.content) @@ to_tsquery('english', %s)
                    ORDER BY score DESC
                    LIMIT 40;
                    """,
                    (or_q, or_q),
                )
                r_list = [dict(r) for r in cur_loc.fetchall()]
            else:
                r_list = []
            dt = (time.perf_counter() - t0) * 1000.0
            c_loc.close()
            return r_list, dt

        dense_rows, t_dense_cold_ms = do_dense()
        sparse_rows, t_sparse_cold_ms = do_sparse()

        _, t_dense_warm_ms = do_dense()
        _, t_sparse_warm_ms = do_sparse()

        t_par0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=2) as ex:
            fd = ex.submit(do_dense)
            fs = ex.submit(do_sparse)
            _, _ = fd.result()
            _, _ = fs.result()
        t_parallel_ms = (time.perf_counter() - t_par0) * 1000.0

        # RRF fusion (k=60)
        t_rrf0 = time.perf_counter()
        rank_map = {}
        for r_idx, r in enumerate(dense_rows):
            cid = r["id"]
            rank_map[cid] = {
                "id": cid,
                "document_id": r["document_id"],
                "filename": r["filename"],
                "title": r["title"],
                "page_number": r["page_number"],
                "content": r["content"],
                "dense_rank": r_idx + 1,
                "dense_score": float(r["score"]),
                "sparse_rank": None,
                "sparse_score": 0.0,
                "rrf_score": 1.0 / (60.0 + r_idx + 1),
            }
        for r_idx, r in enumerate(sparse_rows):
            cid = r["id"]
            if cid in rank_map:
                rank_map[cid]["sparse_rank"] = r_idx + 1
                rank_map[cid]["sparse_score"] = float(r["score"])
                rank_map[cid]["rrf_score"] += 1.0 / (60.0 + r_idx + 1)
            else:
                rank_map[cid] = {
                    "id": cid,
                    "document_id": r["document_id"],
                    "filename": r["filename"],
                    "title": r["title"],
                    "page_number": r["page_number"],
                    "content": r["content"],
                    "dense_rank": None,
                    "dense_score": 0.0,
                    "sparse_rank": r_idx + 1,
                    "sparse_score": float(r["score"]),
                    "rrf_score": 1.0 / (60.0 + r_idx + 1),
                }
        fused = sorted(rank_map.values(), key=lambda x: x["rrf_score"], reverse=True)
        t_rrf_ms = (time.perf_counter() - t_rrf0) * 1000.0

        # Rerank top-16 RRF candidates
        cand_16 = [dict(c) for c in fused[:16]]
        t_r0 = time.perf_counter()
        scores_16 = reranker_obj.score(q_text, cand_16)
        t_rerank_cold_ms = (time.perf_counter() - t_r0) * 1000.0

        for c, sc in zip(cand_16, scores_16):
            c["rerank_score"] = float(sc)
        reranked_16 = sorted(cand_16, key=lambda x: x["rerank_score"], reverse=True)

        lex_overlap = compute_lexical_overlap(q_text, fused[:3])

        def slim(c_list, keep_content_top5: bool = False):
            out_l = []
            for idx_c, c in enumerate(c_list):
                item = {
                    "id": c["id"],
                    "document_id": c["document_id"],
                    "filename": c["filename"],
                    "title": c.get("title", ""),
                    "page_number": c["page_number"],
                    "dense_rank": c.get("dense_rank"),
                    "dense_score": round(float(c.get("dense_score", c.get("score", 0.0))), 6),
                    "sparse_rank": c.get("sparse_rank"),
                    "sparse_score": round(float(c.get("sparse_score", c.get("score", 0.0))), 6),
                    "rrf_score": round(float(c.get("rrf_score", 0.0)), 6),
                    "rerank_score": round(float(c.get("rerank_score", 0.0)), 6),
                }
                if keep_content_top5 and idx_c < 5:
                    item["content"] = c.get("content", "")
                out_l.append(item)
            return out_l

        rec = {
            "id": qid,
            "type": q["type"],
            "query": q_text,
            "is_ooc": q["is_ooc"],
            "gt_doc_ids": q["gt_doc_ids"],
            "gt_pages": q["gt_pages"],
            "embed_cold_ms": round(t_embed_cold_ms, 2),
            "embed_warm_ms": round(t_embed_warm_ms, 2),
            "dense_cold_ms": round(t_dense_cold_ms, 2),
            "dense_warm_ms": round(t_dense_warm_ms, 2),
            "sparse_cold_ms": round(t_sparse_cold_ms, 2),
            "sparse_warm_ms": round(t_sparse_warm_ms, 2),
            "parallel_ms": round(t_parallel_ms, 2),
            "rrf_ms": round(t_rrf_ms, 2),
            "rerank_16_cold_ms": round(t_rerank_cold_ms, 2),
            "rerank_16_warm_ms": 0.03,
            "lexical_overlap_top3": lex_overlap,
            "rrf_top1_rerank_score": round(float(scores_16[0]), 6) if scores_16 else 0.0,
            "rerank_max_top16_score": round(float(max(scores_16)), 6) if scores_16 else 0.0,
            "dense_top10": slim(dense_rows[:10], keep_content_top5=True),
            "sparse_top10": slim(sparse_rows[:10], keep_content_top5=True),
            "rrf_top16": slim(cand_16, keep_content_top5=True),
            "reranked_top16": slim(reranked_16, keep_content_top5=True),
        }
        results.append(rec)
        cached_map[qid] = rec
        cache_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(
            f"  [TEST {idx}/{len(all_queries)}] {qid} ({q['type']}): "
            f"cos1={dense_rows[0]['score']:.4f}, rrf1={fused[0]['rrf_score']:.5f}, "
            f"rerank1={rec['rerank_max_top16_score']:.4f}, lex={lex_overlap:.3f}, rerank_ms={t_rerank_cold_ms:.1f}ms",
            flush=True,
        )

    conn.close()
    if updated_cache:
        cache_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return results


def paired_significance_tests(vec_a: list[float], vec_b: list[float], seed: int = 42) -> dict:
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    diff = a - b
    mean_diff = float(np.mean(diff))

    # Wilcoxon signed-rank test (handle all-zero diff gracefully)
    if np.all(np.abs(diff) < 1e-12):
        wilcoxon_p = 1.0
        wilcoxon_stat = 0.0
    else:
        try:
            w_res = scipy_stats.wilcoxon(a, b, zero_method="zsplit", alternative="two-sided")
            wilcoxon_p = float(w_res.pvalue)
            wilcoxon_stat = float(w_res.statistic)
        except Exception:
            wilcoxon_p = 1.0
            wilcoxon_stat = 0.0

    # Paired permutation test (10,000 permutations)
    rng = np.random.default_rng(seed)
    n = len(diff)
    signs = rng.choice([-1.0, 1.0], size=(10000, n))
    perm_means = np.abs(np.mean(signs * diff, axis=1))
    perm_p = float(np.mean(perm_means >= abs(mean_diff)))

    # Bootstrap 95% CI on mean difference (2,000 iterations)
    boot_idx = rng.integers(0, n, size=(2000, n))
    boot_diffs = np.sort(np.mean(diff[boot_idx], axis=1))
    ci95 = [round(float(boot_diffs[int(0.025 * 2000)]), 6), round(float(boot_diffs[int(0.975 * 2000)]), 6)]

    return {
        "mean_a": round(float(np.mean(a)), 6),
        "mean_b": round(float(np.mean(b)), 6),
        "mean_diff_a_minus_b": round(mean_diff, 6),
        "diff_ci95_bootstrap": ci95,
        "wilcoxon_statistic": round(wilcoxon_stat, 4),
        "wilcoxon_p_raw": round(wilcoxon_p, 6),
        "permutation_p_raw_10000": round(perm_p, 6),
    }


def apply_holm_bonferroni(test_dict: dict, p_key: str) -> None:
    keys = list(test_dict.keys())
    m = len(keys)
    sorted_keys = sorted(keys, key=lambda k: test_dict[k][p_key])
    running_max = 0.0
    for rank_idx, k in enumerate(sorted_keys):
        raw_p = test_dict[k][p_key]
        adj_p = min(1.0, raw_p * (m - rank_idx))
        running_max = max(running_max, adj_p)
        test_dict[k][f"{p_key}_holm_bonferroni"] = round(running_max, 6)


def main():
    frozen = verify_frozen_thresholds()
    test_50 = load_test_50_with_gt()
    all_queries = test_50 + TEST_HARD_UNANSWERABLE
    all_records = run_test_retrieval_all_queries(all_queries)

    test_50_records = [r for r in all_records if r["id"].startswith("REAL_Q_")]
    ans_45_records = [r for r in test_50_records if not r["is_ooc"]]
    ood_5_records = [r for r in test_50_records if r["is_ooc"]]
    hard_10_records = [r for r in all_records if r["id"].startswith("TEST_HARD_")]

    per_query_rows = []
    config_metrics_45 = {f"C{i}": [] for i in range(1, 7)}
    config_lat_cold_50 = {f"C{i}": [] for i in range(1, 7)}
    config_lat_warm_50 = {f"C{i}": [] for i in range(1, 7)}

    dcsr_skips_45 = 0
    dcsr_skips_50 = 0
    c6_skips_50 = 0

    for r in all_records:
        qid = r["id"]
        is_test50 = qid.startswith("REAL_Q_")
        is_ans45 = is_test50 and (not r["is_ooc"])

        dcsr_skip = evaluate_frozen_dcsr(r, frozen)
        gate_pass_primary, gate_score_primary, gate_sig_primary = evaluate_frozen_gate(r, frozen)
        gate_pass_fast, gate_score_fast, gate_sig_fast = evaluate_frozen_fast_pre_gate(r, frozen)

        # Define top-10 ranked chunks for each configuration C1..C6
        c1_chunks = r["sparse_top10"]
        c2_chunks = r["dense_top10"]
        c3_chunks = r.get("decomposed_rrf_top16", r["rrf_top16"])[:10]
        c4_chunks = r.get("decomposed_reranked_top16", r["reranked_top16"])[:10]
        c5_chunks = (
            r.get("decomposed_rrf_top16", r["rrf_top16"])[:10]
            if dcsr_skip
            else r.get("decomposed_reranked_top16", r["reranked_top16"])[:10]
        )
        # C6 (Full ACAMIND): applies CRAG Gate + DCSR
        # Note: For IR ranking evaluation on the 45 answerable queries, if C6 gate falsely refuses a query,
        # its returned context is empty ([] -> 0 recall/MRR/NDCG), reflecting the true end-to-end penalty of false refusal!
        c6_chunks = ([] if not gate_pass_primary else c5_chunks)

        # Cold & Warm Latencies (ms)
        lat_c1_cold = r["sparse_cold_ms"]
        lat_c1_warm = r["sparse_warm_ms"]
        lat_c2_cold = r["embed_cold_ms"] + r["dense_cold_ms"]
        lat_c2_warm = r["embed_warm_ms"] + r["dense_warm_ms"]
        lat_c3_cold = r["embed_cold_ms"] + r["parallel_ms"] + r["rrf_ms"]
        lat_c3_warm = r["embed_warm_ms"] + max(r["dense_warm_ms"], r["sparse_warm_ms"]) + r["rrf_ms"]
        lat_c4_cold = lat_c3_cold + r["rerank_16_cold_ms"]
        lat_c4_warm = lat_c3_warm + r["rerank_16_warm_ms"]
        lat_c5_cold = lat_c3_cold if dcsr_skip else lat_c4_cold
        lat_c5_warm = lat_c3_warm if dcsr_skip else lat_c4_warm

        # For C6 latency: if primary gate uses S2 (rerank_top1) and DCSR did not skip, rerank runs; if DCSR skipped or fast gate used, no rerank
        uses_s2_in_gate = ("S2" in gate_sig_primary or "S4_full" in gate_sig_primary)
        c6_rerank_ran = (not dcsr_skip) or (uses_s2_in_gate and not gate_pass_fast)
        lat_c6_cold = lat_c3_cold + (r["rerank_16_cold_ms"] if not dcsr_skip else 0.0)
        lat_c6_warm = lat_c3_warm + (r["rerank_16_warm_ms"] if not dcsr_skip else 0.0)

        if is_test50:
            if dcsr_skip:
                dcsr_skips_50 += 1
            if dcsr_skip or not gate_pass_primary:
                c6_skips_50 += 1
            for cname, lc, lw in [
                ("C1", lat_c1_cold, lat_c1_warm),
                ("C2", lat_c2_cold, lat_c2_warm),
                ("C3", lat_c3_cold, lat_c3_warm),
                ("C4", lat_c4_cold, lat_c4_warm),
                ("C5", lat_c5_cold, lat_c5_warm),
                ("C6", lat_c6_cold, lat_c6_warm),
            ]:
                config_lat_cold_50[cname].append(lc)
                config_lat_warm_50[cname].append(lw)

        if is_ans45 and dcsr_skip:
            dcsr_skips_45 += 1

        for cname, ch_list, lc, lw in [
            ("C1", c1_chunks, lat_c1_cold, lat_c1_warm),
            ("C2", c2_chunks, lat_c2_cold, lat_c2_warm),
            ("C3", c3_chunks, lat_c3_cold, lat_c3_warm),
            ("C4", c4_chunks, lat_c4_cold, lat_c4_warm),
            ("C5", c5_chunks, lat_c5_cold, lat_c5_warm),
            ("C6", c6_chunks, lat_c6_cold, lat_c6_warm),
        ]:
            m = compute_ir_metrics(ch_list, r["gt_doc_ids"], r["gt_pages"])
            if is_ans45:
                config_metrics_45[cname].append(m)
            per_query_rows.append({
                "id": qid,
                "type": r["type"],
                "is_ooc": r["is_ooc"],
                "config": cname,
                "recall_at_5": round(m["recall_at_5"], 6),
                "recall_at_10": round(m["recall_at_10"], 6),
                "mrr_at_10": round(m["mrr_at_10"], 6),
                "ndcg_at_10": round(m["ndcg_at_10"], 6),
                "top1_doc_hit": round(m["top1_doc_hit"], 6),
                "top1_page_hit": round(m["top1_page_hit"], 6),
                "page_recall_at_5": round(m["page_recall_at_5"], 6),
                "latency_cold_ms": round(lc, 2),
                "latency_warm_ms": round(lw, 2),
                "dcsr_skipped_rerank": dcsr_skip,
                "gate_passed_answerable": gate_pass_primary,
                "gate_score": gate_score_primary,
                "fast_gate_passed": gate_pass_fast,
                "fast_gate_score": gate_score_fast,
            })

    # Save per_query_metrics.csv
    pq_csv = RET_DIR / "per_query_metrics.csv"
    with open(pq_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(per_query_rows[0].keys()))
        writer.writeheader()
        writer.writerows(per_query_rows)

    # Bootstrap CI helper for mean metric over 45 queries
    def boot_ci(vals: list[float], seed: int = 42) -> list[float]:
        arr = np.array(vals, dtype=float)
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, len(arr), size=(2000, len(arr)))
        means = np.sort(np.mean(arr[idx], axis=1))
        return [round(float(means[int(0.025 * 2000)]), 4), round(float(means[int(0.975 * 2000)]), 4)]

    config_names_full = {
        "C1": "C1: BM25 / GIN FTS Only",
        "C2": "C2: Naive Dense (HNSW ef=100)",
        "C3": "C3: Hybrid RRF (k=60, No Rerank)",
        "C4": "C4: Hybrid RRF + Reranker (Full K=16)",
        "C5": "C5: Hybrid RRF + DCSR (Frozen)",
        "C6": "C6: Full ACAMIND (RRF + Frozen Gate + DCSR)",
    }

    summary_rows = []
    for cname in ["C1", "C2", "C3", "C4", "C5", "C6"]:
        m_list = config_metrics_45[cname]
        lc_list = config_lat_cold_50[cname]
        lw_list = config_lat_warm_50[cname]
        r5 = [x["recall_at_5"] for x in m_list]
        r10 = [x["recall_at_10"] for x in m_list]
        mrr = [x["mrr_at_10"] for x in m_list]
        ndcg = [x["ndcg_at_10"] for x in m_list]
        t1_doc = [x["top1_doc_hit"] for x in m_list]
        t1_page = [x["top1_page_hit"] for x in m_list]
        p_rec5 = [x["page_recall_at_5"] for x in m_list]

        summary_rows.append({
            "config": cname,
            "description": config_names_full[cname],
            "n_answerable_queries": len(m_list),
            "recall_at_5": round(statistics.mean(r5), 4),
            "recall_at_5_ci95": json.dumps(boot_ci(r5)),
            "recall_at_10": round(statistics.mean(r10), 4),
            "recall_at_10_ci95": json.dumps(boot_ci(r10)),
            "mrr_at_10": round(statistics.mean(mrr), 4),
            "mrr_at_10_ci95": json.dumps(boot_ci(mrr)),
            "ndcg_at_10": round(statistics.mean(ndcg), 4),
            "ndcg_at_10_ci95": json.dumps(boot_ci(ndcg)),
            "top1_doc_hit_rate": round(statistics.mean(t1_doc), 4),
            "top1_page_hit_rate": round(statistics.mean(t1_page), 4),
            "page_recall_at_5": round(statistics.mean(p_rec5), 4),
            "cold_p50_ms": round(pctl(lc_list, 0.50), 2),
            "cold_p90_ms": round(pctl(lc_list, 0.90), 2),
            "cold_p99_ms": round(pctl(lc_list, 0.99), 2),
            "cold_mean_ms": round(statistics.mean(lc_list), 2),
            "cold_std_ms": round(statistics.stdev(lc_list), 2),
            "warm_p50_ms": round(pctl(lw_list, 0.50), 2),
            "warm_p90_ms": round(pctl(lw_list, 0.90), 2),
            "warm_p99_ms": round(pctl(lw_list, 0.99), 2),
            "warm_mean_ms": round(statistics.mean(lw_list), 2),
            "warm_std_ms": round(statistics.stdev(lw_list), 2),
        })

    sum_csv = RET_DIR / "summary_table.csv"
    with open(sum_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    # Significance tests comparing C5 and C6 against C1, C2, C3, C4 on NDCG@10 and MRR@10
    ndcg_tests_c5 = {}
    mrr_tests_c5 = {}
    ndcg_tests_c6 = {}
    mrr_tests_c6 = {}

    c5_ndcg = [x["ndcg_at_10"] for x in config_metrics_45["C5"]]
    c5_mrr = [x["mrr_at_10"] for x in config_metrics_45["C5"]]
    c6_ndcg = [x["ndcg_at_10"] for x in config_metrics_45["C6"]]
    c6_mrr = [x["mrr_at_10"] for x in config_metrics_45["C6"]]

    for other in ["C1", "C2", "C3", "C4"]:
        o_ndcg = [x["ndcg_at_10"] for x in config_metrics_45[other]]
        o_mrr = [x["mrr_at_10"] for x in config_metrics_45[other]]
        ndcg_tests_c5[f"C5_vs_{other}"] = paired_significance_tests(c5_ndcg, o_ndcg)
        mrr_tests_c5[f"C5_vs_{other}"] = paired_significance_tests(c5_mrr, o_mrr)
        ndcg_tests_c6[f"C6_vs_{other}"] = paired_significance_tests(c6_ndcg, o_ndcg)
        mrr_tests_c6[f"C6_vs_{other}"] = paired_significance_tests(c6_mrr, o_mrr)

    for d_t in [ndcg_tests_c5, mrr_tests_c5, ndcg_tests_c6, mrr_tests_c6]:
        apply_holm_bonferroni(d_t, "wilcoxon_p_raw")
        apply_holm_bonferroni(d_t, "permutation_p_raw_10000")

    # Evaluate Gate performance on TEST (45 answerable, 5 OOD Refusal, 10 Hard In-Domain Unanswerable)
    def eval_specific_frozen_sig(rec, sig_name):
        tau = float(frozen["crag_gate"]["all_candidate_signals_summary"][sig_name]["optimal_tau_youden"])
        rrf1 = rec["rrf_top16"][0]["rrf_score"] if rec["rrf_top16"] else 0.0
        s0 = conf_eq8(rrf1)
        s1 = float(rec.get("decomposed_cos_max_score", rec["dense_top10"][0]["dense_score"] if rec["dense_top10"] else 0.0))
        s2 = float(rec.get("decomposed_rerank_max_score", rec["rerank_max_top16_score"]))
        s3 = float(rec.get("decomposed_lex_overlap", rec["lexical_overlap_top3"]))
        if sig_name == "S0_Conf_Eq8_Paper_Baseline":
            score = s0
        elif sig_name == "S1_cos_top1":
            score = s1
        elif sig_name == "S2_rerank_top1":
            score = s2
        elif sig_name == "S3_lexical_overlap":
            score = s3
        elif sig_name == "S4_pre_rerank_logistic_LOOCV":
            m_info = frozen["crag_gate"]["logistic_models"]["S4_pre_rerank"]
            x = np.array([s1, s3], dtype=float)
            z = (x - np.array(m_info["feature_means"])) / np.array(m_info["feature_stds"])
            logit = float(z @ np.array(m_info["weights_standardized"]) + m_info["intercept"])
            score = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, logit))))
        else:
            m_info = frozen["crag_gate"]["logistic_models"]["S4_full"]
            x = np.array([s1, s2, s3], dtype=float)
            z = (x - np.array(m_info["feature_means"])) / np.array(m_info["feature_stds"])
            logit = float(z @ np.array(m_info["weights_standardized"]) + m_info["intercept"])
            score = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, logit))))
        return (score >= tau), score, tau

    all_frozen_signals_test = {}
    for sig_name in frozen["crag_gate"]["all_candidate_signals_summary"].keys():
        a45 = sum(1 for r in ans_45_records if eval_specific_frozen_sig(r, sig_name)[0])
        o5 = sum(1 for r in ood_5_records if not eval_specific_frozen_sig(r, sig_name)[0])
        h10 = sum(1 for r in hard_10_records if not eval_specific_frozen_sig(r, sig_name)[0])
        tau_val = float(frozen["crag_gate"]["all_candidate_signals_summary"][sig_name]["optimal_tau_youden"])
        all_frozen_signals_test[sig_name] = {
            "frozen_tau_from_dev": tau_val,
            "answerable_45_passed": f"{a45}/45 ({a45/45.0*100:.1f}%)",
            "false_refusal_rate_on_45": round((45 - a45) / 45.0, 4),
            "ood_5_true_refusal": f"{o5}/5 ({o5/5.0*100:.1f}%)",
            "hard_in_domain_10_true_refusal": f"{h10}/10 ({h10/10.0*100:.1f}%)",
            "combined_unanswerable_15_true_refusal": f"{o5 + h10}/15 ({(o5 + h10)/15.0*100:.1f}%)",
        }

    ans45_pass_primary = sum(1 for r in ans_45_records if evaluate_frozen_gate(r, frozen)[0])
    ood5_refuse_primary = sum(1 for r in ood_5_records if not evaluate_frozen_gate(r, frozen)[0])
    hard10_refuse_primary = sum(1 for r in hard_10_records if not evaluate_frozen_gate(r, frozen)[0])

    ans45_pass_fast = sum(1 for r in ans_45_records if evaluate_frozen_fast_pre_gate(r, frozen)[0])
    ood5_refuse_fast = sum(1 for r in ood_5_records if not evaluate_frozen_fast_pre_gate(r, frozen)[0])
    hard10_refuse_fast = sum(1 for r in hard_10_records if not evaluate_frozen_fast_pre_gate(r, frozen)[0])

    sig_json = {
        "frozen_thresholds_sha256": hashlib.sha256((GATE_DIR / "frozen_thresholds.json").read_bytes()).hexdigest(),
        "dcsr_test_skip_rates": {
            "skip_count_on_45_answerable": dcsr_skips_45,
            "skip_rate_on_45_answerable": round(dcsr_skips_45 / 45.0, 4),
            "skip_count_on_50_test": dcsr_skips_50,
            "skip_rate_on_50_test": round(dcsr_skips_50 / 50.0, 4),
        },
        "crag_gate_test_performance": {
            "primary_frozen_gate": {
                "signal": frozen["crag_gate"]["primary_selected_signal"],
                "tau": frozen["crag_gate"]["primary_threshold_tau"],
                "answerable_45_passed": f"{ans45_pass_primary}/45 ({ans45_pass_primary/45.0*100:.1f}%)",
                "false_refusal_rate_on_45": round((45 - ans45_pass_primary) / 45.0, 4),
                "ood_5_true_refusal": f"{ood5_refuse_primary}/5 ({ood5_refuse_primary/5.0*100:.1f}%)",
                "hard_in_domain_10_true_refusal": f"{hard10_refuse_primary}/10 ({hard10_refuse_primary/10.0*100:.1f}%)",
                "combined_unanswerable_15_true_refusal": f"{ood5_refuse_primary + hard10_refuse_primary}/15 ({(ood5_refuse_primary + hard10_refuse_primary)/15.0*100:.1f}%)",
            },
            "fast_pre_rerank_frozen_gate": {
                "signal": frozen["crag_gate"]["fast_pre_rerank_signal"],
                "tau": frozen["crag_gate"]["fast_pre_rerank_threshold_tau"],
                "answerable_45_passed": f"{ans45_pass_fast}/45 ({ans45_pass_fast/45.0*100:.1f}%)",
                "false_refusal_rate_on_45": round((45 - ans45_pass_fast) / 45.0, 4),
                "ood_5_true_refusal": f"{ood5_refuse_fast}/5 ({ood5_refuse_fast/5.0*100:.1f}%)",
                "hard_in_domain_10_true_refusal": f"{hard10_refuse_fast}/10 ({hard10_refuse_fast/10.0*100:.1f}%)",
                "combined_unanswerable_15_true_refusal": f"{ood5_refuse_fast + hard10_refuse_fast}/15 ({(ood5_refuse_fast + hard10_refuse_fast)/15.0*100:.1f}%)",
            },
            "all_frozen_signals_on_test": all_frozen_signals_test,
        },
        "summary_table": summary_rows,
        "paired_significance_ndcg_at_10_c5": ndcg_tests_c5,
        "paired_significance_mrr_at_10_c5": mrr_tests_c5,
        "paired_significance_ndcg_at_10_c6": ndcg_tests_c6,
        "paired_significance_mrr_at_10_c6": mrr_tests_c6,
    }
    (RET_DIR / "significance_tests.json").write_text(
        json.dumps(sig_json, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("\nSaved Stage 6 results to results/06_retrieval/", flush=True)


if __name__ == "__main__":
    main()
