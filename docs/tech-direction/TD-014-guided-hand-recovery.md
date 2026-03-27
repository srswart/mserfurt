# Tech Direction: TD-014 — Guided Hand Recovery via Corridor Tracking and Curriculum Training

## Status
**Proposed** — new hand-model implementation track intended to replace the failed freeform `handsim` path if its gates are met.

## Context
TD-005 and TD-006 correctly identified the ambition: the hand, not the glyph, should be the generative unit. But the implemented path remained illegible because it asked an incomplete controller to recover full letter shape from sparse targets. The planner was only partially wired, most letters fell back to endpoint-only targets, joins were modeled as lifts, and the renderer visualized marks as circles rather than broad-edge sweeps.

TD-014 keeps the original ambition while changing the representation and rollout strategy:

- keep the hand as a continuous dynamic system
- stop asking it to invent the whole letter from sparse keypoints
- give it a dense nominal path plus a legal corridor
- validate every stage with hard promotion gates
- roll out from primitive → glyph → word → line → folio only after passing each gate

This is a new approach. It reuses only the parts of the repo that are already valuable:

- trace extraction and centerline work from TD-008
- guide generation assets under `shared/hands/`
- physics nib and ink logic from TD-002/TD-004/TD-010
- image-comparison and structural metrics from `scribesim.metrics`
- the current render pipeline and folio contracts
- the IIIF/reference-selection stack from TD-009
- evo’s exemplar-aware glyph search, but only as a nominal-form proposer

It does **not** attempt to rescue the old sparse-target freeform simulator in place.

Default data policy:
- automatic extraction, transcription, trace recovery, and guide building are the default path
- human labeling or hand-identification remains a fallback reserve, not the baseline workflow
- low-confidence automatic samples are quarantined rather than promoted silently into training sets
- reviewable exemplar assets may not be populated directly from score-threshold buckets
- coverage repair samples may keep pipeline accounting alive, but they may not masquerade as trustworthy exemplars

Escalation policy:
- if automatic promotion still yields unreadable or mislabeled exemplar sets after the corpus-hardening gates, TD-014 escalates to a reviewed annotation workflow
- reviewed annotations become the authoritative source for exemplar truth on the affected symbols and joins
- the reviewed workflow must expose coverage debt directly, so the operator can see which glyphs and joins still need samples before evofit or guide freeze proceeds
- the reviewed workflow may also attach non-destructive cleanup masks to glyph or join annotations when nearby strokes, bleed, or adjacent characters would otherwise contaminate the exemplar crop

Default nominal-form policy:
- evo may be used to fit nominal glyph and short-join shapes from manuscript exemplars
- evo may not become the promoted folio renderer for TD-014
- every evo-derived proposal must be frozen into `DensePathGuide` assets before handflow can consume it
- nominal guide legibility must be validated before controller realism is considered

## Core Shift

### Old hand-model idea
```
sparse keypoints + free dynamics
→ dynamics fill in the shape
→ shape and control are solved at the same time
```

This is too unconstrained. The controller can satisfy local targets while still producing unreadable letters.

### New hand-model idea
```
dense nominal path + corridor constraints + continuous controller
→ controller tracks a plausible stroke plan
→ dynamics add realism within bounded deviation
→ legibility is preserved while motion remains physically expressive
```

The hand model is still a hand model. The difference is that it now follows a **planned stroke manifold** instead of reconstructing an entire letter from a few structural anchors.

## New Components

### 1. `pathguide` — dense nominal paths
Each glyph and common join is represented as a `DensePathGuide`:

```python
DensePathGuide(
    symbol: str,                    # glyph or join id
    samples_mm: list[(x, y)],       # dense centerline samples
    tangents: list[(dx, dy)],       # desired local direction
    contact: list[bool],            # pen down/up schedule
    speed_nominal: list[float],     # desired speed profile
    pressure_nominal: list[float],  # desired pressure profile
    corridor_half_width_mm: list[float],
    x_advance_mm: float,
    entry_tangent: (dx, dy),
    exit_tangent: (dx, dy),
)
```

Sources:
- extracted centerlines from manuscript crops
- hand-authored corrections for hard letters and joins
- existing guide corpora in `shared/hands/guides_*.toml`

Constraint:
- adjacent on-surface samples must be dense enough to define curvature and not leave shape recovery to the controller
- guides are stored in normalized physical coordinates after extraction; native pixel resolution is preserved only at extraction/measurement time

