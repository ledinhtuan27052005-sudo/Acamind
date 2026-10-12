# -*- coding: utf-8 -*-
"""
ingest_all_500_pdfs.py
Nạp TOÀN BỘ 500 tài liệu PDF từ backend/data/raw_pdfs_500/ vào PostgreSQL (Docker cổng 5433).
Cam kết: Nạp 100% toàn văn, không cắt bớt trang, không giới hạn số chunk.
"""

import os
import sys
import time
import json
import uuid
from pathlib import Path

# Đảm bảo UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

import fitz  # PyMuPDF
import psycopg2
from psycopg2.extras import execute_values
import torch

from app.services.chunking import chunk_text
from sentence_transformers import SentenceTransformer

DB_URL = "postgresql://admin:secret@localhost:5433/rag_db"
PDF_DIR = BACKEND_DIR / "data" / "raw_pdfs_500"
METADATA_FILE = BACKEND_DIR / "data" / "arxiv_500_metadata.json"

DOC_PREFIX = "passage: "

# ── Phân loại chủ đề tự động dựa vào nội dung ─────────────────────────────
def categorize_doc(title: str, summary: str, arxiv_cat: str) -> str:
    text = (title + " " + summary).lower()
    if any(k in text for k in ["neuro", "brain", "cortex", "eeg", "fMRI", "synapse"]):
        return "Neuropsychology"
    if any(k in text for k in ["therapy", "psychotherapy", "counseling", "cbt", "intervention", "treatment"]):
        return "Psychotherapy"
    if any(k in text for k in ["depress", "anxiety", "disorder", "schizophrenia", "clinical", "bipolar"]):
        return "Clinical Psychology"
    if any(k in text for k in ["cognit", "memory", "attention", "perception", "reasoning", "decision"]):
        return "Cognitive Psychology"
    if any(k in text for k in ["diagnos", "dsm", "symptom", "assessment", "scale", "inventory"]):
        return "DSM / ICD / Diagnosis"
    if any(k in text for k in ["behavior", "action", "habit", "reinforcement", "conditioning"]):
        return "Behavioral Psychology"
    if any(k in text for k in ["social", "group", "interpersonal", "stigma", "empathy"]):
        return "Social Psychology"
    if any(k in text for k in ["student", "school", "education", "learning", "academic", "teacher"]):
        return "Educational Psychology"
    if any(k in text for k in ["health", "wellbeing", "stress", "sleep", "physical", "quality of life"]):
        return "Health Psychology"
    if any(k in text for k in ["child", "adolescent", "development", "infant", "aging", "lifespan"]):
        return "Developmental Psychology"
    return "Research & Statistics"


