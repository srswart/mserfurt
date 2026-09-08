# HANDVALIDATE-020 — independent level-letter validation

**Start with the [owner appearance-review sheet](index.html).** It gives enlarged
actual/target panels, toggleable baseline/x-height guides, full-frame originals,
numbered shared strokes and a letter-by-letter checklist. Human review remains
[pending](owner-review.json); implementation completion is not owner approval.

## Frozen contract

- [Specification](spec-v1.json): exact candidate file
  `e3c6e0a41374ada0ac15085df7100a8fbbc2ee855cddc71c9c2df93a84a74ff9`
  from CURRICULUM-014; no source or recipe refitting.
- Consume current frozen source identities, literal source-report and numeric-
  adjudication hashes, complete manifest and live standalone-stem admission.
  The old mixed worker/root receipts remain untouched. They are provenance,
  not the new validator's decision function.
- Independently compute exact centerline extrema and level attachment residuals.
  Do not invoke the curriculum solver, level checker, measurement or pass logic.
  Share the physical compiler/controller and the **unchanged independent target
  definition**, not an independently sourced historical reference.
- Check isolated rotated underturn/overturn, exact n/u/m, and existing `mu` at
  a new small displacement. This last observation is a placement regression,
  not a novel word, unseen exact pair, or learned context.
- Same full frame **[-3,20,2,13] mm**, target version and limits: absolute image
  loss **0.05**, whole-letter nominal benefit ratio **below 0.75**, nominal
  baseline/x-height/attachment residual **1e-8 x-height**, actual centerline-
  extrema residual **0.05 mm**. Independent local windows use target extents
  plus 0.8 mm padding; they may overlap neighbors and are not owner masks.
- Base/finer-arc/finer-time actual execution for every fixture. Source subdivision
  additionally covers isolated rotated returns. Pre-run tests found that whole-
  letter subdivision exceeds the unchanged reference cap; it is not claimed.
  No compiler-cap exception or relaxed motion threshold is introduced.
- Seven negative controls distinguish exact primitive/action lineage, climbing
  compiled geometry, owner corruption, painted air, desired-as-actual substitution,
  and a **rendered 1 mm visible displacement** exceeding the image limit. The
  climbing control shifts only the diagnostic second-arch coordinates upward by
  0.08 x-height; it is not an admissible replacement recipe.
- Seeds 7/19/41 each run first/replay in separate processes with different Python
  hash seeds. Ceilings remain **5000 renders / 1800 seconds per seed including
  replay**, zero retries. No fitting, selection or optimization occurs. These
  seeds repeat the same deterministic candidate, not independently learned hands.

## Review and acceptance boundary

The review page's detail view is presentation only. Numeric measurements and
linked originals use the full frame. Native images are 900 DPI; guide overlays
are separate SVG elements, not alterations to evidence pixels. Centerline guides
do not constrain the finite nib's outer ink edge.

For each of n/u/m, the owner should state **keep or repair**, with comments on
identity, slant/proportions, turns/joins and vocabulary consistency. The analytic
target is not a style authority. If appearance is unsatisfactory, document the
specific shared stroke or assembly repair before authorizing another experiment.
Do not quietly change targets, thresholds or individual letter curves.

Even a complete numerical pass reports `appearance_review=pending`, `S2_accepted=false`,
`real_accepted=false` and `context_training_allowed=false`. This validates bounded
mechanics, not the transform envelope, an alphabet, historical legibility, whole-
letter subdivision, context or fatigue. No automatic appearance-ingestion or
production-default switch is implemented.

## Reproduce

```sh
.venv/bin/python -m pytest tests/test_handvalidate_letter_assembly.py -q
open shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/validation/index.html
```

`python -m scribesim.handvalidate.letter_assembly` creates one immutable run only;
it refuses existing `run-*` paths. Do not use it as an overwrite/rerun command.
Use the separate `scribesim.handvalidate.letter_assembly_evidence` reader with
`--report-sha256` to verify a consumer-pinned report, all artifact hashes,
compiled lineage, physical traces, saved metric pixels, convergence, negative
controls and replay budgets without rendering or refitting.

The frozen execution module's initial archive reader omits the image reattachment
needed by the convergence comparator: compressed traces intentionally exclude
pixel arrays. A regression test reproduces its `KeyError: images`. The separate
canonical reader restores those arrays **in memory from already saved 180-DPI
metric PNGs**, checks them against recorded losses, then recomputes convergence.
It does not use the 900-DPI presentation panels, change verdicts, repair a
trajectory, mutate the archive or rerender. The execution code remains frozen at
`04223d8`; do not use its original `--inspect-sha256` path for archive inspection.

## Results

**Independent bounded mechanical validation: PASS. Owner appearance review: PENDING.**
All three seeds and six first/replay workers pass every declared numeric gate.
No corrected decision or experiment retry is needed.

| Fixture | Worst local actual/target loss |
|---|---:|
| Isolated rotated underturn | 0.0255712 |
| Isolated rotated overturn | 0.0171265 |
| n | 0.0137832 |
| u | 0.0256367 |
| m | 0.0153163 |
| Placed mu regression | 0.0260771 |

Worst global actual loss is **0.0256367**; worst local nominal loss **0.0246598**.
All are below **0.05**. Worst whole-letter benefit ratio is **0.0379762**, below
**0.75**. Nominal level/attachment residual is at most **3.34e-16 x-height**;
actual extrema residual at most **0.00010830 mm**, below **0.05 mm**.

All seven negative controls are detected. The independently measured 1 mm visible
displacement has image loss **0.8919541**; it fails the same 0.05 threshold. The
climbing diagnostic produces **0.08 x-height** residual. Exact primitive/action
drift is rejected by lineage, not presented as a rendered sensitivity test.

**474 renders**, **158 per seed including replay**; maximum cumulative seed time
**267.165 seconds**. Each worker replays **74 non-clock artifacts** exactly; the
full bundle manifest contains **452 artifacts**. The frozen candidate file is
byte-identical across all six workers and to CURRICULUM-014.

[Report](run-001/report.json) / [cumulative ledger](run-001/execution.json).
Report SHA-256:
`bd3def56ffb24c9541815d3234cceddb31d21453331f2a6764f95c009026b28e`.

```sh
.venv/bin/python -m scribesim.handvalidate.letter_assembly_evidence --report-sha256 bd3def56ffb24c9541815d3234cceddb31d21453331f2a6764f95c009026b28e
```

**127 broader tests pass** (92.78 seconds), including 24 new validation/reader
tests. All 24 also pass in a clean committed `2aab160` checkout (35.90 seconds).
The review page is checked at desktop 1280px and mobile 390px: no horizontal
overflow, whole-frame/detail and guide toggles work, native 815x390 image sizes
match the overlays, and all three letters retain margin in the detail view.
These are local checks, not provider CI or human appearance approval.

The [live read-only verification receipt](verification.json) confirms all 452
artifacts and the canonical reader identity. Strict local PR metadata checking
retains the installed `ADV-SS-*` parser limitation; plan/rules/whitespace checks
pass. No provider CI is claimed. Appearance remains pending even though this
implementation/evaluation Advance is complete.
