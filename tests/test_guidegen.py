"""Tests for scribesim/refextract/guidegen.py (ADV-SS-GUIDEGEN-001).

Red phase: should fail until guidegen.py is implemented.
"""

import math
import numpy as np
import pytest
from pathlib import Path

from scribesim.refextract.guidegen import (
    normalize_trace,
    dtw_align,
    average_traces,
    extract_keypoints,
    build_letterform_guide,
)
from scribesim.guides.keypoint import LetterformGuide, Keypoint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_segments_vertical(n=10):
    """Return BezierSegment-like objects forming a vertical stroke (x=0.5, y: 0→1)."""
    from scribesim.evo.genome import BezierSegment
    segs = []
    for i in range(n):
        y0 = i / n
        y1 = (i + 1) / n
        segs.append(BezierSegment(
            p0=(0.5, y0), p1=(0.5, y0 + (y1 - y0) / 3),
            p2=(0.5, y0 + 2 * (y1 - y0) / 3), p3=(0.5, y1),
            contact=True,
        ))
    return segs


def _make_segments_horizontal(n=5, x_start=0.0, x_end=1.0, y=0.5):
    """Return BezierSegment-like objects forming a horizontal stroke."""
    from scribesim.evo.genome import BezierSegment
    segs = []
    for i in range(n):
        x0 = x_start + (x_end - x_start) * i / n
        x1 = x_start + (x_end - x_start) * (i + 1) / n
        segs.append(BezierSegment(
            p0=(x0, y), p1=(x0 + (x1 - x0) / 3, y),
            p2=(x0 + 2 * (x1 - x0) / 3, y), p3=(x1, y),
            contact=True,
        ))
    return segs


# ---------------------------------------------------------------------------
# normalize_trace
# ---------------------------------------------------------------------------

def test_normalize_trace_baseline_at_zero():
    """After normalization, the minimum y maps to 0 and max y maps to 1."""
    segs = _make_segments_vertical()
    x_height_px = 100.0
    points = normalize_trace(segs, x_height_px)
    ys = [p[1] for p in points]
    assert abs(min(ys)) < 0.1, f"baseline should be near 0, got {min(ys):.3f}"
    assert abs(max(ys) - 1.0) < 0.1, f"top should be near 1, got {max(ys):.3f}"


def test_normalize_trace_start_at_zero():
    """After normalization, the x-coordinate of the first point is ~0."""
    segs = _make_segments_vertical()
    points = normalize_trace(segs, x_height_px=100.0)
    assert abs(points[0][0]) < 0.1, f"start x should be ~0, got {points[0][0]:.3f}"


def test_normalize_trace_returns_list_of_tuples():
    """normalize_trace returns a non-empty list of (x, y) tuples."""
    segs = _make_segments_vertical()
    points = normalize_trace(segs, x_height_px=100.0)
    assert len(points) > 0
    for p in points:
        assert len(p) == 2


def test_normalize_trace_skip_non_contact():
    """Non-contact segments are excluded from the sampled points."""
    from scribesim.evo.genome import BezierSegment
    segs = [
        BezierSegment(p0=(0.0, 0.0), p1=(0.1, 0.0), p2=(0.2, 0.0), p3=(0.3, 0.0), contact=True),
        BezierSegment(p0=(0.3, 0.0), p1=(0.4, 0.0), p2=(0.5, 0.0), p3=(0.6, 0.0), contact=False),
        BezierSegment(p0=(0.6, 0.0), p1=(0.7, 0.0), p2=(0.8, 0.0), p3=(0.9, 0.0), contact=True),
    ]
    # Should not raise; non-contact segment is skipped
    points = normalize_trace(segs, x_height_px=100.0)
    assert len(points) > 0


# ---------------------------------------------------------------------------
# dtw_align
# ---------------------------------------------------------------------------

def test_dtw_align_same_length_as_reference():
    """dtw_align returns a list with the same length as the reference."""
    trace = [(float(i), 0.0) for i in range(8)]
    reference = [(float(i), 0.0) for i in range(12)]
    aligned = dtw_align(trace, reference)
    assert len(aligned) == len(reference)


def test_dtw_align_reduces_distance():
    """Aligned L2 total distance ≤ unaligned L2 distance (on a offset trace)."""
    # Reference: y=0 line
    reference = [(float(i) / 10, 0.0) for i in range(11)]
    # Trace: y=0 but shifted 3 samples to the right (time-shifted)
    trace = [(float(i) / 10, 0.0) for i in range(3, 14)]

    aligned = dtw_align(trace, reference)

    # Unaligned: just truncate/pad trace to reference length, compute L2
    unaligned_dist = sum(
        (reference[i][0] - trace[min(i, len(trace)-1)][0])**2 +
        (reference[i][1] - trace[min(i, len(trace)-1)][1])**2
        for i in range(len(reference))
    )
    aligned_dist = sum(
        (reference[i][0] - aligned[i][0])**2 + (reference[i][1] - aligned[i][1])**2
        for i in range(len(reference))
    )
    assert aligned_dist <= unaligned_dist + 1e-9, (
        f"aligned dist {aligned_dist:.4f} > unaligned dist {unaligned_dist:.4f}"
    )


