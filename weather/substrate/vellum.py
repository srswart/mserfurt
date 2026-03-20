"""Vellum substrate generation — stock selection, texture, bleed-through.

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
from PIL import Image

from weather.profile import WeatheringProfile
from weather.substrate.noise import perlin_noise
from weather.substrate.follicles import follicle_marks


class VellumStock(Enum):
    """Two vellum stocks present in MS Erfurt Aug. 12°47."""
    STANDARD = "standard"    # f01–f13: warm cream, smoother
    IRREGULAR = "irregular"  # f14–f17: yellow-shifted, rougher


_FOLIO_RE = re.compile(r"^f?(\d+)[rv]$")


def stock_for_folio(folio_id: str) -> VellumStock:
    """Return the VellumStock for a given folio ID.

    f01–f13 → STANDARD; f14–f17 → IRREGULAR.
    """
    m = _FOLIO_RE.match(folio_id)
    num = int(m.group(1)) if m else 1
    return VellumStock.IRREGULAR if num >= 14 else VellumStock.STANDARD


def generate_substrate(
    width: int,
    height: int,
    stock: VellumStock,
    profile: WeatheringProfile,
    seed: int = 0,
) -> Image.Image:
    """Generate a vellum substrate texture as an RGB PIL Image.

    Compositing pipeline:
      1. Fill with stock base colour from profile
      2. Apply multi-octave Perlin noise as a tonal modulation
      3. Overlay follicle marks as subtle darkening
      4. Apply colour-variation noise pass (slight spatial hue drift)

    Args:
        width:   Output width in pixels.
        height:  Output height in pixels.
        stock:   VellumStock (STANDARD or IRREGULAR).
        profile: WeatheringProfile from load_profile().
        seed:    RNG seed; same seed → identical output.

    Returns:
        RGB PIL Image of shape (width, height).
    """
    sp = (profile.substrate_standard
          if stock == VellumStock.STANDARD
          else profile.substrate_irregular)

    base_r, base_g, base_b = sp.color_base

    # --- Perlin tonal noise (modulates lightness) ---
    roughness = sp.texture_roughness
    scale = max(8.0, 256.0 * (1.0 - roughness))   # rougher → smaller scale
    tonal = perlin_noise(width, height, scale=scale, octaves=3, seed=seed)
    # Map [-1, 1] → [-amplitude, +amplitude] brightness shift
    amplitude = roughness * 30.0
    tonal_shift = (tonal * amplitude).astype(np.int16)

    # --- Colour-variation noise (slight hue drift) ---
    var_scale = max(16.0, scale * 1.5)
    color_var = perlin_noise(width, height, scale=var_scale, octaves=2,
                             seed=seed + 1)
    cv_amplitude = sp.color_variation * 15.0

    # --- Build RGB arrays ---
    r = np.clip(base_r + tonal_shift + (color_var * cv_amplitude).astype(np.int16),
                0, 255).astype(np.uint8)
    g = np.clip(base_g + tonal_shift, 0, 255).astype(np.uint8)
    b = np.clip(base_b + tonal_shift - (color_var * cv_amplitude * 0.5
                                         ).astype(np.int16),
                0, 255).astype(np.uint8)

    img_arr = np.stack([r, g, b], axis=2)
    img = Image.fromarray(img_arr, mode="RGB")

    # --- Follicle marks (subtle darkening) ---
    mark_density = 0.0008 if stock == VellumStock.STANDARD else 0.0015
    marks = follicle_marks(width, height, density=mark_density,
                           grain_angle_deg=15.0, seed=seed + 2)
    # Darken pixels where marks exist (subtract intensity / 3)
    marks_arr = marks.astype(np.int16) // 3
    img_arr2 = np.array(img, dtype=np.int16)
    img_arr2[:, :, 0] = np.clip(img_arr2[:, :, 0] - marks_arr, 0, 255)
    img_arr2[:, :, 1] = np.clip(img_arr2[:, :, 1] - marks_arr, 0, 255)
    img_arr2[:, :, 2] = np.clip(img_arr2[:, :, 2] - marks_arr, 0, 255)

    return Image.fromarray(img_arr2.astype(np.uint8), mode="RGB")


def apply_bleedthrough(
    substrate: Image.Image,
    verso: Image.Image,
    opacity: float = 0.06,
) -> Image.Image:
    """Composite a verso page image onto the substrate at low opacity.

    Simulates vellum translucency where ink on the reverse side shows
    faintly through the parchment.

    Args:
        substrate: RGB PIL Image (the current recto substrate).
        verso:     RGB PIL Image of the verso page (same dimensions).
        opacity:   Blending weight of the verso image (0.0 = no bleed).

    Returns:
        New RGB PIL Image with verso blended in.
    """
    if opacity <= 0.0:
        return substrate.copy()

    sub_arr = np.array(substrate.convert("RGB"), dtype=np.float32)
    verso_arr = np.array(verso.convert("RGB").resize(
        (substrate.width, substrate.height), Image.LANCZOS
    ), dtype=np.float32)

    blended = sub_arr * (1.0 - opacity) + verso_arr * opacity
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8), mode="RGB")
