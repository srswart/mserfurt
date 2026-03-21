"""Extract training word images from manuscript photographs.

Crops a word region from a manuscript image using binarization
and connected-component analysis to find the word boundaries.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import label, gaussian_filter


def extract_word_region(
    image_path: Path,
    line_index: int = 0,
    word_index: int = 0,
    padding: int = 10,
) -> np.ndarray:
    """Extract a word image from a manuscript photograph.

    Args:
        image_path: Path to the manuscript image.
        line_index: Which text line (0-based).
        word_index: Which word within the line (0-based).
        padding: Pixel padding around the word.

    Returns:
        RGB numpy array of the cropped word region.
    """
    img = np.array(Image.open(image_path).convert("RGB"))
    gray = np.mean(img.astype(np.float32), axis=2) / 255.0

    # Binarize (ink = True)
    threshold = 0.65
    binary = gray < threshold

    # Detect text lines via horizontal projection
    proj_h = binary.sum(axis=1).astype(float)
    proj_h = gaussian_filter(proj_h, sigma=3.0)
    line_thresh = proj_h.mean() + proj_h.std() * 0.3
    text_rows = proj_h > line_thresh

    labeled_rows, n_rows = label(text_rows)
    if n_rows == 0:
        return img  # fallback: return whole image

    # Select the requested line
    target_line = min(line_index, n_rows - 1) + 1
    row_indices = np.where(labeled_rows == target_line)[0]
    if len(row_indices) == 0:
        return img

    y0, y1 = max(0, row_indices[0] - padding), min(img.shape[0], row_indices[-1] + padding)
    line_strip = binary[y0:y1, :]

    # Detect words within the line via vertical projection
    proj_v = line_strip.sum(axis=0).astype(float)
    proj_v = gaussian_filter(proj_v, sigma=2.0)
    word_thresh = proj_v.mean() * 0.3
    word_cols = proj_v > word_thresh

    labeled_words, n_words = label(word_cols)
    if n_words == 0:
        return img[y0:y1, :]

    target_word = min(word_index, n_words - 1) + 1
    col_indices = np.where(labeled_words == target_word)[0]
    if len(col_indices) == 0:
        return img[y0:y1, :]

    x0 = max(0, col_indices[0] - padding)
    x1 = min(img.shape[1], col_indices[-1] + padding)

    return img[y0:y1, x0:x1]


def save_word_image(word_img: np.ndarray, output_path: Path) -> Path:
    """Save a word image to a PNG file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(word_img, "RGB").save(str(output_path), format="PNG")
    return output_path
