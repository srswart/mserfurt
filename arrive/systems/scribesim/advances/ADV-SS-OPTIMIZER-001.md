---
advance:
  id: ADV-SS-OPTIMIZER-001
  title: Automated Optimizer — Staged Fitting Against Real Manuscripts
  system: scribesim
  primary_component: tuning
  components:
  - tuning
  - metrics
  started_at: 2026-03-20T16:50:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T12:58:30.592989Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence:
  - tdd:red-green
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Implement the automated parameter optimization loop from TD-003 Part 4: a staged optimizer that adjusts hand parameters to minimize composite metric distance against real manuscript target images. Supports both numerical gradient descent and Bayesian optimization strategies.

## Behavioral Change

After this advance:
- `scribesim fit --target <real.png> --profile <hand.toml> --output <fitted.toml>` runs the automated fitting loop
- **Stage 1 — Coarse fitting** (~14 params): optimize folio + line parameters against M2 (baseline regularity) and M8 (texture). ~28 renders per gradient step, low-resolution preview.
- **Stage 2 — Nib fitting** (~6 params): optimize nib parameters against M1 (stroke width) and M6 (proportions). ~12 renders per step.
- **Stage 3 — Rhythm fitting** (~14 params): optimize word + glyph parameters against M3 (spacing rhythm), M5 (glyph consistency), M7 (connection angles). ~28 renders per step.
- **Stage 4 — Ink fitting** (~11 params): optimize ink + material parameters against M4 (ink density) and per-pixel darkness. ~22 renders per step.
- **Stage 5 — Perceptual fine-tuning** (all params, small steps): optimize against M9 (perceptual similarity) with very small learning rate.
- `--stages coarse,nib,rhythm` selects which stages to run (skip ink/perceptual for faster iteration)
- `--max-iterations 50` caps iterations per stage
- `--interactive` enables human-in-the-loop mode: optimizer proposes changes, human approves or overrides
- `--log fitting_log.json` records per-iteration parameters, distances, and per-metric scores for analysis
- Parameters are clamped to valid ranges after each update; gradient estimates use central finite differences
- Optional Bayesian optimization via `--strategy bayesian` (requires `optuna` or `scikit-optimize`)

## Planned Implementation Tasks

- [ ] Tidy: define `FittingConfig` (stages, max_iterations, learning_rate, convergence threshold) and `FittingLog` data structures
- [ ] Tidy: define `TargetProfile` — JSON file with per-metric target values extracted from real manuscript images
- [ ] Test: write tests — optimizer reduces distance on a trivially misaligned parameter; stage isolation (coarse only touches folio/line params); parameter clamping enforces ranges; log captures per-iteration state
- [ ] Implement: target preparation pipeline — load real manuscript image, run metric suite, store target metric values
- [ ] Implement: numerical gradient estimator — central finite differences with configurable epsilon per parameter (scaled by sensitivity)
- [ ] Implement: parameter update loop — gradient descent with learning rate, range clamping, convergence detection
- [ ] Implement: staged optimizer — freeze/unfreeze parameter groups per stage, select stage-appropriate metrics
- [ ] Implement: `scribesim fit` CLI subcommand with `--stages`, `--max-iterations`, `--log`, `--strategy`, `--interactive` flags
- [ ] Implement: interactive mode — display proposed changes, accept user approval/override, adjust model from overrides
- [ ] Implement: Bayesian optimization strategy (optional, behind `--strategy bayesian` flag, graceful fallback if optuna not installed)
- [ ] Validate: run coarse + nib fitting against a real Bastarda manuscript sample; verify composite distance decreases monotonically; inspect fitted parameter values for reasonableness

## Risk + Rollback

**Risks:**
- Each gradient evaluation requires 2×N renders (N = active parameters) — expensive. Stage isolation keeps N manageable.
- Non-convex optimization surface — gradient descent may find local minima. Bayesian strategy is more robust but requires optional dependency.
- Interactive mode requires careful UX — the optimizer must present changes clearly and handle user input gracefully.

**Rollback:**
- Revert the branch; optimizer is a standalone module with no effect on rendering.

## Evidence

- [ ] 17 tests in `tests/test_optimizer.py` covering gradient estimation, optimization steps, stage isolation, convergence, logging
- [ ] 316 total ScribeSim tests pass (0 failures)
- [ ] `scribesim fit` CLI functional with staged gradient descent against historical samples
