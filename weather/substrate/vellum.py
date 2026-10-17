"""Vellum substrate generation — authentic calfskin (*Kalbspergament*) model with
non-stationary anatomical hide zones (crupper vs. flank), Gregory's Rule hair-side vs.
flesh-side distinction, lunellum scraping arcs, collagen vein tracts, and recto/verso bleed-through.

Public API:
    VellumStock          — enum: STANDARD, IRREGULAR
    VellumSide           — enum: HAIR, FLESH
    stock_for_folio()    — map folio ID to VellumStock
    side_for_folio()     — map folio ID to VellumSide (Gregory's Rule: hair-to-hair, flesh-to-flesh)
    generate_substrate() — produce PIL Image for a given folio/stock
    apply_bleedthrough() — composite verso page at low opacity onto substrate
"""

from __future__ import annotations

import math
import re
from enum import Enum

import numpy as np
from PIL import Image, ImageFilter

from weather.profile import WeatheringProfile
from weather.substrate.noise import perlin_noise
from weather.substrate.follicles import follicle_marks


class VellumStock(Enum):
    """Two vellum stocks present in MS Erfurt Aug. 12°47."""
    STANDARD = "standard"    # f01–f13: selected Thuringian/Bavarian calfskin parchment
    IRREGULAR = "irregular"  # f14–f17: darker, rougher remnant hide cut from an offcut sheet


class VellumSide(Enum):
    """Hair side (*Haarseite*) vs. Flesh side (*Fleischseite*) of the calfskin leaf."""
    HAIR = "hair"
    FLESH = "flesh"


_FOLIO_RE = re.compile(r"^f?(\d+)([rv])$")


def stock_for_folio(folio_id: str) -> VellumStock:
    """Return the VellumStock for a given folio ID.

    f01–f13 → STANDARD (calfskin); f14–f17 → IRREGULAR (remnant offcut).
    """
    m = _FOLIO_RE.match(folio_id)
    num = int(m.group(1)) if m else 1
    return VellumStock.IRREGULAR if num >= 14 else VellumStock.STANDARD


