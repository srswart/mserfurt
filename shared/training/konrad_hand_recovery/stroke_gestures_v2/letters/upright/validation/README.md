# HANDVALIDATE-021: independent upright contact evaluation

This directory is **not another fit**. The owner-approved CURRICULUM-015 candidate
is read byte-for-byte. `spec-v1.json` freezes the independent analytic yardstick,
fixtures, existing gates, source identities and budget before any candidate scoring.
Each immutable worker runs actual `physical-edge-v1` motion with event-time-v2
execution and curve-tangent-v1 timing. The runner writes `run-001/freeze.json`
before rendering; an existing run prevents all automatic retries.

The new yardstick is deliberately independent: vertical lines and semicircular
turns, declared from the upright construction requirements, not candidate curves
or pixels. It is **not an owner-approved appearance target**. Image failure against
it cannot revoke the owner's nominal KEEP verdict or authorize changing the shape.
The absolute/local limit stays 0.05, relative limit 0.75, nominal level limit 1e-8
and actual landmark/port limit 0.05 mm. Old and new nominal constructions use the
same new target for the relative comparison; actual candidate losses are also
reported against that old nominal reference, not claimed as old-vs-new physics.

## Reproduce and inspect

The first attempt is preserved after a pre-score adapter failure. The owner has
authorized one continuation with the unchanged original protocol. Its explicit
authorization, prior debit and output path are in
`continuation-001/authorization.json`. Run it only before its own run exists:

```sh
.venv/bin/python -m scribesim.handvalidate.upright_continuation
```

Inspect the continuation without rendering or fitting:

```sh
.venv/bin/python -m scribesim.handvalidate.upright_continuation \
  --inspect shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/upright/validation/continuation-001/run-001 \
  --report-sha256 REPORT_SHA256
```

From the repository root, before a run exists:

```sh
.venv/bin/python -m scribesim.handvalidate.upright_letters
```

Read an existing archive using its externally recorded report hash:

```sh
.venv/bin/python -m scribesim.handvalidate.upright_evidence --report-sha256 REPORT_SHA256
```

The separate reader verifies source pins, the complete artifact inventory,
first/replay byte equality, cumulative budgets, rebuilt desired plans, actual
event continuity/integration, physical fields, contact/overlap ownership,
landmarks, saved image losses and negative controls. It does **not** rerender or
fit. Original metric pixels and masks remain hash-pinned; the reader recomputes
their numerical summaries rather than synthesizing replacement pixels.

## Scope and representation

- Ten fixtures: four isolated primitives, two turns, n/u/m reversals and a fixed
  translated `mu` placement probe. No new word/context training.
- Base, half arc step, half timestep and exact source subdivision for each.
  De Casteljau halves stay **inside** each existing primitive (two of four allowed
  cubics); no references are added and m remains six expanded references.
- Seeds 7/19/41 each run in two fresh processes with different hash seeds. This
  controller/candidate is deterministic: these are replay identities, not three
  learned candidates or evidence of population robustness.
- Each seed has 5,000 renders and 1,800 seconds **including replay**, zero retries,
  zero optimization evaluations. Occupancy-mask rasterization counts as a render.
- Per-gesture actual swept-nib masks measure repeated coverage independently of
  centerline intersections. Ownership changes are not pen lifts. Raster overlap
  counts are not exact areas or an ink-accumulation/depletion simulation.
- Raw controller air events report width zero; physical display samples use the
  unchanged 0.45-mm nib carrier with zero pressure/contact. Contact widths are
  never replaced. Fixed-angle roundoff tolerance is 1e-10 degrees, not a new
  aesthetic slant tolerance. Slant and repeated-pixel counts are report-only.
- Full-frame metrics are 180 DPI; newly rendered presentation images are 900 DPI.
  Browser detail mode enlarges a view, never changes the measurement frame.
- S2, historical/real-hand acceptance and context permission remain false.
  New actual-ink owner feedback is separate from the nominal approval and numeric
  decision. No fatigue, session effects, relaxed thresholds or candidate repairs.

Implementation and measured outcome are recorded in
`arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-021.md`.
