# Tech Direction: TD-011 — AI-Assisted Weathering with Codex-Coherent Damage

## Status
**Proposed** — alternative/complement to the procedural Weather pipeline.

## Context
The procedural weathering pipeline (TD-002/Weather) produces technically correct but visually unconvincing results. Each effect (vellum texture, foxing, edge darkening, water staining) is implemented individually and they don't compose into the holistic look of a real aged document.

Experiment: passing the clean ScribeSim output to an AI image model with a structured weathering prompt produces dramatically more convincing results. The model has learned from millions of photographs of aged documents and applies that understanding holistically.

TD-011 defines a hybrid approach: ScribeSim produces precise, ground-truth-accurate clean text; an AI image model applies visually convincing weathering guided by structured prompts derived from CLIO-7 metadata; and a validation pipeline ensures the weathered output hasn't corrupted the text or broken ground truth alignment.

The critical addition: weathering must be **spatially coherent across the codex**. Adjacent folios share damage patterns because they are physical neighbors in the same gathering.

---

## Part 1: Physical Model of Damage Propagation

### The gathering structure

MS Erfurt Aug. 12°47 is a single gathering of 17 folios. Each folio is a single sheet with a recto (front) and verso (back). The folios are nested:

```
Folio 1:  [f01r | f01v]
Folio 2:  [f02r | f02v]
...
Folio 17: [f17r | f17v]
```

When the gathering is bound and shelved, the physical adjacency is:

```
f01r is exposed (outermost)
f01v faces f02r (touching)
f02v faces f03r (touching)
...
f16v faces f17r (touching)
f17v is exposed (outermost, against the Lectionary)
```

### Damage propagation rules

**Rule 1: Recto/verso mirror**
Damage on one side of a leaf appears mirrored on the other side. The mirror is horizontal (left-right flip) because you're looking at the same sheet from the other side.

```python
def mirror_damage_map(damage_map, axis='horizontal'):
    """Flip a damage map for the other side of the same leaf."""
    return np.flip(damage_map, axis=1)  # horizontal flip for recto↔verso
```

The severity is similar but not identical — water may penetrate more on the side it contacted first, leaving the reverse side slightly less damaged.

```python
def verso_severity(recto_severity):
    """Damage on verso is slightly less than recto (penetration loss)."""
    return recto_severity * 0.85  # 15% severity reduction through the leaf
```

**Rule 2: Adjacent-leaf penetration**
Damage (especially water) seeps from one leaf to its neighbors. Severity decreases with each leaf of distance:

```python
def propagation_severity(source_severity, leaf_distance):
    """Damage severity decreases exponentially with distance through the gathering."""
    decay_rate = 0.4  # each leaf absorbs ~60% of the remaining damage
    return source_severity * (decay_rate ** leaf_distance)
```

For the water damage on f04r-f05v:
```
f04r: 1.0   (source — direct water contact)
f04v: 0.85  (same leaf, reverse side)
f03v: 0.40  (one leaf away, facing f04r)
f05r: 0.34  (one leaf away, facing f04v)
f03r: 0.16  (two leaves away)
f05v: 0.14  (two leaves away)
f02v: 0.06  (three leaves — barely noticeable)
f06r: 0.05  (three leaves — barely noticeable)
Beyond: negligible
```

**Rule 3: Edge darkening is universal**
Every folio has the same pattern of edge darkening because all edges were exposed to the same environment. The severity varies only by position in the gathering:
- Outermost folios (f01, f17): slightly more darkened (more exposure)
- Inner folios: slightly less
- All folios: gutter side (left on recto, right on verso) has binding shadow

**Rule 4: Foxing is semi-random but spatially clustered**
Foxing (biological spots) tends to appear in clusters that span multiple adjacent leaves. A foxing spot on f06r likely has corresponding spots on f05v and f06v in similar positions, because the mold colony grew through the leaves.

