"""Water damage — 2D isotropic capillary wicking with organic coffee-ring tide lines,
codex leaf-to-leaf propagation, and recto/verso spine symmetry.
"""

from __future__ import annotations

import re
import numpy as np
from PIL import Image, ImageFilter

from weather.profile import WeatheringProfile
from weather.damage.dispatch import folio_is_water_damaged
from weather.damage.zones import DamageResult
from weather.substrate.noise import perlin_noise

_FOLIO_RE = re.compile(r"^f?(\d+)([rv])$")


def _parse_folio(folio_id: str) -> tuple[int, str]:
    m = _FOLIO_RE.match(folio_id)
    if not m:
        return (4, "r")
    return (int(m.group(1)), m.group(2))


def tide_line_mask(
    width: int,
    height: int,
    penetration: float = 0.38,
    seed: int = 0,
) -> np.ndarray:
    """Generate a smooth, lobate 2D water-zone mask without vertical comb streaks."""
    rng = np.random.default_rng(seed)

    base_row = int(height * penetration)
    x_norm = np.linspace(0.0, 1.0, width, dtype=np.float64)
    p1 = rng.uniform(0, 2 * np.pi)
    p2 = rng.uniform(0, 2 * np.pi)
    p3 = rng.uniform(0, 2 * np.pi)

    # Smooth low-frequency organic lobes (no per-column high-frequency jitter!)
    lobe = (
        0.58 * np.sin(2.0 * np.pi * 1.15 * x_norm + p1)
        + 0.28 * np.cos(2.0 * np.pi * 2.40 * x_norm + p2)
        + 0.14 * np.sin(2.0 * np.pi * 4.20 * x_norm + p3)
    )
    if lobe.std() > 0:
        lobe = (lobe - lobe.mean()) / lobe.std()

    max_dev = height * 0.09
    tide_row = np.clip(np.round(base_row + lobe * max_dev).astype(int), 1, height - 1)

    row_grid = np.arange(height)[:, np.newaxis]
    mask = row_grid < tide_row[np.newaxis, :]
    return mask


def apply_water_damage(
    img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
    seed: int = 0,
) -> DamageResult:
    """Apply codex-coherent 2D capillary water staining and organic tide-line rings.

    Uses a 2D scalar moisture field (vertical penetration + 2D multi-scale Perlin
    noise) rather than column-indexed `tide_rows[col]` division, completely
    eliminating vertical streaks and comb artifacts.
    """
    if not folio_is_water_damaged(folio_id):
        return DamageResult(image=img.copy(), water_zone=None)

    w, h = img.size
    arr = np.array(img.convert("RGB"), dtype=np.float32)
    wd = profile.damage_water

    leaf_num, side = _parse_folio(folio_id)
    if leaf_num == 4:
        severity = 1.0 if side == "r" else 0.88
    elif leaf_num == 5:
        severity = 0.62 if side == "r" else 0.48
    else:
        severity = 0.75

    eff_penetration = max(0.18, wd.penetration * (0.76 + 0.28 * severity))

    # Shared codex water seed so the stain contour propagates coherently across leaves
    codex_water_seed = 404 + (seed % 997)
    base_mask = tide_line_mask(w, h, penetration=eff_penetration, seed=codex_water_seed)
    if side == "v":
        water_zone = np.fliplr(base_mask)
    else:
        water_zone = base_mask

    # Construct a smooth 2D moisture scalar field M(y, x) free of 1D column streaks:
    # Start from a Gaussian-blurred version of water_zone + 2D Perlin perturbations
    mask_u8 = (water_zone.astype(np.uint8)) * 255
    blur_r = max(3.0, min(w, h) * 0.045)
    soft_field = np.array(
        Image.fromarray(mask_u8, mode="L").filter(ImageFilter.GaussianBlur(radius=blur_r)),
        dtype=np.float32,
    ) / 255.0

    min_dim = float(max(16, min(w, h)))
    mottle_coarse = perlin_noise(w, h, scale=max(10.0, min_dim * 0.16), octaves=3, seed=codex_water_seed + 19)
    mottle_fine = perlin_noise(w, h, scale=max(4.0, min_dim * 0.04), octaves=3, seed=codex_water_seed + 43)
    if side == "v":
        mottle_coarse = np.fliplr(mottle_coarse)
        mottle_fine = np.fliplr(mottle_fine)

    # Perturb the 2D moisture potential with isotropic 2D noise
    moisture = np.clip(soft_field + 0.14 * mottle_coarse * soft_field + 0.06 * mottle_fine * soft_field, 0.0, 1.0)
    top_grad = np.clip(1.0 - (np.arange(h, dtype=np.float32)[:, np.newaxis] / max(1.0, h * eff_penetration * 1.25)), 0.0, 1.0)

    # Capillary coffee-ring forms along the 2D contour where soft_field ≈ 0.42
    contour_val = soft_field + 0.08 * mottle_coarse + 0.03 * mottle_fine
    ring_band = np.exp(-((contour_val - 0.44) / 0.11) ** 2) * (0.75 + 0.35 * np.abs(mottle_fine))
    secondary_ring = np.exp(-((contour_val - 0.72) / 0.09) ** 2) * (0.45 + 0.30 * np.abs(mottle_coarse))

    interior_weight = (0.55 * moisture + 0.45 * top_grad * moisture) * (0.82 + 0.25 * mottle_coarse)
    total_weight = np.clip(
        (0.68 * interior_weight + 0.55 * ring_band + 0.24 * secondary_ring) * wd.tide_line_opacity * severity,
        0.0,
        0.84,
    )[:, :, np.newaxis]

    stain_base = np.array(wd.stain_color, dtype=np.float32) - np.array([20.0, 26.0, 36.0], dtype=np.float32)
    ring_color = np.clip(stain_base - np.array([30.0, 32.0, 30.0], dtype=np.float32), 38.0, 255.0)
    ring_mix = np.clip((ring_band + 0.45 * secondary_ring)[:, :, np.newaxis] * 0.78, 0.0, 1.0)
    local_stain_rgb = stain_base[None, None, :] * (1.0 - ring_mix) + ring_color[None, None, :] * ring_mix

    absorb_target = arr * (local_stain_rgb / 208.0)
    arr = arr * (1.0 - total_weight) + (0.62 * absorb_target + 0.38 * local_stain_rgb) * total_weight

    result_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    return DamageResult(image=result_img, water_zone=water_zone)
