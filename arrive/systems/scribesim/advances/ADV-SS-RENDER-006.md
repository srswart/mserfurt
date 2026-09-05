---
advance:
  id: "ADV-SS-RENDER-006"
  title: "Konrad Folio Candidate — Guided CLI and Trajectory-Based Exports"
  system: "scribesim"
  primary_component: "render"
  components: ["render", "cli", "handflow", "layout", "groundtruth", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Integrate the G3-passing hand as an explicit opt-in guided folio candidate with exact text accounting and outputs derived from the actual rendered trajectory.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
This is a planned outcome record. The timestamp records drafting; implementation
has not started and no execution, CI or owner approval is claimed.

## Behavioral Change

After implementation: An explicit repertoire and seed select the guided path, with no backend fallback. Folio images, pressure maps and PAGE XML refer to the same positioned ink and input text; unsupported characters and overflow are reported before incomplete output is accepted.

## Component Impact

Primary component: `render`. Impacted components:
`render`, `cli`, `handflow`, `layout`, `groundtruth`, `tests`.

Planned paths (new modules and commands are not available yet):

- scribesim/cli.py (explicit repertoire/seed and hand-proof dispatch)
- scribesim/handflow/folio.py and existing guided layout/session integration
- scribesim/groundtruth/page_xml.py (actual-trajectory ownership export integration)
- tests/test_repertoire_folio.py (new); focused ARRIVE test selector coverage

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-HANDVALIDATE-009](ADV-SS-HANDVALIDATE-009.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [ ] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [ ] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [ ] test: establish failing behavioral tests for the contracts below before implementation.
- [ ] feat/evaluate: Require matching G3 evidence for candidate folio use; wire proposed hand-proof and guided repertoire/seed options with backend/model provenance.
- [ ] feat/evaluate: Expand and validate exact inventory for f01r/f06r/f07r/f14r using the frozen recovery process; if new fitting is required, return the changed model through G1–G3.
- [ ] feat/evaluate: Resolve hand-note and sitting boundaries from current XL data/configuration rather than hardcoded historical line numbers.
- [ ] feat/evaluate: Preserve persistent state through line placement and reject missing forms, clipping, line truncation or overflow with actionable diagnostics.
- [ ] feat/evaluate: Co-generate PNG, pressure map and PAGE XML from actual positioned trajectory plus ownership sidecar, including explicit shared ink for supported multi-character forms.
- [ ] feat/evaluate: Keep existing defaults and input/Weather contracts compatible; implement neutral fixture coverage before running the four-folio evaluation.
- [ ] feat/evaluate: Split CLI/layout and export follow-up work if the concrete change exceeds the review estimate; keep this Advance open until all contract obligations are met.
- [ ] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] No implicit plain/evo fallback; every output declares backend, repertoire/configuration hashes and seed.
- [ ] Every source character and line is accounted for; missing inventory and overflow fail rather than silently omitting text.
- [ ] Image, pressure and XML dimensions/coordinates agree and glyph ownership reflects actual ink, with shared-stroke semantics validated.
- [ ] Existing CLI/default-renderer behavior remains compatible; candidate folios remain opt-in pending G4.

Focused validation: Use deterministic small folio fixtures with overflow, missing symbols, multi-line state, exact diacritics and shared ownership. Raster-check exported regions against actual painted ink and validate pressure dimensions/DPI and XML transcription.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: Folio assembly can truncate text or export geometry from nominal guides while painting different ink. Preserve input accounting and derive exports from the actual trajectory; block unsupported attribution.

Rollback: Select the existing evo renderer and prior assets/output directory; retain candidate bundles without replacing production output.

Review estimate: 40 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Pending implementation; none of these evidence types is claimed as completed.

- [ ] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [ ] `tdd:red-green`: capture focused failing and passing test commands and results.
- [ ] documented reproducible hand-proof and opt-in folio commands
- [ ] CLI dispatch/coverage/overflow/ownership integration results
- [ ] candidate folio images, maps, XML and provenance sidecars
- [ ] Record local integration checks separately from provider CI and owner review.
- [ ] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

None implemented in this planning change. Record scoped defects and their
regressions here during execution; do not imply unrelated renderer defects are fixed.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. What prevents folio layout from silently dropping input lines or unsupported letters?
2. How is shared ink attributed without inventing pixel-accurate independent glyph shapes?

