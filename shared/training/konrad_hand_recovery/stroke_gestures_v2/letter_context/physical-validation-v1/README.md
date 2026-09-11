# CURRICULUM-006 P2b — prepared physical validation

## Current result: independent bounded mechanical inspection passes

The owner-authorized, separately versioned [dimension-check reader](dimension-check-v1/README.md)
completes on 2026-09-10: **1464/1464 cases independently pass**, all three seed
replays match exactly, and all 324 presentations pass the pinned renderer's
exact dimensions and full decoding. The [inspection report](dimension-check-v1/inspection-001/report.json)
has SHA-256 `251d4fd3ff6a9c11ea0162b2b73108d679e22fa6ea7fd2a82756e103fdaddb5b`.
No controller execution, rendering or fitting occurs during reinspection.
All original/recovery source pins, saved artifacts and failed evidence remain
unchanged, as do frames, targets, thresholds and cumulative physical budgets.

**P2b's bounded mechanical gate is cleared.** Appearance review, preference/objective
preparation and fitting authorization remain separate; S2, real-hand and context
training flags stay false. C006 remains in progress and changes uncommitted.
The historical recovery and failed-inspection records below are retained.

P3's preserved [owner-review packet](../owner-review-v1/README.md), built from
54 saved training-pair images, is now **paused by owner decision**. The narrow
affine previews are too similar for a meaningful preference exercise. Next is
the separately planned entry/body/exit and boundary-transition investigation,
not more rankings or fitting. This does not revoke the scoped mechanical pass,
discard drafts, change bounds or reset remaining budgets.

## Historical recovery: execution passes, first independent inspection blocked

The owner approves recovery on 2026-09-09. The [separate recovery protocol](RECOVERY.md)
freezes a fresh seed-41 replay without modifying the original failed attempt or
resetting any budget. Its external contract pin is
`1b454630045689f257ac322f1334cebf614c106d748ca00301f5edfcde01b405`.
The single opt-in recovery finishes successfully: **244/244 worker checks pass**
and its replay artifacts exactly match the original seed-41 first run, excluding
execution receipts. It takes **955.023 seconds / 787 renders**, bringing the
seed-41 total, including the failed replay, to **2120.933 seconds / 1741 renders**
within the original 2700-second / 5000-render limits. Recovery report SHA-256:
`e294db3edc76d2d22f28548e8a5f54834c61e9c3d543b6102410a274ce20dc98`.

The subsequent independent reader stops with `Incomplete presentation frame`.
All **324** saved presentation images match the frozen renderer's 1169×390 size;
the reader instead expects 1170×390. The [read-only metadata audit](recovery-inspection-blocked-001.json)
records the discrepancy; it is not a completed raw-mechanical inspection.
No image, frame, threshold or frozen source is changed to bypass the gate.
At that point overall physical clearance was withheld. The subsequent approved
measurement-only correction and successful reinspection are recorded above;
no new physical run was needed. See [details and storage results](RECOVERY.md).
All changes remain uncommitted; original evidence is unchanged.

## Historical result: original attempt stopped by storage failure

The owner explicitly started the approved three-seed attempt. `run-001` stopped
with **`[Errno 28] No space left on device`** during seed 41's replay. No retry,
geometry/threshold change, fitting or deletion of evidence follows this failure.

| Seed | First pass | Replay | Recorded combined seconds | Render calls |
|---|---|---|---:|---:|
| 7 | 244/244 worker checks pass | 244/244 pass; exact artifact equality | 2117.815 | 1574 |
| 19 | 244/244 worker checks pass | 244/244 pass; exact artifact equality | 1711.584 | 1574 |
| 41 | 244/244 worker checks pass | 52/244 measured; case 53 interrupted | 1165.910 | 954 |

