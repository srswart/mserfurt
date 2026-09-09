---
advance:
  id: "ADV-SS-CURRICULUM-015"
  title: "Upright Construction — Shared Rise and Return Repair Preview"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum", "gesture", "handvalidate", "tests"]
  started_at: "2026-09-08T18:57:52Z"
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

Replace excessive shared slant with a bounded pen-down n/u/m construction and
show the owner reviewable samples before fitting or scored physical evaluation.
Follows [TD-018 Addendum B section 13](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#13-upright-pen-down-construction-repair).
Depends on GESTURE-003 and HANDVALIDATE-020's recorded appearance feedback.

## Behavioral Change

One versioned shared rise/return vocabulary produces near-upright upstrokes,
less-slanted descents and a less-slanted initial u underturn. Preserve the n's
acceptable overturn where compatible and disclose any necessary change. Use
pen-down connections, not per-letter cubics or another whole-letter rotation.
Maintain baseline/x-height, fixed actions and n/u/m's 4/4/6 expanded references.
This produces a deterministic no-fit preview, not a learned or accepted hand.

## Component Impact

- `curriculum`: proposed isolated `upright_letters` builder and review export.
- `gesture`: new-version shared geometry/ports; no edits to the frozen old contract.
- `handvalidate` / `tests`: structural guards, source pins and review evidence.
- Proposed outputs: `shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/upright/`.
- No new component, alphabet, context or default change.

## Planned Implementation Tasks

- [ ] branch: create `advance/ss-curriculum-015` after GESTURE-003 merges.
- [ ] tidy: isolate new experiment from frozen modules; refactor only if needed.
- [ ] test: commit failing lineage, geometry, contact, containment and cap tests.
- [ ] feat/fix: version shared rise/return geometry; prefer the unchanged standalone stem.
- [ ] feat/fix: derive truthful tangent ports and shared attachment transforms.
- [ ] evaluate: report local/chord angles, stem proximity, levels, joins and overlap.
- [ ] evidence: publish same-scale old/new nominal ink, isolated strokes, n/u/m, direction arrows and contact timelines.
- [ ] evidence: show full finite-ink frames plus enlarged detail, clearly labeled nominal.
- [ ] evidence: freeze preview candidate/source hashes and request keep/repair per letter.
- [ ] merge: complete preview implementation with owner review explicitly pending if unanswered.

## Bug Fixes

- [ ] Whole-gesture leveling rotated internal stems while leaving excessive rise slant.
- [ ] Existing slanted synthetic targets cannot serve as unmodified objectives for the requested shape repair.
- [ ] Do not infer pressure reduction or exact retracing from the word upstroke.

## Risk + Rollback

New geometry is unaccepted and may increase ink accumulation during pen-down
retracing. Do not thin the nib or lower pressure to hide it. Any required shared
stem change must be declared with fresh admission debt. Angle and clearance
values are proposals until reviewed, not owner-approved numerical tolerances.
Rollback disables/removes only the new opt-in experiment, preserving old results.

## Evidence

- [ ] tidy:preparatory if necessary, otherwise document isolation rationale.
- [ ] tdd:red-green; tests:unit for shared reuse, exact levels and unchanged old inputs.
- [ ] Review artifact hashes, nominal contact timeline and full-frame containment.
- [ ] Owner-review request with pending/keep/repair state, never agent-authored approval.

## CI Evidence Notes

Run targeted tests, plan/rules/whitespace checks and strict PR metadata checks
before merge. Record actual diff reviewability; split generated evidence from
implementation. Local checks do not establish provider CI or physical acceptance.

## Changes Made

### 2026-09-08 - plan: register shared geometry and visual checkpoint

Scope is limited to a deterministic no-fit preview under the new contact
contract. No geometry or images have been generated. HANDVALIDATE-021 cannot
begin scored evaluation until the preview is reviewed and its protocol frozen.
Planning checks pass for the plan, generated rules and whitespace. The installed
strict PR metadata parser returns `ids=[]` despite explicit Advance IDs in the
title and labels; no provider CI or implementation test pass is claimed.

### 2026-09-09 - prerequisite: GESTURE-003 contract implemented

The new connected-v1 schema supports explicit pen-down boundaries, truthful ports
and fixed-tool corner timing. Its diagnostics are not letter geometry. Shared
compiler identities changed, so old live admissions now fail closed while their
bytes and source snapshots remain intact. Build this preview as explicitly
unaccepted with pinned source bytes; do not bypass or repin an old readiness
reader. Fresh matching-source validation remains necessary before admission use.

## Check for Understanding

1. How does the same shared rise/return change propagate into n, u and m?
2. Why are chord angle, tangent angle and stem clearance separate measurements?
3. Why does a nominal review preview not prove actual continuous-contact behavior?
