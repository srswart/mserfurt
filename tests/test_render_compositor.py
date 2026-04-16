"""Compositor coordinate tests — ADV-SS-RENDER-005.

Verifies that the plain render pipeline places text at the correct page
coordinates (left margin, top margin, line spacing). The original symptom
was text crammed into the top-left corner at x≈0mm rather than at the
configured left margin.

Also verifies the evo line renderer produces correctly spaced words.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scribesim.hand.model import load_base, resolve
from scribesim.layout import place
from scribesim.render.pipeline import render_pipeline, _OUTPUT_DPI

_HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"
_FOLIO_F01R = Path(__file__).parent / "golden" / "f01r" / "folio.json"
_PX_PER_MM_OUTPUT = _OUTPUT_DPI / 25.4  # ≈ 11.811 px/mm at 300 DPI


def _ink_mask(arr: np.ndarray, threshold: float = 20.0) -> np.ndarray:
    """Boolean mask: True where pixels differ from parchment by > threshold."""
    parchment = np.array([245, 238, 220], dtype=float)
    diff = np.linalg.norm(arr.astype(float) - parchment, axis=2)
    return diff > threshold


def _f01r_render(tmp_path):
    """Render f01r with the plain pipeline and return (arr, layout)."""
    folio = json.loads(_FOLIO_F01R.read_text())
    base = load_base(_HAND_TOML)
    params = resolve(base, "f01r")
    layout = place(folio, params)
    page_path, _ = render_pipeline(layout, params, tmp_path, "f01r")
    arr = np.array(Image.open(page_path))
    return arr, layout


# ---------------------------------------------------------------------------
# TestPlainPipelineCoordinates
# ---------------------------------------------------------------------------

class TestPlainPipelineCoordinates:
    """Verify text is placed at the correct page-absolute coordinates."""

    def test_left_margin_respected(self, tmp_path):
        """Leftmost ink should be within 2mm of the configured left margin."""
        arr, layout = _f01r_render(tmp_path)
        mask = _ink_mask(arr)
        assert mask.any(), "No ink pixels found in rendered page"

        _, cols = np.where(mask)
        leftmost_px = int(cols.min())
        leftmost_mm = leftmost_px / _PX_PER_MM_OUTPUT

        margin_mm = layout.geometry.margin_inner
        assert leftmost_mm >= margin_mm - 2.0, (
            f"Text starts at {leftmost_mm:.1f}mm — too far left of {margin_mm}mm margin"
        )
        assert leftmost_mm <= margin_mm + 3.0, (
            f"Text starts at {leftmost_mm:.1f}mm — too far right of {margin_mm}mm margin"
        )

    def test_top_margin_respected(self, tmp_path):
        """Topmost ink should be within 4mm of the expected baseline y."""
        arr, layout = _f01r_render(tmp_path)
        mask = _ink_mask(arr)
        assert mask.any()

        rows, _ = np.where(mask)
        topmost_px = int(rows.min())
        topmost_mm = topmost_px / _PX_PER_MM_OUTPUT

        # First baseline = margin_top + x_height_mm; ascenders reach above that
        first_baseline_mm = layout.lines[0].glyphs[0].baseline_y_mm
        x_height_mm = layout.geometry.x_height_mm
        # Top of tallest ascender can be up to ~2× x_height above baseline
        expected_top_mm = first_baseline_mm - 2.0 * x_height_mm

        assert topmost_mm >= expected_top_mm - 2.0, (
            f"Ink appears at y={topmost_mm:.1f}mm, above expected top {expected_top_mm:.1f}mm"
        )
        assert topmost_mm <= first_baseline_mm, (
            f"Ink starts below the first baseline — text may be shifted down"
        )

    def test_text_not_at_page_origin(self, tmp_path):
        """Text must not start at the raw origin (0,0) — margin must be applied."""
        arr, layout = _f01r_render(tmp_path)
        mask = _ink_mask(arr)
        assert mask.any()

        rows, cols = np.where(mask)
        leftmost_mm = cols.min() / _PX_PER_MM_OUTPUT
        topmost_mm = rows.min() / _PX_PER_MM_OUTPUT

        # With a 20mm margin, text should start well away from origin
        assert leftmost_mm > 10.0, (
            f"Leftmost ink at {leftmost_mm:.1f}mm — no left margin applied"
        )
        assert topmost_mm > 10.0, (
            f"Topmost ink at {topmost_mm:.1f}mm — no top margin applied"
        )

    def test_multiple_lines_span_correct_vertical_range(self, tmp_path):
        """With 8 lines at 7.6mm pitch, ink should span ~53mm vertically."""
        arr, layout = _f01r_render(tmp_path)
        mask = _ink_mask(arr)
        assert mask.any()

        rows, _ = np.where(mask)
        ink_height_mm = (rows.max() - rows.min()) / _PX_PER_MM_OUTPUT

        n_lines = len(layout.lines)
        pitch_mm = layout.geometry.ruling_pitch_mm
        expected_min_height_mm = (n_lines - 1) * pitch_mm * 0.7
        assert ink_height_mm >= expected_min_height_mm, (
            f"Ink vertical span {ink_height_mm:.1f}mm too small for {n_lines} lines "
            f"at {pitch_mm:.1f}mm pitch (expected ≥ {expected_min_height_mm:.1f}mm)"
        )

    def test_line_baselines_at_correct_y(self, tmp_path):
        """Each line's baseline should have a horizontal band of ink nearby."""
        arr, layout = _f01r_render(tmp_path)
        mask = _ink_mask(arr)

        for line in layout.lines[:4]:  # check first 4 lines
            baseline_mm = line.glyphs[0].baseline_y_mm
            # Band: baseline ± x_height (strokes span from below to above baseline)
            x_height_mm = layout.geometry.x_height_mm
            y_lo = max(0, round((baseline_mm - x_height_mm) * _PX_PER_MM_OUTPUT))
            y_hi = round((baseline_mm + x_height_mm * 0.5) * _PX_PER_MM_OUTPUT)
            band = mask[y_lo:y_hi, :]
            assert band.any(), (
                f"No ink in baseline band for line at y={baseline_mm:.1f}mm"
            )


