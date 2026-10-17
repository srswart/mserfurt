"""Follicle mark renderer for vellum texture — clustered micro-pore sampling.

Follicle marks (hair follicle pores on calfskin/goatskin parchment) are tiny
pinprick pores grouped in natural flank clusters along the vellum grain axis.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def follicle_marks(
    width: int,
    height: int,
    density: float = 0.002,
    grain_angle_deg: float = 15.0,
    seed: int = 0,
    min_radius_px: float = 0.6,
    max_radius_px: float = 1.6,
    elongation: float = 1.6,
) -> np.ndarray:
    """Generate a subtle hair-follicle micro-pore alpha mask.

    Args:
        width:          Output width in pixels.
        height:         Output height in pixels.
        density:        Expected marks per pixel (controls quantity).
        grain_angle_deg: Angle of vellum grain axis (degrees from horizontal).
        seed:           RNG seed for reproducibility.
        min_radius_px:  Minimum semi-minor axis of a pore.
        max_radius_px:  Maximum semi-minor axis of a pore.
        elongation:     Ratio of semi-major to semi-minor axis.

    Returns:
        uint8 ndarray of shape (height, width) with follicle pores as
        non-zero values (0 = background, > 0 = pore intensity).
    """
    rng = np.random.default_rng(seed)

    # Keep total pore count natural and cluster pores into organic flank patches
    n_marks = max(1, int(width * height * min(density, 0.00045)))
    grain_rad = math.radians(grain_angle_deg)
    cos_g = math.cos(grain_rad)
    sin_g = math.sin(grain_rad)

    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)

    # Pick 4-7 cluster centers (typically stronger toward flank/margins)
    n_clusters = max(2, min(7, n_marks // 25 + 2))
    cluster_xs = rng.uniform(0.05 * width, 0.95 * width, size=n_clusters)
    cluster_ys = rng.uniform(0.05 * height, 0.95 * height, size=n_clusters)
    cluster_spread_x = max(8.0, width * 0.14)
    cluster_spread_y = max(8.0, height * 0.14)

    for i in range(n_marks):
        if i % 3 != 0:
            cid = int(rng.integers(0, n_clusters))
            cx = float(np.clip(rng.normal(cluster_xs[cid], cluster_spread_x), 0, width - 1))
            cy = float(np.clip(rng.normal(cluster_ys[cid], cluster_spread_y), 0, height - 1))
        else:
            cx = float(rng.uniform(0, width))
            cy = float(rng.uniform(0, height))

        b = float(rng.uniform(min_radius_px, max_radius_px))
        a = b * elongation

        dx = math.sqrt((a * cos_g) ** 2 + (b * sin_g) ** 2)
        dy = math.sqrt((a * sin_g) ** 2 + (b * cos_g) ** 2)

        bbox = [cx - dx, cy - dy, cx + dx, cy + dy]
        intensity = int(rng.integers(14, 42))
        draw.ellipse(bbox, fill=intensity)

    if min(width, height) >= 64:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.55))

    return np.array(img, dtype=np.uint8)
