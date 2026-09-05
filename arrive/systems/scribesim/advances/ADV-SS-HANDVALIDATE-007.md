---
advance:
  id: "ADV-SS-HANDVALIDATE-007"
  title: "Konrad Specimen Benchmark — Visual Target, Baselines and Gate Contract"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "evo", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: "2026-09-05T17:53:53Z"
  review_time_estimate_minutes: 25
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration", "snapshot"]
  model_usage: []
  status: complete
---

## Objective

Establish the reference target and evaluation contract before changing letterforms. Reconcile the saved ADV-SS-EVOFIT-004 results as evidence without assuming that its open implementation record is complete.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
Implemented on `feat/td018-benchmark-contract`. The drafting timestamp is retained;
implementation finished at the timestamp above. The user authorized implementation
and per-Advance merging. Target appearance review remains pending; no provider CI
or paleographic approval is claimed.

## Behavioral Change

Implemented: A versioned benchmark names the actual renderers and assets, separates appearance/text/image/motion evidence, and identifies the first three-line proof. Legacy template and pressure-range metrics cannot silently count as readability or handwriting acceptance.

## Component Impact

Primary component: `handvalidate`. Impacted components:
`handvalidate`, `evo`, `tests`.

Implementation paths:

- scribesim/handvalidate/specimen.py (new benchmark/report contract)
- shared/training/konrad_hand_recovery/benchmark_v1/ (tracked manifest, target sheet and baseline records)
- tests/test_handvalidate_specimen.py (new); focused ARRIVE test selector coverage

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- No new implementation prerequisite. Inspect the saved EVOFIT-004 evidence and preserve its actual open status.

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [x] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [x] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [x] test: establish failing behavioral tests for the contracts below before implementation.
- [x] feat/evaluate: Capture reproducible plain/evo/v1-fitter baseline commands, backend/model hashes and fresh-process outputs; label saved older images separately.
- [x] feat/evaluate: Reconcile v1 report, source exclusions and the prior five-test result; record remaining EVOFIT-004 completion work without fabricating completion.
- [x] feat/evaluate: Define train/development/locked-test manifest schema, immutable proof texts, visual rubric, independent reading status and pass/fail/blocked gate records.
- [x] feat/evaluate: Implement missing-evidence and empty-set rejection, equal-scale panel layout, and metric names that distinguish template similarity from transcription and appearance.
- [x] feat/evaluate: Draft the target sheet and calibration protocol using repeated-source and adverse controls; record target review as pending until supplied.
- [x] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [x] The report identifies each baseline's actual backend, source/model/configuration identity and reproducibility limits.
- [x] Missing review, missing required measurements and an empty test set produce blocked, never pass.
- [x] The target/proof contract identifies source and project-text coverage debt and reserves fresh, uninspected test material.
- [x] ADV-SS-EVOFIT-004 retains its true status and evidence boundaries; no historical or readability claim is inferred from lower loss.

Focused validation: Report-contract fixtures reject an absent reviewer record, empty metric set, mislabeled backend and missing hash; a baseline smoke run proves that the selected command renders the declared model.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: An attractive report could certify stale or unrelated images. Require backend/model/source hashes and fresh-render evidence before using a baseline; treat unknown provenance as blocked.

Rollback: Remove the opt-in benchmark selection and retain the captured artifacts; production renderers and v1 evidence remain usable.

Review estimate: 25 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Actual local evidence:

- Red: `python -m pytest tests/test_handvalidate_specimen.py -q` failed collection
  before `specimen.py` existed (test commit `ba04306`).
- Additional red: the evo canvas regression found 23 ink pixels clipped to rows
  0–1 before the benchmark adapter added its explicit 10mm world baseline
  (test commit `428f31c`). This fixes the benchmark adapter, not the production renderer.
- Green: `.venv/bin/python -m pytest tests/test_handvalidate_specimen.py tests/test_word_recovery.py tests/test_handvalidate_nominal_review.py -q` — 17 passed.
- Capture: `.venv/bin/python -m scribesim.handvalidate.specimen build --output shared/training/konrad_hand_recovery/benchmark_v1`.
- Bundle: `shared/training/konrad_hand_recovery/benchmark_v1/` contains source/model/code/config/image hashes, fresh workers and replays, target sheet, coverage debt, prior experiment reconciliation and G0.
- Visual QA: inspected target sheet; corrected the clipped evo adapter and regenerated the bundle. All three declared raster smoke backends replay under the same pinned seed; plain changes with a different Python hash seed. These are word-raster baselines, not full CLI/folio benchmarks or a rerun of fitting.
- G0 is **blocked**, correctly, on `dataset_missing` and `target_review_missing`.
- `arrive plan check` passes. `arrive pr check --strict --json --title 'Implement specimen benchmark [ADV-SS-HANDVALIDATE-007]'` was run and fails because this installed checker does not recognize the repository's three-part Advance ID. No ID rename, fake CI evidence or successful strict check is claimed.
- No preparatory refactoring was necessary. Test commits precede implementation.

- [x] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [x] `tdd:red-green`: capture focused failing and passing test commands and results.
- [x] baseline_manifest.json and target/reference panels
- [x] benchmark contract, calibration protocol, proposed proof texts and pending/recorded target review
- [x] prior-experiment reconciliation with actual commands and unresolved items
- [x] Record local integration checks separately from provider CI and owner review.
- [x] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

- Fixed the new benchmark adapter's local-to-world y placement before accepting its evo image.
- New fail-closed validation detects absent reviews/data, unsupported metric labels, stale artifact hashes and mislabeled backends.
- Existing plain hash-seed and ink-consumption defects are recorded, not fixed.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Why can the existing OCR proxy and pressure-range metric not certify the intended appearance?
2. How does a missing review differ from a failed render or a completed experiment?


### 2026-09-05 — implement: Capture and validate the benchmark

- Added `scribesim/handvalidate/specimen.py` and eleven focused contract/render regressions.
- Added scoped test/evidence selectors and a narrow tracked training-artifact exception.
- Generated and visually inspected the immutable benchmark bundle; preserved EVOFIT-004 as in progress.
- Implementation is complete; model acceptance is not. Dataset preparation is the next phase item.

### 2026-09-05 — merge: Verify clean checkout and integrate

- A clean local clone passed the same 17 tests (15.26s).
- Merged into local `master` as `0bdb157`; no remote push or provider CI performed.
- An earlier source-archive check lacked Git metadata required by baseline capture; the real clean-clone check replaces that unsuitable harness.
