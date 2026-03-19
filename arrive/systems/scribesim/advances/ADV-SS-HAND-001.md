---
advance:
  id: ADV-SS-HAND-001
  title: "Hand — Initial Implementation"
  system: scribesim
  primary_component: hand
  components: [hand]
  started_at: ~
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags: [new_dependency]
  evidence:
    - tdd:red-green
    - tidy:preparatory
    - tests:unit
  status: planned
---

## Objective

Implement the scribal hand model that loads Brother Konrad's base Bastarda hand parameters from `konrad_erfurt_1457.toml` and applies a folio-specific modifier stack derived from CLIO-7 hand notes, producing a fully resolved hand configuration for each folio.

## Behavioral Change

After this advance:
- Base hand parameters (nib width, nib angle 40 degrees, x-height, ascender/descender ratios, default pressure curve, ink flow rate) load from `shared/hands/konrad_erfurt_1457.toml`
- The modifier stack architecture computes `final_hand(folio) = base_hand + sum(modifiers(folio.hand_notes))`, supporting the documented modifiers: `pressure_increase` (f06r), `ink_density_shift` (f07r multi-sitting boundary), `hand_scale` (f07v lower section, smaller hand), and `spacing_drift + tremor` (f14r onward, fatigue effects)
- Hand resolution is deterministic: the same folio ID and hand notes always produce identical parameters

## Pipeline Context

- **Position**: Phase 2 (ScribeSim — Scribal Hand Simulation)
- **Upstream**: Per-folio JSON from XL containing `hand_notes` fields; `shared/hands/konrad_erfurt_1457.toml` base parameter file
- **Downstream**: Resolved hand parameters feed into layout (line spacing, glyph sizing) and render (nib model, pressure curves, ink flow)
- **Contracts**: TD-001-D (Hand parameter TOML schema — defines required keys, value ranges, and modifier semantics)

## Component Impact

```yaml
components: [hand]
system: scribesim
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/scribesim-hand-init`
- [ ] Tidy: define `HandParams` dataclass with fields for nib_width, nib_angle (default 40 degrees), x_height, pressure_curve, ink_flow_rate, spacing, tremor_amplitude; define `HandModifier` protocol
- [ ] Test: write unit tests — base hand loads correctly from TOML; applying `pressure_increase` modifier raises pressure curve values; `ink_density_shift` modifier adjusts ink flow for f07r sitting boundary; `hand_scale` modifier reduces glyph dimensions for f07v; `spacing_drift + tremor` modifiers produce visible parameter changes for f14r+
- [ ] Implement: TOML parser for `konrad_erfurt_1457.toml` into `HandParams`
- [ ] Implement: modifier registry mapping CLIO-7 hand note keys to modifier functions
- [ ] Implement: `resolve_hand(base, folio_hand_notes)` that applies modifiers in stack order and returns final `HandParams`
- [ ] Validate: round-trip test — resolve hand for f01r (no modifiers, should equal base), f06r (pressure increase), f07r (ink density shift), f07v (scale change), f14r (fatigue drift + tremor)

## Risk + Rollback

**Risks:**
- Modifier interaction effects: applying multiple modifiers to the same folio (e.g., f14r has both spacing_drift and tremor) could produce implausible parameter combinations if ranges are not clamped
- TOML schema drift between the hand parameter file and the parser will silently drop new parameters

**Rollback:**
- Revert the `feat/scribesim-hand-init` branch; hand parameters are stateless and computed on demand

## Evidence

| Type | Status | Notes |
|------|--------|-------|
| tdd:red-green | pending | |
| tidy:preparatory | pending | |
| tests:unit | pending | |

## Changes Made

_No changes yet._

## Check for Understanding

_To be generated after implementation._
