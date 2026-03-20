"""Missing corner damage — random-walk tear path along vellum grain."""

from __future__ import annotations

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile
from weather.damage.dispatch import folio_has_missing_corner
from weather.damage.zones import DamageResult


def corner_tear_mask(
    width: int,
    height: int,
    depth_x: float,
    depth_y: float,
    irregularity: float = 0.65,
    seed: int = 0,
) -> np.ndarray:
    """Generate a boolean mask of the missing-corner region.

    The tear follows a random walk from (width, height - depth_y) to
    (width - depth_x, height), with horizontal jitter proportional to
    *irregularity*.  The region to the bottom-right of the path is masked.

    Args:
        width:        Page width in pixels.
        height:       Page height in pixels.
        depth_x:      Horizontal extent of the torn corner in pixels.
        depth_y:      Vertical extent of the torn corner in pixels.
        irregularity: Jitter amplitude (0 = straight diagonal, 1 = very jagged).
        seed:         RNG seed.

    Returns:
        bool array (height × width); True = removed/missing pixel.
    """
    rng = np.random.default_rng(seed)

    # Tear goes from (width-1, height-depth_y) to (width-depth_x, height-1).
    # Use a scanline approach: for each row in the torn band, compute the
    # x-boundary and mark all columns ≥ that boundary as missing.
    row_start = int(height - depth_y)
    row_end = height - 1
    n_rows = max(1, row_end - row_start + 1)

    jitter_amp = min(depth_x, depth_y) * irregularity * 0.25
    jitter = rng.normal(0.0, jitter_amp, size=n_rows)

    mask = np.zeros((height, width), dtype=bool)
    for i, row in enumerate(range(row_start, height)):
        t = i / (n_rows - 1) if n_rows > 1 else 1.0
        # Base x-boundary: linear interpolation from right edge → depth_x in
        base_x = (width - 1) * (1.0 - t) + (width - 1 - depth_x) * t
        col_boundary = int(np.clip(base_x + jitter[i], 0, width - 1))
        mask[row, col_boundary:] = True

    return mask


def apply_missing_corner(
    img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
    seed: int = 0,
) -> DamageResult:
    """Apply the missing-corner effect to f04v; pass others through unchanged.

    Args:
        img:       RGB PIL Image of the page.
        folio_id:  Folio identifier.
        profile:   WeatheringProfile.
        seed:      RNG seed.

    Returns:
        DamageResult with modified image and corner_mask.
    """
    if not folio_has_missing_corner(folio_id):
        return DamageResult(image=img.copy(), corner_mask=None)

    w, h = img.size
    mc = profile.damage_missing_corner

    # Convert mm-based depths to pixels at 300 DPI (≈ 11.811 px/mm)
    # For synthetic test images the pixel dimensions may be much smaller —
    # cap depths at 35% of page dimensions so tests work at any resolution.
    px_per_mm = 300 / 25.4
    depth_x_px = min(int(35 * px_per_mm), int(w * 0.35))
    depth_y_px = min(int(28 * px_per_mm), int(h * 0.35))

    mask = corner_tear_mask(
        w, h, depth_x_px, depth_y_px,
        irregularity=mc.irregularity,
        seed=seed,
    )

    arr = np.array(img.convert("RGB"), dtype=np.uint8)
    backing = np.array(mc.backing_color, dtype=np.uint8)
    arr[mask] = backing

    result_img = Image.fromarray(arr, mode="RGB")
    return DamageResult(image=result_img, corner_mask=mask)
