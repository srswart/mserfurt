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

    # Explicit connection points in mm (world space), set from Glyph.exit_point /
    # entry_point when the catalog defines them. The renderer prefers these over
    # segment-derived endpoints for inter-glyph hairlines.
    connection_exit_mm: tuple | None = None
    connection_entry_mm: tuple | None = None

    @property
    def exit_point(self) -> tuple[float, float]:
        if self.connection_exit_mm is not None:
            return self.connection_exit_mm
        if self.segments:
            return self.segments[-1].p3
        return (self.x_offset + self.x_advance, 0.0)

    @property
    def entry_point(self) -> tuple[float, float]:
        if self.connection_entry_mm is not None:
            return self.connection_entry_mm
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
    overline: bool = False        # True for scribal Roman numeral groups

    @property
    def letter_sequence(self) -> list[str]:
        return [g.letter for g in self.glyphs]


# ---------------------------------------------------------------------------
# Initialize from letterform guides
# ---------------------------------------------------------------------------

def _load_extracted_guides(guides_path) -> dict:
    """Load a guides_extracted.toml and return a dict mapping letter → LetterformGuide.

    Returns an empty dict if the file does not exist or fails to parse.
    """
    import tomllib
    from pathlib import Path
    from scribesim.guides.keypoint import Keypoint, LetterformGuide

    p = Path(guides_path) if guides_path is not None else None

    # Auto-detect from repo root if not specified
    if p is None:
        candidate = Path("shared/hands/guides_extracted.toml")
        if candidate.exists():
            p = candidate

    if p is None or not p.exists():
        return {}

    try:
        data = tomllib.loads(p.read_text())
    except Exception:
        return {}

    guides: dict = {}
    for letter, entry in data.items():
        if not isinstance(entry, dict):
            continue
        raw_kps = entry.get("keypoints", [])
        kps = tuple(
            Keypoint(
                x=float(k.get("x", 0.0)),
                y=float(k.get("y", 0.0)),
                point_type=str(k.get("point_type", "stroke")),
                contact=bool(k.get("contact", True)),
                direction_deg=float(k.get("direction_deg", 270.0)),
                flexibility_mm=float(k.get("flexibility_mm", 0.2)),
            )
            for k in raw_kps
        )
        guides[letter] = LetterformGuide(
            letter=letter,
            keypoints=kps,
            x_advance=float(entry.get("x_advance", 0.6)),
            ascender=bool(entry.get("ascender", False)),
            descender=bool(entry.get("descender", False)),
        )
    return guides


import re as _re

_ROMAN_TOKEN_RE = _re.compile(r'^([MDCLXVI]{2,})([,.:;!?]*)$')


def preprocess_roman_numerals(text: str) -> tuple[str, list[int]]:
    """Convert uppercase Roman numeral tokens to scribal form with overline flag.

    e.g. "anno MCCCCLVII Domini"  → "anno ·mcccclvij· Domini"
         "anno MCCCCLVII, in..."  → "anno ·mcccclvij·, in..."
    Also returns word indices (in the output list) that need an overline.

    Rules:
      - Tokens where the alphabetic part is all-uppercase MDCLXVI ≥ 2 chars are numerals.
      - Lowercased, final 'i' → 'j', wrapped in interpunct (·) separators.
      - Trailing punctuation (, . : ;) is re-attached after the closing interpunct.
      - Resulting token is flagged for overline rendering.
    """
    words = text.split()
    numeral_indices: list[int] = []
    out: list[str] = []
    for i, w in enumerate(words):
        m = _ROMAN_TOKEN_RE.fullmatch(w)
        if m:
            numeral_part, punct_part = m.group(1), m.group(2)
            lowered = numeral_part.lower()
            # Final 'i' → 'j' (scribal convention for trailing minims)
            if lowered.endswith("i"):
                lowered = lowered[:-1] + "j"
            out.append(f"·{lowered}·{punct_part}")
            numeral_indices.append(i)
        else:
            out.append(w)
    return " ".join(out), numeral_indices


# Per-letter right-bearing adjustment (in x_height units, added to inter-letter gap).
# Negative = tighter coupling to next letter; positive = more breathing room.
_RIGHT_BEARING: dict[str, float] = {
    # Tight exits — rounded or open forms that optically crowd next letter
    "o": -0.05, "c": -0.05, "e": -0.04, "a": -0.04,
    "g": -0.03, "q": -0.03,
    # Wide exits — letters that already carry visual space on their right
    "d": 0.03, "h": 0.02, "l": 0.02, "b": 0.02, "t": 0.02, "k": 0.02,
    # Default (n, m, u, i, r, s, f, z …) → 0.0
}


