# Tech Direction: TD-019 — Kinematic Coarticulation, Bastarda Proportions, and Hybrid Evaluation

## Status
**Proposed** — architectural pivot and execution plan superseding the analytic cubic-splicing loop in Pass 15 (`ADV-SS-CURRICULUM-016` / `TD-018` Addenda D–F), while preserving all `TD-001` system contracts (`XL` → `ScribeSim` → `Weather`) and historical evidence.

**Date:** 2026-10-16  
**Author:** shawn + cursor-agent  

---

## 1. Context and Diagnosis: Why Previous Tracks Stalled

Across 18 Tech Directions and 15 implementation passes, ScribeSim has explored six paradigms for simulating Brother Konrad's mid-15th-century German Bastarda hand. Reviewing their outputs side-by-side reveals why none has yet produced a convincing scribal simulation:

| Track | Core Mechanism | Why It Stalled |
|---|---|---|
| **1. Static Glyph Catalog** (`TD-002`–`004`, `TD-015`, `TD-017`) | ~90 hand-authored cubic Bézier glyphs + polygon sweep + per-glyph jitter / slow state drift | **Typeface effect:** The generative primitive is a static letter template. Repeated letters are clones; inter-letter joins are post-hoc line segments glued between immutable endpoints. |
| **2. Freeform Attractor / PD Dynamics** (`TD-005`, `TD-006`) | Point-mass hand state machine chasing sparse keypoints with attraction and damping forces | **Control instability:** Loose gains caused wild target overshoot and tangled loops; clamped gains (`ADV-SS-CLAMP-001`) made the pen crawl mechanically from point to point. |
| **3. Evolutionary Word Genomes** (`TD-007`, `TD-012`) | Genetic algorithm evolving `Word / Glyph / Stroke` Bézier control points against fitness terms $F_1\text{–}F_7$ | **Metric gaming:** Proxy objectives conflicted—smoothness ($F_6$) ironed out authentic Bastarda crispness, and per-word control-point mutations lacked shared motor structure. |
| **4. Corridor-Guided Curriculum** (`TD-008`, `TD-009`, `TD-014`) | Extracted centerlines frozen as `DensePathGuide` corridors tracked by `GuidedHandFlowController` | **Template tracking:** Penalizing deviation from a narrow corridor around a fixed nominal path forced the controller to reproduce the static guide verbatim. |
| **5. Pure Diffusion Word Synthesis** (`TD-018-learned-scribal-hand.md`) | `One-DM` / `DiffusionPen` conditioned on text + style exemplars | **Plumbing complete, unintegrated:** Captures image texture, but lacks native stroke-level pressure heatmaps and glyph polygons required by `TD-001-C/F` and `Weather`. |
| **6. Analytic Stroke-Gesture Splicing** (`TD-018` Addenda A–F, Pass 15) | Piecewise cubic primitives + analytic boundary splices (`A→F→P→Q→K→C`) + rational self-contact proofs | **Mathematical & governance gridlock:** Treated cursive connection as a static CAD spline-splicing and theorem-proving problem rather than a temporal motor-control problem. |

### Four Root Bottlenecks to Break

1. **CAD Spline-Splicing Cannot Scale to Cursive Coarticulation:**
   In `ADV-SS-CURRICULUM-016` (`scripts/nu_mutual_construction.py`, `scripts/nu_ramp_contact_measurement.py`), connecting a single bigram (`n→u`) required manually specifying cubic parameter cuts (`t = 0.7648068784772746`), fixed Hermite handle ratios (`0.9 * drop`), and 248 unit tests isolating rational polynomial roots to check whether a finite nib rectangle revisits a paper point by $1.6\,\mu\text{m}$. In real calligraphy, wet ink overlaps at every turn and reversal. Hand-designing pairwise spline splices for $26 \times 26 = 676$ letter pairs is intractable, and piecewise $G^1$ cubics with fixed chord-third handles create visible "shelves" and "shoulders" because human hands minimize **temporal jerk ($\dddot{x}$)**, not spatial handle ratios.
