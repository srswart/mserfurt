"""Tests for the TD-014 reviewed annotation workbench."""

from __future__ import annotations

import json
import threading
import time
import tomllib
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image

import scribesim.annotate.workbench as workbench_module
from scribesim.annotate.workbench import AnnotationWorkbenchServer, ReviewedAnnotationWorkbench
from scribesim.pathguide.model import DensePathGuide, GuideSample, GuideSource


def _write_fixture_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    image_path = tmp_path / "folio.jpg"
    Image.new("RGB", (320, 240), color=(250, 247, 240)).save(image_path)

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

    promotion_gate_report = tmp_path / "promotion_gate_report.json"
    promotion_gate_report.write_text(
        json.dumps(
            {
                "summary": {
                    "glyph_candidate_count": 1,
                    "join_candidate_count": 0,
                    "glyph_pass_count": 0,
                    "join_pass_count": 0,
                },
                "glyphs": {
                    "e": [
                        {
                            "kind": "glyphs",
                            "symbol": "e",
                            "rank": 0,
                            "path": "glyphs/auto_admitted/e/e_000_0029_l03_w02_c00.png",
                            "source_path": image_path.as_posix(),
                            "passed": False,
                            "metrics": {
                                "self_ncc_score": 0.31,
                                "competitor_margin": -0.08,
                                "cluster_consistency": 0.92,
                                "cluster_separation": 0.11,
                                "occupancy_balance_score": 0.24,
                            },
                            "failures": [
                                "competitor_margin=-0.0800 does not satisfy >= 0.0400",
                                "occupancy_balance_score=0.2400 does not satisfy >= 0.7000",
                            ],
                        }
                    ]
                },
                "joins": {"d->e": []},
            }
        ),
        encoding="utf-8",
    )

    corpus_manifest = tmp_path / "corpus_manifest.toml"
    corpus_manifest.write_text(
        f"""
schema_version = 1
selection_manifest_path = "{selection_manifest.as_posix()}"
promotion_gate_report_json_path = "{promotion_gate_report.as_posix()}"
required_symbols = ["e"]
priority_joins = ["d->e"]

[[entries]]
kind = "glyph"
symbol = "e"
auto_admitted_count = 1
auto_admitted_paths = ["glyphs/auto_admitted/e/e_000_0029_l03_w02_c00.png"]
quarantined_count = 1
quarantined_paths = ["glyphs/quarantined/e/e_001_0029_l04_w01_c00.png"]
rejected_count = 1
rejected_paths = ["glyphs/rejected/e/e_002_0029_l05_w00_c00.png"]
repair_only_count = 0
repair_only_paths = []
coverage_promoted = false

[[entries]]
kind = "join"
symbol = "d->e"
auto_admitted_count = 0
auto_admitted_paths = []
quarantined_count = 0
quarantined_paths = []
rejected_count = 0
rejected_paths = []
repair_only_count = 0
repair_only_paths = []
coverage_promoted = false
"""
    )

    ledger_path = tmp_path / "coverage_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "corpus_manifest_path": corpus_manifest.as_posix(),
                "summary": {
                    "glyph_reviewed_coverage": 0.0,
                    "join_reviewed_coverage": 0.0,
                    "glyph_promoted_coverage": 0.0,
                    "join_promoted_coverage": 0.0,
                },
                "entries": [
                    {
                        "kind": "glyph",
                        "symbol": "e",
                        "auto_admitted_count": 1,
                        "quarantined_count": 1,
                        "rejected_count": 1,
                        "promoted_count": 0,
                        "reviewed_count": 0,
                        "missing_reviewed": 1,
                    },
                    {
                        "kind": "join",
                        "symbol": "d->e",
                        "auto_admitted_count": 0,
                        "quarantined_count": 0,
                        "rejected_count": 0,
                        "promoted_count": 0,
                        "reviewed_count": 0,
                        "missing_reviewed": 1,
                    },
                ],
            }
        )
    )
    return selection_manifest, corpus_manifest, ledger_path


def _write_png(path: Path, *, size: tuple[int, int] = (24, 24), color: tuple[int, int, int] = (80, 80, 80)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=color).save(path)
    return path


def _dense_test_guide(symbol: str) -> DensePathGuide:
    samples = (
        GuideSample(0.0, 0.0, 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.2),
        GuideSample(0.2, 0.05, 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.2),
        GuideSample(0.4, 0.1, 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.2),
        GuideSample(0.6, 0.15, 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.2),
        GuideSample(0.8, 0.2, 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.2),
        GuideSample(1.0, 0.15, 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.2),
        GuideSample(1.2, 0.1, 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.2),
        GuideSample(1.4, 0.05, 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.2),
        GuideSample(1.6, 0.0, 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.2),
    )
    return DensePathGuide(
        symbol=symbol,
        kind="glyph",
        samples=samples,
        x_advance_mm=1.8,
        x_height_mm=3.8,
        entry_tangent=(1.0, 0.0),
        exit_tangent=(1.0, 0.0),
        sources=(
            GuideSource(
                source_id=f"test:{symbol}",
                source_path="tests",
                confidence_tier="accepted",
                split="validation",
                source_resolution_ppmm=16.0,
            ),
        ),
    )


def test_reviewed_annotation_workbench_saves_glyph_and_join_annotations(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )

    saved_glyph = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "trusted",
            "notes": "clear body letter",
            "bounds_px": {"x": 10, "y": 20, "width": 30, "height": 40},
            "cleanup_strokes": [
                {
                    "mode": "erase",
                    "size_px": 6,
                    "points": [{"x": 4, "y": 6}, {"x": 10, "y": 8}],
                }
            ],
        }
    )
    saved_join = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "join",
            "symbol": "d->e",
            "quality": "usable",
            "notes": "entry join",
            "bounds_px": {"x": 60, "y": 80, "width": 45, "height": 18},
        }
    )

    manifest = tomllib.loads((output_root / "reviewed_manifest.toml").read_text(encoding="utf-8"))
    state = workbench.get_state()
    assert len(state["annotations"]) == 2
    assert saved_glyph["kind"] == "glyph"
    assert saved_glyph["symbol"] == "e"
    assert saved_glyph["catalog_included"] is True
    assert saved_glyph["cleanup_strokes"][0]["mode"] == "erase"
    assert saved_join["kind"] == "join"
    assert saved_join["symbol"] == "d->e"
    assert saved_join["bounds_px"]["width"] == 45
    assert state["reviewed_manifest_path"].endswith("reviewed_manifest.toml")
    assert manifest["entry_count"] == 2
    assert manifest["entries"][0]["kind"] == "glyph"
    assert manifest["entries"][0]["catalog_included"] is True
    assert manifest["entries"][0]["cleanup_strokes"][0]["size_px"] == 6
    assert manifest["entries"][1]["kind"] == "join"


def test_annotation_workbench_state_exposes_symbol_status_and_guidance(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )

    state = workbench.get_state()
    glyph_status = state["symbol_statuses"]["glyph:e"]

    assert state["coverage_debt"][0]["status_key"] == "glyph:e"
    assert glyph_status["stage_statuses"][0]["status"] == "available"
    assert glyph_status["stage_statuses"][1]["status"] == "blocked"
    assert glyph_status["blockers"][0]["source"] == "promotion_gate"
    assert any("confusable" in item for item in glyph_status["guidance"])
    assert any("foreground balance" in item for item in glyph_status["guidance"])
    assert glyph_status["sample_refs"][0]["folio_id"] == "1"


