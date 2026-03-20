"""Polygon-to-pixel IoU computation for PAGE XML glyph validation."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw


def poly_to_mask(points_str: str, width: int, height: int) -> np.ndarray:
    """Rasterize a PAGE XML points string ("x,y x,y ...") to a binary uint8 mask."""
    pts = []
    for pair in points_str.strip().split():
        x_str, y_str = pair.split(",")
        pts.append((int(x_str), int(y_str)))
    img = Image.new("1", (width, height), 0)
    draw = ImageDraw.Draw(img)
    if len(pts) >= 3:
        draw.polygon(pts, fill=1)
    return np.array(img, dtype=np.uint8)


def pixel_mask_from_page(grey_arr: np.ndarray, threshold: int = 220) -> np.ndarray:
    """Return binary ink mask from a grayscale page array (dark pixels = ink)."""
    return (grey_arr < threshold).astype(np.uint8)


def compute_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """Compute intersection-over-union of two binary masks."""
    intersection = np.logical_and(mask_a, mask_b).sum()
    union = np.logical_or(mask_a, mask_b).sum()
    if union == 0:
        return 1.0
    return float(intersection) / float(union)
