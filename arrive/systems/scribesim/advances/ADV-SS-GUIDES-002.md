---
advance:
  id: "ADV-SS-GUIDES-002"
  title: "Full Bastarda Via-Point Alphabet & Contextual Allographs"
  system: "scribesim"
  primary_component: "guides"
  components: ["guides", "handflow", "handvalidate", "tests"]
  started_at: "2026-10-16T04:45:00+00:00"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  # Populated by `arrive usage import` / the LiteLLM callback — leave empty when authoring.
  model_usage: []
  status: planned
---

## Objective

Expand the nib-normalized `ViaPointRecipe` catalog from the 7 starter letters to the complete Early New High German / Ecclesiastical Latin Bastarda inventory required by the MS Erfurt corpus, including contextual allograph variants (`TD-012`) and automated topological counter verification (`A4-TOPOLOGY`).

Follows [TD-019 — Kinematic Coarticulation, Bastarda Proportions, and Hybrid Evaluation](../../../../docs/tech-direction/TD-019-kinematic-coarticulation-and-evaluation.md) (§2 Pillar 2, §4 Tier 1 `A4-TOPOLOGY`, §5 Phase 16b).

## Behavioral Change

After this advance:
- The `ViaPointRecipe` catalog covers all lowercase (`a–z`), Bastarda special forms (long `ſ`, `ß`/`ſz`, superscript-`e` umlauts `ä, ö, ü`, Tironian `⁊`, nasal bar, punctuation, `✦` divider), and simplified Bastarda capitals (`A–Z`).
- Contextual allograph selection chooses position- and neighbor-appropriate via-point variants (e.g., initial/medial `ſ` vs. word-final round `s`, context-aware entry heights for `e`, `r`, `o`, `a`, `d`, `g`) before solving the word's global minimum-jerk trajectory.
- Exact character coverage is $1.0$ across all MS Erfurt proof lines and folios (zero silent alias substitutions), and Tier-1 `A4-TOPOLOGY` automatically verifies open counters in `a, o, d, e, g, b, p` and zero unintended non-adjacent glyph collisions.

## Component Impact

Primary component: `guides`. Impacted components: `guides`, `handflow`, `handvalidate`, `tests`.

- `scribesim/guides/viapoint_catalog.py` (complete Bastarda via-point inventory and contextual allograph selector)
- `scribesim/handflow/coarticulate.py` (support for multi-stroke lifts, diacritics, and superscript-`e` placement within word plans)
- `scribesim/handvalidate/kinematic_gates.py` (Tier-1 `A4-TOPOLOGY` counter Euler-number and collision verifier)
- `tests/test_viapoint_catalog.py` (coverage, allograph selection, and `A4-TOPOLOGY` tests)

## Dependencies

- [ADV-SS-ANNOTATE-007](ADV-SS-ANNOTATE-007.md)
- [ADV-SS-HANDFLOW-012](ADV-SS-HANDFLOW-012.md)

## Planned Implementation Tasks

- [ ] branch: create or confirm feature branch for this advance
- [ ] tidy: organize via-point recipe builders by calligraphic family (minims, bowls, ascender loops, descenders, capitals, marks)
- [ ] test: add failing unit tests for 100% corpus character coverage (zero aliases), contextual `ſ`/`s` and neighbor-variant selection, and `A4-TOPOLOGY` open-counter preservation
- [ ] feat/fix: implement complete Bastarda `ViaPointRecipe` catalog, contextual allograph selector, and `A4-TOPOLOGY` gate

## Bug Fixes

- [ ] None yet

## Risk + Rollback

- Risk: Complex multi-stroke or looped letters (`d, g, a, ß`) can collapse their interior counters if via-point tolerances $\Sigma_k$ are too wide relative to $w_{\text{nib}} = 0.83\text{ mm}$. Mitigate with explicit apex/bowl via-points and automated `A4-TOPOLOGY` counter checks.
- Rollback: Revert `scribesim/guides/viapoint_catalog.py`; earlier glyph catalogs remain untouched.

## Evidence

- [ ] tidy:preparatory
- [ ] tdd:red-green
- [ ] tests:unit

## CI Evidence Notes

- If CI jobs are enabled, link pipeline evidence (`ci:passed`) from PR/MR and default-branch runs.
- If CI jobs are temporarily disabled, run checks externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-GUIDES-002 --status passed` (include provider/run metadata when available)
  - Optional combined flow when provider lookup is available:
    - `arrive pr check --provider-status --advance ADV-SS-GUIDES-002 --record-ci-evidence --json`

## Changes Made

### 2026-10-16 - docs: Draft ADV-SS-GUIDES-002 for TD-019 Pass 16b
- `arrive/systems/scribesim/advances/ADV-SS-GUIDES-002.md`: Created planned advance record for the full Bastarda via-point alphabet and contextual allographs.
