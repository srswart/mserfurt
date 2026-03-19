# Weather ("weather") — Project Brief

## Purpose
Build **Weather**: a manuscript aging and weathering engine that takes the page images from ScribeSim and applies vellum texture, physical degradation, and environmental aging to produce images consistent with a manuscript that has survived approximately 560 years in an Augustinian archive — found in 2019 "undamaged except by age," with specific damage to folios 4r–5v as described in the CLIO-7 apparatus. Weather is the final stage of the XL → ScribeSim → Weather pipeline for producing the physical artifact of *MS Erfurt Aug. 12°47*.

**Phase 1 outcome:** a CLI tool named `weather` that takes ScribeSim page images and applies a configurable stack of weathering effects, producing output that matches the physical description in CLIO-7's apparatus: a document stored for centuries between two other books, "undamaged except by age" on most folios, with water damage to 4r–5v, a missing corner on 4v, and the general patina of a five-and-a-half-century-old vellum manuscript.

## Why this exists
The CLIO-7 apparatus gives us a specific physical description to match. This is not generic "make it look old" — it is a defined target:
- **Storage condition:** bound between a Breviarium and a Lectionary in the Augustinian archive. This means consistent, sheltered storage — the manuscript is not heavily damaged.
- **Age:** approximately 560 years (1457–2019). Vellum yellows, ink oxidizes, edges darken.
- **Water damage (f04r–f05v):** "consistent with liquid exposure from above, suggesting the manuscript was stored open, or read in conditions of moisture." This is localized, not catastrophic.
- **Missing corner (f04v):** "the lower right corner of folio 4v is missing entirely." Physical loss of material.
- **Different vellum stock (f14r onward):** "smaller, cut unevenly, as though taken from a sheet intended for something else." Different base material characteristics.
- **General condition:** "undamaged except by age" on most folios. The manuscript is well-preserved by medieval standards.

Weather must produce exactly this: a mostly-intact manuscript with targeted damage where CLIO-7 says it exists, and the quiet general aging of five centuries elsewhere.

## Phase 1 scope (MVP)
### Input
- ScribeSim page images (PNG, 300 DPI) for all seventeen folios
- ScribeSim PAGE XML ground truth
- ScribeSim pressure heatmaps
- XL folio manifest (damage annotations, vellum stock metadata)
- Weathering profile (TOML)

### CLI deliverable
A `weather` executable (Python, with Rust acceleration for image processing) with:
- `weather apply <image.png> -p <profile.toml> -o <output.png>` — weather a single page
- `weather apply-batch <input_dir> -p <profile.toml> -o <output_dir>` — weather all pages
- `weather apply-batch <input_dir> -p <profile.toml> --manifest <manifest.json> -o <output_dir>` — weather with per-folio damage from XL manifest
- `weather preview <image.png> -p <profile.toml>` — reduced resolution preview
- `weather groundtruth-update <page_xml> <output.png> -o <updated.xml>` — update PAGE XML for geometric distortion
- `weather catalog` — list available effects
- `weather --version`, `weather --help`

### Weathering effects (Phase 1)
**Substrate effects**
- `vellum_texture`: grain pattern, follicle marks, thickness variation
- `vellum_color`: parchment base color — warm cream for standard folios, slightly different tone for f14r onward (different stock)
- `vellum_translucency`: bleed-through of text from verso

**Ink degradation (560 years of iron gall ink on vellum)**
- `ink_fade`: global darkening reduction consistent with iron gall oxidation — the ink has gone from black to dark brown
- `ink_bleed`: very slight lateral spread (iron gall ink is mildly corrosive to vellum over centuries)
- `ink_flake`: minimal — this manuscript was stored carefully. Perhaps slight flaking on the heaviest strokes (uses pressure heatmap to target)

**Targeted damage (from CLIO-7 apparatus)**
- `water_damage`: applied to f04r–f05v. "Consistent with liquid exposure from above." Produces tide-line staining, localized ink dissolution, and darkened/warped vellum in the affected area. The damage is worst at top of page, diminishing downward (exposure from above).
- `missing_corner`: applied to f04v. Lower right corner removed. Tear path follows vellum grain direction. Backing material (the shelf or conservation board) visible through the gap.

**General aging**
- `edge_darkening`: vellum edges darken over centuries of handling and exposure
- `foxing`: light — the Augustinian archive was relatively dry, but some biological spotting over 560 years is expected
- `binding_shadow`: the folio gathering was bound (though informally, inserted between other books). Slight gutter darkening.

**Optical / digitization effects**
- `camera_vignette`: mild — consistent with modern high-quality digitization (the "2019 cataloguing" that discovered the manuscript)
- `page_curl`: very slight — consistent with a carefully digitized folio
- `lighting_gradient`: mild — professional digitization lighting with slight falloff

### Per-folio damage map (from XL manifest)
| Folio | Specific damage | General aging |
|---|---|---|
| f01r–f03v | None | Standard 560-year aging |
| f04r | Water damage (from above, partial) | Standard aging + water |
| f04v | Water damage + missing lower-right corner | Standard aging + water + corner loss |
| f05r–f05v | Water damage (diminishing) | Standard aging + water (lighter) |
| f06r–f13v | None | Standard 560-year aging |
| f14r–f17v | None, but different vellum stock | Standard aging on irregular vellum; may age slightly differently |

### Output
- Weathered PNG per folio (same dimensions, or modified if corner is missing)
- Updated PAGE XML with coordinates adjusted for geometric distortion and glyphs in damaged zones marked
- Weathering metadata JSON per folio (effects applied, parameters, seeds)

