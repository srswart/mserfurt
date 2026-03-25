"""Integration tests for TD-014 gate and dataset policy evaluation."""

from __future__ import annotations

from scribesim.handvalidate import GateDecision, evaluate_dataset_policy, evaluate_gate
from scribesim.pathguide import load_starter_proof_guides


def test_primitive_gate_passes_for_known_good_metrics():
    decision = evaluate_gate(
        "primitive",
        {
            "corridor_containment": 0.99,
            "self_intersections": 0.0,
            "contact_accuracy": 1.0,
            "width_profile_error": 0.05,
        },
    )

    assert isinstance(decision, GateDecision)
    assert decision.passed is True
    assert not decision.failures


def test_primitive_gate_fails_and_reports_reasons():
    decision = evaluate_gate(
        "primitive",
        {
            "corridor_containment": 0.80,
            "self_intersections": 2.0,
            "contact_accuracy": 0.95,
            "width_profile_error": 0.30,
        },
    )

    assert decision.passed is False
    assert len(decision.failures) == 4
    assert any("corridor_containment" in failure.reason for failure in decision.failures)


def test_promotion_dataset_policy_requires_accepted_tier_and_heldout_coverage():
    guides = list(load_starter_proof_guides().values())
    decision = evaluate_dataset_policy(guides, policy_name="promotion")

    assert decision.passed is False
    assert any("heldout_symbol_coverage" in reason for reason in decision.reasons)
