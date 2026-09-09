---
advance:
  id: "ADV-SS-GESTURE-003"
  title: "Upright Construction — Explicit Pen-down Gesture Connections"
  system: "scribesim"
  primary_component: "gesture"
  components: ["gesture", "pathguide", "handflow", "handvalidate", "tests"]
  started_at: "2026-09-08T18:57:52Z"
  implementation_completed_at: "2026-09-09T03:28:13Z"
  review_time_estimate_minutes: 118
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 69
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration"]
  model_usage: []
  status: complete
---

## Objective

Remove the representational blocker to pen-down upward movements, following
[TD-018 Addendum B section 13](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#13-upright-pen-down-construction-repair).
Depends on HANDVALIDATE-020's owner feedback, not its appearance acceptance.

## Behavioral Change

A new opt-in contract permits explicit smooth/corner inter-gesture connections
without changing legacy lift semantics. Contact-run identity is separate from
gesture/action ownership. Intentional reversals retain contact and corner-aware
timing. Unsupported gaps, smooth reversals and undeclared overlaps fail closed.
Fixed tool/actions and existing primitive/gesture/expanded-reference caps remain.

## Component Impact

- `gesture`: versioned schema, connection validation and source lineage.
- `pathguide` / `handflow`: connected-boundary sampling and actual contact timing.
- `handvalidate` / `tests`: contact-run, overlap-owner and legacy regression proofs.
- Existing components suffice; no new component or default activation is required.

## Planned Implementation Tasks

- [x] branch: `advance/ss-gesture-003` from clean `fc562b8`.
- [x] tidy: boundary audit complete; version-gated additions need no preparatory refactor.
- [x] test: red `bcf3934` precedes implementation `db64226`; further control repairs have separate red/green commits.
- [x] feat/fix: connected-v1 schema, no automatic migration or old-contract exception.
- [x] feat/fix: separate contact-run identity, primitive/gesture/action ownership and boundary contributors.
- [x] evaluate: smooth/corner/lift and two-letter separator fixtures, three refinements, exact same-process replay.
- [x] evaluate: gap, false smooth reversal, tangent, short/parallel overlap, macro/reference cap, forged owner and actual lift controls.
- [x] evidence: unchanged legacy guide hashes and historical report bytes; old live admission rejects changed compiler identities.
- [x] merge: completion ed50ead merged locally into master as 4e82325; no geometry admission.

## Bug Fixes

- [x] Old schemas retain mandatory lifts; the explicit new schema supports connected ports.
- [x] Sampling no longer inserts air at every gesture boundary in connected-v1; existing source-derivative timing handles the combined run.
- [x] Conservative finite-width envelopes detect parallel/short retracing and require explicit contributors at corners.
- [x] Boundary metadata identifies the final incoming primitive, not the gesture's first primitive.
- [x] Undeclared internal cubic corners fail before execution; actual owner/corner audits affect tracking verdicts.
- [x] Zero-time event boundaries have zero actuator rate only if the action is unchanged; nonzero instantaneous action changes fail.

## Risk + Rollback

Schema/identity changes can invalidate old live admission. Preserve historical
bytes and source snapshots; never rewrite pinned receipts to hide this. Constant
actions do not excuse lost action ownership. Disable the new opt-in version to
roll back; keep old validators and reject unsupported conversion. No cap increase,
target change, fitting, S2, context or fatigue follows from contract completion.

## Evidence

- [x] Version-gated additions require no preparatory refactor; no tidy evidence is fabricated.
- [x] tdd:red-green: `bcf3934` / `db64226`, `2773e4b` + `f4574b0` / `c95d694`, `5763d1e` / `aa5feed`.
- [x] 28 connected-contract tests pass, including a separate aa5feed checkout (2.77 seconds).
- [x] 127 compiler/action/clock/assembly regression tests pass (41.68 seconds).
- [x] Expanded run: 148 pass and five historical-admission tests reject new source identities; all five pass on fc562b8 (12.37 seconds). Final focused run excludes the historical-admission module, not individual failing assertions.
- [x] [Contract and bounded replay proofs](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/language/connected-contact/README.md): 12 final configurations, 48 metric renders, exact same-process replay; earlier 48-render pre-hardening proof retained separately.
- [x] Preserved HANDVALIDATE-020 report pin and direct live-reader rejection; no historical receipt or target edited.

## CI Evidence Notes

Before merge run local tests, plan/rules/whitespace checks and
`arrive pr check --strict --json`. Record provider/run metadata only when present;
local checks are not provider CI. Recalculate reviewability for the actual diff
and split implementation if required. Planning estimates are not measured review.
Final implementation/evidence reviewability is Red 69 / 118 estimated minutes,
rounded up from 117.1. The two source-bound generated proof files contribute 878
lines; retaining the pre-hardening evidence explains the size. Tests, behavior,
hardening and evidence are separate commits. No actual human review time or
provider CI is claimed. Existing component schema warnings and the installed
strict PR parser's `ids=[]` limitation are recorded separately from local checks.

## Changes Made

### 2026-09-09 - merge: local completion receipt

Completion ed50ead merged as 4e82325. Post-merge connected-contract tests pass
(28), and plan/rules/whitespace checks pass. The temporary validation checkout
was removed. Historical source-identity invalidation and the strict PR parser
limitation remain explicit; no push, provider CI, geometry or hand acceptance.

### 2026-09-09 - feat: implement and measure the connected contract

`connected_contract.py` defines fixed-tool bounded geometry/port admission,
conservative overlap declarations and actual ownership/corner audits.
`stroke_language.py` and `stroke_gestures.py` branch explicitly for the new
version; old guide serializations are unchanged. Connected sampling has one
shared port sample with outgoing ownership and both boundary contributors.
`gesture_actions.py` executes using the existing curve-tangent clock and
event-time-v2 controller, including genuine inter-letter air travel.

The final proof pins aa5feed and its test fixture. Maximum corner speed is
0.031478 mm/s, corner error 0.001548 mm and corridor error 0.025034 mm. Time,
contact and owner errors are zero. These are straight synthetic contract
fixtures, not repaired letters, fresh-seed validation or S2 admission. No target,
threshold, tool profile, fitting, context or fatigue changes.

Historical live admission is deliberately invalidated by changed shared source
identities. Five old-admission regression tests demonstrate this and pass on the
preserved fc562b8 source snapshot. Do not repin old evidence; obtain fresh
matching-source validation before relying on those admissions. CURRICULUM-015
may build an explicitly unaccepted preview, not inherit an old acceptance flag.

### 2026-09-08 - plan: register the contact-contract prerequisite

Source inspection confirms mandatory inter-gesture lifts and immutable old
foundation geometry. The owner explicitly requires pen-down upstrokes. This
record scopes implementation; no compiler, candidate or evidence was changed.
Planning checks pass for the plan, generated rules and whitespace. The installed
strict PR metadata parser returns `ids=[]` despite explicit Advance IDs in the
title and labels; no provider CI or implementation test pass is claimed.

## Check for Understanding

1. Why is contact-run identity distinct from gesture ownership?
2. Why must a pen-down reversal use corner timing rather than a smooth join?
3. Why does changing a compiler hash invalidate admission rather than update an old receipt?
