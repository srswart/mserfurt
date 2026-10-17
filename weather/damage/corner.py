"""Missing corner damage — fibrous collagen tear path with dark wood/leather backing or aged vellum tone."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

from weather.profile import WeatheringProfile
from weather.damage.dispatch import folio_has_missing_corner
from weather.damage.zones import DamageResult
from weather.substrate.noise import perlin_noise


def corner_tear_mask(
    width: int,
    height: int,
    depth_x: float,
    depth_y: float,
    irregularity: float = 0.65,
    seed: int = 0,
) -> np.ndarray:
    """Generate a boolean mask of the missing-corner region."""
    rng = np.random.default_rng(seed)

    row_start = int(height - depth_y)
    row_end = height - 1
    n_rows = max(1, row_end - row_start + 1)

    steps = rng.normal(0.0, 1.0, size=n_rows)
    walk = np.cumsum(steps)
    if walk.std() > 0:
        walk = (walk - walk.mean()) / walk.std()
    fine_jitter = rng.normal(0.0, 0.28, size=n_rows)
    jitter_amp = min(depth_x, depth_y) * irregularity * 0.16
    jitter = (0.82 * walk + 0.18 * fine_jitter) * jitter_amp

    mask = np.zeros((height, width), dtype=bool)
    for i, row in enumerate(range(row_start, height)):
        t = i / (n_rows - 1) if n_rows > 1 else 1.0
        curve_t = t ** 0.92
        base_x = (width - 1) * (1.0 - curve_t) + (width - 1 - depth_x) * curve_t
        col_boundary = int(np.clip(base_x + jitter[i], 0, width - 1))
        mask[row, col_boundary:] = True

    return mask


def apply_missing_corner(
    img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
    seed: int = 0,
) -> DamageResult:
    """Apply the missing-corner effect to f04v; pass others through unchanged."""
    if not folio_has_missing_corner(folio_id):
        return DamageResult(image=img.copy(), corner_mask=None)

    w, h = img.size
    mc = profile.damage_missing_corner

    if min(w, h) >= 320:
        depth_x_px = int(w * 0.15)
        depth_y_px = int(h * 0.12)
    else:
        px_per_mm = 300 / 25.4
        depth_x_px = min(int(35 * px_per_mm), int(w * 0.35))
        depth_y_px = min(int(28 * px_per_mm), int(h * 0.35))

    mask = corner_tear_mask(
        w,
        h,
        depth_x_px,
        depth_y_px,
        irregularity=mc.irregularity,
        seed=seed,
    )

    arr = np.array(img.convert("RGB"), dtype=np.float32)

    # Soft 2D fibrous bevel & drop-shadow along the torn vellum edge
    mask_u8 = (mask.astype(np.uint8)) * 255
    blur_bevel = np.array(
        Image.fromarray(mask_u8, mode="L").filter(ImageFilter.GaussianBlur(radius=max(2.0, min(w, h) * 0.008))),
        dtype=np.float32,
    ) / 255.0
    rim_zone = (~mask) & (blur_bevel > 0.02)
    rim_weight = np.clip(blur_bevel * 1.45, 0.0, 0.72)[:, :, np.newaxis]
    rim_color = np.array([112.0, 88.0, 58.0], dtype=np.float32)
    arr = np.where(rim_zone[:, :, np.newaxis], arr * (1.0 - rim_weight) + rim_color * rim_weight, arr)

    backing = np.array(mc.backing_color, dtype=np.float32)
    if min(w, h) >= 320:
        # On full-folio renders, show a darkened underlying folio/board shadow inside the missing corner
        # rather than glaring bright white [255, 248, 235]
        tex = perlin_noise(w, h, scale=12.0, octaves=3, seed=seed + 71)
        shadow_drop = np.clip((1.0 - blur_bevel) * 1.8, 0.0, 1.0)[:, :, np.newaxis]
        under_vellum = np.array([152.0, 132.0, 98.0], dtype=np.float32) + tex[:, :, None] * 10.0
        under_vellum = under_vellum * (0.72 + 0.28 * (1.0 - shadow_drop))
        arr[mask] = np.clip(under_vellum[mask], 30.0, 220.0)
    else:
        arr[mask] = backing

    result_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    return DamageResult(image=result_img, corner_mask=mask)
