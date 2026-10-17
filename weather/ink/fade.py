"""Ink fade — iron-gall oxidation colour shift toward warm sepia/rust-brown
with spatial intra-word and intra-letter chromatic variation.
"""

from __future__ import annotations

import numpy as np

from weather.profile import WeatheringProfile

# Strong warm iron-gall oxidation shift (+R, -G, --B) so aged ink is unmistakably brownish
_FADE_DELTA = np.array([+16, -2, -16], dtype=np.int16)
_FADE_FRACTION = 0.12   # 12% base lift toward parchment


def ink_fade(
    arr: np.ndarray,
    mask: np.ndarray,
    profile: WeatheringProfile,
) -> np.ndarray:
    """Apply iron-gall oxidation colour shift and subtle age lift to masked ink pixels.

    Thinner/lighter ink strokes (higher initial luminance inside the mask, such as
    hairlines, stroke margins, and pre-dip words) oxidize further toward warm rust-sienna
    than dense pooled stroke cores.
    Non-ink pixels are returned unchanged.
    """
    result = arr.astype(np.int16).copy()
    if not mask.any():
        return result.astype(np.uint8)

    ink_pixels = result[mask].astype(np.float32)
    # Thinner ink pixels (higher grey value) undergo stronger oxidation lift & warmer brown shift
    ink_lum = ink_pixels.mean(axis=1, keepdims=True)
    thinness = np.clip((ink_lum - 30.0) / 150.0, 0.0, 1.0)
    local_fade = _FADE_FRACTION + 0.14 * thinness

    faded = ink_pixels + (255.0 - ink_pixels) * local_fade
    # Shift toward warm brown: extra red/amber boost on thinner strokes
    faded[:, 0] += _FADE_DELTA[0] + 10.0 * thinness[:, 0]
    faded[:, 1] += _FADE_DELTA[1] + 2.0 * thinness[:, 0]
    faded[:, 2] += _FADE_DELTA[2] - 8.0 * thinness[:, 0]

    result[mask] = np.clip(np.round(faded), 0, 255).astype(np.int16)
    return result.astype(np.uint8)
