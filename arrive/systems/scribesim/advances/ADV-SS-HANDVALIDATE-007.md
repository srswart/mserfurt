---
advance:
  id: "ADV-SS-HANDVALIDATE-007"
  title: "Konrad Specimen Benchmark — Visual Target, Baselines and Gate Contract"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "evo", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 25
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Establish the reference target and evaluation contract before changing letterforms. Reconcile the saved ADV-SS-EVOFIT-004 results as evidence without assuming that its open implementation record is complete.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
This is a planned outcome record. The timestamp records drafting; implementation
has not started and no execution, CI or owner approval is claimed.

## Behavioral Change

After implementation: A versioned benchmark names the actual renderers and assets, separates appearance/text/image/motion evidence, and identifies the first three-line proof. Legacy template and pressure-range metrics cannot silently count as readability or handwriting acceptance.

## Component Impact

Primary component: `handvalidate`. Impacted components:
`handvalidate`, `evo`, `tests`.

Planned paths (new modules and commands are not available yet):

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

- [ ] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [ ] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [ ] test: establish failing behavioral tests for the contracts below before implementation.
- [ ] feat/evaluate: Capture reproducible plain/evo/v1-fitter baseline commands, backend/model hashes and fresh-process outputs; label saved older images separately.
- [ ] feat/evaluate: Reconcile v1 report, source exclusions and the prior five-test result; record remaining EVOFIT-004 completion work without fabricating completion.
- [ ] feat/evaluate: Define train/development/locked-test manifest schema, immutable proof texts, visual rubric, independent reading status and pass/fail/blocked gate records.
- [ ] feat/evaluate: Implement missing-evidence and empty-set rejection, equal-scale panel layout, and metric names that distinguish template similarity from transcription and appearance.
- [ ] feat/evaluate: Draft the target sheet and calibration protocol using repeated-source and adverse controls; record target review as pending until supplied.
- [ ] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] The report identifies each baseline's actual backend, source/model/configuration identity and reproducibility limits.
- [ ] Missing review, missing required measurements and an empty test set produce blocked, never pass.
- [ ] The target/proof contract identifies source and project-text coverage debt and reserves fresh, uninspected test material.
- [ ] ADV-SS-EVOFIT-004 retains its true status and evidence boundaries; no historical or readability claim is inferred from lower loss.

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

Pending implementation; none of these evidence types is claimed as completed.

- [ ] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [ ] `tdd:red-green`: capture focused failing and passing test commands and results.
- [ ] baseline_manifest.json and target/reference panels
- [ ] benchmark contract, calibration protocol, proposed proof texts and pending/recorded target review
- [ ] prior-experiment reconciliation with actual commands and unresolved items
- [ ] Record local integration checks separately from provider CI and owner review.
- [ ] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

None implemented in this planning change. Record scoped defects and their
regressions here during execution; do not imply unrelated renderer defects are fixed.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Why can the existing OCR proxy and pressure-range metric not certify the intended appearance?
2. How does a missing review differ from a failed render or a completed experiment?

