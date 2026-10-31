"""Exact file duplicates and conservative metadata-based version candidates."""
import re
import unicodedata
from difflib import SequenceMatcher
from itertools import combinations
from app.models.document import Document


def find_upload_duplicate(db, content_hash, user_id):
    return db.query(Document).filter(Document.content_hash == content_hash,
        Document.user_id == user_id, Document.status.in_(['ready', 'processing'])).first()


def normalize_title(value):
    value = unicodedata.normalize('NFKC', value or '').casefold()
    return ' '.join(re.findall(r'\w+', value))


def detect_duplicate_pairs(documents):
    pairs = []
    for a, b in combinations(documents, 2):
        if str(a.id) == str(b.id):
            continue
        exact = bool(a.content_hash and b.content_hash and a.content_hash == b.content_hash)
        title_a, title_b = normalize_title(a.title), normalize_title(b.title)
        # Filenames and short/generic titles cannot establish version identity.
        informative = min(len(title_a.split()), len(title_b.split())) >= 5 and min(len(title_a), len(title_b)) >= 30
        similarity = SequenceMatcher(None, title_a, title_b).ratio() if informative else None
        if not exact and (similarity is None or similarity < .9):
            continue
        pairs.append({
            'document_a': str(a.id), 'document_b': str(b.id),
            'kind': 'identical_file' if exact else 'possible_version',
            'reason': 'Hai tệp có cùng SHA-256.' if exact else 'Tiêu đề rất giống nhau; cần kiểm tra tác giả, DOI và nội dung trước khi coi là cùng nghiên cứu.',
            'title_similarity': similarity,
            'metadata_a': {'title': a.title or a.filename, 'authors': a.authors, 'year': a.year},
            'metadata_b': {'title': b.title or b.filename, 'authors': b.authors, 'year': b.year},
        })
    return pairs
