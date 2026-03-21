---
advance:
  id: ADV-SS-RENDER-002
  title: Rendering Pipeline v2 — 6-Stage Integration
  system: scribesim
  primary_component: render
  components:
  - render
  - movement
  - ink
  - layout
  started_at: 2026-03-20T14:55:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T11:36:40.584601Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - breaking_change
  - public_api
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Integrate all TD-002 components into the 6-stage rendering pipeline described in TD-002 Part 5. This advance wires together the movement model, physics nib, ink-substrate filters, and cumulative imprecision into a unified pipeline that replaces the current render flow while maintaining the same output contracts (page PNG, pressure heatmap, PAGE XML).

## Behavioral Change

After this advance:
- **Stage 1 — GEOMETRY**: Page posture → ruling lines (with imprecision) → line trajectories → word envelopes → glyph trajectories (with connecting paths). Output: complete vector description of every nib position + metadata.
- **Stage 2 — RAW RENDERING**: Rasterize all nib-contact segments to coverage buffer using the physics nib model. Write metadata buffers (pressure, speed, direction, ink_load, dwell_time). Internally at 400 DPI.
- **Stage 3 — INK-SUBSTRATE FILTERS**: Apply saturation, pooling, wicking, feathering, depletion filters in sequence. Output: final ink layer (grayscale, 400 DPI).
- **Stage 4 — COMPOSITING**: Blend ink layer onto vellum substrate (ink sinks INTO vellum, interacts with texture). Downsample 400→300 DPI. Output: page image.
- **Stage 5 — GROUND TRUTH EXTRACTION**: Extract PAGE XML from Stage 1 geometry (not rendered image). Coordinates are in output (300 DPI) space.
- **Stage 6 — PRESSURE HEATMAP**: Extract from Stage 2 pressure buffer. Downsample to 300 DPI. Output: grayscale PNG.
- Output contracts are unchanged: `{folio_id}.png` (300 DPI), `{folio_id}_pressure.png`, `{folio_id}.xml` (PAGE XML 2019)
- Weather pipeline requires no changes — it consumes the same artifacts
- Internal rendering at 400 DPI with 300 DPI output provides sub-pixel anti-aliasing

## Planned Implementation Tasks

- [ ] Tidy: define the `PipelineContext` data structure that flows through all 6 stages — carries buffers, geometry, metadata, and configuration
- [ ] Tidy: refactor `render_page()` into Stage 2 only — extract geometry (Stage 1), compositing (Stage 4), and groundtruth (Stage 5) into separate stages
- [ ] Test: write integration tests — full 6-stage pipeline produces valid output for f01r; output PNG dimensions are correct (300 DPI); PAGE XML coordinates match rendered glyph positions; pressure heatmap correlates with rendered stroke darkness
- [ ] Implement: Stage 1 — geometry assembly from movement model + imprecision model, producing complete nib-position vector description
- [ ] Implement: Stage 2 — raw rendering at 400 DPI with metadata buffers; integrate physics nib model
- [ ] Implement: Stage 3 — ink-substrate filter pipeline invocation (delegates to `scribesim.ink`)
- [ ] Implement: Stage 4 — compositing with vellum substrate + 400→300 DPI downsampling (Lanczos)
- [ ] Implement: Stage 5 — ground truth extraction from Stage 1 geometry, coordinate transformation to 300 DPI output space
- [ ] Implement: Stage 6 — pressure heatmap extraction + downsampling
- [ ] Implement: update CLI to invoke the 6-stage pipeline, preserving all existing CLI interface contracts
- [ ] Validate: render f01r, f04v, f14r through the full pipeline; compare output quality against v1; verify Weather pipeline produces valid output from v2 rendering
- [ ] Checkpoint: run `./snapshot.sh render-002` (full pipeline, including weather) — VISUAL DIFF vs imprecision-001 snapshot: anti-aliasing should be smoother (400→300 downsampling), overall quality should be the best yet. Weather output should show all effects correctly applied to v2 rendering.

## Risk + Rollback

**Risks:**
- 400 DPI internal rendering doubles memory requirements — a 3307×4724 page at 400 DPI becomes ~4400×6300, requiring ~110MB per buffer
- Breaking change to the internal rendering API — all callsites must be updated
- Performance regression from multiple pipeline stages; may need profiling and optimization pass

**Rollback:**
- Revert the branch; restore the v1 rendering pipeline. Output contract is unchanged so Weather is unaffected.

## Evidence

- [ ] 11 tests in `tests/test_render_pipeline.py` covering output dimensions, modes, determinism, ink filter application, resolution scaling
- [ ] 259 total tests pass (0 failures)
- [ ] Snapshot `render-002` with weather: f01r.png (6.5M, 400→300 DPI Lanczos), f01r_weathered.png (8.3M) — full pipeline validated including downstream Weather compatibility
