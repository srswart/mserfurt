---
advance:
  id: ADV-WX-CODEXMAP-001
  title: Codex Weathering Map — Physical Damage Propagation Model
  system: weather
  primary_component: codexmap
  components:
  - codexmap
  started_at: null
  started_by: null
  implementation_completed_at: null
  implementation_completed_by: null
  updated_by: null
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence:
  - tdd:red-green
  - tests:unit
  status: planned
---

## Objective

Implement the physical damage propagation model (TD-011 Part 2) that computes a complete, deterministic per-folio weathering specification for all 34 pages of the gathering. The output `codex_map.json` is the authoritative source of truth for what damage appears where — consumed by every downstream AI weathering component.

## Behavioral Change

After this advance:
- `compute_codex_weathering_map()` generates a JSON-serialisable dict with one entry per folio (f01r through f17v)
- Water damage propagates from f04r with exact severity: f04r=1.0, f04v=0.85, adjacent leaves decay by 0.4 per leaf, folios beyond 3 leaves receive negligible damage (<0.03)
- Missing corner appears only on f04r (bottom-left) and f04v (bottom-right, mirrored), with depth 8% and width 7% of page
- Edge darkening is universal; f01 and f17 receive severity 0.9, inner folios scale down linearly to 0.6
- Five foxing clusters are generated at seed-determined positions, each spanning 2-4 adjacent leaves with mirrored verso positions
- Vellum stock is 'irregular' for folios 14-17, 'standard' for 1-13
- CLIO-7 per-folio annotations (confidence zones) are merged into the spec when provided
- Output is byte-identical for a given seed (default 1457)
- `codex_map.json` is written to `weather/codex_map.json`

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-codexmap`
- [ ] Tidy: create `weather/codexmap.py` module; define `FolioWeatherSpec` dataclass and `generate_foxing_clusters` helper; no existing code modified
- [ ] Test: `compute_water_propagation(folio_num=4, side='r')` returns 1.0 (source)
- [ ] Test: `compute_water_propagation(folio_num=4, side='v')` returns 0.85
- [ ] Test: `compute_water_propagation(folio_num=3, side='v')` returns 0.40 (one leaf away, facing f04r)
- [ ] Test: `compute_water_propagation(folio_num=2, side='v')` returns ~0.06 (three leaves away)
- [ ] Test: `compute_water_propagation(folio_num=8, side='r')` returns 0.0 / below threshold (no damage)
- [ ] Test: missing corner present only on f04r and f04v; f03v has no missing corner
- [ ] Test: f04r missing corner is 'bottom_left', f04v is 'bottom_right'
- [ ] Test: vellum stock: f13v='standard', f14r='irregular'
- [ ] Test: edge darkening: f01r >= 0.85, inner folio <= 0.7
- [ ] Test: foxing clusters — verify recto position (cx, cy) appears mirrored as (1-cx, cy) on verso
- [ ] Test: determinism — two calls with seed=1457 return identical output
- [ ] Test: CLIO-7 merge — providing clio7_annotations for f04r sets 'text_degradation' zones
- [ ] Implement: `compute_water_propagation(folio_num, side, source_folio=4, source_side='r', source_severity=1.0)`
- [ ] Implement: `compute_edge_darkening(folio_num, gathering_size)` — linear scale, outermost=0.9
- [ ] Implement: `generate_foxing_clusters(n_clusters, gathering_size, seed)` — seeded random
- [ ] Implement: `compute_codex_weathering_map(gathering_size, clio7_annotations, seed)` — assembles all specs
- [ ] Implement: CLI helper `save_codex_map(map, output_path)` — JSON serialization
- [ ] Validate: generate map for gathering_size=17 and manually inspect f04r, f04v, f01r, f14r entries against TD-011 example JSON

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- Propagation formula is pure physics — low risk of errors, but the decay_rate=0.4 constant is specified in TD-011 and should not be changed without a tech direction amendment
- Foxing cluster seeding must be consistent: if the seed changes, all foxing positions change across all folios, breaking visual coherence of the codex

**Rollback:**
- Revert the feat/weather-codexmap branch; no downstream components exist yet; no existing code is modified

## Evidence
