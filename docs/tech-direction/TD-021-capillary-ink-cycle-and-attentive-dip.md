# Tech Direction: TD-021 — Capillary Plateau Ink Cycle & Attentive Scribe Dip Discipline

## Status
**Active** — refines TD-010 (Ink Cycle Simulation) and TD-019 Phase 16c (`KinematicScribeSession` and `render_kinematic_folio`).

## Context & Problem Statement

Visual inspection of the 34 rendered kinematic folios revealed that quill ink depletion appeared too abrupt and mechanical—producing a noticeable sawtooth contrast band across lines where words steadily greyed out and then snapped back to heavy black at the next word boundary.

Tracing the kinematic folio pipeline (`scribesim/handflow/coarticulate.py` $\rightarrow$ `scribesim/handvalidate/tier2_bench.py`) identified three compounding causes:

1. **Double-Applied Depletion:** `solve_word_coarticulation()` scaled sample contact pressure `p_eff` by `session.state.darkness_scale()` (driven by `ink_darkness(reservoir)`), and `render_kinematic_folio()` then multiplied stroke darkness a second time by a steep power curve `dip_dark = 0.50 + 0.54 * (res_level ** 0.55)` while simultaneously narrowing nib width via `ink_width_modifier()`. This squared the reservoir drop, turning a moderate reservoir decline into a 35–40% contrast drop right before each dip.
2. **Missing Capillary Plateau:** A real cut quill holds ink in the slit and under the barrel via surface tension (`capillary hold`). Across the upper 55–65% of the reservoir (`0.88 → 0.42`), ink delivery to the vellum is nearly constant once the initial post-dip surface bead settles (`1.00 → 0.88`). A pure power law (`reservoir ** 0.55`) instead sloped downward across the entire cycle from word 1 onward.
3. **Unattentive Cliff Dipping:** `KinematicScribeSession` used a fixed `preferred_dip_threshold = 0.25` and evaluated `process_word_boundary()` without looking at word length, punctuation pauses, line ends, or scribal affect (`EmotionalLineState`). As a result, Brother Konrad rode the quill down to 25% on every single cycle regardless of whether he was about to begin a 10-letter compound word or had just paused at a period.

---

## Architecture & Mathematical Model

### 1. Three-Regime Capillary Reservoir Curve (`capillary_flow_curve`)

For normalized reservoir $r \in [0, 1]$, we model capillary ink delivery $f_{\text{cap}}(r)$ as the sum of three smooth C¹ (`smoothstep`) regimes in `scribesim/ink/cycle.py`:

$$\operatorname{smoothstep}(a, b, x) = t^2(3 - 2t), \quad t = \operatorname{clamp}\!\left(\frac{x - a}{b - a},\, 0,\, 1\right)$$

1. **Post-dip meniscus settle ($r \in [0.86, 1.00]$):**
   $$S_{\text{fresh}}(r) = \operatorname{smoothstep}(0.86, 1.00, r)$$
   Models the subtle richness (`+3.5%` darkness, `+2.5%` width) over the first word after dipping before excess surface ink clears into the vellum.
2. **Capillary working plateau ($r \in [0.40, 0.86]$):**
   $$P_{\text{plat}}(r) = \operatorname{smoothstep}(0.40, 0.90, r)$$
   Maintains a nearly flat delivery plateau (`0.93 → 0.965` darkness) across the middle ~60% of the reservoir where slit capillary pressure regulates flow.
3. **Soft shoulder & dry tail ($r \in [0.00, 0.40]$):**
   $$D_{\text{shoulder}}(r) = \operatorname{smoothstep}(0.08, 0.42, r)$$
   Gradually rolls off when the meniscus retreats toward the nib tip, without a sudden step.

From these regimes:
- **`ink_darkness_capillary(r)`** (used by kinematic folio rendering and exposed as a smooth curve in `scribesim/ink/cycle.py`):
  $$\text{darkness}(r) = 0.72 + 0.19\,D_{\text{shoulder}}(r) + 0.055\,P_{\text{plat}}(r) + 0.035\,S_{\text{fresh}}(r)$$
  - At $r = 1.00$: $1.000$ (fresh dip)
  - At $r = 0.85$: $0.960$ (settled working plateau)
  - At $r = 0.50$: $0.922$ (still on the capillary plateau — only ~4% lighter than freshsettled)
  - At $r = 0.35$: $0.885$ (upper shoulder where an attentive scribe normally dips)
  - At $r = 0.22$: $0.805$ (late dip under agitation/fatigue — visibly softer, primarily in hairlines, never washed out)
  - At $r = 0.00$: $0.720$ (dry floor)

