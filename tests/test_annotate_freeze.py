"""Tests for the TD-014 reviewed exemplar freeze."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from PIL import Image

from scribesim.annotate import freeze_reviewed_exemplars
from scribesim.annotate.workbench import ReviewedAnnotationWorkbench
from scribesim.evofit import build_evofit_targets


def _write_fixture_inputs(tmp_path: Path) -> tuple[Path, Path]:
    image_path = tmp_path / "folio.jpg"
    image = Image.new("RGB", (240, 180), color=(245, 242, 233))
    for x in range(20, 120):
        for y in range(30, 90):
            image.putpixel((x, y), (20, 20, 20))
    for x in range(130, 210):
        for y in range(95, 125):
            image.putpixel((x, y), (80, 40, 20))
    image.save(image_path)

    selection_manifest = tmp_path / "selection_manifest.toml"
    selection_manifest.write_text(
        f"""
schema_version = 1

[[folios]]
rank = 1
canvas_label = "(0029)"
source_manuscript_label = "MS A"
source_object_id = "msa001"
local_path = "{image_path.as_posix()}"
"""
    )

    corpus_manifest = tmp_path / "corpus_manifest.toml"
    corpus_manifest.write_text(
        f"""
schema_version = 1
selection_manifest_path = "{selection_manifest.as_posix()}"
required_symbols = ["e"]
priority_joins = ["d->e"]
"""
    )

    ledger_path = tmp_path / "coverage_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "corpus_manifest_path": corpus_manifest.as_posix(),
                "summary": {},
                "entries": [
                    {"kind": "glyph", "symbol": "e", "missing_reviewed": 1},
                    {"kind": "join", "symbol": "d->e", "missing_reviewed": 1},
                ],
            }
        )
    )
    return selection_manifest, ledger_path


def _build_reviewed_manifest(tmp_path: Path) -> Path:
    selection_manifest, ledger_path = _write_fixture_inputs(tmp_path)
    reviewed_root = tmp_path / "workbench"
    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=reviewed_root,
        selection_manifest_path=selection_manifest,
    )
    workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "trusted",
            "notes": "body glyph",
            "bounds_px": {"x": 20, "y": 30, "width": 100, "height": 60},
            "cleanup_strokes": [
                {
                    "mode": "erase",
                    "size_px": 14,
                    "points": [{"x": 55, "y": 30}],
                }
            ],
        }
    )
    workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "join",
            "symbol": "d->e",
            "quality": "usable",
            "notes": "join stroke",
            "bounds_px": {"x": 130, "y": 95, "width": 80, "height": 30},
        }
    )
    return reviewed_root / "reviewed_manifest.toml"


def test_freeze_reviewed_exemplars_writes_crops_manifests_and_panels(tmp_path: Path):
    reviewed_manifest = _build_reviewed_manifest(tmp_path)

    result = freeze_reviewed_exemplars(reviewed_manifest, output_root=tmp_path / "frozen")

    manifest = tomllib.loads(result["manifest_path"].read_text(encoding="utf-8"))
    assert manifest["manifest_kind"] == "reviewed_exemplars"
    assert len(manifest["entries"]) == 2
    assert result["raw_glyph_panel_path"].exists()
    assert result["cleaned_glyph_panel_path"].exists()
    assert result["raw_join_panel_path"].exists()
    assert result["downstream_smoke_test_path"].exists()

    glyph_path = Path(manifest["entries"][0]["reviewed_exemplar_paths"][0])
    glyph_raw_path = Path(manifest["entries"][0]["reviewed_raw_exemplar_paths"][0])
    glyph_cleaned_path = Path(manifest["entries"][0]["reviewed_cleaned_exemplar_paths"][0])
    join_path = Path(manifest["entries"][1]["reviewed_exemplar_paths"][0])
    join_raw_path = Path(manifest["entries"][1]["reviewed_raw_exemplar_paths"][0])
    assert Image.open(glyph_path).size == (100, 60)
    assert Image.open(glyph_raw_path).size == (100, 60)
    assert Image.open(glyph_cleaned_path).size == (100, 60)
    assert Image.open(join_path).size == (80, 30)
    assert Image.open(join_raw_path).size == (80, 30)
    assert manifest["entries"][0]["reviewed_cleanup_stroke_counts"] == [1]
    assert manifest["entries"][1]["reviewed_cleanup_stroke_counts"] == [0]

    assert Image.open(glyph_raw_path).tobytes() != Image.open(glyph_cleaned_path).tobytes()

    smoke = json.loads(result["downstream_smoke_test_path"].read_text(encoding="utf-8"))
    assert smoke["passed"] is True
    assert smoke["target_count"] == 2

    targets = build_evofit_targets(result["manifest_path"], allowed_tiers=())
    assert [target.symbol for target in targets] == ["e", "d->e"]
    assert Path(targets[0].candidate_paths[0]) == glyph_cleaned_path


def test_freeze_reviewed_exemplars_is_deterministic_for_same_input(tmp_path: Path):
    reviewed_manifest = _build_reviewed_manifest(tmp_path)
    output_root = tmp_path / "frozen"

    first = freeze_reviewed_exemplars(reviewed_manifest, output_root=output_root)
    first_manifest = first["manifest_path"].read_text(encoding="utf-8")
    first_summary = first["summary_json_path"].read_text(encoding="utf-8")

    second = freeze_reviewed_exemplars(reviewed_manifest, output_root=output_root)
    second_manifest = second["manifest_path"].read_text(encoding="utf-8")
    second_summary = second["summary_json_path"].read_text(encoding="utf-8")

    assert first_manifest == second_manifest
    assert first_summary == second_summary


def test_freeze_reviewed_exemplars_skips_excluded_catalog_references(tmp_path: Path):
    selection_manifest, ledger_path = _write_fixture_inputs(tmp_path)
    reviewed_root = tmp_path / "workbench"
    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=reviewed_root,
        selection_manifest_path=selection_manifest,
    )
    included = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "trusted",
            "notes": "keep",
            "bounds_px": {"x": 20, "y": 30, "width": 100, "height": 60},
        }
    )
    excluded = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "drop",
            "bounds_px": {"x": 24, "y": 34, "width": 80, "height": 40},
        }
    )
    workbench.set_annotation_catalog_included(excluded["id"], False)

    result = freeze_reviewed_exemplars(reviewed_root / "reviewed_manifest.toml", output_root=tmp_path / "frozen")
    manifest = tomllib.loads(result["manifest_path"].read_text(encoding="utf-8"))

    assert len(manifest["entries"]) == 1
    assert manifest["entries"][0]["symbol"] == "e"
    assert len(manifest["entries"][0]["reviewed_exemplar_paths"]) == 1
    assert result["summary"]["reviewed_glyph_count"] == 1
    assert included["id"] != excluded["id"]
