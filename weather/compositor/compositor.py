"""Compositor — manifest-driven per-folio effect stacking pipeline with
high-contrast iron-gall ink preservation, substrate-coupled micro-abrasion,
and wet-zone capillary ink dissolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image, ImageFilter

from weather.profile import WeatheringProfile
from weather.substrate.vellum import VellumStock, generate_substrate
from weather.ink.mask import extract_ink_mask
from weather.ink.aging import apply_ink_aging
from weather.damage.pipeline import apply_damage
from weather.aging import apply_aging
from weather.optics import apply_optics
from weather.substrate.noise import perlin_noise


@dataclass
class CompositorResult:
    """Output of the full compositing pipeline for one folio."""

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
    verso_page_img: Optional[Image.Image] = None,
) -> CompositorResult:
    """Run the full weathering pipeline for one folio."""
    w, h = page_img.width, page_img.height

    # 1. Substrate (+ subtle verso ink bleed-through when bound leaf reverse is provided)
    substrate = generate_substrate(w, h, stock, profile, seed=seed)
    if verso_page_img is not None:
        from weather.substrate.vellum import apply_bleedthrough
        verso_flipped = verso_page_img.transpose(Image.FLIP_LEFT_RIGHT)
        substrate = apply_bleedthrough(substrate, verso_flipped, opacity=0.030)

    # 2. Ink aging
    aged_ink = apply_ink_aging(page_img, heatmap_img, profile, seed=seed + 1)

    # 3. Blend ink into vellum fibers
    ink_mask = extract_ink_mask(page_img)
    sub_arr = np.array(substrate, dtype=np.float32)
    ink_arr = np.array(aged_ink, dtype=np.float32)
    orig_grey = np.array(page_img.convert("L"), dtype=np.float32)

    # Non-linear ink alpha curve so healthy strokes (orig_grey < 130) stay at full 1.0 opacity
    raw_alpha = np.clip((236.0 - orig_grey) / (236.0 - 115.0), 0.0, 1.0) ** 0.82
    alpha = np.where(ink_mask, np.maximum(0.94, raw_alpha), raw_alpha * 0.88)

    if min(w, h) >= 240:
        fiber_tooth = perlin_noise(w, h, scale=max(3.0, min(w, h) * 0.012), octaves=3, seed=seed + 77)
        # Healthy ink has subtle fibrous surface modulation; damaged/lacuna traces break up along vellum grain
        grain_mod = np.where(
            orig_grey > 135.0,
            np.clip(0.68 + 0.48 * fiber_tooth, 0.18, 1.05),
            np.clip(0.95 + 0.07 * fiber_tooth, 0.88, 1.02),
        )
        alpha = np.clip(alpha * grain_mod, 0.0, 1.0)

    is_flaked = ink_mask & (ink_arr.mean(axis=2) > orig_grey + 45.0)
    deep_sepia = np.clip(ink_arr * 0.56 - np.array([3.0, 6.0, 9.0], dtype=np.float32), 12.0, 255.0)
    target_ink = np.where(is_flaked[:, :, np.newaxis], sub_arr * 0.90, deep_sepia)

    eff_alpha = alpha[:, :, np.newaxis]
    blended_arr = np.clip(eff_alpha * target_ink + (1.0 - eff_alpha) * sub_arr, 0.0, 255.0).astype(np.uint8)
    blended = Image.fromarray(blended_arr, mode="RGB")

    # 4. Damage (water staining, missing corner — dispatch internal to apply_damage)
    damage_result = apply_damage(blended, folio_id, profile, seed=seed + 2)

    # 4b. Wet-zone & lacuna-zone substrate stain integration:
    #     Darken and mottle the parchment directly underneath eroded/lacuna strokes (`138 < orig_grey < 232`)
    #     so lacunae look like localized moisture/abrasion stains rather than clean cutouts.
    if min(w, h) >= 240:
        dmg_arr = np.array(damage_result.image, dtype=np.float32)
        eroded_trace = (orig_grey > 132.0) & (orig_grey < 232.0)
        if eroded_trace.any():
            trace_mask_u8 = (eroded_trace.astype(np.uint8)) * 255
            # Expand the damaged text footprint into a soft 2D moisture/abrasion patch
            stain_halo = np.array(
                Image.fromarray(trace_mask_u8, mode="L").filter(
                    ImageFilter.GaussianBlur(radius=max(6.0, min(w, h) * 0.018))
                ),
                dtype=np.float32,
            ) / 255.0
            local_mottle = perlin_noise(w, h, scale=max(4.0, min(w, h) * 0.025), octaves=2, seed=seed + 193)
            patch_weight = np.clip(stain_halo * (0.42 + 0.25 * local_mottle), 0.0, 0.48)[:, :, np.newaxis]
            stain_tone = np.array([156.0, 134.0, 98.0], dtype=np.float32)
            dmg_arr = dmg_arr * (1.0 - patch_weight) + (dmg_arr * (stain_tone / 205.0)) * patch_weight

        if damage_result.water_zone is not None:
            wet_ink = damage_result.water_zone & (orig_grey < 215.0)
            if wet_ink.any():
                feathered = np.array(
                    Image.fromarray(np.clip(dmg_arr, 0, 255).astype(np.uint8), mode="RGB").filter(
                        ImageFilter.GaussianBlur(radius=1.05)
                    ),
                    dtype=np.float32,
                )
                w_mask = wet_ink[:, :, np.newaxis]
                dmg_arr = np.where(w_mask, 0.74 * dmg_arr + 0.26 * feathered, dmg_arr)

        damage_result = CompositorResult(
            image=Image.fromarray(np.clip(dmg_arr, 0, 255).astype(np.uint8), mode="RGB"),
            folio_id=folio_id,
            water_zone=damage_result.water_zone,
            corner_mask=damage_result.corner_mask,
        )

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