- **Stroke-type differentiation in `render_kinematic_folio()`:**
  When the reservoir enters the shoulder ($r < 0.42$), thin low-pressure hairlines lose saturation faster than high-pressure downward stems (because downward pressure splays the slit and draws out the remaining capillary bead):
  $$\text{effective\_dip\_dark}(r, p) = \text{darkness}(r) - (1 - p)\cdot 0.08 \cdot \bigl(1 - D_{\text{shoulder}}(r)\bigr)$$

### 2. Single-Owner Depletion (Eliminating the Squared Drop)

- `solve_word_coarticulation()` in `scribesim/handflow/coarticulate.py` continues to call `session.state.consume_contact_distance(...)` so every `SandboxSample.ink_reservoir` records the exact continuous arc-length reservoir trajectory.
- However, `solve_word_coarticulation()` **no longer** multiplies mechanical contact pressure `p_eff` by `session.state.darkness_scale()`. Instead, as the nib begins to dry ($r < 0.35$), a scribe subtly increases mechanical down-pressure by up to `+3%` (`1.0 + 0.03 * (1 - smoothstep(0.15, 0.38, r))`) to coax ink from the slit, while all optical darkness and width modulation is owned once by the renderer.

### 3. Attentive & Anticipatory Scribe Dip Discipline

In `scribesim/ink/cycle.py` and `scribesim/render/scribe_state.py`, `InkState.process_word_boundary()` is extended with optional context:

```python
def process_word_boundary(
    self,
    *,
    word_text: str = "",
    next_word_len: int = 0,
    is_line_end: bool = False,
    attention: float = 1.0,
) -> DipEvent
```

A careful scribe pays attention to his quill and the text ahead:
- **Base attentive threshold:** `preferred_dip_threshold = 0.36` (on the upper edge of the shoulder, before noticeable paling), `dip_threshold = 0.22`.
- **Clause / punctuation pause (`word_text` ends with `.`, `,`, `;`, `:`, `?`, `!`, `—`):** The scribe naturally glances at the inkhorn during a syntactic pause; if $r < \text{preferred\_threshold} + 0.10$, he dips early (`PreferredDip`).
- **Line-end lookahead (`is_line_end=True`):** During the carriage return to the left margin, if $r < \text{preferred\_threshold} + 0.08$, he refreshes the quill rather than starting the new line half-empty.
- **Long-word lookahead (`next_word_len >= 7`):** Estimates the upcoming word's ink demand ($\Delta r \approx 0.011 \times \text{next\_word\_len}$). If completing the upcoming word would drive the reservoir below `dip_threshold + 0.04`, he dips before starting the long word.
- **Emotional / fatigue modulation (`attention`):**
  - In `deepened_attention`, `sacred_steadiness`, or `latin_formal` (`attention ≈ 1.15–1.25`), the effective preferred threshold rises by `+0.05`, keeping the cycle strictly on the capillary plateau.
  - In `tremor_agitation`, `grief_hesitation`, or high fatigue (`attention ≈ 0.75–0.85`), the effective threshold drops by `-0.06`, allowing the scribe to occasionally write deeper into the soft shoulder (`r ≈ 0.24–0.28`) so visible ink thinning becomes a rare, narrative-motivated event.

---

## Verification Criteria

1. **Plateau Flatness:** Across $r \in [0.45, 0.90]$, `ink_darkness_capillary(r)` varies by less than $0.055$ ($\le 5.5\%$), compared to $>0.15$ under the old power law.
2. **No Squared Drop:** On a standard 12-line folio render, pre-dip word darkness never drops more than $14\%$ below post-dip settled darkness under normal attention, while still showing subtle post-dip richness and hairline-first shoulder softening.
3. **Contextual Dip Timing:** Punctuation pauses, line ends, and long upcoming words trigger earlier `PreferredDip` events than bare mid-clause short words at the same reservoir level.
4. **Tier-1 & Tier-2 Gates:** All existing `test_ink_cycle.py`, `test_kinematic_state.py`, and `test_tier2_bench.py` (`B1–B4`) contracts remain green.
