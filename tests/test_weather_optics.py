"""Unit tests for Weather optics effects — ADV-WX-OPTICS-001.

RED phase: weather.optics modules are not yet implemented.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

PROFILE_TOML = Path(__file__).parent.parent / "shared" / "profiles" / "ms-erfurt-560yr.toml"

_PAGE_W, _PAGE_H = 200, 280


def _grey_page(w=_PAGE_W, h=_PAGE_H, value=180) -> Image.Image:
    return Image.fromarray(
        np.full((h, w, 3), value, dtype=np.uint8), mode="RGB"
    )


@pytest.fixture(scope="module")
def profile():
    from weather.profile import load_profile
    return load_profile(PROFILE_TOML)


@pytest.fixture(scope="module")
def profile_curl_on(profile, tmp_path_factory):
    """Profile with page_curl enabled."""
    import copy
    p = copy.deepcopy(profile)
    p.optics_curl.enabled = True
    return p


# ---------------------------------------------------------------------------
# TestProfileOpticsParams
# ---------------------------------------------------------------------------

class TestProfileOpticsParams:
    def test_optics_curl_loaded(self, profile):
        from weather.profile import PageCurlParams
        assert isinstance(profile.optics_curl, PageCurlParams)

    def test_optics_vignette_loaded(self, profile):
        from weather.profile import CameraVignetteParams
        assert isinstance(profile.optics_vignette, CameraVignetteParams)
        assert profile.optics_vignette.strength > 0

    def test_optics_lighting_loaded(self, profile):
        from weather.profile import LightingGradientParams
        assert isinstance(profile.optics_lighting, LightingGradientParams)
        assert profile.optics_lighting.strength > 0


# ---------------------------------------------------------------------------
# TestCameraVignette
# ---------------------------------------------------------------------------

class TestCameraVignette:
    def test_returns_same_size(self, profile):
        from weather.optics.vignette import apply_vignette
        page = _grey_page()
        result = apply_vignette(page, profile)
        assert result.size == page.size

    def test_corners_darker_than_center(self, profile):
        from weather.optics.vignette import apply_vignette
        page = _grey_page()
        result = apply_vignette(page, profile)
        arr = np.array(result)
        corner = int(arr[0, 0, 0])
        centre = int(arr[_PAGE_H // 2, _PAGE_W // 2, 0])
        assert corner < centre, f"Corner ({corner}) should be darker than centre ({centre})"

    def test_radial_symmetry(self, profile):
        """Top-left and top-right corners should have similar darkening."""
        from weather.optics.vignette import apply_vignette
        page = _grey_page()
        result = apply_vignette(page, profile)
        arr = np.array(result)
        tl = int(arr[0, 0, 0])
        tr = int(arr[0, -1, 0])
        assert abs(tl - tr) <= 2, f"TL ({tl}) and TR ({tr}) should be similar (radial symmetry)"

    def test_no_clipping_to_zero(self, profile):
        """Vignette should darken but not clip pixels to pure black at corners."""
        from weather.optics.vignette import apply_vignette
        page = _grey_page(value=180)
        result = apply_vignette(page, profile)
        arr = np.array(result)
        assert arr.min() > 0, "Vignette should not clip to zero"

    def test_disabled_passthrough(self, profile):
        from weather.optics.vignette import apply_vignette
        import copy
        p = copy.deepcopy(profile)
        p.optics_vignette.enabled = False
        page = _grey_page()
        result = apply_vignette(page, p)
        assert np.array_equal(np.array(result), np.array(page))


# ---------------------------------------------------------------------------
# TestLightingGradient
# ---------------------------------------------------------------------------

class TestLightingGradient:
    def test_returns_same_size(self, profile):
        from weather.optics.lighting import apply_lighting_gradient
        page = _grey_page()
        result = apply_lighting_gradient(page, profile)
        assert result.size == page.size

    def test_top_left_brighter_than_bottom_right(self, profile):
        """Profile direction='top_left' — top-left should be brighter."""
        from weather.optics.lighting import apply_lighting_gradient
        page = _grey_page()
        result = apply_lighting_gradient(page, profile)
        arr = np.array(result)
        tl = int(arr[2, 2, 0])
        br = int(arr[-3, -3, 0])
        assert tl > br, f"Top-left ({tl}) should be brighter than bottom-right ({br})"

    def test_output_values_in_valid_range(self, profile):
        from weather.optics.lighting import apply_lighting_gradient
        page = _grey_page(value=180)
        result = apply_lighting_gradient(page, profile)
        arr = np.array(result)
        assert arr.min() >= 0
        assert arr.max() <= 255

    def test_disabled_passthrough(self, profile):
        from weather.optics.lighting import apply_lighting_gradient
        import copy
        p = copy.deepcopy(profile)
        p.optics_lighting.enabled = False
        page = _grey_page()
        result = apply_lighting_gradient(page, p)
        assert np.array_equal(np.array(result), np.array(page))


# ---------------------------------------------------------------------------
# TestPageCurl
# ---------------------------------------------------------------------------

class TestPageCurl:
    def test_disabled_returns_unchanged_image(self, profile):
        from weather.optics.curl import apply_page_curl
        page = _grey_page()
        result = apply_page_curl(page, "f01r", profile, seed=0)
        assert result.curl_transform is None
        assert np.array_equal(np.array(result.image), np.array(page))

    def test_enabled_returns_transform(self, profile):
        from weather.optics.curl import apply_page_curl
        import copy
        p = copy.deepcopy(profile)
        p.optics_curl.enabled = True
        page = _grey_page()
        result = apply_page_curl(page, "f01r", p, seed=0)
        assert result.curl_transform is not None
        assert result.curl_transform.shape == (_PAGE_H, _PAGE_W, 2)

    def test_enabled_warps_image(self, profile):
        """Curl-enabled output should differ from input (warp changes pixels)."""
        from weather.optics.curl import apply_page_curl
        import copy
        p = copy.deepcopy(profile)
        p.optics_curl.enabled = True
        # Use a non-uniform page so warp is detectable
        arr = np.zeros((_PAGE_H, _PAGE_W, 3), dtype=np.uint8)
        arr[:, _PAGE_W // 2:, :] = 200  # right half bright
        page = Image.fromarray(arr, mode="RGB")
        result = apply_page_curl(page, "f01r", p, seed=0)
        assert not np.array_equal(np.array(result.image), arr)

    def test_result_same_size(self, profile):
        from weather.optics.curl import apply_page_curl
        import copy
        p = copy.deepcopy(profile)
        p.optics_curl.enabled = True
        page = _grey_page()
        result = apply_page_curl(page, "f01r", p, seed=0)
        assert result.image.size == page.size


# ---------------------------------------------------------------------------
# TestApplyOptics (orchestrator)
# ---------------------------------------------------------------------------

class TestApplyOptics:
    def test_returns_optics_result(self, profile):
        from weather.optics import apply_optics, OpticsResult
        page = _grey_page()
        result = apply_optics(page, "f01r", profile, seed=0)
        assert isinstance(result, OpticsResult)

    def test_result_image_same_size(self, profile):
        from weather.optics import apply_optics
        page = _grey_page()
        result = apply_optics(page, "f01r", profile, seed=0)
        assert result.image.size == page.size

    def test_curl_disabled_no_transform(self, profile):
        from weather.optics import apply_optics
        # Default profile has curl disabled
        page = _grey_page()
        result = apply_optics(page, "f01r", profile, seed=0)
        assert result.curl_transform is None

    def test_deterministic(self, profile):
        from weather.optics import apply_optics
        page = _grey_page()
        r1 = np.array(apply_optics(page, "f01r", profile, seed=3).image)
        r2 = np.array(apply_optics(page, "f01r", profile, seed=3).image)
        assert np.array_equal(r1, r2)

    def test_optics_modifies_image(self, profile):
        """Vignette + lighting are enabled — output should differ from input."""
        from weather.optics import apply_optics
        page = _grey_page()
        result = apply_optics(page, "f01r", profile, seed=0)
        assert not np.array_equal(np.array(result.image), np.array(page))
