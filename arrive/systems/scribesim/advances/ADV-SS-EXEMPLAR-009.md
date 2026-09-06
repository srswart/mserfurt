---
advance:
  id: "ADV-SS-EXEMPLAR-009"
  title: "Gesture Coverage Investigation — Vocabulary, Ductus Hypotheses and Admission Debt"
  system: "scribesim"
  primary_component: "refextract"
  components: ["refextract","curriculum","gesture","handvalidate","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Determine which additional stroke variants and continuous constructions the starter letters actually require, and whether real-source evidence can support them. Resolve coverage before adding attractive but unsupported shapes.

**Work kind:** Investigation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Drafting timestamp only: no implementation, investigation run, gate pass, CI or owner approval is claimed.

## Behavioral Change

After this Advance: A source-bound coverage workbook and stop/revise/proceed decision replace an assumed universal stroke inventory. Real G0 readiness is evaluated upstream of learning; unresolved readings and unavailable reviews remain explicit blockers.

## Component Impact

- `scribesim/curriculum/gesture_coverage.py (planned workbook tooling, if required)`
- `tests/test_gesture_coverage.py (planned tooling tests)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/coverage/ (planned evidence)`

These are planned implementation/evidence locations, not existing APIs.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-EXEMPLAR-008](ADV-SS-EXEMPLAR-008.md)
- [ADV-SS-CURRICULUM-004](ADV-SS-CURRICULUM-004.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before creating branches or commits.
- [ ] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [ ] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [ ] Audit at most the existing 52 non-test v3 reservations in one coverage/review pass. Keep all eight test reservations sealed; do not reopen the exhausted mask-repair budget. No new source acquisition or external-image import is authorized by this Advance.
- [ ] Classify directional stems/rises, left/right bowls, upper/lower turns and loops, entries/exits, open/closed forms, underturns, overturns and compound curves. Investigate short cross-strokes, hooks, diamonds and finishing overlaps only where a named letter construction motivates them.
- [ ] Record native source/crop IDs, split, reading/mapping status, independent support counts, proposed primitive decomposition, continuous-contact boundaries and competing ductus hypotheses. Never count multiple slices of one word as independent support or treat brush thick-down/thin-up rules as broad-edge physics.
- [ ] Select at most eight gesture candidates and twelve lowercase starter characters subject to admitted coverage. Record four-primitive expanded-letter limit hits rather than silently widening v1 limits; a required expansion needs a design/Advance revision before implementation.
- [ ] Record genuine externally supplied readings and target review only when available, using the existing source-bound import contract. Use a new immutable derivative if annotations change; preserve v3 and test bytes. Calibrate from admitted train/development repeats and negative controls only, then recompute live G0.
- [ ] If no genuine review/support exists, publish blocked G0 and a precise annotation/source-acquisition request with scope and proposed budget. Synthetic mechanics may proceed, but no real fitting, automatic reading approval or historical action claim follows.
- [ ] Freeze independently generated synthetic construction/transfer fixtures and provenance for the selected vocabulary; publish supported, unresolved, unnecessary/null and rejected rows with an explicit coverage-debt list.
- [ ] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] Every candidate has a named construction use and disjoint transfer exercise, or is explicitly unresolved/excluded; no relabeled old curve is passed off as a new learned variant.
- [ ] Coverage and admission are independently reconstructible; native coordinates, source-line grouping and test isolation remain intact.
- [ ] Deliver an actionable inventory and G0 readiness decision, including missing review/calibration. A completed investigation may conclude blocked; it does not pass G0 or S1.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

Static pixels underdetermine movement and contact. Preserve alternative hypotheses and immutable sources; rollback removes only the new workbook/tooling, never earlier failure evidence.

Review estimate: 30 minutes, not a measured reviewability score.

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

- Added to Pass 15 phase `td018-gesture-investigation`.
- Implementation, experiments and acceptance remain pending.

## Check for Understanding

1. Which proposed gestures have independent source support rather than repeated slices or modern instructional analogies?
2. What must be supplied or separately budgeted before real fitting can begin?