def test_dtw_align_identical_traces():
    """Aligning a trace to itself returns the same points."""
    trace = [(0.0, 0.0), (0.5, 0.5), (1.0, 0.0)]
    aligned = dtw_align(trace, trace)
    for i, (p, a) in enumerate(zip(trace, aligned)):
        assert abs(p[0] - a[0]) < 1e-9 and abs(p[1] - a[1]) < 1e-9, f"point {i} differs"


def test_dtw_align_single_point_trace():
    """Single-point trace aligned to reference returns one value per reference point."""
    trace = [(0.5, 0.5)]
    reference = [(0.0, 0.0), (0.5, 0.5), (1.0, 1.0)]
    aligned = dtw_align(trace, reference)
    assert len(aligned) == 3


# ---------------------------------------------------------------------------
# average_traces
# ---------------------------------------------------------------------------

def test_average_traces_single_trace():
    """Averaging a single trace returns it unchanged."""
    pts = [(0.0, 0.0), (0.5, 1.0), (1.0, 0.0)]
    result = average_traces([pts])
    assert len(result) == len(pts)
    for r, p in zip(result, pts):
        assert abs(r[0] - p[0]) < 0.01 and abs(r[1] - p[1]) < 0.01


def test_average_traces_two_identical():
    """Averaging two identical traces returns the same trace."""
    pts = [(0.0, 0.0), (0.5, 1.0), (1.0, 0.5)]
    result = average_traces([pts, pts])
    assert len(result) == len(pts)
    for r, p in zip(result, pts):
        assert abs(r[0] - p[0]) < 0.05 and abs(r[1] - p[1]) < 0.05


def test_average_traces_returns_same_length_as_first():
    """averaged trace has same number of points as the first trace."""
    t1 = [(float(i) / 10, 0.0) for i in range(11)]
    t2 = [(float(i) / 10, 0.1) for i in range(11)]
    t3 = [(float(i) / 10, -0.1) for i in range(11)]
    result = average_traces([t1, t2, t3])
    assert len(result) == len(t1)


def test_average_traces_midpoint():
    """Averaging two parallel offset traces returns the midpoint."""
    t1 = [(float(i) / 4, 0.0) for i in range(5)]
    t2 = [(float(i) / 4, 1.0) for i in range(5)]
    result = average_traces([t1, t2])
    for r in result:
        assert abs(r[1] - 0.5) < 0.15, f"expected y~0.5, got {r[1]:.3f}"


# ---------------------------------------------------------------------------
# extract_keypoints
# ---------------------------------------------------------------------------

def test_extract_keypoints_returns_start_end():
    """Keypoints always include an entry and exit point."""
    pts = [(float(i) / 10, math.sin(i / 10 * math.pi)) for i in range(11)]
    kps = extract_keypoints(pts)
    types = [k.point_type for k in kps]
    assert "entry" in types, f"no entry keypoint: {types}"
    assert "exit" in types, f"no exit keypoint: {types}"


def test_extract_keypoints_finds_apex():
    """A clear upward arch → at least one peak keypoint between entry and exit."""
    pts = [(float(i) / 20, math.sin(i / 20 * math.pi)) for i in range(21)]
    kps = extract_keypoints(pts)
    types = [k.point_type for k in kps]
    interior = types[1:-1]
    assert any(t in ("peak", "base") for t in interior), f"no peak/base: {types}"


def test_extract_keypoints_all_in_range():
    """All keypoint coordinates are finite and x ≥ 0."""
    pts = [(float(i) / 10, 0.5) for i in range(11)]
    kps = extract_keypoints(pts)
    for k in kps:
        assert math.isfinite(k.x) and math.isfinite(k.y)
        assert k.x >= 0.0


# ---------------------------------------------------------------------------
# build_letterform_guide
# ---------------------------------------------------------------------------

def test_build_letterform_guide_valid():
    """build_letterform_guide returns a LetterformGuide with expected fields."""
    segs = _make_segments_vertical()
    traces = [segs, segs, segs]  # 3 identical traces → should succeed
    guide = build_letterform_guide("n", traces, x_height_px=100.0)
    assert guide is not None
    assert isinstance(guide, LetterformGuide)
    assert guide.letter == "n"
    assert len(guide.keypoints) >= 2


def test_build_letterform_guide_x_advance_in_range():
    """x_advance should be a reasonable fraction of x-height (0.3 to 2.0)."""
    segs = _make_segments_horizontal(x_start=0.0, x_end=60.0)
    traces = [segs, segs, segs]
    guide = build_letterform_guide("u", traces, x_height_px=100.0)
    assert guide is not None
    assert 0.1 <= guide.x_advance <= 3.0, f"x_advance out of range: {guide.x_advance}"


