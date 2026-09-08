# CURRICULUM-013 — Finer shared scales

**COMPLETE — scale-only learning and physical evaluation pass.** All three seeds
select stem/rise/return scales **0.83 / 1.17 / 0.87** from the predeclared uniform
343-proposal grid. All first/replay measurements pass at the unchanged absolute
**0.05** limit. **No return handles were repaired:** the remaining shape residual
does not require that additional freedom for this measured scope.

## Results

| Construction | Worst occurrence-local actual/target loss, all 21 fixtures and four refinements |
|---|---:|
| Underturn | 0.0196063453 |
| Overturn | 0.0197774860 |
| Compound curve | 0.0201621951 |

Every global actual/target comparison also passes. The six fresh transfer
fixtures have maximum global actual/target loss **0.0195151289**. All motion,
full-frame containment, exact contact/source ownership, blank-pocket and tool
checks pass. The unchanged closed-counter diagnostic remains enclosed and blank
in target, nominal and all four actual refinements. All nine adversarial controls
are detected. The counter is a diagnostic carrier, not a learned letter.

Like-for-like scale-1 training comparisons, taking the worst actual refinement
in both the old and new measurements:

| Construction | Previous shared scales | Finer shared scales |
|---|---:|---:|
| Underturn | 0.0437624470 | 0.0196063453 |
| Overturn | 0.1006530975 | 0.0164038174 |
| Compound curve | 0.0970797329 | 0.0201621951 |

The [previous source measurements](../actions/run-001/seed-7/first/report.json)
use the same instance geometry and physical comparison frame as the new training
rows. These are ink-normalized image errors, not percentages of artistic quality.
The narrower error is principally a proportion/placement improvement, not new
stroke vocabulary, a new calligraphic style or a recovered historical hand.

## Samples

- [Three isolated constructions: target / selected nominal / desired / actual](run-001/seed-7/first/train-sheet.png)
- [Fresh transfer examples, including lifted pairs](run-001/seed-7/first/held_out-sheet.png)
- [Previously inspected independent fixtures, now regression evidence](run-001/seed-7/first/regression-sheet.png)
- [Development sheet](run-001/seed-7/first/development-sheet.png)
- [Seed 19 fresh examples](run-001/seed-19/first/held_out-sheet.png)
- [Seed 41 fresh examples](run-001/seed-41/first/held_out-sheet.png)
- [Closed-counter actual](run-001/seed-7/first/closed-counter-carrier-actual.png)
- [Selected candidate](run-001/seed-7/first/candidate.json) / [full selection history](run-001/seed-7/first/selection.json)
- [Complete experiment and artifact manifest](run-001/report.json) / [cumulative ledger](run-001/execution.json)

All ink panels are native 900 DPI at equal physical scale. The inherited sheet
heading “Frozen null nominal” means the newly selected candidate frozen before
transfer evaluation, not the old baseline. Click through to native images rather
than interpreting a reduced browser thumbnail as the evaluation raster.

## What changed, and what did not

Only three shared reference scales and their exactly derived attachment offsets
change. Primitive cubic controls, ports, recipes, fixed tool/action, runtime,
targets and numerical thresholds are identical to the verified admitted source.
No per-occurrence tuning, new stroke, pen rotation, partial edge or finishing pass
is introduced. All seeds produce identical candidate bytes; these are repeatable
searches, not three independently learned hands.

The bounded neighborhood uses offsets -0.03 to +0.03 in steps of 0.01 around
the prior scales, not target-derived proposals. Train ranks by worst construction,
then mean and parameters; development selects from the top eight plus the old
baseline. The selected development worst loss is **0.0181168483**. A selected
minimum could still have failed the unchanged absolute criterion.

Only six train/development targets are rendered for selection. New regression
and transfer measurements begin after candidate freezing. Historical admission
evidence is inspected only to verify source prerequisites. Nine old independent
fixtures are labeled regressions, and six predeclared new transforms/pairs test
same-target-family transfer. All 21 fixtures receive four-refinement physical
evaluation. There is no candidate selection from their post-fit outcomes.

## Reproducibility and limits

- **8484 renders total**, **2828 per seed**, including both first and replay;
  every seed stays within 5000 renders and 1800 seconds. No retry or revision.
- Each worker scores 343 train proposals and nine development proposals:
  **352 scoring evaluations**, **2112 including all seeds and replays**.
- **165 non-clock artifacts** replay byte-for-byte for each seed in separate
  processes with different `PYTHONHASHSEED` values.
- Candidate file SHA-256:
  `6ff3e478799ab1a63d970d1e99fd5d5c454c12557047e5506fec911a65baf4ba`.
- Candidate object SHA-256:
  `ec1a17fa0df7221542939daf8b35546b0fe8f2d20aceaa513189ef7aec8de0f6`.
- Execution code commit: `dff8a31`; observed red tests: `05368a2`.
- **89 focused tests pass**; **16 new tests pass in a clean committed checkout**.
  Broader checks: **329 pass, 18 inherited failures**. All 18 reproduce on the
  pre-change `4fe4cf7` baseline; none is repaired or counted as passing here.
- Plan and generated-rule checks pass. Artifact doctor retains ten inherited
  issues. The local strict PR parser still misses `ADV-SS-*` IDs in supplied
  metadata; no provider CI or human appearance review is claimed.

The runner is deliberately immutable: rerunning
`.venv/bin/python -m scribesim.curriculum.finer_scales` refuses to overwrite or
silently restart this experiment. Focused code verification is available with
`.venv/bin/python -m pytest tests/test_finer_scales.py -q`.

## Next boundary

[HANDVALIDATE-018](../../../../../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-018.md)
is registered as the **planned independent no-refit evaluation** of these exact
replacement bytes, with newly withheld fixtures and unchanged quality/physical
limits. This learning report does not grant S1-action/null admission; the old
underturn-only independent acceptance remains specific to the old candidate.
Do not transfer it automatically to the changed scales.

No shared-handle repair is justified by the completed scale-only measurements.
No letter, word, fatigue, real-hand or default-renderer promotion is granted.
