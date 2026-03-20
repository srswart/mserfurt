"""Camera vignette — radial intensity falloff from page center."""

from __future__ import annotations

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile


def apply_vignette(img: Image.Image, profile: WeatheringProfile) -> Image.Image:
    """Apply camera vignette darkening.

    A smooth radial falloff darkens the image from the center toward the
    corners.  The maximum darkening (at the farthest corner) equals
    `strength`.

    Args:
        img:     RGB PIL Image of the page.
        profile: WeatheringProfile.

    Returns:
        New RGB PIL Image with vignette applied.
    """
    cv = profile.optics_vignette
    if not cv.enabled:
        return img.copy()

    arr = np.array(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]

    # Normalised coordinates in [-1, 1]
    yy = (np.arange(h) - h / 2) / (h / 2)
    xx = (np.arange(w) - w / 2) / (w / 2)
    XX, YY = np.meshgrid(xx, yy)
    dist2 = XX ** 2 + YY ** 2  # 0 at centre, ~2 at corners of a square image

    # Scale so dist2=2 (corner) maps to strength darkening
    scale = 1.0 - (dist2 / 2.0) * cv.strength
    scale = np.clip(scale, 0.0, 1.0)

    arr *= scale[:, :, np.newaxis]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
