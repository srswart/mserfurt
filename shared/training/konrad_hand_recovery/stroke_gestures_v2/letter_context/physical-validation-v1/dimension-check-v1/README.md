# CURRICULUM-006 — measurement-only dimension correction

The owner explicitly authorizes correction of the measurement-only checker and
reinspection of saved files. The original physical reader and recovery reader
remain frozen and unchanged, as do all original and recovery artifacts.

## Result — independent mechanical inspection passes

Completed on 2026-09-10: **1464/1464 cases pass** independent raw/stored-pixel
remeasurement across seeds 7, 19 and 41, first and replay. All three replays match
their first runs exactly. All 324 presentations pass the exact renderer-derived
dimension and full-decode checks. Negative controls, raw finite-ink containment,
local windows, known-base regressions and unchanged numerical criteria pass.

The [inspection report](inspection-001/report.json) has SHA-256
`251d4fd3ff6a9c11ea0162b2b73108d679e22fa6ea7fd2a82756e103fdaddb5b`.
The reader rechecks all source/evidence pins before and after inspection.
Runtime guards remain active throughout: **zero controller executions, zero
raster renders and zero fitting evaluations**. The original storage failure,
partial replay and failed-inspection audit remain preserved and unchanged.

| Seed | Cases independently verified | Exact replay | Existing physical seconds / renders |
|---|---:|---|---:|
| 7 | 488 | PASS | 2117.815 / 1574 |
| 19 | 488 | PASS | 1711.584 / 1574 |
| 41 | 488 | PASS | 2120.933 / 1741 |

Physical debits are unchanged and include the original failed replay and approved
recovery. This clears the **bounded P2b mechanical evidence gate**, not appearance
approval, S2, real-hand acceptance, context training or fitting. Historical
numerical style failure stays diagnostic. Next is P3 owner-review/preference and
objective/budget preparation; no additional physical work is authorized here.
CURRICULUM-006 remains in progress and changes remain uncommitted.

Subsequent owner direction pauses the [affine preference exercise](../../owner-review-v1/README.md)
and plans a bounded entry/body/exit and contact-transition investigation instead.
This inspection's mechanical result and all frozen artifacts remain unchanged;
it is not acceptance of the new context representation or permission to fit it.

## Bounded correction

`scripts/letter_context_dimension_evidence.py` is a separately versioned reader.
Only the presentation dimension calculation changes: the expected image size
follows the pinned renderer's supersampled canvas ceiling and integer downsize,
`max(3, ceil(extent * (dpi * 3 / 25.4))) // 3` per axis. The unchanged 33×11 mm
frame at nominal 900 DPI therefore produces **1169×390**, not 1170×390.
Images are fully decoded; exact dimensions are required, not a one-pixel tolerance.

The raw-motion/finite-ink containment, metric image dimensions, masks, controls,
stored-measurement equality, first/replay equality, source pins and cumulative
budgets are unchanged. Structural regression tests compare the new worker and
composite reader against their frozen predecessors, allowing only replacement
of the presentation check and dispatch to that corrected worker.

## Execution and preservation

Preparation freezes this reader and its tests, the original/recovery contracts,
recovery report, prior failed-inspection audit and renderer source. Inspection
requires an external preparation pin and writes one separate immutable report.
An existing inspection directory prevents overwriting it. Previously failed
inspection evidence is preserved rather than relabeled as successful.

The complete inspection rereads all 1464 cases in the six complete datasets and
324 presentations. Seed 41's replay comes from `recovery-001`; its original
partial replay remains preserved and charged. Runtime guards prohibit physical
controller execution and raster rendering. No refitting, image regeneration,
new physical run, frame/target/threshold change or budget reset is permitted.

Preparation alone grants no clearance. A successful independent inspection
clears only this bounded mechanical evidence gate; appearance review remains
pending and does not grant S2, real-hand acceptance, context training or fitting.
CURRICULUM-006 remains in progress and changes remain uncommitted.

## Preparation and software validation

Prepared contract SHA-256:
`56e3ed722e086ec1415ea54c179070985c8d4841c19368a7c666db56d4f31f11`.
The new test module first fails collection before implementation. Afterward,
**75 focused tests pass in 37.67 seconds**, including 20 new dimension-reader
tests and all 55 prior physical/recovery tests. See the
[software receipt](software-validation.json). Local plan, generated-rule and
whitespace checks pass. This is local validation, not provider CI or a merge.

The owner-authorized full read-only inspection uses the external contract pin;
its completed result is separately recorded under `inspection-001/` above.
