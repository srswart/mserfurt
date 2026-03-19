# Solution Intent — Weather (Phase 1)

This document captures **how we intend to solve** Phase 1 (architecture + constraints). It is not a task plan and not an outcome record.

## Phase 1 intent
Produce a `weather` tool that takes ScribeSim page images of *MS Erfurt Aug. 12°47* and applies physically motivated aging effects matching the CLIO-7 apparatus description: 560 years of archival storage, water damage to folios 4r–5v, missing corner on 4v, different vellum stock for the final gathering, and professional digitization artifacts.

## Core decisions
### Implementation language (Stage 0)
- **Python** for orchestration: CLI, profile loading, per-folio damage map from XL manifest, effect stacking, PAGE XML coordinate updates.
- **Rust** (via PyO3/maturin) for image processing: texture generation, convolution effects, geometric transforms, compositing.
- The Rust crate (`weather_fx`) exposes per-effect functions operating on numpy arrays via PyO3.
- Optional GPU path via `wgpu` in Phase 2; Phase 1 is CPU-only with Rust acceleration.

### Effect architecture
- Each effect is a **pure function**: `(input_image, parameters, rng) → (output_image, coordinate_transform)`.
- Effects compose in a physically motivated order (substrate → ink → damage → aging → optics).
- The compositor chains coordinate transforms for ground truth update.
- Per-folio damage is driven by the XL manifest: the compositor reads damage annotations and selectively enables effects per folio.

Rationale:
- Pure-function effects are testable in isolation and deterministically reproducible.
- The manifest-driven approach ensures CLIO-7 fidelity: if the manifest says f04v has a missing corner, Weather applies the corner loss; if it says f10r has no damage, Weather applies only general aging.

### Restraint principle
This manuscript was stored carefully for 560 years. The default aesthetic is **quiet aging**, not dramatic degradation. The weathering profile for MS Erfurt Aug. 12°47 is calibrated to:
- Vellum that has yellowed but is structurally sound
- Ink that has shifted from black to dark brown but remains legible
- Minimal foxing (dry archive)
- Minimal handling wear (the manuscript was hidden, not frequently consulted)
- Localized water damage where specified, but nowhere else

## Compositing order
1. `vellum_texture` — background substrate generation
2. `vellum_color` — parchment tint (two stocks: standard warm cream, irregular slightly different)
3. `vellum_translucency` — verso bleed-through
4. *ScribeSim image composited onto substrate*
5. `ink_bleed` — very slight lateral spread (centuries of iron gall on vellum)
6. `ink_fade` — black → dark brown shift
7. `ink_flake` — minimal, only on heaviest strokes
8. `water_damage` — **f04r–f05v only**: directional staining from above
9. `missing_corner` — **f04v only**: lower-right corner loss
10. `edge_darkening` — all folios
11. `foxing` — light, all folios
12. `binding_shadow` — gutter side, all folios
13. `page_curl` — very slight, consistent with professional digitization
14. `camera_vignette` — mild
15. `lighting_gradient` — mild, professional digitization quality

