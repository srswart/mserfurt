"""Line breaking — distribute text tokens across ruling lines.

Implements a greedy first-fit algorithm (Knuth-Plass penalty optimisation is
deferred to ADV-SS-RENDER-001 where sub-pixel hinting is available). The
output is a list of token-sequences, one per ruling line, guaranteed not to
exceed the text-block width.

Units: all widths in millimetres.
"""

from __future__ import annotations

from scribesim.hand.params import HandParams
from scribesim.glyphs.catalog import GLYPH_CATALOG, lookup


# mm-per-x-height-unit scaling (must match geometry.py)
from scribesim.layout.geometry import _PX_TO_MM

# Space between glyphs within a word and between words
_GLYPH_GAP_NORM = 0.05   # fraction of x_height between glyphs
_SPACE_WIDTH_NORM = 0.45  # fraction of x_height for inter-word space


def _advance_mm(glyph_id: str, hand: HandParams) -> float:
    """Return the advance width of *glyph_id* in mm, scaled by hand params."""
    glyph = GLYPH_CATALOG.get(glyph_id)
    if glyph is None:
        # Fallback for unmapped characters: use average width
        return hand.x_height_px * _PX_TO_MM * 0.55
    # Glyph advance_width is in x-height units; scale to mm and apply letter spacing
    x_height_mm = hand.x_height_px * _PX_TO_MM
    return glyph.advance_width * x_height_mm * hand.letter_spacing_norm


def _space_mm(hand: HandParams) -> float:
    """Inter-word space width in mm."""
    return hand.x_height_px * _PX_TO_MM * _SPACE_WIDTH_NORM * hand.word_spacing_norm


def char_to_glyph_id(ch: str, register: str = "german") -> str:
    """Map a Unicode character to a glyph catalog key."""
    try:
        glyph = lookup(ch, register)
        return glyph.id
    except (KeyError, ValueError):
        # Unknown characters get a space-width placeholder
        return "period"


def break_lines(text: str, hand: HandParams, text_w_mm: float,
                register: str = "german") -> list[list[tuple[str, float]]]:
    """Break *text* into lines not exceeding *text_w_mm*.

    Returns a list of lines, each a list of (glyph_id, advance_w_mm) pairs.
    Space glyphs between words are represented as (None, space_mm).
    """
    words = text.split()
    if not words:
        return []

    space_w = _space_mm(hand)
    lines: list[list[tuple[str | None, float]]] = []
    current_line: list[tuple[str | None, float]] = []
    current_w = 0.0

    for word in words:
        # Build glyph sequence for this word
        word_glyphs: list[tuple[str, float]] = []
        for ch in word:
            gid = char_to_glyph_id(ch, register)
            word_glyphs.append((gid, _advance_mm(gid, hand)))

        word_w = sum(adv for _, adv in word_glyphs)

        # Check if the word fits on the current line (with preceding space if needed)
        gap = space_w if current_line else 0.0
        if current_w + gap + word_w <= text_w_mm:
            if current_line:
                current_line.append((None, space_w))  # inter-word space
                current_w += space_w
            current_line.extend(word_glyphs)
            current_w += word_w
        else:
            # Flush current line and start a new one
            if current_line:
                lines.append(current_line)
            # If the word itself is wider than a full line, break it character-by-character
            if word_w > text_w_mm:
                seg: list[tuple[str, float]] = []
                seg_w = 0.0
                for gid, adv in word_glyphs:
                    if seg_w + adv > text_w_mm and seg:
                        lines.append(seg)
                        seg = []
                        seg_w = 0.0
                    seg.append((gid, adv))
                    seg_w += adv
                current_line = seg
                current_w = seg_w
            else:
                current_line = list(word_glyphs)
                current_w = word_w

    if current_line:
        lines.append(current_line)

    return lines
