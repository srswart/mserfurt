---
advance:
  id: "ADV-SS-EXEMPLAR-007"
  title: "Konrad Word Observations — Line Masks, Label Uncertainty and Frozen Splits"
  system: "scribesim"
  primary_component: "refextract"
  components: ["refextract", "evo", "handvalidate", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: "2026-09-05T18:13:49Z"
  review_time_estimate_minutes: 45
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

Produce trustworthy whole-word observations for TD-018 using automatic line-aware cleanup, explicit transcription uncertainty and leakage-resistant splits.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
Implemented on `feat/td018-word-observations`. Drafting time is retained. The user
authorized implementation and merging. This completed bounded data-preparation
experiment has a **blocked G0 result**, not a usable or promoted training corpus.

## Behavioral Change

Implemented: Every admitted word has unmodified source pixels, a target/background/unknown mask, a reversible coordinate transform and a documented reading hypothesis. Adjacent-line fragments, ambiguous readings and missing inventory are visible exclusions.

## Component Impact

Primary component: `refextract`. Impacted components:
`refextract`, `evo`, `handvalidate`, `tests`.

Implementation paths:

- scribesim/evofit/reference_dataset.py (new; reuse verified extraction helpers)
- reference/konrad_hand_recovery_v2/ (versioned source/mask/label/split manifest and contact sheets)
- .gitignore (narrow corpus exception only); tests/test_reference_dataset.py (new)
- arrive/systems/scribesim/components/tests.yaml (focused test selector)

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-HANDVALIDATE-007](ADV-SS-HANDVALIDATE-007.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [x] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [x] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [x] test: establish failing behavioral tests for the contracts below before implementation.
- [x] feat/evaluate: Detect lines before word proposals; assign connected ink using baseline and neighbouring-line context, marking ambiguous overlaps unknown.
- [x] feat/evaluate: Store raw crop/mask hashes, native bounds, baseline/x-height uncertainty, logical-to-visible mappings and actual intervention provenance.
- [x] feat/evaluate: Quarantine low-confidence labels and unsupported abbreviations; reject overmasked or background-only observations rather than optimize them away.
- [x] feat/evaluate: Group splits by source line at minimum and page when possible; move previously inspected v1 held-out material into development only.
- [x] feat/evaluate: Collect the initial 30–60-instance target when available; enforce starter-symbol support and test coverage requirements and freeze the G0 artifacts.
- [x] feat/evaluate: Audit tracked versus ignored local helper imports so the dataset builder works from a clean checkout.
- [x] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [x] No source pixels or source-line groups overlap splits; test membership is fixed before model selection.
- [x] Raw pixels are unchanged; cleanup previews show every removal/unknown region and mask coverage stays within the frozen development limit.
- [x] No uncertain reading, repaired fallback or unrelated apparent hand is silently admitted as exact evidence.
- [x] G0 reports coverage and calibration results; insufficient material produces a named blocked case instead of a fabricated dataset.

Focused validation: Use touching-line, descender, pale-stroke and bleed fixtures; assert genuine target ink is preserved or marked uncertain. Reject hash mismatches, shared-line splits, excessive unknown masks and unsupported text mappings.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: Automatic cleanup can erase real strokes or leak adjacent text into the loss. Preserve raw data, uncertainty masks and line groups; never select cleanup parameters on locked-test candidate performance.

Rollback: Select the immutable v1 source bundle and retain v2 as an experimental observation set; no original scan is edited.

Review estimate: 45 minutes after inspecting the actual code and artifacts. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Actual local evidence:

- Red: `python -m pytest tests/test_reference_dataset.py -q` failed collection before implementation (test commit `acf31d5`).
- Additional test-first regressions exposed pale-ink/calibration failures (`fc23256`), unverified pass summaries/coordinate claims (`1575c12`) and duplicate pixel observations (`9afa7eb`).
- Green: `.venv/bin/python -m pytest tests/test_reference_dataset.py tests/test_handvalidate_specimen.py tests/test_word_recovery.py tests/test_handvalidate_nominal_review.py -q` — 38 passed.
- Reproduce the real run: `.venv/bin/python -m scribesim.evofit.reference_dataset --input reference/konrad_hand_recovery_v2/input_manifest.json --output /tmp/konrad-observation-replay`.
- Bundle: `reference/konrad_hand_recovery_v2/` contains 60 candidates: 41 train, 11 development, 8 withheld test reservations. **Zero are admitted.** The 30–60 usable-instance target was attempted but not achieved.
- All 60 lack declared visible mappings; 38 have uncertain/missing labels, 52 excessive unknown ink, and 38 no assigned target ink. Exclusions overlap. Available v1 normalized labels cannot establish exact visible forms; new regions are unlabeled.
- Five synthetic image controls pass; source calibration remains blocked without admitted independent repeats. A separate 40-instance synthetic regression proves valid data can pass readiness, so the gate is not hardcoded to block.
- Visually inspected source/mask/cleaned panels; fixed overly destructive treatment of connected pale ink while retaining touching-line uncertainty and weak-flood quarantine. Locked-test pixels are withheld from sheets and were not visually reviewed.
- Revalidation checks actual source/export hashes, native pixels, masks, transforms, source-line/pixel splits, duplicates, support counts and calibration. G0 requires a verified dataset directory, not an arbitrary pass summary.
- No preparatory refactoring was necessary. The new tracked module does not import ignored extraction/transcription helpers.
- `arrive plan check` and `git diff --check` pass. Strict PR metadata checking was executed but rejects the repository's `ADV-SS-EXEMPLAR-007` ID under the installed parser, as for the first Advance. No successful strict check, provider CI or target approval is claimed.

- [x] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [x] `tdd:red-green`: capture focused failing and passing test commands and results.
- [x] raw/masked/cleaned contact sheets and machine-readable exclusion/coverage report
- [x] source and split manifests, hashes and extraction configuration
- [x] G0 calibration controls and target-review state
- [x] Record local integration checks separately from provider CI and owner review.
- [x] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

- Preserve pale strokes connected to strong ink without admitting unsupported weak floods.
- Reject source aliases leaking across splits, repeated observations and forged geometry/admission/calibration claims.
- Require dataset integrity verification before G0 can pass.
- No production letterform, state, foliation or Weather defect is claimed fixed.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Why must split checks operate on source lines as well as rectangular pixel overlap?
2. How does the loss treat known background differently from unknown ink?


### 2026-09-05 — implement: Freeze word observation evidence

- Added `scribesim/evofit/reference_dataset.py`, twenty observation tests and a benchmark integrity regression.
- Added narrow v2 artifact tracking and focused test selector coverage.
- Generated raw/mask/cleaned crops, source/split manifests, six paginated review sheets, coverage/calibration reports and G0.
- Finished the bounded 60-candidate experiment with its failure reasons retained. This does not unblock nominal recovery.
