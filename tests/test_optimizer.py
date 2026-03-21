"""Unit tests for automated optimizer — ADV-SS-OPTIMIZER-001."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from scribesim.hand.profile import HandProfile, FolioParams, NibParams, _RANGES
from scribesim.tuning.optimizer import (
    FittingConfig,
    FittingLog,
    FittingIteration,
    StagedOptimizer,
    estimate_gradient,
    optimize_step,
    run_fitting,
    _get_param,
    _set_param,
    STAGE_PARAMS,
)


# ---------------------------------------------------------------------------
# Helpers — synthetic objective functions
# ---------------------------------------------------------------------------

def _quadratic_objective(profile: HandProfile) -> tuple[float, dict[str, float]]:
    """Synthetic objective: distance = sum of squared deviations from target values.

    Target: nib.angle_deg=40, folio.base_pressure=0.7
    """
    angle = profile.nib.angle_deg
    pressure = profile.folio.base_pressure
    dist = (angle - 40.0) ** 2 / 100.0 + (pressure - 0.7) ** 2
    return dist, {"M1": abs(angle - 40.0) / 30.0, "M2": abs(pressure - 0.7)}


def _simple_objective(profile: HandProfile) -> float:
    """Simple scalar objective for gradient tests."""
    return (profile.nib.angle_deg - 40.0) ** 2 / 100.0


# ---------------------------------------------------------------------------
# TestParamAccess
# ---------------------------------------------------------------------------

class TestParamAccess:
    def test_get_param(self):
        p = HandProfile()
        assert _get_param(p, "nib.angle_deg") == pytest.approx(40.0)

    def test_set_param(self):
        p = HandProfile()
        p2 = _set_param(p, "nib.angle_deg", 42.0)
        assert p2.nib.angle_deg == pytest.approx(42.0)
        assert p.nib.angle_deg == pytest.approx(40.0)  # original unchanged


# ---------------------------------------------------------------------------
# TestGradient
# ---------------------------------------------------------------------------

class TestGradient:
    def test_gradient_direction_correct(self):
        """If angle > target (40), gradient should be positive (push angle down)."""
        p = HandProfile(nib=NibParams(angle_deg=45.0))
        grad = estimate_gradient(p, ["nib.angle_deg"], _simple_objective, epsilon=0.02)
        # At angle=45, objective increases with angle → gradient > 0
        assert grad["nib.angle_deg"] > 0

    def test_gradient_near_optimum_small(self):
        """Near the optimum, gradient should be close to zero."""
        p = HandProfile(nib=NibParams(angle_deg=40.0))
        grad = estimate_gradient(p, ["nib.angle_deg"], _simple_objective, epsilon=0.02)
        assert abs(grad["nib.angle_deg"]) < 0.5

    def test_gradient_multiple_params(self):
        p = HandProfile(nib=NibParams(angle_deg=45.0), folio=FolioParams(base_pressure=0.8))

        def obj(prof):
            d, _ = _quadratic_objective(prof)
            return d

        grad = estimate_gradient(p, ["nib.angle_deg", "folio.base_pressure"], obj, epsilon=0.02)
        assert len(grad) == 2
        assert "nib.angle_deg" in grad
        assert "folio.base_pressure" in grad


# ---------------------------------------------------------------------------
# TestOptimizeStep
# ---------------------------------------------------------------------------

class TestOptimizeStep:
    def test_step_reduces_objective(self):
        p = HandProfile(nib=NibParams(angle_deg=45.0))
        grad = estimate_gradient(p, ["nib.angle_deg"], _simple_objective, epsilon=0.02)
        p2 = optimize_step(p, grad, learning_rate=0.1)
        assert _simple_objective(p2) < _simple_objective(p)

    def test_clamping_enforced(self):
        p = HandProfile(nib=NibParams(angle_deg=25.5))
        # Huge gradient pushing angle below minimum (25.0)
        grad = {"nib.angle_deg": 100.0}
        p2 = optimize_step(p, grad, learning_rate=1.0)
        lo, hi = _RANGES["nib.angle_deg"]
        assert p2.nib.angle_deg >= lo
        assert p2.nib.angle_deg <= hi


# ---------------------------------------------------------------------------
# TestStageIsolation
# ---------------------------------------------------------------------------

class TestStageIsolation:
    def test_coarse_only_touches_folio_line(self):
        """Coarse stage params should only be folio.* and line.*"""
        for key in STAGE_PARAMS["coarse"]:
            assert key.startswith("folio.") or key.startswith("line."), \
                f"Coarse stage includes unexpected param: {key}"

    def test_nib_only_touches_nib(self):
        for key in STAGE_PARAMS["nib"]:
            assert key.startswith("nib."), f"Nib stage includes: {key}"

    def test_stages_cover_all_ranges(self):
        """All tunable params should appear in at least one stage."""
        all_stage_params = set()
        for params in STAGE_PARAMS.values():
            all_stage_params.update(params)
        for key in _RANGES:
            assert key in all_stage_params, f"Param {key} not in any stage"


# ---------------------------------------------------------------------------
# TestFittingLog
# ---------------------------------------------------------------------------

class TestFittingLog:
    def test_append_and_len(self):
        log = FittingLog()
        log.append(FittingIteration(stage="coarse", iteration=0,
                                    distance=0.5, per_metric={}, params_changed={}))
        assert len(log) == 1

    def test_save_json(self, tmp_path):
        log = FittingLog()
        log.append(FittingIteration(stage="coarse", iteration=0,
                                    distance=0.5, per_metric={"M1": 0.1}, params_changed={}))
        path = tmp_path / "log.json"
        log.save(path)
        assert path.exists()
        import json
        data = json.loads(path.read_text())
        assert len(data) == 1
        assert data[0]["distance"] == 0.5


# ---------------------------------------------------------------------------
# TestStagedOptimizer
# ---------------------------------------------------------------------------

class TestStagedOptimizer:
    def test_optimizer_reduces_distance(self):
        """Running the optimizer should reduce the objective value."""
        p = HandProfile(nib=NibParams(angle_deg=48.0), folio=FolioParams(base_pressure=0.85))
        config = FittingConfig(stages=["nib"], max_iterations=5, learning_rate=0.1)
        optimizer = StagedOptimizer(config)
        fitted = optimizer.run(p, _quadratic_objective)

        initial_dist, _ = _quadratic_objective(p)
        final_dist, _ = _quadratic_objective(fitted)
        assert final_dist <= initial_dist

    def test_convergence_stops_early(self):
        """Already near optimum should converge in 1-2 iterations."""
        p = HandProfile(nib=NibParams(angle_deg=40.0))
        config = FittingConfig(stages=["nib"], max_iterations=20,
                               convergence_threshold=0.01)
        optimizer = StagedOptimizer(config)
        optimizer.run(p, _quadratic_objective)
        assert len(optimizer.log) < 20

    def test_log_populated(self):
        p = HandProfile(nib=NibParams(angle_deg=45.0))
        config = FittingConfig(stages=["nib"], max_iterations=3)
        optimizer = StagedOptimizer(config)
        optimizer.run(p, _quadratic_objective)
        assert len(optimizer.log) >= 1


# ---------------------------------------------------------------------------
# TestRunFitting
# ---------------------------------------------------------------------------

class TestRunFitting:
    def test_run_fitting_returns_profile_and_log(self):
        p = HandProfile(nib=NibParams(angle_deg=45.0))
        config = FittingConfig(stages=["nib"], max_iterations=3)
        fitted, log = run_fitting(p, _quadratic_objective, config)
        assert isinstance(fitted, HandProfile)
        assert isinstance(log, FittingLog)
        assert len(log) >= 1

    def test_run_fitting_saves_log(self, tmp_path):
        p = HandProfile(nib=NibParams(angle_deg=45.0))
        config = FittingConfig(stages=["nib"], max_iterations=2,
                               log_path=tmp_path / "fit.json")
        run_fitting(p, _quadratic_objective, config)
        assert (tmp_path / "fit.json").exists()


# ---------------------------------------------------------------------------
# TestBayesianOptimizer
# ---------------------------------------------------------------------------

class TestBayesianOptimizer:
    def test_bayesian_reduces_distance(self):
        """Bayesian optimizer should find a better solution."""
        from scribesim.tuning.optimizer import BayesianOptimizer
        p = HandProfile(nib=NibParams(angle_deg=48.0), folio=FolioParams(base_pressure=0.85))
        config = FittingConfig(stages=["nib"], max_iterations=10, strategy="bayesian")
        optimizer = BayesianOptimizer(config)
        fitted = optimizer.run(p, _quadratic_objective)

        initial_dist, _ = _quadratic_objective(p)
        final_dist, _ = _quadratic_objective(fitted)
        assert final_dist < initial_dist

    def test_bayesian_log_populated(self):
        from scribesim.tuning.optimizer import BayesianOptimizer
        p = HandProfile(nib=NibParams(angle_deg=45.0))
        config = FittingConfig(stages=["nib"], max_iterations=5, strategy="bayesian")
        optimizer = BayesianOptimizer(config)
        optimizer.run(p, _quadratic_objective)
        assert len(optimizer.log) >= 5

    def test_bayesian_via_run_fitting(self):
        p = HandProfile(nib=NibParams(angle_deg=45.0))
        config = FittingConfig(stages=["nib"], max_iterations=5, strategy="bayesian")
        fitted, log = run_fitting(p, _quadratic_objective, config)
        assert isinstance(fitted, HandProfile)
        assert len(log) >= 5

    def test_bayesian_finds_near_optimum(self):
        """With enough trials, Bayesian should get close to the target (angle=40)."""
        from scribesim.tuning.optimizer import BayesianOptimizer
        p = HandProfile(nib=NibParams(angle_deg=50.0))
        config = FittingConfig(stages=["nib"], max_iterations=20, strategy="bayesian")
        optimizer = BayesianOptimizer(config)
        fitted = optimizer.run(p, _quadratic_objective)
        # Should get within 5 degrees of target (40)
        assert abs(fitted.nib.angle_deg - 40.0) < 5.0
