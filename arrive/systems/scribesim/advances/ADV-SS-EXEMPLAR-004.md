---
advance:
  id: ADV-SS-EXEMPLAR-004
  title: Corpus Semantics — Separate Automatic Admission from Reviewable Exemplar Truth
  system: scribesim
  primary_component: refextract
  components:
  - refextract
  - training
  - handvalidate
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
  - naming
  - public_api
  evidence:
  - dataset
  - dashboard
  status: complete
---

## Objective

Rename and separate the current corpus tiers so score-threshold output is not presented as if it were confirmed readable exemplar truth.

## Planned Implementation Tasks

- [x] replace `accepted` / `soft_accepted` / `rejected` review semantics with `auto_admitted` / `quarantined` / `rejected`
- [x] update manifests, summaries, and folder names so automatic matcher output is clearly labeled
- [x] keep backward-compatible machine fields only where needed for migration, but stop using `accepted` as the review label
- [x] update documentation and dashboards to distinguish matcher admission from promoted exemplar status

## Validation Gates

- [x] no review-facing corpus artifact labels raw matcher output as confirmed exemplar truth
- [x] dashboards report automatic admission coverage separately from promoted exemplar coverage
- [x] migration keeps existing pipeline accounting readable during transition

## Risk + Rollback

This is mostly semantic hardening. If migration churn is too high, preserve compatibility fields in manifests while changing only review-facing outputs first.

## Evidence

- [x] renamed corpus manifests and directories for the active review slice
- [x] updated review summary showing separated automatic vs promoted coverage
- [x] migration notes for downstream consumers

## Implementation Notes

The corpus builder now writes review-facing `auto_admitted` / `quarantined` / `rejected` tiers, preserves legacy `accepted` / `soft_accepted` compatibility fields in manifests for downstream migration, and exposes separate automatic-admission versus promoted-exemplar coverage in summaries. Focused tests cover the renamed semantics. A full refresh of the committed long-running active-review corpus bundle should be rerun separately when convenient; this advance closes on the implemented code path and migration-safe artifacts.
