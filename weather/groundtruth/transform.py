"""Coordinate transform applicator — apply curl displacement to PAGE XML points."""

from __future__ import annotations

from typing import Optional

import numpy as np


def apply_curl_to_points(
    points: list[tuple[int, int]],
    transform: Optional[np.ndarray],
    img_w: int,
    img_h: int,
    canvas_w: int,
    canvas_h: int,
) -> list[tuple[int, int]]:
    """Apply a curl displacement map to a list of canvas-space (x, y) points.

    Points are scaled from canvas space to image pixel space, the displacement
    is looked up at those pixel coordinates, applied, then scaled back to
    canvas space.

    Args:
        points:    List of (x, y) in canvas coordinates.
        transform: Float32 array (img_h, img_w, 2) where [:,:,0]=dy, [:,:,1]=dx.
                   Pass None for identity (points returned unchanged).
        img_w:     Actual image width in pixels.
        img_h:     Actual image height in pixels.
        canvas_w:  Canvas width in the PAGE XML (typically 1000).
        canvas_h:  Canvas height in the PAGE XML (typically 1000).

    Returns:
        New list of (x, y) canvas-space points after displacement.
    """
    if transform is None:
        return list(points)

    result = []
    for x_c, y_c in points:
        # Canvas → pixel
        x_px = int(round(x_c * img_w / canvas_w))
        y_px = int(round(y_c * img_h / canvas_h))
        # Clamp to image bounds
        x_px = max(0, min(img_w - 1, x_px))
        y_px = max(0, min(img_h - 1, y_px))
        # Look up displacement (dy, dx)
        dy = float(transform[y_px, x_px, 0])
        dx = float(transform[y_px, x_px, 1])
        # Apply displacement in pixel space
        x_new_px = x_px + dx
        y_new_px = y_px + dy
        # Pixel → canvas
        x_new_c = int(round(x_new_px * canvas_w / img_w))
        y_new_c = int(round(y_new_px * canvas_h / img_h))
        result.append((x_new_c, y_new_c))

    return result
