"""Parameter tuning tools (TD-003 Part 3 / TD-019 Pillar 3).

CLI commands for comparing rendered output against manuscript samples,
visual diff generation, parameter preset management, and differentiable
soft-ribbon via-point refinement.
"""

from __future__ import annotations

import numpy as np


def baseline_band_weight_mask(
    height_px: int,
    width_px: int,
    baseline_y_px: float,
    xheight_px: float,
    *,
    falloff_sigma_xh: float = 0.65,
) -> np.ndarray:
    """Compute a smooth vertical weighting mask centered on `[baseline - xheight, baseline]`.

    Pixels inside the x-height band receive weight 1.0; pixels above the top of x-height
    or below the baseline decay smoothly via a Gaussian window so neighboring-line
    descenders/ascenders do not corrupt word fitting (TD-019 Pillar 3).
    """
    if height_px <= 0 or width_px <= 0:
        raise ValueError("height_px and width_px must be positive")
    xh = max(4.0, float(xheight_px))
    top_y = float(baseline_y_px) - xh
    bot_y = float(baseline_y_px)
    sigma_px = max(2.0, falloff_sigma_xh * xh)

    y_coords = np.arange(height_px, dtype=np.float64)[:, None]
    dist_outside = np.maximum(0.0, np.maximum(top_y - y_coords, y_coords - bot_y))
    weights_1d = np.exp(-0.5 * (dist_outside / sigma_px) ** 2)
    return np.broadcast_to(weights_1d, (height_px, width_px)).copy()

