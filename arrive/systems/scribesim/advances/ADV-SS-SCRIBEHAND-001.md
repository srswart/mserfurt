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
  review_time_estimate_minutes: 45
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence: []
  model_usage: []
  status: planned
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

- [ ] branch: create or confirm feature branch for this advance
- [ ] tidy: none expected (new subpackage); confirm
- [ ] test: inference-wrapper contract tests with a stub backend (determinism, provenance, cache) — red first
- [ ] feat: training scripts/configs for One-DM and DiffusionPen fine-tunes (GPU-run, artifacts pulled back by manifest)
- [ ] feat: inference wrapper + style anchor freeze + modifier mapping
- [ ] feat: `generate-word` / `generate-line` CLI subcommands

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

(none yet)
