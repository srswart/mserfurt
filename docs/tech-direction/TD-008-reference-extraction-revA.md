# Tech Direction: TD-008 — Reference Extraction from Real Manuscripts

## Status
**Active** — immediate priority. The letterform guides need to come from real manuscripts, not from algorithmic guesses.

## Context
The current letterform guides were defined by guessing keypoint positions based on textual descriptions of Bastarda. The result: letters are recognizable but lack the proportions, stroke weight, structural details, and calligraphic authority of real scribal handwriting. Comparing our best output against the Werbeschreiben target, every letter is visibly inferior — too thin, too hesitant, wrong proportions, missing the characteristic Bastarda features (dramatic thick/thin, confident descenders, looped ascenders, flowing arches).

This TD defines a pipeline for extracting letterform data from the target manuscript image and converting it into improved letterform guides and exemplar sets for the evolutionary fitness function.

## What we extract

From a single high-quality manuscript image, we extract three things:

### 1. Letter exemplar images (for fitness function F1)
Cropped images of individual letter instances, used as the template matching targets in the evolutionary fitness function. More exemplars = sharper fitness signal = better evolved letters.

**Target: 10-15 instances of each letter from the manuscript.**

### 2. Letter centerlines (for improved letterform guides)
The medial axis / skeleton of each letter instance, fitted with Bézier curves. These become the base trajectories in the letterform guides — the paths the evolutionary algorithm seeds from.

**Target: 3-5 high-quality centerline traces per letter, averaged into a canonical guide.**

### 3. Stroke width profiles (for nib parameter calibration)
The width of each stroke along its centerline, which encodes the nib-angle-dependent thick/thin pattern. This calibrates the nib angle, width, and pressure parameters to match the real manuscript.

**Target: stroke width measurements across 50+ strokes to fit the nib model.**

---

## Pipeline Step 1: Line Segmentation

Use Kraken (already in the eScriptorium ecosystem) to segment the manuscript image into lines:

```bash
# Segment the target manuscript image
kraken -i werbeschreiben.jpg lines.json segment

# Or use the Python API
from kraken import blla
segmentation = blla.segment(image)
lines = segmentation['lines']  # list of baseline polygons
```

Output: baseline coordinates and bounding polygons for each text line.

If Kraken isn't available or doesn't segment well on this image, a simpler approach:
- Horizontal projection profile (sum pixel intensities per row)
- Find valleys in the projection = inter-line gaps
- Extract horizontal strips between valleys as line images

## Pipeline Step 2: Word Segmentation

Within each line, segment into words using whitespace detection:

```python
def segment_words(line_image, threshold=0.85):
    """Find word boundaries by detecting vertical white gaps."""
    # Binarize
    binary = (line_image < threshold * 255).astype(np.uint8)
    
    # Vertical projection: sum ink pixels per column
    projection = binary.sum(axis=0)
    
    # Find gaps (columns with very little ink)
    gap_threshold = projection.max() * 0.05
    is_gap = projection < gap_threshold
    
    # Find gap regions
    gaps = find_contiguous_regions(is_gap, min_width=5)
    
    # Split at gap centers
    word_bounds = split_at_gaps(gaps, line_image.shape[1])
    
    return [line_image[:, left:right] for left, right in word_bounds]
```

## Pipeline Step 3: Letter Segmentation

This is the hardest step. Within a word, letters in Bastarda are often connected, making clean segmentation difficult. Three approaches, used together:

### Approach A: Connected component analysis (for well-separated letters)

```python
def segment_letters_cc(word_image):
    """Segment using connected components — works for separated letters."""
    binary = binarize(word_image)
    labels = connected_components(binary)
    
    components = []
    for label_id in unique(labels):
        if label_id == 0: continue  # background
        mask = (labels == label_id)
        bbox = bounding_box(mask)
        components.append((bbox, mask))
    
    # Sort left to right
    components.sort(key=lambda c: c[0].left)
    return components
```

### Approach B: Vertical stroke detection (for connected letters)

In Bastarda, downstrokes are the thickest part of each letter. Detect them and use as letter anchors:

