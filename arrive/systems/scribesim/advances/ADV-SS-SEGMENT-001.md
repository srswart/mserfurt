---
advance:
  id: ADV-SS-SEGMENT-001
  title: Manuscript Segmentation — Line, Word, Letter Split from Image (TD-008 Steps 1-3)
  system: scribesim
  primary_component: refextract
  components:
  - refextract
  started_at: 2026-03-21T10:36:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T10:48:20.379314Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence:
  - tdd:red-green
  - tests:unit
  status: complete
---

## Objective

Implement the first three steps of the TD-008 reference extraction pipeline as a new module `scribesim/refextract/`. This module segments a high-resolution manuscript image (Werbeschreiben or BSB samples) into labeled letter images ready for exemplar extraction.

**Step 1 — Line segmentation**: Horizontal projection profile approach: sum pixel intensities per row, find inter-line valleys, extract line strips. Optionally wire Kraken `blla.segment()` as an alternative backend.

**Step 2 — Word segmentation**: Within each line, detect vertical white-space gaps using column projection profiles. Gap threshold = 5% of peak ink density. Split at gap centers where gap width ≥ 5 pixels.

**Step 3 — Letter segmentation**: Three approaches composed together:
- Connected components (well-separated letters, accept if width is plausible for letter count)
- Vertical stroke detection (thick Bastarda downstrokes anchor letter boundaries; erode horizontally, find peaks in column projection)
- Width-heuristic validation: reject components that are too wide (likely multi-letter) and subdivide at thinnest vertical column

Output: `reference/letters/{letter}/werbeschreiben_{nnn}.png` — labeled letter crops, one directory per character class.

**CLI**: `scribesim extract-lines`, `scribesim extract-words`, `scribesim extract-letters` subcommands.

## Behavioral Change

Adds new module `scribesim/refextract/segment.py`. No changes to existing rendering or evolution code. Outputs a `reference/letters/` tree used by ADV-SS-EXEMPLAR-002.

## Planned Implementation Tasks

1. Create `scribesim/refextract/__init__.py`, `scribesim/refextract/segment.py`
2. `segment_lines(image_path) -> list[LineStrip]` — projection-based line split
3. `segment_words(line_strip) -> list[WordCrop]` — column projection gap detection
4. `segment_letters(word_crop, word_text=None) -> list[tuple[str, np.ndarray]]` — CC + vertical stroke detection
5. `save_letter_crops(letter_list, output_dir)` — write to `reference/letters/{char}/`
6. Add `scribesim extract-lines/extract-words/extract-letters` CLI subcommands in `scribesim/cli.py`
7. Unit tests: projection finds correct line count on synthetic image; gap detection finds word boundaries; CC finds individual letters on synthetic word

## Risk + Rollback

- **New dependency**: `opencv-python` (or `scikit-image`) for morphological ops + connected components. Both are already present transitively via scipy/PIL; cv2 is additive.
- **Rollback**: module is entirely new; no existing code is modified. Removal is safe.
- **Labeling accuracy**: Letter segmentation of Bastarda is hard. The first pass will have errors — this is expected. Manual correction of the labeling is planned as a fallback (ADV-SS-EXEMPLAR-002 can accept manually labeled inputs).

## Evidence

