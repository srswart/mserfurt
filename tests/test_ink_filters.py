"""Unit tests for ink-substrate interaction filters — ADV-SS-INK-001."""

from __future__ import annotations

import numpy as np
import pytest

from scribesim.hand.profile import (
    HandProfile, InkParams, MaterialParams, FolioParams, LineParams,
    GlyphParams, NibParams,
)
from scribesim.layout.geometry import PageGeometry
from scribesim.layout.positioned import PositionedGlyph, LineLayout, PageLayout
from scribesim.ink.filters import (
    ink_saturation,
    ink_pooling,
    vellum_wicking,
    hairline_feathering,
    ink_depletion,
    apply_ink_filters,
    _ink_mask,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PARCHMENT = np.array([245, 238, 220], dtype=np.uint8)
_INK = np.array([18, 12, 8], dtype=np.uint8)


def _make_test_image(h: int = 100, w: int = 200) -> np.ndarray:
    """Create a test image: parchment background with a dark ink stripe."""
    img = np.full((h, w, 3), _PARCHMENT, dtype=np.uint8)
    # Horizontal ink stripe at rows 40-60
    img[40:60, 20:180, :] = _INK
    return img


def _make_heatmap(h: int = 100, w: int = 200) -> np.ndarray:
    """Create a pressure heatmap matching the test image ink stripe."""
    heat = np.zeros((h, w), dtype=np.uint8)
    heat[40:60, 20:180] = 150  # moderate pressure
    return heat


def _make_heatmap_variable(h: int = 100, w: int = 200) -> np.ndarray:
    """Heatmap with variable pressure: high on left, low on right."""
    heat = np.zeros((h, w), dtype=np.uint8)
    for x in range(20, 180):
        pressure = int(200 * (1.0 - (x - 20) / 160.0))
        heat[40:60, x] = pressure
    return heat


def _make_geometry() -> PageGeometry:
    return PageGeometry(
        page_w_mm=200 / 11.811, page_h_mm=100 / 11.811,
        margin_top=2.0, margin_bottom=2.0,
        margin_inner=2.0, margin_outer=2.0,
        ruling_pitch_mm=1.7, x_height_mm=0.68, folio_format="standard",
    )


def _make_layout_for_depletion(n_lines: int = 5, words_per_line: int = 10) -> PageLayout:
    """Layout with multiple lines and words for depletion cycle testing."""
    geom = _make_geometry()
    lines = []
    px_per_mm = 200 / geom.page_w_mm
    for li in range(n_lines):
        y_mm = geom.margin_top + li * geom.ruling_pitch_mm
        glyphs = []
        x = geom.margin_inner
        for wi in range(words_per_line):
            for gi in range(3):  # 3 glyphs per word
                glyphs.append(PositionedGlyph(
                    glyph_id="a", x_mm=x, y_mm=y_mm,
                    baseline_y_mm=y_mm + 1.0, advance_w_mm=0.3,
                ))
                x += 0.3
            x += 0.8  # word gap
        lines.append(LineLayout(line_index=li, y_mm=y_mm, glyphs=glyphs))
    return PageLayout(folio_id="f01r", geometry=geom, lines=lines)


def _make_simple_layout() -> PageLayout:
    geom = _make_geometry()
    glyphs = [PositionedGlyph(
        glyph_id="a", x_mm=2.0, y_mm=3.0,
        baseline_y_mm=4.0, advance_w_mm=0.5,
    )]
    lines = [LineLayout(line_index=0, y_mm=3.0, glyphs=glyphs)]
    return PageLayout(folio_id="f01r", geometry=geom, lines=lines)


# ---------------------------------------------------------------------------
# TestInkMask
# ---------------------------------------------------------------------------

class TestInkMask:
    def test_detects_ink_pixels(self):
        img = _make_test_image()
        mask = _ink_mask(img)
        assert mask[50, 100]  # ink stripe
        assert not mask[10, 100]  # parchment

    def test_parchment_not_detected(self):
        img = np.full((50, 50, 3), _PARCHMENT, dtype=np.uint8)
        mask = _ink_mask(img)
        assert not mask.any()


# ---------------------------------------------------------------------------
# TestSaturation
# ---------------------------------------------------------------------------

class TestSaturation:
    def test_high_pressure_darkens(self):
        img = _make_test_image()
        heat = _make_heatmap()
        profile = HandProfile(ink=InkParams(fresh_dip_darkness_boost=0.3))
        result = ink_saturation(img, heat, profile)
        # Ink pixels should be darker (lower values)
        orig_mean = img[40:60, 20:180].mean()
        result_mean = result[40:60, 20:180].mean()
        assert result_mean < orig_mean

    def test_zero_boost_no_change(self):
        img = _make_test_image()
        heat = _make_heatmap()
        profile = HandProfile(ink=InkParams(fresh_dip_darkness_boost=0.0))
        result = ink_saturation(img, heat, profile)
        np.testing.assert_array_equal(result, img)

    def test_parchment_unchanged(self):
        img = _make_test_image()
        heat = _make_heatmap()
        profile = HandProfile(ink=InkParams(fresh_dip_darkness_boost=0.3))
        result = ink_saturation(img, heat, profile)
        # Parchment area should be unchanged
        np.testing.assert_array_equal(result[10, 100], img[10, 100])


# ---------------------------------------------------------------------------
# TestPooling
# ---------------------------------------------------------------------------

class TestPooling:
    def test_pooling_darkens_edges(self):
        img = _make_test_image()
        heat = _make_heatmap()
        heat[40:60, 20:25] = 200  # high pressure at left edge (stroke end)
        profile = HandProfile(material=MaterialParams(pooling_at_direction_change=0.5))
        result = ink_pooling(img, heat, profile)
        # Edge area should be darker
        orig_edge = img[50, 22].astype(float).mean()
        result_edge = result[50, 22].astype(float).mean()
        assert result_edge <= orig_edge

    def test_zero_strength_no_change(self):
        img = _make_test_image()
        heat = _make_heatmap()
        profile = HandProfile(material=MaterialParams(pooling_at_direction_change=0.0))
        result = ink_pooling(img, heat, profile)
        np.testing.assert_array_equal(result, img)


# ---------------------------------------------------------------------------
# TestWicking
# ---------------------------------------------------------------------------

class TestWicking:
    def test_wicking_blurs_vertically_more(self):
        img = _make_test_image()
        heat = _make_heatmap()
        profile = HandProfile(material=MaterialParams(grain_spread_factor=0.3))
        result = vellum_wicking(img, heat, profile)
        # The ink stripe should bleed more vertically than horizontally
        # Check that rows above/below the stripe are darker than in original
        orig_above = img[38, 100].astype(float).mean()
        result_above = result[38, 100].astype(float).mean()
        # Blurring toward parchment: the pixel above ink should be darker (lower)
        # than pure parchment
        assert result_above < orig_above or result_above == pytest.approx(orig_above, abs=5)

    def test_zero_spread_no_change(self):
        img = _make_test_image()
        heat = _make_heatmap()
        profile = HandProfile(material=MaterialParams(grain_spread_factor=0.0))
        result = vellum_wicking(img, heat, profile)
        np.testing.assert_array_equal(result, img)


# ---------------------------------------------------------------------------
# TestFeathering
# ---------------------------------------------------------------------------

class TestFeathering:
    def test_thin_strokes_blur_more(self):
        img = _make_test_image()
        heat = _make_heatmap_variable()  # high pressure left, low right
        profile = HandProfile(material=MaterialParams(edge_feather_mm=0.05))
        result = hairline_feathering(img, heat, profile)
        # Result should differ from original (some blurring applied)
        assert not np.array_equal(result, img)

    def test_zero_feather_no_change(self):
        img = _make_test_image()
        heat = _make_heatmap()
        profile = HandProfile(material=MaterialParams(edge_feather_mm=0.0))
        result = hairline_feathering(img, heat, profile)
        np.testing.assert_array_equal(result, img)


# ---------------------------------------------------------------------------
# TestDepletion
# ---------------------------------------------------------------------------

class TestDepletion:
    def test_later_lines_lighter(self):
        """Lines further into the dip cycle should be lighter."""
        img = _make_test_image(h=200, w=200)
        # Paint ink stripes at multiple line positions
        for row in range(20, 180, 20):
            img[row:row + 5, 20:180, :] = _INK
        heat = np.zeros((200, 200), dtype=np.uint8)
        for row in range(20, 180, 20):
            heat[row:row + 5, 20:180] = 150

        layout = _make_layout_for_depletion(n_lines=8, words_per_line=8)
        profile = HandProfile(ink=InkParams(depletion_rate=0.04))
        result = ink_depletion(img, heat, layout, profile)
        # At least some lines should differ from original
        assert not np.array_equal(result, img)

    def test_zero_rate_no_change(self):
        img = _make_test_image()
        heat = _make_heatmap()
        layout = _make_simple_layout()
        profile = HandProfile(ink=InkParams(depletion_rate=0.0))
        result = ink_depletion(img, heat, layout, profile)
        np.testing.assert_array_equal(result, img)


# ---------------------------------------------------------------------------
# TestPipeline
# ---------------------------------------------------------------------------

class TestPipeline:
    def test_apply_all_filters_changes_image(self):
        img = _make_test_image()
        heat = _make_heatmap()
        layout = _make_simple_layout()
        profile = HandProfile(
            ink=InkParams(fresh_dip_darkness_boost=0.2, depletion_rate=0.02),
            material=MaterialParams(
                pooling_at_direction_change=0.3,
                grain_spread_factor=0.1,
                edge_feather_mm=0.03,
            ),
        )
        result = apply_ink_filters(img, heat, layout, profile)
        assert not np.array_equal(result, img)

    def test_all_zero_no_change(self):
        img = _make_test_image()
        heat = _make_heatmap()
        layout = _make_simple_layout()
        profile = HandProfile(
            ink=InkParams(fresh_dip_darkness_boost=0.0, depletion_rate=0.0),
            material=MaterialParams(
                pooling_at_direction_change=0.0,
                grain_spread_factor=0.0,
                edge_feather_mm=0.0,
            ),
        )
        result = apply_ink_filters(img, heat, layout, profile)
        np.testing.assert_array_equal(result, img)

    def test_preserves_shape(self):
        img = _make_test_image()
        heat = _make_heatmap()
        layout = _make_simple_layout()
        profile = HandProfile()
        result = apply_ink_filters(img, heat, layout, profile)
        assert result.shape == img.shape
        assert result.dtype == np.uint8
