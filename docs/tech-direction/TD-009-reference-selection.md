# Tech Direction: TD-009 — Reference Manuscript Selection and Provenance

## Status
**Active** — prerequisite for TD-008 (letterform extraction).

## Context
TD-008 requires high-quality manuscript folio images as input for evolutionary letterform extraction. Currently, selecting these images is manual — browsing folios, visually judging quality, hoping the choice is good. TD-009 automates this: download candidate folios from a digitized manuscript via IIIF, analyze each for extraction suitability, rank them, and present the top candidates for human approval. All decisions — which folios were considered, which were selected, which were rejected and why — are recorded for provenance.

## Why provenance matters

This project produces a simulated manuscript that claims to look like a 15th-century artifact. If anyone asks "where did the letterforms come from?", we need a clear, auditable answer: "extracted from BSB Cgm 100, folios 5r, 8v, and 12r, selected from a pool of 15 candidates analyzed on 2026-03-21, with selection criteria and scores documented." The provenance record is also essential for:
- Reproducibility: someone else can re-run the extraction from the same sources
- Attribution: respecting the originating institution's licensing and citation requirements
- Quality assurance: if the output looks wrong, the provenance record helps diagnose whether the reference material was the issue

---

## Part 1: IIIF Folio Download

### Fetching the manifest

Every IIIF-compliant manuscript has a manifest JSON that lists all available pages with their image URLs:

```python
def fetch_manifest(manifest_url):
    """Download and parse a IIIF manifest."""
    response = requests.get(manifest_url)
    manifest = response.json()
    
    canvases = []
    for canvas in manifest['sequences'][0]['canvases']:
        image_url = canvas['images'][0]['resource']['@id']
        label = canvas.get('label', '')
        canvas_id = canvas['@id']
        
        # Extract the IIIF image service URL for flexible resolution requests
        service = canvas['images'][0]['resource'].get('service', {})
        service_url = service.get('@id', '')
        
        canvases.append({
            'id': canvas_id,
            'label': label,
            'image_url': image_url,
            'service_url': service_url,
        })
    
    return {
        'manifest_url': manifest_url,
        'title': manifest.get('label', 'Unknown'),
        'attribution': manifest.get('attribution', ''),
        'license': manifest.get('license', ''),
        'canvases': canvases,
    }
```

### Downloading at appropriate resolution

For analysis: medium resolution is sufficient (1500px on the long side).
For extraction: full resolution (max available, typically 3000-6000px).

```python
def download_folio(canvas, output_dir, resolution="analysis"):
    """Download a single folio image via IIIF Image API."""
    if resolution == "analysis":
        # Medium res for quick analysis
        size = "1500,"  # 1500px wide, height proportional
    elif resolution == "extraction":
        # Full res for letterform extraction
        size = "max"
    
    if canvas['service_url']:
        # Use IIIF Image API for flexible resolution
        url = f"{canvas['service_url']}/full/{size}/0/default.jpg"
    else:
        url = canvas['image_url']
    
    response = requests.get(url)
    
    filename = sanitize_filename(canvas['label']) + '.jpg'
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(response.content)
    
    return filepath
```

### Sampling strategy

For a manuscript like Cgm 100 (387 pages), downloading all pages is wasteful. Sampling strategies:

```python
def select_candidate_pages(manifest, n_candidates=15, strategy="stratified"):
    """Select candidate pages for analysis."""
    canvases = manifest['canvases']
    total = len(canvases)
    
    if strategy == "random":
        # Pure random sampling
        indices = sorted(random.sample(range(total), min(n_candidates, total)))
    
    elif strategy == "stratified":
        # Sample evenly across the manuscript
        # This catches different hands/sections if the manuscript is composite
        stride = total // n_candidates
        base_indices = [i * stride for i in range(n_candidates)]
        # Add small random jitter to avoid always hitting the same relative position
        indices = [min(i + random.randint(0, stride//3), total-1) for i in base_indices]
    
    elif strategy == "text_pages_only":
        # Skip likely non-text pages (front/back matter, blank pages)
        # Heuristic: skip first 3 and last 3 pages (covers, flyleaves)
        text_range = canvases[3:-3]
        indices = sorted(random.sample(range(3, total-3), min(n_candidates, len(text_range))))
    
    elif strategy == "focused":
        # Focus on a specific page range (e.g., if you know which section has the right hand)
        # This is set by the user
        pass
    
    return [canvases[i] for i in indices]
```

**Recommended: 15 candidates with stratified sampling.** This covers the manuscript evenly, catches any variation in hands or quality across the codex, and gives enough candidates for reliable ranking. 15 is cheap to analyze (a few minutes) and gives a much better selection than 5.

