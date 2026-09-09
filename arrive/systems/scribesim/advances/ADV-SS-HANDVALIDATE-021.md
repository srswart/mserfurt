---
advance:
  id: "ADV-SS-HANDVALIDATE-021"
  title: "Upright Construction — Independent Continuous-Contact Evaluation"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "curriculum", "gesture", "tests"]
  started_at: "2026-09-08T18:57:52Z"
  implementation_completed_at: "2026-09-09T06:29:14Z"
  review_time_estimate_minutes: 786
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 120
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration"]
  model_usage: []
  status: complete
---

## Objective

Independently evaluate a reviewed, frozen upright pen-down construction without
refitting or weakening existing gates. Follows
[TD-018 Addendum B section 13](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#13-upright-pen-down-construction-repair).
Depends on GESTURE-003, CURRICULUM-015 and its explicit owner-review checkpoint.

## Behavioral Change

Separate actual contact/overlap/timing and geometric/image evidence from nominal
construction and owner appearance. Use new immutable artifacts and an independent
reader; do not invoke the builder's decision function as validation. Mechanical
success cannot override the owner's repair verdict or grant context permission.

## Component Impact

- `handvalidate`: proposed `upright_letters` frozen replay and read-only evidence reader.
- `curriculum` / `gesture`: consume exact reviewed candidate and new contract identities.
- `tests`: independent gates, adversarial controls, replay and archive immutability.
- Proposed outputs: `letters/upright/validation/` under the existing training tree.

## Planned Implementation Tasks

- [x] branch: create `advance/ss-handvalidate-021` after CURRICULUM-015 merges.
- [x] prerequisite: owner endorses the frozen CURRICULUM-015 nominal n/u/m; candidate-bound keep verdicts recorded. This is not actual-ink review.
- [x] prerequisite: freeze independent analytic target provenance/version, candidate/code hashes and all evaluation budgets before scoring.
- [x] tidy: isolate reader/measurement logic without mutating frozen source artifacts.
- [x] test: commit failing independent decision, ownership and archive tests first.
- [x] feat/fix: implement no-fit actual-motion and full-frame image evaluation.
- [x] evaluate: isolated strokes/reversals, n/u/m and predeclared transfer probes at seeds 7/19/41 with fresh-process replay.
- [x] evaluate: inserted lift, gap, false smooth reversal, overlap-owner, geometry/tool, climbing, desired-as-actual and visible-shift controls.
- [x] evaluate: base/arc/time for letters; subdivision only within unchanged caps.
- [x] evidence: immutable complete reports, actual/nominal comparison samples, independent read-only verification and renewed owner review request; both earlier failures preserved.
- [x] merge: update implementation outcome separately from all acceptance flags; local merge `9368fc4`, no push or provider CI claim.

## Bug Fixes

- [x] Ensure inter-gesture ownership changes do not imply actual pen lifts; saved n/u/m each have one contact run.
- [x] Detect repeated finite-nib coverage and missing overlap contributors, not only crossings; no darkness/depletion simulation claimed.
- [x] Implement rejection of cropped ink, substituted desired motion and stale source identities; complete negative-control experiment detects all eleven intended violations.

## Risk + Rollback

The new target must be independently defined from reviewed requirements, never
candidate pixels/cubics. Keep absolute/local image limits 0.05, relative loss
0.75, nominal level residual 1e-8 and actual landmark limit 0.05 mm unchanged.
The relative comparison uses both candidates against the same new target; reject
an undefined ratio. Freeze proposed angle/clearance criteria separately after
review. Preserve failures, use zero automatic retries and require a new explicit
scope for any fitting. Exact fixtures/render/time budgets are prerequisites, not
permission to inherit an unrelated old budget. Roll back by withholding new
admission, never erasing failed evidence. S2/real/context remain false unless
their separately explicit acceptance requirements are satisfied; no fatigue.

## Evidence

- [x] tidy:preparatory not needed; new wrappers/readers isolate changes without rewriting frozen evaluators.
- [x] tdd:red-green; tests:unit and tests:integration.
- [x] Complete full-frame traces/images, source identities and fresh-process replay.
- [x] All negative controls fail for the intended reason; independent reader verifies archive integrity.
- [x] Candidate/report-bound owner KEEP for actual n/u/m and mu placement, recorded after explicit scope clarification. Numerical target-image failure and S2/real/context restrictions remain unchanged.

## CI Evidence Notes

Latest closeout: 145 focused tests pass in 80.94 s. The broader suite before the
four final reader tests has 163 passes and five pre-existing curve-tangent
admission failures, previously reproduced on pre-work `85e3b44`. No old source
guards are repinned. Plan/rules/whitespace checks pass. Strict PR metadata parsing
still returns `ids=[]` despite explicit IDs in title/body/labels; no provider CI
or remote merge is claimed.

Browser inspection at 1440px and 390px confirms all twelve saved comparison images
load, no page-wide horizontal overflow, and functional full-frame/detail controls.
The page distinguishes completed evaluation, image-target failure and pending
owner review. Screenshots inspected: `/tmp/ss-h021-event-desktop.png` and
`/tmp/ss-h021-event-mobile.png`; actual mu full-frame PNG also inspected. All 206
frozen evaluation identities remain unchanged after read-only reader repair.

Run targeted/broader tests, plan/rules/whitespace and strict PR metadata checks.
Record only real provider/run evidence. Recalculate reviewability on actual work;
split test, implementation and evidence commits before merge.

## Changes Made

### 2026-09-09 - owner approves actual ink and bounded placement sample

Owner: “okay got it -- yes then all are approved.  They look great.” This follows
clarification that mu tests fixed placement and interletter air movement, not
joining, spacing design or contextual stroke adaptation. Record actual n/u/m KEEP
and placed-mu KEEP in `continuation-002/actual-review.json`, bound to the unchanged
candidate and complete report hashes. Nominal approval remains separate.

Gallery and current plan/outcome now show appearance approved. Frozen reports and
the independent inspection retain their historical pending-review values; the
later external owner record does not rewrite evidence or turn numeric failure
into a pass. No code, candidate, target, threshold, render, execution, fit or new
admission changes. Next is separately scoped analytic-yardstick reconciliation,
not automatic context/fatigue work. Earlier entries retain checkpoint history.
Approval hash bindings and all 1,256 archived artifacts verify unchanged;
plan/rules/whitespace checks pass. Documentation/review-only update, no experiment
rerun. The existing strict PR metadata parser limitation persists; no provider CI.

### 2026-09-09 - local merge receipt

Merged `advance/ss-handvalidate-021` into local master at `9368fc4` after the
completed bounded replay, independent saved-evidence verification and 145 passing
focused tests. Final plan/rules/whitespace checks pass. The installed strict PR
metadata parser limitation and five pre-existing old admission test failures are
recorded above, not claimed fixed. No push or provider CI. All frozen identities
and report hashes remain unchanged; no extra experiment follows the merge.
Implementation is complete; numeric target failure and pending owner actual-ink
review continue to withhold all new acceptance and context permission.

### 2026-09-09 - complete repaired replay and independent verification

One authorized no-refit attempt frozen at `a97428b` completes all ten fixtures,
four refinements and eleven negative controls in six fresh workers. Seeds 7/19/41
each replay byte-identically. Archive `continuation-002/run-001` is preserved in
`5a01a6d`; report SHA256
`c986db16fbbac20d8ce66844a6789d5198b8deaa1c00bc70b97682b823488655`.
There are 966 new render calls, 1,115 with prior debits, zero optimization and no
extra execution attempts. Combined per-seed calls/time: 7 = 471/137.381661 s;
19 = 322/95.802606 s; 41 = 322/108.769607 s, within unchanged budgets.

All motion, tracking, nominal/actual level/port, overlap and convergence gates
pass. Total-clock error and projection are zero. Maximum convergence event
position/time/image differences are 0.00560306 mm / 2.0961e-13 s / 0.00224349,
below unchanged 0.01 mm / 0.0001 s / 0.03 limits. Continuous n/u/m and the declared
two-contact-run mu placement complete; all controls detect intended violations.

Only target-image gates fail: nine fixtures times five views = 45 failures per
worker. Stem passes its target gates. n/u/m base target losses remain
0.382013/0.232051/0.589663, exceeding 0.05; relative ratios pass 0.75. This independent
analytic yardstick is not an owner-approved replacement. Implementation/evaluation
is **complete with a numeric failure**, not S2/real/context or actual-ink acceptance.
Nominal KEEP candidate/report/review hashes, targets and all limits are unchanged.

The initial frozen reader caught a negative-control count mismatch: JSON loses
shared owner-object identity, so mutating one decoded owner affects one row rather
than the original eight. Both correctly detect the owner gate. That failure is
preserved in `continuation-002/initial-reader-failure.json`. Red `fa4f8a3`, green
`e3ec964`: separate read-only script reconstructs original mapped-owner aliases
after exact saved-value checks; it rejects corrupted owners and changes no values,
frozen code or archived evidence. No rendering/execution/refit. Four new tests
pass; the complete independent reader verifies **1,256 artifacts**, all six worker
records, controls, replay, budgets and failed decisions. Receipt is outside the
immutable archive at `continuation-002/inspection.json`.

`arrive score --base 85e3b44 --json` remains red, 120; estimated review time is
approximately 786 minutes, dominated by retained evidence files. TDD, core fixes,
orchestration, immutable experiment and separate reader are distinct commits.
Actual human review time is unknown, not this estimate. No unrelated YAML or
historical admission repair is included.

The gallery now includes complete n/u/m/mu nominal/actual/analytic comparisons at
900 DPI, retaining 180-DPI full-frame metric pixels. Actual-ink owner review is
pending in `continuation-002/actual-review.json`. Next checkpoint: review actual
ink and explicitly reconcile the independent yardstick with desired appearance
before any target revision/fitting; no context or fatigue expansion.
The entries below preserve historical checkpoint states, not current blockers.

### 2026-09-09 - authorized boundary/event repair and pre-run freeze

Owner explicitly approves boundary sampling repair, exact-event comparison and
one bounded no-refit rerun with unchanged targets/thresholds. Authorization is
frozen in `continuation-002/authorization.json`, binding the original spec, both
failed reports and the two repair hashes (plus the already approved scalar adapter).

Red `814fc5b`: five regressions fail, including translated mu and old grid-dependent
comparisons. Green `aab177f`: connected-only sampling drops ordinary arc-grid
shadows within eight machine ULPs of an exact boundary, never the boundary itself;
distinct nearby targets and legacy sampling are preserved. The planner's existing
uniqueness/geometric tolerances are unchanged. All ten frozen fixtures and four
refinements pass plan-only preflight without controller execution or scoring.

`declared-contact-events-v1` compares actual records at the same entry/corner/end
events with stable contact, gesture and contributor identity. Missing/duplicate
events and incomplete corner inventories fail closed. Saved n/u/m trace tests
verify event correspondence without rerendering or modifying old results. All
existing endpoint/time/image limits remain unchanged. The focused repair/clock/
gesture suite passes 79 tests; source/replay/repair checks pass 33 tests.

Red `cb593c5` precedes the new `upright_event_replay` wrapper. Its new authorized
source loader checks byte-pinned nominal archives and both prior attempts without
repinning old readers; those readers deliberately reject the changed sampler.
Both failed archives and prior inspection receipts are immutable. Seed 7 starts
with 149 calls and 34.57516137394123 seconds already debited from the unchanged
5,000-render/1,800-second cap; seeds 19/41 have zero debit. One new attempt writes
only `continuation-002/run-001`, freezing all current identities before scoring.
No refactoring of archived runners was needed; new orchestration is isolated.
No candidate/target changes, acceptance or additional automatic retry is implied.

### 2026-09-09 - continuation measured n/u/m, blocked on finer placement plan

The authorized attempt is preserved in `28b1b30`: nine complete saved fixture
records with four refinements each, seed 7 first process only. Its finer-arc
`placed-mu` plan stopped with `Exact unique corner port required`; no full fixture
record, replay, seeds 19/41 or complete negative-control suite follows. There are
147 new render calls, 149 including the first failure, and 34.57516137394123 seconds
combined seed-7 execution. No automatic retry or optimization occurred.

Continuation report: `cc4a202e570d292ad899493e5ca53e7cad7b4f796f5e87349af5274d9e587b5c`.
The separate non-admitting partial reader verifies 180 artifact hashes and all
nine completed records from saved traces/pixels/masks without rendering or motion.
Reader red `7a283bd`, green `a2c938b`; two new tests pass. The broader continuation,
construction, contact, action, clock, corner, reentry and repertoire-state suite
has 100 passes before those two partial-reader additions. Five older admission
failures remain independently reproduced on pre-work `85e3b44`.

Final focused validation includes the partial reader: **102 passed in 44.64s**.
`arrive score --base 85e3b44 --json` is red, 120, with 279.6 estimated review minutes
(frontmatter rounded to 280). The retained partial archive contributes 181 files;
tests, implementation, failed evidence and non-admitting inspection are split into
separate commits rather than hiding the experiment inside one implementation diff.
This is a machine estimate, not completed human review. Existing component-YAML
warnings and the strict PR metadata parser limitation remain outside scope.

Saved n/u/m have one contact run each, passing per-run motion checks at all four
refinements, zero total-clock error/projection and no undeclared overlap pairs.
Maximum port errors are 0.006925/0.019878/0.011017 mm; all are below 0.05 mm.
This is **not a whole-protocol pass**: absolute/local target losses are
0.382013/0.232051/0.589663 versus 0.05, and saved convergence gates also fail.
Relative ratios 0.609119/0.279661/0.662173 pass their separate 0.75 limit.
The synthetic semicircle target is not an owner-approved replacement; nominal
KEEP feedback and candidate/target/gates remain unchanged.

Plan-only diagnosis (no new controller execution, scoring or rendering) finds
two finer-grid samples at m's translated corner: indices 631 and 632, incoming
parameter 0.9999999999999996 and outgoing parameter 0. They differ by only
1.7763568394002505e-15 mm. Exact `np.unique` retains a near-boundary ordinary grid
sample beside the explicit outgoing port; the clock correctly rejects two nearby
matches. Separately, convergence compares first/last gesture-owned integration
samples, whose times vary with resolution. Saved declared corner/terminal times
match base/arc/time exactly and subdivision within 2.10e-13 s; saved comparison
errors up to 0.008 s are not evidence of total-clock drift. No gate was changed.

Next scope: repair boundary sample canonicalization preserving outgoing ownership
and both contributors, and use identical declared events for convergence. Only a
new explicit bounded authorization may rerun repaired code, retaining both failed
archives/debits and unchanged candidates/targets/limits. Image-target failure is
still separate. This Advance stays **in progress and unmerged**. The gallery shows
only verified saved partial n/u/m and explicitly withholds incomplete mu. Actual
owner review is pending in `continuation-001/actual-review.json`; S2/real/context
remain false. Detailed measurements and source locations are in the training
tree's `letters/upright/validation/outcome.md`.

### 2026-09-09 - owner authorizes one bounded no-refit continuation

Owner: “Yes approved - go ahead.” Authorization is recorded before execution in
`letters/upright/validation/continuation-001/authorization.json`. The original spec
hash, failed report hash and sole scalar-adapter repair hash are pinned. No old
archive, candidate, target, fixture, criterion or budget is changed. The new runner
debits two render calls and 0.8869196659652516 seconds from seed 7's unchanged
5,000-render/1,800-second allowance; waiting for authorization is not execution.
Seeds 19/41 have no prior debit. No further automatic attempt is permitted.

Red `ab653a5` precedes the new continuation wrapper; 13 evaluator/continuation
tests pass, including source binding, budget debit, no-overwrite and consumer-pin
checks. Existing measurement/reader code is unchanged. The generic worker and
read-only evidence reader are reused; continuation accounting is separately
verified against the pinned failed ledger. New artifacts go only to
`continuation-001/run-001`, with identities frozen before any render.

### 2026-09-09 - preserve pre-score failure, repair adapter, await continuation

The one permitted attempt stopped before scoring in seed 7's first process:
`Unsupported physical contact fields`. Two render calls were charged; nominal
guide coordinates were NumPy float64 rather than supported Python scalars. No
fixture completed, no replay/seed 19/41 ran, and this is **not** a candidate
appearance or numeric failure verdict. `run-001` is immutable in `c722bd1`, with
report SHA256 `6f4678661d6d5103311ac88040f29ad36cd0247d03c45fb9909e0145e4685421`.

Red `50b5330` reproduces the adapter boundary without rendering or scoring the
candidate. Green `21151c4` performs scalar conversion only, without rounding or
changing geometry, targets, thresholds or physical fields. Eight evaluator tests
and adjacent nominal/connection/action tests pass: 49 total. The five older
curve-tangent admission failures reproduce on clean pre-work `85e3b44` (22 pass,
five fail in that file). Existing source candidate, report and KEEP review hashes
are unchanged. New modules isolate the change; no tidy/refactor claim is needed.

Plan/rules/whitespace checks pass. Strict PR metadata still fails with `ids=[]`
despite explicit title/body/label IDs; no provider CI is asserted. The reviewer
gallery explicitly withholds missing actual samples rather than displaying broken
or mislabeled comparisons.

**No automatic retry.** One new bounded no-refit continuation has been requested
from the owner and is not yet authorized or executed. It must preserve this
failure, freeze the new code/authorization and output path, bind the failed report
hash and include the two prior seed-7 calls in its cumulative budget. All candidate,
target and acceptance limits stay unchanged. This Advance remains in progress;
evaluation, actual-ink owner review and merge are deliberately not marked done.

See `letters/upright/validation/outcome.md` under the training tree for the exact
boundary and remaining work. No S2/real/context admission, fitting or fatigue.

### 2026-09-09 - implementation and pre-score protocol freeze

New isolated `upright_targets`, `upright_measurement`, `upright_letters` and
`upright_evidence` modules leave all frozen builders, controllers and previous
readers untouched. No preparatory refactoring is needed. The target accepts only
the frozen specification and fixture: vertical lines and round-number semicircles,
not candidate curves/pixels. This is an independent synthetic yardstick, **not an
owner-approved aesthetic target**. New aesthetic angle/clearance thresholds are
not invented; slant and repeated coverage remain diagnostics.

The pre-score spec pins candidate `01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd`,
its report and nominal KEEP record, the old comparison candidate, ten fixtures,
four refinements, unchanged numeric gates and 5,000 renders/1,800 seconds per seed
including replay, zero retries and zero optimization. The runner writes complete
code/spec identities before executing any candidate. Source subdivision uses two
exact internal cubics, not extra references: all existing caps validate, including
six expanded references for m. It can therefore be measured for full letters.

Red: `c937cc0` missing evaluator import; `5e43d25` exercises a synthetic two-letter
retrace and fails on serialized identity/air-field handling. Green: seven new
tests pass. The broader five-file suite has 70 passes and five pre-existing stale
admission failures in `test_curve_tangents.py`; no archived source is repinned.
The synthetic integration fixture is not the reviewed candidate and does not
score it. Actual candidate evaluation has not run at this checkpoint.

### 2026-09-09 - prerequisite: nominal appearance checkpoint satisfied

The owner approves CURRICULUM-015's nominal n/u/m appearance; all three verdicts
are keep in its separate candidate-bound owner-review record. The candidate and
frozen evidence are unchanged. This Advance remains planned: independent target,
fixture, criterion and budget freeze still precedes execution. No refitting or
physical validation is performed by recording the feedback.

### 2026-09-08 - plan: register independent evaluation after visual review

No render, target revision, fitting or acceptance occurs when registering this
Advance. Exact target/fixture/budget freeze and reviewed candidate are execution
prerequisites. HANDVALIDATE-020's archived evidence remains unchanged.
Planning checks pass for the plan, generated rules and whitespace. The installed
strict PR metadata parser returns `ids=[]` despite explicit Advance IDs in the
title and labels; no provider CI or implementation test pass is claimed.

## Check for Understanding

1. Why must a nominal preview and an actual-ink owner review be separate?
2. How is continuous contact proven without losing individual gesture ownership?
3. Why cannot an undefined ratio or isolated subdivision proof pass a whole-letter gate?
