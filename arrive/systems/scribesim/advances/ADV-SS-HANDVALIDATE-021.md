---
advance:
  id: "ADV-SS-HANDVALIDATE-021"
  title: "Upright Construction — Independent Continuous-Contact Evaluation"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "curriculum", "gesture", "tests"]
  started_at: "2026-09-08T18:57:52Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 280
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 120
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration"]
  model_usage: []
  status: in_progress
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
- [ ] evaluate: isolated strokes/reversals, n/u/m and predeclared transfer probes at seeds 7/19/41 with fresh-process replay.
- [ ] evaluate: inserted lift, gap, false smooth reversal, overlap-owner, geometry/tool, climbing, desired-as-actual and visible-shift controls.
- [ ] evaluate: base/arc/time for letters; subdivision only within unchanged caps.
- [x] evidence: immutable partial reports, actual/nominal comparison samples, independent partial reader and renewed owner review request; full evaluation remains incomplete.
- [ ] merge: update implementation outcome separately from all acceptance flags.

## Bug Fixes

- [x] Ensure inter-gesture ownership changes do not imply actual pen lifts; saved n/u/m each have one contact run.
- [x] Detect repeated finite-nib coverage and missing overlap contributors, not only crossings; no darkness/depletion simulation claimed.
- [x] Implement rejection of cropped ink, substituted desired motion and stale source identities; the complete control experiment remains outstanding.

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

- [ ] tidy:preparatory if needed, otherwise record why isolation suffices.
- [ ] tdd:red-green; tests:unit and tests:integration.
- [ ] Complete full-frame traces/images, source identities and fresh-process replay.
- [ ] All negative controls fail for the intended reason; independent reader verifies archive integrity.
- [ ] Candidate-bound actual-ink owner review, distinct from numerical results.

## CI Evidence Notes

Continuation closeout: plan/rules/whitespace checks pass; provider CI is not claimed.
Browser inspection at 1440px and 390px confirms all nine saved comparison images
load, no page-wide horizontal overflow, and functional full-frame/detail controls.
The page explicitly identifies partial evidence and missing mu/replay/seeds/controls.
Screenshots were inspected at `/tmp/ss-h021-cont-desktop.png` and
`/tmp/ss-h021-cont-mobile.png`. The complete-run reader correctly rejects the
incomplete archive; all 204 frozen evaluation identity entries remain unchanged.

Run targeted/broader tests, plan/rules/whitespace and strict PR metadata checks.
Record only real provider/run evidence. Recalculate reviewability on actual work;
split test, implementation and evidence commits before merge.

## Changes Made

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
