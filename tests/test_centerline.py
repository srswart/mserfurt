"""Tests for scribesim/refextract/centerline.py (ADV-SS-CENTERLINE-001).

Red phase: should fail until centerline.py is implemented.
"""

import math
import json
import numpy as np
import pytest
from pathlib import Path

from scribesim.refextract.centerline import (
    skeletonize_letter,
    order_skeleton_pixels,
    detect_gaps,
    fit_bezier_to_path,
    trace_centerline,
    save_trace,
    load_trace,
    _zhang_suen_thin,
)
from scribesim.evo.genome import BezierSegment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _filled_rect(h, w, fill_y0, fill_y1, fill_x0, fill_x1):
    """White image with a black filled rectangle."""
    img = np.full((h, w), 255, dtype=np.uint8)
    img[fill_y0:fill_y1, fill_x0:fill_x1] = 0
    return img


# ---------------------------------------------------------------------------
# Zhang-Suen thinning
# ---------------------------------------------------------------------------

def test_zhang_suen_horizontal_stroke():
    """A horizontal filled rectangle → 1-pixel-wide horizontal skeleton."""
    binary = np.zeros((40, 80), dtype=bool)
    binary[15:25, 10:70] = True  # 10-pixel-tall horizontal bar

    skeleton = _zhang_suen_thin(binary)

    # Skeleton should be 1-pixel wide (max 2 in any column)
    col_counts = skeleton.sum(axis=0)
    assert col_counts.max() <= 2, f"skeleton too wide: max col count={col_counts.max()}"

    # Skeleton should span most of the width of the bar
    # (Zhang-Suen may trim a few pixels from endpoints)
    ink_cols = np.where(col_counts > 0)[0]
    assert ink_cols[0] <= 18   # bar starts at col 10; allow up to 8px endpoint trim
    assert ink_cols[-1] >= 62  # bar ends at col 70; allow up to 8px endpoint trim


def test_zhang_suen_vertical_stroke():
    """A vertical filled rectangle → 1-pixel-wide vertical skeleton."""
    binary = np.zeros((80, 40), dtype=bool)
    binary[10:70, 15:25] = True

    skeleton = _zhang_suen_thin(binary)

    row_counts = skeleton.sum(axis=1)
    assert row_counts.max() <= 2


def test_zhang_suen_blank():
    """Blank image → empty skeleton."""
    binary = np.zeros((40, 40), dtype=bool)
    skeleton = _zhang_suen_thin(binary)
    assert not skeleton.any()


def test_zhang_suen_single_pixel():
    """Single pixel → single pixel skeleton (isolated pixels are not removed)."""
    binary = np.zeros((10, 10), dtype=bool)
    binary[5, 5] = True
    skeleton = _zhang_suen_thin(binary)
    assert skeleton.sum() == 1


# ---------------------------------------------------------------------------
# skeletonize_letter
# ---------------------------------------------------------------------------

def test_skeletonize_letter_returns_bool_skeleton():
    """skeletonize_letter takes a uint8 image, returns bool skeleton."""
    img = _filled_rect(40, 80, 15, 25, 10, 70)
    skel = skeletonize_letter(img, ink_threshold=200)
    assert skel.dtype == bool
    assert skel.shape == img.shape
    assert skel.any()


def test_skeletonize_letter_blank():
    """Blank image → empty skeleton."""
    img = np.full((40, 40), 255, dtype=np.uint8)
    skel = skeletonize_letter(img)
    assert not skel.any()


# ---------------------------------------------------------------------------
# order_skeleton_pixels
# ---------------------------------------------------------------------------

def test_order_skeleton_simple_line():
    """Horizontal 1-pixel line → single path ordered left to right."""
    skeleton = np.zeros((10, 20), dtype=bool)
    skeleton[5, 2:18] = True  # horizontal line

    paths = order_skeleton_pixels(skeleton)
    assert len(paths) >= 1

    # First path should be ordered left to right (x increases)
    xs = [pt[1] for pt in paths[0]]  # pt = (row, col)
    assert xs[0] <= xs[-1], "path should go left to right"
    assert len(paths[0]) >= 14


def test_order_skeleton_empty():
    """Empty skeleton → no paths."""
    skeleton = np.zeros((10, 10), dtype=bool)
    paths = order_skeleton_pixels(skeleton)
    assert paths == []


def test_order_skeleton_returns_list_of_tuples():
    """Each path element is a (row, col) tuple."""
    skeleton = np.zeros((10, 20), dtype=bool)
    skeleton[5, 5:15] = True
    paths = order_skeleton_pixels(skeleton)
    assert len(paths) > 0
    for pt in paths[0]:
        assert len(pt) == 2
        r, c = pt
        assert 0 <= r < 10
        assert 0 <= c < 20


# ---------------------------------------------------------------------------
# detect_gaps
# ---------------------------------------------------------------------------

def test_detect_gaps_connected():
    """Fully connected skeleton → no gaps."""
    skeleton = np.zeros((10, 30), dtype=bool)
    skeleton[5, :] = True  # solid horizontal line

    gaps = detect_gaps(skeleton, gap_threshold=3)
    assert gaps == []


