"""Ink flake — pressure-targeted stochastic ink loss."""

from __future__ import annotations

import numpy as np

from weather.profile import WeatheringProfile

# Pressure heatmap threshold above which flaking probability applies (0–1 scale)
_PRESSURE_THRESHOLD = 0.85   # heatmap value / 255 must exceed this


def ink_flake(
    arr: np.ndarray,
    mask: np.ndarray,
    heatmap: np.ndarray,
    profile: WeatheringProfile,
    seed: int = 0,
) -> np.ndarray:
    """Remove small clusters of ink pixels preferentially at high-pressure strokes.

    Only pixels where the normalised pressure heatmap exceeds
    ``_PRESSURE_THRESHOLD`` (0.85) are candidates.  Each candidate pixel is
    removed (replaced with a sample from its neighbourhood background) with
    probability ``profile.ink_flake.flake_probability``.  Removal expands to
    a 2-pixel cluster by also removing one adjacent ink pixel.

    Args:
        arr:      uint8 RGB array of shape (H, W, 3).
        mask:     bool array of shape (H, W); True = ink pixel.
        heatmap:  uint8 array of shape (H, W); 0–255 pressure values.
        profile:  WeatheringProfile for flake parameters.
        seed:     RNG seed for reproducibility.

    Returns:
        uint8 ndarray of shape (H, W, 3) with flaked pixels replaced.
    """
    rng = np.random.default_rng(seed)
    result = arr.copy()
    h, w = mask.shape

    fp = profile.ink_flake
    prob = fp.flake_probability

    # Normalise heatmap to [0, 1]
    pressure = heatmap.astype(np.float32) / 255.0

    # Candidate pixels: ink AND above pressure threshold
    candidates = mask & (pressure >= _PRESSURE_THRESHOLD)
    cand_ys, cand_xs = np.where(candidates)

    if len(cand_ys) == 0:
        return result

    # Estimate background colour from near-border region (top-left corner proxy)
    bg_sample = arr[0:4, 0:4].reshape(-1, 3).astype(np.float32).mean(axis=0)
    bg_colour = np.clip(bg_sample, 0, 255).astype(np.uint8)

    for cy, cx in zip(cand_ys, cand_xs):
        if rng.random() < prob:
            # Remove primary pixel
            result[cy, cx] = bg_colour
            # Expand cluster: remove one adjacent ink pixel if present
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx]:
                    result[ny, nx] = bg_colour
                    break

    return result
