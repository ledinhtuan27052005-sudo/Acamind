"""Expose recorded ranking signals without generating post-hoc rationales."""
import math

from app.services.facet_reranker import FACET_PROMPTS


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def explain_ranking(chunk, position):
    source = chunk.get('score_source')
    if source not in ('cross_encoder', 'heuristic', 'llm_order', 'unscored', 'unavailable'):
        source = 'unavailable'
    model = _number(chunk.get('cross_encoder_score'))
    if source != 'cross_encoder' or chunk.get('rerank_score_available') is not True or model is None or not 0 <= model <= 1:
        model = None
    labels = {
        'cross_encoder': 'Có chấm điểm liên quan bằng Cross-Encoder.' if model is not None else 'Không có điểm Cross-Encoder hợp lệ.',
        'heuristic': 'Đoạn này dùng điểm heuristic; không có điểm Cross-Encoder.',
        'llm_order': 'Thứ tự dự phòng do mô hình ngôn ngữ sắp xếp; không có điểm Cross-Encoder.',
        'unscored': 'Chưa chấm lại đoạn này bằng Cross-Encoder.',
        'unavailable': 'Không có thông tin chấm điểm rerank cho đoạn này.',
    }
    facets = []
    scores = chunk.get('facet_scores') or {}
    selected = chunk.get('facet_selection') or []
    for key, label in FACET_PROMPTS.items():
        if key in scores:
            value = _number(scores[key])
            facets.append({'key': key, 'label': label,
                           'score': value if value is not None and 0 <= value <= 1 else None,
                           'selected': key in selected})
    return {
        'retrieval_position': position, 'score_source': source, 'summary': labels[source],
        'model_score': model, 'ranking_score': _number(chunk.get('ranking_score')),
        'heuristic_score': _number(chunk.get('heuristic_score')),
        'rrf_score': _number(chunk.get('rrf_score')),
        'composite_score': _number(chunk.get('composite_priority_score')),
        'facets': facets,
        'note': 'Điểm biểu thị tín hiệu xếp hạng, không phải xác suất đúng hay chất lượng nghiên cứu. '
                'Vị trí trả về có thể còn chịu phân bổ theo tiêu chí, tài liệu và đa dạng trang; không nhất thiết giảm dần theo điểm mô hình.',
    }
