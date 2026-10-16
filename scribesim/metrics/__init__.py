"""Comparison metrics M1-M9 (TD-003 Part 2).

Quantitative measurement of distance between a rendered folio
and a real manuscript sample across 9 dimensions.
"""

from __future__ import annotations

import numpy as np
from scribesim.metrics.suite import MetricResult, run_metrics, composite_score


def orientation_histogram(angles_deg: list[float] | np.ndarray, bins: int = 18) -> np.ndarray:
    """Compute normalized orientation histogram on [-90°, 90°]."""
    arr = np.asarray(angles_deg, dtype=np.float64)
    if arr.size == 0:
        return np.ones(bins, dtype=np.float64) / bins
    folded = ((arr + 90.0) % 180.0) - 90.0
    hist, _ = np.histogram(folded, bins=bins, range=(-90.0, 90.0), density=False)
    total = float(np.sum(hist))
    return (hist / total) if total > 0 else (np.ones(bins, dtype=np.float64) / bins)


def orientation_histogram_emd(
    angles_a: list[float] | np.ndarray,
    angles_b: list[float] | np.ndarray,
    bins: int = 18,
) -> float:
    """Compute circular 1D Earth Mover's Distance between two stroke orientation distributions."""
    ha = orientation_histogram(angles_a, bins=bins)
    hb = orientation_histogram(angles_b, bins=bins)
    cdf_diff = np.cumsum(ha - hb)
    return float(np.mean(np.abs(cdf_diff)))


def projection_autocorrelation_peak(ink_map: np.ndarray, min_lag_px: int = 4, max_lag_px: int = 45) -> tuple[int, float]:
    """Compute primary horizontal minim-spacing autocorrelation lag and correlation peak."""
    if ink_map.ndim == 3:
        ink = 1.0 - (ink_map.mean(axis=2) / 255.0)
    else:
        ink = np.asarray(ink_map, dtype=np.float64)
    proj = np.mean(ink, axis=0)
    proj = proj - np.mean(proj)
    norm = float(np.sum(proj * proj))
    if norm <= 1e-9 or len(proj) <= min_lag_px + 2:
        return min_lag_px, 0.0

    upper = min(max_lag_px, len(proj) - 2)
    best_lag = min_lag_px
    best_val = -1.0
    for lag in range(min_lag_px, max(min_lag_px + 1, upper)):
        val = float(np.sum(proj[:-lag] * proj[lag:]) / norm)
        if val > best_val:
            best_val = val
            best_lag = lag
    return best_lag, best_val


__all__ = [
    "MetricResult",
    "run_metrics",
    "composite_score",
    "orientation_histogram",
    "orientation_histogram_emd",
    "projection_autocorrelation_peak",
]