### 2. `handflow` — corridor-following controller
The controller tracks desired state from a plan, not raw keypoints:

```python
TrackPlan(
    desired_pos_mm,
    desired_vel_mm_s,
    desired_pressure,
    desired_contact,
    corridor_half_width_mm,
)
```

The hand state remains continuous:
- position, velocity, acceleration
- nib angle, nib pressure, contact state
- ink reservoir and dip state
- fatigue / tremor / rhythm
- carried state across glyphs, words, and lines

But the control law changes:
- proportional-derivative tracking follows the plan
- out-of-corridor error gets a strong corrective term
- contact and lift are explicit planned states
- joins are modeled as either planned contact segments or planned air transitions

This makes “physics” secondary to legible tracking, which is the right order.

### 3. `curriculum` — staged training and promotion
Training proceeds in five levels:

1. Primitive strokes
2. Single glyphs
3. Connected glyph pairs and common words
4. Full lines
5. Representative folios

Each level freezes a checkpoint before the next begins. No stage may advance on “looks promising” alone.

### 4. `handvalidate` — gate-based validation
Validation is first-class, not an afterthought. Every stage writes metrics, thresholds, and visual evidence.

### 5. `evofit` — exemplar-driven nominal form recovery
TD-014 now adds a bounded reuse of evo:

- fit glyph-level and, when necessary, short-word / short-join forms from real manuscript exemplars
- rank candidates using exemplar similarity and structural checks
- export accepted proposals into `pathguide`
- handflow then uses those guides as templates for stroke approach and flow

This lets TD-014 use evo where it is strong, without letting evo own page writing.

## Representation Details

### Dense guides over sparse keypoints
Sparse keypoints still matter, but only as annotations or coarse anchors. They are not the primary driver of geometry anymore.

Dense guides must encode:
- centerline geometry
- expected entry/exit tangents
- contact schedule
- speed schedule
- pressure schedule
- corridor width

That makes it possible to distinguish:
- “the intended ductus”
- “the allowable expressive variation”

### Common joins are separate assets
For cursive manuscript writing, joins are not a small detail. They are part of the writing system. TD-014 defines join guides for frequent transitions, not only standalone glyphs.

Initial join inventory:
- `u→n`
- `n→d`
- `d→e`
- `e→r`
- `r→space`
- `space→d`
- `m→i`
- `i→n`

This is enough to train proof phrases such as `und`, `der`, `in`, `mir`, `und der`.

### Automatic-first data admission
The training corpus should be assembled automatically where possible:
- segment lines, words, and letters automatically
- transcribe words automatically
- extract centerlines automatically
- build dense guides automatically from accepted traces

But automatic does not mean unfiltered. Every extracted sample is assigned one of:
- accepted
- soft accepted
- rejected

Promotion rules:
- promoted checkpoints train and validate only on accepted samples by default
- soft accepted samples may be used for exploratory runs, but not for checkpoint promotion unless explicitly approved
- rejected samples remain available for inspection and future recovery, but do not affect guide assets or metrics

### Corpus admission semantics
TD-014 now distinguishes clearly between automatic matcher output and reviewable exemplar truth.

Working tiers:
- `auto_admitted`: crops that cleared the current matcher thresholds
- `quarantined`: crops that remain plausible but are not fit for promotion
- `rejected`: crops that failed the current matcher or structural checks

Reviewable exemplar tier:
- `promoted_exemplars`: crops that passed the stronger exemplar gate and may be used as human-review evidence or nominal-form recovery input
- `reviewed_cleaned_exemplars`: reviewed glyph or join crops with an attached cleanup mask applied during freeze/export while preserving the raw reviewed crop separately

Rules:
- folders or dashboards may not label `auto_admitted` crops as if they were confirmed readable exemplars
- `promoted_exemplars` must be populated only after stronger validation than score threshold + margin
- `coverage_promoted` or fallback-filled samples may not enter `promoted_exemplars`
- corpus dashboards must report automatic admission coverage separately from promoted exemplar coverage
- evofit may begin exploratory nominal-form search from the automatic corpus, but promoted guide freeze may consume only `promoted_exemplars`
- reviewed cleanup must be non-destructive: raw reviewed bounds remain frozen, and cleanup is stored as an explicit mask or erase-stroke layer with separate provenance
- reviewed-cleaned crops may be preferred by reviewed evofit, but raw reviewed crops must remain inspectable and recoverable

