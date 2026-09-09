---
advance:
  id: "ADV-SS-CURRICULUM-015"
  title: "Upright Construction — Shared Rise and Return Repair Preview"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum", "gesture", "handvalidate", "tests"]
  started_at: "2026-09-08T18:57:52Z"
  implementation_completed_at: "2026-09-09T03:48:45Z"
  review_time_estimate_minutes: 163
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 93
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit"]
  model_usage: []
  status: complete
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

- [x] branch: `advance/ss-curriculum-015` from merged GESTURE-003 on master.
- [x] tidy: isolated new builder; no frozen-module refactor required.
- [x] test: red 792fc29 before a579d95; isolated-ink/archive red c1ac80b before e3631d5.
- [x] feat/fix: new shared rise/returns; stem cubics byte-equivalent as values, metadata corrected.
- [x] feat/fix: tangent-compatible handles and bounded uniform scales, no whole-gesture rotation.
- [x] evaluate: sampled tangent/chord angles, adjacent rise-body separation, exact extrema and connected ownership.
- [x] evidence: 900-DPI full and 1800-DPI detail nominal ink, four isolated primitive tiles and vector direction diagrams.
- [x] evidence: full finite-nib containment before each paint; one common detail frame without per-letter stretching.
- [x] evidence: candidate/report/source hashes frozen; candidate-bound owner-review record remains pending.
- [x] merge: f2fab6b merged locally into master as dadafc3; owner review explicitly pending.

## Bug Fixes

- [x] Unrotated shared stems replace the unwanted rotation; rise chord decreases from 45 to 5.090 degrees.
- [x] No old target is changed or reused as a fitting objective; zero target creation/optimization.
- [x] Fixed pressure and nib remain unchanged. Increased overlap remains visible rather than being cosmetically hidden.
- [x] Preserve cap height profile and width, but disclose the changed exit handle/curvature required for the upright stem.

## Risk + Rollback

New geometry is unaccepted and may increase ink accumulation during pen-down
retracing. Do not thin the nib or lower pressure to hide it. Any required shared
stem change must be declared with fresh admission debt. Angle and clearance
values are proposals until reviewed, not owner-approved numerical tolerances.
Rollback disables/removes only the new opt-in experiment, preserving old results.

## Evidence

- [x] New isolated module needs no preparatory refactor; no tidy evidence fabricated.
- [x] Seven new tests; 125 focused compiler/action/clock/alignment tests pass (27.66 seconds, includes new tests).
- [x] Seven new tests also pass in a separate e3631d5 checkout (10.04 seconds).
- [x] All 21 run-001 files replay byte-for-byte in a fresh process, including 13 PNGs and four SVGs.
- [x] Read-only verifier rejects changed artifacts/review binding and checks source identities/scope.
- [x] Desktop 1280px/mobile 390px browser checks: images load, no horizontal overflow, detail/whole-frame toggle and direction disclosure work. Optional favicon alone returns 404.
- [x] Pending owner-review request, not acceptance: [review sheet and evidence](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/upright/README.md).

## CI Evidence Notes

Run targeted tests, plan/rules/whitespace checks and strict PR metadata checks
before merge. Record actual diff reviewability; split generated evidence from
implementation. Local checks do not establish provider CI or physical acceptance.
Generated same-scale images, SVGs and the immutable source-bound measurement
manifest dominate review size. Test/implementation/evidence commits are separate;
retain the complete correlated sample bundle rather than splitting the before/
after evidence. Actual human review time remains unknown. No provider CI claim.
Final reviewability: Red 93 / 163 estimated minutes (162.7 rounded up). Local
plan, generated-rule and whitespace checks pass. The installed strict PR parser
still returns `ids=[]` for explicit Advance title/body/label metadata; existing
component-schema warnings are unrelated. Neither limitation is reported as a
provider CI pass.

## Changes Made

### 2026-09-09 - merge: local completion receipt

Completion f2fab6b merged as dadafc3. Post-merge read-only checks verify the
candidate/report hashes, complete preview artifacts and source identities.
Plan/rules/whitespace checks pass, and the local review URL responds successfully.
The temporary validation checkout is removed. No push, provider CI or appearance
acceptance is claimed; owner review remains the next checkpoint.

### 2026-09-09 - feat: complete deterministic upright preview

`scribesim/curriculum/upright_letters.py` loads only the pinned HANDVALIDATE-020
candidate/report bytes as unaccepted scaffolding. It does not invoke stale
readiness readers. Stem cubics are unchanged; metadata now matches true tangents.
One shared rise and two shared return primitives produce level n/u/m with 4/4/6
references, no rotations and no intra-letter lifts. N/u/m body rise-to-adjacent-
stem maximum horizontal separations are 0.123023/0.260118/0.124543 mm at y=0.2..0.7
x-height; initial m rise has no adjacent stem and is excluded from that metric.

The new rise chord is 5.090 degrees from vertical, a proposal rather than an
owner-approved tolerance. Its final tangent still turns into the cap. Upper
return y controls, width and first handle are retained; its exit-handle x changes
for the upright stem. Both lower-return handle x coordinates change. The review
sheet explicitly discloses curvature, width and fixed-pressure overlap tradeoffs.

Builder frozen at e3631d5; candidate SHA-256
`01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd`;
report SHA-256
`53f5beefadd9bb3dc0000eb7f9fb730de549bcb68d4b063936eaade3821ff5fb`.
Artifacts live in `letters/upright/run-001`, with gallery links from letter and
foundation pages. No actual hand simulation, target, fitting, acceptance, context
or fatigue. The next substantive checkpoint
is owner keep/repair feedback before scored HANDVALIDATE-021 evaluation.

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