2. **Incorrect Calligraphic Proportions and Spacing:**
   The Pass 15 candidate (`candidate.json`) uses `x_height_mm = 3.5` with `nib_width_mm = 0.45` (a $7.8 : 1$ ratio—a fine technical pen) and places `u`'s first stem $3.39\text{ mm}$ away from `n`'s foot (nearly a full x-height gap). Historical Bastarda has an x-height of **$4.0\text{–}4.5$ nib widths** ($\sim 0.8\text{ mm}$ nib for a $3.5\text{ mm}$ x-height) and a minim bay width of **$\sim 1.0\text{–}1.3$ nib widths** ($\sim 0.9\text{ mm}$). Because the letters were spaced $3.4\text{ mm}$ apart, the join could not rise along the natural $40^\circ$ nib plane, which in turn forced an artificial "10% active corner edge" (`[0, 0.1]`) hack to make the connector thin.
3. **Black-Box Optimization Over Non-Differentiable Rasterization:**
   Fitting stroke parameters via derivative-free search (`CMA-ES`, genetic algorithms, or finite grids) over non-differentiable `PIL` polygon draws requires thousands of evaluations and cannot jointly optimize letter shapes and timing.
4. **Governance & Gate Lockout (Zero-Visual-Feedback Loop):**
   Pass 15 scripts verify 1,800+ SHA-256 artifact hashes and require 31 analytic geometry/contact proofs to pass *before* emitting a single PNG—while `G0` (real manuscript admission) has `0 / 52` admitted words. A writing simulator cannot be designed blind.

---

## 2. Core Technical Architecture (TD-019)

`TD-019` replaces pairwise spline-splicing and narrow corridor-following with **Global Kinematic Coarticulation over Nib-Normalized Via-Points**, supported by fast visual iteration and differentiable refinement.

```
XL Folio JSON + CLIO-7 HandNotes
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 1. Allograph & Via-Point Composer (scribesim/guides/, TD-012)        │
│    Selects context-appropriate allographs in nib-width (w_nib) units │
│    and emits a word sequence of Via-Points (μ_k, Σ_k, v_k, p_k, c_k) │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 2. ScribeState Modulator (scribesim/render/scribe_state.py, TD-017)  │
│    Applies slow correlated drift to via-points, tempo, nib angle,    │
│    and ink reservoir (TD-010) + CLIO-7 folio modifiers               │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 3. Global Minimum-Jerk Coarticulation Solver (scribesim/handflow/)   │
│    Solves banded QP across the entire word in <1 ms:                 │
│    min ∫ ||x'''(t)||² dt + Σ (x(t_k) - μ_k)^T Σ_k^-1 (x(t_k) - μ_k)  │
│    → Reciprocal letter-to-letter flow emerges automatically          │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 4. Broad-Nib Physical Sweep (scribesim/render/)                      │
│    True 40° chisel geometry (w_nib ≈ H/4.2) + pressure tine splay    │
│    + velocity-minimum ink pooling → Page PNG + Pressure Map + XML    │
└──────────────────────────────────────────────────────────────────────┘
```

### Pillar 1: Calligraphic Geometry in Nib-Width Units ($w_{\text{nib}}$)
All spatial dimensions in letter recipes are defined in multiples of the physical nib width $w_{\text{nib}}$, anchored to historical 15th-century German Bastarda proportions:
* **Nib-to-x-height ratio:** $H = 4.2\,w_{\text{nib}}$ (for $H = 3.5\text{ mm}$, $w_{\text{nib}} = 0.83\text{ mm}$, thickness $t_{\text{nib}} = 0.08\text{ mm}$).
* **Minim bay and inter-letter spacing:** Interior minim counter $= 1.2\,w_{\text{nib}}$ ($\approx 1.0\text{ mm}$); inter-letter connected minim gap $= 1.1\,w_{\text{nib}}$.
* **Natural $40^\circ$ hairline joins (no partial-edge hacks):** With proper minim spacing, the pen exits a stem foot at the baseline and rises toward the next letter's entry along $\theta \approx 40^\circ$. Because the nib edge is held at $\alpha_{\text{nib}} \approx 40^\circ$ (with subtle $\pm 3^\circ$ wrist roll on curves per `TD-013`), the apparent stroke width:
  $$w(\theta, p) = w_{\text{nib}}\,(1 + \kappa_{\text{splay}}\,p)\,|\sin(\theta - \alpha_{\text{nib}})| + t_{\text{nib}}\,|\cos(\theta - \alpha_{\text{nib}})|$$
  naturally collapses to a crisp hairline $t_{\text{nib}}$ on $40^\circ$ upstrokes and expands to full width on downstrokes.
