"""Cubic Bezier curve evaluation with adaptive subdivision.

All coordinates are in millimetres. The caller supplies control points and
receives a list of (x, y, t) sample points dense enough for 300 DPI rendering.

300 DPI → 1 pixel ≈ 0.0847 mm.  We sample at half that density (0.04 mm
step) so every pixel along the stroke is hit at least once.
"""

from __future__ import annotations

import math
from typing import Iterator

# Minimum chord length before we stop subdividing (mm)
_CHORD_THRESHOLD = 0.04   # ≈ half a pixel at 300 DPI
_MAX_DEPTH = 12           # guard against infinite recursion


def _lerp(a: tuple, b: tuple, t: float) -> tuple:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _chord_len(p0: tuple, p3: tuple) -> float:
    return math.hypot(p3[0] - p0[0], p3[1] - p0[1])


def _subdivide(p0, p1, p2, p3, depth, out: list, t_start: float, t_end: float) -> None:
    """Recursively subdivide until the chord is below threshold."""
    if depth >= _MAX_DEPTH or _chord_len(p0, p3) <= _CHORD_THRESHOLD:
        t_mid = (t_start + t_end) * 0.5
        out.append((p0[0], p0[1], t_start))
        return

    t_mid = (t_start + t_end) * 0.5
    # De Casteljau split at t=0.5
    p01  = _lerp(p0, p1, 0.5)
    p12  = _lerp(p1, p2, 0.5)
    p23  = _lerp(p2, p3, 0.5)
    p012 = _lerp(p01, p12, 0.5)
    p123 = _lerp(p12, p23, 0.5)
    pm   = _lerp(p012, p123, 0.5)

    _subdivide(p0, p01, p012, pm,  depth + 1, out, t_start, t_mid)
    _subdivide(pm, p123, p23, p3, depth + 1, out, t_mid, t_end)


def sample_bezier(
    p0: tuple, p1: tuple, p2: tuple, p3: tuple
) -> list[tuple[float, float, float]]:
    """Return adaptive sample points along a cubic Bezier.

    Args:
        p0, p1, p2, p3: Control points as (x_mm, y_mm) tuples.

    Returns:
        List of (x_mm, y_mm, t) where t ∈ [0, 1].
    """
    points: list[tuple] = []
    _subdivide(p0, p1, p2, p3, 0, points, 0.0, 1.0)
    # Append the endpoint
    points.append((p3[0], p3[1], 1.0))
    return points


def interpolate_pressure(profile: tuple, t: float) -> float:
    """Linearly interpolate a pressure profile tuple at parameter t ∈ [0, 1]."""
    n = len(profile)
    if n == 1:
        return profile[0]
    idx_f = t * (n - 1)
    idx_lo = min(int(idx_f), n - 2)
    frac = idx_f - idx_lo
    return profile[idx_lo] * (1.0 - frac) + profile[idx_lo + 1] * frac
