"""Tests for TD-014 primitive curriculum promotion."""

from __future__ import annotations

import json

from scribesim.curriculum import (
    DEFAULT_GLYPH_JOIN_MANIFEST_PATH,
    DEFAULT_PRIMITIVE_MANIFEST_PATH,
    DEFAULT_WORD_LINE_MANIFEST_PATH,
    load_glyph_join_manifest,
    load_primitive_manifest,
    load_word_line_manifest,
    run_glyph_join_curriculum,
    run_primitive_curriculum,
    run_word_line_curriculum,
)


def test_load_primitive_manifest_from_committed_asset():
    manifest = load_primitive_manifest()

    assert manifest.stage_id == "primitive"
    assert manifest.checkpoint_id == "primitive-v1"
    assert "downstroke" in manifest.exercises
    assert "minim_pair" in manifest.exercises
    assert len(manifest.candidates) >= 2


def test_run_primitive_curriculum_writes_checkpoint_and_artifacts(tmp_path):
    result = run_primitive_curriculum(tmp_path, manifest_path=DEFAULT_PRIMITIVE_MANIFEST_PATH)

    assert result.passed is True
    assert result.selected_candidate is not None
    assert result.checkpoint_path is not None

    checkpoint_path = tmp_path / "checkpoints" / "primitive-v1" / "checkpoint.json"
    summary_path = tmp_path / "curriculum_summary.json"
    dataset_path = tmp_path / "dataset_summary.json"

    assert checkpoint_path.exists()
    assert summary_path.exists()
    assert dataset_path.exists()
    payload = json.loads(checkpoint_path.read_text())
    assert payload["checkpoint_id"] == "primitive-v1"
    assert payload["passed"] is True

    for candidate_name in {"baseline", "primitive_v1_tuned"}:
        candidate_dir = tmp_path / "candidates" / candidate_name
        assert candidate_dir.exists()
        assert (candidate_dir / "snapshot_panel.png").exists()


def test_load_glyph_join_manifest_from_committed_asset():
    manifest = load_glyph_join_manifest()

    assert manifest.stage_id == "glyph_join"
    assert manifest.checkpoint_id == "glyph-join-v1"
    assert "a" in manifest.promotion_glyphs
    assert "space->d" in manifest.promotion_joins
    assert manifest.primitive_candidate_name == "primitive_v1_tuned"
    assert len(manifest.candidates) >= 2


def test_run_glyph_join_curriculum_writes_checkpoint_and_reports(tmp_path):
    result = run_glyph_join_curriculum(tmp_path, manifest_path=DEFAULT_GLYPH_JOIN_MANIFEST_PATH)

    assert result.passed is True
    assert result.selected_candidate is not None
    assert result.checkpoint_path is not None

    checkpoint_path = tmp_path / "checkpoints" / "glyph-join-v1" / "checkpoint.json"
    summary_path = tmp_path / "curriculum_summary.json"
    dataset_path = tmp_path / "dataset_summary.json"

    assert checkpoint_path.exists()
    assert summary_path.exists()
    assert dataset_path.exists()
    payload = json.loads(checkpoint_path.read_text())
    assert payload["checkpoint_id"] == "glyph-join-v1"
    assert payload["passed"] is True

    for candidate_name in {"primitive_transfer", "glyph_join_v1_tuned"}:
        candidate_dir = tmp_path / "candidates" / candidate_name
        assert candidate_dir.exists()
        assert (candidate_dir / "recognition_summary.json").exists()
        assert (candidate_dir / "join_continuity_report.json").exists()
        assert (candidate_dir / "good_examples_panel.png").exists()
        assert (candidate_dir / "bad_examples_panel.png").exists()


def test_load_word_line_manifest_from_committed_asset():
    manifest = load_word_line_manifest()

    assert manifest.stage_id == "word_line"
    assert manifest.checkpoint_id == "line-v1"
    assert "und" in manifest.proof_entries
    assert "und der wir" in manifest.promotion_lines
    assert manifest.glyph_join_candidate_name == "glyph_join_v1_tuned"
    assert len(manifest.candidates) >= 2


def test_run_word_line_curriculum_writes_checkpoint_and_reports(tmp_path):
    result = run_word_line_curriculum(tmp_path, manifest_path=DEFAULT_WORD_LINE_MANIFEST_PATH)

    assert result.passed is True
    assert result.selected_candidate is not None
    assert result.checkpoint_path is not None

    checkpoint_path = tmp_path / "checkpoints" / "line-v1" / "checkpoint.json"
    summary_path = tmp_path / "curriculum_summary.json"
    dataset_path = tmp_path / "dataset_summary.json"

    assert checkpoint_path.exists()
    assert summary_path.exists()
    assert dataset_path.exists()
    payload = json.loads(checkpoint_path.read_text())
    assert payload["checkpoint_id"] == "line-v1"
    assert payload["passed"] is True

    for candidate_name in {"glyph_join_transfer", "line_v1_tuned"}:
        candidate_dir = tmp_path / "candidates" / candidate_name
        assert candidate_dir.exists()
        assert (candidate_dir / "proof_line_panel.png").exists()
        assert (candidate_dir / "evo_baseline_report.json").exists()
        assert (candidate_dir / "proof_vocabulary_panel.png").exists()
