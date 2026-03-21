"""Page geometry — folio dimensions, margins, and ruling-line generation."""

from __future__ import annotations

from dataclasses import dataclass, field

from scribesim.hand.params import HandParams

# ---------------------------------------------------------------------------
# Page dimensions (millimetres)
# ---------------------------------------------------------------------------

# Standard folios f01–f13
_STD_W_MM  = 280.0
_STD_H_MM  = 400.0
_STD_MT    = 25.0   # margin top
_STD_MB    = 70.0   # margin bottom
_STD_MI    = 25.0   # margin inner (spine side)
_STD_MO    = 50.0   # margin outer

# Final folios f14–f17 (smaller gathering)
_FIN_W_MM  = 240.0
_FIN_H_MM  = 340.0
_FIN_MT    = 22.0
_FIN_MB    = 60.0
_FIN_MI    = 22.0
_FIN_MO    = 44.0

# Physical x-height: maps x_height_px to millimetres on the page.
# German Bastarda x-height is ~3-4mm. With x_height_px=38, _PX_TO_MM=0.100
# gives x_height_mm=3.8mm, matching historical manuscripts.
# Previous value (0.250) produced 9.5mm x-height — far too large, causing
# ascender/descender overlap between adjacent lines.
_PX_TO_MM  = 0.100
_MIN_PITCH = 7.0   # minimum baseline-to-baseline distance (mm)


def _folio_number(folio_id: str) -> int:
    """Extract integer folio number from e.g. 'f14r' → 14."""
    stripped = folio_id.lstrip("f")
    digits = ""
    for ch in stripped:
        if ch.isdigit():
            digits += ch
        else:
            break
    return int(digits) if digits else 1


@dataclass(frozen=True)
class PageGeometry:
    """Resolved page geometry for one folio.

    All measurements are in millimetres.
    """

    page_w_mm: float
    page_h_mm: float
    margin_top: float
    margin_bottom: float
    margin_inner: float
    margin_outer: float
    ruling_pitch_mm: float   # vertical distance between adjacent ruling lines
    x_height_mm: float       # physical x-height for glyph scaling
    folio_format: str        # "standard" or "final"

    # -----------------------------------------------------------------------
    # Derived geometry
    # -----------------------------------------------------------------------

    @property
    def text_w_mm(self) -> float:
        return self.page_w_mm - self.margin_inner - self.margin_outer

    @property
    def text_h_mm(self) -> float:
        return self.page_h_mm - self.margin_top - self.margin_bottom

    @property
    def ruling_count(self) -> int:
        """Number of full ruling lines that fit in the text block height."""
        return int(self.text_h_mm / self.ruling_pitch_mm)

    def ruling_y(self, line_index: int) -> float:
        """Y coordinate (from page top) of ruling line *line_index* (0-based)."""
        return self.margin_top + line_index * self.ruling_pitch_mm


def make_geometry(folio_id: str, hand: HandParams) -> PageGeometry:
    """Build a PageGeometry appropriate for *folio_id* and resolved *hand*."""
    folio_num = _folio_number(folio_id)
    final = folio_num >= 14

    if final:
        pw, ph = _FIN_W_MM, _FIN_H_MM
        mt, mb, mi, mo = _FIN_MT, _FIN_MB, _FIN_MI, _FIN_MO
        fmt = "final"
    else:
        pw, ph = _STD_W_MM, _STD_H_MM
        mt, mb, mi, mo = _STD_MT, _STD_MB, _STD_MI, _STD_MO
        fmt = "standard"

    # Ruling pitch: baseline-to-baseline distance.
    # x_height_mm × line_height_norm gives the physical baseline-to-baseline
    # spacing. With x_height=3.8mm and line_height_norm=2.5, pitch ≈ 9.5mm
    # which fits ~32 lines on a standard page and avoids ascender/descender
    # overlap (total glyph extent is ~2.3× x_height).
    x_height_mm = hand.x_height_px * _PX_TO_MM
    pitch = max(_MIN_PITCH, round(x_height_mm * hand.line_height_norm, 2))

    return PageGeometry(
        page_w_mm=pw, page_h_mm=ph,
        margin_top=mt, margin_bottom=mb,
        margin_inner=mi, margin_outer=mo,
        ruling_pitch_mm=pitch,
        x_height_mm=x_height_mm,
        folio_format=fmt,
    )
