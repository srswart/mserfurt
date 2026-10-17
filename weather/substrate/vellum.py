"""Vellum substrate generation — multi-scale domain-warped collagen mottling,
anisotropic hide fibers, clustered hair-follicle pores, and recto/verso bleed-through.

Public API:
    VellumStock          — enum: STANDARD, IRREGULAR
    stock_for_folio()    — map folio ID to VellumStock
    generate_substrate() — produce PIL Image for a given folio/stock
    apply_bleedthrough() — composite verso page at low opacity onto substrate
"""

from __future__ import annotations

import re
from enum import Enum

import numpy as np
from PIL import Image, ImageFilter

from weather.profile import WeatheringProfile
from weather.substrate.noise import perlin_noise
from weather.substrate.follicles import follicle_marks


class VellumStock(Enum):
    """Two vellum stocks present in MS Erfurt Aug. 12°47."""
    STANDARD = "standard"    # f01–f13: warm aged calfskin parchment
    IRREGULAR = "irregular"  # f14–f17: darker, rougher remnant hide


_FOLIO_RE = re.compile(r"^f?(\d+)[rv]$")


def stock_for_folio(folio_id: str) -> VellumStock:
    """Return the VellumStock for a given folio ID.

    f01–f13 → STANDARD; f14–f17 → IRREGULAR.
    """
    m = _FOLIO_RE.match(folio_id)
    num = int(m.group(1)) if m else 1
    return VellumStock.IRREGULAR if num >= 14 else VellumStock.STANDARD


def _domain_warped_fbm(
    width: int,
    height: int,
    base_scale: float,
    warp_strength: float,
    seed: int,
) -> np.ndarray:
    """Compute 2D domain-warped fractional Brownian motion for organic vellum mottling."""
    n_base = perlin_noise(width, height, scale=base_scale, octaves=4, persistence=0.62, seed=seed)
    warp_x = perlin_noise(width, height, scale=max(4.0, base_scale * 0.60), octaves=3, seed=seed + 11)
    warp_y = perlin_noise(width, height, scale=max(4.0, base_scale * 0.60), octaves=3, seed=seed + 23)

    yg, xg = np.meshgrid(np.arange(height), np.arange(width), indexing="ij")
    xs = np.clip(np.round(xg + warp_x * warp_strength).astype(np.int32), 0, width - 1)
    ys = np.clip(np.round(yg + warp_y * warp_strength).astype(np.int32), 0, height - 1)
    warped = n_base[ys, xs]

    turb = np.abs(perlin_noise(width, height, scale=max(3.0, base_scale * 0.35), octaves=3, seed=seed + 37))
    return 0.66 * warped - 0.34 * (turb - 0.42)


