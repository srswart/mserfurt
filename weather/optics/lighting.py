"""Lighting gradient — directional studio illumination ramp."""

from __future__ import annotations

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile

# Maps direction name to (dy, dx) unit vector pointing toward the bright end
_DIRECTION_VECTORS = {
    "top_left":     (-1.0, -1.0),
    "top_right":    (-1.0,  1.0),
    "bottom_left":  ( 1.0, -1.0),
    "bottom_right": ( 1.0,  1.0),
    "top":          (-1.0,  0.0),
    "bottom":       ( 1.0,  0.0),
    "left":         ( 0.0, -1.0),
    "right":        ( 0.0,  1.0),
}


def apply_lighting_gradient(img: Image.Image, profile: WeatheringProfile) -> Image.Image:
    """Apply a directional lighting gradient.

    The brightest point is at the corner/edge indicated by `direction`;
    the darkest point is at the opposite corner/edge.  The multiplicative
    scale ranges from ``(1 + strength)`` at the bright end to
    ``(1 - strength)`` at the dark end.

    Args:
        img:     RGB PIL Image of the page.
        profile: WeatheringProfile.

    Returns:
        New RGB PIL Image with lighting gradient applied.
    """
    lg = profile.optics_lighting
    if not lg.enabled:
        return img.copy()

    arr = np.array(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]

    dy, dx = _DIRECTION_VECTORS.get(lg.direction, (-1.0, -1.0))
    # Normalise
    mag = (dx ** 2 + dy ** 2) ** 0.5 or 1.0
    dy, dx = dy / mag, dx / mag

    # Normalised coordinates in [-1, 1]
    yy = (np.arange(h) - h / 2) / (h / 2)
    xx = (np.arange(w) - w / 2) / (w / 2)
    XX, YY = np.meshgrid(xx, yy)

    # Projection onto direction vector: range [-1, 1]
    proj = YY * dy + XX * dx  # 1 at bright end, -1 at dark end

    # Multiplicative scale: 1+strength at bright, 1-strength at dark
    scale = 1.0 + proj * lg.strength
    scale = np.clip(scale, 0.0, 2.0)

    arr *= scale[:, :, np.newaxis]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
