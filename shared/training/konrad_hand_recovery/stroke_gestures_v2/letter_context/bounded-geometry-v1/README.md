# CURRICULUM-006 P2b — Bounded geometry and frame preflight

Owner approves the ±3% width grid, independent ±0.05 normalized advances and
`[-3, 30, 2, 13]` mm context frame. This implementation validates **geometry and
desired planning only**. Actual tracking, physical overlap pixels, replay and
appearance are not validated by this preflight. Fitting remains blocked and
changes remain uncommitted. The later physical gate is reported separately below.

**Current result (snapshot-003):** 860 geometry/frame checks PASS;
**244/244 desired plans PASS** on the same 430 assignments. The six rejected
mn/mm subdivision plans now pass after the approved derived-only sampler repair.
Geometry, measurement windows, grid and acceptance thresholds are unchanged.
The owner has approved the 45-minute combined per-seed budget. Physical validation
has now been attempted under the [separate physical contract](../physical-validation-v1/README.md).
After preserving the original storage failure, an authorized seed-41 recovery
and measurement-only reader correction clear the bounded mechanical gate:
[1464 independent checks and all three exact replays pass](../physical-validation-v1/dimension-check-v1/README.md).
The preflight below remains unchanged and passing; it is not itself physical
or appearance evidence. No fitting or owner preference approval is inferred.
Fresh-process read-only reinspection reconstructs the complete snapshot-003
report exactly against its external pin, with zero rejected plans.

The [corner diagnostic](corner-diagnostic.json) finds two contact samples at the
first m corner, separated by only 1.42e-14 mm. Both fall inside the existing
1e-8 mm corner tolerance, which correctly requires exactly one match. This is a
near-duplicate sample issue, not evidence that the measurement frame is too small.
The old **snapshot-002 remains unchanged: 238/244 plans PASS, six FAIL**. Its
read-only inspection and exact sampler/reader sources are preserved, not repinned.
**Current next step:** the owner has paused the [P3 affine preference exercise](../owner-review-v1/README.md)
and approved planning of a bounded stroke-context investigation into entry/body/exit
forms and explicit transitions. Existing mechanical evidence and physical debits
carry forward; no new run, wider bounds or fitting follows automatically.

## Approved corner repair

The [arithmetic diagnostic](corner-repair-diagnostic.json) identifies an ordinary
arc midpoint just 1.5099e-14 mm beyond the exact boundary, outside the frozen
sampler's 1.4211e-14 mm roundoff suppression. The derived adapter retains the
exact boundary sample and both contributors, removing only consecutive ordinary
interior samples on the adjacent source cubic within 16 coordinate ULPs
(2.8422e-14 mm here), capped at the unchanged 1e-8 mm corner gate. This is numerical
coalescing, not relaxed acceptance. Distinct nearby events, endpoints, other
owners, protected boundaries and ambiguous/missing anchors remain untouched.
Retained sample values and all compiled geometry remain exact; null planning
bypasses the repair completely. The diagnosed contact run changes from 638 to
637 samples by removing ordinary sample 319, not exact boundary sample 318.

The [pinned before/after comparison](corner-repair-comparison.json) verifies:

- All 860 geometry records and all frozen local windows are exactly unchanged.
- The grid, criteria, physical inventory, core/P1/P2a identities and prior pins are unchanged.
- All 238 previously passing timing hashes and metrics are exactly unchanged.
- All 52 null action bundles are exactly unchanged.
- All six formerly rejected cases remain present and now pass.

Nonidentity bundle hashes change because they bind the repaired source identities;
this is not a geometry or prior passing timing change. No failed artifact is deleted.

## Implemented contract

`scripts/letter_context_variants.py` defines `letter-context-bounded-geometry-v1`:

- Width choices: 0.97, 1.0, 1.03 around the canonical letter entry x.
- Advance choices: -0.05, 0, +0.05 normalized units; at 3.5 mm x-height the maximum change is 0.175 mm.
- Width and advance are independent; the final letter remains locally identity but inherits preceding advances.
- Six following-entry cells are shared across occurrences; no word keys, previous-neighbor rules or per-occurrence parameters.
- Original primitives, gestures, fixed pen action, recipes and vertical coordinates remain unchanged.
- Derived cubics, source owners, canonical hashes, rule/anchor/displacement and normalized ports are bound in sidecars.

