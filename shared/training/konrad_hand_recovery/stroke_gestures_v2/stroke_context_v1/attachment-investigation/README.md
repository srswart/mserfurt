# Attachment-site investigation — existing curves only

**Result: necessary constraints established; no connector or attachment site
approved.** No new stroke geometry, previews, fitting or physical runs.

Follow-up: the [finite-nib clearance audit](../clearance-investigation/README.md)
finds clear other-stroke footprints for nm/mm, but a retained-rise overlap
dependency at um's departure. It recommends nm as the first construction study;
an open central strip is not a proof that a connector can be constructed.

The pinned [report](snapshot-001/report.json) records canonical parameter
locations, directed tangents, exact source ownership and potential retained/
replaced intervals. These are evaluations of existing curves, not new sample
strokes or a generated connector. Its SHA-256 is
`b555be20ccfc179be57b7ac701ded640741a4a9947a124ccbddef91550fe5a1e`.

Design input: `docs/tech-direction/TD-018-addendum-e-boundary-construction.md`,
SHA-256 `32df0e82832cf3f2defef651a51673af58785f0764fc1c9ab340b9df6cace0b3`.

## Scope and method

- Compile unchanged n/u/m, nm/nn/um/mm: seven already exposed strings only.
- Inspect the final stem of the left letter and first rising occurrence of the
  right m. Do not skip into a later internal rise of n to force a match.
- Use three fixed inspection heights: baseline, half and full height of the
  existing lower-return primitive's entry (0, 0.434496 and 0.868992 mm).
  This is a finite inspection grid grounded in existing geometry, **not new
  allowed bounds, optimization, ranking or a fitted choice**.
- Solve monotonic canonical cubic height equations by bisection; record the
  parameter and tangent. No cubic is replaced, split into a new program or edited.
- Evaluate 3×3 site pairs for each of nm/um/mm: 27 combinations. nn is a
  topology negative control, and isolated letters remain exact controls.
- Reverify frozen candidate/source contracts and original/recovery artifacts.
  Controller/raster entry points are blocked throughout the audit.

## 1. Both baseline attachment points are obstructed

Under the proposed **smooth, centerline-not-below-baseline** family:

- At a baseline departure with downward tangent, a smooth continuation initially
  travels below the baseline.
- At a baseline receiving point with upward tangent, a smooth incoming path must
  have come from below the baseline immediately before attachment.

Thus merely appending a connector to the completed left stem does not solve the
problem, and moving only the left attachment also does not solve it if the right
attachment remains at its original baseline start.

This is a local tangent argument, not a physical simulation or a blanket claim
that no connected writing is possible. A deliberate corner or changed baseline
policy would be a different, unapproved construction—not a silently smooth join.
The baseline constraint here concerns the centerline; finite-nib ink extent has
separate requirements and is not proved by this argument.

**15 of 27 combinations fail this necessary condition.** The other 12 have
positive-height sites at both ends and are **not ruled out by this test**. That
does not prove clearance, legibility, turn feasibility, dynamics or acceptance.

## 2. Concrete candidate sites to investigate further

The following matched-height rows are a readable subset, not selected winners.
The report also includes both mixed-height combinations per pair.

| Pair | Height above baseline | Depart: last-stem t | Receive: first-rise t | Horizontal gap | Baseline-touch path length lower bound |
|---|---:|---:|---:|---:|---:|
| nm | 0.434496 mm | 0.891970614 | 0.151800086 | 3.403910 mm | 3.513083 mm |
| nm | 0.868992 mm | 0.764806878 | 0.270541392 | 3.421766 mm | 3.837847 mm |
| um | 0.434496 mm | 0.918913626 | 0.151800086 | 3.433267 mm | 3.541535 mm |
| um | 0.868992 mm | 0.827432203 | 0.270541392 | 3.454483 mm | 3.867045 mm |
| mm | 0.434496 mm | 0.891970614 | 0.151800086 | 5.221353 mm | 5.293173 mm |
| mm | 0.868992 mm | 0.764806878 | 0.270541392 | 5.239209 mm | 5.519954 mm |

