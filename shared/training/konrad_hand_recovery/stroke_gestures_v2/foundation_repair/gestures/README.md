# CURRICULUM-011: shared gesture attachment learning

**COMPLETE — learning pass, not independent S1-gesture acceptance.**
The approved diagnostic lift repair and continuation finish all three seeds.
Seed 7 is remeasured **without refitting**; seeds 19 and 41 finish the unchanged
bounded search. All select shared stem/rise/return scales **0.85 / 1.15 / 0.85**.
Every primitive curve, fixed action and tool parameter remains unchanged.

## Current results and samples

- [Corrected seed-7 comparison sheet](run-003/seed-7/attachment/first/practice-sheet.png)
- [Seed-19 comparison sheet](run-003/seed-19/attachment/first/practice-sheet.png)
- [Seed-41 comparison sheet](run-003/seed-41/attachment/first/practice-sheet.png)
- [Shared constituents, entry directions and ports](run-003/seed-7/attachment/first/ports.svg)
- [Actual lifted pair](run-003/seed-7/attachment/first/underturn-overturn-pair-actual.png)
- [Frozen selected candidate](run-003/seed-7/attachment/first/candidate.json)
- [Complete learning report and artifact manifest](run-003/report.json)
- [Continuation verification](continuation-verification.json)

The native 900-DPI sheets now preserve lifted separation in **all five columns**:
unchanged initial, independent target, fitted nominal, sampled desired and actual
controller output. Continuous primitive joins within each gesture are unchanged.
The repair adds pen-up boundaries between gesture owners; it changes no existing
contact point or curve.

| Held-out lifted pairing | Learned / initial loss, every seed |
|---|---:|
| Underturn → overturn | 0.157574 |
| Overturn → underturn | 0.157807 |
| Compound → terminal | 0.132465 |
| Repeated underturn, unseen scale | 0.066255 |

All required occurrence-local ratios also pass (largest **0.408835**, limit
<0.75). All base, half-step, half-dt and all-cubic-subdivision motion proofs pass:
maximum actual/desired loss **0.010016**, contact corridor **0.007936 mm** and
refinement endpoint difference **0.005718 mm**. Exact text/contact/owner checks
and every open-return blank pocket pass. All eight adversarial controls are
detected; small defects that miss the old global 0.1 threshold remain explicitly
reported as global misses and are caught by the frozen ownership/local guards.

The **fixed** ablation correctly has no learning benefit. **Placement-only**
does not satisfy all occurrence-local/pocket gates, even when a whole-image
average looks better. Primary attachment learning was preselected by protocol,
not chosen after inspecting these held-out control results.

## No-refit and replay evidence

The [explicit approval](continuation-v1.json) pins the historical stop, frozen
seed-7 candidates and selections, unchanged functions and original protocol.
All six seed-7 candidate/selection files are byte-identical to run-002.
The seed-7 worker does **zero selection or training scoring** and charges only
117 evaluation/presentation renders per ablation/pass. Its 42 sampled/actual PNGs,
21 trace archives and 27 isolated diagnostic PNGs also remain byte-identical.
Only paired diagnostic ink separation and its measured comparisons change.

Every ablation at every seed replays **54 non-wall-clock artifacts** identically
in separate processes. All three primary candidate files have SHA-256
`d8b26fba2655b0bba961865fb74b543829cb1b11ac850afd672dd02ba0822e5a`.
The report SHA-256 is
`7dbec24cd0bf82e9f45d55c5417cf2c36551ee7dfe6294bd7b0c409219066911`.

Run-003 uses **6594 new renders**; the retained failures/interruption add 3121,
for **9715 cumulative renders across nine seed/ablation budgets**. Every individual
budget remains below 5000 renders / 1800 seconds, including replay and old costs.
The largest render use is seed-7 attachment at **2592**. Failed attempts and the
interrupted worker's final counter remain immutable.

Implementation commit `ba2c16c`: **32 focused tests pass**, including all eight
previously red lift reproductions and no-refit/source-integrity checks. Local and
clean-checkout expanded suites both have **249 passes and the same 12 inherited
failures**, with no new failures. Provider CI and human review are not claimed.

## Next acceptance boundary

**HANDVALIDATE-016** must independently reconstruct and evaluate these frozen
candidates before S1-gesture or any next-stage eligibility. This demonstrates
shared proportions and previously unseen **lifted pairings**, not learned pair
spacing, new continuous topologies, an alphabet, words, dynamic actions,
historical handwriting, fatigue or default-renderer promotion.

## Retained failures

[Run-001](run-001/report.json) stopped at the legacy four-occurrence subdivision
adapter. One diagnosed revision introduced cap-preserving compiled-source
subdivision. [Run-002's stop decision](validation-stop.json) then quarantined
false connectors in paired diagnostic trajectories; actual execution had
correct lifts. Its [old comparison sheet](run-002/seed-7/attachment/first/practice-sheet.png)
and automatic worker flags are retained as **invalid paired image evidence**.
The user explicitly approved the additional diagnostic repair/no-refit measurement
and untouched-seed continuation; run-003 supplies the corrected evidence.

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

Recorded command from the clean implementation checkout follows. The approved
worker automatically reuses seed 7 and trains only seeds 19/41. Use a new output
directory for deliberate reproduction; this command is not an authorization for
additional tuning or a new unbudgeted experiment.

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
