---
advance:
  id: "ADV-SS-HANDVALIDATE-020"
  title: "Independent Level-Assembly Validation and Appearance Review"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "curriculum", "tests"]
  started_at: "2026-09-08T17:50:21Z"
  implementation_completed_at: "2026-09-08T18:20:55Z"
  review_time_estimate_minutes: 361.4
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 110
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit"]
  model_usage: []
  status: complete
---

## Objective

Independently validate the frozen rotated returns and level n/u/m assemblies,
and give the owner an explicit appearance-review sheet. Follow
[TD-018 Addendum B section 11](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#11-level-assembly-and-standalone-stem-admission).
No context, fatigue, fitting, target revision or relaxed threshold is authorized.

## Behavioral Change

New opt-in validation measures exact isolated rotated occurrences and complete
frozen recipes against the unchanged target version, with independent level and
decision logic, full-frame/local image checks, base/arc/time physical refinements
plus isolated-gesture subdivision,
negative controls and three first/replay seeds. A numeric pass is explicitly
separate from pending human appearance/reading approval; it cannot release S2.

## Dependencies

- [ADV-SS-CURRICULUM-014](ADV-SS-CURRICULUM-014.md)
- [ADV-SS-HANDVALIDATE-019](ADV-SS-HANDVALIDATE-019.md)

## Planned Implementation Tasks

- [x] branch: `advance/ss-handvalidate-020`, standing update/merge workflow.
- [x] tidy: no refactor of pinned modules; reuse immutable replay infrastructure unchanged.
- [x] test: `f2a86b0` records missing-module red; 21 tests now pass, including live rotated and complete-assembly measurements, control detection and serialization stability.
- [x] feat/fix: freeze protocol and candidate/source hashes before measurement.
- [x] evaluate: all declared checks and seven controls pass for six fixtures and seeds 7/19/41 with replay. 474 renders, 158 per seed, maximum 267.165 seconds; zero fitting/retries.
- [x] review: enlarged guided actual-ink sheet and numbered stroke construction; owner verdict remains pending and the review request has been presented.
- [x] evidence: live read-only audit verifies all 452 artifacts, saved pixels, traces, controls and replay; local merge receipt follows.

## Bug Fixes

The new gate accepts finite numeric scalars consistently before/after JSON,
without changing the frozen prior checker or its mixed worker/root receipts.
The canonical archive reader also restores saved metric pixels in memory for
convergence checks; no rerendering or altered execution record is required.

## Component Impact

- `scribesim/handvalidate/letter_assembly.py`: independent bounded measurement and decision gates.
- `scribesim/handvalidate/letter_assembly_evidence.py`: canonical no-render archived-proof reader.
- `tests/test_handvalidate_letter_assembly*.py`: 24 new behavioral, live-measurement and archive tests.
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/validation/`: specification, immutable bundle, separate verification receipt and owner-review page/record.
- Existing component interface, plan, TD-018 and gallery links; no new component or stage promotion.

## Risk + Rollback

Matching synthetic targets cannot establish intended style or historical
legibility. Isolated rotated occurrences and exact whole recipes are bounded
coverage, not a transform envelope or accepted alphabet. Negative lineage guards
are not image-sensitivity evidence; retain an explicit rendered image control.
Remove only new opt-in validation/review artifacts to roll back. Preserve old
code/evidence and keep S2, real, context and fatigue permissions false.

## Evidence

- [x] tidy:preparatory assessed; no pinned runtime cleanup required.
- [x] tdd:red-green: `f2a86b0` before execution implementation `04223d8`; `463ecae` before archive-reader repair `2aab160`.
- [x] 127 broader tests pass in 92.78 seconds; all 24 new tests pass in clean `2aab160` checkout (35.90 seconds).
- [x] [Independent results and verification](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/validation/README.md): 452 artifacts and 74 non-clock files per worker replay exactly.
- [x] [Appearance sheet](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/validation/index.html) published; desktop 1280px and mobile 390px inspected, no overflow, both toggles verified. Native image bounds leave all ink visible in detail views.
- [x] Plan, generated rules, whitespace and local-link checks pass. No human appearance approval is inferred.

## CI Evidence Notes

Run local plan/rules/whitespace and strict PR metadata checks before merge.
Record installed parser/schema limitations separately; no provider CI claim.
The installed strict PR parser returns `ids=[]` despite explicit Advance metadata
in title/body/label. Existing component-schema warnings remain unrelated.

## Changes Made

### 2026-09-08 — feat: complete independent mechanics, retain appearance gate

All declared local/global absolute losses pass the unchanged 0.05 limit; worst
actual local loss is 0.02607704, nominal local 0.02465973 and whole-letter benefit
ratio 0.03797615 (limit 0.75). Worst nominal level residual is 3.331e-16 x-height;
actual extrema residual 0.000108295 mm (limit 0.05 mm). The 1 mm rendered image
control fails with 0.89195411 loss; the climbing control yields 0.08 x-height.
All exact-lineage/ownership/contact/tool controls are detected.

Report SHA-256:
`bd3def56ffb24c9541815d3234cceddb31d21453331f2a6764f95c009026b28e`.
The canonical live reader returns `mechanical_validation_pass=true`, verifies
452 artifacts and reads saved measurement pixels without rendering. Root and
worker numerical decisions agree; no adjudication or changed verdict is needed.
Review is bound to the candidate/report and remains pending. The Advance is
complete as implementation/evaluation work, not as owner or S2 acceptance.

Reviewability Red 110 is dominated by the inseparable generated replay manifest.
Tests, runtime, archive-reader repair and evidence are separate commits. No
pinned old code, renderer, target, threshold, candidate, context or fatigue change.

### 2026-09-08 — fix: reconstruct archived convergence without rerendering

Red commit `463ecae` requires archived metric-pixel reconstruction. The original
execution reader passes compact traces (which deliberately omit pixel arrays)
straight to the image convergence comparator, causing `KeyError: images`.
The separate `letter_assembly_evidence` reader attaches the already saved metric
PNGs in memory, independently rechecks their numeric losses and convergence,
and preserves every frozen execution byte. No changed decision, fitting,
rerendering or repaired trajectory is involved. Its tests forbid execution/
painting, assert archive byte preservation, and reject a corrupted metric PNG.

### 2026-09-08 — test: establish pre-run subdivision boundary

Live pre-run tests pass isolated rotated-return subdivision but reject complete
letter subdivision at the unchanged recipe-reference cap (`Recipe bounds`).
No experiment has started and no candidate or threshold changes. Freeze explicit
per-kind coverage: four refinements for isolated returns, the prior three for
whole letters. Do not widen the compiler cap or claim whole-letter subdivision.
The climbing control perturbs compiled second-arch coordinates diagnostically,
not a newly admissible recipe; independent level logic catches it without using
the grammar's crossing rejection as a substitute for a level measurement.

### 2026-09-08 — plan: register bounded independent validation

Owner approved the proposed validation/review work. No new primitive fitting,
expanded alphabet, word/context learning or fatigue is included.

## Check for Understanding

1. Why are rotated returns newly scoped occurrences rather than inherited admission?
2. How does independent level/decision logic avoid merely repeating the curriculum verdict?
3. Which negative controls exercise images, and which only exercise exact lineage?
4. Why does a numeric pass still leave human appearance and S2 approval pending?
5. Why must the archive reader restore saved metric pixels instead of rerendering or using presentation crops?