---

## Part 2: Folio Analysis

Each candidate folio is analyzed across seven criteria. All scores are normalized to 0.0–1.0 where higher is better.

### A1: Ink contrast

How well-separated are ink pixels from the background? Higher contrast = cleaner extraction.

```python
def analyze_ink_contrast(image):
    """Score 0-1 based on histogram separation between ink and background."""
    gray = to_grayscale(image)
    
    # Otsu's method finds the optimal threshold separating two distributions
    threshold, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)
    
    # Measure the valley depth at the threshold
    hist = np.histogram(gray, bins=256)[0]
    ink_peak = np.argmax(hist[:threshold])
    bg_peak = threshold + np.argmax(hist[threshold:])
    valley = hist[threshold]
    peak_mean = (hist[ink_peak] + hist[bg_peak]) / 2
    
    # Deeper valley = better separation
    separation = 1.0 - (valley / max(peak_mean, 1))
    
    # Also measure the distance between peaks (wider = more contrast)
    peak_distance = (bg_peak - ink_peak) / 255.0
    
    return 0.5 * separation + 0.5 * peak_distance
```

### A2: Line regularity

Are the text lines evenly spaced and approximately horizontal?

```python
def analyze_line_regularity(image):
    """Score 0-1 based on consistency of line spacing and alignment."""
    gray = to_grayscale(image)
    binary = binarize(gray)
    
    # Horizontal projection profile
    h_proj = binary.sum(axis=1)
    
    # Find text lines as peaks in the projection
    peaks = find_peaks(h_proj, distance=20, height=h_proj.max() * 0.1)
    
    if len(peaks) < 5:
        return 0.0  # not enough lines detected
    
    # Measure inter-line spacing
    spacings = np.diff(peaks)
    spacing_cv = np.std(spacings) / max(np.mean(spacings), 1)  # coefficient of variation
    
    # Lower CV = more regular spacing
    regularity_score = max(0, 1.0 - spacing_cv * 3)  # CV of 0.33 = score 0
    
    # Count detected lines (more = better, up to a point)
    line_count_score = min(len(peaks) / 25, 1.0)  # 25+ lines = full score
    
    return 0.6 * regularity_score + 0.4 * line_count_score
```

### A3: Script consistency

Is the writing consistent across the page (single hand, steady quality)?

```python
def analyze_script_consistency(image):
    """Score 0-1 based on consistency of stroke characteristics across the page."""
    gray = to_grayscale(image)
    binary = binarize(gray)
    
    # Divide the text block into horizontal strips (roughly per-line)
    strips = divide_into_strips(binary, n_strips=8)
    
    # For each strip, measure:
    # - average stroke width (via distance transform)
    # - stroke angle distribution (via Hough transform or gradient analysis)
    # - ink density (fraction of dark pixels)
    measurements = []
    for strip in strips:
        dt = cv2.distanceTransform(strip, cv2.DIST_L2, 5)
        avg_width = dt[strip > 0].mean() if (strip > 0).any() else 0
        ink_density = strip.sum() / max(strip.size, 1)
        measurements.append({'width': avg_width, 'density': ink_density})
    
    # Consistency = low variance across strips
    width_cv = np.std([m['width'] for m in measurements]) / max(np.mean([m['width'] for m in measurements]), 0.1)
    density_cv = np.std([m['density'] for m in measurements]) / max(np.mean([m['density'] for m in measurements]), 0.1)
    
    width_score = max(0, 1.0 - width_cv * 5)
    density_score = max(0, 1.0 - density_cv * 5)
    
    return 0.5 * width_score + 0.5 * density_score
```

### A4: Text density

Enough text for extraction, but not crammed or sparse?

```python
def analyze_text_density(image):
    """Score 0-1 based on text filling an appropriate fraction of the page."""
    gray = to_grayscale(image)
    binary = binarize(gray)
    
    # Find the text block (largest rectangular region with significant ink)
    text_block = find_text_block(binary)
    
    if text_block is None:
        return 0.0
    
    # Ink ratio within the text block
    block_region = binary[text_block.y:text_block.y+text_block.h, 
                          text_block.x:text_block.x+text_block.w]
    ink_ratio = block_region.sum() / max(block_region.size, 1)
    
    # Ideal range: 15-35% ink coverage in text block
    # Too low = sparse text or faded ink
    # Too high = crammed or heavily damaged
    if 0.15 <= ink_ratio <= 0.35:
        density_score = 1.0
    elif ink_ratio < 0.15:
        density_score = ink_ratio / 0.15
    else:
        density_score = max(0, 1.0 - (ink_ratio - 0.35) / 0.15)
    
    # Text block should fill a reasonable fraction of the page
    page_coverage = (text_block.w * text_block.h) / max(binary.size, 1)
    coverage_score = min(page_coverage / 0.4, 1.0)  # 40%+ of page = full score
    
    return 0.6 * density_score + 0.4 * coverage_score
```

