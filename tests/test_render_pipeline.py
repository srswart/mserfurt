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
