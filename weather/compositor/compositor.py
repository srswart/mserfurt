"""Compositor — manifest-driven per-folio effect stacking pipeline with
calfskin vellum side/anatomy awareness, intra-letter brownish iron-gall ink
variegation, quill-dip cycle preservation, and wet-zone capillary dissolution.
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
    """Run the full weathering pipeline for one folio.

    Layer order (strict):
      1. Substrate  — generate calfskin vellum texture (with Gregory's Rule hair/flesh side,
                      anatomical hide zones, and optional verso bleed-through)
      2. Ink aging  — apply iron-gall brown oxidation shift, micro-bleed, and pressure flaking
      3. Blend      — composite aged ink into vellum fibers with intra-letter / intra-word
                      brownish pigment variegation (deep roasted umber at pooled nib turns vs.
                      warm rust-sienna/ochre on mid-strokes, hairlines, and pre-dip words)
      4. Damage     — water staining + wet-zone capillary ink dissolution + missing corner
      5. Aging      — organic edge darkening/handling lobes, foxing, binding shadow
      6. Optics     — page curl warp, subtle vignette, lighting gradient
    """
    w, h = page_img.width, page_img.height

    # 1. Substrate (+ subtle verso ink bleed-through when bound leaf reverse is provided)
    substrate = generate_substrate(w, h, stock, profile, seed=seed, folio_id=folio_id)
    if verso_page_img is not None:
        from weather.substrate.vellum import apply_bleedthrough
        verso_flipped = verso_page_img.transpose(Image.FLIP_LEFT_RIGHT)
        substrate = apply_bleedthrough(substrate, verso_flipped, opacity=0.030)

    # 2. Ink aging
    aged_ink = apply_ink_aging(page_img, heatmap_img, profile, seed=seed + 1)

    # 3. Blend ink into vellum fibers with intra-letter & intra-word brown iron-gall physics
    ink_mask = extract_ink_mask(page_img)
    sub_arr = np.array(substrate, dtype=np.float32)
    ink_arr = np.array(aged_ink, dtype=np.float32)
    orig_grey = np.array(page_img.convert("L"), dtype=np.float32)
    heat_arr = np.array(
        heatmap_img.convert("L").resize((w, h), Image.NEAREST),
        dtype=np.float32,
    ) / 255.0

    # Preserve the scribe's quill-dip darkness cycle AND intra-letter darkness variation!
    # Do NOT clamp ink_mask to 0.94 — let raw_alpha reflect whether the quill was freshly dipped
    # (orig_grey ~ 40 -> alpha ~ 0.96) or running low before a dip (orig_grey ~ 95 -> alpha ~ 0.72).
    raw_alpha = np.clip((236.0 - orig_grey) / (236.0 - 38.0), 0.0, 1.0)
    alpha = np.where(ink_mask, np.clip(raw_alpha * 1.04, 0.15, 0.98), raw_alpha * 0.86)

    if min(w, h) >= 240:
        # Multi-scale sub-stroke granulation & calfskin fiber abrasion:
        #   - fine_gran (scale ~ 2.4px) creates intra-letter pigment flocculation & stroke-interior mottling
        #   - word_gran (scale ~ 9.5px) creates intra-word uneven tannin oxidation across adjacent letters
        fine_gran = perlin_noise(w, h, scale=2.4, octaves=2, seed=seed + 77)
        word_gran = perlin_noise(w, h, scale=9.5, octaves=2, seed=seed + 113)
        sub_stroke_mod = 0.58 * fine_gran + 0.42 * word_gran

        # Modulate ink alpha within every letter so no stroke is a flat digital paint fill
        alpha_mod = np.where(
            orig_grey > 130.0,
            np.clip(0.72 + 0.44 * sub_stroke_mod, 0.20, 1.06),
            np.clip(0.88 + 0.22 * sub_stroke_mod, 0.68, 1.05),
        )
        alpha = np.clip(alpha * alpha_mod, 0.0, 0.98)
    else:
        sub_stroke_mod = np.zeros((h, w), dtype=np.float32)

    # Compute local iron-gall ink film thickness `film_t` in [0, 1]:
    # High at pooled nib turns, diamond feet, and post-dip downstroke cores;
    # Lower on fast mid-stems, stroke edges, 40° hairlines, and pre-dip words.
    film_t = np.clip(
        0.48 * raw_alpha + 0.40 * heat_arr + 0.22 * sub_stroke_mod,
        0.0,
        1.0,
    )[:, :, np.newaxis]

    # Two-pole iron-gall brown palette:
    #   - Pooled thick core ink (`film_t -> 1.0`): deep roasted bistre/umber [34, 20, 9]
    #   - Thin/oxidized ink (`film_t -> 0.0`): warm rust-sienna / golden-ochre brown [142, 90, 44]
    deep_umber = np.array([34.0, 20.0, 9.0], dtype=np.float32)
    warm_sienna = np.array([142.0, 90.0, 44.0], dtype=np.float32)
    brown_ink_rgb = warm_sienna[None, None, :] * (1.0 - film_t ** 1.25) + deep_umber[None, None, :] * (film_t ** 1.25)

    # Blend 15% of `ink_arr` so upstream ink_aging / ink_flake deltas remain active
    brown_ink_rgb = 0.85 * brown_ink_rgb + 0.15 * (ink_arr * 0.65)

    is_flaked = ink_mask & (ink_arr.mean(axis=2) > orig_grey + 42.0)
    target_ink = np.where(is_flaked[:, :, np.newaxis], sub_arr * 0.88, brown_ink_rgb)

    eff_alpha = alpha[:, :, np.newaxis]
    blended_arr = np.clip(eff_alpha * target_ink + (1.0 - eff_alpha) * sub_arr, 0.0, 255.0).astype(np.uint8)
    blended = Image.fromarray(blended_arr, mode="RGB")

    # 4. Damage (water staining, missing corner — dispatch internal to apply_damage)
    damage_result = apply_damage(blended, folio_id, profile, seed=seed + 2)

    # 4b. Wet-zone & lacuna-zone substrate stain integration
    if min(w, h) >= 240:
        dmg_arr = np.array(damage_result.image, dtype=np.float32)
        eroded_trace = (orig_grey > 132.0) & (orig_grey < 232.0)
        if eroded_trace.any():
            trace_mask_u8 = (eroded_trace.astype(np.uint8)) * 255
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