### A5: Damage level

Minimal damage in the text area?

```python
def analyze_damage(image):
    """Score 0-1 where 1.0 = no damage, 0.0 = heavily damaged."""
    gray = to_grayscale(image)
    
    # Detect staining: large low-frequency color variation in the text block
    text_block = find_text_block(binarize(gray))
    if text_block is None:
        return 0.0
    
    block = gray[text_block.y:text_block.y+text_block.h, 
                 text_block.x:text_block.x+text_block.w]
    
    # Low-frequency background variation (staining indicator)
    blurred = cv2.GaussianBlur(block, (51, 51), 0)
    background_variation = np.std(blurred) / 255.0
    stain_score = max(0, 1.0 - background_variation * 8)
    
    # High-frequency noise in non-ink areas (foxing, mold indicator)
    # Mask out ink pixels
    non_ink = block[block > 128]  # approximate background pixels
    noise_level = np.std(non_ink) / 255.0 if len(non_ink) > 0 else 0
    noise_score = max(0, 1.0 - noise_level * 10)
    
    return 0.5 * stain_score + 0.5 * noise_score
```

### A6: Thick/thin contrast

Does the script show clear nib-angle-dependent width variation?

```python
def analyze_thick_thin(image):
    """Score 0-1 based on presence of thick/thin stroke contrast."""
    gray = to_grayscale(image)
    binary = binarize(gray)
    
    # Distance transform gives approximate stroke width at each ink pixel
    dt = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    ink_widths = dt[binary > 0]
    
    if len(ink_widths) < 100:
        return 0.0
    
    # Measure the ratio between thick and thin strokes
    thick = np.percentile(ink_widths, 90)
    thin = np.percentile(ink_widths, 10)
    
    if thin < 0.5:
        thin = 0.5  # avoid division by near-zero
    
    ratio = thick / thin
    
    # Ideal ratio for Bastarda: 3:1 to 5:1
    if 3.0 <= ratio <= 5.0:
        return 1.0
    elif 2.0 <= ratio < 3.0:
        return 0.5 + 0.5 * (ratio - 2.0)
    elif 5.0 < ratio <= 7.0:
        return 0.5 + 0.5 * (7.0 - ratio) / 2.0
    elif ratio < 2.0:
        return ratio / 4.0  # very low contrast
    else:
        return 0.3  # extremely high contrast (unusual)
```

### A7: Letter variety

Does the page contain a good spread of different letter shapes?

```python
def analyze_letter_variety(image):
    """Score 0-1 based on diversity of connected component shapes."""
    gray = to_grayscale(image)
    binary = binarize(gray)
    
    # Find connected components
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
    
    # Filter to reasonable letter-sized components
    heights = stats[1:, cv2.CC_STAT_HEIGHT]  # skip background
    widths = stats[1:, cv2.CC_STAT_WIDTH]
    areas = stats[1:, cv2.CC_STAT_AREA]
    
    # Typical letter height range (in pixels, depends on resolution)
    median_h = np.median(heights)
    letter_mask = (heights > median_h * 0.3) & (heights < median_h * 3.0) & (areas > 20)
    
    n_components = letter_mask.sum()
    
    # Enough components for extraction (want 200+ for good letter coverage)
    count_score = min(n_components / 200, 1.0)
    
    # Shape variety: measure the distribution of aspect ratios
    # More variety = more different letter shapes present
    aspect_ratios = widths[letter_mask] / np.maximum(heights[letter_mask], 1)
    if len(aspect_ratios) > 10:
        variety = np.std(aspect_ratios) / max(np.mean(aspect_ratios), 0.1)
        variety_score = min(variety * 2, 1.0)  # higher std = more variety
    else:
        variety_score = 0.0
    
    return 0.5 * count_score + 0.5 * variety_score
```

### Composite suitability score

```python
def composite_suitability(scores):
    """Weighted composite of all analysis criteria."""
    weights = {
        'ink_contrast':       0.20,  # most important — can't extract from faded text
        'line_regularity':    0.15,
        'script_consistency': 0.15,
        'text_density':       0.10,
        'damage':             0.15,
        'thick_thin':         0.15,  # important — this is what makes Bastarda look right
        'letter_variety':     0.10,
    }
    
    total = sum(weights[k] * scores[k] for k in weights)
    return total
```