def test_annotation_workbench_word_assist_can_propose_and_accept_segments(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    image_path = tmp_path / "folio.jpg"
    folio = Image.open(image_path).convert("L")
    array = np.array(folio, dtype=np.uint8)
    array[70:150, 40:56] = 0
    array[70:150, 88:104] = 0
    array[70:150, 136:152] = 0
    Image.fromarray(array).save(image_path)

    output_root = tmp_path / "reviewed"
    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )

    proposal = workbench.propose_word_assist(
        {
            "folio_id": "1",
            "bounds_px": {"x": 30, "y": 60, "width": 140, "height": 100},
            "transcript": "iii",
        }
    )

    assert proposal["units"] == ["i", "i", "i"]
    assert len(proposal["segments"]) == 3
    assert len(proposal["boundaries"]) == 4
    assert proposal["word_bounds_px"]["width"] == 140

    accepted = workbench.accept_word_assist(
        {
            "folio_id": "1",
            "bounds_px": proposal["word_bounds_px"],
            "transcript": proposal["transcript"],
            "units": proposal["units"],
            "boundaries": proposal["boundaries"],
            "quality": "usable",
        }
    )

    assert len(accepted["saved"]) == 3
    assert [entry["symbol"] for entry in accepted["saved"]] == ["i", "i", "i"]
    assert all('word assist transcript="iii"' in entry["notes"] for entry in accepted["saved"])


def test_annotation_workbench_stroke_assist_can_propose_segments(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    image_path = tmp_path / "folio.jpg"
    folio = Image.open(image_path).convert("L")
    array = np.array(folio, dtype=np.uint8)
    array[40:150, 90:108] = 0
    Image.fromarray(array).save(image_path)

    output_root = tmp_path / "reviewed"
    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "x",
            "quality": "usable",
            "notes": "stroke assist source",
            "bounds_px": {"x": 84, "y": 34, "width": 30, "height": 126},
        }
    )

    proposal = workbench.propose_stroke_assist({"annotation_id": saved["id"], "desired_stroke_count": 2})

    assert proposal["annotation_id"] == saved["id"]
    assert proposal["segments"]
    assert proposal["stroke_count"] >= 1
    assert proposal["mode"] == "requested-count"
    assert proposal["requested_stroke_count"] == 2
    assert proposal["template_stroke_count"] == 2
    assert proposal["selected_stroke_count"] == 2
    assert proposal["image_fit"] > 0.0
    assert len(proposal["segments"][0]["pressure_curve"]) == 4
    assert proposal["segments"][0]["nib_angle_mode"] == "auto"
    assert len(proposal["segments"][0]["nib_angle_curve"]) == 4
    assert len(proposal["segments"][0]["nib_angle_confidence"]) == 4


