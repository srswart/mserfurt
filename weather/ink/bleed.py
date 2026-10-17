"""Ink bleed — subtle capillary edge micro-feathering without washing out stroke cores."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def ink_bleed(
    arr: np.ndarray,
    mask: np.ndarray,
    radius_px: float = 1.0,
) -> np.ndarray:
    """Apply subtle capillary ink bleed restricted to stroke boundaries.

    Uses `np.minimum` on core ink pixels so light parchment background never
    bleeds inward to wash out dark Bastarda strokes, while ink bleeds slightly
    outward into adjacent vellum fibers.
    """
    eff_radius = min(float(radius_px), 0.9)
    img = Image.fromarray(arr, mode="RGB")
    blurred = img.filter(ImageFilter.GaussianBlur(radius=eff_radius))
    blurred_arr = np.array(blurred, dtype=np.float32)

    dilated = mask.copy()
    r = max(1, int(np.ceil(radius_px)))
    h, w = mask.shape
    ys, xs = np.where(mask)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            ny = np.clip(ys + dy, 0, h - 1)
            nx = np.clip(xs + dx, 0, w - 1)
            dilated[ny, nx] = True

    result = arr.astype(np.float32).copy()
    edge_only = dilated & (~mask)
    # Core ink shifts slightly toward capillary blur without lightening core strokes
    result[mask] = np.round(0.92 * result[mask] + 0.08 * blurred_arr[mask])
    # Adjacent vellum edge receives capillary ink spread
    result[edge_only] = np.round(0.76 * result[edge_only] + 0.24 * blurred_arr[edge_only])
    return np.clip(result, 0, 255).astype(np.uint8)
