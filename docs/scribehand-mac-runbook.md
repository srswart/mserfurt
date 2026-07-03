# ScribeHand Mac Runbook — TD-018 training, generation, and evaluation

Step-by-step workflow for the GPU workstation (Mac M5 Max / MPS). Each stage
ends with a **diagnostic checkpoint**: what to inspect yourself, and what to
pack into a bundle to share back for cloud-side evaluation.

> **Agent orchestration:** A local agent can run every step here **except §8
> (human visual review)**. Use the companion
> [agent runbook](./scribehand-mac-runbook-agent.md) with
> [`scribehand-orchestration.yaml`](./scribehand-orchestration.yaml) and
> `python scripts/scribehand/orchestrate.py`, or invoke `/scribehand-orchestrate`
> in Cursor.

The CPU dev VM already validated all plumbing end-to-end with stub backends;
everything below exercises the same code paths with real models.

---

## 0. Setup

```bash
git pull
uv sync --extra scribehand
uv run python scripts/scribehand/env_check.py   # expect mps_available: true, device_smoke_ok: true
```

Clone the upstream model repos (anywhere outside this repo):

```bash
git clone https://github.com/dailenson/One-DM        ~/src/One-DM
git clone https://github.com/koninik/DiffusionPen    ~/src/DiffusionPen
```

Follow each repo's README to install its requirements (in separate venvs is
fine — the runners execute with `workdir` inside those clones) and download
the pretrained IAM checkpoints they publish.

> **Diagnostic checkpoint 0:** save `env_check.py` output; it goes into every
> bundle's `run.json` automatically, but keep a copy on first setup.

## 1. Build the corpus (Tier 1: CATMuS)

```bash
# smoke first (a few hundred lines) to verify the live column names
uv run scribesim build-scribehand-corpus --catmus --catmus-max-lines 300

# then the full pull (filters: cursiva/bastarda/hybrida, 14th-16th c.)
uv run scribesim build-scribehand-corpus --catmus
```

If the CATMuS schema differs from the defaults (`im`, `text`, `script_type`,
`century`, `language`, `shelfmark`), pass a corrected `field_map` via a small
driver script around `scribesim.handcorpus.builder.build_catmus_tier` — and
report the actual column names back so the defaults get fixed.

## 2. Build the anchor tier (Tier 2: BSB anchor hand)

Harvest and review the anchor manuscript with the existing tooling
(`harvest-exemplars`, `annotate-reviewed-exemplars`, `extract-lines/words`,
`transcribe-words`), then assemble `images/ + labels.tsv`
(`filename<TAB>text<TAB>writer`) and ingest:

```bash
uv run scribesim build-scribehand-corpus --anchor-dir /path/to/reviewed_anchor
```

Target 300–1,000 reviewed pairs. Also freeze the **style anchor**: pick 5–10
clean word crops, place them in `shared/models/scribehand/style_anchor_v1/`
with a `style.json` (`{"id": "anchor_v1", "exemplars": ["ex1.png", ...],
"source": {"shelfmark": "..."}}`).

## 3. Gate the corpus

```bash
uv run scribesim check-scribehand-corpus --report diagnostics/corpus_gates.json
```

Charset gaps fail loudly. Fill genuine gaps in
`shared/training/scribehand/charset_map.toml` (only map characters the corpus
truly lacks). Re-run until green.

```bash
uv run scribesim export-scribehand-corpus --out-dir shared/training/scribehand/exports/generic_v1
```

> **Diagnostic checkpoint 3:** commit `manifest.json` (small, no images),
> `corpus_gates.json`, and the charset map. That is enough for cloud-side
> review of corpus composition.

## 4. Fine-tune the generators

Fine-tune both models (TD-018 selects by bench results, not by assumption):

- **One-DM** and **DiffusionPen**: prepare their expected IAM-style data from
  `exports/generic_v1` (`labels.tsv` carries id/path/text/writer/split; the
  writer column maps to their style-class labels) and run each repo's training
  entry point starting from the published IAM checkpoints.
  Sequence per TD-018 §2.3: Tier 1 (script) → Tier 2 anchor-only at low LR.

Record for each run: base checkpoint, dataset export name, epochs, LR, and
final loss — a `training_report.json` next to each checkpoint.