```python
def detect_vertical_strokes(word_image):
    """Find thick vertical strokes — these anchor letter positions."""
    binary = binarize(word_image)
    
    # Morphological operation: erode horizontally to isolate verticals
    kernel = np.ones((1, 3))  # horizontal kernel
    eroded = cv2.erode(binary, kernel, iterations=2)
    
    # Find vertical stroke centers
    projection = eroded.sum(axis=0)
    peaks = find_peaks(projection, min_distance=5, min_height=projection.max() * 0.3)
    
    return peaks  # x-positions of vertical strokes
```

Between vertical strokes, the thin connecting material belongs to connections or letter features (arches, bowls). The segmentation boundary falls at the thinnest point between two vertical strokes.

### Approach C: HTR-guided segmentation

If we have a transcription of the word (which we do — we can read the Werbeschreiben), we know how many letters there are and what they are. Use CTC alignment or forced alignment to map each letter to a horizontal span:

```python
def htr_guided_segment(word_image, word_text, htr_model):
    """Use HTR model to align letters to image positions."""
    # Run HTR with CTC output
    ctc_output = htr_model.predict_ctc(word_image)
    
    # Force-align against known text
    alignment = ctc_force_align(ctc_output, word_text)
    
    # Each letter maps to a column range
    letter_spans = []
    for char, start_col, end_col in alignment:
        letter_image = word_image[:, start_col:end_col]
        letter_spans.append((char, letter_image))
    
    return letter_spans
```

### Combined approach

Use connected components first. Where components correspond to single letters (verified by width heuristics), accept them. Where components span multiple letters (too wide), apply vertical stroke detection to subdivide. Use HTR-guided alignment as a verification/correction pass.

## Pipeline Step 4: Exemplar Extraction

For each segmented letter, extract a clean exemplar image:

```python
def extract_exemplar(letter_image, target_size=(64, 64)):
    """Clean and normalize a letter image for use as fitness exemplar."""
    # Tight crop to ink bounding box
    cropped = tight_crop(letter_image, padding=2)
    
    # Normalize size (preserve aspect ratio, pad to square)
    normalized = resize_and_pad(cropped, target_size)
    
    # Normalize intensity (consistent background/foreground levels)
    normalized = normalize_intensity(normalized, bg=255, fg=0)
    
    return normalized
```

Store exemplars organized by letter:

```
reference/exemplars/
├── a/
│   ├── werbeschreiben_001.png
│   ├── werbeschreiben_002.png
│   └── ... (10-15 instances)
├── b/
│   └── ...
├── d/
│   └── ...
└── z/
    └── ...
```

## Pipeline Step 5: Centerline Tracing

For each exemplar, extract the medial axis and fit Bézier curves:

```python
def trace_centerline(letter_image):
    """Extract the writing path as a sequence of Bézier curves."""
    binary = binarize(letter_image)
    
    # Skeletonize to get 1-pixel-wide centerline
    skeleton = skeletonize(binary)  # Zhang-Suen or Lee algorithm
    
    # Order the skeleton pixels into a writing path
    # (left to right, with detected branch points for multi-stroke letters)
    path_points = order_skeleton_pixels(skeleton)
    
    # Fit cubic Bézier curves to the path
    segments = fit_bezier_to_path(path_points, max_error=0.5)  # pixels
    
    # Detect lift points (where the skeleton has gaps = pen lifted)
    lifts = detect_gaps(skeleton)
    
    # Mark each segment as contact or lift
    for seg in segments:
        seg.contact = not any(lift_overlaps(seg, lift) for lift in lifts)
    
    return segments

def fit_bezier_to_path(points, max_error):
    """Fit a sequence of cubic Bézier curves to a point sequence."""
    # Philip Schneider's algorithm (from Graphics Gems I)
    # Iteratively fits Bézier curves, splitting where error exceeds threshold
    segments = []
    
    remaining = points
    while len(remaining) > 1:
        # Try fitting a single Bézier to the remaining points
        bezier = fit_single_bezier(remaining)
        error = max_distance(bezier, remaining)
        
        if error < max_error:
            segments.append(bezier)
            break
        else:
            # Split at the point of maximum error and recurse
            split_idx = argmax_distance(bezier, remaining)
            left_bezier = fit_single_bezier(remaining[:split_idx+1])
            segments.append(left_bezier)
            remaining = remaining[split_idx:]
    
    return segments
```