All **1272 completed measured cases** pass their recorded worker checks. There
are **1273 controller reservations and 4102 charged render calls**. Seed 41's
53rd replay case retains its reservation, document and a zero-byte trace file;
it has no completed measurement. The supervisor exits 120 and no root
`run-001/report.json` is written. Thus the complete independent root inspection
cannot run and **overall physical clearance remains withheld**. The recorded
successful worker checks are not a completed three-seed acceptance result.

The [failure manifest](failed-run-001-manifest.json) independently hashes all
12771 retained attempt files (1432953917 bytes), records every worker report pin,
preserves the budget ledger and confirms first/replay artifact equality for
seeds 7 and 19. Its external SHA-256 is
`adec239210591bf83b37abbe22543012e89ed5912fea2aea359be4e958fd086e`.
This is an explicitly separate forensic record, **not a fabricated root report**.
The [execution authorization](execution-approval-001.json), prepared contract,
prior reports, partial output and original code remain unchanged.

**Historical next step (now superseded by recovery above):** establish adequate disk headroom and approve a bounded no-refit recovery
plan for the unfinished seed-41 replay. Do not rerun `--run`, reset the seed's
ledger, delete frozen inputs, or reuse the truncated trace as valid evidence.
The recorded seed-41 allowance remaining is approximately **1534.09 seconds and
4046 render calls**, before any separately authorized recovery debits. No recovery
or storage cleanup has been performed. C006 remains in progress and uncommitted.

## Historical preparation

This work package implements the runner, independent raw-evidence reader,
negative controls and combined budget accounting. **Preparation is not execution
or acceptance.** No new physical controller run, raster render, fitting attempt
or sealed-holdout access occurs while preparing this contract. Changes remain
uncommitted; CURRICULUM-006 and physical P2b remain in progress.

The [preparation receipt](preparation.json) records a fresh-process source/contract
check and live P1 readiness recheck. Prepared contract SHA-256:
`db909d00cd3d7c26cff021e2c9ff9ad19a6ebb8ca08bfd873bd41dd13d443eb5`.

The historical command used to start this attempt (do not repeat it):

```sh
.venv/bin/python -m scripts.letter_context_physical --run \
  --contract-sha256 db909d00cd3d7c26cff021e2c9ff9ad19a6ebb8ca08bfd873bd41dd13d443eb5
```

After execution, independently inspect using the resulting externally pinned
report SHA-256; do not substitute a hash from a changed report:

```sh
.venv/bin/python -m scripts.letter_context_physical_evidence \
  --inspect shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/run-001 \
  --report-sha256 "${EXPECTED_REPORT_SHA256:?Set the externally pinned report SHA256}" \
  --contract-sha256 db909d00cd3d7c26cff021e2c9ff9ad19a6ebb8ca08bfd873bd41dd13d443eb5
```

## Frozen scope

- [Owner budget approval](../bounded-geometry-v1/budget-approval-001.json): 2700 seconds and 5000 render calls per seed 7/19/41, including first/replay; zero automatic retries or revisions.
- [Cleared preflight](../bounded-geometry-v1/snapshot-003/report.json): external SHA-256 `190cc9975bfb307ebd60b293cb7e62bef49a137bbaf5fe5a217b9f9b88c02cfb`.
- [Prepared contract](prepared-001/contract.json): exact source identities, candidate, 244 ordered case/program/refinement bindings, union-frozen local windows, original criteria, controls, DPI, seed/process inventory and approval pin.
- 54 training-pair assignments, three isolated controls and four known regressions, each at base/arc/time/subdivision: **244 controller runs per process; 488 per seed; 1464 over all three first/replay pairs**.
- Actual and desired metric images plus one overlap-mask render call per case; 54 actual 900-DPI presentations and one visible-shift control per process: **787 scheduled render calls per process, 1574 per seed**, inside the unchanged 1588 planning bound and 5000 ceiling. Seven of the eight control-render slots per process remain unused, not spent or silently repurposed.

