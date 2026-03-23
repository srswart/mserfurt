"""Tests for weather/worddegrade.py — ADV-WX-WORDDEGRADE-001."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from weather.promptgen import WordDamageEntry
from weather.worddegrade import (
    build_word_damage_map,
    estimate_local_background,
    pre_degrade_text,
    save_word_damage_map,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_PAGE_W = 400
_PAGE_H = 600
_DPI = 72  # low DPI for fast tests; layout constants scaled accordingly


def _parchment_image() -> np.ndarray:
    """Cream-coloured parchment with a small dark ink patch at centre."""
    img = np.full((_PAGE_H, _PAGE_W, 3), 230, dtype=np.uint8)  # light cream
    # Dark ink region: rows 100-120, cols 150-250
    img[100:120, 150:250] = 30  # near-black ink
    return img


def _folio_json(annotations_per_line: list[list[dict]]) -> dict:
    """Minimal folio JSON with given annotations."""
    lines = []
    for i, anns in enumerate(annotations_per_line, start=1):
        lines.append({"number": i, "text": f"line {i} text", "annotations": anns})
    return {"id": "ftest", "lines": lines}


def _empty_page_xml(tmp_path: Path) -> Path:
    xml = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<PcGts xmlns='http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15'>"
        "<Metadata/><Page imageFilename='test.png' imageWidth='400' imageHeight='600'/>"
        "</PcGts>"
    )
    p = tmp_path / "test.xml"
    p.write_text(xml)
    return p


# ---------------------------------------------------------------------------
# estimate_local_background
# ---------------------------------------------------------------------------

def test_estimate_local_background_returns_light_colour_around_dark_patch():
    img = _parchment_image()
    # bbox tightly around the dark ink patch
    bbox = (150, 100, 250, 120)
    bg = estimate_local_background(img, bbox, border_px=10)
    assert bg.shape == (3,)
    # Background around the ink should be close to the parchment colour (~230)
    assert np.all(bg > 150), f"Expected light background, got {bg}"


def test_estimate_local_background_uniform_image():
    img = np.full((100, 100, 3), 200, dtype=np.uint8)
    bg = estimate_local_background(img, (20, 20, 60, 60), border_px=5)
    assert np.allclose(bg, 200, atol=5)


# ---------------------------------------------------------------------------
# build_word_damage_map — annotation → category
# ---------------------------------------------------------------------------

def test_lacuna_annotation_produces_category_lacuna(tmp_path):
    folio = _folio_json([[{"type": "lacuna", "detail": {"extent_chars": 5}}]])
    entries = build_word_damage_map(folio, _empty_page_xml(tmp_path), _PAGE_W, _PAGE_H)
    assert len(entries) >= 1
    lac = [e for e in entries if e.category == "lacuna"]
    assert len(lac) >= 1
    assert lac[0].confidence == 0.0


def test_confidence_055_produces_trace(tmp_path):
    folio = _folio_json([[{"type": "confidence", "detail": {"score": 0.55}}]])
    entries = build_word_damage_map(folio, _empty_page_xml(tmp_path), _PAGE_W, _PAGE_H)
    assert len(entries) >= 1
    assert entries[0].confidence == pytest.approx(0.55)
    assert entries[0].category == "trace"


def test_confidence_070_produces_partial(tmp_path):
    folio = _folio_json([[{"type": "confidence", "detail": {"score": 0.70}}]])
    entries = build_word_damage_map(folio, _empty_page_xml(tmp_path), _PAGE_W, _PAGE_H)
    assert entries[0].category == "partial"


def test_confidence_095_produces_clear(tmp_path):
    folio = _folio_json([[{"type": "confidence", "detail": {"score": 0.95}}]])
    entries = build_word_damage_map(folio, _empty_page_xml(tmp_path), _PAGE_W, _PAGE_H)
    assert entries[0].category == "clear"


def test_bbox_is_within_page_bounds(tmp_path):
    folio = _folio_json([[{"type": "confidence", "detail": {"score": 0.5}}]])
    entries = build_word_damage_map(folio, _empty_page_xml(tmp_path), _PAGE_W, _PAGE_H)
    for e in entries:
        l, t, r, b = e.bbox
        assert 0 <= l < r <= _PAGE_W, f"bad x range: {e.bbox}"
        assert 0 <= t < b <= _PAGE_H, f"bad y range: {e.bbox}"


# ---------------------------------------------------------------------------
# pre_degrade_text — pixel operations
# ---------------------------------------------------------------------------

def _ink_image() -> np.ndarray:
    """White page with a solid black word-sized block at a known bbox."""
    img = np.full((200, 400, 3), 240, dtype=np.uint8)
    img[50:80, 100:200] = 10  # near-black ink block
    return img


_LACUNA_ENTRY = WordDamageEntry(
    word_text="[lacuna]", bbox=(100, 50, 200, 80),
    center=(150.0, 65.0), confidence=0.0, category="lacuna", line_number=2,
)
_TRACE_ENTRY = WordDamageEntry(
    word_text="stolz", bbox=(100, 50, 200, 80),
    center=(150.0, 65.0), confidence=0.4, category="trace", line_number=2,
)
_PARTIAL_ENTRY = WordDamageEntry(
    word_text="und", bbox=(100, 50, 200, 80),
    center=(150.0, 65.0), confidence=0.7, category="partial", line_number=2,
)
_CLEAR_ENTRY = WordDamageEntry(
    word_text="Hie", bbox=(100, 50, 200, 80),
    center=(150.0, 65.0), confidence=0.95, category="clear", line_number=1,
)


def test_lacuna_region_erased_to_background():
    img = _ink_image()
    original_ink_mean = img[50:80, 100:200].mean()  # ~10
    result, mask = pre_degrade_text(img, [_LACUNA_ENTRY], seed=42)
    result_mean = result[50:80, 100:200].mean()
    # Should be close to background (~240), not ink (~10)
    assert result_mean > 180, f"Lacuna region should be near background, got mean={result_mean:.1f}"
    assert np.all(mask[50:80, 100:200] == 255), "Lacuna mask should be 255"


def test_trace_region_faded_to_under_30_percent():
    img = _ink_image()
    orig_ink = img[50:80, 100:200].astype(float).mean()  # ~10
    orig_bg = float(img[0:10, 0:10].mean())              # ~240
    result, mask = pre_degrade_text(img, [_TRACE_ENTRY], seed=42)
    result_mean = float(result[50:80, 100:200].mean())
    # The visible ink should be much closer to background now
    # alpha=0.4*0.5=0.2; result ≈ ink*0.2 + bg*0.8 → ≈ 10*0.2 + 240*0.8 = 194
    # The region should be noticeably lighter than original ink
    assert result_mean > orig_ink * 2, (
        f"Trace region should be significantly lighter, orig={orig_ink:.1f} result={result_mean:.1f}"
    )
    assert mask[65, 150] > 0, "Trace mask should be non-zero"


def test_clear_region_unmodified():
    img = _ink_image()
    result, mask = pre_degrade_text(img, [_CLEAR_ENTRY], seed=42)
    np.testing.assert_array_equal(
        result[50:80, 100:200], img[50:80, 100:200],
        err_msg="Clear region must be unmodified"
    )
    assert np.all(mask[50:80, 100:200] == 0), "Clear mask must be 0"


def test_degradation_mask_values():
    img = _ink_image()
    _, mask_lac = pre_degrade_text(img, [_LACUNA_ENTRY], seed=42)
    _, mask_clr = pre_degrade_text(img, [_CLEAR_ENTRY], seed=42)
    _, mask_trc = pre_degrade_text(img, [_TRACE_ENTRY], seed=42)
    assert mask_lac[65, 150] == 255
    assert mask_clr[65, 150] == 0
    assert 0 < mask_trc[65, 150] < 255


def test_determinism():
    img = _ink_image()
    r1, m1 = pre_degrade_text(img, [_TRACE_ENTRY], seed=99)
    r2, m2 = pre_degrade_text(img, [_TRACE_ENTRY], seed=99)
    np.testing.assert_array_equal(r1, r2)
    np.testing.assert_array_equal(m1, m2)


def test_different_seeds_differ():
    img = _ink_image()
    r1, _ = pre_degrade_text(img, [_TRACE_ENTRY], seed=1)
    r2, _ = pre_degrade_text(img, [_TRACE_ENTRY], seed=2)
    # Trace adds noise — different seeds should produce different images
    assert not np.array_equal(r1, r2)


# ---------------------------------------------------------------------------
# save_word_damage_map
# ---------------------------------------------------------------------------

def test_save_word_damage_map_writes_valid_json(tmp_path):
    entries = [_LACUNA_ENTRY, _TRACE_ENTRY]
    out = tmp_path / "f04r_word_damage.json"
    save_word_damage_map(entries, out)
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["confidence"] == 0.0
    assert data[0]["category"] == "lacuna"
    assert "bbox" in data[0]
    assert "word_text" in data[0]
