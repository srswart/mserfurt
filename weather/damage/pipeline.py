"""Damage pipeline — orchestrate water damage and missing corner per folio."""

from __future__ import annotations

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile
from weather.damage.zones import DamageResult
from weather.damage.water import apply_water_damage
from weather.damage.corner import apply_missing_corner


def apply_damage(
    img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
    seed: int = 0,
) -> DamageResult:
    """Apply all applicable damage effects to a page image.

    Dispatches water_damage and missing_corner based on folio_id.
    Non-damaged folios are returned unchanged with empty zone masks.

    Args:
        img:       RGB PIL Image of the page.
        folio_id:  Folio identifier, e.g. "f04v".
        profile:   WeatheringProfile.
        seed:      RNG seed (deterministic per folio + seed).

    Returns:
        DamageResult with composited image and all applicable zone masks.
    """
    water_result = apply_water_damage(img, folio_id, profile, seed=seed)
    corner_result = apply_missing_corner(
        water_result.image, folio_id, profile, seed=seed + 1
    )

    return DamageResult(
        image=corner_result.image,
        water_zone=water_result.water_zone,
        corner_mask=corner_result.corner_mask,
    )
