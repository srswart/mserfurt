---
advance:
  id: ADV-SS-SCRIBEHAND-001
  title: ScribeHand Model Bring-Up — Fine-Tuned Diffusion Word Generation with Style Anchor
  system: scribesim
  primary_component: scribehand
  components:
  - scribehand
  - handcorpus
  started_at: 2026-07-03T14:00:00Z
  implementation_completed_at: ~
  updated_by: cursor-agent
  review_time_estimate_minutes: 45
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence: []
  model_usage: []
  status: in_progress
---

## Objective

Bring up the learned letterform engine per
[TD-018](../../../../docs/tech-direction/TD-018-learned-scribal-hand.md) §2.2–§2.4:

- Fine-tune **One-DM** and **DiffusionPen** (parallel bring-up) on the Tier-1
  script-family corpus, then low-LR fine-tune on the Tier-2 anchor-hand corpus.
- Freeze the style anchor exemplar set (`shared/models/scribehand/style_anchor_v1/`).
- Implement `scribesim/scribehand/` inference wrapper: `generate_word(text,
  style_anchor, seed, modifiers)` returning an ink strip + provenance, with the
  deterministic seed policy (folio, line, word index) and word-image caching.
- Map CLIO-7 folio modifiers to generation controls (style-embedding
  interpolation/noise, guidance scale, x-height scale) per TD-018 §2.4.

## Behavioral Change

After this advance:
- `scribesim generate-word --text "und" --seed ...` produces a Bastarda word strip
  in the anchor hand, deterministically for fixed inputs.
- Two fine-tuned checkpoints exist with a documented selection comparison
  (side-by-side sheets on a shared prompt set) feeding the ADV-SS-HANDVALIDATE-007
  gate decision.
- Model weights are referenced by checksummed manifest, not committed to git.

## Planned Implementation Tasks

- [x] branch: cursor/learned-scribal-hand-direction-3c31
- [x] tidy: none required (new subpackage)
- [x] test: inference-wrapper contract tests with stub backends (determinism, provenance, cache) — red first
- [x] feat: inference wrapper + style anchor + CLIO-7 modifier mapping + generate-word/render CLI
- [x] feat: CommandBackend protocol + One-DM/DiffusionPen runner scripts (Mac-side, best-effort against upstream APIs)
- [ ] Mac: fine-tune One-DM + DiffusionPen (Tier 1 then Tier 2), freeze style_anchor_v1, checkpoint selection sheets

## Bug Fixes

- [ ] None yet

## Risk + Rollback

- Risk: fine-tune quality on medieval script may underperform (IAM-pretrained
  priors are modern cursive); mitigation ladder: longer Tier-1 schedule → VATr++
  fallback → stop-rule in TD-018 (TD-014 resumes as primary).
- Risk: GPU dependency for training; dev VM (no GPU) covers only CPU smoke
  inference. Training runs are external, reproducible from committed configs.
- Rollback: the neural path is additive and flag-gated; remove
  `scribesim/scribehand/` and the model manifest.

## Evidence

- [ ] tdd:red-green
- [ ] tests:unit
- [ ] snapshot (generated word sheets vs anchor exemplars, both checkpoints)

## CI Evidence Notes

- CI jobs are currently disabled; run externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-SCRIBEHAND-001 --status passed`

## Changes Made

### 2026-07-03 - test: scribehand core contracts
- tests/test_scribehand.py: seeds, backends, cache, style anchor, modifier mapping (red first)

### 2026-07-03 - feat: scribehand core
- scribesim/scribehand/{types,seeds,generate,style,modifiers}.py
- scribesim/scribehand/backends/{stub,command}.py + backends.toml resolver
- scripts/scribehand/{onedm_runner,diffusionpen_runner,env_check}.py
- shared/models/scribehand/backends.toml: backend registry template
- pyproject.toml: optional scribehand extra (torch/transformers/datasets/diffusers)
