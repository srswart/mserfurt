"""Legibility scorer — compute per-TextLine legibility from damage masks."""

from __future__ import annotations

from typing import Optional

import numpy as np


def compute_legibility(
    cx: int,
    cy: int,
    water_zone: Optional[np.ndarray],
    corner_mask: Optional[np.ndarray],
    img_w: int,
    img_h: int,
    canvas_w: int,
    canvas_h: int,
) -> float:
    """Compute legibility score for a TextLine centroid in canvas coordinates.

    Scoring rules (applied in priority order):
      1. If the centroid falls within the corner_mask → 0.0 (completely occluded).
      2. If the centroid falls within the water_zone → gradient score based on
         vertical position: 0.0 at the top of the page, approaching 1.0 at the
         tide line.
      3. Otherwise → 1.0 (fully legible).

    Args:
        cx, cy:       Centroid in canvas coordinates.
        water_zone:   Bool array (img_h, img_w); True = wet pixel.  None = no water.
        corner_mask:  Bool array (img_h, img_w); True = removed pixel.  None = no corner.
        img_w:        Actual image width in pixels.
        img_h:        Actual image height in pixels.
        canvas_w:     Canvas width (typically 1000).
        canvas_h:     Canvas height (typically 1000).

    Returns:
        Float in [0.0, 1.0].
    """
    # Convert centroid to pixel space
    x_px = int(round(cx * img_w / canvas_w))
    y_px = int(round(cy * img_h / canvas_h))
    x_px = max(0, min(img_w - 1, x_px))
    y_px = max(0, min(img_h - 1, y_px))

    # 1. Corner occlusion — complete removal
    if corner_mask is not None and corner_mask[y_px, x_px]:
        return 0.0

    # 2. Water damage — gradient based on depth in wet zone
    if water_zone is not None and water_zone[y_px, x_px]:
        # Find the tide line at this column (last wet row in this column)
        col_wet = np.where(water_zone[:, x_px])[0]
        if len(col_wet) == 0:
            return 1.0
        tide_row = int(col_wet[-1]) + 1  # first dry row
        if tide_row <= 0:
            return 1.0
        # Legibility: 0.0 at top (row 0), 1.0 at tide line
        return float(np.clip(y_px / tide_row, 0.0, 1.0))

    return 1.0
