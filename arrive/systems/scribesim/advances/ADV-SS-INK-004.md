---
advance:
  id: ADV-SS-INK-004
  title: Hairline Quality Degradation — Thinning, Gaps, and Raking at Low Reservoir
  system: scribesim
  primary_component: ink
  components:
  - ink
  - evo
  started_at: 2026-03-22T00:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-22T12:26:24.766965Z
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

Implement the three continuous hairline degradation effects from TD-010 Part 2.3.
Hairlines (strokes where the rendered width is < 25% of nib width) become thinner,
develop gaps, and occasionally split (raking) as the reservoir approaches empty.
All three effects use sigmoid curves — no thresholds, no discrete states — so the
degradation is gradual and physically realistic.

## Behavioral Change

After this advance:
- `hairline_effects(reservoir)` returns three smooth-curve values:
  - **Width reduction**: `1/(1+exp(15*(reservoir-0.18))) * 0.45` — effectively zero
    above reservoir=0.4; reaches max 45% width reduction at empty
  - **Gap probability**: `1/(1+exp(18*(reservoir-0.15))) * 0.25` — per-sample-point
    probability of a gap (zero sample drawn, hairline broken); effectively zero above
    reservoir=0.4; max 25% gap chance at empty
  - **Raking probability**: `1/(1+exp(25*(reservoir-0.08))) * 0.30` — per-stroke
    probability that the nib splits and draws a raked double-line; effectively zero
    above reservoir=0.2; max 30% raking at empty
- A **raked stroke** renders as two parallel thin lines (distance = 40% of nib width)
  at 70% of normal darkness, simulating the split-nib effect visible in fatigued
  sections of real manuscripts
- Heavy strokes (width ≥ 25% of nib width) are not affected by these effects —
  they are governed by darkness modulation only (ADV-SS-INK-003)
- In normal writing (reservoir > 0.3), none of these effects are visible — this is
  correct behaviour. They only emerge near the end of a depletion cycle and are
  subtle even then.

## Planned Implementation Tasks

- [ ] Tidy: add `hairline_effects(reservoir: float) -> HairlineEffects` to
  `scribesim/ink/cycle.py`; define `HairlineEffects` as a dataclass with
  `width_reduction`, `gap_probability`, `raking_probability`
- [ ] Test: verify all three sigmoid functions return effectively 0.0 at reservoir=0.5;
  verify width_reduction ≈ 0.40 at reservoir=0.02; verify gap_probability ≈ 0.22
  at reservoir=0.02; verify raking_probability is near zero at reservoir=0.15 but
  meaningful at reservoir=0.02
- [ ] Implement: in the renderer's segment sample loop, detect hairline strokes
  (modified nib width < 25% of base nib width) and apply the three effects:
  - Width reduction: scale `hx_seg`/`hy_seg` by `(1 - width_reduction)`
  - Gap: skip drawing the segment quad for this sample if `random() < gap_probability`
  - Raking: before drawing, check `random() < raking_probability`; if raking,
    offset two parallel quads at ±20% of nib width instead of single centre quad
- [ ] Validate: render Konrad lines with a deliberately lowered `dip_threshold`
  (e.g. 0.35) to force the renderer to render through low-reservoir states; confirm
  hairlines thin and break naturally without heavy strokes being affected

## Risk + Rollback

**Risks:**
- Raking adds rendering complexity — the two-parallel-quad approach needs to avoid
  crossing hairlines that are already very thin at low reservoir; clamp minimum
  raking separation to 0.5px
- Gap probability is per-sample-point (not per-segment); at `n_samples=80` and
  `gap_probability=0.25`, approximately 20 gaps per segment — this may look too
  broken; may need to smooth gaps by requiring consecutive gap samples

**Rollback:**
- Return `HairlineEffects(0.0, 0.0, 0.0)` from `hairline_effects()` to disable all
  effects without removing the code path

## Evidence

- [ ] Tests in `tests/test_ink_cycle.py` covering sigmoid boundary values for all three effects
- [ ] Visual: render with forced low reservoir shows hairline degradation in thin strokes; heavy downstrokes remain solid
- [ ] No hairline degradation visible at reservoir > 0.35 in any normal render
