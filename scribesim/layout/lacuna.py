"""Lacuna handling — apply damage regions to positioned glyph sequences.

Damage is encoded in the folio JSON at two levels:
  - Folio level: folio_dict["damage"] = {type, extent, ...} — summary
  - Line level:  line["annotations"] with type="lacuna" and char_start/char_end

This module handles the line-level span approach: glyphs at positions within
a lacuna span get their opacity reduced.
"""

from __future__ import annotations

from scribesim.layout.positioned import PositionedGlyph


def _lacuna_opacity(reason: str) -> float:
    """Map lacuna reason string to opacity value."""
    _MAP = {
        "water_damage": 0.35,
        "ink_fade":     0.50,
        "physical_loss": 0.05,
        "missing":      0.05,
    }
    return _MAP.get(reason, 0.40)


def apply_line_lacuna(
    glyphs: list[PositionedGlyph],
    annotations: list[dict],
    char_count: int,
) -> list[PositionedGlyph]:
    """Apply lacuna annotations to glyphs on a single line.

    Args:
        glyphs:      Positioned glyphs for the line (index = character position).
        annotations: Line annotation list from the folio JSON.
        char_count:  Total characters on the line (for range mapping).

    Returns:
        New list with opacity-adjusted PositionedGlyphs.
    """
    lacuna_spans: list[tuple[int, int, float]] = []  # (start, end, opacity)
    for ann in annotations:
        if ann.get("type") != "lacuna":
            continue
        span = ann.get("span", {})
        reason = ann.get("detail", {}).get("reason", "unknown")
        start = span.get("char_start", 0)
        end = span.get("char_end", char_count)
        lacuna_spans.append((start, end, _lacuna_opacity(reason)))

    if not lacuna_spans:
        return glyphs

    # Map glyph index to minimum opacity over all overlapping lacuna spans
    result: list[PositionedGlyph] = []
    for i, pg in enumerate(glyphs):
        # Each glyph roughly maps to one character position
        char_pos = i
        min_opacity = 1.0
        for start, end, op in lacuna_spans:
            if start <= char_pos < end:
                min_opacity = min(min_opacity, op)
        if min_opacity < 1.0:
            pg = PositionedGlyph(
                glyph_id=pg.glyph_id,
                x_mm=pg.x_mm,
                y_mm=pg.y_mm,
                baseline_y_mm=pg.baseline_y_mm,
                advance_w_mm=pg.advance_w_mm,
                opacity=min_opacity,
            )
        result.append(pg)

    return result