def test_annotation_workbench_symbol_rerun_collects_diagnostics(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "manual review",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )

    def fake_freeze_reviewed_exemplars(reviewed_manifest_path: Path, *, output_root: Path):
        output_root.mkdir(parents=True, exist_ok=True)
        manifest_path = output_root / "reviewed_exemplar_manifest.toml"
        manifest_path.write_text('manifest_kind = "reviewed_exemplars"\n', encoding="utf-8")
        summary_md_path = output_root / "summary.md"
        summary_md_path.write_text("freeze summary\n", encoding="utf-8")
        return {
            "manifest_path": manifest_path,
            "summary_md_path": summary_md_path,
            "summary": {"reviewed_glyph_count": 1, "reviewed_join_count": 0},
        }

    def fake_run_reviewed_evofit(
        reviewed_manifest_path: Path,
        *,
        output_root: Path,
        config,
        kind: str,
        symbols,
        guides_path=None,
        baseline_summary_path=None,
    ):
        output_root.mkdir(parents=True, exist_ok=True)
        comparison_path = output_root / "comparison.png"
        Image.new("RGB", (40, 20), color=(200, 200, 200)).save(comparison_path)
        fit_source_copy_path = output_root / "fit_source.png"
        Image.new("RGB", (20, 20), color=(20, 20, 20)).save(fit_source_copy_path)
        best_render_path = output_root / "best_render.png"
        Image.new("RGB", (20, 20), color=(120, 120, 120)).save(best_render_path)
        summary_md_path = output_root / "summary.md"
        summary_md_path.write_text("evofit summary\n", encoding="utf-8")
        manifest_path = output_root / "manifest.toml"
        manifest_path.write_text("schema_version = 1\n", encoding="utf-8")
        proposal_catalog_path = output_root / "proposal_guides.toml"
        proposal_catalog_path.write_text("", encoding="utf-8")
        return {
            "manifest_path": manifest_path,
            "summary_md_path": summary_md_path,
            "proposal_catalog_path": proposal_catalog_path,
            "summary": {
                "fit_source_count": 1,
                "converted_guide_count": 0,
                "fit_sources": [
                    {
                        "kind": kind,
                        "symbol": symbols[0],
                        "selected_source_quality_tier": "usable",
                        "selected_source_variant": "raw",
                        "selected_source_document_path": str(reviewed_manifest_path),
                        "structurally_convertible": False,
                        "validation_errors": ["contact polyline must not self-intersect"],
                        "comparison_path": comparison_path.as_posix(),
                        "fit_source_copy_path": fit_source_copy_path.as_posix(),
                        "best_render_path": best_render_path.as_posix(),
                        "prior_render_path": "",
                    }
                ],
            },
        }

    monkeypatch.setattr(workbench_module, "freeze_reviewed_exemplars", fake_freeze_reviewed_exemplars)
    monkeypatch.setattr(workbench_module, "run_reviewed_evofit", fake_run_reviewed_evofit)

    workbench.start_symbol_rerun("glyph", "e")
    for _ in range(100):
        rerun = workbench.get_state()["symbol_reruns"].get("glyph:e")
        if rerun and rerun["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    else:
        raise AssertionError("expected symbol rerun to complete")

    rerun = workbench.get_state()["symbol_reruns"]["glyph:e"]
    assert rerun["status"] == "completed"
    assert rerun["result"]["fit_source"]["symbol"] == "e"
    assert rerun["result"]["fit_source"]["structurally_convertible"] is False
    assert "contact polyline must not self-intersect" in rerun["result"]["fit_source"]["validation_errors"][0]
    assert rerun["result"]["artifacts"]["comparison"]["url"].startswith("/api/artifact?path=")


def test_annotation_workbench_symbol_rerun_exposes_final_guide_snapshots(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "manual review",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )

    def fake_freeze_reviewed_exemplars(reviewed_manifest_path: Path, *, output_root: Path):
        output_root.mkdir(parents=True, exist_ok=True)
        manifest_path = output_root / "reviewed_exemplar_manifest.toml"
        manifest_path.write_text('manifest_kind = "reviewed_exemplars"\n', encoding="utf-8")
        summary_md_path = output_root / "summary.md"
        summary_md_path.write_text("freeze summary\n", encoding="utf-8")
        return {
            "manifest_path": manifest_path,
            "summary_md_path": summary_md_path,
            "summary": {"reviewed_glyph_count": 1, "reviewed_join_count": 0},
        }

    def fake_run_reviewed_evofit(
        reviewed_manifest_path: Path,
        *,
        output_root: Path,
        config,
        kind: str,
        symbols,
        guides_path=None,
        baseline_summary_path=None,
    ):
        output_root.mkdir(parents=True, exist_ok=True)
        comparison_path = output_root / "comparison.png"
        Image.new("RGB", (40, 20), color=(200, 200, 200)).save(comparison_path)
        fit_source_copy_path = output_root / "fit_source.png"
        Image.new("RGB", (20, 20), color=(20, 20, 20)).save(fit_source_copy_path)
        best_render_path = output_root / "best_render.png"
        Image.new("RGB", (20, 20), color=(120, 120, 120)).save(best_render_path)
        summary_md_path = output_root / "summary.md"
        summary_md_path.write_text("evofit summary\n", encoding="utf-8")
        manifest_path = output_root / "manifest.toml"
        manifest_path.write_text("schema_version = 1\n", encoding="utf-8")
        proposal_catalog_path = output_root / "proposal_guides.toml"
        proposal_catalog_path.write_text("", encoding="utf-8")
        return {
            "manifest_path": manifest_path,
            "summary_md_path": summary_md_path,
            "proposal_catalog_path": proposal_catalog_path,
            "summary": {
                "fit_source_count": 1,
                "converted_guide_count": 1,
                "fit_sources": [
                    {
                        "kind": kind,
                        "symbol": symbols[0],
                        "selected_source_quality_tier": "usable",
                        "selected_source_variant": "raw",
                        "selected_source_document_path": str(reviewed_manifest_path),
                        "structurally_convertible": True,
                        "validation_errors": [],
                        "comparison_path": comparison_path.as_posix(),
                        "fit_source_copy_path": fit_source_copy_path.as_posix(),
                        "best_render_path": best_render_path.as_posix(),
                        "prior_render_path": "",
                    }
                ],
            },
        }

    def fake_freeze_reviewed_evofit_guides(bundle_manifest_path: Path, *, output_root: Path, guide_catalog_path: Path):
        output_root.mkdir(parents=True, exist_ok=True)
        overlay_dir = output_root / "overlay_snapshots"
        nominal_dir = output_root / "nominal_snapshots"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        nominal_dir.mkdir(parents=True, exist_ok=True)
        overlay_path = overlay_dir / "e.png"
        nominal_path = nominal_dir / "e.png"
        overlay_panel = overlay_dir / "panel.png"
        nominal_panel = nominal_dir / "panel.png"
        for path in (overlay_path, nominal_path, overlay_panel, nominal_panel):
            Image.new("RGB", (24, 24), color=(80, 80, 80)).save(path)
        coverage_md = output_root / "coverage_provenance_report.md"
        validation_md = output_root / "validation_report.md"
        manifest_path = output_root / "manifest.toml"
        guide_catalog_path.write_text("", encoding="utf-8")
        coverage_md.write_text("coverage\n", encoding="utf-8")
        validation_md.write_text("validation\n", encoding="utf-8")
        manifest_path.write_text("schema_version = 1\n", encoding="utf-8")
        return {
            "summary": {"guide_count": 1},
            "guide_catalog_path": guide_catalog_path,
            "manifest_path": manifest_path,
            "validation_report_json_path": output_root / "validation_report.json",
            "validation_report_md_path": validation_md,
            "coverage_provenance_report_json_path": output_root / "coverage_provenance_report.json",
            "coverage_provenance_report_md_path": coverage_md,
            "overlay_panel_path": overlay_panel,
            "nominal_panel_path": nominal_panel,
        }

    monkeypatch.setattr(workbench_module, "freeze_reviewed_exemplars", fake_freeze_reviewed_exemplars)
    monkeypatch.setattr(workbench_module, "run_reviewed_evofit", fake_run_reviewed_evofit)
    monkeypatch.setattr(workbench_module, "freeze_reviewed_evofit_guides", fake_freeze_reviewed_evofit_guides)

    workbench.start_symbol_rerun("glyph", "e")
    for _ in range(100):
        rerun = workbench.get_state()["symbol_reruns"].get("glyph:e")
        if rerun and rerun["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    else:
        raise AssertionError("expected symbol rerun to complete")

    rerun = workbench.get_state()["symbol_reruns"]["glyph:e"]
    assert rerun["status"] == "completed"
    assert rerun["result"]["artifacts"]["guide_overlay"]["url"].startswith("/api/artifact?path=")
    assert rerun["result"]["artifacts"]["guide_nominal"]["url"].startswith("/api/artifact?path=")
    assert rerun["result"]["artifacts"]["guide_overlay_panel"]["url"].startswith("/api/artifact?path=")
    assert rerun["result"]["artifacts"]["guide_nominal_panel"]["url"].startswith("/api/artifact?path=")


def test_annotation_workbench_can_save_manual_guide_and_expose_preview_artifacts(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "manual guide source",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )

    def fake_preview(entry: dict[str, object]) -> dict[str, str]:
        guide_root = output_root / "manual_guides_v1" / "glyph_e"
        overlay = _write_png(guide_root / "overlay.png")
        nominal = _write_png(guide_root / "nominal.png")
        crop = _write_png(guide_root / "source_crop.png", size=(22, 28), color=(120, 120, 120))
        catalog = guide_root / "manual_proposal_guides.toml"
        catalog.write_text("", encoding="utf-8")
        return {
            "guide_catalog_path": catalog.as_posix(),
            "preview_overlay_path": overlay.as_posix(),
            "preview_nominal_path": nominal.as_posix(),
            "source_crop_path": crop.as_posix(),
        }

    monkeypatch.setattr(workbench, "_write_manual_guide_previews", fake_preview)

    guide = workbench.save_manual_guide(
        {
            "annotation_id": saved["id"],
            "x_height_px": 28,
            "x_advance_px": 18,
            "corridor_half_width_mm": 0.24,
            "canvas_padding_px": 36,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "nib_angle_mode": "manual",
                    "nib_angle_curve": [33.0, 36.0, 42.0, 45.0],
                    "nib_angle_confidence": [0.4, 0.6, 0.8, 0.9],
                    "p0": {"x": 2, "y": 25},
                    "p1": {"x": 5, "y": 6},
                    "p2": {"x": 14, "y": 4},
                    "p3": {"x": 17, "y": 18},
                }
            ],
        }
    )

    state = workbench.get_state()
    assert guide["annotation_id"] == saved["id"]
    assert guide["symbol"] == "e"
    assert guide["catalog_name"] == "Workbench"
    assert guide["canvas_padding_px"] == 36
    assert len(guide["segments"]) == 1
    assert guide["segments"][0]["nib_angle_mode"] == "manual"
    assert guide["segments"][0]["nib_angle_curve"] == [33.0, 36.0, 42.0, 45.0]
    assert guide["segments"][0]["nib_angle_confidence"] == [0.4, 0.6, 0.8, 0.9]
    assert guide["preview_artifacts"]["overlay"]["url"].startswith("/api/artifact?path=")
    assert guide["preview_artifacts"]["nominal"]["url"].startswith("/api/artifact?path=")
    assert state["manual_guides"]["glyph:e"]["annotation_id"] == saved["id"]
    assert state["manual_guides"]["glyph:e"]["preview_artifacts"]["source_crop"]["url"].startswith(
        "/api/artifact?path="
    )
    manual_manifest = json.loads((output_root / "manual_guides_v1" / "manual_guides.json").read_text(encoding="utf-8"))
    assert manual_manifest["entry_count"] == 1
    assert manual_manifest["entries"][0]["symbol"] == "e"
    assert manual_manifest["entries"][0]["catalog_name"] == "Workbench"


