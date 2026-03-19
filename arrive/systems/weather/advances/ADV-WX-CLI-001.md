---
advance:
  id: ADV-WX-CLI-001
  title: "CLI — Initial Implementation"
  system: weather
  primary_component: cli
  components: [cli]
  started_at: ~
  implementation_completed_at: ~
  review_time_estimate_minutes: 20
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

Provide the command-line entry point for the Weather system, exposing `weather apply`, `weather apply-batch`, `weather preview`, `weather groundtruth-update`, and `weather catalog` commands that drive 560-year aging and damage simulation on ScribeSim page images.

## Behavioral Change

After this advance:
- Running `weather apply --folio f04r` loads the weathering profile (ms-erfurt-560yr.toml) and applies the full compositing pipeline to a single folio image
- Running `weather apply-batch` processes all 17 folios (f01r through f17v) from the ScribeSim output directory, writing `{folio_id}_weathered.png` and `{folio_id}_weathered.xml` to the output directory
- Running `weather preview --folio f04v --effect damage` renders an isolated preview of a single effect layer for rapid iteration
- Running `weather catalog` lists all folios with their assigned vellum stock (standard vs irregular) and damage annotations from the XL manifest

## Pipeline Context

- **Position**: Phase 3 (Weather — Manuscript Aging & Weathering)
- **Upstream**: ScribeSim page images, pressure heatmaps, PAGE XML; XL manifest.json; shared/profiles/ms-erfurt-560yr.toml
- **Downstream**: Dispatches to compositor for effect application; no external consumers (CLI is the user-facing entry point)
- **Contracts**: TD-001-E (Weathering profile TOML), TD-001-C (PAGE XML)

## Component Impact

```yaml
components: [cli]
system: weather
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-cli-init`
- [ ] Tidy: set up weather system package structure, define CLI argument schema for all five commands
- [ ] Test: write tests for argument parsing, profile loading (ms-erfurt-560yr.toml), and folio ID validation (f01r-f17v format)
- [ ] Implement: build CLI dispatcher that loads the weathering profile, resolves input paths for ScribeSim outputs and XL manifest, and routes to the appropriate command handler
- [ ] Implement: `weather apply` single-folio pipeline invocation with --folio and --output flags
- [ ] Implement: `weather apply-batch` multi-folio iteration with progress reporting
- [ ] Implement: `weather preview` isolated effect rendering with --effect flag accepting substrate, ink, damage, aging, optics
- [ ] Implement: `weather groundtruth-update` PAGE XML coordinate correction entry point
- [ ] Implement: `weather catalog` folio listing with vellum stock and damage annotation summary
- [ ] Validate: run `weather catalog` against XL manifest and confirm f04r-f05v show water_damage, f04v shows missing_corner, f14-f17 show irregular stock

## Risk + Rollback

**Risks:**
- Incorrect path resolution for ScribeSim outputs could silently process stale images
- Profile TOML schema changes in ms-erfurt-560yr.toml would break CLI startup without clear error messages

**Rollback:**
- Revert the feat/weather-cli-init branch; no downstream components depend on CLI internals

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