### Resolution policy
Accuracy and writing quality take precedence over render cost.

Rules:
- extraction, segmentation, centerline tracing, width measurement, and guide generation run at the highest native resolution available
- dense guides are normalized into physical coordinates (`mm`, x-height-relative measures) after extraction so the controller is not tied to source pixel grids
- guided proof renders may use configurable internal supersampling above the current 400 DPI baseline when it materially improves stroke crispness or measurement fidelity
- final folio outputs must continue to satisfy existing downstream contracts unless and until a separate contract change is approved

### Exemplar-first nominal recovery
The current failure mode shows that exact symbol coverage is not enough. The active guides themselves must be readable.

TD-014 therefore inserts an explicit exemplar-fit phase between extraction and handflow curriculum:
- acquire a provenance-backed folio sample set from the target manuscript family
- build accepted exemplar corpora for glyphs and common joins
- fit nominal forms using evo at glyph level and selective short-word level
- freeze only accepted reviewed-evofit proposals as promoted guides, with raw-vs-cleaned reviewed provenance preserved
- render the nominal guides alone and confirm they are legible before controller dynamics are introduced

### Reviewed cleanup for contaminated crops
Manual reviewed annotation is still not enough if a correct glyph box contains stray strokes from neighboring characters, bleed-through, or line interference. TD-014 therefore adds a reviewed cleanup layer:

- the workbench may attach an erase/restore mask to an existing reviewed glyph or join annotation
- cleanup acts only on the reviewed crop export; it does not alter the source folio image or the raw reviewed bounds
- freeze/export must emit both raw and cleaned reviewed crops, plus cleanup provenance
- reviewed evofit prefers the cleaned reviewed crop when available, while retaining the raw crop for audit and rollback

Acceptance rules:
- every cleaned reviewed crop must preserve its raw reviewed counterpart
- cleanup masks must be attributable to a specific reviewed annotation and operator action history
- downstream bundles must disclose whether a fit source came from a raw reviewed crop or a cleaned reviewed crop

## Training Strategy

### Exemplar-fit prerequisite
Before Level 1 glyph training proceeds on a folio slice, the slice must have an accepted nominal guide set derived from exemplars.

Train on:
- 30–40 sampled folios from the target manuscript family or a tightly matched family
- automatically extracted glyph and join exemplars
- held-out crops for glyph-level readability checks

Goal:
- recover readable nominal forms from manuscript evidence instead of sparse or toy sketches

Acceptance gates:
- nominal glyph render legibility passes on held-out exemplar crops
- exact guide coverage = 1.0 for the promoted review slice
- exemplar-backed recognition beats the previous nominal guide set by a configured margin
- no promoted uppercase or diacritic form is merely a lowercase clone or normalization fallback

### Exemplar promotion gates
Automatic admission is not enough for nominal guide recovery.

A glyph or join may enter `promoted_exemplars` only if it satisfies all of:
- readable by a stronger proxy or direct review workflow
- cluster membership is stable against competing symbols
- not produced solely by coverage repair or fallback promotion
- trace/shape evidence remains consistent across at least one held-out split

This prevents misleading folders where unreadable crops appear under an "accepted" label merely because the matcher had no better option.

### Reviewed annotation workflow
When automatic exemplar recovery is not trustworthy, TD-014 uses a local reviewed-annotation workbench.

The workbench must support:
- opening harvested manuscript reference images locally
- viewing current exemplar coverage by symbol and join before labeling begins
- drawing bounding boxes for glyphs and joins directly on the source folio image
- assigning explicit labels such as `e`, `h`, `ů`, or `d->e`
- recording multiple samples per symbol across multiple manuscripts
- tagging annotation quality as `trusted`, `usable`, or `uncertain`
- freezing reviewed crops and annotation manifests as a separate dataset with full provenance

Rules:
- reviewed annotations are stored separately from automatic corpus tiers
- reviewed exports may seed evofit and nominal guide recovery directly
- automatic and reviewed sample counts must be reported side by side so remaining gaps stay visible
- join annotations are first-class assets, not implied by glyph proximity

Initial reviewed-annotation goals:
- expose exact sample counts for all required symbols and joins on the current review slice
- fill the blocking gaps and mislabeled cases in the promoted exemplar set
- seed a cleaner reviewed exemplar corpus for evo normalization across multiple documents

### Level 0 — primitives
Train on:
- vertical downstroke
- hairline upstroke
- minim pair
- bowl arc
- ascender loop
- pen lift