The independent reader reconstructs the horizontal derivation and rejects altered
geometry, ports, owner metadata, frame, bounds or permission flags. After this
check, the new planner samples derived curves and recomputes action plans and
curve-tangent timing. It does not shift an old rendered image or reuse old motion
vectors. Identity short-circuits to the exact original action bundle. The frozen
connected-v1 and P2a readers remain unchanged and reject nonempty/new contracts.

## Measurement inventory

The exhaustive unsealed **geometric** inventory is:

| Role | Assignments |
|---|---:|
| Six training pairs | 54 |
| Six development triples | 342 |
| Three previously reviewed pair probes | 27 |
| Isolated n/u/m controls | 3 |
| Original-frame known regressions | 4 |
| Total | 430 |

Every assignment has canonical and exact internal-subdivision geometry proofs.
Repeated rule cells share values: mmm has nine assignments, whereas nmm has 81.
Sealed contextual holdouts are not compiled, rendered or scored.

Frame containment uses a conservative Bezier control hull plus the fixed
physical-edge-v1 nib rectangle; the nib is never stretched. Every local window
is the union over all allowed assignments/subdivisions plus 0.8 mm, frozen before
checks. Thus cropping cannot improve a metric or grant clearance. Old known
regressions retain `[-3, 20, 2, 13]` mm. The old mmm crop is a negative test;
the wider frame must contain its complete footprint and windows.

Port continuity, normalized tangents, declared finite-width overlap and nominal
baseline/x-height use existing criteria. Desired-plan safety separately checks
fixed-nib containment, speed, acceleration and discontinuities using unchanged
limits. These proofs do not establish actual ink containment or physical dynamics.

## Physical gate and budget decision

The next pair-variant mechanical gate has **244 cases per process**:
54 pair assignments × four refinements, three isolated controls × four, and
four original known regressions × four. First/replay gives **488 runs per seed**
for seeds 7, 19 and 41. Development/probe physical checks follow one frozen
selection; this initial pair gate cannot grant unseen-triple acceptance.

Planning allowance per seed, including replay:

- Actual, desired and overlap render calls: 488 × 3 = 1,464.
- Training actual presentations: 54 × 2 = 108.
- Raster negative-control allowance: 8 × 2 = 16.
- Total planning bound: **1,588 renders**, below the proposed 5,000 ceiling.

The old **30-minute** seed cap has not demonstrated enough capacity. H024's
slowest 80-run seed took 351.94 seconds. Scaling by run count estimates **35.78
minutes before reserve**. A 25% planning reserve rounded to five minutes suggests
**45 minutes per seed**, including first/replay. This is historical extrapolation,
not a new runtime benchmark, guarantee or observed timeout.

**Approved by the owner on 2026-09-09:** a 45-minute (2700-second) combined cap
for each seed 7/19/41, including first/replay, retaining 5,000 renders,
zero automatic retries/revisions and no fitting. See [budget-approval-001.json](budget-approval-001.json).
Next freeze the concrete
physical runner, independent reader and negative controls before execution.
P2b preview/validation debits carry into C006's combined budget; they do not reset
per arm or stage. `require_physical_execution` currently rejects all requests,
including repinned/forged permission flags. No physical run has started.
The frozen preflight code and snapshots still describe the original pending
budget state. They are historical evidence, not the current approval ledger;
do not edit or repin them. The new physical execution contract must bind this
separate owner approval and implement the remaining execution safeguards.

## Evidence and validation

**Repaired focused suite: 167 tests pass in 190.87 seconds** (70 bounded-variant
tests plus 97 P1/P2a/reference/event tests). Thirteen new sampler regressions fail
before implementation and pass after it, including all six real rejected cases.
Two more tests cover incoming roundoff and ambiguous boundaries; 13 pinned
comparison tests check the unchanged inventory and reject repinned mutations to
geometry, windows, grid, thresholds, timing, null bundles, case inventory,
failures, permissions and archived evidence. A temporary-directory fixture issue
in the first expanded test run is fixed; the final full focused rerun is green.

