"""Visual difference between two rendered images."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def generate_diff(img1_path: Path, img2_path: Path,
                  output_path: Path) -> Path:
    """Generate a visual difference image between two PNGs.

    Produces a heatmap where bright = large difference, dark = similar.
    """
    img1 = np.array(Image.open(img1_path).convert("RGB")).astype(np.float32)
    img2 = np.array(Image.open(img2_path).convert("RGB")).astype(np.float32)

    # Resize to match if different dimensions
    h = min(img1.shape[0], img2.shape[0])
    w = min(img1.shape[1], img2.shape[1])
    img1 = img1[:h, :w]
    img2 = img2[:h, :w]

    # Per-pixel L2 distance across channels
    diff = np.linalg.norm(img1 - img2, axis=2)

    # Normalize to [0, 255]
    max_diff = diff.max()
    if max_diff > 0:
        diff_norm = (diff / max_diff * 255).astype(np.uint8)
    else:
        diff_norm = np.zeros((h, w), dtype=np.uint8)

    # Apply a colormap: blue→red (cold→hot)
    diff_rgb = np.zeros((h, w, 3), dtype=np.uint8)
    diff_rgb[:, :, 0] = diff_norm  # red channel = difference
    diff_rgb[:, :, 2] = 255 - diff_norm  # blue channel = similarity

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(diff_rgb, "RGB").save(str(output_path), format="PNG")
    return output_path
