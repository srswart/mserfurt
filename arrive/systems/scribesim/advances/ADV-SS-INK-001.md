---
advance:
  id: ADV-SS-INK-001
  title: Ink-Substrate Interaction — Saturation, Pooling, Wicking, Feathering, Depletion
  system: scribesim
  primary_component: ink
  components:
  - ink
  - render
  started_at: 2026-03-20T14:20:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T10:30:36.777898Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Implement the five ink-substrate interaction filters from TD-002 Part 3. These are post-rasterization filters that transform the raw coverage buffer and metadata buffers (pressure, speed, direction, ink_load, dwell_time) into a realistic ink layer where darkness, edge quality, and micro-texture emerge from physical properties rather than design choices.

## Behavioral Change

After this advance:
- The rasterizer produces two outputs: a **coverage buffer** and **metadata buffers** (pressure, speed, direction, ink_load, dwell_time per pixel)
- **Filter 1 — Ink saturation**: `darkness = base_darkness * ink_load * (1 + pressure_boost * pressure) * (1 + speed_penalty / speed)` — slower strokes are darker, heavy pressure is denser, words after a fresh dip are richer
- **Filter 2 — Ink pooling**: at stroke terminations and direction changes where the nib pauses, ink pools — producing characteristic dark dots at stroke ends and cusps
- **Filter 3 — Vellum grain wicking**: anisotropic Gaussian blur along the calfskin grain direction (roughly vertical; sigma_along ≈ 0.4px, sigma_across ≈ 0.15px at 400 DPI) — ink follows the grain structure
- **Filter 4 — Hairline feathering**: where less ink meets more absorbent surface, edges break down — heavy strokes have crisp edges, hairlines have soft, slightly irregular edges
- **Filter 5 — Ink depletion cycle**: ink_remaining follows `initial_load * (1 - (strokes/capacity)^1.5)`, producing a visible periodic darkness rhythm across the page — rich after each dip, thinning before the next, sudden return to richness (~30-50 words per cycle)
- All filters are parameterized via the `[ink]` and `[material]` sections of `HandProfile`
- The existing pressure heatmap output is extended to include the metadata buffers needed by these filters

## Planned Implementation Tasks

- [ ] Tidy: define metadata buffer format — per-pixel arrays for pressure, speed, direction, ink_load, dwell_time; determine memory layout for efficient filter application
- [ ] Tidy: design the ink filter pipeline interface — each filter is a function `(coverage, metadata, params) -> coverage`, composable in sequence
- [ ] Test: write tests for each filter independently — saturation produces darker output for slower speed; pooling creates dark spots at stroke terminations; wicking produces directional blur; feathering softens hairlines but not heavy strokes; depletion creates periodic darkness variation
- [ ] Implement: extend rasterizer to produce metadata buffers alongside coverage buffer
- [ ] Implement: Filter 1 — ink saturation with pressure boost and speed penalty
- [ ] Implement: Filter 2 — ink pooling at dwell points (detected from low speed + high dwell_time)
- [ ] Implement: Filter 3 — vellum grain wicking (anisotropic Gaussian, grain direction parameterized)
- [ ] Implement: Filter 4 — hairline feathering (edge softening inversely proportional to ink_load)
- [ ] Implement: Filter 5 — ink depletion cycle (reservoir model, ~35-word cycle, visible darkness rhythm)
- [ ] Integrate: wire filter pipeline into the rendering path after rasterization, before final compositing
- [ ] Integrate: wire ink filter pipeline into the rendering path — filters run automatically after rasterization, before final compositing. Each filter individually toggleable via `[ink]` params (set strength to 0 to disable).
- [ ] Validate: render f01r with all filters enabled; verify ink variation is visible but not overwhelming; compare periodic darkness pattern against real manuscript samples
- [ ] Checkpoint: run `./snapshot.sh ink-001` — VISUAL DIFF vs nib-002 snapshot: stroke terminations should show pooling dots, hairlines should feather, periodic ink depletion rhythm should be visible across lines (look for ~35 word darkness cycle)

## Risk + Rollback

**Risks:**
- Five chained filters could amplify small artifacts into visible defects — each filter must be individually toggleable for debugging
- Performance: five full-image filter passes at 400 DPI is computationally expensive; may need Rust implementation for the wicking filter (anisotropic Gaussian)
- The depletion cycle length (~35 words) requires integration with the layout engine to count words accurately

**Rollback:**
- Revert the branch; ink filters are a new module with no existing dependencies

## Evidence

- [ ] 16 tests in `tests/test_ink_filters.py` covering all 5 filters + pipeline + ink mask
- [ ] 234 total tests pass (0 failures)
- [ ] Snapshot `ink-001` visually differs from `nib-002` — ink filters produce saturation variation, pooling at stroke ends, vellum grain wicking, hairline feathering, periodic depletion cycle
