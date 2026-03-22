"""Unit tests for scribesim/refselect/analysis.py — ADV-SS-REFSELECT-002."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Synthetic image helpers
# ---------------------------------------------------------------------------

def _high_contrast_image(h=200, w=200) -> np.ndarray:
    """Half black (0), half white (255) — very bimodal histogram."""
    img = np.zeros((h, w), dtype=np.uint8)
    img[:, w // 2:] = 255
    return img


def _low_contrast_image(h=200, w=200) -> np.ndarray:
    """Uniform mid-grey — unimodal histogram, no clear ink/paper separation."""
    return np.full((h, w), 128, dtype=np.uint8)


def _regular_lines_image(h=200, w=200, n_lines=6, strip_height=8) -> np.ndarray:
    """Evenly-spaced horizontal black strips on white background."""
    img = np.full((h, w), 255, dtype=np.uint8)
    spacing = h // (n_lines + 1)
    for i in range(1, n_lines + 1):
        row = i * spacing
        img[max(0, row - strip_height // 2): row + strip_height // 2, :] = 0
    return img


def _irregular_lines_image(h=200, w=200, n_lines=6, strip_height=8) -> np.ndarray:
    """Black strips with random inter-line gaps."""
    rng = np.random.default_rng(7)
    img = np.full((h, w), 255, dtype=np.uint8)
    rows = sorted(rng.integers(strip_height, h - strip_height, n_lines))
    for row in rows:
        img[max(0, row - strip_height // 2): row + strip_height // 2, :] = 0
    return img


def _make_jpeg(img_array: np.ndarray, path: Path) -> Path:
    Image.fromarray(img_array).convert("RGB").save(path, format="JPEG")
    return path


# ---------------------------------------------------------------------------
# Tests: analyze_ink_contrast
# ---------------------------------------------------------------------------

class TestAnalyzeInkContrast:
    def test_high_contrast_score(self):
        from scribesim.refselect.analysis import analyze_ink_contrast
        score = analyze_ink_contrast(_high_contrast_image())
        assert score >= 0.7

    def test_low_contrast_score(self):
        from scribesim.refselect.analysis import analyze_ink_contrast
        score = analyze_ink_contrast(_low_contrast_image())
        assert score <= 0.3

    def test_score_in_range(self):
        from scribesim.refselect.analysis import analyze_ink_contrast
        for img in [_high_contrast_image(), _low_contrast_image()]:
            score = analyze_ink_contrast(img)
            assert 0.0 <= score <= 1.0

    def test_high_beats_low(self):
        from scribesim.refselect.analysis import analyze_ink_contrast
        assert analyze_ink_contrast(_high_contrast_image()) > analyze_ink_contrast(_low_contrast_image())


# ---------------------------------------------------------------------------
# Tests: analyze_line_regularity
# ---------------------------------------------------------------------------

class TestAnalyzeLineRegularity:
    def test_regular_lines_score(self):
        from scribesim.refselect.analysis import analyze_line_regularity
        score = analyze_line_regularity(_regular_lines_image())
        assert score >= 0.7

    def test_irregular_lines_score(self):
        from scribesim.refselect.analysis import analyze_line_regularity
        score = analyze_line_regularity(_irregular_lines_image())
        assert score <= 0.75  # irregular should score lower than regular

    def test_score_in_range(self):
        from scribesim.refselect.analysis import analyze_line_regularity
        for img in [_regular_lines_image(), _irregular_lines_image(), _low_contrast_image()]:
            score = analyze_line_regularity(img)
            assert 0.0 <= score <= 1.0

    def test_regular_beats_irregular(self):
        from scribesim.refselect.analysis import analyze_line_regularity
        assert analyze_line_regularity(_regular_lines_image()) > analyze_line_regularity(_irregular_lines_image())


# ---------------------------------------------------------------------------
# Tests: analyze_folio
# ---------------------------------------------------------------------------

class TestAnalyzeFolio:
    def test_returns_required_keys(self, tmp_path):
        from scribesim.refselect.analysis import analyze_folio
        p = _make_jpeg(_high_contrast_image(), tmp_path / "test.jpg")
        result = analyze_folio(p)
        assert "ink_contrast" in result
        assert "line_regularity" in result
        assert "composite" in result

    def test_composite_in_range(self, tmp_path):
        from scribesim.refselect.analysis import analyze_folio
        p = _make_jpeg(_high_contrast_image(), tmp_path / "test.jpg")
        result = analyze_folio(p)
        assert 0.0 <= result["composite"] <= 1.0

    def test_accepts_path_object(self, tmp_path):
        from scribesim.refselect.analysis import analyze_folio
        p = _make_jpeg(_regular_lines_image(), tmp_path / "lines.jpg")
        result = analyze_folio(Path(p))
        assert isinstance(result["composite"], float)

    def test_high_contrast_image_has_decent_composite(self, tmp_path):
        from scribesim.refselect.analysis import analyze_folio
        p = _make_jpeg(_high_contrast_image(), tmp_path / "hi.jpg")
        result = analyze_folio(p)
        assert result["composite"] >= 0.3
