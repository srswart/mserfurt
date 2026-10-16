---
advance:
  id: "ADV-SS-HAND-004"
  title: "Bastarda Nib-Width Proportions, Natural Chisel Contact & Fast Sandbox CLI"
  system: "scribesim"
  primary_component: "hand"
  components: ["hand", "render", "cli", "tests"]
  started_at: "2026-10-16T04:45:00+00:00"
  implementation_completed_at: 2026-10-16T18:28:53.338456Z
  review_time_estimate_minutes: 30
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

Recalibrate the Bastarda hand profile and broad-nib contact model to historical nib-width ($w_{\text{nib}}$) proportions ($H = 4.2\,w_{\text{nib}}$, $w_{\text{nib}} = 0.83\text{ mm}$ for $H = 3.5\text{ mm}$) and provide a fast, zero-lockout `scribesim sandbox` CLI command for sub-second visual and kinematic iteration.

Follows [TD-019 — Kinematic Coarticulation, Bastarda Proportions, and Hybrid Evaluation](../../../../docs/tech-direction/TD-019-kinematic-coarticulation-and-evaluation.md) (§2 Pillar 1 & Pillar 4, §4 Tier 1 `A1-PROPORTION`).

## Behavioral Change

After this advance:
- Hand geometry and letter spacing can be specified in nib-width ($w_{\text{nib}}$) units so x-height ($4.2\,w_{\text{nib}}$) and minim bay width ($1.1\text{–}1.2\,w_{\text{nib}}$) reflect authentic 15th-century German Bastarda proportions rather than a thin pointed pen ($1:7.8$).
- Broad-edge polygon sweep naturally produces crisp $40^\circ$ hairline upstrokes when moving parallel to the chisel edge, plus pressure-driven tine splay and velocity-minimum ink pooling at turns (forming diamond feet and clubbed heads without artificial 10%-corner step schedules).
- `scribesim sandbox <text>` renders single words, bigrams, or 3-line specimens in $<0.5\text{ s}$ alongside an interactive HTML diagnostic sheet (1:1 ink render + kinematic/nib overlay + Tier-1 `A1-PROPORTION` metrics) without blocking image output on hash-pin lockouts.

## Component Impact

Primary component: `hand`. Impacted components: `hand`, `render`, `cli`, `tests`.

- `scribesim/hand/profile.py` and `shared/hands/konrad_erfurt_1457.toml` (nib-width proportion helpers and calibrated Bastarda defaults)
- `scribesim/render/nib.py` and `scribesim/render/sandbox.py` (true chisel projection with tine splay, turn pooling, and fast sandbox HTML/PNG emitter)
- `scribesim/cli.py` (`scribesim sandbox` subcommand)
- `tests/test_bastarda_proportions.py` (Tier-1 `A1-PROPORTION` and sandbox CLI tests)

## Dependencies

- [ADV-SS-HAND-003](ADV-SS-HAND-003.md)
- [ADV-SS-RENDER-005](ADV-SS-RENDER-005.md)

## Planned Implementation Tasks

- [x] branch: create or confirm feature branch for this advance (`feat/adv-ss-hand-004`)
- [x] tidy: preparatory refactoring of nib-width conversion helpers in `scribesim/hand/` (no behavior change)
- [x] test: add failing unit tests for $w_{\text{nib}}$ proportion scaling, $40^\circ$ natural hairline projection, turn pooling, Tier-1 `A1-PROPORTION` ($P_{95}/P_{05} \in [3.2, 5.0]$, $H/w_{\text{nib}} \in [3.8, 4.6]$), and `scribesim sandbox` output
- [x] feat/fix: implement nib-width calibration, tine splay + velocity-minimum turn pooling, and `scribesim sandbox` CLI + HTML diagnostic view

## Bug Fixes

- [x] Avoided eager import of `scribesim.handflow.__init__` in `scribesim/render/sandbox.py` so cold-start sandbox renders complete in ~0.04s (<0.5s target).

## Risk + Rollback

- Risk: Changing default nib width in `konrad_erfurt_1457.toml` could alter legacy golden image assertions if not scoped to the kinematic/calibrated preset or opt-in flag.
- Rollback: Keep legacy `evo` defaults intact and expose the nib-calibrated profile cleanly via preset / `--approach kinematic`; revert `scribesim/render/sandbox.py` if needed.

## Evidence

- [x] tidy:preparatory
- [x] tdd:red-green
- [x] tests:unit

## CI Evidence Notes

- If CI jobs are enabled, link pipeline evidence (`ci:passed`) from PR/MR and default-branch runs.
- If CI jobs are temporarily disabled, run checks externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-HAND-004 --status passed` (include provider/run metadata when available)
  - Optional combined flow when provider lookup is available:
    - `arrive pr check --provider-status --advance ADV-SS-HAND-004 --record-ci-evidence --json`

## Changes Made

### 2026-10-16 - docs: Draft ADV-SS-HAND-004 for TD-019 Pass 16a
- `arrive/systems/scribesim/advances/ADV-SS-HAND-004.md`: Created planned advance record for Bastarda nib-width proportions and fast sandbox CLI.

### 2026-10-16 - tidy: add nib-width proportion helpers and component selectors
- `scribesim/hand/profile.py`: Added `nib_width_for_x_height` and `x_height_to_nib_ratio` helpers and widened `_RANGES["nib.width_mm"]` to `(0.6, 3.0)`.
- `scribesim/hand/__init__.py`: Exported proportion helper functions.
- `arrive/systems/scribesim/components/{hand,render,tests}.yaml`: Added path selectors for `scribesim/render/**`, `shared/hands/**`, and TD-019 test files.

### 2026-10-16 - test: add Bastarda nib-width proportion, chisel contact, A1 gate, and sandbox CLI tests
- `tests/test_bastarda_proportions.py`: Added 5 unit and CLI tests covering $H = 4.2\,w_{\text{nib}}$ calibration, $40^\circ$ chisel hairline projection + tine splay, velocity-minimum turn pooling, Tier-1 `A1-PROPORTION` gate, and `<0.5s` `scribesim sandbox` execution.

### 2026-10-16 - feat: implement Bastarda nib-width calibration, natural chisel contact, A1 gate, and sandbox CLI
- `scribesim/hand/profile.py`: Added `bastarda_nib_calibrated_profile()` ($H=3.5\text{ mm}, w_{\text{nib}}=0.8333\text{ mm}, \alpha=40^\circ$).
- `scribesim/render/nib.py`: Implemented `chisel_apparent_width_mm()`, `turn_pooling_factor()`, and `evaluate_a1_proportion()`.
- `scribesim/render/sandbox.py`: Implemented `render_trajectory_samples()` and `render_sandbox()` emitting `sandbox.png`, `overlay.svg`, `metrics.json`, and `index.html` in $<0.5\text{ s}$.
- `scribesim/cli.py`: Added `scribesim sandbox` subcommand.

## Check for Understanding

1. Why does a $40^\circ$ broad-edged nib produce a natural hairline upstroke in `chisel_apparent_width_mm()` without requiring the Pass 15 `edge: [0, 0.1]` 10%-corner step schedule?
2. How does `turn_pooling_factor()` in `scribesim/render/nib.py` model diamond feet and crown turns without triggering self-overlap prohibitions?
3. What two invariants does `evaluate_a1_proportion()` verify for Tier-1 `A1-PROPORTION`, and why does it reject the old $0.45\text{ mm}$ nib on $3.5\text{ mm}$ x-height?

