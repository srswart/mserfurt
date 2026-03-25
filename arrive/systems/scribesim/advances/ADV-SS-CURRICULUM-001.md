---
advance:
  id: ADV-SS-CURRICULUM-001
  title: Primitive Curriculum — Strokes, Minims, and Contact/Lift Control
  system: scribesim
  primary_component: curriculum
  components:
  - curriculum
  - handflow
  - handvalidate
  started_at: 2026-03-24T13:47:51Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T13:47:51Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence:
  - tests:integration
  - snapshot
  status: complete
---

## Objective

Train and validate the controller at the primitive level before any alphabet work. This stage establishes stable contact control, lift behavior, and corridor tracking on the smallest units that matter.

## Behavioral Change

After this advance:
- the guided controller has a frozen primitive checkpoint
- later glyph training consumes a known-good primitive basis instead of tuning everything at once

## Planned Implementation Tasks

- [x] Build primitive training manifests for downstroke, upstroke, bowl arc, ascender loop, pen lift, minim pair
- [x] Ensure primitive promotion manifests use accepted-tier samples only; soft-tier data allowed only in explicitly labeled exploratory runs
- [x] Train or tune controller and rendering parameters against these manifests
- [x] Freeze checkpoint `primitive-v1` on gate pass
- [x] Reject promotion if any hard gate fails
- [x] Save proof snapshots and metric reports under the curriculum output tree

## Validation Gates

- [x] corridor containment >= 0.98
- [x] self intersections = 0
- [x] contact/lift accuracy >= 0.99
- [x] width-profile error <= 0.15 normalized

## Risk + Rollback

No runtime rollout. Failure simply prevents curriculum promotion.

## Evidence

- [x] stage manifest committed
- [x] dataset admission summary committed with accepted / soft / rejected counts
- [x] checkpoint metadata for `primitive-v1`
- [x] snapshot panel for all primitive exercises
