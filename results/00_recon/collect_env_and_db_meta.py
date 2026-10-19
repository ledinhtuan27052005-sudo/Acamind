# -*- coding: utf-8 -*-
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import fitz
import psycopg2
import sentence_transformers
import torch

info = {
    "python": sys.version,
    "executable": sys.executable,
    "platform": platform.platform(),
    "processor": platform.processor(),
    "cpu_count_logical": os.cpu_count(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "sentence_transformers": sentence_transformers.__version__,
    "pymupdf": fitz.__doc__,
}

try:
    import psutil
    info["cpu_count_physical"] = psutil.cpu_count(logical=False)
    info["ram_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
except Exception as e:
    info["psutil"] = str(e)

try:
    import FlagEmbedding
    info["FlagEmbedding"] = getattr(FlagEmbedding, "__version__", "installed")
except Exception as e:
    info["FlagEmbedding"] = str(e)

try:
    import rank_bm25
    info["rank_bm25"] = getattr(rank_bm25, "__version__", "installed")
except Exception as e:
    info["rank_bm25"] = str(e)

try:
    git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    git_status = subprocess.check_output(["git", "status", "--short"], text=True).strip()
    info["git_commit"] = git_hash
    info["git_dirty_files_count"] = len(git_status.splitlines()) if git_status else 0
except Exception as e:
    info["git_commit"] = str(e)

for port in [5432, 5433]:
    conn = psycopg2.connect(f"postgresql://admin:secret@localhost:{port}/rag_db")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    pg_ver = cur.fetchone()[0]
    cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname='vector';")
    vec_ver = cur.fetchone()
    cur.execute(
        "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE tablename IN ('chunks', 'page_texts', 'documents') ORDER BY tablename, indexname;"
    )
    idxs = cur.fetchall()
    cur.execute(
        "SELECT category, count(*), sum(total_pages) FROM documents GROUP BY category ORDER BY category;"
    )
    cats = cur.fetchall()
    cur.execute(
        "SELECT d.category, count(c.id), count(c.embedding) FROM documents d LEFT JOIN chunks c ON d.id = c.document_id GROUP BY d.category ORDER BY d.category;"
    )
    chunk_cats = cur.fetchall()
    cur.execute("SHOW hnsw.ef_search;")
    ef_search_default = cur.fetchone()[0]
    info[f"db_{port}"] = {
        "pg_version": pg_ver,
        "pgvector": vec_ver,
        "default_ef_search": ef_search_default,
        "indexes": idxs,
        "doc_categories": cats,
        "chunk_categories": chunk_cats,
    }
    conn.close()

# Check character density across all 499 PDFs in backend/data/raw_pdfs_500
pdf_dir = Path("backend/data/raw_pdfs_500")
pdf_files = sorted(pdf_dir.glob("*.pdf"))
low_density_docs = []
zero_char_pages = 0
low_char_pages = 0
min_doc_density = float("inf")
min_doc_name = None

for pf in pdf_files:
    doc = fitz.open(str(pf))
    n_pages = len(doc)
    total_chars = 0
    for pno in range(n_pages):
        txt = doc[pno].get_text().strip()
        clen = len(txt)
        total_chars += clen
        if clen == 0:
            zero_char_pages += 1
        if clen < 50:
            low_char_pages += 1
    doc.close()
    density = total_chars / max(1, n_pages)
    if density < min_doc_density:
        min_doc_density = density
        min_doc_name = pf.name
    if density < 50:
        low_density_docs.append({"filename": pf.name, "density": density, "pages": n_pages})

info["pdf_scan_audit_499"] = {
    "total_pdfs": len(pdf_files),
    "docs_with_density_below_50": len(low_density_docs),
    "low_density_docs": low_density_docs,
    "min_doc_density": round(min_doc_density, 2),
    "min_doc_name": min_doc_name,
    "pages_with_0_chars": zero_char_pages,
    "pages_with_below_50_chars": low_char_pages,
}

out_path = Path("results/00_recon/env_and_db_meta.json")
out_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
print("Saved to", out_path)
