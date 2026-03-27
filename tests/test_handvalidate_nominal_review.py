"""Tests for TD-014 reviewed nominal validation."""

from __future__ import annotations

import json
from pathlib import Path

from scribesim.handvalidate import run_reviewed_nominal_validation
from scribesim.pathguide import guide_from_waypoints, write_pathguides_toml


def _write_crop(path: Path) -> Path:
    from PIL import Image

    image = Image.new("L", (64, 64), 255)
    for x in range(18, 46):
        for y in range(16, 48):
            image.putpixel((x, y), 0)
    image.save(path)
    return path


def _write_nominal_fixture(tmp_path: Path) -> tuple[Path, Path]:
    reviewed_manifest_path = tmp_path / "reviewed_exemplar_manifest.toml"
    reviewed_manifest_path.write_text(
        """
schema_version = 1
manifest_kind = "reviewed_exemplars"
dataset_id = "reviewed-fixture"
required_symbols = ["u"]
priority_joins = ["u->n"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    raw_u = _write_crop(tmp_path / "u.raw.png")
    cleaned_u = _write_crop(tmp_path / "u.cleaned.png")
    raw_join = _write_crop(tmp_path / "u_to_n.raw.png")
    cleaned_join = _write_crop(tmp_path / "u_to_n.cleaned.png")

    raw_guides = {
        "u": guide_from_waypoints(
            "u",
            [(0.0, 0.6, True), (0.5, 0.2, True), (1.0, 0.6, True)],
            x_height_mm=3.5,
            x_advance_xh=1.0,
            kind="glyph",
            source_id="raw:u",
            source_path=raw_u.as_posix(),
            confidence_tier="soft_accepted",
            split="validation",
            source_resolution_ppmm=16.0,
        ),
        "u->n": guide_from_waypoints(
            "u->n",
            [(0.0, 0.55, True), (0.4, 0.58, True), (0.8, 0.52, True)],
            x_height_mm=3.5,
            x_advance_xh=0.8,
            kind="join",
            source_id="raw:u->n",
            source_path=raw_join.as_posix(),
            confidence_tier="soft_accepted",
            split="validation",
            source_resolution_ppmm=16.0,
        ),
    }
    raw_catalog_path = tmp_path / "raw_proposal_guides.toml"
    write_pathguides_toml(raw_guides, raw_catalog_path)

    promoted_guides = {
        "u": guide_from_waypoints(
            "u",
            [(0.0, 0.6, True), (0.5, 0.2, True), (1.0, 0.6, True)],
            x_height_mm=3.5,
            x_advance_xh=1.0,
            kind="glyph",
            source_id="reviewed-cleaned:u",
            source_path=cleaned_u.as_posix(),
            confidence_tier="accepted",
            split="validation",
            source_resolution_ppmm=16.0,
        ),
        "u->n": guide_from_waypoints(
            "u->n",
            [(0.0, 0.55, True), (0.4, 0.58, True), (0.8, 0.52, True)],
            x_height_mm=3.5,
            x_advance_xh=0.8,
            kind="join",
            source_id="reviewed-cleaned:u->n",
            source_path=cleaned_join.as_posix(),
            confidence_tier="accepted",
            split="test",
            source_resolution_ppmm=16.0,
        ),
    }
    promoted_catalog_path = tmp_path / "reviewed_promoted_v1.toml"
    write_pathguides_toml(promoted_guides, promoted_catalog_path)

    raw_summary_path = tmp_path / "raw_summary.json"
    raw_summary_path.write_text(
        json.dumps(
            {
                "proposal_catalog_path": raw_catalog_path.as_posix(),
                "fit_sources": [
                    {
                        "symbol": "u",
                        "selected_source_path": raw_u.as_posix(),
                        "selected_source_raw_path": raw_u.as_posix(),
                        "selected_source_variant": "raw",
                    },
                    {
                        "symbol": "u->n",
                        "selected_source_path": raw_join.as_posix(),
                        "selected_source_raw_path": raw_join.as_posix(),
                        "selected_source_variant": "raw",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    cleaned_summary_path = tmp_path / "cleaned_summary.json"
    cleaned_summary_path.write_text(
        json.dumps(
            {
                "raw_reviewed_baseline_summary_path": raw_summary_path.as_posix(),
                "fit_sources": [
                    {
                        "symbol": "u",
                        "selected_source_path": cleaned_u.as_posix(),
                        "selected_source_raw_path": raw_u.as_posix(),
                        "selected_source_cleaned_path": cleaned_u.as_posix(),
                        "selected_source_variant": "cleaned",
                    },
                    {
                        "symbol": "u->n",
                        "selected_source_path": cleaned_join.as_posix(),
                        "selected_source_raw_path": raw_join.as_posix(),
                        "selected_source_cleaned_path": cleaned_join.as_posix(),
                        "selected_source_variant": "cleaned",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    reviewed_evofit_manifest_path = tmp_path / "reviewed_evofit_manifest.toml"
    reviewed_evofit_manifest_path.write_text(
        f"""
schema_version = 1
corpus_manifest_path = "{reviewed_manifest_path.as_posix()}"
summary_json_path = "{cleaned_summary_path.as_posix()}"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return reviewed_evofit_manifest_path, promoted_catalog_path


def test_run_reviewed_nominal_validation_writes_dashboard_and_reports(tmp_path: Path):
    evofit_manifest_path, promoted_catalog_path = _write_nominal_fixture(tmp_path)

    result = run_reviewed_nominal_validation(
        evofit_manifest_path,
        promoted_guide_catalog_path=promoted_catalog_path,
        output_root=tmp_path / "out",
    )

    dashboard = json.loads(result["dashboard_json_path"].read_text(encoding="utf-8"))
    assert result["dashboard_md_path"].exists()
    assert result["stage_report_md_path"].exists()
    assert result["raw_nominal_panel_path"].exists()
    assert result["cleaned_nominal_panel_path"].exists()
    assert result["guided_panel_path"].exists()
    assert dashboard["summary_metrics"]["exact_symbol_coverage"] == 1.0
    assert dashboard["summary_metrics"]["cleaned_nominal_mean_score"] >= 0.20
    assert dashboard["summary_metrics"]["guided_mean_score"] >= 0.20
    assert len(dashboard["rows"]) == 2
