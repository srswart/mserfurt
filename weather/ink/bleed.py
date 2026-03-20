"""Ink bleed — capillary spread via masked Gaussian blur."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def ink_bleed(
    arr: np.ndarray,
    mask: np.ndarray,
    radius_px: float = 1.0,
) -> np.ndarray:
    """Apply ink bleed via a Gaussian blur restricted to ink-adjacent regions.

    The blur is applied to the full image but only *propagated* back to pixels
    that are within the ink mask or immediately adjacent to it (within the blur
    radius).  Far-background pixels retain their original values exactly.

    Args:
        arr:       uint8 RGB array of shape (H, W, 3).
        mask:      bool array of shape (H, W); True = ink pixel.
        radius_px: Gaussian blur radius in pixels.

    Returns:
        uint8 ndarray of shape (H, W, 3) with bleed applied.
    """
    img = Image.fromarray(arr, mode="RGB")
    blurred = img.filter(ImageFilter.GaussianBlur(radius=radius_px))
    blurred_arr = np.array(blurred, dtype=np.uint8)

    # Dilate the mask by the blur radius to include edge-adjacent pixels
    # Simple dilation: for each masked pixel, mark a square neighbourhood
    dilated = mask.copy()
    r = max(1, int(np.ceil(radius_px)))
    h, w = mask.shape
    ys, xs = np.where(mask)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            ny = np.clip(ys + dy, 0, h - 1)
            nx = np.clip(xs + dx, 0, w - 1)
            dilated[ny, nx] = True

    result = arr.copy()
    result[dilated] = blurred_arr[dilated]
    return result
