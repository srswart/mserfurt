# TD-011 Addendum A — Word-Level Text Degradation from CLIO-7 Annotations

## Context
TD-011's text degradation zones operate at the line level ("Lines 7-12: barely visible"). But CLIO-7's apparatus is word-specific — individual words and phrases have different confidence levels on the same line. The weathering prompt needs to be equally specific to produce the right pattern of legibility and illegibility.

## The CLIO-7 damage vocabulary

From the English manuscript, CLIO-7 uses four levels of text damage:

| CLIO-7 markup | Meaning | What the manuscript looks like |
|---|---|---|
| Normal text | ≥80% confidence, clearly legible | Ink fully present, aged to brown but readable |
| *Italics* | 60-80% confidence, reconstructed | Ink faded, partially dissolved by water — readable with effort, some letters ambiguous |
| ***Bold italics*** | <60% confidence, speculative | Ink mostly gone — isolated letter fragments, a scholar's guess at what was there |
| [—] | Lacuna, 4+ words completely lost | No ink at all — bare vellum (or missing material if in the torn corner zone) |
| Specific notes | Per-word ambiguity | "The word 'proud' is partially obscured" — targeted damage to specific characters |

## Mapping CLIO-7 to ScribeSim coordinates

XL's folio JSON already carries per-line annotations with confidence levels. ScribeSim's ground truth PAGE XML records where each word and glyph is positioned on the rendered page. The bridge:

```python
def build_word_damage_map(folio_json, page_xml):
    """Map CLIO-7 confidence annotations to pixel regions on the rendered page."""
    
    word_damage = []
    
    for line in folio_json['lines']:
        for annotation in line.get('annotations', []):
            if annotation['type'] == 'confidence':
                # Find the corresponding word(s) in the PAGE XML
                affected_words = find_words_in_span(
                    page_xml, 
                    line['number'], 
                    annotation['span']['char_start'], 
                    annotation['span']['char_end']
                )
                
                for word in affected_words:
                    word_damage.append({
                        'word_text': word.text,
                        'bbox': word.bounding_box,  # pixel coordinates
                        'center': word.center,
                        'confidence': annotation['detail']['level'],
                        'category': annotation['detail']['category'],
                        'line_number': line['number'],
                    })
            
            elif annotation['type'] == 'lacuna':
                # Complete text loss — mark the region
                affected_region = find_region_for_span(
                    page_xml,
                    line['number'],
                    annotation['span']['char_start'],
                    annotation['span']['char_end']
                )
                
                word_damage.append({
                    'word_text': '[lacuna]',
                    'bbox': affected_region,
                    'center': affected_region.center,
                    'confidence': 0.0,
                    'category': 'lacuna',
                    'line_number': line['number'],
                    'extent_chars': annotation['detail'].get('extent_chars', 20),
                })
    
    return word_damage
```

## Enhanced prompt generation

Instead of line-level damage descriptions, the prompt specifies word-level damage with pixel positions:

