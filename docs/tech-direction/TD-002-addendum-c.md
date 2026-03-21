# TD-002 Addendum C — Alignment with TD-005 (Generative Hand Model)

## Context
TD-002 Rev B is implemented. TD-005 introduces a generative hand model that changes how several TD-002 concepts are realized in code. This addendum maps TD-002 components to their TD-005 implementation status.

---

## Part 1: Multi-Scale Movement Model — Implementation Mapping

TD-002 Part 1 defined five scales (folio → line → word → glyph → stroke) with each scale inheriting dynamics from the one above. Under TD-005, these scales are **still the correct conceptual model** but they are implemented differently:

### Scale 1: Folio (writing session) — **no change**
`FolioState` (page rotation, ruling imperfection, ink level, base pressure, tremor) is initialized before the hand simulator starts and feeds into `HandState` as initial conditions. Implementation remains as-is.

### Scale 2: Line (arm positioning) — **implemented by hand simulator**
`LineState` (start_x variance, baseline undulation, margin compression) was previously a positioning calculation. Under TD-005, these become **target adjustments** — the hand simulator's targets for each line are offset by the ruling imperfection and the baseline undulation model. The hand doesn't follow the ruled line exactly; it follows the *intended* baseline, which itself deviates from the ruled line.

**What to change:** extract the baseline undulation computation from the current line-positioning code and feed it into the hand simulator's target generation. The undulation model itself doesn't change — it just drives target positions instead of glyph positions.

### Scale 3: Word (hand positioning) — **implemented by hand simulator**
`WordState` (spacing, slant drift, speed factor) was previously applied as per-word parameter overrides. Under TD-005, these become modifications to the hand simulator's state at word boundaries:
- Word spacing → the hand lifts and repositions; the repositioning distance is drawn from the word spacing distribution
- Slant drift → the hand's nib angle or target slant shifts slightly at each word boundary
- Speed factor → the hand simulator's `base_tempo` adjusts per word

**What to change:** the word-level parameter adjustments now happen inside the hand simulator's `plan_word()` function rather than as external overrides. The distributions and ranges remain the same.

### Scale 4: Glyph — **replaced by letterform guides**
The `GlyphInstance` with its base trajectory, warp, and entry angle adaptation is **superseded by TD-005's letterform guides**. Instead of a complete trajectory that gets warped, each letter is a set of keypoints that the hand steers through.

**What to change:** replace the glyph trajectory lookup + warp with the keypoint-based target generation from TD-005. The trajectory warping concept (correlated control-point displacement) is no longer needed — natural variation emerges from the hand's continuous dynamics.

### Scale 5: Stroke — **replaced by hand simulator's continuous mark emission**
Individual `StrokeInstance` objects with explicit Bézier curves are **superseded by the hand simulator's continuous output.** The hand moves through space and emits marks whenever the nib is in contact — there is no discrete "stroke" object.

**What to change:** the stroke renderer still rasterizes curves with nib-angle-dependent width, but the curves come from the hand simulator's sampled output rather than from pre-defined Bézier segments. The nib physics (width equation from TD-002-A, pressure model) remain exactly as implemented.

---

## Part 2: Ink-Substrate Material Interaction — **no change**

The ink state model, vellum surface interaction, and stroke overlap darkening from TD-002 Part 2 remain as-is. These operate on the marks produced by the renderer regardless of whether those marks came from placed glyphs or from the hand simulator.

The rendering pipeline passes are unchanged:
- Pass 1 (Geometry): now comes from the hand simulator instead of glyph placement
- Pass 2 (Ink Deposit): no change
- Pass 3 (Pressure Map): no change
- Pass 4 (Fine Detail Filters): no change
- Pass 5 (Ground Truth Extraction): no change — bounding polygons are computed from rendered marks
- Pass 6 (Composition): no change

---

## Part 3: What Stays, What Moves, What Goes

| TD-002 Component | Status under TD-005 |
|---|---|
| Nib model (TD-002-A) | **Stays** — foundation of mark-making |
| Direction-dependent width (TD-002-C) | **Stays** — the core thick/thin equation |
| Multi-scale hierarchy (Part 1) | **Stays as concept**, implementation moves into hand simulator |
| Folio state | **Stays** — initializes hand simulator |
| Ruling imperfection | **Stays** — feeds into target generation |
| Baseline undulation | **Stays** — feeds into target generation |
| Glyph trajectories (TD-002-B) | **Goes** — replaced by letterform guides |
| Inter-letter connections (TD-002-D) | **Goes** — emergent from hand dynamics |
| Structured variation (TD-002-E) | **Goes** — emergent from hand state evolution |
| Reference extraction (TD-002-F) | **Moves** — now extracts writing paths for hand training, not glyph templates |
| Ink state model (Part 2) | **Stays** — post-process on hand simulator output |
| Vellum interaction (Part 2) | **Stays** — post-process |
| Rendering pipeline (Part 3) | **Stays** — Pass 1 input source changes, Passes 2-6 unchanged |

---

## Action items

1. Extract baseline undulation and ruling imperfection from current line-positioning code into a `target_generation` module that the hand simulator calls
2. Extract word-level parameter adjustments into the hand simulator's `plan_word()` interface
3. Keep nib physics, ink model, and rendering passes 2-6 exactly as implemented
4. The glyph trajectory code can remain in the codebase as a fallback renderer (per TD-005's risk mitigation) but the primary path becomes the hand simulator
