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
  - naming
  - public_api
  evidence:
  - dataset
  - dashboard
  status: proposed
---

## Objective

Rename and separate the current corpus tiers so score-threshold output is not presented as if it were confirmed readable exemplar truth.

## Planned Implementation Tasks

- [ ] replace `accepted` / `soft_accepted` / `rejected` review semantics with `auto_admitted` / `quarantined` / `rejected`
- [ ] update manifests, summaries, and folder names so automatic matcher output is clearly labeled
- [ ] keep backward-compatible machine fields only where needed for migration, but stop using `accepted` as the review label
- [ ] update documentation and dashboards to distinguish matcher admission from promoted exemplar status

## Validation Gates

- [ ] no review-facing corpus artifact labels raw matcher output as confirmed exemplar truth
- [ ] dashboards report automatic admission coverage separately from promoted exemplar coverage
- [ ] migration keeps existing pipeline accounting readable during transition

## Risk + Rollback

This is mostly semantic hardening. If migration churn is too high, preserve compatibility fields in manifests while changing only review-facing outputs first.

## Evidence

- [ ] renamed corpus manifests and directories for the active review slice
- [ ] updated review summary showing separated automatic vs promoted coverage
- [ ] migration notes for downstream consumers
