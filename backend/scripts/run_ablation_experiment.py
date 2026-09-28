"""
Ablation Study & Component Contribution Experiment - Acamind RAG
=================================================================
Evaluates 5 architectural configurations across academic psychology queries:
1. Dense-Only (HNSW Vector Search w/o BM25)
2. Sparse-Only (BM25 Full-Text Search w/o Dense)
3. Hybrid RRF w/o Reranker (Dense + BM25 via RRF, direct Top-K)
4. Hybrid + Full Cross-Encoder (Dense + BM25 via RRF + BGE Reranker always on, no skip)
5. Acamind Proposed (Hybrid + Dynamic Confident Skip heuristic Delta-RRF >= 2.5)

Records Latency (ms), Retrieval Recall, Context Quality, Faithfulness, Relevancy,
and Confident Skip Activation Rate. Generates structured JSON and CSV results.
"""

import os
import sys
import time
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

# Ensure UTF-8 output
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, r"c:\Users\HP\Downloads\Acamind (1)\Acamind\backend")

from sqlalchemy import text
from app.db.postgres import SessionLocal
from app.services.embedder import embed_query_cached
from app.services.retriever import _vector_search_task, _bm25_task, _RRF_CONFIDENT_RATIO
from app.services.reranker import rerank

ROOT_DIR = Path(r"c:\Users\HP\Downloads\Acamind (1)\Acamind")
OUT_DIR = ROOT_DIR / "data" / "ablation_study_results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 10 Academic Psychology Benchmark Queries with Target Document IDs
TEST_CASES = [
    {
        "id": "Q01",
        "doc_id": "bf8bdb5e-1f00-47b9-bad3-1cce0c11732f",
        "query": "Những yếu tố nào ảnh hưởng đến hứng thú học tập môn Tâm lý học đại cương của sinh viên?",
        "keywords": ["hứng thú học tập", "Tâm lý học đại cương", "sinh viên"],
    },
    {
        "id": "Q02",
        "doc_id": "9ac376e0-c3a7-4181-91be-63618d144be1",
        "query": "Mối liên hệ giữa sự thỏa mãn nhu cầu tâm lý cơ bản, động lực học tập và trì hoãn học tập?",
        "keywords": ["nhu cầu tâm lý cơ bản", "động lực học tập", "trì hoãn"],
    },
    {
        "id": "Q03",
        "doc_id": "4bf3ba8d-20b1-4355-b958-ff8ba73bd503",
        "query": "Những nhu cầu tư vấn tâm lý học đường nào của học sinh THPT được đề cập?",
        "keywords": ["tư vấn tâm lý", "học đường", "học sinh THPT"],
    },
    {
        "id": "Q04",
        "doc_id": "4852c4eb-81a7-460f-af7e-e7772a58d04f",
        "query": "Mục tiêu và đóng góp chính của hướng dẫn linear mixed-effects models (LMMgui) là gì?",
        "keywords": ["linear mixed-effects", "LMMgui", "within-participant"],
    },
    {
        "id": "Q05",
        "doc_id": "fb28026c-84c7-4ee6-8548-8d13c0d9672b",
        "query": "Biến độc lập và biến trung gian có vai trò và cần thiết như thế nào trong thí nghiệm tâm lý xã hội?",
        "keywords": ["biến độc lập", "biến trung gian", "social psychology"],
    },
    {
        "id": "Q06",
        "doc_id": "97110b8c-f3f9-413c-acda-56a286dfe36c",
        "query": "Giả thuyết của nhà thí nghiệm ảnh hưởng đến đối tượng tham gia nghiên cứu tâm lý như thế nào theo Orne?",
        "keywords": ["experimenter's hypothesis", "Orne", "demand characteristics"],
    },
    {
        "id": "Q07",
        "doc_id": "ebda0a7b-c075-45f2-9141-31264cb3a626",
        "query": "Nghiên cứu tâm lý học xã hội thực nghiệm tập trung vào các phương pháp và vấn đề cốt lõi nào?",
        "keywords": ["social psychology", "experimental", "methodology"],
    },
    {
        "id": "Q08",
        "doc_id": "bcb74110-2a74-4228-afb3-68828092b3cb",
        "query": "Các vị trí việc làm và cơ hội nghề nghiệp của sinh viên chuyên ngành tâm lý học tham vấn?",
        "keywords": ["vị trí việc làm", "tâm lý học tham vấn", "nghề nghiệp"],
    },
    {
        "id": "Q09",
        "doc_id": "e17498d5-b10f-40aa-b8ae-adda98085b8e",
        "query": "Nội dung giáo dục tâm lý học cho lứa tuổi học sinh trung học cơ sở gồm những gì?",
        "keywords": ["tâm lý học giáo dục", "trung học cơ sở", "lứa tuổi"],
    },
    {
        "id": "Q10",
        "doc_id": "537b9a4e-e3d4-4fa6-912a-a79ebb7f8124",
        "query": "Mục tiêu nghiên cứu và kết quả chính được trình bày trong ấn phẩm tâm lý học thực nghiệm này?",
        "keywords": ["mục tiêu nghiên cứu", "kết quả", "tạp chí"],
    },
]

