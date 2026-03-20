"""Ink pixel mask extraction from ScribeSim page images."""

from __future__ import annotations

import numpy as np
from PIL import Image


def extract_ink_mask(page_img: Image.Image, threshold: int = 200) -> np.ndarray:
    """Extract a boolean mask of ink pixels from a ScribeSim page image.

    Ink pixels are identified by luminance below *threshold*.  The ScribeSim
    parchment background is warm off-white (≈245, 238, 220 → luminance ~237),
    while ink strokes are near-black (≈18, 12, 8 → luminance ~14).

    Args:
        page_img:  RGB (or RGBA) PIL Image from ScribeSim render_page().
        threshold: Luminance cutoff; pixels with luminance < threshold are ink.

    Returns:
        bool ndarray of shape (H, W); True = ink pixel.
    """
    grey = np.array(page_img.convert("L"), dtype=np.uint8)
    return grey < threshold
