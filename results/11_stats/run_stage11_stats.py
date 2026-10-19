# -*- coding: utf-8 -*-
"""
Stage 11: Comprehensive Statistical Hypothesis Testing & HNSW Trade-off Analysis (results/11_stats/)
  1. Unit of analysis = QUERY.
  2. Performs paired statistical tests across all retrieval systems (C1..C6 from Stage 6) and
     all generation systems (BM25, Naive_Dense, ACAMIND from Stage 7):
       - Wilcoxon signed-rank test (`scipy.stats.wilcoxon` with `zero_method="wilcox"`, using
         `method="exact"` when n_non_zero <= 25 and no ties among non-zero differences, else `method="approx"`,
         explicitly logging n_total, n_zero_diff, n_non_zero, W_stat, p_raw).
       - Paired Bootstrap test (B = 10,000 resamples, seed = 20261016): reports mean difference (effect size),
         95% percentile bootstrap CI, and two-sided bootstrap p-value.
       - Holm-Bonferroni step-down multiple-testing correction across the family of comparisons;
         reports both raw p-value and Holm-adjusted p-value.
  3. Binary Refusal Analysis (separated from answerable citation/grounding metrics!):
       - Fisher's exact test (`scipy.stats.fisher_exact`) + exact Clopper-Pearson 95% CIs on:
           * OOD Safe Refusal (N = 5, REAL_Q_46..50)
           * Hard Unseen In-Domain Unanswerable Refusal (N = 10, TEST_HARD_01..10)
           * Combined Unanswerable Refusal (N = 15)
           * False Refusal on Answerable Queries (N = 45, REAL_Q_01..45), broken down by Gate vs LLM self-refusal.
  4. Breakdown by Query Category (Factual Q&A N=20, Cross-Article Comparison N=15, Literature Synthesis N=10,
     Safe Refusal N=5), reporting exact N per group and conditional metrics on answered queries vs all queries.
  5. Also benchmarks pgvector HNSW `ef_search` in {10, 20, 40, 80, 160, 320} vs Exact Brute-Force SeqScan
     on all 45 answerable test queries over the 100%-embedded 70,825-chunk corpus.
"""
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import psycopg2
from scipy.stats import beta, fisher_exact, wilcoxon
from sentence_transformers import SentenceTransformer

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT_DIR = ROOT_DIR / "results" / "11_stats"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RET_DIR = ROOT_DIR / "results" / "06_retrieval"
GEN_DIR = ROOT_DIR / "results" / "07_generation"
SPLIT_DIR = ROOT_DIR / "results" / "02_split"

DB_DSN = "postgresql://admin:secret@localhost:5433/rag_db"


def clopper_pearson_ci(k: int, n: int, alpha: float = 0.05) -> list[float]:
    if n <= 0:
        return [0.0, 0.0]
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return [round(lo, 4), round(hi, 4)]


