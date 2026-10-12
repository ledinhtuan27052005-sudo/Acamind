import psycopg2

conn = psycopg2.connect("postgresql://admin:secret@localhost:5432/rag_db")
cur = conn.cursor()

cur.execute("SELECT status, count(*) FROM documents GROUP BY status;")
print("Status counts:", cur.fetchall())

cur.execute("SELECT count(*), sum(total_pages), avg(total_pages), min(total_pages), max(total_pages) FROM documents WHERE total_pages IS NOT NULL;")
print("Pages stats:", cur.fetchone())

cur.execute("SELECT count(*) FROM documents WHERE is_paywall = true;")
print("Paywall / failed count:", cur.fetchone())

cur.execute("SELECT count(*) FROM chunks WHERE page_number IS NOT NULL;")
print("Chunks with page_number:", cur.fetchone())
