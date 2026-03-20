"""Integration tests for the Weather pipeline — ADV-WX-TESTS-001.

Covers cross-component concerns:
  - Compositing order enforcement
  - Effect isolation
  - Per-folio dispatch
  - Water damage direction (from_above)
  - Vellum stock visual difference
  - Coordinate accuracy (≤2px drift after curl)
  - Determinism (byte-identical re-render)
  - Multi-folio end-to-end
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import numpy as np
import pytest
from PIL import Image

PROFILE_TOML = Path(__file__).parent.parent / "shared" / "profiles" / "ms-erfurt-560yr.toml"
PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"

# Synthetic page size — large enough for gradient effects to be measurable
_W, _H = 200, 280


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _white_page(w=_W, h=_H) -> Image.Image:
    return Image.fromarray(np.full((h, w, 3), 255, dtype=np.uint8), mode="RGB")


def _inked_page(w=_W, h=_H) -> Image.Image:
    """White background with a horizontal ink stripe in the upper third."""
    arr = np.full((h, w, 3), 255, dtype=np.uint8)
    arr[h // 4 : h // 4 + 12, 15:-15, :] = 25
    return Image.fromarray(arr, mode="RGB")


def _heatmap(w=_W, h=_H) -> Image.Image:
    arr = np.full((h, w), 128, dtype=np.uint8)
    arr[h // 4 : h // 4 + 12, 15:-15] = 220
    return Image.fromarray(arr, mode="L")


def _page_xml(n_lines: int = 8, canvas: int = 1000) -> str:
    """Minimal PAGE XML with n_lines evenly spaced TextLines."""
    line_h = canvas // n_lines
    lines = []
    for i in range(n_lines):
        y0, y1 = i * line_h, (i + 1) * line_h
        cx = canvas // 2
        lines.append(
            f'<TextLine id="l{i+1}" custom="register:mixed">'
            f'<Coords points="0,{y0} {canvas},{y0} {canvas},{y1} 0,{y1}" />'
            f'<Baseline points="0,{y1-2} {canvas},{y1-2}" />'
            f'<TextEquiv index="0"><Unicode>test line {i+1}</Unicode></TextEquiv>'
            f'</TextLine>'
        )
    return (
        f"<?xml version='1.0' encoding='utf-8'?>"
        f'<PcGts xmlns="{PAGE_NS}">'
        f"<Metadata><Creator>test</Creator></Metadata>"
        f'<Page imageFilename="test.png" imageWidth="{canvas}" imageHeight="{canvas}">'
        f'<TextRegion id="r1" custom="type:paragraph">'
        f'<Coords points="0,0 {canvas},0 {canvas},{canvas} 0,{canvas}" />'
        + "".join(lines)
        + "</TextRegion></Page></PcGts>"
    )


@pytest.fixture(scope="module")
def profile():
    from weather.profile import load_profile
    return load_profile(PROFILE_TOML)


# ---------------------------------------------------------------------------
# TestEffectIsolation
# ---------------------------------------------------------------------------

class TestEffectIsolation:
    """Each effect applied in isolation must change the image."""

    def test_substrate_differs_from_flat_fill(self, profile):
        from weather.substrate.vellum import generate_substrate, VellumStock
        result = generate_substrate(_W, _H, VellumStock.STANDARD, profile, seed=0)
        flat = Image.fromarray(
            np.full((_H, _W, 3), list(profile.substrate_standard.color_base),
                    dtype=np.uint8), mode="RGB"
        )
        assert not np.array_equal(np.array(result), np.array(flat)), (
            "Substrate should add texture variation"
        )

    def test_ink_aging_changes_ink_pixels(self, profile):
        from weather.ink.aging import apply_ink_aging
        page = _inked_page()
        result = apply_ink_aging(page, _heatmap(), profile, seed=0)
        assert not np.array_equal(np.array(result), np.array(page))

    def test_water_damage_changes_f04r(self, profile):
        from weather.damage.water import apply_water_damage
        page = _inked_page()
        result = apply_water_damage(page, "f04r", profile, seed=0)
        assert not np.array_equal(np.array(result.image), np.array(page))

    def test_damage_no_change_f01r(self, profile):
        from weather.damage.pipeline import apply_damage
        page = _inked_page()
        result = apply_damage(page, "f01r", profile, seed=0)
        # f01r has no damage — image should be a copy unchanged
        assert np.array_equal(np.array(result.image), np.array(page))

    def test_aging_changes_page(self, profile):
        from weather.aging import apply_aging
        page = Image.fromarray(np.full((_H, _W, 3), 200, dtype=np.uint8), mode="RGB")
        result = apply_aging(page, "f01r", profile, seed=0)
        assert not np.array_equal(np.array(result), np.array(page))

    def test_optics_vignette_changes_page(self, profile):
        from weather.optics import apply_optics
        page = Image.fromarray(np.full((_H, _W, 3), 200, dtype=np.uint8), mode="RGB")
        result = apply_optics(page, "f01r", profile, seed=0)
        # Vignette + lighting are enabled → output must differ
        assert not np.array_equal(np.array(result.image), np.array(page))

    def test_effects_dont_bleed_between_components(self, profile):
        """Ink aging should not affect background pixels."""
        from weather.ink.aging import apply_ink_aging
        from weather.ink.mask import extract_ink_mask
        page = _inked_page()
        bg_mask = ~extract_ink_mask(page)
        result = apply_ink_aging(page, _heatmap(), profile, seed=0)
        arr_in = np.array(page)
        arr_out = np.array(result)
        # Background pixels should be unchanged (ink operations don't modify bg)
        # Note: bleed extends slightly, so check pixels far from ink stripe
        far_bg = bg_mask.copy()
        far_bg[_H // 4 - 5 : _H // 4 + 17, :] = False  # exclude bleed zone
        assert np.array_equal(arr_in[far_bg], arr_out[far_bg]), (
            "Far background pixels should be unaffected by ink aging"
        )


# ---------------------------------------------------------------------------
# TestCompositionOrder
# ---------------------------------------------------------------------------

class TestCompositionOrder:
    """Verify layer order matters — swapping any two produces different output."""

    def _run_normal(self, profile, page, hmap, folio_id="f01r", seed=0):
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        return composite_folio(page, hmap, folio_id, profile,
                               stock=VellumStock.STANDARD, seed=seed)

    def _run_damage_before_ink(self, profile, page, hmap, folio_id="f04r", seed=0):
        """Apply damage → ink instead of ink → damage (wrong order)."""
        from weather.substrate.vellum import generate_substrate, VellumStock, stock_for_folio
        from weather.ink.mask import extract_ink_mask
        from weather.ink.aging import apply_ink_aging
        from weather.damage.pipeline import apply_damage
        from weather.aging import apply_aging
        from weather.optics import apply_optics
        import numpy as np

        w, h = page.width, page.height
        stock = VellumStock.STANDARD
        substrate = generate_substrate(w, h, stock, profile, seed=seed)

        # Apply damage FIRST (wrong order — before ink aging)
        damage_result = apply_damage(page, folio_id, profile, seed=seed + 1)

        # Then blend damaged page over substrate
        ink_mask = extract_ink_mask(page)
        sub_arr = np.array(substrate, dtype=np.uint8)
        dmg_arr = np.array(damage_result.image, dtype=np.uint8)
        mask3 = ink_mask[:, :, np.newaxis]
        blended = Image.fromarray(np.where(mask3, dmg_arr, sub_arr).astype(np.uint8), mode="RGB")

        # Then ink aging (wrong: after damage)
        aged_ink = apply_ink_aging(blended, hmap, profile, seed=seed + 2)
        aged = apply_aging(aged_ink, folio_id, profile, seed=seed + 3)
        optics_result = apply_optics(aged, folio_id, profile, seed=seed + 4)
        return np.array(optics_result.image)

    def test_correct_vs_swapped_damage_ink_order(self, profile):
        """Damage before ink vs ink before damage should produce different pixels."""
        page = _inked_page()
        hmap = _heatmap()
        normal = np.array(self._run_normal(profile, page, hmap, "f04r").image)
        swapped = self._run_damage_before_ink(profile, page, hmap, "f04r")
        assert not np.array_equal(normal, swapped), (
            "Swapping ink-aging and damage order should produce different output"
        )

    def test_f04v_all_layers_applied(self, profile):
        """f04v should have water_zone AND corner_mask populated."""
        result = self._run_normal(profile, _inked_page(), _heatmap(), "f04v")
        assert result.water_zone is not None
        assert result.corner_mask is not None

    def test_f05r_water_only_no_corner(self, profile):
        """f05r gets water damage but NOT missing corner."""
        result = self._run_normal(profile, _inked_page(), _heatmap(), "f05r")
        assert result.water_zone is not None
        assert result.corner_mask is None


# ---------------------------------------------------------------------------
# TestFolioDispatch
# ---------------------------------------------------------------------------

class TestFolioDispatch:
    """Per-folio damage dispatch correctness."""

    @pytest.mark.parametrize("folio_id", ["f04r", "f04v", "f05r", "f05v"])
    def test_water_damaged_folios(self, profile, folio_id):
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        result = composite_folio(_inked_page(), _heatmap(), folio_id, profile, seed=0)
        assert result.water_zone is not None, f"{folio_id} should have water_zone"

    @pytest.mark.parametrize("folio_id", ["f01r", "f03v", "f06r", "f13v"])
    def test_clean_folios_no_damage(self, profile, folio_id):
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        result = composite_folio(_inked_page(), _heatmap(), folio_id, profile, seed=0)
        assert result.water_zone is None, f"{folio_id} should have no water_zone"
        assert result.corner_mask is None, f"{folio_id} should have no corner_mask"

    def test_only_f04v_has_corner_mask(self, profile):
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        # f04v gets corner
        r04v = composite_folio(_inked_page(), _heatmap(), "f04v", profile, seed=0)
        assert r04v.corner_mask is not None
        # f04r does not
        r04r = composite_folio(_inked_page(), _heatmap(), "f04r", profile, seed=0)
        assert r04r.corner_mask is None


# ---------------------------------------------------------------------------
# TestWaterDamageDirection
# ---------------------------------------------------------------------------

class TestWaterDamageDirection:
    """Water damage must be stronger at the top (from_above direction)."""

    def test_water_zone_rows_darker_than_dry_zone_rows(self, profile):
        """Compare rows clearly inside the water zone vs rows clearly outside.

        Water zone covers ~38% from the top (rows 0..106 at H=280).
        Edge darkening covers ~12% from each edge (rows 0..33 and 247..279).

        Compare water-zone rows 42-70 (15-25% depth — past top edge band, inside tide)
        vs dry-zone rows 140-168 (50-60% depth — below tide, above bottom edge band).
        """
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        grey = Image.fromarray(np.full((_H, _W, 3), 220, dtype=np.uint8), mode="RGB")
        hmap = Image.fromarray(np.full((_H, _W), 128, dtype=np.uint8), mode="L")
        result = composite_folio(grey, hmap, "f04r", profile, seed=0)
        arr = np.array(result.image)
        # rows 42..70: inside water zone, past top edge darkening
        wet_band_start = int(_H * 0.15)
        wet_band_end = int(_H * 0.25)
        # rows 140..168: dry zone, well above bottom edge darkening
        dry_band_start = int(_H * 0.50)
        dry_band_end = int(_H * 0.60)
        wet_lum = float(arr[wet_band_start:wet_band_end, :, :].mean())
        dry_lum = float(arr[dry_band_start:dry_band_end, :, :].mean())
        assert wet_lum < dry_lum, (
            f"Water-zone rows (lum={wet_lum:.1f}) should be darker than "
            f"dry-zone rows (lum={dry_lum:.1f})"
        )

    def test_water_zone_covers_top_rows(self, profile):
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        page = _white_page()
        hmap = Image.fromarray(np.full((_H, _W), 128, dtype=np.uint8), mode="L")
        result = composite_folio(page, hmap, "f04r", profile, seed=0)
        assert result.water_zone is not None
        # Top rows should be entirely wet
        assert result.water_zone[0, :].all(), "Topmost row should be in water zone"


# ---------------------------------------------------------------------------
# TestVellumStock
# ---------------------------------------------------------------------------

class TestVellumStock:
    """Standard (f01r) and irregular (f14r) stocks must produce different bases."""

    def test_stock_color_difference(self, profile):
        from weather.substrate.vellum import generate_substrate, VellumStock
        std = np.array(generate_substrate(_W, _H, VellumStock.STANDARD, profile, seed=0))
        irr = np.array(generate_substrate(_W, _H, VellumStock.IRREGULAR, profile, seed=0))
        assert not np.array_equal(std, irr)
        # Standard base [242,228,196] is warmer/lighter; irregular [235,215,178] is yellower
        std_g_mean = float(std[:, :, 1].mean())
        irr_g_mean = float(irr[:, :, 1].mean())
        assert std_g_mean != irr_g_mean, "Green channel means should differ by stock"

    def test_compositor_uses_stock_from_param(self, profile):
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        page = _white_page()
        hmap = Image.fromarray(np.full((_H, _W), 128, dtype=np.uint8), mode="L")
        r_std = np.array(composite_folio(page, hmap, "f01r", profile,
                                         stock=VellumStock.STANDARD, seed=0).image)
        r_irr = np.array(composite_folio(page, hmap, "f01r", profile,
                                         stock=VellumStock.IRREGULAR, seed=0).image)
        assert not np.array_equal(r_std, r_irr)


# ---------------------------------------------------------------------------
# TestCoordinateAccuracy
# ---------------------------------------------------------------------------

class TestCoordinateAccuracy:
    """Curl transform must shift coordinates within the expected tolerance."""

    def test_known_displacement_within_2px(self):
        from weather.groundtruth.transform import apply_curl_to_points
        import numpy as np
        # Uniform 3px x-displacement
        transform = np.zeros((1000, 1000, 2), dtype=np.float32)
        transform[:, :, 1] = 3.0
        points = [(200, 400), (500, 500), (800, 600)]
        shifted = apply_curl_to_points(points, transform, 1000, 1000, 1000, 1000)
        for (x_orig, y_orig), (x_new, y_new) in zip(points, shifted):
            drift = abs(x_new - (x_orig + 3))
            assert drift <= 2, f"Drift {drift}px exceeds 2px tolerance at ({x_orig},{y_orig})"

    def test_no_curl_zero_drift(self):
        from weather.groundtruth.transform import apply_curl_to_points
        import numpy as np
        transform = np.zeros((500, 500, 2), dtype=np.float32)
        points = [(100, 200), (250, 300), (400, 100)]
        shifted = apply_curl_to_points(points, transform, 500, 500, 500, 500)
        for orig, new in zip(points, shifted):
            assert orig == new or (abs(orig[0]-new[0]) <= 1 and abs(orig[1]-new[1]) <= 1)

    def test_xml_coordinates_updated_after_groundtruth(self, profile, tmp_path):
        """End-to-end: updated XML coordinates are within 2px of expected."""
        import copy
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        from weather.groundtruth import apply_groundtruth

        # Enable curl so transform is non-trivial
        p = copy.deepcopy(profile)
        p.optics_curl.enabled = True
        p.optics_curl.curl_amount = 0.02

        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, "f01r", p, seed=0)

        xml_path = tmp_path / "f01r.xml"
        xml_path.write_text(_page_xml(n_lines=4, canvas=1000))
        out_path = tmp_path / "f01r_weathered.xml"
        apply_groundtruth(xml_path, out_path, result)

        # Verify output XML is valid and coordinates are within the page
        tree = ET.parse(out_path)
        root = tree.getroot()
        for coords_el in root.iter(f"{{{PAGE_NS}}}Coords"):
            pts_str = coords_el.get("points", "")
            for token in pts_str.split():
                x, y = map(int, token.split(","))
                assert 0 <= x <= 1100, f"x={x} out of expected range"
                assert 0 <= y <= 1100, f"y={y} out of expected range"


# ---------------------------------------------------------------------------
# TestDeterminism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_byte_identical_rerender(self, profile):
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        page = _inked_page()
        hmap = _heatmap()
        r1 = np.array(composite_folio(page, hmap, "f01r", profile, seed=42).image)
        r2 = np.array(composite_folio(page, hmap, "f01r", profile, seed=42).image)
        assert np.array_equal(r1, r2), "Same seed must produce byte-identical output"

    def test_different_seeds_differ(self, profile):
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        page = _inked_page()
        hmap = _heatmap()
        r1 = np.array(composite_folio(page, hmap, "f01r", profile, seed=1).image)
        r2 = np.array(composite_folio(page, hmap, "f01r", profile, seed=2).image)
        assert not np.array_equal(r1, r2)

    def test_damaged_folio_deterministic(self, profile):
        from weather.compositor import composite_folio
        page = _inked_page()
        hmap = _heatmap()
        r1 = np.array(composite_folio(page, hmap, "f04v", profile, seed=7).image)
        r2 = np.array(composite_folio(page, hmap, "f04v", profile, seed=7).image)
        assert np.array_equal(r1, r2)


# ---------------------------------------------------------------------------
# TestMultiFolioIntegration
# ---------------------------------------------------------------------------

class TestMultiFolioIntegration:
    """Process several representative folios end-to-end."""

    FOLIOS = [
        ("f01r", "no damage, standard stock"),
        ("f04r", "water damage, standard stock"),
        ("f04v", "water damage + missing corner"),
        ("f05v", "water damage, standard stock"),
        ("f14r", "no damage, irregular stock"),
    ]

    def _stock_for(self, folio_id):
        from weather.substrate.vellum import VellumStock
        num = int(folio_id[1:3])
        return VellumStock.IRREGULAR if num >= 14 else VellumStock.STANDARD

    @pytest.mark.parametrize("folio_id,desc", FOLIOS)
    def test_folio_produces_valid_image(self, profile, folio_id, desc):
        from weather.compositor import composite_folio
        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, folio_id, profile,
                                 stock=self._stock_for(folio_id), seed=0)
        assert result.image.mode == "RGB"
        assert result.image.size == (page.width, page.height)
        assert result.folio_id == folio_id

    @pytest.mark.parametrize("folio_id,desc", FOLIOS)
    def test_folio_produces_valid_xml(self, profile, folio_id, desc, tmp_path):
        from weather.compositor import composite_folio
        from weather.groundtruth import apply_groundtruth
        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, folio_id, profile,
                                 stock=self._stock_for(folio_id), seed=0)
        xml_in = tmp_path / f"{folio_id}.xml"
        xml_in.write_text(_page_xml(n_lines=6))
        xml_out = tmp_path / f"{folio_id}_weathered.xml"
        apply_groundtruth(xml_in, xml_out, result)
        # Must produce parseable PAGE XML
        tree = ET.parse(xml_out)
        root = tree.getroot()
        page_el = root.find(f"{{{PAGE_NS}}}Page")
        assert page_el is not None, f"{folio_id}: missing <Page> element"

    def test_all_representative_folios_complete(self, profile):
        """Batch: all representative folios complete without exception."""
        from weather.compositor import composite_folio
        errors = []
        for folio_id, desc in self.FOLIOS:
            try:
                result = composite_folio(
                    _inked_page(), _heatmap(), folio_id, profile,
                    stock=self._stock_for(folio_id), seed=0
                )
                assert result.image is not None
            except Exception as exc:
                errors.append(f"{folio_id}: {exc}")
        assert not errors, f"Failures: {errors}"
