"""Unit tests for Weather ink aging — ADV-WX-INK-001.

RED phase: weather.ink modules are not yet implemented.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

PROFILE_TOML = Path(__file__).parent.parent / "shared" / "profiles" / "ms-erfurt-560yr.toml"

# ---------------------------------------------------------------------------
# Helpers: synthetic test images
# ---------------------------------------------------------------------------

def _parchment_with_ink_stripe(width=64, height=64) -> Image.Image:
    """RGB image: warm parchment background with a horizontal black ink stripe."""
    arr = np.full((height, width, 3), [242, 228, 196], dtype=np.uint8)
    arr[20:30, 10:54] = [18, 12, 8]   # ink stripe
    return Image.fromarray(arr, mode="RGB")


def _flat_heatmap(width=64, height=64, value=0) -> Image.Image:
    """Grayscale heatmap filled with a uniform value (0–255)."""
    return Image.fromarray(
        np.full((height, width), value, dtype=np.uint8), mode="L"
    )


def _stripe_heatmap(width=64, height=64) -> Image.Image:
    """Grayscale heatmap: high pressure (230) in the same stripe as the ink."""
    arr = np.zeros((height, width), dtype=np.uint8)
    arr[20:30, 10:54] = 230
    return Image.fromarray(arr, mode="L")


@pytest.fixture(scope="module")
def profile():
    from weather.profile import load_profile
    return load_profile(PROFILE_TOML)


@pytest.fixture
def ink_image():
    return _parchment_with_ink_stripe()


@pytest.fixture
def zero_heatmap():
    return _flat_heatmap(value=0)


@pytest.fixture
def high_heatmap():
    return _stripe_heatmap()


# ---------------------------------------------------------------------------
# TestExtractInkMask
# ---------------------------------------------------------------------------

class TestExtractInkMask:
    def test_returns_bool_array_same_shape(self, ink_image):
        from weather.ink.mask import extract_ink_mask
        mask = extract_ink_mask(ink_image)
        arr = np.array(ink_image)
        assert mask.shape == (arr.shape[0], arr.shape[1])
        assert mask.dtype == bool

    def test_ink_pixels_are_true(self, ink_image):
        from weather.ink.mask import extract_ink_mask
        mask = extract_ink_mask(ink_image)
        # Pixels in the ink stripe (rows 20–29) should be masked
        assert mask[25, 32], "Central ink pixel not detected as ink"

    def test_background_pixels_are_false(self, ink_image):
        from weather.ink.mask import extract_ink_mask
        mask = extract_ink_mask(ink_image)
        # Parchment pixels (row 5) should not be masked
        assert not mask[5, 32], "Parchment pixel incorrectly detected as ink"

    def test_threshold_controls_sensitivity(self):
        from weather.ink.mask import extract_ink_mask
        # Grey pixel (128, 128, 128): above strict threshold → not ink; below loose → ink
        grey = Image.fromarray(
            np.full((8, 8, 3), 128, dtype=np.uint8), mode="RGB"
        )
        strict = extract_ink_mask(grey, threshold=100)  # 128 > 100 → not ink
        loose  = extract_ink_mask(grey, threshold=200)  # 128 < 200 → ink
        assert not strict.any(), "Strict threshold incorrectly detected grey as ink"
        assert loose.any(),  "Loose threshold missed grey pixel as ink"


# ---------------------------------------------------------------------------
# TestInkFade
# ---------------------------------------------------------------------------

class TestInkFade:
    def test_ink_pixels_become_brighter(self, ink_image, profile):
        from weather.ink.mask import extract_ink_mask
        from weather.ink.fade import ink_fade
        mask = extract_ink_mask(ink_image)
        result = ink_fade(np.array(ink_image), mask, profile)
        orig_mean = np.array(ink_image)[mask].astype(float).mean()
        result_mean = result[mask].astype(float).mean()
        assert result_mean > orig_mean, (
            f"Faded ink mean ({result_mean:.1f}) should exceed original ({orig_mean:.1f})"
        )

    def test_ink_red_channel_increases(self, ink_image, profile):
        """Iron gall fade shifts ink toward brown — red channel should increase."""
        from weather.ink.mask import extract_ink_mask
        from weather.ink.fade import ink_fade
        mask = extract_ink_mask(ink_image)
        orig = np.array(ink_image)
        result = ink_fade(orig, mask, profile)
        assert result[mask, 0].mean() > orig[mask, 0].mean(), (
            "Red channel of ink pixels did not increase after fade"
        )

    def test_red_increases_more_than_blue(self, ink_image, profile):
        """Red lift exceeds blue lift — net shift toward warm brown (less blue gain)."""
        from weather.ink.mask import extract_ink_mask
        from weather.ink.fade import ink_fade
        mask = extract_ink_mask(ink_image)
        orig = np.array(ink_image)
        result = ink_fade(orig, mask, profile)
        r_gain = result[mask, 0].mean() - orig[mask, 0].mean()
        b_gain = result[mask, 2].mean() - orig[mask, 2].mean()
        assert r_gain > b_gain, (
            f"Red gain ({r_gain:.1f}) should exceed blue gain ({b_gain:.1f}) — "
            "fade should shift ink toward warm brown"
        )

    def test_non_ink_pixels_unchanged(self, ink_image, profile):
        from weather.ink.mask import extract_ink_mask
        from weather.ink.fade import ink_fade
        mask = extract_ink_mask(ink_image)
        orig = np.array(ink_image)
        result = ink_fade(orig, mask, profile)
        np.testing.assert_array_equal(
            orig[~mask], result[~mask],
            err_msg="ink_fade modified non-ink (background) pixels"
        )

    def test_returns_uint8_array(self, ink_image, profile):
        from weather.ink.mask import extract_ink_mask
        from weather.ink.fade import ink_fade
        mask = extract_ink_mask(ink_image)
        result = ink_fade(np.array(ink_image), mask, profile)
        assert result.dtype == np.uint8
        assert result.shape == np.array(ink_image).shape


# ---------------------------------------------------------------------------
# TestInkBleed
# ---------------------------------------------------------------------------

class TestInkBleed:
    def test_output_differs_from_input(self, ink_image, profile):
        from weather.ink.mask import extract_ink_mask
        from weather.ink.bleed import ink_bleed
        mask = extract_ink_mask(ink_image)
        orig = np.array(ink_image)
        result = ink_bleed(orig, mask, profile.ink_bleed.radius_px)
        assert not np.array_equal(orig, result), "ink_bleed produced no change"

    def test_non_ink_background_unchanged(self, ink_image, profile):
        """Background pixels far from ink edges must remain exactly unchanged."""
        from weather.ink.mask import extract_ink_mask
        from weather.ink.bleed import ink_bleed
        mask = extract_ink_mask(ink_image)
        orig = np.array(ink_image)
        result = ink_bleed(orig, mask, profile.ink_bleed.radius_px)
        # Row 5 is far from the ink stripe (rows 20-29) — should be unchanged
        np.testing.assert_array_equal(
            orig[5, :], result[5, :],
            err_msg="ink_bleed changed far-background pixels"
        )

    def test_returns_uint8_array(self, ink_image, profile):
        from weather.ink.mask import extract_ink_mask
        from weather.ink.bleed import ink_bleed
        mask = extract_ink_mask(ink_image)
        result = ink_bleed(np.array(ink_image), mask, profile.ink_bleed.radius_px)
        assert result.dtype == np.uint8
        assert result.shape == np.array(ink_image).shape


# ---------------------------------------------------------------------------
# TestInkFlake
# ---------------------------------------------------------------------------

class TestInkFlake:
    def test_high_pressure_removes_ink_pixels(self, ink_image, profile):
        from weather.ink.mask import extract_ink_mask
        from weather.ink.flake import ink_flake
        mask = extract_ink_mask(ink_image)
        orig = np.array(ink_image)
        heatmap = np.full((64, 64), 230, dtype=np.uint8)   # above 0.85 threshold
        result = ink_flake(orig, mask, heatmap, profile, seed=42)
        # At least some ink pixels should become lighter (flaked)
        ink_before = orig[mask].astype(float).mean()
        ink_after  = result[mask].astype(float).mean()
        assert ink_after > ink_before, (
            "ink_flake with high pressure removed no ink pixels"
        )

    def test_zero_pressure_removes_nothing(self, ink_image, profile):
        from weather.ink.mask import extract_ink_mask
        from weather.ink.flake import ink_flake
        mask = extract_ink_mask(ink_image)
        orig = np.array(ink_image)
        heatmap = np.zeros((64, 64), dtype=np.uint8)   # no pressure → no flaking
        result = ink_flake(orig, mask, heatmap, profile, seed=42)
        np.testing.assert_array_equal(
            orig, result,
            err_msg="ink_flake with zero heatmap modified pixels"
        )

    def test_deterministic_with_same_seed(self, ink_image, profile):
        from weather.ink.mask import extract_ink_mask
        from weather.ink.flake import ink_flake
        mask = extract_ink_mask(ink_image)
        orig = np.array(ink_image)
        heatmap = np.full((64, 64), 230, dtype=np.uint8)
        r1 = ink_flake(orig, mask, heatmap, profile, seed=7)
        r2 = ink_flake(orig, mask, heatmap, profile, seed=7)
        np.testing.assert_array_equal(r1, r2, err_msg="ink_flake not deterministic")

    def test_returns_uint8_array(self, ink_image, profile):
        from weather.ink.mask import extract_ink_mask
        from weather.ink.flake import ink_flake
        mask = extract_ink_mask(ink_image)
        orig = np.array(ink_image)
        heatmap = np.zeros((64, 64), dtype=np.uint8)
        result = ink_flake(orig, mask, heatmap, profile, seed=0)
        assert result.dtype == np.uint8
        assert result.shape == orig.shape


# ---------------------------------------------------------------------------
# TestApplyInkAging
# ---------------------------------------------------------------------------

class TestApplyInkAging:
    def test_returns_pil_image(self, ink_image, zero_heatmap, profile):
        from weather.ink.aging import apply_ink_aging
        result = apply_ink_aging(ink_image, zero_heatmap, profile, seed=0)
        assert isinstance(result, Image.Image)

    def test_output_dimensions_match_input(self, ink_image, zero_heatmap, profile):
        from weather.ink.aging import apply_ink_aging
        result = apply_ink_aging(ink_image, zero_heatmap, profile, seed=0)
        assert result.size == ink_image.size

    def test_aging_modifies_ink(self, ink_image, zero_heatmap, profile):
        from weather.ink.aging import apply_ink_aging
        result = apply_ink_aging(ink_image, zero_heatmap, profile, seed=0)
        orig_arr = np.array(ink_image)
        result_arr = np.array(result)
        assert not np.array_equal(orig_arr, result_arr), (
            "apply_ink_aging produced no change to the page image"
        )

    def test_deterministic_with_same_seed(self, ink_image, high_heatmap, profile):
        from weather.ink.aging import apply_ink_aging
        r1 = apply_ink_aging(ink_image, high_heatmap, profile, seed=1457)
        r2 = apply_ink_aging(ink_image, high_heatmap, profile, seed=1457)
        np.testing.assert_array_equal(
            np.array(r1), np.array(r2),
            err_msg="apply_ink_aging is not deterministic"
        )
