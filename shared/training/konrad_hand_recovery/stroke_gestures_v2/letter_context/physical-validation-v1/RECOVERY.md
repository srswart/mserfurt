# Owner-authorized storage recovery

The owner approves a bounded recovery with disk monitoring, unchanged frozen
candidates, geometry, targets, measurement frames, thresholds and total budgets.
This is not fitting, a budget reset, or permission for automatic retries.

## Current follow-up: independent inspection passes

On 2026-09-10 the owner-authorized [dimension-check-v1 reader](dimension-check-v1/README.md)
passes all 1464 independent case checks, 324 presentations and exact first/replay
comparisons for all three seeds. Inspection report SHA-256:
`251d4fd3ff6a9c11ea0162b2b73108d679e22fa6ea7fd2a82756e103fdaddb5b`.
The bounded mechanical evidence gate is cleared with zero new controller/raster
calls or fitting. Physical budgets and all frozen evidence remain unchanged.
Appearance approval and fitting permission remain separate and pending.

## Historical result: physical recovery passes; first reader inspection fails

The single recovery finishes with 244/244 recorded worker checks passing,
all 15 controls passing and exact saved-artifact equality against seed 41's
original first run (excluding execution receipts). The original failed attempt,
its 12771 files, and both frozen source contracts are reverified unchanged.
Recovery report SHA-256:
`e294db3edc76d2d22f28548e8a5f54834c61e9c3d543b6102410a274ce20dc98`.

| Seed | Combined seconds including failure/recovery | Charged renders |
|---|---:|---:|
| 7 | 2117.8151799580082 | 1574 |
| 19 | 1711.5840171249583 | 1574 |
| 41 | 2120.9332175429445 | 1741 |

The recovery alone costs 955.0227957089664 seconds and 787 renders. Total charged
renders across all seeds are 4889, including the original incomplete replay.
Seed 41 retains 579.0667824570555 seconds and 3259 render calls; this is not
authorization to spend them. No further physical run or fitting is performed.

Saved recovery artifacts occupy 272 MiB. Supervisor-observed free space starts
at 13958983680 bytes and reaches a minimum of 6579449856 bytes (about 6.13 GiB),
remaining above the 5-GiB stop guard. Afterward the volume has about 15 GiB free.
The worker's recorded peak resident memory is 469909504 bytes (about 448 MiB).
This attempt fits available storage, but the transient free-space drop is not
attributed to a particular process. More headroom before longer runs remains
advisable; a 20–30 GiB cushion is an operational recommendation, not a measured
minimum requirement or proof the original storage-growth cause is repaired.

### Independent inspection failure

The composite read-only inspection exits 1 at the frozen reader's presentation
dimension guard, with `ValueError: Incomplete presentation frame`. There is no
successful `recovery-inspection-001.json`, no full six-dataset raw-inspection
claim and no overall physical clearance. The recovery worker pass is preserved
separately from this failed inspection.

The frozen renderer in `scribesim/handvalidate/bridge.py` creates a supersampled
canvas using `ceil(extent * (900 * 3 / 25.4))`, then resizes the entire canvas to
`size // 3`. For the unchanged 33×11 mm frame this yields **1169×390** pixels.
The frozen reader in `scripts/letter_context_physical_evidence.py` independently
uses `ceil(extent * 900 / 25.4)`, expecting **1170×390**. Resizing the full canvas
is not a crop operation, but this discrepancy must be resolved explicitly rather
than bypassing the full-frame gate or rescaling stored images.

A separate [metadata-only audit](recovery-inspection-blocked-001.json) checks all
324 presentation images across the six complete datasets: all match the frozen
renderer and all disagree with the frozen reader. It performs zero controller
or raster calls and does not substitute for raw/stored-pixel remeasurement.
Audit SHA-256:
`90d6287394d1feec8cdf40a141a5678dc602c77eba382a5d5fee070d8d947463`.

**Historical next proposed work (now completed above):** approve a separately versioned, measurement-only reader
correction that derives exact expected dimensions from the pinned renderer,
retains raw finite-ink containment and rejects truly cropped/incorrect-DPI images,
then remeasure all six existing datasets without refitting or rerendering.
Do not alter either already-frozen source contract or discard failed inspection
evidence. All targets, frames and numerical mechanical thresholds stay unchanged.

