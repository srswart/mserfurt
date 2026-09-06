# Stroke phase: learned primitives, not yet recovered handwriting

## Start with these examples

- [Stroke practice sheet](strokes/synthetic/practice-sheet.png): starting shape,
  synthetic target, learned nominal stroke and the actual neutral pen trajectory.
  Look especially at the curved starting stem/rise/turn becoming the target shapes.
- [Shared-stroke decomposition](language/decomposition.png): blue stems and orange
  exits are shared references, not copied independent letter curves. The `i` and
  `u` recipes are supplied demonstrations, **not learned letters**.
- [Before learning](strokes/synthetic/transfer-initial.png),
  [synthetic target](strokes/synthetic/transfer-target.png), and
  [after learning](strokes/synthetic/transfer-learned.png): the same frozen `i/u`
  recipes automatically receive learned stem/exit geometry. All use 240 DPI;
  tight bounding frames can differ. No letter or context training occurs here.

The practice sheet uses one common physical frame and isotropic display scaling.
The images are native renderer output, not AI-generated illustrations or pasted
manuscript pixels. Target strokes are deliberately handcrafted synthetic shapes.
This establishes that shared geometry can learn and transfer; it does not establish
historical stroke order, pressure, speed, reading accuracy or Konrad's appearance.

## Results

| Seed | Fitting renders | Held-out loss before | After |
|---|---:|---:|---:|
| 7 | 586 | 0.4910 | 0.0815 |
| 19 | 586 | 0.4910 | 0.0857 |
| 41 | 584 | 0.4910 | 0.0650 |

Six families were fitted: stem, rise, bowl, turn, loop and exit. The loss is
normalized ink-image disagreement on synthetic exercises, not a handwriting
quality/readability percentage. Training uses isolated strokes at two scales;
development selects checkpoints at another scale. Held-out scale/position and
two-stroke compositions are scored only after fitting, without influencing it.
Seed 41 is selected by development loss, not by its test result. Each seed stays
under the frozen 5000-render/1800-second cap; two fresh processes replay every
seed with different Python hash seeds and identical results.

The learned parameters are the interior control points of **shared primitives**.
Endpoints, declared tangent half-planes, recipe references, nib, pressure and
nominal speed stay fixed. Geometry/port constraints are engineering bounds, not
a calibrated historical curvature law. Real letter construction is the next
curriculum, not something inferred from this synthetic checkpoint.

The selected model's six actual neutral stroke runs have image disagreement
0.0203–0.0554 (bound 0.35), maximum corridor error approximately 0.2 mm (bound
0.25 mm), exact coverage and preserved contact schedules. `S0` and synthetic
`S1` pass. **Real G0 remains blocked and no hand is promoted.** Ink depletion,
fatigue, expressive rhythm, tremor and warp remain disabled.

## Reference repair result

[`reference/konrad_hand_recovery_v3`](../../../../reference/konrad_hand_recovery_v3/README.md)
preserves v2 and the eight sealed test reservations. Among 52 non-test candidates,
no-target-ink exclusions fall 32 → 10 and excessive unknown ink 44 → 36. But zero
observations are admitted: exact mappings/readings, source calibration and genuine
target review remain unresolved. The real stroke attempt stops before fitting
and records zero evaluations in `strokes/real_attempt/report.json`.

Pending reviews are not manufactured approvals. Synthetic progress must not
bypass that source gate. Another extraction/source-acquisition revision needs
a separately diagnosed budget, rather than repeatedly tuning admission thresholds.

## Reproduce and inspect

```sh
.venv/bin/python -m scribesim.evofit.stroke_language --output /tmp/new-language
.venv/bin/python -m scribesim.curriculum.stroke_learning build --output /tmp/new-strokes
.venv/bin/python -m scribesim.curriculum.stroke_learning evaluate \
  --output shared/training/konrad_hand_recovery/stroke_language_v1/strokes/synthetic
.venv/bin/python -m scribesim.curriculum.stroke_learning build \
  --dataset-root reference/konrad_hand_recovery_v3 --output /tmp/new-real-strokes
```

Use new output directories. `freeze.json` binds targets, exercise/split identities,
initialization, limits, code and environment before trials. Each seed record retains
the actual parameter-update ledger and per-exercise before/after scores. The
evaluator refits frozen exercises, checks selected model identity, replays actual
trajectories/ownership and transfer pixels, and rejects incomplete evidence.

`actual-traces.json.gz` contains every actual stroke sample and primitive/recipe
ownership; compression has fixed timestamps. Inspect it with Python `gzip`/`json`.
`candidate.json` retains the full shared model, not just generated letter images.

Implementation validation: 122 focused/regression tests pass locally. Provider
CI and human appearance approval are not claimed. The installed strict PR checker
still fails to parse this repository's three-part Advance IDs.
