"""Tests for weather/aivalidation.py — ADV-WX-AIVALIDATE-001."""

from __future__ import annotations

import json
import numpy as np
import pytest

from weather.promptgen import FolioWeatherSpec, WaterDamageSpec, WordDamageEntry
from weather.aivalidation import (
    ValidationResult,
    ValidationSummary,
    validate_text_positions,
    validate_pre_degradation_preserved,
    validate_damage_consistency,
    validate_folio,
)


# ---------------------------------------------------------------------------
# Image fixtures
# ---------------------------------------------------------------------------

_H, _W = 100, 100


def _parchment(ink_region: tuple[int, int, int, int] | None = None) -> np.ndarray:
    """Light cream image with optional dark ink block."""
    img = np.full((_H, _W, 3), 230, dtype=np.uint8)
    if ink_region:
        t, b, l, r = ink_region
        img[t:b, l:r] = 20
    return img


def _shift_image(img: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """Shift image by (dx, dy), filling gaps with 230."""
    result = np.full_like(img, 230)
    if dx >= 0:
        result[:, dx:] = img[:, : _W - dx]
    else:
        result[:, :_W + dx] = img[:, -dx:]
    return result


def _spec(water: bool = False) -> FolioWeatherSpec:
    s = FolioWeatherSpec(
        folio_id="f04r",
        vellum_stock="standard",
        edge_darkening=0.7,
        gutter_side="left",
    )
    if water:
        s.water_damage = WaterDamageSpec(severity=1.0, origin="top_right", penetration=0.4)
    return s


def _spec_no_water() -> FolioWeatherSpec:
    return FolioWeatherSpec(
        folio_id="f01r",
        vellum_stock="standard",
        edge_darkening=0.65,
        gutter_side="left",
    )


# ---------------------------------------------------------------------------
# V1: validate_text_positions
# ---------------------------------------------------------------------------

def test_v1_zero_drift_passes():
    img = _parchment(ink_region=(30, 50, 20, 60))
    bboxes = [(20, 30, 60, 50)]  # (left, top, right, bottom)
    result = validate_text_positions(img, img.copy(), bboxes)
    assert result.passed is True
    assert result.value == pytest.approx(0.0, abs=1.0)


def test_v1_shifted_10px_fails():
    img = _parchment(ink_region=(30, 50, 20, 60))
    shifted = _shift_image(img, dx=20, dy=0)  # 20px shift → centroid moves >5px
    bboxes = [(20, 30, 60, 50)]
    result = validate_text_positions(img, shifted, bboxes)
    assert result.passed is False
    assert result.value > 5.0


def test_v1_no_bboxes_passes_vacuously():
    img = _parchment()
    result = validate_text_positions(img, img.copy(), bbox_list=[])
    assert result.passed is True


# ---------------------------------------------------------------------------
# V2-A: validate_pre_degradation_preserved
# ---------------------------------------------------------------------------

def _lacuna_entry() -> WordDamageEntry:
    return WordDamageEntry(
        word_text="[lacuna]",
        bbox=(20, 30, 60, 50),
        center=(40.0, 40.0),
        confidence=0.0,
        category="lacuna",
        line_number=2,
    )


def _trace_entry() -> WordDamageEntry:
    return WordDamageEntry(
        word_text="stolz",
        bbox=(20, 30, 60, 50),
        center=(40.0, 40.0),
        confidence=0.4,
        category="trace",
        line_number=2,
    )


def test_v2a_lacuna_preserved_passes():
    """AI kept lacuna region blank (matching pre-degraded) → pass."""
    pre_deg = _parchment()  # blank parchment in that region
    weathered = _parchment()  # AI also left it blank
    mask = np.zeros((_H, _W), dtype=np.uint8)
    mask[30:50, 20:60] = 255
    result = validate_pre_degradation_preserved(pre_deg, weathered, mask, [_lacuna_entry()])
    assert result.passed is True


def test_v2a_lacuna_restored_fails():
    """AI added dark ink into a lacuna region → fail."""
    pre_deg = _parchment()  # blank in lacuna region
    weathered = _parchment(ink_region=(30, 50, 20, 60))  # AI darkened it
    mask = np.zeros((_H, _W), dtype=np.uint8)
    mask[30:50, 20:60] = 255
    result = validate_pre_degradation_preserved(pre_deg, weathered, mask, [_lacuna_entry()])
    assert result.passed is False


def test_v2a_trace_not_brightened_passes():
    """AI left faded trace at same level → pass."""
    # Pre-degraded: region faded to ~150
    pre_deg = np.full((_H, _W, 3), 230, dtype=np.uint8)
    pre_deg[30:50, 20:60] = 150
    weathered = pre_deg.copy()  # identical — no brightening
    mask = np.zeros((_H, _W), dtype=np.uint8)
    mask[30:50, 20:60] = 200
    result = validate_pre_degradation_preserved(pre_deg, weathered, mask, [_trace_entry()])
    assert result.passed is True


def test_v2a_empty_damage_map_passes():
    img = _parchment()
    mask = np.zeros((_H, _W), dtype=np.uint8)
    result = validate_pre_degradation_preserved(img, img, mask, [])
    assert result.passed is True


# ---------------------------------------------------------------------------
# V3: validate_damage_consistency
# ---------------------------------------------------------------------------

def _stained_image(stain_region: tuple[int, int, int, int]) -> np.ndarray:
    """Image with a dark stain in the given region (top, bot, left, right)."""
    img = np.full((_H, _W, 3), 230, dtype=np.uint8)
    t, b, l, r = stain_region
    img[t:b, l:r] = 60  # dark stain
    return img


def test_v3_matching_stains_passes():
    """Recto and verso with matching water stain zones → IoU >= 0.5, passed."""
    # Stain in top-right quadrant of recto
    recto = _stained_image((0, 40, 50, 100))
    # Verso is horizontally mirrored — stain in top-left → after mirroring overlaps recto's top-right
    verso = _stained_image((0, 40, 0, 50))

    recto_spec = FolioWeatherSpec(
        folio_id="f04r", vellum_stock="standard", edge_darkening=0.7, gutter_side="left",
        water_damage=WaterDamageSpec(severity=1.0, origin="top_right", penetration=0.4),
    )
    verso_spec = FolioWeatherSpec(
        folio_id="f04v", vellum_stock="standard", edge_darkening=0.7, gutter_side="right",
        water_damage=WaterDamageSpec(severity=0.85, origin="top_left", penetration=0.4),
    )
    result = validate_damage_consistency(recto, verso, recto_spec, verso_spec)
    assert result.passed is True
    assert result.value >= 0.5


def test_v3_non_overlapping_stains_fails():
    """Recto stain top-right, verso stain bottom-left → IoU near 0 → failed."""
    recto = _stained_image((0, 30, 70, 100))   # top-right
    verso = _stained_image((70, 100, 0, 30))   # bottom-left

    recto_spec = FolioWeatherSpec(
        folio_id="f04r", vellum_stock="standard", edge_darkening=0.7, gutter_side="left",
        water_damage=WaterDamageSpec(severity=1.0, origin="top_right", penetration=0.4),
    )
    verso_spec = FolioWeatherSpec(
        folio_id="f04v", vellum_stock="standard", edge_darkening=0.7, gutter_side="right",
        water_damage=WaterDamageSpec(severity=0.85, origin="top_left", penetration=0.4),
    )
    result = validate_damage_consistency(recto, verso, recto_spec, verso_spec)
    assert result.passed is False
    assert len(result.issues) > 0


def test_v3_no_water_damage_passes_vacuously():
    """Neither folio has water damage → V3 not applicable → passed=True."""
    img = _parchment()
    result = validate_damage_consistency(img, img, _spec_no_water(), _spec_no_water())
    assert result.passed is True


# ---------------------------------------------------------------------------
# validate_folio
# ---------------------------------------------------------------------------

def test_validate_folio_returns_summary():
    img = _parchment()
    summary = validate_folio(
        folio_id="f01r",
        clean_image=img,
        weathered_image=img.copy(),
        pre_degraded_image=img.copy(),
        degradation_mask=np.zeros((_H, _W), dtype=np.uint8),
        word_damage_map=[],
        recto_spec=_spec_no_water(),
        verso_image=None,
        verso_spec=None,
        bbox_list=[],
    )
    assert isinstance(summary, ValidationSummary)
    assert summary.folio_id == "f01r"
    assert summary.v1_text_positions is not None
    assert summary.v2a_pre_degradation is not None
    assert summary.v3_damage_consistency is not None


def test_validate_folio_clean_copy_all_passed():
    """Weathered = clean copy, no damage entries, no water damage → all checks pass."""
    img = _parchment()
    summary = validate_folio(
        folio_id="f01r",
        clean_image=img,
        weathered_image=img.copy(),
        pre_degraded_image=img.copy(),
        degradation_mask=np.zeros((_H, _W), dtype=np.uint8),
        word_damage_map=[],
        recto_spec=_spec_no_water(),
        verso_image=None,
        verso_spec=None,
        bbox_list=[],
    )
    assert summary.all_passed is True


def test_validate_folio_serializes_to_dict():
    img = _parchment()
    summary = validate_folio(
        folio_id="f01r",
        clean_image=img,
        weathered_image=img.copy(),
        pre_degraded_image=img.copy(),
        degradation_mask=np.zeros((_H, _W), dtype=np.uint8),
        word_damage_map=[],
        recto_spec=_spec_no_water(),
        verso_image=None,
        verso_spec=None,
        bbox_list=[],
    )
    d = summary.to_dict()
    assert d["folio_id"] == "f01r"
    assert "all_passed" in d
    assert "v1_text_positions" in d
    assert "v2a_pre_degradation" in d
    assert "v3_damage_consistency" in d
    # Should round-trip through JSON
    json.dumps(d)
