"""Unit and CLI tests for ADV-SS-ANNOTATE-007: Human-Eyes Review Board
(`scribesim review-sheet`), 4-question rubric, quick-tag-to-parameter mapping,
and Human Checkpoint #1 board generation.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
import pytest

from scribesim.annotate.review_board import (
    CHECKPOINT_1_SPECIMENS,
    RUBRIC_QUESTIONS,
    build_review_sheet,
    map_quick_tags_to_parameters,
)
from scribesim.cli import main
from scribesim.handvalidate.review_gate import (
    save_human_review,
    validate_human_review,
)


def test_quick_tag_to_parameter_mapping() -> None:
    """Quick-tags selected by a human reviewer map directly to actionable parameter adjustments."""
    recs = map_quick_tags_to_parameters(["too_wide_gap", "abrupt_shoulder", "nib_too_thin"])
    assert len(recs) == 3
    by_tag = {r["tag"]: r for r in recs}

    assert by_tag["too_wide_gap"]["parameter_group"] == "guides"
    assert "advance_wnib" in by_tag["too_wide_gap"]["field"]
    assert by_tag["abrupt_shoulder"]["parameter_group"] == "handflow"
    assert "sigma" in by_tag["abrupt_shoulder"]["field"]
    assert by_tag["nib_too_thin"]["parameter_group"] == "hand"
    assert "width_mm" in by_tag["nib_too_thin"]["field"]


def test_build_review_sheet_checkpoint_1(tmp_path: Path) -> None:
    """`build_review_sheet` generates the 3-way comparison board and Tier-1 badges for Checkpoint #1."""
    out_dir = tmp_path / "checkpoint_1_board"
    manifest = build_review_sheet(
        stage_id="checkpoint-1-coarticulation",
        specimens=CHECKPOINT_1_SPECIMENS,
        out_dir=out_dir,
        dpi=160,
    )

    assert manifest["stage_id"] == "checkpoint-1-coarticulation"
    assert len(manifest["specimens"]) == len(CHECKPOINT_1_SPECIMENS)
    assert manifest["tier1_summary"]["a1_all_passed"] is True
    assert manifest["tier1_summary"]["a2_all_passed"] is True
    assert manifest["tier1_summary"]["a3_coarticulate"]["passed"] is True

    html_text = (out_dir / "index.html").read_text(encoding="utf-8")
    for q in RUBRIC_QUESTIONS:
        assert q["id"] in html_text
    assert "checkpoint-1-coarticulation" in html_text
    assert (out_dir / "board_manifest.json").exists()


def test_save_and_validate_human_review_gate(tmp_path: Path) -> None:
    """Saved human review JSON validates 4-question rubric, candidate hash, and quick-tag actions."""
    board_dir = tmp_path / "board"
    manifest = build_review_sheet(
        stage_id="checkpoint-1-coarticulation",
        specimens=("nu", "und"),
        out_dir=board_dir,
        dpi=150,
    )

    review_path = tmp_path / "checkpoint-1-coarticulation-review.json"
    record = save_human_review(
        review_path,
        stage_id="checkpoint-1-coarticulation",
        candidate_sha256=manifest["candidate_sha256"],
        reviewer="shawn",
        answers={
            "join_ductus_flow": "pass",
            "bastarda_script_identity": "pass",
            "organic_hand_variation": "pass",
        },
        overall_stage_verdict="promote_checkpoint",
        quick_tags=["missing_foot_turn"],
        notes="Coarticulated nu and und flow cleanly at 40 degrees.",
    )

    verdict = validate_human_review(
        review_path,
        expected_stage_id="checkpoint-1-coarticulation",
        expected_candidate_sha256=manifest["candidate_sha256"],
    )
    assert verdict["valid"] is True
    assert verdict["promoted"] is True
    assert len(record["parameter_recommendations"]) == 1


def test_review_sheet_cli_command(tmp_path: Path) -> None:
    """`scribesim review-sheet` CLI generates the Checkpoint #1 board and manifest."""
    out_dir = tmp_path / "cli_board"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "review-sheet",
            "--stage",
            "checkpoint-1-coarticulation",
            "--out-dir",
            str(out_dir),
            "--dpi",
            "150",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out_dir / "index.html").exists()
    manifest = json.loads((out_dir / "board_manifest.json").read_text())
    assert manifest["stage_id"] == "checkpoint-1-coarticulation"
