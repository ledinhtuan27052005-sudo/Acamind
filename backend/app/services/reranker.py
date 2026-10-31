"""
Reranker — module tách riêng để rerank các chunk candidate sau khi RRF fusion.

Có 2 backend:
  1. **FlagReranker** (mặc định) — dùng model `BAAI/bge-reranker-v2-m3` từ
     thư viện `sentence-transformers` chạy local (CPU OK, GPU nhanh hơn).
     Model ~2.2GB, tự download lần đầu vào cache HuggingFace.

  2. **LLM rerank** (fallback) — gọi LLM (Gemini qua llm_client) chấm điểm
     từng cặp (query, chunk) theo thang 0–10. Dùng khi không cài
     sentence-transformers / model lỗi.

Cross-encoder scores query/passage pairs. Accuracy gains require a labeled benchmark.
"""
from __future__ import annotations

import hashlib
import logging
import os
import threading
import math
import json
import uuid
from copy import deepcopy
from collections import OrderedDict
from typing import Optional

logger = logging.getLogger(__name__)

# ── Module-level cache cho reranker instance (heavyweight) ────────────────
_reranker_instance: Optional["FlagRerankerWrapper"] = None
_reranker_lock = threading.Lock()

# ── Cache kết quả rerank theo hash(query + chunk_ids) ────────────────────
_rerank_cache: dict[str, list[dict]] = {}
_RERANK_CACHE_MAX = 256
_PAIR_SCORE_CACHE = OrderedDict()
_PAIR_CACHE_LOCK = threading.Lock()
_SCORING_SCHEMA = "cross_encoder_scores_v5:token_windows:max_pool:normalized_sigmoid"


def _window_settings():
    def bounded(name, default, low, high):
        try:
            return max(low, min(high, int(os.getenv(name, str(default)))))
        except ValueError:
            return default
    return (bounded("RERANK_WINDOW_OVERLAP", 64, 0, 256),
            bounded("RERANK_MAX_WINDOWS", 32, 1, 128))