```python
def generate_text_degradation_prompt(word_damage_map, page_width, page_height):
    """Generate specific text degradation instructions from word-level damage data."""
    
    if not word_damage_map:
        return ""
    
    parts = []
    parts.append(
        "SPECIFIC TEXT DEGRADATION INSTRUCTIONS — follow these precisely. "
        "Page coordinates are given as percentages from top-left (0%,0%) to bottom-right (100%,100%)."
    )
    
    # Group by confidence category for clarity
    clear_zones = [w for w in word_damage_map if w['confidence'] >= 0.8]
    faded_zones = [w for w in word_damage_map if 0.6 <= w['confidence'] < 0.8]
    trace_zones = [w for w in word_damage_map if 0.0 < w['confidence'] < 0.6]
    lost_zones = [w for w in word_damage_map if w['confidence'] == 0.0]
    
    if clear_zones:
        parts.append(
            f"LEGIBLE TEXT ({len(clear_zones)} regions): The following areas contain text that "
            f"should remain fully legible — ink faded to brown with age but clearly readable. "
            f"Do not degrade these regions beyond normal aging."
        )
    
    if faded_zones:
        parts.append(
            f"PARTIALLY LEGIBLE TEXT ({len(faded_zones)} regions): The following text has been "
            f"damaged by water exposure. The ink is faded and partially dissolved. A careful reader "
            f"can make out most words but some letters are ambiguous."
        )
        for w in faded_zones:
            x_pct = w['center'][0] / page_width * 100
            y_pct = w['center'][1] / page_height * 100
            width_pct = (w['bbox'][2] - w['bbox'][0]) / page_width * 100
            parts.append(
                f"  - At position ({x_pct:.0f}%, {y_pct:.0f}%), width ~{width_pct:.0f}%: "
                f"the word '{w['word_text']}' — fade ink to approximately {int(w['confidence']*100)}% "
                f"of normal darkness. Some letters should be partially dissolved but the overall "
                f"word shape remains recognizable."
            )
    
    if trace_zones:
        parts.append(
            f"BARELY LEGIBLE TEXT ({len(trace_zones)} regions): The following text is heavily "
            f"damaged. Only faint ink traces remain — isolated fragments of letter strokes. "
            f"A scholar might reconstruct some words but most are speculative."
        )
        for w in trace_zones:
            x_pct = w['center'][0] / page_width * 100
            y_pct = w['center'][1] / page_height * 100
            width_pct = (w['bbox'][2] - w['bbox'][0]) / page_width * 100
            parts.append(
                f"  - At position ({x_pct:.0f}%, {y_pct:.0f}%), width ~{width_pct:.0f}%: "
                f"reduce ink to faint traces — {int(w['confidence']*100)}% of normal darkness. "
                f"Only isolated vertical strokes and fragments should be visible. "
                f"The word shape should NOT be clearly recognizable."
            )
    
    if lost_zones:
        parts.append(
            f"COMPLETELY LOST TEXT ({len(lost_zones)} regions): The following areas have no "
            f"surviving ink. The text is entirely gone — these are lacunae where the water "
            f"(or physical damage) has completely removed the writing."
        )
        for w in lost_zones:
            x_pct = w['center'][0] / page_width * 100
            y_pct = w['center'][1] / page_height * 100
            width_pct = (w['bbox'][2] - w['bbox'][0]) / page_width * 100
            parts.append(
                f"  - At position ({x_pct:.0f}%, {y_pct:.0f}%), width ~{width_pct:.0f}%: "
                f"no ink whatsoever. Bare vellum surface (with water staining if in the "
                f"water-damaged zone). This should look like a gap in the text where "
                f"writing once existed but has been completely erased by damage."
            )
    
    # The specific Eckhart crux — the most important single-word damage
    # CLIO-7: "The word rendered 'proud' here is partially obscured"
    specific_notes = [w for w in word_damage_map if w.get('specific_note')]
    for w in specific_notes:
        x_pct = w['center'][0] / page_width * 100
        y_pct = w['center'][1] / page_height * 100
        parts.append(
            f"SPECIFIC DAMAGE NOTE: At position ({x_pct:.0f}%, {y_pct:.0f}%): "
            f"{w['specific_note']} — partially obscure this word so that the first "
            f"and last letters are faintly visible but the middle letters are ambiguous. "
            f"A reader should be able to see that a word exists here but should NOT be "
            f"certain what it says."
        )
    
    return "\n".join(parts)
```

## The specific damaged passages in MS Erfurt Aug. 12°47

From the CLIO-7 apparatus, these are the exact damage points that need word-level treatment:

### Folio 4r-5v: Peter narrative (water damage from above)

```python
peter_narrative_damage = [
    # "Within three weeks I knew that Peter was not going to be [—] the cloth trade"
    {'line': 3, 'text': '[lacuna]', 'confidence': 0.0, 
     'note': '4+ words lost to water damage between "be" and "the cloth trade"'},
    
    # "which I noted in my records and told [—]"
    {'line': 11, 'text': '[lacuna]', 'confidence': 0.0,
     'note': 'words lost after "told"'},
    
    # "I remember [—] the light"
    {'line': 15, 'text': '[lacuna]', 'confidence': 0.0,
     'note': 'words lost between "remember" and "the light"'},
    
    # "There is a particular light in the scriptorium in late [—] that I have always [—]"
    {'line': 16, 'text': '[lacuna]', 'confidence': 0.0,
     'note': 'two separate lacunae in one sentence'},
    
    # "I said [—]." / "He said [—]." / "I said that I was [—] proud [—]."
    {'line': 22, 'text': '[lacuna]', 'confidence': 0.0,
     'note': 'dialogue almost entirely lost'},
    {'line': 23, 'text': '[lacuna]', 'confidence': 0.0},
    {'line': 24, 'text': 'stolz', 'confidence': 0.55,
     'note': '"proud" partially obscured — alternative reading "verloren" (lost) cannot be ruled out'},
    
    # "and I am [—] years older"
    {'line': 35, 'text': '[lacuna]', 'confidence': 0.0,
     'note': 'number of years lost'},
    
    # "my eyes, in the morning light, are [—]"
    {'line': 36, 'text': '[lacuna]', 'confidence': 0.0,
     'note': 'description of eye condition lost — sentence trails off into damage'},
]
```

