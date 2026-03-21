"""Unit tests for CMA-ES group optimizer — ADV-SS-CMAES-001."""

from __future__ import annotations

import pytest

from scribesim.hand.profile import HandProfile, NibParams, FolioParams
from scribesim.tuning.cmaes_optimizer import (
    ParameterGroup,
    CMAESGroupOptimizer,
    PARAMETER_GROUPS,
    QualityGate,
    parse_gates,
    run_staged_optimization,
)


# ---------------------------------------------------------------------------
# Synthetic objective (same quadratic as test_optimizer.py)
# ---------------------------------------------------------------------------

def _quadratic_objective(profile: HandProfile) -> tuple[float, dict[str, float]]:
    angle = profile.nib.angle_deg
    pressure = profile.folio.base_pressure
    dist = (angle - 40.0) ** 2 / 100.0 + (pressure - 0.7) ** 2
    return dist, {"M1": abs(angle - 40.0) / 30.0, "M2": abs(pressure - 0.7)}


# ---------------------------------------------------------------------------
# TestParameterGroup
# ---------------------------------------------------------------------------

class TestParameterGroup:
    def test_nib_physics_group_exists(self):
        assert "nib_physics" in PARAMETER_GROUPS

    def test_baseline_geometry_group_exists(self):
        assert "baseline_geometry" in PARAMETER_GROUPS

    def test_extract_values(self):
        group = PARAMETER_GROUPS["nib_physics"]
        profile = HandProfile()
        values = group.extract(profile)
        assert len(values) == len(group.parameters)
        assert all(isinstance(v, (int, float)) for v in values)

    def test_ranges_correct_length(self):
        group = PARAMETER_GROUPS["nib_physics"]
        lowers, uppers = group.ranges()
        assert len(lowers) == len(group.parameters)
        assert len(uppers) == len(group.parameters)
        for lo, hi in zip(lowers, uppers):
            assert lo < hi


# ---------------------------------------------------------------------------
# TestCMAESGroupOptimizer
# ---------------------------------------------------------------------------

class TestCMAESGroupOptimizer:
    def test_reduces_distance(self):
        """CMA-ES should find better nib params on the quadratic objective."""
        group = ParameterGroup(
            name="test_nib", description="test",
            parameters=["nib.angle_deg"],
            target_metrics=["M1"],
        )
        profile = HandProfile(nib=NibParams(angle_deg=50.0))
        optimizer = CMAESGroupOptimizer(group, max_iterations=15)
        fitted = optimizer.run(profile, _quadratic_objective)

        initial_dist, _ = _quadratic_objective(profile)
        final_dist, _ = _quadratic_objective(fitted)
        assert final_dist < initial_dist

    def test_log_populated(self):
        group = ParameterGroup(
            name="test", description="test",
            parameters=["nib.angle_deg"],
            target_metrics=["M1"],
        )
        profile = HandProfile(nib=NibParams(angle_deg=50.0))
        optimizer = CMAESGroupOptimizer(group, max_iterations=10)
        optimizer.run(profile, _quadratic_objective)
        # CMA-ES evaluates popsize candidates per generation; at least some logged
        assert len(optimizer.log) >= 1

    def test_multi_param_group(self):
        """Test with multiple correlated parameters."""
        group = ParameterGroup(
            name="test_multi", description="test",
            parameters=["nib.angle_deg", "folio.base_pressure"],
            target_metrics=["M1", "M2"],
        )
        profile = HandProfile(
            nib=NibParams(angle_deg=50.0),
            folio=FolioParams(base_pressure=0.9),
        )
        optimizer = CMAESGroupOptimizer(group, max_iterations=20)
        fitted = optimizer.run(profile, _quadratic_objective)

        initial_dist, _ = _quadratic_objective(profile)
        final_dist, _ = _quadratic_objective(fitted)
        assert final_dist < initial_dist


# ---------------------------------------------------------------------------
# TestQualityGates
# ---------------------------------------------------------------------------

class TestQualityGates:
    def test_parse_gates(self):
        gates = parse_gates("M1<0.15,M2<0.20")
        assert len(gates) == 2
        assert gates[0].metric_id == "M1"
        assert gates[0].threshold == 0.15

    def test_gate_passes(self):
        gate = QualityGate("M1", 0.15)
        assert gate.passes(0.10)
        assert not gate.passes(0.20)

    def test_gate_boundary(self):
        gate = QualityGate("M1", 0.15)
        assert gate.passes(0.15)  # exactly at threshold = passes


# ---------------------------------------------------------------------------
# TestStagedOptimization
# ---------------------------------------------------------------------------

class TestStagedOptimization:
    def test_staged_returns_profile_and_log(self):
        profile = HandProfile(nib=NibParams(angle_deg=50.0))
        fitted, log = run_staged_optimization(
            profile, _quadratic_objective,
            groups=["nib_physics"],
            max_iterations=5,
        )
        assert isinstance(fitted, HandProfile)
        assert len(log) >= 5

    def test_staged_reduces_distance(self):
        profile = HandProfile(nib=NibParams(angle_deg=50.0))
        fitted, _ = run_staged_optimization(
            profile, _quadratic_objective,
            groups=["nib_physics"],
            max_iterations=15,
        )
        initial_dist, _ = _quadratic_objective(profile)
        final_dist, _ = _quadratic_objective(fitted)
        assert final_dist < initial_dist
