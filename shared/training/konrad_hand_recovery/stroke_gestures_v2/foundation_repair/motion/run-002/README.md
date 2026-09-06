# Motion revision 1 — stable endpoints, failed re-entry corridor

**HANDFLOW-010 remains in progress, not merged or accepted.** No later foundation
Advance or new learning experiment has run. This is the single permitted revision;
another motion attempt requires [explicit new scope](../revision-request.md).

Implementation: `c66e9f5`. Frozen criteria: [spec-v2.json](../spec-v2.json).
Experiment: 266 renders, 14.706725 seconds, zero optimizer evaluations. The
[cumulative ledger](../ledger.json) retains both attempts and separately labels
regression verification; replay is not another candidate search.

## Results

| Required measurement | Result |
|---|---|
| Saved u arc-refinement endpoint difference | 0.000927 mm, previously 0.399871 mm; passes 0.01 mm |
| Worst endpoint difference, six fixtures/all refinements | 0.002557 mm; passes 0.01 mm |
| Worst cross-sampling contact-event time difference | 0.067086 ms; passes 0.1 ms |
| Planned versus executed duration | Exact agreement for every measured event-time fixture |
| Contact/gesture-owner errors | Zero |
| Corridor projection | Zero; no pose or velocity reset |
| Fixed-tool image/convergence checks | All pass |
| Current old-six primitive baseline | Original nominal scores reproduce; all six actual checks pass, maximum lag <0.144 mm |
| Saved i u maximum actual contact lag | **0.795909 mm: FAIL** against 0.25 mm |
| Independent physical-edge fixed-profile replay | Convergence passes; repeated-contact tracking fails |
| Downstream primitive-training admission | **False** |

These numeric successes do not replace the failed corridor check. The existing
six primitive families were revalidated, not retrained. Supplied i/u scaffolds
are not learned letters, and no missing return primitive has been added yet.

## Remaining diagnosis

The saved u trace reaches the second contact at 0.613454 s with actual velocity
approximately (1.026, -16.602) mm/s: upward in the physical y-down frame. The
next desired stroke goes downward at 12 mm/s. With the unchanged 500 mm/s²
acceleration bound, reversing that velocity cannot be instantaneous. Lag peaks
at 0.795908 mm about 57 ms after entry, even though the entry itself is close to
the requested point and the final ink looks similar. A corridor-only pose
projection would hide this; it is deliberately absent.

The implementation keeps legacy playback and event-time-v1. New event-time-v2
uses a global physical clock, explicit zero-duration contact events, interpolated
desired state, an acceleration/speed-limited velocity servo with the existing
position gain and trapezoidal endpoint predictor, and trapezoidal integration.
Explicit gesture-arc-v3 preserves primitive/cubic boundaries instead of chording
across a corner. There was no gain search, ink change or geometric fitting.
Guide-aligned diagnostic samples use the most recent actual observation; acceptance
uses the full actual trajectory and exact event records, not the aligned view.

## Browse the evidence

- [Visual index with enlarged re-entry path, velocity and lag plots](../../index.html)
- [Equal-frame desired / legacy / revised / timestep-refined ink](comparison.png)
- [Six frozen nominal primitives versus actual](baseline.png)
- [Full gate and comparisons](report.json)
- [Read-only baseline evaluation](baseline.json)
- `traces.json.gz`: desired plans, actual state, contact events, velocities,
  original primitive/gesture/text owners and measured projection displacement.

## Verification and replay

Eighteen new tests pass. Expanded local and clean-checkout suites each report
84 passed and one pre-existing constructor failure in
`tests/test_handflow.py::test_desired_velocity_affects_acceleration` (missing
`nib_angle_deg`), reproduced at pre-repair `64f818f`. An additional old gesture
learning/evaluation suite has eleven stale-identity failures, also reproduced at
`64f818f`; old freezes and tests were not relaxed to make these green.

Clean-checkout verification at `ca08732` repeats 266 renders in 6.870599 seconds,
with identical fixture rows, checks, baseline measurements and baseline actual
traces. That commit adds only fail-closed completeness/identity checking and a
time-grid allocation guard after the experimental freeze. It does not create a
new motion candidate or replace these historical code identities. See
[verification summary](../verification.json).

```sh
python -m pytest tests/test_handflow_reentry.py -q
python -m scribesim.handvalidate.foundation_motion --output /tmp/foundation-motion-verification-NEW
```

Use a new directory; the runner refuses existing output. Exact old-attempt
replay requires its frozen implementation commit. A current revalidation must
bind current identities and independently recompute checks, not copy `status`.
Neither a baseline pass nor a complete JSON label alone admits later fitting.

`arrive plan check`, changed-link checks and `git diff --check` pass; artifact
doctor still reports ten pre-existing issues. The installed strict PR parser
does not recognize `ADV-SS-HANDFLOW-010`; no provider CI or successful strict
metadata gate is claimed. No implementation merge was performed.
