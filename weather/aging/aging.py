"""Aging orchestrator — edge darkening, foxing, binding shadow."""

from __future__ import annotations

from PIL import Image

from weather.profile import WeatheringProfile
from weather.aging.edge import apply_edge_darkening
from weather.aging.foxing import apply_foxing
from weather.aging.shadow import apply_binding_shadow


def apply_aging(
    img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
    seed: int = 0,
) -> Image.Image:
    """Apply all aging effects to a page image.

    Applies effects in order: edge darkening → foxing → binding shadow.
    """
    result = apply_edge_darkening(img, profile, folio_id=folio_id, seed=seed)
    result = apply_foxing(result, profile, seed=seed)
    result = apply_binding_shadow(result, folio_id, profile)
    return result