## Weathering profile — MS Erfurt Aug. 12°47
```toml
[meta]
name = "ms_erfurt_560yr"
description = "560 years of careful archival storage in the Erfurt Augustinian archive"
seed = 0  # 0 = derive from folio ID hash
target_manuscript = "MS Erfurt Aug. 12°47"

# --- SUBSTRATE ---

[substrate.vellum_texture]
enabled = true
grain_scale = 0.6           # moderate grain visibility
follicle_density = 0.2      # calfskin has fewer follicle marks than sheepskin
thickness_variation = 0.10

[substrate.vellum_color]
enabled = true
# Standard stock (f01–f13)
standard_base_hue = 38      # warm cream, yellowed with age
standard_saturation = 0.22
standard_lightness_mean = 0.80
standard_lightness_stddev = 0.03
# Irregular stock (f14–f17): slightly different — "taken from a sheet
# intended for something else"
irregular_base_hue = 42     # slightly more yellow
irregular_saturation = 0.20
irregular_lightness_mean = 0.78
irregular_lightness_stddev = 0.04

[substrate.vellum_translucency]
enabled = true
bleed_opacity = 0.06        # subtle — this is relatively thick calfskin

# --- INK AGING ---

[ink.fade]
enabled = true
# Iron gall ink after 560 years: shifted from black to dark brown
global_fade = 0.20
color_shift = [8, -3, -12]  # RGB: slight warm shift (toward brown)

[ink.bleed]
enabled = true
spread_px = 1.0             # very slight — well-stored vellum

[ink.flake]
enabled = true
probability = 0.008         # minimal — careful storage
cluster_size = 2
pressure_threshold = 0.85   # only heaviest strokes affected

# --- TARGETED DAMAGE ---

[damage.water_damage]
enabled = false              # overridden per-folio by manifest
# When enabled (f04r–f05v):
direction = "from_above"
origin_edge = "top"
max_penetration_fraction = 0.6   # water reached ~60% down the page on worst folio
tide_line_contrast = 0.15
ink_dissolution_strength = 0.4   # moderate — some text lost but much remains
vellum_darkening = 0.12

[damage.missing_corner]
enabled = false              # overridden per-folio by manifest
# When enabled (f04v only):
corner = "bottom_right"
tear_depth_mm = 35           # significant corner loss
tear_width_mm = 28
irregularity = 0.65
backing_color = [45, 42, 38]  # dark conservation board

# --- GENERAL AGING ---

[aging.edge_darkening]
enabled = true
width_mm = 8
max_darkening = 0.15         # subtle — edges handled over centuries but not heavily

[aging.foxing]
enabled = true
spot_count = 12              # light — dry archive
spot_diameter_range_mm = [0.3, 1.5]
color_shift = [12, -2, -10]

[aging.binding_shadow]
enabled = true
width_mm = 10
max_darkening = 0.12         # light — informal binding

# --- DIGITIZATION ---

[optics.page_curl]
enabled = true
max_displacement_mm = 1.0    # very slight — professional digitization
edge = "left"                # gutter side

[optics.camera_vignette]
enabled = true
strength = 0.08              # mild — modern equipment

[optics.lighting_gradient]
enabled = true
direction_degrees = 150      # light from upper-left
intensity_range = [0.95, 1.02]  # very even — professional setup
```

## Effect implementations (Phase 1)
### Vellum texture
- Multi-octave Perlin noise (3 octaves) for base texture
- Follicle marks: Poisson-distributed, elongated along grain direction (vertical for vellum)
- Two stock variants: standard (f01–f13) and irregular (f14–f17) with slightly different noise seed and color
- Optional: blend with tiled vellum photograph sample for additional realism

### Iron gall ink aging
- **Fade:** multiply ink pixel darkness by `(1 - global_fade)`, then apply color shift (black → dark brown). The shift models iron gall oxidation: Fe²⁺ complexes darkening then fading over centuries.
- **Bleed:** Gaussian blur applied only to ink pixels (threshold-detected), radius 1.0px. Models centuries of slight corrosive spread into vellum.
- **Flake:** remove ink in small clusters where ScribeSim pressure heatmap exceeds threshold. The heaviest strokes deposited the most ink, which is also where flaking is most likely. Minimal for this well-stored manuscript.

### Water damage (f04r–f05v)
- **Direction model:** water entered from above. The damage map is a gradient: strongest at top of page, diminishing downward. On f04r (first affected), penetration is moderate. On f04v–f05r, it is at maximum. On f05v (last affected), it is diminishing.
- **Tide line:** the boundary of the wetted area is rendered as a characteristic brown ring (mineral deposits from evaporating water). Generated via diffusion-limited aggregation from the top edge, then the boundary extracted as a contour.
- **Ink dissolution:** within the wetted area, ink darkness is reduced by `ink_dissolution_strength`. Not total — iron gall ink is reasonably water-resistant after decades of curing, but prolonged exposure dissolves some.
- **Vellum darkening:** the wetted area is slightly darker/more discolored than surrounding vellum.
- **Text legibility:** most text within the damaged area should remain partially legible — matching CLIO-7's reconstructed passages (60–80% confidence means "hard to read" not "completely gone").

### Missing corner (f04v)
- **Tear path:** random walk from the corner point inward, biased along vellum grain direction, with `irregularity` parameter controlling raggedness.
- **Material removal:** the torn region is replaced with the backing color (conservation board or shelf surface).
- **Edge treatment:** 1–2px of fiber fraying along the tear path.
- **Ground truth:** any glyph whose bounding box overlaps the torn region is marked `@damaged="true"` in PAGE XML. CLIO-7 says "the lower right corner of folio 4v is missing entirely" and "CLIO-7 has not attempted to reconstruct the missing corner" — so text in this region should be genuinely lost.

### Edge darkening
- Darkening gradient from all four edges inward, strongest at corners.
- Width ~8mm. Maximum darkening 15%.
- Represents centuries of handling and atmospheric exposure at the edges of a bound gathering.

