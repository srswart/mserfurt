---
advance:
  id: "ADV-SS-HANDFLOW-012"
  title: "Global Minimum-Jerk Via-Point Coarticulation Solver"
  system: "scribesim"
  primary_component: "handflow"
  components: ["handflow", "guides", "tests"]
  started_at: "2026-10-16T04:45:00+00:00"
  implementation_completed_at: 2026-10-16T18:34:20.094719Z
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tidy:preparatory", "tdd:red-green", "tests:unit"]
  # Populated by `arrive usage import` / the LiteLLM callback — leave empty when authoring.
  model_usage: []
  status: complete
---

## Objective

Replace pairwise cubic spline-splicing with a global Minimum-Jerk Via-Point Quadratic Programming (QP) trajectory solver (`scribesim/handflow/coarticulate.py`) over nib-normalized `ViaPointRecipe` definitions for the starter Bastarda inventory (`i, n, u, m, d, e, r`).

Follows [TD-019 — Kinematic Coarticulation, Bastarda Proportions, and Hybrid Evaluation](../../../../docs/tech-direction/TD-019-kinematic-coarticulation-and-evaluation.md) (§2 Pillar 2, §4 Tier 1 `A2-KINEMATICS` and `A3-COARTICULATE`).

## Behavioral Change

After this advance:
- Letters are defined declaratively as `ViaPointRecipe` sequences with target positions $\mu_k$ (in $w_{\text{nib}}$ units), $2\times 2$ spatial tolerance covariance matrices $\Sigma_k$ (tight on protected stem cores, flexible on exit feet and entry crowns), preferred velocities $v_k^{\text{pref}}$, and contact/pressure states.
- Word trajectories are solved globally in $<1\text{ ms}$ via a banded minimum-jerk QP:
  $$\min_{x(t), y(t)} \int_0^T \left(\|\dddot{x}(t)\|^2 + \lambda_v \|\ddot{x}(t)\|^2\right) dt + \sum_{k=1}^K (x(t_k) - \mu_k)^\top \Sigma_k^{-1} (x(t_k) - \mu_k) + \sum_{k \in \mathcal{D}} \gamma_k \|\dot{x}(t_k) - v_k^{\text{pref}}\|^2$$
- Reciprocal letter-to-letter coarticulation (`nu`, `nm`, `um`, `nn`, `und`, `der`, `mir`) emerges automatically from the global trajectory optimization with zero pair-specific cubic cuts or rational self-contact proofs.
- Automated Tier-1 checks `A2-KINEMATICS` (bounded dimensionless jerk, bell-shaped velocity profiles) and `A3-COARTICULATE` (nonzero bounded reciprocal adaptation $0.03\,w_{\text{nib}} \le \Delta_{\text{coart}} \le 0.35\,w_{\text{nib}}$) pass across all starter pairs and words.

## Component Impact

Primary component: `handflow`. Impacted components: `handflow`, `guides`, `tests`.

- `scribesim/handflow/coarticulate.py` (banded Minimum-Jerk QP solver and word trajectory assembly)
- `scribesim/guides/viapoint.py` (`ViaPoint`, `ViaPointRecipe`, and starter Bastarda definitions for `i, n, u, m, d, e, r`)
- `scribesim/handvalidate/kinematic_gates.py` (`A2-KINEMATICS` and `A3-COARTICULATE` automated evaluators)
- `tests/test_coarticulate.py` (unit and kinematic invariant tests)

## Dependencies

- [ADV-SS-HAND-004](ADV-SS-HAND-004.md)

## Planned Implementation Tasks

- [x] branch: create or confirm feature branch for this advance (`feat/adv-ss-handflow-012`)
- [x] tidy: preparatory refactoring to expose shared trajectory sample conversions in `scribesim/handflow/` (no behavior change)
- [x] test: add failing unit tests for `ViaPointRecipe` validation, minimum-jerk QP solver optimality/$C^2$ continuity, `A2-KINEMATICS` jerk bounds, and `A3-COARTICULATE` reciprocal neighbor adaptation (`nu` vs `nm` vs isolated `n` and `u`)
- [x] feat/fix: implement `scribesim/guides/viapoint.py`, `scribesim/handflow/coarticulate.py`, and starter recipes for `i, n, u, m, d, e, r`

