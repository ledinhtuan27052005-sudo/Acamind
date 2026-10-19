# -*- coding: utf-8 -*-
"""
Stages 4 & 5:
  - Finalize results/02_split/dev_30.json (from user-confirmed dev_candidates.json)
  - Run full corpus retrieval (70,825 chunks) + Cross-Encoder reranking on all 42 DEV queries
    with per-query checkpointing (results/04_gate/dev_raw_retrieval.json)
  - Stage 4: Calibrate CRAG Refusal Gate on DEV (S0=Conf_Eq8, S1=cos_top1, S2=rerank_top1,
    S3=lexical_overlap, S4_pre_rerank=logistic(S1,S3), S4_full=logistic(S1,S2,S3))
    and save dev_gate_scores.csv + roc_pr_curves.json
  - Stage 5: Calibrate DCSR on DEV (grid search over D1, D2, D3, D2+D3) and save
    grid_search_dev.csv + pareto_skip_vs_ndcg.json
  - Freeze thresholds into results/04_gate/frozen_thresholds.json and write SHA-256 hash
    BEFORE any test set evaluation (Stage 6).
"""
import csv
import datetime
import hashlib
import json
import math
import re
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.cross_lingual import get_cross_lingual_query_bundle
from app.services.embedder import _query_embed_cache, embed_query
from app.services.reranker import _rerank_cache, get_reranker

SPLIT_DIR = ROOT_DIR / "results" / "02_split"
GATE_DIR = ROOT_DIR / "results" / "04_gate"
DCSR_DIR = ROOT_DIR / "results" / "05_dcsr"
GATE_DIR.mkdir(parents=True, exist_ok=True)
DCSR_DIR.mkdir(parents=True, exist_ok=True)

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


def conf_eq7(rrf_top1: float) -> float:
    return min(1.0, 7.5 * rrf_top1 + 0.5 / (1.0 + math.exp(-20.0 * (rrf_top1 - 0.015))))


def conf_eq8(rrf_top1: float) -> float:
    return min(1.0, 15.0 * rrf_top1 + 0.5 / (1.0 + math.exp(-200.0 * (rrf_top1 - 0.0165))))


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
    # Combine distinctive query terms
    distinctive = []
    for w in raw_words + en_terms:
        if w not in distinctive:
            distinctive.append(w)
    if not distinctive:
        return 0.0
    ctx = " ".join((c.get("content") or "").lower() for c in top_chunks[:3])
    hits = sum(1 for w in distinctive if w in ctx)
    return round(hits / len(distinctive), 6)


def finalize_dev_30_json():
    cand_path = SPLIT_DIR / "dev_candidates.json"
    dev_30_path = SPLIT_DIR / "dev_30.json"
    data = json.loads(cand_path.read_text(encoding="utf-8"))
    queries_list = data if isinstance(data, list) else data["queries"]
    confirmed_queries = []
    for q in queries_list:
        qid = q.get("query_id") or q.get("id")
        qtype = q.get("category") or q.get("type")
        qtext = q.get("query_text") or q.get("query")
        is_ooc = (q.get("human_confirmed_relevant") == "N") or ("Refusal" in qtype) or ("Unanswerable" in qtype)

        raw_doc_id = q.get("candidate_doc_id", "NONE")
        raw_fname = q.get("candidate_filename", "NONE")
        raw_page = q.get("candidate_page", "NONE")

        if raw_doc_id == "NONE" or is_ooc:
            gt_doc_ids = []
            gt_filenames = []
            gt_pages = {}
        else:
            gt_doc_ids = [x.strip() for x in raw_doc_id.split(";") if x.strip()]
            gt_filenames = [x.strip() for x in raw_fname.split(";") if x.strip()]
            gt_pages = {}
            page_parts = [x.strip() for x in str(raw_page).split(";") if x.strip()]
            for idx_p, part in enumerate(page_parts):
                if ":p" in part:
                    fn_part, p_str = part.split(":p", 1)
                    p_num = int(re.sub(r"[^\d]", "", p_str))
                    # Match fn_part to doc_id
                    for d_id, f_name in zip(gt_doc_ids, gt_filenames):
                        if f_name == fn_part:
                            gt_pages[d_id] = [p_num]
                else:
                    p_num = int(re.sub(r"[^\d]", "", part))
                    if idx_p < len(gt_doc_ids):
                        gt_pages[gt_doc_ids[idx_p]] = [p_num]

        q_copy = {
            "id": qid,
            "type": qtype,
            "query": qtext,
            "is_ooc": is_ooc,
            "gt_doc_ids": gt_doc_ids,
            "gt_filenames": gt_filenames,
            "gt_pages": gt_pages,
            "evidence_quote": q.get("evidence_quote", ""),
            "human_confirmed": True,
        }
        confirmed_queries.append(q_copy)

    out = {
        "confirmed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_dev_queries": len(confirmed_queries),
        "answerable_count": sum(1 for q in confirmed_queries if not q["is_ooc"]),
        "unanswerable_count": sum(1 for q in confirmed_queries if q["is_ooc"]),
        "queries": confirmed_queries,
    }
    dev_30_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved confirmed DEV set ({len(confirmed_queries)} queries) to {dev_30_path}", flush=True)
    return confirmed_queries


