"""Foxing — multi-scale organic fungal/ferric oxidation specks and clusters on vellum."""

from __future__ import annotations

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile


def apply_foxing(img: Image.Image, profile: WeatheringProfile, seed: int = 0) -> Image.Image:
    """Apply realistic foxing spots and fine ferric micro-specks to a page image.

    Combines:
      - A few irregular, soft-haloing fungal/mold blooms near the margins
      - Hundreds of tiny (0.5–1.6 px) irregular ferric/dust micro-specks with varied
        opacity and warm umber/rust tones (avoiding uniform big polka-dots).
    """
    fx = profile.aging_foxing
    if not fx.enabled:
        return img.copy()

    rng = np.random.default_rng(seed + fx.seed_offset)
    arr = np.array(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]

    raw_count = max(1, int(fx.spot_density * w * h))
    # Allow up to 260 micro-specks on full-res pages, but keep 92% of them tiny (<1.6px)
    n_spots = min(raw_count, 260)

    r_min, r_max = fx.spot_radius_range
    spot_color = np.array(fx.spot_color, dtype=np.float32)

    n_colonies = max(3, min(8, n_spots // 25 + 3))
    # Bias colonies toward the outer margins (top, bottom, left, right)
    col_xs = rng.choice([rng.uniform(0.02 * w, 0.25 * w), rng.uniform(0.75 * w, 0.98 * w)], size=n_colonies)
    col_ys = rng.uniform(0.03 * h, 0.97 * h, size=n_colonies)

    for i in range(n_spots):
        if i == 0:
            cx = float(rng.uniform(0.2 * w, 0.8 * w))
            cy = float(rng.uniform(0.2 * h, 0.8 * h))
            radius = float(rng.uniform(max(1.5, r_min), max(2.5, r_max * 0.65)))
            opacity = float(rng.uniform(0.28, 0.44))
        else:
            if rng.random() < 0.72:
                cid = int(rng.integers(0, n_colonies))
                spread = max(10.0, min(w, h) * 0.15)
                cx = float(np.clip(rng.normal(col_xs[cid], spread), 0, w - 1))
                cy = float(np.clip(rng.normal(col_ys[cid], spread), 0, h - 1))
            else:
                cx = float(rng.uniform(0, w))
                cy = float(rng.uniform(0, h))

            # 92% tiny pinpoint ferric/mold specks (0.6–1.7px), 8% irregular stain blooms
            if rng.random() < 0.92:
                radius = float(rng.uniform(0.65, 1.75))
                opacity = float(rng.uniform(0.12, 0.34))
            else:
                radius = float(rng.uniform(r_min * 0.8, r_max * 0.75))
                opacity = float(rng.uniform(0.06, 0.15))

        stretch_x = float(rng.uniform(0.70, 1.40))
        stretch_y = float(rng.uniform(0.70, 1.40))
        phase = float(rng.uniform(0.0, 2.0 * np.pi))

        pad = int(radius * 1.5) + 2
        x0 = max(0, int(cx) - pad)
        x1 = min(w, int(cx) + pad + 1)
        y0 = max(0, int(cy) - pad)
        y1 = min(h, int(cy) + pad + 1)
        if x1 <= x0 or y1 <= y0:
            continue

        ly = (np.arange(y0, y1, dtype=np.float32) - cy) / stretch_y
        lx = (np.arange(x0, x1, dtype=np.float32) - cx) / stretch_x
        dist = np.sqrt(lx[np.newaxis, :] ** 2 + ly[:, np.newaxis] ** 2)
        angle = np.arctan2(ly[:, np.newaxis], lx[np.newaxis, :])
        wobble = 1.0 + 0.22 * np.sin(3.0 * angle + phase) + 0.14 * np.cos(5.0 * angle - phase)
        eff_r = max(0.6, radius) * wobble

        weight = (np.clip(1.0 - dist / eff_r, 0.0, 1.0) ** 2.0) * opacity
        w3 = weight[:, :, np.newaxis]
        patch = arr[y0:y1, x0:x1]
        arr[y0:y1, x0:x1] = patch * (1.0 - w3) + spot_color * w3

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
