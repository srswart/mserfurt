# CURRICULUM-011: shared gesture attachment learning

> **STOPPED — not complete or accepted; do not launch another attempt yet.**
> Seed-7 fitting ran, but paired target/nominal trajectories draw false connector
> ink. The actual controller correctly lifts. Automatic per-worker `pass` flags
> and paired image ratios are quarantined by [validation-stop.json](validation-stop.json).
> The permitted revision was already used. Further diagnostic repair and
> no-refit remeasurement require approval; no merge or S1-gesture is claimed.

## Results you can inspect

- [Seed-7 actual underturn](run-002/seed-7/attachment/first/underturn-isolated-actual.png)
- [Seed-7 actual overturn](run-002/seed-7/attachment/first/overturn-isolated-actual.png)
- [Seed-7 actual compound](run-002/seed-7/attachment/first/compound-isolated-actual.png)
- [Actual lifted pair, without false connector](run-002/seed-7/attachment/first/underturn-overturn-pair-actual.png)
- [Full quarantined comparison sheet](run-002/seed-7/attachment/first/practice-sheet.png): isolated rows are usable diagnostics; in paired rows **initial, target and fitted nominal contain false connector ink**. Sampled and actual columns correctly separate the gestures.
- [Constituents, entry directions and ports](run-002/seed-7/attachment/first/ports.svg)
- [Frozen selected candidate](run-002/seed-7/attachment/first/candidate.json) and [pre-held-out selection](run-002/seed-7/attachment/first/selection.json)

Seed 7 selects shared stem/rise/return reference scales **0.85 / 1.15 / 0.85**.
All primitive curves, actions and tool settings stay fixed. This is real fitting
on isolated train/development constructions, not learned letters. Its primary
54 non-wall-clock artifacts replay exactly, but reproducibility does not make
the flawed paired measurement valid. Seeds 19/41 learning is not executed.

The visual discrepancy identifies the cause without a new render: both
`nominal()` and `target()` call the old single-contact `segment_trajectory()`
helper across multiple gesture instances. Eight no-render regression tests now
fail because each two-instance target/nominal trajectory has **one** contact run
instead of two. The painter sweeps between consecutive contact points, so this
omission creates the unwanted lines. Training/development contain one instance,
so the next step can reuse the selected candidate without refitting.

**Requested next step:** add explicit pen-up boundaries between gesture
instances in diagnostic trajectories, while preserving continuous primitive
joins within each gesture. Remeasure the frozen seed-7 candidates with unchanged
targets/splits/metrics; retain all old results; then finish untouched seeds
19/41 under the original bounded search. No test-driven parameter reselection,
threshold change or new ablation. This requires approval beyond the original
one-diagnosed-revision allowance.

Total retained usage: **3121 renders / 229.715709 worker-seconds**. This includes
the 69-render first stop, first/replay work and the interrupted seed-19 fixed
worker's final 106-render counter. `run-002/ledger.json` is retained as originally
written; `validation-stop.json` adds that final interrupted counter rather than
silently editing the old ledger. Seed-7 primary used 2358/5000 renders, so the
stop concerns invalid evidence/revision authorization, not render exhaustion.

At implementation commit `a56908a`, 18 new tests pass; local and clean expanded
suites both have 235 passes and the same 12 inherited failures. The eight
subsequent red diagnostic-lift tests remain deliberately unresolved. They are
not hidden among those pre-existing failures.

## Frozen protocol, before target pixels

`spec-v1.json`, retained unchanged by the diagnosed `spec-v2.json` revision,
specifies an actual bounded fitting experiment, not replay of the
supplied i/n/u/m/h scaffolds. Matching `curve-tangent-v1` primitive admission is
required at every process start. Every original and learned primitive cubic,
port, fixed action and tool parameter stays unchanged.

The three learned parameters are positive **stem, rise and return reference
scales**, shared across underturn, overturn and compound gesture dictionaries.
All attachment offsets are derived from exact endpoint coincidence; tangent
directions are retained. Discrete reference topology is already fixed by the
audited vocabulary, not relearned or mislabeled as a new discovery. No candidate
can change an individual occurrence, primitive handle, recipe, letter or action.
The unchanged admitted construction is the initialization: there is no deliberately
spoiled baseline. Its supplied letter scaffolds are replaced by one diagnostic
`i` carrier, not fitted letters. All eight primitive definitions are retained.

Three predeclared ablations at seeds 7/19/41:

- **fixed**: unchanged shared construction, no search.
- **placement-only**: one common scale for every constituent, geometrically a
  uniform placement transform about the original first contact.
- **attachment**: independent shared stem/rise/return proportions, with exact
  attachment translations. This is the primary experiment, not chosen by test results.

