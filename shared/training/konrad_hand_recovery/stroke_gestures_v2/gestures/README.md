# Fixed-tool shared gesture construction learning

**Implemented: a bounded synthetic stem-terminal lesson, not the full gesture vocabulary.**
Shared primitive cubics, tool profiles and supplied i/u recipes stay frozen.
The initial program is deliberately perturbed (stem then rise); fitting chooses
a shared terminal primitive and its scale/rotation, not independent character curves.

## Samples and results

- [Current practice sheet](run-002/practice-sheet.png): initial, synthetic target,
  fitted dense nominal, sampled desired and actual neutral output at equal scale.
- [Current report](run-002/report.json), [candidate](run-002/candidate.json),
  [freeze](run-002/freeze.json) and [actual traces](run-002/actual-traces.json.gz).
- The unseen smaller single and lifted pair use the same fitted gesture. Their
  supplied i/u text probes are not learned letters or historical ductus evidence.

Three seeds and three frozen ablations give held-out image loss 0.4424 unchanged
for the fixed baseline, 0.3116 for placement-only, and 0.0 for composition plus
placement. Zero loss is possible because these synthetic targets were explicitly
constructed within the small frozen search space; it is not real handwriting recovery.
All seeds select the same development-best shared model.

Each attempt uses 396 first-run renders plus 378 verification-replay renders,
including target generation and presentation. One diagnosed revision was used:
run-001 incorrectly included pen-up travel in the contact corridor statistic.
The red-test-backed repair changes the statistic, not controller motion, target,
weights, bounds or fitting freedoms. Run-001 remains immutable and can be
replayed at commit e80e40c; run-002 is the current code-bound candidate.

The broad gesture gate remains unaccepted: the current primitives do not yet
establish the requested underturn/overturn/compound-return and directional-loop
coverage. See [the separately bounded primitive-extension request](primitive-extension-request.md).
[Real fitting stopped](real-attempt-001/report.json) with zero renders; no source
images were opened and no prior blocked G0 summary was treated as a pass.

## Replay

Use a fresh directory; existing output is refused:

    .venv/bin/python -m scribesim.curriculum.gesture_learning build --revision 1 --output /tmp/gesture-learning-replay

Semantic files replay exactly; execution.json records variable wall time.
HANDVALIDATE-013 independently checks metrics, topology, ownership and actual
execution before any downstream action-fitting readiness decision.
