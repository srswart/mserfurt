"""BezierStroke — a single named pen stroke as a cubic Bezier curve."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

# A 2-D point as (x, y) floats in glyph-coordinate space.
# x: horizontal, positive rightward; y: vertical, positive upward.
# Units are normalised to x-height = 1.0.
Point = Tuple[float, float]


@dataclass(frozen=True)
class BezierStroke:
    """One pen stroke: a cubic Bezier curve with per-stroke pressure profile.

    Attributes:
        control_points: Exactly 4 (x, y) points — P0 (start), P1, P2, P3 (end).
        pressure_profile: Sequence of pressure values in [0.0, 1.0] sampled
            along the curve from t=0 to t=1.  At least two values required.
        stroke_name: Human-readable name for the stroke, e.g. "body", "ascender".
    """

    control_points: Tuple[Point, Point, Point, Point]
    pressure_profile: Tuple[float, ...] = field(default=(0.5, 0.8, 0.8, 0.5))
    stroke_name: str = ""

    def __post_init__(self) -> None:
        if len(self.control_points) != 4:
            raise ValueError(
                f"BezierStroke requires exactly 4 control points, "
                f"got {len(self.control_points)}"
            )
        if len(self.pressure_profile) < 2:
            raise ValueError("pressure_profile must have at least 2 values")
        if not all(0.0 <= p <= 1.0 for p in self.pressure_profile):
            raise ValueError("pressure_profile values must be in [0.0, 1.0]")
        # Validate no zero-length segment: P0 ≠ P3
        p0, _, _, p3 = self.control_points
        if p0 == p3 and len(set(self.control_points)) == 1:
            raise ValueError("degenerate stroke: all control points identical")

    def length_approx(self) -> float:
        """Rough chord length P0→P3 (fast degenerate-check proxy)."""
        p0, _, _, p3 = self.control_points
        return ((p3[0] - p0[0]) ** 2 + (p3[1] - p0[1]) ** 2) ** 0.5
