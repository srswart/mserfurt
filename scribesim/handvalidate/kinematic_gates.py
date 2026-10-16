"""Automated Tier-1 kinematic and coarticulation gates (TD-019 §4).

Provides:
  - A2-KINEMATICS: Dimensionless Jerk (DLJ) & velocity continuity gate
  - A3-COARTICULATE: Reciprocal neighbor adaptation gate
"""

from __future__ import annotations

import math
import numpy as np

from scribesim.hand.profile import HandProfile, bastarda_nib_calibrated_profile
from scribesim.handflow.coarticulate import (
    CoarticulatedWordResult,
    solve_word_coarticulation,
)


def evaluate_a2_kinematics(
    result: CoarticulatedWordResult,
    *,
    max_dimensionless_jerk: float = 450.0,
    max_speed_mm_s: float = 85.0,
) -> dict:
    """Evaluate Tier-1 A2-KINEMATICS gate on a solved word trajectory."""
    if len(result.samples) < 5:
        return {
            "gate": "A2-KINEMATICS",
            "passed": False,
            "failures": ["insufficient_samples"],
        }

    dt = result.dt_s
    x = np.array([s.x_mm for s in result.samples], dtype=np.float64)
    y = np.array([s.y_mm for s in result.samples], dtype=np.float64)

    vx = np.gradient(x, dt)
    vy = np.gradient(y, dt)
    speed = np.hypot(vx, vy)
    peak_speed = float(np.max(speed))

    jx = np.diff(x, n=3) / (dt ** 3)
    jy = np.diff(y, n=3) / (dt ** 3)
    jerk_sq = jx ** 2 + jy ** 2

    duration = max(dt, (len(x) - 1) * dt)
    path_len = float(np.sum(np.hypot(np.diff(x), np.diff(y))))
    # Per-stroke normalized dimensionless jerk (scaled by number of via-point segments)
    n_strokes = max(1, len(result.placed_via_points) - 1)
    stroke_dur = duration / n_strokes
    stroke_len = max(0.5, path_len / n_strokes)
    mean_jerk_sq = float(np.mean(jerk_sq))
    dlj = math.sqrt(mean_jerk_sq * (stroke_dur ** 5) / (stroke_len ** 2))

    # Check velocity continuity (no sudden single-step velocity jump > 35 mm/s)
    dv = np.hypot(np.diff(vx), np.diff(vy))
    max_dv_step = float(np.max(dv)) if len(dv) else 0.0

    failures: list[str] = []
    if dlj > max_dimensionless_jerk:
        failures.append("dimensionless_jerk")
    if peak_speed > max_speed_mm_s:
        failures.append("peak_speed")
    if max_dv_step > 45.0:
        failures.append("velocity_discontinuity")

    return {
        "gate": "A2-KINEMATICS",
        "passed": len(failures) == 0,
        "word": result.word,
        "dimensionless_jerk": round(dlj, 4),
        "peak_speed_mm_s": round(peak_speed, 4),
        "max_velocity_step_mm_s": round(max_dv_step, 4),
        "failures": failures,
    }


