"""Automated parameter optimizer (TD-003 Part 4).

Staged gradient descent that adjusts hand parameters to minimize
composite metric distance against a real manuscript target.
"""

from __future__ import annotations

import copy
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable

import numpy as np

from scribesim.hand.profile import HandProfile, validate_ranges, _RANGES


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class FittingConfig:
    """Configuration for a fitting run."""
    stages: list[str] = field(default_factory=lambda: ["coarse", "nib", "rhythm", "ink"])
    max_iterations: int = 20
    learning_rate: float = 0.05
    epsilon: float = 0.01       # finite difference step (fraction of range)
    convergence_threshold: float = 0.001
    strategy: str = "gradient"  # "gradient" or "bayesian"
    log_path: Path | None = None


# Stage definitions: which param keys are active and which metrics matter
STAGE_PARAMS: dict[str, list[str]] = {
    "coarse": [k for k in _RANGES
               if k.startswith("folio.")
               or k.startswith("line.")
               or k.startswith("letterform.")],
    "nib": [k for k in _RANGES
            if k.startswith("nib.")
            or k.startswith("stroke.")],
    "rhythm": [k for k in _RANGES
               if k.startswith("word.")
               or k.startswith("glyph.")
               or k.startswith("dynamics.")],
    "ink": [k for k in _RANGES if k.startswith("ink.") or k.startswith("material.")],
}

STAGE_METRICS: dict[str, list[str]] = {
    "coarse": ["M2", "M8"],
    "nib": ["M1", "M6"],
    "rhythm": ["M3", "M5", "M7"],
    "ink": ["M4"],
}


# ---------------------------------------------------------------------------
# Fitting log
# ---------------------------------------------------------------------------

@dataclass
class FittingIteration:
    """Record of a single optimization iteration."""
    stage: str
    iteration: int
    distance: float
    per_metric: dict[str, float]
    params_changed: dict[str, float]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class FittingLog:
    """Append-only log of fitting iterations."""

    def __init__(self):
        self.iterations: list[FittingIteration] = []

    def append(self, record: FittingIteration) -> None:
        self.iterations.append(record)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(it) for it in self.iterations]
        path.write_text(json.dumps(data, indent=2))

    def __len__(self) -> int:
        return len(self.iterations)


# ---------------------------------------------------------------------------
# Gradient estimation
# ---------------------------------------------------------------------------

def _get_param(profile: HandProfile, key: str) -> float:
    """Get a parameter value by dotted key (e.g. 'nib.angle_deg')."""
    scale_name, field_name = key.split(".", 1)
    return getattr(getattr(profile, scale_name), field_name)


def _set_param(profile: HandProfile, key: str, value: float) -> HandProfile:
    """Return a new profile with one parameter changed."""
    return profile.apply_delta({key: value})


def estimate_gradient(
    profile: HandProfile,
    active_params: list[str],
    objective_fn: Callable[[HandProfile], float],
    epsilon: float = 0.01,
) -> dict[str, float]:
    """Estimate gradient via central finite differences.

    Args:
        profile: Current parameter profile.
        active_params: List of dotted param keys to differentiate.
        objective_fn: Callable that takes a HandProfile and returns a scalar distance.
        epsilon: Step size as fraction of parameter range.

    Returns:
        Dict mapping param key → gradient estimate.
    """
    gradient: dict[str, float] = {}

    for key in active_params:
        lo, hi = _RANGES.get(key, (0.0, 1.0))
        step = (hi - lo) * epsilon
        if step < 1e-10:
            gradient[key] = 0.0
            continue

        current = _get_param(profile, key)

        # Forward
        val_plus = min(hi, current + step)
        prof_plus = _set_param(profile, key, val_plus)
        dist_plus = objective_fn(prof_plus)

        # Backward
        val_minus = max(lo, current - step)
        prof_minus = _set_param(profile, key, val_minus)
        dist_minus = objective_fn(prof_minus)

        gradient[key] = (dist_plus - dist_minus) / (val_plus - val_minus + 1e-12)

    return gradient


# ---------------------------------------------------------------------------
# Parameter update
# ---------------------------------------------------------------------------

def optimize_step(
    profile: HandProfile,
    gradient: dict[str, float],
    learning_rate: float = 0.05,
) -> HandProfile:
    """Apply one gradient descent step and clamp to valid ranges.

    Returns a new profile with updated parameters.
    """
    delta: dict[str, float] = {}
    for key, grad in gradient.items():
        lo, hi = _RANGES.get(key, (0.0, 1.0))
        current = _get_param(profile, key)
        new_val = current - learning_rate * grad * (hi - lo)
        new_val = max(lo, min(hi, new_val))
        delta[key] = new_val

    return profile.apply_delta(delta)


# ---------------------------------------------------------------------------
# Staged optimizer
# ---------------------------------------------------------------------------

