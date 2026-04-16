"""Integration tests for v2 rendering pipeline — ADV-SS-RENDER-002."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scribesim.hand.params import HandParams
from scribesim.hand.profile import HandProfile, load_profile, resolve_profile
from scribesim.layout.geometry import PageGeometry
from scribesim.layout.positioned import PositionedGlyph, LineLayout, PageLayout
from scribesim.render.pipeline import (
    render_pipeline,
    _page_size_output,
    _page_size_internal,
    _INTERNAL_DPI,
    _OUTPUT_DPI,
    _nib_half_vec,
    _polygon_sweep_stroke,
    _ink_color,
    _INT_PX_PER_MM,
    _PARCHMENT_RGB,
    _INK_RGB,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"


def _make_geometry() -> PageGeometry:
    return PageGeometry(
        page_w_mm=280.0, page_h_mm=400.0,
        margin_top=25.0, margin_bottom=70.0,
        margin_inner=25.0, margin_outer=50.0,
        ruling_pitch_mm=9.5, x_height_mm=3.8, folio_format="standard",
    )


def _make_minimal_layout() -> PageLayout:
    """Layout with a few glyphs for fast rendering."""
    geom = _make_geometry()
    glyphs = [
        PositionedGlyph(glyph_id="a", x_mm=30.0, y_mm=30.0,
                        baseline_y_mm=39.5, advance_w_mm=3.0),
        PositionedGlyph(glyph_id="b", x_mm=33.0, y_mm=30.0,
                        baseline_y_mm=39.5, advance_w_mm=3.0),
        PositionedGlyph(glyph_id="c", x_mm=36.0, y_mm=30.0,
                        baseline_y_mm=39.5, advance_w_mm=3.0),
    ]
    lines = [LineLayout(line_index=0, y_mm=30.0, glyphs=glyphs)]
    return PageLayout(folio_id="f01r", geometry=geom, lines=lines)


# ---------------------------------------------------------------------------
# TestResolutionScaling
# ---------------------------------------------------------------------------

class TestResolutionScaling:
    def test_internal_larger_than_output(self):
        layout = _make_minimal_layout()
        int_w, int_h = _page_size_internal(layout)
        out_w, out_h = _page_size_output(layout)
        assert int_w > out_w
        assert int_h > out_h

    def test_scale_ratio(self):
        layout = _make_minimal_layout()
        int_w, int_h = _page_size_internal(layout)
        out_w, out_h = _page_size_output(layout)
        ratio_w = int_w / out_w
        ratio_h = int_h / out_h
        expected = _INTERNAL_DPI / _OUTPUT_DPI
        assert ratio_w == pytest.approx(expected, abs=0.02)
        assert ratio_h == pytest.approx(expected, abs=0.02)


# ---------------------------------------------------------------------------
# TestPipelineOutput
# ---------------------------------------------------------------------------

class TestPipelineOutput:
    def test_produces_page_png(self, tmp_path):
        layout = _make_minimal_layout()
        params = HandParams()
        page_path, _ = render_pipeline(layout, params, tmp_path, "f01r")
        assert page_path.exists()
        assert page_path.suffix == ".png"

    def test_produces_heatmap_png(self, tmp_path):
        layout = _make_minimal_layout()
        params = HandParams()
        _, heatmap_path = render_pipeline(layout, params, tmp_path, "f01r")
        assert heatmap_path.exists()
        assert heatmap_path.suffix == ".png"

    def test_output_dimensions_300dpi(self, tmp_path):
        layout = _make_minimal_layout()
        params = HandParams()
        page_path, heatmap_path = render_pipeline(layout, params, tmp_path, "f01r")

        page_img = Image.open(page_path)
        heat_img = Image.open(heatmap_path)

        out_w, out_h = _page_size_output(layout)
        assert page_img.size == (out_w, out_h)
        assert heat_img.size == (out_w, out_h)

    def test_page_is_rgb(self, tmp_path):
        layout = _make_minimal_layout()
        params = HandParams()
        page_path, _ = render_pipeline(layout, params, tmp_path, "f01r")
        img = Image.open(page_path)
        assert img.mode == "RGB"

    def test_heatmap_is_grayscale(self, tmp_path):
        layout = _make_minimal_layout()
        params = HandParams()
        _, heatmap_path = render_pipeline(layout, params, tmp_path, "f01r")
        img = Image.open(heatmap_path)
        assert img.mode == "L"

    def test_page_has_ink(self, tmp_path):
        """Rendered page should contain non-parchment pixels (ink)."""
        layout = _make_minimal_layout()
        params = HandParams()
        page_path, _ = render_pipeline(layout, params, tmp_path, "f01r")
        img = np.array(Image.open(page_path))
        parchment = np.array([245, 238, 220])
        diff = np.linalg.norm(img.astype(float) - parchment, axis=2)
        assert (diff > 30).any()  # some ink pixels

    def test_heatmap_has_pressure(self, tmp_path):
        layout = _make_minimal_layout()
        params = HandParams()
        _, heatmap_path = render_pipeline(layout, params, tmp_path, "f01r")
        heat = np.array(Image.open(heatmap_path))
        assert heat.max() > 0

    def test_with_profile_ink_filters(self, tmp_path):
        """Pipeline with profile applies ink filters."""
        layout = _make_minimal_layout()
        params = HandParams()
        profile = HandProfile()
        page_no_profile, _ = render_pipeline(layout, params, tmp_path / "no_profile", "f01r")
        page_with_profile, _ = render_pipeline(layout, params, tmp_path / "with_profile", "f01r", profile=profile)

        img_no = np.array(Image.open(page_no_profile))
        img_with = np.array(Image.open(page_with_profile))
        # Should differ due to ink filters
        assert not np.array_equal(img_no, img_with)


# ---------------------------------------------------------------------------
# TestDeterminism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_output(self, tmp_path):
        layout = _make_minimal_layout()
        params = HandParams()
        p1, _ = render_pipeline(layout, params, tmp_path / "r1", "f01r")
        p2, _ = render_pipeline(layout, params, tmp_path / "r2", "f01r")
        img1 = np.array(Image.open(p1))
        img2 = np.array(Image.open(p2))
        np.testing.assert_array_equal(img1, img2)


# ---------------------------------------------------------------------------
# TestNibHalfVec — geometry helpers (TD-015 / ADV-SS-RENDER-004)
# ---------------------------------------------------------------------------

class TestNibHalfVec:
    def test_returns_tuple_of_two_floats(self):
        hx, hy = _nib_half_vec(40.0, 1.8, _INT_PX_PER_MM)
        assert isinstance(hx, float)
        assert isinstance(hy, float)

    def test_nib_at_40deg_hx_greater_than_hy(self):
        # cos(40°) > sin(40°), so hx > hy for nib angles < 45°
        hx, hy = _nib_half_vec(40.0, 1.8, _INT_PX_PER_MM)
        assert hx > hy

    def test_nib_at_45deg_hx_equals_hy(self):
        hx, hy = _nib_half_vec(45.0, 1.8, _INT_PX_PER_MM)
        assert abs(hx - hy) < 0.001

    def test_scale_with_nib_width(self):
        hx1, hy1 = _nib_half_vec(40.0, 1.0, _INT_PX_PER_MM)
        hx2, hy2 = _nib_half_vec(40.0, 2.0, _INT_PX_PER_MM)
        assert abs(hx2 / hx1 - 2.0) < 0.001
        assert abs(hy2 / hy1 - 2.0) < 0.001

    def test_full_nib_to_hairline_ratio_exceeds_3(self):
        # Full nib (2*hx) vs hairline nib (6.5% of full nib) → ratio >> 3
        # This is the meaningful thick/thin ratio for Bastarda polygon sweep.
        nib_width_mm = 1.8
        hx_full, _ = _nib_half_vec(40.0, nib_width_mm, _INT_PX_PER_MM)
        hx_hair, _ = _nib_half_vec(40.0, nib_width_mm * 0.065, _INT_PX_PER_MM)
        ratio = (2 * hx_full) / (2 * hx_hair)
        assert ratio >= 3.0, f"Expected >= 3.0, got {ratio:.2f}"

    def test_ink_color_full_alpha_is_ink(self):
        assert _ink_color(1.0) == _INK_RGB

    def test_ink_color_zero_alpha_is_parchment(self):
        assert _ink_color(0.0) == _PARCHMENT_RGB

    def test_ink_color_clamps(self):
        assert _ink_color(-0.5) == _PARCHMENT_RGB
        assert _ink_color(1.5) == _INK_RGB


# ---------------------------------------------------------------------------
# TestPolygonSweep — the new stroke renderer (TD-015 / ADV-SS-RENDER-004)
# ---------------------------------------------------------------------------

def _draw_vertical_stroke(hx, hy, px_per_mm, canvas_px=200):
    """Render a straight vertical stroke via polygon sweep to a small canvas."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (canvas_px, canvas_px), _PARCHMENT_RGB)
    draw = ImageDraw.Draw(img)
    heat = np.zeros((canvas_px, canvas_px), dtype=np.uint8)

    # Vertical stroke: x = 5mm, y from 1mm to 11mm
    x_mm = 5.0
    pts = [(x_mm, 1.0 + i * 0.1, i / 100.0) for i in range(101)]
    _polygon_sweep_stroke(
        draw, pts, hx, hy, px_per_mm,
        (0.49, 0.63, 0.63, 0.49),  # _BODY pressure profile
        stroke_weight=0.9,
        ink_density=0.85,
        glyph_opacity=1.0,
        heat_arr=heat,
        img_h=canvas_px,
        img_w=canvas_px,
    )
    return np.array(img)


