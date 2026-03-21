"""Extract writing path from a manuscript word image (TD-005 Part 2).

Skeletonizes the word, orders the skeleton into a writing sequence,
and estimates speed/pressure from stroke width and darkness.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import label, distance_transform_edt, gaussian_filter


@dataclass
class PathPoint:
    """A point on the extracted writing path."""
    x: float       # pixel x
    y: float       # pixel y
    width: float   # estimated stroke width (pixels)
    darkness: float # ink darkness [0, 1]


def extract_writing_path(word_img: np.ndarray) -> list[PathPoint]:
    """Extract the probable writing path from a word image.

    1. Binarize and compute distance transform (width estimate)
    2. Skeletonize via thinning the binary mask
    3. Order skeleton pixels left-to-right (writing direction)
    4. Estimate speed from width: thick = slow, thin = fast

    Args:
        word_img: RGB numpy array of a word crop.

    Returns:
        Ordered list of PathPoints along the writing path.
    """
    # Convert to grayscale
    if word_img.ndim == 3:
        gray = np.mean(word_img.astype(np.float32), axis=2) / 255.0
    else:
        gray = word_img.astype(np.float32) / 255.0

    # Binarize (ink = True)
    binary = gray < 0.65
    if not binary.any():
        return []

    # Distance transform: value at each ink pixel = distance to nearest background
    dt = distance_transform_edt(binary)

    # Simple skeleton: thin the binary mask by keeping only local maxima of dt
    # (points that are further from the edge than their neighbors)
    skeleton = np.zeros_like(binary)
    h, w = binary.shape
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not binary[y, x]:
                continue
            val = dt[y, x]
            if val < 0.5:
                continue
            # Check if this is a local maximum or ridge in at least one direction
            neighbors = [dt[y-1, x], dt[y+1, x], dt[y, x-1], dt[y, x+1]]
            if val >= min(neighbors):
                skeleton[y, x] = True

    # Thin further: keep only pixels where dt > median
    sk_vals = dt[skeleton]
    if len(sk_vals) > 0:
        med = np.median(sk_vals)
        skeleton = skeleton & (dt >= med * 0.5)

    if not skeleton.any():
        # Fallback: use all ink pixels
        skeleton = binary

    # Order skeleton pixels left-to-right
    ys, xs = np.where(skeleton)
    if len(xs) == 0:
        return []

    # Sort by x (left to right), breaking ties by y
    order = np.lexsort((ys, xs))
    xs, ys = xs[order], ys[order]

    # Build path points
    path = []
    for i in range(len(xs)):
        x, y = int(xs[i]), int(ys[i])
        width = dt[y, x] * 2  # diameter
        darkness = 1.0 - gray[y, x]
        path.append(PathPoint(x=float(x), y=float(y), width=width, darkness=darkness))

    # Subsample for efficiency (every Nth point)
    if len(path) > 200:
        step = max(1, len(path) // 200)
        path = path[::step]

    return path


def path_to_mm(path: list[PathPoint], px_per_mm: float) -> list[tuple[float, float]]:
    """Convert a pixel path to mm coordinates."""
    return [(p.x / px_per_mm, p.y / px_per_mm) for p in path]