class StagedOptimizer:
    """Orchestrates staged parameter fitting."""

    def __init__(self, config: FittingConfig):
        self.config = config
        self.log = FittingLog()

    def run(
        self,
        profile: HandProfile,
        objective_fn: Callable[[HandProfile], tuple[float, dict[str, float]]],
    ) -> HandProfile:
        """Run all configured stages.

        Args:
            profile: Starting parameter profile.
            objective_fn: Takes HandProfile, returns (composite_distance, {metric_id: distance}).

        Returns:
            Fitted HandProfile.
        """
        current = copy.deepcopy(profile)

        for stage_name in self.config.stages:
            if stage_name not in STAGE_PARAMS:
                continue

            active_params = STAGE_PARAMS[stage_name]
            prev_dist = float("inf")

            for iteration in range(self.config.max_iterations):
                # Evaluate current
                dist, per_metric = objective_fn(current)

                # Log
                self.log.append(FittingIteration(
                    stage=stage_name,
                    iteration=iteration,
                    distance=dist,
                    per_metric=per_metric,
                    params_changed={k: _get_param(current, k) for k in active_params[:5]},
                ))

                # Convergence check
                if abs(prev_dist - dist) < self.config.convergence_threshold:
                    break
                prev_dist = dist

                # Estimate gradient using stage-filtered objective
                stage_metrics = STAGE_METRICS.get(stage_name)

                def _stage_objective(prof: HandProfile) -> float:
                    d, pm = objective_fn(prof)
                    if stage_metrics:
                        relevant = [pm[m] for m in stage_metrics if m in pm and pm[m] >= 0]
                        return sum(relevant) / max(len(relevant), 1)
                    return d

                gradient = estimate_gradient(
                    current, active_params, _stage_objective,
                    epsilon=self.config.epsilon,
                )

                # Update
                current = optimize_step(current, gradient, self.config.learning_rate)

        return current


# ---------------------------------------------------------------------------
# Bayesian optimizer (optuna)
# ---------------------------------------------------------------------------

class BayesianOptimizer:
    """Bayesian optimization using optuna's TPE sampler.

    Much more sample-efficient than gradient descent — builds a
    probabilistic surrogate model of the objective surface and picks
    the most promising parameter set to evaluate next.
    """

    def __init__(self, config: FittingConfig):
        self.config = config
        self.log = FittingLog()

    def run(
        self,
        profile: HandProfile,
        objective_fn: Callable[[HandProfile], tuple[float, dict[str, float]]],
    ) -> HandProfile:
        """Run Bayesian optimization across all configured stages.

        Returns the best-found HandProfile.
        """
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        best_profile = copy.deepcopy(profile)

        for stage_name in self.config.stages:
            if stage_name not in STAGE_PARAMS:
                continue

            active_params = STAGE_PARAMS[stage_name]
            stage_metrics = STAGE_METRICS.get(stage_name)
            base_profile = copy.deepcopy(best_profile)

            # Capture the best profile found during this stage
            stage_best_dist = float("inf")
            stage_best_profile = base_profile

            def _optuna_objective(trial: optuna.Trial) -> float:
                nonlocal stage_best_dist, stage_best_profile

                # Sample each active parameter within its range
                delta: dict[str, Any] = {}
                for key in active_params:
                    lo, hi = _RANGES.get(key, (0.0, 1.0))
                    current = _get_param(base_profile, key)
                    # Use current value as the center, search within range
                    if isinstance(current, int) or (isinstance(lo, int) and isinstance(hi, int)):
                        val = trial.suggest_int(key, int(lo), int(hi))
                    else:
                        val = trial.suggest_float(key, float(lo), float(hi))
                    delta[key] = val

                candidate = base_profile.apply_delta(delta)
                dist, per_metric = objective_fn(candidate)

                # Stage-filtered score
                if stage_metrics:
                    relevant = [per_metric[m] for m in stage_metrics
                                if m in per_metric and per_metric[m] >= 0]
                    score = sum(relevant) / max(len(relevant), 1)
                else:
                    score = dist

                # Log
                self.log.append(FittingIteration(
                    stage=stage_name,
                    iteration=len(self.log),
                    distance=score,
                    per_metric=per_metric,
                    params_changed={k: delta.get(k, 0) for k in active_params[:5]},
                ))

                # Track best
                if score < stage_best_dist:
                    stage_best_dist = score
                    stage_best_profile = candidate

                return score

            study = optuna.create_study(direction="minimize")
            study.optimize(_optuna_objective, n_trials=self.config.max_iterations)

            best_profile = stage_best_profile

        return best_profile


# ---------------------------------------------------------------------------
# High-level fitting function
# ---------------------------------------------------------------------------

def run_fitting(
    profile: HandProfile,
    objective_fn: Callable[[HandProfile], tuple[float, dict[str, float]]],
    config: FittingConfig | None = None,
) -> tuple[HandProfile, FittingLog]:
    """Run the full fitting pipeline.

    Args:
        profile: Starting parameter profile.
        objective_fn: Takes HandProfile, returns (composite, {metric_id: distance}).
        config: Fitting configuration (defaults if None).

    Returns:
        (fitted_profile, fitting_log).
    """
    if config is None:
        config = FittingConfig()

    if config.strategy == "bayesian":
        optimizer = BayesianOptimizer(config)
    else:
        optimizer = StagedOptimizer(config)
    fitted = optimizer.run(profile, objective_fn)

    if config.log_path:
        optimizer.log.save(config.log_path)

    return fitted, optimizer.log
