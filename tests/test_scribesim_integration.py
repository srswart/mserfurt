"""ScribeSim integration tests — ADV-SS-TESTS-001.

Validates the full pipeline: layout → render → groundtruth, plus
perceptual regression, hand variation distinguishability, sitting-boundary
ink shift, and German-specific glyph correctness.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scribesim.hand.model import load_base, resolve
from scribesim.layout import place
from scribesim.layout.geometry import make_geometry
from scribesim.layout.positioned import PositionedGlyph, LineLayout, PageLayout

HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"
GOLDEN_F01R = Path(__file__).parent / "golden" / "f01r" / "folio.json"
GOLDEN_F07R = Path(__file__).parent / "golden" / "f07r" / "folio.json"
GOLDEN_F14R = Path(__file__).parent / "golden" / "f14r" / "folio.json"

_PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def base_hand():
    return load_base(HAND_TOML)


@pytest.fixture(scope="module")
def f01r_layout(base_hand):
    folio = json.loads(GOLDEN_F01R.read_text())
    params = resolve(base_hand, "f01r")
    return place(folio, params), params


@pytest.fixture(scope="module")
def f07r_layout(base_hand):
    folio = json.loads(GOLDEN_F07R.read_text())
    params = resolve(base_hand, "f07r")
    return place(folio, params), params


@pytest.fixture(scope="module")
def f14r_layout(base_hand):
    folio = json.loads(GOLDEN_F14R.read_text())
    params = resolve(base_hand, "f14r")
    return place(folio, params), params


def _make_single_glyph_layout(glyph_id: str, hand_toml: Path = HAND_TOML) -> tuple:
    """Build a minimal PageLayout containing a single glyph for visual inspection."""
    from scribesim.glyphs.catalog import GLYPH_CATALOG

    base = load_base(hand_toml)
    params = resolve(base, "f01r")
    geom = make_geometry("f01r", params)
    x_height_mm = geom.ruling_pitch_mm

    glyph = GLYPH_CATALOG[glyph_id]
    adv_mm = glyph.advance_width * x_height_mm

    pg = PositionedGlyph(
        glyph_id=glyph_id,
        x_mm=geom.margin_inner + 2.0,
        y_mm=geom.ruling_y(0),
        baseline_y_mm=geom.ruling_y(0) + x_height_mm * 0.8,
        advance_w_mm=max(adv_mm, 0.5),
        opacity=1.0,
    )
    line = LineLayout(line_index=0, y_mm=geom.ruling_y(0), glyphs=[pg])
    layout = PageLayout(folio_id="f01r", geometry=geom, lines=[line])
    return layout, params


# ---------------------------------------------------------------------------
# TestDeterminism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_render_f01r_twice_identical(self, tmp_path, f01r_layout):
        """Rendering the same layout twice must produce byte-for-byte identical output."""
        from scribesim.render.rasteriser import render_page

        layout, params = f01r_layout
        path_a = render_page(layout, params, tmp_path / "f01r_a.png")
        path_b = render_page(layout, params, tmp_path / "f01r_b.png")

        assert path_a.read_bytes() == path_b.read_bytes(), (
            "render_page is not deterministic: two renders of f01r differ"
        )


# ---------------------------------------------------------------------------
# TestHandVariation
# ---------------------------------------------------------------------------

class TestHandVariation:
    def test_f01r_and_f14r_visually_distinguishable(self, tmp_path, f01r_layout, f14r_layout):
        """f01r (baseline) and f14r (wider, slower hand) must be perceptually distinct."""
        from scribesim.render.rasteriser import render_page
        from tests.helpers.phash import compute_phash, hamming_distance

        layout_01, params_01 = f01r_layout
        layout_14, params_14 = f14r_layout

        path_01 = render_page(layout_01, params_01, tmp_path / "f01r.png")
        path_14 = render_page(layout_14, params_14, tmp_path / "f14r.png")

        dist = hamming_distance(compute_phash(path_01), compute_phash(path_14))
        assert dist >= 5, (
            f"f01r and f14r pHash distance {dist} is below minimum threshold 5 — "
            "hand variation not visually distinguishable"
        )

    def test_f14r_has_larger_glyphs_than_f01r(self, base_hand):
        """f14r hand params must have a larger x_height than f01r (slower, wider hand)."""
        params_01 = resolve(base_hand, "f01r")
        params_14 = resolve(base_hand, "f14r")
        assert params_14.x_height_px > params_01.x_height_px, (
            f"f14r x_height_px ({params_14.x_height_px}) should exceed "
            f"f01r ({params_01.x_height_px})"
        )


# ---------------------------------------------------------------------------
# TestSittingBoundary
# ---------------------------------------------------------------------------

class TestSittingBoundary:
    def test_f07r_has_higher_ink_density_than_f01r(self, base_hand):
        """f07r (multi-sitting) must resolve to higher ink_density than f01r baseline."""
        params_01 = resolve(base_hand, "f01r")
        params_07 = resolve(base_hand, "f07r")
        assert params_07.ink_density > params_01.ink_density, (
            f"f07r ink_density ({params_07.ink_density}) should exceed "
            f"f01r ({params_01.ink_density})"
        )

    def test_higher_ink_density_produces_darker_render(self, tmp_path, base_hand):
        """Rendering with higher ink_density must produce measurably darker output."""
        from scribesim.render.rasteriser import render_page
        from scribesim.hand.params import HandParams

        folio = json.loads(GOLDEN_F01R.read_text())
        params_base = resolve(base_hand, "f01r")   # ink_density = 0.85
        params_dense = HandParams.from_dict({
            **params_base.to_dict(),
            "ink_density": 0.95,
        })

        layout = place(folio, params_base)

        path_base = render_page(layout, params_base, tmp_path / "base.png")
        path_dense = render_page(layout, params_dense, tmp_path / "dense.png")

        arr_base = np.array(Image.open(path_base).convert("L"), dtype=float)
        arr_dense = np.array(Image.open(path_dense).convert("L"), dtype=float)

        dark_base = (255 - arr_base).mean()
        dark_dense = (255 - arr_dense).mean()

        assert dark_dense > dark_base, (
            f"Higher ink_density should produce darker render: "
            f"dense={dark_dense:.4f}, base={dark_base:.4f}"
        )


# ---------------------------------------------------------------------------
# TestGermanGlyphs
# ---------------------------------------------------------------------------

class TestGermanGlyphs:
    def _ink_pixel_count(self, image_path: Path, threshold: int = 220) -> int:
        """Count pixels darker than threshold (proxy for rendered ink area)."""
        arr = np.array(Image.open(image_path).convert("L"))
        return int((arr < threshold).sum())

    def test_long_s_renders_visible_ink(self, tmp_path):
        """long_s glyph (ſ) must render non-zero ink pixels."""
        from scribesim.render.rasteriser import render_page

        layout, params = _make_single_glyph_layout("long_s")
        path = render_page(layout, params, tmp_path / "long_s.png")
        assert self._ink_pixel_count(path) > 0, "long_s rendered no visible ink"

    def test_esszett_renders_visible_ink(self, tmp_path):
        """esszett glyph (ß) must render non-zero ink pixels."""
        from scribesim.render.rasteriser import render_page

        layout, params = _make_single_glyph_layout("esszett")
        path = render_page(layout, params, tmp_path / "esszett.png")
        assert self._ink_pixel_count(path) > 0, "esszett rendered no visible ink"

    def test_umlaut_a_renders_visible_ink(self, tmp_path):
        """a_umlaut glyph (ä) must render non-zero ink pixels."""
        from scribesim.render.rasteriser import render_page

        layout, params = _make_single_glyph_layout("a_umlaut")
        path = render_page(layout, params, tmp_path / "a_umlaut.png")
        assert self._ink_pixel_count(path) > 0, "a_umlaut rendered no visible ink"

    def test_umlaut_o_renders_visible_ink(self, tmp_path):
        """o_umlaut glyph (ö) must render non-zero ink pixels."""
        from scribesim.render.rasteriser import render_page

        layout, params = _make_single_glyph_layout("o_umlaut")
        path = render_page(layout, params, tmp_path / "o_umlaut.png")
        assert self._ink_pixel_count(path) > 0, "o_umlaut rendered no visible ink"

    def test_umlaut_u_renders_visible_ink(self, tmp_path):
        """u_umlaut glyph (ü) must render non-zero ink pixels."""
        from scribesim.render.rasteriser import render_page

        layout, params = _make_single_glyph_layout("u_umlaut")
        path = render_page(layout, params, tmp_path / "u_umlaut.png")
        assert self._ink_pixel_count(path) > 0, "u_umlaut rendered no visible ink"

    def test_long_s_distinct_from_round_s(self, tmp_path):
        """long_s and round_s must produce distinct rendered output."""
        from scribesim.render.rasteriser import render_page

        layout_ls, params = _make_single_glyph_layout("long_s")
        layout_rs, _ = _make_single_glyph_layout("round_s")

        path_ls = render_page(layout_ls, params, tmp_path / "long_s.png")
        path_rs = render_page(layout_rs, params, tmp_path / "round_s.png")

        assert path_ls.read_bytes() != path_rs.read_bytes(), (
            "long_s and round_s produced identical rendered output — "
            "catalog strokes must differ between the two glyphs"
        )

    def test_esszett_has_more_ink_than_single_glyph(self, tmp_path):
        """esszett (compound ligature) must have more ink than a simple letter."""
        from scribesim.render.rasteriser import render_page

        layout_sz, params = _make_single_glyph_layout("esszett")
        layout_a, _ = _make_single_glyph_layout("a")

        path_sz = render_page(layout_sz, params, tmp_path / "esszett.png")
        path_a = render_page(layout_a, params, tmp_path / "a.png")

        ink_sz = self._ink_pixel_count(path_sz)
        ink_a = self._ink_pixel_count(path_a)

        assert ink_sz >= ink_a, (
            f"esszett ink pixels ({ink_sz}) should be >= 'a' ink pixels ({ink_a})"
        )


# ---------------------------------------------------------------------------
# TestIoUValidation
# ---------------------------------------------------------------------------

class TestIoUValidation:
    def test_glyph_polygon_ink_overlap(self, tmp_path, f01r_layout):
        """At least 80% of PAGE XML glyph Coords polygons must overlap rendered ink."""
        from scribesim.render.rasteriser import render_page
        from scribesim.groundtruth.page_xml import generate
        from tests.helpers.iou import poly_to_mask, pixel_mask_from_page, compute_iou

        layout, params = f01r_layout

        png_path = render_page(layout, params, tmp_path / "f01r.png")
        xml_path = generate(layout, tmp_path / "f01r.xml")

        img_grey = np.array(Image.open(png_path).convert("L"))
        h, w = img_grey.shape
        ink_mask = pixel_mask_from_page(img_grey)

        root = ET.parse(str(xml_path)).getroot()
        glyphs = root.findall(f".//{{{_PAGE_NS}}}Glyph")
        assert len(glyphs) > 0, "PAGE XML contains no Glyph elements"

        sample = glyphs[:20]
        non_zero = 0
        for glyph_el in sample:
            coords_el = glyph_el.find(f"{{{_PAGE_NS}}}Coords")
            pts_str = coords_el.attrib.get("points", "")
            poly_mask = poly_to_mask(pts_str, w, h)
            if compute_iou(poly_mask, ink_mask) > 0.0:
                non_zero += 1

        ratio = non_zero / len(sample)
        assert ratio >= 0.8, (
            f"Only {non_zero}/{len(sample)} ({ratio:.0%}) glyph polygons overlap "
            "rendered ink pixels — coordinate alignment issue"
        )

    def test_glyph_coords_within_page_bounds(self, tmp_path, f01r_layout):
        """All PAGE XML glyph polygon points must lie within page pixel dimensions."""
        from scribesim.render.rasteriser import render_page
        from scribesim.groundtruth.page_xml import generate

        layout, params = f01r_layout

        png_path = render_page(layout, params, tmp_path / "f01r.png")
        xml_path = generate(layout, tmp_path / "f01r.xml")

        img = Image.open(png_path)
        w, h = img.size

        root = ET.parse(str(xml_path)).getroot()
        out_of_bounds = 0
        for coords_el in root.findall(f".//{{{_PAGE_NS}}}Coords"):
            for pair in coords_el.attrib.get("points", "").strip().split():
                x_str, y_str = pair.split(",")
                x, y = int(x_str), int(y_str)
                if not (0 <= x <= w and 0 <= y <= h):
                    out_of_bounds += 1

        assert out_of_bounds == 0, (
            f"{out_of_bounds} coordinate points lie outside page bounds "
            f"({w}×{h} px)"
        )


# ---------------------------------------------------------------------------
# TestFullPipeline
# ---------------------------------------------------------------------------

class TestFullPipeline:
    def test_full_pipeline_f01r_produces_valid_outputs(self, tmp_path, f01r_layout):
        """Full pipeline: layout → render → heatmap → PAGE XML, no exceptions."""
        from scribesim.render.rasteriser import render_page, render_heatmap
        from scribesim.groundtruth.page_xml import generate

        layout, params = f01r_layout

        png_path = render_page(layout, params, tmp_path / "f01r.png")
        heatmap_path = render_heatmap(layout, params, tmp_path / "f01r_pressure.png")
        xml_path = generate(layout, tmp_path / "f01r.xml")

        assert png_path.exists(), "render_page did not write output PNG"
        assert heatmap_path.exists(), "render_heatmap did not write heatmap PNG"
        assert xml_path.exists(), "generate did not write PAGE XML"

        root = ET.parse(str(xml_path)).getroot()
        assert root.tag == f"{{{_PAGE_NS}}}PcGts"

    def test_full_pipeline_f07r_produces_valid_outputs(self, tmp_path, f07r_layout):
        """Full pipeline for f07r (multi-sitting folio) completes without error."""
        from scribesim.render.rasteriser import render_page, render_heatmap
        from scribesim.groundtruth.page_xml import generate

        layout, params = f07r_layout

        png_path = render_page(layout, params, tmp_path / "f07r.png")
        heatmap_path = render_heatmap(layout, params, tmp_path / "f07r_pressure.png")
        xml_path = generate(layout, tmp_path / "f07r.xml")

        assert png_path.exists()
        assert heatmap_path.exists()
        assert xml_path.exists()

    def test_full_pipeline_f14r_produces_valid_outputs(self, tmp_path, f14r_layout):
        """Full pipeline for f14r (final-gathering folio) completes without error."""
        from scribesim.render.rasteriser import render_page, render_heatmap
        from scribesim.groundtruth.page_xml import generate

        layout, params = f14r_layout

        png_path = render_page(layout, params, tmp_path / "f14r.png")
        heatmap_path = render_heatmap(layout, params, tmp_path / "f14r_pressure.png")
        xml_path = generate(layout, tmp_path / "f14r.xml")

        assert png_path.exists()
        assert heatmap_path.exists()
        assert xml_path.exists()

    def test_page_and_heatmap_same_pixel_dimensions(self, tmp_path, f01r_layout):
        """Page PNG and pressure heatmap must have identical pixel dimensions."""
        from scribesim.render.rasteriser import render_page, render_heatmap

        layout, params = f01r_layout

        png_path = render_page(layout, params, tmp_path / "f01r.png")
        heatmap_path = render_heatmap(layout, params, tmp_path / "f01r_pressure.png")

        img_page = Image.open(png_path)
        img_heat = Image.open(heatmap_path)

        assert img_page.size == img_heat.size, (
            f"Page {img_page.size} and heatmap {img_heat.size} differ in dimensions"
        )
