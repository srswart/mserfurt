---
advance:
  id: ADV-SS-PATHGUIDE-001
  title: Dense Path Guide Schema — Corridor-Based Nominal Paths
  system: scribesim
  primary_component: pathguide
  components:
  - pathguide
  - guides
  - training
  started_at: 2026-03-24T12:20:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T12:45:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - public_api
  evidence:
  - tidy:preparatory
  - tdd:red-green
  - tests:unit
  status: complete
---

## Objective

Define the new dense path representation used by TD-014. Replace sparse freeform target chasing with a `DensePathGuide` schema that captures centerline geometry, corridor width, contact schedule, nominal speed, nominal pressure, and entry/exit tangents for glyphs and joins. The schema must support automatic-first ingestion from extracted traces while preserving provenance, confidence tier, and source-resolution metadata.

## Behavioral Change

After this advance:
- hand-model planning has a concrete nominal path to follow
- joins can be represented as first-class assets rather than inferred lifts
- later controller work can measure “inside corridor” versus “outside corridor”

## Planned Implementation Tasks

- [ ] Define `DensePathGuide` schema and serialization format
- [ ] Define `GuideSample` structure: `(x, y, tangent, contact, speed_nominal, pressure_nominal, corridor_half_width)`
- [ ] Define guide manifest metadata: source crops, extraction run, confidence tier, source resolution, held-out split
- [ ] Implement importers from existing extracted guides / trace outputs
- [ ] Implement exporters to JSON/TOML for checkpointed guide assets
- [ ] Support both glyph guides and join guides in one catalog
- [ ] Normalize imported guides into physical coordinates (`mm`, x-height-relative units) while preserving native-resolution source metadata
- [ ] Add confidence-tier handling: accepted, soft accepted, rejected
- [ ] Add validation rules: monotonic sample ordering, finite `x_advance`, dense-enough sample spacing, no accidental self-intersection
- [ ] Build starter proof assets for `u`, `n`, `d`, `e`, `r` and joins `u→n`, `n→d`, `d→e`, `e→r`

## Risk + Rollback

New public representation. If it proves too rigid, keep it as an internal experimental schema and leave the current renderers unchanged. Main risk is silently admitting poor automatic samples; rollback is to quarantine them and rebuild manifests without changing controller code.

## Evidence

- [ ] `tests:unit` for serialization, validation, and sample-density checks
- [ ] fixture guides for proof glyphs and joins committed under shared assets
- [ ] manifest example showing accepted / soft / rejected provenance entries
- [ ] one rendered overlay image per proof guide showing centerline and corridor
