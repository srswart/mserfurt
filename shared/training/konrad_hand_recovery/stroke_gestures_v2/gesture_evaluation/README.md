# Independent fixed-tool gesture evaluation

**Decision: STOP / REVISE. S1-gesture is blocked, including the narrow learned
stem-terminal subset. Do not fit actions or advance to learned letters.**

The evaluator reconstructs the frozen experiment, primitive acceptance, code,
targets, all three ablations and development-selected checkpoints. It performs
no optimization. All three seeds reproduce the same results in fresh processes.

## Samples and evidence

- [Learning practice sheet](../gestures/run-002/practice-sheet.png): initial,
  synthetic target, fitted nominal, sampled desired and actual at equal scale.
  Only a shared stem-terminal construction is fitted; i/u recipes are supplied.
- [Local failure controls](run-001/local-controls.png): expected terminal,
  hidden connector, extra terminal and erased counter. These are independent
  analytic guard fixtures, not learned letters or learned-counter acceptance.
- [S1-gesture decision](run-001/S1-gesture.json), [seed 7 measurements](run-001/7-first.json),
  [frozen criteria](spec-v1.json), [bound identities](run-001/freeze.json) and
  [execution receipt](run-001/execution.json).
- [Full actual traces](run-001/7-first.json.gz) include training-resolution,
  coarse, refined arc-step, refined timestep and repartitioned executions,
  realized coordinates/contact, plan indices and exact owners. Seeds 19/41 and
  hash-seed-839 replays are retained alongside them.

## What passed, and what did not

| Check | Result, identical across seeds 7/19/41 |
|---|---|
| Held-out synthetic loss | 0.4424 initial → 0.0 composition; target is exactly representable in the frozen search grid |
| Actual desired/image loss | 0.049–0.079; frozen maximum 0.35 |
| Contact corridor | 0.2 mm; maximum 0.25 mm; air travel excluded |
| Contact, text and contributor checks | Pass; undeclared lift, painted air and extra contributor controls rejected |
| Detached per-letter geometry | Rejected; only shared placement/composition freedoms are permitted |
| Exact cubic subdivision | Image loss 0; endpoint difference below 0.000001 mm |
| Timestep refinement 0.002 → 0.001 s | Pass: endpoint differences below 0.0032 mm |
| Arc-step refinement 0.025 → 0.0125 mm | **FAIL on lifted pair: endpoint difference 0.399871 mm > 0.01 mm** |
| Full gesture vocabulary | Blocked: no learned underturn/overturn/compound-return/directional-loop coverage |
| Real source and owner review | Blocked / not performed; no sealed source pixels accessed |

The pair's image change is only 0.022739, below the frozen 0.03 image limit.
That does **not** override the endpoint failure. The second contact starts at
(1.897835, 6.698147) mm in the coarse run and (1.942074, 6.300730) mm in the refined
run. Both can satisfy a 0.2 mm point corridor while starting on opposite sides
of the desired entry. This is precisely why aggregate image/corridor checks
alone cannot certify stroke combinations.

Read-only diagnosis points to lift/re-entry integration: the controller advances
to discrete desired samples and projects contact position onto the corridor.
Changing the guide partition changes the state arriving from air travel. This
is a diagnosis to test in a separately scoped repair, not proof of a corrected
controller. No controller or threshold was changed to obtain acceptance.

The original NIBCONTACT-001 global negative-control failures remain unchanged:
hidden connector 0.010179 and overbuilt terminal 0.096616, both below 0.1.
Predeclared local blank-region fractions are 0.058459 and 0.094282, respectively,
above the 0.01 local limit; clean controls score 0.0. Erased-counter ink fraction
is 1.0. Exact realized contact/contributor checks supplement these local guards.
This does not validate counter preservation in an unlearned alphabet.

## Budget and reproducibility

73 renders per seed attempt, two processes per seed, plus six control/presentation
renders charged to seed 7: **444 renders total**, 21.39 seconds, zero optimization
and zero revisions. Each seed remains below 5000 renders / 1800 seconds including
replay and presentation. Thresholds were frozen before evaluation; failures stay.

    .venv/bin/python -m scribesim.handvalidate.gestures build --output /tmp/td018-gesture-evaluation

Use a new empty directory. Semantic JSON, trace gzip and PNG artifacts replay
byte-for-byte; only `execution.json` wall times vary. Training run-002 is pinned;
changed code, models, targets, primitive acceptance or source-coverage identities
require newly authorized evidence rather than reusing this report as a gate.

## Required next work

1. [Scope the missing primitive vocabulary](../gestures/primitive-extension-request.md)
   and revalidate the fixed-tool primitive layer before expanding gesture fits.
2. Scope a lift/re-entry stability repair, beginning with the saved pair failure
   as a red test. Preserve legacy behavior explicitly; do not silently alter old
   renderer/controller acceptance identities. Recheck contact endpoints, local
   attachment/counters, sampling and timestep convergence without relaxed bounds.
3. Only after repaired, scope-matching fixed-tool evidence passes should action
   fitting and later learned letter construction be considered. No fatigue,
   depletion, random rhythm or historical appearance promotion is authorized.