def test_annotation_workbench_manual_guide_validation_error_mentions_stroke_order(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "manual guide source",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )

    try:
        workbench.save_manual_guide(
            {
                "annotation_id": saved["id"],
                "x_height_px": 28,
                "x_advance_px": 18,
                "corridor_half_width_mm": 0.24,
                "segments": [
                    {
                        "stroke_order": 1,
                        "contact": True,
                        "p0": {"x": 2, "y": 25},
                        "p1": {"x": 18, "y": -8},
                        "p2": {"x": -6, "y": 34},
                        "p3": {"x": 17, "y": 18},
                    }
                ],
            }
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected manual guide validation to fail")

    assert "likely affected stroke order(s): 1" in message


def test_annotation_workbench_manual_dense_guide_uses_per_segment_nib_angle_curve(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "manual guide nib curve source",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )

    guide = workbench._build_manual_dense_guide(
        {
            "annotation_id": saved["id"],
            "kind": "glyph",
            "symbol": "e",
            "x_height_px": 28,
            "x_advance_px": 18,
            "corridor_half_width_mm": 0.24,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "nib_angle_mode": "manual",
                    "nib_angle_curve": [32.0, 35.0, 47.0, 50.0],
                    "nib_angle_confidence": [0.2, 0.5, 0.7, 0.9],
                    "p0": {"x": 3, "y": 24},
                    "p1": {"x": 5, "y": 11},
                    "p2": {"x": 12, "y": 5},
                    "p3": {"x": 17, "y": 18},
                }
            ],
        }
    )

    nib_angles = [sample.nib_angle_deg for sample in guide.samples if sample.contact]
    confidences = [sample.nib_angle_confidence for sample in guide.samples if sample.contact]
    assert min(nib_angles) >= 31.5
    assert max(nib_angles) <= 50.5
    assert max(nib_angles) - min(nib_angles) >= 8.0
    assert max(confidences) >= 0.8


def test_annotation_workbench_manual_dense_guide_preserves_editor_y_orientation(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "l",
            "quality": "usable",
            "notes": "manual guide orientation source",
            "bounds_px": {"x": 12, "y": 14, "width": 15, "height": 43},
        }
    )

    guide = workbench._build_manual_dense_guide(
        {
            "annotation_id": saved["id"],
            "kind": "glyph",
            "symbol": "l",
            "x_height_px": 43,
            "x_advance_px": 15,
            "corridor_half_width_mm": 0.2,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "p0": {"x": 7, "y": 4},
                    "p1": {"x": 7, "y": 14},
                    "p2": {"x": 7, "y": 28},
                    "p3": {"x": 7, "y": 39},
                }
            ],
        }
    )

    contact_samples = [sample for sample in guide.samples if sample.contact]
    assert contact_samples[0].y_mm < contact_samples[-1].y_mm


def test_annotation_workbench_preserves_manual_guides_in_separate_named_catalogs(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "manual guide source",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )

    def fake_preview(entry: dict[str, object]) -> dict[str, str]:
        guide_root = output_root / "manual_guides_v1" / str(entry["id"])
        overlay = _write_png(guide_root / "overlay.png")
        nominal = _write_png(guide_root / "nominal.png")
        crop = _write_png(guide_root / "source_crop.png", size=(22, 28), color=(120, 120, 120))
        catalog = guide_root / "manual_proposal_guides.toml"
        catalog.write_text("", encoding="utf-8")
        return {
            "guide_catalog_path": catalog.as_posix(),
            "preview_overlay_path": overlay.as_posix(),
            "preview_nominal_path": nominal.as_posix(),
            "source_crop_path": crop.as_posix(),
        }

    monkeypatch.setattr(workbench, "_write_manual_guide_previews", fake_preview)

    first = workbench.save_manual_guide(
        {
            "annotation_id": saved["id"],
            "catalog_name": "Catalog A",
            "x_height_px": 28,
            "x_advance_px": 18,
            "corridor_half_width_mm": 0.24,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "p0": {"x": 2, "y": 25},
                    "p1": {"x": 5, "y": 6},
                    "p2": {"x": 14, "y": 4},
                    "p3": {"x": 17, "y": 18},
                }
            ],
        }
    )
    second = workbench.save_manual_guide(
        {
            "annotation_id": saved["id"],
            "catalog_name": "Catalog B",
            "x_height_px": 28,
            "x_advance_px": 18,
            "corridor_half_width_mm": 0.24,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "p0": {"x": 3, "y": 24},
                    "p1": {"x": 6, "y": 7},
                    "p2": {"x": 13, "y": 5},
                    "p3": {"x": 18, "y": 19},
                }
            ],
        }
    )

    state = workbench.get_state()
    entries = state["manual_guide_groups"]["glyph:e"]["entries"]
    assert {entry["catalog_name"] for entry in entries} == {"Catalog A", "Catalog B"}
    catalogs = {entry["name"]: entry for entry in state["manual_guide_catalogs"]}
    assert catalogs["Catalog A"]["active_entry_count"] == 1
    assert catalogs["Catalog B"]["active_entry_count"] == 1


def test_annotation_workbench_save_manual_guide_does_not_collapse_null_ids(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved_a = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "manual guide source a",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )
    saved_b = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "n",
            "quality": "usable",
            "notes": "manual guide source b",
            "bounds_px": {"x": 44, "y": 14, "width": 22, "height": 28},
        }
    )

    def fake_preview(entry: dict[str, object]) -> dict[str, str]:
        guide_root = output_root / "manual_guides_v1" / str(entry["id"])
        overlay = _write_png(guide_root / "overlay.png")
        nominal = _write_png(guide_root / "nominal.png")
        crop = _write_png(guide_root / "source_crop.png", size=(22, 28), color=(120, 120, 120))
        catalog = guide_root / "manual_proposal_guides.toml"
        catalog.write_text("", encoding="utf-8")
        return {
            "guide_catalog_path": catalog.as_posix(),
            "preview_overlay_path": overlay.as_posix(),
            "preview_nominal_path": nominal.as_posix(),
            "source_crop_path": crop.as_posix(),
        }

    monkeypatch.setattr(workbench, "_write_manual_guide_previews", fake_preview)
    monkeypatch.setattr(workbench, "_build_manual_dense_guide", lambda entry: _dense_test_guide(str(entry["symbol"])))

    guide_a = workbench.save_manual_guide(
        {
            "id": None,
            "annotation_id": saved_a["id"],
            "catalog_name": "Workbench",
            "x_height_px": 28,
            "x_advance_px": 18,
            "corridor_half_width_mm": 0.24,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "p0": {"x": 2, "y": 25},
                    "p1": {"x": 5, "y": 6},
                    "p2": {"x": 14, "y": 4},
                    "p3": {"x": 17, "y": 18},
                }
            ],
        }
    )
    guide_b = workbench.save_manual_guide(
        {
            "id": None,
            "annotation_id": saved_b["id"],
            "catalog_name": "Workbench",
            "x_height_px": 28,
            "x_advance_px": 18,
            "corridor_half_width_mm": 0.24,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "p0": {"x": 3, "y": 24},
                    "p1": {"x": 6, "y": 7},
                    "p2": {"x": 13, "y": 5},
                    "p3": {"x": 18, "y": 19},
                }
            ],
        }
    )

    entries = workbench.manual_guides["entries"]
    assert len(entries) == 2
    assert guide_a["id"] != guide_b["id"]
    assert {entry["symbol"] for entry in entries} == {"e", "n"}