def main():
    print("=" * 80)
    print("🚀 BẮT ĐẦU NẠP 100% TOÀN BỘ 500 TÀI LIỆU PDF VÀO ACAMIND (DOCKER POSTGRES)")
    print(f"📁 Thư mục PDF: {PDF_DIR}")
    print(f"💾 CSDL: {DB_URL}")
    print("=" * 80, flush=True)

    if not PDF_DIR.exists():
        print(f"❌ Không tìm thấy thư mục {PDF_DIR}")
        return

    # 1. Đọc metadata
    meta_dict = {}
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            for item in json.load(f):
                clean_id = item["id"].replace("/", "_")
                meta_dict[clean_id] = item

    pdf_files = sorted(list(PDF_DIR.glob("*.pdf")))
    total_files = len(pdf_files)
    print(f"📦 Đã tìm thấy {total_files} file PDF thực tế trên đĩa.", flush=True)

    # 2. Khởi tạo model SentenceTransformer
    print("🧠 Đang tải embedding model: intfloat/multilingual-e5-base...")
    num_threads = os.cpu_count() or 4
    torch.set_num_threads(num_threads)
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    print(f"✓ Model sẵn sàng (768 chiều, CPU {num_threads} threads).", flush=True)

    # 3. Kết nối Database
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    # Kiểm tra các file đã nạp trước đó
    cur.execute("SELECT filename FROM documents;")
    existing_filenames = {row[0] for row in cur.fetchall()}
    print(f"ℹ️ Đã có {len(existing_filenames)} file trong database (sẽ bỏ qua nếu trùng lặp).", flush=True)

    total_chunks_added = 0
    total_pages_added = 0
    start_time = time.time()

    for idx, pdf_path in enumerate(pdf_files, 1):
        filename = pdf_path.name
        stem = pdf_path.stem

        if filename in existing_filenames:
            continue

        meta = meta_dict.get(stem, {})
        title = (meta.get("title") or stem.replace("_", " ")).replace("\x00", "")
        raw_authors = ", ".join(meta.get("authors", [])) if meta.get("authors") else "Academic Researcher"
        authors = raw_authors.replace("\x00", "")
        category = categorize_doc(title, meta.get("summary", ""), meta.get("category", ""))
        year = 2024
        try:
            # Lấy năm từ arXiv ID (ví dụ: 2405.xxxxx -> 2024)
            if stem[:2].isdigit():
                y_prefix = int(stem[:2])
                year = 2000 + y_prefix if y_prefix < 50 else 1900 + y_prefix
        except Exception:
            year = 2024

        # 4. Trích xuất TOÀN BỘ trang của PDF
        doc_uuid = str(uuid.uuid4())
        try:
            doc_fitz = fitz.open(str(pdf_path))
            total_pages = len(doc_fitz)
            pages_data = []
            page_text_records = []

            for pno in range(total_pages):
                page_text = doc_fitz[pno].get_text().replace("\x00", "")
                pnum = pno + 1
                pages_data.append({"page": pnum, "text": page_text})
                if page_text.strip():
                    page_text_records.append((
                        str(uuid.uuid4()),
                        doc_uuid,
                        pnum,
                        page_text
                    ))
            doc_fitz.close()
        except Exception as e:
            print(f"⚠️ Lỗi đọc PDF {filename}: {e}", flush=True)
            continue

        # 5. Cắt chunk TOÀN BỘ nội dung không bỏ sót
        full_text = "\n\n".join(p["text"] for p in pages_data)
        if not full_text.strip():
            print(f"⚠️ File {filename} không có văn bản (trang rỗng).", flush=True)
            continue

        chunks = chunk_text(full_text, doc_uuid, pages_data)
        if not chunks:
            continue

        # 6. Vector hóa TOÀN BỘ chunks
        clean_chunks = []
        for c in chunks:
            clean_c = c.copy()
            clean_c["content"] = c["content"].replace("\x00", "")
            if clean_c["content"].strip():
                clean_chunks.append(clean_c)

        if not clean_chunks:
            continue

        chunk_texts = [DOC_PREFIX + c["content"] for c in clean_chunks]
        vectors = model.encode(
            chunk_texts,
            batch_size=128,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        chunk_records = []
        for i, (c, vec) in enumerate(zip(clean_chunks, vectors)):
            chunk_records.append((
                str(uuid.uuid4()),
                doc_uuid,
                c["content"],
                vec.tolist(),
                c.get("page_number", 1),
                c.get("chunk_index", i)
            ))

        # 7. Ghi vào database (Document -> Page Texts -> Chunks)
        try:
            # Insert document
            cur.execute("""
                INSERT INTO documents (
                    id, user_id, filename, file_path, title, authors, year,
                    total_pages, status, category, is_paywall, has_memory, memory_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                doc_uuid,
                None, # Public
                filename,
                str(pdf_path.resolve()),
                title,
                authors,
                year,
                total_pages,
                "ready",
                category,
                False,
                False,
                "pending"
            ))

            # Bulk insert page_texts
            if page_text_records:
                execute_values(
                    cur,
                    """
                    INSERT INTO page_texts (id, document_id, page_number, content)
                    VALUES %s;
                    """,
                    page_text_records
                )

            # Bulk insert chunks
            if chunk_records:
                execute_values(
                    cur,
                    """
                    INSERT INTO chunks (id, document_id, content, embedding, page_number, chunk_index)
                    VALUES %s;
                    """,
                    chunk_records
                )

            conn.commit()
            total_chunks_added += len(chunk_records)
            total_pages_added += total_pages
            existing_filenames.add(filename)

            elapsed = time.time() - start_time
            rate = total_chunks_added / max(0.1, elapsed)
            print(f"[{idx}/{total_files}] ✓ {stem[:28]}: {total_pages} trang, {len(chunk_records)} chunks ({category}) | Tổng chunks: {total_chunks_added:,} ({rate:.1f} c/s)", flush=True)

        except Exception as db_err:
            conn.rollback()
            print(f"❌ Lỗi ghi DB {filename}: {db_err}", flush=True)

    cur.close()
    conn.close()

    total_time = time.time() - start_time
    print("=" * 80)
    print(f"🎉 HOÀN TẤT NẠP TOÀN BỘ TÀI LIỆU VÀO DATABASE!")
    print(f"  • Tổng tài liệu đã xử lý: {len(existing_filenames)}")
    print(f"  • Tổng số trang văn bản: {total_pages_added:,}")
    print(f"  • Tổng số chunks vector: {total_chunks_added:,}")
    print(f"  • Thời gian thực thi: {total_time/60:.2f} phút")
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
