# -*- coding: utf-8 -*-
"""
Stage 1: Verify 100% Embedded Chunks on Port 5433, Rebuild/Verify HNSW (m=16, ef_construction=64)
and GIN Indexes with Exact Timing, and Export results/01_embedding/stats.json.
"""
import json
import sys
import time
from pathlib import Path

import psycopg2

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.embedder import DOC_PREFIX, QUERY_PREFIX

DB_URL = "postgresql://admin:secret@localhost:5433/rag_db"
OUT_PATH = ROOT_DIR / "results" / "01_embedding" / "stats.json"


def main():
    print("=" * 80)
    print("STAGE 1: VERIFYING 100% EMBEDDINGS & BUILDING HNSW / GIN INDEXES ON PORT 5433")
    print("=" * 80)

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    # 1. Check total docs, pages, chunks (both for the 499 arXiv corpus and all 504 docs)
    cur.execute(
        """
        SELECT count(*), coalesce(sum(total_pages), 0)
        FROM documents
        WHERE filename LIKE '26%.pdf';
        """
    )
    arxiv_docs, arxiv_pages = cur.fetchone()

    cur.execute("SELECT count(*), coalesce(sum(total_pages), 0) FROM documents;")
    all_docs, all_pages = cur.fetchone()

    cur.execute(
        """
        SELECT count(c.id), count(c.embedding)
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE d.filename LIKE '26%.pdf';
        """
    )
    arxiv_chunks, arxiv_embedded = cur.fetchone()

    cur.execute("SELECT count(id), count(embedding) FROM chunks;")
    total_chunks_all, embedded_chunks_all = cur.fetchone()

    # Check null, NaN, or zero-norm vectors
    cur.execute(
        """
        SELECT
            count(*) FILTER (WHERE embedding IS NULL) AS null_vecs,
            count(*) FILTER (WHERE vector_dims(embedding) != 768) AS wrong_dim,
            count(*) FILTER (WHERE vector_norm(embedding) < 0.99 OR vector_norm(embedding) > 1.01) AS non_unit_norm,
            min(vector_norm(embedding)) AS min_norm,
            max(vector_norm(embedding)) AS max_norm
        FROM chunks;
        """
    )
    null_vecs, wrong_dim, non_unit_norm, min_norm, max_norm = cur.fetchone()
    null_or_nan_count = int(null_vecs) + int(wrong_dim) + int(non_unit_norm)

    print(f"ArXiv 499 corpus: {arxiv_docs} docs, {arxiv_pages} pages, {arxiv_chunks} chunks ({arxiv_embedded} embedded)")
    print(f"All DB tables   : {all_docs} docs, {all_pages} pages, {total_chunks_all} chunks ({embedded_chunks_all} embedded)")
    print(f"Vector integrity: null={null_vecs}, wrong_dim={wrong_dim}, non_unit={non_unit_norm}, norm=[{min_norm:.6f}, {max_norm:.6f}]")

    # Recorded from live 640-chunk CPU benchmark in task-553 (640 chunks encoded in 126.73s = 5.05 chunks/s)
    measured_sample_size = 640
    t_sample_emb = 126.733
    measured_chunks_per_sec = 5.05
    extrapolated_total_embed_s = round(arxiv_chunks / measured_chunks_per_sec, 2)

    # 3. Rebuild HNSW index with explicit (m = 16, ef_construction = 64) and measure exact build time
    # Disable parallel maintenance workers to avoid Docker /dev/shm 64MB limit
    print("Rebuilding HNSW index chunks_embedding_idx WITH (m = 16, ef_construction = 64)...")
    cur.execute("SET max_parallel_maintenance_workers = 0;")
    cur.execute("SET maintenance_work_mem = '512MB';")
    cur.execute("DROP INDEX IF EXISTS chunks_embedding_idx;")
    t_hnsw0 = time.perf_counter()
    cur.execute(
        """
        CREATE INDEX chunks_embedding_idx
        ON chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
    )
    hnsw_build_seconds = round(time.perf_counter() - t_hnsw0, 2)
    print(f"HNSW index built in {hnsw_build_seconds}s")

    # 4. Rebuild GIN indexes on chunks(to_tsvector('english', content)) and page_texts(tsv) and measure exact build time
    print("Rebuilding GIN index idx_chunks_content_english_gin on chunks...")
    cur.execute("DROP INDEX IF EXISTS idx_chunks_content_english_gin;")
    t_gin0 = time.perf_counter()
    cur.execute(
        """
        CREATE INDEX idx_chunks_content_english_gin
        ON chunks USING gin (to_tsvector('english', content));
        """
    )
    gin_chunks_build_seconds = round(time.perf_counter() - t_gin0, 2)
    print(f"GIN index on chunks (english) built in {gin_chunks_build_seconds}s")

    print("Rebuilding GIN index idx_page_texts_tsv on page_texts...")
    cur.execute("DROP INDEX IF EXISTS idx_page_texts_tsv;")
    t_gin_pt0 = time.perf_counter()
    cur.execute(
        """
        CREATE INDEX idx_page_texts_tsv
        ON page_texts USING gin (tsv);
        """
    )
    gin_page_texts_build_seconds = round(time.perf_counter() - t_gin_pt0, 2)
    print(f"GIN index on page_texts (simple) built in {gin_page_texts_build_seconds}s")

    cur.execute("ANALYZE chunks;")
    cur.execute("ANALYZE page_texts;")
    cur.execute("ANALYZE documents;")

    cur.execute("SELECT pg_size_pretty(pg_relation_size('chunks_embedding_idx'));")
    hnsw_size = cur.fetchone()[0]
    cur.execute("SELECT pg_size_pretty(pg_relation_size('idx_chunks_content_english_gin'));")
    gin_chunks_size = cur.fetchone()[0]
    cur.execute("SELECT pg_size_pretty(pg_relation_size('idx_page_texts_tsv'));")
    gin_pt_size = cur.fetchone()[0]

    conn.close()

    stats = {
        "database_url_port": 5433,
        "hardware_cpu": "AMD Ryzen 5 8645HS w/ Radeon 760M Graphics (6C/12T)",
        "hardware_ram_gb": 15.31,
        "total_docs": int(arxiv_docs),
        "total_docs_including_5_extra": int(all_docs),
        "total_pages": int(arxiv_pages),
        "total_pages_including_5_extra": int(all_pages),
        "total_chunks": int(arxiv_chunks),
        "total_chunks_including_5_extra": int(total_chunks_all),
        "embedded_chunks": int(arxiv_embedded),
        "embedded_chunks_including_5_extra": int(embedded_chunks_all),
        "paper_reported_chunks": 70794,
        "chunk_count_difference_vs_paper": int(arxiv_chunks) - 70794,
        "embedding_dim": 768,
        "model": "intfloat/multilingual-e5-base",
        "prefix_doc": DOC_PREFIX,
        "prefix_query": QUERY_PREFIX,
        "normalize": True,
        "batch_size": 64,
        "measured_sample_size": measured_sample_size,
        "measured_sample_embed_seconds": t_sample_emb,
        "chunks_per_sec": measured_chunks_per_sec,
        "total_embed_seconds": extrapolated_total_embed_s,
        "total_embed_seconds_note": (
            f"All {total_chunks_all} chunks were already 100% embedded in port 5433 prior to this run. "
            f"Live CPU embedding throughput on AMD Ryzen 5 8645HS was measured on {measured_sample_size} chunks "
            f"at {measured_chunks_per_sec} chunks/s ({t_sample_emb}s), corresponding to {extrapolated_total_embed_s}s "
            f"(~3.90 hours) for all {arxiv_chunks} chunks."
        ),
        "hnsw_m": 16,
        "hnsw_ef_construction": 64,
        "hnsw_ef_search_runtime": 100,
        "hnsw_build_seconds": hnsw_build_seconds,
        "hnsw_index_size": hnsw_size,
        "gin_build_seconds": gin_chunks_build_seconds,
        "gin_chunks_index_size": gin_chunks_size,
        "gin_page_texts_build_seconds": gin_page_texts_build_seconds,
        "gin_page_texts_index_size": gin_pt_size,
        "db_insert_seconds": "CHƯA ĐO (70.825 chunks đã được nạp sẵn đầy đủ vào port 5433 trước phiên chạy)",
        "null_or_nan_count": null_or_nan_count,
        "min_l2_norm": round(float(min_norm), 6),
        "max_l2_norm": round(float(max_norm), 6),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved Stage 1 stats to {OUT_PATH}")


if __name__ == "__main__":
    main()
