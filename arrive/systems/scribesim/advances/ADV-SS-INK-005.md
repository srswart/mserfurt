---
advance:
  id: ADV-SS-INK-005
  title: Post-Dip Blob and Ink Cycle Diagnostics
  system: scribesim
  primary_component: ink
  components:
  - ink
  - evo
  - cli
  started_at: 2026-03-22T00:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-22T12:34:08.576154Z
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
  status: complete
---

## Objective

Add the post-dip blob effect (TD-010 Part 2.4) and the two diagnostic outputs
(ink state overlay, ink cycle graph) from TD-010 Part 5. The blob is a small detail
but highly characteristic of real manuscripts. The diagnostics make the ink cycle
visible during calibration without manual inspection of rendered output.

## Behavioral Change

After this advance:

### Post-dip blob
- After `InkState.dip()`, the first contact stroke (when `strokes_since_dip == 0`
  and `reservoir > 0.90`) has a 15% chance of depositing a small excess ink blob
  at the stroke start point
- Blob parameters: radius 0.2–0.5mm, 20% darker than surrounding ink,
  slightly elongated ellipse (not a perfect circle) aligned with the first stroke direction
- Blob is rendered as a filled polygon ellipse at 3× supersample resolution, then
  downsampled with the rest of the word image

### Ink state overlay (`--show-ink-state` flag)
- `render_line()` accepts `show_ink_state: bool` parameter
- When enabled, each word image is tinted with a colour overlay based on the
  reservoir level at the start of that word:
  - Green (reservoir > 0.7): fresh
  - No tint (0.3–0.7): normal
  - Yellow (0.15–0.3): getting low
  - Red (< 0.15): critical, dip imminent
- Dip points are marked with a small blue dot above the first letter of the
  post-dip word
- Overlay is semi-transparent (30% opacity) so the letterforms remain visible

### Ink cycle graph (`--ink-graph` flag in `render-line`)
- Outputs a separate PNG plotting reservoir level (y-axis) vs. word index (x-axis)
- Shows the sawtooth pattern: gradual depletion, vertical refill, repeat
- Dip points are marked with a vertical blue line
- Saved alongside the rendered line output as `{output_stem}_ink_graph.png`

## Planned Implementation Tasks

- [ ] Implement: `post_dip_blob(reservoir, strokes_since_dip) -> Optional[BlobParams]`
  in `scribesim/ink/cycle.py`; `BlobParams` is a dataclass with `radius_mm`,
  `darkness_boost`, `elongation` (1.0=circle, >1=elongated along stroke direction)
- [ ] Implement: blob rendering in `renderer.py` — draw filled ellipse polygon at
  the first contact point when `InkState` signals a fresh dip; integrate into the
  supersampled canvas before downsample
- [ ] Implement: `--show-ink-state` flag in `render-line` CLI command; add
  `show_ink_state` parameter to `render_line()` and `render_word_from_genome()`
- [ ] Implement: ink state overlay tinting using per-word reservoir snapshot stored
  during word rendering; composite the tint as a semi-transparent colour rect on
  the word canvas before final line compositing
- [ ] Implement: `--ink-graph` flag in `render-line`; collect `(word_index, reservoir)`
  tuples during rendering and plot with matplotlib (or a minimal PIL-based line plot
  to avoid adding a heavy dependency)
- [ ] Test: blob appears on first stroke after dip with probability ≈ 0.15; blob
  does not appear when `strokes_since_dip > 0` or `reservoir < 0.90`
- [ ] Validate: render Konrad lines with `--show-ink-state`; confirm colour bands
  transition correctly across words; confirm dip markers appear at the right word indices

## Risk + Rollback

**Risks:**
- matplotlib is a large dependency; if it's not already in the project, use a
  minimal PIL-based line plot instead (draw lines between `(x, reservoir)` points
  directly on a white canvas)
- The blob ellipse must not extend outside the letter canvas; clip to canvas bounds

**Rollback:**
- Blob: `post_dip_blob()` returns `None` always — no visual change
- Diagnostics: `--show-ink-state` and `--ink-graph` flags default to false and
  are purely additive; removing them has no effect on production renders

## Evidence

- [ ] Test: blob probability ≈ 0.15 over 500 trials
- [ ] Ink state overlay PNG shows correct colour banding for a 7-word line that crosses one dip
- [ ] Ink cycle graph shows sawtooth pattern with correct dip positions for Konrad test lines
