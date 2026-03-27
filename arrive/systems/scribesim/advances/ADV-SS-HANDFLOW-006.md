---
advance:
  id: ADV-SS-HANDFLOW-006
  title: Core Parameter Activation — Base Pressure and Baseline Jitter in Reviewed Guided Handflow
  system: scribesim
  primary_component: handflow
  components:
  - handflow
  - handvalidate
  - training
  started_at: 2026-03-26T00:00:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-26T00:00:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 4
  risk_flags:
  - legibility
  evidence:
  - tests:integration
  - snapshot
  status: complete
---

## Objective

Activate the first two high-value expressive controls in the reviewed guided path: `folio.base_pressure` and `glyph.baseline_jitter_mm`. These should create visible, bounded variation without collapsing glyph identity.

## Implemented Tasks

- [x] wired `folio.base_pressure` into the reviewed handflow pressure/width calculation, scoped to the reviewed lane
- [x] wired `glyph.baseline_jitter_mm` into reviewed line/session composition as a deterministic bounded per-glyph vertical offset
- [x] emitted reviewed folio metadata recording the activated parameter values used for a render
- [x] added focused proof/test coverage showing low/high parameter effects

## Validation Gates

- [x] changing `folio.base_pressure` measurably changes guided proof darkness/width while preserving exact-symbol success
- [x] changing `glyph.baseline_jitter_mm` measurably changes per-glyph vertical placement while preserving legibility
- [x] low/high parameter studies are deterministic for fixed inputs

## Risk + Rollback

Pressure and baseline offsets can easily make reviewed proofs look noisier without becoming more expressive. Keep both effects bounded and revert to the previous controller behavior if legibility or corridor gates regress.

## Evidence

- [x] before/after reviewed proof sheet for `g n`
- [x] sensitivity metrics showing non-zero output deltas for both parameters
- [x] tests proving both parameters affect the reviewed guided path

## Implementation Notes

- `folio.base_pressure` is now active only in the reviewed lane and explicit sensitivity tests; legacy curriculum paths keep prior behavior.
- `glyph.baseline_jitter_mm` is deterministic, bounded, and only applied when explicitly activated for reviewed line/session composition.
- Reviewed folio metadata now records `folio.base_pressure` and `glyph.baseline_jitter_mm` under `activated_parameters`.
- Focused verification passed with:
  - `uv run pytest tests/test_handflow.py tests/test_handflow_folio.py tests/test_scribesim_cli.py -q`
  - `uv run pytest tests/test_curriculum.py tests/test_curriculum_integration.py tests/test_handflow.py tests/test_handflow_folio.py tests/test_handvalidate_folio_bench.py tests/test_handvalidate_nominal_review.py tests/test_scribesim_cli.py -q`
- Residual failures remain in the older `word_line` curriculum promotion tests. Those are outside the reviewed-lane scope of this advance and should be handled separately if we want the broader curriculum suite green again.