# ---------------------------------------------------------------------------
# TestLineRendererWordSpacing
# ---------------------------------------------------------------------------

def _word_segments(line_png_arr: np.ndarray, min_gap_px: int = 6) -> list[tuple[int, int]]:
    """Find word-level segments by merging small intra-word gaps.

    Returns list of (col_start, col_end) for each detected word.
    """
    mask = _ink_mask(line_png_arr)
    has_ink = mask.any(axis=0)  # per-column ink presence

    # Build raw segments (runs of ink columns)
    segments: list[tuple[int, int]] = []
    in_ink = False
    start = 0
    for col, ink in enumerate(has_ink):
        if ink and not in_ink:
            start = col
            in_ink = True
        elif not ink and in_ink:
            segments.append((start, col))
            in_ink = False
    if in_ink:
        segments.append((start, len(has_ink)))

    if not segments:
        return []

    # Merge segments separated by small gaps (≤ min_gap_px — intra-word noise)
    merged: list[tuple[int, int]] = [segments[0]]
    for start, end in segments[1:]:
        if start - merged[-1][1] <= min_gap_px:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))

    return merged


class TestLineRendererWordSpacing:
    """Verify the evo line renderer places words with correct spacing."""

    def test_four_words_are_separated(self, tmp_path):
        """'und das waz gut' should produce 4 visually distinct word segments."""
        from scribesim.evo.compose import render_line

        arr = render_line(
            "und das waz gut",
            dpi=150.0,
            verbose=False,
        )
        assert isinstance(arr, np.ndarray)
        segs = _word_segments(arr)
        assert len(segs) == 4, (
            f"Expected 4 word segments, got {len(segs)}: {segs}"
        )

    def test_words_spaced_not_touching(self, tmp_path):
        """There should be visible gaps between words (pen lifted between words)."""
        from scribesim.evo.compose import render_line

        arr = render_line(
            "und das waz gut",
            dpi=150.0,
            verbose=False,
        )
        segs = _word_segments(arr, min_gap_px=4)
        assert len(segs) >= 3, (
            f"Words appear to run together — found only {len(segs)} segment(s)"
        )

    def test_line_has_ink(self, tmp_path):
        """Rendered line should contain non-parchment pixels."""
        from scribesim.evo.compose import render_line

        arr = render_line(
            "und das waz gut",
            dpi=150.0,
            verbose=False,
        )
        mask = _ink_mask(arr)
        assert mask.sum() > 200, "Line render has too few ink pixels"
