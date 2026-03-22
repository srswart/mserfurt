"""Tests for scribesim/refextract/nibcal.py (ADV-SS-NIBCAL-001).

Red phase: should fail until nibcal.py is implemented.
"""

import math
import numpy as np
import pytest
from pathlib import Path

from scribesim.refextract.nibcal import (
    cast_ray,
    measure_stroke_width,
    estimate_nib_angle,
    estimate_nib_width,
    estimate_pressure_modulation,
    calibrate_nib,
    write_calibration_toml,
)


# ---------------------------------------------------------------------------
# cast_ray
# ---------------------------------------------------------------------------

def test_cast_ray_finds_boundary():
    """Ray cast perpendicular to a vertical ink stripe hits the boundary correctly."""
    # All-ink image with a white gap on the right
    binary = np.ones((20, 40), dtype=bool)
    binary[:, 25:] = False  # background starts at col 25

    # Start point inside ink at (10, 10), cast rightward (direction=0 = +x)
    dist = cast_ray(binary, (10.0, 10.0), direction_rad=0.0, max_distance=30)
    # Should hit boundary at col 25 → distance = 15 pixels
    assert abs(dist - 15.0) <= 2.0, f"expected ~15, got {dist}"


def test_cast_ray_no_boundary():
    """Ray cast into all-ink image returns max_distance."""
    binary = np.ones((20, 40), dtype=bool)
    dist = cast_ray(binary, (10.0, 10.0), direction_rad=0.0, max_distance=10)
    assert dist == pytest.approx(10.0, abs=1.0)


def test_cast_ray_immediate_background():
    """Ray starting outside ink region returns 0."""
    binary = np.zeros((20, 40), dtype=bool)  # all background
    dist = cast_ray(binary, (10.0, 10.0), direction_rad=0.0, max_distance=20)
    assert dist == pytest.approx(0.0, abs=1.0)


def test_cast_ray_upward():
    """Ray cast upward finds boundary at expected distance."""
    binary = np.ones((40, 20), dtype=bool)
    binary[:10, :] = False  # background in top 10 rows

    # Start at col=10, row=20; cast upward (direction = -π/2 = up in image coords)
    dist = cast_ray(binary, (10.0, 20.0), direction_rad=-math.pi / 2, max_distance=30)
    # Boundary at row 10, start at row 20 → ~10 pixels
    assert abs(dist - 10.0) <= 2.0, f"expected ~10, got {dist}"


# ---------------------------------------------------------------------------
# measure_stroke_width
# ---------------------------------------------------------------------------

def test_measure_stroke_width_uniform_horizontal():
    """Uniform-width horizontal stroke returns consistent width measurements."""
    # Create a 10-pixel-tall horizontal ink band
    img = np.full((40, 80), 255, dtype=np.uint8)
    img[15:25, 5:75] = 0  # 10px tall ink band

    # Centerline points along the middle of the band, horizontal
    centerline = [(float(x), 20.0) for x in range(10, 70, 5)]
    widths, directions = measure_stroke_width(img, centerline)

    assert len(widths) == len(centerline)
    assert len(directions) == len(centerline)

    # Most width measurements should be close to 10px (band height)
    # Allow some tolerance for endpoints and edge effects
    interior = widths[1:-1]
    if interior:
        median_w = float(np.median(interior))
        assert 6.0 <= median_w <= 16.0, f"expected ~10px width, got median={median_w}"


def test_measure_stroke_width_returns_directions():
    """Directions are returned as radians."""
    img = np.full((40, 80), 255, dtype=np.uint8)
    img[15:25, 5:75] = 0

    centerline = [(float(x), 20.0) for x in range(10, 70, 10)]
    widths, directions = measure_stroke_width(img, centerline)

    for d in directions:
        assert -math.pi <= d <= math.pi, f"direction out of range: {d}"


def test_measure_stroke_width_empty_centerline():
    """Empty centerline returns empty lists."""
    img = np.full((40, 80), 255, dtype=np.uint8)
    widths, directions = measure_stroke_width(img, [])
    assert widths == []
    assert directions == []


# ---------------------------------------------------------------------------
# estimate_nib_angle
# ---------------------------------------------------------------------------

def test_estimate_nib_angle_recovers_known_35():
    """Synthetic data from 35° nib → estimator recovers ~35° (±8°)."""
    rng = np.random.default_rng(42)
    true_angle = math.radians(35.0)
    directions = rng.uniform(0, math.pi, 200).tolist()
    # Width proportional to |sin(direction - nib_angle)|, plus small noise
    widths = [abs(math.sin(d - true_angle)) * 10 + rng.normal(0, 0.3)
              for d in directions]
    widths = [max(0.1, w) for w in widths]

    estimated = estimate_nib_angle(widths, directions)
    assert 25.0 <= estimated <= 55.0, f"out of Bastarda range: {estimated}"
    assert abs(estimated - 35.0) <= 8.0, f"expected ~35°, got {estimated:.1f}°"


def test_estimate_nib_angle_recovers_known_45():
    """Synthetic data from 45° nib → estimator recovers ~45° (±8°)."""
    rng = np.random.default_rng(7)
    true_angle = math.radians(45.0)
    directions = rng.uniform(0, math.pi, 300).tolist()
    widths = [abs(math.sin(d - true_angle)) * 8 + rng.normal(0, 0.2)
              for d in directions]
    widths = [max(0.1, w) for w in widths]

    estimated = estimate_nib_angle(widths, directions)
    assert abs(estimated - 45.0) <= 8.0, f"expected ~45°, got {estimated:.1f}°"


