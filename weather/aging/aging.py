"""Aging orchestrator — edge darkening, foxing, binding shadow, and physical edge nicks / corner curl."""

from __future__ import annotations

from PIL import Image

from weather.profile import WeatheringProfile
from weather.aging.edge import apply_edge_darkening, apply_edge_wear_and_corner_curl
from weather.aging.foxing import apply_foxing
from weather.aging.shadow import apply_binding_shadow


def apply_aging(
    img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
    seed: int = 0,
) -> Image.Image:
    """Apply all aging effects to a page image.

    Applies effects in order:
      1. Edge darkening & marginal damp colonies
      2. Foxing specks & clusters
      3. Binding shadow along spine gutter
      4. Physical cut-edge nicks, fibrous bevel, and two-reader outer-corner curl (on full folios)
    """
    result = apply_edge_darkening(img, profile, folio_id=folio_id, seed=seed)
    result = apply_foxing(result, profile, seed=seed)
    result = apply_binding_shadow(result, folio_id, profile)
    if min(img.width, img.height) >= 320:
        result = apply_edge_wear_and_corner_curl(result, folio_id=folio_id, profile=profile, seed=seed)
    return result
