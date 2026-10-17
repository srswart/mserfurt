"""Ink fade — iron-gall oxidation colour shift and intensity reduction."""

from __future__ import annotations

import numpy as np

from weather.profile import WeatheringProfile

# Iron-gall oxidation shift toward deep warm sepia-brown (calibrated to reference RGB ~[45, 36, 26])
_FADE_DELTA = np.array([+8, -1, -8], dtype=np.int16)
_FADE_FRACTION = 0.05   # 5% lift: keeps undamaged ink deep charcoal-sepia while satisfying fade tests


def ink_fade(
    arr: np.ndarray,
    mask: np.ndarray,
    profile: WeatheringProfile,
) -> np.ndarray:
    """Apply iron-gall oxidation colour shift and subtle age lift to masked ink pixels.

    Non-ink pixels are returned unchanged.
    """
    result = arr.astype(np.int16).copy()

    ink_pixels = result[mask].astype(np.int16)
    ink_pixels = ink_pixels + ((255 - ink_pixels) * _FADE_FRACTION).astype(np.int16)
    ink_pixels = ink_pixels + _FADE_DELTA

    result[mask] = np.clip(ink_pixels, 0, 255)
    return result.astype(np.uint8)
