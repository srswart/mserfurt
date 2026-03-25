"""Integration coverage for TD-014 folio rollout validation."""

from __future__ import annotations

import json
from pathlib import Path

from scribesim.handvalidate.folio_bench import (
    load_folio_bench_manifest,
    run_folio_regression_bench,
)


GOLDEN_F01R = Path(__file__).parent / "golden" / "f01r" / "folio.json"


def test_load_folio_bench_manifest_from_committed_asset():
    manifest = load_folio_bench_manifest()

    assert manifest.stage_id == "folio"
    assert manifest.checkpoint_id == "guided-folio-ab-v1"
    assert len(manifest.cases) == 4
    assert any(case.name == "fatigue" for case in manifest.cases)


def test_run_folio_regression_bench_writes_dashboard_and_decision(tmp_path: Path):
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(
        """
schema_version = 1
stage_id = "folio"
checkpoint_id = "test-guided-folio-ab"
word_line_manifest_path = "shared/training/handsim/word_line/manifest.toml"
word_line_candidate_name = "line_v1_tuned"
weather_profile_path = "shared/profiles/ms-erfurt-560yr.toml"
guided_supersample = 4
proof_dpi = 180
proof_supersample = 2
dt = 0.002
evo_quality = "balanced"
evo_evolve = false

[[cases]]
name = "clean_baseline"
folio_id = "f01r"
folio_path = "tests/golden/f01r/folio.json"
description = "Trimmed regression slice."
line_limit = 1
""".strip()
        + "\n"
    )

    result = run_folio_regression_bench(tmp_path / "out", manifest_path=manifest_path)

    dashboard = json.loads((tmp_path / "out" / "dashboard.json").read_text())
    decision = json.loads((tmp_path / "out" / "promotion_decision.json").read_text())
    case_dir = tmp_path / "out" / "clean_baseline"

    assert result.manifest.checkpoint_id == "test-guided-folio-ab"
    assert dashboard["summary_metrics"]["deterministic_pass_rate"] == 1.0
    assert "organicness_win_rate" in dashboard["summary_metrics"]
    assert "exact_character_coverage" in dashboard["summary_metrics"]
    assert "alias_substitution_count" in dashboard["summary_metrics"]
    assert decision["checkpoint_id"] == "test-guided-folio-ab"
    assert (tmp_path / "out" / "dashboard.md").exists()
    assert (tmp_path / "out" / "folio.json").exists()
    assert (tmp_path / "out" / "folio.md").exists()
    assert (case_dir / "panel.png").exists()
    assert (case_dir / "page.xml").exists()
    assert (case_dir / "summary.json").exists()
    assert (case_dir / "guided_aligned.png").exists()
    assert (case_dir / "guided_actual_vs_aligned_diff.png").exists()
    case_summary = json.loads((case_dir / "summary.json").read_text())
    assert case_summary["alias_substitution_count"] == 0.0
    assert case_summary["exact_character_coverage"] == 1.0
    assert case_summary["resolution_status"] == "exact"
    assert case_summary["guided_render_trajectory_mode"] == "actual"
