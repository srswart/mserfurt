# TD-012 Addendum A — DP-Assisted Glyph Extraction

## Context
Manual glyph annotation in the Workbench is accurate but tedious. The operator must identify where each letter starts and ends within a connected Bastarda word — a process that requires careful visual judgment for every letter boundary. For a library of 8-15 allographs per letter across 26+ characters, this means hundreds of individual segmentation decisions.

DP can automate the segmentation step while keeping the human in the verification loop. If the transcription of a word is known (which it is — the operator can read the manuscript), the segmentation problem reduces to: find the optimal set of horizontal cut points that partition the word image into letter-sized segments matching the known transcript.

## The Algorithm: Forced Alignment via DP

### Input
- **Word image:** a cropped word from the reference manuscript (e.g., "schreiber")
- **Transcription:** the known character sequence: `['ſ', 'c', 'h', 'r', 'e', 'i', 'b', 'e', 'r']`
- **Template library:** the current set of allograph templates (even rough ones), or a character classifier

### The DP table

Let the word image have width W pixels. We need to place N-1 cut points to divide W into N segments (one per letter).

```
State: dp[i][x] = minimum cost to assign the first i letters 
                  using columns 0..x of the word image

Transition: dp[i][x] = min over all x' < x of:
            dp[i-1][x'] + match_cost(letter[i], image_columns[x'..x])

Where match_cost measures how well the image slice x'..x 
matches the expected letter[i].
```

```rust
fn dp_segment_word(
    word_image: &GrayImage,
    transcript: &[char],
    templates: &AllographLibrary,
) -> Vec<(usize, usize)> {  // returns (start_col, end_col) per letter
    let w = word_image.width() as usize;
    let n = transcript.len();
    
    // Expected width range for each letter (in pixels)
    // This constrains the search — an 'i' can't be 50px wide
    let width_ranges: Vec<(usize, usize)> = transcript.iter()
        .map(|&ch| expected_width_range(ch, word_image.height()))
        .collect();
    
    // DP table
    // dp[i][x] = minimum cost to assign letters 0..i ending at column x
    let mut dp = vec![vec![f64::MAX; w + 1]; n + 1];
    let mut back = vec![vec![0usize; w + 1]; n + 1];
    
    dp[0][0] = 0.0;  // base case: zero letters assigned at column 0
    
    for i in 1..=n {
        let ch = transcript[i - 1];
        let (min_w, max_w) = width_ranges[i - 1];
        
        for x in 1..=w {
            // Try all possible start columns for letter i
            let earliest_start = if x > max_w { x - max_w } else { 0 };
            let latest_start = if x > min_w { x - min_w } else { 0 };
            
            for x_start in earliest_start..=latest_start {
                if dp[i - 1][x_start] == f64::MAX { continue; }
                
                // Extract the candidate letter image
                let slice = &word_image.sub_image(
                    x_start as u32, 0, 
                    (x - x_start) as u32, word_image.height()
                );
                
                // How well does this slice match the expected letter?
                let cost = match_cost(ch, slice, templates);
                
                let total = dp[i - 1][x_start] + cost;
                
                if total < dp[i][x] {
                    dp[i][x] = total;
                    back[i][x] = x_start;
                }
            }
        }
    }
    
    // Traceback — find the best final column and work backward
    // The last letter should end near the right edge of the word image
    let mut best_end = w;
    let mut best_cost = f64::MAX;
    
    // Allow some slack at the right edge (trailing whitespace)
    for x in (w - w/10)..=w {
        if dp[n][x] < best_cost {
            best_cost = dp[n][x];
            best_end = x;
        }
    }
    
    // Trace back through the DP table
    let mut segments = Vec::new();
    let mut x = best_end;
    for i in (1..=n).rev() {
        let x_start = back[i][x];
        segments.push((x_start, x));
        x = x_start;
    }
    segments.reverse();
    
    segments
}
```

### Match cost function

The match cost compares a candidate image slice against what we expect for a given letter. Multiple signals can be combined:

