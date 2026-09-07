# Source-tangent repair and frozen-candidate reevaluation

**PASS for `curve-tangent-v1` fixed-tool synthetic primitives.** HANDFLOW-011
repairs the subdivision direction spike and independently replays all three
unchanged candidates. The next learning Advance is **CURRICULUM-011**; no gesture
fitting, learned letters, dynamic actions, fatigue or real-hand acceptance occurred here.

## What changed

The old guide describes each cubic with 256 straight chords. A newly inserted
cubic seam can change the chord direction abruptly, even though the underlying
curve is smooth. The opt-in planner now derives velocity direction from the
validated source cubic derivative. It retains every input contact position,
owner, pressure, angle and speed schedule and reuses the existing curve-derived
clock, corner rests, lifted braking policy and `event-time-v2` controller.
Air braking uses the corrected departure direction; no controller pose reset,
hidden lift, extra dwell, sample removal or acceleration clamp is introduced.

The original compiler, controller, renderer, tool and legacy planner code are
unchanged. A separately identified execution adapter drives those same components;
the existing independent evaluator adds explicit version dispatch without changing
its legacy default. Frozen learning/measurement identities still verify exactly.
Stationary derivatives/cusps, unknown owners and invalid source provenance fail closed.

## Results

| Required proof | Result, every seed |
|---|---|
| Compound subdivision desired acceleration | **126.422220 mm/s²**, formerly **402.431643**; limit 250 |
| Original-six nominal/actual baseline | Fresh pass before new-mode proofs |
| New-mode motion baseline | **51 executions / 13 groups pass**: original six, six motion fixtures, fixed physical bridge |
| Five held-out return fixtures and every local family benefit | Pass |
| Contact/ownership, corners, lifted reentry, density/time/all-cubic subdivision | Pass |
| Wrong ports/directions, detached geometry, hidden lift/air connector, extra owner, erased counter | All seven detected |
| First/replay artifacts | **40 per seed, byte-identical**, including models, metrics, traces and images |

Across the return proofs, maximum actual/desired image loss is **0.014465** and
maximum contact lag is **0.005517 mm**. The compound image-benefit ratios remain
upper **0.303233**, lower **0.327130**. This is the same learned geometry; no new
stroke fitting or target selection occurred. The pictures should look very similar
to the last work because this repairs motion direction rather than drawing new forms.

The complete motion suite's largest desired-acceleration value is
250.00000000004135 mm/s², within the **pre-existing 1e-8 numerical tolerance**.
No limit or tolerance is widened. Historical global sensitivity failures remain
failures under the original 0.1 threshold; the predeclared exact owner/contact and
local blank/counter controls remain mandatory. A guard counter is not an accepted
letter counter or a completed alphabet.

## Samples and evidence

- [Seed 7 complete practice sheet](run-002/seed-7/first/practice-sheet.png)
- [Seed 19 complete practice sheet](run-002/seed-19/first/practice-sheet.png)
- [Seed 41 complete practice sheet](run-002/seed-41/first/practice-sheet.png)
- [Original six: sampled versus actual gallery](run-002/seed-7/first/original-six-gallery.png)
- [Full-size compound actual ink](run-002/seed-7/first/compound-attachment-actual-900dpi.png)
- [Independent local guard sheet](run-002/seed-7/first/local-controls.png)
- [Current S1 decision and artifact manifest](run-002/S1-primitives.json)
- [Return metrics and controls](run-002/seed-7/first/report.json)
- [New-mode baseline metrics](run-002/seed-7/first/motion-baseline.json)
- [Motion traces](run-002/seed-7/first/motion-traces.json.gz), [return traces](run-002/seed-7/first/traces.json.gz)
- [Cumulative budget ledger](run-002/execution.json), [verification](verification.json)
- [Initial protocol](spec-v1.json), [one diagnosed revision](spec-v2.json)

Presentation uses native 900-DPI paths, unchanged full frame [-2,9,3,16] mm and
smooth downsampling only. Evaluation remains at 180 DPI. No ink is retouched.

## Immutable attempts and budgets

**Run-001 stopped before candidate evaluation** after refreshing the original
baseline. Its generic language exercise declares `allow_crossings=True`, so the
strict lossless migration correctly rejected it. No curve, controller or acceptance
gate failed there; the new baseline adapter was inappropriate for that format.

The single diagnosed revision constructs a one-occurrence diagnostic probe from
the identical frozen primitive table, then proves exact compiled curve, span,
placement, transition and tool equality against the original exercise. It neither
strips crossing declarations nor relaxes migration, and rejects mismatched geometry.
The original exercise and all prior reports remain unchanged.

| Seed | Stopped first/replay renders | Successful first/replay renders | Cumulative renders | Cumulative seconds |
|---|---:|---:|---:|---:|
| 7 | 324 | 854 | **1178** | 61.020 |
| 19 | 324 | 854 | **1178** | 55.982 |
| 41 | 324 | 854 | **1178** | 55.809 |

Each seed remains within the same **5000-render / 1800-second** allowance, including
both attempts, setup, baseline, refinements, controls, presentation and replay.
Total: **3534 renders**, of which 2562 belong to the successful attempt; zero
optimization. The one allowed diagnosed retry is used. Software tests are separately
labeled verification, not additional candidate selection or fitting.

Both attempts run from clean detached checkouts with fresh hash-seed-0/839 workers.
Run-002 uses implementation `571a70d`; every copied candidate is byte-identical to
the original `primitives/run-002` selection. The earlier HANDVALIDATE-015 failure
and this adapter stop remain immutable, not edited into passes.

## Admission and next work

All 27 new tests pass. The final clean expanded suite has 217 passes and twelve
failures; the pre-change baseline has 190 passes and exactly the same twelve
failures. Plan, artifact/identity, 207 local-link and diff checks pass, with ten
unchanged doctor issues and no stale generated rules. The installed strict PR
parser still rejects this repository's ID format; no provider CI or human
appearance approval is claimed.

Consumers must pin report SHA
`e17be78e54d91b73076f17ece07cb6c530f0088ac32bc0e2db76a32ac12ebb89`
and call `scribesim.handvalidate.tangent_evaluation.require_readiness` with their
required family inventory. The reader verifies current code/spec/source identities,
complete artifacts and replay, fresh baseline and numeric criteria. It returns
the required execution version **`curve-tangent-v1`**. The legacy S1 reader cannot
admit this report, and a consumer must not silently execute the old timing mode.

CURRICULUM-011 can now freeze this admission and learn shared underturn, overturn
and compound constructions with primitives and tool fixed, using topology-disjoint
held-out combinations. Its experiment has **not** run. Opposite bowl, lower loop,
closed-counter letter attachments, learned letters/words, dynamic actions, historical
handwriting and session effects remain separate work.

```sh
.venv/bin/python -m pytest tests/test_curve_tangents.py -q
.venv/bin/python -m scribesim.handvalidate.tangent_evaluation --output /tmp/tangent-replay-new
```

Use a new output directory. The latter command is a reproducibility check of the
same frozen protocol, not permission for another repair/search revision. Never edit
an existing run directory or reset the retained budget ledger.