---

## Part 3: Provenance Record

Every selection run produces a provenance record that documents the complete decision chain:

```json
{
    "provenance": {
        "run_id": "ref-select-20260321-143000",
        "timestamp": "2026-03-21T14:30:00Z",
        "operator": "shawn",
        "tool_version": "scribesim 0.3.0",
        
        "source_manuscript": {
            "institution": "Bayerische Staatsbibliothek",
            "shelfmark": "Cgm 100",
            "title": "Mystikertexte",
            "manifest_url": "https://api.digitale-sammlungen.de/iiif/presentation/v2/bsb00096343/manifest",
            "date_attributed": "14. Jh.",
            "license": "Public Domain",
            "total_pages": 387
        },
        
        "sampling": {
            "strategy": "stratified",
            "n_candidates": 15,
            "page_range": "all",
            "random_seed": 42
        },
        
        "candidates": [
            {
                "canvas_label": "5r",
                "canvas_id": "...",
                "image_url": "...",
                "download_resolution": "1500px",
                "scores": {
                    "ink_contrast": 0.82,
                    "line_regularity": 0.91,
                    "script_consistency": 0.88,
                    "text_density": 0.75,
                    "damage": 0.93,
                    "thick_thin": 0.79,
                    "letter_variety": 0.85,
                    "composite": 0.849
                },
                "rank": 1,
                "selected": true,
                "selection_reason": "highest composite score; clean text, strong thick/thin, minimal damage"
            },
            {
                "canvas_label": "23v",
                "canvas_id": "...",
                "image_url": "...",
                "download_resolution": "1500px",
                "scores": {
                    "ink_contrast": 0.78,
                    "line_regularity": 0.85,
                    "script_consistency": 0.90,
                    "text_density": 0.80,
                    "damage": 0.88,
                    "thick_thin": 0.72,
                    "letter_variety": 0.82,
                    "composite": 0.821
                },
                "rank": 2,
                "selected": true,
                "selection_reason": "second reference for cross-validation; different section of manuscript"
            },
            {
                "canvas_label": "180r",
                "canvas_id": "...",
                "scores": {
                    "ink_contrast": 0.45,
                    "line_regularity": 0.60,
                    "script_consistency": 0.55,
                    "text_density": 0.70,
                    "damage": 0.40,
                    "thick_thin": 0.50,
                    "letter_variety": 0.65,
                    "composite": 0.538
                },
                "rank": 12,
                "selected": false,
                "rejection_reason": "low ink contrast (faded); significant damage; possible different hand"
            }
            // ... all 15 candidates
        ],
        
        "selection_summary": {
            "n_selected": 3,
            "n_rejected": 12,
            "selected_folios": ["5r", "23v", "8v"],
            "composite_score_range": "0.538 - 0.849",
            "selection_threshold": 0.75,
            "human_approved": true,
            "human_notes": "Selected top 3 by composite score. All from same hand. Folio 5r has the clearest thick/thin."
        }
    }
}
```

### Provenance storage

```
reference/
├── provenance/
│   ├── ref-select-20260321-143000.json    — full provenance record
│   └── ref-select-20260321-143000/
│       ├── candidate_005r.jpg              — downloaded candidate images
│       ├── candidate_023v.jpg
│       ├── candidate_180r.jpg
│       └── ...                             — all candidates preserved
├── selected/
│   ├── cgm100_005r.jpg                    — selected folios at full resolution
│   ├── cgm100_023v.jpg
│   └── cgm100_008v.jpg
└── analysis/
    ├── report.html                         — visual report for human review
    └── scores.csv                          — all scores in tabular form
```

**All candidates are preserved**, not just the selected ones. Rejected candidates may become useful later (different hand for variation, damaged pages for Weather reference, etc.). Storage is cheap; provenance is priceless.

---

## Part 4: Visual Report for Human Review

