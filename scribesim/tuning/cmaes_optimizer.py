"""CMA-ES group optimizer (TD-004 Part 3, TD-003-A §2).

Optimizes parameter groups using Covariance Matrix Adaptation Evolution
Strategy — handles correlated parameters (e.g. nib angle + width +
flexibility all affect thick/thin together) that single-parameter
optimization can't fit.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from scribesim.hand.profile import HandProfile, _RANGES
from scribesim.tuning.optimizer import (
    FittingConfig,
    FittingLog,
    FittingIteration,
    _get_param,
)


# ---------------------------------------------------------------------------
# Parameter group definitions
# ---------------------------------------------------------------------------

@dataclass
class ParameterGroup:
    """A group of related parameters optimized together."""
    name: str
    description: str
    parameters: list[str]
    target_metrics: list[str]
    method: str = "cma-es"     # "cma-es" or "nelder-mead"
    priority: int = 1

    def ranges(self) -> tuple[list[float], list[float]]:
        """Return (lower_bounds, upper_bounds) for all parameters."""
        lowers, uppers = [], []
        for key in self.parameters:
            lo, hi = _RANGES.get(key, (0.0, 1.0))
            lowers.append(float(lo))
            uppers.append(float(hi))
        return lowers, uppers

    def extract(self, profile: HandProfile) -> list[float]:
        """Extract current parameter values from a profile."""
        return [_get_param(profile, k) for k in self.parameters]


# Pre-defined groups from TD-004
PARAMETER_GROUPS: dict[str, ParameterGroup] = {
    "nib_physics": ParameterGroup(
        name="nib_physics",
        description="Nib-driven mark-making quality (TD-004)",
        parameters=[
            "nib.width_mm", "nib.angle_deg", "nib.flexibility",
            "nib.cut_quality",
        ],
        target_metrics=["M1"],
        method="cma-es",
        priority=1,
    ),
    "baseline_geometry": ParameterGroup(
        name="baseline_geometry",
        description="Page geometry and line positioning (TD-002)",
        parameters=[
            "folio.ruling_slope_variance", "folio.ruling_spacing_variance_mm",
            "folio.margin_left_variance_mm",
            "line.start_x_variance_mm", "line.baseline_undulation_amplitude_mm",
            "line.baseline_undulation_period_ratio", "line.line_spacing_variance_mm",
        ],
        target_metrics=["M2"],
        method="nelder-mead",
        priority=2,
    ),
    "hand_dynamics": ParameterGroup(
        name="hand_dynamics",
        description="Hand simulator mechanics (TD-005)",
        parameters=[
            "dynamics.attraction_strength", "dynamics.damping_coefficient",
            "dynamics.lookahead_strength", "dynamics.max_speed",
            "dynamics.rhythm_strength", "dynamics.target_radius_mm",
        ],
        target_metrics=["M10", "M3", "M7"],
        method="cma-es",
        priority=3,
    ),
    "letterform_proportion": ParameterGroup(
        name="letterform_proportion",
        description="Letter shape and proportion",
        parameters=[
            "letterform.keypoint_flexibility_mm", "letterform.ascender_height_ratio",
            "letterform.descender_depth_ratio", "letterform.x_height_mm",
        ],
        target_metrics=["M6", "M5"],
        method="nelder-mead",
        priority=4,
    ),
    "ink_material": ParameterGroup(
        name="ink_material",
        description="Ink depletion and material interaction",
        parameters=[
            "ink.depletion_rate", "ink.fresh_dip_darkness_boost",
            "ink.dry_threshold", "ink.raking_threshold",
            "material.edge_feather_mm", "material.pooling_at_direction_change",
            "material.overlap_darkening_factor",
        ],
        target_metrics=["M4"],
        method="cma-es",
        priority=5,
    ),
}


# ---------------------------------------------------------------------------
# Quality gate
# ---------------------------------------------------------------------------

@dataclass
class QualityGate:
    """A metric threshold that must pass before proceeding."""
    metric_id: str
    threshold: float

    def passes(self, score: float) -> bool:
        return score <= self.threshold


def parse_gates(gate_str: str) -> list[QualityGate]:
    """Parse gate string like 'M1<0.15,M2<0.15' into QualityGate list."""
    gates = []
    for part in gate_str.split(","):
        part = part.strip()
        if "<" in part:
            metric, val = part.split("<", 1)
            gates.append(QualityGate(metric.strip(), float(val.strip())))
    return gates


# ---------------------------------------------------------------------------
# CMA-ES group optimizer
# ---------------------------------------------------------------------------

class CMAESGroupOptimizer:
    """Optimize a parameter group using CMA-ES."""

    def __init__(self, group: ParameterGroup, max_iterations: int = 100):
        self.group = group
        self.max_iterations = max_iterations
        self.log = FittingLog()

    def run(
        self,
        profile: HandProfile,
        objective_fn: Callable[[HandProfile], tuple[float, dict[str, float]]],
    ) -> HandProfile:
        """Run CMA-ES optimization on this group.

        Args:
            profile: Starting profile.
            objective_fn: Returns (composite, {metric_id: distance}).

        Returns:
            Optimized HandProfile.
        """
        import cma

        initial = self.group.extract(profile)
        lowers, uppers = self.group.ranges()

        # Sigma: ~10% of range
        ranges = [u - l for l, u in zip(lowers, uppers)]
        sigma = np.mean(ranges) * 0.1

        best_profile = copy.deepcopy(profile)
        best_score = float("inf")

        def _objective(params: list[float]) -> float:
            nonlocal best_profile, best_score

            # Apply params to profile
            delta = {}
            for key, val in zip(self.group.parameters, params):
                delta[key] = float(val)
            candidate = profile.apply_delta(delta)

            dist, per_metric = objective_fn(candidate)

            # Stage-filtered score using target metrics
            if self.group.target_metrics:
                relevant = [per_metric.get(m, 1.0) for m in self.group.target_metrics
                            if per_metric.get(m, -1) >= 0]
                score = sum(relevant) / max(len(relevant), 1)
            else:
                score = dist

            self.log.append(FittingIteration(
                stage=self.group.name,
                iteration=len(self.log),
                distance=score,
                per_metric=per_metric,
                params_changed={k: float(v) for k, v in zip(self.group.parameters[:5], params[:5])},
            ))

            if score < best_score:
                best_score = score
                best_profile = candidate

            return score

        # CMA-ES requires ≥2 dimensions; fall back to optuna for 1-param groups
        if len(initial) < 2:
            return self._run_optuna_fallback(profile, objective_fn, initial, lowers, uppers, _objective)

        opts = {
            'bounds': [lowers, uppers],
            'maxiter': self.max_iterations,
            'popsize': max(8, 4 + int(3 * len(initial))),
            'verbose': -9,  # suppress cma output
            'tolx': 1e-4,
            'tolfun': 1e-4,
        }

        es = cma.CMAEvolutionStrategy(initial, sigma, opts)
        while not es.stop():
            candidates = es.ask()
            scores = [_objective(c) for c in candidates]
            es.tell(candidates, scores)

        return best_profile

    def _run_optuna_fallback(self, profile, objective_fn, initial, lowers, uppers, _objective):
        """Fallback for 1-param groups where CMA-ES doesn't work."""
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        best_profile_holder = [copy.deepcopy(profile)]
        best_score_holder = [float("inf")]

        def optuna_obj(trial):
            params = []
            for i, key in enumerate(self.group.parameters):
                params.append(trial.suggest_float(key, lowers[i], uppers[i]))
            score = _objective(params)
            if score < best_score_holder[0]:
                best_score_holder[0] = score
                delta = {k: float(v) for k, v in zip(self.group.parameters, params)}
                best_profile_holder[0] = profile.apply_delta(delta)
            return score

        study = optuna.create_study(direction="minimize")
        study.optimize(optuna_obj, n_trials=self.max_iterations)
        return best_profile_holder[0]


