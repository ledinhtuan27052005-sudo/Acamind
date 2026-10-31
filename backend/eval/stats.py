"""Kiểm định thống kê cho so sánh cặp (paired) giữa các cấu hình.

Thay thế wilcoxon_approx_p / mcnemar_p tự viết (có chặn sàn p = 1e-12) bằng:
- Wilcoxon signed-rank (scipy) cho chỉ số liên tục (MRR, nDCG, Recall).
- McNemar chính xác = kiểm định nhị thức trên các cặp bất đồng (scipy.stats.binomtest)
  cho chỉ số nhị phân (Hit@k).
- Bootstrap cặp 95% CI cho chênh lệch trung bình.
- Hiệu chỉnh Holm–Bonferroni cho nhiều so sánh.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import binomtest, wilcoxon


def paired(a: list, b: list) -> tuple[np.ndarray, np.ndarray]:
    """Giữ các câu có giá trị ở cả hai cấu hình (bỏ None)."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if not pairs:
        return np.array([]), np.array([])
    arr = np.asarray(pairs, dtype=float)
    return arr[:, 0], arr[:, 1]


def wilcoxon_p(a, b) -> float | None:
    x, y = paired(a, b)
    if len(x) == 0 or np.allclose(x, y):
        return None
    return float(wilcoxon(x, y, zero_method="wilcox", alternative="two-sided").pvalue)


def mcnemar_exact_p(a, b) -> float | None:
    x, y = paired(a, b)
    if len(x) == 0:
        return None
    b01 = int(np.sum((x >= 0.5) & (y < 0.5)))
    b10 = int(np.sum((x < 0.5) & (y >= 0.5)))
    if b01 + b10 == 0:
        return None
    return float(binomtest(b01, b01 + b10, 0.5, alternative="two-sided").pvalue)


def bootstrap_ci(a, b, n: int = 10000, seed: int = 42) -> tuple[float, float, float] | None:
    """Trả về (Δ trung bình, CI 2.5%, CI 97.5%) với Δ = a − b."""
    x, y = paired(a, b)
    if len(x) == 0:
        return None
    d = x - y
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), (n, len(d)))
    means = d[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi)


def holm(pvals: list[float | None]) -> list[float | None]:
    """Hiệu chỉnh Holm–Bonferroni; giữ None ở vị trí cũ."""
    idx = [i for i, p in enumerate(pvals) if p is not None]
    m = len(idx)
    order = sorted(idx, key=lambda i: pvals[i])
    adj: list[float | None] = [None] * len(pvals)
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, (m - rank) * pvals[i])
        running = max(running, val)
        adj[i] = running
    return adj


def fmt_p(p: float | None) -> str:
    if p is None:
        return "n/a"
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"
