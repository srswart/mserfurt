"""Three-layer genome representation (TD-007 Part 1).

Layer 1: WordGenome — macro envelope (baseline, slant, width, ink state)
Layer 2: GlyphGenome — letter shapes (Bézier segments, connections)
Layer 3: StrokeGenome — micro texture (pressure, speed per segment)

The genome provides paths; the nib physics renders them as marks.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Layer 3: Stroke-level genome (per Bézier segment)
# ---------------------------------------------------------------------------

@dataclass
class BezierSegment:
    """A cubic Bézier curve segment with rendering metadata."""
    p0: tuple[float, float]   # start point (x, y) in mm
    p1: tuple[float, float]   # control point 1
    p2: tuple[float, float]   # control point 2
    p3: tuple[float, float]   # end point
    contact: bool = True      # nib on surface?

    # Stroke-level genome (Layer 3)
    pressure_curve: list[float] = field(default_factory=lambda: [0.4, 0.8, 0.8, 0.4])
    speed_curve: list[float] = field(default_factory=lambda: [0.8, 1.0, 1.0, 0.8])
    nib_angle_drift: float = 0.0  # degrees offset from base nib angle

    def evaluate(self, t: float) -> tuple[float, float]:
        """Evaluate cubic Bézier at parameter t ∈ [0, 1]."""
        u = 1.0 - t
        x = (u**3 * self.p0[0] + 3*u**2*t * self.p1[0] +
             3*u*t**2 * self.p2[0] + t**3 * self.p3[0])
        y = (u**3 * self.p0[1] + 3*u**2*t * self.p1[1] +
             3*u*t**2 * self.p2[1] + t**3 * self.p3[1])
        return (x, y)

    def tangent(self, t: float) -> tuple[float, float]:
        """Tangent vector at parameter t."""
        u = 1.0 - t
        dx = (3*u**2 * (self.p1[0] - self.p0[0]) +
              6*u*t * (self.p2[0] - self.p1[0]) +
              3*t**2 * (self.p3[0] - self.p2[0]))
        dy = (3*u**2 * (self.p1[1] - self.p0[1]) +
              6*u*t * (self.p2[1] - self.p1[1]) +
              3*t**2 * (self.p3[1] - self.p2[1]))
        return (dx, dy)

    def direction_deg(self, t: float) -> float:
        """Stroke direction in degrees at parameter t."""
        dx, dy = self.tangent(t)
        return math.degrees(math.atan2(dy, dx))

    def pressure_at(self, t: float) -> float:
        """Interpolate pressure curve at t."""
        return _interp(self.pressure_curve, t)

    def speed_at(self, t: float) -> float:
        """Interpolate speed curve at t."""
        return _interp(self.speed_curve, t)

    def length(self) -> float:
        """Approximate arc length by sampling."""
        n = 20
        total = 0.0
        prev = self.evaluate(0.0)
        for i in range(1, n + 1):
            t = i / n
            curr = self.evaluate(t)
            total += math.sqrt((curr[0]-prev[0])**2 + (curr[1]-prev[1])**2)
            prev = curr
        return total


def _interp(curve: list[float], t: float) -> float:
    """Linearly interpolate a curve at parameter t ∈ [0, 1]."""
    n = len(curve)
    if n == 0:
        return 0.5
    if n == 1:
        return curve[0]
    idx_f = t * (n - 1)
    idx_lo = min(int(idx_f), n - 2)
    frac = idx_f - idx_lo
    return curve[idx_lo] * (1.0 - frac) + curve[idx_lo + 1] * frac


# ---------------------------------------------------------------------------
# Layer 2: Glyph-level genome
# ---------------------------------------------------------------------------

@dataclass
class GlyphGenome:
    """The shape of one letter — a sequence of Bézier segments."""
    letter: str
    segments: list[BezierSegment] = field(default_factory=list)
    x_offset: float = 0.0      # where this glyph starts within the word (mm)
    x_advance: float = 2.0     # horizontal space it occupies (mm)

    @property
    def exit_point(self) -> tuple[float, float]:
        if self.segments:
            return self.segments[-1].p3
        return (self.x_offset + self.x_advance, 0.0)

    @property
    def entry_point(self) -> tuple[float, float]:
        if self.segments:
            return self.segments[0].p0
        return (self.x_offset, 0.0)

    def exit_tangent(self) -> tuple[float, float]:
        if self.segments:
            return self.segments[-1].tangent(1.0)
        return (1.0, 0.0)

    def entry_tangent(self) -> tuple[float, float]:
        if self.segments:
            return self.segments[0].tangent(0.0)
        return (1.0, 0.0)


# ---------------------------------------------------------------------------
# Layer 1: Word-level genome
# ---------------------------------------------------------------------------

@dataclass
class WordGenome:
    """Complete genome for one word."""
    text: str = ""
    glyphs: list[GlyphGenome] = field(default_factory=list)

    # Word envelope (Layer 1)
    baseline_y: float = 0.0           # mm
    baseline_drift: list[float] = field(default_factory=list)  # per-glyph y-offsets
    word_width_mm: float = 10.0
    global_slant_deg: float = 3.0
    slant_drift: list[float] = field(default_factory=list)     # per-glyph slant variation
    ink_state_start: float = 0.85
    tempo: float = 1.0

    @property
    def letter_sequence(self) -> list[str]:
        return [g.letter for g in self.glyphs]


# ---------------------------------------------------------------------------
# Initialize from letterform guides
# ---------------------------------------------------------------------------

def genome_from_guides(
    word_text: str,
    baseline_y_mm: float = 10.0,
    x_height_mm: float = 3.8,
) -> WordGenome:
    """Create a WordGenome by converting letterform guides to Bézier segments.

    Falls back to the glyph catalog for letters without guides.
    """
    from scribesim.guides.catalog import lookup_guide
    from scribesim.glyphs.catalog import GLYPH_CATALOG
    from scribesim.layout.linebreak import char_to_glyph_id

    glyphs = []
    x = 0.0

    for ch in word_text:
        guide = lookup_guide(ch)

        if guide is not None:
            # Build Bézier segments from guide keypoints
            segments = []
            kps = guide.keypoints
            for i in range(len(kps) - 1):
                kp0 = kps[i]
                kp1 = kps[i + 1]

                # Convert keypoint coords to mm
                x0 = x + kp0.x * x_height_mm
                y0 = baseline_y_mm - kp0.y * x_height_mm
                x1 = x + kp1.x * x_height_mm
                y1 = baseline_y_mm - kp1.y * x_height_mm

                # Control points: slight arc between keypoints
                mx = (x0 + x1) / 2
                my = (y0 + y1) / 2
                # Offset control points for curvature
                dx = x1 - x0
                dy = y1 - y0
                perp_x = -dy * 0.15
                perp_y = dx * 0.15

                seg = BezierSegment(
                    p0=(x0, y0),
                    p1=(x0 + dx * 0.33 + perp_x, y0 + dy * 0.33 + perp_y),
                    p2=(x0 + dx * 0.67 - perp_x, y0 + dy * 0.67 - perp_y),
                    p3=(x1, y1),
                    contact=kp0.contact and kp1.contact,
                )
                segments.append(seg)

            adv = guide.x_advance * x_height_mm
            glyphs.append(GlyphGenome(
                letter=ch, segments=segments,
                x_offset=x, x_advance=adv,
            ))
            x += adv + 0.3 * x_height_mm  # inter-letter gap

        else:
            # Fallback: convert glyph catalog strokes to segments
            glyph_id = char_to_glyph_id(ch, "german")
            glyph = GLYPH_CATALOG.get(glyph_id)
            if glyph is None:
                x += 1.0
                continue

            segments = []
            for stroke in glyph.strokes:
                pts = stroke.control_points
                seg = BezierSegment(
                    p0=(x + pts[0][0] * x_height_mm,
                        baseline_y_mm - pts[0][1] * x_height_mm),
                    p1=(x + pts[1][0] * x_height_mm,
                        baseline_y_mm - pts[1][1] * x_height_mm),
                    p2=(x + pts[2][0] * x_height_mm,
                        baseline_y_mm - pts[2][1] * x_height_mm),
                    p3=(x + pts[3][0] * x_height_mm,
                        baseline_y_mm - pts[3][1] * x_height_mm),
                    contact=True,
                    pressure_curve=list(stroke.pressure_profile),
                )
                segments.append(seg)

            adv = glyph.advance_width * x_height_mm
            glyphs.append(GlyphGenome(
                letter=ch, segments=segments,
                x_offset=x, x_advance=adv,
            ))
            x += adv + 0.2 * x_height_mm

    return WordGenome(
        text=word_text,
        glyphs=glyphs,
        baseline_y=baseline_y_mm,
        baseline_drift=[0.0] * len(glyphs),
        word_width_mm=x,
        global_slant_deg=3.0,
        slant_drift=[0.0] * len(glyphs),
        ink_state_start=0.85,
        tempo=1.0,
    )
