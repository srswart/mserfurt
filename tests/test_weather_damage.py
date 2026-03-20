"""Unit tests for Weather damage effects — ADV-WX-DAMAGE-001.

RED phase: weather.damage modules are not yet implemented.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

PROFILE_TOML = Path(__file__).parent.parent / "shared" / "profiles" / "ms-erfurt-560yr.toml"

_BACKING_COLOR = (255, 248, 235)  # backing board color from ms-erfurt-560yr.toml
_PAGE_W, _PAGE_H = 128, 160   # small synthetic page for fast tests


def _parchment_page(w=_PAGE_W, h=_PAGE_H) -> Image.Image:
    return Image.fromarray(
        np.full((h, w, 3), [242, 228, 196], dtype=np.uint8), mode="RGB"
    )


@pytest.fixture(scope="module")
def profile():
    from weather.profile import load_profile
    return load_profile(PROFILE_TOML)


@pytest.fixture
def page():
    return _parchment_page()


# ---------------------------------------------------------------------------
# TestDispatch
# ---------------------------------------------------------------------------

class TestDispatch:
    @pytest.mark.parametrize("folio_id", ["f04r", "f04v", "f05r", "f05v"])
    def test_water_damaged_folios(self, folio_id):
        from weather.damage.dispatch import folio_is_water_damaged
        assert folio_is_water_damaged(folio_id), f"{folio_id} should have water damage"

    @pytest.mark.parametrize("folio_id", ["f01r", "f03v", "f06r", "f14r", "f17v"])
    def test_non_water_damaged_folios(self, folio_id):
        from weather.damage.dispatch import folio_is_water_damaged
        assert not folio_is_water_damaged(folio_id), f"{folio_id} should not have water damage"

    def test_missing_corner_only_f04v(self):
        from weather.damage.dispatch import folio_has_missing_corner
        assert folio_has_missing_corner("f04v")

    @pytest.mark.parametrize("folio_id", ["f04r", "f05r", "f05v", "f01r", "f14r"])
    def test_no_missing_corner_other_folios(self, folio_id):
        from weather.damage.dispatch import folio_has_missing_corner
        assert not folio_has_missing_corner(folio_id), (
            f"{folio_id} should not have missing corner"
        )


# ---------------------------------------------------------------------------
# TestTideLine
# ---------------------------------------------------------------------------

class TestTideLine:
    def test_returns_binary_array_correct_shape(self):
        from weather.damage.water import tide_line_mask
        mask = tide_line_mask(width=64, height=80, penetration=0.4, seed=42)
        assert mask.shape == (80, 64)
        assert mask.dtype == bool

    def test_has_both_wet_and_dry_regions(self):
        from weather.damage.water import tide_line_mask
        mask = tide_line_mask(width=64, height=80, penetration=0.4, seed=7)
        assert mask.any(), "Tide line mask has no wet pixels"
        assert not mask.all(), "Tide line mask is entirely wet"

    def test_top_rows_wetter_than_bottom(self):
        """Top of page (water ingress from above) should have more wet pixels."""
        from weather.damage.water import tide_line_mask
        mask = tide_line_mask(width=64, height=80, penetration=0.4, seed=0)
        top_wet = mask[:10, :].sum()
        bottom_wet = mask[-10:, :].sum()
        assert top_wet > bottom_wet, (
            f"Top wet ({top_wet}) should exceed bottom wet ({bottom_wet}) for from_above damage"
        )

    def test_deterministic_with_same_seed(self):
        from weather.damage.water import tide_line_mask
        a = tide_line_mask(width=64, height=80, penetration=0.4, seed=1)
        b = tide_line_mask(width=64, height=80, penetration=0.4, seed=1)
        np.testing.assert_array_equal(a, b)

    def test_different_seeds_produce_distinct_masks(self):
        from weather.damage.water import tide_line_mask
        a = tide_line_mask(width=64, height=80, penetration=0.4, seed=1)
        b = tide_line_mask(width=64, height=80, penetration=0.4, seed=2)
        assert not np.array_equal(a, b)


# ---------------------------------------------------------------------------
# TestWaterDamage
# ---------------------------------------------------------------------------

class TestWaterDamage:
    def test_passthrough_for_undamaged_folio(self, page, profile):
        from weather.damage.water import apply_water_damage
        result = apply_water_damage(page, "f01r", profile, seed=0)
        np.testing.assert_array_equal(
            np.array(page), np.array(result.image),
            err_msg="apply_water_damage modified an undamaged folio"
        )

    def test_passthrough_has_no_zone_mask(self, page, profile):
        from weather.damage.water import apply_water_damage
        result = apply_water_damage(page, "f01r", profile, seed=0)
        assert result.water_zone is None or not result.water_zone.any()

    def test_f04r_top_darker_than_bottom(self, profile):
        from weather.damage.water import apply_water_damage
        page = _parchment_page()
        result = apply_water_damage(page, "f04r", profile, seed=42)
        arr = np.array(result.image.convert("L"), dtype=float)
        top_mean = arr[:16, :].mean()
        bottom_mean = arr[-16:, :].mean()
        assert top_mean < bottom_mean, (
            f"Top mean ({top_mean:.1f}) should be darker than bottom ({bottom_mean:.1f})"
        )

    def test_f04r_returns_water_zone_mask(self, profile):
        from weather.damage.water import apply_water_damage
        page = _parchment_page()
        result = apply_water_damage(page, "f04r", profile, seed=0)
        assert result.water_zone is not None
        assert result.water_zone.any(), "Water zone mask is empty for f04r"

    def test_returns_damage_result(self, page, profile):
        from weather.damage.water import apply_water_damage
        from weather.damage.zones import DamageResult
        result = apply_water_damage(page, "f04r", profile, seed=0)
        assert isinstance(result, DamageResult)

    def test_output_dimensions_unchanged(self, profile):
        from weather.damage.water import apply_water_damage
        page = _parchment_page()
        result = apply_water_damage(page, "f04r", profile, seed=0)
        assert result.image.size == page.size


# ---------------------------------------------------------------------------
# TestMissingCorner
# ---------------------------------------------------------------------------

class TestMissingCorner:
    def test_passthrough_for_non_f04v(self, page, profile):
        from weather.damage.corner import apply_missing_corner
        result = apply_missing_corner(page, "f04r", profile, seed=0)
        np.testing.assert_array_equal(
            np.array(page), np.array(result.image),
            err_msg="apply_missing_corner modified a folio other than f04v"
        )

    def test_passthrough_has_no_corner_mask(self, page, profile):
        from weather.damage.corner import apply_missing_corner
        result = apply_missing_corner(page, "f01r", profile, seed=0)
        assert result.corner_mask is None or not result.corner_mask.any()

    def test_f04v_bottom_right_has_backing_color(self, profile):
        from weather.damage.corner import apply_missing_corner
        page = _parchment_page()
        result = apply_missing_corner(page, "f04v", profile, seed=42)
        arr = np.array(result.image)
        # Bottom-right corner pixel should be close to backing color
        corner_pixel = arr[-4, -4]
        for ch, expected in enumerate(_BACKING_COLOR):
            assert abs(int(corner_pixel[ch]) - expected) < 20, (
                f"Corner pixel channel {ch}: {corner_pixel[ch]} far from backing {expected}"
            )

    def test_f04v_returns_corner_mask(self, profile):
        from weather.damage.corner import apply_missing_corner
        page = _parchment_page()
        result = apply_missing_corner(page, "f04v", profile, seed=0)
        assert result.corner_mask is not None
        assert result.corner_mask.any(), "Corner mask is empty for f04v"

    def test_corner_mask_concentrated_in_bottom_right(self, profile):
        from weather.damage.corner import apply_missing_corner
        page = _parchment_page()
        result = apply_missing_corner(page, "f04v", profile, seed=0)
        mask = result.corner_mask
        h, w = mask.shape
        # Majority of corner removal should be in bottom-right quadrant
        br_count = mask[h // 2:, w // 2:].sum()
        total = mask.sum()
        assert br_count / total >= 0.6, (
            f"Only {br_count/total:.0%} of corner removal is in bottom-right quadrant"
        )

    def test_output_dimensions_unchanged(self, profile):
        from weather.damage.corner import apply_missing_corner
        page = _parchment_page()
        result = apply_missing_corner(page, "f04v", profile, seed=0)
        assert result.image.size == page.size


# ---------------------------------------------------------------------------
# TestApplyDamage
# ---------------------------------------------------------------------------

class TestApplyDamage:
    def test_f01r_passes_through_unchanged(self, page, profile):
        from weather.damage.pipeline import apply_damage
        result = apply_damage(page, "f01r", profile, seed=0)
        np.testing.assert_array_equal(
            np.array(page), np.array(result.image),
            err_msg="apply_damage modified f01r (no damage expected)"
        )

    def test_f04v_has_both_water_and_corner(self, profile):
        from weather.damage.pipeline import apply_damage
        page = _parchment_page()
        result = apply_damage(page, "f04v", profile, seed=42)
        assert result.water_zone is not None and result.water_zone.any()
        assert result.corner_mask is not None and result.corner_mask.any()

    def test_f04r_has_water_but_no_corner(self, profile):
        from weather.damage.pipeline import apply_damage
        page = _parchment_page()
        result = apply_damage(page, "f04r", profile, seed=0)
        assert result.water_zone is not None and result.water_zone.any()
        assert result.corner_mask is None or not result.corner_mask.any()

    def test_returns_damage_result(self, page, profile):
        from weather.damage.pipeline import apply_damage
        from weather.damage.zones import DamageResult
        result = apply_damage(page, "f04v", profile, seed=0)
        assert isinstance(result, DamageResult)

    def test_deterministic_with_same_seed(self, profile):
        from weather.damage.pipeline import apply_damage
        page = _parchment_page()
        r1 = apply_damage(page, "f04v", profile, seed=7)
        r2 = apply_damage(page, "f04v", profile, seed=7)
        np.testing.assert_array_equal(
            np.array(r1.image), np.array(r2.image),
            err_msg="apply_damage is not deterministic"
        )
