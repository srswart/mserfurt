"""Place glyphs on the page canvas — stub pending ADV-SS-LAYOUT-001."""

from __future__ import annotations


def place(folio_dict: dict, hand_params: dict) -> dict:
    """Distribute lines and glyphs across the page canvas.

    Args:
        folio_dict: TD-001-A folio JSON dict.
        hand_params: Resolved hand parameters from the hand model.

    Returns:
        Layout dict with line bounding boxes and glyph positions.

    Raises:
        NotImplementedError: Until ADV-SS-LAYOUT-001 is implemented.
    """
    raise NotImplementedError("Layout not yet implemented (ADV-SS-LAYOUT-001)")
