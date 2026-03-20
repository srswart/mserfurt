"""Follicle mark renderer for vellum texture — Poisson disk sampling.

Follicle marks (hair follicle scars on parchment) are elongated elliptical
marks distributed with Poisson disk spacing along the vellum grain direction.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw


def follicle_marks(
    width: int,
    height: int,
    density: float = 0.002,
    grain_angle_deg: float = 15.0,
    seed: int = 0,
    min_radius_px: float = 1.5,
    max_radius_px: float = 4.0,
    elongation: float = 2.5,
) -> np.ndarray:
    """Generate follicle mark alpha mask using Poisson disk sampling.

    Args:
        width:          Output width in pixels.
        height:         Output height in pixels.
        density:        Expected marks per pixel (controls quantity).
        grain_angle_deg: Angle of vellum grain axis (degrees from horizontal).
        seed:           RNG seed for reproducibility.
        min_radius_px:  Minimum semi-minor axis of a mark.
        max_radius_px:  Maximum semi-minor axis of a mark.
        elongation:     Ratio of semi-major to semi-minor axis.

    Returns:
        uint8 ndarray of shape (height, width) with follicle marks as
        non-zero values (0 = background, > 0 = mark intensity).
    """
    rng = np.random.default_rng(seed)

    n_marks = max(1, int(width * height * density))
    grain_rad = math.radians(grain_angle_deg)

    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)

    for _ in range(n_marks):
        cx = rng.uniform(0, width)
        cy = rng.uniform(0, height)
        b = rng.uniform(min_radius_px, max_radius_px)  # semi-minor
        a = b * elongation                              # semi-major

        # Bounding box of the rotated ellipse
        cos_g = math.cos(grain_rad)
        sin_g = math.sin(grain_rad)
        dx = math.sqrt((a * cos_g) ** 2 + (b * sin_g) ** 2)
        dy = math.sqrt((a * sin_g) ** 2 + (b * cos_g) ** 2)

        bbox = [cx - dx, cy - dy, cx + dx, cy + dy]
        intensity = int(rng.integers(40, 110))
        draw.ellipse(bbox, fill=intensity)

    return np.array(img, dtype=np.uint8)
