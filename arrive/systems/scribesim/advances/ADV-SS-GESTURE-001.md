---
advance:
  id: "ADV-SS-GESTURE-001"
  title: "Stroke Gestures — Versioned Composition, Actions and Legacy Migration"
  system: "scribesim"
  primary_component: "gesture"
  components: ["gesture","evo","pathguide","handvalidate","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api","migration"]
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Introduce first-class continuous gesture and intentional action-profile identities without duplicating primitive geometry or reinterpreting frozen v1 bundles.

**Work kind:** Implementation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Drafting timestamp only: no implementation, investigation run, gate pass, CI or owner approval is claimed.

## Behavioral Change

After this Advance: An opt-in versioned compiler expands primitive → gesture → letter → word → line ownership. Continuous multi-segment strokes retain contact, while lifts and overlapping finishing gestures remain explicit.

## Component Impact

- `scribesim/evofit/stroke_gestures.py (planned schema/compiler sibling)`
- `scribesim/evofit/stroke_language.py (explicit version dispatch only as needed)`
- `tests/test_stroke_gestures.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/language/ (planned fixtures)`

These are planned implementation/evidence locations, not existing APIs.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-EVOFIT-007](ADV-SS-EVOFIT-007.md)
- [ADV-SS-EXEMPLAR-009](ADV-SS-EXEMPLAR-009.md)
- [ADV-SS-NIBCONTACT-001](ADV-SS-NIBCONTACT-001.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before creating branches or commits.
- [ ] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [ ] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [ ] Implement versioned StrokeGesture and PenActionProfile records over shared primitive IDs. Enforce flat nonrecursive gesture references, ports, declared smooth/corner topology and explicit separate lift/overlap occurrences.
- [ ] Validate finite ordered normalized-arc-length knots, endpoint coverage, units/frame, active-edge intervals and frozen action/rate envelopes. Reject required unsupported actions, stationary dabs and nonconstant pressure/speed in the initial contract.
- [ ] Enforce at most eight gestures, four primitive references per gesture and four knots per active track, plus all existing expanded-letter/character/context budgets. Macro expansion must not multiply the four-primitive-per-letter allowance.
- [ ] Compile globally by gesture arc length so repartitioning a continuous path introduces no settling pause, lift or pressure reset. Preserve primitive, gesture, action-profile and exact letter/word/line spans, including overlap contributors.
- [ ] Hash all shared records and dependencies, invalidate compiled caches after changes and reject stale summaries or hidden per-letter residual geometry.
- [ ] Provide explicit v1 fixed-action migration with lifts splitting gestures. Preserve legacy rendered pixels, contact schedules and logical/occurrence lineage with a recorded ID mapping, or refuse unsupported migration. Old readers fail on required new fields; no silent fallback.
- [ ] Publish decomposition and segmentation-equivalence fixtures with the fixed-tool path; dynamic actions remain execution-unsupported until the contact/bridge Advances land.
- [ ] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] Tests reject cycles, missing identities, malformed tracks, illegal contacts/crossings, expansion bypasses, unsupported actions and stale caches.
- [ ] Repartitioning equivalent continuous geometry preserves contact and output within frozen tolerances; separate finishing passes retain explicit lifts and multiple owners.
- [ ] Legacy bundle replay remains unchanged or migration is explicitly rejected. No completed v1 S1 record is relabeled as a new gesture-learning pass.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

Macros can hide copied character curves or bypass budgets. Keep v1 loaders/evidence unchanged and the new schema opt-in; rollback removes only new version dispatch and dependent bundles.

Review estimate: 40 minutes, not a measured reviewability score.

## Evidence

- [ ] Frozen inputs, criteria and identities; complete render/time and revision ledger.
- [ ] Readable equal-scale evidence and a reproducible command/sample index under the planned bundle.
- [ ] Scope-qualified decision with negative/null/unresolved outcomes and genuine review only when performed.
- [ ] Tidy assessment and TDD red/green evidence for code changes; focused tests and clean-checkout replay where applicable.
- [ ] `arrive plan check`, changed-link checks and `git diff --check`.
- [ ] Before authorized merge, run `arrive pr check --strict --json`; report installed-tool limitations separately from provider CI. Never claim unobserved CI or owner approval.

## Bug Fixes

None implemented. Defects discovered during execution require a recorded
diagnosis and bounded repair; unrelated changes and threshold relaxation are excluded.

## Changes Made

### 2026-09-06 — plan: Scope TD-018 gesture and intentional-action work

- Added to Pass 15 phase `td018-gestures`.
- Implementation, experiments and acceptance remain pending.

## Check for Understanding

1. How can three primitive segments remain one pen-down gesture without losing their individual ownership?
2. Which changes invalidate a compiled model, and when must legacy migration fail?