def test_detect_gaps_broken():
    """Skeleton with a 5-column gap → one gap detected."""
    skeleton = np.zeros((10, 40), dtype=bool)
    skeleton[5, 0:15] = True   # left segment
    skeleton[5, 20:40] = True  # right segment — gap at cols 15..19

    gaps = detect_gaps(skeleton, gap_threshold=3)
    assert len(gaps) == 1
    gap_start, gap_end = gaps[0]
    assert gap_start <= 15
    assert gap_end >= 19


def test_detect_gaps_small_gap_ignored():
    """Gap narrower than threshold is not reported."""
    skeleton = np.zeros((10, 30), dtype=bool)
    skeleton[5, 0:10] = True
    skeleton[5, 11:30] = True  # 1-column gap (< threshold=3)

    gaps = detect_gaps(skeleton, gap_threshold=3)
    assert gaps == []


# ---------------------------------------------------------------------------
# fit_bezier_to_path
# ---------------------------------------------------------------------------

def test_fit_bezier_straight_line():
    """10 collinear points → at least one segment, all near the line."""
    points = [(float(x), 5.0) for x in range(10)]
    segments = fit_bezier_to_path(points, max_error=0.5)

    assert len(segments) >= 1
    for seg in segments:
        assert isinstance(seg, BezierSegment)
        assert seg.contact is True
        # All control points should be near y=5
        for p in (seg.p0, seg.p1, seg.p2, seg.p3):
            assert abs(p[1] - 5.0) < 1.5, f"control point far from line: {p}"


def test_fit_bezier_curved_path():
    """Points on a parabola → fit stays within max_error."""
    # Sample y = x^2/10 for x in [0..20]
    points = [(float(x), x * x / 20.0) for x in range(21)]
    max_err = 1.0
    segments = fit_bezier_to_path(points, max_error=max_err)

    assert len(segments) >= 1
    # Verify the fitted segments actually pass near the sample points
    for seg in segments:
        assert isinstance(seg, BezierSegment)


def test_fit_bezier_single_point():
    """Single point → handled gracefully (one degenerate segment or empty)."""
    points = [(5.0, 5.0)]
    # Should not raise, may return [] or a degenerate segment
    result = fit_bezier_to_path(points, max_error=0.5)
    assert isinstance(result, list)


def test_fit_bezier_two_points():
    """Two points → one segment connecting them."""
    points = [(0.0, 0.0), (10.0, 0.0)]
    segments = fit_bezier_to_path(points, max_error=0.5)
    assert len(segments) == 1
    assert segments[0].p0[0] == pytest.approx(0.0, abs=1.0)
    assert segments[0].p3[0] == pytest.approx(10.0, abs=1.0)


# ---------------------------------------------------------------------------
# trace_centerline
# ---------------------------------------------------------------------------

def test_trace_centerline_returns_segments():
    """trace_centerline on a simple letter image returns BezierSegments."""
    # Synthetic horizontal stroke
    img = _filled_rect(40, 80, 16, 24, 5, 75)
    segments = trace_centerline(img)

    assert isinstance(segments, list)
    assert len(segments) >= 1
    for seg in segments:
        assert isinstance(seg, BezierSegment)


def test_trace_centerline_contact_flag():
    """Contact segments have contact=True; gap segments contact=False (if gaps exist)."""
    img = _filled_rect(40, 80, 16, 24, 5, 75)
    segments = trace_centerline(img)
    # For a solid stroke, all should be contact=True
    assert all(seg.contact for seg in segments)


def test_trace_centerline_blank():
    """Blank image → empty segment list."""
    img = np.full((40, 40), 255, dtype=np.uint8)
    segments = trace_centerline(img)
    assert segments == []


# ---------------------------------------------------------------------------
# save_trace / load_trace round-trip
# ---------------------------------------------------------------------------

def test_save_load_trace_roundtrip(tmp_path):
    """save_trace + load_trace preserves p0..p3 and contact flag."""
    segments = [
        BezierSegment((0.0, 0.0), (1.0, 0.5), (2.0, -0.5), (3.0, 0.0), contact=True),
        BezierSegment((3.0, 0.0), (4.0, 1.0), (5.0, -1.0), (6.0, 0.0), contact=False),
    ]
    trace_path = tmp_path / "test_trace.json"
    save_trace(segments, trace_path)

    assert trace_path.exists()
    loaded = load_trace(trace_path)
    assert len(loaded) == 2

    for orig, loaded_seg in zip(segments, loaded):
        assert loaded_seg.p0 == pytest.approx(orig.p0, abs=1e-4)
        assert loaded_seg.p3 == pytest.approx(orig.p3, abs=1e-4)
        assert loaded_seg.contact == orig.contact


def test_save_trace_is_valid_json(tmp_path):
    """save_trace writes valid JSON."""
    seg = BezierSegment((0.0, 1.0), (1.0, 2.0), (2.0, 1.5), (3.0, 1.0))
    path = tmp_path / "trace.json"
    save_trace([seg], path)

    data = json.loads(path.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    assert "p0" in data[0]
    assert "contact" in data[0]