- [Current freeze](snapshot-003/freeze.json): original approval plus sampler-only repair authorization, source identities, unchanged P1/P2a pins, fixtures, bounds, criteria and physical inventory.
- [Current report](snapshot-003/report.json): 860 geometric/frame checks and all 244 desired plans pass.
- [Current fresh-process reinspection](corner-repair-inspection.json): exact full-report reconstruction against the new external pin; no controller, raster or optimizer calls.
- [Original failed report](snapshot-002/report.json) and [its prior read-only reinspection](inspection.json): six planning rejections preserved.
- [Archived failed sampler](failed-snapshot-002-letter_context_variants.py.txt) and [reader](failed-snapshot-002-letter_context_variant_evidence.py.txt): byte-exact hashes match snapshot-002's original freeze.
- [Original aborted preflight](failed-snapshot-001.json): snapshot-001's unchanged freeze and original reader source are preserved; an exact-corner planning exception interrupted report generation.
- [Technical design](../../../../../../docs/tech-direction/TD-018-addendum-c-letter-context.md).

Current report SHA-256: `190cc9975bfb307ebd60b293cb7e62bef49a137bbaf5fe5a217b9f9b88c02cfb`.
Preserved failed report SHA-256: `a58c673514efc2bd89a23e04b644caa50150a0e21b9864a1c747955f844c7671`.

```sh
.venv/bin/python -m scripts.letter_context_variant_evidence \
  --inspect shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/bounded-geometry-v1/snapshot-003 \
  --report-sha256 190cc9975bfb307ebd60b293cb7e62bef49a137bbaf5fe5a217b9f9b88c02cfb
```

Reproduce the fast pinned comparison (not a substitute for full reinspection):

```sh
.venv/bin/python - <<'PY'
from scripts import letter_context_variant_evidence as evidence
print(evidence.compare_previous(evidence.BASE/'snapshot-003',
    '190cc9975bfb307ebd60b293cb7e62bef49a137bbaf5fe5a217b9f9b88c02cfb'))
PY
```

The current reader deliberately rejects snapshot-002's old source identities.
Its historical inspection and source archives preserve that failure; do not
repin it to the repaired code.

The original new tests failed collection before implementation. Before the sampler repair, **139 focused tests
pass** in 170.37 seconds (42 new, plus the 97 existing P1/P2a/reference/event
tests):

```sh
.venv/bin/python -m pytest -q tests/test_letter_context_variants.py \
  tests/test_letter_context_contract.py tests/test_current_foundation_readiness.py \
  tests/test_upright_reference_contract.py tests/test_upright_event_replay.py
```

Tests cover all nine width/advance choices, source preservation, real nonidentity
planning, exact null behavior, shared-cell enumeration, forgery rejection,
full-nib crop/window checks, sealed-text exclusion, immutable pinned snapshots,
budget escalation rejection and a reduced real geometric preflight with physical
execution/rendering forbidden.

The first full preflight encountered `Exact unique corner port required`. The
report collector originally stopped on this exception. Its sole repair records
each rejected plan and continues the fixed inventory; it does not alter geometry,
sampling or thresholds. A new regression fails before that collector repair and
passes afterwards (42 module tests pass). Snapshot-002 measures the same grid;
it is not another fitted candidate or a repeated physical experiment. The
rejection remains recorded in that historical snapshot. Snapshot-003 separately
records the explicitly authorized sampler repair; it does not rewrite snapshot-002.

Plan, generated-rule and whitespace checks pass. The installed strict PR parser
still returns `ids=[]` despite explicit title/body/label IDs. No successful strict
PR check, provider CI, commit or merge is claimed.

No actual-output samples were produced. Controller executions, raster renders,
optimizer evaluations and new S2/real/context-training admissions are all zero.
Existing [H024 samples](../../letters/upright/validation/placement-validation-v1/index.html)
remain the approved baseline, not examples of the new variants.
