# CURRICULUM-006 P2a — Identity-only context and lineage

Owner-authorized contract and exact unchanged-output checks, 2026-09-09.
Changes remain uncommitted. P2a does not authorize nonidentity transforms,
new physical executions, new frames or fitting. P2b–P5 remain pending.

## What changed

`scripts/letter_context_contract.py` adds the opt-in `letter-context-null-v1`
program and separate occurrence-lineage sidecar. Its only admitted parameter
values are width scale **1.0** and advance delta **0.0**. The current-letter ×
following-entry selectors have six shared cells; empty/no matching rules and
the final letter are identity. Unknown fields, duplicate cells, per-word keys,
nonfinite/boolean parameters and nonidentity values fail closed.

Identity takes the original compiled geometry directly, without applying affine
arithmetic. Each sidecar occurrence names its canonical and execution primitive,
gesture, fixed action and recipe hashes, original owner/span/contact run, rule
and source/derived geometry. Internal subdivision retains its canonical parent
and names the exact execution primitive. The sidecar never enters physical owner
metadata or mutates the candidate.

`scripts/letter_context_evidence.py` independently reconstructs these declarations
from the canonical candidate without calling the new compiler. Only a verified
null document may reach `prepare_null_plan`, which uses the original action
planner and curve-tangent timing. Its outputs are a retimed action bundle and
timing record, **not** a controller execution or rendered image.

## Evidence boundary

The snapshot compares context-off and all six identity rules against direct
baseline compilation/planning for the original ten fixtures and four refinements.
It binds the identical plans, corner/arrival events and owner maps to the archived
seed 7/19/41 first/replay traces. It also checks archived replay trace/pixel hashes
and known-base actual pixels against the already approved reference registry.

| Check | Result |
|---|---|
| Exact compilation/action-plan/timing comparisons | 80 PASS: 10 fixtures × 4 refinements × 2 null modes |
| Archived runs with exact plan/event/owner binding | 240 PASS |
| Original actual/desired images bound by file and pixel hashes | 480 |
| Known-base approved actual pixel reference comparisons | 24 exact matches |
| Original H024 source artifacts verified through P1 | 1,808 unchanged |

The fresh-process read-only reinspection reproduces the complete pinned report:
**PASS**. P2a is complete; this does not complete the nonidentity part of P2.

This is **exact null input equivalence and archived-output binding**. It is not
a fresh physical null replay or a new rendered-output comparison. Original H024
physical evidence and the externally pinned P1 clearance are reused; archived
images are not copied or labeled as new output. Controller/render/fitting counts
are all zero. Historical numeric failures and acceptance flags stay unchanged.

All six rule cells have resolver tests. Only five are exercised by H024's fixed
placements: n followed by m has no archived fixture. Its schema test does not
create physical coverage. No new triple is compiled, rendered or scored here.

## API and scope

```python
from scripts import letter_context_contract as context

program = context.null_program(candidate)
document = context.compile_context(candidate, fixture, program, 'base')
bundle, timing = context.prepare_null_plan(document, candidate, fixture, 'base')
```

`candidate` must be the exact decoded approved candidate; `fixture` must equal
one of the ten original H024 fixture records, including its placement.
Refinements are exactly `base`, `arc`, `time`, `subdivision`. `enabled=False`
in `null_program` produces context-off. These compile/plan APIs make no readiness
or execution claim: the evidence runner separately calls the pinned P1 consumer.

The lineage reader does not trust a saved pass flag or self-supplied geometry
hash. It reconstructs every occurrence and rejects extra/missing/altered fields.
Do not pass transformed cubics to the legacy action bundle: a future nonidentity
compiled-geometry-to-plan adapter requires an approved contract and mechanical
evidence. This null version deliberately cannot consume them.

## Artifacts and verification

- [Snapshot report](snapshot-001/report.json): programs, per-mode lineage and plan hashes, per-run archived trace/pixel bindings and explicit permissions.
- [Freeze](snapshot-001/freeze.json): source identities, pinned P1 report, owner authorization and exact comparison inventory, written before scanning.
- [Read-only reinspection](inspection.json): fresh-process reconstruction against the external report pin.
- [P1 baseline evidence](../readiness-v1/README.md): unchanged dependency and baseline-only scope.
- [Technical design](../../../../../../docs/tech-direction/TD-018-addendum-c-letter-context.md#p2a-implemented-contract--identity-only).

P1 report SHA-256 remains:
`af4e70fc3c1b61c4e69ff46f0a9a3e70ecf5d737659901d0d5730edb976181aa`.

Null report SHA-256:
`7d8030f9818238a6e7d1252d4b152c844c0e423f9d2909df4400f52e428700ac`.

From the repository root:

```sh
.venv/bin/python -m scripts.letter_context_evidence \
  --inspect shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/null-contract-v1/snapshot-001 \
  --report-sha256 7d8030f9818238a6e7d1252d4b152c844c0e423f9d2909df4400f52e428700ac
```

Inspection recomputes the P1 check, null plans, lineage and archived bindings
without writing; it takes several minutes of read-only processing. `--build` requires a
new directory and never overwrites a snapshot. Changing permissions and repinning
the document cannot expand the executable contract.

## Tests and remaining work

Red: the new test module failed import before implementation. Green: **97 tests
passed** in 139.24 seconds using:

```sh
.venv/bin/python -m pytest -q tests/test_letter_context_contract.py \
  tests/test_current_foundation_readiness.py tests/test_upright_reference_contract.py \
  tests/test_upright_event_replay.py
```

The 50 new tests cover exact compilation/planning/timing, all-six-cell resolution,
final/missing-rule identity, sidecar independence, immutable candidate/fixture
scope, geometry/lineage/authority forgeries, archived plan/event/owner corruption,
snapshot pinning and an integration check against real archived pixels. The old
connected-v1 schema still rejects nonempty context rules. Frozen core and old
readiness readers are unchanged.

Plan, generated-rule and whitespace checks pass. Imports also pass in an isolated
export of HEAD code plus the three new modules, with shared evidence symlinked
from this checkout; this is an import smoke test, not a fresh physical experiment.
The installed strict PR parser still returns `ids=[]` with explicit title/body/
label IDs. No successful strict PR check, provider CI, commit or merge is claimed.

Next is **P2b**: approve the bounded nonidentity transform and frame contract,
complete the physical fixture/replay inventory and budget, then implement and
measure those variants. P3 still needs owner training preferences and a frozen
objective. No context fitting, S2/real admission, word rules, joins or fatigue
is unlocked by P2a.

No new visual samples were generated. The [existing H024 actual gallery](../../letters/upright/validation/placement-validation-v1/index.html)
remains the unchanged baseline.