### Folio 4v: Missing corner

```python
missing_corner_damage = {
    'corner': 'bottom_right',
    'affected_lines': [20, 24],  # last 4-5 lines on the page
    'confidence': 0.0,
    'note': 'CLIO-7 has not attempted to reconstruct the missing corner, '
            'as there is insufficient adjacent text to establish a basis for inference. '
            'The absence is noted.'
}
```

## Integration with TD-011 prompt pipeline

The word-level damage map is generated once (when ScribeSim produces its output and XL's annotations are mapped to pixel positions) and stored alongside the codex weathering map:

```
weather/
├── codex_map.json              — physical damage propagation (TD-011)
├── text_damage/
│   ├── f04r_word_damage.json   — word-level damage map for f04r
│   ├── f04v_word_damage.json   — word-level damage map for f04v
│   ├── f05r_word_damage.json   — diminishing damage
│   └── f05v_word_damage.json
└── prompts/
    ├── f04r_prompt.txt         — complete prompt including word-level degradation
    └── ...
```

The prompt generator (TD-011 Part 3) calls `generate_text_degradation_prompt()` and appends the word-level instructions to the physical weathering prompt. The AI model receives both: "the upper right has water staining with tide lines" (physical) AND "the word 'stolz' at position (65%, 72%) should be partially obscured with ambiguous middle letters" (text-specific).

## Pre-weathering text degradation (alternative approach)

Instead of relying on the AI model to selectively degrade text at specific positions, we could apply text degradation BEFORE the AI weathering pass:

```python
def pre_degrade_text(clean_image, word_damage_map):
    """Apply text degradation to the clean image before AI weathering."""
    degraded = clean_image.copy()
    
    for word in word_damage_map:
        bbox = word['bbox']
        region = degraded[bbox.top:bbox.bottom, bbox.left:bbox.right]
        
        if word['confidence'] == 0.0:
            # Lacuna: erase text completely (replace with background)
            background = estimate_local_background(degraded, bbox)
            degraded[bbox.top:bbox.bottom, bbox.left:bbox.right] = background
        
        elif word['confidence'] < 0.6:
            # Barely legible: fade to 20-30% opacity
            alpha = word['confidence'] * 0.5  # 0.0-0.3
            background = estimate_local_background(degraded, bbox)
            blended = (region * alpha + background * (1 - alpha)).astype(np.uint8)
            # Add noise to simulate partial ink dissolution
            noise = np.random.normal(0, 15, blended.shape).astype(np.int16)
            blended = np.clip(blended.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            degraded[bbox.top:bbox.bottom, bbox.left:bbox.right] = blended
        
        elif word['confidence'] < 0.8:
            # Partially legible: fade to 50-70% opacity
            alpha = 0.5 + word['confidence'] * 0.25  # 0.5-0.7
            background = estimate_local_background(degraded, bbox)
            blended = (region * alpha + background * (1 - alpha)).astype(np.uint8)
            degraded[bbox.top:bbox.bottom, bbox.left:bbox.right] = blended
    
    return degraded
```

This approach is more controllable: we know exactly which pixels were degraded and by how much. The AI model then applies surface weathering (staining, vellum aging) on top of the pre-degraded text. The text degradation is precise; the surface weathering is holistic. Best of both worlds.

## Recommended approach

Use BOTH:
1. **Pre-degrade** text at specific word positions using the damage map (precise, controllable)
2. **AI weathering** applies surface effects on top (holistic, convincing)
3. **Validate** that pre-degraded regions weren't restored by the AI model (the model might try to "fix" faded text)

This ensures the CLIO-7 damage specification is honored exactly — the AI model can't accidentally make a lacuna legible or a speculative passage too clear.