## 5. Fine-tune the HTR gate

```bash
uv run python scripts/scribehand/train_htr_trocr.py \
  --data shared/training/scribehand/exports/generic_v1 \
  --out  shared/models/scribehand/weights/htr_trocr_v1
```

**Calibrate before gating generation:** score held-out *real* anchor words
(`scribesim verify-words heldout.tsv --htr shared/models/scribehand/weights/htr_trocr_v1`).
Real words must pass the CER threshold — if they don't, the scorer is not
ready and the gate would reject authentic style. Threshold lives in
`shared/hands/validation/neural_gates.toml`.

## 6. Configure backends and generate proofs

Fill in `shared/models/scribehand/backends.toml` (see comments), then:

```bash
# single words first — expect the first runner invocation to surface API
# drift in the research repos; fix load_pipeline/sampling in the runner and retry
uv run scribesim generate-word "und" --backend onedm --seed 7 --out /tmp/und.png
uv run scribesim generate-word "schreiber" --backend diffusionpen --seed 7 --out /tmp/schreiber.png

# then a full folio with the HTR gate + diagnostics
uv run scribesim render f01r --approach neural \
  --neural-backend onedm \
  --neural-htr shared/models/scribehand/weights/htr_trocr_v1 \
  --neural-diag-dir diagnostics/onedm_f01r
```

## 7. Bench + pack diagnostics

```bash
uv run scribesim bench-neural f01r \
  --backend onedm \
  --htr shared/models/scribehand/weights/htr_trocr_v1 \
  --anchor-words-dir /path/to/anchor_word_crops \
  --reference-page  /path/to/anchor_page.jpg \
  --out-dir diagnostics/onedm_f01r

uv run scribesim diag-pack diagnostics/onedm_f01r --out diagnostics/onedm_f01r.zip
```

Repeat for `diffusionpen`. **Calibration rule:** run `bench-neural` gates on a
*real* anchor page first (compose-free: score real word crops with
`verify-words`, run the acceptance bands with the real page as both inputs’
population) — real pages must pass their own gates before thresholds are
trusted.

> **Diagnostic checkpoint 7 — what to share back:** commit or attach
> `diagnostics/<run>.zip` for each backend. The bundle contains `run.json`
> (environment + seeds + checkpoints), `metrics.json` (gate verdicts),
> `report.json`, page sheets, sampled word crops, and per-word provenance —
> everything needed for cloud-side evaluation without the weights.

## 8. Guided human evaluation (your eyes)

For each candidate backend, review the bench sheets side by side with a real
anchor folio and score 1–5 on each axis:

1. **Letterform authenticity** — would a paleographer read this as Bastarda?
   Check `a`, `g`, long s, ascender loops against the anchor.
2. **Instance variation** — find a repeated word (`und` appears often); the
   instances must differ visibly but stay the same hand.
3. **Word rhythm** — slant/weight/x-height co-vary naturally along a line?
4. **Ink behavior** — stroke-internal weight modulation, no uniform outlines?
5. **Text fidelity** — read 3 random lines against the folio JSON text.

Record scores in a `human_review.md` inside the diagnostic directory before
packing. Anything ≤ 3 on axes 1–2 means the fine-tune needs more Tier-2
epochs or better anchor data — file that observation with the bundle.

## 9. Promotion

Only after both automated gates and human review pass on the proof-folio set
(f01r, one pressure-heavy folio, one fatigue folio, one final-stock folio):
flip the default in your workflow to `--approach neural`, keep `evo` as
fallback per TD-018 rollout policy, and record the decision in
ADV-SS-HANDVALIDATE-007.

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Runner ImportError | Research repo API drift — adjust `load_pipeline`/sampling imports in `scripts/scribehand/*_runner.py` against your clone; the stderr excerpt is in the scribesim error |
| CATMuS columns differ | Pass `field_map` to `build_catmus_tier`; report actual names back |
| HTR over-rejects | Re-calibrate on real held-out anchor words before gating (step 5) |
| Words look great, page looks flat | Movement/ink params: adjust profile TOML; composition honors `line.*` and `folio.*` movement fields |
| MPS op unsupported | `PYTORCH_ENABLE_MPS_FALLBACK=1` for the affected run; note it in the bundle |
