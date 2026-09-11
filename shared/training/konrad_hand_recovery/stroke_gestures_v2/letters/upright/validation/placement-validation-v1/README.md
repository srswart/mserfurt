# HANDVALIDATE-024 — held-out placement physical validation

**Execution/mechanical protocol PASS. Held-out actual appearance APPROVED.**

The owner approves the six displayed actual samples: “Looks good -- what is next ?”
This closes their appearance review only. Frozen execution/inspection records
retain their at-run pending-review state. Current lower-layer readiness and a
separate bounded context protocol must be established before context training.

Open [the actual-ink gallery](index.html). Review **un, nu, um, nn, uu and mm**.
Each primary image is actual simulated physical ink, at 900 DPI in the complete
unchanged frame. Diagnostic nominal/style images are expandable, not replacement
letters. The six pairs test fixed placement and interletter air movement, not
joining, contextual stroke changes, spacing design or fatigue.

## Outcome

- All ten fixtures pass the unchanged mechanical/level/port/tracking/convergence
  requirements at base, finer arc, finer time and exact internal subdivision.
- Seeds 7, 19 and 41 each finish first + fresh-process replay with identical
  per-seed artifact manifests. These are deterministic executions, not fitted seeds.
- All four known base fixtures (n/u/m/mu) exactly match their approved pixel
  anchors in all six workers: **24 matches**, scoped identity, not new quality.
- All eleven physical/model/trace/image negative controls detect the intended
  violation in every worker. The visible-shift control compares to the same
  unshifted actual image, not an already-failing style target; its original 0.05
  detection threshold is not a new appearance or held-out regression tolerance.
- **1,086 charged render calls**, 240 actual controller executions, zero fitting,
  automatic retries or candidate changes. Pre-scoring vector/reference construction
  has no raster or controller calls. The independent reader performs neither.
- Owner appearance for all six new pairs is KEEP in
  [the report/candidate-bound review record](actual-review.json). S2, real-hand,
  context and overall admission remain withheld.

The independent analytic style comparison still fails its unchanged historical
0.05/0.75 criteria. It is diagnostic only under this prospectively approved
preservation contract. **HANDVALIDATE-021's historical numeric FAIL stays FAIL**.
Candidate-derived nominal losses are report-only; no 0.05 gate is transplanted.

| Held-out pair | Base actual vs derived nominal | Base actual vs independent style |
|---|---:|---:|
| un | 0.001291305 | 0.299118264 |
| nu | 0.000415202 | 0.300593878 |
| um | 0.001493714 | 0.444189204 |
| nn | 0.000722099 | 0.366982177 |
| uu | 0.002020348 | 0.234446838 |
| mm | 0.002092527 | 0.576997171 |

First seed-7 global diagnostics are shown above; full per-letter losses and all
refinements are saved in every worker. Maximum actual port error is 0.019878 mm
against the unchanged 0.05 mm bound. Maximum refinement endpoint difference is
0.005568 mm (limit 0.01); exact-event time difference is 5.12e-13 s (limit 1e-4).
Full finite-ink and per-letter reference/actual windows are checked before local
measurements are used. No cropped image grants acceptance.

## Budget and immutable evidence

The new [authorization](authorization.json) binds the owner's request to the
previously prepared H023 report, registry and protocol. It does not edit those
historical snapshots or borrow old run allowances. All candidate/core source
identities (206 entries) stay unchanged. New runner and independent reader are
frozen at implementation commit d718d05 before the experiment starts.

| Seed | Renders including replay | Elapsed seconds including replay |
|---|---:|---:|
| 7 | 362 | 327.683 |
| 19 | 362 | 326.274 |
| 41 | 362 | 351.945 |

Each authorized limit is 5,000 renders / 1,800 seconds, with zero retries. The
immutable [run archive](run-001/report.json) pins 1,808 artifacts, including raw
traces, owner masks, metric/presentation images, candidate and execution receipts.
The 44,145,873-byte source freeze deliberately includes all exact derived vector
references and local windows before any scoring; this large generated artifact
is evidence, not newly learned geometry. Do not rewrite or rebuild over run-001.

Report SHA256: `25b0e886ab643ff5dee969d1393b1f3f1e235e75f945e3c94025aedcfffe36b4`.

## Read-only verification

The [inspection receipt](inspection.json) belongs outside the immutable run.
The separate reader checks the consumer pin and artifact inventory, reconstructs
motion/clock/owner/overlap/landmark/event proofs from raw traces and masks,
recomputes losses from saved pixels and decisions without trusting saved pass
flags, and reconstructs negative controls with original mapped-owner aliasing.
It verifies regenerated pre-scoring vectors against the source freeze, but does
not independently rerasterize them or claim an independent rendering engine.

```sh
.venv/bin/python -m scripts.upright_placement_evidence \\
  --report-sha256 25b0e886ab643ff5dee969d1393b1f3f1e235e75f945e3c94025aedcfffe36b4
```

Implementation checks: 53 focused tests pass (33 harness/contract tests and 20
existing reconciliation/raw-reader/replay/measurement tests). The new harness and
contract tests prohibit controller/raster calls and reject missing/nonfinite measurements,
scope or approval leakage, raw-trace/metric mutations, ineffective shift controls
and automatic retries. An independent read-only check is distinct from provider
CI, owner appearance approval and new layer admission. Separately, the existing
regression suite runs one tiny synthetic `ii` controller test (not this candidate),
with two image-render calls and one owner-mask generation call. Those unit-test
operations are not part of the journaled 1,086-render physical experiment.
