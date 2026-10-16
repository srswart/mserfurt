---
advance:
  id: "ADV-SS-TUNING-002"
  title: "Differentiable Nib Renderer & Reference Word Grounding"
  system: "scribesim"
  primary_component: "tuning"
  components: ["tuning", "annotate", "handvalidate", "tests"]
  started_at: "2026-10-16T04:45:00+00:00"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  # Populated by `arrive usage import` / the LiteLLM callback — leave empty when authoring.
  model_usage: []
  status: planned
---

## Objective

Unblock real manuscript reference grounding by confirming ~30 clean BSB reference word crops with soft baseline-band weighting, and implement a differentiable PyTorch broad-nib ribbon renderer (`scribesim/tuning/diff_render.py`) to refine shared via-point coordinates $\mu_k$, tolerances $\Sigma_k$, and stroke-type nib angle drift (`TD-013`) via gradient optimization, culminating in **Human Checkpoint #2** on the 3-line proof specimen.

Follows [TD-019 — Kinematic Coarticulation, Bastarda Proportions, and Hybrid Evaluation](../../../../docs/tech-direction/TD-019-kinematic-coarticulation-and-evaluation.md) (§2 Pillar 3, §4 Tier 2 & Tier 3, §5 Phase 16b).

## Behavioral Change

After this advance:
- Reference word crops from the BSB anchor manuscript are admitted via verified transcription + baseline/x-height box and evaluated with a smooth vertical window centered on the `[baseline, x_height]` core band, removing the brittle binary connected-component mask lockout that blocked `G0` in Pass 15.
- `scribesim/tuning/diff_render.py` provides a differentiable soft-SDF broad-nib quad sweep in PyTorch, enabling `Adam` / `L-BFGS` optimization of shared via-point parameters ($\mu_k, \Sigma_k$, advance, and subtle stroke-type nib angle drift) in seconds rather than thousands of black-box `CMA-ES` evaluations.
- The 3-line proof specimen (1. reconstructed reference words, 2. unseen words, 3. MS Erfurt project text line) passes Tier-1 checks, improves reference distribution alignment (`B2-ANGLE-EMD`, `B3-RHYTHM-ACF`), and is reviewed by the owner in `scribesim review-sheet` (**Human Checkpoint #2**).

## Component Impact

Primary component: `tuning`. Impacted components: `tuning`, `annotate`, `handvalidate`, `tests`.

- `scribesim/tuning/diff_render.py` (differentiable broad-nib ribbon renderer and gradient-based via-point refiner)
- `scribesim/annotate/reference_confirm.py` (streamlined CLI/workbench helper to confirm ~30 BSB reference words with baseline-band weights)
- `shared/hands/konrad_kinematic_v1.toml` (fitted via-point and nib parameters)
- `tests/test_diff_render.py` (unit tests for soft-quad gradients, parameter updates, and Tier-1 preservation during refinement)

## Dependencies

- [ADV-SS-GUIDES-002](ADV-SS-GUIDES-002.md)
- [ADV-SS-ANNOTATE-007](ADV-SS-ANNOTATE-007.md)

## Planned Implementation Tasks

- [ ] branch: create or confirm feature branch for this advance
- [ ] tidy: preparatory cleanup of shared loss utilities in `scribesim/tuning/` (no behavior change)
- [ ] test: add failing unit tests for differentiable quad SDF forward/backward gradients, baseline-band loss weighting, and bounded via-point refinement preserving `A1–A4` invariants
- [ ] feat/fix: implement `scribesim/tuning/diff_render.py`, confirm ~30 BSB reference word crops, and run bounded gradient refinement of the shared `ViaPointRecipe` catalog
- [ ] review: capture owner visual review for **Human Checkpoint #2** (3-line specimen) in `shared/training/reviews/checkpoint-2-specimen.json`

## Bug Fixes

- [ ] None yet

## Risk + Rollback

- Risk: Unconstrained gradient descent on image overlap can overfit noisy reference crops or collapse counters. Mitigate by optimizing only shared recipe parameters (never per-word instance residuals), clamping displacements within prior envelopes, and enforcing `A1–A4` structural penalties.
- Rollback: Revert to the pre-refinement `ViaPointRecipe` catalog from `ADV-SS-GUIDES-002`.

## Evidence

- [ ] tidy:preparatory
- [ ] tdd:red-green
- [ ] tests:unit
- [ ] review:owner

## CI Evidence Notes

- If CI jobs are enabled, link pipeline evidence (`ci:passed`) from PR/MR and default-branch runs.
- If CI jobs are temporarily disabled, run checks externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-TUNING-002 --status passed` (include provider/run metadata when available)
  - Optional combined flow when provider lookup is available:
    - `arrive pr check --provider-status --advance ADV-SS-TUNING-002 --record-ci-evidence --json`

## Changes Made

### 2026-10-16 - docs: Draft ADV-SS-TUNING-002 for TD-019 Pass 16b
- `arrive/systems/scribesim/advances/ADV-SS-TUNING-002.md`: Created planned advance record for the Differentiable Nib Renderer and Reference Word Grounding.
