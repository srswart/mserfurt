---
advance:
  id: ADV-SS-IMPRECISION-001
  title: Cumulative Imprecision — Ruling, Baseline Wander, Margin Drift
  system: scribesim
  primary_component: layout
  components:
  - layout
  - movement
  started_at: 2026-03-20T14:35:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T10:51:01.679284Z
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
  status: complete
---

## Objective

Implement the cumulative imprecision model from TD-002 Part 4. Ruling lines, baselines, margins, and inter-line spacing all carry structured imprecision that compounds across the page. The scribe is precise but never exact — the deviations are not random noise but structured patterns that a trained eye recognizes as human.

## Behavioral Change

After this advance:
- **Ruling lines** have per-line imprecision: y-position jitter (±0.2mm), slight bow (straightness parameter), angle jitter (±0.1° from horizontal)
- **Baseline wander**: the written baseline follows the ruling line but with low-frequency sinusoidal wander (amplitude ±0.3mm, frequency ~0.5/line_width) — visible under magnification
- **Left margin alignment**: line start x-position = target_margin + systematic_drift × line_number + per_line_jitter + first_letter_adjustment — the margin slowly drifts and individual lines have small offsets
- **Right margin behavior**: the scribe makes real-time decisions at the right margin — write normally, compress slightly, compress more, hyphenate, or extend into the margin. The right margin is ragged in a structured way, not uniform.
- **Inter-line spacing**: follows ruling but not precisely (±0.3mm). Additional space where descenders from the line above would collide with ascenders below.
- All imprecision parameters are sourced from the `HandProfile` (folio and line scale groups)
- The layout engine applies imprecision after line breaking but before final coordinate assignment

## Planned Implementation Tasks

- [ ] Tidy: separate ruling generation from line placement in `layout/geometry.py` — ruling is a physical property of the page, placement is the scribe's response to it
- [ ] Test: write tests — ruling lines have measurable jitter (not perfectly horizontal); baselines wander around ruling lines within tolerance; left margin drifts systematically across lines; right margin shows structured raggedness; inter-line spacing varies
- [ ] Implement: `RulingLine` with y_position jitter, straightness (bow), angle jitter — one per text line on the page
- [ ] Implement: baseline wander — low-frequency sinusoidal noise overlaid on ruling position, parameterized by amplitude and frequency
- [ ] Implement: left margin drift — systematic component (drift × line_number) + per-line stochastic component + first-letter width adjustment
- [ ] Implement: right margin behavior — decision model at margin compression zone: normal → compress → compress more → hyphenate → extend; probability weights from `HandProfile`
- [ ] Implement: inter-line spacing variation — ruling-based spacing ± jitter, with collision avoidance (extra space when descenders meet ascenders)
- [ ] Integrate: apply imprecision offsets to `PositionedGlyph` coordinates in the layout placer, after line breaking and movement model composition
- [ ] Integrate: wire imprecision into layout placer — imprecision offsets applied after line breaking and movement composition. Active by default.
- [ ] Validate: render f01r with imprecision enabled; measure baseline regularity, margin drift, and spacing variation; verify they fall within TD-002 parameter ranges
- [ ] Checkpoint: run `./snapshot.sh imprecision-001` — VISUAL DIFF vs ink-001 snapshot: ruling lines should show slight jitter, left margin should drift systematically across lines, right margin should be structured-ragged, inter-line spacing should vary subtly

## Risk + Rollback

**Risks:**
- Right margin behavior interacts with Knuth-Plass line breaking — the imprecision model must respect the line breaking decisions while adding margin-level variation
- Excessive imprecision makes text hard to read; the parameters must be conservative initially and tuned upward

**Rollback:**
- Revert the branch; imprecision is additive to existing layout coordinates

## Evidence

- [ ] 14 tests in `tests/test_imprecision.py` covering ruling_imprecision offsets and apply_imprecision layout modification
- [ ] 248 total tests pass (0 failures)
- [ ] Snapshot `imprecision-001` visually differs from `ink-001` — inter-line spacing varies subtly from ruling imprecision
