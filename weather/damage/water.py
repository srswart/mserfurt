"""Water damage — top-down gradient with DLA tide line, ink dissolution."""

from __future__ import annotations

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile
from weather.damage.dispatch import folio_is_water_damaged
from weather.damage.zones import DamageResult


def tide_line_mask(
    width: int,
    height: int,
    penetration: float = 0.38,
    seed: int = 0,
) -> np.ndarray:
    """Generate a boolean water-zone mask via a diffusion-inspired random walk boundary.

    The tide line separates the wet upper region from the dry lower region.
    The boundary is a horizontally-varying row index derived from a seeded
    random walk, producing the irregular, naturalistic tide line characteristic
    of water damage.

    Args:
        width:        Page width in pixels.
        height:       Page height in pixels.
        penetration:  Fraction of page height that is wet on average.
        seed:         RNG seed for reproducibility.

    Returns:
        bool array (height × width); True = wet/water-affected pixel.
    """
    rng = np.random.default_rng(seed)

    # Base tide line row (mean penetration depth)
    base_row = int(height * penetration)

    # Random walk along the horizontal axis to create an irregular boundary
    walk = np.zeros(width, dtype=np.float64)
    step_std = height * 0.06   # ≈ 6% of page height per step
    steps = rng.normal(0.0, step_std, size=width)
    walk = np.cumsum(steps)
    # Centre and scale so deviation is ≤ ±15% of page height
    max_dev = height * 0.15
    if walk.std() > 0:
        walk = walk / walk.std() * max_dev
    walk -= walk.mean()

    tide_row = np.clip(base_row + walk.astype(int), 1, height - 1)

    # Build mask: True for rows above the tide line per column
    mask = np.zeros((height, width), dtype=bool)
    for col in range(width):
        mask[:tide_row[col], col] = True

    return mask


def apply_water_damage(
    img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
    seed: int = 0,
) -> DamageResult:
    """Apply water damage to a page image if applicable to this folio.

    For non-water-damaged folios, returns the image unchanged with no zone mask.
    For f04r–f05v, applies:
      - Vertical gradient darkening (from_above direction)
      - Vellum colour staining in wet zone (darkened, shifted toward stain colour)
      - Tide line boundary via random walk

    Args:
        img:       RGB PIL Image of the page.
        folio_id:  Folio identifier, e.g. "f04r".
        profile:   WeatheringProfile.
        seed:      RNG seed.

    Returns:
        DamageResult with modified image and water_zone mask.
    """
    if not folio_is_water_damaged(folio_id):
        return DamageResult(image=img.copy(), water_zone=None)

    w, h = img.size
    arr = np.array(img.convert("RGB"), dtype=np.float32)
    wd = profile.damage_water

    water_zone = tide_line_mask(w, h, penetration=wd.penetration, seed=seed)

    # Vertical gradient: full stain at row 0, fading to 0 at the tide line per column
    stain_r, stain_g, stain_b = wd.stain_color

    # Per-column tide row (last wet row index + 1) — vectorised over columns.
    # water_zone is True for rows above the tide line.  argmin on the reversed
    # column finds the first False from the bottom, i.e. the tide boundary.
    row_idx = np.arange(h, dtype=np.float32)[:, np.newaxis]  # (H, 1)

    # tide_rows[col] = number of wet rows in that column (0 if none)
    tide_rows = water_zone.sum(axis=0).astype(np.float32)  # (W,)
    # Avoid division by zero for dry columns
    safe_tide = np.where(tide_rows > 0, tide_rows, 1.0)

    # weight[row, col]: gradient from 1 at top to 0 at tide line; 0 outside zone
    weight = np.where(
        water_zone,
        (1.0 - row_idx / safe_tide[np.newaxis, :]) * wd.tide_line_opacity,
        0.0,
    ).astype(np.float32)  # (H, W)

    w3 = weight[:, :, np.newaxis]  # (H, W, 1)
    stain = np.array([stain_r, stain_g, stain_b], dtype=np.float32)
    arr = arr * (1.0 - w3) + stain * w3

    result_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    return DamageResult(image=result_img, water_zone=water_zone)
