# Corner-aware timing — run 004

**Partial success; full motion gate FAIL. HANDFLOW-010 stays in progress and
unmerged.** This is the one user-authorized spec-v4 candidate, not new learning.

## Results

- Saved-u maximum contact lag: **0.370963 → 0.007516 mm**, against 0.25 mm.
- All 27 new-mode fixture/refinement/physical runs meet corridor, corner rest,
  arrival, image/endpoint, desired/actual acceleration and ownership requirements.
- Maximum actual corner speed 0.019188 mm/s; position error 0.000944 mm.
- Desired acceleration <= 250 mm/s² within floating-point tolerance; actual
  maximum 252.720752 mm/s² against 500. No pose reset, hidden lift or air ink.
- Original six-primitive baseline passes its fresh read-only checks; no refitting.
- **233/239 checks pass. Six fail:** five repeated-fixture arc convergence checks
  and physical:arc. Only event timing exceeds the bound: worst **0.437750 ms**
  versus **0.1 ms**. Endpoint and image portions pass; time-step and exact cubic
  subdivision refinements pass. The continuous single fixture shifts 0.083603 ms;
  repetition accumulates the error.

The planner uses exact compiled corner/smooth joins, not letter identities.
Corners get a zero-speed instant with contact down and no dwell. Smooth sections
have curvature-derived speed ceilings and analytic acceleration ramps. Existing
air braking remains; all source contact geometry and tool state are unchanged.
This deliberately conservative first policy is not optimized handwriting rhythm:
saved-u planned duration increases from run-003's 1.338408 to 3.571327 seconds.

The remaining clock uses sampled chord distances, so its duration shifts slightly
with guide density. [Evidence and the next bounded proposal](../arc-clock-request.md).
No relaxed tolerance, automatic revision or downstream training is authorized.

## Inspect samples

- [Six frozen primitives: nominal / actual](primitive-gallery.png)
- [Six motion fixtures: desired / legacy actual / corner-timed / refined](comparison.png)
- [Before/after corner speed and lag](../corner-timing.svg)
- [Browsable explanation](../../index.html)

The L-like fixtures are supplied stem-terminal compositions, not learned letters.
Presentation rerenders actual paths at native 900 DPI and only downsamples;
evaluation remains at its frozen 180 DPI. Similar-looking ink cannot waive timing.

## Evidence and replay

Implementation `1597ed1`; red tests `a5154e5`, `2ef8393`. No preparatory tidy needed.
[Freeze](freeze.json), [report](report.json), [baseline](baseline.json),
[actual and desired traces](traces.json.gz), [wall receipt](execution.json),
[cumulative ledger](../ledger.json). Old runs and hashes are unchanged.

303 total diagnostic/baseline/presentation renders; 49.002829 seconds; zero
optimization; zero revisions. The separate allowance is exhausted after this
one candidate, even though its numerical ceilings were not exhausted.

Expanded local regression: 100 passed, one pre-existing missing-nib-angle
constructor failure in test_handflow.py (already reproduced at pre-repair
64f818f). The 34 focused repair tests pass. Do not repair unrelated tests or
rewrite historical code identities to obtain a green report.

Clean-checkout hash-seed-839 replay at 1597ed1 reproduces report rows/checks/
decision, freeze, baseline, all traces and PNGs byte-for-byte. Its separate
verification allowance uses 303 renders in 29.342524 seconds, with no changed
candidate. Clean regression also has 100 passes and the same pre-existing failure.
[Verification receipt](../corner-verification.json). Plan check passes; artifact
doctor retains ten pre-existing issues and agent rules are not stale. Strict PR
check ran but the installed parser recognizes no ADV-SS-HANDFLOW-010 ID. No
provider CI, successful strict PR gate or human appearance approval is claimed.

Replay from implementation commit 1597ed1 in a clean checkout, with the project
environment's Python and a new output path:

```sh
PYTHONHASHSEED=839 /absolute/path/to/.venv/bin/python -m scribesim.handvalidate.foundation_motion --output /tmp/corner-replay-new
```

Compare report rows/checks/decision, all traces, baseline records and PNG bytes,
not wall time. Later code changes must declare new identities; this freeze is
not retroactively refreshed. No real-hand or S1-action acceptance is claimed.