def test_estimate_nib_angle_returns_float_in_range():
    """estimate_nib_angle always returns a float in [25, 55]."""
    widths = [5.0] * 50
    directions = [0.5] * 50
    result = estimate_nib_angle(widths, directions)
    assert isinstance(result, float)
    assert 25.0 <= result <= 55.0


# ---------------------------------------------------------------------------
# estimate_nib_width
# ---------------------------------------------------------------------------

def test_estimate_nib_width_percentile():
    """95th percentile of widths 1..20 pixels at 300 DPI → correct mm."""
    widths = list(range(1, 21))  # 1..20 px; 95th pct ≈ 19.05
    result_mm = estimate_nib_width(widths, dpi=300.0)
    expected_mm = 19.05 / 300.0 * 25.4  # ≈ 1.613 mm
    assert abs(result_mm - expected_mm) < 0.1, f"expected ~{expected_mm:.3f}, got {result_mm:.3f}"


def test_estimate_nib_width_single_value():
    """Single width value returns that value converted to mm."""
    result_mm = estimate_nib_width([30.0], dpi=300.0)
    expected = 30.0 / 300.0 * 25.4
    assert abs(result_mm - expected) < 0.01


def test_estimate_nib_width_uses_dpi():
    """Higher DPI → smaller mm output for same pixel width."""
    widths = [60.0] * 10
    w_300 = estimate_nib_width(widths, dpi=300.0)
    w_600 = estimate_nib_width(widths, dpi=600.0)
    assert w_300 > w_600


# ---------------------------------------------------------------------------
# estimate_pressure_modulation
# ---------------------------------------------------------------------------

def test_estimate_pressure_modulation_zero_variance():
    """When all widths are identical, pressure modulation is ~0."""
    widths = [10.0] * 100
    directions = [float(i) * 0.1 for i in range(100)]
    result = estimate_pressure_modulation(widths, directions)
    assert result < 0.05, f"expected near 0, got {result}"


def test_estimate_pressure_modulation_high_variance():
    """High within-group variance → higher pressure modulation."""
    rng = np.random.default_rng(99)
    # Two direction groups with high within-group width variance
    directions = [0.1] * 50 + [1.5] * 50
    widths = rng.uniform(2, 18, 100).tolist()  # high variance
    result = estimate_pressure_modulation(widths, directions)
    assert result > 0.0


def test_estimate_pressure_modulation_clamped():
    """Result is always in [0, 1]."""
    widths = list(range(1, 101))
    directions = [float(i % 12) * 0.25 for i in range(100)]
    result = estimate_pressure_modulation(widths, directions)
    assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# calibrate_nib (end-to-end)
# ---------------------------------------------------------------------------

def test_calibrate_nib_returns_required_keys():
    """calibrate_nib returns dict with all required parameter keys."""
    rng = np.random.default_rng(0)
    widths = rng.uniform(3, 15, 200).tolist()
    directions = rng.uniform(0, math.pi, 200).tolist()

    result = calibrate_nib(widths, directions, dpi=300.0)

    assert "nib.angle_deg" in result
    assert "nib.width_mm" in result
    assert "nib.min_hairline_ratio" in result
    assert "stroke.pressure_modulation_range" in result


def test_calibrate_nib_angle_in_range():
    """Calibrated nib angle is in Bastarda range [25°, 55°]."""
    rng = np.random.default_rng(1)
    widths = rng.uniform(3, 15, 100).tolist()
    directions = rng.uniform(0, math.pi, 100).tolist()
    result = calibrate_nib(widths, directions)
    assert 25.0 <= result["nib.angle_deg"] <= 55.0


def test_calibrate_nib_hairline_ratio():
    """min_hairline_ratio = 5th_pct / 95th_pct, in [0, 1]."""
    widths = list(range(1, 21))
    directions = [0.5] * 20
    result = calibrate_nib(widths, directions)
    ratio = result["nib.min_hairline_ratio"]
    assert 0.0 <= ratio <= 1.0
    # 5th pct ≈ 1.95, 95th pct ≈ 19.05 → ratio ≈ 0.10
    assert ratio < 0.5


# ---------------------------------------------------------------------------
# write_calibration_toml
# ---------------------------------------------------------------------------

def test_write_calibration_toml_creates_file(tmp_path):
    """write_calibration_toml creates a TOML file at the specified path."""
    params = {
        "nib.angle_deg": 37.5,
        "nib.width_mm": 1.6,
        "nib.min_hairline_ratio": 0.12,
        "stroke.pressure_modulation_range": 0.25,
    }
    out = tmp_path / "nib_calibrated.toml"
    write_calibration_toml(params, out)
    assert out.exists()
    content = out.read_text()
    assert "nib" in content.lower()
    assert "37.5" in content or "37" in content


def test_write_calibration_toml_contains_all_params(tmp_path):
    """All parameter keys appear in the TOML output."""
    params = {
        "nib.angle_deg": 42.0,
        "nib.width_mm": 1.8,
        "nib.min_hairline_ratio": 0.15,
        "stroke.pressure_modulation_range": 0.30,
    }
    out = tmp_path / "cal.toml"
    write_calibration_toml(params, out)
    content = out.read_text()
    assert "angle_deg" in content
    assert "width_mm" in content
    assert "min_hairline_ratio" in content
    assert "pressure_modulation_range" in content


def test_write_calibration_toml_with_comment(tmp_path):
    """Comment string appears in the TOML output."""
    params = {"nib.angle_deg": 40.0, "nib.width_mm": 1.5,
              "nib.min_hairline_ratio": 0.1,
              "stroke.pressure_modulation_range": 0.2}
    out = tmp_path / "cal.toml"
    write_calibration_toml(params, out, comment="Calibrated from Werbeschreiben")
    assert "Werbeschreiben" in out.read_text()
