# HANDVALIDATE-017 — Independent fixed-null evaluation

## Completed approved measurement — scoped result

The approved diagnostic repair works. **All three frozen seeds complete with
exact replay and all nine adversarial controls detected.** Underturn receives
independent fixed-tool null acceptance for the declared synthetic scope.
Overturn and compound remain unresolved at the unchanged absolute 0.05 limit.
The whole-inventory report correctly says `status=fail`, while
`evaluation_complete=true` and `accepted_gestures=[underturn]`.

| Construction | Worst local actual/target loss | Independent disposition |
|---|---:|---|
| Underturn | 0.044704 | Accepted scoped fixed-tool null |
| Overturn | 0.099430 | Unresolved; exceeds 0.05 |
| Compound curve | 0.093600 | Unresolved; exceeds 0.05 |

Actual paths, prior rendered pixels, targets, local regions and motion metrics
are unchanged from run-002. Only diagnostic representation/classification and
control evidence completion change. No candidate fitting, reference change or
threshold relaxation occurs. Nominal geometry already misses the independent
overturn/compound targets; this is not evidence for adding dynamic pen actions.

The physical-edge test now detects the swapped side: endpoint error changes
from approximately 8.9e-16 mm to 0.2475 mm, with global loss 0.788730. It remains
an asymmetric physical-render diagnostic on the selected actual path, not an
accepted active physical action. The diagnostic counter is enclosed and blank
for target, nominal and all four actual refinements; filling its frozen region
changes local ink fraction from 0 to 1. This is not a learned letter.

All eight other control images still evade the unchanged global 0.1 detector.
Wrong angle scores 0.082283; overbuilt terminal 0.007314; erased counter 0.007294;
filled open pocket 0.007951; air connector 0.001112; the remaining three score 0.
Exact tool/contact/contributor audits and local blank guards reject them.
Historical failed controls remain preserved, not reclassified as global passes.

New renders: 1086; prior failed renders: 1650; cumulative total: **2736**, or
**912/5000 per seed**, including every first/replay, control and presentation.
Per-seed cumulative time stays below 260/1800 seconds. One original revision
plus one explicitly user-approved measurement-only continuation; zero fitting.
No further automatic attempt is authorized.

- [Native four-column seed-7 workbook](run-003/seed-7/first/practice-sheet.png)
- [Seed 19 workbook](run-003/seed-19/first/practice-sheet.png) / [seed 41 workbook](run-003/seed-41/first/practice-sheet.png)
- [Actual diagnostic closed counter](run-003/seed-7/first/closed-counter-carrier-actual.png)
- [Independent manifest](run-003/S1-actions.json) / [complete control checkpoints](run-003/seed-7/first/controls.json)

Frozen execution code: `9100977`; approved repair RED: `2e79204`. Manifest SHA:
`90f26d501d8860717bf8c40d394c7a25df679c8e63d4b58995ecba3e61fba2ef`.
The opt-in reader accepts an explicitly requested underturn-only fixed-null
scope and rejects the full three-construction inventory. It never grants
letter or real-hand approval. CURRICULUM-005 remains blocked pending matching
complete gesture/action/reference prerequisites. Next: investigate shared
geometry/target fidelity before proposing new fitting or pen actions.

Verification: **73 focused tests pass**, including current scoped admission,
rejection of forged whole-inventory flags, and unchanged prior paths/pixels.
The expanded selection passes 310 tests with the same 18 inherited failures
(before three additional saved-evidence regressions). See
[approved verification](approved-verification.json). Local merge and governance
receipts are recorded in the Advance; no provider CI or owner review is claimed.

## Historical run-002 stop — retained, superseded only by approved measurement

The following records the stop before the user's additional repair approval;
it is not the current completion or acceptance decision.