# ---------------------------------------------------------------------------
# Staged pipeline
# ---------------------------------------------------------------------------

def run_staged_optimization(
    profile: HandProfile,
    objective_fn: Callable[[HandProfile], tuple[float, dict[str, float]]],
    groups: list[str] | None = None,
    max_iterations: int = 50,
    gates: list[QualityGate] | None = None,
) -> tuple[HandProfile, FittingLog]:
    """Run parameter groups in priority order with quality gates.

    Args:
        profile: Starting profile.
        objective_fn: Returns (composite, {metric_id: distance}).
        groups: Group names to run (default: all, in priority order).
        max_iterations: Max CMA-ES iterations per group.
        gates: Quality gates to check after each group.

    Returns:
        (optimized_profile, combined_log).
    """
    combined_log = FittingLog()
    current = copy.deepcopy(profile)

    # Select and sort groups
    group_names = groups or sorted(PARAMETER_GROUPS.keys(),
                                    key=lambda g: PARAMETER_GROUPS[g].priority)

    for gname in group_names:
        group = PARAMETER_GROUPS.get(gname)
        if group is None:
            continue

        optimizer = CMAESGroupOptimizer(group, max_iterations)
        current = optimizer.run(current, objective_fn)

        # Merge log
        for it in optimizer.log.iterations:
            combined_log.append(it)

        # Check gates
        if gates:
            dist, per_metric = objective_fn(current)
            for gate in gates:
                score = per_metric.get(gate.metric_id, 1.0)
                if not gate.passes(score):
                    # Gate failed — log but continue
                    combined_log.append(FittingIteration(
                        stage=f"{gname}_gate_fail",
                        iteration=len(combined_log),
                        distance=dist,
                        per_metric=per_metric,
                        params_changed={"gate": gate.metric_id, "threshold": gate.threshold},
                    ))

    return current, combined_log
