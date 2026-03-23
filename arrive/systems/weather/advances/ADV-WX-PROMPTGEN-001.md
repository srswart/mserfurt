---
advance:
  id: ADV-WX-PROMPTGEN-001
  title: AI Weathering Prompt Generator — Codex Map to Structured Prompts
  system: weather
  primary_component: promptgen
  components:
  - promptgen
  started_at: 2026-03-22T00:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-22T17:14:31.831870Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence:
  - tdd:red-green
  - tests:unit
  status: in_progress
---

## Objective

Implement the prompt generator (TD-011 Parts 3 and Addendum A) that translates a `FolioWeatherSpec` into a structured text prompt for the AI image model. The generator handles both physical damage description (vellum, ink aging, edge darkening, water, corner, foxing) and word-level text degradation from the Addendum A `WordDamageEntry` list. It also builds the coherence context (adjacent folio descriptions and reference images) to anchor each folio's weathering to its neighbors.

## Behavioral Change

After this advance:
- `generate_weathering_prompt(folio_spec, context, word_damage_map, ...)` returns a complete structured text prompt
- Prompt always opens with the preservation instruction — "Do NOT alter, move, or regenerate any text or letterforms"
- Prompt sections appear in canonical order: base → vellum stock → ink aging → edge darkening → water damage (if present) → missing corner (if present) → foxing spots (if present) → text degradation (word-level, if word_damage_map provided) → coherence context (if adjacent_folios present)
- Water damage description uses 'severe'/'moderate'/'light' vocabulary based on severity thresholds (>0.7 / >0.3 / ≤0.3)
- Word-level degradation groups words into LEGIBLE / PARTIALLY_LEGIBLE / BARELY_LEGIBLE / COMPLETELY_LOST with per-word position percentages
- `build_coherence_context(folio_id, weathering_map, weathered_so_far)` identifies same-leaf partner and facing page, attaches reference images for already-weathered folios
- Prompts are written to `weather/prompts/{folio_id}_prompt.txt` during codex processing
- `summarize_weathering(spec)` returns a one-line description for use in coherence context ("moderate water damage from top-right, 2 foxing spots")

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-promptgen`
- [ ] Tidy: create `weather/promptgen.py`; no existing code modified
- [ ] Test: f01r prompt contains preservation instruction and "standard calfskin parchment"
- [ ] Test: f01r prompt does NOT contain water damage, missing corner, or text degradation sections
- [ ] Test: f04r prompt contains 'severe' water damage from 'top_right' with penetration 60%
- [ ] Test: f04v prompt contains missing corner at 'bottom_right'
- [ ] Test: prompt section order — preservation instruction is always the first sentence
- [ ] Test: word-level degradation — a lacuna entry at (65%, 72%) produces "no ink whatsoever" instruction at those coordinates
- [ ] Test: word-level degradation — partial word (confidence=0.55, 'stolz') produces "partially obscure" with ambiguous middle letters instruction
- [ ] Test: `build_coherence_context('f04v', map)` identifies f04r (same-leaf recto) and f05r (facing page)
- [ ] Test: coherence context includes reference_image only when that folio is in weathered_so_far
- [ ] Test: `summarize_weathering` returns a non-empty string for any spec
- [ ] Implement: `generate_weathering_prompt(folio_spec, context, word_damage_map, page_width, page_height)`
- [ ] Implement: `generate_text_degradation_prompt(word_damage_map, page_width, page_height)` (per Addendum A)
- [ ] Implement: `build_coherence_context(folio_id, weathering_map, weathered_so_far)`
- [ ] Implement: `summarize_weathering(spec)` — one-line summary for coherence descriptions
- [ ] Validate: generate prompts for f04r, f04v, f01r, f14r; read each and verify they describe the correct physical reality for those folios

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- Prompt quality directly determines AI output quality — if the preservation instruction is ambiguous or the damage descriptions are imprecise, the AI model may alter text or apply the wrong damage pattern
- Word-level position percentages must be computed from actual page_width/page_height of the rendered image; getting these wrong produces spatially displaced degradation instructions

**Rollback:**
- Revert the feat/weather-promptgen branch; no existing code modified; AIWEATHER is blocked until this is complete

## Evidence

