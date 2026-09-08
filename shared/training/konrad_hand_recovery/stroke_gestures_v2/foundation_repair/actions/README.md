# CURRICULUM-012 — Fixed-tool null experiment

## Result — complete experiment, mixed null support

All three seeds complete with exact replay. **The full three-construction null
hypothesis is not supported at the unchanged absolute 0.05 limit.** This is a
measured result, not a missing implementation or an unexecuted experiment.

| Construction | Worst occurrence-local actual/target loss | Experimental result |
|---|---:|---|
| Underturn | 0.045681 | Fixed-tool null hypothesis supported in this scope |
| Overturn | 0.100653 | Unresolved; target error exceeds 0.05 |
| Compound curve | 0.097080 | Unresolved; target error exceeds 0.05 |

The per-construction rotation/edge/finishing dispositions mean **no added action
was needed by the supported null cases**, not that three dynamic profiles were
fitted or independently tested. No action is activated and no S1-action/null is
accepted here. Both whole-model null support and letter-training permission
remain false. HANDVALIDATE-016's earlier relative-improvement/motion acceptance
remains valid and unchanged; the absolute target criterion asks a different question.

Held-out isolated actual/target losses are 0.041174 (underturn), 0.096164
(overturn) and 0.091013 (compound). The two lifted pairings measure approximately
0.069721 and 0.069808. Overturn and compound miss the cap already in their frozen
nominal geometry: held-out nominal/target losses are 0.097100 and 0.090039.
The controller, contact boundaries, all four refinements, overlap/space controls
and all six declared negative controls pass. Good motion does not erase target error.
Actual/desired loss remains <=0.009494 and corridor error <=0.005519 mm across
the eleven null fixtures; their maximum refinement endpoint difference is
0.001063 mm. All five measured negative images still evade global 0.1: wrong
angle scores 0.047868, filled pocket 0.007885 and the three remaining mutations
are pixel-identical at evaluation resolution. Frozen exact tool/trace/local
guards reject them; the global misses are retained, not reclassified as passes.

**Diagnosis:** investigate remaining shared-geometry/target fidelity before
adding pen actions. Train-coordinate comparisons show accumulated source/target
endpoint gaps of 0.156525 mm for underturn/overturn and 0.175 mm for compound.
These are nominal-to-target differences, not controller tracking errors. They
support investigating attachment proportions and representational limits;
they do not prove a particular refit or finer grid will pass. No refitting or
threshold adjustment was attempted, and no held-out candidate replacement occurred.

**Evidence:** 1140 renders total, 380/5000 per seed including replay, each below
1800 seconds. No retry and zero optimization. Each seed replays 88 non-clock
artifacts exactly; all 536 manifest artifacts verify. All six candidate files
remain byte-identical to the admitted source. The selected-candidate reader
verifies the complete negative experiment without promoting it.

Report SHA: `ba2d46377b59787065486738e861aaea00c042cf0be2704072821aed3ac0fa3a`.
Experiment code: `623a687`; observed-red test commit: `77ff696`.

Validation: 48 focused tests pass, including all three saved-evidence regressions
in a clean detached checkout of `087be8c` (66.79 seconds). Expanded tests: 284
pass with the same 12 inherited failures. Plan/link/diff checks pass. Artifact
doctor retains its same 10 inherited issues and agent rules have no stale
outputs. The installed strict PR parser still returns `ids=[]` despite the
Advance ID in title/body/label; no provider CI, push or human review is claimed.

Local completion: merged into `master` as `6edc81d` on 2026-09-08. The completion
record distinguishes scientific null failure from finished implementation.
Test logs retain observed output; expanded-log trailing whitespace is normalized.

- [Layered sample index](../index.html)
- [Seed 7 native 900-DPI workbook](run-001/seed-7/first/practice-sheet.png)
- [Seed 19 workbook](run-001/seed-19/first/practice-sheet.png)
- [Seed 41 workbook](run-001/seed-41/first/practice-sheet.png)
- [Held-out overturn target](run-001/seed-7/first/held_out-overturn-target.png), [nominal](run-001/seed-7/first/held_out-overturn-nominal.png), [actual](run-001/seed-7/first/held_out-overturn-actual.png)
- [Selected hypothesis](run-001/seed-7/first/selection.json), [full report](run-001/report.json), [verification and geometry diagnosis](verification.json)

## What this work does

