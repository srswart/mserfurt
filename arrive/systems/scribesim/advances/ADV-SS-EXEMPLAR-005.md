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
  started_at: 2026-03-25T00:00:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-25T00:00:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 3
  risk_flags:
  - data_quality
  evidence:
  - dataset
  - snapshot
  status: complete
---

## Objective

Add a `promoted_exemplars` stage so only stronger, reviewable glyph and join crops become the corpus that nominal-form recovery consumes.

## Planned Implementation Tasks

- [x] define `promoted_exemplars` storage and manifest schema distinct from automatic admission buckets
- [x] write a promotion pass that selects the best candidate set per symbol and join from automatic tiers
- [x] emit separate review panels for `promoted_exemplars`
- [x] make evofit and later nominal-form stages consume only `promoted_exemplars`, not raw auto-admitted crops

## Validation Gates

- [x] every promoted exemplar set is materially smaller and cleaner than the auto-admitted set
- [x] promoted exemplar manifests are frozen and reproducible
- [x] downstream nominal-form stages can point only at `promoted_exemplars`

## Risk + Rollback

If the promoted tier is too sparse initially, keep the automatic corpus for diagnosis but do not let downstream stages silently fall back to it.

## Evidence

- [x] promoted exemplar manifest for the active review slice
- [x] symbol-grouped contact sheet for promoted glyphs and joins
- [x] downstream config updated to reference promoted exemplar roots

## Implementation Notes

The corpus builder now writes a separate `promoted_exemplars` tier, emits `promoted_manifest.toml` plus dedicated promoted glyph/join panels, and keeps evofit pointed at the promoted manifest by default. The current promoted selection is intentionally conservative and deterministic: it takes the top non-coverage-promoted `auto_admitted` candidate per symbol or join, which is enough to decouple downstream nominal-form recovery from raw matcher buckets while stronger promotion gates are still being implemented in later advances. Focused exemplar/evofit/CLI tests cover the new manifest contract and default consumer behavior.