The analysis produces an HTML report that shows:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Reference Selection Report — BSB Cgm 100                          │
│  Date: 2026-03-21 | Candidates: 15 | Selected: 3                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  RANK 1: Folio 5r — Composite: 0.849                               │
│  ┌──────────────┐  Ink contrast:       ████████░░  0.82            │
│  │              │  Line regularity:    █████████░  0.91            │
│  │  [thumbnail] │  Script consistency: ████████░░  0.88            │
│  │              │  Text density:       ███████░░░  0.75            │
│  │              │  Damage:             █████████░  0.93            │
│  └──────────────┘  Thick/thin:         ███████░░░  0.79            │
│  ✓ SELECTED        Letter variety:     ████████░░  0.85            │
│                                                                     │
│  RANK 2: Folio 23v — Composite: 0.821                              │
│  ┌──────────────┐  ...                                              │
│  │  [thumbnail] │                                                   │
│  └──────────────┘                                                   │
│  ✓ SELECTED                                                         │
│                                                                     │
│  ...                                                                │
│                                                                     │
│  RANK 12: Folio 180r — Composite: 0.538                            │
│  ┌──────────────┐  Ink contrast:       ████░░░░░░  0.45  ⚠        │
│  │  [thumbnail] │  Damage:             ████░░░░░░  0.40  ⚠        │
│  └──────────────┘                                                   │
│  ✗ REJECTED: low contrast, significant damage                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

The human reviews the report, confirms or overrides the automatic selection, and adds notes. The provenance record is updated with the human's decision.

---

## Part 5: Multi-Manuscript Support

The same pipeline works across multiple manuscripts. For cross-validation or to build a broader style reference:

```bash
# Analyze candidates from multiple manuscripts
scribesim select-reference \
    --manifest "https://api.digitale-sammlungen.de/iiif/presentation/v2/bsb00096343/manifest" \
    --manifest-label "Cgm 100 — Mystikertexte" \
    --manifest "https://api.digitale-sammlungen.de/iiif/presentation/v2/bsb00XXXXX/manifest" \
    --manifest-label "Cgm 452 — Predigten" \
    --sample 10 \
    --output reference/ \
    --analyze
```

The provenance record tracks which manuscript each candidate came from. Selected folios from different manuscripts can be used together — the letterform extraction averages across instances, and cross-manuscript exemplars help the evolutionary algorithm generalize to "Bastarda" rather than overfitting to one scribe.

---

## Part 6: What Changes in TD-008

TD-008 (evolutionary letterform extraction) currently assumes the reference images are already available. With TD-009, the input pipeline becomes:

```
TD-009: select-reference → analyze → rank → human approval → download full-res
    ↓
TD-008: extract-letters → evolve letterforms → build library
    ↓
TD-007: evolve words → render folios
```

TD-008's `extract-letters` command gains a `--provenance` flag that links the extraction to the specific selection run:

```bash
scribesim extract-letters \
    --reference reference/selected/ \
    --provenance reference/provenance/ref-select-20260321-143000.json \
    --output reference/extracted/
```

The extraction output includes the provenance chain: which manuscript → which folio → which letter crop → which evolved genome. Complete traceability from source to output.

---

## CLI Commands

```bash
# Full selection pipeline
scribesim select-reference \
    --manifest <IIIF_MANIFEST_URL> \
    --manifest-label "BSB Cgm 100" \
    --sample 15 \
    --strategy stratified \
    --output reference/ \
    --analyze \
    --report reference/analysis/report.html

# Download only (skip analysis — useful if you know which pages you want)
scribesim download-folios \
    --manifest <IIIF_MANIFEST_URL> \
    --pages 5,8,12,23,45 \
    --resolution max \
    --output reference/selected/

# Re-analyze previously downloaded candidates
scribesim analyze-reference \
    --input reference/candidates/ \
    --output reference/analysis/ \
    --report reference/analysis/report.html

# View provenance for a selection run
scribesim provenance show reference/provenance/ref-select-20260321-143000.json

# Export provenance as citation
scribesim provenance cite reference/provenance/ref-select-20260321-143000.json --format bibtex
```

---

## Implementation Priority

1. **IIIF manifest download + page sampling** — fetch manifest, select candidate pages, download at analysis resolution. Straightforward HTTP + JSON parsing.

2. **Analysis criteria A1 (ink contrast) and A2 (line regularity)** — the two most important criteria. Implement these first and rank on them alone.

3. **Provenance record** — create the JSON structure and write it alongside every download/analysis operation. Do this early, not as an afterthought.

4. **Remaining analysis criteria (A3-A7)** — add the remaining criteria and the composite score.

5. **Visual report** — HTML report for human review. Can be a simple template.

6. **Full-resolution download of selected folios** — after human approval, re-download at maximum resolution.

7. **Multi-manuscript support** — extend to handle multiple manifests in one run.

---

## Dependency chain update

```
TD-009: Reference selection + provenance  ← NEW, implement first
   ↓
TD-008: Evolutionary letterform extraction (uses selected folios)
   ↓
TD-007: Word-level evolution (uses extracted letterforms)
   ↓
TD-004: Nib physics (used in rendering throughout)
```

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-21 | Initial draft — IIIF selection, analysis, provenance | shawn + claude |
