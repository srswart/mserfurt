---
advance:
  id: ADV-SS-INK-003
  title: Ink Darkness and Width Modulation from Reservoir Level
  system: scribesim
  primary_component: ink
  components:
  - ink
  - evo
  started_at: 2026-03-22T00:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-22T12:19:04.747989Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence:
  - tidy:preparatory
  - tdd:red-green
  - tests:unit
  status: in_progress
---

## Objective

Apply the `ink_darkness()` and `ink_width_modifier()` curves from TD-010 Parts 2.1
and 2.2 to the renderer. This is the highest-impact change: it makes the ink cycle
*visible* — dark after a fresh dip, gradually lightening, then dark again. Every
rendered stroke now has darkness and width that are functions of the current reservoir
level.

## Behavioral Change

After this advance:
- Every stroke's darkness is multiplied by `ink_darkness(reservoir)`:
  - Formula: `factor = 0.55 + 0.57 * reservoir^0.4` (maps 0–1 reservoir to 0.55–1.12 factor)
  - At reservoir=1.0: factor=1.12 (slightly boosted — fresh dip saturation)
  - At reservoir=0.5: factor=0.97 (barely lighter — correct; a half-full quill looks nearly identical)
  - At reservoir=0.2: factor=0.79 (visibly lighter)
  - At reservoir=0.05: factor=0.61 (quite faded but not invisible)
- Every stroke's nib width is scaled by `ink_width_modifier(reservoir)`:
  - Formula: `0.94 + 0.14 * reservoir^0.5` (maps 0–1 reservoir to 0.94–1.08)
  - Fresh nib: strokes 8% wider (ink wicks laterally into the vellum)
  - Nearly empty nib: strokes 6% thinner (minimal ink spread)
  - Maximum total width range across a full cycle: ±7%
- The ink cycle becomes visible as a sawtooth pattern across a line: slightly wider,
  darker strokes near a dip point, gradually narrowing and lightening, then a sudden
  reset after the next dip
- The existing `base_dark = 0.88 + 0.12 * pressure` formula is preserved; the ink
  factor multiplies the result (not replaces it) so per-stroke pressure variation
  is retained on top of the ink cycle

## Planned Implementation Tasks

- [ ] Tidy: add `ink_darkness(reservoir: float) -> float` and `ink_width_modifier(reservoir: float) -> float` to `scribesim/ink/cycle.py`
- [ ] Test: verify `ink_darkness(1.0)` ≈ 1.12, `ink_darkness(0.5)` ≈ 0.97, `ink_darkness(0.2)` ≈ 0.79, `ink_darkness(0.05)` ≈ 0.61; verify `ink_width_modifier(1.0)` ≈ 1.08, `ink_width_modifier(0.0)` ≈ 0.94
- [ ] Implement: in `renderer.py` `_draw_nib_sweep()`, multiply the final darkness by `ink.ink_darkness(reservoir)` where `ink` is the `InkState` passed from `render_word_from_genome()`
- [ ] Implement: in `renderer.py`, multiply `hx_seg` and `hy_seg` by `ink.ink_width_modifier(reservoir)` for each glyph segment
- [ ] Validate: render the two Konrad test lines; visually confirm the ink cycle is visible — first word after a dip should be slightly darker and wider than the last word before the dip. Use `--variation 0` to isolate ink cycle effects from scribal variance.
- [ ] Validate: confirm that darkness stays above 0.50 even at reservoir=0 (the `min_factor=0.55` floor) — a dry quill leaves faint but visible marks

## Risk + Rollback

**Risks:**
- The `min_factor=0.55` floor combined with `base_dark=0.88` gives a minimum darkness
  of ~0.49 at full depletion — may need calibration against reference manuscripts
  once TD-009 reference images are available
- Width modulation interacts with the `nib_angle_drift` from the scribal variance layer;
  these should multiply rather than compete (both are physical effects)

**Rollback:**
- Set `ink_darkness()` to return 1.0 and `ink_width_modifier()` to return 1.0;
  the ink state is still tracked but has no visual effect

## Evidence

- [ ] Tests in `tests/test_ink_cycle.py` covering both modulation functions at boundary values
- [ ] Rendered Konrad line 1 visually shows ink cycle gradient from word 1 to word 7
- [ ] `--variation 0` render confirms cycle is deterministic and not noise-driven
