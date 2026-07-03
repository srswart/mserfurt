---
advance:
  id: ADV-SS-SCRIBEHAND-003
  title: Neural Page Composition — Layout Integration, Word-Level PAGE XML, --approach neural
  system: scribesim
  primary_component: scribehand
  components:
  - scribehand
  - layout
  - movement
  - groundtruth
  - cli
  started_at: 2026-07-03T14:00:00Z
  implementation_completed_at: ~
  review_time_estimate_minutes: 45
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - public_api
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Compose HTR-verified generated word strips into full folio pages per
[TD-018](../../../../docs/tech-direction/TD-018-learned-scribal-hand.md) §2.5–§2.6:

- `layout.place()` slots words using measured strip advances; the existing
  movement/imprecision model applies baseline wander, word envelope offsets, and
  ruling drift; strips are alpha-composited with the existing sepia ink blending,
  with optional TD-010 ink-cycle tone modulation per word.
- Emit **word-level** PAGE XML (bbox + baseline + transcription) by construction;
  glyph polygons become optional via forced alignment (TD-001 addendum required).
- Expose the path as `scribesim render --approach neural` behind the TD-014
  A/B bench, with evo remaining the default.

## Behavioral Change

After this advance:
- `scribesim render --folio f01r --approach neural` produces a full 300 DPI folio
  PNG in the anchor hand plus word-level PAGE XML, deterministic for fixed seeds.
- Weather consumes the output unmodified (word boxes available for
  `worddegrade`); lacuna opacity handling is preserved.

## Planned Implementation Tasks

- [ ] branch: create or confirm feature branch for this advance
- [ ] tidy: extract compositor interfaces shared between evo and neural paths (no behavior change)
- [ ] test: composition geometry + PAGE XML word-level contract tests — red first
- [ ] feat: word-strip compositor with movement integration and ink tone pass
- [ ] feat: word-level PAGE XML emission + TD-001 addendum documenting the contract change
- [ ] feat: `--approach neural` CLI wiring + render report (per-word provenance summary)

## Bug Fixes

- [ ] None yet

## Risk + Rollback

- Risk: PAGE XML granularity change may surprise downstream consumers; the
  TD-001 addendum and a schema version bump make the change explicit; Weather's
  actual dependency is word-level (verified against `weather/worddegrade.py`).
- Risk: tonal mismatch between generated strips and parchment base; the ink
  compositing pass normalizes strip contrast against the calibrated sepia curve.
- Rollback: flip `--approach` back to evo; contracts for evo/guided are untouched.

## Evidence

- [ ] tidy:preparatory
- [ ] tdd:red-green
- [ ] tests:integration (folio render end-to-end)
- [ ] snapshot (proof folios, neural vs evo side-by-side)

## CI Evidence Notes

- CI jobs are currently disabled; run externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-SCRIBEHAND-003 --status passed`

## Changes Made

(none yet)
