"""Foxing — pseudo-random fungal spots on vellum surface."""

from __future__ import annotations

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile


def apply_foxing(img: Image.Image, profile: WeatheringProfile, seed: int = 0) -> Image.Image:
    """Apply foxing spots to a page image.

    Spots are placed at pseudo-random locations using the profile density.
    Each spot is a soft-edged circular blot blended toward `spot_color`.

    Args:
        img:     RGB PIL Image of the page.
        profile: WeatheringProfile.
        seed:    RNG seed.

    Returns:
        New RGB PIL Image with foxing spots applied.
    """
    fx = profile.aging_foxing
    if not fx.enabled:
        return img.copy()

    rng = np.random.default_rng(seed + fx.seed_offset)
    arr = np.array(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]

    n_spots = max(1, int(fx.spot_density * w * h))
    r_min, r_max = fx.spot_radius_range
    spot_color = np.array(fx.spot_color, dtype=np.float32)

    # Vectorised: work within each spot's bounding box only (avoids full-image
    # distance computation per spot, which is O(n_spots × H × W)).
    cxs = rng.uniform(0, w, size=n_spots)
    cys = rng.uniform(0, h, size=n_spots)
    radii = rng.uniform(r_min, r_max, size=n_spots)
    opacities = rng.uniform(0.4, 0.85, size=n_spots)

    for i in range(n_spots):
        cx, cy = cxs[i], cys[i]
        radius = radii[i]
        opacity = opacities[i]
        pad = int(radius) + 1
        x0 = max(0, int(cx) - pad)
        x1 = min(w, int(cx) + pad + 1)
        y0 = max(0, int(cy) - pad)
        y1 = min(h, int(cy) + pad + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        # Local coordinate grid for the bounding box only
        ly = np.arange(y0, y1, dtype=np.float32) - cy
        lx = np.arange(x0, x1, dtype=np.float32) - cx
        dist = np.sqrt(lx[np.newaxis, :] ** 2 + ly[:, np.newaxis] ** 2)
        weight = np.clip(1.0 - dist / radius, 0.0, 1.0) ** 2 * opacity
        w3 = weight[:, :, np.newaxis]
        patch = arr[y0:y1, x0:x1]
        arr[y0:y1, x0:x1] = patch * (1.0 - w3) + spot_color * w3

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
