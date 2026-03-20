"""Place glyphs on the page canvas — full layout engine.

Implements ADV-SS-LAYOUT-001:
  - PageGeometry for standard (f01–f13) and final (f14–f17) folios
  - Per-line glyph placement using advance widths from the glyph catalog
  - Lacuna opacity adjustments from per-line annotations
"""

from __future__ import annotations

from scribesim.hand.params import HandParams
from scribesim.layout.geometry import make_geometry, _PX_TO_MM
from scribesim.layout.positioned import PositionedGlyph, LineLayout, PageLayout
from scribesim.layout.linebreak import char_to_glyph_id, _advance_mm
from scribesim.layout.lacuna import apply_line_lacuna


def place(folio_dict: dict, hand_params: HandParams) -> PageLayout:
    """Distribute lines and glyphs across the page canvas.

    Args:
        folio_dict:  TD-001-A folio JSON dict.
        hand_params: Resolved HandParams from the hand model.

    Returns:
        PageLayout with one LineLayout per folio text line, each populated
        with PositionedGlyphs respecting margins and lacuna regions.
    """
    folio_id = folio_dict["id"]
    geom = make_geometry(folio_id, hand_params)

    x_height_mm = hand_params.x_height_px * _PX_TO_MM
    lines_data = folio_dict.get("lines", [])
    register = _dominant_register(folio_dict)

    line_layouts: list[LineLayout] = []

    for i, line in enumerate(lines_data):
        text: str = line.get("text", "")
        line_register = line.get("register", register)
        annotations: list[dict] = line.get("annotations", [])

        baseline_y = geom.ruling_y(i) + x_height_mm

        glyphs = _place_line_glyphs(
            text=text,
            hand=hand_params,
            x_start=geom.margin_inner,
            baseline_y_mm=baseline_y,
            x_height_mm=x_height_mm,
            register=line_register,
        )

        # Apply lacuna opacity from annotations
        glyphs = apply_line_lacuna(glyphs, annotations, len(text))

        line_layouts.append(LineLayout(
            line_index=i,
            y_mm=geom.ruling_y(i),
            glyphs=glyphs,
        ))

    return PageLayout(folio_id=folio_id, geometry=geom, lines=line_layouts)


def _place_line_glyphs(
    text: str,
    hand: HandParams,
    x_start: float,
    baseline_y_mm: float,
    x_height_mm: float,
    register: str,
) -> list[PositionedGlyph]:
    """Place all glyphs in *text* left-to-right starting at *x_start*.

    Returns a list of PositionedGlyphs. Spaces are silently skipped (their
    width is included in advance_w_mm of the preceding glyph or as a small
    inter-word gap).
    """
    glyphs: list[PositionedGlyph] = []
    x = x_start

    i = 0
    while i < len(text):
        ch = text[i]

        if ch == " ":
            # Inter-word space: advance x only
            x += _advance_mm("period", hand) * 0.8 * hand.word_spacing_norm
            i += 1
            continue

        glyph_id = char_to_glyph_id(ch, register)
        adv = _advance_mm(glyph_id, hand)

        glyphs.append(PositionedGlyph(
            glyph_id=glyph_id,
            x_mm=x,
            y_mm=baseline_y_mm - x_height_mm,
            baseline_y_mm=baseline_y_mm,
            advance_w_mm=adv,
        ))
        x += adv
        i += 1

    return glyphs


def _dominant_register(folio_dict: dict) -> str:
    """Determine the dominant text register for this folio."""
    meta = folio_dict.get("metadata", {})
    ratios = meta.get("register_ratio", {})
    if not ratios:
        return "german"
    dominant = max(ratios, key=lambda k: ratios[k])
    # Map XL register codes to glyph lookup registers
    return "latin" if dominant in ("la", "latin") else "german"
