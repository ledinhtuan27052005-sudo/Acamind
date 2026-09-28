"""
Reranker — module tách riêng để rerank các chunk candidate sau khi RRF fusion.

Có 2 backend:
  1. **FlagReranker** (mặc định) — dùng model `BAAI/bge-reranker-v2-m3` từ
     thư viện `sentence-transformers` chạy local (CPU OK, GPU nhanh hơn).
     Model ~2.2GB, tự download lần đầu vào cache HuggingFace.

  2. **LLM rerank** (fallback) — gọi LLM (Gemini qua llm_client) chấm điểm
     từng cặp (query, chunk) theo thang 0–10. Dùng khi không cài
     sentence-transformers / model lỗi.

Việc rerank thường tăng context_precision từ ~60% lên ~85%+ vì
cross-encoder "đọc" cả query + chunk cùng lúc thay vì so sánh cosine
naive giữa 2 vector.
"""
from __future__ import annotations

import hashlib
import logging
import os
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# ── Module-level cache cho reranker instance (heavyweight) ────────────────
_reranker_instance: Optional["FlagRerankerWrapper"] = None
_reranker_lock = threading.Lock()

# ── Cache kết quả rerank theo hash(query + chunk_ids) ────────────────────
_rerank_cache: dict[str, list[dict]] = {}
_RERANK_CACHE_MAX = 256


def _cache_key(query: str, chunk_ids: list[str]) -> str:
    h = hashlib.md5()
    h.update(query.encode("utf-8"))
    for cid in chunk_ids:
        h.update(b"|")
        h.update(cid.encode("utf-8"))
    return h.hexdigest()


def _llm_rerank(query: str, chunks: list[dict], top_n: int) -> list[dict]:
    """Fallback: dùng LLM chấm điểm từng chunk theo thang 0–10.

    Prompt yêu cầu LLM trả về JSON array các index theo thứ tự liên quan giảm dần.
    Chậm hơn FlagReranker nhưng đỡ tốn disk/model.
    """
    from app.services.llm_client import get_default_client

    if not chunks:
        return []

    # Giới hạn 20 chunk để LLM không quá tải
    candidates = chunks[:20]

    items_text = ""
    for i, c in enumerate(candidates):
        snippet = c.get("content", "")[:500]
        items_text += f"\n[{i}] {snippet}\n"

    prompt = (
        f"Bạn là hệ thống rerank. Cho câu hỏi: \"{query}\"\n\n"
        f"Các đoạn văn bản ứng viên (đã có index):{items_text}\n\n"
        "Hãy trả về JSON array chứa index của TỐI ĐA "
        f"{top_n} đoạn LIÊN QUAN NHẤT với câu hỏi, theo thứ tự liên quan giảm dần.\n"
        'Ví dụ: [3, 0, 7, 1]\n'
        "Chỉ trả về JSON array, không giải thích."
    )

    try:
        client = get_default_client()
        raw = client.complete(
            messages=[{"role": "user", "content": prompt}],
            system="Bạn là reranker chính xác. Chỉ trả về JSON array các index.",
            max_tokens=200,
            temperature=0.0,
        )
        # Parse JSON array
        import json, re
        match = re.search(r"\[[\d,\s]+\]", raw)
        if match:
            indices = json.loads(match.group(0))
            out = []
            for idx in indices:
                if isinstance(idx, int) and 0 <= idx < len(candidates):
                    out.append(candidates[idx])
            if out:
                return out[:top_n]
    except Exception as e:
        logger.warning("LLM rerank thất bại: %s", e)

    # Nếu LLM fail → trả về nguyên thứ tự
    return candidates[:top_n]