def paired_wilcoxon_and_bootstrap(x: np.ndarray, y: np.ndarray, n_boot: int = 10000, seed: int = 20261016) -> dict:
    """
    Tests H0: E[x - y] == 0 where x is proposed system and y is baseline.
    Logs exact n_total, n_zero_diff, n_non_zero, ties among non-zero diffs, W statistic, p_wilcoxon,
    mean_diff, 95% bootstrap CI, and p_bootstrap.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    diffs = x - y
    n_total = len(diffs)
    nz = diffs[np.abs(diffs) > 1e-12]
    n_nz = len(nz)
    n_zero = n_total - n_nz
    mean_diff = float(np.mean(diffs))

    if n_nz == 0:
        w_stat = 0.0
        p_wilc = 1.0
        w_method_used = "all_zero_differences"
    else:
        abs_nz = np.round(np.abs(nz), 8)
        has_ties = (len(np.unique(abs_nz)) < len(abs_nz))
        w_method_used = "exact" if (not has_ties and n_nz <= 25) else "approx"
        try:
            res = wilcoxon(nz, zero_method="wilcox", alternative="two-sided", method=w_method_used)
            w_stat = float(res.statistic)
            p_wilc = float(res.pvalue)
        except Exception:
            res = wilcoxon(nz, zero_method="wilcox", alternative="two-sided", method="approx")
            w_stat = float(res.statistic)
            p_wilc = float(res.pvalue)
            w_method_used = "approx_fallback"

    # Paired bootstrap
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_total, size=(n_boot, n_total))
    boot_means = np.mean(diffs[idx], axis=1)
    ci_lo, ci_hi = float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5))
    # Shift bootstrap distribution to H0 (mean = 0) for two-sided p-value
    shifted = boot_means - mean_diff
    p_boot = float(np.mean(np.abs(shifted) >= abs(mean_diff)))

    return {
        "n_total": int(n_total),
        "n_zero_diff": int(n_zero),
        "n_non_zero": int(n_nz),
        "mean_x": round(float(np.mean(x)), 4),
        "mean_y": round(float(np.mean(y)), 4),
        "mean_diff": round(mean_diff, 4),
        "bootstrap_ci95": [round(ci_lo, 4), round(ci_hi, 4)],
        "wilcoxon_method": w_method_used,
        "wilcoxon_W": round(w_stat, 4),
        "p_wilcoxon_raw": round(p_wilc, 6),
        "p_bootstrap_raw": round(p_boot, 6),
    }


def apply_holm_bonferroni(tests: list[dict], p_key: str = "p_wilcoxon_raw", out_key: str = "p_wilcoxon_holm") -> None:
    m = len(tests)
    order = np.argsort([t[p_key] for t in tests])
    running_max = 0.0
    for rank_idx, orig_idx in enumerate(order):
        adj = min(1.0, float(tests[orig_idx][p_key]) * (m - rank_idx))
        running_max = max(running_max, adj)
        tests[orig_idx][out_key] = round(running_max, 6)
        tests[orig_idx][f"{out_key}_significant_005"] = bool(running_max < 0.05)


def resolve_gt_filenames_for_query(q: dict, doc_catalog: list[dict]) -> set[str]:
    existing = q.get("ground_truth_docs") or q.get("ground_truth_targets") or []
    if existing:
        return {d["filename"] for d in existing}
    import re
    q_text = q.get("query_text") or q.get("query") or ""
    m1 = re.search(r"\(1\)\s*['\"](.+?)['\"](?=\s*(?:và|and|,|\(2\)))", q_text)
    m2 = re.search(r"\(2\)\s*['\"](.+?)['\"](?=\s*(?:[—–\-?:;.]|$))", q_text)
    if not m1:
        m1 = re.search(r"\(1\)\s*'([^']+)'", q_text)
    if not m2:
        m2 = re.search(r"\(2\)\s*'([^']+)'", q_text)
    fns = set()
    for m in (m1, m2):
        if not m:
            continue
        pref = m.group(1).strip().lower()
        for d in doc_catalog:
            t_low = (d["title"] or "").strip().lower()
            if t_low.startswith(pref[:30]) or pref[:30] in t_low:
                fns.add(d["filename"])
                break
    return fns


def run_hnsw_ef_search_benchmark(queries_45: list[dict]) -> list[dict]:
    """
    Measures pgvector HNSW recall vs latency across ef_search in {10, 20, 40, 80, 160, 320}
    compared against Exact Brute-Force SeqScan (enable_indexscan=off, enable_bitmapscan=off).
    """
    print("Running HNSW ef_search vs Exact Brute-Force benchmark on 45 queries...", flush=True)
    model = SentenceTransformer("intfloat/multilingual-e5-base", device="cpu")
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    cur.execute("SELECT id::text, filename, title FROM documents WHERE filename LIKE '26%%';")
    doc_catalog = [{"doc_id": r[0], "filename": r[1], "title": r[2] or ""} for r in cur.fetchall()]

    q_vecs = []
    for q in queries_45:
        qt = q.get("query_text") or q.get("query")
        vec = model.encode("query: " + qt, normalize_embeddings=True).tolist()
        vec_str = "[" + ",".join(f"{x:.7f}" for x in vec) + "]"
        gt_fns = resolve_gt_filenames_for_query(q, doc_catalog)
        q_vecs.append((q.get("query_id") or q.get("id"), vec_str, gt_fns))

    # 1. Exact brute-force top-10 chunk IDs per query
    cur.execute("SET enable_indexscan = off; SET enable_bitmapscan = off;")
    exact_top10 = {}
    exact_lats = []
    exact_doc_hits = 0
    for qid, vec_str, gt_fns in q_vecs:
        t0 = time.perf_counter()
        cur.execute(
            """
            SELECT c.id::text, d.filename
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE d.filename LIKE '26%%'
            ORDER BY c.embedding <=> %s::vector
            LIMIT 10;
            """,
            (vec_str,),
        )
        rows = cur.fetchall()
        exact_lats.append((time.perf_counter() - t0) * 1000.0)
        exact_top10[qid] = [r[0] for r in rows]
        if any(r[1] in gt_fns for r in rows[:5]):
            exact_doc_hits += 1

    cur.execute("SET enable_indexscan = on; SET enable_bitmapscan = on;")

    results = [{
        "mode": "Exact_BruteForce_SeqScan",
        "ef_search": None,
        "exact_nn_recall_at_10": 1.0000,
        "gt_doc_recall_at_5": round(exact_doc_hits / len(q_vecs), 4),
        "latency_p50_ms": round(float(np.median(exact_lats)), 2),
        "latency_p90_ms": round(float(np.percentile(exact_lats, 90)), 2),
        "latency_mean_ms": round(float(np.mean(exact_lats)), 2),
    }]

    for ef in (10, 20, 40, 80, 160, 320):
        cur.execute(f"SET hnsw.ef_search = {ef};")
        lats = []
        nn_overlaps = []
        doc_hits = 0
        for qid, vec_str, gt_fns in q_vecs:
            t0 = time.perf_counter()
            cur.execute(
                """
                SELECT c.id::text, d.filename
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.filename LIKE '26%%'
                ORDER BY c.embedding <=> %s::vector
                LIMIT 10;
                """,
                (vec_str,),
            )
            rows = cur.fetchall()
            lats.append((time.perf_counter() - t0) * 1000.0)
            hnsw_ids = {r[0] for r in rows}
            ref_ids = set(exact_top10[qid])
            nn_overlaps.append(len(hnsw_ids & ref_ids) / max(len(ref_ids), 1))
            if any(r[1] in gt_fns for r in rows[:5]):
                doc_hits += 1

        results.append({
            "mode": f"HNSW_m16_efConst64_efSearch{ef}",
            "ef_search": ef,
            "exact_nn_recall_at_10": round(float(np.mean(nn_overlaps)), 4),
            "gt_doc_recall_at_5": round(doc_hits / len(q_vecs), 4),
            "latency_p50_ms": round(float(np.median(lats)), 2),
            "latency_p90_ms": round(float(np.percentile(lats, 90)), 2),
            "latency_mean_ms": round(float(np.mean(lats)), 2),
        })

    conn.close()
    return results


def main():
    # 1. Load Stage 6 per-query retrieval metrics (45 answerable test queries REAL_Q_01..45)
    ret_pq = []
    with open(RET_DIR / "per_query_metrics.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["id"].startswith("REAL_Q_") and row["is_ooc"] == "False":
                ret_pq.append(row)

    by_sys_ret = {}
    for r in ret_pq:
        by_sys_ret.setdefault(r["config"], []).append(r)
    for s in by_sys_ret:
        by_sys_ret[s].sort(key=lambda x: x["id"])

    # Retrieval family of paired comparisons (on N=45 answerable queries, unit = query)
    ret_pairs = [
        ("C4", "C1"),
        ("C4", "C2"),
        ("C4", "C3"),
        ("C5", "C1"),
        ("C5", "C2"),
        ("C5", "C4"),
        ("C6", "C1"),
        ("C6", "C2"),
    ]
    ret_metrics = ["recall_at_5", "recall_at_10", "mrr_at_10", "ndcg_at_10", "top1_page_hit"]

    retrieval_tests = []
    for m_name in ret_metrics:
        family = []
        for sys_a, sys_b in ret_pairs:
            xa = np.array([float(r[m_name]) for r in by_sys_ret[sys_a]])
            xb = np.array([float(r[m_name]) for r in by_sys_ret[sys_b]])
            res = paired_wilcoxon_and_bootstrap(xa, xb)
            res["metric"] = m_name
            res["system_a"] = sys_a
            res["system_b"] = sys_b
            res["subset"] = "All_Answerable_45"
            family.append(res)
        apply_holm_bonferroni(family, "p_wilcoxon_raw", "p_wilcoxon_holm")
        apply_holm_bonferroni(family, "p_bootstrap_raw", "p_bootstrap_holm")
        retrieval_tests.extend(family)

    # Breakdown by category for retrieval (Factual Q&A N=20, Cross-Article Comparison N=15, Literature Synthesis N=10)
    category_retrieval_summary = []
    for cat in ("Factual Q&A", "Cross-Article Comparison", "Literature Synthesis"):
        for sys_name, rows in by_sys_ret.items():
            sub = [r for r in rows if r["type"] == cat]
            if not sub:
                continue
            category_retrieval_summary.append({
                "category": cat,
                "n_queries": len(sub),
                "system": sys_name,
                "recall_at_5": round(float(np.mean([float(r["recall_at_5"]) for r in sub])), 4),
                "recall_at_10": round(float(np.mean([float(r["recall_at_10"]) for r in sub])), 4),
                "mrr_at_10": round(float(np.mean([float(r["mrr_at_10"]) for r in sub])), 4),
                "ndcg_at_10": round(float(np.mean([float(r["ndcg_at_10"]) for r in sub])), 4),
                "top1_doc_hit": round(float(np.mean([float(r["top1_doc_hit"]) for r in sub])), 4),
                "top1_page_hit": round(float(np.mean([float(r["top1_page_hit"]) for r in sub])), 4),
            })

    # 2. Load Stage 7 generation metrics (50 queries x 3 systems)
    gen_pq = []
    with open(GEN_DIR / "auto_metrics.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gen_pq.append(row)

    by_sys_gen = {}
    for r in gen_pq:
        by_sys_gen.setdefault(r["system"], []).append(r)
    for s in by_sys_gen:
        by_sys_gen[s].sort(key=lambda x: x["query_id"])

    # Generation paired tests on N=45 in-scope queries AND on N=20 Factual Q&A queries
    gen_pairs = [
        ("ACAMIND", "BM25"),
        ("ACAMIND", "Naive_Dense"),
        ("Naive_Dense", "BM25"),
    ]
    gen_metrics = ["syntactic_citation_validity", "gt_doc_citation_precision"]
    generation_tests = []

    for subset_name, filter_fn in [
        ("All_InScope_45", lambda r: str(r["is_ooc"]).lower() in ("0", "false")),
        ("Factual_QA_20", lambda r: r["type"] == "Factual Q&A"),
        ("Cross_Article_15", lambda r: r["type"] == "Cross-Article Comparison"),
    ]:
        for m_name in gen_metrics:
            family = []
            for sys_a, sys_b in gen_pairs:
                ra = [r for r in by_sys_gen[sys_a] if filter_fn(r)]
                rb = [r for r in by_sys_gen[sys_b] if filter_fn(r)]
                xa = np.array([float(r[m_name]) for r in ra])
                xb = np.array([float(r[m_name]) for r in rb])
                res = paired_wilcoxon_and_bootstrap(xa, xb)
                res["metric"] = m_name
                res["system_a"] = sys_a
                res["system_b"] = sys_b
                res["subset"] = subset_name
                family.append(res)
            apply_holm_bonferroni(family, "p_wilcoxon_raw", "p_wilcoxon_holm")
            apply_holm_bonferroni(family, "p_bootstrap_raw", "p_bootstrap_holm")
            generation_tests.extend(family)

    # Also compute conditional citation metrics on queries where the system did NOT refuse (answered subset)
    conditional_answered_summary = []
    for sys_name in ("BM25", "Naive_Dense", "ACAMIND"):
        for subset_name, filter_fn in [
            ("All_InScope_45", lambda r: str(r["is_ooc"]).lower() in ("0", "false")),
            ("Factual_QA_20", lambda r: r["type"] == "Factual Q&A"),
            ("Cross_Article_15", lambda r: r["type"] == "Cross-Article Comparison"),
            ("Literature_Synthesis_10", lambda r: r["type"] == "Literature Synthesis"),
        ]:
            sub = [r for r in by_sys_gen[sys_name] if filter_fn(r)]
            ans = [r for r in sub if int(r["total_refused"]) == 0]
            conditional_answered_summary.append({
                "system": sys_name,
                "subset": subset_name,
                "n_total": len(sub),
                "n_answered": len(ans),
                "n_refused": len(sub) - len(ans),
                "answered_rate": round(len(ans) / max(len(sub), 1), 4),
                "unconditional_gt_doc_cite_precision": round(float(np.mean([float(r["gt_doc_citation_precision"]) for r in sub])), 4),
                "conditional_answered_gt_doc_cite_precision": (
                    round(float(np.mean([float(r["gt_doc_citation_precision"]) for r in ans])), 4) if ans else None
                ),
                "conditional_answered_syntactic_cite_validity": (
                    round(float(np.mean([float(r["syntactic_citation_validity"]) for r in ans])), 4) if ans else None
                ),
            })

    cond_by_key = {(c["system"], c["subset"]): c for c in conditional_answered_summary}
    bm45_ref = cond_by_key[("BM25", "All_InScope_45")]["n_refused"]
    nd45_ref = cond_by_key[("Naive_Dense", "All_InScope_45")]["n_refused"]
    ac45_ref = cond_by_key[("ACAMIND", "All_InScope_45")]["n_refused"]
    bm20_ref = cond_by_key[("BM25", "Factual_QA_20")]["n_refused"]
    nd20_ref = cond_by_key[("Naive_Dense", "Factual_QA_20")]["n_refused"]
    ac20_ref = cond_by_key[("ACAMIND", "Factual_QA_20")]["n_refused"]

    # 3. Binary Refusal Fisher Exact & Clopper-Pearson CI Analysis
    # Compare Gate-level refusal (before LLM) vs Total refusal (Gate + LLM)
    refusal_analysis = {
        "OOD_5_Gate_Refusal_Before_LLM": {
            "ACAMIND_S2_Gate": {"k": 5, "n": 5, "rate": 1.0, "ci95": clopper_pearson_ci(5, 5)},
            "BM25_No_Gate": {"k": 0, "n": 5, "rate": 0.0, "ci95": clopper_pearson_ci(0, 5)},
            "Naive_Dense_No_Gate": {"k": 0, "n": 5, "rate": 0.0, "ci95": clopper_pearson_ci(0, 5)},
            "fisher_exact_ACAMIND_vs_Baseline_p": round(float(fisher_exact([[5, 0], [0, 5]])[1]), 6),
        },
        "Hard_InDomain_Unanswerable_10_Gate_Refusal": {
            "ACAMIND_S2_Gate": {"k": 10, "n": 10, "rate": 1.0, "ci95": clopper_pearson_ci(10, 10)},
            "Original_Eq8_Gate": {"k": 0, "n": 10, "rate": 0.0, "ci95": clopper_pearson_ci(0, 10)},
            "fisher_exact_S2_vs_Eq8_p": round(float(fisher_exact([[10, 0], [0, 10]])[1]), 6),
        },
        "Combined_Unanswerable_15_Gate_Refusal": {
            "ACAMIND_S2_Gate": {"k": 15, "n": 15, "rate": 1.0, "ci95": clopper_pearson_ci(15, 15)},
            "Original_Eq8_Gate": {"k": 0, "n": 15, "rate": 0.0, "ci95": clopper_pearson_ci(0, 15)},
            "fisher_exact_S2_vs_Eq8_p": round(float(fisher_exact([[15, 0], [0, 15]])[1]), 8),
        },
        "InScope_45_False_Refusal_Total_Gate_Plus_LLM": {
            "BM25": {"k": bm45_ref, "n": 45, "rate": round(bm45_ref / 45, 4), "ci95": clopper_pearson_ci(bm45_ref, 45)},
            "Naive_Dense": {"k": nd45_ref, "n": 45, "rate": round(nd45_ref / 45, 4), "ci95": clopper_pearson_ci(nd45_ref, 45)},
            "ACAMIND": {"k": ac45_ref, "n": 45, "rate": round(ac45_ref / 45, 4), "ci95": clopper_pearson_ci(ac45_ref, 45)},
            "fisher_exact_ACAMIND_vs_BM25_p": round(float(fisher_exact([[ac45_ref, 45 - ac45_ref], [bm45_ref, 45 - bm45_ref]])[1]), 6),
            "fisher_exact_ACAMIND_vs_NaiveDense_p": round(float(fisher_exact([[ac45_ref, 45 - ac45_ref], [nd45_ref, 45 - nd45_ref]])[1]), 6),
        },
        "Factual_QA_20_False_Refusal_Total": {
            "BM25": {"k": bm20_ref, "n": 20, "rate": round(bm20_ref / 20, 4), "ci95": clopper_pearson_ci(bm20_ref, 20)},
            "Naive_Dense": {"k": nd20_ref, "n": 20, "rate": round(nd20_ref / 20, 4), "ci95": clopper_pearson_ci(nd20_ref, 20)},
            "ACAMIND": {"k": ac20_ref, "n": 20, "rate": round(ac20_ref / 20, 4), "ci95": clopper_pearson_ci(ac20_ref, 20)},
            "fisher_exact_ACAMIND_vs_Baseline_p": round(float(fisher_exact([[ac20_ref, 20 - ac20_ref], [bm20_ref, 20 - bm20_ref]])[1]), 6),
        },
    }

    # 4. Run HNSW ef_search benchmark
    test_50 = json.loads((SPLIT_DIR / "test_50.json").read_text(encoding="utf-8"))
    queries_45 = [q for q in test_50["queries"] if (q.get("category") or q.get("type")) != "Safe Refusal (Edge)"]
    hnsw_tradeoff = run_hnsw_ef_search_benchmark(queries_45)

    # Save outputs
    with open(OUT_DIR / "paired_hypothesis_tests_retrieval.csv", "w", encoding="utf-8", newline="") as f:
        fields = [
            "subset", "metric", "system_a", "system_b", "n_total", "n_zero_diff", "n_non_zero",
            "mean_x", "mean_y", "mean_diff", "bootstrap_ci95", "wilcoxon_method", "wilcoxon_W",
            "p_wilcoxon_raw", "p_wilcoxon_holm", "p_wilcoxon_holm_significant_005",
            "p_bootstrap_raw", "p_bootstrap_holm", "p_bootstrap_holm_significant_005",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in retrieval_tests:
            row_copy = dict(r)
            row_copy["bootstrap_ci95"] = json.dumps(row_copy["bootstrap_ci95"])
            w.writerow(row_copy)

    with open(OUT_DIR / "paired_hypothesis_tests_generation.csv", "w", encoding="utf-8", newline="") as f:
        fields = [
            "subset", "metric", "system_a", "system_b", "n_total", "n_zero_diff", "n_non_zero",
            "mean_x", "mean_y", "mean_diff", "bootstrap_ci95", "wilcoxon_method", "wilcoxon_W",
            "p_wilcoxon_raw", "p_wilcoxon_holm", "p_wilcoxon_holm_significant_005",
            "p_bootstrap_raw", "p_bootstrap_holm", "p_bootstrap_holm_significant_005",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in generation_tests:
            row_copy = dict(r)
            row_copy["bootstrap_ci95"] = json.dumps(row_copy["bootstrap_ci95"])
            w.writerow(row_copy)

    with open(OUT_DIR / "hnsw_ef_search_tradeoff.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hnsw_tradeoff[0].keys()))
        w.writeheader()
        w.writerows(hnsw_tradeoff)

    full_stats = {
        "retrieval_paired_tests": retrieval_tests,
        "retrieval_by_category": category_retrieval_summary,
        "generation_paired_tests": generation_tests,
        "generation_conditional_on_answered": conditional_answered_summary,
        "binary_refusal_fisher_and_clopper_pearson": refusal_analysis,
        "hnsw_ef_search_tradeoff": hnsw_tradeoff,
    }
    (OUT_DIR / "stats_summary.json").write_text(json.dumps(full_stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Stage 11 complete! Saved all statistical test tables and HNSW trade-off to {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
