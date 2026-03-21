"""Live fitting loop — renders with each candidate parameter set.

Renders a small subset of lines (fast) for each optimizer evaluation,
saves every iteration's output for visual comparison, and measures
metrics against a real manuscript target.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.hand.params import HandParams
from scribesim.hand.profile import HandProfile, load_profile, resolve_profile
from scribesim.layout import place
from scribesim.render.pipeline import render_pipeline
from scribesim.metrics.suite import run_metrics, composite_score, MetricResult


@dataclass
class TrialResult:
    """Record of one optimizer trial with rendered output."""
    trial: int
    stage: str
    distance: float
    per_metric: dict[str, float]
    params: dict[str, float]
    render_path: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%H:%M:%S")


def _render_quick(
    folio_dict: dict,
    profile: HandProfile,
    output_dir: Path,
    label: str,
    max_lines: int = 8,
) -> Path:
    """Render a few lines quickly for optimizer evaluation.

    Trims the folio to max_lines for speed (~5-10s instead of ~60s).
    """
    # Trim to max_lines
    trimmed = {**folio_dict}
    trimmed["lines"] = folio_dict["lines"][:max_lines]
    trimmed["metadata"] = {**folio_dict["metadata"], "line_count": min(max_lines, folio_dict["metadata"]["line_count"])}

    params = profile.to_v1()
    layout = place(trimmed, params, profile=profile)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    page_path, _ = render_pipeline(layout, params, output_dir, label, profile=profile)
    return page_path


def run_live_fitting(
    folio_json_path: Path,
    target_path: Path,
    output_dir: Path,
    stages: list[str] | None = None,
    max_iterations: int = 10,
    max_lines: int = 8,
    hand_toml: Path | None = None,
    folio_id: str = "f01r",
) -> list[TrialResult]:
    """Run the optimizer with actual rendering at each evaluation.

    Each trial:
      1. Apply candidate parameters to the profile
      2. Render max_lines lines at 400→300 DPI
      3. Compare against target manuscript
      4. Save the rendered output for visual review

    Args:
        folio_json_path: Path to XL folio JSON.
        target_path: Path to target manuscript image.
        output_dir: Directory to save all trial outputs.
        stages: Optimizer stages (default: ["nib"]).
        max_iterations: Trials per stage.
        max_lines: Lines to render per trial (fewer = faster).
        hand_toml: Optional hand profile TOML.
        folio_id: Folio ID for rendering.

    Returns:
        List of TrialResult records.
    """
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    from scribesim.tuning.optimizer import STAGE_PARAMS, STAGE_METRICS, _RANGES, _get_param

    if stages is None:
        stages = ["nib"]

    folio_dict = json.loads(Path(folio_json_path).read_text())
    target_img = np.array(Image.open(target_path).convert("RGB"))
    base_profile = load_profile(hand_toml)
    base_profile = resolve_profile(base_profile, folio_id, hand_toml)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    trials: list[TrialResult] = []
    trial_num = 0

    # Render baseline first
    print(f"  rendering baseline ({max_lines} lines)...")
    baseline_path = _render_quick(folio_dict, base_profile, output_dir / "trial_000_baseline", "render", max_lines)
    baseline_img = np.array(Image.open(baseline_path))
    baseline_results = run_metrics(baseline_img, target_img)
    baseline_score = composite_score(baseline_results)
    trials.append(TrialResult(
        trial=0, stage="baseline", distance=baseline_score,
        per_metric={r.id: r.distance for r in baseline_results},
        params={}, render_path=str(baseline_path),
    ))
    print(f"  baseline composite: {baseline_score:.3f}")

    best_score = baseline_score
    best_profile = base_profile

    for stage_name in stages:
        if stage_name not in STAGE_PARAMS:
            print(f"  unknown stage: {stage_name}, skipping")
            continue

        active_params = STAGE_PARAMS[stage_name]
        stage_metrics = STAGE_METRICS.get(stage_name)
        print(f"\n  === Stage: {stage_name} ({len(active_params)} params, {max_iterations} trials) ===")

        def _objective(optuna_trial: optuna.Trial) -> float:
            nonlocal trial_num, best_score, best_profile

            trial_num += 1

            # Sample parameters
            delta = {}
            for key in active_params:
                lo, hi = _RANGES.get(key, (0.0, 1.0))
                current = _get_param(best_profile, key)
                if isinstance(lo, int) and isinstance(hi, int):
                    delta[key] = optuna_trial.suggest_int(key, int(lo), int(hi))
                else:
                    delta[key] = optuna_trial.suggest_float(key, float(lo), float(hi))

            candidate = best_profile.apply_delta(delta)

            # Render
            trial_dir = output_dir / f"trial_{trial_num:03d}_{stage_name}"
            render_path = _render_quick(folio_dict, candidate, trial_dir, "render", max_lines)

            # Measure
            rendered_img = np.array(Image.open(render_path))
            results = run_metrics(rendered_img, target_img)
            per_metric = {r.id: r.distance for r in results}

            # Stage-filtered score
            if stage_metrics:
                relevant = [per_metric[m] for m in stage_metrics if m in per_metric and per_metric[m] >= 0]
                score = sum(relevant) / max(len(relevant), 1)
            else:
                score = composite_score(results)

            # Log
            trials.append(TrialResult(
                trial=trial_num, stage=stage_name, distance=score,
                per_metric=per_metric,
                params={k: delta[k] for k in list(active_params)[:8]},
                render_path=str(render_path),
            ))

            if score < best_score:
                best_score = score
                best_profile = candidate

            param_summary = ", ".join(
                f"{k.split('.')[1]}={delta[k]:.2f}" for k in list(active_params)[:3]
            )
            print(f"    trial {trial_num:3d}: score={score:.3f}  "
                  f"(best={best_score:.3f})  {param_summary}")

            return score

        study = optuna.create_study(direction="minimize")
        study.optimize(_objective, n_trials=max_iterations)

    # Save fitting log
    log_path = output_dir / "fitting_log.json"

    def _json_default(obj):
        if hasattr(obj, "item"):  # numpy scalar
            return obj.item()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    log_path.write_text(json.dumps([asdict(t) for t in trials], indent=2, default=_json_default))

    # Save best profile
    flat = best_profile.to_flat_dict()
    lines = ["# Best fitted profile\n"]
    current_section = None
    for key in sorted(flat):
        if "." in key and not key.startswith("v1."):
            section = key.split(".")[0]
            if section != current_section:
                current_section = section
                lines.append(f"\n[{section}]")
            lines.append(f"{key.split('.', 1)[1]} = {flat[key]!r}")
    (output_dir / "best_profile.toml").write_text("\n".join(lines) + "\n")

    print(f"\n  === Done ===")
    print(f"  trials: {len(trials)}")
    print(f"  best composite: {best_score:.3f} (baseline was {baseline_score:.3f})")
    print(f"  output: {output_dir}")
    print(f"  log: {log_path}")

    return trials