def generate_substrate(
    width: int,
    height: int,
    stock: VellumStock,
    profile: WeatheringProfile,
    seed: int = 0,
) -> Image.Image:
    """Generate a realistic 560-year-old vellum substrate texture as an RGB PIL Image.

    Calibrated directly to the multi-scale texture spectrum of the target reference:
      - High-frequency organic calfskin grain, pores & mineral grit (`std ≈ 13–15` at display scale)
      - Medium-frequency collagen mottling & chalk preparation clouds (`std ≈ 13–15` at display scale)
      - Macro thickness & age-patina undulation
    """
    sp = (profile.substrate_standard
          if stock == VellumStock.STANDARD
          else profile.substrate_irregular)

    base_r = float(sp.color_base[0]) - 28.0
    base_g = float(sp.color_base[1]) - 31.0
    base_b = float(sp.color_base[2]) - 33.0

    roughness = float(sp.texture_roughness)
    min_dim = float(max(16, min(width, height)))

    # 1. Macro domain-warped hide thickness & translucency clouds
    macro_scale = max(12.0, min_dim * (0.30 if stock == VellumStock.STANDARD else 0.22))
    macro_warp = max(2.0, min_dim * 0.09)
    macro_cloud = _domain_warped_fbm(width, height, base_scale=macro_scale, warp_strength=macro_warp, seed=seed)

    # 2. Mesoscale preparation mottling (survives 2x downsampling with strong visual grit)
    meso_scale = max(5.0, min_dim * 0.055)
    meso_mottle = _domain_warped_fbm(
        width, height, base_scale=meso_scale, warp_strength=max(1.5, min_dim * 0.03), seed=seed + 101
    )

    # 3. Medium-fine dermal grain (scale ~ 6-14px so it remains crisp at any viewing zoom)
    dermal_scale = max(3.0, min_dim * 0.016)
    dermal_noise = _domain_warped_fbm(
        width, height, base_scale=dermal_scale, warp_strength=max(1.0, min_dim * 0.01), seed=seed + 157
    )

    # 4. Fine collagen fiber & pumice striae (scale ~ 3-5px)
    fine_scale = max(2.0, min_dim * 0.0055)
    fine_noise = perlin_noise(width, height, scale=fine_scale, octaves=2, persistence=0.65, seed=seed + 211)

    # 5. Tactile parchment tooth + multi-pixel mineral/hide inclusions (survives Lanczos resize)
    rng = np.random.default_rng(seed + 307)
    micro_raw = rng.normal(0.0, 1.0, size=(height, width)).astype(np.float32)
    fleck_draw = rng.uniform(0.0, 1.0, size=(height, width))
    flecks = np.where(fleck_draw < 0.022, -rng.uniform(22.0, 48.0, size=(height, width)), 0.0)
    flecks = np.where(fleck_draw > 0.985, +rng.uniform(12.0, 26.0, size=(height, width)), flecks).astype(np.float32)

    if min_dim >= 48:
        fleck_img = Image.fromarray(np.clip(flecks + 128.0, 0, 255).astype(np.uint8), mode="L")
        # 1.2px blur spreads mineral flecks to 2-3px so they remain visible when downsampled
        fleck_soft = np.array(fleck_img.filter(ImageFilter.GaussianBlur(radius=1.15)), dtype=np.float32) - 128.0
        micro_img = Image.fromarray(np.clip((micro_raw * 32.0) + 128.0, 0, 255).astype(np.uint8), mode="L")
        micro_blur = np.array(micro_img.filter(ImageFilter.GaussianBlur(radius=1.1)), dtype=np.float32) - 128.0
        micro_grain = 0.45 * (micro_raw * 8.5) + 0.55 * (micro_blur * 0.65) + 0.55 * flecks + 1.15 * fleck_soft
    else:
        micro_grain = micro_raw * 6.0 + flecks * 0.5

    amp_macro = (48.0 if stock == VellumStock.STANDARD else 58.0) * roughness
    amp_meso = (46.0 if stock == VellumStock.STANDARD else 56.0) * roughness
    amp_dermal = (36.0 if stock == VellumStock.STANDARD else 44.0) * roughness
    amp_fine = (28.0 if stock == VellumStock.STANDARD else 34.0) * roughness

    tonal = (
        macro_cloud * amp_macro
        + meso_mottle * amp_meso
        + dermal_noise * amp_dermal
        + fine_noise * amp_fine
        + micro_grain * (1.05 + 0.75 * roughness)
    )

    color_var = perlin_noise(width, height, scale=max(7.0, meso_scale * 0.95), octaves=3, seed=seed + 401)
    cv_amp = float(sp.color_variation) * 56.0

    r = np.clip(base_r + tonal * 0.90 + color_var * cv_amp, 0, 255)
    g = np.clip(base_g + tonal * 1.02 + color_var * (cv_amp * 0.42), 0, 255)
    b = np.clip(base_b + tonal * 1.24 - color_var * (cv_amp * 0.76), 0, 255)

    img_arr = np.stack([r, g, b], axis=2)

    # 6. Clustered hair-follicle pores
    mark_density = 0.00042 if stock == VellumStock.STANDARD else 0.00075
    marks = follicle_marks(width, height, density=mark_density, grain_angle_deg=15.0, seed=seed + 2)
    marks_f = marks.astype(np.float32) * 0.28
    img_arr[:, :, 0] = np.clip(img_arr[:, :, 0] - marks_f * 0.85, 0, 255)
    img_arr[:, :, 1] = np.clip(img_arr[:, :, 1] - marks_f * 1.02, 0, 255)
    img_arr[:, :, 2] = np.clip(img_arr[:, :, 2] - marks_f * 1.20, 0, 255)

    return Image.fromarray(img_arr.astype(np.uint8), mode="RGB")


def apply_bleedthrough(
    substrate: Image.Image,
    verso: Image.Image,
    opacity: float = 0.06,
) -> Image.Image:
    """Composite a verso page image onto the substrate at low opacity."""
    if opacity <= 0.0:
        return substrate.copy()

    sub_arr = np.array(substrate.convert("RGB"), dtype=np.float32)
    verso_resized = verso.convert("RGB").resize((substrate.width, substrate.height), Image.LANCZOS)
    if min(substrate.width, substrate.height) >= 64:
        verso_resized = verso_resized.filter(ImageFilter.GaussianBlur(radius=1.4))
    verso_arr = np.array(verso_resized, dtype=np.float32)

    blended = sub_arr * (1.0 - opacity) + verso_arr * opacity
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8), mode="RGB")
