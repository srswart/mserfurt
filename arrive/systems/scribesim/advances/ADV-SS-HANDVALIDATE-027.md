---
advance:
  id: "ADV-SS-HANDVALIDATE-027"
  title: "Automated HTR/Distribution Bench & 4-Folio Human Sign-Off"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "groundtruth", "cli", "tests"]
  started_at: "2026-10-16T04:45:00+00:00"
  implementation_completed_at: 2026-10-16T19:29:16.407004Z
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

Implement the complete Tier-2 automated evaluation suite (`B1-HTR-CER`, `B2-ANGLE-EMD`, `B3-RHYTHM-ACF`, `B4-CONTRACTS`), co-generate exact PAGE XML (`TD-001-C`) and pressure heatmaps (`TD-001-F`) from the rendered kinematic trajectories across the 4 representative proof folios (`f01r`, `f06r`, `f07r`, `f14r`), and capture **Human Checkpoint #3** for default renderer promotion.

Follows [TD-019 — Kinematic Coarticulation, Bastarda Proportions, and Hybrid Evaluation](../../../../docs/tech-direction/TD-019-kinematic-coarticulation-and-evaluation.md) (§4 Tier 2 & Tier 3, §5 Phase 16c).

## Behavioral Change

After this advance:
- `scribesim render <folio_json> --approach kinematic` renders complete 300 DPI folios, pressure heatmaps, and glyph/word-accurate PAGE XML derived from the actual coarticulated trajectory.
- `scribesim validate-kinematic` runs all Tier-1 (`A1–A5`) and Tier-2 (`B1-HTR-CER` $\le 0.05$ on clean folios, `B2-ANGLE-EMD` stroke orientation match, `B3-RHYTHM-ACF` minim spacing autocorrelation, and `B4-CONTRACTS` PAGE XML IoU $\ge 0.95$ + `Weather` dry-run) checks automatically.
- Owner sign-off on `f01r`, `f06r`, `f07r`, and `f14r` via `scribesim review-sheet` (**Human Checkpoint #3**, saved to `shared/training/reviews/checkpoint-3-folios.json`) promotes the kinematic hand model.

## Component Impact

Primary component: `handvalidate`. Impacted components: `handvalidate`, `groundtruth`, `cli`, `tests`.

- `scribesim/handvalidate/tier2_bench.py` (`B1-HTR-CER`, `B2-ANGLE-EMD`, `B3-RHYTHM-ACF`, and `B4-CONTRACTS` automated bench)
- `scribesim/groundtruth/page_xml.py` (trajectory-owned glyph/word bounding polygon and Kraken baseline emission for `--approach kinematic`)
- `scribesim/cli.py` (`--approach kinematic` folio dispatch and `validate-kinematic` subcommand)
- `tests/test_tier2_bench.py` (integration tests for Tier-2 gates, PAGE XML IoU, and Weather contract compatibility)

## Dependencies

- [ADV-SS-STATE-002](ADV-SS-STATE-002.md)
- [ADV-SS-ANNOTATE-007](ADV-SS-ANNOTATE-007.md)

## Planned Implementation Tasks

- [ ] branch: create or confirm feature branch for this advance
- [ ] tidy: extract shared orientation-histogram and projection-autocorrelation helpers in `scribesim/metrics/` (no behavior change)
- [ ] test: add failing integration tests for `B1-HTR-CER`, `B2-ANGLE-EMD`, `B3-RHYTHM-ACF`, `B4-CONTRACTS` (PAGE XML IoU $\ge 0.95$, heatmap range, Weather dry-run), and `--approach kinematic` CLI rendering
- [ ] feat/fix: implement `scribesim/handvalidate/tier2_bench.py`, wire `--approach kinematic` full-folio export, and run the 4-folio benchmark (`f01r`, `f06r`, `f07r`, `f14r`)
- [ ] review: capture owner visual review for **Human Checkpoint #3** (4 proof folios) in `shared/training/reviews/checkpoint-3-folios.json`

## Bug Fixes

- [ ] None yet

## Risk + Rollback

- Risk: Coarticulated joins share ink between adjacent letters, which could inflate naive bounding boxes in PAGE XML. Mitigate by splitting shared join ownership at the velocity minimum / inflection midpoint between adjacent letter via-points so glyph polygons partition cleanly with IoU $\ge 0.95$.
- Rollback: Keep `--approach evo` as the fallback CLI flag while retaining all benchmark reports.

## Evidence

- [ ] tidy:preparatory
- [ ] tdd:red-green
- [ ] tests:integration
- [ ] review:owner

## CI Evidence Notes

- If CI jobs are enabled, link pipeline evidence (`ci:passed`) from PR/MR and default-branch runs.
- If CI jobs are temporarily disabled, run checks externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-HANDVALIDATE-027 --status passed` (include provider/run metadata when available)
  - Optional combined flow when provider lookup is available:
    - `arrive pr check --provider-status --advance ADV-SS-HANDVALIDATE-027 --record-ci-evidence --json`

## Changes Made

### 2026-10-16 - docs: Draft ADV-SS-HANDVALIDATE-027 for TD-019 Pass 16c
- `arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-027.md`: Created planned advance record for Automated HTR/Distribution Bench and 4-Folio Human Sign-Off.