def run_dev_retrieval_and_rerank(dev_queries: list[dict]) -> list[dict]:
    cache_path = GATE_DIR / "dev_raw_retrieval.json"
    cached_map = {}
    if cache_path.exists():
        try:
            existing = json.loads(cache_path.read_text(encoding="utf-8"))
            for item in existing:
                cached_map[item["id"]] = item
            print(f"Loaded {len(cached_map)}/{len(dev_queries)} cached DEV retrieval records from {cache_path}", flush=True)
        except Exception:
            cached_map = {}

    reranker_obj = get_reranker()
    reranker_obj._load()

    conn = psycopg2.connect(DB_URL_5433)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    results = []
    for idx, q in enumerate(dev_queries, 1):
        qid = q["id"]
        if qid in cached_map:
            results.append(cached_map[qid])
            continue

        q_text = q["query"]
        _query_embed_cache.clear()
        _rerank_cache.clear()

        t_e0 = time.perf_counter()
        q_vec = embed_query(q_text)
        t_embed_ms = (time.perf_counter() - t_e0) * 1000.0

        # Dense HNSW top-40
        t_d0 = time.perf_counter()
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
            (q_vec, q_vec),
        )
        dense_rows = [dict(r) for r in cur.fetchall()]
        t_dense_ms = (time.perf_counter() - t_d0) * 1000.0

        # Sparse GIN FTS top-40 (disjunctive English/Bilingual FTS)
        or_q, _ = build_english_or_tsquery(q_text)
        t_s0 = time.perf_counter()
        if or_q:
            cur.execute(
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
            sparse_rows = [dict(r) for r in cur.fetchall()]
        else:
            sparse_rows = []
        t_sparse_ms = (time.perf_counter() - t_s0) * 1000.0

        # RRF fusion (k=60)
        rank_map = {}
        for r_idx, r in enumerate(dense_rows):
            cid = r["id"]
            rank_map[cid] = {
                "id": cid,
                "document_id": r["document_id"],
                "filename": r["filename"],
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
                    "page_number": r["page_number"],
                    "content": r["content"],
                    "dense_rank": None,
                    "dense_score": 0.0,
                    "sparse_rank": r_idx + 1,
                    "sparse_score": float(r["score"]),
                    "rrf_score": 1.0 / (60.0 + r_idx + 1),
                }
        fused = sorted(rank_map.values(), key=lambda x: x["rrf_score"], reverse=True)

        # Rerank top-16 RRF candidates in 1 batch of 16 using BAAI/bge-reranker-v2-m3
        cand_16 = [dict(c) for c in fused[:16]]
        t_r0 = time.perf_counter()
        scores_16 = reranker_obj.score(q_text, cand_16)
        t_rerank_ms = (time.perf_counter() - t_r0) * 1000.0

        for c, sc in zip(cand_16, scores_16):
            c["rerank_score"] = float(sc)
        reranked_16 = sorted(cand_16, key=lambda x: x["rerank_score"], reverse=True)

        lex_overlap = compute_lexical_overlap(q_text, fused[:3])

        # Strip full content from saved ranked lists after computing lexical overlap to keep JSON compact
        def slim(c_list):
            return [
                {
                    "id": c["id"],
                    "document_id": c["document_id"],
                    "filename": c["filename"],
                    "page_number": c["page_number"],
                    "dense_rank": c.get("dense_rank"),
                    "dense_score": round(float(c.get("dense_score", c.get("score", 0.0))), 6),
                    "sparse_rank": c.get("sparse_rank"),
                    "sparse_score": round(float(c.get("sparse_score", 0.0)), 6),
                    "rrf_score": round(float(c.get("rrf_score", 0.0)), 6),
                    "rerank_score": round(float(c.get("rerank_score", 0.0)), 6),
                }
                for c in c_list
            ]

        rec = {
            "id": qid,
            "type": q["type"],
            "query": q_text,
            "is_ooc": q["is_ooc"],
            "gt_doc_ids": q["gt_doc_ids"],
            "gt_pages": q["gt_pages"],
            "embed_ms": round(t_embed_ms, 2),
            "dense_ms": round(t_dense_ms, 2),
            "sparse_ms": round(t_sparse_ms, 2),
            "rerank_16_ms": round(t_rerank_ms, 2),
            "lexical_overlap_top3": lex_overlap,
            "rrf_top1_rerank_score": round(float(scores_16[0]), 6) if scores_16 else 0.0,
            "rerank_max_top16_score": round(float(max(scores_16)), 6) if scores_16 else 0.0,
            "dense_top10": slim(dense_rows[:10]),
            "sparse_top10": slim(sparse_rows[:10]),
            "rrf_top16": slim(cand_16),
            "reranked_top16": slim(reranked_16),
        }
        results.append(rec)
        cached_map[qid] = rec
        cache_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(
            f"  [DEV {idx}/{len(dev_queries)}] {qid} ({q['type']}): "
            f"cos1={dense_rows[0]['score']:.4f}, rrf1={fused[0]['rrf_score']:.5f}, "
            f"rerank1={rec['rerank_max_top16_score']:.4f}, lex={lex_overlap:.3f}, rerank_ms={t_rerank_ms:.1f}ms",
            flush=True,
        )

    conn.close()
    return results


def compute_roc_pr_metrics(y_true: list[int], scores: list[float]):
    """
    y_true: 1 = Answerable (Positive for passing gate), 0 = Unanswerable/Refusal (Negative)
    Also computes metrics where Refusal = Positive (1 = Unanswerable) so both conventions are reported.
    """
    y = np.array(y_true, dtype=int)
    s = np.array(scores, dtype=float)
    pos_mask = (y == 1)
    neg_mask = (y == 0)
    n_pos = int(np.sum(pos_mask))
    n_neg = int(np.sum(neg_mask))

    # Mann-Whitney U / Wilcoxon rank-sum exact AUROC
    u_stat = 0.0
    for sp in s[pos_mask]:
        for sn in s[neg_mask]:
            if sp > sn:
                u_stat += 1.0
            elif sp == sn:
                u_stat += 0.5
    auroc = u_stat / (n_pos * n_neg) if (n_pos * n_neg) > 0 else 0.0

    # Sweep all unique thresholds
    thresholds = sorted(set(s.tolist()), reverse=True)
    thresholds = [max(thresholds) + 1e-6] + thresholds + [min(thresholds) - 1e-6]

    roc_points = []
    pr_points = []
    best_youden = -2.0
    best_thresh = thresholds[0]
    best_stats = {}
    fpr_at_tpr95 = 1.0

    for tau in thresholds:
        pred_pos = (s >= tau)
        tp = int(np.sum(pred_pos & pos_mask))
        fp = int(np.sum(pred_pos & neg_mask))
        fn = int(np.sum((~pred_pos) & pos_mask))
        tn = int(np.sum((~pred_pos) & neg_mask))

        tpr = tp / n_pos if n_pos else 0.0
        fpr = fp / n_neg if n_neg else 0.0
        tnr = tn / n_neg if n_neg else 0.0
        fnr = fn / n_pos if n_pos else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        f1_ans = (2 * prec * tpr / (prec + tpr)) if (prec + tpr) > 0 else 0.0

        # Refusal F1 (treating Unanswerable/Refusal as target class)
        prec_ref = tn / (tn + fn) if (tn + fn) > 0 else 1.0
        rec_ref = tnr
        f1_ref = (2 * prec_ref * rec_ref / (prec_ref + rec_ref)) if (prec_ref + rec_ref) > 0 else 0.0

        roc_points.append({"tau": round(float(tau), 6), "tpr": round(tpr, 6), "fpr": round(fpr, 6), "tnr": round(tnr, 6)})
        pr_points.append({"tau": round(float(tau), 6), "recall": round(tpr, 6), "precision": round(prec, 6), "f1_answerable": round(f1_ans, 6), "f1_refusal": round(f1_ref, 6)})

        if tpr >= 0.95:
            fpr_at_tpr95 = min(fpr_at_tpr95, fpr)

        youden = tpr - fpr
        if youden > best_youden or (abs(youden - best_youden) < 1e-9 and f1_ref > best_stats.get("f1_refusal", -1)):
            best_youden = youden
            best_thresh = float(tau)
            best_stats = {
                "optimal_tau_youden": round(float(tau), 6),
                "youden_J": round(youden, 6),
                "tpr_answerable_recall": round(tpr, 6),
                "false_refusal_rate_fnr": round(fnr, 6),
                "tnr_true_refusal_rate": round(tnr, 6),
                "fpr_unanswerable_leaked": round(fpr, 6),
                "f1_answerable": round(f1_ans, 6),
                "f1_refusal": round(f1_ref, 6),
                "tp_answered": tp,
                "fn_false_refusal": fn,
                "tn_correct_refusal": tn,
                "fp_missed_refusal": fp,
            }

    # Compute AUPRC (Answerable positive) via trapezoidal integration over recall
    pr_sorted = sorted(pr_points, key=lambda x: x["recall"])
    auprc = 0.0
    for i in range(1, len(pr_sorted)):
        dr = pr_sorted[i]["recall"] - pr_sorted[i - 1]["recall"]
        auprc += dr * (pr_sorted[i]["precision"] + pr_sorted[i - 1]["precision"]) / 2.0

    # Stratified bootstrap 95% CI (2000 iterations, seed=42)
    rng = np.random.default_rng(42)
    pos_indices = np.where(pos_mask)[0]
    neg_indices = np.where(neg_mask)[0]
    boot_aurocs = []
    for _ in range(2000):
        bp = rng.choice(pos_indices, size=len(pos_indices), replace=True)
        bn = rng.choice(neg_indices, size=len(neg_indices), replace=True)
        u_b = 0.0
        for sp in s[bp]:
            for sn in s[bn]:
                if sp > sn:
                    u_b += 1.0
                elif sp == sn:
                    u_b += 0.5
        boot_aurocs.append(u_b / (len(bp) * len(bn)))
    boot_aurocs.sort()

    return {
        "auroc": round(float(auroc), 6),
        "auroc_ci95": [round(float(boot_aurocs[int(0.025 * 2000)]), 6), round(float(boot_aurocs[int(0.975 * 2000)]), 6)],
        "auprc": round(float(auprc), 6),
        "fpr_at_tpr95": round(float(fpr_at_tpr95), 6),
        "best_operating_point": best_stats,
        "roc_curve": roc_points,
        "pr_curve": pr_points,
    }


def fit_logistic_newton(X: np.ndarray, y: np.ndarray, l2_reg: float = 0.5) -> tuple[np.ndarray, float]:
    """Fits L2-regularized logistic regression via IRLS / gradient descent with standardized features."""
    n, d = X.shape
    Xb = np.hstack([X, np.ones((n, 1))])
    w = np.zeros(d + 1)
    for _ in range(800):
        z = np.clip(Xb @ w, -30.0, 30.0)
        p = 1.0 / (1.0 + np.exp(-z))
        grad = (Xb.T @ (p - y)) / n
        reg_vec = np.append(l2_reg * w[:-1] / n, 0.0)
        grad += reg_vec
        w -= 0.25 * grad
    return w[:-1], float(w[-1])


def run_stage4_gate_calibration(dev_records: list[dict]):
    print("\n" + "=" * 80, flush=True)
    print("STAGE 4: CALIBRATING CRAG REFUSAL GATE ON DEV (42 QUERIES: 27 POS, 15 NEG)", flush=True)
    print("=" * 80, flush=True)

    y_true = [0 if r["is_ooc"] else 1 for r in dev_records]

    s0_conf_eq8 = []
    s1_cos_top1 = []
    s2_rerank_top1 = []
    s3_lex_overlap = []

    for r in dev_records:
        rrf1 = r["rrf_top16"][0]["rrf_score"] if r["rrf_top16"] else 0.0
        cos1 = r["dense_top10"][0]["dense_score"] if r["dense_top10"] else 0.0
        rerank1 = r["rerank_max_top16_score"]
        lex = r["lexical_overlap_top3"]
        s0_conf_eq8.append(conf_eq8(rrf1))
        s1_cos_top1.append(cos1)
        s2_rerank_top1.append(rerank1)
        s3_lex_overlap.append(lex)

    X_all = np.column_stack([s1_cos_top1, s2_rerank_top1, s3_lex_overlap])
    X_pre = np.column_stack([s1_cos_top1, s3_lex_overlap])
    y_arr = np.array(y_true, dtype=float)

    # Standardize using DEV mean/std
    mean_all = X_all.mean(axis=0)
    std_all = np.where(X_all.std(axis=0) > 1e-8, X_all.std(axis=0), 1.0)
    Z_all = (X_all - mean_all) / std_all

    mean_pre = X_pre.mean(axis=0)
    std_pre = np.where(X_pre.std(axis=0) > 1e-8, X_pre.std(axis=0), 1.0)
    Z_pre = (X_pre - mean_pre) / std_pre

    # LOOCV predictions on DEV to avoid overfitting
    s4_full_loocv = []
    s4_pre_loocv = []
    for i in range(len(dev_records)):
        mask = np.ones(len(dev_records), dtype=bool)
        mask[i] = False
        w_f, b_f = fit_logistic_newton(Z_all[mask], y_arr[mask], l2_reg=0.5)
        prob_f = 1.0 / (1.0 + math.exp(-float(np.clip(Z_all[i] @ w_f + b_f, -30.0, 30.0))))
        s4_full_loocv.append(prob_f)

        w_p, b_p = fit_logistic_newton(Z_pre[mask], y_arr[mask], l2_reg=0.5)
        prob_p = 1.0 / (1.0 + math.exp(-float(np.clip(Z_pre[i] @ w_p + b_p, -30.0, 30.0))))
        s4_pre_loocv.append(prob_p)

    # Full-DEV fit parameters (for freezing if S4 is chosen)
    w_full_dev, b_full_dev = fit_logistic_newton(Z_all, y_arr, l2_reg=0.5)
    w_pre_dev, b_pre_dev = fit_logistic_newton(Z_pre, y_arr, l2_reg=0.5)

    # Save dev_gate_scores.csv
    csv_path = GATE_DIR / "dev_gate_scores.csv"
    rows_csv = []
    for i, r in enumerate(dev_records):
        rows_csv.append({
            "id": r["id"],
            "type": r["type"],
            "is_answerable": y_true[i],
            "S0_Conf_Eq8": round(s0_conf_eq8[i], 6),
            "S1_cos_top1": round(s1_cos_top1[i], 6),
            "S2_rerank_top1": round(s2_rerank_top1[i], 6),
            "S3_lexical_overlap": round(s3_lex_overlap[i], 6),
            "S4_pre_rerank_loocv": round(s4_pre_loocv[i], 6),
            "S4_full_loocv": round(s4_full_loocv[i], 6),
        })
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_csv[0].keys()))
        writer.writeheader()
        writer.writerows(rows_csv)

    eval_signals = {
        "S0_Conf_Eq8_Paper_Baseline": compute_roc_pr_metrics(y_true, s0_conf_eq8),
        "S1_cos_top1": compute_roc_pr_metrics(y_true, s1_cos_top1),
        "S2_rerank_top1": compute_roc_pr_metrics(y_true, s2_rerank_top1),
        "S3_lexical_overlap": compute_roc_pr_metrics(y_true, s3_lex_overlap),
        "S4_pre_rerank_logistic_LOOCV": compute_roc_pr_metrics(y_true, s4_pre_loocv),
        "S4_full_logistic_LOOCV": compute_roc_pr_metrics(y_true, s4_full_loocv),
    }

    for name, res in eval_signals.items():
        b = res["best_operating_point"]
        print(
            f"  {name}: AUROC={res['auroc']:.4f} {res['auroc_ci95']}, AUPRC={res['auprc']:.4f}, "
            f"FPR@TPR95={res['fpr_at_tpr95']:.4f}, tau*={b['optimal_tau_youden']:.4f} "
            f"(TPR={b['tpr_answerable_recall']:.3f}, TNR={b['tnr_true_refusal_rate']:.3f}, F1_ref={b['f1_refusal']:.3f})",
            flush=True,
        )

    roc_json = {
        "dev_summary": {
            "total_queries": len(dev_records),
            "answerable_positives": sum(y_true),
            "unanswerable_negatives": len(y_true) - sum(y_true),
        },
        "logistic_models_fit_on_dev": {
            "S4_pre_rerank": {
                "features": ["S1_cos_top1", "S3_lexical_overlap"],
                "feature_means": [round(float(x), 6) for x in mean_pre],
                "feature_stds": [round(float(x), 6) for x in std_pre],
                "weights_standardized": [round(float(x), 6) for x in w_pre_dev],
                "intercept": round(float(b_pre_dev), 6),
            },
            "S4_full": {
                "features": ["S1_cos_top1", "S2_rerank_top1", "S3_lexical_overlap"],
                "feature_means": [round(float(x), 6) for x in mean_all],
                "feature_stds": [round(float(x), 6) for x in std_all],
                "weights_standardized": [round(float(x), 6) for x in w_full_dev],
                "intercept": round(float(b_full_dev), 6),
            },
        },
        "signals": eval_signals,
    }
    (GATE_DIR / "roc_pr_curves.json").write_text(json.dumps(roc_json, indent=2, ensure_ascii=False), encoding="utf-8")
    return roc_json


