"""Glyph — a single letterform as an ordered sequence of Bezier strokes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from scribesim.glyphs.strokes import BezierStroke


@dataclass(frozen=True)
class Glyph:
    """A Bastarda letterform defined as an ordered sequence of pen strokes.

    Attributes:
        id:              Unique glyph identifier, e.g. "a", "long_s", "A_cap".
        unicode_codepoint: Unicode codepoint of the primary character (0 for
            ligatures/specials with no single codepoint).
        strokes:         Ordered pen strokes in ductus sequence (the order a
            scribe would draw them).
        advance_width:   Horizontal advance in x-height units (≥ 0).
        baseline_offset: Vertical offset of the glyph origin from baseline
            in x-height units (positive = above baseline; negative = below).
        entry_point:     (x, y) where the pen arrives, in x-height units.
                         Auto-derived from first stroke's P0 if not specified.
        exit_point:      (x, y) where the pen departs, in x-height units.
                         Auto-derived from last stroke's P3 if not specified.
    """

    id: str
    unicode_codepoint: int
    strokes: tuple  # tuple[BezierStroke, ...]
    advance_width: float
    baseline_offset: float = 0.0
    entry_point: tuple | None = None  # (x, y) in x-height units
    exit_point: tuple | None = None   # (x, y) in x-height units

    def __post_init__(self) -> None:
        if self.advance_width <= 0:
            raise ValueError(
                f"Glyph '{self.id}': advance_width must be > 0, "
                f"got {self.advance_width}"
            )
        if not self.strokes:
            raise ValueError(f"Glyph '{self.id}': strokes must not be empty")
        # Auto-derive entry/exit from stroke endpoints if not specified
        if self.entry_point is None:
            first_stroke = self.strokes[0]
            object.__setattr__(self, 'entry_point', first_stroke.control_points[0])
        if self.exit_point is None:
            last_stroke = self.strokes[-1]
            object.__setattr__(self, 'exit_point', last_stroke.control_points[-1])