* **Wet-ink turn pooling (no self-overlap prohibitions):** When pen speed $|\dot{x}(t)|$ drops at a foot or crown turn, ink deposition per unit arc length increases slightly, naturally creating the characteristic Bastarda diamond foot / clubbed head where the nib pivots on wet ink.

### Pillar 2: Global Minimum-Jerk Via-Point Coarticulation
Instead of storing rigid cubic Bézier curves per letter and splicing their tails, each letter allograph is represented as a sequence of $4\text{–}8$ **Kinematic Via-Points**:

$$\mathcal{V}_k = \left(\mu_k \in \mathbb{R}^2,\; \Sigma_k \in \mathbb{R}^{2\times 2},\; v_k^{\text{pref}} \in \mathbb{R}^2,\; c_k \in \{\text{down}, \text{air}\},\; p_k \in [0, 1],\; \text{role}_k\right)$$

* $\mu_k$: Nominal target position in nib-width coordinates.
* $\Sigma_k$: $2\times 2$ spatial tolerance covariance matrix (inverse stiffness $\Sigma_k^{-1}$).
  * *Protected body anchors* (e.g., mid-stem corridor, baseline foot height) have tight variance along their constrained axis ($\sigma_\perp \approx 0.03\,w_{\text{nib}}$).
  * *Flexible boundary anchors* (e.g., terminal departure foot, receiving entry crown) have larger variance ($\sigma \approx 0.15\text{–}0.25\,w_{\text{nib}}$) oriented along the stroke flow.
* **Word-Level Trajectory Solution:**
  To write a word (or a continuous pen-down run within a word), concatenate its via-points at cumulative nominal times $0 = t_1 < t_2 < \dots < t_K = T$ (scaled by chord distances and turn angles) and solve the **Minimum-Jerk Quadratic Program**:

  $$\min_{x(t), y(t)} \int_0^T \left(\|\dddot{x}(t)\|^2 + \lambda_v \|\ddot{x}(t)\|^2\right) dt + \sum_{k=1}^K (x(t_k) - \mu_k)^\top \Sigma_k^{-1} (x(t_k) - \mu_k) + \sum_{k \in \mathcal{D}} \gamma_k \|\dot{x}(t_k) - v_k^{\text{pref}}\|^2$$

* **Why this solves mutual letter flow (`Addendum F`) universally:**
  * The minimum-jerk trajectory is a natural quintic spline (or离散 banded finite-difference trajectory) whose position and velocity at via-point $k$ depend on both $k-1$ and $k+1$ weighted by their stiffnesses $\Sigma_k^{-1}$.
  * When `n` is followed by `u` (high entry at $y = H$), `n`'s flexible exit via-point is pulled upward and rightward, causing `n`'s second minim to begin turning slightly earlier; simultaneously, `u`'s entry crown bends leftward to meet the incoming velocity vector from `n`.
  * When `n` is followed by `m` or `o` or `d`, the **exact same linear solver** produces the appropriate mutual adaptation without a single pair-specific rule or manual cubic cut.
  * Solving the banded linear system takes $< 1\text{ ms}$ per word on CPU.

