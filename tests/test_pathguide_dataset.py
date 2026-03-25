"""Tests for the TD-014 starter alphabet pathguide dataset."""

from __future__ import annotations

import json
import math
from pathlib import Path
import tomllib

from scribesim.pathguide import (
    ACTIVE_FOLIO_ALPHABET_V1_GLYPHS,
    ACTIVE_FOLIO_ALPHABET_V1_NEW_GLYPHS,
    ACTIVE_FOLIO_ALPHABET_V1_PATH,
    ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS,
    ACTIVE_FOLIO_ALPHABET_V1_REVIEW_FOLIOS,
    ACTIVE_FOLIO_ALPHABET_V1_SOURCE_MODES,
    ACTIVE_FOLIO_ALPHABET_V1_SPLITS,
    STARTER_ALPHABET_V1_GLYPHS,
    STARTER_ALPHABET_V1_JOINS,
    STARTER_ALPHABET_V1_JOIN_SCHEDULES,
    STARTER_ALPHABET_V1_PATH,
    STARTER_ALPHABET_V1_REQUIRED_SYMBOLS,
    STARTER_ALPHABET_V1_SPLITS,
    build_active_folio_alphabet_v1_confidence_manifest,
    build_active_folio_alphabet_v1_guides,
    build_active_folio_inventory_report,
    build_active_folio_review_inventory,
    build_starter_alphabet_v1_confidence_manifest,
    build_starter_alphabet_v1_guides,
    build_starter_dataset_report,
    load_active_folio_alphabet_v1_guides,
    load_starter_alphabet_v1_guides,
    validate_dense_path_guide,
    write_dataset_report_bundle,
    write_active_folio_inventory_report_bundle,
    write_guide_overlay_snapshot,
    write_pathguides_toml,
    write_snapshot_panel,
)


def test_build_starter_alphabet_v1_guides_contains_expected_symbols():
    guides = build_starter_alphabet_v1_guides()
    assert set(guides) == set(STARTER_ALPHABET_V1_REQUIRED_SYMBOLS)

    for symbol in STARTER_ALPHABET_V1_REQUIRED_SYMBOLS:
        assert not validate_dense_path_guide(guides[symbol]), symbol
        assert guides[symbol].sources[0].split == STARTER_ALPHABET_V1_SPLITS[symbol]

    assert guides["a"].sources[0].source_path == "shared/hands/guides_extracted.toml"
    assert any(not sample.contact for sample in guides["r->space"].samples)
    assert any(not sample.contact for sample in guides["space->d"].samples)


def test_build_active_folio_review_inventory_matches_committed_character_set():
    assert build_active_folio_review_inventory() == tuple(sorted(ACTIVE_FOLIO_ALPHABET_V1_GLYPHS))


def test_build_active_folio_alphabet_v1_guides_contains_expected_symbols():
    guides = build_active_folio_alphabet_v1_guides()
    assert set(guides) == set(ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS)

    for symbol in ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS:
        assert not validate_dense_path_guide(guides[symbol]), symbol
        assert guides[symbol].sources[0].split == ACTIVE_FOLIO_ALPHABET_V1_SPLITS[symbol]

    assert guides["H"].sources[0].source_path == ACTIVE_FOLIO_ALPHABET_V1_PATH.as_posix()
    assert guides["E"].sources[0].source_path == ACTIVE_FOLIO_ALPHABET_V1_PATH.as_posix()
    assert any(not sample.contact for sample in guides["ů"].samples)


def test_build_starter_alphabet_v1_confidence_manifest_records_source_modes():
    manifest = build_starter_alphabet_v1_confidence_manifest()

    assert manifest["a"]["source_mode"] == "automatic"
    assert manifest["u"]["source_mode"] == "legacy_fallback"
    assert manifest["space->d"]["contact_schedule"] == "lift_then_contact"
    assert manifest["m"]["counts"]["accepted"] == 1


