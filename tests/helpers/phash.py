"""Perceptual hash utilities for golden image regression testing."""

from __future__ import annotations

from pathlib import Path

import imagehash
from PIL import Image


def compute_phash(image_path: Path) -> imagehash.ImageHash:
    """Compute pHash for a PNG image (converted to grayscale)."""
    img = Image.open(str(image_path)).convert("L")
    return imagehash.phash(img)


def hamming_distance(hash1: imagehash.ImageHash, hash2: imagehash.ImageHash) -> int:
    """Return Hamming distance between two pHashes (imagehash overloads -)."""
    return hash1 - hash2
