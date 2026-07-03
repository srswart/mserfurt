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
  started_by: null
  implementation_completed_at: null
  implementation_completed_by: null
  updated_by: cursor-agent
  archived_at: null
  archived_by: null
  review_time_estimate_minutes: 45
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - public_api
  evidence:
  - ci:passed
  status: in_progress
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

- [x] branch: cursor/learned-scribal-hand-direction-3c31
- [x] tidy: deferred refextract import in pathguide.io (fresh clones could not import handvalidate at all)
- [x] test: composition geometry + word-level PAGE XML contract tests — red first
- [x] feat: word-strip compositor with seeded movement, gap compression + bounded squeeze, lacuna fading
- [x] feat: word-level PAGE XML emission (TD-001 addendum still pending)
- [x] feat: --approach neural CLI wiring + render report + diagnostic bundle hook
- [ ] TD-001 addendum documenting the word-level PAGE XML contract change
- [ ] Mac: full-folio proofs with fine-tuned backends

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

## Changes Made

### 2026-07-03: defer refextract import in pathguide.io

**tidy**

- `scribesim/pathguide/io.py: import moved into load_trace_as_dense (also un-broke collection of 6+ existing test files on fresh clones)`: 

### 2026-07-03: neural composition + CLI

**test**

- `tests/test_scribehand_compose.py, tests/test_scribehand_cli.py (red first)`: 

### 2026-07-03: neural page composition

**feat**

- `scribesim/scribehand/{compose,pagexml,diagnostics}.py`: 
- `scribesim/cli.py: --approach neural + --neural-* options, diag-pack command`: 
- `Verified end-to-end on f01r with stub-evo: 175 words generated, verified (stub HTR), composed, word-level PAGE XML emitted`: 

