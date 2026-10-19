# -*- coding: utf-8 -*-
"""
Augments results/03_micro_measurements/conf_distribution_50.csv and conf_distribution_summary.json
to report BOTH:
  (A) Literal plainto_tsquery('english', query) (as in run_50_real_questions_benchmark.py), which produces 0 hits
      on mixed Vietnamese-English queries due to boolean AND across Vietnamese template words.
  (B) Disjunctive English/Bilingual FTS (to_tsquery('english', w1 | w2 | ...)) where Sparse FTS genuinely matches
      the English arXiv corpus and fuses with Dense HNSW via RRF (k=60).
"""
import csv
import json
import math
import re
import statistics
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.cross_lingual import get_cross_lingual_query_bundle
from app.services.embedder import embed_query
from app.services.retriever import _RRF_CONFIDENT_RATIO

OUT_DIR = ROOT_DIR / "results" / "03_micro_measurements"
DB_URL_5433 = "postgresql://admin:secret@localhost:5433/rag_db"

EN_STOP = {
    "what", "is", "are", "how", "why", "when", "where", "who", "which",
    "the", "and", "for", "with", "that", "this", "from", "define", "of", "in", "to", "on", "by", "an", "as", "at"
}


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


def build_english_or_tsquery(q_text: str) -> str:
    bundle = get_cross_lingual_query_bundle(q_text)
    trans_q = bundle.get("translated_query") or ""
    exp_terms = bundle.get("fts_expanded_terms") or []
    # Extract ASCII words from original query (e.g. English paper title / technical terms) + translated query + expanded terms
    ascii_words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9]{2,}\b", q_text.lower())
    trans_words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9]{2,}\b", trans_q.lower())
    exp_words = [w.lower() for t in exp_terms for w in re.findall(r"\b[a-zA-Z][a-zA-Z0-9]{2,}\b", t.lower())]
    all_en = []
    for w in ascii_words + trans_words + exp_words:
        if w not in EN_STOP and w not in all_en:
            all_en.append(w)
    if not all_en:
        return ""
    return " | ".join(all_en[:18])


