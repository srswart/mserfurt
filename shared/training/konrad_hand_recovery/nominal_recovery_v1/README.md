# Nominal recovery implementation and evaluation

**Not a recovered Konrad hand.** `real_attempt_final/report.json` records the real
dataset G0 refusal: zero admitted observations, zero fitting evaluations, no locked
test scoring. `real_attempt/` retains the earlier identical gate outcome.

`synthetic/` proves that a missing loop can be recovered in reusable programs.
The source is deliberately a broad-edge-rendered circle, not manuscript ink.
All three modes use seeds 7, 19 and 41, 5,000 word-render evaluations and a
30-minute cap per run. A 24-evaluation smoke precedes them. Full traces include
every fully scored candidate and all component losses; a partial final evaluation
still counts toward the reported budget. No render cache discounts fitting work.

| Mode | Seed 7 dev loss | Seed 19 | Seed 41 |
|---|---:|---:|---:|
| Fixed topology | 0.3962 | 0.3992 | 0.3969 |
| Structural | 0.0664 | 0.0890 | 0.0684 |
| Structural + context | 0.0846 | 0.1146 | 0.1102 |

The structural seed-7 checkpoint is selected only on development. The synthetic
case does not establish a context benefit, historical ductus or novel manuscript
word generalization. Train and development panels show every synthetic case.

```sh
python -m scribesim.evofit.recovery --output /tmp/new-synthetic-run --evaluations 5000
python -m scribesim.evofit.recovery --dataset-root reference/konrad_hand_recovery_v2 --output /tmp/new-real-attempt
```

The real entry point recomputes G0 with native dataset integrity checks and accepts
an optional `--review` target-review JSON. A summary claiming readiness is not
enough. No test sample is passed into fitting/proposal generation. Actual test
evaluation belongs to the later frozen G1 specimen, after G0 passes.

Native x-height and bounded initial nuisance alignment remain assumptions. Skeleton
paths, loops and pen order are hypotheses. The objective weights have synthetic
controls, not real-source perceptual calibration. There is no production promotion.