def test_build_active_folio_alphabet_v1_confidence_manifest_records_source_modes():
    manifest = build_active_folio_alphabet_v1_confidence_manifest()

    assert manifest["H"]["source_mode"] == "capital_exact"
    assert manifest["s"]["source_mode"] == "curated_fallback"
    assert manifest["ů"]["source_mode"] == "curated_variant"
    assert manifest["z"]["counts"]["accepted"] == 1


def test_starter_dataset_report_passes_validation_and_policy():
    guides = build_starter_alphabet_v1_guides()
    report = build_starter_dataset_report(
        guides,
        required_symbols=STARTER_ALPHABET_V1_REQUIRED_SYMBOLS,
        join_schedules=STARTER_ALPHABET_V1_JOIN_SCHEDULES,
    )

    assert report.gate.passed is True
    assert report.dataset_policy_passed is True
    assert report.metrics["required_symbol_coverage"] == 1.0
    assert report.metrics["heldout_symbol_coverage"] >= 0.20


def test_active_folio_dataset_report_passes_validation_and_coverage():
    guides = build_active_folio_alphabet_v1_guides()
    report = build_starter_dataset_report(
        guides,
        required_symbols=ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS,
        join_schedules={},
    )
    coverage = build_active_folio_inventory_report(
        guides,
        required_symbols=ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS,
        review_folios=ACTIVE_FOLIO_ALPHABET_V1_REVIEW_FOLIOS,
    )

    assert report.gate.passed is True
    assert report.dataset_policy_passed is True
    assert report.metrics["required_symbol_coverage"] == 1.0
    assert report.metrics["join_schedule_ratio"] == 1.0
    assert coverage["exact_character_coverage"] == 1.0
    assert coverage["missing_symbols"] == []


def test_starter_dataset_review_artifacts_are_written(tmp_path):
    guides = build_starter_alphabet_v1_guides()
    snapshot_dir = tmp_path / "snapshots"
    image_paths = []
    for symbol in ("u", "a", "i->n", "space->d"):
        image_paths.append(write_guide_overlay_snapshot(guides[symbol], snapshot_dir / f"{symbol}.png"))

    panel_path = write_snapshot_panel(image_paths, tmp_path / "panel.png")
    report = build_starter_dataset_report(
        guides,
        required_symbols=STARTER_ALPHABET_V1_REQUIRED_SYMBOLS,
        join_schedules=STARTER_ALPHABET_V1_JOIN_SCHEDULES,
    )
    json_path, markdown_path = write_dataset_report_bundle(report, tmp_path)

    assert panel_path.exists()
    assert json_path.exists()
    assert markdown_path.exists()


def test_active_folio_review_artifacts_are_written(tmp_path):
    guides = build_active_folio_alphabet_v1_guides()
    snapshot_dir = tmp_path / "snapshots"
    image_paths = []
    for symbol in ACTIVE_FOLIO_ALPHABET_V1_NEW_GLYPHS:
        image_paths.append(write_guide_overlay_snapshot(guides[symbol], snapshot_dir / f"{symbol}.png"))

    panel_path = write_snapshot_panel(image_paths, tmp_path / "panel.png")
    report = build_active_folio_inventory_report(
        guides,
        required_symbols=ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS,
        review_folios=ACTIVE_FOLIO_ALPHABET_V1_REVIEW_FOLIOS,
    )
    json_path, markdown_path = write_active_folio_inventory_report_bundle(report, tmp_path)

    assert panel_path.exists()
    assert json_path.exists()
    assert markdown_path.exists()


def test_load_starter_alphabet_v1_from_committed_assets():
    guides = load_starter_alphabet_v1_guides()
    assert set(guides) == set(STARTER_ALPHABET_V1_REQUIRED_SYMBOLS)
    assert not validate_dense_path_guide(guides["m"])
    assert guides["a"].sources[0].split == "validation"
    assert guides["space->d"].sources[0].split == "test"


def test_load_active_folio_alphabet_v1_from_committed_assets():
    guides = load_active_folio_alphabet_v1_guides()
    assert set(guides) == set(ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS)
    assert not validate_dense_path_guide(guides["s"])
    assert guides["H"].sources[0].split == "validation"
    assert guides["E"].sources[0].split == "test"