### Pillar 3: Differentiable Ribbon Fitting & Pragmatic Reference Grounding
* **Differentiable PyTorch Nib Renderer:** Implement a lightweight (~80 LOC) differentiable renderer in `scribesim/tuning/diff_render.py` that evaluates the soft signed distance from pixel coordinates to each swept nib quad. This allows gradient-based optimization (`Adam` / `L-BFGS`) of via-point positions $\mu_k$, tolerances $\Sigma_k$, and timing ratios against real manuscript crops using multi-scale pyramid $L_1$ + Soft-DTW skeleton loss.
* **Pragmatic Reference Grounding (Unblocking `G0`):** Stop requiring automatic connected-component pixel masks to cleanly separate touching lines before admitting a word crop. Instead:
  1. Use a 15-minute pass in the existing Annotation Workbench (`scribesim/annotate/`) to confirm transcriptions and baseline boxes for **30 clean reference words** from the BSB anchor manuscript.
  2. Weight image loss with a smooth vertical window centered on the `[baseline, x_height]` core band so stray descenders from adjacent lines do not corrupt gradient fitting.

### Pillar 4: Fast Sandbox First (Decoupling Exploration from Promotion Gates)
* Add `scribesim sandbox`—a zero-lockout CLI command that renders a word (`nu`, `nm`, `und`, `schreiber`), an alphabet grid, or the 3-line proof specimen in $< 0.5\text{ s}$ and emits a self-contained HTML view showing:
  1. Clean 1:1 physical-scale ink render (the scribe output).
  2. Zoomed kinematic overlay (via-points $\mu_k$, tolerance ellipses $\Sigma_k$, actual solved trajectory $x(t)$, velocity heatmap, and oriented nib rectangles).
* **Governance rule:** No script or Advance may block rendering a preview image on failing a geometric or contact check. Diagnostics are reported *alongside* the rendered image so the developer and owner can always see what the pen did.

---

## 3. System, Component, and Advance Structure

### 3.1 System Impact (`XL` → `ScribeSim` → `Weather`)
* **`xl` (unchanged):** Continues to emit per-folio JSON (`TD-001-A`) and manifest (`TD-001-B`).
* **`scribesim` (primary impact):** Adds the kinematic via-point solver and evaluation workbench behind `--approach kinematic` (and updates `--approach guided` once promoted), emitting standard 300 DPI `{id}.png`, `{id}_pressure.png`, and glyph/word-accurate `{id}.xml`.
* **`weather` (unchanged):** Consumes `{id}.png`, `{id}_pressure.png`, and `{id}.xml` without contract changes.

### 3.2 Component Ownership inside `scribesim`
To stop the proliferation of one-off `scripts/nu_*.py` files in the root `scripts/` folder, all new work is housed cleanly inside `scribesim/` under existing components (all currently `stage: incubating`):

| Component | Path Selector | Responsibility in TD-019 |
|---|---|---|
| `hand` | `scribesim/hand/**`, `shared/hands/**` | Nib-width ($w_{\text{nib}}$) proportion parameters, Bastarda calibration (`w_nib = 0.83 mm`, `x_height = 3.5 mm`), `CLIO-7` per-folio modifier mapping. |
| `render` / `nibcontact` | `scribesim/render/**` | True $40^\circ$ broad-nib polygon sweep, pressure-driven tine splay, velocity-minimum turn pooling, and fast `<0.5s` sandbox sheet rendering. |
| `handflow` | `scribesim/handflow/**` | `coarticulate.py`: Global Minimum-Jerk Via-Point QP solver, pen-down/air transition timing, and integration with `ScribeState` (`TD-017`) + `InkState` (`TD-010`). |
| `guides` | `scribesim/guides/**` | Declarative `ViaPointRecipe` catalog for Bastarda lowercase, uppercase, long-`ſ`, `ß`, umlauts, and contextual allograph variants (`TD-012`). |
| `tuning` | `scribesim/tuning/**` | PyTorch differentiable soft-ribbon renderer (`diff_render.py`) and gradient-based via-point/tolerance refinement against reference word crops. |
| `annotate` | `scribesim/annotate/**` | Fast workbench confirmation of 30 reference words + the **Human-Eyes Review UI** (`review-sheet`) for capturing structured visual judgments. |
| `handvalidate` & `metrics` | `scribesim/handvalidate/**`, `scribesim/metrics/**` | Automated Tier-1 (kinematic/structural) and Tier-2 (HTR CER + reference distribution) gates + ingestion of Tier-3 human review JSONs. |
| `scribehand` *(optional)* | `scribesim/scribehand/**` | Optional Stage-2 structure-conditioned neural texture pass (ControlNet / img2img over kinematic render) if deeper ink-parchment micro-texture is desired. |

