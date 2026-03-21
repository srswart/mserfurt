---
advance:
  id: ADV-SS-KERNING-001
  title: Pair-Dependent Spacing & Contextual Glyph Adaptation
  system: scribesim
  primary_component: layout
  components:
  - layout
  - glyphs
  started_at: 2026-03-20T20:40:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T16:41:06.569411Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - public_api
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Implement pair-dependent letter spacing and contextual glyph adaptation so that words feel like organic pen gestures rather than uniformly-spaced stamp sequences. Currently every glyph gets a fixed advance_width regardless of its neighbors, producing mechanical-looking words. Real Bastarda spacing depends on the letter pair: some pairs sit tight (the pen barely lifts), others need breathing room.

## Behavioral Change

After this advance:
- Each Glyph has `entry_x`, `entry_y`, `exit_x`, `exit_y` — where the pen arrives and departs (x-height units)
- A kerning function computes pair-specific spacing: `kern(prev_glyph, next_glyph) -> float` (additional x-offset in x-height units)
- The placer applies kerning offsets when placing consecutive glyphs within a word
- Letter spacing within words has visible structured variation (not uniform)
- Word spacing (at spaces) remains controlled by `word_spacing_norm`
- Small random jitter (~±5% of advance) adds organic feel

## Planned Implementation Tasks

- [ ] Tidy: add `entry_x`, `entry_y`, `exit_x`, `exit_y` to Glyph dataclass
- [ ] Tidy: assign entry/exit points to all glyphs based on stroke start/end positions
- [ ] Test: kerning between "r" and "a" differs from "o" and "o"
- [ ] Test: total word width with kerning differs from uniform spacing
- [ ] Test: kerning values are within reasonable bounds (no overlap, no huge gaps)
- [ ] Implement: compute entry/exit points from each glyph's first/last stroke endpoints
- [ ] Implement: `kern(prev, next)` — distance between prev.exit and next.entry determines spacing adjustment
- [ ] Implement: small per-pair jitter (seeded) for organic variation
- [ ] Implement: update placer to apply kerning between consecutive glyphs within words
- [ ] Validate: render f01r — words show variable inter-letter spacing
- [ ] Checkpoint: `./snapshot.sh kerning-001`

## Risk + Rollback

**Risks:**
- Aggressive kerning could cause letter overlap — need minimum spacing guard
- Entry/exit point assignment for 90 glyphs needs care

**Rollback:**
- Revert the branch; kerning is additive to the placer

## Evidence

