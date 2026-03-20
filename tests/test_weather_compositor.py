"""Unit tests for Weather compositor — ADV-WX-COMPOSITOR-001.

RED phase: weather.compositor modules are not yet implemented.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

PROFILE_TOML = Path(__file__).parent.parent / "shared" / "profiles" / "ms-erfurt-560yr.toml"

_PAGE_W, _PAGE_H = 128, 180


def _parchment_page(w=_PAGE_W, h=_PAGE_H) -> Image.Image:
    """Warm parchment background — like ScribeSim output before ink."""
    return Image.fromarray(
        np.full((h, w, 3), [242, 228, 196], dtype=np.uint8), mode="RGB"
    )


def _inked_page(w=_PAGE_W, h=_PAGE_H) -> Image.Image:
    """Page with a horizontal ink stripe — simulates ScribeSim output."""
    arr = np.full((h, w, 3), 255, dtype=np.uint8)  # white background
    arr[h // 3 : h // 3 + 10, 10:-10, :] = 20  # dark ink stripe
    return Image.fromarray(arr, mode="RGB")


def _heatmap(w=_PAGE_W, h=_PAGE_H) -> Image.Image:
    arr = np.full((h, w), 128, dtype=np.uint8)
    arr[h // 3 : h // 3 + 10, 10:-10] = 200  # high pressure at ink stripe
    return Image.fromarray(arr, mode="L")


def _manifest_json(tmp_path: Path, folios: list[dict]) -> Path:
    data = {
        "manuscript": {"shelfmark": "test"},
        "folios": folios,
    }
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(data))
    return p


@pytest.fixture(scope="module")
def profile():
    from weather.profile import load_profile
    return load_profile(PROFILE_TOML)


# ---------------------------------------------------------------------------
# TestManifestReader
# ---------------------------------------------------------------------------

class TestManifestReader:
    def test_parses_standard_stock(self, tmp_path):
        from weather.compositor.manifest import load_manifest
        mf = _manifest_json(tmp_path, [
            {"id": "f01r", "vellum_stock": "standard", "damage_type": None},
        ])
        entries = load_manifest(mf)
        assert "f01r" in entries
        assert entries["f01r"].vellum_stock == "standard"
        assert entries["f01r"].damage_type is None

    def test_parses_irregular_stock(self, tmp_path):
        from weather.compositor.manifest import load_manifest
        mf = _manifest_json(tmp_path, [
            {"id": "f14r", "vellum_stock": "irregular", "damage_type": None},
        ])
        entries = load_manifest(mf)
        assert entries["f14r"].vellum_stock == "irregular"

    def test_parses_damage_type(self, tmp_path):
        from weather.compositor.manifest import load_manifest
        mf = _manifest_json(tmp_path, [
            {"id": "f04r", "vellum_stock": "standard", "damage_type": "water_damage"},
        ])
        entries = load_manifest(mf)
        assert entries["f04r"].damage_type == "water_damage"

    def test_missing_fields_use_defaults(self, tmp_path):
        from weather.compositor.manifest import load_manifest
        mf = _manifest_json(tmp_path, [
            {"id": "f03r"},  # minimal entry
        ])
        entries = load_manifest(mf)
        assert entries["f03r"].vellum_stock == "standard"
        assert entries["f03r"].damage_type is None

    def test_multiple_folios(self, tmp_path):
        from weather.compositor.manifest import load_manifest
        mf = _manifest_json(tmp_path, [
            {"id": "f01r", "vellum_stock": "standard"},
            {"id": "f14r", "vellum_stock": "irregular"},
            {"id": "f04v", "vellum_stock": "standard", "damage_type": "water_damage"},
        ])
        entries = load_manifest(mf)
        assert len(entries) == 3
        assert "f01r" in entries
        assert "f14r" in entries
        assert "f04v" in entries


# ---------------------------------------------------------------------------
# TestStockSelection
# ---------------------------------------------------------------------------

class TestStockSelection:
    def test_f01r_standard(self, profile):
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, "f01r", profile, seed=0)
        assert result.folio_id == "f01r"

    def test_manifest_stock_overrides_default(self, tmp_path):
        from weather.compositor.manifest import load_manifest, ManifestEntry
        # f01r is normally standard, but manifest can override
        mf = _manifest_json(tmp_path, [
            {"id": "f01r", "vellum_stock": "irregular"},
        ])
        entries = load_manifest(mf)
        assert entries["f01r"].vellum_stock == "irregular"

    def test_stock_affects_output(self, profile):
        """Standard and irregular stock produce different substrate textures."""
        from weather.compositor import composite_folio
        from weather.substrate.vellum import VellumStock
        page = _inked_page()
        hmap = _heatmap()
        r_std = np.array(composite_folio(
            page, hmap, "f01r", profile, stock=VellumStock.STANDARD, seed=0
        ).image)
        r_irr = np.array(composite_folio(
            page, hmap, "f01r", profile, stock=VellumStock.IRREGULAR, seed=0
        ).image)
        assert not np.array_equal(r_std, r_irr)


# ---------------------------------------------------------------------------
# TestCompositorDispatch
# ---------------------------------------------------------------------------

class TestCompositorDispatch:
    def test_f04r_no_curl_transform(self, profile):
        """Curl is disabled in default profile — no transform returned."""
        from weather.compositor import composite_folio
        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, "f04r", profile, seed=0)
        assert result.curl_transform is None

    def test_f01r_output_image_size(self, profile):
        from weather.compositor import composite_folio
        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, "f01r", profile, seed=0)
        assert result.image.size == (page.width, page.height)

    def test_f04v_output_image_size(self, profile):
        """f04v gets all damage effects — still same size."""
        from weather.compositor import composite_folio
        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, "f04v", profile, seed=0)
        assert result.image.size == (page.width, page.height)

    def test_f04v_differs_from_f01r(self, profile):
        """f04v gets water damage + missing corner; f01r gets none."""
        from weather.compositor import composite_folio
        page = _inked_page()
        hmap = _heatmap()
        r04v = np.array(composite_folio(page, hmap, "f04v", profile, seed=0).image)
        r01r = np.array(composite_folio(page, hmap, "f01r", profile, seed=0).image)
        assert not np.array_equal(r04v, r01r)


# ---------------------------------------------------------------------------
# TestCompositorResult
# ---------------------------------------------------------------------------

class TestCompositorResult:
    def test_returns_compositor_result(self, profile):
        from weather.compositor import composite_folio, CompositorResult
        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, "f01r", profile, seed=0)
        assert isinstance(result, CompositorResult)

    def test_result_has_folio_id(self, profile):
        from weather.compositor import composite_folio
        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, "f07r", profile, seed=0)
        assert result.folio_id == "f07r"

    def test_result_image_is_rgb(self, profile):
        from weather.compositor import composite_folio
        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, "f01r", profile, seed=0)
        assert result.image.mode == "RGB"

    def test_deterministic(self, profile):
        from weather.compositor import composite_folio
        page = _inked_page()
        hmap = _heatmap()
        r1 = np.array(composite_folio(page, hmap, "f01r", profile, seed=5).image)
        r2 = np.array(composite_folio(page, hmap, "f01r", profile, seed=5).image)
        assert np.array_equal(r1, r2)

    def test_substrate_visible_in_output(self, profile):
        """Output background should reflect substrate color (not pure white)."""
        from weather.compositor import composite_folio
        page = _inked_page()  # has white background, dark ink stripe
        hmap = _heatmap()
        result = composite_folio(page, hmap, "f01r", profile, seed=0)
        arr = np.array(result.image)
        # Find a pixel that was white in input (not in ink stripe)
        bg_pixel = arr[_PAGE_H - 5, _PAGE_W // 2]
        # Standard substrate base is [242, 228, 196] — not pure white [255, 255, 255]
        assert not np.array_equal(bg_pixel, [255, 255, 255]), (
            "Background should show substrate, not pure white"
        )

    def test_curl_enabled_returns_transform(self, profile):
        import copy
        from weather.compositor import composite_folio
        p = copy.deepcopy(profile)
        p.optics_curl.enabled = True
        page = _inked_page()
        hmap = _heatmap()
        result = composite_folio(page, hmap, "f01r", p, seed=0)
        assert result.curl_transform is not None
        assert result.curl_transform.shape == (_PAGE_H, _PAGE_W, 2)
