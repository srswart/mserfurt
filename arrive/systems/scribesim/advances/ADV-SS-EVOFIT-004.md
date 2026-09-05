---
advance:
  id: "ADV-SS-EVOFIT-004"
  title: "Automatic Whole-Word Recovery — Shared Geometry and Held-Out Evidence"
  system: "scribesim"
  primary_component: "evo"
  components: ["evo", "refextract", "tests"]
  started_at: "2026-09-05T15:35:34.380866+00:00"
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  # Populated by `arrive usage import` / the LiteLLM callback — leave empty when authoring.
  model_usage: []
  status: in_progress
---

## Objective

Test whether shared nominal letter geometry can be recovered from approximately
24 whole-word manuscript crops and reused on held-out/new words, without a
calligrapher or new human stroke tracing. Follows the automatic-first admission
and nominal-before-controller constraints of TD-014, particularly its
2026-09-05 Automatic Whole-Word Recovery Experiment section. The geometry-only
proof reuses TD-015's broad-edge polygon sweep, without changing production
renderers or claiming reconstructed historical stroke order.

## Behavioral Change

After this advance:
- A reproducible experiment consumes whole-word source bounds and machine-label
  hypotheses with image identity and confidence, not a manually traced alphabet.
- A bounded search updates shared character geometry using actual rendered
  training images; held-out pixels never participate in candidate selection.
- Output includes a reusable learned hand, source/baseline/fitted comparisons,
  held-out and novel-word evidence, exclusions and actual human interventions.
- Experiment completion and model promotion are distinct. Similarity metrics
  cannot promote a hand or establish correct transcription/paleographic fidelity.

## Planned Implementation Tasks

- [x] branch: created `experiment/konrad-word-recovery` from the existing branch
- [x] tidy: no source refactoring required; repair plan parsing and selector coverage separately
- [x] test: add leakage, real-image objective, source-integrity and RNG isolation regressions; establish red
- [ ] feat/fix: implement shared-geometry fitting and machine-labeled source dataset
- [ ] experiment: run the real source corpus and inspect generated/held-out specimens
- [ ] evidence: record outcome, limitations, human interventions and decision

## Bug Fixes

- [x] Replace the unsupported plan item status `proposed` with `planned` for
  ADV-SS-ANNOTATE-006, preserving its unstarted state and ID. The installed ARRIVE
  CLI can now parse and validate the authoritative plan.
- [x] Include `scribesim/evofit/**` in the existing `evo` component selector and
  the new regression file in `tests`; no component stage or ownership changes.
- Existing production renderer, legacy fit/train, foliation and ground-truth
  defects identified in the review are not silently claimed fixed by this experiment.

## Risk + Rollback

- Risk: machine-proposed transcriptions and apparent single-hand attribution can
  be wrong. Source hashes/bounds, label uncertainty and exclusions remain visible;
  no machine label is represented as expert approval.
- Risk: shared fixed stroke topology may improve image similarity while remaining
  unreadable or failing on new words. Keep source/baseline/fitted panels and a
  non-promotion decision regardless of scalar improvements.
- Risk: training/held-out leakage or a static objective could manufacture progress.
  Tests reject shared source pixels and stale image identity, check real-image
  residuals and ensure held-out changes do not alter the learned hand.
- Rollback: stop using the opt-in experiment module and its exported hand; existing
  production rendering and previous guide assets remain untouched. Retain failed
  evidence and the source manifest for diagnosis rather than overwrite old runs.
- Reviewability: one isolated runner, one bounded corpus and focused tests share a
  single manifest/report contract. No production integration or dependency change.

## Evidence

- [x] TDD red: `uv run pytest tests/test_word_recovery.py -q` failed collection with
  `ModuleNotFoundError: scribesim.evofit.word_recovery` before implementation.
- [x] Governance prerequisite: `arrive plan check` reports `Plan is valid` after
  the status repair.
- [ ] TDD green and focused integration checks
- [ ] Real-source experiment command, reports and visual specimens
- [ ] Final experiment verdict and model-promotion decision
- Preparatory source refactoring was unnecessary; no tidy/test/implementation
  commits or owner approval are claimed before they actually occur.

## CI Evidence Notes

- Run `arrive pr check --strict --json` before merge. Local experiment and test
  results are not provider CI evidence or owner approval.
- Record provider/run metadata with `arrive evidence record` only for an actual
  external CI run; do not record a passed status for unexecuted checks.

## Changes Made

### 2026-09-05 - test: Define trustworthy automatic-recovery boundaries
- `tests/test_word_recovery.py`: real rendered fixture, held-out isolation,
  source hash mismatch, overlapping source pixels and RNG isolation.

### 2026-09-05 - fix: Restore plan access and experiment ownership
- `arrive/implementation-plan.yaml`: normalize one unsupported unstarted status.
- `arrive/systems/scribesim/components/evo.yaml`: cover existing evofit code.
- `arrive/systems/scribesim/components/tests.yaml`: cover the new regression file.
- `docs/tech-direction/TD-014-guided-hand-recovery.md`: specify the bounded
  whole-word experiment, leakage boundaries and non-promotion requirement.

## Check for Understanding

1. Why does the experiment fit shared character geometry rather than store an
   independently optimized drawing for each observed word?
2. How do source checksums, cross-split bounds checks and held-out isolation guard
   against false evidence of progress?
3. Why do lower image losses and zero human tracing not establish readable,
   historically plausible handwriting or permission to promote this hand?
4. Which production assets remain unchanged, and how is this experiment rolled back?