*Note on Pass 15 artifacts:* All existing files under `scripts/nu_*.py`, `scripts/stroke_*.py`, and `shared/training/konrad_hand_recovery/stroke_gestures_v2/` remain untouched and frozen for historical integrity, but `ADV-SS-CURRICULUM-016` is closed/superseded by Pass 16 rather than extended with further ramp-contact proofs.

---

## 4. Evaluation Architecture: Maximize Automation, Capture Human Eyes Where Decisive

A central lesson of `TD-003`, `TD-007`, and `TD-018` is that **using automated proxy metrics for things only human eyes can judge leads to metric gaming**, while **using human review or manual theorem-proving for things machines can check leads to paralysis**.

`TD-019` separates evaluation into **three explicit tiers**:

### Tier 1: Fast Automated Kinematic & Structural Checks (Every Run / CI, $< 2\text{ s}$)
These metrics verify physical and geometric invariants that have objective mathematical definitions:

| Check ID | Metric | Automated Target / Gate | Why Automated |
|---|---|---|---|
| `A1-PROPORTION` | Thick-to-thin stroke width ratio ($P_{95} / P_{05}$) & $H / w_{\text{nib}}$ | Ratio $\in [3.2, 5.0]$; $H / w_{\text{nib}} \in [3.8, 4.6]$ | Prevents regressing to thin/wiry pointed-pen strokes or blobbed ellipses. |
| `A2-KINEMATICS` | Dimensionless Jerk ($\text{DLJ}$) & velocity continuity | Smooth bell-shaped speed profiles between turns; zero uncommanded velocity spikes | Guarantees trajectories obey human motor bounds without manual spline-handle audits. |
| `A3-COARTICULATE` | Reciprocal Context Sensitivity ($\Delta_{\text{coart}}$) | $0.03\,w_{\text{nib}} \le \|\mathbf{x}_{n\text{ in }nu} - \mathbf{x}_{n\text{ in }nm}\| \le 0.35\,w_{\text{nib}}$ | Automatically proves that neighboring letters mutually adapt each other's terminal/entry strokes without distorting the protected letter body. |
| `A4-TOPOLOGY` | Counter preservation & unintended collision check | Euler number / interior background components preserved in `a, o, d, e, g, b, p`; zero non-adjacent glyph bounding-core overlaps | Catches collapsed loops or smashed letters automatically. |
| `A5-ANTI-CLONE` | Intra-page instance variation ($D_{\text{DTW}}(w_i, w_j)$) | Repeated letters/words on a page have $0 < \epsilon_{\min} \le D_{\text{DTW}} \le \epsilon_{\max}$ | Proves output is neither a stamped font ($D = 0$) nor chaotic ($D > \epsilon_{\max}$). |

### Tier 2: Automated Legibility & Reference-Distribution Gates (Stage Completion, $< 30\text{ s}$)
Before asking for human review, an automated batch evaluator tests whether the writing is **readable** and **statistically consistent with the reference manuscript**:

| Check ID | Metric | Automated Target / Gate | Implementation |
|---|---|---|---|
| `B1-HTR-CER` | Independent HTR Character Error Rate (CER) | $\text{CER} \le 0.05$ on clean proof lines; $\le 0.12$ on fatigued/agitated folios | Runs a pretrained Bastarda HTR recognizer (Kraken or TrOCR fine-tuned on CATMuS/BSB in `scripts/scribehand/train_htr_trocr.py`). Replaces template-matching "OCR proxies." |
| `B2-ANGLE-EMD` | Stroke Orientation Histogram Distance | Earth Mover's Distance $\text{EMD}(\text{hist}_\theta^{\text{gen}}, \text{hist}_\theta^{\text{ref}}) \le \tau_\theta$ | Measures whether rendered words share the authentic Bastarda directional signature ($90^\circ/\text{slant}$ minims + $40^\circ$ hairline joins) of the BSB reference crops. |
| `B3-RHYTHM-ACF` | Horizontal Ink-Projection Autocorrelation | Peak spacing lag and decay match reference line crops within $\pm 15\%$ | Measures the "picket-fence" minim rhythm and inter-word cadence of a professional scribe. |
| `B4-CONTRACTS` | Downstream `TD-001` Contract Verification | Exact character coverage $= 1.0$ (zero silent aliases); PAGE XML polygon IoU $\ge 0.95$; pressure heatmap dynamic range $\ge 0.4$; `Weather` dry-run passes | Guarantees full pipeline compatibility automatically. |

