"""Tests for the TD-014 exemplar harvest wrapper."""

from __future__ import annotations

import json
from pathlib import Path
import tomllib
from unittest.mock import patch

from click.testing import CliRunner

from scribesim.cli import main
from scribesim.refselect.harvest import (
    build_mdz_manifest_url,
    extract_mdz_object_id,
    load_exemplar_harvest_manifest,
    run_exemplar_harvest,
)


def _normalized_manifest(label: str, manifest_url: str, n_pages: int = 6) -> dict:
    return {
        "manifest_url": manifest_url,
        "title": label,
        "label": label,
        "attribution": "Bayerische Staatsbibliothek",
        "license": "Public Domain",
        "canvases": [
            {
                "id": f"{manifest_url}/canvas/{index}",
                "label": f"{index}r",
                "image_url": f"https://example.com/{label}_{index}.jpg",
                "service_url": f"https://example.com/iiif/{label}_{index}",
            }
            for index in range(1, n_pages + 1)
        ],
    }


def test_extract_mdz_object_id_from_details_url():
    assert extract_mdz_object_id("https://www.digitale-sammlungen.de/en/details/bsb00144295") == "bsb00144295"


def test_load_exemplar_harvest_manifest_resolves_details_urls(tmp_path):
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(
        """
schema_version = 1
harvest_id = "demo-harvest"
output_dir = "shared/training/handsim/demo_harvest"
target_script_family = "German Bastarda"
min_folios = 4
max_folios = 4
default_strategy = "stratified"
default_seed = 17

[[manuscripts]]
label = "Cgm 628"
details_url = "https://www.digitale-sammlungen.de/en/details/bsb00144295"
n_candidates = 4
"""
    )

    config = load_exemplar_harvest_manifest(manifest_path)

    assert config["harvest_id"] == "demo-harvest"
    assert config["requested_total"] == 4
    spec = config["manuscripts"][0]
    assert spec["object_id"] == "bsb00144295"
    assert spec["manifest_url"] == build_mdz_manifest_url("bsb00144295")
    assert spec["strategy"] == "stratified"
    assert spec["seed"] == 17


def test_run_exemplar_harvest_writes_bundle(tmp_path):
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(
        """
schema_version = 1
harvest_id = "demo-harvest"
description = "Fixture harvest"
output_dir = "ignored/by/test"
target_script_family = "German Bastarda"
target_date_range = "c. 1450-1470"
min_folios = 4
max_folios = 4
default_strategy = "stratified"
default_seed = 9

[[manuscripts]]
label = "BSB Cgm 628"
manifest_url = "https://example.com/m1"
n_candidates = 2

[[manuscripts]]
label = "BSB Cgm 1112"
manifest_url = "https://example.com/m2"
n_candidates = 2
"""
    )
    output_root = tmp_path / "out"
    manifests = [
        _normalized_manifest("BSB Cgm 628", "https://example.com/m1"),
        _normalized_manifest("BSB Cgm 1112", "https://example.com/m2"),
    ]

    def _download(canvas: dict, output_dir: Path, resolution: str = "analysis", timeout: int = 60) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{canvas['label']}.jpg"
        path.write_bytes(b"jpg")
        return path

    with patch("scribesim.refselect.harvest.fetch_all_manifests", return_value=manifests), patch(
        "scribesim.refselect.harvest.download_folio", side_effect=_download
    ):
        result = run_exemplar_harvest(manifest_path, output_dir=output_root)

    provenance = json.loads(result["provenance_path"].read_text())
    inventory = json.loads(result["sample_inventory_path"].read_text())
    selection = tomllib.loads(result["selection_manifest_path"].read_text())
    review = result["review_summary_path"].read_text()

    assert result["provenance_path"].exists()
    assert result["sample_inventory_path"].exists()
    assert result["selection_manifest_path"].exists()
    assert result["review_summary_path"].exists()
    assert inventory["selected_folio_count"] == 4
    assert inventory["downloaded_folio_count"] == 4
    assert inventory["range_gate"]["passed"] is True
    assert inventory["local_asset_gate"]["passed"] is True
    assert len(provenance["provenance"]["candidates"]) == 4
    assert selection["selected_folio_count"] == 4
    assert len(selection["folios"]) == 4
    assert "BSB Cgm 628" in review
    assert "BSB Cgm 1112" in review


def test_harvest_exemplars_cli_invokes_command(tmp_path):
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(
        """
schema_version = 1
harvest_id = "cli-demo"
output_dir = "shared/training/handsim/cli_demo"
target_script_family = "German Bastarda"
min_folios = 4
max_folios = 4

[[manuscripts]]
label = "BSB Cgm 628"
manifest_url = "https://example.com/m1"
n_candidates = 4
"""
    )
    out_dir = tmp_path / "cli-out"
    runner = CliRunner()
    fake_result = {
        "inventory": {
            "harvest_id": "cli-demo",
            "selected_folio_count": 4,
            "downloaded_folio_count": 4,
            "download_resolution": "analysis",
            "manuscripts": [{"label": "BSB Cgm 628"}],
        },
        "provenance_path": out_dir / "provenance.json",
        "selection_manifest_path": out_dir / "selection_manifest.toml",
        "review_summary_path": out_dir / "review_summary.md",
    }

    with patch("scribesim.refselect.run_exemplar_harvest", return_value=fake_result):
        result = runner.invoke(main, ["harvest-exemplars", str(manifest_path), "--output-dir", str(out_dir)])

    assert result.exit_code == 0
    assert "Harvest: cli-demo" in result.output
    assert "Selected 4 folios" in result.output


def test_committed_exemplar_harvest_manifest_is_in_target_range():
    manifest_path = Path("shared/training/handsim/exemplar_harvest_v1/manifest.toml")
    manifest = tomllib.loads(manifest_path.read_text())

    requested_total = sum(entry["n_candidates"] for entry in manifest["manuscripts"])
    assert manifest["harvest_id"] == "td014-exemplar-harvest-v1"
    assert manifest["target_script_family"] == "German Bastarda"
    assert manifest["min_folios"] == 30
    assert manifest["max_folios"] == 40
    assert 30 <= requested_total <= 40
    assert all("digitale-sammlungen.de" in entry["details_url"] for entry in manifest["manuscripts"])
