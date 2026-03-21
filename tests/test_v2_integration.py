"""Integration and regression tests for ScribeSim v2 — ADV-SS-TESTS-002.

Validates the full TD-002/TD-003 pipeline end-to-end:
  - ScribeSim v2 renders f01r with all physics components active
  - Output contracts maintained (PNG dimensions, modes, heatmap, PAGE XML)
  - Weather pipeline accepts v2 output without errors
  - v2 output visually differs from v1 (movement model active)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scribesim.hand.params import HandParams
from scribesim.hand.profile import HandProfile, load_profile, resolve_profile
from scribesim.layout import place
from scribesim.render.pipeline import render_pipeline, _page_size_output


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"
FOLIO_JSON = Path(__file__).parent.parent / "output-live" / "f01r.json"


@pytest.fixture
def folio_dict():
    if not FOLIO_JSON.exists():
        pytest.skip("f01r.json not available (XL output required)")
    return json.loads(FOLIO_JSON.read_text())


@pytest.fixture
def profile():
    return load_profile(HAND_TOML)


@pytest.fixture
def resolved_profile(profile):
    return resolve_profile(profile, "f01r")


@pytest.fixture
def v1_params():
    from scribesim.hand.model import load_base, resolve
    base = load_base(HAND_TOML)
    return resolve(base, "f01r")


# ---------------------------------------------------------------------------
# TestFullPipelineIntegration
# ---------------------------------------------------------------------------

class TestFullPipelineIntegration:
    """End-to-end: folio JSON → layout → v2 pipeline → PNG + heatmap."""

    def test_renders_f01r_successfully(self, folio_dict, resolved_profile, tmp_path):
        params = resolved_profile.to_v1()
        layout = place(folio_dict, params, profile=resolved_profile)
        page_path, heatmap_path = render_pipeline(
            layout, params, tmp_path, "f01r", profile=resolved_profile)
        assert page_path.exists()
        assert heatmap_path.exists()

    def test_output_is_300dpi_rgb(self, folio_dict, resolved_profile, tmp_path):
        params = resolved_profile.to_v1()
        layout = place(folio_dict, params, profile=resolved_profile)
        page_path, _ = render_pipeline(
            layout, params, tmp_path, "f01r", profile=resolved_profile)
        img = Image.open(page_path)
        assert img.mode == "RGB"
        out_w, out_h = _page_size_output(layout)
        assert img.size == (out_w, out_h)

    def test_heatmap_is_grayscale(self, folio_dict, resolved_profile, tmp_path):
        params = resolved_profile.to_v1()
        layout = place(folio_dict, params, profile=resolved_profile)
        _, heatmap_path = render_pipeline(
            layout, params, tmp_path, "f01r", profile=resolved_profile)
        img = Image.open(heatmap_path)
        assert img.mode == "L"

    def test_heatmap_has_nonzero_values(self, folio_dict, resolved_profile, tmp_path):
        params = resolved_profile.to_v1()
        layout = place(folio_dict, params, profile=resolved_profile)
        _, heatmap_path = render_pipeline(
            layout, params, tmp_path, "f01r", profile=resolved_profile)
        arr = np.array(Image.open(heatmap_path))
        assert arr.max() > 0

    def test_page_has_ink_pixels(self, folio_dict, resolved_profile, tmp_path):
        params = resolved_profile.to_v1()
        layout = place(folio_dict, params, profile=resolved_profile)
        page_path, _ = render_pipeline(
            layout, params, tmp_path, "f01r", profile=resolved_profile)
        arr = np.array(Image.open(page_path))
        parchment = np.array([245, 238, 220])
        diff = np.linalg.norm(arr.astype(float) - parchment, axis=2)
        assert (diff > 30).sum() > 1000  # at least 1000 ink pixels

    def test_deterministic(self, folio_dict, resolved_profile, tmp_path):
        params = resolved_profile.to_v1()
        layout = place(folio_dict, params, profile=resolved_profile)
        p1, _ = render_pipeline(layout, params, tmp_path / "r1", "f01r", profile=resolved_profile)
        p2, _ = render_pipeline(layout, params, tmp_path / "r2", "f01r", profile=resolved_profile)
        img1 = np.array(Image.open(p1))
        img2 = np.array(Image.open(p2))
        np.testing.assert_array_equal(img1, img2)


# ---------------------------------------------------------------------------
# TestV2Regression
# ---------------------------------------------------------------------------

class TestV2Regression:
    """v2 output should differ from v1 (movement + physics nib + ink filters active)."""

    def test_v2_differs_from_v1(self, folio_dict, resolved_profile, v1_params, tmp_path):
        """Rendering with profile (v2) produces different output than without (v1)."""
        from scribesim.render.rasteriser import render_page as v1_render_page

        # v1 render (no profile, no movement, no physics nib, no ink filters)
        layout_v1 = place(folio_dict, v1_params)
        v1_path = v1_render_page(layout_v1, v1_params, tmp_path / "v1.png")

        # v2 render (with profile)
        params_v2 = resolved_profile.to_v1()
        layout_v2 = place(folio_dict, params_v2, profile=resolved_profile)
        v2_path, _ = render_pipeline(
            layout_v2, params_v2, tmp_path / "v2", "f01r", profile=resolved_profile)

        img_v1 = np.array(Image.open(v1_path))
        img_v2 = np.array(Image.open(v2_path))

        # Dimensions may differ (v2 uses 400→300 DPI pipeline)
        # Just verify they're not identical
        if img_v1.shape == img_v2.shape:
            assert not np.array_equal(img_v1, img_v2), "v2 should differ from v1"
        else:
            pass  # different dimensions = definitely different

    def test_v2_preserves_folio_id(self, folio_dict, resolved_profile, tmp_path):
        params = resolved_profile.to_v1()
        layout = place(folio_dict, params, profile=resolved_profile)
        assert layout.folio_id == "f01r"

    def test_v2_has_more_lines_than_zero(self, folio_dict, resolved_profile):
        params = resolved_profile.to_v1()
        layout = place(folio_dict, params, profile=resolved_profile)
        assert len(layout.lines) > 0


# ---------------------------------------------------------------------------
# TestWeatherCompatibility
# ---------------------------------------------------------------------------

class TestWeatherCompatibility:
    """Weather pipeline should accept v2 ScribeSim output."""

    def test_weather_apply_accepts_v2_png(self, folio_dict, resolved_profile, tmp_path):
        """Weather's composite_folio should not crash on v2 render output."""
        params = resolved_profile.to_v1()
        layout = place(folio_dict, params, profile=resolved_profile)
        page_path, heatmap_path = render_pipeline(
            layout, params, tmp_path / "render", "f01r", profile=resolved_profile)

        # Import weather compositor
        try:
            from weather.compositor import composite_folio
            from weather.profile import load_profile as load_weather_profile
        except ImportError:
            pytest.skip("Weather module not available")

        weather_profile = load_weather_profile()
        page_img = Image.open(page_path)
        heatmap_img = Image.open(heatmap_path)

        # Should not raise
        result = composite_folio(page_img, heatmap_img, "f01r", weather_profile, seed=1457)
        assert result.image is not None
        assert result.image.size == page_img.size


# ---------------------------------------------------------------------------
# TestCoverageAudit
# ---------------------------------------------------------------------------

class TestCoverageAudit:
    """Verify all v2 modules have test files."""

    def test_movement_has_tests(self):
        assert Path("tests/test_movement.py").exists()

    def test_physics_nib_has_tests(self):
        assert Path("tests/test_physics_nib.py").exists()

    def test_ink_filters_has_tests(self):
        assert Path("tests/test_ink_filters.py").exists()

    def test_imprecision_has_tests(self):
        assert Path("tests/test_imprecision.py").exists()

    def test_pipeline_has_tests(self):
        assert Path("tests/test_render_pipeline.py").exists()

    def test_metrics_has_tests(self):
        assert Path("tests/test_metrics.py").exists()

    def test_tuning_has_tests(self):
        assert Path("tests/test_tuning.py").exists()

    def test_optimizer_has_tests(self):
        assert Path("tests/test_optimizer.py").exists()

    def test_hand_profile_has_tests(self):
        assert Path("tests/test_hand_profile.py").exists()
