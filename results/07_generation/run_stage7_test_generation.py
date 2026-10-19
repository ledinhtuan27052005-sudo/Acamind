# -*- coding: utf-8 -*-
"""
Stage 7: Fair 50-Query Generation Benchmark across all 3 Systems (BM25, Naive_Dense, ACAMIND)
  - Reads pre-computed top-5 chunks and latencies from results/06_retrieval/test_raw_retrieval.json
    and results/06_retrieval/per_query_metrics.csv
  - Calls Gemini 2.5 Flash-Lite (temperature=0.1, identical PSYCHOLOGY_SYSTEM_PROMPT, lang='vi')
    with per-query/per-system checkpointing in results/07_generation/raw_outputs/{system}/{query_id}.json
  - Respects 15 RPM Gemini quota (4.5s sleep between live API calls; 0s on cached checkpoints)
  - Computes strictly objective automatic metrics in results/07_generation/auto_metrics.csv
    and results/07_generation/generation_summary.json (never uses the biased lexical formula!).
"""
import csv
import json
import math
import re
import statistics
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from app.services.generator import generate_answer

RET_DIR = ROOT_DIR / "results" / "06_retrieval"
GEN_DIR = ROOT_DIR / "results" / "07_generation"
RAW_OUT_DIR = GEN_DIR / "raw_outputs"
GEN_DIR.mkdir(parents=True, exist_ok=True)

SYSTEMS = ["BM25", "Naive_Dense", "ACAMIND"]
for s in SYSTEMS:
    (RAW_OUT_DIR / s).mkdir(parents=True, exist_ok=True)


