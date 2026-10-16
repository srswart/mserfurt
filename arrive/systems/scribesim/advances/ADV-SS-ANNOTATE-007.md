---
advance:
  id: "ADV-SS-ANNOTATE-007"
  title: "Human-Eyes Review Board & Checkpoint #1 (Core Coarticulation)"
  system: "scribesim"
  primary_component: "annotate"
  components: ["annotate", "handvalidate", "cli", "tests"]
  started_at: "2026-10-16T04:45:00+00:00"
  implementation_completed_at: 2026-10-16T18:41:30.728354Z
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tidy:preparatory", "tdd:red-green", "tests:unit", "review:owner"]
  # Populated by `arrive usage import` / the LiteLLM callback — leave empty when authoring.
  model_usage: []
  status: complete
---

## Objective

Build the structured Human-Eyes Review Board (`scribesim review-sheet`) in the annotation workbench to capture high-signal visual judgments and parameter-mapped diagnostic quick-tags, and record **Human Checkpoint #1** on the core coarticulated letters and words (`n, u, m, nu, nm, um, und, der, mir`).

Follows [TD-019 — Kinematic Coarticulation, Bastarda Proportions, and Hybrid Evaluation](../../../../docs/tech-direction/TD-019-kinematic-coarticulation-and-evaluation.md) (§4 Tier 3 Structured Human-Eyes Checkpoints).

## Behavioral Change

After this advance:
- `scribesim review-sheet --stage <stage_id>` generates an interactive equal-scale 3-way comparison board showing:
  1. Real BSB manuscript reference word/line crops at matched x-height scale,
  2. Previous baseline render (1:1 physical scale + 3× detail loupe),
  3. Current candidate render (1:1 physical scale + toggleable kinematic via-point/nib overlay),
  4. Automated Tier-1 metric badges (`A1-PROPORTION`, `A2-KINEMATICS`, `A3-COARTICULATE`).
- The human reviewer answers a concise 4-question rubric (`Join & Ductus Flow`, `Bastarda Script Identity`, `Organic Hand Variation`, `Overall Stage Verdict`) with single-click status (`pass` / `revise` / `reject`) and actionable quick-tags (`bridge_too_flat`, `abrupt_shoulder`, `too_wide_gap`, `nib_too_thin`, `missing_foot_turn`, etc.).
- Submitting the form writes a machine-readable review record (`shared/training/reviews/<stage_id>-review.json`) that maps any selected quick-tags to concrete parameter adjustment suggestions and gates downstream stage promotion in `handvalidate`.

## Component Impact

Primary component: `annotate`. Impacted components: `annotate`, `handvalidate`, `cli`, `tests`.

- `scribesim/annotate/review_board.py` (HTML/HTTP review board generator, 4-question rubric schema, and quick-tag-to-parameter mapper)
- `scribesim/handvalidate/review_gate.py` (validator for saved Tier-3 human review JSONs)
- `scribesim/cli.py` (`scribesim review-sheet` subcommand)
- `tests/test_review_board.py` (unit tests for board generation, quick-tag parameter mapping, and review JSON validation)

## Dependencies

- [ADV-SS-HANDFLOW-012](ADV-SS-HANDFLOW-012.md)
- [ADV-SS-ANNOTATE-002](ADV-SS-ANNOTATE-002.md)

## Planned Implementation Tasks

- [x] branch: create or confirm feature branch for this advance (`feat/adv-ss-annotate-007`)
- [x] tidy: preparatory extraction of shared workbench HTTP/static-asset helpers in `scribesim/annotate/` (no behavior change)
- [x] test: add failing unit tests for 3-way review sheet generation, 4-question rubric serialization, quick-tag parameter recommendation mapping, and `review_gate` verification
- [x] feat/fix: implement `scribesim/annotate/review_board.py`, `scribesim/handvalidate/review_gate.py`, and `scribesim review-sheet` CLI
- [x] review: capture owner visual review for **Human Checkpoint #1** (`n, u, m, nu, nm, um, und, der, mir`) in `shared/training/reviews/checkpoint-1-coarticulation-review.json` (`promote_checkpoint`, candidate `c80eb01f74839ef71cbc952fc49a173f92871a045167ea829d394ffac9fceab1`)

## Bug Fixes

- [x] Connected consecutive quad vertices `(prev_hx_px, prev_hy_px)` across curved segments in `scribesim/render/sandbox.py` and separated top-arch overturns (`n`, `m`) from baseline underturns (`u`) in `scribesim/guides/viapoint.py` so ribbon renders are seamless and distinct.

## Risk + Rollback

- Risk: Human review UI could become cumbersome if it requires ranking dozens of items. Mitigate by strictly limiting the board to the 3-way comparison strip and the 4-question rubric with clickable quick-tags.
- Rollback: Revert `scribesim/annotate/review_board.py` and `scribesim/handvalidate/review_gate.py`; existing glyph annotation workbench (`workbench.py`) is unaffected.

## Evidence

- [x] tidy:preparatory
- [x] tdd:red-green
- [x] tests:unit
- [x] review:owner (`shared/training/reviews/checkpoint-1-coarticulation-review.json`)

## CI Evidence Notes

- If CI jobs are enabled, link pipeline evidence (`ci:passed`) from PR/MR and default-branch runs.
- If CI jobs are temporarily disabled, run checks externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-ANNOTATE-007 --status passed` (include provider/run metadata when available)
  - Optional combined flow when provider lookup is available:
    - `arrive pr check --provider-status --advance ADV-SS-ANNOTATE-007 --record-ci-evidence --json`

## Changes Made

### 2026-10-16 - docs: Draft ADV-SS-ANNOTATE-007 for TD-019 Pass 16a
- `arrive/systems/scribesim/advances/ADV-SS-ANNOTATE-007.md`: Created planned advance record for the Human-Eyes Review Board and Checkpoint #1.

### 2026-10-16 - tidy: add review-sheet selector and interface to annotate component
- `arrive/systems/scribesim/components/annotate.yaml`: Added `shared/training/reviews/**` selector and `scribesim review-sheet` interface.

### 2026-10-16 - test: add Human-Eyes Review Board, 4-question rubric, quick-tag mapper, and review gate tests
- `tests/test_review_board.py`: Added unit and CLI tests covering quick-tag-to-parameter mapping, Checkpoint #1 3-way board generation, `save_human_review` / `validate_human_review`, and `scribesim review-sheet`.

### 2026-10-16 - feat: implement Human-Eyes Review Board, 4-question rubric, quick-tag mapper, and review-sheet CLI
- `scribesim/annotate/review_board.py`: Implemented `build_review_sheet()`, `map_quick_tags_to_parameters()`, `RUBRIC_QUESTIONS`, and `CHECKPOINT_1_SPECIMENS`.
- `scribesim/handvalidate/review_gate.py`: Implemented `save_human_review()` and `validate_human_review()`.
- `scribesim/cli.py`: Added `scribesim review-sheet` subcommand and `__main__` entrypoint.
- `scribesim/guides/viapoint.py` & `scribesim/render/sandbox.py`: Refined top-arch vs. baseline-underturn via-points and seamless quad vertex chaining.

## Check for Understanding

1. How does `map_quick_tags_to_parameters()` translate qualitative reviewer tags (such as `too_wide_gap` or `abrupt_shoulder`) into concrete parameter adjustments in `guides` and `handflow`?
2. Why does `validate_human_review()` verify both `stage_id` and `candidate_sha256` before reporting `promoted: True`?
3. What three views are displayed side-by-side for each specimen on the `scribesim review-sheet` board?

