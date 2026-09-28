"""
rechunk_and_rerank.py — Re-process toàn bộ PDF trong DB với chunking + embedding mới.

Cần chạy SAU KHI đã sửa:
  - chunking.py (chunk_size=800, overlap=200, _find_page cải tiến)
  - embedder.py (prefix search_query: / search_document:)

Lý do cần re-process:
  - Chunk cũ dùng size=1500/overlap=150; chunk mới dùng 800/200 → không tương thích
  - Embed cũ không có prefix → retrieval mới (có prefix) sẽ không match

Cách chạy:
    cd backend
    python scripts/rechunk_and_rerank.py

Hoặc chỉ re-embed (giữ chunk cũ):
    python scripts/rechunk_and_rerank.py --skip-chunk

Tùy chọn:
    --doc-id <uuid>     chỉ re-process 1 document
    --skip-chunk        bỏ qua chunking, chỉ re-embed chunks hiện có
    --limit N           chỉ xử lý N document đầu tiên
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.document import Document
from app.services.parser import parse_pdf
from app.services.chunking import chunk_text as _chunk_text
from app.services.embedder import embed_and_store


# Alias để tránh shadowing bởi biến cục bộ
def _do_chunk(text, doc_id, pages):
    return _chunk_text(text, doc_id, pages)


def has_chunks(db, doc_id: str) -> bool:
    return db.execute(
        text("SELECT COUNT(*) FROM chunks WHERE document_id = :id"),
        {"id": doc_id},
    ).scalar() > 0


def delete_chunks(db, doc_id: str) -> int:
    result = db.execute(
        text("DELETE FROM chunks WHERE document_id = :id"),
        {"id": doc_id},
    )
    return result.rowcount or 0


def main():
    parser = argparse.ArgumentParser(description="Re-process PDF với chunk + embed mới")
    parser.add_argument("--doc-id", help="Chỉ re-process 1 document_id")
    parser.add_argument("--skip-chunk", action="store_true", help="Bỏ chunking, chỉ re-embed")
    parser.add_argument("--limit", type=int, help="Giới hạn số document xử lý")
    args = parser.parse_args()

    engine = create_engine(settings.POSTGRES_URL)
    Session = sessionmaker(bind=engine)

    db = Session()
    try:
        # Lấy danh sách document cần xử lý
        q = db.query(Document).filter(Document.status.in_(["ready", "processing"]))
        if args.doc_id:
            q = q.filter(Document.id == args.doc_id)
        if args.limit:
            q = q.limit(args.limit)
        docs = q.all()
        print(f"📚 Tìm thấy {len(docs)} document cần re-process\n")

        ok = 0
        fail = 0
        start = time.time()

        for i, doc in enumerate(docs, 1):
            doc_label = f"[{i}/{len(docs)}] {doc.title or doc.filename}"
            print(f"{doc_label[:80]}")
            t0 = time.time()

            try:
                if args.skip_chunk:
                    # Chỉ re-embed: xóa vector, giữ nguyên content
                    old_count = delete_chunks(db, str(doc.id))
                    print(f"  → Xóa {old_count} chunks cũ, đang re-embed...")
                    # Tạo lại chunk object từ page_texts
                    page_rows = db.execute(text("""
                        SELECT page_number, content FROM page_texts
                        WHERE document_id = :id ORDER BY page_number
                    """), {"id": str(doc.id)}).fetchall()
                    pages_data = [{"page": r.page_number, "text": r.content} for r in page_rows]
                    full_text = "\n".join(f"[Trang {p['page']}]\n{p['text']}" for p in pages_data)
                    new_chunks = _do_chunk(full_text, str(doc.id), pages_data)
                    print(f"  → Tạo {len(new_chunks)} chunks mới, đang embed với prefix search_document:")
                    embed_and_store(new_chunks, db)
                else:
                    # Re-parse + re-chunk + re-embed từ file PDF
                    print(f"  → Đang parse PDF...")
                    parsed = parse_pdf(doc.file_path)
                    if not parsed["full_text"].strip():
                        print(f"  ⚠ PDF rỗng text, bỏ qua")
                        fail += 1
                        continue
                    delete_chunks(db, str(doc.id))
                    # Cập nhật page_texts
                    db.execute(text("DELETE FROM page_texts WHERE document_id = :id"), {"id": str(doc.id)})
                    from sqlalchemy import text as sql_text
                    for p in parsed["pages"]:
                        if p.get("text", "").strip():
                            db.execute(sql_text("""
                                INSERT INTO page_texts (document_id, page_number, content)
                                VALUES (:doc_id, :page, :content)
                                ON CONFLICT (document_id, page_number) DO UPDATE SET content = EXCLUDED.content
                            """), {"doc_id": str(doc.id), "page": p["page"], "content": p["text"]})
                    db.commit()

                    new_chunks = _do_chunk(parsed["full_text"], str(doc.id), parsed["pages"])
                    print(f"  → Tạo {len(new_chunks)} chunks mới, đang embed với prefix search_document:")
                    embed_and_store(new_chunks, db)

                # Cập nhật metadata nếu parse lại
                if not args.skip_chunk:
                    doc.total_pages = parsed.get("total_pages", doc.total_pages)
                    if not doc.title and parsed.get("metadata", {}).get("title"):
                        doc.title = parsed["metadata"]["title"]
                    if not doc.authors and parsed.get("metadata", {}).get("author"):
                        doc.authors = parsed["metadata"]["author"]
                doc.status = "ready"
                db.commit()

                elapsed = time.time() - t0
                print(f"  ✅ Done ({elapsed:.1f}s)\n")
                ok += 1
            except Exception as e:
                print(f"  ❌ Lỗi: {e}\n")
                try:
                    db.rollback()
                except Exception:
                    pass
                fail += 1

        total = time.time() - start
        print("=" * 60)
        print(f"✅ Thành công: {ok}/{len(docs)} | ❌ Lỗi: {fail}")
        print(f"⏱ Tổng thời gian: {total:.1f}s ({total/60:.1f} phút)")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    main()