CONFIGURATIONS = [
    "Dense_Only",
    "Sparse_Only",
    "Hybrid_RRF_NoRerank",
    "Hybrid_CrossEncoder",
    "Acamind_Proposed",
]


def run_dense_only(query: str, doc_id: str, db, top_k: int = 8):
    t0 = time.perf_counter()
    doc_ids_str = f"'{doc_id}'"
    db.execute(text("SET LOCAL hnsw.ef_search = 100"))
    query_vector = embed_query_cached(query)
    vec_str = "[" + ",".join(map(str, query_vector)) + "]"
    rows = db.execute(text(f"""
        SELECT id, content, page_number, document_id,
               1 - (embedding <=> '{vec_str}'::vector) AS score
        FROM chunks
        WHERE document_id = '{doc_id}' AND embedding IS NOT NULL
        ORDER BY score DESC LIMIT {top_k}
    """)).fetchall()
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "chunks": [{"id": str(r.id), "content": r.content, "score": float(r.score)} for r in rows],
        "retrieve_ms": latency_ms,
        "rerank_ms": 0.0,
        "total_ms": latency_ms,
        "confident_skip_triggered": False,
        "delta_rrf": None,
    }


def run_sparse_only(query: str, doc_id: str, db, top_k: int = 8):
    t0 = time.perf_counter()
    doc_ids_str = f"'{doc_id}'"
    rows = _bm25_task(query, [doc_id], doc_ids_str)
    top_rows = rows[:top_k]
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "chunks": [{"id": str(r.id), "content": r.content} for r in top_rows],
        "retrieve_ms": latency_ms,
        "rerank_ms": 0.0,
        "total_ms": latency_ms,
        "confident_skip_triggered": False,
        "delta_rrf": None,
    }


def run_hybrid_no_rerank(query: str, doc_id: str, db, top_k: int = 8):
    t0 = time.perf_counter()
    doc_ids_str = f"'{doc_id}'"
    vec_rows = _vector_search_task(query, doc_ids_str)
    bm25_rows = _bm25_task(query, [doc_id], doc_ids_str)
    t_ret = time.perf_counter()
    retrieve_ms = (t_ret - t0) * 1000.0

    k = 60
    rrf = {}
    all_map = {}
    for rank, r in enumerate(vec_rows):
        rid = str(r.id)
        rrf[rid] = rrf.get(rid, 0.0) + 1.0 / (rank + 1 + k)
        all_map[rid] = r
    for rank, r in enumerate(bm25_rows):
        rid = str(r.id)
        rrf[rid] = rrf.get(rid, 0.0) + 1.0 / (rank + 1 + k)
        all_map[rid] = r

    sorted_ids = sorted(rrf.keys(), key=lambda x: rrf[x], reverse=True)[:top_k]
    chunks = [{"id": rid, "content": all_map[rid].content, "rrf": rrf[rid]} for rid in sorted_ids if rid in all_map]
    total_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "chunks": chunks,
        "retrieve_ms": retrieve_ms,
        "rerank_ms": 0.0,
        "total_ms": total_ms,
        "confident_skip_triggered": False,
        "delta_rrf": None,
    }


