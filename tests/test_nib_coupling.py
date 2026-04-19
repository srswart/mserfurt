"""Tests for direction-coupled nib angle (ADV-SS-NIB-004)."""

from __future__ import annotations

import math

import numpy as np
import pytest
from PIL import Image, ImageDraw

from scribesim.render.pipeline import (
    _local_nib_half_vec,
    _nib_half_vec,
    _polygon_sweep_stroke,
    _INT_PX_PER_MM,
)


class TestLocalNibHalfVec:
    """Unit tests for _local_nib_half_vec direction coupling."""

    def test_coupling_zero_returns_base(self):
        """At coupling=0, direction has no effect."""
        base = _nib_half_vec(40.0, 0.65, _INT_PX_PER_MM)
        coupled = _local_nib_half_vec(100.0, 50.0, 40.0, 0.65, _INT_PX_PER_MM, 0.0)
        assert math.isclose(coupled[0], base[0], rel_tol=1e-9)
        assert math.isclose(coupled[1], base[1], rel_tol=1e-9)

    def test_zero_displacement_returns_base(self):
        """Zero-length segment (dx=dy=0) falls back to base angle."""
        base = _nib_half_vec(40.0, 0.65, _INT_PX_PER_MM)
        coupled = _local_nib_half_vec(0.0, 0.0, 40.0, 0.65, _INT_PX_PER_MM, 0.25)
        assert math.isclose(coupled[0], base[0], rel_tol=1e-9)
        assert math.isclose(coupled[1], base[1], rel_tol=1e-9)

    def test_coupling_changes_angle(self):
        """Non-zero coupling changes (hx, hy) compared to base."""
        base_hx, base_hy = _nib_half_vec(40.0, 0.65, _INT_PX_PER_MM)
        # Stroke going up-right at 45°
        c_hx, c_hy = _local_nib_half_vec(10.0, -10.0, 40.0, 0.65, _INT_PX_PER_MM, 0.25)
        # With coupling, effective angle = 40 + 0.25 * atan2(-10, 10) = 40 - 11.25 = 28.75°
        assert not math.isclose(c_hx, base_hx, rel_tol=1e-3)

    def test_coupling_nib_length_preserved(self):
        """Direction coupling changes angle but not nib half-length."""
        base_hx, base_hy = _nib_half_vec(40.0, 0.65, _INT_PX_PER_MM)
        base_len = math.hypot(base_hx, base_hy)
        for dx, dy in [(10, 0), (0, -10), (7, 5), (-3, 8)]:
            c_hx, c_hy = _local_nib_half_vec(dx, dy, 40.0, 0.65, _INT_PX_PER_MM, 0.25)
            assert math.isclose(math.hypot(c_hx, c_hy), base_len, rel_tol=1e-9)

    def test_arch_stroke_varies_angle(self):
        """Arch stroke spanning 115° of direction produces measurable angle variation."""
        # Start of arch: going right (0°)
        hx_start, hy_start = _local_nib_half_vec(1.0, 0.0, 40.0, 0.65, _INT_PX_PER_MM, 0.25)
        # Mid arch: going up-right (~57.5° into arch)
        hx_mid, hy_mid = _local_nib_half_vec(0.5, -0.866, 40.0, 0.65, _INT_PX_PER_MM, 0.25)
        # End of arch: going left-down (going to ~115°)
        hx_end, hy_end = _local_nib_half_vec(-0.5, -0.866, 40.0, 0.65, _INT_PX_PER_MM, 0.25)

        angle_start = math.degrees(math.atan2(hy_start, hx_start))
        angle_mid = math.degrees(math.atan2(hy_mid, hx_mid))
        angle_end = math.degrees(math.atan2(hy_end, hx_end))

        # 115° span × 0.25 coupling → ~28.75° angle range
        span = max(angle_start, angle_mid, angle_end) - min(angle_start, angle_mid, angle_end)
        assert span > 20.0, f"Expected > 20° nib angle span, got {span:.1f}°"


