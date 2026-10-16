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


def solve_word_coarticulation(
    word: str,
    *,
    profile: HandProfile | None = None,
    start_x_wnib: float = 1.2,
    baseline_y_mm: float | None = None,
    substeps_per_segment: int = 8,
    w_jerk: float = 0.0045,
    w_acc: float = 0.025,
    dt_s: float = 0.008,
) -> CoarticulatedWordResult:
    """Solve the global Minimum-Jerk Via-Point QP for `word`."""
    prof = profile or bastarda_nib_calibrated_profile()
    w_nib = prof.nib.width_mm
    xh = prof.letterform.x_height_mm
    base_y_mm = baseline_y_mm if baseline_y_mm is not None else xh * 2.1
    nib_angle = prof.nib.angle_deg

    cursor_wnib = start_x_wnib
    raw_vias: list[tuple[str, int, int, ViaPoint, float, float]] = []

    for l_idx, ch in enumerate(word):
        recipe = select_contextual_viapoint_recipe(word, l_idx)
        for v_idx, vp in enumerate(recipe.via_points):
            raw_vias.append(
                (recipe.letter, l_idx, v_idx, vp, cursor_wnib + vp.x_wnib, vp.y_wnib)
            )
        cursor_wnib += recipe.advance_wnib

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
    for k, (ch, l_idx, v_idx, vp, x_w, y_w) in enumerate(raw_vias):
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

    samples: list[SandboxSample] = []
    for idx in range(n_samples):
        seg_k = min(k_pts - 2, idx // substeps_per_segment) if k_pts > 1 else 0
        u = (idx - seg_k * substeps_per_segment) / max(1, substeps_per_segment)
        p_a = placed[seg_k]
        p_b = placed[min(k_pts - 1, seg_k + 1)]

        # Smooth cosine interpolation of target pressure, modulated by vertical travel direction
        p_interp = p_a.pressure + (0.5 - 0.5 * math.cos(math.pi * u)) * (p_b.pressure - p_a.pressure)
        # Rising strokes (vy_mm_s < 0 in y-down canvas) naturally lighten pressure
        if vy_arr[idx] < -0.5:
            p_eff = min(p_interp, 0.30)
        else:
            p_eff = p_interp

        role = "join" if (p_a.letter_index != p_b.letter_index or p_b.role in ("exit", "peak", "loop")) else "body"
        samples.append(
            SandboxSample(
                x_mm=float(x_mm_arr[idx]),
                y_mm=float(y_mm_arr[idx]),
                vx_mm_s=float(vx_arr[idx]),
                vy_mm_s=float(vy_arr[idx]),
                contact=p_a.contact and p_b.contact,
                pressure=float(p_eff),
                nib_angle_deg=nib_angle,
                letter=p_a.letter if u < 0.5 else p_b.letter,
                role=role,
            )
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


def compose_text_kinematic(
    text: str,
    *,
    profile: HandProfile | None = None,
) -> tuple[list[SandboxSample], list[dict]]:
    """Compose multi-word/multi-line text using the global minimum-jerk coarticulation solver."""
    prof = profile or bastarda_nib_calibrated_profile()
    w_nib = prof.nib.width_mm
    xh = prof.letterform.x_height_mm

    lines = text.splitlines() or [text]
    all_samples: list[SandboxSample] = []
    all_vias: list[dict] = []

    for line_idx, line in enumerate(lines):
        baseline_y_mm = xh * 2.1 + line_idx * (xh * 2.5)
        cursor_wnib = 1.2
        words = line.split(" ")
        for w in words:
            if not w:
                cursor_wnib += 2.2
                continue
            res = solve_word_coarticulation(
                w,
                profile=prof,
                start_x_wnib=cursor_wnib,
                baseline_y_mm=baseline_y_mm,
            )
            if all_samples and res.samples:
                # Insert pen-up air transition sample between words
                prev_s = all_samples[-1]
                first_s = res.samples[0]
                all_samples.append(
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
