---
advance:
  id: ADV-WX-COMPOSITOR-001
  title: "Compositor — Initial Implementation"
  system: weather
  primary_component: compositor
  components: [compositor]
  started_at: ~
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags: [new_dependency, public_api]
  evidence:
    - tdd:red-green
    - tidy:preparatory
    - tests:unit
  status: planned
---

## Objective

Orchestrate manifest-driven per-folio effect dispatch and layer compositing, stacking weathering effects in the defined order (substrate, ink, damage, aging, optics) while chaining coordinate transforms for downstream ground truth update.

## Behavioral Change

After this advance:
- Compositor reads the XL manifest to determine per-folio damage annotations and vellum stock, dispatching only applicable effects for each folio (e.g., water_damage only on f04r-f05v, missing_corner only on f04v)
- Layer compositing follows the strict order: substrate (base) -> ink -> damage -> aging -> optics (top), producing the final `{folio_id}_weathered.png`
- Coordinate transforms from page_curl (and any future spatial effects) are chained into a single composed transform and exported for groundtruth consumption
- Per-folio dispatch correctly selects irregular vellum stock for f14r-f17v and standard stock for f01r-f13v based on manifest data

## Pipeline Context

- **Position**: Phase 3 (Weather — Manuscript Aging & Weathering)
- **Upstream**: All effect components (substrate, ink, damage, aging, optics); XL manifest.json for per-folio configuration
- **Downstream**: Weathered page images consumed by groundtruth for PAGE XML update; final output imported into eScriptorium
- **Contracts**: TD-001-E (Weathering profile TOML — compositing order), TD-001-C (PAGE XML)

## Component Impact

```yaml
components: [compositor]
system: weather
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-compositor-init`
- [ ] Tidy: define compositor public API (compositing interface consumed by CLI and tests), layer protocol that each effect component must satisfy
- [ ] Test: write tests verifying compositing order is substrate -> ink -> damage -> aging -> optics (swap two layers, assert output differs)
- [ ] Test: verify per-folio dispatch applies water_damage only to f04r, f04v, f05r, f05v
- [ ] Test: verify per-folio dispatch applies missing_corner only to f04v
- [ ] Test: verify vellum stock selection maps f14r to irregular and f01r to standard
- [ ] Test: verify coordinate transform chain composes page_curl transform correctly
- [ ] Implement: manifest reader — parse XL manifest.json to extract per-folio damage annotations and vellum stock assignments
- [ ] Implement: per-folio dispatch logic — select applicable effects based on manifest annotations
- [ ] Implement: layer compositing pipeline — sequential application of substrate, ink, damage, aging, optics with intermediate buffer management
- [ ] Implement: coordinate transform chainer — compose all spatial transforms (currently page_curl only) into a single displacement map
- [ ] Implement: output writer — save `{folio_id}_weathered.png` with composited result
- [ ] Validate: process f04v end-to-end (all five layers including water_damage + missing_corner), confirm output image contains all effects; process f01r (no damage), confirm clean compositing without damage artifacts

## Risk + Rollback

**Risks:**
- Compositing order is critical: swapping damage and aging produces visually incorrect results (edge darkening should not appear on the backing board behind a missing corner)
- Public API stability is important since both CLI and tests depend on the compositing interface
- Memory pressure from holding multiple full-resolution layer buffers simultaneously for 17 folios in batch mode

**Rollback:**
- Revert the feat/weather-compositor-init branch; CLI cannot produce weathered output but individual effect components remain testable in isolation

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