### Tier 3: Structured Human-Eyes Checkpoints (High-Signal, Low-Friction)
Automated metrics cannot judge whether a join feels "calligraphically alive" or whether an allograph looks authentically 15th-century vs. modern cursive. However, human review must never be a tedious 54-item ranking of invisible $\pm 3\%$ tweaks.

#### Rules for Human Checkpoints
1. **Pre-filtered by Automation:** A candidate is only presented for human review after Tier 1 passes (and Tier 2 for stage gates), OR when the developer invokes `scribesim review-sheet` during interactive design.
2. **Equal-Scale 3-Way Visual Board (`scribesim review-sheet`):**
   Generates a single browser page (served by `scribesim/annotate/workbench.py` or static HTML with local JSON save) showing:
   * **Top strip:** Real BSB manuscript reference word/line crops at matching x-height scale.
   * **Middle strip:** Previous baseline render (plain ink at 1:1 physical scale + 3× detail loupe).
   * **Bottom strip:** Current candidate render (plain ink at 1:1 physical scale + toggleable kinematic/nib overlay).
3. **4-Question Structured Rubric & Diagnostic Tags:**
   The reviewer answers at most **4 questions** with a single click (`pass` / `revise` / `reject`) plus optional quick-tags:
   1. **Join & Ductus Flow:** Do letters flow into one another as continuous pen movements, with natural reciprocal adaptation at boundaries (`nu`, `nm`, `und`, `der`)?
      * *Quick tags if `revise`:* `bridge_too_flat`, `abrupt_shoulder`, `too_wide_gap`, `artificial_hook`, `cramped`
   2. **Bastarda Script Identity:** Do the letter shapes, thick/thin contrast, and feet/crowns read as authentic mid-15th-century German Bastarda?
      * *Quick tags if `revise`:* `nib_too_thin`, `nib_too_broad`, `wrong_letter_form:<char>`, `missing_foot_turn`, `too_modern`
   3. **Organic Hand Variation:** Across repeated letters and words (`und ... und`, `in ... in`), does the sample feel written by a living hand rather than stamped by a font?
      * *Quick tags if `revise`:* `clones_visible`, `jitter_looks_random`, `baseline_too_rigid`, `excessive_messiness`
   4. **Overall Stage Verdict:** `promote_checkpoint` | `iterate_with_notes` | `reject`
4. **Machine-Readable Persistence:**
   Clicking **"Save Review"** writes `shared/training/reviews/<stage_id>-review.json` containing the candidate SHA-256, scores, quick-tags, free-text notes, and timestamp.
   * `handvalidate` reads this JSON directly to unlock the next curriculum stage.
   * Even more importantly, the **quick-tags map directly to parameter groups** (e.g., `too_wide_gap` $\rightarrow$ reduce inter-letter advance in `ViaPointRecipe`; `abrupt_shoulder` $\rightarrow$ increase boundary via-point covariance $\Sigma_k$ in `coarticulate.py`), turning human visual intuition into an immediate, actionable engineering adjustment.

---

## 5. Planned Implementation Sequence (Pass 16)

We structure this work as **Pass 16 (`TD-019 — Kinematic Coarticulation & Bastarda Hand Recovery`)** in `arrive/implementation-plan.yaml`, consisting of **7 focused Advances across 3 phases** (plus 1 optional hybrid-texture Advance), each staying well within the Green reviewability budget ($\le 30$):

### Phase 16a: Fast Sandbox, Bastarda Proportions & Core Coarticulation
Goal: Prove natural reciprocal letter flow on core letters (`n, u, m, i, d, e, r`) and words (`nu, nm, um, und, der, mir`) in an interactive sub-second loop.

