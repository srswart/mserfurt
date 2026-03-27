"""Tests for TD-014 reviewed evofit guide freeze."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from scribesim.pathguide import freeze_reviewed_evofit_guides, guide_from_waypoints, load_pathguides_toml, write_pathguides_toml


def _write_reviewed_evofit_fixture(tmp_path: Path) -> Path:
    reviewed_manifest_path = tmp_path / "reviewed_exemplar_manifest.toml"
    reviewed_manifest_path.write_text(
        """
schema_version = 1
manifest_kind = "reviewed_exemplars"
dataset_id = "reviewed-fixture"
required_symbols = ["e"]
priority_joins = ["d->e"]
"""
    )

    raw_glyph = tmp_path / "raw_e.png"
    raw_glyph.write_bytes(b"raw-glyph")
    cleaned_glyph = tmp_path / "cleaned_e.png"
    cleaned_glyph.write_bytes(b"cleaned-glyph")
    raw_join = tmp_path / "raw_d_to_e.png"
    raw_join.write_bytes(b"raw-join")

    guides = {
        "e": guide_from_waypoints(
            "e",
            [(0.0, 0.2, True), (0.5, 0.6, True), (1.0, 0.3, True)],
            x_height_mm=3.5,
            x_advance_xh=1.05,
            kind="glyph",
            source_id="evofit:e",
            source_path=cleaned_glyph.as_posix(),
            confidence_tier="soft_accepted",
            split="validation",
        ),
        "d->e": guide_from_waypoints(
            "d->e",
            [(0.0, 0.5, True), (0.6, 0.55, True), (1.2, 0.45, True)],
            x_height_mm=3.5,
            x_advance_xh=1.3,
            kind="join",
            source_id="evofit:d->e",
            source_path=raw_join.as_posix(),
            confidence_tier="soft_accepted",
            split="validation",
        ),
    }
    proposal_catalog_path = tmp_path / "proposal_guides.toml"
    write_pathguides_toml(guides, proposal_catalog_path)

    summary_json_path = tmp_path / "summary.json"
    summary_json_path.write_text(
        json.dumps(
            {
                "fit_sources": [
                    {
                        "kind": "glyph",
                        "symbol": "e",
                        "selected_source_path": cleaned_glyph.as_posix(),
                        "selected_source_raw_path": raw_glyph.as_posix(),
                        "selected_source_cleaned_path": cleaned_glyph.as_posix(),
                        "selected_source_variant": "cleaned",
                        "selected_source_cleanup_stroke_count": 3,
                        "selected_source_manuscript": "MS A",
                        "selected_source_quality_tier": "trusted",
                        "selected_source_object_id": "msa001",
                        "best_fitness": 0.83,
                        "nominal_ncc": 0.45,
                        "evofit_ncc": 0.71,
                        "beats_prior_nominal": True,
                        "structurally_convertible": True,
                    },
                    {
                        "kind": "join",
                        "symbol": "d->e",
                        "selected_source_path": raw_join.as_posix(),
                        "selected_source_raw_path": raw_join.as_posix(),
                        "selected_source_cleaned_path": "",
                        "selected_source_variant": "raw",
                        "selected_source_cleanup_stroke_count": 0,
                        "selected_source_manuscript": "MS A",
                        "selected_source_quality_tier": "usable",
                        "selected_source_object_id": "msa001",
                        "best_fitness": 0.79,
                        "nominal_ncc": 0.42,
                        "evofit_ncc": 0.68,
                        "beats_prior_nominal": True,
                        "structurally_convertible": True,
                    },
                ]
            },
            indent=2,
        )
        + "\n"
    )

    evofit_manifest_path = tmp_path / "manifest.toml"
    evofit_manifest_path.write_text(
        f"""
schema_version = 1
corpus_manifest_path = "{reviewed_manifest_path.as_posix()}"
proposal_catalog_path = "{proposal_catalog_path.as_posix()}"
summary_json_path = "{summary_json_path.as_posix()}"
summary_md_path = "{(tmp_path / "summary.md").as_posix()}"
"""
    )
    return evofit_manifest_path


def test_freeze_reviewed_evofit_guides_writes_promoted_catalog_and_reports(tmp_path: Path):
    evofit_manifest_path = _write_reviewed_evofit_fixture(tmp_path)
    output_root = tmp_path / "reviewed_promoted_guides_v1"
    guide_catalog_path = tmp_path / "reviewed_promoted_v1.toml"

    result = freeze_reviewed_evofit_guides(
        evofit_manifest_path,
        output_root=output_root,
        guide_catalog_path=guide_catalog_path,
    )

    promoted_guides = load_pathguides_toml(result["guide_catalog_path"])
    assert set(promoted_guides) == {"e", "d->e"}
    assert all(guide.accepted_only for guide in promoted_guides.values())
    assert {source.source_id for source in promoted_guides["e"].sources} == {
        "reviewed-raw:e",
        "reviewed-cleaned:e",
    }
    assert {source.confidence_tier for source in promoted_guides["d->e"].sources} == {"accepted"}
    assert result["overlay_panel_path"].exists()
    assert result["nominal_panel_path"].exists()
    assert result["validation_report_md_path"].exists()
    assert result["coverage_provenance_report_md_path"].exists()
    assert result["summary"]["exact_symbol_coverage"] == 1.0
    assert result["summary"]["validation_gate_passed"] is True

    validation = json.loads(result["validation_report_json_path"].read_text(encoding="utf-8"))
    assert validation["metrics"]["required_symbol_coverage"] == 1.0
    assert validation["metrics"]["accepted_source_ratio"] == 1.0

    manifest = tomllib.loads(result["manifest_path"].read_text(encoding="utf-8"))
    assert manifest["manifest_kind"] == "reviewed_promoted_guides"
    assert manifest["guide_catalog_path"] == guide_catalog_path.as_posix()
    assert len(manifest["symbols"]) == 2


def test_freeze_reviewed_evofit_guides_requires_convertible_guides(tmp_path: Path):
    evofit_manifest_path = _write_reviewed_evofit_fixture(tmp_path)
    payload = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    for item in payload["fit_sources"]:
        item["structurally_convertible"] = False
    (tmp_path / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    try:
        freeze_reviewed_evofit_guides(evofit_manifest_path, output_root=tmp_path / "out", guide_catalog_path=tmp_path / "cat.toml")
    except ValueError as exc:
        assert "no structurally convertible" in str(exc)
    else:
        raise AssertionError("expected reviewed evofit guide freeze to fail without convertible guides")
