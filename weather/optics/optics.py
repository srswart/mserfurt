"""Optics orchestrator — page curl, vignette, lighting gradient."""

from __future__ import annotations

from PIL import Image

from weather.profile import WeatheringProfile
from weather.optics.curl import apply_page_curl
from weather.optics.vignette import apply_vignette
from weather.optics.lighting import apply_lighting_gradient
from weather.optics.result import OpticsResult


def apply_optics(
    img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
    seed: int = 0,
) -> OpticsResult:
    """Apply all optics effects to a page image.

    Order: page curl (spatial warp) → vignette → lighting gradient.

    Args:
        img:       RGB PIL Image of the page.
        folio_id:  Folio identifier (used by page curl for gutter side).
        profile:   WeatheringProfile.
        seed:      RNG seed (forwarded to page curl).

    Returns:
        OpticsResult with final image and optional curl_transform.
    """
    curl_result = apply_page_curl(img, folio_id, profile, seed=seed)
    result = apply_vignette(curl_result.image, profile)
    result = apply_lighting_gradient(result, profile)
    return OpticsResult(image=result, curl_transform=curl_result.curl_transform)
