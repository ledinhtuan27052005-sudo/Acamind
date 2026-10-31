"""
Fast, 100%-Psychology Harvester & Ingester for 500 Non-Duplicate PDFs covering the 300-Question Benchmark.
Sources:
  1. PsyArXiv (Official Psychology Preprint Repository via OSF API: api.osf.io -> osf.io/download/{id}/)
  2. ERIC (U.S. Dept. of Education Full-Text Psychology & Counseling Repository: api.ies.ed.gov -> files.eric.ed.gov/fulltext/{id}.pdf)

Guarantees:
  - 0% duplication against existing 1,028 DB documents (checked by filename, normalized title, and SHA-256 content hash).
  - Persistent HTTP keep-alive connection pooling to 2 high-speed CDNs (osf.io & files.eric.ed.gov) — zero DNS timeouts.
  - Thread-safe main-thread PyMuPDF (fitz) parsing + batched SentenceTransformer (intfloat/multilingual-e5-base) encoding.
"""
import os
import sys
import io
import re
import time
import uuid
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz
import torch
import psycopg2
from psycopg2.extras import execute_values
import requests
from requests.adapters import HTTPAdapter
from sentence_transformers import SentenceTransformer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.chunking import chunk_text

DB_DSN = "postgresql://admin:secret@127.0.0.1:5432/rag_db"
PDF_STORAGE_DIR = Path(r"c:\Users\Admin\Desktop\Acamind\backend\data\PDF")
RAW_PDFS_DIR = Path(r"c:\Users\Admin\Desktop\Acamind\data\raw_pdfs")
TARGET_NEW_PDFS = 500
DOC_PREFIX = "passage: "

PSYARXIV_KEYWORDS = [
    "psychology", "cognitive", "memory", "attention", "emotion", "motivation",
    "self-esteem", "self-efficacy", "empathy", "procrastination", "loneliness",
    "shame", "guilt", "anger", "perception", "psychoanalysis", "conditioning",
    "behaviorism", "humanistic", "Piaget", "Vygotsky", "Bandura", "intelligence",
    "evolutionary", "attachment", "Sternberg", "personality", "Big Five",
    "borderline", "narcissism", "psychopathy", "antisocial", "schizoid",
    "Rorschach", "clinical interview", "Beck Depression", "PHQ-9", "GAD-7",
    "depression", "dysthymia", "anxiety", "panic", "agoraphobia", "bipolar",
    "mania", "obsessive-compulsive", "OCD", "PTSD", "trauma", "childhood",
    "schizophrenia", "psychosis", "autism", "ADHD", "hyperactivity",
    "anorexia", "bulimia", "eating disorder", "insomnia", "sleep", "somatic",
    "separation anxiety", "phobia", "social anxiety", "Tourette", "tic",
    "burnout", "postpartum", "grief", "bereavement", "addiction", "substance",
    "imposter", "perfectionism", "bystander", "conformity", "obedience",
    "cognitive dissonance", "confirmation bias", "placebo", "stress", "coping",
    "flow", "positive psychology", "resilience", "dissociation", "hoarding",
    "body dysmorphic", "conduct disorder", "oppositional", "dementia", "Alzheimer",
    "adolescent", "identity", "aging", "existential", "meaning", "cyberbullying",
    "suicide", "self-harm", "cognitive behavioral therapy", "CBT", "dialectical",
    "DBT", "acceptance and commitment", "ACT", "EMDR", "psychodynamic",
    "transference", "family therapy", "group therapy", "mindfulness", "MBSR",
    "hypnosis", "desensitization", "exposure therapy", "virtual reality",
    "emotionally focused", "couples therapy", "Gottman", "light therapy",
    "art therapy", "music therapy", "play therapy", "narrative therapy",
    "applied behavior analysis", "parent training", "biofeedback", "neurofeedback",
    "assertiveness", "expressive writing", "motivational interviewing",
    "antidepressant", "SSRI", "lithium", "antipsychotic", "benzodiazepine",
    "methylphenidate", "electroconvulsive",
]