def test_annotation_workbench_can_store_multiple_manual_guides_per_symbol(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    first = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "first guide source",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )
    second = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "trusted",
            "notes": "second guide source",
            "bounds_px": {"x": 40, "y": 18, "width": 20, "height": 26},
        }
    )

    def fake_preview(entry: dict[str, object]) -> dict[str, str]:
        guide_root = output_root / "manual_guides_v1" / str(entry["id"])
        overlay = _write_png(guide_root / "overlay.png")
        nominal = _write_png(guide_root / "nominal.png")
        crop = _write_png(
            guide_root / "source_crop.png",
            size=(int(entry["bounds_px"]["width"]), int(entry["bounds_px"]["height"])),
            color=(120, 120, 120),
        )
        catalog = guide_root / "manual_proposal_guides.toml"
        catalog.write_text("", encoding="utf-8")
        return {
            "guide_catalog_path": catalog.as_posix(),
            "preview_overlay_path": overlay.as_posix(),
            "preview_nominal_path": nominal.as_posix(),
            "source_crop_path": crop.as_posix(),
        }

    monkeypatch.setattr(workbench, "_write_manual_guide_previews", fake_preview)

    workbench.save_manual_guide(
        {
            "annotation_id": first["id"],
            "x_height_px": 28,
            "x_advance_px": 18,
            "corridor_half_width_mm": 0.24,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "p0": {"x": 2, "y": 25},
                    "p1": {"x": 5, "y": 6},
                    "p2": {"x": 14, "y": 4},
                    "p3": {"x": 17, "y": 18},
                }
            ],
        }
    )
    second_guide = workbench.save_manual_guide(
        {
            "annotation_id": second["id"],
            "x_height_px": 26,
            "x_advance_px": 17,
            "corridor_half_width_mm": 0.21,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "p0": {"x": 3, "y": 22},
                    "p1": {"x": 6, "y": 8},
                    "p2": {"x": 11, "y": 5},
                    "p3": {"x": 15, "y": 17},
                }
            ],
        }
    )

    state = workbench.get_state()
    group = state["manual_guide_groups"]["glyph:e"]
    assert len(group["entries"]) == 2
    assert group["active_id"] == second_guide["id"]
    assert state["manual_guides"]["glyph:e"]["annotation_id"] == second["id"]

    reactivated = workbench.set_manual_guide_active(group["entries"][1]["id"])
    state = workbench.get_state()
    assert reactivated["id"] == group["entries"][1]["id"]
    assert state["manual_guide_groups"]["glyph:e"]["active_id"] == group["entries"][1]["id"]


