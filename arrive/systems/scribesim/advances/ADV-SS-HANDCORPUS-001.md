---
advance:
  id: ADV-SS-HANDCORPUS-001
  title: Bastarda Training Corpus — CATMuS Filter, Anchor-Hand Freeze, Charset Gates
  system: scribesim
  primary_component: handcorpus
  components:
  - handcorpus
  - refselect
  - refextract
  - annotate
  started_at: 2026-07-03T14:00:00Z
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Assemble the two-tier training corpus for TD-018 learned scribal hand synthesis
([TD-018](../../../../docs/tech-direction/TD-018-learned-scribal-hand.md) §2.3):

- **Tier 1 (script family):** filter CATMuS Medieval (HF `CATMuS/medieval`) to
  cursiva/bastarda/hybrida script families, 14th–16th century, German + Latin,
  producing transcribed line images with per-line provenance metadata.
- **Tier 2 (anchor hand):** freeze a reviewed line/word corpus from the selected
  BSB anchor manuscript using the existing TD-009 `refselect` harvest and the
  TD-014 annotation workbench (`shared/training/scribehand/anchor_v1`).
- **Charset contract:** build and validate the XL→training charset normalization
  table (MUFI-aligned); unmappable characters fail loudly (no silent aliasing,
  per the TD-014 exact-character-coverage lesson).

## Behavioral Change

After this advance:
- `scribesim build-scribehand-corpus` produces a manifest of image/transcription
  pairs with tier, split (train/val/held-out), and provenance for every sample.
- Corpus gates report charset coverage against the full XL folio-JSON character
  inventory and fail on gaps.
- The anchor-hand corpus (target 300–1,000 reviewed pairs) is frozen with
  IIIF shelfmark/canvas provenance retained.

## Planned Implementation Tasks

- [ ] branch: create or confirm feature branch for this advance
- [ ] tidy: extract shared segmentation/transcription helpers needed from refextract without behavior change
- [ ] test: corpus manifest schema tests; charset-coverage gate tests (red first)
- [ ] feat: CATMuS filter/download tooling (HF datasets), tier manifests, split assignment
- [ ] feat: anchor-hand freeze from reviewed workbench exports into `shared/training/scribehand/anchor_v1`
- [ ] feat: charset normalization table + validation gate wired into corpus build

## Bug Fixes

- [ ] None yet

## Risk + Rollback

- Risk: CATMuS Bastarda/German subset may be smaller than estimated, weakening the
  script prior; mitigate by widening to all cursiva-family lines and adding TRIDIS.
- Risk: new heavy dependencies (`datasets`, `torch`) enter the dev environment;
  keep them in an optional dependency group so the base pipeline stays lean.
- Rollback: corpus artifacts are additive (new directories + manifests); delete
  `shared/training/scribehand/` and the optional dependency group.

## Evidence

- [ ] tidy:preparatory
- [ ] tdd:red-green
- [ ] tests:unit
- [ ] docs:updated (corpus manifest + license/provenance notes)

## CI Evidence Notes

- CI jobs are currently disabled; run externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-HANDCORPUS-001 --status passed`

## Changes Made

(none yet)
