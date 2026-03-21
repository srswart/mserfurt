"""Unit tests for physics-based nib model — ADV-SS-NIB-002."""

from __future__ import annotations

import math

import pytest

from scribesim.render.nib import PhysicsNib, mark_width, stroke_direction


# ---------------------------------------------------------------------------
# Test mark_width — direction-dependent width
# ---------------------------------------------------------------------------

class TestMarkWidth:
    def test_perpendicular_to_nib_is_widest(self):
        """Stroke perpendicular to nib angle produces maximum base width."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0, flexibility=0.0)
        # Perpendicular = nib_angle + 90 = 130°
        w = mark_width(nib, direction_deg=130.0, pressure=0.5, t=0.5)
        # sin(130 - 40) = sin(90) = 1.0 → width ≈ nib_width
        assert w == pytest.approx(1.8, abs=0.1)

    def test_parallel_to_nib_is_hairline(self):
        """Stroke parallel to nib angle produces hairline (minimum width)."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0, flexibility=0.0, cut_quality=1.0)
        # Parallel = same angle as nib → sin(0) = 0
        w = mark_width(nib, direction_deg=40.0, pressure=0.5, t=0.5)
        # Hairline min = 1.8 * 0.05 = 0.09 (cut_quality=1.0)
        assert w < 0.2
        assert w > 0.0

    def test_horizontal_stroke_at_40deg_nib(self):
        """Horizontal stroke (0°) at 40° nib: sin(0 - 40) = sin(-40°) ≈ 0.643."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0, flexibility=0.0)
        w = mark_width(nib, direction_deg=0.0, pressure=0.5, t=0.5)
        expected_base = 1.8 * abs(math.sin(math.radians(-40)))
        assert w == pytest.approx(expected_base, abs=0.05)

    def test_vertical_stroke_at_40deg_nib(self):
        """Vertical stroke (90°) at 40° nib: sin(90 - 40) = sin(50°) ≈ 0.766."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0, flexibility=0.0)
        w = mark_width(nib, direction_deg=90.0, pressure=0.5, t=0.5)
        expected_base = 1.8 * abs(math.sin(math.radians(50)))
        assert w == pytest.approx(expected_base, abs=0.05)

    def test_vertical_wider_than_horizontal(self):
        """At 40° nib, vertical strokes are wider than horizontal."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0, flexibility=0.0)
        w_horiz = mark_width(nib, direction_deg=0.0, pressure=0.5, t=0.5)
        w_vert = mark_width(nib, direction_deg=90.0, pressure=0.5, t=0.5)
        assert w_vert > w_horiz

    def test_45deg_stroke_intermediate_width(self):
        """A 45° stroke at 40° nib is between hairline and max width."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0, flexibility=0.0)
        w_hairline = mark_width(nib, direction_deg=40.0, pressure=0.5, t=0.5)
        w_max = mark_width(nib, direction_deg=130.0, pressure=0.5, t=0.5)
        w_mid = mark_width(nib, direction_deg=45.0, pressure=0.5, t=0.5)
        assert w_hairline < w_mid < w_max


# ---------------------------------------------------------------------------
# Test flexibility
# ---------------------------------------------------------------------------

class TestPressureModulation:
    """TD-004 Fix B: pressure modulates ±20% (range 0.8 to 1.2)."""

    def test_high_pressure_wider(self):
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0)
        w_low = mark_width(nib, direction_deg=90.0, pressure=0.0, t=0.5)
        w_high = mark_width(nib, direction_deg=90.0, pressure=1.0, t=0.5)
        assert w_high > w_low

    def test_pressure_range_limited(self):
        """Pressure effect should be modest — ±20%, not 0-100%."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0)
        w_zero = mark_width(nib, direction_deg=90.0, pressure=0.0, t=0.5)
        w_full = mark_width(nib, direction_deg=90.0, pressure=1.0, t=0.5)
        ratio = w_full / w_zero
        # Should be ~1.5 (1.2/0.8), not wildly different
        assert 1.2 < ratio < 1.8

    def test_hairline_unaffected_by_pressure(self):
        """At hairline direction, pressure shouldn't make it thick."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0)
        w_hair_high = mark_width(nib, direction_deg=40.0, pressure=1.0, t=0.5)
        w_full = mark_width(nib, direction_deg=130.0, pressure=0.5, t=0.5)
        # Hairline should still be much thinner than full stroke
        assert w_hair_high < w_full * 0.3