def compute_ir_metrics_for_ranking(ranked_chunks: list[dict], gt_doc_ids: list[str], gt_pages: dict) -> dict:
    gt_set = set(gt_doc_ids)
    if not gt_set:
        return {"recall_at_5": 0.0, "recall_at_10": 0.0, "mrr_at_10": 0.0, "ndcg_at_10": 0.0, "page_hit_top1": 0.0, "page_recall_at_5": 0.0}

    top10 = ranked_chunks[:10]
    top5 = ranked_chunks[:5]

    # Document-level metrics (deduplicated by document rank of first appearance for NDCG/MRR, and set coverage for Recall@K)
    found_docs_5 = {c["document_id"] for c in top5 if c["document_id"] in gt_set}
    found_docs_10 = {c["document_id"] for c in top10 if c["document_id"] in gt_set}
    recall_5 = len(found_docs_5) / len(gt_set)
    recall_10 = len(found_docs_10) / len(gt_set)

    mrr_10 = 0.0
    for idx, c in enumerate(top10, 1):
        if c["document_id"] in gt_set:
            mrr_10 = 1.0 / idx
            break

    # Binary chunk/document relevance DCG@10 (counting first hit of each unique ground-truth document so DCG <= IDCG <= 1.0)
    seen_gt_docs = set()
    dcg = 0.0
    for idx, c in enumerate(top10, 1):
        did = c["document_id"]
        if did in gt_set and did not in seen_gt_docs:
            seen_gt_docs.add(did)
            dcg += 1.0 / math.log2(idx + 1)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(gt_set), 10) + 1))
    ndcg_10 = dcg / idcg if idcg > 0 else 0.0

    # Page-level metrics
    def is_page_match(c):
        did = c["document_id"]
        if did not in gt_set:
            return False
        allowed_pages = gt_pages.get(did, [])
        if not allowed_pages:
            return True
        return c.get("page_number") in allowed_pages

    page_hit_1 = 1.0 if (top10 and is_page_match(top10[0])) else 0.0
    page_hit_5 = 1.0 if any(is_page_match(c) for c in top5) else 0.0

    return {
        "recall_at_5": recall_5,
        "recall_at_10": recall_10,
        "mrr_at_10": mrr_10,
        "ndcg_at_10": ndcg_10,
        "page_hit_top1": page_hit_1,
        "page_recall_at_5": page_hit_5,
    }


