"""Unit tests for Weather substrate generation — ADV-WX-SUBSTRATE-001.

RED phase: weather.substrate modules are not yet implemented.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from weather.profile import load_profile

PROFILE_TOML = __import__("pathlib").Path(__file__).parent.parent / "shared" / "profiles" / "ms-erfurt-560yr.toml"


@pytest.fixture(scope="module")
def profile():
    return load_profile(PROFILE_TOML)


# ---------------------------------------------------------------------------
# TestPerlinNoise
# ---------------------------------------------------------------------------

class TestPerlinNoise:
    def test_output_shape_matches_requested(self):
        from weather.substrate.noise import perlin_noise
        arr = perlin_noise(width=64, height=48, scale=16.0, octaves=1, seed=42)
        assert arr.shape == (48, 64)

    def test_values_in_unit_range(self):
        from weather.substrate.noise import perlin_noise
        arr = perlin_noise(width=128, height=128, scale=16.0, octaves=1, seed=0)
        assert arr.min() >= -1.0 - 1e-6
        assert arr.max() <= 1.0 + 1e-6

    def test_three_octaves_differs_from_one_octave(self):
        """Multi-octave noise must produce a different field than 1-octave."""
        from weather.substrate.noise import perlin_noise
        one = perlin_noise(width=64, height=64, scale=16.0, octaves=1, seed=7)
        three = perlin_noise(width=64, height=64, scale=16.0, octaves=3, seed=7)
        assert not np.allclose(one, three), "1-octave and 3-octave noise are identical"
        # Both should have non-trivial spatial variation
        assert one.std() > 0.01
        assert three.std() > 0.01

    def test_same_seed_is_deterministic(self):
        from weather.substrate.noise import perlin_noise
        a = perlin_noise(width=64, height=64, scale=16.0, octaves=3, seed=42)
        b = perlin_noise(width=64, height=64, scale=16.0, octaves=3, seed=42)
        np.testing.assert_array_equal(a, b)

    def test_different_seeds_produce_distinct_arrays(self):
        from weather.substrate.noise import perlin_noise
        a = perlin_noise(width=64, height=64, scale=16.0, octaves=3, seed=1)
        b = perlin_noise(width=64, height=64, scale=16.0, octaves=3, seed=2)
        assert not np.allclose(a, b), "Different seeds produced identical noise"

    def test_nonzero_spatial_variation(self):
        from weather.substrate.noise import perlin_noise
        arr = perlin_noise(width=64, height=64, scale=16.0, octaves=3, seed=0)
        assert arr.std() > 0.01, "Perlin noise has no spatial variation"


# ---------------------------------------------------------------------------
# TestFollicleMarks
# ---------------------------------------------------------------------------

class TestFollicleMarks:
    def test_output_shape_matches_input(self):
        from weather.substrate.follicles import follicle_marks
        arr = follicle_marks(width=128, height=128, density=0.001,
                             grain_angle_deg=15.0, seed=0)
        assert arr.shape == (128, 128)

    def test_nonzero_marks_present(self):
        from weather.substrate.follicles import follicle_marks
        arr = follicle_marks(width=256, height=256, density=0.003,
                             grain_angle_deg=15.0, seed=42)
        assert arr.max() > 0, "No follicle marks rendered"

    def test_different_seeds_produce_different_marks(self):
        from weather.substrate.follicles import follicle_marks
        a = follicle_marks(width=128, height=128, density=0.002,
                           grain_angle_deg=15.0, seed=1)
        b = follicle_marks(width=128, height=128, density=0.002,
                           grain_angle_deg=15.0, seed=99)
        assert not np.array_equal(a, b), "Different seeds produced identical follicles"

    def test_same_seed_is_deterministic(self):
        from weather.substrate.follicles import follicle_marks
        a = follicle_marks(width=128, height=128, density=0.002,
                           grain_angle_deg=15.0, seed=7)
        b = follicle_marks(width=128, height=128, density=0.002,
                           grain_angle_deg=15.0, seed=7)
        np.testing.assert_array_equal(a, b)


# ---------------------------------------------------------------------------
# TestVellumStock
# ---------------------------------------------------------------------------

class TestVellumStock:
    def test_f01r_is_standard(self):
        from weather.substrate.vellum import stock_for_folio, VellumStock
        assert stock_for_folio("f01r") == VellumStock.STANDARD

    def test_f13v_is_standard(self):
        from weather.substrate.vellum import stock_for_folio, VellumStock
        assert stock_for_folio("f13v") == VellumStock.STANDARD

    def test_f14r_is_irregular(self):
        from weather.substrate.vellum import stock_for_folio, VellumStock
        assert stock_for_folio("f14r") == VellumStock.IRREGULAR

    def test_f17v_is_irregular(self):
        from weather.substrate.vellum import stock_for_folio, VellumStock
        assert stock_for_folio("f17v") == VellumStock.IRREGULAR


# ---------------------------------------------------------------------------
# TestGenerateSubstrate
# ---------------------------------------------------------------------------

class TestGenerateSubstrate:
    def test_returns_pil_image(self, profile):
        from weather.substrate.vellum import generate_substrate, VellumStock
        img = generate_substrate(width=128, height=160, stock=VellumStock.STANDARD,
                                 profile=profile, seed=42)
        assert isinstance(img, Image.Image)

    def test_output_dimensions_match_request(self, profile):
        from weather.substrate.vellum import generate_substrate, VellumStock
        img = generate_substrate(width=200, height=150, stock=VellumStock.STANDARD,
                                 profile=profile, seed=0)
        assert img.width == 200
        assert img.height == 150

    def test_standard_stock_warmer_than_irregular(self, profile):
        """Standard stock (warm cream) must have a higher mean red channel than irregular."""
        from weather.substrate.vellum import generate_substrate, VellumStock
        std_img = generate_substrate(width=128, height=128, stock=VellumStock.STANDARD,
                                     profile=profile, seed=42)
        irr_img = generate_substrate(width=128, height=128, stock=VellumStock.IRREGULAR,
                                     profile=profile, seed=42)
        std_r = np.array(std_img.convert("RGB"))[:, :, 0].mean()
        irr_r = np.array(irr_img.convert("RGB"))[:, :, 0].mean()
        assert std_r >= irr_r, (
            f"Standard stock red mean ({std_r:.1f}) should be >= irregular ({irr_r:.1f})"
        )

    def test_standard_and_irregular_are_visually_distinct(self, profile):
        from weather.substrate.vellum import generate_substrate, VellumStock
        std_img = generate_substrate(width=128, height=128, stock=VellumStock.STANDARD,
                                     profile=profile, seed=42)
        irr_img = generate_substrate(width=128, height=128, stock=VellumStock.IRREGULAR,
                                     profile=profile, seed=42)
        std_arr = np.array(std_img.convert("RGB"), dtype=float)
        irr_arr = np.array(irr_img.convert("RGB"), dtype=float)
        mean_diff = np.abs(std_arr - irr_arr).mean()
        assert mean_diff > 1.0, (
            f"Standard and irregular substrates too similar (mean diff={mean_diff:.2f})"
        )

    def test_same_seed_is_deterministic(self, profile):
        from weather.substrate.vellum import generate_substrate, VellumStock
        img_a = generate_substrate(width=64, height=64, stock=VellumStock.STANDARD,
                                   profile=profile, seed=1457)
        img_b = generate_substrate(width=64, height=64, stock=VellumStock.STANDARD,
                                   profile=profile, seed=1457)
        np.testing.assert_array_equal(
            np.array(img_a), np.array(img_b),
            err_msg="generate_substrate not deterministic with same seed"
        )

    def test_image_is_rgb(self, profile):
        from weather.substrate.vellum import generate_substrate, VellumStock
        img = generate_substrate(width=64, height=64, stock=VellumStock.STANDARD,
                                 profile=profile, seed=0)
        assert img.mode in ("RGB", "RGBA")


# ---------------------------------------------------------------------------
# TestBleedThrough
# ---------------------------------------------------------------------------

class TestBleedThrough:
    def test_bleedthrough_returns_pil_image(self, profile):
        from weather.substrate.vellum import apply_bleedthrough
        base = Image.new("RGB", (64, 64), (242, 228, 196))
        verso = Image.new("RGB", (64, 64), (18, 12, 8))
        result = apply_bleedthrough(base, verso, opacity=0.06)
        assert isinstance(result, Image.Image)

    def test_bleedthrough_modifies_base(self, profile):
        """Bleed-through at opacity > 0 must change pixel values."""
        from weather.substrate.vellum import apply_bleedthrough
        base = Image.new("RGB", (64, 64), (242, 228, 196))
        verso = Image.new("RGB", (64, 64), (0, 0, 0))   # solid black verso
        result = apply_bleedthrough(base, verso, opacity=0.06)
        base_arr = np.array(base, dtype=float)
        result_arr = np.array(result, dtype=float)
        assert not np.allclose(base_arr, result_arr), (
            "Bleed-through at opacity=0.06 produced no change"
        )

    def test_zero_opacity_bleedthrough_unchanged(self, profile):
        from weather.substrate.vellum import apply_bleedthrough
        base = Image.new("RGB", (64, 64), (242, 228, 196))
        verso = Image.new("RGB", (64, 64), (0, 0, 0))
        result = apply_bleedthrough(base, verso, opacity=0.0)
        np.testing.assert_array_equal(np.array(base), np.array(result))
