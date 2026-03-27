---
advance:
  id: ADV-SS-HANDFLOW-007
  title: Secondary Parameter Activation — Tremor and Warp in Corridor-Bounded Reviewed Handflow
  system: scribesim
  primary_component: handflow
  components:
  - handflow
  - handvalidate
  - training
  started_at: null
  started_by: null
  implementation_completed_at: null
  implementation_completed_by: null
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - legibility
  - controller_stability
  evidence:
  - tests:integration
  - snapshot
  status: proposed
---

## Objective

Activate `folio.tremor_amplitude` and `glyph.warp_amplitude_mm` in the reviewed guided path, but only as bounded effects inside the corridor so the parameters add controlled irregularity rather than unreadable distortion.

## Planned Implementation Tasks

- [ ] add deterministic tremor to the active reviewed guided path
- [ ] add bounded nominal-path deformation for `glyph.warp_amplitude_mm`
- [ ] ensure both effects are corridor-aware and disabled or clipped when they threaten legibility
- [ ] generate reviewed proof studies that isolate tremor and warp from the already activated core parameters

## Validation Gates

- [ ] tremor and warp each produce measurable output deltas on reviewed proof lines
- [ ] corridor containment and nominal legibility do not regress beyond approved thresholds
- [ ] parameter studies clearly separate gentle and stressed variants without collapsing symbol identity

## Risk + Rollback

These are the easiest controls to overdo. If activation makes proofs obviously less readable or causes guide-following instability, disable them and keep only the core activated controls from `ADV-SS-HANDFLOW-006`.

## Evidence

- [ ] reviewed proof sheets for gentle vs stressed tremor/warp studies
- [ ] parameter sensitivity metrics with corridor and legibility comparisons
- [ ] tests proving tremor/warp are active but bounded
