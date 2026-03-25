"""Tests for TD-014 hand validation metrics and report generation."""

from __future__ import annotations

import json

import numpy as np

from scribesim.handvalidate import (
    GateDecision,
    StageReport,
    baseline_drift_ratio,
    contact_accuracy,
    corridor_containment_ratio,
    curvature_histogram_distance,
    dataset_admission_metrics,
    dtw_centerline_distance,
    exemplar_cluster_consistency,
    exemplar_cluster_separation,
    exemplar_competitor_margin,
    exemplar_template_score,
    exit_tangent_error_deg,
    ink_state_determinism,
    ink_state_monotonicity,
    load_dataset_policy,
    load_gate_config,
    normalized_hausdorff_distance,
    occupancy_balance_score,
    self_intersection_count,
    stage_report_markdown,
    template_score,
    thick_thin_ratio_error,
    trajectory_from_guide,
    uncontrolled_exit_count,
    width_profile_error,
    write_stage_report,
)
from scribesim.handvalidate.folio_bench import DEFAULT_FOLIO_BENCH_MANIFEST_PATH
from scribesim.pathguide import DensePathGuide, GuideSample, GuideSource, load_starter_proof_guides


def _simple_guide() -> DensePathGuide:
    return DensePathGuide(
        symbol="stroke",
        kind="glyph",
        samples=(
            GuideSample(0.0, 0.0, 1.0, 0.0, contact=True, pressure_nominal=0.40, corridor_half_width_mm=0.20),
            GuideSample(0.2, 0.0, 1.0, 0.0, contact=True, pressure_nominal=0.45, corridor_half_width_mm=0.20),
            GuideSample(0.4, 0.0, 1.0, 0.0, contact=True, pressure_nominal=0.50, corridor_half_width_mm=0.20),
            GuideSample(0.6, 0.0, 1.0, 0.0, contact=True, pressure_nominal=0.55, corridor_half_width_mm=0.20),
        ),
        x_advance_mm=0.6,
        x_height_mm=3.5,
        entry_tangent=(1.0, 0.0),
        exit_tangent=(1.0, 0.0),
        sources=(
            GuideSource(
                source_id="stroke-train",
                confidence_tier="accepted",
                split="train",
                source_resolution_ppmm=12.0,
            ),
        ),
    )


def _crossing_trajectory():
    from scribesim.handvalidate import TrajectorySample

    return (
        TrajectorySample(0.0, 0.0),
        TrajectorySample(0.6, 0.6),
        TrajectorySample(0.0, 0.6),
        TrajectorySample(0.6, 0.0),
    )


def test_core_path_metrics_accept_nominal_guide():
    guide = _simple_guide()
    observed = trajectory_from_guide(guide, width_scale_mm=1.0)

    assert corridor_containment_ratio(observed, guide) == 1.0
    assert contact_accuracy(observed, guide) == 1.0
    assert dtw_centerline_distance(observed, guide) == 0.0
    assert curvature_histogram_distance(observed, guide) == 0.0
    assert normalized_hausdorff_distance(observed, guide) == 0.0
    assert baseline_drift_ratio(observed, x_height_mm=guide.x_height_mm) == 0.0
    assert exit_tangent_error_deg(observed, guide) == 0.0
    assert width_profile_error(
        [sample.width_mm for sample in observed],
        [sample.pressure_nominal for sample in guide.samples],
    ) == 0.0


def test_self_intersection_count_detects_crossing_path():
    assert self_intersection_count(_crossing_trajectory()) == 1


def test_template_score_rewards_identical_images():
    img = np.full((32, 32, 3), 255, dtype=np.uint8)
    img[10:22, 14:18, :] = 0

    assert template_score(img, img) == 1.0


def test_dataset_admission_metrics_summarize_tiers_and_resolution():
    starter_guides = load_starter_proof_guides()
    metrics = dataset_admission_metrics([_simple_guide(), *starter_guides.values()])

    assert metrics["accepted_count"] >= 10
    assert metrics["soft_accepted_count"] == 0
    assert metrics["min_source_resolution_ppmm"] > 0.0


def test_load_configs_from_committed_assets():
    gates = load_gate_config()
    policies = load_dataset_policy()

    assert "primitive" in gates
    assert "join" in gates
    assert "stateful_word" in gates
    assert "folio" in gates
    assert "exemplar_promotion_glyph" in gates
    assert "exemplar_promotion_join" in gates
    assert any(rule.metric == "organicness_win_rate" for rule in gates["folio"].rules)
    assert "promotion" in policies
    assert policies["promotion"].allowed_confidence_tiers == ("accepted",)
    assert DEFAULT_FOLIO_BENCH_MANIFEST_PATH.exists()


def test_uncontrolled_exit_and_thick_thin_ratio_accept_nominal_path():
    guide = _simple_guide()
    observed = trajectory_from_guide(guide, width_scale_mm=1.0)

    assert uncontrolled_exit_count(observed, guide) == 0
    assert thick_thin_ratio_error(
        [sample.width_mm for sample in observed],
        [sample.pressure_nominal for sample in guide.samples],
    ) == 0.0


def test_ink_state_metrics_reward_monotonic_and_identical_sequences():
    levels = [1.0, 0.98, 0.93, 0.90]

    assert ink_state_monotonicity(levels) == 1.0
    assert ink_state_determinism(levels, levels) == 1.0


def test_exemplar_promotion_metrics_reject_black_blocks_and_reward_true_symbol():
    from scribesim.refextract.corpus import build_symbol_template_bank

    template_bank = build_symbol_template_bank(required_symbols=("u", "n"))
    u_image = template_bank["u"][0]
    n_image = template_bank["n"][0]
    centroids = {"u": u_image, "n": n_image}
    black_block = np.zeros((64, 64), dtype=np.uint8)

    assert exemplar_template_score(u_image, "u", template_bank) >= 0.9
    assert exemplar_competitor_margin(u_image, "u", template_bank) > 0.0
    assert exemplar_cluster_consistency(u_image, centroids["u"]) >= 0.9
    assert exemplar_cluster_separation(u_image, "u", centroids) > 0.0
    assert occupancy_balance_score(black_block) == 0.0


def test_write_stage_report_emits_json_and_markdown(tmp_path):
    report = StageReport(
        stage="primitive",
        metrics={"corridor_containment": 1.0, "self_intersections": 0.0},
        gate=GateDecision(stage="primitive", passed=True),
        notes=("starter proof",),
    )

    json_path, markdown_path = write_stage_report(report, tmp_path)
    payload = json.loads(json_path.read_text())

    assert json_path.exists()
    assert markdown_path.exists()
    assert payload["stage"] == "primitive"
    assert "TD-014 Validation Report" in markdown_path.read_text()
    assert "corridor_containment" in stage_report_markdown(report)
