---
advance:
  id: ADV-SS-SCRIBEHAND-002
  title: HTR Fidelity Gate — Bastarda HTR Rejection Sampling with Per-Word Provenance
  system: scribesim
  primary_component: scribehand
  components:
  - scribehand
  - handcorpus
  - handvalidate
  started_at: 2026-07-03T14:00:00Z
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - legibility
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Implement the text-fidelity invariant of
[TD-018](../../../../docs/tech-direction/TD-018-learned-scribal-hand.md) §2.7:
every AI-generated word must be verified to read as its source text.

- Fine-tune a Bastarda HTR scorer (Kraken or TrOCR-base) on the same
  Tier-1/Tier-2 corpus (or adopt an existing CATMuS-trained checkpoint if its
  held-out CER on the anchor hand is acceptable).
- Wrap `generate_word` in a rejection-sampling loop: regenerate with a new seed
  when CER/confidence thresholds fail; bounded retries, then flag for review.
- Record per-word provenance (seed, retry count, HTR score) mirroring Weather's
  provenance sidecar pattern.

## Behavioral Change

After this advance:
- Generated word strips carry an HTR verification verdict; unverified words
  cannot enter page composition silently.
- A calibration report documents the CER threshold against held-out real anchor
  words (so the gate rejects hallucination without rejecting authentic style).

## Planned Implementation Tasks

- [ ] branch: create or confirm feature branch for this advance
- [ ] tidy: none expected; confirm
- [ ] test: rejection-loop behavior with stub scorer (pass, retry, exhaust) — red first
- [ ] feat: HTR scorer training config + evaluation on held-out anchor lines
- [ ] feat: rejection-sampling wrapper + provenance sidecar emission
- [ ] feat: `scribesim verify-words` CLI for batch re-scoring existing strips

## Bug Fixes

- [ ] None yet

## Risk + Rollback

- Risk: a weak HTR scorer under-rejects (hallucinated letterforms pass) or
  over-rejects (authentic variation fails); calibrate thresholds on real anchor
  words before gating generation, and keep the threshold in config.
- Rollback: disable the gate flag; generation still works but is marked
  unverified (composition refuses unverified words by default).

## Evidence

- [ ] tdd:red-green
- [ ] tests:unit
- [ ] tests:integration (end-to-end generate→verify on a proof vocabulary)

## CI Evidence Notes

- CI jobs are currently disabled; run externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-SCRIBEHAND-002 --status passed`

## Changes Made

(none yet)