Only the existing unsealed pair/control/regression grid runs. There is no new
development/probe/holdout physical scope, training preference target, parameter
selection or fitting. Geometry, frames, measurement windows and all mechanical,
tracking, event-convergence and visible-shift thresholds are unchanged. Known
base regressions keep their original frame and exact scoped pixel comparisons.
The old analytic style FAIL remains historical diagnostic evidence, not a new
context target. S2, real-hand and context-training flags remain false.

## Execution and accounting

`scripts/letter_context_physical.py` has separate `--prepare` and explicit `--run`
modes. Preparation checks live P1 readiness, preserved preflight/source pins and
owner approval without invoking the controller or renderer. The run mode requires
the external prepared-contract pin and creates one immutable `run-001`; any prior
`run-*` prevents another attempt. Preparation cannot overwrite `prepared-001`.

The supervisor allocates only the remaining combined seed time and renders to
fresh first/replay workers (`PYTHONHASHSEED=7/839`). Workers require matching
supervisor permits. Each controller attempt is reserved on disk before calling
the unchanged fixed-action controller with the cleared derived plan. Each render
is reserved in an atomically replaced, flushed journal before invocation; failed
or interrupted renders remain charged. Parent timeouts, startup, computation,
PNG/gzip writing and replay hashing count against the same cap. Root artifact
sealing is charged to the final active seed. No retry, per-arm reset or fitting
path exists. Failed attempts, partial traces, reservations and receipts remain.

Later P2b preview/validation work must consume the remaining recorded seed
allowance rather than resetting the budget. This runner does not implement a
later fitting stage or authorize spending beyond its frozen inventory.

## Independent evidence

`scripts/letter_context_physical_evidence.py` reconstructs the expected derived
plan and raw dynamics independently of saved verdicts. It checks exact source
and occurrence ownership, explicit contact boundaries, clock continuity, desired
interpolation, trapezoidal integration/projection, fixed tool state, corner and
entry events, full finite-nib and per-letter containment, vertical levels,
derived gesture ports, declared overlap and unchanged motion/image criteria.
Internal subdivisions use the existing exact-event comparator, not arbitrary
nearest samples. Width changes are explicitly distinguished from translation;
spacing-only results cannot be labeled stroke changes.

The reader reconstructs measurements from raw traces and saved metric pixels,
rechecks negative controls, validates all journal operations and combined seed
allowances, and requires exact first/replay artifact equality. It does not execute
a controller or rerasterize during read-only inspection. Stored image hashes and
frozen producer identities bind the raster evidence; this is not a claim that
consumer inspection independently rerenders every pixel. Controller/raster
acceptance still requires the real frozen experiment and its pinned inspection.

Fifteen negative controls cover identity/bounds/unknown/per-word rule tampering,
geometry and ports, overlap ownership, frame changes, raw owner/contact/clock/tool
corruption, desired-as-actual substitution, visible image shift and spacing
misclassification. An ineffective same-image shift control must fail.

## Validation boundary

**205 tests pass in 228.38 seconds**: 38 physical-preparation tests and 167
existing regressions. [Software-validation receipt](software-validation.json)
records the exact command and evidence boundary. Plan, generated-rule, local-link
and whitespace checks pass. The installed strict PR parser still returns
`ids=[]` despite explicit Advance IDs; no provider CI or merge is claimed.

New tests start red before the modules exist. Test coverage includes immutable
preparation, exact case enumeration, budget/time exhaustion, failed-render
reservation, timeout/worker-failure preservation without retry, recorded-event
serialization, derived-plan routing, raw-evidence mutations, exact old null
audits and scoped archived pixels, stored-measurement reconstruction and repinned
ledger/permission forgeries. Controller-routing tests stop at a stub; recorded
events and pixels come from preserved H024 evidence. These are software tests,
not new physical runs or physical acceptance of any contextual variant.

Preparation is preserved as historical evidence. Do not call `--prepare` or
`--run` again, or edit frozen files to refresh their hashes. The storage-failure
recovery requirements above supersede the original next-run instruction.
