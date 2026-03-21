"""Unit tests for comparison metrics M1-M9 — ADV-SS-METRICS-001."""

from __future__ import annotations

import numpy as np
import pytest

from scribesim.metrics.suite import (
    MetricResult,
    run_metrics,
    composite_score,
    m1_stroke_width,
    m2_baseline_regularity,
    m3_spacing_rhythm,
    m4_ink_density,
    m5_glyph_consistency,
    m6_ascender_proportion,
    m7_connection_angles,
    m8_frequency_texture,
    m9_perceptual,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BG = np.array([245, 238, 220], dtype=np.uint8)
_INK = np.array([18, 12, 8], dtype=np.uint8)


def _make_page(h: int = 200, w: int = 300) -> np.ndarray:
    """Parchment background with horizontal ink stripes (simulated text lines)."""
    img = np.full((h, w, 3), _BG, dtype=np.uint8)
    for row_start in range(30, h - 20, 25):
        img[row_start:row_start + 8, 20:w - 20, :] = _INK
    return img


def _make_different_page(h: int = 200, w: int = 300) -> np.ndarray:
    """Different layout: thicker lines, different spacing."""
    img = np.full((h, w, 3), _BG, dtype=np.uint8)
    for row_start in range(40, h - 20, 35):
        img[row_start:row_start + 14, 30:w - 30, :] = _INK
    return img


def _make_blank(h: int = 200, w: int = 300) -> np.ndarray:
    """Pure parchment — no ink."""
    return np.full((h, w, 3), _BG, dtype=np.uint8)


# ---------------------------------------------------------------------------
# TestIdenticalImages
# ---------------------------------------------------------------------------

class TestIdenticalImages:
    def test_all_metrics_zero_on_identical(self):
        img = _make_page()
        results = run_metrics(img, img.copy())
        for r in results:
            if r.distance >= 0:  # skip unavailable (M9)
                assert r.distance == pytest.approx(0.0, abs=0.01), \
                    f"{r.id} ({r.name}) should be ~0 for identical images, got {r.distance}"

    def test_composite_zero_on_identical(self):
        img = _make_page()
        results = run_metrics(img, img.copy())
        score = composite_score(results)
        assert score < 0.05


# ---------------------------------------------------------------------------
# TestDifferentImages
# ---------------------------------------------------------------------------

class TestDifferentImages:
    def test_different_images_nonzero(self):
        rendered = _make_page()
        target = _make_different_page()
        results = run_metrics(rendered, target)
        available = [r for r in results if r.distance >= 0]
        nonzero = [r for r in available if r.distance > 0.01]
        # At least some metrics should detect the difference
        assert len(nonzero) >= 3, \
            f"Only {len(nonzero)} metrics detected difference: {[(r.id, r.distance) for r in available]}"

    def test_composite_nonzero(self):
        rendered = _make_page()
        target = _make_different_page()
        results = run_metrics(rendered, target)
        score = composite_score(results)
        assert score > 0.01


# ---------------------------------------------------------------------------
# TestIndividualMetrics
# ---------------------------------------------------------------------------

class TestIndividualMetrics:
    def test_m1_returns_metric_result(self):
        img = _make_page()
        r = m1_stroke_width(img, img)
        assert isinstance(r, MetricResult)
        assert r.id == "M1"

    def test_m2_returns_metric_result(self):
        img = _make_page()
        r = m2_baseline_regularity(img, img)
        assert isinstance(r, MetricResult)
        assert r.id == "M2"

    def test_m3_returns_metric_result(self):
        img = _make_page()
        r = m3_spacing_rhythm(img, img)
        assert isinstance(r, MetricResult)
        assert r.id == "M3"

    def test_m4_returns_metric_result(self):
        img = _make_page()
        r = m4_ink_density(img, img)
        assert isinstance(r, MetricResult)
        assert r.id == "M4"

    def test_m5_returns_metric_result(self):
        img = _make_page()
        r = m5_glyph_consistency(img, img)
        assert isinstance(r, MetricResult)
        assert r.id == "M5"

    def test_m6_returns_metric_result(self):
        img = _make_page()
        r = m6_ascender_proportion(img, img)
        assert isinstance(r, MetricResult)
        assert r.id == "M6"

    def test_m7_returns_metric_result(self):
        img = _make_page()
        r = m7_connection_angles(img, img)
        assert isinstance(r, MetricResult)
        assert r.id == "M7"

    def test_m8_returns_metric_result(self):
        img = _make_page()
        r = m8_frequency_texture(img, img)
        assert isinstance(r, MetricResult)
        assert r.id == "M8"

    def test_m9_returns_metric_result(self):
        img = _make_page()
        r = m9_perceptual(img, img)
        assert isinstance(r, MetricResult)
        assert r.id == "M9"


# ---------------------------------------------------------------------------
# TestRating
# ---------------------------------------------------------------------------

class TestRating:
    def test_good_rating(self):
        assert MetricResult.rate(0.05) == "good"

    def test_okay_rating(self):
        assert MetricResult.rate(0.20) == "okay"

    def test_needs_work_rating(self):
        assert MetricResult.rate(0.50) == "needs_work"

    def test_zero_is_good(self):
        assert MetricResult.rate(0.0) == "good"

    def test_boundary_good_okay(self):
        assert MetricResult.rate(0.15) == "good"
        assert MetricResult.rate(0.16) == "okay"


# ---------------------------------------------------------------------------
# TestCompositeScore
# ---------------------------------------------------------------------------

class TestCompositeScore:
    def test_equal_weights_is_mean(self):
        results = [
            MetricResult("M1", "test", 0.1, "good", ""),
            MetricResult("M2", "test", 0.3, "okay", ""),
        ]
        score = composite_score(results)
        assert score == pytest.approx(0.2)

    def test_custom_weights(self):
        results = [
            MetricResult("M1", "test", 0.1, "good", ""),
            MetricResult("M2", "test", 0.3, "okay", ""),
        ]
        score = composite_score(results, weights={"M1": 3.0, "M2": 1.0})
        expected = (0.1 * 3.0 + 0.3 * 1.0) / 4.0
        assert score == pytest.approx(expected)

    def test_excludes_unavailable(self):
        results = [
            MetricResult("M1", "test", 0.2, "okay", ""),
            MetricResult("M9", "test", -1.0, "unavailable", ""),
        ]
        score = composite_score(results)
        assert score == pytest.approx(0.2)

    def test_all_unavailable_returns_1(self):
        results = [
            MetricResult("M9", "test", -1.0, "unavailable", ""),
        ]
        score = composite_score(results)
        assert score == 1.0


# ---------------------------------------------------------------------------
# TestSuiteRunner
# ---------------------------------------------------------------------------

class TestSuiteRunner:
    def test_run_metrics_returns_9_results(self):
        img = _make_page()
        results = run_metrics(img, img)
        assert len(results) == 10

    def test_run_metrics_all_have_ids(self):
        img = _make_page()
        results = run_metrics(img, img)
        ids = {r.id for r in results}
        assert ids == {"M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10"}

    def test_handles_blank_images(self):
        blank = _make_blank()
        results = run_metrics(blank, blank)
        # Should not crash, all results should be valid
        assert len(results) == 10
        for r in results:
            assert isinstance(r, MetricResult)