All three seeds execute nine fresh heldouts, three mechanical contexts and the
closed-counter carrier, then reproduce the same diagnostic adapter failure.
Each first/replay pair matches 80 non-clock artifacts. All candidate bytes are
unchanged. New renders: 1062; retained failed renders: 588; total: 1650, or
550/5000 per seed. Cumulative per-seed time is at most 148.318/1800 seconds.
Zero fitting; the one allowed automatic revision is used.

| Construction | Worst fresh local actual/target loss | Absolute 0.05 check only |
|---|---:|---|
| Underturn | 0.044704 | Meets target limit; NOT independently admitted |
| Overturn | 0.099430 | Exceeds target limit |
| Compound curve | 0.093600 | Exceeds target limit |

Existing motion/contact/refinement checks pass. The closed blank is enclosed
and unpainted for target, nominal and all four actual refinements. These partial
proofs do not override missing adversarial controls or the new diagnostic guard.

Two evaluator defects need a measurement-only repair:

1. `physical_samples` forwards live NumPy scalar coordinates into the strict
   physical `ContactSample` contract, which requires built-in scalar types.
   A no-render controller replay confirms actual `float64` coordinates;
   serialization converts them to Python floats and hides the mismatch.
   Normalize scalar representation at this diagnostic boundary, preserving
   values, physical constraints and the unchanged selected candidate.
2. The new constant-tool guard compares a computed angular rate with exact zero.
   Floating interpolation of 40 degrees produces rates up to 2.50748e-10 deg/s,
   although every angle passes the existing 1e-12-degree fixed-angle check.
   Preserve raw rate diagnostics and classify the constant tool using its
   already-frozen sample tolerance; do not relax angle or physical limits.

The first six mutation images are preserved, but the interrupted controls
function did not save its completed numeric record. Swapped-edge rendering,
erased-counter/open-pocket negatives and complete control proof remain missing.
No new control pass or S1-action/null acceptance is claimed, including underturn.
The reader rejects this incomplete report. CURRICULUM-005 remains blocked.

**Approval requested:** one additional diagnosed measurement-only repair and
fresh replay, keeping candidates, independent targets, limits and all failed
artifacts unchanged and charging the same cumulative per-seed budgets. Also
journal each completed control immediately so a later stop preserves its proof.
No additional run or implementation of that repair has been performed.

- [Recorded stop and all artifact hashes](run-002/S1-actions.json)
- [Verification and budget summary](verification.json)
- [Actual closed-counter carrier](run-002/seed-7/first/closed-counter-carrier-actual.png)
- [Fresh underturn](run-002/seed-7/first/independent-underturn-1-actual.png),
  [overturn](run-002/seed-7/first/independent-overturn-1-actual.png),
  [compound](run-002/seed-7/first/independent-compound_curve-1-actual.png)
- [Counter proof across refinements](run-002/seed-7/first/closed-counter-carrier.json)

Native actual counter image inspected; no browser or human appearance review
claimed. Code is preserved at `8e578f8`, with stop report SHA
`f7a6d96dccb418e058f7a5daf96bde8af754e76f3868e2d0a609f8b7afb51933`.

Validation: **65 focused tests pass** (64.19 seconds). The expanded selection
passes 305 tests and has 18 existing failures: the prior 12 unchanged failures,
plus six folio-resolution failures reproduced in a clean pre-task `ac08daf`
checkout. Logs are retained with trailing whitespace normalized. Plan, 132
local links and diff checks pass; artifact doctor retains the same ten issues,
and agent rules are current. No provider CI, push, merge or owner review claimed.

## Preserved stop and one diagnosed revision

`run-001` at code `8151001` stops on a carrier-construction error, not a new
target-quality decision: compound plus return contains seven primitives, above
the unchanged six-per-carrier cap. The first counter placement also exceeds
the unchanged lowered +/-2 transform bound. All six workers retain their
seven completed fixtures, 98 renders each (588 total, 196 per seed).
No counter, six-class control or complete action acceptance is claimed there.

