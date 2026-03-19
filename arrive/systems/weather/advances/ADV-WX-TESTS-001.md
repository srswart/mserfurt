---
advance:
  id: ADV-WX-TESTS-001
  title: "Tests — Initial Implementation"
  system: weather
  primary_component: tests
  components: [tests]
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

Provide comprehensive integration and system-level tests for the Weather pipeline: effect isolation verification, compositing order enforcement, per-folio dispatch correctness, coordinate accuracy within 2px tolerance, damage zone annotation validation, deterministic output reproducibility, and a full 17-folio integration test producing eScriptorium-ready output.

## Behavioral Change

After this advance:
- Effect isolation tests confirm each weathering effect (substrate, ink, damage, aging, optics) can be applied independently and produces the expected visual transformation without side effects on other layers
- Compositing order tests verify that swapping any two layers in the substrate -> ink -> damage -> aging -> optics sequence produces a detectably different output
- Per-folio dispatch tests confirm water_damage applies exclusively to f04r, f04v, f05r, f05v and missing_corner applies exclusively to f04v
- Coordinate accuracy tests verify all PAGE XML glyph coordinates in weathered output are within 2px of their mathematically expected positions after page_curl transform
- Damage zone tests confirm f04v corner glyphs are marked legibility 0.0 and water-damaged zone glyphs on f04r-f05v carry graduated legibility scores
- Water damage direction tests verify the gradient is strongest at top (from_above) with measurable intensity falloff
- Vellum stock tests confirm f14r uses irregular stock (yellow-shifted, different noise seed) while f01r uses standard stock (warm cream)
- Determinism tests verify two runs with the same seed produce byte-identical output images
- Integration test processes all 17 folios end-to-end and validates output is importable into eScriptorium

## Pipeline Context

- **Position**: Phase 3 (Weather — Manuscript Aging & Weathering)
- **Upstream**: All Weather components (compositor, groundtruth, and transitively all effect components); ScribeSim output fixtures for test input
- **Downstream**: No downstream consumers; tests validate final output quality for eScriptorium import
- **Contracts**: TD-001-E (Weathering profile TOML — all sections), TD-001-C (PAGE XML — coordinate and legibility validation)

## Component Impact

```yaml
components: [tests]
system: weather
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-tests-init`
- [ ] Tidy: set up test fixtures — minimal ScribeSim page images, pressure heatmaps, PAGE XML, and XL manifest for a representative folio subset (f01r standard, f04v damaged, f14r irregular)
- [ ] Test: effect isolation — apply each of 5 effects independently, verify output differs from input and other effects don't bleed through
- [ ] Test: compositing order — run pipeline with correct order and one swapped pair, assert pixel-level difference in output
- [ ] Test: per-folio dispatch — process f04r (water_damage only), f04v (water_damage + missing_corner), f01r (no damage), confirm correct effect selection
- [ ] Test: coordinate accuracy — apply page_curl transform to known glyph coordinates, verify weathered XML positions are within 2px of analytical expectation
- [ ] Test: damage zones — load f04v weathered XML, confirm glyphs in bottom-right 35mm x 28mm corner have legibility 0.0
- [ ] Test: water damage direction — measure ink dissolution intensity at top vs bottom of f04r, assert top > bottom
- [ ] Test: vellum stock — compare substrate output for f01r (standard, warm cream) and f14r (irregular, yellow-shifted), assert different base colors and noise patterns
- [ ] Test: determinism — run full pipeline twice with fixed seed, assert byte-identical PNG output
- [ ] Test: integration — process all 17 folios (f01r through f17v), verify 17 weathered PNGs and 17 weathered XMLs are produced, validate PAGE XML schema compliance for eScriptorium import
- [ ] Validate: all tests pass in CI; integration test completes within acceptable time budget

## Risk + Rollback

**Risks:**
- Test fixtures must be representative but small enough to keep test execution fast; full-resolution 17-folio integration test may be slow
- Byte-identical determinism requires all random number generators to be seeded consistently across all effect components

**Rollback:**
- Revert the feat/weather-tests-init branch; individual component tests (written as part of each component's advance) remain functional

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