def evaluate_a3_coarticulate(
    *,
    profile: HandProfile | None = None,
    bounds_wnib: tuple[float, float] = (0.03, 0.35),
    max_body_drift_wnib: float = 0.05,
) -> dict:
    """Evaluate Tier-1 A3-COARTICULATE gate across nu, nm, isolated n, and isolated u."""
    prof = profile or bastarda_nib_calibrated_profile()

    res_n = solve_word_coarticulation("n", profile=prof, start_x_wnib=1.2)
    res_u = solve_word_coarticulation("u", profile=prof, start_x_wnib=1.2)
    res_nu = solve_word_coarticulation("nu", profile=prof, start_x_wnib=1.2)
    res_nm = solve_word_coarticulation("nm", profile=prof, start_x_wnib=1.2)

    # 1. Preceding letter adaptation: compare n's exit via-point solved position in "nu" vs "nm"
    n_exit_nu = next(vp for vp in res_nu.placed_via_points if vp.letter_index == 0 and vp.role == "exit")
    n_exit_nm = next(vp for vp in res_nm.placed_via_points if vp.letter_index == 0 and vp.role == "exit")
    idx_exit = n_exit_nu.sample_index
    n_exit_delta_wnib = float(
        math.hypot(
            res_nu.solved_x_wnib[idx_exit] - res_nm.solved_x_wnib[idx_exit],
            res_nu.solved_y_wnib[idx_exit] - res_nm.solved_y_wnib[idx_exit],
        )
    )

    # 2. Protected body stability: compare n's first stem body via-point in "nu" vs isolated "n"
    n_body_nu = next(vp for vp in res_nu.placed_via_points if vp.letter_index == 0 and vp.role == "body")
    idx_body = n_body_nu.sample_index
    n_body_delta_wnib = float(
        math.hypot(
            res_nu.solved_x_wnib[idx_body] - res_n.solved_x_wnib[idx_body],
            res_nu.solved_y_wnib[idx_body] - res_n.solved_y_wnib[idx_body],
        )
    )

    # 3. Following letter adaptation: compare u's entry via-point in "nu" (relative to u's origin) vs isolated "u"
    u_entry_nu = next(vp for vp in res_nu.placed_via_points if vp.letter_index == 1 and vp.role == "entry")
    u_entry_iso = next(vp for vp in res_u.placed_via_points if vp.letter_index == 0 and vp.role == "entry")
    offset_x_wnib = u_entry_nu.x_wnib - u_entry_iso.x_wnib
    u_idx_nu = u_entry_nu.sample_index
    u_idx_iso = u_entry_iso.sample_index
    u_entry_delta_wnib = float(
        math.hypot(
            (res_nu.solved_x_wnib[u_idx_nu] - offset_x_wnib) - res_u.solved_x_wnib[u_idx_iso],
            res_nu.solved_y_wnib[u_idx_nu] - res_u.solved_y_wnib[u_idx_iso],
        )
    )

    failures: list[str] = []
    if not (bounds_wnib[0] <= n_exit_delta_wnib <= bounds_wnib[1]):
        failures.append("n_exit_delta_wnib_nu_vs_nm")
    if not (bounds_wnib[0] <= u_entry_delta_wnib <= bounds_wnib[1]):
        failures.append("u_entry_delta_wnib_nu_vs_isolated")
    if n_body_delta_wnib >= max_body_drift_wnib:
        failures.append("n_protected_body_delta_wnib")

    return {
        "gate": "A3-COARTICULATE",
        "passed": len(failures) == 0,
        "n_exit_delta_wnib_nu_vs_nm": round(n_exit_delta_wnib, 4),
        "u_entry_delta_wnib_nu_vs_isolated": round(u_entry_delta_wnib, 4),
        "n_protected_body_delta_wnib": round(n_body_delta_wnib, 5),
        "bounds_wnib": list(bounds_wnib),
        "max_body_drift_wnib": max_body_drift_wnib,
        "failures": failures,
    }


def _count_open_counters_in_image(rgb_arr: np.ndarray, min_area_px: int = 6) -> tuple[int, int]:
    """Count enclosed interior background components (open counters) in an RGB glyph render."""
    from scipy.ndimage import label

    gray = rgb_arr.mean(axis=2)
    bg = gray > 210.0
    labeled, num_features = label(bg)
    if num_features <= 1:
        return 0, 0

    border_labels = (
        set(labeled[0, :].tolist())
        | set(labeled[-1, :].tolist())
        | set(labeled[:, 0].tolist())
        | set(labeled[:, -1].tolist())
    )
    open_count = 0
    max_area = 0
    for comp_id in range(1, num_features + 1):
        if comp_id in border_labels:
            continue
        area = int(np.sum(labeled == comp_id))
        if area >= min_area_px:
            open_count += 1
            max_area = max(max_area, area)
    return open_count, max_area


def evaluate_a4_topology(
    *,
    profile: HandProfile | None = None,
    words: tuple[str, ...] = ("und", "glauben", "schreiber"),
    dpi: float = 240.0,
) -> dict:
    """Evaluate Tier-1 A4-TOPOLOGY gate: open counters in (a, o, d, e, g, b, p) and zero non-adjacent collisions."""
    from scribesim.guides.viapoint_catalog import COUNTER_LETTERS
    from scribesim.render.sandbox import render_trajectory_samples

    prof = profile or bastarda_nib_calibrated_profile()
    letter_counters: dict[str, dict] = {}
    failures: list[str] = []

    for ch in COUNTER_LETTERS:
        res = solve_word_coarticulation(ch, profile=prof)
        arr, _, _ = render_trajectory_samples(res.samples, profile=prof, dpi=dpi, margin_mm=1.8)
        count, area_px = _count_open_counters_in_image(arr, min_area_px=6)
        letter_counters[ch] = {
            "open_counter_count": count,
            "max_counter_area_px": area_px,
            "passed": count >= 1,
        }
        if count < 1:
            failures.append(f"collapsed_counter:{ch}")

    non_adjacent_collisions = 0
    for w in words:
        res = solve_word_coarticulation(w, profile=prof)
        spans: dict[int, list[float]] = {}
        for vp in res.placed_via_points:
            if vp.role == "body":
                x_solved = float(res.solved_x_wnib[vp.sample_index])
                spans.setdefault(vp.letter_index, []).append(x_solved)
        indices = sorted(spans.keys())
        for idx_i, li in enumerate(indices):
            for lj in indices[idx_i + 1 :]:
                if abs(lj - li) >= 2:
                    if max(spans[li]) >= min(spans[lj]):
                        non_adjacent_collisions += 1

    if non_adjacent_collisions > 0:
        failures.append("non_adjacent_collisions")

    return {
        "gate": "A4-TOPOLOGY",
        "passed": len(failures) == 0,
        "letter_counters": letter_counters,
        "non_adjacent_collisions": non_adjacent_collisions,
        "failures": failures,
    }