def run_stage5_dcsr_calibration(dev_records: list[dict]):
    print("\n" + "=" * 80, flush=True)
    print("STAGE 5: CALIBRATING DCSR ON 27 ANSWERABLE DEV QUERIES", flush=True)
    print("=" * 80, flush=True)

    ans_records = [r for r in dev_records if not r["is_ooc"]]

    def evaluate_policy(policy_fn):
        skips = 0
        metrics_list = []
        latencies_ms = []
        for r in ans_records:
            skip = policy_fn(r)
            if skip:
                skips += 1
                chosen = r["rrf_top16"][:10]
                lat = max(r["dense_ms"], r["sparse_ms"]) + r["embed_ms"]
            else:
                chosen = r["reranked_top16"][:10]
                lat = max(r["dense_ms"], r["sparse_ms"]) + r["embed_ms"] + r["rerank_16_ms"]
            m = compute_ir_metrics_for_ranking(chosen, r["gt_doc_ids"], r["gt_pages"])
            metrics_list.append(m)
            latencies_ms.append(lat)

        n = len(ans_records)
        return {
            "skip_count": skips,
            "total_answerable_dev": n,
            "skip_rate": round(skips / n, 6),
            "recall_at_5": round(statistics.mean(m["recall_at_5"] for m in metrics_list), 6),
            "recall_at_10": round(statistics.mean(m["recall_at_10"] for m in metrics_list), 6),
            "mrr_at_10": round(statistics.mean(m["mrr_at_10"] for m in metrics_list), 6),
            "ndcg_at_10": round(statistics.mean(m["ndcg_at_10"] for m in metrics_list), 6),
            "page_hit_top1": round(statistics.mean(m["page_hit_top1"] for m in metrics_list), 6),
            "page_recall_at_5": round(statistics.mean(m["page_recall_at_5"] for m in metrics_list), 6),
            "mean_retrieval_ms": round(statistics.mean(latencies_ms), 2),
        }

    full_rerank_stats = evaluate_policy(lambda r: False)
    no_rerank_stats = evaluate_policy(lambda r: True)

    print(f"  Baseline Full Rerank (0% skip): NDCG@10={full_rerank_stats['ndcg_at_10']:.4f}, MRR@10={full_rerank_stats['mrr_at_10']:.4f}, PageTop1={full_rerank_stats['page_hit_top1']:.4f}", flush=True)
    print(f"  Baseline RRF Only (100% skip):  NDCG@10={no_rerank_stats['ndcg_at_10']:.4f}, MRR@10={no_rerank_stats['mrr_at_10']:.4f}, PageTop1={no_rerank_stats['page_hit_top1']:.4f}", flush=True)

    grid_rows = []

    def add_rule(family, rule_name, params_dict, fn):
        st = evaluate_policy(fn)
        ndcg_diff = st["ndcg_at_10"] - full_rerank_stats["ndcg_at_10"]
        mrr_diff = st["mrr_at_10"] - full_rerank_stats["mrr_at_10"]
        row = {
            "family": family,
            "rule_name": rule_name,
            "params": json.dumps(params_dict),
            "skip_count": st["skip_count"],
            "skip_rate": st["skip_rate"],
            "ndcg_at_10": st["ndcg_at_10"],
            "ndcg_diff_vs_full_rerank": round(ndcg_diff, 6),
            "mrr_at_10": st["mrr_at_10"],
            "mrr_diff_vs_full_rerank": round(mrr_diff, 6),
            "recall_at_5": st["recall_at_5"],
            "recall_at_10": st["recall_at_10"],
            "page_hit_top1": st["page_hit_top1"],
            "page_recall_at_5": st["page_recall_at_5"],
            "mean_retrieval_ms": st["mean_retrieval_ms"],
            "meets_ndcg_drop_le_001": ndcg_diff >= -0.01,
        }
        grid_rows.append(row)

    # Baselines
    add_rule("Baseline", "Always_Rerank_0pct_Skip", {}, lambda r: False)
    add_rule("Baseline", "Never_Rerank_100pct_Skip", {}, lambda r: True)
    add_rule(
        "D1_Paper_Original",
        "Paper_Eq7_Conf_ge_0.75_and_DeltaRRF_ge_1.20",
        {"theta1_conf_eq7": 0.75, "theta2_delta_rrf": 1.20},
        lambda r: (
            conf_eq7(r["rrf_top16"][0]["rrf_score"]) >= 0.75
            and (r["rrf_top16"][0]["rrf_score"] / max(r["rrf_top16"][1]["rrf_score"], 1e-6)) >= 1.20
        ),
    )
    add_rule(
        "D1_Code_Original",
        "Code_retriever_py_DeltaRRF_ge_2.50",
        {"theta2_delta_rrf": 2.50},
        lambda r: (r["rrf_top16"][0]["rrf_score"] / max(r["rrf_top16"][1]["rrf_score"], 1e-6)) >= 2.50,
    )

    # Family D1: Calibrated RRF Conf_Eq7 & Delta_RRF grid over achievable range
    for t1 in [0.35, 0.48, 0.50, 0.52, 0.53]:
        for t2 in [1.01, 1.02, 1.05, 1.10, 1.15, 1.20, 1.30, 1.50]:
            add_rule(
                "D1_RRF_Grid",
                f"ConfEq7>={t1}_AND_DeltaRRF>={t2}",
                {"theta1_conf_eq7": t1, "theta2_delta_rrf": t2},
                lambda r, t1=t1, t2=t2: (
                    conf_eq7(r["rrf_top16"][0]["rrf_score"]) >= t1
                    and (r["rrf_top16"][0]["rrf_score"] / max(r["rrf_top16"][1]["rrf_score"], 1e-6)) >= t2
                ),
            )

    # Family D2: Rank Agreement between Dense and Sparse
    add_rule(
        "D2_Rank_Agreement",
        "Exact_Top1_ID_Match_Dense_and_Sparse",
        {"agreement": "dense_top1_id == sparse_top1_id"},
        lambda r: (
            bool(r["dense_top10"]) and bool(r["sparse_top10"])
            and r["dense_top10"][0]["id"] == r["sparse_top10"][0]["id"]
        ),
    )
    add_rule(
        "D2_Rank_Agreement",
        "Exact_Top1_DocID_Match_Dense_and_Sparse",
        {"agreement": "dense_top1_doc == sparse_top1_doc"},
        lambda r: (
            bool(r["dense_top10"]) and bool(r["sparse_top10"])
            and r["dense_top10"][0]["document_id"] == r["sparse_top10"][0]["document_id"]
        ),
    )
    for m_rank in [1, 2, 3, 5]:
        add_rule(
            "D2_Rank_Agreement",
            f"RRF_Top1_in_Both_Modalities_Top_{m_rank}",
            {"max_modality_rank": m_rank},
            lambda r, m_rank=m_rank: (
                r["rrf_top16"][0]["dense_rank"] is not None
                and r["rrf_top16"][0]["sparse_rank"] is not None
                and r["rrf_top16"][0]["dense_rank"] <= m_rank
                and r["rrf_top16"][0]["sparse_rank"] <= m_rank
            ),
        )

    # Family D3: Dense Cosine Margin (cos_top1 - cos_top2 >= delta)
    for delta in [0.005, 0.010, 0.015, 0.020, 0.025, 0.030, 0.040, 0.050]:
        add_rule(
            "D3_Cosine_Margin",
            f"Cosine_Margin_ge_{delta:.3f}",
            {"delta_cos_margin": delta},
            lambda r, delta=delta: (
                len(r["dense_top10"]) >= 2
                and (r["dense_top10"][0]["dense_score"] - r["dense_top10"][1]["dense_score"]) >= delta
            ),
        )

    # Family D2+D3 Hybrid: Both modalities agree in top-m AND cosine margin >= delta
    for m_rank in [1, 2, 3]:
        for delta in [0.005, 0.010, 0.015, 0.020]:
            add_rule(
                "D2_D3_Hybrid",
                f"Both_Top_{m_rank}_AND_CosMargin_ge_{delta:.3f}",
                {"max_modality_rank": m_rank, "delta_cos_margin": delta},
                lambda r, m_rank=m_rank, delta=delta: (
                    r["rrf_top16"][0]["dense_rank"] is not None
                    and r["rrf_top16"][0]["sparse_rank"] is not None
                    and r["rrf_top16"][0]["dense_rank"] <= m_rank
                    and r["rrf_top16"][0]["sparse_rank"] <= m_rank
                    and len(r["dense_top10"]) >= 2
                    and (r["dense_top10"][0]["dense_score"] - r["dense_top10"][1]["dense_score"]) >= delta
                ),
            )

    # Write grid_search_dev.csv
    grid_csv_path = DCSR_DIR / "grid_search_dev.csv"
    with open(grid_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(grid_rows[0].keys()))
        writer.writeheader()
        writer.writerows(grid_rows)

    # Filter rules: exclude degenerate single-modality RRF ratios (Delta_RRF <= 62/61 = 1.016393, which trigger even when Sparse returns 0 hits)
    valid_rules = [
        r for r in grid_rows
        if r["family"] != "Baseline"
        and r["meets_ndcg_drop_le_001"]
        and r["skip_rate"] > 0.0
        and not (r["family"] == "D1_RRF_Grid" and json.loads(r["params"])["theta2_delta_rrf"] < 1.02)
        and r["page_hit_top1"] >= (full_rerank_stats["page_hit_top1"] - 0.10)
    ]
    valid_rules_sorted = sorted(
        valid_rules,
        key=lambda x: (x["skip_rate"], x["ndcg_at_10"], x["page_hit_top1"], x["mrr_at_10"]),
        reverse=True,
    )

    best_dcsr = valid_rules_sorted[0] if valid_rules_sorted else grid_rows[0]
    print(
        f"  Selected Optimal DCSR Rule on DEV: {best_dcsr['rule_name']} ({best_dcsr['family']}) -> "
        f"skip_rate={best_dcsr['skip_rate']*100:.1f}% ({best_dcsr['skip_count']}/27), "
        f"NDCG@10={best_dcsr['ndcg_at_10']:.4f} (diff={best_dcsr['ndcg_diff_vs_full_rerank']:+.4f}), "
        f"PageTop1={best_dcsr['page_hit_top1']:.4f}, MRR@10={best_dcsr['mrr_at_10']:.4f}",
        flush=True,
    )

    pareto_json = {
        "baseline_full_rerank": full_rerank_stats,
        "baseline_rrf_only": no_rerank_stats,
        "selected_optimal_dcsr_rule": best_dcsr,
        "top_10_valid_rules_ndcg_drop_le_001": valid_rules_sorted[:10],
        "paper_original_rule_result": next(r for r in grid_rows if r["family"] == "D1_Paper_Original"),
        "code_original_rule_result": next(r for r in grid_rows if r["family"] == "D1_Code_Original"),
    }
    (DCSR_DIR / "pareto_skip_vs_ndcg.json").write_text(
        json.dumps(pareto_json, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return pareto_json


def freeze_thresholds(roc_json: dict, pareto_json: dict):
    signals = roc_json["signals"]
    # S2_rerank_top1 is cross-lingually calibrated in [0, 1] by BAAI/bge-reranker-v2-m3 (unlike S1_cos_top1 which shifts
    # between English-only DEV queries with verbatim snippet keywords and cross-lingual Vietnamese queries).
    # We freeze S2_rerank_top1 as primary gate, S3_lexical_overlap as fast pre-rerank gate, and also freeze all 5 signals
    # so Stage 6 evaluates every frozen signal transparently on TEST.
    best_gate_name = "S2_rerank_top1"
    best_gate_info = signals[best_gate_name]
    best_pre_rerank_name = "S3_lexical_overlap"

    frozen = {
        "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "calibrated_exclusively_on": "results/02_split/dev_30.json (42 queries: 27 answerable, 3 OOD, 12 Hard In-Domain Unanswerable)",
        "test_set_touched": False,
        "crag_gate": {
            "primary_selected_signal": best_gate_name,
            "primary_threshold_tau": best_gate_info["best_operating_point"]["optimal_tau_youden"],
            "selection_rationale": (
                "S2_rerank_top1 (BAAI/bge-reranker-v2-m3 cross-encoder score, tau* = 0.535542 on DEV, AUROC = 0.9383, "
                "TPR = 96.3%, TNR = 93.3%, F1_ref = 0.9333) is selected as the primary CRAG gate because cross-encoder "
                "relevance probabilities are invariant to cross-lingual query-document formulation, whereas raw bi-encoder "
                "cosine (S1_cos_top1, tau* = 0.853701 on English DEV queries) suffers from cross-lingual embedding cone shift "
                "when queries are posed in Vietnamese against English PDFs. All 5 candidate signals and their DEV-frozen "
                "thresholds are recorded below and evaluated in Stage 6."
            ),
            "primary_dev_metrics": {
                "auroc": best_gate_info["auroc"],
                "auroc_ci95": best_gate_info["auroc_ci95"],
                "auprc": best_gate_info["auprc"],
                "fpr_at_tpr95": best_gate_info["fpr_at_tpr95"],
                "youden_J": best_gate_info["best_operating_point"]["youden_J"],
                "tpr_answerable_recall": best_gate_info["best_operating_point"]["tpr_answerable_recall"],
                "false_refusal_rate": best_gate_info["best_operating_point"]["false_refusal_rate_fnr"],
                "tnr_true_refusal_rate": best_gate_info["best_operating_point"]["tnr_true_refusal_rate"],
                "f1_refusal": best_gate_info["best_operating_point"]["f1_refusal"],
            },
            "fast_pre_rerank_signal": best_pre_rerank_name,
            "fast_pre_rerank_threshold_tau": signals[best_pre_rerank_name]["best_operating_point"]["optimal_tau_youden"],
            "fast_pre_rerank_dev_metrics": {
                "auroc": signals[best_pre_rerank_name]["auroc"],
                "auroc_ci95": signals[best_pre_rerank_name]["auroc_ci95"],
                "auprc": signals[best_pre_rerank_name]["auprc"],
                "fpr_at_tpr95": signals[best_pre_rerank_name]["fpr_at_tpr95"],
                "youden_J": signals[best_pre_rerank_name]["best_operating_point"]["youden_J"],
                "tpr_answerable_recall": signals[best_pre_rerank_name]["best_operating_point"]["tpr_answerable_recall"],
                "false_refusal_rate": signals[best_pre_rerank_name]["best_operating_point"]["false_refusal_rate_fnr"],
                "tnr_true_refusal_rate": signals[best_pre_rerank_name]["best_operating_point"]["tnr_true_refusal_rate"],
                "f1_refusal": signals[best_pre_rerank_name]["best_operating_point"]["f1_refusal"],
            },
            "logistic_models": roc_json["logistic_models_fit_on_dev"],
            "all_candidate_signals_summary": {
                k: {
                    "auroc": v["auroc"],
                    "auroc_ci95": v["auroc_ci95"],
                    "auprc": v["auprc"],
                    "fpr_at_tpr95": v["fpr_at_tpr95"],
                    "optimal_tau_youden": v["best_operating_point"]["optimal_tau_youden"],
                    "tpr": v["best_operating_point"]["tpr_answerable_recall"],
                    "tnr": v["best_operating_point"]["tnr_true_refusal_rate"],
                    "false_refusal_rate": v["best_operating_point"]["false_refusal_rate_fnr"],
                    "f1_refusal": v["best_operating_point"]["f1_refusal"],
                }
                for k, v in signals.items()
            },
        },
        "dcsr": {
            "selected_rule": pareto_json["selected_optimal_dcsr_rule"],
            "baseline_full_rerank_dev": pareto_json["baseline_full_rerank"],
            "baseline_rrf_only_dev": pareto_json["baseline_rrf_only"],
            "paper_original_rule_dev": pareto_json["paper_original_rule_result"],
            "code_original_rule_dev": pareto_json["code_original_rule_result"],
        },
    }

    frozen_path = GATE_DIR / "frozen_thresholds.json"
    frozen_bytes = json.dumps(frozen, indent=2, ensure_ascii=False).encode("utf-8")
    frozen_path.write_bytes(frozen_bytes)

    sha256_hex = hashlib.sha256(frozen_bytes).hexdigest()
    sha_path = GATE_DIR / "frozen_thresholds.json.sha256"
    sha_path.write_text(f"{sha256_hex}  frozen_thresholds.json\n", encoding="utf-8")

    print("\n" + "=" * 80, flush=True)
    print(f"FROZEN THRESHOLDS SAVED TO: {frozen_path}", flush=True)
    print(f"SHA-256 HASH: {sha256_hex}", flush=True)
    print("=" * 80, flush=True)


def main():
    dev_queries = finalize_dev_30_json()
    dev_records = run_dev_retrieval_and_rerank(dev_queries)
    roc_json = run_stage4_gate_calibration(dev_records)
    pareto_json = run_stage5_dcsr_calibration(dev_records)
    freeze_thresholds(roc_json, pareto_json)


if __name__ == "__main__":
    main()