```python
def generate_foxing_clusters(n_clusters=5, gathering_size=17):
    """Generate foxing clusters that span multiple adjacent leaves."""
    clusters = []
    for _ in range(n_clusters):
        # Random position on the page
        cx, cy = random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)
        # Random center folio
        center_folio = random.randint(1, gathering_size)
        # Spread across 2-4 adjacent folios
        spread = random.randint(2, 4)
        # Intensity varies per folio (strongest at center)
        for offset in range(-spread//2, spread//2 + 1):
            folio = center_folio + offset
            if 1 <= folio <= gathering_size:
                intensity = 1.0 - abs(offset) / (spread/2 + 1)
                # Slight position jitter per folio (the spot isn't in exactly the same place)
                jx = cx + random.gauss(0, 0.02)
                jy = cy + random.gauss(0, 0.02)
                clusters.append({
                    'folio': folio,
                    'position': (jx, jy),
                    'intensity': intensity * random.uniform(0.5, 1.0),
                    'radius': random.uniform(0.005, 0.02),  # fraction of page
                })
    return clusters
```

**Rule 5: Missing material is absolute**
The missing corner on f04v means material is gone. This affects:
- f04v: corner missing (primary)
- f04r: same corner missing (same leaf, mirrored position)
- No propagation to other leaves (you can't tear a corner off an adjacent page)

**Rule 6: Overall vellum tone varies by stock**
f01-f13 use standard vellum stock (one base tone). f14-f17 use different stock ("smaller, cut unevenly, as though taken from a sheet intended for something else"). The AI model needs to be told which stock each folio uses, so the base tone is consistent within each group but different between them.

---

## Part 2: Codex Weathering Map

Before any AI model is invoked, we compute a **codex weathering map** — a per-folio specification of exactly what damage appears where, at what severity, derived from the physical propagation rules.

```python
def compute_codex_weathering_map(gathering_size=17, clio7_annotations=None):
    """Compute the complete weathering specification for all folios."""
    
    weathering_map = {}
    
    for folio_num in range(1, gathering_size + 1):
        for side in ['r', 'v']:
            folio_id = f"f{folio_num:02d}{side}"
            
            spec = {
                'folio_id': folio_id,
                'vellum_stock': 'irregular' if folio_num >= 14 else 'standard',
                'edge_darkening': compute_edge_darkening(folio_num, gathering_size),
                'gutter_side': 'left' if side == 'r' else 'right',
                'water_damage': None,
                'missing_corner': None,
                'foxing_spots': [],
                'overall_aging': 'standard',
            }
            
            # Water damage propagation from f04r source
            water_severity = compute_water_propagation(folio_num, side, 
                source_folio=4, source_side='r', source_severity=1.0)
            if water_severity > 0.03:  # threshold for visible damage
                spec['water_damage'] = {
                    'severity': water_severity,
                    'origin': 'top_right',  # water came from above-right per CLIO-7
                    'penetration': min(0.6 * water_severity, 0.6),  # how far down the page
                }
            
            # Missing corner (f04r and f04v only — same leaf)
            if folio_num == 4:
                spec['missing_corner'] = {
                    'corner': 'bottom_right' if side == 'v' else 'bottom_left',  # mirrored
                    'depth_fraction': 0.08,  # ~8% of page height
                    'width_fraction': 0.07,  # ~7% of page width
                }
            
            weathering_map[folio_id] = spec
    
    # Add foxing clusters (consistent across folios)
    foxing = generate_foxing_clusters(n_clusters=5, gathering_size=gathering_size)
    for spot in foxing:
        folio_id = f"f{spot['folio']:02d}r"  # apply to recto
        if folio_id in weathering_map:
            weathering_map[folio_id]['foxing_spots'].append(spot)
        # Mirror to verso
        verso_id = f"f{spot['folio']:02d}v"
        if verso_id in weathering_map:
            mirrored_spot = {**spot, 'position': (1.0 - spot['position'][0], spot['position'][1])}
            weathering_map[verso_id]['foxing_spots'].append(mirrored_spot)
    
    # CLIO-7 per-folio annotations
    if clio7_annotations:
        for folio_id, annotations in clio7_annotations.items():
            if folio_id in weathering_map:
                if 'confidence_zones' in annotations:
                    weathering_map[folio_id]['text_degradation'] = annotations['confidence_zones']
    
    return weathering_map
```

### Weathering map output (per folio)

```json
{
    "f04r": {
        "folio_id": "f04r",
        "vellum_stock": "standard",
        "edge_darkening": 0.7,
        "gutter_side": "left",
        "water_damage": {
            "severity": 1.0,
            "origin": "top_right",
            "penetration": 0.6
        },
        "missing_corner": {
            "corner": "bottom_left",
            "depth_fraction": 0.08,
            "width_fraction": 0.07
        },
        "foxing_spots": [],
        "text_degradation": [
            { "lines": [1, 8], "confidence": 0.7, "description": "water-affected, partially legible" },
            { "lines": [9, 14], "confidence": 0.5, "description": "heavily water-damaged" }
        ]
    },
    "f04v": {
        "folio_id": "f04v",
        "vellum_stock": "standard",
        "edge_darkening": 0.7,
        "gutter_side": "right",
        "water_damage": {
            "severity": 0.85,
            "origin": "top_left",
            "penetration": 0.51
        },
        "missing_corner": {
            "corner": "bottom_right",
            "depth_fraction": 0.08,
            "width_fraction": 0.07
        },
        "text_degradation": [
            { "lines": [1, 6], "confidence": 0.65, "description": "water-affected" },
            { "lines": [7, 12], "confidence": 0.4, "description": "heavily damaged, speculative reconstruction" },
            { "lines": [18, 24], "confidence": 0.0, "description": "missing corner — text completely lost" }
        ]
    },
    "f01r": {
        "folio_id": "f01r",
        "vellum_stock": "standard",
        "edge_darkening": 0.9,
        "gutter_side": "left",
        "water_damage": null,
        "missing_corner": null,
        "foxing_spots": [
            { "position": [0.72, 0.35], "intensity": 0.6, "radius": 0.012 },
            { "position": [0.15, 0.78], "intensity": 0.4, "radius": 0.008 }
        ],
        "text_degradation": null,
        "overall_aging": "standard"
    }
}
```

---

## Part 3: AI Weathering Prompt Generation

The codex weathering map is translated into a structured prompt for the AI image model.

### Prompt template

```python
def generate_weathering_prompt(folio_spec, context):
    """Generate an AI image model prompt from the weathering specification."""
    
    prompt_parts = []
    
    # Base instruction
    prompt_parts.append(
        "Apply realistic aging and weathering to this manuscript page image. "
        "The manuscript is approximately 560 years old (written 1457, discovered 2019), "
        "stored in an Augustinian archive between two other books. "
        "Do NOT alter, move, or regenerate any text or letterforms. "
        "Only modify the surface appearance: vellum color, ink aging, staining, and damage. "
        "Preserve all text exactly as rendered — every letter must remain in its precise position."
    )
    
    # Vellum stock
    if folio_spec['vellum_stock'] == 'standard':
        prompt_parts.append(
            "The vellum is standard calfskin parchment, aged to a warm cream-yellow tone "
            "with slight spatial color variation."
        )
    else:
        prompt_parts.append(
            "The vellum is irregular stock — slightly different tone than standard pages, "
            "cut unevenly, as though taken from a sheet intended for something else. "
            "Slightly more yellow than the standard pages."
        )
    
    # Ink aging
    prompt_parts.append(
        "The ink is iron gall, aged from its original black to a warm dark brown. "
        "The color shift should be uniform across the page — all text the same brown tone."
    )
    
    # Edge darkening
    severity = folio_spec['edge_darkening']
    prompt_parts.append(
        f"Edge darkening at {'strong' if severity > 0.8 else 'moderate' if severity > 0.5 else 'light'} "
        f"intensity on all four edges, darkest at the corners. "
        f"The {'left' if folio_spec['gutter_side'] == 'left' else 'right'} edge has additional "
        f"binding shadow from the book's spine."
    )
    
    # Water damage
    if folio_spec['water_damage']:
        wd = folio_spec['water_damage']
        severity_word = 'severe' if wd['severity'] > 0.7 else 'moderate' if wd['severity'] > 0.3 else 'light'
        prompt_parts.append(
            f"Water damage from above, originating from the {wd['origin']} of the page. "
            f"Severity: {severity_word}. The water stain extends approximately {int(wd['penetration']*100)}% "
            f"down the page from the top edge. Show characteristic tide lines (brown rings at the "
            f"boundary of the wetted area), vellum darkening and wrinkling in the affected zone, "
            f"and partial ink dissolution — text in the water-damaged area should be faded and "
            f"partially illegible but not completely erased."
        )
    
    # Missing corner
    if folio_spec['missing_corner']:
        mc = folio_spec['missing_corner']
        prompt_parts.append(
            f"The {mc['corner']} corner of the page is physically missing — torn away. "
            f"The tear extends approximately {int(mc['depth_fraction']*100)}% of the page height "
            f"and {int(mc['width_fraction']*100)}% of the page width. "
            f"The tear edge should look like torn vellum — irregular, slightly fibrous, not a clean cut. "
            f"Behind the missing corner, show a dark background (the shelf or conservation board)."
        )
    
    # Foxing spots
    if folio_spec['foxing_spots']:
        n = len(folio_spec['foxing_spots'])
        prompt_parts.append(
            f"Add {n} small foxing spots (brown biological staining dots) scattered across the page. "
            f"They should be small (1-3mm), roughly circular, and brown/tan in color. "
            f"Light foxing — this manuscript was stored in a relatively dry archive."
        )
    
    # Text degradation zones
    if folio_spec.get('text_degradation'):
        for zone in folio_spec['text_degradation']:
            if zone['confidence'] == 0:
                prompt_parts.append(
                    f"Lines {zone['lines'][0]}-{zone['lines'][1]}: text completely absent "
                    f"({zone['description']}). No ink visible in this region."
                )
            elif zone['confidence'] < 0.5:
                prompt_parts.append(
                    f"Lines {zone['lines'][0]}-{zone['lines'][1]}: text barely visible — "
                    f"only faint traces of ink remain ({zone['description']}). "
                    f"A reader would struggle to make out more than isolated words."
                )
            elif zone['confidence'] < 0.8:
                prompt_parts.append(
                    f"Lines {zone['lines'][0]}-{zone['lines'][1]}: text partially legible — "
                    f"ink is faded but most words can still be read with difficulty "
                    f"({zone['description']})."
                )
    
    # Coherence reference
    if context.get('adjacent_folios'):
        prompt_parts.append(
            "IMPORTANT — maintain visual coherence with adjacent pages: "
        )
        for adj in context['adjacent_folios']:
            prompt_parts.append(
                f"The {'preceding' if adj['relation'] == 'before' else 'following'} page "
                f"({adj['folio_id']}) has {adj['description']}. "
                f"This page should show {'similar' if adj['severity_here'] > 0.3 else 'diminishing'} "
                f"effects in {'matching' if adj['same_leaf'] else 'corresponding'} positions."
            )
    
    return " ".join(prompt_parts)
```

### Coherence context

When weathering folio N, the prompt includes descriptions of adjacent folios' weathering so the AI model can maintain consistency:

```python
def build_coherence_context(folio_id, weathering_map):
    """Build context about adjacent folios for prompt coherence."""
    folio_num = int(folio_id[1:3])
    side = folio_id[3]
    
    context = {'adjacent_folios': []}
    
    # Same leaf, other side
    other_side = 'v' if side == 'r' else 'r'
    other_id = f"f{folio_num:02d}{other_side}"
    if other_id in weathering_map:
        spec = weathering_map[other_id]
        context['adjacent_folios'].append({
            'folio_id': other_id,
            'relation': 'verso' if side == 'r' else 'recto',
            'same_leaf': True,
            'description': summarize_weathering(spec),
            'severity_here': spec.get('water_damage', {}).get('severity', 0) * 0.85,
        })
    
    # Facing page (the page that touches this one when the book is closed)
    if side == 'r' and folio_num > 1:
        facing_id = f"f{folio_num-1:02d}v"
    elif side == 'v' and folio_num < 17:
        facing_id = f"f{folio_num+1:02d}r"
    else:
        facing_id = None
    
    if facing_id and facing_id in weathering_map:
        spec = weathering_map[facing_id]
        context['adjacent_folios'].append({
            'folio_id': facing_id,
            'relation': 'facing',
            'same_leaf': False,
            'description': summarize_weathering(spec),
            'severity_here': spec.get('water_damage', {}).get('severity', 0) * 0.4,
        })
    
    return context
```

---

## Part 4: Weathering Execution Pipeline

### Sequential processing with reference passing

Folios are weathered in physical order (as they sit in the gathering), with each weathered result available as reference for the next:

```python
def weather_codex(clean_images, weathering_map, model_api):
    """Weather all folios with cross-page coherence."""
    
    weathered = {}
    
    # Process in gathering order
    folio_order = generate_gathering_order(weathering_map)
    
    for folio_id in folio_order:
        spec = weathering_map[folio_id]
        clean_image = clean_images[folio_id]
        
        # Build coherence context (references already-weathered adjacent pages)
        context = build_coherence_context(folio_id, weathering_map)
        
        # Add references to already-weathered adjacent pages
        for adj in context['adjacent_folios']:
            if adj['folio_id'] in weathered:
                adj['reference_image'] = weathered[adj['folio_id']]['image']
        
        # Generate the prompt
        prompt = generate_weathering_prompt(spec, context)
        
        # Call the AI image model
        weathered_image = model_api.apply_weathering(
            image=clean_image,
            prompt=prompt,
            reference_images=[adj.get('reference_image') for adj in context['adjacent_folios'] 
                            if adj.get('reference_image') is not None],
            seed=hash(folio_id) % 2**32,  # deterministic seed per folio
        )
        
        weathered[folio_id] = {
            'image': weathered_image,
            'prompt': prompt,
            'spec': spec,
        }
        
        log(f"Weathered {folio_id}: {summarize_weathering(spec)}")
    
    return weathered
```

### Gathering order

Process folios in an order that maximizes coherence reference availability:

```python
def generate_gathering_order(weathering_map):
    """Order folios so that when we process each one, its neighbors are already done."""
    # Start from the most damaged folio (f04r) and work outward
    # This ensures the damage source is established first, then propagation
    
    # Phase 1: the damage epicenter
    order = ['f04r', 'f04v']  # same leaf, source of water damage
    
    # Phase 2: immediately adjacent leaves
    order += ['f03v', 'f05r']  # facing pages
    order += ['f03r', 'f05v']  # other sides of those leaves
    
    # Phase 3: remaining folios outward from damage
    order += ['f02v', 'f06r', 'f02r', 'f06v']
    order += ['f01v', 'f07r', 'f01r', 'f07v']
    
    # Phase 4: undamaged folios (order matters less)
    remaining = [f"f{n:02d}{s}" for n in range(8, 18) for s in ['r', 'v']]
    order += [f for f in remaining if f in weathering_map]
    
    return order
```

---

## Part 5: Validation Pipeline

After AI weathering, validate that the text hasn't been corrupted:

### V1: Text position integrity

```python
def validate_text_positions(clean_image, weathered_image, page_xml):
    """Verify text hasn't shifted position during weathering."""
    # Extract text regions from both images using the same binarization
    clean_regions = extract_text_regions(clean_image)
    weathered_regions = extract_text_regions(weathered_image)
    
    # Compare centroids of corresponding regions
    max_drift = 0
    for cr, wr in zip(clean_regions, weathered_regions):
        drift = distance(cr.centroid, wr.centroid)
        max_drift = max(max_drift, drift)
    
    return {
        'max_drift_px': max_drift,
        'passed': max_drift < 5,  # allow up to 5px drift
        'note': 'FAIL: text positions shifted' if max_drift >= 5 else 'OK'
    }
```

### V2: Text content integrity

```python
def validate_text_content(clean_image, weathered_image, expected_text):
    """Verify the AI model hasn't added, removed, or altered text."""
    # Run OCR/HTR on both images
    clean_text = ocr(clean_image)
    weathered_text = ocr(weathered_image)
    
    # The weathered text should be a subset of the clean text
    # (some text may be intentionally illegible from damage, but no NEW text should appear)
    clean_chars = set(enumerate(clean_text))
    weathered_chars = set(enumerate(weathered_text))
    
    added = weathered_chars - clean_chars  # characters that appeared from nowhere
    
    return {
        'added_characters': len(added),
        'passed': len(added) == 0,
        'note': f'FAIL: {len(added)} characters added by weathering model' if added else 'OK'
    }
```

### V3: Damage zone consistency

```python
def validate_damage_consistency(weathered_images, weathering_map):
    """Verify that damage is consistent across adjacent folios."""
    issues = []
    
    for folio_id, spec in weathering_map.items():
        if not spec.get('water_damage'):
            continue
        
        folio_num = int(folio_id[1:3])
        side = folio_id[3]
        
        # Check that the other side of the same leaf has matching damage
        other_side = 'v' if side == 'r' else 'r'
        other_id = f"f{folio_num:02d}{other_side}"
        
        if other_id in weathered_images:
            # Compare water stain positions (should be mirrored)
            this_stain = detect_stain_region(weathered_images[folio_id])
            other_stain = detect_stain_region(weathered_images[other_id])
            
            if this_stain is not None and other_stain is not None:
                # Mirror this_stain and compare overlap with other_stain
                mirrored = mirror_horizontal(this_stain)
                overlap = compute_iou(mirrored, other_stain)
                
                if overlap < 0.5:  # less than 50% overlap after mirroring
                    issues.append(f"{folio_id} and {other_id}: water stain positions inconsistent (IoU={overlap:.2f})")
    
    return {
        'issues': issues,
        'passed': len(issues) == 0,
    }
```

---

## Part 6: Provenance

Every weathered folio records:

```json
{
    "folio_id": "f04r",
    "method": "ai_assisted",
    "model": "gpt-image-1",
    "prompt": "Apply realistic aging...",
    "seed": 284719,
    "weathering_spec": { ... },
    "coherence_references": ["f04v", "f03v"],
    "validation": {
        "text_position_integrity": { "max_drift_px": 2.3, "passed": true },
        "text_content_integrity": { "added_characters": 0, "passed": true },
        "damage_consistency": { "issues": [], "passed": true }
    },
    "timestamp": "2026-03-21T16:00:00Z"
}
```

---

## Part 7: API Integration

### Which AI image model?

The model needs to support:
- Image-to-image transformation (input: clean manuscript page, output: weathered version)
- Text prompts guiding the transformation
- Ideally: reference images for coherence
- Ideally: seed parameter for reproducibility

Candidates:
- **GPT-Image (OpenAI)** — image editing with text instructions. You already have an OpenAI API key.
- **Stable Diffusion img2img** — with ControlNet to preserve text layout. More control but more setup.
- **Manual workflow** — use ChatGPT or Midjourney with the generated prompts. Less automated but quick to test.

### CLI commands

```bash
# Compute the codex weathering map
scribesim weather-map \
    --gathering-size 17 \
    --clio7 xl-output/manifest.json \
    --output weather/codex_map.json

# Weather a single folio
scribesim weather-folio f04r \
    --clean scribesim-output/f04r.png \
    --map weather/codex_map.json \
    --model openai \
    --output weather/f04r_weathered.png

# Weather the complete codex in coherence order
scribesim weather-codex \
    --clean-dir scribesim-output/ \
    --map weather/codex_map.json \
    --model openai \
    --output-dir weather/weathered/ \
    --validate

# Validate coherence across the codex
scribesim weather-validate \
    --weathered-dir weather/weathered/ \
    --map weather/codex_map.json \
    --clean-dir scribesim-output/
```

---

## Implementation Priority

1. **Codex weathering map computation** — implement the physical propagation model and generate the per-folio JSON specs. This is pure computation, no AI model needed.

2. **Prompt generation** — translate specs into structured prompts. Test by reading the prompts and verifying they describe the right damage for each folio.

3. **Single-folio AI weathering** — test with one folio (f04r, the most damaged) using the OpenAI API or manual prompt. Verify the result looks right.

4. **Coherence validation** — implement the recto/verso mirror check and adjacent-leaf consistency check.

5. **Sequential codex weathering** — process all 34 pages in gathering order with coherence references.

6. **Text integrity validation** — verify no text was corrupted or shifted.

---

## What This Replaces

TD-011 replaces the procedural Weather system for visual weathering. The procedural code from TD-002/Weather may still be useful for:
- Ground truth coordinate updates (geometric distortions from page curl)
- Generating the damage masks that the AI prompt describes
- Fallback rendering when AI API is unavailable

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-21 | Initial draft — AI-assisted weathering with codex coherence | shawn + claude |
