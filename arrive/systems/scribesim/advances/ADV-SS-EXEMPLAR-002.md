---
advance:
  id: ADV-SS-EXEMPLAR-002
  title: Exemplar Extraction + F1 Fitness Integration (TD-008 Step 4)
  system: scribesim
  primary_component: refextract
  components:
  - refextract
  - evo
  started_at: 2026-03-21T11:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T10:58:27.542751Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence:
  - tdd:red-green
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Two tightly coupled changes:

**Part A — Improved exemplar extraction** (`scribesim/refextract/exemplar.py`):
- `extract_exemplar(letter_image, target_size=(64, 64)) -> np.ndarray`: tight crop to ink bounding box (2px padding), resize preserving aspect ratio, pad to square, normalize intensity (bg=255, fg=0).
- `build_exemplar_set(letter_dir, output_dir)`: process all crops in `reference/letters/{char}/`, write normalized images to `reference/exemplars/{char}/werbeschreiben_{nnn}.png`.
- Target: 10–15 instances per letter. Letters already in `training/labeled_exemplars/` can be migrated here as a bootstrap.
- CLI: `scribesim extract-exemplars --letters reference/letters/ -o reference/exemplars/`

**Part B — Update F1 fitness function** (`scribesim/evo/fitness.py`):
- Change `_load_exemplars()` to prefer `reference/exemplars/{char}/` when available; fall back to `training/labeled_exemplars/{char}/` for backward compatibility.
- The rest of F1 (template matching correlation) is unchanged — it already works with 64×64 normalized images.
- Add `exemplar_root` parameter to `evaluate_fitness()` so callers can override the exemplar path for testing.

The net effect: F1 immediately gets sharper signal (10–15 real Bastarda instances per letter vs. the handful of rough crops in `training/labeled_exemplars/`).

## Behavioral Change

- `evaluate_fitness()` gains an optional `exemplar_root` parameter (default = auto-detect reference/ then training/).
- Exemplar loading path changes — backwards compatible.
- No changes to genome representation, rendering, or evolution loop.

## Planned Implementation Tasks

1. `scribesim/refextract/exemplar.py`: `extract_exemplar()`, `build_exemplar_set()`
2. CLI: `scribesim extract-exemplars` subcommand
3. Update `fitness.py` `_load_exemplars()` — prefer `reference/exemplars/`, fallback to `training/labeled_exemplars/`
4. Add `exemplar_root` param to `evaluate_fitness()`
5. Migrate or symlink best crops from `training/labeled_exemplars/` into `reference/exemplars/` bootstrap
6. Unit tests: exemplar normalization preserves aspect ratio; F1 loads from new path; F1 produces higher scores on real BSB crops vs. synthetic

## Risk + Rollback

- F1 scores will shift (likely improve) once new exemplars are loaded. Fitness history becomes non-comparable across the transition.
- Rollback: remove `reference/exemplars/` and F1 reverts to `training/labeled_exemplars/` automatically.

## Evidence

