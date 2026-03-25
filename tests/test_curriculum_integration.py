"""Integration tests for primitive curriculum and gate enforcement."""

from __future__ import annotations

import json

from scribesim.curriculum import (
    DEFAULT_GLYPH_JOIN_MANIFEST_PATH,
    DEFAULT_PRIMITIVE_MANIFEST_PATH,
    DEFAULT_WORD_LINE_MANIFEST_PATH,
    run_glyph_join_curriculum,
    run_primitive_curriculum,
    run_word_line_curriculum,
)


def test_curriculum_summary_records_dataset_policy_and_candidates(tmp_path):
    result = run_primitive_curriculum(tmp_path, manifest_path=DEFAULT_PRIMITIVE_MANIFEST_PATH)

    assert result.passed is True
    summary = json.loads((tmp_path / "curriculum_summary.json").read_text())
    assert summary["dataset_policy"]["passed"] is True
    assert len(summary["candidates"]) >= 2
    assert any(candidate["passed"] for candidate in summary["candidates"])


def test_glyph_join_summary_records_heldout_promotion_and_candidates(tmp_path):
    result = run_glyph_join_curriculum(tmp_path, manifest_path=DEFAULT_GLYPH_JOIN_MANIFEST_PATH)

    assert result.passed is True
    summary = json.loads((tmp_path / "curriculum_summary.json").read_text())
    assert summary["dataset_policy"]["passed"] is True
    assert summary["dataset_policy"]["accepted_tier_only"] is True
    assert set(summary["dataset_policy"]["promotion_symbols"]) == {"a", "i", "o", "h", "i->n", "m->i", "r->space", "space->d"}
    assert len(summary["candidates"]) >= 2
    assert any(candidate["passed"] for candidate in summary["candidates"])


def test_word_line_summary_records_line_gates_and_baseline_comparison(tmp_path):
    result = run_word_line_curriculum(tmp_path, manifest_path=DEFAULT_WORD_LINE_MANIFEST_PATH)

    assert result.passed is True
    summary = json.loads((tmp_path / "curriculum_summary.json").read_text())
    assert summary["dataset_policy"]["passed"] is True
    assert summary["dataset_policy"]["accepted_tier_only"] is True
    assert "und der wir in mir und der wir" in summary["dataset_policy"]["promotion_lines"]
    assert len(summary["candidates"]) >= 2
    assert any(candidate["passed"] for candidate in summary["candidates"])