## Ground truth update pipeline
### Coordinate transform chain
- `page_curl` produces a sinusoidal displacement field → coordinate transform recorded.
- `missing_corner` produces a binary mask → glyphs in the masked region marked damaged.
- `water_damage` produces a damage intensity map → glyphs in high-damage zones receive `@legibility` attribute (0.0–1.0).
- Transforms composed and applied to PAGE XML in a single pass after all effects.

### Damage annotations in PAGE XML
```xml
<Glyph id="g_0247" damaged="true" legibility="0.0">
  <!-- glyph in missing corner: completely lost -->
</Glyph>
<Glyph id="g_0185" damaged="true" legibility="0.65">
  <!-- glyph in water-damaged zone: partially legible -->
</Glyph>
```

## Per-folio effect dispatch (manifest-driven)
The compositor reads XL's manifest and the weathering profile to decide which effects to apply per folio:

```python
for folio in manifest.folios:
    effects = base_effects.copy()  # substrate + ink aging + general aging + optics

    if folio.damage and folio.damage.type == "water":
        effects.insert_at_position(8, water_damage(
            direction="from_above",
            penetration=folio.damage.extent_fraction
        ))

    if folio.damage and folio.damage.type == "missing_corner":
        effects.insert_at_position(9, missing_corner(
            corner=folio.damage.corner,
            depth=folio.damage.depth_mm
        ))

    if folio.vellum_stock == "irregular":
        effects.replace("vellum_color", vellum_color_irregular)

    compositor.apply(folio.image, effects, seed=hash(folio.id))
```

## Determinism + reproducibility
- All stochastic processes use seeded PRNG, default seed = hash(folio_id + profile_name).
- Weathering metadata JSON records per-folio: input hash, effect list, per-effect seeds, software version.
- Explicit `--seed` overrides for testing.

## eScriptorium integration
### Full manuscript import
1. Create eScriptorium project: "MS Erfurt Aug. 12°47"
2. Import seventeen weathered folio images as document pages
3. Import updated PAGE XML as segmentation + transcription
4. The result: a complete eScriptorium document that looks like a digitized medieval manuscript, with ground truth

### HTR evaluation workflow
1. Import clean ScribeSim images → train Kraken model on "perfect" data
2. Import weathered Weather images → evaluate same model on degraded data
3. Measure CER difference → quantifies how much weathering degrades HTR performance
4. Use weathered images as training data → build more robust models

## Testing strategy (Phase 1)
- **Effect isolation tests:** each effect in isolation → expected visual properties
- **Compositing order tests:** effects in correct order, no ordering artifacts
- **Per-folio dispatch tests:** manifest with water damage on f04r → water damage applied only to f04r, not f10r
- **Coordinate accuracy tests:** page curl → ground truth shift ≤ 2px
- **Damage zone tests:** missing corner on f04v → overlapping glyphs marked damaged
- **Water damage direction tests:** damage strongest at top of page, diminishing downward
- **Vellum stock tests:** f14r uses irregular stock parameters, f01r uses standard
- **Determinism tests:** same input + profile + seed → bitwise identical output
- **Integration test:** full pipeline → seventeen weathered folios import into eScriptorium

Development discipline:
- default commit sequence: tidy → test → implement

## Repository layout (suggested)
- `weather/` (Python package)
  - `cli.py`
  - `substrate/` — vellum texture, color (two stocks), translucency
  - `ink/` — iron gall aging (fade, bleed, flake)
  - `damage/` — water damage (directional), missing corner (tear path)
  - `aging/` — edge darkening, foxing, binding shadow
  - `optics/` — vignette, page curl, lighting
  - `compositor.py` — manifest-driven effect dispatch and layer stacking
  - `groundtruth/` — PAGE XML coordinate update, damage annotation
  - `models/` — data classes
- `weather-fx/` (Rust crate, PyO3)
  - `src/perlin.rs`, `src/texture.rs`, `src/damage.rs`, `src/stain.rs`, `src/transform.rs`, `src/composite.rs`
- `profiles/`
  - `ms-erfurt-560yr.toml` — the canonical profile for MS Erfurt Aug. 12°47
  - `light-archival.toml` — generic light aging preset
  - `heavy-handling.toml` — generic heavy aging preset (for other manuscripts)
- `textures/` — optional vellum photograph samples (with licensing notes)
- `examples/`, `tests/`, `docs/`

## Out of scope (Phase 1)
- 3D page geometry
- Physical ink chemistry simulation
- Palimpsest or erasure simulation
- Fire damage
- Animated aging sequences
- IIIF tile serving
- GPU-mandatory processing
- Conservation repair simulation
