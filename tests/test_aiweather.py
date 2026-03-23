"""Tests for weather/aiweather.py — ADV-WX-AIWEATHER-001."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from weather.promptgen import FolioWeatherSpec, WaterDamageSpec, WordDamageEntry
from weather.aiweather import (
    WeatheredResult,
    _compute_seed,
    generate_gathering_order,
    weather_folio,
    weather_codex,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_weathering_map() -> dict[str, FolioWeatherSpec]:
    """Minimal 34-folio weathering map (17 leaves × 2 sides)."""
    specs = {}
    for n in range(1, 18):
        for s in ("r", "v"):
            fid = f"f{n:02d}{s}"
            specs[fid] = FolioWeatherSpec(
                folio_id=fid,
                vellum_stock="standard",
                edge_darkening=0.65,
                gutter_side="left" if s == "r" else "right",
            )
    specs["f04r"].water_damage = WaterDamageSpec(severity=1.0, origin="top_right", penetration=0.6)
    specs["f04v"].water_damage = WaterDamageSpec(severity=0.85, origin="top_left", penetration=0.51)
    return specs


def _make_image(seed: int = 0) -> np.ndarray:
    """Tiny reproducible test image (80×60 RGB)."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, (60, 80, 3), dtype=np.uint8)


_WMAP = _make_weathering_map()


# ---------------------------------------------------------------------------
# generate_gathering_order
# ---------------------------------------------------------------------------

def test_gathering_order_starts_with_f04r():
    order = generate_gathering_order(_WMAP)
    assert order[0] == "f04r"


def test_gathering_order_f04v_second():
    order = generate_gathering_order(_WMAP)
    assert order[1] == "f04v"


def test_gathering_order_contains_all_34():
    order = generate_gathering_order(_WMAP)
    assert len(order) == 34
    assert len(set(order)) == 34


def test_gathering_order_f01r_before_f08r():
    order = generate_gathering_order(_WMAP)
    assert order.index("f01r") < order.index("f08r")


def test_gathering_order_subset_map():
    """Only folios in the map are returned."""
    small_map = {k: v for k, v in _WMAP.items() if k in ("f04r", "f04v", "f03r")}
    order = generate_gathering_order(small_map)
    assert set(order) == {"f04r", "f04v", "f03r"}
    assert order[0] == "f04r"


# ---------------------------------------------------------------------------
# _compute_seed
# ---------------------------------------------------------------------------

def test_compute_seed_deterministic():
    assert _compute_seed("f04r", 42) == _compute_seed("f04r", 42)


def test_compute_seed_differs_by_folio():
    assert _compute_seed("f04r", 42) != _compute_seed("f04v", 42)


def test_compute_seed_within_uint32():
    s = _compute_seed("f17v", 9999)
    assert 0 <= s < 2 ** 32


# ---------------------------------------------------------------------------
# weather_folio — dry_run
# ---------------------------------------------------------------------------

def test_weather_folio_dry_run_returns_weighted_result(tmp_path):
    img = _make_image()
    result = weather_folio(
        folio_id="f04r",
        clean_image=img,
        folio_spec=_WMAP["f04r"],
        word_damage_map=[],
        weathering_map=_WMAP,
        weathered_so_far={},
        output_dir=tmp_path,
        dry_run=True,
    )
    assert isinstance(result, WeatheredResult)
    assert result.folio_id == "f04r"
    assert result.image.dtype == np.uint8
    assert result.image.shape == img.shape


def test_weather_folio_dry_run_image_equals_pre_degraded(tmp_path):
    """With no word_damage_map entries, pre-degraded == clean; dry_run copies it."""
    img = _make_image(seed=7)
    result = weather_folio(
        folio_id="f01r",
        clean_image=img,
        folio_spec=_WMAP["f01r"],
        word_damage_map=[],
        weathering_map=_WMAP,
        weathered_so_far={},
        output_dir=tmp_path,
        dry_run=True,
    )
    np.testing.assert_array_equal(result.image, img)


def test_weather_folio_dry_run_writes_prompt_file(tmp_path):
    img = _make_image()
    weather_folio(
        folio_id="f04r",
        clean_image=img,
        folio_spec=_WMAP["f04r"],
        word_damage_map=[],
        weathering_map=_WMAP,
        weathered_so_far={},
        output_dir=tmp_path,
        dry_run=True,
    )
    prompt_file = tmp_path / "f04r_prompt.txt"
    assert prompt_file.exists()
    assert len(prompt_file.read_text()) > 50


def test_weather_folio_dry_run_writes_provenance(tmp_path):
    img = _make_image()
    result = weather_folio(
        folio_id="f04r",
        clean_image=img,
        folio_spec=_WMAP["f04r"],
        word_damage_map=[],
        weathering_map=_WMAP,
        weathered_so_far={},
        output_dir=tmp_path,
        dry_run=True,
    )
    assert result.provenance_path.exists()
    data = json.loads(result.provenance_path.read_text())
    assert data["method"] == "dry_run"


def test_provenance_contains_required_fields(tmp_path):
    img = _make_image()
    result = weather_folio(
        folio_id="f04r",
        clean_image=img,
        folio_spec=_WMAP["f04r"],
        word_damage_map=[],
        weathering_map=_WMAP,
        weathered_so_far={},
        output_dir=tmp_path,
        dry_run=True,
    )
    data = json.loads(result.provenance_path.read_text())
    for field in ("folio_id", "method", "model", "prompt", "seed",
                  "weathering_spec", "coherence_references", "timestamp"):
        assert field in data, f"Missing field: {field}"