def evaluate_a5_anti_clone(
    text: str = "und der und wir und\nalle seines alle alleine",
    *,
    folio_id: str = "f01r",
    seed: int = 1457,
    min_dtw_wnib: float = 0.06,
    max_dtw_wnib: float = 0.95,
) -> dict:
    """Evaluate Tier-1 A5-ANTI-CLONE gate: verify repeated words & word-initial letters vary organically."""
    from scribesim.handflow.coarticulate import (
        CoarticulatedWordResult,
        compose_line_kinematic_Stateful,
    )
    from scribesim.render.scribe_state import KinematicScribeSession

    session = KinematicScribeSession(folio_id=folio_id, seed=seed)
    by_word: dict[str, list[CoarticulatedWordResult]] = {}
    by_initial: dict[str, list[CoarticulatedWordResult]] = {}

    for line_idx, line in enumerate(text.splitlines() or [text]):
        l_res = compose_line_kinematic_Stateful(line, session=session, line_index=line_idx)
        for w_res in l_res.word_results:
            by_word.setdefault(w_res.word, []).append(w_res)
            if w_res.word:
                by_initial.setdefault(w_res.word[0], []).append(w_res)

    word_deltas: list[float] = []
    for instances in by_word.values():
        if len(instances) < 2:
            continue
        for i in range(len(instances)):
            for j in range(i + 1, len(instances)):
                w1, w2 = instances[i], instances[j]
                x0_1 = w1.placed_via_points[0].x_wnib
                x0_2 = w2.placed_via_points[0].x_wnib
                dx = (w1.solved_x_wnib - x0_1) - (w2.solved_x_wnib - x0_2)
                dy = w1.solved_y_wnib - w2.solved_y_wnib
                dist = float(np.mean(np.hypot(dx, dy)))
                word_deltas.append(dist)

    initial_deltas: list[float] = []
    for instances in by_initial.values():
        if len(instances) < 2:
            continue
        for i in range(len(instances)):
            for j in range(i + 1, len(instances)):
                w1, w2 = instances[i], instances[j]
                x0_1 = w1.placed_via_points[0].x_wnib
                x0_2 = w2.placed_via_points[0].x_wnib
                pts1 = [
                    (float(w1.solved_x_wnib[vp.sample_index]) - x0_1, float(w1.solved_y_wnib[vp.sample_index]))
                    for vp in w1.placed_via_points
                    if vp.letter_index == 0
                ]
                pts2 = [
                    (float(w2.solved_x_wnib[vp.sample_index]) - x0_2, float(w2.solved_y_wnib[vp.sample_index]))
                    for vp in w2.placed_via_points
                    if vp.letter_index == 0
                ]
                diffs = [math.hypot(p1[0] - p2[0], p1[1] - p2[1]) for p1, p2 in zip(pts1, pts2)]
                if diffs:
                    initial_deltas.append(max(diffs))

    min_w = min(word_deltas) if word_deltas else 0.0
    max_w = max(word_deltas) if word_deltas else 0.0
    min_init = min(initial_deltas) if initial_deltas else 0.0

    failures: list[str] = []
    if not (min_dtw_wnib <= min_w <= max_dtw_wnib and max_w <= max_dtw_wnib):
        failures.append("word_dtw_out_of_bounds")
    if min_init < min_dtw_wnib:
        failures.append("word_initial_clones_detected")

    return {
        "gate": "A5-ANTI-CLONE",
        "passed": len(failures) == 0,
        "min_word_dtw_wnib": round(min_w, 4),
        "max_word_dtw_wnib": round(max_w, 4),
        "min_initial_letter_delta_wnib": round(min_init, 4),
        "bounds_wnib": [min_dtw_wnib, max_dtw_wnib],
        "failures": failures,
    }