def test_annotation_workbench_symbol_rerun_can_use_manual_guide_override(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "manual guide source",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )

    def fake_preview(entry: dict[str, object]) -> dict[str, str]:
        guide_root = output_root / "manual_guides_v1" / "glyph_e"
        overlay = _write_png(guide_root / "overlay.png")
        nominal = _write_png(guide_root / "nominal.png")
        crop = _write_png(guide_root / "source_crop.png", size=(22, 28), color=(120, 120, 120))
        catalog = guide_root / "manual_proposal_guides.toml"
        catalog.write_text("", encoding="utf-8")
        return {
            "guide_catalog_path": catalog.as_posix(),
            "preview_overlay_path": overlay.as_posix(),
            "preview_nominal_path": nominal.as_posix(),
            "source_crop_path": crop.as_posix(),
        }

    monkeypatch.setattr(workbench, "_write_manual_guide_previews", fake_preview)

    workbench.save_manual_guide(
        {
            "annotation_id": saved["id"],
            "x_height_px": 28,
            "x_advance_px": 18,
            "corridor_half_width_mm": 0.24,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "p0": {"x": 2, "y": 25},
                    "p1": {"x": 5, "y": 6},
                    "p2": {"x": 14, "y": 4},
                    "p3": {"x": 17, "y": 18},
                }
            ],
        }
    )

    def fake_freeze_reviewed_exemplars(reviewed_manifest_path: Path, *, output_root: Path):
        output_root.mkdir(parents=True, exist_ok=True)
        manifest_path = output_root / "reviewed_exemplar_manifest.toml"
        manifest_path.write_text('manifest_kind = "reviewed_exemplars"\n', encoding="utf-8")
        summary_md_path = output_root / "summary.md"
        summary_md_path.write_text("freeze summary\n", encoding="utf-8")
        return {
            "manifest_path": manifest_path,
            "summary_md_path": summary_md_path,
            "summary": {"reviewed_glyph_count": 1, "reviewed_join_count": 0},
        }

    def fake_run_reviewed_evofit(
        reviewed_manifest_path: Path,
        *,
        output_root: Path,
        config,
        kind: str,
        symbols,
        guides_path=None,
        baseline_summary_path=None,
    ):
        output_root.mkdir(parents=True, exist_ok=True)
        comparison_path = _write_png(output_root / "comparison.png", size=(40, 20), color=(200, 200, 200))
        fit_source_copy_path = _write_png(output_root / "fit_source.png", size=(20, 20), color=(20, 20, 20))
        best_render_path = _write_png(output_root / "best_render.png", size=(20, 20), color=(120, 120, 120))
        summary_md_path = output_root / "summary.md"
        summary_md_path.write_text("evofit summary\n", encoding="utf-8")
        manifest_path = output_root / "manifest.toml"
        manifest_path.write_text("schema_version = 1\n", encoding="utf-8")
        proposal_catalog_path = output_root / "proposal_guides.toml"
        proposal_catalog_path.write_text("", encoding="utf-8")
        return {
            "manifest_path": manifest_path,
            "summary_md_path": summary_md_path,
            "proposal_catalog_path": proposal_catalog_path,
            "summary": {
                "fit_source_count": 1,
                "converted_guide_count": 0,
                "fit_sources": [
                    {
                        "kind": kind,
                        "symbol": symbols[0],
                        "selected_source_quality_tier": "usable",
                        "selected_source_variant": "raw",
                        "selected_source_document_path": str(reviewed_manifest_path),
                        "structurally_convertible": False,
                        "validation_errors": ["contact polyline must not self-intersect"],
                        "comparison_path": comparison_path.as_posix(),
                        "fit_source_copy_path": fit_source_copy_path.as_posix(),
                        "best_render_path": best_render_path.as_posix(),
                        "prior_render_path": "",
                    }
                ],
            },
        }

    def fake_write_manual_guide_bundle(*, run_root: Path, freeze_manifest_path: Path, manual_guide: dict[str, object]):
        bundle_root = run_root / "manual_guide_override"
        bundle_root.mkdir(parents=True, exist_ok=True)
        manifest_path = bundle_root / "manifest.toml"
        manifest_path.write_text("schema_version = 1\n", encoding="utf-8")
        return manifest_path, {
            "kind": manual_guide["kind"],
            "symbol": manual_guide["symbol"],
            "structurally_convertible": True,
            "validation_errors": [],
        }

    def fake_freeze_reviewed_evofit_guides(bundle_manifest_path: Path, *, output_root: Path, guide_catalog_path: Path):
        output_root.mkdir(parents=True, exist_ok=True)
        overlay_dir = output_root / "overlay_snapshots"
        nominal_dir = output_root / "nominal_snapshots"
        overlay_path = _write_png(overlay_dir / "e.png")
        nominal_path = _write_png(nominal_dir / "e.png")
        overlay_panel = _write_png(overlay_dir / "panel.png")
        nominal_panel = _write_png(nominal_dir / "panel.png")
        coverage_md = output_root / "coverage_provenance_report.md"
        validation_md = output_root / "validation_report.md"
        manifest_path = output_root / "manifest.toml"
        guide_catalog_path.write_text("", encoding="utf-8")
        coverage_md.write_text("coverage\n", encoding="utf-8")
        validation_md.write_text("validation\n", encoding="utf-8")
        manifest_path.write_text("schema_version = 1\n", encoding="utf-8")
        assert bundle_manifest_path.name == "manifest.toml"
        assert overlay_path.exists() and nominal_path.exists()
        return {
            "summary": {"guide_count": 1},
            "guide_catalog_path": guide_catalog_path,
            "manifest_path": manifest_path,
            "validation_report_json_path": output_root / "validation_report.json",
            "validation_report_md_path": validation_md,
            "coverage_provenance_report_json_path": output_root / "coverage_provenance_report.json",
            "coverage_provenance_report_md_path": coverage_md,
            "overlay_panel_path": overlay_panel,
            "nominal_panel_path": nominal_panel,
        }

    monkeypatch.setattr(workbench_module, "freeze_reviewed_exemplars", fake_freeze_reviewed_exemplars)
    monkeypatch.setattr(workbench_module, "run_reviewed_evofit", fake_run_reviewed_evofit)
    monkeypatch.setattr(workbench_module, "freeze_reviewed_evofit_guides", fake_freeze_reviewed_evofit_guides)
    monkeypatch.setattr(workbench, "_write_manual_guide_bundle", fake_write_manual_guide_bundle)

    workbench.start_symbol_rerun("glyph", "e")
    for _ in range(100):
        rerun = workbench.get_state()["symbol_reruns"].get("glyph:e")
        if rerun and rerun["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    else:
        raise AssertionError("expected symbol rerun to complete")

    rerun = workbench.get_state()["symbol_reruns"]["glyph:e"]
    assert rerun["status"] == "completed"
    assert rerun["result"]["guide_source"] == "manual"
    assert rerun["result"]["manual_guide"]["annotation_id"] == saved["id"]
    assert rerun["result"]["artifacts"]["manual_source"]["url"].startswith("/api/artifact?path=")
    assert rerun["result"]["artifacts"]["manual_overlay"]["url"].startswith("/api/artifact?path=")
    assert rerun["result"]["artifacts"]["manual_nominal"]["url"].startswith("/api/artifact?path=")
    assert rerun["result"]["artifacts"]["guide_overlay"]["url"].startswith("/api/artifact?path=")
    assert rerun["result"]["guide_catalog_path"].endswith("reviewed_promoted_v1.toml")


def test_annotation_workbench_can_exclude_reviewed_references_from_catalog(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    first = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "first candidate",
            "bounds_px": {"x": 10, "y": 12, "width": 20, "height": 24},
        }
    )
    second = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "trusted",
            "notes": "second candidate",
            "bounds_px": {"x": 40, "y": 20, "width": 24, "height": 28},
        }
    )

    updated = workbench.set_annotation_catalog_included(first["id"], False)
    state = workbench.get_state()
    glyph_status = state["symbol_statuses"]["glyph:e"]

    assert updated["catalog_included"] is False
    assert glyph_status["counts"]["reviewed"] == 1
    assert glyph_status["counts"]["reviewed_excluded"] == 1

    workbench.set_annotation_catalog_included(second["id"], False)
    state = workbench.get_state()
    glyph_status = state["symbol_statuses"]["glyph:e"]
    assert glyph_status["counts"]["reviewed"] == 0
    assert glyph_status["counts"]["reviewed_excluded"] == 2
    assert any(item["status_key"] == "glyph:e" for item in state["coverage_debt"])


def test_annotation_workbench_state_includes_reviewed_symbols_outside_ledger_inventory(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "x",
            "quality": "usable",
            "notes": "reviewed-only symbol",
            "bounds_px": {"x": 18, "y": 22, "width": 20, "height": 24},
        }
    )

    state = workbench.get_state()

    extra_entry = next((item for item in state["coverage_entries"] if item["kind"] == "glyph" and item["symbol"] == "x"), None)
    assert extra_entry is not None
    assert extra_entry["reviewed_count"] == 1
    assert extra_entry["missing_reviewed"] == 0
    assert state["symbol_statuses"]["glyph:x"]["counts"]["reviewed"] == 1
    assert saved["id"] in {item["id"] for item in state["annotations"]}


