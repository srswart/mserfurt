"""Unit tests for A3-A7 analysis criteria and composite scoring — ADV-SS-REFSELECT-003."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Synthetic image helpers
# ---------------------------------------------------------------------------

def _blank(h=200, w=200) -> np.ndarray:
    return np.full((h, w), 255, dtype=np.uint8)


def _uniform_strips(h=200, w=200, n_strips=6, strip_h=8, density=0.5) -> np.ndarray:
    """Horizontal strips with uniform ink density (checkerboard pattern within strip)."""
    img = np.full((h, w), 255, dtype=np.uint8)
    spacing = h // (n_strips + 1)
    for i in range(1, n_strips + 1):
        row = i * spacing
        r0, r1 = max(0, row - strip_h // 2), row + strip_h // 2
        # Fill fraction of each strip column as ink
        n_ink_cols = int(w * density)
        img[r0:r1, :n_ink_cols] = 0
    return img


def _text_block_image(h=300, w=300, ink_ratio=0.25) -> np.ndarray:
    """Image with a centred rectangular text block at given ink ratio (scattered)."""
    img = np.full((h, w), 255, dtype=np.uint8)
    # Text block: middle 60% of image
    r0, r1 = h // 5, 4 * h // 5
    c0, c1 = w // 5, 4 * w // 5
    block_h, block_w = r1 - r0, c1 - c0
    n_ink = int(block_h * block_w * ink_ratio)
    rng = np.random.default_rng(42)
    indices = rng.choice(block_h * block_w, n_ink, replace=False)
    flat = np.full(block_h * block_w, 255, dtype=np.uint8)
    flat[indices] = 0
    img[r0:r1, c0:c1] = flat.reshape(block_h, block_w)
    return img


def _stained_image(h=200, w=200) -> np.ndarray:
    """Image with a large dark blotch in the background (simulated stain)."""
    img = np.full((h, w), 220, dtype=np.uint8)
    # Large low-frequency dark region (stain)
    img[50:150, 50:150] = 80
    # Some ink lines
    for row in [30, 60, 90, 120, 150]:
        img[row:row+4, :] = 10
    return img


def _clean_lined_image(h=200, w=200) -> np.ndarray:
    """Clean image: bright background with regular ink strips, no stain."""
    img = np.full((h, w), 240, dtype=np.uint8)
    for row in [30, 60, 90, 120, 150, 180]:
        img[row:row+5, :] = 10
    return img


def _thick_thin_strokes(h=200, w=100) -> np.ndarray:
    """Image with both thick (wide) and thin strokes — good thick/thin contrast."""
    img = np.full((h, w), 255, dtype=np.uint8)
    # Thick stroke: 12px wide
    img[20:80, 20:32] = 0
    # Thin stroke: 2px wide
    img[20:80, 50:52] = 0
    # Medium stroke: 6px wide
    img[100:160, 30:36] = 0
    # Another thin stroke
    img[100:160, 70:72] = 0
    return img


def _uniform_thin_strokes(h=200, w=100) -> np.ndarray:
    """Image with only uniform thin strokes — poor thick/thin contrast."""
    img = np.full((h, w), 255, dtype=np.uint8)
    for c in range(10, 90, 10):
        img[20:180, c:c+2] = 0
    return img


def _many_blobs(h=300, w=300, n=20, blob_size=12) -> np.ndarray:
    """Image with many similar-size rectangular blobs (simulated letters)."""
    img = np.full((h, w), 255, dtype=np.uint8)
    rng = np.random.default_rng(42)
    placed = 0
    for _ in range(n * 3):
        r = int(rng.integers(10, h - blob_size - 10))
        c = int(rng.integers(10, w - blob_size - 10))
        h_var = int(rng.integers(blob_size - 3, blob_size + 3))
        w_var = int(rng.integers(blob_size - 3, blob_size + 3))
        img[r:r+h_var, c:c+w_var] = 0
        placed += 1
        if placed >= n:
            break
    return img


def _make_jpeg(arr: np.ndarray, path: Path) -> Path:
    Image.fromarray(arr).convert("RGB").save(path, format="JPEG")
    return path


# ---------------------------------------------------------------------------
# A3: script consistency
# ---------------------------------------------------------------------------

class TestScriptConsistency:
    def test_uniform_strips_score(self):
        from scribesim.refselect.analysis import analyze_script_consistency
        score = analyze_script_consistency(_uniform_strips())
        assert score >= 0.6

    def test_range(self):
        from scribesim.refselect.analysis import analyze_script_consistency
        for img in [_uniform_strips(), _blank(), _many_blobs()]:
            assert 0.0 <= analyze_script_consistency(img) <= 1.0


# ---------------------------------------------------------------------------
# A4: text density
# ---------------------------------------------------------------------------

class TestTextDensity:
    def test_good_density_score(self):
        from scribesim.refselect.analysis import analyze_text_density
        score = analyze_text_density(_text_block_image(ink_ratio=0.25))
        assert score >= 0.5

    def test_empty_image_score(self):
        from scribesim.refselect.analysis import analyze_text_density
        score = analyze_text_density(_blank())
        assert score <= 0.2

    def test_range(self):
        from scribesim.refselect.analysis import analyze_text_density
        for img in [_text_block_image(), _blank(), _uniform_strips()]:
            assert 0.0 <= analyze_text_density(img) <= 1.0


# ---------------------------------------------------------------------------
# A5: damage
# ---------------------------------------------------------------------------

class TestDamage:
    def test_clean_image_score(self):
        from scribesim.refselect.analysis import analyze_damage
        score = analyze_damage(_clean_lined_image())
        assert score >= 0.6

    def test_stained_image_score(self):
        from scribesim.refselect.analysis import analyze_damage
        score = analyze_damage(_stained_image())
        assert score <= 0.5

    def test_range(self):
        from scribesim.refselect.analysis import analyze_damage
        for img in [_clean_lined_image(), _stained_image(), _blank()]:
            assert 0.0 <= analyze_damage(img) <= 1.0


# ---------------------------------------------------------------------------
# A6: thick/thin
# ---------------------------------------------------------------------------

class TestThickThin:
    def test_good_variation_score(self):
        from scribesim.refselect.analysis import analyze_thick_thin
        score = analyze_thick_thin(_thick_thin_strokes())
        assert score >= 0.5

    def test_uniform_thin_score(self):
        """2px strokes have no interior pixels (EDT ≤ 1.5 everywhere) → must return 0.0."""
        from scribesim.refselect.analysis import analyze_thick_thin
        score = analyze_thick_thin(_uniform_thin_strokes())
        assert score == 0.0

    def test_blank_image(self):
        from scribesim.refselect.analysis import analyze_thick_thin
        assert analyze_thick_thin(_blank()) == 0.0

    def test_range(self):
        from scribesim.refselect.analysis import analyze_thick_thin
        for img in [_thick_thin_strokes(), _uniform_thin_strokes(), _blank()]:
            assert 0.0 <= analyze_thick_thin(img) <= 1.0

    def test_real_crop_bsb_95r(self):
        """Real BSB 95r letter crop should score in Bastarda range [0.3, 0.9]."""
        from scribesim.refselect.analysis import analyze_thick_thin
        from PIL import Image
        fixture = Path(__file__).parent / "fixtures" / "bsb_95r_d_sample.png"
        img = np.array(Image.open(fixture).convert("L"))
        score = analyze_thick_thin(img)
        assert 0.3 <= score <= 0.9, f"Real Bastarda crop scored {score:.3f}, expected [0.3, 0.9]"


# ---------------------------------------------------------------------------
# A7: letter variety
# ---------------------------------------------------------------------------

class TestLetterVariety:
    def test_many_blobs_score(self):
        from scribesim.refselect.analysis import analyze_letter_variety
        score = analyze_letter_variety(_many_blobs(n=20))
        assert score >= 0.4

    def test_blank_image(self):
        from scribesim.refselect.analysis import analyze_letter_variety
        assert analyze_letter_variety(_blank()) == 0.0

    def test_range(self):
        from scribesim.refselect.analysis import analyze_letter_variety
        for img in [_many_blobs(), _blank(), _uniform_strips()]:
            assert 0.0 <= analyze_letter_variety(img) <= 1.0


# ---------------------------------------------------------------------------
# composite_suitability
# ---------------------------------------------------------------------------

class TestCompositeSuitability:
    def test_full_scores_range(self):
        from scribesim.refselect.analysis import composite_suitability
        scores = {
            "ink_contrast": 0.8, "line_regularity": 0.7,
            "script_consistency": 0.6, "text_density": 0.5,
            "damage": 0.9, "thick_thin": 0.7, "letter_variety": 0.6,
        }
        c = composite_suitability(scores)
        assert 0.0 <= c <= 1.0

    def test_partial_criteria_renormalises(self):
        from scribesim.refselect.analysis import composite_suitability
        # Only A1+A2 — should still return a valid score
        scores = {"ink_contrast": 1.0, "line_regularity": 1.0}
        c = composite_suitability(scores)
        assert c == pytest.approx(1.0, abs=0.01)

    def test_all_zero_returns_zero(self):
        from scribesim.refselect.analysis import composite_suitability
        scores = {
            "ink_contrast": 0.0, "line_regularity": 0.0,
            "script_consistency": 0.0, "text_density": 0.0,
            "damage": 0.0, "thick_thin": 0.0, "letter_variety": 0.0,
        }
        assert composite_suitability(scores) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# analyze_folio — all 7 criteria
# ---------------------------------------------------------------------------

class TestAnalyzeFolloFull:
    _EXPECTED_KEYS = {
        "ink_contrast", "line_regularity", "script_consistency",
        "text_density", "damage", "thick_thin", "letter_variety", "composite",
    }

    def test_has_all_criteria(self, tmp_path):
        from scribesim.refselect.analysis import analyze_folio
        p = _make_jpeg(_uniform_strips(), tmp_path / "test.jpg")
        result = analyze_folio(p)
        assert self._EXPECTED_KEYS == set(result.keys())

    def test_composite_in_range(self, tmp_path):
        from scribesim.refselect.analysis import analyze_folio
        p = _make_jpeg(_uniform_strips(), tmp_path / "test.jpg")
        result = analyze_folio(p)
        assert 0.0 <= result["composite"] <= 1.0


# ---------------------------------------------------------------------------
# rank_candidates — rejection reason
# ---------------------------------------------------------------------------

class TestRankWithReasons:
    def _make_record_with_candidate(self, composite, weakest_key, weakest_val):
        from scribesim.refselect.provenance import new_provenance_record, add_candidate
        manifest = {
            "manifest_url": "https://x", "title": "T",
            "attribution": "", "license": "", "canvases": [],
        }
        sampling = {"strategy": "stratified", "n_candidates": 5,
                    "page_range": "all", "random_seed": 42}
        rec = new_provenance_record(manifest, sampling)
        scores = {
            "ink_contrast": 0.8, "line_regularity": 0.8,
            "script_consistency": 0.8, "text_density": 0.8,
            "damage": 0.8, "thick_thin": 0.8, "letter_variety": 0.8,
            "composite": composite,
        }
        scores[weakest_key] = weakest_val
        add_candidate(rec, {"id": "c1", "label": "1r", "image_url": ""}, Path("x.jpg"), scores)
        return rec

    def test_rejected_candidate_has_rejection_reason(self):
        from scribesim.refselect.provenance import rank_candidates
        rec = self._make_record_with_candidate(0.3, "damage", 0.1)
        rank_candidates(rec, selection_threshold=0.75)
        entry = rec["provenance"]["candidates"][0]
        assert entry["selected"] is False
        assert "rejection_reason" in entry
        assert entry["rejection_reason"] is not None

    def test_selected_candidate_has_selection_reason(self):
        from scribesim.refselect.provenance import rank_candidates
        rec = self._make_record_with_candidate(0.85, "damage", 0.9)
        rank_candidates(rec, selection_threshold=0.75)
        entry = rec["provenance"]["candidates"][0]
        assert entry["selected"] is True
        assert "selection_reason" in entry