def test_committed_starter_alphabet_v1_manifests_align_with_dataset():
    manifest_path = Path("shared/training/handsim/starter_alphabet_v1/manifest.toml")
    confidence_path = Path("shared/training/handsim/starter_alphabet_v1/confidence_manifest.toml")
    report_path = Path("shared/training/handsim/starter_alphabet_v1/validation_report.json")
    snapshot_panel = Path("shared/training/handsim/starter_alphabet_v1/snapshots/panel.png")

    manifest = tomllib.loads(manifest_path.read_text())
    confidence = tomllib.loads(confidence_path.read_text())
    report = json.loads(report_path.read_text())

    assert manifest["dataset_id"] == "starter-alphabet-v1"
    assert set(manifest["glyphs"]) == set(STARTER_ALPHABET_V1_GLYPHS)
    assert set(manifest["joins"]) == set(STARTER_ALPHABET_V1_JOINS)
    assert manifest["proof_words"]["validation"] == ["in", "mir"]
    assert confidence["symbols"]["a"]["source_mode"] == "automatic"
    assert confidence["symbols"]["space->d"]["contact_schedule"] == "lift_then_contact"
    assert snapshot_panel.exists()
    assert report_path.exists()
    assert report["gate"]["passed"] is True


def test_committed_active_folio_alphabet_v1_manifests_align_with_dataset():
    manifest_path = Path("shared/training/handsim/active_folio_alphabet_v1/manifest.toml")
    confidence_path = Path("shared/training/handsim/active_folio_alphabet_v1/confidence_manifest.toml")
    report_path = Path("shared/training/handsim/active_folio_alphabet_v1/validation_report.json")
    coverage_path = Path("shared/training/handsim/active_folio_alphabet_v1/coverage_report.json")
    snapshot_panel = Path("shared/training/handsim/active_folio_alphabet_v1/snapshots/panel.png")

    manifest = tomllib.loads(manifest_path.read_text())
    confidence = tomllib.loads(confidence_path.read_text())
    report = json.loads(report_path.read_text())
    coverage = json.loads(coverage_path.read_text())

    assert manifest["dataset_id"] == "active-folio-alphabet-v1"
    assert set(manifest["glyphs"]) == set(ACTIVE_FOLIO_ALPHABET_V1_GLYPHS)
    assert set(manifest["new_glyphs"]) == set(ACTIVE_FOLIO_ALPHABET_V1_NEW_GLYPHS)
    assert manifest["proof_words"]["test"] == ["bůch", "Eckehart", "daz", "volkommenheit"]
    assert confidence["symbols"]["H"]["source_mode"] == "capital_exact"
    assert confidence["symbols"]["ů"]["source_mode"] == "curated_variant"
    assert snapshot_panel.exists()
    assert report_path.exists()
    assert report["gate"]["passed"] is True
    assert coverage["exact_character_coverage"] == 1.0


def test_committed_starter_alphabet_v1_roundtrip_matches_builder(tmp_path):
    built = build_starter_alphabet_v1_guides()
    output_path = tmp_path / "starter_alphabet_v1.toml"
    write_pathguides_toml(built, output_path)
    loaded = load_starter_alphabet_v1_guides(output_path)

    assert set(loaded) == set(STARTER_ALPHABET_V1_REQUIRED_SYMBOLS)
    assert math.isclose(loaded["m"].x_advance_mm, built["m"].x_advance_mm, rel_tol=0.0, abs_tol=1e-6)


def test_committed_active_folio_alphabet_v1_roundtrip_matches_builder(tmp_path):
    built = build_active_folio_alphabet_v1_guides()
    output_path = tmp_path / "active_folio_alphabet_v1.toml"
    write_pathguides_toml(built, output_path)
    loaded = load_active_folio_alphabet_v1_guides(output_path)

    assert set(loaded) == set(ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS)
    assert math.isclose(loaded["z"].x_advance_mm, built["z"].x_advance_mm, rel_tol=0.0, abs_tol=1e-6)