```rust
fn match_cost(
    letter: char,
    slice: &GrayImage,
    templates: &AllographLibrary,
) -> f64 {
    let mut cost = 0.0;
    
    // --- Template matching ---
    // Compare against known allographs for this letter
    if let Some(allographs) = templates.get_rendered(letter) {
        let best_template_match = allographs.iter()
            .map(|template| {
                let resized = resize_to_match(template, slice);
                normalized_cross_correlation(slice, &resized)
            })
            .fold(0.0f64, f64::max);
        
        cost += (1.0 - best_template_match) * 5.0;
    }
    
    // --- Width plausibility ---
    // Is this slice a plausible width for this letter?
    let expected_width = expected_mean_width(letter, slice.height());
    let width_deviation = (slice.width() as f64 - expected_width).abs() / expected_width;
    cost += width_deviation * 2.0;
    
    // --- Vertical ink profile ---
    // Does the ink distribution match what we expect?
    // 'i' has ink only in the center; 'm' has three vertical strokes; etc.
    let v_profile = vertical_ink_profile(slice);
    let expected_profile = expected_vertical_profile(letter);
    if let Some(ep) = expected_profile {
        let profile_mismatch = profile_distance(&v_profile, &ep);
        cost += profile_mismatch * 3.0;
    }
    
    // --- Cut point quality ---
    // Good cut points fall in whitespace or thin connecting strokes
    // Penalize cuts through thick vertical strokes
    let left_edge_ink = column_ink_density(slice, 0);
    let right_edge_ink = column_ink_density(slice, slice.width() - 1);
    
    // Low ink at edges = good cut point (between letters)
    cost += left_edge_ink * 1.0;
    cost += right_edge_ink * 1.0;
    
    cost
}
```

### Expected width ranges

Bastarda letters have characteristic width ranges relative to the x-height:

```rust
fn expected_width_range(letter: char, image_height: u32) -> (usize, usize) {
    let x_height = image_height as f64 * 0.6;  // approximate
    
    let (min_ratio, max_ratio) = match letter {
        'i' | 'l' | '·' => (0.15, 0.40),
        'j' | 't' | 'r' => (0.25, 0.55),
        'a' | 'c' | 'e' | 'o' | 'n' | 'u' | 's' | 'ſ' => (0.35, 0.70),
        'd' | 'b' | 'h' | 'g' | 'p' | 'q' | 'v' => (0.40, 0.80),
        'f' | 'k' | 'z' => (0.35, 0.65),
        'm' | 'w' => (0.60, 1.10),
        _ => (0.30, 0.80),
    };
    
    let min_px = (x_height * min_ratio) as usize;
    let max_px = (x_height * max_ratio) as usize;
    
    (min_px.max(3), max_px)
}
```

---

## Integration with the Annotation Workbench

### The new workflow

**Before (fully manual):**
1. Operator sees a word image in the Workbench
2. Operator reads the word (e.g., "schreiber")
3. Operator manually draws 8 cut boundaries between the 9 letters
4. Operator labels each segment
5. Repeat for every word → hundreds of manual segmentation decisions

**After (DP-assisted):**
1. Operator sees a word image in the Workbench
2. Operator types the transcription: "schreiber"
3. DP proposes cut boundaries instantly
4. Workbench displays the proposed segmentation overlaid on the image
5. Operator reviews:
   - **Accept** — boundaries look correct (most common case)
   - **Nudge** — drag one or two boundaries to better positions
   - **Reject** — request re-segmentation with adjusted parameters
6. Accepted segments are saved as labeled glyph crops
7. Repeat for every word → but each word takes 5 seconds instead of 60

### Workbench UI integration

```
┌─────────────────────────────────────────────────────────────┐
│  Word: "schreiber"    Transcript: ſ c h r e i b e r        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ ſ │ c │ h │ r │ e │ i │ b │ e │ r │               │    │
│  │   │   │   │   │   │   │   │   │   │  [word image] │    │
│  │   │   │   │   │   │   │   │   │   │               │    │
│  └─────────────────────────────────────────────────────┘    │
│       ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑                                     │
│       proposed cut boundaries (draggable)                   │
│                                                             │
│  Confidence: 0.87  (high — all boundaries fall in gaps)     │
│                                                             │
│  [ Accept All ]  [ Accept & Nudge ]  [ Re-segment ]        │
│                                                             │
│  DP cost breakdown:                                         │
│  ſ: 0.12  c: 0.08  h: 0.15  r: 0.11  e: 0.07              │
│  i: 0.05  b: 0.19  e: 0.09  r: 0.14                       │
│  Highest cost: 'b' (0.19) — may need manual adjustment     │
└─────────────────────────────────────────────────────────────┘
```

The cost breakdown flags which letters the algorithm is least confident about. The operator can focus attention on the flagged letters rather than checking all nine.

### Confidence scoring

