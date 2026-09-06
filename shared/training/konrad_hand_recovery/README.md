# TD-018 evidence

`benchmark_v1/` is the first frozen benchmark bundle. It captures actual plain,
evo and v1-fitted **word raster** entrypoints on `und`, not full CLI/folio
rendering or a new fitting run. The fresh worker records identify code, model,
source, configuration, environment and replay images. Plain needs a pinned
Python hash seed for replay; that production limitation remains unfixed.

Reproduce in a new empty directory:

```sh
.venv/bin/python -m scribesim.handvalidate.specimen build --output /tmp/konrad-benchmark-replay
```

Commands in captured worker manifests record the original executable/output
paths. Use the command above for relocation. `code.json` records working-file
hashes and `working.patch` records the tracked dirty diff at capture time.

Read `target_sheet.png`, `coverage_debt.json`, `prior_experiment.json` and
`G0.json`. Source x-height estimates are provisional and appear on the sheet;
all rescaling preserves aspect ratio. Original contaminated source crops remain
visible. Target appearance and independent readings are unreviewed.

The three proof texts are frozen in `contract.json`. The contract digest is
computed using sorted JSON through `object_digest`; reviewer and dataset
records must reference it. New versions use new directories. The v1 experiment's
previously inspected held-out pixels are development evidence only.

G0 being blocked is an expected, honest result while a required dataset or
target review is missing. Completing the implementation does not promote a hand.

The second phase item produced `reference/konrad_hand_recovery_v2/`: 60 candidate
regions, zero admitted, with raw/mask/cleaned panels and explicit coverage debt.
Its `G0.json` preserves the initial combined dataset/benchmark readiness result.
The implementation rejects forged pass summaries by revalidating actual dataset
artifacts. Missing exact visible mappings, usable observations, source calibration
and target review still block the nominal-recovery milestone.

The latest [stroke-language phase](stroke_language_v1/README.md) supplies actual
shared-primitive learning, visible practice sheets, decomposition and held-out
synthetic transfer. The new v3 admission repair improves non-test masks but still
admits zero observations; its G0 remains blocked. The older guided control sheets
are not stages of learning this new vocabulary. Real learned letters and both
context layers remain later work.