def pctl(arr, p):
    if not arr:
        return 0.0
    s = sorted(arr)
    k = (len(s) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    return s[int(k)] if f == c else s[int(f)] * (c - k) + s[int(c)] * (k - f)


CITE_PATTERN = re.compile(
    r"([0-9]{4}\.[0-9]{4,5}v[0-9]+\.pdf|[A-Za-z0-9_.\-]+\.pdf)\s*[-–,:\s|]*(?:Trang|Page|p\.?|tr\.?)\s*(\d+)",
    re.IGNORECASE,
)


def parse_and_verify_citations(answer_text: str, provided_chunks: list[dict], gt_doc_ids: list[str], doc_id_by_fname: dict) -> dict:
    if not answer_text or "__NO_CONTEXT__" in answer_text:
        return {
            "total_citations": 0,
            "valid_in_context_citations": 0,
            "valid_in_gt_doc_citations": 0,
            "syntactic_citation_validity": 0.0,
            "gt_doc_citation_precision": 0.0,
            "has_at_least_one_valid_citation": 0,
            "distinct_cited_files": 0,
            "extracted_citations": [],
        }

    allowed_pairs = {
        ((c.get("filename") or "").lower().strip(), int(c.get("page_number", -1)))
        for c in provided_chunks
        if c.get("filename") and c.get("page_number") is not None
    }
    gt_set = set(gt_doc_ids)

    # Extract all bracketed [...] blocks first, plus fallback scan on full text
    bracket_blocks = re.findall(r"\[([^\[\]]+)\]", answer_text)
    matches = []
    for blk in bracket_blocks:
        for m in CITE_PATTERN.finditer(blk):
            matches.append((m.group(1).strip(), int(m.group(2))))

    if not matches:
        for m in CITE_PATTERN.finditer(answer_text):
            matches.append((m.group(1).strip(), int(m.group(2))))

    total = len(matches)
    if total == 0:
        return {
            "total_citations": 0,
            "valid_in_context_citations": 0,
            "valid_in_gt_doc_citations": 0,
            "syntactic_citation_validity": 0.0,
            "gt_doc_citation_precision": 0.0,
            "has_at_least_one_valid_citation": 0,
            "distinct_cited_files": 0,
            "extracted_citations": [],
        }

    valid_ctx = 0
    valid_gt = 0
    cited_files = set()
    extracted = []
    for fname, pnum in matches:
        fl = fname.lower()
        cited_files.add(fl)
        in_ctx = (fl, pnum) in allowed_pairs
        did = doc_id_by_fname.get(fl)
        in_gt = (did in gt_set) and in_ctx
        if in_ctx:
            valid_ctx += 1
        if in_gt:
            valid_gt += 1
        extracted.append({"filename": fname, "page": pnum, "in_context": in_ctx, "in_gt_doc": in_gt})

    return {
        "total_citations": total,
        "valid_in_context_citations": valid_ctx,
        "valid_in_gt_doc_citations": valid_gt,
        "syntactic_citation_validity": round(valid_ctx / total, 6),
        "gt_doc_citation_precision": round(valid_gt / total, 6),
        "has_at_least_one_valid_citation": 1 if valid_ctx > 0 else 0,
        "distinct_cited_files": len(cited_files),
        "extracted_citations": extracted,
    }


def call_llm_with_retry(q_text: str, chunks_top5: list[dict]) -> tuple[str, float]:
    # Prepare chunk dicts with doc_filename and doc_title expected by generator.py
    prepared = []
    for c in chunks_top5:
        cc = dict(c)
        cc["doc_filename"] = c.get("filename") or c.get("doc_filename") or "document.pdf"
        cc["doc_title"] = c.get("title") or c.get("doc_title") or cc["doc_filename"]
        prepared.append(cc)

    for attempt in range(5):
        try:
            t0 = time.perf_counter()
            ans = generate_answer(q_text, prepared, lang="vi")
            dt_ms = (time.perf_counter() - t0) * 1000.0
            return ans, round(dt_ms, 2)
        except Exception as e:
            wait_s = 8.0 * (attempt + 1)
            print(f"    [WARN] Gemini API error on attempt {attempt+1}/5: {e}. Sleeping {wait_s}s...", flush=True)
            time.sleep(wait_s)
    raise RuntimeError(f"Failed to generate answer after 5 attempts for query: {q_text[:60]}")


def main():
    raw_ret_path = RET_DIR / "test_raw_retrieval.json"
    pq_csv_path = RET_DIR / "per_query_metrics.csv"
    if not raw_ret_path.exists() or not pq_csv_path.exists():
        raise RuntimeError("Stage 6 outputs not found! Run run_stage6_test_retrieval.py first.")

    all_ret = json.loads(raw_ret_path.read_text(encoding="utf-8"))
    test_50_ret = [r for r in all_ret if r["id"].startswith("REAL_Q_")]

    # Map (id, config) -> row from per_query_metrics.csv
    pq_map = {}
    with open(pq_csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pq_map[(row["id"], row["config"])] = row

    # Build filename -> document_id map from all retrieved chunks
    doc_id_by_fname = {}
    for r in test_50_ret:
        for ch_list in [
            r["dense_top10"],
            r["sparse_top10"],
            r["rrf_top16"],
            r["reranked_top16"],
            r.get("decomposed_rrf_top16", []),
            r.get("decomposed_reranked_top16", []),
        ]:
            for c in ch_list:
                if c.get("filename") and c.get("document_id"):
                    doc_id_by_fname[c["filename"].lower()] = c["document_id"]

    auto_rows = []
    made_live_call = False

    for idx, r in enumerate(test_50_ret, 1):
        qid = r["id"]
        qtype = r["type"]
        qtext = r["query"]
        is_ooc = r["is_ooc"]
        gt_docs = r["gt_doc_ids"]

        c1_row = pq_map[(qid, "C1")]
        c2_row = pq_map[(qid, "C2")]
        c6_row = pq_map[(qid, "C6")]

        dcsr_skipped = c6_row["dcsr_skipped_rerank"].lower() == "true"
        gate_passed = c6_row["gate_passed_answerable"].lower() == "true"
        gate_score = float(c6_row["gate_score"])

        has_decomp = "decomposed_reranked_top16" in r
        k_ctx = 6 if has_decomp else 5
        acamind_pool = r.get("decomposed_rrf_top16", r["rrf_top16"]) if dcsr_skipped else r.get("decomposed_reranked_top16", r["reranked_top16"])

        sys_Specs = [
            ("BM25", r["sparse_top10"][:5], float(c1_row["latency_cold_ms"]), float(c1_row["latency_warm_ms"]), True),
            ("Naive_Dense", r["dense_top10"][:5], float(c2_row["latency_cold_ms"]), float(c2_row["latency_warm_ms"]), True),
            (
                "ACAMIND",
                acamind_pool[:k_ctx] if gate_passed else [],
                float(c6_row["latency_cold_ms"]),
                float(c6_row["latency_warm_ms"]),
                gate_passed,
            ),
        ]

        for sys_name, top5_chunks, ret_cold_ms, ret_warm_ms, pass_gate in sys_Specs:
            out_file = RAW_OUT_DIR / sys_name / f"{qid}.json"
            if out_file.exists():
                saved = json.loads(out_file.read_text(encoding="utf-8"))
                if saved.get("is_ooc") != is_ooc:
                    saved["is_ooc"] = is_ooc
                    out_file.write_text(json.dumps(saved, indent=2, ensure_ascii=False), encoding="utf-8")
                ans_text = saved["answer"]
                llm_ms = float(saved["llm_ms"])
                gate_refused = bool(saved.get("gate_refused", False))
                llm_self_refused = bool(saved.get("llm_self_refused", False))
            else:
                if sys_name == "ACAMIND" and not pass_gate:
                    # Stopped by pre-LLM CRAG Gate!
                    ans_text = "__NO_CONTEXT__\nKhông tìm thấy thông tin phù hợp trong các tài liệu đã đăng tải. (Từ chối bởi CRAG Gate)"
                    llm_ms = 0.0
                    gate_refused = True
                    llm_self_refused = False
                elif len(top5_chunks) == 0:
                    # E.g. BM25 returned 0 matching chunks
                    if made_live_call:
                        time.sleep(1.0)
                    ans_text, llm_ms = call_llm_with_retry(qtext, [])
                    made_live_call = True
                    gate_refused = False
                    llm_self_refused = "__NO_CONTEXT__" in ans_text
                else:
                    if made_live_call:
                        time.sleep(1.0)
                    ans_text, llm_ms = call_llm_with_retry(qtext, top5_chunks)
                    made_live_call = True
                    gate_refused = False
                    llm_self_refused = "__NO_CONTEXT__" in ans_text

                saved = {
                    "query_id": qid,
                    "type": qtype,
                    "query": qtext,
                    "is_ooc": is_ooc,
                    "system": sys_name,
                    "gate_passed": pass_gate,
                    "gate_score": gate_score if sys_name == "ACAMIND" else None,
                    "dcsr_skipped": dcsr_skipped if sys_name == "ACAMIND" else None,
                    "gate_refused": gate_refused,
                    "llm_self_refused": llm_self_refused,
                    "retrieval_cold_ms": ret_cold_ms,
                    "retrieval_warm_ms": ret_warm_ms,
                    "llm_ms": llm_ms,
                    "e2e_cold_ms": round(ret_cold_ms + llm_ms, 2),
                    "e2e_warm_ms": round(ret_warm_ms + llm_ms, 2),
                    "provided_chunks": [
                        {
                            "id": c["id"],
                            "document_id": c["document_id"],
                            "filename": c["filename"],
                            "page_number": c["page_number"],
                            "content": c.get("content", ""),
                        }
                        for c in top5_chunks
                    ],
                    "answer": ans_text,
                }
                out_file.write_text(json.dumps(saved, indent=2, ensure_ascii=False), encoding="utf-8")
                print(
                    f"  [GEN {idx}/50] {qid} | {sys_name}: ret_cold={ret_cold_ms:.1f}ms, llm={llm_ms:.1f}ms, "
                    f"gate_ref={gate_refused}, llm_ref={llm_self_refused}",
                    flush=True,
                )

            cite_info = parse_and_verify_citations(ans_text, top5_chunks, gt_docs, doc_id_by_fname)
            any_refusal = gate_refused or llm_self_refused

            auto_rows.append({
                "query_id": qid,
                "type": qtype,
                "is_ooc": is_ooc,
                "system": sys_name,
                "retrieval_cold_ms": round(ret_cold_ms, 2),
                "retrieval_warm_ms": round(ret_warm_ms, 2),
                "llm_ms": round(llm_ms, 2),
                "e2e_cold_ms": round(ret_cold_ms + llm_ms, 2),
                "e2e_warm_ms": round(ret_warm_ms + llm_ms, 2),
                "gate_refused": int(gate_refused),
                "llm_self_refused": int(llm_self_refused),
                "total_refused": int(any_refusal),
                "total_citations": cite_info["total_citations"],
                "valid_in_context_citations": cite_info["valid_in_context_citations"],
                "valid_in_gt_doc_citations": cite_info["valid_in_gt_doc_citations"],
                "syntactic_citation_validity": cite_info["syntactic_citation_validity"],
                "gt_doc_citation_precision": cite_info["gt_doc_citation_precision"],
                "has_at_least_one_valid_citation": cite_info["has_at_least_one_valid_citation"],
                "distinct_cited_files": cite_info["distinct_cited_files"],
                "answer_char_len": len(ans_text),
            })

    # Write auto_metrics.csv
    auto_csv_path = GEN_DIR / "auto_metrics.csv"
    with open(auto_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(auto_rows[0].keys()))
        writer.writeheader()
        writer.writerows(auto_rows)

    # Summarize per system and per query category (verifying E[E2E] == E[Ret] + E[LLM])
    summary = {"by_system": {}, "by_system_and_category": {}}
    for sys_name in SYSTEMS:
        s_rows = [r for r in auto_rows if r["system"] == sys_name]
        ans_rows = [r for r in s_rows if not r["is_ooc"]]
        ood_rows = [r for r in s_rows if r["is_ooc"]]

        total_cites_all = sum(r["total_citations"] for r in ans_rows)
        valid_ctx_cites_all = sum(r["valid_in_context_citations"] for r in ans_rows)
        valid_gt_cites_all = sum(r["valid_in_gt_doc_citations"] for r in ans_rows)

        ret_c = [r["retrieval_cold_ms"] for r in s_rows]
        ret_w = [r["retrieval_warm_ms"] for r in s_rows]
        llm_l = [r["llm_ms"] for r in s_rows]
        e2e_c = [r["e2e_cold_ms"] for r in s_rows]
        e2e_w = [r["e2e_warm_ms"] for r in s_rows]

        summary["by_system"][sys_name] = {
            "n_total": len(s_rows),
            "n_answerable": len(ans_rows),
            "n_ood": len(ood_rows),
            "micro_syntactic_citation_validity_45": round(valid_ctx_cites_all / total_cites_all, 4) if total_cites_all else 0.0,
            "macro_syntactic_citation_validity_45": round(statistics.mean(r["syntactic_citation_validity"] for r in ans_rows), 4),
            "micro_gt_doc_citation_precision_45": round(valid_gt_cites_all / total_cites_all, 4) if total_cites_all else 0.0,
            "macro_gt_doc_citation_precision_45": round(statistics.mean(r["gt_doc_citation_precision"] for r in ans_rows), 4),
            "responses_with_valid_citation_rate_45": round(statistics.mean(r["has_at_least_one_valid_citation"] for r in ans_rows), 4),
            "mean_distinct_cited_files_45": round(statistics.mean(r["distinct_cited_files"] for r in ans_rows), 2),
            "ood_5_gate_refusal_count": sum(r["gate_refused"] for r in ood_rows),
            "ood_5_llm_self_refusal_count": sum(r["llm_self_refused"] for r in ood_rows),
            "ood_5_total_refusal_count": sum(r["total_refused"] for r in ood_rows),
            "ood_5_total_refusal_rate": round(sum(r["total_refused"] for r in ood_rows) / len(ood_rows), 4),
            "in_scope_45_false_gate_refusal_count": sum(r["gate_refused"] for r in ans_rows),
            "in_scope_45_false_llm_refusal_count": sum(r["llm_self_refused"] for r in ans_rows),
            "in_scope_45_total_false_refusal_count": sum(r["total_refused"] for r in ans_rows),
            "in_scope_45_total_false_refusal_rate": round(sum(r["total_refused"] for r in ans_rows) / len(ans_rows), 4),
            "latency_cold_ms": {
                "ret_p50": round(pctl(ret_c, 0.50), 2),
                "ret_mean": round(statistics.mean(ret_c), 2),
                "llm_p50": round(pctl(llm_l, 0.50), 2),
                "llm_mean": round(statistics.mean(llm_l), 2),
                "e2e_p50": round(pctl(e2e_c, 0.50), 2),
                "e2e_p90": round(pctl(e2e_c, 0.90), 2),
                "e2e_p99": round(pctl(e2e_c, 0.99), 2),
                "e2e_mean": round(statistics.mean(e2e_c), 2),
                "e2e_std": round(statistics.stdev(e2e_c), 2),
                "mean_additivity_check_diff": round(statistics.mean(e2e_c) - (statistics.mean(ret_c) + statistics.mean(llm_l)), 4),
            },
            "latency_warm_ms": {
                "ret_p50": round(pctl(ret_w, 0.50), 2),
                "ret_mean": round(statistics.mean(ret_w), 2),
                "llm_p50": round(pctl(llm_l, 0.50), 2),
                "llm_mean": round(statistics.mean(llm_l), 2),
                "e2e_p50": round(pctl(e2e_w, 0.50), 2),
                "e2e_p90": round(pctl(e2e_w, 0.90), 2),
                "e2e_p99": round(pctl(e2e_w, 0.99), 2),
                "e2e_mean": round(statistics.mean(e2e_w), 2),
                "e2e_std": round(statistics.stdev(e2e_w), 2),
                "mean_additivity_check_diff": round(statistics.mean(e2e_w) - (statistics.mean(ret_w) + statistics.mean(llm_l)), 4),
            },
        }

        summary["by_system_and_category"][sys_name] = {}
        for cat in ["Factual Q&A", "Cross-Article Comparison", "Literature Synthesis", "Safe Refusal (Edge)"]:
            c_rows = [r for r in s_rows if r["type"] == cat]
            if not c_rows:
                continue
            rc = [r["retrieval_cold_ms"] for r in c_rows]
            rw = [r["retrieval_warm_ms"] for r in c_rows]
            ll = [r["llm_ms"] for r in c_rows]
            ec = [r["e2e_cold_ms"] for r in c_rows]
            ew = [r["e2e_warm_ms"] for r in c_rows]
            summary["by_system_and_category"][sys_name][cat] = {
                "n": len(c_rows),
                "ret_cold_p50_ms": round(pctl(rc, 0.50), 2),
                "ret_cold_mean_ms": round(statistics.mean(rc), 2),
                "ret_warm_p50_ms": round(pctl(rw, 0.50), 2),
                "ret_warm_mean_ms": round(statistics.mean(rw), 2),
                "llm_p50_ms": round(pctl(ll, 0.50), 2),
                "llm_mean_ms": round(statistics.mean(ll), 2),
                "e2e_cold_p50_ms": round(pctl(ec, 0.50), 2),
                "e2e_cold_p90_ms": round(pctl(ec, 0.90), 2),
                "e2e_cold_p99_ms": round(pctl(ec, 0.99), 2),
                "e2e_cold_mean_ms": round(statistics.mean(ec), 2),
                "e2e_warm_p50_ms": round(pctl(ew, 0.50), 2),
                "e2e_warm_p90_ms": round(pctl(ew, 0.90), 2),
                "e2e_warm_p99_ms": round(pctl(ew, 0.99), 2),
                "e2e_warm_mean_ms": round(statistics.mean(ew), 2),
                "macro_syntactic_cite_validity": round(statistics.mean(r["syntactic_citation_validity"] for r in c_rows), 4),
                "macro_gt_doc_cite_precision": round(statistics.mean(r["gt_doc_citation_precision"] for r in c_rows), 4),
                "refusal_rate": round(sum(r["total_refused"] for r in c_rows) / len(c_rows), 4),
            }

    (GEN_DIR / "generation_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nSaved Stage 7 results to {auto_csv_path} and generation_summary.json", flush=True)


if __name__ == "__main__":
    main()
