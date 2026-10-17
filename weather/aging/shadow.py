"""Binding shadow — organic gutter-side darkening without artificial linear curtain bands."""

from __future__ import annotations

import re

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile
from weather.substrate.noise import perlin_noise

_FOLIO_SIDE_RE = re.compile(r"^f?\d+([rv])$")


def _is_recto(folio_id: str) -> bool:
    m = _FOLIO_SIDE_RE.match(folio_id)
    return (m.group(1) == "r") if m else True


def apply_binding_shadow(
    img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
) -> Image.Image:
    """Apply binding shadow along the gutter edge.

    Recto folios (side='r') have the gutter on the left; verso on the right.
    Uses a non-linear quadratic falloff toward warm deep umber (rather than pure
    black linear bands) with subtle vertical organic modulation on full folios.
    """
    bs = profile.aging_shadow
    if not bs.enabled:
        return img.copy()

    arr = np.array(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]

    gutter_w = max(1, int(w * bs.width_fraction))
    cols = np.arange(min(gutter_w, w), dtype=np.float32)
    # Quadratic falloff hugs the spine tightly without creating a wide vertical stripe across the page
    t = 1.0 - cols / gutter_w
    gradient = (t ** 1.75) * (bs.opacity * 0.72)

    # Warm deep spine umber instead of flat RGB [0,0,0]
    shadow = np.array([48.0, 36.0, 24.0], dtype=np.float32)

    if min(h, w) >= 320:
        mod = 1.0 + 0.18 * perlin_noise(gutter_w, h, scale=max(12.0, h * 0.08), octaves=2, seed=911)
    else:
        mod = np.ones((h, gutter_w), dtype=np.float32)

    if _is_recto(folio_id):
        w3 = np.clip((gradient[np.newaxis, :] * mod)[:, :, np.newaxis], 0.0, 0.85)
        arr[:, :gutter_w, :] = arr[:, :gutter_w, :] * (1.0 - w3) + shadow * w3
    else:
        w3 = np.clip((gradient[::-1][np.newaxis, :] * mod)[:, :, np.newaxis], 0.0, 0.85)
        arr[:, w - gutter_w :, :] = arr[:, w - gutter_w :, :] * (1.0 - w3) + shadow * w3

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