## Bug Fixes

- [x] Scaled finite-difference smoothness operators ($D_3^\top D_3, D_2^\top D_2$) by segment substep density and solved via `scipy.linalg.solveh_banded` so coarticulation stiffness is step-invariant and solves in $<1\text{ ms}$.

## Risk + Rollback

- Risk: Overly loose tolerance covariances $\Sigma_k$ on stem via-points could allow fast words to Slur or tilt stems excessively. Mitigate with anisotropic $\Sigma_k$ (tight horizontal variance on vertical stems, looser tangential variance at turns) validated by `A3-COARTICULATE`.
- Rollback: Revert `scribesim/handflow/coarticulate.py` and `scribesim/guides/viapoint.py`; existing `GuidedHandFlowController` and `evo` paths remain untouched.

## Evidence

- [x] tidy:preparatory
- [x] tdd:red-green
- [x] tests:unit

## CI Evidence Notes

- If CI jobs are enabled, link pipeline evidence (`ci:passed`) from PR/MR and default-branch runs.
- If CI jobs are temporarily disabled, run checks externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-HANDFLOW-012 --status passed` (include provider/run metadata when available)
  - Optional combined flow when provider lookup is available:
    - `arrive pr check --provider-status --advance ADV-SS-HANDFLOW-012 --record-ci-evidence --json`

## Changes Made

### 2026-10-16 - docs: Draft ADV-SS-HANDFLOW-012 for TD-019 Pass 16a
- `arrive/systems/scribesim/advances/ADV-SS-HANDFLOW-012.md`: Created planned advance record for the Global Minimum-Jerk Via-Point Coarticulation Solver.

### 2026-10-16 - tidy: add TrackPlanSample.to_trajectory_sample conversion helper
- `scribesim/handflow/model.py`: Added `to_trajectory_sample()` method on `TrackPlanSample`.

### 2026-10-16 - test: add via-point catalog, minimum-jerk coarticulation solver, and A2/A3 gate tests
- `tests/test_coarticulate.py`: Added unit tests covering starter `ViaPointRecipe` definitions (`i, n, u, m, d, e, r`), solver execution speed ($<15\text{ ms}$), Tier-1 `A2-KINEMATICS`, Tier-1 `A3-COARTICULATE` reciprocal neighbor adaptation (`nu` vs `nm` vs isolated `n`/`u`), and sandbox integration.

### 2026-10-16 - feat: implement global minimum-jerk via-point coarticulation solver and A2/A3 gates
- `scribesim/guides/viapoint.py`: Implemented `ViaPoint`, `ViaPointRecipe`, `VIAPOINT_STARTER_CATALOG` (`i, n, u, m, d, e, r`), and `lookup_viapoint_recipe()`.
- `scribesim/handflow/coarticulate.py`: Implemented `solve_word_coarticulation()` using `scipy.linalg.solveh_banded` over the 7-diagonal minimum-jerk + acceleration quadratic form and `compose_text_kinematic()`.
- `scribesim/handvalidate/kinematic_gates.py`: Implemented `evaluate_a2_kinematics()` and `evaluate_a3_coarticulate()`.
- `scribesim/render/nib.py`: Added unloaded rising hairline release in `chisel_apparent_width_mm()`.

## Check for Understanding

1. How does the 7-diagonal banded matrix in `solve_word_coarticulation()` couple the exit trajectory of `n` to the entry height of the following letter (`u` vs `m`) without pair-specific splice rules?
2. Why do `role="body"` stem via-points use $\sigma_x \approx 0.015\text{–}0.02\,w_{\text{nib}}$ while `role="entry"` and `role="exit"` via-points use $\sigma \approx 0.16\text{–}0.26\,w_{\text{nib}}$?
3. What three quantities does `evaluate_a3_coarticulate()` compare to verify both reciprocal boundary adaptation and protected stem stability?

