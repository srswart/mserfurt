# scribehand Mac-side scripts

These scripts run on the GPU workstation (Mac M-series / CUDA box), not on the
CPU dev VM. They implement the TD-018 contracts:

| Script | Role |
|--------|------|
| `env_check.py` | Print device/versions JSON — include in every diagnostic bundle |
| `onedm_runner.py` | CommandBackend runner for a fine-tuned **One-DM** checkpoint |
| `diffusionpen_runner.py` | CommandBackend runner for a fine-tuned **DiffusionPen** checkpoint |
| `train_htr_trocr.py` | Fine-tune a TrOCR word reader on the generic corpus export |

## Runner protocol (schema 1)

Runners are invoked by `scribesim` as:

```
python <runner>.py --request request.json --response response.json
```

`request.json` carries `words: [{id, text, seed, controls, out}]`, plus
`style_dir` and `checkpoint`. The runner writes one grayscale ink-mask PNG per
word (0 = no ink, 255 = full ink) to each `out` path and a `response.json`
mapping ids to images with `baseline_frac` / `xheight_frac` estimates.

Runners execute **inside your clone of the upstream repo** (One-DM /
DiffusionPen) so their internal imports resolve; configure clone paths in
`shared/models/scribehand/backends.toml`.

> Expectation: the upstream research repos evolve, so the model-loading code
> in each runner may need adjustment against your checked-out revision on the
> first run. Both runners fail loudly with the exact import/shape error in
> stderr, which `scribesim` surfaces — include that output in the diagnostic
> bundle if you need cloud-side help debugging.

## Orchestration (local agent)

| Resource | Role |
|----------|------|
| `docs/scribehand-mac-runbook-agent.md` | Agent-oriented runbook (human review is the only stop) |
| `docs/scribehand-orchestration.yaml` | Machine-readable step manifest |
| `scripts/scribehand/orchestrate.py` | Status / next / validate / record |
| `.cursor/commands/scribehand-orchestrate.md` | Cursor slash command |

Copy `docs/scribehand-orchestration.env.example` → `diagnostics/scribehand.env`
and fill paths before running the pipeline.

## Typical order (see docs/scribehand-mac-runbook.md for the full runbook)

1. `uv sync --extra scribehand`
2. `python scripts/scribehand/env_check.py`
3. Build + export the corpus (`scribesim build-scribehand-corpus … export-scribehand-corpus …`)
4. Fine-tune One-DM / DiffusionPen in their repos (upstream training entry
   points, IAM-style data prepared from our generic export)
5. Fine-tune the HTR gate: `python scripts/scribehand/train_htr_trocr.py --data exports/…`
6. Configure `shared/models/scribehand/backends.toml`
7. `scribesim render f01r --approach neural --neural-backend onedm --neural-htr <ckpt> --neural-diag-dir diagnostics/run1`
8. `scribesim bench-neural f01r --backend onedm --htr <ckpt> --anchor-words-dir … --out-dir diagnostics/run1`
9. `scribesim diag-pack diagnostics/run1 --out diagnostics/run1.zip` → share back