def test_annotation_workbench_server_serves_state_and_saves_annotations(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    server = AnnotationWorkbenchServer(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
        host="127.0.0.1",
        port=0,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        state = json.loads(urlopen(f"{server.url}/api/state", timeout=2).read().decode("utf-8"))
        assert state["folios"][0]["canvas_label"] == "(0029)"
        assert state["coverage_debt"][0]["symbol"] == "e"

        payload = {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "trusted",
            "notes": "manual review",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
            "cleanup_strokes": [
                {
                    "mode": "erase",
                    "size_px": 4,
                    "points": [{"x": 2, "y": 3}],
                }
            ],
        }
        request = Request(
            f"{server.url}/api/annotations",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        response = json.loads(urlopen(request, timeout=2).read().decode("utf-8"))
        assert response["saved"]["symbol"] == "e"
        assert response["saved"]["cleanup_strokes"][0]["size_px"] == 4
        assert len(response["annotations"]) == 1
        assert response["state"]["symbol_statuses"]["glyph:e"]["counts"]["reviewed"] == 1
        assert response["state"]["coverage_summary"]["glyph_reviewed_coverage"] == 1.0

        delete_request = Request(
            f"{server.url}/api/annotations/{response['saved']['id']}",
            method="DELETE",
        )
        deleted = json.loads(urlopen(delete_request, timeout=2).read().decode("utf-8"))
        assert deleted["deleted"] == response["saved"]["id"]
        assert deleted["annotations"] == []
        assert deleted["state"]["symbol_statuses"]["glyph:e"]["counts"]["reviewed"] == 0
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_annotation_workbench_string_render_reports_missing_exact_glyphs(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )

    def fake_catalog(*, run_root: Path, x_height_mm: float, catalog_names=None):
        catalog_path = run_root / "effective_guides.toml"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text("schema_version = 1\n", encoding="utf-8")
        return {
            "catalog": {"e": _dense_test_guide("e")},
            "catalog_path": catalog_path,
            "summary": {
                "source_label": "test",
                "guide_catalog_path": catalog_path.as_posix(),
                "guide_count": 1,
                "glyph_count": 1,
                "join_count": 0,
                "manual_override_count": 0,
            },
        }

    monkeypatch.setattr(workbench, "_build_effective_render_catalog", fake_catalog)

    workbench.start_string_render({"text": "eb", "check_only": True})
    for _ in range(100):
        render = workbench.get_state()["string_render"]
        if render and render.get("status") in {"completed", "failed"}:
            break
        time.sleep(0.01)
    else:
        raise AssertionError("expected string render to complete")

    render = workbench.get_state()["string_render"]
    assert render["status"] == "completed"
    assert render["result"]["rendered"] is False
    assert render["result"]["availability"]["available"] is False
    assert render["result"]["availability"]["missing_symbols"] == ["b"]
    assert "Missing exact guides for: b" in render["message"]


def test_annotation_workbench_string_render_writes_render_artifacts(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )

    def fake_catalog(*, run_root: Path, x_height_mm: float, catalog_names=None):
        catalog_path = run_root / "effective_guides.toml"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text("schema_version = 1\n", encoding="utf-8")
        return {
            "catalog": {
                "e": _dense_test_guide("e"),
                "n": _dense_test_guide("n"),
            },
            "catalog_path": catalog_path,
            "summary": {
                "source_label": "test",
                "guide_catalog_path": catalog_path.as_posix(),
                "guide_count": 2,
                "glyph_count": 2,
                "join_count": 0,
                "manual_override_count": 0,
            },
        }

    def fake_render_guided_folio_lines(
        lines,
        *,
        profile,
        dpi,
        supersample,
        x_height_mm,
        line_spacing_mm,
        page_width_mm,
        page_height_mm,
        margin_left_mm,
        margin_top_mm,
        exact_symbols,
        guide_catalog_path,
        return_metadata,
    ):
        assert lines == ["en"]
        assert exact_symbols is True
        assert return_metadata is True
        page = np.full((16, 48, 3), 180, dtype=np.uint8)
        heat = np.full((16, 48), 120, dtype=np.uint8)
        aligned_page = np.full((16, 48, 3), 210, dtype=np.uint8)
        aligned_heat = np.full((16, 48), 90, dtype=np.uint8)
        return page, heat, {
            "render_trajectory_mode": "actual",
            "exact_symbols": True,
            "activated_parameters": {
                "folio.base_pressure": profile.folio.base_pressure,
                "glyph.baseline_jitter_mm": profile.glyph.baseline_jitter_mm,
            },
            "guide_catalog": {
                "source_label": "test",
                "guide_count": 2,
                "glyph_count": 2,
                "join_count": 0,
                "manual_override_count": 0,
            },
            "resolution": {
                "glyph_count": 2,
                "exact_character_coverage": 1.0,
                "alias_substitution_count": 0,
                "normalized_substitution_count": 0,
                "exact_only_passed": True,
                "line_statuses": [],
            },
            "aligned_page": aligned_page,
            "aligned_heat": aligned_heat,
        }

    monkeypatch.setattr(workbench, "_build_effective_render_catalog", fake_catalog)
    monkeypatch.setattr(workbench_module, "render_guided_folio_lines", fake_render_guided_folio_lines)

    workbench.start_string_render({"text": "en", "dpi": 220, "supersample": 2})
    for _ in range(100):
        render = workbench.get_state()["string_render"]
        if render and render.get("status") in {"completed", "failed"}:
            break
        time.sleep(0.01)
    else:
        raise AssertionError("expected string render to complete")

    render = workbench.get_state()["string_render"]
    assert render["status"] == "completed"
    assert render["result"]["rendered"] is True
    assert render["result"]["availability"]["available"] is True
    assert render["result"]["artifacts"]["page"]["url"].startswith("/api/artifact?path=")
    assert render["result"]["artifacts"]["pressure_heat"]["url"].startswith("/api/artifact?path=")
    assert render["result"]["artifacts"]["aligned_page"]["url"].startswith("/api/artifact?path=")
    assert render["result"]["artifacts"]["aligned_heat"]["url"].startswith("/api/artifact?path=")
    assert render["result"]["artifacts"]["metadata"]["url"].startswith("/api/artifact?path=")
    assert render["result"]["parameters"]["dpi"] == 220
    assert render["result"]["parameters"]["supersample"] == 2
    assert render["result"]["resolution"]["exact_character_coverage"] == 1.0


def test_annotation_workbench_string_render_filters_manual_guides_by_catalog(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "manual guide source",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )

    def fake_preview(entry: dict[str, object]) -> dict[str, str]:
        guide_root = output_root / "manual_guides_v1" / str(entry["id"])
        overlay = _write_png(guide_root / "overlay.png")
        nominal = _write_png(guide_root / "nominal.png")
        crop = _write_png(guide_root / "source_crop.png", size=(22, 28), color=(120, 120, 120))
        catalog = guide_root / "manual_proposal_guides.toml"
        catalog.write_text("", encoding="utf-8")
        return {
            "guide_catalog_path": catalog.as_posix(),
            "preview_overlay_path": overlay.as_posix(),
            "preview_nominal_path": nominal.as_posix(),
            "source_crop_path": crop.as_posix(),
        }

    monkeypatch.setattr(workbench, "_write_manual_guide_previews", fake_preview)
    monkeypatch.setattr(workbench, "_build_manual_dense_guide", lambda entry: _dense_test_guide(str(entry["symbol"])))

    workbench.save_manual_guide(
        {
            "annotation_id": saved["id"],
            "catalog_name": "Catalog A",
            "x_height_px": 28,
            "x_advance_px": 18,
            "corridor_half_width_mm": 0.24,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "p0": {"x": 2, "y": 25},
                    "p1": {"x": 5, "y": 6},
                    "p2": {"x": 14, "y": 4},
                    "p3": {"x": 17, "y": 18},
                }
            ],
        }
    )
    workbench.save_manual_guide(
        {
            "annotation_id": saved["id"],
            "catalog_name": "Catalog B",
            "x_height_px": 28,
            "x_advance_px": 18,
            "corridor_half_width_mm": 0.24,
            "segments": [
                {
                    "stroke_order": 1,
                    "contact": True,
                    "p0": {"x": 3, "y": 24},
                    "p1": {"x": 6, "y": 7},
                    "p2": {"x": 13, "y": 5},
                    "p3": {"x": 18, "y": 19},
                }
            ],
        }
    )

    a_catalog = workbench._build_effective_render_catalog(
        run_root=output_root / "render_a",
        x_height_mm=3.8,
        catalog_names=["Catalog A"],
    )
    b_catalog = workbench._build_effective_render_catalog(
        run_root=output_root / "render_b",
        x_height_mm=3.8,
        catalog_names=["Catalog B"],
    )
    combined_catalog = workbench._build_effective_render_catalog(
        run_root=output_root / "render_ab",
        x_height_mm=3.8,
        catalog_names=["Catalog A", "Catalog B"],
    )

    assert a_catalog["summary"]["catalog_names"] == ["Catalog A"]
    assert b_catalog["summary"]["catalog_names"] == ["Catalog B"]
    assert combined_catalog["summary"]["catalog_names"] == ["Catalog A", "Catalog B"]
    assert a_catalog["summary"]["manual_override_count"] == 1
    assert b_catalog["summary"]["manual_override_count"] == 1
    assert combined_catalog["summary"]["manual_override_count"] == 1
    assert any(entry["symbol"] == "e" and entry["source"] == "manual" for entry in combined_catalog["summary"]["effective_symbols"])


def test_annotation_workbench_string_render_defaults_include_all_populated_manual_catalogs(tmp_path: Path, monkeypatch):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )
    saved = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "usable",
            "notes": "manual guide source",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
        }
    )

    def fake_preview(entry: dict[str, object]) -> dict[str, str]:
        guide_root = output_root / "manual_guides_v1" / str(entry["id"])
        overlay = _write_png(guide_root / "overlay.png")
        nominal = _write_png(guide_root / "nominal.png")
        crop = _write_png(guide_root / "source_crop.png", size=(22, 28), color=(120, 120, 120))
        catalog = guide_root / "manual_proposal_guides.toml"
        catalog.write_text("", encoding="utf-8")
        return {
            "guide_catalog_path": catalog.as_posix(),
            "preview_overlay_path": overlay.as_posix(),
            "preview_nominal_path": nominal.as_posix(),
            "source_crop_path": crop.as_posix(),
        }

    monkeypatch.setattr(workbench, "_write_manual_guide_previews", fake_preview)
    monkeypatch.setattr(workbench, "_build_manual_dense_guide", lambda entry: _dense_test_guide(str(entry["symbol"])))

    for name in ("Catalog A", "Catalog B"):
        workbench.save_manual_guide(
            {
                "annotation_id": saved["id"],
                "catalog_name": name,
                "x_height_px": 28,
                "x_advance_px": 18,
                "corridor_half_width_mm": 0.24,
                "segments": [
                    {
                        "stroke_order": 1,
                        "contact": True,
                        "p0": {"x": 2, "y": 25},
                        "p1": {"x": 5, "y": 6},
                        "p2": {"x": 14, "y": 4},
                        "p3": {"x": 17, "y": 18},
                    }
                ],
            }
        )

    defaults = workbench._string_render_defaults()

    assert defaults["catalog_names"] == ["Catalog A", "Catalog B"]


