# HANDVALIDATE-018 — Independent finer-scale acceptance

**COMPLETE — all three declared constructions receive independent scoped
fixed-tool null acceptance.** Frozen seeds 7, 19 and 41 pass with exact replay.
There is no refitting, return-handle repair, target change or threshold change.

| Construction | Worst local actual/target loss | Unchanged limit | Disposition |
|---|---:|---:|---|
| Underturn | 0.0223815595 | 0.05 | Accepted scoped fixed-tool null |
| Overturn | 0.0222582860 | 0.05 | Accepted scoped fixed-tool null |
| Compound curve | 0.0221278593 | 0.05 | Accepted scoped fixed-tool null |

These maxima cover all occurrences across 30 fixtures and four actual execution
refinements. Every global comparison also passes. Nine fixtures are fresh
same-family holdouts; the 21 previously measured learning fixtures are explicitly
regressions. Three fresh plus three regression mechanical contexts, unchanged
closed-counter diagnostics and all nine adversarial controls pass.

The three seeds are deterministic repetitions of the same frozen candidate, not
three different hands. Independence means separate evaluation and new withheld
transforms/contexts, not an external handwriting source or new artistic target
family. Image losses are ink-normalized differences, not artistic-quality scores.

## Samples

- [Seed 7: nine fresh target / nominal / desired / actual comparisons](run-001/seed-7/first/held_out-sheet.png)
- [Seed 19 fresh workbook](run-001/seed-19/first/held_out-sheet.png)
- [Seed 41 fresh workbook](run-001/seed-41/first/held_out-sheet.png)
- [All 21 remeasured regression fixtures](run-001/seed-7/first/regression-sheet.png)
- [Fresh adjacent carriers](run-001/seed-7/first/fresh-adjacent-actual.png) / [fresh spaced carriers](run-001/seed-7/first/fresh-spaced-actual.png)
- [Closed diagnostic counter](run-001/seed-7/first/closed-counter-carrier-actual.png)
- [Frozen candidate](run-001/seed-7/first/candidate.json) / [all nine controls](run-001/seed-7/first/controls.json)
- [Independent report and artifact manifest](run-001/S1-actions.json) / [budget ledger](run-001/execution.json) / [verification](verification.json)

Panels are native **900 DPI**, at equal physical scale. Sheet captions show base
actual/target loss; the table above includes the worst of all four refinements.
Open the original images rather than judging pixelation in a reduced thumbnail.
The inherited “Frozen null nominal” header denotes the unchanged selected
CURRICULUM-013 candidate. Diagnostic `i`, `ii` and `i i` carriers do not constitute
learned letters or words.

## What the new admission verifies

The new opt-in `scribesim.handvalidate.finer_scales` module reconstructs:

- The pinned CURRICULUM-013 report, current source identities, all six learning
  workers, cumulative render/time receipts and exact first/replay artifacts.
- All 343 recorded training proposals, their finite per-construction losses,
  the development shortlist and the selected minimum. This is arithmetic
  verification of saved provenance, not a selector call or new scoring.
- The admitted primitive/action/recipe dictionaries and only the three selected
  reference scales **0.83 / 1.17 / 0.87**, with exactly derived endpoint-coincident
  attachment offsets. New per-occurrence freedom, curves or tool profiles fail.
- Fresh physical/target measurements at the unchanged 0.05 global/local limit,
  motion/contact/ownership and containment gates, blank pockets, the enclosed
  counter and adversarial controls. Compiled-source identities are reconstructed
  instead of accepting a summary flag.

The old candidate-specific admission APIs are deliberately unchanged and still
reject replacement bytes. Underturn is independently reevaluated, not admitted
by inheritance from its old scoped pass. The new consumer requires the exact
report hash and explicit supported inventory/tool scope.

## Reproducibility and validation

- **3036 renders**, **1012 per seed including first/replay**, zero optimization,
  zero retries. Cumulative seed times are 249.026 / 238.372 / 231.039 seconds,
  below the unchanged 1800-second and 5000-render per-seed caps.
- **227 non-clock artifacts per seed replay exactly** in separate processes;
  all **1370 manifest artifacts** verify through the live admission reader.
- **145 old learning artifacts per worker** remeasure byte-for-byte, including
  104 PNGs and 26 trace/evidence archives. Across six workers this preserves 870
  matching artifacts. No handwriting changes were introduced by evaluation.
- **116 focused tests pass**. The 27 new tests also pass in a clean committed
  checkout. Broader checks: **356 pass, 18 inherited failures**; all 18 reproduce
  on pre-task `ac5fdb3` in the affected baseline test subset.
- Initial failing tests: `09b1911`; implementation: `024b427`; additional empty-
  seed failure: `ffbe57c`; pre-render fix/execution code: `9c09768`.
- Plan and generated-rule checks pass. Artifact doctor retains ten inherited
  issues. The strict PR metadata parser still returns `ids=[]` for explicit
  `ADV-SS-*` IDs. No provider CI or human appearance review is claimed.

Independent report SHA-256:
`49e72a04df648ef1295b94e8436c34cdb385a992d7b173c0316899a05f6f837b`.
Unchanged selected candidate file SHA-256:
`6ff3e478799ab1a63d970d1e99fd5d5c454c12557047e5506fec911a65baf4ba`.

Example explicit admission, without rendering or fitting:

```python
from scribesim.handvalidate import finer_scales

admission = finer_scales.require_readiness(
    finer_scales.BASE / 'run-001',
    expected_report_sha256='49e72a04df648ef1295b94e8436c34cdb385a992d7b173c0316899a05f6f837b',
    required_gestures=['underturn', 'overturn', 'compound_curve'],
)
```

The reader was exercised with the learning fitter and selector forbidden; full
declared inventory admits, while unsupported inventory/tool/real requests fail.
The evaluation runner refuses to overwrite or silently restart `run-001`.

## Next boundary

The declared fixed-tool null prerequisite is now satisfied for these exact
candidate bytes and synthetic constructions. Next is bounded letter-recipe work
under [CURRICULUM-005](../../../../../../arrive/systems/scribesim/advances/ADV-SS-CURRICULUM-005.md),
which must explicitly verify and scope its required layers before fitting.

This is **not** an accepted alphabet, learned word spacing, universal null-action
claim, active nib manipulation, fatigue model, historical hand or default switch.
Other gesture families and unsupported seven-stroke compound/return carriers
remain coverage debt. The report and API keep letter/real approval false.
