---
advance:
  id: ADV-WX-INK-001
  title: "Ink — Initial Implementation"
  system: weather
  primary_component: ink
  components: [ink]
  started_at: ~
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
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

Simulate 560 years of iron gall ink degradation through three distinct aging effects: global fade with color shift, localized bleed via Gaussian blur, and pressure-dependent flaking that targets the heaviest strokes identified by ScribeSim pressure heatmaps.

## Behavioral Change

After this advance:
- Ink fade applies a global 20% intensity reduction and shifts ink color from black toward dark brown using the RGB delta [+8, -3, -12], simulating iron gall oxidation over 560 years
- Ink bleed applies a 1.0px Gaussian blur restricted to ink pixels only (non-ink regions remain sharp), simulating capillary spread into vellum fibers
- Ink flake removes small clusters (size 2) of ink pixels with probability 0.008, preferentially targeting strokes where the ScribeSim pressure heatmap exceeds the 0.85 threshold, simulating mechanical loss from the heaviest pen strokes

## Pipeline Context

- **Position**: Phase 3 (Weather — Manuscript Aging & Weathering)
- **Upstream**: ScribeSim page images (ink layer), ScribeSim pressure heatmaps (for flake targeting), ms-erfurt-560yr.toml for ink aging parameters
- **Downstream**: Ink-aged images consumed by damage (water dissolves already-faded ink), compositor (ink layer stacked after substrate)
- **Contracts**: TD-001-E (Weathering profile TOML — ink section)

## Component Impact

```yaml
components: [ink]
system: weather
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-ink-init`
- [ ] Tidy: define ink module interface, ink pixel mask extraction from ScribeSim page images, pressure heatmap loader
- [ ] Test: write tests for ink_fade verifying 20% intensity reduction and RGB shift [+8, -3, -12] applied uniformly to ink pixels
- [ ] Test: verify ink_bleed applies 1.0px Gaussian blur only to ink-masked regions, leaving non-ink pixels unchanged
- [ ] Test: verify ink_flake targets pixels above pressure heatmap threshold 0.85 with probability 0.008, producing clusters of size 2
- [ ] Test: verify flake probability is near-zero for pixels below pressure threshold 0.85
- [ ] Implement: ink pixel mask extraction using luminance threshold on ScribeSim page images
- [ ] Implement: ink_fade effect — apply RGB delta [+8, -3, -12] and 20% intensity reduction to masked ink pixels
- [ ] Implement: ink_bleed effect — masked 1.0px Gaussian blur that only spreads within and from ink regions
- [ ] Implement: ink_flake effect — pressure-aware stochastic removal with cluster expansion (size 2) seeded by heatmap values above 0.85
- [ ] Validate: process a folio with known heavy strokes, confirm flake clusters concentrate on high-pressure areas; measure global fade matches 20% reduction target

## Risk + Rollback

**Risks:**
- Ink mask extraction threshold may need calibration per folio if ScribeSim renders with varying ink density
- Gaussian blur on ink-only pixels requires careful edge handling to avoid halo artifacts at ink/vellum boundaries

**Rollback:**
- Revert the feat/weather-ink-init branch; compositor can pass through unaged ink layer from ScribeSim

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