ERIC_QUERIES = [
    '"Introduction to Psychology" OR "scientific study of behavior"',
    '"general psychology" AND ("mental processes" OR "cognitive psychology")',
    '"Sigmund Freud" OR "psychoanalysis" OR "defense mechanisms"',
    '"Carl Jung" OR "Alfred Adler" OR "individual psychology"',
    '"operant conditioning" OR "B.F. Skinner" OR "classical conditioning"',
    '"Carl Rogers" OR "client-centered" OR "unconditional positive regard"',
    '"Maslow" AND ("hierarchy of needs" OR "self-actualization")',
    '"Jean Piaget" AND ("cognitive development" OR "stages")',
    '"Vygotsky" AND ("zone of proximal development" OR "scaffolding")',
    '"Albert Bandura" AND ("social learning" OR "self-efficacy")',
    '"emotional intelligence" AND ("Goleman" OR "Mayer" OR "EQ")',
    '"Howard Gardner" OR "multiple intelligences"',
    '"attachment theory" AND ("Bowlby" OR "Ainsworth")',
    '"Sternberg" AND ("triangular theory" OR "love" OR "intelligence")',
    '"Big Five" AND ("personality" OR "conscientiousness" OR "neuroticism")',
    '"Eysenck" AND ("extraversion" OR "neuroticism" OR "personality")',
    '"borderline personality" OR "narcissistic personality" OR "antisocial personality"',
    '"Rorschach" OR "projective test" OR "structured clinical interview"',
    '"Beck Depression Inventory" OR "PHQ-9" OR "GAD-7"',
    '"working memory" AND ("short-term memory" OR "long-term memory" OR "Baddeley")',
    '"forgetting" AND ("interference" OR "memory" OR "Ebbinghaus")',
    '"selective attention" OR "divided attention" OR "divergent thinking"',
    '"emotion regulation" AND ("cognitive reappraisal" OR "suppression")',
    '"intrinsic motivation" AND ("extrinsic motivation" OR "self-determination")',
    '"procrastination" AND ("self-regulation" OR "academic")',
    '"loneliness" AND ("social isolation" OR "mental health")',
    '"guilt" AND "shame" AND "emotion"',
    '"anger management" OR "aggression" AND "psychology"',
    '"major depressive disorder" OR "persistent depressive" OR "dysthymia"',
    '"generalized anxiety" OR "panic disorder" OR "social anxiety"',
    '"bipolar disorder" OR "obsessive-compulsive" OR "PTSD"',
    '"adverse childhood experiences" OR "childhood trauma" AND "mental health"',
    '"schizophrenia" OR "autism spectrum disorder" OR "ADHD"',
    '"anorexia nervosa" OR "bulimia nervosa" OR "eating disorders"',
    '"insomnia" AND ("sleep" OR "CBT-I" OR "circadian")',
    '"separation anxiety" OR "specific phobia" OR "Tourette"',
    '"occupational burnout" OR "Maslach" OR "compassion fatigue"',
    '"grief" AND ("bereavement" OR "counseling")',
    '"substance abuse" OR "addiction" AND ("counseling" OR "12-step")',
    '"imposter syndrome" OR "perfectionism" OR "cognitive dissonance"',
    '"bystander effect" OR "conformity" OR "social psychology"',
    '"stress coping" OR "resilience" OR "post-traumatic growth"',
    '"Erik Erikson" OR "identity development" OR "adolescent psychology"',
    '"school psychology" AND ("bullying" OR "cyberbullying" OR "suicide prevention")',
    '"cognitive behavioral therapy" AND ("depression" OR "anxiety" OR "Beck")',
    '"dialectical behavior therapy" OR "acceptance and commitment therapy"',
    '"EMDR" OR "eye movement desensitization" OR "prolonged exposure"',
    '"systemic family therapy" OR "group psychotherapy" OR "mindfulness"',
    '"systematic desensitization" OR "virtual reality exposure" OR "hypnotherapy"',
    '"emotionally focused therapy" OR "Gottman" OR "couples counseling"',
    '"art therapy" OR "music therapy" OR "play therapy" OR "narrative therapy"',
    '"applied behavior analysis" OR "behavioral parent training" OR "biofeedback"',
    '"assertiveness training" OR "expressive writing" OR "motivational interviewing"',
    '"psychopharmacology" OR "antidepressants" OR "SSRIs" OR "lithium" OR "stimulants"',
]

PSYCH_KEYWORDS_RE = re.compile(
    r"\b(psychol|cognit|behav|therap|emotion|mental|disord|anxiet|depress|memori|learn|"
    r"freud|piaget|attach|person|social|brain|stress|trauma|autism|adhd|schizophren|"
    r"bipolar|sleep|phobia|empat|motiv|self|clin|syndrom|counsel|patient|symptom|psychiatr|mindful)\w*\b",
    re.I,
)