It tests the already learned strokes, without changing them: can the admitted
fixed full-edge tool reproduce independent synthetic targets accurately enough
without rotation, partial-edge contact or an added finishing pass? There is one
predeclared null hypothesis per seed, not an optimization search.

See the [pre-render scope investigation](investigation.md) and [frozen protocol](spec-v1.json).
All primitive curves, gesture reference proportions, recipes, pen settings and
controller/compiler code stay byte-identical to HANDVALIDATE-016's admitted input.
No existing gate, historical report or production renderer changes.

## Different questions, different gates

| Measurement | Question | Limit |
|---|---|---|
| Foundation relative improvement | Did learned geometry improve over its initial geometry? | Ratio <0.75; already accepted |
| Actual versus sampled desired | Does the controller follow its planned geometry? | Unchanged foundation motion/refinement limits |
| Actual versus independent target | Is the fixed-tool result absolutely close enough to the target? | Existing null loss <=0.05, also required locally |
| Nominal versus independent target | Does a target mismatch already exist before execution? | Diagnostic; not a substitute for actual evidence |

Loss is dimensionless, not an artistic score or a distance in millimeters.
Passing relative improvement or accurate motion does **not** establish the
stricter absolute null condition. Every occurrence and every refinement must
meet the local cap; averages cannot hide a poor constituent.

## Implementation and evidence

`scribesim/curriculum/foundation_actions.py` verifies the consumer-pinned live
foundation report and exact candidate bytes before writing a selected hypothesis
or opening target pixels. It freezes `selection.json` before measurements.
Train and development fixtures are diagnostic strata: neither selects a new
candidate. Held-out results cannot substitute a replacement. No fitting occurs.

The independent target family and frozen local regions are reused unchanged,
with eleven predeclared train/development/held-out fixtures. New held-out
transforms and pairings test same-target-family generalization, not a new hand.
Every fixture includes base, half arc step, half timestep and exact all-cubic
subdivision through existing execution adapters. Explicit lifted overlap,
adjacent and spaced carriers remain mechanical controls, not learned words.

Six controls reject wrong angles, partial-edge model requests, undeclared lifts,
overbuilt contributors, filled open pockets and substitution of desired poses
for actual traces. Wrong-angle realized ink is measured too. Global 0.1 misses
are retained. Partial-edge rejection is a schema guard, **not active physical
edge sensitivity**. Open pockets are **not closed-letter counters**. Independent
selected-action controls and broader physical action coverage remain separate.

Each seed receives 5000 renders or 1800 seconds including first/replay, controls
and refinements. Renders are journaled before execution. Existing outputs cannot
be overwritten, and another attempt requires a diagnosed cumulative protocol;
there is no automatic unbudgeted retry. All failures remain evidence.

## Reproduce and hand off

Run from a clean checkout of the committed experiment code with the existing
project environment. The stored destination is immutable:

```sh
.venv/bin/python -m scribesim.curriculum.foundation_actions \
  --output shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/actions/run-001
```

The parent runs fresh subprocesses with `PYTHONHASHSEED=0` and `839`. All
non-wall-clock artifacts must match byte-for-byte, and clock receipts remain
in the full manifest and budget. No optimizer, dynamic action fit, new tool
model or geometry fit is invoked.
All three seeds use the same frozen candidate: this demonstrates repeatability,
not three statistically independent learned hands or historical validity.

The selected-evidence reader is deliberately not an acceptance API:

```python
from scribesim.curriculum.foundation_actions import require_candidates

evidence = require_candidates(report_directory, expected_report_sha256=pinned_sha)
assert evidence['S1_action_accepted'] is False
assert evidence['letter_training_allowed'] is False
```

It verifies live foundation admission, current code/target identities, all-seed
measurements, exact candidate/selection/compiled-source lineage, replay and
budgets. It can return a scientifically negative but fully measured hypothesis
for independent review. A fabricated completion flag or omitted measurements
cannot authorize even that handoff.

HANDVALIDATE-017 must independently evaluate the scoped frozen candidates before
any S1-action/null claim. A target mismatch already present in nominal geometry
does not demonstrate that rotation, edge release or finishing is needed. Keep
that ambiguity explicit and investigate the shared geometry/target contract
before proposing dynamic actions. CURRICULUM-005 remains blocked. No fatigue,
ink depletion, real G0/G1/G2, owner appearance approval or default switch occurs.
