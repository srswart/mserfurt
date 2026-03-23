"""Tests for AI weather CLI subcommands — ADV-WX-AICLI-001."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
from click.testing import CliRunner
from PIL import Image as PILImage

from weather.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def _write_tiny_png(path: Path) -> None:
    """Write a 40×30 parchment-coloured PNG for test use."""
    img = PILImage.fromarray(
        np.full((30, 40, 3), 230, dtype=np.uint8), mode="RGB"
    )
    img.save(path)


# ---------------------------------------------------------------------------
# Help — all new commands advertise their flags
# ---------------------------------------------------------------------------

def test_weather_map_help(runner):
    result = runner.invoke(main, ["weather-map", "--help"])
    assert result.exit_code == 0
    assert "--gathering-size" in result.output or "gathering" in result.output.lower()
    assert "--output" in result.output or "--output-dir" in result.output.lower()


def test_weather_folio_help(runner):
    result = runner.invoke(main, ["weather-folio", "--help"])
    assert result.exit_code == 0
    assert "--folio" in result.output
    assert "--dry-run" in result.output


def test_weather_codex_help(runner):
    result = runner.invoke(main, ["weather-codex", "--help"])
    assert result.exit_code == 0
    assert "--dry-run" in result.output


def test_weather_validate_help(runner):
    result = runner.invoke(main, ["weather-validate", "--help"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# weather-map
# ---------------------------------------------------------------------------

def test_weather_map_writes_json(runner, tmp_path):
    out = tmp_path / "codex_map.json"
    result = runner.invoke(main, [
        "weather-map",
        "--gathering-size", "17",
        "--output", str(out),
    ])
    assert result.exit_code == 0, result.output
    assert out.exists()
    data = json.loads(out.read_text())
    assert "f04r" in data
    assert "f01r" in data


def test_weather_map_output_mentions_damage(runner, tmp_path):
    out = tmp_path / "codex_map.json"
    result = runner.invoke(main, [
        "weather-map",
        "--gathering-size", "17",
        "--output", str(out),
    ])
    assert result.exit_code == 0
    # Summary table should mention f04r
    assert "f04r" in result.output


def test_weather_map_contains_34_folios(runner, tmp_path):
    out = tmp_path / "codex_map.json"
    runner.invoke(main, [
        "weather-map", "--gathering-size", "17", "--output", str(out),
    ])
    data = json.loads(out.read_text())
    assert len(data) == 34


# ---------------------------------------------------------------------------
# weather-folio --dry-run
# ---------------------------------------------------------------------------

def test_weather_folio_dry_run_exits_zero(runner, tmp_path):
    # Write a minimal clean image
    clean_png = tmp_path / "f04r.png"
    _write_tiny_png(clean_png)

    # Write a minimal codex map
    from weather.codexmap import compute_codex_weathering_map, save_codex_map
    wmap = compute_codex_weathering_map()
    map_path = tmp_path / "codex_map.json"
    save_codex_map(wmap, map_path)

    out_dir = tmp_path / "weather-out"
    result = runner.invoke(main, [
        "weather-folio",
        "--folio", "f04r",
        "--clean", str(clean_png),
        "--map", str(map_path),
        "--output-dir", str(out_dir),
        "--dry-run",
    ])
    assert result.exit_code == 0, result.output


def test_weather_folio_dry_run_writes_prompt(runner, tmp_path):
    clean_png = tmp_path / "f04r.png"
    _write_tiny_png(clean_png)

    from weather.codexmap import compute_codex_weathering_map, save_codex_map
    map_path = tmp_path / "codex_map.json"
    save_codex_map(compute_codex_weathering_map(), map_path)

    out_dir = tmp_path / "weather-out"
    runner.invoke(main, [
        "weather-folio",
        "--folio", "f04r",
        "--clean", str(clean_png),
        "--map", str(map_path),
        "--output-dir", str(out_dir),
        "--dry-run",
    ])
    assert (out_dir / "f04r_prompt.txt").exists()


def test_weather_folio_invalid_folio_id_exits_nonzero(runner, tmp_path):
    map_path = tmp_path / "codex_map.json"
    map_path.write_text("{}")
    result = runner.invoke(main, [
        "weather-folio",
        "--folio", "not-a-folio",
        "--clean", str(tmp_path / "fake.png"),
        "--map", str(map_path),
        "--output-dir", str(tmp_path),
        "--dry-run",
    ])
    assert result.exit_code != 0
    assert "invalid" in result.output.lower() or "error" in result.output.lower()


def test_weather_folio_prints_prompt_before_api_call(runner, tmp_path):
    clean_png = tmp_path / "f01r.png"
    _write_tiny_png(clean_png)

    from weather.codexmap import compute_codex_weathering_map, save_codex_map
    map_path = tmp_path / "codex_map.json"
    save_codex_map(compute_codex_weathering_map(), map_path)

    out_dir = tmp_path / "weather-out"
    result = runner.invoke(main, [
        "weather-folio",
        "--folio", "f01r",
        "--clean", str(clean_png),
        "--map", str(map_path),
        "--output-dir", str(out_dir),
        "--dry-run",
    ])
    assert result.exit_code == 0
    # Prompt is printed to output
    assert "Apply realistic aging" in result.output or "Do NOT alter" in result.output


# ---------------------------------------------------------------------------
# weather-codex --dry-run
# ---------------------------------------------------------------------------

def test_weather_codex_dry_run_exits_zero(runner, tmp_path):
    # Set up a mini clean-dir with images for 4 folios
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    out_dir = tmp_path / "weather-out"

    from weather.codexmap import compute_codex_weathering_map, save_codex_map
    wmap = compute_codex_weathering_map()
    map_path = tmp_path / "codex_map.json"
    save_codex_map(wmap, map_path)

    # Only provide images for 4 folios; others are skipped
    for fid in ("f04r", "f04v", "f03r", "f05r"):
        _write_tiny_png(clean_dir / f"{fid}.png")

    result = runner.invoke(main, [
        "weather-codex",
        "--clean-dir", str(clean_dir),
        "--map", str(map_path),
        "--output-dir", str(out_dir),
        "--dry-run",
    ])
    assert result.exit_code == 0, result.output


def test_weather_codex_dry_run_writes_provenance(runner, tmp_path):
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    out_dir = tmp_path / "weather-out"

    from weather.codexmap import compute_codex_weathering_map, save_codex_map
    map_path = tmp_path / "codex_map.json"
    save_codex_map(compute_codex_weathering_map(), map_path)

    for fid in ("f04r", "f04v", "f03r"):
        _write_tiny_png(clean_dir / f"{fid}.png")

    runner.invoke(main, [
        "weather-codex",
        "--clean-dir", str(clean_dir),
        "--map", str(map_path),
        "--output-dir", str(out_dir),
        "--dry-run",
    ])
    # Provenance files should exist for each folio that had an image
    for fid in ("f04r", "f04v", "f03r"):
        assert (out_dir / f"{fid}_provenance.json").exists(), f"missing provenance for {fid}"


def test_weather_codex_skips_completed_folios(runner, tmp_path):
    """If provenance already exists, folio is skipped (resumable)."""
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    out_dir = tmp_path / "weather-out"
    out_dir.mkdir()

    from weather.codexmap import compute_codex_weathering_map, save_codex_map
    map_path = tmp_path / "codex_map.json"
    save_codex_map(compute_codex_weathering_map(), map_path)

    _write_tiny_png(clean_dir / "f04r.png")

    # Pre-write provenance to simulate completed run
    existing = {"folio_id": "f04r", "method": "dry_run", "model": "gpt-image-1",
                "prompt": "x", "seed": 0, "weathering_spec": {}, "coherence_references": [],
                "timestamp": "2026-01-01T00:00:00+00:00"}
    (out_dir / "f04r_provenance.json").write_text(json.dumps(existing))

    result = runner.invoke(main, [
        "weather-codex",
        "--clean-dir", str(clean_dir),
        "--map", str(map_path),
        "--output-dir", str(out_dir),
        "--dry-run",
    ])
    assert result.exit_code == 0
    assert "skip" in result.output.lower() or "already" in result.output.lower()


# ---------------------------------------------------------------------------
# weather-validate
# ---------------------------------------------------------------------------

def test_weather_validate_writes_report(runner, tmp_path):
    """Run validate on dry_run output (image = pre-degraded, no drift)."""
    weathered_dir = tmp_path / "weathered"
    weathered_dir.mkdir()
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()

    from weather.codexmap import compute_codex_weathering_map, save_codex_map
    map_path = tmp_path / "codex_map.json"
    wmap = compute_codex_weathering_map()
    save_codex_map(wmap, map_path)

    # Write 2 folio images (identical clean = zero drift)
    for fid in ("f01r", "f01v"):
        _write_tiny_png(clean_dir / f"{fid}.png")
        _write_tiny_png(weathered_dir / f"{fid}_weathered.png")

    report_path = tmp_path / "validation_report.json"
    result = runner.invoke(main, [
        "weather-validate",
        "--weathered-dir", str(weathered_dir),
        "--clean-dir", str(clean_dir),
        "--map", str(map_path),
        "--report", str(report_path),
    ])
    assert result.exit_code == 0, result.output
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert "total_folios" in report


def test_weather_validate_prints_summary_table(runner, tmp_path):
    weathered_dir = tmp_path / "weathered"
    weathered_dir.mkdir()
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()

    from weather.codexmap import compute_codex_weathering_map, save_codex_map
    map_path = tmp_path / "codex_map.json"
    save_codex_map(compute_codex_weathering_map(), map_path)

    _write_tiny_png(clean_dir / "f01r.png")
    _write_tiny_png(weathered_dir / "f01r_weathered.png")

    result = runner.invoke(main, [
        "weather-validate",
        "--weathered-dir", str(weathered_dir),
        "--clean-dir", str(clean_dir),
        "--map", str(map_path),
        "--report", str(tmp_path / "report.json"),
    ])
    assert result.exit_code == 0
    # Table should mention PASS or V1/V2/V3
    assert "PASS" in result.output or "V1" in result.output or "f01r" in result.output