# ---------------------------------------------------------------------------
# Test stroke foot and attack (TD-004 Fix C, D)
# ---------------------------------------------------------------------------

class TestStrokeEffects:
    def test_foot_thickens_at_end(self):
        """Stroke foot produces diamond feet at end of downstrokes."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0)
        w_mid = mark_width(nib, direction_deg=270.0, pressure=0.7, t=0.5)
        w_foot = mark_width(nib, direction_deg=270.0, pressure=0.7, t=0.92)
        assert w_foot > w_mid

    def test_attack_thickens_at_start(self):
        """Stroke onset produces slight thickening."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0)
        w_start = mark_width(nib, direction_deg=270.0, pressure=0.7, t=0.02)
        w_mid = mark_width(nib, direction_deg=270.0, pressure=0.7, t=0.5)
        assert w_start > w_mid

    def test_mid_stroke_no_effects(self):
        """Middle of stroke has neither foot nor attack."""
        from scribesim.render.nib import stroke_foot_effect, stroke_attack_effect
        fw, fi = stroke_foot_effect(0.5)
        aw, ai = stroke_attack_effect(0.5)
        assert fw == 1.0
        assert fi == 1.0
        assert aw == 1.0
        assert ai == 1.0


# ---------------------------------------------------------------------------
# Test attack and release
# ---------------------------------------------------------------------------

class TestThickThinRatio:
    """TD-004 Fix E: verify the thick/thin ratio is ≥3:1."""

    def test_ratio_at_least_3_to_1(self):
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0)
        w_full = mark_width(nib, direction_deg=130.0, pressure=0.7, t=0.5)
        w_hair = mark_width(nib, direction_deg=40.0, pressure=0.5, t=0.5)
        ratio = w_full / w_hair
        assert ratio >= 3.0

    def test_hairline_is_thin_in_pixels(self):
        """Hairline should be ~2px at 300 DPI."""
        nib = PhysicsNib(width_mm=1.8, angle_deg=40.0)
        w_hair = mark_width(nib, direction_deg=40.0, pressure=0.5, t=0.5)
        px = w_hair * (300 / 25.4)
        assert 1 <= px <= 4  # 1-4 pixels is a good hairline range


# ---------------------------------------------------------------------------
# Test stroke_direction
# ---------------------------------------------------------------------------

class TestStrokeDirection:
    def test_horizontal_right(self):
        pts = [(0, 0, 0.0), (1, 0, 0.5), (2, 0, 1.0)]
        d = stroke_direction(pts, 1)
        assert d == pytest.approx(0.0, abs=0.1)

    def test_vertical_down(self):
        pts = [(0, 0, 0.0), (0, 1, 0.5), (0, 2, 1.0)]
        d = stroke_direction(pts, 1)
        assert d == pytest.approx(90.0, abs=0.1)

    def test_diagonal_45(self):
        pts = [(0, 0, 0.0), (1, 1, 0.5), (2, 2, 1.0)]
        d = stroke_direction(pts, 1)
        assert d == pytest.approx(45.0, abs=0.1)

    def test_endpoint_uses_forward_difference(self):
        pts = [(0, 0, 0.0), (1, 0, 0.5), (2, 0, 1.0)]
        d = stroke_direction(pts, 0)
        assert d == pytest.approx(0.0, abs=0.1)

    def test_last_point_uses_backward_difference(self):
        pts = [(0, 0, 0.0), (1, 0, 0.5), (2, 0, 1.0)]
        d = stroke_direction(pts, 2)
        assert d == pytest.approx(0.0, abs=0.1)

    def test_single_point_returns_zero(self):
        pts = [(0, 0, 0.0)]
        d = stroke_direction(pts, 0)
        assert d == 0.0
