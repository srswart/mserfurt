---
advance:
  id: "ADV-SS-INK-006"
  title: "Capillary Plateau Ink Curve & Attentive Scribe Dip Discipline"
  system: "scribesim"
  primary_component: "ink"
  components: ["ink", "render", "handflow", "handvalidate", "tests"]
  started_at: "2026-10-18T15:46:00+00:00"
  implementation_completed_at: "2026-10-18T15:52:00+00:00"
  review_time_estimate_minutes: 25
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: ["tidy:preparatory", "tdd:red-green", "tests:unit"]
  # Populated by `arrive usage import` / the LiteLLM callback — leave empty when authoring.
  model_usage: []
  status: complete
---

## Objective

Refine the quill ink depletion and dip-timing model in `scribesim` (`TD-021`) so that rendered folios exhibit a realistic capillary working plateau, a smooth sigmoid shoulder falloff (affecting thin rising hairlines before heavy downstrokes), single-owner optical depletion without double-multiplying pressure and darkness, and attentive/anticipatory scribe dipping at clause pauses, line ends, and before long words.

Follows [TD-021 — Capillary Plateau Ink Cycle & Attentive Scribe Dip Discipline](../../../../docs/tech-direction/TD-021-capillary-ink-cycle-and-attentive-dip.md).

## Behavioral Change

After this advance:
- `scribesim/ink/cycle.py` provides `smoothstep()`, `capillary_flow_curve()`, `ink_darkness_capillary()`, and `ink_width_modifier_capillary()` modeling three physical regimes: post-dip meniscus settle ($1.00 \to 0.86$), flat capillary working plateau ($0.86 \to 0.42$), and soft sigmoid shoulder ($0.42 \to 0.08$).
- `InkState.process_word_boundary()` accepts optional contextual lookahead (`word_text`, `next_word_len`, `is_line_end`, `attention`) so the scribe dips early at punctuation pauses, at line ends, and before long words ($\ge 7$ chars), and modulates dip vigilance according to `EmotionalLineState` and fatigue.
- `solve_word_coarticulation()` no longer double-applies reservoir darkness on top of mechanical contact pressure; `render_kinematic_folio()` owns the optical darkness curve and softens low-pressure hairlines first when the reservoir enters the lower shoulder.

## Component Impact

Primary component: `ink`. Impacted components: `ink`, `render`, `handflow`, `handvalidate`, `tests`.

- `scribesim/ink/cycle.py` and `scribesim/ink/__init__.py` (capillary plateau curve helpers and contextual `process_word_boundary`)
- `scribesim/render/scribe_state.py` (`KinematicScribeSession` attentive dip thresholds and `dip_attention_factor()`)
- `scribesim/handflow/coarticulate.py` (single-owner depletion and word/line lookahead passed to `process_word_boundary`)
- `scribesim/handvalidate/tier2_bench.py` (capillary plateau darkness and hairline-first shoulder softening in `render_kinematic_folio`)
- `tests/test_ink_cycle.py` and `tests/test_kinematic_state.py` (unit tests for capillary plateau flatness, anticipatory dipping, and bounded pre-dip contrast)

## Dependencies

- [ADV-SS-INK-005](ADV-SS-INK-005.md)
- [ADV-SS-STATE-002](ADV-SS-STATE-002.md)

## Planned Implementation Tasks

- [x] branch: confirm current working branch for this advance
- [x] tidy: add `smoothstep` and `ink_darkness_capillary` helpers in `scribesim/ink/cycle.py` and register `TD-021` in `system.yaml` / `ink.yaml` (no behavior change to existing callers)
- [x] test: add failing unit tests in `tests/test_ink_cycle.py` and `tests/test_kinematic_state.py` for capillary plateau flatness, punctuation/line-end/long-word anticipatory dipping, emotional attention dip modulation, and elimination of double-multiplied pressure drop
- [x] feat/fix: implement contextual `process_word_boundary()`, single-owner depletion in `coarticulate.py`, and capillary shoulder rendering in `tier2_bench.py`, and generate a before/after prototype comparison

## Bug Fixes

- [x] Eliminated double-applied reservoir darkness multiplication between `solve_word_coarticulation()` and `render_kinematic_folio()`.

## Risk + Rollback

- Risk: Altering `ink_darkness()` directly could break legacy `test_ink_cycle.py` power-curve assertions or Tier-2 `pressure_dynamic_range` gates.
- Rollback: Keep legacy `ink_darkness()` intact for TD-010 unit tests, expose `ink_darkness_capillary()` for the kinematic pipeline, and keep backward-compatible defaults on `process_word_boundary()`.

## Evidence

- [x] tidy:preparatory
- [x] tdd:red-green
- [x] tests:unit

## CI Evidence Notes

- If CI jobs are enabled, link pipeline evidence (`ci:passed`) from PR/MR and default-branch runs.
- If CI jobs are temporarily disabled, run checks externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-INK-006 --status passed` (include provider/run metadata when available)
  - Optional combined flow when provider lookup is available:
    - `arrive pr check --provider-status --advance ADV-SS-INK-006 --record-ci-evidence --json`

## Changes Made

### 2026-10-18 - docs: Author TD-021 and ADV-SS-INK-006
- `docs/tech-direction/TD-021-capillary-ink-cycle-and-attentive-dip.md`: Authored tech direction for capillary plateau ink curve and attentive scribe dip discipline.
- `arrive/systems/scribesim/advances/ADV-SS-INK-006.md`: Created advance record.

### 2026-10-18 - tidy: Add capillary plateau curve helpers and register TD-021
- `scribesim/ink/cycle.py` and `scribesim/ink/__init__.py`: Added `smoothstep()`, `capillary_flow_curve()`, `ink_darkness_capillary()`, and `ink_width_modifier_capillary()`.
- `arrive/systems/scribesim/system.yaml` and `arrive/systems/scribesim/components/ink.yaml`: Linked `TD-021`.

### 2026-10-18 - test: Add TD-021 capillary plateau and attentive dip unit tests
- `tests/test_ink_cycle.py`: Added `test_capillary_plateau_flatness_and_soft_shoulder`, `test_attentive_dip_on_punctuation_line_end_and_long_word`, and `test_attention_modulates_dip_threshold`.
- `tests/test_kinematic_state.py`: Added `test_td021_no_double_pressure_drop_and_attentive_dips`.

### 2026-10-18 - feat: Implement contextual scribe dipping, single-owner depletion, and capillary shoulder rendering
- `scribesim/ink/cycle.py`: Extended `InkState.wants_to_dip()` and `InkState.process_word_boundary()` with punctuation, line-end, long-word lookahead, and `attention` modulation.
- `scribesim/render/scribe_state.py`: Updated `KinematicScribeSession` dip thresholds (`0.36` preferred / `0.22` forced) and added `dip_attention_factor()`.
- `scribesim/handflow/coarticulate.py`: Removed double-applied `darkness_scale()` from `solve_word_coarticulation()` and passed word/line lookahead to `process_word_boundary()`.
- `scribesim/handvalidate/tier2_bench.py`: Wired `ink_darkness_capillary()`, `ink_width_modifier_capillary()`, and hairline-first shoulder softening into `render_kinematic_folio()`.

## Check for Understanding

1. Why did the pre-TD-021 kinematic folio pipeline produce a ~35–40% contrast drop before each quill dip?
2. How does `capillary_flow_curve()` in `scribesim/ink/cycle.py` separate the post-dip meniscus settle, the working capillary plateau, and the lower shoulder?
3. What four contextual signals does `InkState._evaluate_dip_trigger()` inspect at a word boundary to decide whether an attentive scribe refreshes the quill early?
