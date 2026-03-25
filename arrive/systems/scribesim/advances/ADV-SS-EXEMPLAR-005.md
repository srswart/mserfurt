---
advance:
  id: ADV-SS-EXEMPLAR-005
  title: Promoted Exemplars — Create a Reviewable Tier Above Automatic Admission
  system: scribesim
  primary_component: refextract
  components:
  - refextract
  - training
  - guides
  started_at: null
  started_by: null
  implementation_completed_at: null
  implementation_completed_by: null
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - data_quality
  evidence:
  - dataset
  - snapshot
  status: proposed
---

## Objective

Add a `promoted_exemplars` stage so only stronger, reviewable glyph and join crops become the corpus that nominal-form recovery consumes.

## Planned Implementation Tasks

- [ ] define `promoted_exemplars` storage and manifest schema distinct from automatic admission buckets
- [ ] write a promotion pass that selects the best candidate set per symbol and join from automatic tiers
- [ ] emit separate review panels for `promoted_exemplars`
- [ ] make evofit and later nominal-form stages consume only `promoted_exemplars`, not raw auto-admitted crops

## Validation Gates

- [ ] every promoted exemplar set is materially smaller and cleaner than the auto-admitted set
- [ ] promoted exemplar manifests are frozen and reproducible
- [ ] downstream nominal-form stages can point only at `promoted_exemplars`

## Risk + Rollback

If the promoted tier is too sparse initially, keep the automatic corpus for diagnosis but do not let downstream stages silently fall back to it.

## Evidence

- [ ] promoted exemplar manifest for the active review slice
- [ ] symbol-grouped contact sheet for promoted glyphs and joins
- [ ] downstream config updated to reference promoted exemplar roots
