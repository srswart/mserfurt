"""Binding shadow — gutter-side darkening from centuries of codex compression."""

from __future__ import annotations

import re

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile

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
    The shadow gradient fades from the gutter inward over `width_fraction` of
    page width at maximum `opacity`.

    Args:
        img:       RGB PIL Image of the page.
        folio_id:  Folio identifier, e.g. "f01r".
        profile:   WeatheringProfile.

    Returns:
        New RGB PIL Image with binding shadow applied.
    """
    bs = profile.aging_shadow
    if not bs.enabled:
        return img.copy()

    arr = np.array(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]

    gutter_w = max(1, int(w * bs.width_fraction))
    cols = np.arange(min(gutter_w, w), dtype=np.float32)
    # Linear gradient: 1.0 at gutter edge → 0.0 at gutter_w columns in
    gradient = (1.0 - cols / gutter_w) * bs.opacity  # shape (gutter_w,)

    # Shadow color: pure black blend (darkening)
    shadow = np.zeros(3, dtype=np.float32)

    if _is_recto(folio_id):
        # Gutter on left
        w3 = gradient[np.newaxis, :, np.newaxis]  # (1, gutter_w, 1)
        arr[:, :gutter_w, :] = arr[:, :gutter_w, :] * (1.0 - w3) + shadow * w3
    else:
        # Gutter on right — reverse gradient
        w3 = gradient[::-1][np.newaxis, :, np.newaxis]
        arr[:, w - gutter_w:, :] = arr[:, w - gutter_w:, :] * (1.0 - w3) + shadow * w3

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
