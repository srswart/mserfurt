---
advance:
  id: ADV-SS-MOVEMENT-001
  title: Multi-Scale Movement Model — Page, Line, Word, Glyph Dynamics
  system: scribesim
  primary_component: movement
  components:
  - movement
  - layout
  started_at: 2026-03-20T13:10:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T09:43:41.616635Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  - public_api
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Implement the multi-scale movement model from TD-002 Part 1: four nested movement scales (page posture, line trajectory, word envelope, glyph trajectory) whose contributions compose additively to produce the final nib position at each point in time. This replaces the current deterministic grid placement with a physically-motivated trajectory system that produces naturalistic variation.

## Behavioral Change

After this advance:
- `PagePosture` applies page-level rotation (±1°), drift over the page, vertical reach curve affecting baseline straightness, and left margin drift
- `LineTrajectory` generates per-line baselines as Bezier curves (gentle arcs, not straight lines), with x-height drift and speed profiles along each line
- `WordEnvelope` applies attack/sustain/release speed dynamics per word, with per-word baseline offset and context-dependent inter-word spacing (exit/entry stroke angles)
- `GlyphTrajectory` wraps each glyph's Bezier strokes with entry/exit angle adaptation and per-glyph baseline jitter
- Nib position is computed as: `page_posture(line) + line_trajectory(x) + word_envelope(word_progress) + glyph_trajectory(glyph_progress)`
- The layout engine produces `PositionedGlyph` records with the composed trajectory offsets, replacing the current grid-based placement
- All movement parameters are sourced from the `HandProfile` (folio, line, word, glyph scale groups)
- Movement is deterministic given a seed — same seed produces identical trajectories

## Planned Implementation Tasks

- [ ] Tidy: define interfaces between movement model and existing layout placer — movement produces trajectory offsets, placer consumes them
- [ ] Test: write tests for each scale independently — page posture rotation, line baseline curvature, word spacing variation, glyph jitter; then composition (sum of all scales produces plausible nib positions)
- [ ] Implement: `PagePosture` — page rotation, rotation drift, vertical reach curve, left margin cumulative drift
- [ ] Implement: `LineTrajectory` — Bezier baseline curves, per-line start position jitter (±0.5-1.5mm), x-height drift function, speed profile
- [ ] Implement: `WordEnvelope` — attack/sustain/release speed dynamics, per-word baseline offset (±0.2mm), context-dependent spacing from exit/entry angles
- [ ] Implement: `GlyphTrajectory` — per-glyph baseline jitter, entry angle adaptation from preceding glyph's exit angle
- [ ] Implement: `compose_trajectory()` — sum all four scales to produce final nib position offsets for each positioned glyph
- [ ] Integrate: update `layout/placer.py` to apply composed trajectory offsets to `PositionedGlyph` coordinates
- [ ] Integrate: wire movement model into `layout/placer.py` so it is ACTIVE by default — composed trajectory offsets applied to all PositionedGlyph coordinates
- [ ] Validate: render f01r with movement model enabled; verify baselines are curved (not straight), word spacing varies, left margin drifts; compare visual output against v1
- [ ] Checkpoint: run `./snapshot.sh movement-001` — VISUAL DIFF vs hand-002 snapshot: baselines should curve, word spacing should vary, left margin should drift. This is the first visually distinct output from v2.

## Risk + Rollback

**Risks:**
- Movement parameters must be carefully tuned to avoid either too-perfect (synthetic-looking) or too-chaotic (unreadable) output
- Integration with the existing layout placer requires careful coordination — line breaking must happen before movement offsets are applied
- The composition of four noise sources could produce unexpected amplification at certain frequencies

**Rollback:**
- Revert the branch; movement model is a new module with no existing dependencies

## Evidence

- [ ] 26 tests in `tests/test_movement.py` covering all four scales, composition, determinism, apply_movement
- [ ] 197 total tests pass (0 failures)
- [ ] Snapshot `movement-001` visually differs from `hand-002` — movement model is active and producing baseline curvature, margin drift, word spacing variation