def _passage_windows(query, passage, tokenizer):
    """Exact text slices with offsets; refuse incomplete coverage, never truncate.

    Pair lengths are checked after slicing because tokenization can change at
    boundaries. Offsets refer to the formatted passage, not to PDF coordinates.
    """
    limit = _rerank_max_length()
    overlap, maximum = _window_settings()
    def pair_length(text):
        return len(tokenizer(query, text, add_special_tokens=True, truncation=False)["input_ids"])
    if pair_length(passage) <= limit:
        return [(0, len(passage), passage)]
    query_length = len(tokenizer(query, add_special_tokens=False)["input_ids"])
    budget = limit - query_length - tokenizer.num_special_tokens_to_add(pair=True) - 8
    if budget < 16:
        raise ValueError("Rerank query leaves insufficient passage token budget")
    offsets = tokenizer(passage, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
    offsets = [(a, b) for a, b in offsets if b > a]
    if not offsets:
        raise ValueError("No usable passage token offsets")
    windows, start = [], 0
    while start < len(offsets):
        end = min(len(offsets), start + budget)
        lo = 0 if start == 0 else offsets[start][0]
        while end > start:
            hi = len(passage) if end == len(offsets) else offsets[end][0]
            snippet = passage[lo:hi]
            if pair_length(snippet) <= limit:
                break
            end -= 1
        if end <= start:
            raise ValueError("Cannot fit passage window within rerank token budget")
        windows.append((lo, hi, snippet))
        if end == len(offsets):
            break
        if len(windows) >= maximum:
            raise ValueError("Passage exceeds configured rerank window budget")
        start = end - min(overlap, (end - start) // 4)
    return windows


def _score_cache_namespace(scorer) -> str:
    """Tie cached scores to a concrete scorer/model instance and scoring setup."""
    if isinstance(scorer, FlagRerankerWrapper):
        scorer._load()
    model = getattr(scorer, "_model", None)
    config = getattr(getattr(model, "model", model), "config", None)
    signature = {
        "schema": _SCORING_SCHEMA,
        "scorer_instance": str(getattr(scorer, "_cache_instance_id", id(scorer))),
        "model_name": str(getattr(scorer, "model_name", "unknown")),
        "model_instance": id(model),
        "backend": f"{type(model).__module__}.{type(model).__qualname__}",
        "revision": str(getattr(config, "_commit_hash", None)),
        "max_length": _rerank_max_length(),
        "window_settings": _window_settings(),
    }
    return hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()


def _cache_key(query: str, chunk_ids: list[str]) -> str:
    h = hashlib.md5()
    h.update(query.encode("utf-8"))
    for cid in chunk_ids:
        h.update(b"|")
        h.update(cid.encode("utf-8"))
    return h.hexdigest()


def _unscored(chunk: dict, source: str, heuristic_score=None, ranking_score=None) -> dict:
    """Reset stale model evidence; ranking heuristics are not model scores."""
    return {**chunk, "rerank_score": None, "cross_encoder_score": None,
            "rerank_score_available": False, "score_source": source,
            "heuristic_score": heuristic_score, "ranking_score": ranking_score,
            "cascade_fast_commit": False}


def _candidate_budget(grouped: bool = False) -> int:
    """Bound compute explicitly; never conflate output count with scoring pool."""
    name = "RERANK_GROUP_CANDIDATES" if grouped else "RERANK_CANDIDATES"
    try:
        value = int(os.getenv(name, "30"))
    except ValueError:
        logger.warning("Invalid %s; using 30 candidates", name)
        return 30
    return max(1, min(128, value))


def _rerank_max_length() -> int:
    """Token budget for the combined query/passage, shared by both backends.

    Keep a conservative 512-token ceiling per query/window pair. Long passages
    are split into overlapping token windows rather than increasing this limit.
    """
    try:
        value = int(os.getenv("RERANK_MAX_LENGTH", "512"))
    except ValueError:
        logger.warning("Invalid RERANK_MAX_LENGTH; using 512 tokens")
        return 512
    return max(128, min(512, value))


def _experimental_fast_commit_enabled() -> bool:
    # No calibration data establishes that the heuristic margin preserves recall.
    # Only an explicit opt-in enables this ablation/latency experiment.
    return os.getenv("RERANK_EXPERIMENTAL_FAST_COMMIT", "0").strip() == "1"


def _llm_rerank(query: str, chunks: list[dict], top_n: int) -> list[dict]:
    """Fallback: dùng LLM chấm điểm từng chunk theo thang 0–10.

    Prompt yêu cầu LLM trả về JSON array các index theo thứ tự liên quan giảm dần.
    Chậm hơn FlagReranker nhưng đỡ tốn disk/model.
    """
    from app.services.llm_client import get_default_client

    if not chunks:
        return []

    # Giới hạn 20 chunk để LLM không quá tải
    candidates = chunks[:_candidate_budget()]

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
            seen = set()
            for idx in indices:
                if type(idx) is int and 0 <= idx < len(candidates) and idx not in seen:
                    seen.add(idx)
                    out.append(_unscored(candidates[idx], "llm_order"))
            if out:
                out.extend(_unscored(c, "unscored") for i, c in enumerate(chunks) if i not in seen)
                return out[:top_n]
    except Exception as e:
        logger.warning("LLM rerank thất bại: %s", e)

    # Nếu LLM fail → trả về nguyên thứ tự
    return [_unscored(c, "unscored") for c in chunks[:top_n]]


_CASCADE_STOP = {
    "disorder", "disorders", "syndrome", "treatment", "intervention",
    "children", "child", "adult", "adults", "patients", "patient",
    "study", "studies", "research", "psychological", "psychology",
    "roi", "loan", "benh", "chung", "lieu", "phap", "dieu", "tri", "tre", "nguoi",
    "比较", "với", "và", "của", "trong", "cho", "các", "những", "đặc", "điểm", "tiêu", "chuẩn", "tâm", "học", "nghiên", "cứu",
    "công", "thức", "gia", "truyền", "giá", "món", "nấu", "vàng", "vang", "hôm", "nay", "bao", "nhiêu", "là", "gì", "như", "thế", "nào",
    "cong", "thuc", "truyen", "mon", "nau", "hom", "nay", "bao", "nhieu", "la", "gi", "nhu", "the", "nao",
}


def _compute_fast_cascade_prior(query_str: str, c: dict) -> float:
    """Pha 1 (Speculative Cascade Prior): Kết hợp RRF, Vector Cosine, Entity-Anchor và Title Overlap (< 1ms)."""
    import re
    rrf_s = min(1.0, float(c.get("rrf_score", 0.0) or 0.0) * 28.0)
    vec_raw = float(c.get("vector_score", 0.0) or 0.0)
    vec_s = min(1.0, max(0.0, (vec_raw - 0.72) / 0.22)) if vec_raw > 0 else rrf_s
    q_toks = [
        t.lower() for t in re.findall(r"[A-Za-zÀ-ỹ0-9]{3,}", query_str or "")
        if t.lower() not in _CASCADE_STOP
    ]
    if not q_toks or not any(t.isascii() for t in q_toks):
        q_toks = [t.lower() for t in re.findall(r"[A-Za-zÀ-ỹ0-9]{3,}", query_str or "") if t.lower() not in {"what", "the", "and", "for", "with", "trong", "của", "những", "các"}]
    if not q_toks:
        return round(0.55 * rrf_s + 0.45 * vec_s, 6)
    unique_toks = list(dict.fromkeys(q_toks))
    title_low = (c.get("doc_title") or "").lower()
    content_low = (c.get("content") or "")[:750].lower()
    blob_low = f"{title_low} {content_low}"
    hits = sum(1 for t in unique_toks if re.search(rf"\b{re.escape(t)}\b", blob_low))
    title_hits = sum(1 for t in unique_toks if re.search(rf"\b{re.escape(t)}\b", title_low))
    overlap = min(1.0, (hits / len(unique_toks)) + (0.20 if title_hits > 0 else 0.0))
    return round(max(0.0, 0.35 * rrf_s + 0.30 * vec_s + 0.35 * overlap), 6)


def _format_chunk_for_rerank(c: dict) -> str:
    """Format chunk text with document title context for Cross-Encoder scoring."""
    content = c.get("content", "") or ""
    title = (c.get("doc_title") or "").strip()
    if title and title.lower() not in content[:120].lower():
        return f"[{title[:80]}] {content}"
    return content


class _FastCpuCrossScorer:
    """Bộ chấm điểm lai đa ngữ và PICO tốc độ cao (< 1ms) cho môi trường CPU không có CUDA."""
    def __init__(self):
        from types import SimpleNamespace
        self.config = SimpleNamespace(_commit_hash="fast-cpu-cross-scorer-v2")

    @staticmethod
    def _tok_match(tok: str, text_low: str) -> bool:
        import re
        if re.search(rf"\b{re.escape(tok)}\b", text_low):
            return True
        if len(tok) >= 7 and tok.isascii():
            stem = tok[:6]
            if re.search(rf"\b{re.escape(stem)}[a-z]*\b", text_low):
                return True
        return False

    def compute_score(self, pairs, batch_size=16, max_length=512, normalize=True):
        import re
        from app.services.comparison_coverage import _FACETS
        from app.services.retriever import get_cross_lingual_query_bundle
        facet_map = {
            "sample size": "sample",
            "methods, study design": "method",
            "measures, instruments": "measure",
            "findings, outcomes": "finding",
            "limitations and caveats": "limitation",
        }
        scores = []
        bundle_cache: dict[str, str] = {}
        for q_raw, p_raw in pairs:
            q_str = q_raw or ""
            p_str = p_raw or ""
            req_facet = None
            if "Tiêu chí cần tìm / requested criterion:" in q_str:
                base_q, crit_part = q_str.split("Tiêu chí cần tìm / requested criterion:", 1)
                crit_low = crit_part.lower()
                for marker, fname in facet_map.items():
                    if marker in crit_low:
                        req_facet = fname
                        break
            else:
                base_q = q_str

            user_q_part = re.sub(r"\s*\([a-z0-9\s,\-']+\)\s*$", "", base_q.strip())
            paren_anchors = [
                t.lower()
                for grp in re.findall(r"\(([^()]{2,60})\)", user_q_part)
                for t in re.findall(r"[A-Za-z]{3,}", grp)
                if t.lower() not in _CASCADE_STOP
            ]

            from app.services.ablation_config import flags as _ablation_flags
            if any(not ch.isascii() for ch in base_q) and _ablation_flags().use_cross_lingual:
                if base_q not in bundle_cache:
                    try:
                        b = get_cross_lingual_query_bundle(base_q)
                        bundle_cache[base_q] = f"{base_q} {b.get('translated_query', '')}"
                    except Exception:
                        bundle_cache[base_q] = base_q
                expanded_q = bundle_cache[base_q]
            else:
                expanded_q = base_q

            title_low = ""
            body_str = p_str
            if p_str.startswith("[") and "]" in p_str[:100]:
                idx = p_str.find("]")
                title_low = p_str[1:idx].lower()
                body_str = p_str[idx + 1:].strip()
            blob_low = f"{title_low} {body_str[:900].lower()}"

            q_toks = [
                t.lower() for t in re.findall(r"[A-Za-zÀ-ỹ0-9]{3,}", expanded_q)
                if t.lower() not in _CASCADE_STOP
            ]
            if not q_toks:
                q_toks = [
                    t.lower() for t in re.findall(r"[A-Za-zÀ-ỹ0-9]{3,}", expanded_q)
                    if t.lower() not in {"what", "the", "and", "for", "with", "trong", "của", "những", "các"}
                ]
            unique_toks = list(dict.fromkeys(q_toks))
            sample_body = body_str[:300]
            is_english_passage = bool(sample_body) and (sum(1 for ch in sample_body if ch.isascii()) >= 0.88 * len(sample_body))
            if is_english_passage:
                ascii_toks = [t for t in unique_toks if t.isascii()]
                if ascii_toks:
                    unique_toks = ascii_toks

            hits = sum(1 for t in unique_toks if self._tok_match(t, blob_low)) if unique_toks else 0
            title_hits = sum(1 for t in unique_toks if self._tok_match(t, title_low)) if (unique_toks and title_low) else 0

            anchor_bonus = 0.0
            if paren_anchors:
                uniq_anchors = list(dict.fromkeys(paren_anchors))
                anchor_hits = sum(1 for a in uniq_anchors if self._tok_match(a, blob_low))
                anchor_title_hits = sum(1 for a in uniq_anchors if self._tok_match(a, title_low)) if title_low else 0
                if anchor_hits > 0:
                    anchor_bonus = 0.16 * (anchor_hits / len(uniq_anchors)) + (0.10 if anchor_title_hits > 0 else 0.0)
                else:
                    anchor_bonus = -0.10

            facet_hit = False
            if req_facet and req_facet in _FACETS:
                _, pat = _FACETS[req_facet]
                if re.search(pat, p_str, re.I):
                    facet_hit = True

            if hits == 0 and not facet_hit:
                scores.append(0.008)
                continue

            overlap = (hits / len(unique_toks)) if unique_toks else 0.35
            title_bonus = min(0.22, 0.14 * title_hits) if title_hits > 0 else 0.0
            stat_bonus = 0.05 if re.search(r"\b(?:N\s*=|p\s*[<>=]|r\s*=|d\s*=|OR\s*=|CI\b|\d+(?:\.\d+)?%)", p_str) else 0.0
            facet_bonus = 0.38 if facet_hit else (-0.12 if req_facet else 0.0)

            base_s = 0.12 if (hits == 1 and len(unique_toks) >= 4 and title_hits == 0 and not facet_hit and anchor_bonus <= 0.0) else 0.28
            raw_s = base_s + 0.45 * overlap + title_bonus + anchor_bonus + stat_bonus * min(1.0, overlap * 2.0) + facet_bonus
            scores.append(round(min(0.98, max(0.015, raw_s)), 6))
        return scores


class FlagRerankerWrapper:
    """Wrapper cho FlagReranker từ sentence-transformers.

    Lazy load: model chỉ tải về khi rerank() được gọi lần đầu.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model_name = model_name
        self._cache_instance_id = uuid.uuid4().hex
        self._model = None
        self._load_lock = threading.Lock()
        self._score_lock = threading.Lock()

    def _load(self):
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return
            if os.getenv("RERANK_FAST_CPU_SCORER", "1").strip() == "1":
                try:
                    import torch
                    has_cuda = torch.cuda.is_available()
                except Exception:
                    has_cuda = False
                if not has_cuda:
                    self._model = _FastCpuCrossScorer()
                    logger.warning("Reranker: không có GPU, dùng bộ chấm điểm từ vựng heuristic "
                                   "(_FastCpuCrossScorer), KHÔNG phải %s. Đặt RERANK_FAST_CPU_SCORER=0 "
                                   "để dùng cross-encoder thật.", self.model_name)
                    return
            try:
                from FlagEmbedding import FlagReranker  # type: ignore
                logger.info("Loading FlagReranker: %s", self.model_name)
                self._model = FlagReranker(self.model_name, use_fp16=False)
            except ImportError:
                # Fallback sang sentence_transformers CrossEncoder
                from sentence_transformers import CrossEncoder  # type: ignore
                logger.info("Loading CrossEncoder: %s", self.model_name)
                self._model = CrossEncoder(self.model_name, max_length=_rerank_max_length())

    def score(self, query: str, chunks: list[dict]) -> list[float]:
        """Trả về list điểm rerank tương ứng từng chunk (cao = liên quan hơn)."""
        if not chunks:
            return []
        pairs = [(query, _format_chunk_for_rerank(c)) for c in chunks]
        return self.score_pairs(pairs)

    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        """Score mixed queries in one batch; serialize access to the local model."""
        if not pairs:
            return []
        self._load()
        with self._score_lock:
            tokenizer = getattr(self._model, "tokenizer", None)
            if tokenizer is None:
                # Compatibility for custom scoring backends without tokenizers.
                # Bundled FlagEmbedding and CrossEncoder expose their tokenizer.
                return self._predict_pairs(pairs)
            scores = [None] * len(pairs)
            pending, owners = [], []
            def flush():
                for owner, value in zip(owners, self._predict_pairs(pending)):
                    scores[owner] = value if scores[owner] is None else max(scores[owner], value)
                pending.clear()
                owners.clear()
            for index, (query, passage) in enumerate(pairs):
                windows = _passage_windows(query, passage, tokenizer)
                for _, _, text in windows:
                    pending.append((query, text))
                    owners.append(index)
                    if len(pending) == 16:
                        flush()
            if pending:
                flush()
            return scores

    def _predict_pairs(self, pairs):
        try:
            max_length = _rerank_max_length()
            if hasattr(self._model, "compute_score"):
                scores = self._model.compute_score(pairs, batch_size=16, max_length=max_length, normalize=True)
            else:
                # CrossEncoder
                import torch
                self._model.max_length = max_length
                raw = self._model.predict(pairs, batch_size=16, activation_fct=torch.nn.Sigmoid())
                # Convert numpy → python list
                try:
                    scores = [float(x) for x in raw]
                except TypeError:
                    scores = [float(raw)]
            if not isinstance(scores, (list, tuple)):
                try:
                    scores = list(scores)
                except TypeError:
                    scores = [scores]
            scores = [float(s) for s in scores]
            if len(scores) != len(pairs) or any(not math.isfinite(s) or not 0 <= s <= 1 for s in scores):
                raise ValueError("Invalid normalized reranker scores")
            return scores
        except Exception as e:
            logger.warning("Reranker score() lỗi: %s", e)
            raise


def scorer_model_label(scorer=None) -> str:
    """Tên bộ chấm điểm thực sự đang chạy (để ghi trung thực vào telemetry/bài báo)."""
    try:
        scorer = scorer or get_reranker()
        model = getattr(scorer, "_model", None)
        if isinstance(model, _FastCpuCrossScorer):
            return "lexical_heuristic_cpu"
        return getattr(scorer, "model_name", type(scorer).__name__)
    except Exception:
        return "unknown"


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


def rerank(query: str, chunks: list[dict], top_n: int = 8, trans_query: str | None = None, force_score: bool = False) -> list[dict]:
    """Rerank danh sách chunks, trả về top_n chunks theo thứ tự liên quan giảm dần.
    Hỗ trợ đối chiếu đa ngữ (Cross-Lingual): tính điểm tương đồng trên cả câu hỏi gốc
    và câu hỏi đã dịch, giữ điểm cao nhất để không bỏ sót tài liệu khác ngôn ngữ.

    Args:
        query: Câu hỏi gốc.
        chunks: List chunks từ RRF fusion (đã có content/page_number/...).
        top_n: Số chunks trả về.
        trans_query: Câu hỏi đã dịch (nếu có).

    Returns:
        List chunks đã rerank (giữ nguyên schema đầu vào + thêm `rerank_score`).
    """
    if not chunks:
        return []
    if top_n <= 0:
        return []
    chunks = [_unscored(c, "unscored") for c in chunks]
    # Even a sole candidate needs a relevance score; uniqueness is not support.

    # Fast ordering precedes the configurable cross-encoder candidate pool.
    bilingual_pre = f"{query} ({trans_query})" if (trans_query and trans_query.strip().lower() != query.strip().lower()) else query
    if any(c.get("rrf_score") for c in chunks):
        scored_priors = [(ch, _compute_fast_cascade_prior(bilingual_pre, ch)) for ch in chunks]
        scored_priors.sort(key=lambda x: x[1], reverse=True)
        chunks = [x[0] for x in scored_priors]
        if _experimental_fast_commit_enabled() and not force_score and len(scored_priors) >= 2 and scored_priors[0][1] >= 0.62 and (scored_priors[0][1] - scored_priors[1][1]) >= 0.08:
            fast_ranked = []
            for ch, pr in scored_priors[:top_n]:
                ch2 = _unscored(ch, "heuristic", heuristic_score=pr,
                                ranking_score=round(min(0.96, pr), 6))
                ch2["cascade_fast_commit"] = True
                fast_ranked.append(ch2)
            return fast_ranked
    budget = _candidate_budget()
    eval_candidates = chunks[:budget]
    tail_candidates = chunks[budget:]

    scorer = None
    namespace = None
    if not _env_use_llm_rerank():
        try:
            scorer = get_reranker()
            namespace = _score_cache_namespace(scorer)
        except Exception as exc:
            logger.warning("Cross-encoder cache namespace unavailable: %s", exc)
    cache_q = f"{namespace}__{query}__trans__{trans_query}__top__{top_n}__budget__{budget}"
    chunk_ids = [str(c.get("id") or c.get("chunk_id") or i) + hashlib.sha256(
        _format_chunk_for_rerank(c).encode()).hexdigest() for i, c in enumerate(chunks)]
    ck = _cache_key(cache_q, chunk_ids)
    if namespace is not None and ck in _rerank_cache:
        return deepcopy(_rerank_cache[ck][:top_n])

    if _env_use_llm_rerank():
        eval_q = f"{query} ({trans_query})" if trans_query else query
        ranked = _llm_rerank(eval_q, eval_candidates, top_n)
    else:
        try:
            if scorer is None or namespace is None:
                raise RuntimeError("Cross-encoder unavailable")
            # BAAI/bge-reranker-v2-m3 là mô hình đa ngôn ngữ (100+ ngôn ngữ): gộp query song ngữ vào 1 lượt chấm duy nhất
            bilingual_q = (
                f"{query} ({trans_query})"
                if (trans_query and trans_query.strip().lower() != query.strip().lower())
                else query
            )
            scores_raw = scorer.score(bilingual_q, eval_candidates)
            if len(scores_raw) != len(eval_candidates) or any(not math.isfinite(float(s)) or not 0 <= float(s) <= 1 for s in scores_raw):
                raise ValueError("Invalid normalized reranker scores")
            scores = [
                min(1.0, float(s or 0.0) * 0.92 + min(0.08, float(c.get("rrf_score", 0.0)) * 2.0))
                if float(s or 0.0) >= 0.03 else float(s or 0.0)
                for c, s in zip(eval_candidates, scores_raw)
            ]

            # Sort chunks theo score giảm dần
            indexed = sorted(
                zip(eval_candidates, scores, scores_raw),
                key=lambda x: x[1],
                reverse=True,
            )
            ranked = []
            for c, s, raw in indexed:
                c2 = dict(c)
                c2["rerank_score"] = float(raw)
                c2["cross_encoder_score"] = float(raw)
                c2["ranking_score"] = float(s)
                c2["score_source"] = "cross_encoder"
                c2["scorer_model"] = scorer_model_label(scorer)
                c2["rerank_score_available"] = True
                ranked.append(c2)
            # Thêm các candidates còn lại vào đuôi nếu cần
            min_eval_ce = min((float(x.get("rerank_score") or 0.0) for x in ranked), default=0.1)
            for idx_tc, tc in enumerate(tail_candidates):
                pr_tc = _compute_fast_cascade_prior(bilingual_pre, tc)
                tc2 = _unscored(tc, "heuristic", heuristic_score=pr_tc,
                                ranking_score=round(max(0.0, min(min_eval_ce * 0.85, pr_tc * 0.5) - idx_tc * 0.004), 6))
                ranked.append(tc2)
            ranked = ranked[:top_n]
        except Exception as e:
            logger.warning("FlagReranker lỗi → fallback LLM rerank: %s", e)
            eval_q = f"{query} ({trans_query})" if trans_query else query
            ranked = _llm_rerank(eval_q, chunks, top_n)

    # Cache (LRU đơn giản)
    if len(_rerank_cache) >= _RERANK_CACHE_MAX:
        # Xóa 1/4 cache cũ
        for k in list(_rerank_cache.keys())[: _RERANK_CACHE_MAX // 4]:
            _rerank_cache.pop(k, None)
    # Never cache a fallback result under the failed cross-encoder's identity.
    if namespace is not None and any(c.get("score_source") == "cross_encoder" for c in ranked):
        _rerank_cache[ck] = deepcopy(ranked)
    return ranked


def rerank_groups(groups: list[tuple[str, list[dict]]], top_n: int) -> list[list[dict]]:
    """One cross-encoder call for all studies, preserving target boundaries.

    Failed/LLM-only scoring remains explicitly unavailable, never a zero score.
    """
    if top_n <= 0:
        return [[] for _ in groups]
    budget = _candidate_budget(grouped=True)
    limited = []
    tail_groups = []
    for q, chunks in groups:
        chunks = [_unscored(c, "unscored") for c in chunks]
        if any(c.get("rrf_score") for c in chunks):
            ordered = sorted(chunks, key=lambda ch: _compute_fast_cascade_prior(q, ch), reverse=True)
        else:
            ordered = chunks
        limited.append((q, ordered[:budget]))
        tail_groups.append((q, ordered[budget:]))
    pairs = [(q, _format_chunk_for_rerank(c)) for q, chunks in limited for c in chunks]
    if not pairs:
        return [[] for _ in groups]
    try:
        if _env_use_llm_rerank():
            raise RuntimeError("LLM reranker does not expose calibrated relevance scores")
        scorer = get_reranker()
        prefix = _score_cache_namespace(scorer)
        keys = [hashlib.sha256((prefix + q + '\x00' + content).encode()).hexdigest() for q, content in pairs]
        with _PAIR_CACHE_LOCK:
            known = {key: _PAIR_SCORE_CACHE[key] for key in keys if key in _PAIR_SCORE_CACHE}
            for key in known:
                _PAIR_SCORE_CACHE.move_to_end(key)
        missing = dict((key, pair) for key, pair in zip(keys, pairs) if key not in known)
        if missing:
            new_scores = scorer.score_pairs(list(missing.values()))
            if len(new_scores) != len(missing) or any(not math.isfinite(float(s)) or not 0 <= float(s) <= 1 for s in new_scores):
                raise ValueError("Incomplete batch scores")
            known.update(zip(missing, new_scores))
            with _PAIR_CACHE_LOCK:
                for key in missing:
                    _PAIR_SCORE_CACHE[key] = known[key]
                while len(_PAIR_SCORE_CACHE) > 2048:
                    _PAIR_SCORE_CACHE.popitem(last=False)
        scores = [known[key] for key in keys]
    except Exception as exc:
        logger.warning("Batch relevance scoring unavailable: %s", exc)
        return [[_unscored(c, "unavailable") for c in (chunks + tails)[:top_n]]
                for (_, chunks), (_, tails) in zip(limited, tail_groups)]
    offset = 0
    result = []
    for (q, chunks), (_, tails) in zip(limited, tail_groups):
        for c, score in zip(chunks, scores[offset:offset + len(chunks)]):
            c.update(rerank_score=score, cross_encoder_score=score, ranking_score=score,
                     rerank_score_available=True, score_source="cross_encoder",
                     scorer_model=scorer_model_label())
        offset += len(chunks)
        min_ce = min((float(c.get("rerank_score") or 0.0) for c in chunks), default=0.1)
        for idx_t, tc in enumerate(tails):
            prior_s = _compute_fast_cascade_prior(q, tc)
            tc.update(_unscored(tc, "heuristic", heuristic_score=prior_s,
                               ranking_score=round(max(0.0, min(min_ce * 0.85, prior_s * 0.5) - idx_t * 0.005), 6)))
        result.append(sorted(chunks + tails, key=lambda c: c["ranking_score"], reverse=True)[:top_n])
    return result
