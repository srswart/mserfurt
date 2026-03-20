"""Ink fade — iron-gall oxidation colour shift and intensity reduction."""

from __future__ import annotations

import numpy as np

from weather.profile import WeatheringProfile

# Ink-to-brown RGB delta and fade fraction from TD-001-E / advance spec
_FADE_DELTA = np.array([+8, -3, -12], dtype=np.int16)
_FADE_FRACTION = 0.20   # 20% intensity reduction (darken → lighter / fade)


def ink_fade(
    arr: np.ndarray,
    mask: np.ndarray,
    profile: WeatheringProfile,
) -> np.ndarray:
    """Apply iron-gall fade to masked ink pixels.

    Applies the RGB delta [+8, -3, -12] and a 20% intensity reduction
    (lifting the ink toward the parchment) to pixels selected by *mask*.
    Non-ink pixels are returned unchanged.

    Args:
        arr:     uint8 RGB array of shape (H, W, 3).
        mask:    bool array of shape (H, W); True = ink pixel.
        profile: WeatheringProfile (used for spatial_variance if needed).

    Returns:
        uint8 ndarray of shape (H, W, 3) with ink pixels faded.
    """
    result = arr.astype(np.int16).copy()

    # Lighten ink pixels toward background (20% of the way to 255)
    ink_pixels = result[mask].astype(np.int16)
    ink_pixels = ink_pixels + ((255 - ink_pixels) * _FADE_FRACTION).astype(np.int16)

    # Apply hue shift toward warm brown
    ink_pixels = ink_pixels + _FADE_DELTA

    result[mask] = np.clip(ink_pixels, 0, 255)
    return result.astype(np.uint8)
