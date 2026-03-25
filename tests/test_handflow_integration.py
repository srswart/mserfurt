"""Integration coverage for TD-014 handflow plus validation."""

from __future__ import annotations

from scribesim.hand.profile import HandProfile
from scribesim.handflow import GuidedHandFlowController, build_primitive_proof_guides, run_stateful_word_proof
from scribesim.handvalidate import (
    contact_accuracy,
    corridor_containment_ratio,
    evaluate_gate,
    self_intersection_count,
)


def test_primitive_controller_metrics_feed_gate_evaluation():
    profile = HandProfile()
    profile.letterform.x_height_mm = 3.5
    controller = GuidedHandFlowController(profile)
    guide = build_primitive_proof_guides()["downstroke"]
    result = controller.simulate_guide(guide, dt=0.002)

    metrics = {
        "corridor_containment": corridor_containment_ratio(result.trajectory, guide),
        "self_intersections": float(self_intersection_count(result.trajectory)),
        "contact_accuracy": contact_accuracy(result.trajectory, guide),
        "width_profile_error": 0.10,
    }
    decision = evaluate_gate("primitive", metrics)

    assert decision.passed is True
    assert not decision.failures


def test_stateful_word_session_feeds_word_gate_evaluation(tmp_path):
    profile = HandProfile()
    profile.letterform.x_height_mm = 3.5
    profile.dynamics.position_gain = 26.0
    profile.dynamics.velocity_gain = 10.0
    profile.dynamics.max_speed = 30.0
    profile.dynamics.max_acceleration = 540.0
    reports = run_stateful_word_proof(tmp_path, profile=profile, dpi=180, supersample=2)

    assert reports["und"].gate.passed is True
