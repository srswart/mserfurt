"""Build letterform guides directly from the Musteralphabet letter crops.

Bypasses manuscript segmentation and skeleton tracing entirely.  Instead, uses
column-projection stroke analysis to extract keypoints directly from ink pixels:

  1. Column ink profile → find local maxima (vertical stroke centers)
  2. For each peak → measure topmost/bottommost ink rows in that column band
  3. Map to guide coordinates: y=0 at baseline (image bottom), y=h/x_height at top

Using peak detection rather than threshold groups allows round letters (o, a, e)
to correctly produce two keypoint columns (left and right sides of the bowl)
even though their ink is continuous across all columns.

Usage:
    python scripts/build_guides_from_alphabet.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from PIL import Image
from scipy.signal import find_peaks

from scribesim.guides.keypoint import Keypoint, LetterformGuide
from scribesim.refextract.guidegen import write_guides_toml

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

LETTERS_DIR = Path("reference/letters_alpha")
OUTPUT_TOML = Path("shared/hands/guides_extracted.toml")

# Letters we trust from the Musteralphabet (skip ones with messy multi-variant crops)
SKIP = {"d", "n", "s", "u", "v", "y", "z"}  # these have variant slashes or merged forms

# ---------------------------------------------------------------------------
# Stroke-peak guide extraction
# ---------------------------------------------------------------------------

def _find_stroke_peaks(
    binary: np.ndarray,
    min_distance_ratio: float = 0.10,
    height_ratio: float = 0.30,
) -> list[int]:
    """Find column indices of vertical stroke centers via local-maxima detection.

    Uses scipy find_peaks on the column ink projection.  This correctly finds
    multiple strokes within connected letterforms (e.g. both sides of 'o').

    Args:
        binary: Bool array (True=ink), shape (h, w).
        min_distance_ratio: Minimum peak separation as fraction of image width.
        height_ratio: Minimum peak height as fraction of the maximum column ink count.

    Returns:
        List of column indices (stroke centers), sorted left to right.
    """
    col_ink = binary.sum(axis=0).astype(float)
    if col_ink.max() == 0:
        return []

    w = binary.shape[1]
    min_dist = max(3, int(w * min_distance_ratio))
    min_height = col_ink.max() * height_ratio

    peaks, _ = find_peaks(col_ink, height=min_height, distance=min_dist)
    return list(peaks)


def _top_bottom_rows(binary: np.ndarray, c0: int, c1: int) -> tuple[int, int] | None:
    """Find topmost and bottommost ink rows in column band [c0, c1].

    Args:
        binary: Bool array (True=ink).
        c0, c1: Column range (inclusive).

    Returns:
        (top_row, bottom_row) in image coordinates, or None if no ink.
    """
    region = binary[:, c0:c1 + 1]
    rows_with_ink = np.where(region.any(axis=1))[0]
    if len(rows_with_ink) == 0:
        return None
    return int(rows_with_ink[0]), int(rows_with_ink[-1])


def build_guide_from_crop(letter: str, crop_path: Path) -> LetterformGuide | None:
    """Build a LetterformGuide from a clean letter crop using peak stroke analysis.

    Identifies vertical stroke centers via local maxima of the column ink projection,
    then places keypoints at the top (entry/peak) and bottom (base/exit) of each
    stroke's ink extent.

    Guide coordinates: y=0 at baseline (image bottom), y≈1 at x-height (image top).
    x=0 at the first stroke center; x_advance spans from first to last stroke center.

    Args:
        letter: Single character label.
        crop_path: Path to a grayscale PNG of the isolated letter.

    Returns:
        LetterformGuide or None if extraction fails.
    """
    img = np.array(Image.open(crop_path).convert("L"))
    h, w = img.shape

    binary = img < 128  # True = ink
    if not binary.any():
        print(f"  [{letter}] no ink found")
        return None

    # x_height in pixels — crop height ≈ letter height for tightly-cropped forms
    x_height_px = float(h * 0.85)

    # Find stroke centers (column local maxima)
    stroke_cols = _find_stroke_peaks(binary)

    # Fallback: if no peaks found, use the column with max ink as a single stroke
    if not stroke_cols:
        col_ink = binary.sum(axis=0).astype(float)
        stroke_cols = [int(np.argmax(col_ink))]

    # Determine per-stroke column window: midpoints between adjacent peaks
    # Window for peak i = [mid(i-1, i), mid(i, i+1)]
    half_gaps = []
    for i, peak in enumerate(stroke_cols):
        left = (stroke_cols[i-1] + peak) // 2 if i > 0 else 0
        right = (peak + stroke_cols[i+1]) // 2 if i < len(stroke_cols)-1 else w - 1
        half_gaps.append((left, right))

    # Normalize x from first ink column so x=0 at the letter's left edge.
    # x_advance is the actual ink column span (last - first ink column).
    all_ink_cols = np.where(binary.any(axis=0))[0]
    x_origin = float(all_ink_cols[0]) if len(all_ink_cols) else 0.0
    ink_span = float(all_ink_cols[-1] - all_ink_cols[0] + 1) if len(all_ink_cols) > 1 else 1.0
    x_advance = max(0.3, min(2.5, ink_span / x_height_px))

    # Guide coordinate transform:
    #   x_guide = (col - x_origin) / x_height_px  → x=0 at first stroke center
    #   y_guide = (h - 1 - row) / x_height_px     → y=0 at baseline (image bottom)
    def to_xy(col: float, row: int) -> tuple[float, float]:
        return (col - x_origin) / x_height_px, (h - 1 - row) / x_height_px

    keypoints: list[Keypoint] = []

    for i, (peak_col, (c0, c1)) in enumerate(zip(stroke_cols, half_gaps)):
        result = _top_bottom_rows(binary, c0, c1)
        if result is None:
            continue
        r_top, r_bot = result

        x_top, y_top = to_xy(float(peak_col), r_top)  # high y = x-height
        x_bot, y_bot = to_xy(float(peak_col), r_bot)  # low y  = baseline

        if i == 0:
            keypoints.append(Keypoint(
                x=x_top, y=y_top,
                point_type="entry", contact=True, direction_deg=270.0,
            ))
            keypoints.append(Keypoint(
                x=x_bot, y=y_bot,
                point_type="base", contact=True, direction_deg=270.0,
            ))
        else:
            keypoints.append(Keypoint(
                x=x_top, y=y_top,
                point_type="peak", contact=True, direction_deg=270.0,
            ))
            keypoints.append(Keypoint(
                x=x_bot, y=y_bot,
                point_type="base", contact=True, direction_deg=270.0,
            ))

    if not keypoints:
        print(f"  [{letter}] no keypoints extracted")
        return None

    # Replace the final base with an exit keypoint
    last = keypoints[-1]
    keypoints[-1] = Keypoint(
        x=last.x, y=last.y,
        point_type="exit", contact=True, direction_deg=270.0,
    )

    ascenders = set("bdfhijklt")
    descenders = set("gjpqy")

    guide = LetterformGuide(
        letter=letter,
        keypoints=tuple(keypoints),
        x_advance=x_advance,
        ascender=letter in ascenders,
        descender=letter in descenders,
    )

    n_kp = len(keypoints)
    print(f"  [{letter}] {n_kp} keypoints, x_advance={x_advance:.3f}, {len(stroke_cols)} strokes")
    return guide


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not LETTERS_DIR.exists():
        print(f"ERROR: {LETTERS_DIR} not found. Run extract first.")
        sys.exit(1)

    crops = sorted(LETTERS_DIR.glob("*.png"))
    print(f"Found {len(crops)} letter crops in {LETTERS_DIR}/\n")

    guides: dict[str, LetterformGuide] = {}
    failed: list[str] = []

    for crop_path in crops:
        letter = crop_path.stem
        if letter in SKIP:
            print(f"  [{letter}] skipped (multi-variant crop)")
            continue
        if len(letter) > 1:
            print(f"  [{letter}] skipped (ligature)")
            continue

        guide = build_guide_from_crop(letter, crop_path)
        if guide is not None:
            guides[letter] = guide
        else:
            failed.append(letter)

    print(f"\nBuilt {len(guides)} guides. Failed: {failed or 'none'}")

    if not guides:
        print("No guides produced.")
        sys.exit(1)

    write_guides_toml(guides, OUTPUT_TOML)
    print(f"Wrote → {OUTPUT_TOML}")

    # Summary
    print("\nGuide summary:")
    for ch, g in sorted(guides.items()):
        kp_types = [k.point_type for k in g.keypoints]
        print(f"  {ch}: {len(g.keypoints)} kps {kp_types}, x_adv={g.x_advance:.3f}")


if __name__ == "__main__":
    main()