For departure parameter t, the potential replacement is [t,1], retaining [0,t].
For receiving parameter t, it is [0,t], retaining [t,1]. All refer to cubic 0
of the named canonical occurrence, not an arbitrary fraction of the image.

Departures are occurrence `0:3` for n/u and `0:5` for m; receiving is `1:0`
(the first m rise). Contact-run and gesture/action identities are recorded
separately. Current separate letters retain distinct contact runs. No existing
metadata is treated as ownership permission for new connecting ink.

These would be meaningful construction changes: the terminal 0.43–0.87 mm of
the stem and the initial rise region would need rebuilding, not just a tiny
endpoint tangent adjustment. In particular, replacing these intervals removes
the original baseline anchors. A future construction must deliberately restore
the required foot/extremum and retain the upright body's protected anchors.
No such restoration has been constructed or verified here.

## 3. The frozen gap is a substantial design constraint

The existing lower-return primitive's endpoint horizontal span is **1.378902 mm**.
The inspected gaps are approximately **2.47–2.51 reference-turn widths** for the
matched-height nm/um cases and **3.79–3.80** for mm. These are scale comparisons,
not new gap thresholds or grounds for automatically rejecting/accepting a family.

The path-length bound uses reflection about the baseline:
sqrt(horizontal_gap² + (departure_height + receiving_height)²). Any path touching
that baseline must be at least this long. It ignores tangent, curvature and
obstacle constraints, so it cannot establish a realizable connector.

The connector would span a substantial part of the inter-letter space at the
frozen advances. It is not simply an existing small underturn transplanted into
the gap. Do not hide a spacing reduction or draw a long decorative stroke merely
to produce a visible difference.

## 4. Negative control and conclusion

nn begins the receiving n with a descending stem at x-height, not a baseline
rising prefix. It is **unsupported for this particular turn-to-rise family**;
its canonical separate boundary remains valid. This is not a rejection of n in
all possible connecting styles.

**No site is fully established as feasible.** We now know where a candidate
could attach without the immediate smooth-baseline contradiction and exactly
which canonical regions would have to change. Remaining gates are real work:

1. Owner review of whether a connected boundary spanning these fixed gaps is
   wanted at all, and of the proposed stem-foot/receiving-prefix replacement.
2. Protected-region and finite-nib corridor/overlap investigation for the
   positive-height sites; no connector geometry is required to first map those
   constraints. Do not treat all 12 surviving combinations as admissible.
3. Prospectively reviewed length, excursion, curvature/corner, ownership and
   baseline-foot requirements before any new construction or nominal preview.
4. A separately versioned topology/consumer and physical protocol if a useful
   supported construction is eventually found.

Recommend keeping nm/um as the first positive-candidate study and mm as a
larger-gap control, with no spacing change. If that scope cannot support a
restrained useful construction, retain separate letters and return to the style/
layout decision rather than enlarge bounds automatically. H1–H3 remain paused.

## Verification

```sh
.venv/bin/python -m pytest -q tests/test_stroke_attachment_audit.py
.venv/bin/python -m scripts.stroke_attachment_audit inspect --report-sha256 b555be20ccfc179be57b7ac701ded640741a4a9947a124ccbddef91550fe5a1e
```

Snapshot refuses overwrite. Reinspection reruns the same analysis
and compares the exact report; it is reproducibility evidence, not a separate
physical checker. No physical/appearance acceptance, new budget, commit or merge.

Local results:98 focused/regression tests pass,48 unchanged exact-null tests
deselected. Exact pinned reinspection, ARRIVE plan, generated-rule, local-link
and whitespace checks pass. All original/recovery source and artifact checks
are preserved; local verification is not provider CI or physical acceptance.
