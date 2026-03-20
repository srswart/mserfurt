"""Unit tests for Weather aging effects — ADV-WX-AGING-001.

RED phase: weather.aging modules are not yet implemented.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

PROFILE_TOML = Path(__file__).parent.parent / "shared" / "profiles" / "ms-erfurt-560yr.toml"

_PAGE_W, _PAGE_H = 200, 280  # synthetic page sized to exercise mm-based effects


def _grey_page(w=_PAGE_W, h=_PAGE_H, value=200) -> Image.Image:
    """Neutral grey page — makes darkening easy to measure."""
    return Image.fromarray(
        np.full((h, w, 3), value, dtype=np.uint8), mode="RGB"
    )


@pytest.fixture(scope="module")
def profile():
    from weather.profile import load_profile
    return load_profile(PROFILE_TOML)


# ---------------------------------------------------------------------------
# TestProfileAgingParams
# ---------------------------------------------------------------------------

class TestProfileAgingParams:
    def test_aging_edge_loaded(self, profile):
        from weather.profile import EdgeDarkeningParams
        assert isinstance(profile.aging_edge, EdgeDarkeningParams)
        assert 0 < profile.aging_edge.width_fraction < 1
        assert 0 < profile.aging_edge.opacity <= 1

    def test_aging_foxing_loaded(self, profile):
        from weather.profile import FoxingParams
        assert isinstance(profile.aging_foxing, FoxingParams)
        assert profile.aging_foxing.spot_density > 0
        assert len(profile.aging_foxing.spot_radius_range) == 2

    def test_aging_shadow_loaded(self, profile):
        from weather.profile import BindingShadowParams
        assert isinstance(profile.aging_shadow, BindingShadowParams)
        assert 0 < profile.aging_shadow.width_fraction < 1
        assert 0 < profile.aging_shadow.opacity <= 1


# ---------------------------------------------------------------------------
# TestEdgeDarkening
# ---------------------------------------------------------------------------

class TestEdgeDarkening:
    def test_returns_same_size(self, profile):
        from weather.aging.edge import apply_edge_darkening
        page = _grey_page()
        result = apply_edge_darkening(page, profile)
        assert result.size == page.size

    def test_corners_darkest(self, profile):
        from weather.aging.edge import apply_edge_darkening
        page = _grey_page()
        result = apply_edge_darkening(page, profile)
        arr = np.array(result)
        # Corner pixel (0, 0) should be darkest — two edge gradients overlap
        corner = int(arr[0, 0, 0])
        centre = int(arr[_PAGE_H // 2, _PAGE_W // 2, 0])
        assert corner < centre, "Corner should be darker than centre"

    def test_top_edge_darker_than_centre(self, profile):
        from weather.aging.edge import apply_edge_darkening
        page = _grey_page()
        result = apply_edge_darkening(page, profile)
        arr = np.array(result)
        top_mid = int(arr[2, _PAGE_W // 2, 0])
        centre = int(arr[_PAGE_H // 2, _PAGE_W // 2, 0])
        assert top_mid < centre, "Top edge should be darker than centre"

    def test_bottom_edge_darker_than_centre(self, profile):
        from weather.aging.edge import apply_edge_darkening
        page = _grey_page()
        result = apply_edge_darkening(page, profile)
        arr = np.array(result)
        bot_mid = int(arr[-3, _PAGE_W // 2, 0])
        centre = int(arr[_PAGE_H // 2, _PAGE_W // 2, 0])
        assert bot_mid < centre, "Bottom edge should be darker than centre"

    def test_darkening_grows_toward_edge(self, profile):
        from weather.aging.edge import apply_edge_darkening
        page = _grey_page()
        result = apply_edge_darkening(page, profile)
        arr = np.array(result)
        # Luminance should monotonically decrease from centre to top along centre column
        col = _PAGE_W // 2
        centre_row = _PAGE_H // 2
        quarter_row = _PAGE_H // 4
        top_row = 2
        lum_centre = int(arr[centre_row, col, 0])
        lum_quarter = int(arr[quarter_row, col, 0])
        lum_top = int(arr[top_row, col, 0])
        assert lum_centre >= lum_quarter >= lum_top, (
            f"Luminance should decrease toward top edge: "
            f"centre={lum_centre}, quarter={lum_quarter}, top={lum_top}"
        )


# ---------------------------------------------------------------------------
# TestFoxing
# ---------------------------------------------------------------------------

class TestFoxing:
    def test_returns_same_size(self, profile):
        from weather.aging.foxing import apply_foxing
        page = _grey_page()
        result = apply_foxing(page, profile, seed=0)
        assert result.size == page.size

    def test_spots_present(self, profile):
        """At least some pixels should be shifted toward spot_color."""
        from weather.aging.foxing import apply_foxing
        page = _grey_page(value=220)
        result = apply_foxing(page, profile, seed=0)
        arr_in = np.array(page)
        arr_out = np.array(result)
        # Foxing spots shift R channel down (spot_color R=165 < background 220)
        diff = arr_in[:, :, 0].astype(int) - arr_out[:, :, 0].astype(int)
        assert diff.max() > 5, "Expected some pixels darkened by foxing spots"

    def test_spots_within_bounds(self, profile):
        """No pixel outside the page should be affected (trivially true for arrays)."""
        from weather.aging.foxing import apply_foxing
        page = _grey_page()
        result = apply_foxing(page, profile, seed=42)
        arr = np.array(result)
        assert arr.shape == (_PAGE_H, _PAGE_W, 3)

    def test_deterministic(self, profile):
        from weather.aging.foxing import apply_foxing
        page = _grey_page()
        r1 = np.array(apply_foxing(page, profile, seed=7))
        r2 = np.array(apply_foxing(page, profile, seed=7))
        assert np.array_equal(r1, r2)

    def test_different_seeds_differ(self, profile):
        from weather.aging.foxing import apply_foxing
        page = _grey_page()
        r1 = np.array(apply_foxing(page, profile, seed=1))
        r2 = np.array(apply_foxing(page, profile, seed=2))
        assert not np.array_equal(r1, r2)


# ---------------------------------------------------------------------------
# TestBindingShadow
# ---------------------------------------------------------------------------

class TestBindingShadow:
    def test_returns_same_size(self, profile):
        from weather.aging.shadow import apply_binding_shadow
        page = _grey_page()
        result = apply_binding_shadow(page, "f01r", profile)
        assert result.size == page.size

    def test_recto_shadow_on_left(self, profile):
        """Recto folio (f01r): gutter is on the left — left column darker."""
        from weather.aging.shadow import apply_binding_shadow
        page = _grey_page()
        result = apply_binding_shadow(page, "f01r", profile)
        arr = np.array(result)
        left_col = int(arr[_PAGE_H // 2, 2, 0])
        right_col = int(arr[_PAGE_H // 2, -3, 0])
        assert left_col < right_col, (
            f"Recto: left col ({left_col}) should be darker than right col ({right_col})"
        )

    def test_verso_shadow_on_right(self, profile):
        """Verso folio (f01v): gutter is on the right — right column darker."""
        from weather.aging.shadow import apply_binding_shadow
        page = _grey_page()
        result = apply_binding_shadow(page, "f01v", profile)
        arr = np.array(result)
        left_col = int(arr[_PAGE_H // 2, 2, 0])
        right_col = int(arr[_PAGE_H // 2, -3, 0])
        assert right_col < left_col, (
            f"Verso: right col ({right_col}) should be darker than left col ({left_col})"
        )

    def test_shadow_fades_from_gutter(self, profile):
        """Shadow intensity decreases moving away from the gutter (recto = left)."""
        from weather.aging.shadow import apply_binding_shadow
        page = _grey_page()
        result = apply_binding_shadow(page, "f01r", profile)
        arr = np.array(result)
        mid_row = _PAGE_H // 2
        lum_near = int(arr[mid_row, 1, 0])
        lum_mid = int(arr[mid_row, _PAGE_W // 4, 0])
        lum_far = int(arr[mid_row, _PAGE_W // 2, 0])
        assert lum_near <= lum_mid <= lum_far, (
            f"Shadow should fade from gutter: near={lum_near}, mid={lum_mid}, far={lum_far}"
        )

    def test_non_damage_folio_still_gets_shadow(self, profile):
        """All folios get binding shadow — it's general aging, not damage."""
        from weather.aging.shadow import apply_binding_shadow
        page = _grey_page()
        result = apply_binding_shadow(page, "f14r", profile)
        arr = np.array(result)
        assert arr[_PAGE_H // 2, 2, 0] < arr[_PAGE_H // 2, -3, 0]  # recto = left shadow


# ---------------------------------------------------------------------------
# TestApplyAging (orchestrator)
# ---------------------------------------------------------------------------

class TestApplyAging:
    def test_returns_pil_image(self, profile):
        from weather.aging import apply_aging
        page = _grey_page()
        result = apply_aging(page, "f01r", profile, seed=0)
        assert isinstance(result, Image.Image)

    def test_same_size(self, profile):
        from weather.aging import apply_aging
        page = _grey_page()
        result = apply_aging(page, "f01r", profile, seed=0)
        assert result.size == page.size

    def test_deterministic(self, profile):
        from weather.aging import apply_aging
        page = _grey_page()
        r1 = np.array(apply_aging(page, "f01r", profile, seed=5))
        r2 = np.array(apply_aging(page, "f01r", profile, seed=5))
        assert np.array_equal(r1, r2)

    def test_output_darker_than_input(self, profile):
        """All aging effects darken — mean luminance should decrease."""
        from weather.aging import apply_aging
        page = _grey_page(value=220)
        result = apply_aging(page, "f01r", profile, seed=0)
        mean_in = np.array(page).mean()
        mean_out = np.array(result).mean()
        assert mean_out < mean_in, "Aging should darken the page overall"

    def test_recto_and_verso_differ(self, profile):
        """Binding shadow differs by side — recto and verso outputs should differ."""
        from weather.aging import apply_aging
        page = _grey_page()
        r = np.array(apply_aging(page, "f01r", profile, seed=0))
        v = np.array(apply_aging(page, "f01v", profile, seed=0))
        assert not np.array_equal(r, v)
