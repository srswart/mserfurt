"""Compositor — manifest-driven per-folio effect stacking pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile
from weather.substrate.vellum import VellumStock, generate_substrate
from weather.ink.mask import extract_ink_mask
from weather.ink.aging import apply_ink_aging
from weather.damage.pipeline import apply_damage
from weather.aging import apply_aging
from weather.optics import apply_optics


@dataclass
class CompositorResult:
    """Output of the full compositing pipeline for one folio.

    Attributes:
        image:           Final RGB PIL Image (substrate + ink + damage + aging + optics).
        folio_id:        Folio identifier, e.g. "f04v".
        curl_transform:  Float32 displacement array (H, W, 2) from page_curl,
                         or None if page_curl is disabled.
        water_zone:      Bool array (H, W); True = water-affected pixel.  None if no damage.
        corner_mask:     Bool array (H, W); True = missing corner pixel.  None if no damage.
    """

    image: Image.Image
    folio_id: str
    curl_transform: Optional[np.ndarray] = None
    water_zone: Optional[np.ndarray] = None
    corner_mask: Optional[np.ndarray] = None


def composite_folio(
    page_img: Image.Image,
    heatmap_img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
    stock: VellumStock = VellumStock.STANDARD,
    seed: int = 0,
) -> CompositorResult:
    """Run the full weathering pipeline for one folio.

    Layer order (strict):
      1. Substrate  — generate vellum texture as background
      2. Ink aging  — apply fade / bleed / flake to ScribeSim ink
      3. Blend      — composite aged ink over substrate using ink mask
      4. Damage     — water staining and/or missing corner (folio-dependent)
      5. Aging      — edge darkening, foxing, binding shadow (universal)
      6. Optics     — page curl warp, camera vignette, lighting gradient

    Args:
        page_img:    RGB PIL Image from ScribeSim (white background + ink).
        heatmap_img: Grayscale PIL Image (pressure heatmap from ScribeSim).
        folio_id:    Folio identifier, e.g. "f04v".
        profile:     WeatheringProfile.
        stock:       VellumStock to use for substrate generation.
        seed:        Base RNG seed (each layer increments by 1).

    Returns:
        CompositorResult with the fully composited image and optional transform.
    """
    w, h = page_img.width, page_img.height

    # 1. Substrate
    substrate = generate_substrate(w, h, stock, profile, seed=seed)

    # 2. Ink aging
    aged_ink = apply_ink_aging(page_img, heatmap_img, profile, seed=seed + 1)

    # 3. Blend ink over substrate
    #    Extract ink mask from *original* page (pre-fade, reliable threshold)
    ink_mask = extract_ink_mask(page_img)
    sub_arr = np.array(substrate, dtype=np.uint8)
    ink_arr = np.array(aged_ink, dtype=np.uint8)
    mask3 = ink_mask[:, :, np.newaxis]
    blended_arr = np.where(mask3, ink_arr, sub_arr).astype(np.uint8)
    blended = Image.fromarray(blended_arr, mode="RGB")

    # 4. Damage (water staining, missing corner — dispatch internal to apply_damage)
    damage_result = apply_damage(blended, folio_id, profile, seed=seed + 2)

    # 5. Aging (edge darkening, foxing, binding shadow — applied to all folios)
    aged = apply_aging(damage_result.image, folio_id, profile, seed=seed + 3)

    # 6. Optics (page curl, vignette, lighting gradient)
    optics_result = apply_optics(aged, folio_id, profile, seed=seed + 4)

    return CompositorResult(
        image=optics_result.image,
        folio_id=folio_id,
        curl_transform=optics_result.curl_transform,
        water_zone=damage_result.water_zone,
        corner_mask=damage_result.corner_mask,
    )
