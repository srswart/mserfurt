---
advance:
  id: "ADV-SS-EXEMPLAR-007"
  title: "Konrad Word Observations — Line Masks, Label Uncertainty and Frozen Splits"
  system: "scribesim"
  primary_component: "refextract"
  components: ["refextract", "evo", "handvalidate", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
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

Produce trustworthy whole-word observations for TD-018 using automatic line-aware cleanup, explicit transcription uncertainty and leakage-resistant splits.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
This is a planned outcome record. The timestamp records drafting; implementation
has not started and no execution, CI or owner approval is claimed.

## Behavioral Change

After implementation: Every admitted word has unmodified source pixels, a target/background/unknown mask, a reversible coordinate transform and a documented reading hypothesis. Adjacent-line fragments, ambiguous readings and missing inventory are visible exclusions.

## Component Impact

Primary component: `refextract`. Impacted components:
`refextract`, `evo`, `handvalidate`, `tests`.

Planned paths (new modules and commands are not available yet):

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

- [ ] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [ ] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [ ] test: establish failing behavioral tests for the contracts below before implementation.
- [ ] feat/evaluate: Detect lines before word proposals; assign connected ink using baseline and neighbouring-line context, marking ambiguous overlaps unknown.
- [ ] feat/evaluate: Store raw crop/mask hashes, native bounds, baseline/x-height uncertainty, logical-to-visible mappings and actual intervention provenance.
- [ ] feat/evaluate: Quarantine low-confidence labels and unsupported abbreviations; reject overmasked or background-only observations rather than optimize them away.
- [ ] feat/evaluate: Group splits by source line at minimum and page when possible; move previously inspected v1 held-out material into development only.
- [ ] feat/evaluate: Collect the initial 30–60-instance target when available; enforce starter-symbol support and test coverage requirements and freeze the G0 artifacts.
- [ ] feat/evaluate: Audit tracked versus ignored local helper imports so the dataset builder works from a clean checkout.
- [ ] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] No source pixels or source-line groups overlap splits; test membership is fixed before model selection.
- [ ] Raw pixels are unchanged; cleanup previews show every removal/unknown region and mask coverage stays within the frozen development limit.
- [ ] No uncertain reading, repaired fallback or unrelated apparent hand is silently admitted as exact evidence.
- [ ] G0 reports coverage and calibration results; insufficient material produces a named blocked case instead of a fabricated dataset.

Focused validation: Use touching-line, descender, pale-stroke and bleed fixtures; assert genuine target ink is preserved or marked uncertain. Reject hash mismatches, shared-line splits, excessive unknown masks and unsupported text mappings.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: Automatic cleanup can erase real strokes or leak adjacent text into the loss. Preserve raw data, uncertainty masks and line groups; never select cleanup parameters on locked-test candidate performance.

Rollback: Select the immutable v1 source bundle and retain v2 as an experimental observation set; no original scan is edited.

Review estimate: 30 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Pending implementation; none of these evidence types is claimed as completed.

- [ ] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [ ] `tdd:red-green`: capture focused failing and passing test commands and results.
- [ ] raw/masked/cleaned contact sheets and machine-readable exclusion/coverage report
- [ ] source and split manifests, hashes and extraction configuration
- [ ] G0 calibration controls and target-review state
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

1. Why must split checks operate on source lines as well as rectangular pixel overlap?
2. How does the loss treat known background differently from unknown ink?