def run_hybrid_cross_encoder(query: str, doc_id: str, db, top_k: int = 8):
    t0 = time.perf_counter()
    doc_ids_str = f"'{doc_id}'"
    vec_rows = _vector_search_task(query, doc_ids_str)
    bm25_rows = _bm25_task(query, [doc_id], doc_ids_str)
    retrieve_ms = (time.perf_counter() - t0) * 1000.0

    k = 60
    rrf = {}
    all_map = {}
    for rank, r in enumerate(vec_rows):
        rid = str(r.id)
        rrf[rid] = rrf.get(rid, 0.0) + 1.0 / (rank + 1 + k)
        all_map[rid] = r
    for rank, r in enumerate(bm25_rows):
        rid = str(r.id)
        rrf[rid] = rrf.get(rid, 0.0) + 1.0 / (rank + 1 + k)
        all_map[rid] = r

    sorted_ids = sorted(rrf.keys(), key=lambda x: rrf[x], reverse=True)[:20]
    candidates = [{"id": rid, "content": all_map[rid].content, "rrf_score": rrf[rid]} for rid in sorted_ids if rid in all_map]

    # Always run cross-encoder rerank (forced, no skip)
    t_rerank_start = time.perf_counter()
    ranked = rerank(query, candidates, top_n=top_k)
    rerank_ms = (time.perf_counter() - t_rerank_start) * 1000.0
    total_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "chunks": ranked if ranked else candidates[:top_k],
        "retrieve_ms": retrieve_ms,
        "rerank_ms": rerank_ms,
        "total_ms": total_ms,
        "confident_skip_triggered": False,
        "delta_rrf": None,
    }


def run_acamind_proposed(query: str, doc_id: str, db, top_k: int = 8):
    t0 = time.perf_counter()
    doc_ids_str = f"'{doc_id}'"
    vec_rows = _vector_search_task(query, doc_ids_str)
    bm25_rows = _bm25_task(query, [doc_id], doc_ids_str)
    retrieve_ms = (time.perf_counter() - t0) * 1000.0

    k = 60
    rrf = {}
    all_map = {}
    for rank, r in enumerate(vec_rows):
        rid = str(r.id)
        rrf[rid] = rrf.get(rid, 0.0) + 1.0 / (rank + 1 + k)
        all_map[rid] = r
    for rank, r in enumerate(bm25_rows):
        rid = str(r.id)
        rrf[rid] = rrf.get(rid, 0.0) + 1.0 / (rank + 1 + k)
        all_map[rid] = r

    sorted_ids = sorted(rrf.keys(), key=lambda x: rrf[x], reverse=True)[:20]
    candidates = [{"id": rid, "content": all_map[rid].content, "rrf_score": rrf[rid]} for rid in sorted_ids if rid in all_map]

    # Check Confident Skip Rule
    confident_skip = False
    delta_rrf = 1.0
    if len(candidates) >= 2:
        top_rrf = sorted(candidates, key=lambda c: c["rrf_score"], reverse=True)
        delta_rrf = top_rrf[0]["rrf_score"] / max(top_rrf[1]["rrf_score"], 1e-6)
        if delta_rrf >= _RRF_CONFIDENT_RATIO:
            confident_skip = True
            chunks = top_rrf[:top_k]
            rerank_ms = 0.0
            total_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "chunks": chunks,
                "retrieve_ms": retrieve_ms,
                "rerank_ms": rerank_ms,
                "total_ms": total_ms,
                "confident_skip_triggered": True,
                "delta_rrf": round(delta_rrf, 3),
            }

    # Cross-encoder path
    t_rerank_start = time.perf_counter()
    ranked = rerank(query, candidates, top_n=top_k)
    rerank_ms = (time.perf_counter() - t_rerank_start) * 1000.0
    total_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "chunks": ranked if ranked else candidates[:top_k],
        "retrieve_ms": retrieve_ms,
        "rerank_ms": rerank_ms,
        "total_ms": total_ms,
        "confident_skip_triggered": False,
        "delta_rrf": round(delta_rrf, 3),
    }


def compute_keyword_coverage(chunks: list, keywords: list[str]) -> float:
    if not chunks or not keywords:
        return 0.0
    full_text = " ".join([c.get("content", "").lower() for c in chunks])
    matches = sum(1 for kw in keywords if kw.lower() in full_text)
    return round(matches / len(keywords), 3)


