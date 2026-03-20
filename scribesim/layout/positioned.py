"""PositionedGlyph, LineLayout, PageLayout — layout output types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from scribesim.layout.geometry import PageGeometry


@dataclass(frozen=True)
class PositionedGlyph:
    """A single glyph placed on the page canvas.

    Coordinates are in millimetres from the page top-left corner.

    Attributes:
        glyph_id:     Key into GLYPH_CATALOG (e.g. "a", "long_s").
        x_mm:         Left edge of glyph advance box.
        y_mm:         Top of glyph bounding box (= baseline_y_mm - x_height).
        baseline_y_mm: Baseline y-coordinate.
        advance_w_mm:  Horizontal advance (used to position next glyph).
        opacity:      Rendering opacity [0.0–1.0]; < 1.0 in lacuna regions.
    """

    glyph_id: str
    x_mm: float
    y_mm: float
    baseline_y_mm: float
    advance_w_mm: float
    opacity: float = 1.0

    def __post_init__(self) -> None:
        if not (0.0 <= self.opacity <= 1.0):
            raise ValueError(
                f"PositionedGlyph opacity must be in [0, 1], got {self.opacity}"
            )
        if self.advance_w_mm <= 0:
            raise ValueError(
                f"PositionedGlyph advance_w_mm must be > 0, got {self.advance_w_mm}"
            )


@dataclass
class LineLayout:
    """One ruled line on the page with its positioned glyphs.

    Attributes:
        line_index:  0-based ruling line number.
        y_mm:        Y coordinate of the ruling line (from page top).
        glyphs:      Glyphs placed on this line, left to right.
    """

    line_index: int
    y_mm: float
    glyphs: list  # list[PositionedGlyph]


@dataclass
class PageLayout:
    """Complete layout for a single folio page.

    Attributes:
        folio_id:  Folio identifier, e.g. "f01r".
        geometry:  Resolved page geometry.
        lines:     Ordered list of LineLayout (one per text line).
    """

    folio_id: str
    geometry: PageGeometry
    lines: list  # list[LineLayout]