class FlagRerankerWrapper:
    """Wrapper cho FlagReranker từ sentence-transformers.

    Lazy load: model chỉ tải về khi rerank() được gọi lần đầu.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model_name = model_name
        self._model = None
        self._load_lock = threading.Lock()

    def _load(self):
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return
            try:
                from FlagEmbedding import FlagReranker  # type: ignore
                logger.info("Loading FlagReranker: %s", self.model_name)
                self._model = FlagReranker(self.model_name, use_fp16=False)
            except ImportError:
                # Fallback sang sentence_transformers CrossEncoder
                from sentence_transformers import CrossEncoder  # type: ignore
                logger.info("Loading CrossEncoder: %s", self.model_name)
                self._model = CrossEncoder(self.model_name)

    def score(self, query: str, chunks: list[dict]) -> list[float]:
        """Trả về list điểm rerank tương ứng từng chunk (cao = liên quan hơn)."""
        if not chunks:
            return []
        self._load()
        pairs = [(query, c.get("content", "")) for c in chunks]
        try:
            if hasattr(self._model, "compute_score"):
                # FlagReranker: compute_score nhận list of pairs, trả về list float
                scores = self._model.compute_score(pairs, normalize=True)
            else:
                # CrossEncoder
                raw = self._model.predict(pairs)
                # Convert numpy → python list
                try:
                    scores = [float(x) for x in raw]
                except TypeError:
                    scores = [float(raw)]
            return scores
        except Exception as e:
            logger.warning("Reranker score() lỗi: %s", e)
            return [0.0] * len(chunks)


def get_reranker() -> FlagRerankerWrapper:
    """Lấy singleton FlagReranker (heavyweight)."""
    global _reranker_instance
    if _reranker_instance is None:
        with _reranker_lock:
            if _reranker_instance is None:
                _reranker_instance = FlagRerankerWrapper()
    return _reranker_instance


def _env_use_llm_rerank() -> bool:
    """Cho phép tắt FlagReranker bằng env var (vd khi model chưa tải về).

    RERANK_BACKEND=llm  → dùng LLM rerank
    RERANK_BACKEND=flag (mặc định) → dùng FlagReranker
    """
    return os.getenv("RERANK_BACKEND", "flag").lower() == "llm"


def rerank(query: str, chunks: list[dict], top_n: int = 8) -> list[dict]:
    """Rerank danh sách chunks, trả về top_n chunks theo thứ tự liên quan giảm dần.

    Args:
        query: Câu hỏi gốc.
        chunks: List chunks từ RRF fusion (đã có content/page_number/...).
        top_n: Số chunks trả về.

    Returns:
        List chunks đã rerank (giữ nguyên schema đầu vào + thêm `rerank_score`).
    """
    if not chunks:
        return []
    if len(chunks) <= top_n:
        # Không cần rerank nếu ít hơn top_n
        for c in chunks:
            c["rerank_score"] = 0.0
        return chunks

    chunk_ids = [str(c.get("id") or c.get("chunk_id") or i) for i, c in enumerate(chunks)]
    ck = _cache_key(query, chunk_ids)
    if ck in _rerank_cache:
        return _rerank_cache[ck][:top_n]

    if _env_use_llm_rerank():
        ranked = _llm_rerank(query, chunks, top_n)
    else:
        try:
            reranker = get_reranker()
            scores = reranker.score(query, chunks)
            # Sort chunks theo score giảm dần
            indexed = sorted(
                zip(chunks, scores),
                key=lambda x: x[1] if x[1] is not None else 0.0,
                reverse=True,
            )
            ranked = []
            for c, s in indexed[:top_n]:
                c2 = dict(c)
                c2["rerank_score"] = float(s) if s is not None else 0.0
                ranked.append(c2)
        except Exception as e:
            logger.warning("FlagReranker lỗi → fallback LLM rerank: %s", e)
            ranked = _llm_rerank(query, chunks, top_n)

    # Cache (LRU đơn giản)
    if len(_rerank_cache) >= _RERANK_CACHE_MAX:
        # Xóa 1/4 cache cũ
        for k in list(_rerank_cache.keys())[: _RERANK_CACHE_MAX // 4]:
            _rerank_cache.pop(k, None)
    _rerank_cache[ck] = ranked
    return ranked
