---
advance:
  id: ADV-WX-AIWEATHER-001
  title: AI Weathering Execution — Sequential Gathering-Order API Pipeline
  system: weather
  primary_component: aiweather
  components:
  - aiweather
  - worddegrade
  - promptgen
  started_at: null
  started_by: null
  implementation_completed_at: null
  implementation_completed_by: null
  updated_by: null
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  - external_api
  evidence:
  - tdd:red-green
  - tests:unit
  - tests:integration
  status: planned
---

## Objective

Implement the AI weathering execution pipeline (TD-011 Parts 4 and 7). This ties together: codex map lookup → word pre-degradation → prompt generation → AI image model API call → provenance recording. Folios are processed in gathering order (f04r first, outward from damage epicenter) so that each folio's coherence context can include already-weathered adjacent pages as reference images.

## Behavioral Change

After this advance:
- `generate_gathering_order(weathering_map)` returns the canonical 34-folio sequence starting with f04r, f04v, then outward to f01r, f17v
- `weather_folio(...)` applies pre-degradation, builds the prompt with coherence context, calls the AI image model API, and writes the weathered image + provenance JSON to the output directory
- `weather_codex(...)` processes all 34 folios in gathering order; each weathered image is held in memory as a reference for subsequent folios; progress is logged per folio
- Model adapter supports at minimum `openai` (GPT-Image-1 via `openai` library); `dry_run=True` generates prompts and provenance stubs without making API calls
- Provenance JSON per folio records: folio_id, method, model, prompt (full text), seed, weathering_spec, coherence_references (list of folio_ids used as reference), timestamp
- API retry: max 3 attempts with exponential backoff (2s, 4s, 8s) on rate-limit or transient errors
- `seed` per folio is `hash((folio_id, seed_base)) % 2**32` for determinism
- On `dry_run`, all output images are copies of the pre-degraded input (no API call); provenance records `"method": "dry_run"`

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-aiweather`
- [ ] Tidy: create `weather/aiweather.py`; define `WeatheredResult` dataclass (image, prompt, spec, provenance_path); add `openai` to pyproject.toml dependencies
- [ ] Test: `generate_gathering_order` — first two items are f04r, f04v; f01r appears before f08r
- [ ] Test: `generate_gathering_order` — all 34 folio IDs present exactly once
- [ ] Test: `weather_folio` in dry_run mode — output image equals pre-degraded input; provenance JSON exists with method='dry_run'
- [ ] Test: `weather_folio` dry_run — prompt written to weather/prompts/{folio_id}_prompt.txt
- [ ] Test: provenance JSON contains all required fields (folio_id, method, model, prompt, seed, weathering_spec, coherence_references, timestamp)
- [ ] Test: seed is deterministic — two calls for the same folio_id and seed_base return the same seed integer
- [ ] Test: retry logic — mock API to fail twice then succeed; confirm 3rd call succeeds and provenance records no error
- [ ] Test: coherence context for f04v includes reference_image from f04r's weathered output
- [ ] Integration test: run `weather_codex` in dry_run mode for all 34 folios; confirm 34 provenance JSONs and 34 output images are written; confirm gathering order is respected (f04r provenance timestamp <= f04v timestamp)
- [ ] Implement: `_openai_apply_weathering(image, prompt, reference_images, seed)` — OpenAI image edit API call
- [ ] Implement: `weather_folio(folio_id, clean_image, folio_spec, word_damage_map, context, output_dir, model, seed)`
- [ ] Implement: `weather_codex(clean_images, weathering_map, word_damage_maps, output_dir, model, seed_base, dry_run)`
- [ ] Implement: `generate_gathering_order(weathering_map)` — epicenter-first ordering per TD-011 Part 4
- [ ] Implement: `_write_provenance(folio_id, result, output_dir)` — JSON serialization
- [ ] Validate: run single-folio weather on f04r in live (non-dry_run) mode; inspect weathered image for convincing aging without text alteration

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- OpenAI GPT-Image-1 API cost: each folio is one API call; 34 folios × image edit cost. Budget before running full codex
- API does not guarantee text preservation — the AI model may alter letterforms despite the instruction. Validation (AIVALIDATE-001) is the safety net, not the prompt alone
- Reference image size: passing multiple high-resolution reference images per API call may exceed payload limits. May need to downsample references before passing
- Rate limiting: sequential processing at 34 folios may hit API rate limits; backoff and resume capability is essential

**Rollback:**
- Revert the feat/weather-aiweather branch; procedural Weather pipeline (ADV-WX-COMPOSITOR-001) remains functional as fallback

## Evidence