```rust
fn segmentation_confidence(dp_costs: &[f64]) -> f64 {
    // High confidence = all individual letter costs are low
    // Low confidence = one or more letters had high match cost
    let max_cost = dp_costs.iter().cloned().fold(0.0f64, f64::max);
    let mean_cost = dp_costs.iter().sum::<f64>() / dp_costs.len() as f64;
    
    // Transform to 0-1 range where 1 = very confident
    let confidence = 1.0 / (1.0 + mean_cost * 2.0);
    
    // Penalize if any single letter is very uncertain
    let worst_penalty = if max_cost > 1.0 { (max_cost - 1.0) * 0.2 } else { 0.0 };
    
    (confidence - worst_penalty).max(0.0).min(1.0)
}
```

### Handling ligatures and special cases

Some Bastarda letter combinations are written as ligatures that can't be cleanly separated:

```rust
fn preprocess_transcript(raw: &str) -> Vec<String> {
    // Detect ligature sequences and keep them as single units
    let mut result = Vec::new();
    let chars: Vec<char> = raw.chars().collect();
    let mut i = 0;
    
    while i < chars.len() {
        // Check for known ligatures (3-char first, then 2-char)
        if i + 2 < chars.len() {
            let tri = format!("{}{}{}", chars[i], chars[i+1], chars[i+2]);
            if LIGATURES.contains(&tri.as_str()) {
                result.push(tri);
                i += 3;
                continue;
            }
        }
        if i + 1 < chars.len() {
            let bi = format!("{}{}", chars[i], chars[i+1]);
            if LIGATURES.contains(&bi.as_str()) {
                result.push(bi);
                i += 2;
                continue;
            }
        }
        result.push(chars[i].to_string());
        i += 1;
    }
    
    result
}

const LIGATURES: &[&str] = &[
    "ch", "ck", "ſt", "ſſ", "tz", "ſch", "ng", "pf", "sp",
];
```

When the transcript contains "sch" in "schreiber", the DP treats it as a single unit — it looks for a 3-letter-wide segment that matches the "sch" ligature template, rather than trying to split s, c, h individually.

---

## Bootstrapping: First Run Without Templates

On the very first run, the allograph library is empty — there are no templates to match against. The DP can still work using structural heuristics:

```rust
fn bootstrap_match_cost(letter: char, slice: &GrayImage) -> f64 {
    let mut cost = 0.0;
    
    // Width plausibility (primary signal without templates)
    let expected = expected_mean_width(letter, slice.height());
    cost += ((slice.width() as f64 - expected) / expected).abs() * 4.0;
    
    // Structural features
    let has_ascender = top_ink_ratio(slice) > 0.3;  // ink in top 30% of image
    let has_descender = bottom_ink_ratio(slice) > 0.2;  // ink below baseline
    let n_vertical_strokes = count_vertical_strokes(slice);
    
    // Penalize structural mismatches
    match letter {
        'b' | 'd' | 'h' | 'k' | 'l' | 'ſ' | 'f' | 't' => {
            if !has_ascender { cost += 3.0; }  // these letters must have ascenders
        },
        'g' | 'p' | 'q' | 'y' | 'f' | 'ſ' => {
            if !has_descender { cost += 3.0; }  // these must have descenders
        },
        'm' => {
            if n_vertical_strokes < 3 { cost += 2.0; }  // m has 3 minims
        },
        'n' | 'u' => {
            if n_vertical_strokes < 2 { cost += 2.0; }  // 2 minims
        },
        'i' => {
            if n_vertical_strokes > 1 { cost += 1.5; }  // just 1 minim
        },
        _ => {}
    }
    
    // Cut point quality (always available)
    let left_ink = column_ink_density(slice, 0);
    let right_ink = column_ink_density(slice, slice.width() - 1);
    cost += (left_ink + right_ink) * 1.5;
    
    cost
}
```

This bootstrap mode won't be as accurate as template-based matching, but it will propose reasonable boundaries for the first batch of words. After the operator approves those segmentations and the resulting crops are evolved into allograph genomes (TD-008), the template library is populated and subsequent segmentations become much more accurate. The system bootstraps itself: each round of annotation makes the next round easier.

---

## Performance

| Operation | Time | Note |
|---|---|---|
| DP segmentation per word (10 letters, W=300px) | ~20ms | With template matching |
| Bootstrap segmentation (no templates) | ~5ms | Structural heuristics only |
| Full word with Workbench UI response | <100ms | Feels instant to operator |
| Batch segmentation of 50 words | ~1s | For bulk processing |

The operator's experience: type the transcription, segmentation appears instantly, review and accept. The bottleneck is human judgment, not computation.

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-27 | Initial draft — DP-assisted glyph extraction | shawn + claude |
