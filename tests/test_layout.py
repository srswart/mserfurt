"""Unit tests for scribesim layout engine — ADV-SS-LAYOUT-001.

RED phase: placer.place() is a stub (NotImplementedError).
Geometry and positioned-glyph dataclass tests should be green immediately.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scribesim.hand.params import HandParams
from scribesim.hand.model import load_base, resolve
from scribesim.layout.geometry import PageGeometry, make_geometry
from scribesim.layout.positioned import PositionedGlyph, LineLayout, PageLayout

HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"
GOLDEN_F01R = Path(__file__).parent / "golden" / "f01r" / "folio.json"


# ---------------------------------------------------------------------------
# TestPageGeometry — geometry dataclass + make_geometry factory
# ---------------------------------------------------------------------------

class TestPageGeometry:
    def test_standard_folio_dimensions(self):
        base = load_base(HAND_TOML)
        g = make_geometry("f01r", base)
        assert g.page_w_mm == pytest.approx(280.0)
        assert g.page_h_mm == pytest.approx(400.0)
        assert g.folio_format == "standard"

    def test_final_folio_dimensions(self):
        base = load_base(HAND_TOML)
        g = make_geometry("f14r", base)
        assert g.page_w_mm == pytest.approx(240.0)
        assert g.page_h_mm == pytest.approx(340.0)
        assert g.folio_format == "final"

    def test_standard_folio_ruling_count_30_to_32(self):
        base = load_base(HAND_TOML)
        g = make_geometry("f01r", base)
        assert 30 <= g.ruling_count <= 32, (
            f"Expected 30–32 ruling lines, got {g.ruling_count}"
        )

    def test_final_folio_ruling_count_26_to_28(self):
        base = load_base(HAND_TOML)
        # f14r has slightly reduced x_height (42px) and writing_speed 0.82
        g14 = make_geometry("f14r", base)
        assert 26 <= g14.ruling_count <= 28, (
            f"Expected 26–28 ruling lines on f14r, got {g14.ruling_count}"
        )

    def test_text_w_mm(self):
        base = load_base(HAND_TOML)
        g = make_geometry("f01r", base)
        assert g.text_w_mm == pytest.approx(280.0 - 25.0 - 50.0)  # 205 mm

    def test_text_h_mm(self):
        base = load_base(HAND_TOML)
        g = make_geometry("f01r", base)
        assert g.text_h_mm == pytest.approx(400.0 - 25.0 - 70.0)  # 305 mm

    def test_ruling_y_first_line_at_margin_top(self):
        base = load_base(HAND_TOML)
        g = make_geometry("f01r", base)
        assert g.ruling_y(0) == pytest.approx(g.margin_top)

    def test_ruling_y_within_text_block(self):
        base = load_base(HAND_TOML)
        g = make_geometry("f01r", base)
        for i in range(g.ruling_count):
            y = g.ruling_y(i)
            assert y >= g.margin_top
            assert y <= (g.page_h_mm - g.margin_bottom)

    def test_hand_scale_affects_ruling_pitch(self):
        """f07v has hand_scale modifier — smaller x_height → tighter ruling."""
        base = load_base(HAND_TOML)
        g_std = make_geometry("f01r", base)
        base_f07v = resolve(base, "f07v")
        g_f07v = make_geometry("f07v", base_f07v)
        # smaller x_height → smaller pitch → more lines
        assert g_f07v.ruling_count >= g_std.ruling_count

    def test_ruling_pitch_has_minimum(self):
        """Pitch should never be so small as to produce implausible line density."""
        tiny = HandParams(x_height_px=5)
        g = make_geometry("f01r", tiny)
        assert g.ruling_pitch_mm >= 7.0


# ---------------------------------------------------------------------------
# TestPositionedGlyph — dataclass contracts
# ---------------------------------------------------------------------------

class TestPositionedGlyph:
    def test_valid_construction(self):
        pg = PositionedGlyph(
            glyph_id="a", x_mm=10.0, y_mm=20.0,
            baseline_y_mm=21.0, advance_w_mm=2.0,
        )
        assert pg.opacity == pytest.approx(1.0)

    def test_opacity_out_of_range_raises(self):
        with pytest.raises(ValueError, match="opacity"):
            PositionedGlyph(
                glyph_id="a", x_mm=0, y_mm=0,
                baseline_y_mm=1.0, advance_w_mm=2.0, opacity=1.5,
            )

    def test_zero_advance_raises(self):
        with pytest.raises(ValueError, match="advance_w_mm"):
            PositionedGlyph(
                glyph_id="a", x_mm=0, y_mm=0,
                baseline_y_mm=1.0, advance_w_mm=0.0,
            )

    def test_immutable(self):
        pg = PositionedGlyph(
            glyph_id="a", x_mm=0, y_mm=0,
            baseline_y_mm=1.0, advance_w_mm=2.0,
        )
        with pytest.raises(Exception):
            pg.glyph_id = "b"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TestPageLayout — RED: place() is still a stub
# ---------------------------------------------------------------------------

class TestPageLayout:
    def _place(self):
        from scribesim.layout.placer import place  # noqa: PLC0415
        return place

    def _folio(self) -> dict:
        return json.loads(GOLDEN_F01R.read_text())

    def test_place_returns_page_layout(self):
        place = self._place()
        folio = self._folio()
        base = load_base(HAND_TOML)
        result = place(folio, base)
        assert isinstance(result, PageLayout)

    def test_place_folio_id_matches(self):
        place = self._place()
        folio = self._folio()
        base = load_base(HAND_TOML)
        result = place(folio, base)
        assert result.folio_id == "f01r"

    def test_place_geometry_is_page_geometry(self):
        place = self._place()
        folio = self._folio()
        base = load_base(HAND_TOML)
        result = place(folio, base)
        assert isinstance(result.geometry, PageGeometry)

    def test_place_produces_lines(self):
        place = self._place()
        folio = self._folio()
        base = load_base(HAND_TOML)
        result = place(folio, base)
        assert len(result.lines) > 0

    def test_f01r_line_count_matches_folio_metadata(self):
        """place() must produce exactly as many LineLayouts as text lines in the folio."""
        place = self._place()
        folio = self._folio()
        base = load_base(HAND_TOML)
        result = place(folio, base)
        assert len(result.lines) == folio["metadata"]["line_count"]

    def test_all_lines_have_glyphs(self):
        place = self._place()
        folio = self._folio()
        base = load_base(HAND_TOML)
        result = place(folio, base)
        for line in result.lines:
            assert len(line.glyphs) > 0, f"Line {line.line_index} has no glyphs"

    def test_glyphs_within_text_block_width(self):
        """No glyph should extend beyond the right margin."""
        place = self._place()
        folio = self._folio()
        base = load_base(HAND_TOML)
        result = place(folio, base)
        tw = result.geometry.text_w_mm
        left = result.geometry.margin_inner
        for line in result.lines:
            for pg in line.glyphs:
                right_edge = pg.x_mm - left + pg.advance_w_mm
                assert right_edge <= tw + 0.1, (
                    f"Glyph '{pg.glyph_id}' at x={pg.x_mm:.2f} overflows "
                    f"text block (width={tw:.2f}mm)"
                )

    def test_glyph_y_within_page(self):
        place = self._place()
        folio = self._folio()
        base = load_base(HAND_TOML)
        result = place(folio, base)
        for line in result.lines:
            for pg in line.glyphs:
                assert 0 <= pg.baseline_y_mm <= result.geometry.page_h_mm

    def test_water_damage_sets_opacity_below_one(self):
        """Glyphs inside a water_damage region must have opacity < 1.0."""
        place = self._place()
        # Use f04v golden folio which has water_damage
        f04v_path = Path(__file__).parent / "golden" / "f04v" / "folio.json"
        folio = json.loads(f04v_path.read_text())
        base = load_base(HAND_TOML)
        params = resolve(base, "f04v")
        result = place(folio, params)
        # At least some glyphs should have reduced opacity
        all_opacities = [pg.opacity for line in result.lines for pg in line.glyphs]
        assert any(op < 1.0 for op in all_opacities), (
            "f04v has water_damage but no glyphs have opacity < 1.0"
        )

    def test_all_glyph_opacities_in_range(self):
        place = self._place()
        folio = self._folio()
        base = load_base(HAND_TOML)
        result = place(folio, base)
        for line in result.lines:
            for pg in line.glyphs:
                assert 0.0 <= pg.opacity <= 1.0
