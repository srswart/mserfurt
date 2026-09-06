# TD-018 guided phase: implemented, not accepted

The three guided Advances are implemented. **No recovered Konrad hand has passed
G1, G2 or G3.** All executed guided specimens use clearly labeled unaccepted
catalog priors. The actual candidate paths refuse execution while prerequisites
are missing; no owner approval or historical ductus is invented.

## Results worth distinguishing

| Experiment | Actual outcome |
|---|---|
| `../guided_bridge_v1/synthetic/` | Exact ownership/sampling works; legacy actual nib-width delta fails the synthetic bound. |
| `../persistent_execution_v1/neutral_bridge/` | Opt-in nominal-pressure/broad-nib major-width contract meets synthetic bridge bounds. G2 still blocked by G1/synthetic scope. |
| `../persistent_execution_v1/synthetic/` | 161.179944 mm contact travel consumes 0.475218516 reservoir units, no refill. State/event tests cover explicit dips and breaks. |
| `synthetic/` | Three seeds, six configurations, full three-line proof inventory. Pressure/angle/rhythm active-safe; ink and combined active-unsafe on all seeds. Synthetic G3 fails. |
| `real_attempt/` | G3 blocked before execution because no accepted matching G2 bundle exists. |

The unsafe ink settings fade too much before a boundary-triggered refill.
Worst per-line image loss is about 0.646 for ink and 0.630–0.654 for combined,
against the frozen engineering bound 0.35. Pressure/angle/rhythm worst-case losses
are about 0.230–0.234. These are masked image-agreement measurements, not reading
accuracy. All 15 active-control rows pass same-seed replay and state audits;
neutral runs pass numeric checks for all three seeds. None replaces human review.

Inspect `synthetic/neutral-three-line.png`, `synthetic/ink-three-line.png` and
`synthetic/combined-three-line.png` for quick visual comparisons. These are derived
overview sheets from the hashed original line PNGs. `synthetic/comparison.png`
shows every seed-7 configuration; all seeds and all lines are retained individually.
`reference-sheet.png` is the unchanged benchmark sheet, not a newly accepted target.

## Contracts and replay

`freeze.json` is written before trials and binds the model, exact lines, explicit
seeds 7/19/41, all control configurations, timestep, DPI, limits and code identities.
Two fresh workers with Python hash seeds 7/839 execute all 18 sessions each.
Their deterministic compressed JSON traces preserve every actual controller
sample, ownership, consumed units, dip/pause events and motor state. Use Python
`gzip`/`json` to inspect `*.json.gz`; compression has a fixed timestamp.

`report.json` retains every per-line loss and word-gap measurement, per-control
state/image deltas, inactive/active-safe/active-unsafe classification, neutral
checks, replay and artifact hashes. `evaluate` reruns frozen sessions, verifies
that actual state paints the reviewed pixels, and rejects stale or altered
summaries. A larger pressure range or pixel delta alone cannot produce a pass.

```sh
python -m scribesim.handvalidate.bridge --output /tmp/new-bridge
python -m scribesim.handvalidate.bridge --repertoire-mode --output /tmp/new-neutral-bridge
python -m scribesim.handflow.execution --output /tmp/new-state-diagnostic
python -m scribesim.handvalidate.expressive build --output /tmp/new-expressive
python -m scribesim.handvalidate.expressive evaluate --output shared/training/konrad_hand_recovery/expressive_specimen_v1/synthetic
```

Use new directories; evidence is not overwritten. The low-level converter and
session class are explicitly unaccepted diagnostic APIs, not a way to promote a
hand. Existing DensePathGuide/TOML readers remain compatible; the exact adapter
uses a mandatory versioned JSON ownership sidecar instead of losing metadata in
the legacy single-symbol catalog. Optional legacy extraction dependencies are
loaded only when their extraction functions are invoked.

## Future real execution

First repair/admit the native corpus and obtain genuine G0/G1 acceptance. For a
real bridge, provide `--nominal-root`, `--dataset-root`, `--benchmark-root`,
`--target-review`, `--review` (G1 owner/reading evidence), `--repertoire-mode` and
`--tolerances`. The tolerance object contains `status: frozen_development`,
`nominal_freeze_sha256` and `limits` with sampled/actual image loss, actual corridor
error and width-delta bounds. Calibrate before inspecting candidate proof results.

State/expressive candidate trials require a revalidated real `--bridge-root` for
the exact neutral repertoire mode. The expressive CLI uses `--nominal-review` for
G1 and a separate `--review` for the G3 owner rubric. Its `--limits` file binds
`bridge_freeze_sha256`, `status: frozen_development` and finite image/corridor/
angle/pressure limits. Complete a copy of `review-template.json` only after real
review. A pass summary without its actual models, proofs and upstream evidence
cannot authorize execution.

**Stop decision:** keep neutral execution; disable ink/combined settings until
they are revised and re-evaluated. Do not proceed to folio promotion while real
G1–G3 are blocked. Main renderer defaults are unchanged. Broader tremor/warp and
folio Advances remain deferred; this work does not close those scopes.