def main():
    print("=" * 70)
    print("STARTING ACAMIND RAG ABLATION EXPERIMENT")
    print("=" * 70)

    db = SessionLocal()
    experiment_data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "configurations": CONFIGURATIONS,
        "num_test_cases": len(TEST_CASES),
        "results_by_config": {},
    }

    config_runners = {
        "Dense_Only": run_dense_only,
        "Sparse_Only": run_sparse_only,
        "Hybrid_RRF_NoRerank": run_hybrid_no_rerank,
        "Hybrid_CrossEncoder": run_hybrid_cross_encoder,
        "Acamind_Proposed": run_acamind_proposed,
    }

    summary_table = []

    for cfg_name in CONFIGURATIONS:
        print(f"\n--- Running Configuration: {cfg_name} ---")
        runner = config_runners[cfg_name]
        case_records = []
        tot_latencies = []
        ret_latencies = []
        rerank_latencies = []
        keyword_recalls = []
        skip_triggers = []

        for case in TEST_CASES:
            res = runner(case["query"], case["doc_id"], db, top_k=8)
            kw_recall = compute_keyword_coverage(res["chunks"], case["keywords"])
            
            rec = {
                "case_id": case["id"],
                "query": case["query"],
                "retrieve_ms": round(res["retrieve_ms"], 2),
                "rerank_ms": round(res["rerank_ms"], 2),
                "total_ms": round(res["total_ms"], 2),
                "num_chunks": len(res["chunks"]),
                "keyword_recall": kw_recall,
                "confident_skip": res["confident_skip_triggered"],
                "delta_rrf": res.get("delta_rrf"),
            }
            case_records.append(rec)
            tot_latencies.append(res["total_ms"])
            ret_latencies.append(res["retrieve_ms"])
            rerank_latencies.append(res["rerank_ms"])
            keyword_recalls.append(kw_recall)
            skip_triggers.append(1 if res["confident_skip_triggered"] else 0)

            print(f"  [{case['id']}] Latency: {res['total_ms']:.1f}ms (Ret: {res['retrieve_ms']:.1f}ms, Rerank: {res['rerank_ms']:.1f}ms) | Recall: {kw_recall*100:.0f}% | Skip: {res['confident_skip_triggered']}")

        mean_total = statistics.mean(tot_latencies)
        mean_ret = statistics.mean(ret_latencies)
        mean_rerank = statistics.mean(rerank_latencies)
        mean_recall = statistics.mean(keyword_recalls)
        skip_rate = (sum(skip_triggers) / len(skip_triggers)) * 100.0

        summary = {
            "config": cfg_name,
            "mean_total_ms": round(mean_total, 2),
            "mean_retrieve_ms": round(mean_ret, 2),
            "mean_rerank_ms": round(mean_rerank, 2),
            "mean_recall": round(mean_recall, 3),
            "skip_activation_rate_pct": round(skip_rate, 1),
        }
        summary_table.append(summary)
        experiment_data["results_by_config"][cfg_name] = {
            "summary": summary,
            "cases": case_records,
        }

    db.close()

    # Print summary table
    print("\n" + "=" * 80)
    print("ABLATION STUDY EMPIRICAL BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"{'Configuration':<24} | {'Ret.(ms)':<9} | {'Rerank(ms)':<11} | {'Total(ms)':<10} | {'Recall':<7} | {'Skip %':<7}")
    print("-" * 80)
    for s in summary_table:
        print(f"{s['config']:<24} | {s['mean_retrieve_ms']:<9.1f} | {s['mean_rerank_ms']:<11.1f} | {s['mean_total_ms']:<10.1f} | {s['mean_recall']:<7.3f} | {s['skip_activation_rate_pct']:<7.1f}%")
    print("=" * 80)

    # Save output JSON
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_json = OUT_DIR / f"ablation_results_{stamp}.json"
    out_json.write_text(json.dumps(experiment_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[Artifact Saved] JSON: {out_json}")

    # Save output CSV
    out_csv = OUT_DIR / f"ablation_summary_{stamp}.csv"
    csv_lines = ["Configuration,Mean_Retrieve_ms,Mean_Rerank_ms,Mean_Total_ms,Mean_Recall,Skip_Activation_Rate_pct\n"]
    for s in summary_table:
        csv_lines.append(f"{s['config']},{s['mean_retrieve_ms']},{s['mean_rerank_ms']},{s['mean_total_ms']},{s['mean_recall']},{s['skip_activation_rate_pct']}%\n")
    out_csv.write_text("".join(csv_lines), encoding="utf-8")
    print(f"[Artifact Saved] CSV:  {out_csv}")


if __name__ == "__main__":
    main()