def side_for_folio(folio_id: str) -> VellumSide:
    """Return Hair or Flesh side under Gregory's Rule (facing pages match in the quire).

    - f01r: HAIR (outermost recto)
    - f01v | f02r: FLESH facing FLESH
    - f02v | f03r: HAIR facing HAIR
    - f03v | f04r: FLESH facing FLESH
    - f04v | f05r: HAIR facing HAIR
    - f05v | f06r: FLESH facing FLESH
    """
    m = _FOLIO_RE.match(folio_id)
    if not m:
        return VellumSide.HAIR
    leaf = int(m.group(1))
    rv = m.group(2)
    # Odd leaves have Hair on recto, Flesh on verso; Even leaves have Flesh on recto, Hair on verso
    if leaf % 2 == 1:
        return VellumSide.HAIR if rv == "r" else VellumSide.FLESH
    return VellumSide.FLESH if rv == "r" else VellumSide.HAIR


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
    folio_id: str | None = None,
) -> Image.Image:
    """Generate a non-uniform 560-year-old calfskin vellum substrate as an RGB PIL Image.

    Models:
      1. Gregory's Rule Hair-side vs. Flesh-side base tone & pore/scraping characteristics
      2. Non-stationary anatomical hide topography (opaque chalky crupper/back vs.
         warmer, slightly translucent gelatinous flank/belly zones)
      3. Sweeping *lunellum* (half-moon knife) scraping striae & dermal stretch tension lines
      4. Branching subcutaneous collagen/vein ridges (via ridged multifractal noise)
      5. Multi-scale dermal grain, mineral grit, and clustered calfskin hair-follicle pores
    """
    sp = (profile.substrate_standard
          if stock == VellumStock.STANDARD
          else profile.substrate_irregular)

    v_side = side_for_folio(folio_id) if folio_id else (VellumSide.HAIR if (seed % 2 == 0) else VellumSide.FLESH)

    # Hair side is slightly warmer/ochre (+3 R, -4 B); Flesh side is slightly chalkier/creamier
    # Keep the clean interior bright warm calfskin ([215, 202, 175], matching the AI reference!)
    side_r_shift = +2.5 if v_side == VellumSide.HAIR else -1.5
    side_b_shift = -4.0 if v_side == VellumSide.HAIR else +2.0

    base_r = float(sp.color_base[0]) - 18.0 + side_r_shift
    base_g = float(sp.color_base[1]) - 19.0
    base_b = float(sp.color_base[2]) - 16.0 + side_b_shift

    roughness = float(sp.texture_roughness)
    min_dim = float(max(16, min(width, height)))
    rng = np.random.default_rng(seed + 307)

    # --- 1. Non-Stationary Anatomical Hide Patches (Localized Flank Blotches vs. Clean Crupper) ---
    # Instead of darkening the entire page uniformly, real calfskin has a mostly clean, warm-cream
    # central crupper/back region with localized, irregular darker amber/ochre patches near the flanks.
    macro_warp_field = _domain_warped_fbm(
        width, height, base_scale=max(14.0, min_dim * 0.28), warp_strength=max(3.0, min_dim * 0.08), seed=seed + 5
    )
    # Thresholded patch map: 65% of the interior remains bright & clean (~0), while 35% forms irregular darker hide patches
    anatomy_patch = np.clip((macro_warp_field - 0.08) * 2.2, 0.0, 1.0) ** 1.35
    anatomy_zone = anatomy_patch - 0.22

    # --- 2. Macro & Mesoscale Domain-Warped Collagen Mottling ---
    macro_scale = max(12.0, min_dim * (0.30 if stock == VellumStock.STANDARD else 0.22))
    macro_warp = max(2.0, min_dim * 0.09)
    macro_cloud = _domain_warped_fbm(width, height, base_scale=macro_scale, warp_strength=macro_warp, seed=seed)

    meso_scale = max(5.0, min_dim * 0.055)
    meso_mottle = _domain_warped_fbm(
        width, height, base_scale=meso_scale, warp_strength=max(1.5, min_dim * 0.03), seed=seed + 101
    )

    # --- 3. Subcutaneous Collagen Vein Tracts & Lunellum Scraping Arcs ---
    vein_raw = perlin_noise(width, height, scale=max(8.0, min_dim * 0.18), octaves=3, seed=seed + 131)
    # Ridged noise: narrow branching tracts where |vein_raw| is near 0
    vein_ridge = np.exp(-((vein_raw / 0.11) ** 2)) * (0.4 + 0.6 * np.clip(anatomy_zone + 0.5, 0.0, 1.0))

    # Curved lunellum scraping striae (stronger on flesh side)
    yg = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, np.newaxis]
    xg = np.linspace(0.0, 1.0, width, dtype=np.float32)[np.newaxis, :]
    arc_coord = (xg - float(rng.uniform(-0.3, 1.3))) ** 2 + (yg - float(rng.uniform(-0.3, 1.3))) ** 2
    scrape_wave = np.sin(arc_coord * 42.0 + 3.5 * macro_warp_field) * (1.2 if v_side == VellumSide.FLESH else 0.65)

    # --- 4. Medium-Fine Dermal Grain & Fibrous Striae ---
    dermal_scale = max(3.0, min_dim * 0.016)
    dermal_noise = _domain_warped_fbm(
        width, height, base_scale=dermal_scale, warp_strength=max(1.0, min_dim * 0.01), seed=seed + 157
    )
    fine_scale = max(2.0, min_dim * 0.0055)
    fine_noise = perlin_noise(width, height, scale=fine_scale, octaves=2, persistence=0.65, seed=seed + 211)

    # Spatial modulation: grain amplitude is 35% stronger in the flank zone than in the smooth crupper zone
    local_rough_mod = 0.85 + 0.32 * anatomy_zone

    # --- 5. Tactile Parchment Tooth + Multi-Pixel Mineral/Chalk Inclusions ---
    micro_raw = rng.normal(0.0, 1.0, size=(height, width)).astype(np.float32)
    fleck_draw = rng.uniform(0.0, 1.0, size=(height, width))
    flecks = np.where(fleck_draw < 0.022, -rng.uniform(22.0, 48.0, size=(height, width)), 0.0)
    flecks = np.where(fleck_draw > 0.984, +rng.uniform(14.0, 28.0, size=(height, width)), flecks).astype(np.float32)

    if min_dim >= 48:
        fleck_img = Image.fromarray(np.clip(flecks + 128.0, 0, 255).astype(np.uint8), mode="L")
        fleck_soft = np.array(fleck_img.filter(ImageFilter.GaussianBlur(radius=1.15)), dtype=np.float32) - 128.0
        micro_img = Image.fromarray(np.clip((micro_raw * 32.0) + 128.0, 0, 255).astype(np.uint8), mode="L")
        micro_blur = np.array(micro_img.filter(ImageFilter.GaussianBlur(radius=1.1)), dtype=np.float32) - 128.0
        micro_grain = (0.45 * (micro_raw * 8.2) + 0.55 * (micro_blur * 0.65) + 0.55 * flecks + 1.15 * fleck_soft) * local_rough_mod
    else:
        micro_grain = (micro_raw * 6.0 + flecks * 0.5) * local_rough_mod

    amp_macro = (48.0 if stock == VellumStock.STANDARD else 58.0) * roughness
    amp_meso = (46.0 if stock == VellumStock.STANDARD else 56.0) * roughness
    amp_dermal = (36.0 if stock == VellumStock.STANDARD else 44.0) * roughness
    amp_fine = (26.0 if stock == VellumStock.STANDARD else 32.0) * roughness

    tonal = (
        -11.5 * anatomy_zone  # Flank zone is naturally darker/more translucent than chalky back zone
        + macro_cloud * amp_macro
        + meso_mottle * amp_meso * local_rough_mod
        + dermal_noise * amp_dermal * local_rough_mod
        + fine_noise * amp_fine
        - 6.5 * vein_ridge
        + 2.8 * scrape_wave
        + micro_grain * (1.02 + 0.75 * roughness)
    )

    color_var = perlin_noise(width, height, scale=max(7.0, meso_scale * 0.95), octaves=3, seed=seed + 401)
    cv_amp = float(sp.color_variation) * 58.0

    # Translucent flank zones shift warmer/amber (larger drop in Blue than Red)
    r = np.clip(base_r + tonal * 0.88 + color_var * cv_amp + 3.5 * anatomy_zone, 0, 255)
    g = np.clip(base_g + tonal * 1.02 + color_var * (cv_amp * 0.40) - 1.0 * anatomy_zone, 0, 255)
    b = np.clip(base_b + tonal * 1.25 - color_var * (cv_amp * 0.78) - 8.5 * anatomy_zone, 0, 255)

    img_arr = np.stack([r, g, b], axis=2)

    # --- 6. Clustered Calfskin Hair-Follicle Pores (denser on Hair side & Flank zones) ---
    base_density = 0.00048 if stock == VellumStock.STANDARD else 0.00082
    if v_side == VellumSide.FLESH:
        base_density *= 0.45
    marks = follicle_marks(width, height, density=base_density, grain_angle_deg=15.0, seed=seed + 2)
    marks_f = marks.astype(np.float32) * (0.32 if v_side == VellumSide.HAIR else 0.18) * np.clip(0.75 + 0.55 * anatomy_zone, 0.4, 1.4)
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
