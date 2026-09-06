---
advance:
  id: "ADV-SS-HANDVALIDATE-014"
  title: "Pen-Action Evaluation — S1-Action and Letter-Readiness Decision"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","gesture","nibcontact","curriculum","pathguide","handflow","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: "2026-09-06T14:47:04Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: ["tdd:red-green", "tests:unit", "tests:integration"]
  model_usage: []
  status: complete
---

## Objective

Decide whether the frozen gesture/action layer is ready for letter-recipe learning, with supported and null actions explicitly scoped and real acceptance kept distinct from synthetic mechanics.

**Work kind:** Evaluation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Implementation/evaluation status and any unexecuted acceptance work are recorded below. No provider CI or owner approval is claimed.

## Behavioral Change

After this Advance: A reproducible S1-action/readiness record binds primitive, gesture, tool, controller and action identities. It permits only the evidenced scope downstream and explains blocked or rejected actions visibly.

## Component Impact

- `scribesim/handvalidate/pen_actions.py (planned evaluator)`
- `tests/test_handvalidate_pen_actions.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/action_evaluation/ (planned decision/sample index)`

These are planned implementation/evidence locations, not existing APIs.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-CURRICULUM-009](ADV-SS-CURRICULUM-009.md)
- [ADV-SS-HANDVALIDATE-013](ADV-SS-HANDVALIDATE-013.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [x] branch: confirm authorization before creating branches or commits.
- [x] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [x] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [ ] Validate live lower-layer hashes and S1-gesture decisions, then independently recompute the predeclared action metrics on frozen selected candidates. No tuning, new objectives or posthoc threshold relaxation.
- [ ] Replay all three seed checkpoints in fresh processes; compare direct, sampled desired and realized footprints, edge endpoints, angular/contact-rate tracking, contact topology and counter preservation.
- [ ] Use wrong-angle, swapped-edge, undeclared-lift, overbuilt-terminal, erased-counter and desired-only controls; verify each is detected by a named criterion.
- [ ] Preserve NIBCONTACT-001's failed global controls (hidden connector 0.0102; overbuilt terminal 0.0966 versus frozen 0.1 minimum). Add predeclared local-region and exact contact/overlap ownership checks; do not lower the original threshold or treat these investigation failures as action acceptance.
- [ ] Check fixed-geometry ablations, held-out combinations, finite bounds and action activation. A profile labeled active but insensitive fails; supported fixed/null profiles may pass only within their declared scope.
- [ ] Apply timestep and arc-length refinement against the frozen convergence bounds and common replay budget. Record scope and spent renders/time even if the evaluation stops early.
- [x] Publish a side-by-side sample index covering the original primitive baseline, continuous gesture practice, action comparisons and shared supplied-letter probes. Label synthetic, reference-grounded and human-reviewed evidence separately.
- [x] Issue an explicit letter-readiness decision: synthetic construction may proceed only with matching accepted synthetic lower layers; real fitting additionally requires live G0 and matching accepted real lower-layer evidence. Missing mandatory construction/action coverage blocks that inventory, not the entire existence of a fixed-tool baseline.
- [x] Carry forward G1 appearance/independent reading and G2 actual fidelity requirements; no action result authorizes fatigue, ink repair, folios or a default switch.
- [x] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] All activated actions have actual tracking and held-out benefit under frozen criteria; justified null outcomes retain an exact fixed-tool mode without pretending activation.
- [x] Readiness is invalidated by model/tool/controller/split changes and missing required coverage; stale or fabricated gate records fail closed.
- [x] A completed evaluation publishes stop/revise/proceed with all failures and scope restrictions. CURRICULUM-005 cannot infer accepted real prerequisites from Advance completion.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

A broad GO label can turn synthetic tool success into an unsupported historical-hand claim. Emit scope-qualified decisions and required inventory debt; rollback to fixed-tool checkpoints while retaining all negative evidence.

Review estimate: 40 minutes, not a measured reviewability score.

## Evidence

- [x] Frozen inputs, criteria and identities; complete render/time and revision ledger.
- [x] Readable equal-scale evidence and a reproducible command/sample index under the planned bundle.
- [x] Scope-qualified decision with negative/null/unresolved outcomes and genuine review only when performed.
- [x] Tidy assessment and TDD red/green evidence for code changes; focused tests and clean-checkout replay where applicable.
- [x] `arrive plan check`, changed-link checks and `git diff --check`.
- [x] Before authorized merge, run `arrive pr check --strict --json`; report installed-tool limitations separately from provider CI. Never claim unobserved CI or owner approval.

## Bug Fixes

None implemented. Defects discovered during execution require a recorded
diagnosis and bounded repair; unrelated changes and threshold relaxation are excluded.

## Changes Made

### 2026-09-06 — plan: Scope TD-018 gesture and intentional-action work

- Added to Pass 15 phase `td018-pen-actions`.
- Implementation, experiments and acceptance remain pending.

### 2026-09-06 — complete: Implementation outcome

- Evaluation outcome complete: STOP / REVISE. This is the required early-stop
  evaluation on current blocked inputs, not an implemented/accepted execution
  of selected-candidate metrics. Unexecuted candidate tasks remain unchecked.
- Red `fa1dab7`; pre-evaluation frozen scope `12d213f`; evaluator and immutable
  evidence `28750d1`. No preparatory refactor or optimizer invocation.
- Independently verify registered learning/upstream report identities, artifact
  digests, live code/tool/model binding, actual failed gesture checks and bridge
  convergence. Do not reuse a runner pass label or regenerate an old pass hash.
- All three seeds (7/19/41) repeat in fresh hash-seed-7/839 processes. Zero renders,
  zero optimization, 8.73 seconds total, no revision. Prerequisite failure prevents
  new target pixels or nonexistent selected-checkpoint evaluation.
- Failure reasons: unmatched covered S1-gesture, stale original renderer/bridge
  code identities, failed actual gesture/bridge convergence and no admitted
  fitted or justified-null actions. Letter training is disallowed in both scopes.
- Original global hidden-connector/overbuilt-terminal failures remain bound.
  Six new selected-action controls, held-out benefit, learned-counter checks and
  candidate refinement are explicitly not run. A fresh accepted experiment
  requires a newly frozen candidate evaluation; this reader has no optimistic
  approval fallback. Owner review is not performed; real G0/G1/G2 requirements stand.
- Mutation tests reject forged learning status and hand-edited GO. Tests forbid
  optimizer/render entry during early admission evaluation.
- 68 targeted/regression tests pass locally (31.44s) and clean clone
  `/tmp/td018-action-evaluation-clean.AMJnbV` at `28750d1` (20.58s).
  Full replay matches every semantic artifact; elapsed receipts vary.
- Local plan, 117 changed-document links and diff checks pass. Artifact doctor
  retains 10 pre-existing unrelated errors; agent rules are current. Strict PR
  check runs but the existing three-part-ID parser reports `ids: []`; no CI claimed.
- Base positional controller/planner, references, frozen primitive/gesture data
  and source reservations remain unchanged. A broader handflow test probe finds
  the pre-existing missing nib_angle_deg constructor argument, reproduced at the
  prior contact checkout and left outside scope. Older acceptance-consuming
  suites must use their archived code or newly validated gates, not edited hashes.
- [Layered samples, decision and remaining evaluation](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/action_evaluation/README.md).

## Check for Understanding

1. Which exact layer/tool/controller identities authorize the next letter experiment?
2. What is permitted after synthetic readiness when real G0 or appearance review remains blocked?