def test_annotation_workbench_root_html_exposes_500_percent_zoom(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    server = AnnotationWorkbenchServer(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
        host="127.0.0.1",
        port=0,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        html = urlopen(f"{server.url}/", timeout=2).read().decode("utf-8")
        assert 'id="zoom"' in html
        assert 'max="500"' in html
        assert 'id="magnifier-canvas"' in html
        assert 'id="zoom-in"' in html
        assert 'id="zoom-out"' in html
        assert 'id="zoom-reset"' in html
        assert 'id="pan-toggle"' in html
        assert 'id="symbol-status-title"' in html
        assert 'id="symbol-status-blockers"' in html
        assert 'id="symbol-status-guidance"' in html
        assert 'id="symbol-status-samples"' in html
        assert 'id="coverage-browser"' in html
        assert 'id="symbol-menu-modal"' in html
        assert 'id="symbol-menu-rerun"' in html
        assert 'id="symbol-menu-guide-editor"' in html
        assert 'id="symbol-menu-delete-guide"' in html
        assert 'id="symbol-reference-list"' in html
        assert 'id="guide-editor-modal"' in html
        assert 'id="guide-editor-mode-add"' in html
        assert 'id="guide-editor-mode-edit"' in html
        assert 'id="guide-editor-zoom"' in html
        assert 'id="guide-editor-zoom-in"' in html
        assert 'id="guide-editor-zoom-out"' in html
        assert 'id="guide-editor-zoom-reset"' in html
        assert 'id="guide-editor-canvas-viewport"' in html
        assert 'id="guide-editor-canvas"' in html
        assert 'id="guide-editor-catalog"' in html
        assert 'id="guide-editor-analyze"' in html
        assert 'id="guide-editor-reset-proposal"' in html
        assert 'id="guide-editor-padding-px"' in html
        assert 'id="guide-editor-desired-stroke-count"' in html
        assert 'id="guide-editor-save"' in html
        assert 'id="guide-editor-process"' in html
        assert 'id="guide-editor-delete"' in html
        assert 'id="guide-editor-proposal"' in html
        assert 'id="guide-editor-saved-guides"' in html
        assert 'id="guide-editor-preview-artifacts"' in html
        assert 'id="guide-editor-rerun-artifacts"' in html
        assert 'id="symbol-rerun-button"' in html
        assert 'id="symbol-rerun-open"' in html
        assert 'id="symbol-rerun-modal"' in html
        assert 'id="symbol-rerun-modal-close"' in html
        assert 'id="symbol-rerun-details"' in html
        assert 'id="symbol-rerun-artifacts"' in html
        assert 'id="string-render-open"' in html
        assert 'id="string-render-modal"' in html
        assert 'id="string-render-close"' in html
        assert 'id="string-render-text"' in html
        assert 'id="string-render-catalogs"' in html
        assert 'id="string-render-catalog-list"' in html
        assert 'id="string-render-check"' in html
        assert 'id="string-render-run"' in html
        assert 'id="string-render-dpi"' in html
        assert 'id="string-render-supersample"' in html
        assert 'id="string-render-x-height-mm"' in html
        assert 'id="string-render-line-spacing-mm"' in html
        assert 'id="string-render-page-width-mm"' in html
        assert 'id="string-render-page-height-mm"' in html
        assert 'id="string-render-nib-width-mm"' in html
        assert 'id="string-render-advanced-overrides"' in html
        assert 'id="string-render-details"' in html
        assert 'id="string-render-artifacts"' in html
        assert 'id="word-assist-open"' in html
        assert 'id="word-assist-modal"' in html
        assert 'id="word-assist-close"' in html
        assert 'id="word-assist-canvas"' in html
        assert 'id="word-assist-transcript"' in html
        assert 'id="word-assist-run"' in html
        assert 'id="word-assist-rescore"' in html
        assert 'id="word-assist-accept"' in html
        assert 'id="word-assist-summary"' in html
        assert 'id="word-assist-segments"' in html
        assert 'id="cleanup-raw-canvas"' in html
        assert 'id="cleanup-clean-canvas"' in html
        assert 'id="cleanup-mode-erase"' in html
        assert 'id="cleanup-mode-restore"' in html
        assert html.index("Magnifier") < html.index("Reviewed manifest")
        assert html.index("Cleanup Editor") > html.index("Save Annotation")
    finally:
        server.shutdown()
        thread.join(timeout=2)