def test_build_letterform_guide_fewer_than_3_returns_none():
    """With fewer than 3 traces, build_letterform_guide returns None."""
    segs = _make_segments_vertical()
    guide = build_letterform_guide("n", [segs, segs], x_height_px=100.0)
    assert guide is None


def test_build_letterform_guide_empty_traces_returns_none():
    """Empty trace list returns None."""
    guide = build_letterform_guide("n", [], x_height_px=100.0)
    assert guide is None


# ---------------------------------------------------------------------------
# ADV-SS-GUIDEGEN-002 — Part A: measure_ink_x_advance + bounding-box x_advance
# ---------------------------------------------------------------------------

def _make_ink_image(h: int, w: int, ink_left: int, ink_right: int) -> Path:
    """Write a grayscale PNG with an ink column from ink_left to ink_right."""
    import tempfile
    from PIL import Image
    arr = np.full((h, w), 240, dtype=np.uint8)
    arr[:, ink_left:ink_right] = 20  # dark ink band
    img = Image.fromarray(arr)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    return Path(tmp.name)


def test_measure_ink_x_advance_wide():
    """Full-width ink block returns ~1.0 (ink spans full x-height)."""
    from scribesim.refextract.guidegen import measure_ink_x_advance
    # 100px wide image, ink from 0 to 100 → width/x_height = 100/100 = 1.0
    p = _make_ink_image(h=100, w=100, ink_left=0, ink_right=100)
    result = measure_ink_x_advance([p], x_height_px=100.0)
    assert result is not None
    assert 0.8 <= result <= 1.2, f"Expected ~1.0, got {result}"


def test_measure_ink_x_advance_narrow():
    """Narrow central strip (30px wide in 100px image) returns ~0.3."""
    from scribesim.refextract.guidegen import measure_ink_x_advance
    p = _make_ink_image(h=100, w=100, ink_left=35, ink_right=65)
    result = measure_ink_x_advance([p], x_height_px=100.0)
    assert result is not None
    assert 0.2 <= result <= 0.5, f"Expected ~0.3, got {result}"


def test_measure_ink_x_advance_median():
    """Three images with widths 20, 40, 60px — returns median (40px / 100px = 0.4)."""
    from scribesim.refextract.guidegen import measure_ink_x_advance
    p1 = _make_ink_image(h=100, w=100, ink_left=40, ink_right=60)   # 20px
    p2 = _make_ink_image(h=100, w=100, ink_left=30, ink_right=70)   # 40px
    p3 = _make_ink_image(h=100, w=100, ink_left=20, ink_right=80)   # 60px
    result = measure_ink_x_advance([p1, p2, p3], x_height_px=100.0)
    assert result is not None
    assert 0.35 <= result <= 0.45, f"Expected ~0.40 (median), got {result}"


def test_build_letterform_guide_uses_bounding_box(tmp_path):
    """When exemplar_paths provided, x_advance comes from ink extent not trace endpoint."""
    # Make a looping trace where endpoint x ≈ 0 (like letter 'o') but ink spans ~0.5 x-height
    from scribesim.refextract.guidegen import build_letterform_guide, measure_ink_x_advance
    from scribesim.evo.genome import BezierSegment
    # Circular-ish trace: starts at (0.5, 0), goes to (1.0, 0.5), (0.5, 1.0), back to (0.0, 0.5)
    # Final point x ≈ 0 — endpoint would give wrong x_advance
    def _loop_segs():
        return [
            BezierSegment((0.5, 0.0), (1.0, 0.0), (1.0, 0.5), (1.0, 0.5)),
            BezierSegment((1.0, 0.5), (1.0, 1.0), (0.5, 1.0), (0.5, 1.0)),
            BezierSegment((0.5, 1.0), (0.0, 1.0), (0.0, 0.5), (0.0, 0.5)),
        ]
    traces = [_loop_segs(), _loop_segs(), _loop_segs()]
    # Exemplar images with ink spanning 40-60% of width (x_advance ≈ 0.4–0.6)
    exemplar_paths = [
        _make_ink_image(h=100, w=100, ink_left=30, ink_right=70),  # 40px
        _make_ink_image(h=100, w=100, ink_left=30, ink_right=70),  # 40px
        _make_ink_image(h=100, w=100, ink_left=30, ink_right=70),  # 40px
    ]
    guide_with = build_letterform_guide("o", traces, x_height_px=100.0,
                                        exemplar_paths=exemplar_paths)
    guide_without = build_letterform_guide("o", traces, x_height_px=100.0)
    assert guide_with is not None
    assert guide_without is not None
    # With bounding box: ~0.4; without: max trace extent ~1.0
    assert guide_with.x_advance < guide_without.x_advance, (
        f"Bounding-box x_advance ({guide_with.x_advance:.2f}) should be < "
        f"trace-endpoint x_advance ({guide_without.x_advance:.2f})"
    )
