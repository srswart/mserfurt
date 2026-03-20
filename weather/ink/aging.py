"""Ink aging pipeline — orchestrate mask → fade → bleed → flake."""

from __future__ import annotations

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile
from weather.ink.mask import extract_ink_mask
from weather.ink.fade import ink_fade
from weather.ink.bleed import ink_bleed
from weather.ink.flake import ink_flake


def apply_ink_aging(
    page_img: Image.Image,
    heatmap_img: Image.Image,
    profile: WeatheringProfile,
    seed: int = 0,
) -> Image.Image:
    """Apply the full ink aging pipeline to a ScribeSim page image.

    Pipeline: extract ink mask → fade (colour shift) → bleed (Gaussian spread)
              → flake (pressure-targeted removal).

    Args:
        page_img:    RGB PIL Image from ScribeSim render_page().
        heatmap_img: Grayscale PIL Image from ScribeSim render_heatmap().
        profile:     WeatheringProfile from load_profile().
        seed:        RNG seed for deterministic flaking.

    Returns:
        RGB PIL Image with ink aging applied.
    """
    arr = np.array(page_img.convert("RGB"), dtype=np.uint8)
    heatmap = np.array(
        heatmap_img.convert("L").resize(
            (page_img.width, page_img.height), Image.NEAREST
        ),
        dtype=np.uint8,
    )

    mask = extract_ink_mask(page_img)

    if profile.ink_fade.enabled:
        arr = ink_fade(arr, mask, profile)
        # Re-extract mask after fade (ink slightly lighter but still masked)
        # Use same mask — fade doesn't move pixels across threshold significantly

    if profile.ink_bleed.enabled:
        arr = ink_bleed(arr, mask, profile.ink_bleed.radius_px)

    if profile.ink_flake.enabled:
        arr = ink_flake(arr, mask, heatmap, profile,
                        seed=seed + profile.ink_flake.seed_offset)

    return Image.fromarray(arr, mode="RGB")