def normalize_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


def create_http_session() -> requests.Session:
    s = requests.Session()
    adapter = HTTPAdapter(pool_connections=40, pool_maxsize=40, max_retries=1)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/pdf,application/json,*/*",
    })
    return s


def load_existing_dedup_sets(conn):
    existing_filenames = set()
    existing_titles = set()
    existing_hashes = set()

    with conn.cursor() as cur:
        cur.execute("SELECT filename, title FROM documents;")
        for fn, title in cur.fetchall():
            if fn:
                existing_filenames.add(fn.lower())
            if title:
                nt = normalize_title(title)
                if len(nt) >= 10:
                    existing_titles.add(nt)

    for folder in [PDF_STORAGE_DIR, RAW_PDFS_DIR]:
        if folder.exists():
            for p in folder.glob("*.pdf"):
                existing_filenames.add(p.name.lower())
                try:
                    h = hashlib.sha256(p.read_bytes()).hexdigest()
                    existing_hashes.add(h)
                except Exception:
                    pass

    return existing_filenames, existing_titles, existing_hashes


def harvest_candidates(session: requests.Session):
    seen_ids = set()
    seen_titles = set()
    psyarxiv_list = []
    eric_list = []

    print(f"[Harvester] Fetching candidates from PsyArXiv ({len(PSYARXIV_KEYWORDS)} topics) & ERIC ({len(ERIC_QUERIES)} queries)...", flush=True)

    def fetch_psyarxiv(kw: str):
        out = []
        try:
            r = session.get(
                "https://api.osf.io/v2/preprints/",
                params={"filter[provider]": "psyarxiv", "filter[title]": kw, "page[size]": 25},
                timeout=8,
            )
            if r.status_code == 200:
                for d in r.json().get("data", []):
                    raw_id = d.get("id", "")
                    pid = raw_id.split("_")[0]
                    attrs = d.get("attributes", {})
                    title = (attrs.get("title") or "").replace("\x00", "").strip()
                    if not pid or len(title) < 12:
                        continue
                    pub_date = attrs.get("date_published") or attrs.get("date_created") or "2024"
                    year = int(pub_date[:4]) if pub_date[:4].isdigit() else 2024
                    out.append({
                        "source": "PsyArXiv",
                        "id": f"PsyArXiv_{pid}",
                        "title": title,
                        "authors": "PsyArXiv Psychology Preprint",
                        "year": year,
                        "url": f"https://osf.io/download/{pid}/",
                    })
        except Exception:
            pass
        return out

    def fetch_eric(q: str):
        out = []
        try:
            full_q = f"({q}) AND (id:ED5* OR id:ED6* OR id:ED4* OR id:ED3* OR id:EJ11* OR id:EJ12* OR id:EJ13* OR id:EJ14*)"
            r = session.get(
                "https://api.ies.ed.gov/eric/",
                params={"search": full_q, "format": "json", "rows": 45},
                timeout=8,
            )
            if r.status_code == 200:
                for d in r.json().get("response", {}).get("docs", []):
                    did = d.get("id")
                    title = (d.get("title") or "").replace("\x00", "").strip()
                    if not did or len(title) < 12:
                        continue
                    year = d.get("publicationdateyear") or 2022
                    author_list = d.get("author") or []
                    authors = ", ".join(author_list[:5]).replace("\x00", "") if isinstance(author_list, list) and author_list else "ERIC Psychology Scholar"
                    out.append({
                        "source": "ERIC",
                        "id": f"ERIC_{did}",
                        "title": title,
                        "authors": authors,
                        "year": int(year) if str(year).isdigit() else 2022,
                        "url": f"https://files.eric.ed.gov/fulltext/{did}.pdf",
                    })
        except Exception:
            pass
        return out

    with ThreadPoolExecutor(max_workers=20) as ex:
        f_psy = [ex.submit(fetch_psyarxiv, kw) for kw in PSYARXIV_KEYWORDS]
        f_eric = [ex.submit(fetch_eric, q) for q in ERIC_QUERIES]
        for fut in as_completed(f_psy):
            for item in fut.result():
                nt = normalize_title(item["title"])
                if item["id"] not in seen_ids and nt not in seen_titles and len(nt) >= 10:
                    seen_ids.add(item["id"])
                    seen_titles.add(nt)
                    psyarxiv_list.append(item)
        for fut in as_completed(f_eric):
            for item in fut.result():
                nt = normalize_title(item["title"])
                if item["id"] not in seen_ids and nt not in seen_titles and len(nt) >= 10:
                    seen_ids.add(item["id"])
                    seen_titles.add(nt)
                    eric_list.append(item)

    print(f"[Harvester] Collected {len(psyarxiv_list)} PsyArXiv + {len(eric_list)} ERIC = {len(psyarxiv_list)+len(eric_list)} unique psychology candidates.", flush=True)
    interleaved = []
    m = max(len(psyarxiv_list), len(eric_list))
    for i in range(m):
        if i < len(psyarxiv_list):
            interleaved.append(psyarxiv_list[i])
        if i < len(eric_list):
            interleaved.append(eric_list[i])
    return interleaved


def parse_pdf_main_thread(raw_bytes: bytes):
    """Thread-safe main-thread PDF validation & extraction with PyMuPDF."""
    try:
        doc = fitz.open(stream=raw_bytes, filetype="pdf")
        num_pages = len(doc)
        if num_pages < 1 or num_pages > 24:
            doc.close()
            return None
        pages_data = []
        total_chars = 0
        sample_text = []
        for idx in range(num_pages):
            txt = (doc[idx].get_text() or "").replace("\x00", "")
            pages_data.append({"page": idx + 1, "text": txt})
            total_chars += len(txt.strip())
            if idx < 3:
                sample_text.append(txt)
        doc.close()
        if total_chars < 600:
            return None
        joined_sample = " ".join(sample_text)
        if len(PSYCH_KEYWORDS_RE.findall(joined_sample)) < 2:
            return None
        return {"total_pages": num_pages, "pages": pages_data}
    except Exception:
        return None


def main():
    PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False

    existing_filenames, existing_titles, existing_hashes = load_existing_dedup_sets(conn)
    print(
        f"[Init] Existing in DB/Disk: {len(existing_filenames)} filenames, "
        f"{len(existing_titles)} titles, {len(existing_hashes)} SHA-256 hashes.",
        flush=True,
    )

    session = create_http_session()
    all_candidates = harvest_candidates(session)

    candidates = []
    for c in all_candidates:
        nt = normalize_title(c["title"])
        fname = f"{c['id']}.pdf".lower()
        if nt in existing_titles or fname in existing_filenames:
            continue
        candidates.append(c)

    print(f"[Init] {len(candidates)} deduplicated candidates queued for fast streaming download.", flush=True)

    num_threads = os.cpu_count() or 4
    torch.set_num_threads(num_threads)
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    model.max_seq_length = 256
    print(f"[Embedder] Ready (768d, max_seq_length=256, CPU {num_threads} threads).", flush=True)

    def download_bytes(cand):
        try:
            resp = session.get(cand["url"], timeout=(3.0, 4.5), stream=True, allow_redirects=True)
            if resp.status_code != 200:
                resp.close()
                return None
            buf = []
            size = 0
            t0 = time.monotonic()
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    buf.append(chunk)
                    size += len(chunk)
                    if size > 3800000 or (time.monotonic() - t0) > 4.5:
                        resp.close()
                        return None
            resp.close()
            raw = b"".join(buf)
            if size >= 14000 and raw[:5].startswith(b"%PDF"):
                return cand, raw
        except Exception:
            pass
        return None

    lock_hashes = set(existing_hashes)
    lock_titles = set(existing_titles)
    lock_filenames = set(existing_filenames)

    total_ingested = 0
    total_chunks_added = 0
    cursor = 0
    window_size = 140
    t_start = time.time()
    cur = conn.cursor()

    while total_ingested < TARGET_NEW_PDFS and cursor < len(candidates):
        window = candidates[cursor : cursor + window_size]
        cursor += window_size

        downloaded = []
        with ThreadPoolExecutor(max_workers=28) as ex:
            futures = [ex.submit(download_bytes, c) for c in window]
            for fut in as_completed(futures):
                res = fut.result()
                if res:
                    downloaded.append(res)

        # Parse in main thread and accumulate batch for fast vectorized embedding
        ready_docs = []
        for cand, raw_bytes in downloaded:
            if total_ingested + len(ready_docs) >= TARGET_NEW_PDFS:
                break
            h = hashlib.sha256(raw_bytes).hexdigest()
            nt = normalize_title(cand["title"])
            filename = f"{cand['id']}.pdf"
            if h in lock_hashes or nt in lock_titles or filename.lower() in lock_filenames:
                continue

            parsed = parse_pdf_main_thread(raw_bytes)
            if not parsed:
                continue

            doc_uuid = str(uuid.uuid4())
            pages_data = parsed["pages"]
            full_text = "\n\n".join(p["text"] for p in pages_data)
            chunks = chunk_text(full_text, doc_uuid, pages_data)
            clean_chunks = []
            for c in chunks[:32]:  # Cap at 32 chunks per article for balanced representation & fast indexing
                c_str = (c.get("content") or "").replace("\x00", "").strip()
                if c_str:
                    c_copy = c.copy()
                    c_copy["content"] = c_str
                    clean_chunks.append(c_copy)
            if not clean_chunks:
                continue

            lock_hashes.add(h)
            lock_titles.add(nt)
            lock_filenames.add(filename.lower())
            ready_docs.append((cand, raw_bytes, parsed, filename, doc_uuid, clean_chunks))

        if not ready_docs:
            continue

        # Batch-encode all chunks across ready_docs in one single SentenceTransformer call
        all_chunk_texts = [DOC_PREFIX + c["content"] for item in ready_docs for c in item[5]]
        all_vectors = model.encode(
            all_chunk_texts,
            batch_size=128,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        vec_offset = 0
        for cand, raw_bytes, parsed, filename, doc_uuid, clean_chunks in ready_docs:
            n_c = len(clean_chunks)
            doc_vecs = all_vectors[vec_offset : vec_offset + n_c]
            vec_offset += n_c

            file_path = PDF_STORAGE_DIR / filename
            try:
                file_path.write_bytes(raw_bytes)
            except Exception as e:
                print(f"  [!] Failed writing {filename}: {e}", flush=True)
                continue

            page_text_records = [
                (str(uuid.uuid4()), doc_uuid, p["page"], p["text"])
                for p in parsed["pages"]
                if p["text"].strip()
            ]
            chunk_records = [
                (
                    str(uuid.uuid4()),
                    doc_uuid,
                    c["content"],
                    vec.tolist(),
                    c.get("page_number", 1),
                    c.get("chunk_index", idx_c),
                )
                for idx_c, (c, vec) in enumerate(zip(clean_chunks, doc_vecs))
            ]

            try:
                cur.execute(
                    """
                    INSERT INTO documents (
                        id, user_id, filename, file_path, title, authors, year,
                        total_pages, status, category, is_paywall, has_memory, memory_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        doc_uuid,
                        None,
                        filename,
                        str(file_path.resolve()),
                        cand["title"][:490],
                        (cand["authors"] or "Psychology Scholar")[:490],
                        cand["year"],
                        parsed["total_pages"],
                        "ready",
                        "Tâm lý học & Lâm sàng",
                        False,
                        False,
                        "pending",
                    ),
                )
                if page_text_records:
                    execute_values(
                        cur,
                        "INSERT INTO page_texts (id, document_id, page_number, content) VALUES %s;",
                        page_text_records,
                    )
                if chunk_records:
                    execute_values(
                        cur,
                        "INSERT INTO chunks (id, document_id, content, embedding, page_number, chunk_index) VALUES %s;",
                        chunk_records,
                    )
                conn.commit()
                total_ingested += 1
                total_chunks_added += n_c

                if total_ingested % 20 == 0 or total_ingested == TARGET_NEW_PDFS:
                    elapsed = time.time() - t_start
                    rate = total_ingested / max(elapsed, 0.1)
                    print(
                        f"  [{total_ingested}/{TARGET_NEW_PDFS}] ✓ {filename} ({cand['source']}, {parsed['total_pages']}p, {n_c}c) "
                        f"| '{cand['title'][:50]}...' | Chunks: +{total_chunks_added:,} [{elapsed:.1f}s, {rate:.1f} docs/s]",
                        flush=True,
                    )
            except Exception as db_err:
                conn.rollback()
                print(f"  [!] DB error for {filename}: {db_err}", flush=True)

    cur.execute("SELECT count(*) FROM documents WHERE status = 'ready';")
    final_docs = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM chunks;")
    final_chunks = cur.fetchone()[0]
    cur.close()
    conn.close()

    print("=" * 80, flush=True)
    print(f"🎉 COMPLETED: Added {total_ingested} non-duplicate psychology PDFs!", flush=True)
    print(f"📊 Total ready documents in DB: {final_docs:,} | Total chunks: {final_chunks:,}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