def _draw_nib_angle_stroke(hx, hy, px_per_mm, nib_angle_deg=40.0, canvas_px=200):
    """Render a stroke going at the nib angle — should produce minimum width."""
    from PIL import Image, ImageDraw
    import math

    img = Image.new("RGB", (canvas_px, canvas_px), _PARCHMENT_RGB)
    draw = ImageDraw.Draw(img)
    heat = np.zeros((canvas_px, canvas_px), dtype=np.uint8)

    # Stroke going at nib_angle_deg (the hairline direction)
    angle_rad = math.radians(nib_angle_deg)
    start_x, start_y = 2.0, 6.0
    pts = [(start_x + i * 0.1 * math.cos(angle_rad),
            start_y + i * 0.1 * math.sin(angle_rad),
            i / 100.0)
           for i in range(101)]
    _polygon_sweep_stroke(
        draw, pts, hx, hy, px_per_mm,
        (0.49, 0.63, 0.63, 0.49),
        stroke_weight=0.9,
        ink_density=0.85,
        glyph_opacity=1.0,
        heat_arr=heat,
        img_h=canvas_px,
        img_w=canvas_px,
    )
    return np.array(img)


class TestPolygonSweep:
    def _ink_pixels(self, arr, threshold=220):
        """Count pixels darker than threshold (ink vs parchment)."""
        return int(np.sum(arr.min(axis=2) < threshold))

    def _horizontal_ink_width(self, arr, threshold=220):
        """Max horizontal span of ink pixels across any single row."""
        max_width = 0
        for row in arr:
            ink = row.min(axis=1) < threshold
            if ink.any():
                cols = np.where(ink)[0]
                max_width = max(max_width, int(cols[-1] - cols[0] + 1))
        return max_width

    def test_vertical_stroke_has_ink(self):
        hx, hy = _nib_half_vec(40.0, 1.8, _INT_PX_PER_MM)
        arr = _draw_vertical_stroke(hx, hy, _INT_PX_PER_MM)
        assert self._ink_pixels(arr) > 0, "Vertical stroke produced no ink"

    def test_vertical_stroke_has_minimum_width(self):
        # At 400 DPI with 1.8mm nib at 40°, vertical stroke should be ≥ 10px wide
        hx, hy = _nib_half_vec(40.0, 1.8, _INT_PX_PER_MM)
        arr = _draw_vertical_stroke(hx, hy, _INT_PX_PER_MM)
        width = self._horizontal_ink_width(arr)
        assert width >= 10, f"Vertical stroke too narrow: {width}px (expected ≥ 10)"

    def test_vertical_wider_than_hairline_angle_stroke(self):
        # Vertical stroke should be substantially wider horizontally than a
        # stroke going at the nib angle (the hairline direction).
        nib_width_mm = 1.8
        hx_full, hy_full = _nib_half_vec(40.0, nib_width_mm, _INT_PX_PER_MM)
        hx_hair, hy_hair = _nib_half_vec(40.0, nib_width_mm * 0.065, _INT_PX_PER_MM)

        arr_vert = _draw_vertical_stroke(hx_full, hy_full, _INT_PX_PER_MM)
        arr_hair = _draw_nib_angle_stroke(hx_hair, hy_hair, _INT_PX_PER_MM)

        w_vert = self._horizontal_ink_width(arr_vert)
        w_hair = self._horizontal_ink_width(arr_hair)

        assert w_vert > 0, "Vertical stroke produced no measurable width"
        assert w_hair > 0, "Hairline stroke produced no measurable width"

        ratio = w_vert / max(1, w_hair)
        assert ratio >= 3.0, (
            f"Expected thick/thin ratio ≥ 3.0, got {ratio:.2f} "
            f"(vertical={w_vert}px, hairline={w_hair}px)"
        )

    def test_pipeline_has_ink_after_polygon_sweep(self, tmp_path):
        layout = _make_minimal_layout()
        params = HandParams()
        page_path, _ = render_pipeline(layout, params, tmp_path, "f01r")
        arr = np.array(Image.open(page_path))
        ink = np.sum(arr.min(axis=2) < 220)
        assert ink > 100, f"Pipeline produced too few ink pixels: {ink}"

    def test_pipeline_max_darkness_after_polygon_sweep(self, tmp_path):
        # At least some pixels should be substantially dark (downstrokes)
        layout = _make_minimal_layout()
        params = HandParams()
        page_path, _ = render_pipeline(layout, params, tmp_path, "f01r")
        arr = np.array(Image.open(page_path))
        min_brightness = int(arr.min(axis=2).min())
        # parchment is ~220+, ink should be << 220; check something is < 100
        assert min_brightness < 100, (
            f"Darkest pixel is {min_brightness} — strokes may be too faint"
        )