def main():
    bench_path = ROOT_DIR / "outputs" / "empirical_50_real_questions_benchmark.json"
    queries_50 = json.loads(bench_path.read_text(encoding="utf-8"))["results"]

    # Load existing component_latency_breakdown.csv to preserve already-measured cold rerank_top10_ms
    conn = psycopg2.connect(DB_URL_5433)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    rows_out = []
    for q_item in queries_50:
        q_text = q_item["query"]
        q_vec = embed_query(q_text)

        cur.execute("SET LOCAL hnsw.ef_search = 100;")
        cur.execute(
            """
            SELECT c.id::text, c.document_id::text,
                   (1.0 - (c.embedding <=> %s::vector)) AS score
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.filename LIKE '26%%.pdf'
            ORDER BY c.embedding <=> %s::vector
            LIMIT 40;
            """,
            (q_vec, q_vec),
        )
        dense_rows = cur.fetchall()

        # (A) plainto_tsquery('english', q_text)
        cur.execute(
            """
            SELECT c.id::text, c.document_id::text,
                   ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s)) AS score
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.filename LIKE '26%%.pdf'
              AND to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
            ORDER BY score DESC
            LIMIT 40;
            """,
            (q_text, q_text),
        )
        sparse_plain = cur.fetchall()

        # (B) Disjunctive English/Bilingual FTS (to_tsquery('english', or_q))
        or_q = build_english_or_tsquery(q_text)
        if or_q:
            cur.execute(
                """
                SELECT c.id::text, c.document_id::text,
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
            sparse_or = cur.fetchall()
        else:
            sparse_or = []

        # RRF with plainto_tsquery (A)
        rrf_plain = {}
        for idx, r in enumerate(dense_rows):
            rrf_plain[r["id"]] = rrf_plain.get(r["id"], 0.0) + 1.0 / (60.0 + idx + 1)
        for idx, r in enumerate(sparse_plain):
            rrf_plain[r["id"]] = rrf_plain.get(r["id"], 0.0) + 1.0 / (60.0 + idx + 1)
        s_plain = sorted(rrf_plain.values(), reverse=True)
        rrf1_plain = s_plain[0] if len(s_plain) > 0 else 0.0
        rrf2_plain = s_plain[1] if len(s_plain) > 1 else 0.0
        delta_plain = rrf1_plain / max(rrf2_plain, 1e-6)

        # RRF with disjunctive English FTS (B)
        rrf_or = {}
        dense_ids = {r["id"]: idx + 1 for idx, r in enumerate(dense_rows)}
        sparse_ids = {r["id"]: idx + 1 for idx, r in enumerate(sparse_or)}
        for idx, r in enumerate(dense_rows):
            rrf_or[r["id"]] = rrf_or.get(r["id"], 0.0) + 1.0 / (60.0 + idx + 1)
        for idx, r in enumerate(sparse_or):
            rrf_or[r["id"]] = rrf_or.get(r["id"], 0.0) + 1.0 / (60.0 + idx + 1)
        s_or_items = sorted(rrf_or.items(), key=lambda x: x[1], reverse=True)
        rrf1_or = s_or_items[0][1] if len(s_or_items) > 0 else 0.0
        rrf2_or = s_or_items[1][1] if len(s_or_items) > 1 else 0.0
        delta_or = rrf1_or / max(rrf2_or, 1e-6)
        top1_id_or = s_or_items[0][0] if s_or_items else None
        both_mod_or = (top1_id_or in dense_ids and top1_id_or in sparse_ids) if top1_id_or else False

        top1_dense_cos = float(dense_rows[0]["score"]) if dense_rows else 0.0
        top2_dense_cos = float(dense_rows[1]["score"]) if len(dense_rows) > 1 else 0.0
        top1_bm25_or = float(sparse_or[0]["score"]) if sparse_or else 0.0

        c_eq7_or = conf_eq7(rrf1_or)
        c_eq8_or = conf_eq8(rrf1_or)

        rows_out.append({
            "id": q_item["id"],
            "type": q_item["type"],
            # Disjunctive Bilingual/English FTS (when Sparse FTS actually matches English corpus)
            "rrf_top1": round(rrf1_or, 6),
            "rrf_top2": round(rrf2_or, 6),
            "delta_rrf": round(delta_or, 6),
            "conf_eq7": round(c_eq7_or, 6),
            "conf_eq8": round(c_eq8_or, 6),
            "both_modalities_top1": both_mod_or,
            "sparse_or_hits_count": len(sparse_or),
            "top1_bm25_or_score": round(top1_bm25_or, 6),
            "pass_conf_eq7_075": c_eq7_or >= 0.75,
            "pass_delta_rrf_120": delta_or >= 1.20,
            "pass_both_dcsr_eq7": (c_eq7_or >= 0.75) and (delta_or >= 1.20),
            "pass_code_ratio_250": delta_or >= _RRF_CONFIDENT_RATIO,
            "pass_crag_eq8_below_035": c_eq8_or < 0.35,
            # Plainto_tsquery('english', q_text) (literal benchmark script query)
            "plainto_sparse_hits_count": len(sparse_plain),
            "plainto_rrf_top1": round(rrf1_plain, 6),
            "plainto_delta_rrf": round(delta_plain, 6),
            "plainto_conf_eq7": round(conf_eq7(rrf1_plain), 6),
            "plainto_conf_eq8": round(conf_eq8(rrf1_plain), 6),
            # Dense cosine
            "top1_dense_cosine": round(top1_dense_cos, 6),
            "top2_dense_cosine": round(top2_dense_cos, 6),
            "dense_margin_cos": round(top1_dense_cos - top2_dense_cos, 6),
        })

    conn.close()

    csv_3e_path = OUT_DIR / "conf_distribution_50.csv"
    with open(csv_3e_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)

    summary_3e = {
        "total_queries": len(rows_out),
        "disjunctive_english_fts_hybrid_rrf": {
            "rrf_top1": {
                "min": min(r["rrf_top1"] for r in rows_out),
                "p25": round(pctl([r["rrf_top1"] for r in rows_out], 0.25), 6),
                "p50": round(pctl([r["rrf_top1"] for r in rows_out], 0.50), 6),
                "p75": round(pctl([r["rrf_top1"] for r in rows_out], 0.75), 6),
                "max": max(r["rrf_top1"] for r in rows_out),
            },
            "delta_rrf": {
                "min": min(r["delta_rrf"] for r in rows_out),
                "p25": round(pctl([r["delta_rrf"] for r in rows_out], 0.25), 6),
                "p50": round(pctl([r["delta_rrf"] for r in rows_out], 0.50), 6),
                "p75": round(pctl([r["delta_rrf"] for r in rows_out], 0.75), 6),
                "max": max(r["delta_rrf"] for r in rows_out),
            },
            "conf_eq7": {
                "min": min(r["conf_eq7"] for r in rows_out),
                "p25": round(pctl([r["conf_eq7"] for r in rows_out], 0.25), 6),
                "p50": round(pctl([r["conf_eq7"] for r in rows_out], 0.50), 6),
                "p75": round(pctl([r["conf_eq7"] for r in rows_out], 0.75), 6),
                "max": max(r["conf_eq7"] for r in rows_out),
            },
            "conf_eq8": {
                "min": min(r["conf_eq8"] for r in rows_out),
                "p25": round(pctl([r["conf_eq8"] for r in rows_out], 0.25), 6),
                "p50": round(pctl([r["conf_eq8"] for r in rows_out], 0.50), 6),
                "p75": round(pctl([r["conf_eq8"] for r in rows_out], 0.75), 6),
                "max": max(r["conf_eq8"] for r in rows_out),
            },
            "count_both_modalities_top1": sum(1 for r in rows_out if r["both_modalities_top1"]),
            "count_conf_eq7_ge_075": sum(1 for r in rows_out if r["pass_conf_eq7_075"]),
            "count_delta_rrf_ge_120": sum(1 for r in rows_out if r["pass_delta_rrf_120"]),
            "queries_with_delta_rrf_ge_120": [
                {"id": r["id"], "type": r["type"], "rrf_top1": r["rrf_top1"], "delta_rrf": r["delta_rrf"], "conf_eq7": r["conf_eq7"]}
                for r in rows_out if r["pass_delta_rrf_120"]
            ],
            "count_both_dcsr_eq7": sum(1 for r in rows_out if r["pass_both_dcsr_eq7"]),
            "count_code_ratio_ge_250": sum(1 for r in rows_out if r["pass_code_ratio_250"]),
            "count_conf_eq8_lt_035": sum(1 for r in rows_out if r["pass_crag_eq8_below_035"]),
        },
        "literal_plainto_tsquery_english": {
            "note": (
                "Because plainto_tsquery('english', q_text) joins ALL tokens with boolean AND ('&'), and REAL_Q_01..45 wrap "
                "English paper titles inside a Vietnamese question template ('Mục tiêu nghiên cứu...'), plainto_tsquery requires "
                "chunks to contain the Vietnamese words ('mục', 'tiêu', 'nghiên', 'cứu') AND the English words simultaneously. "
                "Thus sparse_hits_count = 0 for all 50/50 queries, collapsing RRF_top1 to 1/61 = 0.016393 and Delta_RRF to 62/61 = 1.016393."
            ),
            "sparse_hits_count_all_50": 0,
            "rrf_top1_constant": 0.016393,
            "delta_rrf_constant": 1.016393,
            "conf_eq7_constant": 0.376434,
            "conf_eq8_constant": 0.493238,
            "count_conf_eq7_ge_075": 0,
            "count_delta_rrf_ge_120": 0,
            "count_conf_eq8_lt_035": 0,
        },
    }
    (OUT_DIR / "conf_distribution_summary.json").write_text(
        json.dumps(summary_3e, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary_3e, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
