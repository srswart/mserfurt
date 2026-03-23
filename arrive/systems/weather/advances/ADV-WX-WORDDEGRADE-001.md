---
advance:
  id: ADV-WX-WORDDEGRADE-001
  title: Word-Level Pre-Degradation — CLIO-7 Annotations to Pixel Regions
  system: weather
  primary_component: worddegrade
  components:
  - worddegrade
  started_at: 2026-03-22T00:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-22T17:21:30.070180Z
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
  status: complete
---

## Objective

Implement the word-level pre-degradation pipeline (TD-011 Addendum A). Before the AI model applies surface weathering, we programmatically degrade specific words and passages at the exact pixel positions specified by CLIO-7. This ensures the scholarly damage annotation is honored precisely regardless of what the AI model decides to do. The AI then applies holistic surface weathering on top of the pre-degraded image.

## Behavioral Change

After this advance:
- `build_word_damage_map(folio_json, page_xml_path)` reads per-word confidence annotations from the XL folio JSON, finds corresponding word bounding boxes in the ScribeSim PAGE XML, and returns a list of `WordDamageEntry` objects with pixel coordinates
- `pre_degrade_text(clean_image, word_damage_map, seed)` applies opacity-based degradation to the clean image at each word's bbox:
  - `confidence == 0.0` (lacuna): erase to estimated local background — `estimate_local_background()` samples a 20px border around the bbox
  - `confidence < 0.6` (trace): fade to `confidence × 0.5` opacity (15-30%), add Gaussian pixel noise (σ=15) to simulate partial dissolution
  - `confidence < 0.8` (partial): fade to `0.5 + confidence × 0.25` opacity (50-70%)
  - `confidence >= 0.8` (clear): no modification
- Returns both the degraded image AND a degradation mask (uint8, 0=unmodified, 255=fully erased, proportional for partial)
- The specific CLIO-7 damage passages for f04r-f05v (from Addendum A §"The specific damaged passages") are handled correctly — the "stolz" entry with confidence=0.55 produces a partial fade that leaves the outer letters faintly readable while the middle is ambiguous
- Word damage map is written to `weather/text_damage/{folio_id}_word_damage.json`

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-worddegrade`
- [ ] Tidy: create `weather/worddegrade.py`; define `WordDamageEntry` dataclass (word_text, bbox, center, confidence, category, line_number, specific_note); no existing code modified
- [ ] Test: `build_word_damage_map` with minimal folio JSON (one annotated line) and matching PAGE XML returns correct WordDamageEntry with correct bbox
- [ ] Test: lacuna annotation (confidence=0.0) produces WordDamageEntry with category='lacuna'
- [ ] Test: `pre_degrade_text` on a synthetic image — lacuna region becomes background color (within 10% of sampled background)
- [ ] Test: trace region (confidence=0.4) faded to ≤30% of original ink brightness
- [ ] Test: partial region (confidence=0.7) faded to 55-75% of original ink brightness
- [ ] Test: clear region (confidence=0.9) — pixels unmodified (mask=0 in that region)
- [ ] Test: degradation mask is 255 at lacuna pixels, proportional at faded pixels, 0 at clear pixels
- [ ] Test: `estimate_local_background` returns a plausible parchment color for a typical ScribeSim page region
- [ ] Test: determinism — two calls with same seed produce identical output
- [ ] Test: f04r damage map contains at least 5 lacuna entries (matching the CLIO-7 damage vocabulary in Addendum A)
- [ ] Implement: `estimate_local_background(image, bbox, border_px=20)` — median of border pixels
- [ ] Implement: `build_word_damage_map(folio_json, page_xml_path)` — CLIO-7 → PAGE XML bridge
- [ ] Implement: `pre_degrade_text(clean_image, word_damage_map, seed)` — opacity + noise degradation
- [ ] Implement: `save_word_damage_map(word_damage_map, output_path)` — JSON serialization
- [ ] Validate: apply to f04r; visually inspect that lacunae are blank, "stolz" region is partially obscured, and surrounding clear text is unmodified

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- XL folio JSON and PAGE XML must use compatible coordinate systems and word-boundary alignment; a mismatch in how word spans are indexed between the two formats will shift damage to wrong words
- `estimate_local_background` must avoid sampling from adjacent text — if the bbox border overlaps other letters, the background estimate will be too dark, leaving visible artifacts at lacuna edges
- The AI model may attempt to "fix" obviously blank regions (lacunae) by hallucinating text — this is caught by ADV-WX-AIVALIDATE-001

**Rollback:**
- Revert the feat/weather-worddegrade branch; AIWEATHER can proceed without pre-degradation using the AI-prompt-only path, but damage precision will be lower

## Evidence

