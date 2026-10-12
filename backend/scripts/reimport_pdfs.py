"""
Re-import PDF files from raw_pdfs directory into the database.
Run from the backend/ directory:
    python scripts/reimport_pdfs.py
"""
import sys, os, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.document import Document

engine = create_engine(settings.POSTGRES_URL)
Session = sessionmaker(bind=engine)

RAW_PDFS = Path(settings.get_pdf_upload_dir())

def main():
    db = Session()

    # Lấy tất cả file_path đang có trong DB
    existing_paths = {row[0] for row in db.execute(text("SELECT file_path FROM documents")).fetchall()}
    existing_ids   = {str(row[0]) for row in db.execute(text("SELECT id FROM documents")).fetchall()}

    pdf_files = list(RAW_PDFS.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files on disk, {len(existing_paths)} in DB")

    inserted = 0
    skipped  = 0

    for fpath in sorted(pdf_files):
        abs_path = str(fpath)

        # Bỏ qua nếu đã có trong DB theo file_path
        if abs_path in existing_paths:
            skipped += 1
            continue

        # Trích UUID và tên gốc từ tên file: {uuid}_{original}.pdf
        name = fpath.stem  # bỏ .pdf
        parts = name.split("_", 1)

        # Thử parse UUID từ phần đầu
        doc_id = None
        original_name = name
        if len(parts) == 2:
            try:
                doc_id = str(uuid.UUID(parts[0]))
                original_name = parts[1]
            except ValueError:
                pass

        if doc_id is None:
            doc_id = str(uuid.uuid4())

        # Bỏ qua nếu ID này đã có
        if doc_id in existing_ids:
            skipped += 1
            continue

        filename = original_name + ".pdf"

        doc = Document(
            id=uuid.UUID(doc_id),
            filename=filename,
            file_path=abs_path,
            title=original_name.replace("_", " "),
            status="processing",
            user_id=None,
        )
        db.add(doc)
        existing_ids.add(doc_id)
        inserted += 1
        try:
            print(f"  [+] {filename[:60]}")
        except Exception:
            print(f"  [+] {filename[:60].encode('ascii', 'replace').decode('ascii')}")

    db.commit()
    db.close()
    print(f"\nDone: {inserted} inserted, {skipped} skipped.")
    print("Files are marked 'processing'. Restart backend to auto-process, or re-upload to trigger pipeline.")

if __name__ == "__main__":
    main()
