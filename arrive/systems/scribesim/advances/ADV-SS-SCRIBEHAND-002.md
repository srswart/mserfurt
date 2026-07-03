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
  started_by: null
  implementation_completed_at: null
  implementation_completed_by: null
  updated_by: cursor-agent
  archived_at: null
  archived_by: null
  review_time_estimate_minutes: 30
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - legibility
  evidence:
  - ci:passed
  status: in_progress
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

- [x] branch: cursor/learned-scribal-hand-direction-3c31
- [x] tidy: none required
- [x] test: rejection-loop behavior with stub scorer (pass, retry, exhaust, flaky-recovery) — red first
- [x] feat: rejection-sampling wrapper + per-word provenance (verified/htr_cer/retries)
- [x] feat: verify-words CLI for batch re-scoring; TrOCRScorer adapter (torch-optional)
- [x] feat: HTR fine-tune script (scripts/scribehand/train_htr_trocr.py)
- [ ] Mac: train htr_trocr_v1, calibrate CER threshold on real held-out anchor words

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

## Changes Made

### 2026-07-03: HTR gate

**test**

- `tests/test_scribehand.py: CER, StubScorer, verify_words retry semantics (red first)`: 

### 2026-07-03: HTR fidelity gate

**feat**

- `scribesim/scribehand/{htr,verify}.py: CER, scorers, rejection sampling`: 
- `scribesim/cli.py: verify-words command; --neural-htr wiring`: 
- `scripts/scribehand/train_htr_trocr.py: TrOCR fine-tune glue (Mac-side)`: 

