"""Edge darkening — oxidation and handling gradient along all four page edges."""

from __future__ import annotations

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile


def apply_edge_darkening(img: Image.Image, profile: WeatheringProfile) -> Image.Image:
    """Apply edge darkening to a page image.

    A linear gradient darkens each edge inward by `width_fraction` of the
    page dimension.  Each edge contributes independently; corners receive the
    sum of the two overlapping edge gradients (strongest darkening).

    Args:
        img:     RGB PIL Image of the page.
        profile: WeatheringProfile.

    Returns:
        New RGB PIL Image with edge darkening applied.
    """
    ed = profile.aging_edge
    if not ed.enabled:
        return img.copy()

    arr = np.array(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]

    # Per-edge gradient weight (1.0 at edge → 0.0 at width_fraction inward)
    edge_w = max(1, int(w * ed.width_fraction))
    edge_h = max(1, int(h * ed.width_fraction))

    # Build 2D weight map: max weight from any edge at each pixel
    weight = np.zeros((h, w), dtype=np.float32)

    # Top edge
    rows = np.arange(min(edge_h, h))
    weight[rows, :] = np.maximum(weight[rows, :], (1.0 - rows / edge_h)[:, np.newaxis])

    # Bottom edge
    rows = np.arange(min(edge_h, h))
    weight[h - 1 - rows, :] = np.maximum(
        weight[h - 1 - rows, :], (1.0 - rows / edge_h)[:, np.newaxis]
    )

    # Left edge
    cols = np.arange(min(edge_w, w))
    weight[:, cols] = np.maximum(weight[:, cols], (1.0 - cols / edge_w)[np.newaxis, :])

    # Right edge
    cols = np.arange(min(edge_w, w))
    weight[:, w - 1 - cols] = np.maximum(
        weight[:, w - 1 - cols], (1.0 - cols / edge_w)[np.newaxis, :]
    )

    # Scale by opacity
    weight *= ed.opacity

    # Blend toward edge color
    ec = np.array(ed.color, dtype=np.float32)
    w3 = weight[:, :, np.newaxis]
    arr = arr * (1.0 - w3) + ec * w3

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