Goal:
- stable contact control
- stable corridor tracking
- clean nib rendering

Acceptance gates:
- corridor containment >= 0.98
- self intersections = 0
- contact classification accuracy >= 0.99
- width-profile error <= 0.15 normalized

### Level 1 — glyphs
Train on a small starter alphabet:
- `u`, `n`, `d`, `e`, `r`, `i`, `m`, `a`, `o`, `t`, `h`

Goal:
- recognizably legible letters before any full-word ambition

Acceptance gates:
- template/recognition score >= 0.90 on training glyphs
- DTW centerline distance <= 0.20 x-height
- zero uncontrolled exits outside corridor
- thick/thin ratio remains within configured script bounds

### Level 2 — joins and common words
Train on:
- `un`, `nd`, `de`, `er`, `in`, `mi`
- `und`, `der`, `wir`, `in`, `mir`

Goal:
- cross-glyph continuity with persistent hand state

Acceptance gates:
- join continuity score >= 0.90
- no forced lift inside guides marked as contact joins
- word recognition score >= 0.88
- baseline drift <= 0.15 x-height within word

### Level 3 — lines
Train on short manuscript-like lines:
- 3 to 5 words
- then 6 to 10 words

Goal:
- rhythm, spacing, and state carryover across words

Acceptance gates:
- line OCR proxy >= 0.85
- spacing CV within calibrated band
- no catastrophic drift in slant, x-height, or baseline
- dip cycle and pressure variation remain inside allowed envelope

### Level 4 — folios
Render representative folios:
- clean baseline page
- pressure-heavy page
- multi-sitting page
- fatigue page

Goal:
- integrate with page layout and existing output contracts

Acceptance gates:
- page render remains deterministic for fixed seed
- PAGE XML coordinates remain valid
- current Weather pipeline accepts the output without modification
- manuscript-level regression metrics are no worse than the evo baseline by more than an agreed tolerance on readability-critical measures

## Measurement Logic

### Structural metrics
- corridor containment ratio
- self-intersection count
- missed-anchor count
- exit tangent error
- lift/contact confusion rate

### Shape metrics
- DTW distance between rendered and reference centerlines
- curvature histogram distance
- normalized Hausdorff distance
- width profile error
- pressure profile error

### Legibility metrics
- glyph recognizer accuracy on held-out examples
- word recognizer accuracy on proof vocabulary
- OCR proxy score on lines and pages

### Page metrics
- baseline drift per line
- spacing distribution shift
- x-height stability
- join continuity rate

### Data-quality metrics
- accepted / soft / rejected sample counts per glyph and join
- automatic transcription confidence distribution
- held-out versus training split coverage by glyph, join, word, and line
- guide provenance report linking each dense guide to source crops and extraction runs

### Rollout metrics
- A/B diff versus evo baseline
- human-review snapshots for proof words and proof folios
- downstream import check into PAGE XML / Weather

Every training run must emit:
- JSON metrics
- per-stage snapshot images
- accepted/rejected gate decisions
- checkpoint metadata (parent checkpoint, training set, commit hash)
- dataset admission summary (accepted / soft / rejected counts, source resolution, held-out split)

## Implementation Sequence

1. Define dense guide schema and import/export path.
2. Define automatic-first data admission and confidence-tier policy.
3. Build stage gates before rewriting the controller.
4. Implement corridor-following controller with planned-state tracking.
5. Train primitives.
6. Expand guide dataset to starter alphabet + joins.
7. Train glyphs and joins.
8. Add persistent state across glyphs and words.
9. Train words and lines.
10. Integrate into folio renderer behind a feature flag.
11. Promote only if folio regression bench passes.

## Rollout Policy

The current `evo` renderer remains the production default until TD-014 passes the folio gate.

Evo reuse policy:
- evo may propose nominal glyphs and short joins
- evo may not write promoted folio pages for TD-014
- handflow remains the only renderer eligible for promotion on this track

Feature-flag progression:
- `render-word --approach guided`
- `render-line --approach guided`
- `render --approach guided --feature-flag`
- only later consider making it non-experimental

Rollback is simple:
- disable the guided-hand flag
- keep all existing folio contracts and renderers unchanged

## Definition of Success
TD-014 succeeds when the repo has a hand-model path that is:

- legible at word and line level
- measured and gated at every stage
- physically expressive inside constrained corridors
- able to render proof folios without breaking downstream contracts

