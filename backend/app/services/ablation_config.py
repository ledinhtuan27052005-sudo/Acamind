"""Cờ bật/tắt từng thành phần truy xuất phục vụ thực nghiệm loại bỏ thành phần (ablation).

Mặc định mọi cờ đều bật (FULL) nên hành vi hệ thống khi chạy thật KHÔNG thay đổi.
Chỉ script đánh giá (backend/eval) mới đặt cờ khác qua `use_flags(...)`.

Lưu ý: ContextVar không tự truyền sang thread của ThreadPoolExecutor; retriever phải
submit qua `contextvars.copy_context().run` để cờ đi theo các truy vấn con.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AblationFlags:
    use_fts: bool = True             # Truy xuất từ vựng (Postgres FTS/BM25) + hợp nhất RRF
    use_rerank: bool = True          # Bộ chấm điểm lại (cross-encoder / CPU scorer)
    use_cross_lingual: bool = True   # Dịch + mở rộng thuật ngữ Việt→Anh (vector, FTS, reranker)
    use_subquery: bool = True        # Phân rã câu hỏi so sánh thành truy vấn con song song
    use_facet_rerank: bool = True    # Chấm lại theo khía cạnh (sample/method/measure/finding/limitation)
    use_density_priority: bool = True  # Ưu tiên mật độ từ khóa/số liệu + entity gating + đa dạng tài liệu (KHÔNG chấm độ uy tín)
    use_parent_context: bool = True  # Mở rộng ngữ cảnh toàn trang (parent context)
    # Không phải một thành phần: khi đánh giá, giữ cố định độ sâu danh sách xếp hạng (tắt
    # adaptive_context_budget) để Recall@k/nDCG@k so sánh được giữa các cấu hình.
    fixed_depth: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


FULL = AblationFlags()

# Cấu hình lũy tiến: mỗi bậc bật thêm đúng MỘT thành phần so với bậc trước.
CONFIGS: dict[str, AblationFlags] = {
    "M1_Dense":         AblationFlags(False, False, False, False, False, False, False),
    "M2_Hybrid_RRF":    AblationFlags(True,  False, False, False, False, False, False),
    "M3_Rerank":        AblationFlags(True,  True,  False, False, False, False, False),
    "M4_Cross_Lingual": AblationFlags(True,  True,  True,  False, False, False, False),
    "M5_SubQuery":      AblationFlags(True,  True,  True,  True,  False, False, False),
    "M6_Facet_Rerank":  AblationFlags(True,  True,  True,  True,  True,  False, False),
    "M7_Acamind_Full":  FULL,
}

_current: ContextVar[AblationFlags] = ContextVar("acamind_ablation_flags", default=FULL)


def flags() -> AblationFlags:
    return _current.get()


@contextmanager
def use_flags(f: AblationFlags):
    token = _current.set(f)
    try:
        yield f
    finally:
        _current.reset(token)


def clear_all_caches() -> None:
    """Xóa mọi bộ nhớ đệm trong tiến trình để đo độ trễ ở trạng thái 'lạnh' công bằng."""
    from app.services import cross_lingual, embedder, evidence_policy, reranker

    cross_lingual._TRANSLATION_CACHE.clear()
    embedder._query_embed_cache.clear()
    reranker._rerank_cache.clear()
    reranker._PAIR_SCORE_CACHE.clear()
    evidence_policy._CACHE.clear()