def genome_from_guides(
    word_text: str,
    baseline_y_mm: float = 10.0,
    x_height_mm: float = 3.8,
    guides_path=None,
    letter_gap: float = 0.12,
) -> WordGenome:
    """Create a WordGenome by converting letterform guides to Bézier segments.

    Prefers extracted guides from *guides_path* (or auto-detected
    ``shared/hands/guides_extracted.toml``) over the hand-defined catalog.
    Falls back to the glyph catalog for letters without any guide.

    Args:
        word_text: Word to seed.
        baseline_y_mm: Y position of baseline in mm.
        x_height_mm: X-height in mm.
        guides_path: Optional path to a ``guides_extracted.toml`` file.
        letter_gap: Base inter-letter gap as a fraction of x_height_mm (default 0.12).
    """
    from scribesim.guides.catalog import lookup_guide
    from scribesim.glyphs.catalog import GLYPH_CATALOG
    from scribesim.layout.linebreak import char_to_glyph_id

    extracted = _load_extracted_guides(guides_path)

    glyphs = []
    x = 0.0

    for ch in word_text:
        # Try GLYPH_CATALOG first — it has proper multi-stroke geometry.
        # Guide keypoints (lookup_guide) are structural markers that collapse
        # to 1 Bézier per letter when all points are contact=True, which
        # produces unrecognizable letterforms in the genome.
        glyph_id = char_to_glyph_id(ch, "german")
        glyph = GLYPH_CATALOG.get(glyph_id)

        if glyph is not None:
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

            # Convert explicit catalog entry/exit from x-height units to mm
            # (baseline_y_mm - y_xh * x_height_mm gives world y in mm).
            def _xh_to_mm(pt_xh: tuple, _x: float = x) -> tuple[float, float]:
                return (
                    _x + pt_xh[0] * x_height_mm,
                    baseline_y_mm - pt_xh[1] * x_height_mm,
                )

            conn_exit = _xh_to_mm(glyph.exit_point) if glyph.exit_point is not None else None
            conn_entry = _xh_to_mm(glyph.entry_point) if glyph.entry_point is not None else None

            # Only store overrides when they differ from the raw segment endpoints
            # (i.e. the catalog explicitly set them via entry=/exit= kwargs).
            raw_exit_xh = glyph.strokes[-1].control_points[-1]
            raw_entry_xh = glyph.strokes[0].control_points[0]
            conn_exit = conn_exit if glyph.exit_point != raw_exit_xh else None
            conn_entry = conn_entry if glyph.entry_point != raw_entry_xh else None

            glyphs.append(GlyphGenome(
                letter=ch, segments=segments,
                x_offset=x, x_advance=adv,
                connection_exit_mm=conn_exit,
                connection_entry_mm=conn_entry,
            ))
            gap = letter_gap + _RIGHT_BEARING.get(ch, 0.0)
            x += adv + gap * x_height_mm

        else:
            # Fallback: guide keypoints → group into strokes by pen contact,
            # fit one cubic Bézier per run. Used only when GLYPH_CATALOG has
            # no entry for this character.
            guide = extracted.get(ch) or lookup_guide(ch)
            if guide is None:
                x += 1.0
                continue

            segments = []
            kps = guide.keypoints

            stroke_pts: list[list] = []
            current: list = []
            for kp in kps:
                if kp.contact:
                    current.append(kp)
                else:
                    if len(current) >= 2:
                        stroke_pts.append(current)
                    current = []
            if len(current) >= 2:
                stroke_pts.append(current)

            for stroke in stroke_pts:
                n = len(stroke)
                p0_kp = stroke[0]
                p1_kp = stroke[max(1, n // 3)]
                p2_kp = stroke[max(1, 2 * n // 3)]
                p3_kp = stroke[-1]

                def _to_mm(kp, _x=x):
                    return (_x + kp.x * x_height_mm,
                            baseline_y_mm - kp.y * x_height_mm)

                seg = BezierSegment(
                    p0=_to_mm(p0_kp), p1=_to_mm(p1_kp),
                    p2=_to_mm(p2_kp), p3=_to_mm(p3_kp),
                    contact=True,
                )
                segments.append(seg)

            # Align first p0 with cursor x
            if segments:
                shift = x - segments[0].p0[0]
                for seg in segments:
                    seg.p0 = (seg.p0[0] + shift, seg.p0[1])
                    seg.p1 = (seg.p1[0] + shift, seg.p1[1])
                    seg.p2 = (seg.p2[0] + shift, seg.p2[1])
                    seg.p3 = (seg.p3[0] + shift, seg.p3[1])

            adv = guide.x_advance * x_height_mm
            glyphs.append(GlyphGenome(
                letter=ch, segments=segments,
                x_offset=x, x_advance=adv,
            ))
            gap = letter_gap + _RIGHT_BEARING.get(ch, 0.0)
            x += adv + gap * x_height_mm

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