### Integration with eScriptorium
- Output images replace ScribeSim clean images in the eScriptorium document
- Updated PAGE XML maintains valid segmentation
- The full seventeen-folio set can be imported as a single eScriptorium document: "MS Erfurt Aug. 12°47"
- Weathered output serves as realistic test data for HTR models: Kraken should be able to transcribe most folios, struggle on water-damaged ones

### Developer experience (Phase 1)
- Deterministic output for same input + profile + seed
- Per-effect toggles
- Diagnostic mode: each effect layer rendered separately
- Preview mode for rapid iteration

## Non-goals (Phase 1)
- Fire or severe physical destruction
- Palimpsest simulation
- 3D page geometry
- Physical simulation of ink chemistry
- Color illustration weathering (no illustrations in this manuscript)
- Real-time preview
- GPU-mandatory processing

## Design principles (project constraints)
- **CLIO-7 fidelity:** the weathering must match the physical description in the apparatus. Water damage from above on 4r–5v. Missing lower-right corner on 4v. Undamaged except by age elsewhere. This is a defined target, not artistic license.
- **Restrained aging:** this manuscript was stored carefully in a library for 560 years. It is not a battle-damaged codex. Most weathering effects should be subtle. The water damage is the exception, and even that is localized.
- **Effect composability:** each effect is an independent, stackable layer.
- **Ground truth preservation:** geometric distortion updates PAGE XML coordinates. Damage zones mark affected glyphs.
- **Reproducibility:** same input + profile + seed = identical output.

## ARRIVE governance plan
We run Weather development with outcome-first discipline:
- work as a sequence of small, reviewable Advances
- keep changes within the reviewability budget
- follow **Tidy First → Test First → Implement** as default execution order

### Weather system + components (initial)
System: `weather`

Components (all **incubating** initially):
- `cli` — command-line driver, batch orchestration
- `substrate` — vellum texture, color, translucency (two vellum stocks: standard and irregular)
- `ink` — iron gall ink aging (fade to brown, minimal bleed, minimal flake)
- `damage` — targeted damage: water stain with directional flow, missing corner with tear path
- `aging` — general aging: edge darkening, foxing, binding shadow
- `optics` — digitization artifacts: vignette, curl, lighting
- `compositor` — effect stacking, layer compositing
- `groundtruth` — PAGE XML coordinate update, damage zone annotation
- `tests` — golden image tests, ground truth consistency, per-folio damage accuracy
- `docs` — weathering profile guide, CLIO-7 damage mapping, eScriptorium integration

## Phase plan
### Phase 1 — "560 years in sixty seconds"
Deliver the minimal end-to-end pipeline:
1. Load ScribeSim images + ground truth + pressure heatmaps
2. Load XL manifest for per-folio damage map
3. Generate vellum substrate (two stocks: standard and irregular)
4. Apply iron gall ink aging across all folios
5. Apply water damage to f04r–f05v with directional flow (from above)
6. Apply missing corner to f04v
7. Apply general aging (edge darkening, foxing, binding shadow) to all folios
8. Apply digitization optical effects
9. Update PAGE XML coordinates and damage annotations
10. Produce the complete seventeen-folio weathered manuscript

### Phase 2 (preview)
- Physically-based iron gall ink model (pH-dependent corrosion)
- Conservation treatment simulation (repairs visible under UV)
- Multi-page binding simulation (consistent gutter wear across gathering)

### Phase 3 (preview)
- Time-lapse aging mode (view the manuscript at 100-year intervals)
- IIIF tile serving for the complete weathered manuscript
- Integration with mirador viewer

## Definition of Done (Phase 1)
- `weather apply-batch scribesim-out/ -p profiles/ms-erfurt-560yr.toml --manifest xl-out/manifest.json -o weathered/` produces seventeen weathered folio images
- Folios f04r–f05v show water damage from above; f04v has missing lower-right corner
- Remaining folios show restrained aging consistent with careful archival storage
- f14r–f17v show slightly different vellum tone (different stock)
- Updated PAGE XML imports into eScriptorium; damaged glyphs on f04r–f05v are marked
- All effects are individually toggleable in the profile TOML
- Automated tests cover: compositing order, coordinate accuracy (≤ 2px drift), damage zone placement, folio-specific effect application, deterministic output
- Repo includes the `ms-erfurt-560yr.toml` profile, effect catalog, and eScriptorium import walkthrough

## Key risks + mitigations
- **Water damage realism:** directional water staining is complex to simulate convincingly. Study real water-damaged manuscripts (publicly available digitizations from e-codices, Gallica, etc.) for reference tide-line patterns.
- **Vellum texture:** supplement procedural generation with tiled samples from public-domain vellum photographs.
- **Over-weathering:** the manuscript is described as well-preserved. Resist the temptation to add dramatic damage. Provide "archival-quality" and "heavily-handled" presets; default to archival.
- **Ground truth drift:** validate coordinate accuracy after every geometric effect.

## Success metrics (Phase 1)
- Can weather all seventeen folios in ≤ 90 seconds on commodity hardware (CPU-only)
- Ground truth coordinates accurate to ≤ 2px after geometric distortion
- Water damage on f04r–f05v is visually consistent with "liquid exposure from above"
- Missing corner on f04v looks like torn vellum, not a software crop
- Kraken HTR model achieves ≤ 10% CER on non-damaged folios; higher CER on water-damaged folios (demonstrating realistic challenge)
- At least one person unfamiliar with the project, shown the weathered output, does not immediately identify it as computer-generated