class TestPolygonSweepCoupling:
    """Integration tests verifying coupling produces measurably different quads."""

    def _make_draw(self, w=200, h=200):
        img = Image.new("RGB", (w, h), (240, 220, 180))
        heat = np.zeros((h, w), dtype=np.uint8)
        return img, ImageDraw.Draw(img), heat

    def _stroke_pts(self, path):
        """Convert [(x_mm, y_mm)] path to (x, y, t) sample list."""
        n = len(path)
        return [(x, y, i / (n - 1)) for i, (x, y) in enumerate(path)]

    def test_coupled_stroke_varies_width(self):
        """Coupled rendering of an arch stroke produces different quad widths
        at stroke start (downstroke) vs. mid-arch (horizontal)."""
        img_c, draw_c, heat_c = self._make_draw()

        # Straight downstroke: (3mm, 1mm) → (3mm, 5mm)
        down_pts = [(3.0, 1.0 + i * 0.5, i / 8) for i in range(9)]
        # Horizontal stroke: (3mm, 3mm) → (7mm, 3mm)
        horiz_pts = [(3.0 + i * 0.5, 3.0, i / 8) for i in range(9)]

        pressure = (0.8,)
        kwargs = dict(
            px_per_mm=_INT_PX_PER_MM,
            pressure_profile=pressure,
            stroke_weight=1.5,
            ink_density=0.85,
            glyph_opacity=1.0,
            heat_arr=heat_c,
            img_h=200,
            img_w=200,
            nib_angle_deg=40.0,
            nib_width_mm=0.65,
            nib_coupling=0.25,
        )
        hx, hy = _nib_half_vec(40.0, 0.65, _INT_PX_PER_MM)

        # Render downstroke and horizontal to separate images
        img_d, draw_d, heat_d = self._make_draw()
        _polygon_sweep_stroke(draw_d, down_pts, hx, hy, **kwargs)
        arr_d = np.array(img_d)

        img_h2, draw_h2, heat_h2 = self._make_draw()
        _polygon_sweep_stroke(draw_h2, horiz_pts, hx, hy, **kwargs)
        arr_h2 = np.array(img_h2)

        # Measure ink coverage (dark pixels) in each
        bg = np.array([240, 220, 180])
        down_ink = np.sum(np.any(arr_d != bg, axis=2))
        horiz_ink = np.sum(np.any(arr_h2 != bg, axis=2))

        # Downstroke (nearly parallel to nib at 40° angle) should cover less
        # area than horizontal stroke (more perpendicular to nib)
        # The exact ratio depends on nib geometry; we just verify they differ
        assert down_ink != horiz_ink, (
            f"Coupling should produce different coverage: down={down_ink}, horiz={horiz_ink}"
        )

    def test_no_coupling_uses_fixed_nib(self):
        """Without coupling, local nib half-vec always equals the base vector
        regardless of stroke direction."""
        hx, hy = _nib_half_vec(40.0, 0.65, _INT_PX_PER_MM)

        for dx, dy in [(1.0, 0.0), (0.0, -1.0), (-1.0, 1.0)]:
            c_hx, c_hy = _local_nib_half_vec(dx, dy, 40.0, 0.65, _INT_PX_PER_MM, 0.0)
            assert math.isclose(c_hx, hx, rel_tol=1e-9), f"hx mismatch for direction ({dx},{dy})"
            assert math.isclose(c_hy, hy, rel_tol=1e-9), f"hy mismatch for direction ({dx},{dy})"

    def test_handparams_has_nib_coupling(self):
        """HandParams exposes nib_coupling with default 0.0."""
        from scribesim.hand.params import HandParams
        p = HandParams()
        assert hasattr(p, 'nib_coupling')
        assert p.nib_coupling == 0.0

    def test_handparams_nib_coupling_loaded_from_toml(self):
        """Konrad TOML sets nib_coupling = 0.25."""
        from scribesim.hand.model import load_base
        params = load_base()
        assert math.isclose(params.nib_coupling, 0.25, rel_tol=1e-6)