Train renders propose; the top eight plus unchanged initialization are compared
on development data. Lexical parameter order breaks ties. Selection is saved to
disk **before** held-out targets are rendered. Three isolated constructions train;
development uses translated/scaled isolated constructions. Held-out includes both
ordered underturn/overturn lifted pairings, compound/terminal, and a repeated
underturn pairing at unseen scale. These are unseen **lifted attachment pairings**,
not unseen continuous topologies or learned pair spacing. Pair placements are
predeclared fixtures, not fitted context. Multiple occurrences consume the same
gesture dictionary. Two compounds in one carrier would exceed six constituents
and are deliberately not tested; compound parameters instead propagate across
isolated and paired fixtures.

Independent `gesture_targets.py` consumes only authored endpoint/derivative
specifications and fixture placements. Hermite paths have nonzero sinusoidal
perturbations and off-grid dimensions; they cannot be exact search-grid copies.
The audited endpoint rays are shared interface constraints, not optimizer handles.
These targets describe synthetic proportion exercises, **not historical ductus**.

Every proof uses the complete predeclared `[-2,10,0,22] mm` frame at 180 DPI for
evaluation and native 900 DPI for presentation. Local loss boxes and open-return
blank pockets are derived only from independent specifications, before evaluating
any candidate. Out-of-frame footprints/regions fail rather than clipping.
These open pockets are not evidence for closed letter counters.

Required primary benefits are checked for every construction occurrence and seed:
held-out ratio `<0.75`, actual/desired loss `<=0.35`, corridor `<=0.25 mm`, endpoint
refinement difference `<=0.01 mm`, image refinement difference `<=0.03`, event-time
difference `<=0.0001 s`, zero text/contact/owner errors and blank ink fraction
`<=0.01`. Base, half-arc-step, half-time-step and **all-cubic exact subdivision**
are executed using the existing repaired controller. All eight declared negative
controls must be caught; historical global `0.1` misses remain visible rather
than being relabeled as image passes. Exact ownership and local pockets provide
the predeclared small-defect guards.

## Reproduction and budgets

Recorded reproduction command from the clean implementation checkout follows.
**Do not rerun now:** the contact encoding defect and exhausted revision
allowance must be resolved first. A rerun with this code reproduces invalid
paired diagnostics, not acceptance.

```sh
.venv/bin/python -m pytest tests/test_foundation_gestures.py -q
.venv/bin/python -m scribesim.curriculum.foundation_gestures --output /tmp/gesture-learning-replay
```

The output must not exist. A pre-render freeze binds code, admitted inputs,
targets, splits, initialization and criteria. Each seed/ablation runs in fresh
first/replay processes with different Python hash seeds. Every non-wall-clock
artifact must replay byte-for-byte. Their **combined** renders/time must remain
below 5000/1800 seconds for each seed/ablation; target setup, fitting, motion,
controls, full-resolution panels and overlays are charged. Failures are retained.
There is at most one diagnosed revision; a failed primary proof stops later seeds,
with no held-out-driven alternative candidate or hidden new search.

Successful execution completes only gesture **learning**. Frozen candidates go
to HANDVALIDATE-016 for independent S1-gesture admission. No action, alphabet,
words, historical hand, fatigue or default renderer promotion follows automatically.

## Retained stop and bounded revision

Run-001 stopped in seed-7 fixed control after 69 renders / 9.544348 seconds.
The old all-cubic refinement helper converted the diagnostic model to the legacy
schema to permit two cubic pieces per primitive. That schema also has a four-
occurrence recipe cap, so it cannot evaluate a valid six-occurrence lifted pair.
This was an evaluator adapter failure, not failed primary gesture optimization;
primary learning had not started. The three isolated proofs and partial paired
proof remain in `run-001/`, along with the selection, freeze and ledger.

The single permitted revision uses `gesture_refinements.py`: first validate and
compile the original foundation model under its unchanged six-occurrence cap,
then exactly subdivide a diagnostic copy of **compiled source curves**. Original
primitive/gesture/action hashes and occurrence owners stay attached. The same
arc sampler includes every new seam, the same `curve-tangent-v1` clock retimes
it, and the existing controller executes the whole lifted pair. No alternate
grammar, cap override, projection, sample omission or hidden finishing pass.
The independent trace reconstruction checks every contact/air owner and plan
position against that exact source subdivision. Regression tests also require
the new diagnostic binding without subdivision to match the existing runtime's
full plan, metrics, trace and groups exactly. Lower-layer code and admission are
unchanged; targets, fixtures, search, initialization and thresholds cannot change.
The old cost is carried into the new cumulative seed-7 fixed budget.
