"""Global Minimum-Jerk Via-Point Coarticulation Solver (TD-019 Pillar 2).

Solves a single banded Minimum-Jerk + Acceleration-Regularized Quadratic Program
across all via-points of a connected word run simultaneously:

    min_{x(t), y(t)} ∫ (||x'''(t)||^2 + lambda_a ||x''(t)||^2) dt
                     + sum_k (p(t_k) - mu_k)^T Sigma_k^-1 (p(t_k) - mu_k)

Because the third-derivative operator couples adjacent letter boundaries across
finite-stiffness exit/entry via-points (Sigma_k), reciprocal neighbor adaptation
(coarticulation) emerges automatically in <1 ms per word without pair-specific
spline-splicing formulas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.linalg import solveh_banded

from scribesim.guides.viapoint import (
    VIAPOINT_STARTER_CATALOG,
    ViaPoint,
    ViaPointRecipe,
    lookup_viapoint_recipe,
)
from scribesim.guides.viapoint_catalog import (
    VIAPOINT_CATALOG,
    select_contextual_viapoint_recipe,
)
from scribesim.hand.profile import HandProfile, bastarda_nib_calibrated_profile
from scribesim.render.sandbox import SandboxSample
from scribesim.render.scribe_state import (
    KinematicScribeSession,
    resolve_clio7_kinematic_profile,
)


@dataclass(frozen=True)
class PlacedViaPoint:
    """One via-point placed in word/line coordinates (in both w_nib and physical mm)."""

    letter: str
    letter_index: int
    local_index: int
    role: str
    sample_index: int
    x_wnib: float
    y_wnib: float
    x_mm: float
    y_mm: float
    sigma_x_wnib: float
    sigma_y_wnib: float
    pressure: float
    contact: bool


@dataclass(frozen=True)
class CoarticulatedWordResult:
    """Solved trajectory and placed via-point metadata for one word."""

    word: str
    w_nib_mm: float
    x_height_mm: float
    baseline_y_mm: float
    dt_s: float
    samples: tuple[SandboxSample, ...]
    placed_via_points: tuple[PlacedViaPoint, ...]
    solved_x_wnib: np.ndarray
    solved_y_wnib: np.ndarray


def _build_banded_smoothness_matrix(
    n: int,
    w_jerk: float,
    w_acc: float,
    substeps_per_segment: int = 8,
) -> np.ndarray:
    """Build upper-triangular banded representation `ab` (4 x n) of scaled D3^T D3 + D2^T D2."""
    # Scale finite-difference operators by segment density so weights are step-invariant
    ab = np.zeros((4, n), dtype=np.float64)
    s_jerk = w_jerk * (substeps_per_segment ** 5)
    s_acc = w_acc * (substeps_per_segment ** 3)

    # Accumulate D3^T D3 (stencil [-1, 3, -3, 1] for rows 0..n-4)
    if n >= 4 and s_jerk > 0:
        c3 = np.array([-1.0, 3.0, -3.0, 1.0], dtype=np.float64)
        for d in range(4):
            for k in range(4 - d):
                start_j = d + k
                end_j = (n - 4) + d + k + 1
                ab[3 - d, start_j:end_j] += s_jerk * c3[k] * c3[k + d]

    # Accumulate D2^T D2 (stencil [1, -2, 1] for rows 0..n-3)
    if n >= 3 and s_acc > 0:
        c2 = np.array([1.0, -2.0, 1.0], dtype=np.float64)
        for d in range(3):
            for k in range(3 - d):
                start_j = d + k
                end_j = (n - 3) + d + k + 1
                ab[3 - d, start_j:end_j] += s_acc * c2[k] * c2[k + d]

    return ab


@dataclass(frozen=True)
class StatefulLineResult:
    """Solved trajectory and word metadata for a full line with ScribeState carryover."""

    line_text: str
    line_index: int
    word_results: tuple[CoarticulatedWordResult, ...]
    samples: tuple[SandboxSample, ...]
    vias: list[dict]


def solve_word_coarticulation(
    word: str,
    *,
    profile: HandProfile | None = None,
    start_x_wnib: float = 1.2,
    baseline_y_mm: float | None = None,
    substeps_per_segment: int = 14,
    w_jerk: float = 0.0045,
    w_acc: float = 0.025,
    dt_s: float = 0.005,
    session: KinematicScribeSession | None = None,
    next_word_len: int = 0,
    is_line_end: bool = False,
) -> CoarticulatedWordResult:
    """Solve the global Minimum-Jerk Via-Point QP for `word`."""
    prof = profile or bastarda_nib_calibrated_profile()
    w_nib = prof.nib.width_mm
    xh = prof.letterform.x_height_mm
    base_y_mm = baseline_y_mm if baseline_y_mm is not None else xh * 2.1
    nib_angle = prof.nib.angle_deg
    spacing_norm = getattr(prof, "letter_spacing_norm", 1.0) or 1.0

    cursor_wnib = start_x_wnib
    raw_vias: list[tuple[str, int, int, ViaPoint, float, float, float]] = []

    for l_idx, ch in enumerate(word):
        recipe = select_contextual_viapoint_recipe(word, l_idx)
        if session is not None:
            var = session.next_letter_variation(
                recipe.letter,
                is_word_initial=(l_idx == 0),
                prev_word_exit_y_wnib=session.last_word_exit_y_wnib,
            )
        else:
            var = {
                "dx_wnib": 0.0,
                "dy_wnib": 0.0,
                "slant_shear": 0.0,
                "peak_arch_dy": 0.0,
                "x_scale": 1.0,
                "y_scale": 1.0,
                "entry_hook_dx": 0.0,
                "entry_hook_dy": 0.0,
                "loop_spread_dx": 0.0,
                "loop_height_dy": 0.0,
                "nib_angle_drift_deg": 0.0,
            }

        for v_idx, vp in enumerate(recipe.via_points):
            x_v = vp.x_wnib * var["x_scale"] + var["dx_wnib"] + (vp.y_wnib / 4.2) * var["slant_shear"]
            y_v = vp.y_wnib * var.get("y_scale", 1.0) + var["dy_wnib"]
            p_v = vp.pressure
            if vp.role in ("peak", "turn"):
                y_v += var["peak_arch_dy"]
            elif vp.role == "loop" or vp.y_wnib > 4.4 or vp.y_wnib < -0.4:
                x_v += var["loop_spread_dx"]
                y_v += var["loop_height_dy"]
            if l_idx == 0 and v_idx == 0:
                x_v += var["entry_hook_dx"]
                y_v += var["entry_hook_dy"]
            elif l_idx == 0 and v_idx == 1:
                x_v += 0.45 * var["entry_hook_dx"]
                y_v += 0.25 * var["entry_hook_dy"]

            if session is not None:
                v_dx, v_dy, v_dp = session.viapoint_internal_nuance(
                    recipe.letter,
                    int(var.get("occ", 0)),
                    v_idx,
                    vp.role,
                    is_word_initial=(l_idx == 0),
                )
                x_v += v_dx
                y_v += v_dy
                if vp.contact:
                    p_v = max(0.18, min(0.96, p_v + v_dp))
                vp = ViaPoint(
                    x_wnib=vp.x_wnib,
                    y_wnib=vp.y_wnib,
                    sigma_x_wnib=vp.sigma_x_wnib,
                    sigma_y_wnib=vp.sigma_y_wnib,
                    vx_pref_wnib=vp.vx_pref_wnib,
                    vy_pref_wnib=vp.vy_pref_wnib,
                    velocity_weight=vp.velocity_weight,
                    contact=vp.contact,
                    pressure=p_v,
                    role=vp.role,
                )

            raw_vias.append(
                (recipe.letter, l_idx, v_idx, vp, cursor_wnib + x_v, y_v, var["nib_angle_drift_deg"])
            )
        cursor_wnib += recipe.advance_wnib * var["x_scale"] * spacing_norm

    k_pts = len(raw_vias)
    if k_pts == 0:
        return CoarticulatedWordResult(
            word=word,
            w_nib_mm=w_nib,
            x_height_mm=xh,
            baseline_y_mm=base_y_mm,
            dt_s=dt_s,
            samples=(),
            placed_via_points=(),
            solved_x_wnib=np.zeros(0),
            solved_y_wnib=np.zeros(0),
        )

    n_samples = (k_pts - 1) * substeps_per_segment + 1
    ab_base = _build_banded_smoothness_matrix(
        n_samples, w_jerk=w_jerk, w_acc=w_acc, substeps_per_segment=substeps_per_segment
    )
    ab_x = ab_base.copy()
    ab_y = ab_base.copy()
    bx = np.zeros(n_samples, dtype=np.float64)
    by = np.zeros(n_samples, dtype=np.float64)

    placed: list[PlacedViaPoint] = []
    for k, (ch, l_idx, v_idx, vp, x_w, y_w, _) in enumerate(raw_vias):
        s_idx = k * substeps_per_segment
        wx = 1.0 / max(1e-4, vp.sigma_x_wnib ** 2)
        wy = 1.0 / max(1e-4, vp.sigma_y_wnib ** 2)
        ab_x[3, s_idx] += wx
        ab_y[3, s_idx] += wy
        bx[s_idx] += wx * x_w
        by[s_idx] += wy * y_w

        placed.append(
            PlacedViaPoint(
                letter=ch,
                letter_index=l_idx,
                local_index=v_idx,
                role=vp.role,
                sample_index=s_idx,
                x_wnib=x_w,
                y_wnib=y_w,
                x_mm=x_w * w_nib,
                y_mm=base_y_mm - y_w * w_nib,
                sigma_x_wnib=vp.sigma_x_wnib,
                sigma_y_wnib=vp.sigma_y_wnib,
                pressure=vp.pressure,
                contact=vp.contact,
            )
        )

    sol_x = solveh_banded(ab_x, bx, lower=False, overwrite_ab=True, overwrite_b=True, check_finite=False)
    sol_y = solveh_banded(ab_y, by, lower=False, overwrite_ab=True, overwrite_b=True, check_finite=False)

    # Convert solved w_nib coordinates to physical mm (y-down canvas frame)
    x_mm_arr = sol_x * w_nib
    y_mm_arr = base_y_mm - sol_y * w_nib

    vx_arr = np.gradient(x_mm_arr, dt_s)
    vy_arr = np.gradient(y_mm_arr, dt_s)

    emo = session.active_emotion if session is not None else None
    emo_p_mult = emo.pressure_mult if emo is not None else 1.0
    emo_speed_mult = emo.speed_mult if emo is not None else 1.0
    emo_tremor_mm = emo.tremor_amp_mm if emo is not None else 0.0
    emo_name = emo.state_name if emo is not None else "standard"

    pressure_scale = (prof.folio.base_pressure / 0.72 if prof.folio else 1.0) * emo_p_mult
    samples: list[SandboxSample] = []
    for idx in range(n_samples):
        seg_k = min(k_pts - 2, idx // substeps_per_segment) if k_pts > 1 else 0
        u = (idx - seg_k * substeps_per_segment) / max(1, substeps_per_segment)
        p_a = placed[seg_k]
        p_b = placed[min(k_pts - 1, seg_k + 1)]
        angle_drift = raw_vias[seg_k][6]

        # Smooth cosine interpolation of target pressure, smoothly lightened on rising strokes
        p_interp = (p_a.pressure + (0.5 - 0.5 * math.cos(math.pi * u)) * (p_b.pressure - p_a.pressure)) * pressure_scale
        # In grief_hesitation, pressure tapers slightly across the word as the scribe's hand hesitates
        if emo_name == "grief_hesitation":
            word_prog = idx / max(1, n_samples - 1)
            p_interp *= (1.06 - 0.18 * word_prog)
        # Smoothly blend toward hairline pressure (0.28) when moving upward (vy_arr[idx] < 0 in y-down canvas)
        upward_blend = 0.5 * (1.0 - math.tanh(vy_arr[idx] / 1.5))
        p_eff = p_interp * (1.0 - upward_blend) + 0.28 * upward_blend
        p_eff = max(0.18, min(1.05, p_eff))

        is_contact = p_a.contact and p_b.contact
        cur_reservoir = session.state.ink_level if session is not None else 0.85
        if session is not None and idx > 0 and is_contact:
            seg_dist = math.hypot(float(x_mm_arr[idx] - x_mm_arr[idx - 1]), float(y_mm_arr[idx] - y_mm_arr[idx - 1]))
            cur_reservoir = session.state.consume_contact_distance(seg_dist, avg_pressure=float(p_eff), avg_width_mm=w_nib)
            # TD-021: Do NOT multiply mechanical pressure by optical darkness_scale() (avoids squared depletion).
            # Instead, as the quill enters the dry shoulder (<0.38), the scribe subtly presses up to +2.5%
            # harder to coax capillary ink from the slit, while optical darkness is owned once by the renderer.
            if cur_reservoir < 0.38:
                coax = max(0.0, min(1.0, (0.38 - cur_reservoir) / 0.22))
                p_eff = max(0.18, min(1.05, p_eff * (1.0 + 0.025 * coax)))

        # Apply subtle low-frequency hand micro-unsteadiness only when emotional agitation or grief elevates it
        tx_mm = 0.0
        ty_mm = 0.0
        if emo_tremor_mm > 0.020 and is_contact:
            eff_tremor_mm = min(0.026, emo_tremor_mm * 0.42)
            t_phase = idx * 0.24 + (session.word_counter * 1.9 if session else 0.0)
            tx_mm = eff_tremor_mm * math.sin(t_phase)
            ty_mm = 0.55 * eff_tremor_mm * math.cos(t_phase * 1.21)

        role = "join" if (p_a.letter_index != p_b.letter_index or p_b.role in ("exit", "peak", "loop")) else "body"
        samples.append(
            SandboxSample(
                x_mm=float(x_mm_arr[idx]) + tx_mm,
                y_mm=float(y_mm_arr[idx]) + ty_mm,
                vx_mm_s=float(vx_arr[idx]) * emo_speed_mult,
                vy_mm_s=float(vy_arr[idx]) * emo_speed_mult,
                contact=is_contact,
                pressure=float(p_eff),
                nib_angle_deg=nib_angle + angle_drift,
                letter=p_a.letter if u < 0.5 else p_b.letter,
                role=role,
                ink_reservoir=float(cur_reservoir),
                emotional_state=emo_name,
            )
        )

    if session is not None:
        session.last_word_exit_y_wnib = float(sol_y[-1])
        session.word_counter += 1
        from scribesim.ink.cycle import DipEvent
        pre_dip_res = round(float(session.state.ink_level), 4)
        dip_ev = session.state.ink_state.process_word_boundary(
            word_text=word,
            next_word_len=next_word_len,
            is_line_end=is_line_end,
            attention=session.dip_attention_factor(),
        )
        if dip_ev in (DipEvent.ForcedDip, DipEvent.PreferredDip):
            session.dip_events.append(
                {
                    "folio_id": session.folio_id,
                    "line_index": session.current_line,
                    "word_counter": session.word_counter,
                    "word": word,
                    "pre_dip_reservoir": pre_dip_res,
                    "trigger": session.state.ink_state.last_dip_trigger,
                    "reason": "forced_dip" if dip_ev == DipEvent.ForcedDip else "preferred_dip",
                }
            )

    return CoarticulatedWordResult(
        word=word,
        w_nib_mm=w_nib,
        x_height_mm=xh,
        baseline_y_mm=base_y_mm,
        dt_s=dt_s,
        samples=tuple(samples),
        placed_via_points=tuple(placed),
        solved_x_wnib=sol_x,
        solved_y_wnib=sol_y,
    )


def compose_line_kinematic_Stateful(
    line_text: str,
    *,
    session: KinematicScribeSession | None = None,
    line_index: int = 0,
    profile: HandProfile | None = None,
    register: str = "de",
) -> StatefulLineResult:
    """Compose a full line of words with ScribeState, word-initial attack, EmotionalLineState, and InkState."""
    sess = session or KinematicScribeSession(folio_id="f01r", seed=1457)
    sess.advance_to_line(line_index, line_text=line_text, register=register)

    prof = profile or resolve_clio7_kinematic_profile(sess.folio_id, line_index=line_index)
    w_nib = prof.nib.width_mm
    xh = prof.letterform.x_height_mm
    emo = sess.active_emotion
    baseline_sag_mm = sess.state.baseline_drift_mm(line_index) + emo.baseline_undulation_mm * math.sin(line_index * 1.7)
    # Accumulate line y-positions using standard 3.5mm spacing for lines before a register scale change
    base_xh = 3.5
    if xh < base_xh and line_index >= 16:
        baseline_y_mm = base_xh * 2.1 + 16 * (base_xh * 2.5) + (line_index - 16) * (xh * 2.5) + baseline_sag_mm
    else:
        baseline_y_mm = xh * 2.1 + line_index * (xh * 2.5) + baseline_sag_mm

    word_gap_wnib = 2.2 * (prof.word.spacing_mean_ratio / 1.2) * emo.word_gap_mult
    cursor_wnib = 1.2
    word_results: list[CoarticulatedWordResult] = []
    line_samples: list[SandboxSample] = []
    line_vias: list[dict] = []

    tokens = line_text.split(" ")
    nonempty_indices = [idx for idx, tok in enumerate(tokens) if tok]
    last_nonempty_idx = nonempty_indices[-1] if nonempty_indices else -1

    for tok_i, w in enumerate(tokens):
        if not w:
            cursor_wnib += word_gap_wnib
            continue
        next_len = 0
        for nxt_tok in tokens[tok_i + 1 :]:
            if nxt_tok:
                next_len = len(nxt_tok)
                break
        res = solve_word_coarticulation(
            w,
            profile=prof,
            start_x_wnib=cursor_wnib,
            baseline_y_mm=baseline_y_mm,
            session=sess,
            next_word_len=next_len,
            is_line_end=(tok_i == last_nonempty_idx),
        )
        word_results.append(res)
        if line_samples and res.samples:
            prev_s = line_samples[-1]
            first_s = res.samples[0]
            line_samples.append(
                SandboxSample(
                    x_mm=0.5 * (prev_s.x_mm + first_s.x_mm),
                    y_mm=0.5 * (prev_s.y_mm + first_s.y_mm) - 0.8 * w_nib,
                    vx_mm_s=0.0,
                    vy_mm_s=0.0,
                    contact=False,
                    pressure=0.0,
                    nib_angle_deg=prof.nib.angle_deg,
                    letter=" ",
                    role="air",
                )
            )
        line_samples.extend(res.samples)
        for vp in res.placed_via_points:
            line_vias.append(
                {
                    "x_mm": vp.x_mm,
                    "y_mm": vp.y_mm,
                    "sigma_x_mm": vp.sigma_x_wnib * w_nib,
                    "sigma_y_mm": vp.sigma_y_wnib * w_nib,
                    "role": "boundary" if vp.role in ("entry", "exit") else "body",
                    "letter": vp.letter,
                }
            )
        last_x_wnib = float(res.solved_x_wnib[-1]) if len(res.solved_x_wnib) else cursor_wnib
        cursor_wnib = last_x_wnib + word_gap_wnib

    return StatefulLineResult(
        line_text=line_text,
        line_index=line_index,
        word_results=tuple(word_results),
        samples=tuple(line_samples),
        vias=line_vias,
    )


def compose_text_kinematic(
    text: str,
    *,
    profile: HandProfile | None = None,
    folio_id: str = "f01r",
    seed: int = 1457,
    use_state: bool = True,
) -> tuple[list[SandboxSample], list[dict]]:
    """Compose multi-word/multi-line text using the global minimum-jerk coarticulation solver."""
    session = KinematicScribeSession(folio_id=folio_id, seed=seed) if use_state else None
    lines = text.splitlines() or [text]
    all_samples: list[SandboxSample] = []
    all_vias: list[dict] = []

    for line_idx, line in enumerate(lines):
        if session is not None:
            l_res = compose_line_kinematic_Stateful(
                line, session=session, line_index=line_idx, profile=profile
            )
            all_samples.extend(l_res.samples)
            all_vias.extend(l_res.vias)
        else:
            prof = profile or bastarda_nib_calibrated_profile()
            w_nib = prof.nib.width_mm
            xh = prof.letterform.x_height_mm
            baseline_y_mm = xh * 2.1 + line_idx * (xh * 2.5)
            cursor_wnib = 1.2
            for w in line.split(" "):
                if not w:
                    cursor_wnib += 2.2
                    continue
                res = solve_word_coarticulation(
                    w, profile=prof, start_x_wnib=cursor_wnib, baseline_y_mm=baseline_y_mm
                )
                all_samples.extend(res.samples)
                for vp in res.placed_via_points:
                    all_vias.append(
                        {
                            "x_mm": vp.x_mm,
                            "y_mm": vp.y_mm,
                            "sigma_x_mm": vp.sigma_x_wnib * w_nib,
                            "sigma_y_mm": vp.sigma_y_wnib * w_nib,
                            "role": "boundary" if vp.role in ("entry", "exit") else "body",
                            "letter": vp.letter,
                        }
                    )
                last_x_wnib = float(res.solved_x_wnib[-1]) if len(res.solved_x_wnib) else cursor_wnib
                cursor_wnib = last_x_wnib + 2.2

    return all_samples, all_vias
