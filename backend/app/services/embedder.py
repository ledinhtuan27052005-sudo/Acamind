import hashlib
import json
import logging
import threading
import urllib.request
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Embedding Configuration ──────────────────────────────────────────────────
# Primary: Gemini API embedding (models/gemini-embedding-001) với outputDimensionality=768
# Phù hợp hoàn hảo với schema VECTOR(768) trong PostgreSQL pgvector, không bị lỗi DLL PyTorch trên Windows.
# Fallback: intfloat/multilingual-e5-base via sentence-transformers nếu không có API key.
_EMBED_MODEL_NAME = "intfloat/multilingual-e5-base"
_EMBED_DIM = 768
DOC_PREFIX = "passage: "
QUERY_PREFIX = "query: "

_model_lock = threading.Lock()
_local_model = None


def _get_local_model():
    """Lazy load local sentence-transformers model as fallback."""
    global _local_model
    if _local_model is not None:
        return _local_model
    with _model_lock:
        if _local_model is not None:
            return _local_model
        try:
            logger.info("Loading local embedding model: %s...", _EMBED_MODEL_NAME)
            from sentence_transformers import SentenceTransformer
            _local_model = SentenceTransformer(_EMBED_MODEL_NAME)
            logger.info("Local embedding model loaded OK")
            return _local_model
        except Exception as e:
            logger.warning("Local SentenceTransformer could not be loaded: %s", e)
            return None


_get_model = _get_local_model


def _embed_gemini_single(text: str, is_query: bool = False) -> list:
    """Call Gemini Embedding API for single text with retry on 429."""
    import time
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": _EMBED_DIM,
        "taskType": "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    }
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(1, 5):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("embedding", {}).get("values", [])
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(2 * attempt)
                continue
            raise
        except Exception:
            if attempt < 4:
                time.sleep(1.5 * attempt)
                continue
            raise


def _embed_gemini_batch(texts: list) -> list:
    """Call Gemini Embedding API for batch of texts with retry on 429."""
    import time
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")
    
    all_embeddings = []
    chunk_size = 25
    for i in range(0, len(texts), chunk_size):
        batch = texts[i:i + chunk_size]
        requests = [{
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": t}]},
            "outputDimensionality": _EMBED_DIM,
            "taskType": "RETRIEVAL_DOCUMENT"
        } for t in batch]
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={settings.GEMINI_API_KEY}"
        data = json.dumps({"requests": requests}).encode("utf-8")
        
        batch_embs = None
        for attempt in range(1, 5):
            try:
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    embs = res.get("embeddings", [])
                    batch_embs = [e.get("values", []) for e in embs]
                    break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 4:
                    logger.warning("Gemini embedding 429 rate limit, sleeping %ds (attempt %d/4)...", 2 * attempt, attempt)
                    time.sleep(2 * attempt)
                    continue
                raise
            except Exception:
                if attempt < 4:
                    time.sleep(2 * attempt)
                    continue
                raise
                
        if batch_embs:
            all_embeddings.extend(batch_embs)
        time.sleep(0.5)
                
    return all_embeddings


# ── Query embedding cache ────────────────────────────────────────────────────
_query_embed_cache: dict = {}
_QUERY_EMBED_CACHE_MAX = 256


def embed_text(text: str, is_query: bool = False) -> list:
    """Embed text thành vector 768-dim. Ưu tiên multilingual-e5-base đồng bộ với 71.000+ chunks trong DB."""
    model = _get_local_model()
    if model is not None:
        try:
            prefix = QUERY_PREFIX if is_query else DOC_PREFIX
            vec = model.encode(
                prefix + text,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return vec.tolist() if isinstance(vec, np.ndarray) else list(vec)
        except Exception as e:
            logger.warning("Local multilingual-e5 embedding failed: %s, trying Gemini fallback", e)

    # Fallback to Gemini if local model fails
    if settings.GEMINI_API_KEY:
        try:
            return _embed_gemini_single(text, is_query=is_query)
        except Exception as e:
            logger.warning("Gemini embedding API failed: %s", e)

    raise RuntimeError("No embedding provider available (both local model and Gemini API failed)")


def embed_and_store(chunks: list, db) -> None:
    """Embed danh sách chunks rồi bulk insert vào DB. Ưu tiên multilingual-e5-base."""
    from app.models.document import Chunk
    import uuid

    if not chunks:
        return

    texts = [c["content"] for c in chunks]
    vectors = None

    model = _get_local_model()
    if model is not None:
        prefixed = [DOC_PREFIX + t for t in texts]
        try:
            vectors = model.encode(
                prefixed,
                batch_size=32,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        except Exception as e:
            logger.exception("Local batch embed failed: %s, trying Gemini fallback", e)

    if vectors is None and settings.GEMINI_API_KEY:
        try:
            vectors = _embed_gemini_batch(texts)
        except Exception as e:
            logger.warning("Gemini batch embed failed: %s", e)

    if vectors is None:
        logger.error("No embedding model available to store chunks.")
        return

    objects = []
    for i, (c, vec) in enumerate(zip(chunks, vectors)):
        objects.append(Chunk(
            id=uuid.uuid4(),
            document_id=c["document_id"],
            content=c["content"],
            embedding=vec.tolist() if isinstance(vec, np.ndarray) else list(vec),
            page_number=c.get("page_number", 1),
            chunk_index=c.get("chunk_index", i),
        ))
    if objects:
        db.bulk_save_objects(objects)
        db.commit()


def embed_query(query: str) -> list:
    """Embed query without caching."""
    return embed_text(query, is_query=True)


def embed_query_cached(query: str) -> list:
    """Embed query with MD5 cache."""
    key = hashlib.md5(query.encode("utf-8")).hexdigest()
    if key in _query_embed_cache:
        return _query_embed_cache[key]
    vec = embed_text(query, is_query=True)
    if len(_query_embed_cache) >= _QUERY_EMBED_CACHE_MAX:
        for k in list(_query_embed_cache.keys())[: _QUERY_EMBED_CACHE_MAX // 4]:
            _query_embed_cache.pop(k, None)
    _query_embed_cache[key] = vec
    return vec