def test_provenance_folio_id_matches(tmp_path):
    img = _make_image()
    result = weather_folio(
        folio_id="f04r",
        clean_image=img,
        folio_spec=_WMAP["f04r"],
        word_damage_map=[],
        weathering_map=_WMAP,
        weathered_so_far={},
        output_dir=tmp_path,
        dry_run=True,
    )
    data = json.loads(result.provenance_path.read_text())
    assert data["folio_id"] == "f04r"


# ---------------------------------------------------------------------------
# weather_folio — coherence context propagation
# ---------------------------------------------------------------------------

def test_weather_folio_f04v_coherence_includes_f04r(tmp_path):
    """After f04r is weathered, f04v gets f04r as a reference."""
    f04r_img = _make_image(seed=1)
    f04v_img = _make_image(seed=2)

    # Simulate f04r already weathered
    weathered_so_far = {"f04r": f04r_img}

    result = weather_folio(
        folio_id="f04v",
        clean_image=f04v_img,
        folio_spec=_WMAP["f04v"],
        word_damage_map=[],
        weathering_map=_WMAP,
        weathered_so_far=weathered_so_far,
        output_dir=tmp_path,
        dry_run=True,
    )
    data = json.loads(result.provenance_path.read_text())
    assert "f04r" in data["coherence_references"]


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

def test_retry_succeeds_after_two_failures(tmp_path):
    """weather_folio in live mode retries on transient errors."""
    img = _make_image()
    call_count = {"n": 0}

    def flaky_apply(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise RuntimeError("transient error")
        return img.copy()

    with patch("weather.aiweather._openai_apply_weathering", side_effect=flaky_apply), \
         patch("weather.aiweather.time.sleep"):  # don't actually sleep
        result = weather_folio(
            folio_id="f04r",
            clean_image=img,
            folio_spec=_WMAP["f04r"],
            word_damage_map=[],
            weathering_map=_WMAP,
            weathered_so_far={},
            output_dir=tmp_path,
            dry_run=False,
        )
    assert call_count["n"] == 3
    data = json.loads(result.provenance_path.read_text())
    assert "error" not in data


def test_retry_raises_after_max_attempts(tmp_path):
    """After 3 failures, the exception propagates."""
    img = _make_image()

    with patch("weather.aiweather._openai_apply_weathering",
               side_effect=RuntimeError("always fails")), \
         patch("weather.aiweather.time.sleep"):
        with pytest.raises(RuntimeError, match="always fails"):
            weather_folio(
                folio_id="f04r",
                clean_image=img,
                folio_spec=_WMAP["f04r"],
                word_damage_map=[],
                weathering_map=_WMAP,
                weathered_so_far={},
                output_dir=tmp_path,
                dry_run=False,
            )


# ---------------------------------------------------------------------------
# weather_codex — integration (dry_run)
# ---------------------------------------------------------------------------

def _mini_map() -> dict[str, FolioWeatherSpec]:
    """4-folio map for fast integration tests."""
    fids = ["f04r", "f04v", "f03r", "f05r"]
    return {
        fid: FolioWeatherSpec(
            folio_id=fid,
            vellum_stock="standard",
            edge_darkening=0.6,
            gutter_side="left" if fid.endswith("r") else "right",
        )
        for fid in fids
    }


def test_weather_codex_dry_run_mini(tmp_path):
    mini = _mini_map()
    clean_images = {fid: _make_image(i) for i, fid in enumerate(mini)}
    results = weather_codex(
        clean_images=clean_images,
        weathering_map=mini,
        word_damage_maps={},
        output_dir=tmp_path,
        dry_run=True,
    )
    assert set(results.keys()) == set(mini.keys())


def test_weather_codex_writes_provenance_for_each(tmp_path):
    mini = _mini_map()
    clean_images = {fid: _make_image(i) for i, fid in enumerate(mini)}
    results = weather_codex(
        clean_images=clean_images,
        weathering_map=mini,
        word_damage_maps={},
        output_dir=tmp_path,
        dry_run=True,
    )
    for fid in mini:
        assert (tmp_path / f"{fid}_provenance.json").exists()


def test_weather_codex_f04r_before_f04v(tmp_path):
    """f04r provenance must be written before f04v (gathering order)."""
    mini = _mini_map()
    clean_images = {fid: _make_image(i) for i, fid in enumerate(mini)}
    weather_codex(
        clean_images=clean_images,
        weathering_map=mini,
        word_damage_maps={},
        output_dir=tmp_path,
        dry_run=True,
    )
    f04r_mtime = (tmp_path / "f04r_provenance.json").stat().st_mtime
    f04v_mtime = (tmp_path / "f04v_provenance.json").stat().st_mtime
    assert f04r_mtime <= f04v_mtime


@pytest.mark.slow
def test_weather_codex_all_34_folios_dry_run(tmp_path):
    """Full 34-folio dry_run completes without error."""
    wmap = _make_weathering_map()
    clean_images = {fid: _make_image(i) for i, fid in enumerate(wmap)}
    results = weather_codex(
        clean_images=clean_images,
        weathering_map=wmap,
        word_damage_maps={},
        output_dir=tmp_path,
        dry_run=True,
    )
    assert len(results) == 34
    for fid in wmap:
        assert (tmp_path / f"{fid}_provenance.json").exists()