1. **`ADV-SS-HAND-004` — Bastarda Nib-Width Proportions, Natural Chisel Contact & Fast Sandbox CLI**
   * *Components:* `hand`, `render`, `cli`, `tests`
   * *Deliverables:*
     * Recalibrate Bastarda profile to nib-width units ($H = 4.2\,w_{\text{nib}}$, $w_{\text{nib}} = 0.83\text{ mm}$ for $H = 3.5\text{ mm}$), natural $40^\circ$ hairline sweep, pressure tine-splay factor, and velocity-minimum turn pooling.
     * Add `scribesim sandbox` CLI that renders words/specimens + kinematic diagnostic HTML in $< 0.5\text{ s}$ with zero hash-pin lockouts.
     * Implement Tier-1 `A1-PROPORTION` automated check.
2. **`ADV-SS-HANDFLOW-012` — Global Minimum-Jerk Via-Point Coarticulation Solver**
   * *Components:* `handflow`, `guides`, `tests`
   * *Dependencies:* `ADV-SS-HAND-004`
   * *Deliverables:*
     * Implement `ViaPointRecipe` (positions $\mu_k$, tolerance covariances $\Sigma_k$, preferred velocities $v_k^{\text{pref}}$, contact/pressure states) and `solve_word_trajectory()` banded minimum-jerk QP solver in `scribesim/handflow/coarticulate.py`.
     * Author starter via-point recipes for `i, n, u, m, d, e, r` in nib-width units.
     * Implement Tier-1 `A2-KINEMATICS` and `A3-COARTICULATE` automated checks, proving reciprocal adaptation across `nu`, `nm`, `um`, `nn`, `und`, `der`, `mir` with zero pair-specific splice formulas.
3. **`ADV-SS-ANNOTATE-007` — Human-Eyes Review Board & Checkpoint #1 (Core Coarticulation)**
   * *Components:* `annotate`, `handvalidate`, `tests`
   * *Dependencies:* `ADV-SS-HANDFLOW-012`
   * *Deliverables:*
     * Add `scribesim review-sheet` mode to the workbench (equal-scale reference vs. baseline vs. candidate + 4-question rubric + quick-tag JSON export).
     * **Human Checkpoint #1:** Owner reviews `n, u, m, nu, nm, um, und, der` side-by-side with BSB reference crops and records `checkpoint-1-coarticulation.json`.

### Phase 16b: Full Bastarda Alphabet & Differentiable Reference Tuning
Goal: Expand to the complete manuscript character set and refine via-points/tolerances against real BSB manuscript word crops.

4. **`ADV-SS-GUIDES-002` — Full Bastarda Via-Point Alphabet & Contextual Allographs**
   * *Components:* `guides`, `handflow`, `tests`
   * *Dependencies:* `ADV-SS-ANNOTATE-007`
   * *Deliverables:*
     * Complete lowercase (`a–z`), Bastarda specials (`ſ`, `ß`, superscript-`e` umlauts `ä/ö/ü`, Tironian `⁊`, nasal bar, `✦`), and simplified Bastarda capitals (`A–Z`).
     * Integrate `TD-012` position/neighbor allograph selection (e.g., initial/medial `ſ` vs. final `s`, context-adapted `r` and `e` entries).
     * Verify Tier-1 `A4-TOPOLOGY` (open counters in `a, o, d, e, g, b, p`) and exact character coverage $= 1.0$ on all proof lines.
5. **`ADV-SS-TUNING-002` — Differentiable Nib Renderer & Reference Word Grounding**
   * *Components:* `tuning`, `annotate`, `handvalidate`, `tests`
   * *Dependencies:* `ADV-SS-GUIDES-002`
   * *Deliverables:*
     * Confirm ~30 clean BSB reference word crops in the workbench (soft baseline-band weighting—no brittle binary pixel mask admission lockout).
     * Implement PyTorch differentiable soft-quad renderer (`scribesim/tuning/diff_render.py`) and refine shared via-point coordinates $\mu_k$, tolerances $\Sigma_k$, and stroke-type nib angle drift (`TD-013`) via `Adam`/`L-BFGS`.
     * **Human Checkpoint #2:** Owner reviews the 3-line specimen (admitted reference words + unseen words + project text line) on the Review Board and records `checkpoint-2-specimen.json`.

