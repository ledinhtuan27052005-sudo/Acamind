import hashlib
import logging
import threading
import numpy as np

logger = logging.getLogger(__name__)

# ── Embedding model: sentence-transformers (local) ───────────────────────────
# Dùng intfloat/multilingual-e5-base — 768-dim, multilingual (tốt cho tiếng Việt),
# đã cài sẵn qua sentence-transformers. Match với schema VECTOR(768) trong DB.
# Lý do đổi từ Ollama sang local model:
# - Không cần cài Ollama + pull model (tiết kiệm disk, RAM, thời gian)
# - Mọi AI dùng 1 chỗ duy nhất (Gemini cho LLM, local model cho embedding) → đơn giản
# - Ổn định, không phụ thuộc service ngoài
_EMBED_MODEL_NAME = "intfloat/multilingual-e5-base"
_EMBED_DIM = 768 # output dim của multilingual-e5-base, khớp VECTOR(768) trong schema

# E5 yêu cầu prefix theo task:
# - "query: " cho câu hỏi
# - "passage: " cho đoạn văn lưu DB
# Thiếu prefix → retrieval chất lượng giảm rõ rệt (theo paper E5).
DOC_PREFIX = "passage: "
QUERY_PREFIX = "query: "

# ── Lazy model loader (thread-safe singleton) ────────────────────────────────
_model_lock = threading.Lock()
_model = None


def _get_model():
 """Lazy load + cache sentence-transformers model. Thread-safe."""
 global _model
 if _model is not None:
  return _model
 with _model_lock:
  if _model is not None: # double-check
   return _model
  logger.info("Loading embedding model: %s (lần đầu ~10-30s)...", _EMBED_MODEL_NAME)
  from sentence_transformers import SentenceTransformer
  _model = SentenceTransformer(_EMBED_MODEL_NAME)
  dim = _model.get_sentence_embedding_dimension()
  logger.info("Embedding model loaded OK (dim=%d)", dim)
  return _model


# ── Query embedding cache ────────────────────────────────────────────────────
# Cache theo md5(query). User thường hỏi lặp lại câu tương tự → tránh embed trùng.
# LRU đơn giản: khi đầy cache, xóa 1/4 entries cũ nhất.
_query_embed_cache: dict = {}
_QUERY_EMBED_CACHE_MAX = 256


def embed_text(text: str, is_query: bool = False) -> list:
 """Embed text thành vector 768-dim. Dùng sentence-transformers local.

 Tự thêm prefix theo task cho E5.
 """
 prefix = QUERY_PREFIX if is_query else DOC_PREFIX
 model = _get_model()
 vec = model.encode(
  prefix + text,
  normalize_embeddings=True, # cosine-friendly (L2 norm = 1)
  show_progress_bar=False,
  convert_to_numpy=True,
 )
 # Trả về list[float] để tương thích với code cũ + lưu DB (pgvector nhận list).
 return vec.tolist() if isinstance(vec, np.ndarray) else list(vec)


def embed_and_store(chunks: list, db) -> None:
 """Embed danh sách chunks (lưu document → dùng prefix passage)
 rồi bulk insert vào DB. Không raise nếu 1 chunk fail — best-effort.

 Optimize: encode theo batch (nhanh hơn 5-10× so với encode từng cái).
 """
 from app.models.document import Chunk
 import uuid

 if not chunks:
  return

 model = _get_model()
 texts = [DOC_PREFIX + c["content"] for c in chunks]

 # Batch encode — sentence-transformers tự tối ưu batching.
 try:
  vectors = model.encode(
   texts,
   batch_size=32,
   normalize_embeddings=True,
   show_progress_bar=False,
   convert_to_numpy=True,
  )
 except Exception as e:
  logger.exception("Batch embed failed: %s", e)
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
 """Embed câu hỏi / query (dùng prefix query). Không cache."""
 return embed_text(query, is_query=True)


def embed_query_cached(query: str) -> list:
 """Embed câu hỏi với cache theo md5(query)."""
 key = hashlib.md5(query.encode("utf-8")).hexdigest()
 if key in _query_embed_cache:
  return _query_embed_cache[key]
 vec = embed_text(query, is_query=True)
 if len(_query_embed_cache) >= _QUERY_EMBED_CACHE_MAX:
  for k in list(_query_embed_cache.keys())[: _QUERY_EMBED_CACHE_MAX // 4]:
   _query_embed_cache.pop(k, None)
 _query_embed_cache[key] = vec
 return vec
