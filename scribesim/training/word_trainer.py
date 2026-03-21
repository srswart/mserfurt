"""Word-level training: fit hand dynamics to reproduce a manuscript word (TD-005 Part 2).

Uses CMA-ES to optimize hand simulator dynamics parameters so the
simulated writing path matches the extracted path from a real manuscript.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.hand.profile import HandProfile
from scribesim.handsim.targets import plan_word
from scribesim.handsim.state import HandSimulator
from scribesim.training.path_extract import extract_writing_path, path_to_mm


@dataclass
class WordTrainingResult:
    """Result of word-level training."""
    word: str
    initial_distance: float
    final_distance: float
    iterations: int
    best_params: dict


def dtw_distance(path_a: list[tuple[float, float]],
                 path_b: list[tuple[float, float]]) -> float:
    """Simple Dynamic Time Warping distance between two 2D paths.

    Uses a fast approximation: compare corresponding points after
    resampling both paths to the same length.
    """
    if not path_a or not path_b:
        return 1000.0

    # Resample both to 100 points
    n = 100

    def resample(path, n):
        arr = np.array(path)
        indices = np.linspace(0, len(arr) - 1, n).astype(int)
        return arr[indices]

    a = resample(path_a, n)
    b = resample(path_b, n)

    # Pairwise Euclidean distances
    dists = np.sqrt(np.sum((a - b) ** 2, axis=1))
    return float(dists.mean())


def train_word(
    word: str,
    target_image_path: Path,
    profile: HandProfile,
    x_height_mm: float = 3.8,
    max_iterations: int = 30,
) -> tuple[HandProfile, WordTrainingResult]:
    """Train hand dynamics on a single word from a manuscript.

    1. Extract writing path from target image
    2. Generate targets for the word using letterform guides
    3. Simulate with current dynamics
    4. Compare paths via DTW
    5. Optimize dynamics with CMA-ES to minimize path distance

    Args:
        word: The word text (e.g., "und").
        target_image_path: Path to the extracted word image.
        profile: Starting hand profile.
        x_height_mm: Physical x-height.
        max_iterations: CMA-ES iterations.

    Returns:
        (fitted_profile, training_result).
    """
    # Extract target path
    target_img = np.array(Image.open(target_image_path).convert("RGB"))
    target_path_px = extract_writing_path(target_img)
    if not target_path_px:
        return profile, WordTrainingResult(word, 1000.0, 1000.0, 0, {})

    # Estimate px_per_mm from image size and expected word width
    word_width_mm = len(word) * 0.5 * x_height_mm  # rough estimate
    px_per_mm = target_img.shape[1] / max(word_width_mm, 1.0)
    target_path = path_to_mm(target_path_px, px_per_mm)

    # Dynamics parameters to optimize
    dyn_keys = [
        "dynamics.attraction_strength",
        "dynamics.damping_coefficient",
        "dynamics.lookahead_strength",
        "dynamics.max_speed",
        "dynamics.rhythm_strength",
        "dynamics.target_radius_mm",
    ]

    from scribesim.hand.profile import _RANGES
    from scribesim.tuning.optimizer import _get_param

    initial_vals = [_get_param(profile, k) for k in dyn_keys]

    def simulate_and_compare(params: list[float]) -> float:
        """Simulate word with candidate params, compare to target path."""
        delta = {k: float(v) for k, v in zip(dyn_keys, params)}
        candidate = profile.apply_delta(delta)

        # Generate targets
        baseline_y = 10.0  # arbitrary, consistent
        wt = plan_word(word, 2.0, baseline_y, x_height_mm, candidate)

        # Simulate
        sim = HandSimulator(candidate)
        marks = sim.simulate(wt.targets, dt=0.001, max_steps=50000)

        if not marks:
            return 1000.0

        # Convert marks to path
        sim_path = [(m.x_mm, m.y_mm) for m in marks if m.width_mm > 0.01]
        if not sim_path:
            return 1000.0

        # Normalize both paths to [0,1] range for scale-invariant comparison
        sim_arr = np.array(sim_path)
        tgt_arr = np.array(target_path)

        for arr in [sim_arr, tgt_arr]:
            for dim in range(2):
                mn, mx = arr[:, dim].min(), arr[:, dim].max()
                if mx > mn:
                    arr[:, dim] = (arr[:, dim] - mn) / (mx - mn)

        sim_norm = [(p[0], p[1]) for p in sim_arr.tolist()]
        tgt_norm = [(p[0], p[1]) for p in tgt_arr.tolist()]

        return dtw_distance(sim_norm, tgt_norm)

    # Initial distance
    initial_dist = simulate_and_compare(initial_vals)

    # Optimize with CMA-ES (or optuna for small groups)
    try:
        import cma
        lowers = [float(_RANGES[k][0]) for k in dyn_keys]
        uppers = [float(_RANGES[k][1]) for k in dyn_keys]

        # Clamp initial values to be within bounds (required by CMA-ES)
        initial_vals = [max(lo, min(hi, v)) for v, lo, hi in zip(initial_vals, lowers, uppers)]

        sigma = np.mean([u - l for l, u in zip(lowers, uppers)]) * 0.1

        es = cma.CMAEvolutionStrategy(initial_vals, sigma, {
            'bounds': [lowers, uppers],
            'maxiter': max_iterations,
            'popsize': max(8, 4 + int(3 * len(initial_vals))),
            'verbose': -9,
        })

        best_score = initial_dist
        best_params = initial_vals

        while not es.stop():
            candidates = es.ask()
            scores = [simulate_and_compare(c) for c in candidates]
            es.tell(candidates, scores)
            if min(scores) < best_score:
                best_score = min(scores)
                best_params = candidates[scores.index(best_score)]

    except ImportError:
        # Fallback: keep initial
        best_score = initial_dist
        best_params = initial_vals

    # Apply best params
    delta = {k: float(v) for k, v in zip(dyn_keys, best_params)}
    fitted = profile.apply_delta(delta)

    return fitted, WordTrainingResult(
        word=word,
        initial_distance=initial_dist,
        final_distance=best_score,
        iterations=max_iterations,
        best_params=delta,
    )