If it cannot beat or at least match the evo path on readability-critical metrics by the folio gate, it remains an experimental path and is not promoted.

## Post-Bench Findings

The first folio review bench surfaced a critical limitation in the current TD-014 implementation:

- the controller and renderer can now satisfy folio contracts and produce stable, expressive trajectories
- but the rendered text can still be unreadable because missing glyphs are silently substituted through fallback aliases
- examples observed in the current repo path include `s -> r`, `v -> u`, `z -> r`, and `ů -> u`

This means the system can pass shape-based or path-based checks while still rendering the wrong text.

From this point forward, TD-014 must distinguish clearly between:

- motion fidelity: did the hand move plausibly?
- shape fidelity: did the trajectory follow the intended guide?
- text fidelity: did the rendered output use the correct symbol inventory for the intended manuscript text?

The first two are no longer enough by themselves.

## Readability Recovery Sequence

After the initial folio bench, the next implementation track is:

1. Exact character coverage gates
   - surface exact/normalized/alias resolution explicitly in session data
   - fail review/rollout benches when aliases are used
   - emit exact character coverage and alias substitution metrics

2. Active folio alphabet expansion
   - build exact guides for the active character inventory in the proof folios
   - prioritize missing lowercase forms, capitals, and diacritics that appear in benchmark lines
   - stop relying on wrong-shape fallback aliases for production review lines

3. Exact-symbol rendering path
   - render the controller's actual trajectory for folio output
   - keep guide-aligned trajectories only for evaluation alignment
   - add an exact-symbol-only review mode that refuses unresolved characters

4. Exemplar-fit nominal guide recovery
   - sample 30–40 manuscript folios through the existing IIIF/reference-selection tooling
   - extract accepted glyph and join exemplars for the active review alphabet
   - run evo fitting only to recover nominal glyph forms and difficult joins
   - freeze accepted evo proposals as the guide set consumed by handflow

5. Folio-specific curriculum refresh
   - train and validate on real manuscript words and line slices from the proof folios
   - require exemplar-fit nominal guides and exact character coverage before any readability/organicness promotion claim

## Additional Rollout Gates

For review and promotion benches, TD-014 now additionally requires:

- exact character coverage = 1.0 on promoted folio cases
- alias substitution count = 0 on promoted folio cases
- normalized substitution count = 0 unless explicitly approved for a temporary exploratory run

If these gates fail, the output is not considered readable enough for rollout, even if the controller and visual metrics otherwise look strong.

## Parameter Activation Recovery

The current reviewed proof studies exposed a second structural limitation in TD-014:

- the hand profile exposes many expressive parameters
- but the active `handflow` path only responds to a small subset of them
- proof sheets can therefore look almost unchanged even when multiple profile values are varied

This means TD-014 cannot yet use parameter studies as credible evidence of expressivity, because several profile knobs are effectively inert in the current controller/render path.

From this point forward, TD-014 must distinguish between:

- exposed parameters: values present in `HandProfile`
- activated parameters: values that measurably change guided output
- promoted parameters: activated values that improve legibility or controlled expressivity without breaking corridor or nominal-guide gates

### Activation Order

TD-014 should activate profile parameters in this order:

1. pressure baseline and pressure shaping
   - `folio.base_pressure`
   - related nib pressure multipliers already used by the controller

2. per-glyph vertical placement variation
   - `glyph.baseline_jitter_mm`

3. deterministic micro-instability
   - `folio.tremor_amplitude`

4. bounded nominal-path deformation
   - `glyph.warp_amplitude_mm`

The first two are the safest because they can create visible variation while preserving glyph identity. Tremor and warp are still important, but they must be corridor-bounded and validated against legibility gates before they are used in promoted proof or folio renders.

### Activation Requirements

For a parameter to count as activated in TD-014:

- it must affect the active reviewed handflow path, not only legacy or non-guided renderers
- a focused proof study must show a visible and measurable difference when the parameter changes
- the difference must be deterministic for fixed inputs
- the parameter must have a validation bound so it cannot destroy readability unnoticed

### Parameter Sensitivity Evidence

TD-014 therefore adds a dedicated parameter-sensitivity track:

- activate a small set of high-value parameters in `handflow`
- generate proof sheets where only activated parameters are varied
- compute per-parameter output deltas so inert parameters fail fast
- refuse to treat unwired profile fields as tuning evidence

This closes the current gap where the repo exposes more expressive controls than the reviewed guided path actually uses.