The one permitted revision freezes `spec-v2.json` before new rendering. Its
seven already executed fixtures are identical. The two unrenderable pairings
become compound/terminal and reverse-return controls; seven-stroke coverage
stays missing, not silently accepted. Both counter instances translate by
-0.2 normalized y and its frozen blank region by +0.7 mm, preserving relative
geometry. Candidate curves/proportions, independent target definitions and
every numerical limit remain unchanged. No target-quality ranking informs this
schema repair. Added tests expose the original error before the revision.

`continuation-v1.json` pins the failed report and charges its actual renders and
time to the same per-seed budgets. No second revision or refitting is authorized.

## Frozen method

Pin CURRICULUM-012 report
`ba2d46377b59787065486738e861aaea00c042cf0be2704072821aed3ac0fa3a`,
and candidate bytes
`d8b26fba2655b0bba961865fb74b543829cb1b11ac850afd672dd02ba0822e5a`.
Reconstruct live independent foundation admission before new target access.
No fitting, action activation, candidate replacement or threshold relaxation.

Nine new held-out transforms/pairings use the independently authored, unchanged
Hermite-plus-sine target family. Absolute actual/target loss remains <=0.05,
both globally and for every occurrence/refinement. Nominal/target error remains
diagnostic; accurate actual/desired tracking alone cannot grant null acceptance.
The evaluator does not call the learning measurement or acceptance predicates.
Shared frozen execution, raster, metric and presentation helpers remain identical.

Three overlap/adjacent/space carriers preserve contact entry/exit, source and
contributor ownership, fixed footprint, zero angular rate, and timestep/arc/
exact all-cubic subdivision proofs. They are not learned letters or words.

Six historical adversarial classes are frozen: wrong angle, swapped edge,
undeclared lift, overbuilt terminal, erased counter and desired-only actual
proof. Additional missing-overlap, air-connector and open-pocket controls are
required. Overbuilt terminals alter actual ink as well as contributor identity.
Global 0.1 misses and historical failed controls remain visible.

The swapped-edge control uses the existing explicit physical renderer on a
selected actual path, with asymmetric intervals [0,0.45] and [0.55,1]. An
independent analytic endpoint check distinguishes their sides. This diagnostic
does not change the selected legacy-full-edge candidate or accept a physical
action; cross-tool admission remains forbidden.

The closed-counter carrier combines unchanged underturn/overturn gestures at
predeclared offsets [0,-0.2] and [0,0.8]. Its fixed region must be blank and disconnected
from the image border for target, nominal and all actual refinements. An open
pocket is not an enclosure. This is a diagnostic combination, not a letter recipe.

First/replay workers use hash seeds 7/839 for candidate seeds 7/19/41. Combined
per-seed limits are 5000 renders and 1800 seconds, including controls, refinements,
presentation and replay. A failed attempt is preserved; no automatic retries or
unbudgeted new output directories. At most one diagnosed cumulative revision.

## Admission boundary

The new opt-in `scribesim.handvalidate.foundation_actions.require_readiness`
requires a consumer-pinned independent manifest, explicit gesture inventory,
current identities, numeric proofs and exact replay. A whole-inventory failure
can coexist with a narrower independently supported fixed-null subset. This
never means all actions are unnecessary or that letters are ready. All required
gesture/action/reference prerequisites must precede CURRICULUM-005; real
G0/G1/G2, human appearance review, fatigue and defaults remain separate.

Existing legacy readers and every pinned foundation module remain untouched.
TDD RED commit: `6787023`; initial 14 focused tests pass. Full-frame trajectory
and local-region containment checked analytically before the first render.

## Command and samples

Run only from the frozen clean approved code checkout into its immutable continuation:

```sh
.venv/bin/python -m scribesim.handvalidate.foundation_actions \
  --output shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/action_evaluation/run-003
```

Native target/nominal/desired/actual panels, the complete workbook and all
control images are stored under `run-003/seed-{7,19,41}/first/`. Prior attempts
remain untouched. Do not rerun an immutable destination or treat this command
as authorization for another attempt.