## Pipeline Step 6: Stroke Width Measurement

Along each centerline, measure the stroke width (distance from centerline to edge of ink on both sides):

```python
def measure_stroke_width(letter_image, centerline_points):
    """Measure stroke width at each point along the centerline."""
    binary = binarize(letter_image)
    widths = []
    directions = []
    
    for i, point in enumerate(centerline_points):
        # Direction of the centerline at this point
        if i > 0 and i < len(centerline_points) - 1:
            tangent = centerline_points[i+1] - centerline_points[i-1]
        elif i == 0:
            tangent = centerline_points[1] - centerline_points[0]
        else:
            tangent = centerline_points[-1] - centerline_points[-2]
        
        direction = math.atan2(tangent[1], tangent[0])
        directions.append(direction)
        
        # Normal to the centerline
        normal = direction + math.pi / 2
        
        # Cast ray in both directions along the normal, find ink edges
        left_edge = cast_ray(binary, point, normal, max_distance=20)
        right_edge = cast_ray(binary, point, normal + math.pi, max_distance=20)
        
        width = left_edge + right_edge  # total width in pixels
        widths.append(width)
    
    return widths, directions
```

### Nib angle estimation from width/direction data

The nib angle is the angle where strokes are thinnest. Across many strokes:

```python
def estimate_nib_angle(all_widths, all_directions):
    """Estimate the nib angle from the width-direction relationship."""
    # Width should be proportional to |sin(direction - nib_angle)|
    # Find the nib_angle that best fits this relationship
    
    def model_error(nib_angle):
        predicted = [abs(math.sin(d - nib_angle)) for d in all_directions]
        # Normalize both to 0-1 range
        predicted_norm = normalize(predicted)
        widths_norm = normalize(all_widths)
        return sum((p - w)**2 for p, w in zip(predicted_norm, widths_norm))
    
    # Search over possible nib angles (25° to 55° typical for Bastarda)
    best_angle = minimize_scalar(model_error, bounds=(0.4, 1.0)).x  # radians
    
    return math.degrees(best_angle)
```

## Pipeline Step 7: Build Improved Letterform Guides

Combine the centerline traces from multiple exemplars into a canonical letterform guide:

```python
def build_letterform_guide(letter, exemplar_traces):
    """Average multiple traced exemplars into a canonical guide."""
    
    # Normalize all traces to the same coordinate system
    # (baseline at y=0, x-height at y=1, start at x=0)
    normalized = [normalize_trace(trace) for trace in exemplar_traces]
    
    # Compute the "average" trace using Dynamic Time Warping alignment
    # DTW aligns the traces temporally, then we average corresponding points
    reference = normalized[0]  # use first trace as initial reference
    
    for iteration in range(3):  # iterative averaging
        aligned_traces = [dtw_align(trace, reference) for trace in normalized]
        reference = average_points(aligned_traces)
    
    # Convert averaged points back to Bézier segments
    canonical_segments = fit_bezier_to_path(reference, max_error=0.3)
    
    # Extract keypoints from the canonical trace
    # Keypoints are at: start, end, direction reversals, and extrema
    keypoints = extract_keypoints(canonical_segments)
    
    # Measure the x_advance from the canonical trace
    x_advance = max(p.x for seg in canonical_segments for p in seg.points)
    
    # Build the guide
    guide = LetterformGuide(
        letter=letter,
        segments=canonical_segments,
        keypoints=keypoints,
        x_advance=x_advance,
        ascender=(max(p.y for seg in canonical_segments for p in seg.points) > 1.3),
        descender=(min(p.y for seg in canonical_segments for p in seg.points) < -0.2),
    )
    
    return guide
```

## Pipeline Step 8: Calibrate Nib Parameters

Using the stroke width data from Step 6 across all extracted letters:

```python
def calibrate_nib(all_width_data, all_direction_data):
    """Fit nib parameters to match the real manuscript's stroke characteristics."""
    
    # Estimate nib angle
    nib_angle = estimate_nib_angle(all_width_data, all_direction_data)
    
    # Estimate nib width (the maximum observed stroke width)
    nib_width_px = percentile(all_width_data, 95)  # 95th percentile to avoid outliers
    nib_width_mm = nib_width_px / dpi * 25.4
    
    # Estimate minimum hairline width
    min_width_px = percentile(all_width_data, 5)
    min_hairline_ratio = min_width_px / nib_width_px
    
    # Estimate pressure modulation range
    # Group widths by direction, look at width variance within direction groups
    # High variance at a given direction = large pressure effect
    direction_groups = group_by_direction(all_width_data, all_direction_data, n_bins=12)
    within_group_variance = [variance(group) for group in direction_groups]
    pressure_modulation = mean(within_group_variance) / nib_width_px
    
    return {
        'nib.angle_deg': nib_angle,
        'nib.width_mm': nib_width_mm,
        'nib.min_hairline_ratio': min_hairline_ratio,
        'stroke.pressure_modulation_range': pressure_modulation,
    }
```

---

## CLI Commands

```bash
# Full extraction pipeline from a manuscript image
scribesim extract --image werbeschreiben.jpg \
    --transcription "Unser freuntlich dienst..." \
    --output reference/ \
    --steps all

# Individual steps
scribesim extract-lines --image werbeschreiben.jpg -o reference/lines/
scribesim extract-words --lines reference/lines/ -o reference/words/
scribesim extract-letters --words reference/words/ --transcription text.txt -o reference/letters/
scribesim extract-exemplars --letters reference/letters/ -o reference/exemplars/
scribesim trace-centerlines --exemplars reference/exemplars/ -o reference/traces/
scribesim measure-widths --letters reference/letters/ --traces reference/traces/ -o reference/widths/
scribesim build-guides --traces reference/traces/ -o shared/hands/guides_extracted.toml
scribesim calibrate-nib --widths reference/widths/ -o shared/hands/nib_calibrated.toml

# Quick check: overlay extracted centerlines on the original image
scribesim extract-preview --image werbeschreiben.jpg --traces reference/traces/ -o debug/extraction_overlay.png
```

---

## What This Gives the Evolutionary Algorithm

### Before TD-008:
- Letterform guides: guessed keypoints, wrong proportions
- Exemplar set: empty or minimal
- Nib parameters: hand-tuned estimates
- Result: letters are recognizable but look nothing like Bastarda

### After TD-008:
- Letterform guides: traced from real Bastarda, correct proportions and stroke structure
- Exemplar set: 10-15 real instances per letter, sharp fitness signal
- Nib parameters: calibrated from actual stroke width measurements
- Result: the evolutionary algorithm starts from a much better place and converges toward the real manuscript's style

The evolutionary algorithm still does the work of producing natural variation and word-level flow. But it's now starting from seeds that are *already close to correct* and optimizing against exemplars that show *exactly what correct looks like*.

---

## What You Need to Provide

1. **The Werbeschreiben image** at the highest resolution you have
2. **A transcription of the Werbeschreiben text** (even partial — we need to know which letter is which)
3. **Optionally: 2-3 additional manuscript images** from BSB/e-codices for cross-validation (different scribes in the same style period help the algorithm generalize rather than overfitting to one hand)

---

## Implementation Priority

1. **Line + word segmentation** — get the Werbeschreiben split into words. This is standard image processing, can be done in Python with OpenCV.

2. **Letter segmentation** — the hardest step. Start with connected components + vertical stroke detection. Fall back to manual segmentation for the first pass if automated methods struggle.

3. **Exemplar extraction** — crop, normalize, and store 10+ instances per letter. This immediately improves the evolutionary fitness function even before the guides are updated.

4. **Centerline tracing + Bézier fitting** — extract writing paths. These become the new letterform guide segments.

5. **Nib calibration** — measure stroke widths, estimate nib angle and width. Update the nib parameters.

6. **Build improved guides** — average the traces, extract keypoints, produce new TOML guides.

7. **Re-run evolution with extracted guides + exemplars** — the acid test. Does the output look closer to the target?

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-21 | Initial draft — reference extraction pipeline | shawn + claude |