## Execution contract

- Preserve every file in `run-001`, including the failed seed-41 replay and
  zero-byte trace, against the existing externally pinned failure manifest.
- Freeze the separate recovery runner and composite reader in
  `recovery-prepared-001/contract.json` before execution. The original physical
  runner, reader, candidate and preflight contract remain byte-identical.
- Execute one fresh **full seed-41 replay** in `recovery-001/replay`, using the
  original 244-case order, NumPy seed 41 and `PYTHONHASHSEED=839`. Repeating the
  52 previously completed replay cases avoids claiming an unproven RNG-state
  resume; no seed-7/19 or seed-41 first-pass physical execution is repeated.
- Carry forward all seed-41 costs, including the failed replay:
  1165.910421833978 seconds and 954 render calls. The recovery, supervision,
  comparisons and artifact sealing have at most 1534.089578166022 seconds and
  4046 further render calls. The exact fresh replay schedules 787 renders.
- Use the existing frozen controller, renderers, measurement functions and
  controls. Collect unreachable Python objects between cases, not inside
  simulation or measurement calculations. Exact saved-artifact comparison
  against the original seed-41 first run remains mandatory.
- Require at least 10 GiB free to start and stop below 5 GiB, checked before
  controller/render calls and every second by the supervising process. The
  supervisor kills the child on storage/time exhaustion and preserves output.
  One-second polling is a safety margin, not a guarantee against external
  processes exhausting the volume between checks.
- Record per-case progress, free bytes and peak resident memory; preserve the
  charged render journal on every failure. An existing recovery directory
  prohibits another attempt. No automatic retries or deletion of evidence.

## Storage assessment

At preparation the volume has about 13 GiB available. The original seed-41
first-pass directory occupies 272 MiB; the complete failed three-seed attempt
occupies about 1.4 GiB and the entire repository about 6.5 GiB. A fresh replay's
saved evidence should therefore require roughly 0.3 GB, not tens of GB.

System swap occupies roughly 23 GiB, but there is no per-process historical
measurement proving how much the failed physical run caused. Thirteen GiB is
enough for expected saved evidence with the above guards; more free space is
preferable while the transient-growth cause remains unresolved. The guards and
memory collection do not constitute a demonstrated fix for that cause.

## Independent inspection and evidence boundary

The separate composite reader verifies the original failure manifest and all
source pins, original first/replay permits and render journals, carried-forward
recovery debits, complete inventories, exact first/replay artifact equality,
and raw/stored-pixel measurements for all six complete worker datasets (1464
cases). Only seed 41's replay is sourced from the recovery directory. The
original partial replay is retained and charged, never relabeled as complete.

As with the original independent reader, this subsequent read-only inspection
performs no physical controller calls or raster renders and reports separately
from the physical execution budget. It does not fabricate a missing original
root report. A separately pinned recovery report identifies the composite result.

Physical mechanics clearance, if obtained, does not grant appearance approval,
S2, real-hand acceptance, context training or fitting. Historical numerical style
failure remains diagnostic. CURRICULUM-006 stays in progress and all changes
remain uncommitted.

## Software validation before execution

Prepared recovery contract SHA-256:
`1b454630045689f257ac322f1334cebf614c106d748ca00301f5edfcde01b405`.
Preparation verifies the original pins and records 13962702848 free bytes,
zero controller executions and zero raster renders. The owner-authorized
single recovery is then started with this external pin; completion and
independent inspection are not implied by launch.

`tests/test_letter_context_recovery.py` first fails collection because the new
module does not yet exist. After implementation, it and the original physical
tests pass: **55 tests in 34.97 seconds**. Tests cover carried-forward costs,
original evidence preservation, source/contract pins, disk guards, reservation
ordering, exact render schedules, malformed timing, subprocess failure, disk
exhaustion, time exhaustion, termination and refusal of a second attempt.
No fresh physical validation is performed by preparation.