### Phase 16c: Temporal State, Automated HTR/Distribution Gates & Folio Promotion
Goal: Activate coherent page-scale variation (`ScribeState`, `InkState`, `CLIO-7` apparatus) and validate full folios through Tier-1, Tier-2, and Tier-3 gates.

6. **`ADV-SS-STATE-002` — Coarticulated ScribeState, Ink Cycle & CLIO-7 Folio Modifiers**
   * *Components:* `render`, `handflow`, `ink`, `layout`, `tests`
   * *Dependencies:* `ADV-SS-TUNING-002`
   * *Deliverables:*
     * Wire `ScribeState` (`TD-017` slow correlated random walks on via-points, tempo, and nib angle), `InkState` (`TD-010` continuous contact-distance ink depletion, split-nib hairlines, and dip surges), and `CLIO-7` folio overrides (`f06r` lateral pressure, `f07r` multi-sitting ink reloads, `f07v` smaller working register, `f14r+` wider compensating spacing) into the kinematic word/line composer.
     * Verify Tier-1 `A5-ANTI-CLONE` (no two instances of `und` pixel-identical; coherent slow drift across lines).
7. **`ADV-SS-HANDVALIDATE-027` — Automated HTR/Distribution Bench & 4-Folio Human Sign-Off**
   * *Components:* `handvalidate`, `groundtruth`, `cli`, `tests`
   * *Dependencies:* `ADV-SS-STATE-002`
   * *Deliverables:*
     * Run full Tier-2 automated evaluation (`B1-HTR-CER` $\le 0.05$, `B2-ANGLE-EMD`, `B3-RHYTHM-ACF`, `B4-CONTRACTS` PAGE XML IoU $\ge 0.95$ + pressure heatmap + `Weather` dry-run) on the 4 representative proof folios (`f01r`, `f06r`, `f07r`, `f14r`).
     * **Human Checkpoint #3:** Owner reviews full-folio renders and 1:1 crops in `scribesim review-sheet` and records `checkpoint-3-folios.json` to promote `--approach kinematic` as the default ScribeSim renderer.

### Optional Phase 16d: Hybrid Neural Micro-Texture (Only If Needed After Checkpoint #3)
8. **`ADV-SS-SCRIBEHAND-004` — Structure-Conditioned Neural Ink-Edge Texture Pass** *(Optional)*
   * *Components:* `scribehand`, `render`, `handvalidate`
   * *Dependencies:* `ADV-SS-HANDVALIDATE-027`
   * *Scope:* If human review at Checkpoint #3 finds the macro-ductus, coarticulation, and rhythm convincing but wants more organic quill-on-vellum edge micro-texture than polygon sweep + `Weather` provides, use the existing `scribesim/scribehand/` infrastructure to run a structure-preserving img2img / ControlNet pass conditioned on the kinematic ink + pressure map (preserving 100% text fidelity and exact PAGE XML coordinates).

---

## 6. Summary of Governance Improvements

1. **Visuals First, Metrics Alongside:** Every CLI run (`scribesim sandbox`, `scribesim review-sheet`) renders the visual output immediately and attaches Tier-1/Tier-2 metrics as a diagnostic sidecar—never locking out image generation behind unproven geometric theorems.
2. **One Home for Code:** All kinematic, rendering, and validation logic lives in tested modules under `scribesim/`, eliminating the proliferation of numbered standalone scripts in `scripts/`.
3. **Clear Division of Labor Between Machine and Human:**
   * **Machines check:** stroke-width ratios, jerk smoothness, nonzero coarticulation deltas, open counters, non-cloning, HTR Character Error Rate (CER), orientation/spacing distributions, and `TD-001` XML/heatmap contracts.
   * **Human eyes judge (at 3 explicit checkpoints via a 4-question UI):** naturalness of join flow, 15th-century Bastarda character identity, organic hand rhythm, and multi-folio narrative expression.
