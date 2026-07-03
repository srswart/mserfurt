# ScribeHand Mac Runbook — Agent Orchestration (TD-018)

Machine-oriented companion to [scribehand-mac-runbook.md](./scribehand-mac-runbook.md).
A local agent runs every step **except** human visual review (§8).

**Manifest:** [`scribehand-orchestration.yaml`](./scribehand-orchestration.yaml)  
**State file:** `diagnostics/.scribehand-orchestration-state.json` (created by the orchestrator)  
**Helper:** `python scripts/scribehand/orchestrate.py`

---

## Agent protocol

1. **Load env** — copy `docs/scribehand-orchestration.env.example` to
   `diagnostics/scribehand.env` (gitignored) and fill absolute paths.
2. **Check status** — `uv run python scripts/scribehand/orchestrate.py status --json`
3. **Get next step** — `uv run python scripts/scribehand/orchestrate.py next --json`
4. **Run commands** for that step (from manifest or this doc).
5. **Validate** — `uv run python scripts/scribehand/orchestrate.py validate <step_id> --json`
6. **Record** — `uv run python scripts/scribehand/orchestrate.py record <step_id> --status passed`
7. **Repeat** until `next` returns `step_8_human_review` with `executor: human`.
8. **STOP** at human review — deliver bundle zips + rubric to the human reviewer.
9. After human writes `human_review.md` in each diagnostic dir, resume from step 9.

### Hard stop: human review

When `next` returns step `step_8_human_review`:

- Do **not** auto-approve or skip.
- Notify the human with:
  - `${DIAG_ONEDM}.zip` and `${DIAG_DIFFUSIONPEN}.zip`
  - Side-by-side sheets in each diagnostic directory
  - The five-axis rubric (see [human runbook §8](./scribehand-mac-runbook.md#8-guided-human-evaluation-your-eyes))
- Wait until both files exist:
  - `diagnostics/onedm_f01r/human_review.md`
  - `diagnostics/diffusionpen_f01r/human_review.md`

Each `human_review.md` should contain YAML frontmatter the agent can parse:

```yaml
---
backend: onedm
reviewer: "<name>"
date: "2026-07-03"
scores:
  letterform_authenticity: 4
  instance_variation: 4
  word_rhythm: 4
  ink_behavior: 3
  text_fidelity: 5
pass: true
notes: "Optional observations for cloud-side iteration."
---
```

**Pass rule:** all scores 4–5; nothing ≤3 on letterform or instance variation.

---

## Environment variables

Set in `diagnostics/scribehand.env` (sourced by the orchestrator):

| Variable | Purpose |
|----------|---------|
| `REPO_ROOT` | This repo (default `.`) |
| `ONEDM_ROOT` | Clone of github.com/dailenson/One-DM |
| `DIFFUSIONPEN_ROOT` | Clone of github.com/koninik/DiffusionPen |
| `ANCHOR_DIR` | Reviewed anchor tier (`images/` + `labels.tsv`) |
| `ANCHOR_WORDS_DIR` | Word crop PNGs for style gate |
| `REFERENCE_PAGE` | Anchor folio page JPEG/PNG |
| `ONEDM_CKPT` | Fine-tuned One-DM checkpoint path |
| `DIFFUSIONPEN_CKPT` | Fine-tuned DiffusionPen checkpoint path |

Defaults for corpus/export/HTR paths live in the YAML manifest.

---

## Step reference (agent-executable)

Each step maps 1:1 to the human runbook. Success = exit code 0 **and** artifact checks
from `validate`.

### step_0_setup — §0 Setup

```bash
git pull
uv sync --extra scribehand
uv run python scripts/scribehand/env_check.py > diagnostics/env_check.json
```

**Validate:** `mps_available: true`, `device_smoke_ok: true` in `diagnostics/env_check.json`.

### step_0b_clone_upstream — §0 upstream clones

```bash
test -d "$ONEDM_ROOT" || git clone https://github.com/dailenson/One-DM "$ONEDM_ROOT"
test -d "$DIFFUSIONPEN_ROOT" || git clone https://github.com/koninik/DiffusionPen "$DIFFUSIONPEN_ROOT"
```

Install each repo's requirements and IAM checkpoints per upstream README (agent may run
those commands inside each clone).

### step_1_corpus_smoke / step_1_corpus_full — §1 CATMuS

```bash
uv run scribesim build-scribehand-corpus --catmus --catmus-max-lines 300
uv run scribesim build-scribehand-corpus --catmus
```

**Validate:** `shared/training/scribehand/corpus_v1/manifest.json` exists.

### step_2_anchor_tier — §2 Anchor hand

Requires `ANCHOR_DIR`. Human harvest/review happens **before** this step; agent runs ingest:

```bash
uv run scribesim build-scribehand-corpus --anchor-dir "$ANCHOR_DIR"
```

**Validate:** `shared/models/scribehand/style_anchor_v1/style.json` exists.

### step_3_corpus_gates / step_3_export — §3 Gates

```bash
uv run scribesim check-scribehand-corpus --report diagnostics/corpus_gates.json
uv run scribesim export-scribehand-corpus --out-dir shared/training/scribehand/exports/generic_v1
```

**Validate:** `corpus_gates.json` has `"ok": true`.

### step_4_finetune_* — §4 Generator fine-tune

Agent-orchestrated but **upstream-repo specific** (marked `manual: true` in manifest).
Prepare IAM-style data from the generic export; run each repo's training entry point.
Record `training_report.json` beside each checkpoint; set `ONEDM_CKPT` / `DIFFUSIONPEN_CKPT`
in env before step 6.

### step_5_htr_train / step_5_htr_calibrate — §5 HTR gate

```bash
uv run python scripts/scribehand/train_htr_trocr.py \
  --data shared/training/scribehand/exports/generic_v1 \
  --out  shared/models/scribehand/weights/htr_trocr_v1

# heldout_anchor.tsv: image_path<TAB>expected_text
uv run scribesim verify-words diagnostics/heldout_anchor.tsv \
  --htr shared/models/scribehand/weights/htr_trocr_v1 \
  --report diagnostics/htr_calibration.json
```

**Validate:** `htr_calibration.json` → `"failures": 0`.

### step_6_configure_backends — §6 backends.toml

Uncomment and fill `shared/models/scribehand/backends.toml` with absolute paths.

### step_6_word_proofs — §6 single words

```bash
uv run scribesim generate-word "und" --backend onedm --seed 7 --out diagnostics/proofs/und_onedm.png
uv run scribesim generate-word "schreiber" --backend diffusionpen --seed 7 --out diagnostics/proofs/schreiber_diffusionpen.png
```

### step_6_folio_render_* / step_7_bench_* / step_7_pack_* — §6–7 render, bench, pack

Per backend (`onedm`, then `diffusionpen`):

```bash
uv run scribesim render f01r --approach neural \
  --neural-backend onedm \
  --neural-htr shared/models/scribehand/weights/htr_trocr_v1 \
  --neural-diag-dir diagnostics/onedm_f01r

uv run scribesim bench-neural f01r \
  --backend onedm \
  --htr shared/models/scribehand/weights/htr_trocr_v1 \
  --anchor-words-dir "$ANCHOR_WORDS_DIR" \
  --reference-page "$REFERENCE_PAGE" \
  --out-dir diagnostics/onedm_f01r

uv run scribesim diag-pack diagnostics/onedm_f01r --out diagnostics/onedm_f01r.zip
```

**Validate:** `metrics.json` → `"ok": true`; zip exists.

**Calibration rule (agent checks before trusting gates):** real anchor pages must pass
`verify-words` and `bench-neural` on real crops first.

### step_8_human_review — §8 **HUMAN REQUIRED**

Agent stops. See [Hard stop](#hard-stop-human-review) above.

### step_9_promotion — §9

After human review passes, agent may:

- Run additional proof folios (pressure, fatigue, final-stock)
- Write `diagnostics/promotion_decision.json` with `"approved": true`
- Update ADV-SS-HANDVALIDATE-007

---

## Orchestrator commands

```bash
# Show pipeline state
uv run python scripts/scribehand/orchestrate.py status [--json]

# Next actionable step (respects depends_on + human gate)
uv run python scripts/scribehand/orchestrate.py next [--json]

# Check artifacts / JSON gates for a step
uv run python scripts/scribehand/orchestrate.py validate step_3_corpus_gates [--json]

# Mark step outcome (after validate passes)
uv run python scripts/scribehand/orchestrate.py record step_3_corpus_gates --status passed

# Print unresolved env vars
uv run python scripts/scribehand/orchestrate.py env-check [--json]

# Emit shell exports from diagnostics/scribehand.env
uv run python scripts/scribehand/orchestrate.py env-export
```

---

## Sharing results with cloud evaluation

After each `step_7_pack_*`, commit or attach the `.zip` bundles. Cloud-side agents read them via:

```python
from scribesim.scribehand.diagnostics import summarize_bundle
```

Include `human_review.md` in the diagnostic directory **before** final `diag-pack` if the
human reviewed before re-pack; otherwise attach separately.

---

## Troubleshooting (agent actions)

| Symptom | Agent action |
|---------|--------------|
| `validate` fails on JSON field | Read artifact; apply fix from manifest `on_failure`; re-run step |
| Runner ImportError | Read stderr; patch `scripts/scribehand/*_runner.py`; retry step_6_word_proofs |
| `corpus_gates.json` ok=false | Edit charset_map.toml; re-run step_3 |
| HTR over-rejects real words | Do not proceed to render; re-calibrate step_5 |
| `next` returns human step | Stop and notify human — do not skip |

See the [human runbook troubleshooting table](./scribehand-mac-runbook.md#troubleshooting) for detail.
