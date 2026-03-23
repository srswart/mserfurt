---
advance:
  id: ADV-SS-ALLOGRAPH-001
  title: Contextual Style Memory and Experimental Allograph Variation
  system: scribesim
  primary_component: evo
  components:
  - evo
  - cli
  started_at: 2026-03-23T00:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-23T09:15:00Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - experimental
  evidence:
  - tdd:red-green
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Reduce the printed, clone-like feel of repeated words and letters in the
evolutionary renderer without losing the sense that one disciplined Bastarda
scribe wrote the page. Introduce folio-level style memory, repeated-word priors,
contextual glyph memory, and an experimental bounded allograph pass that varies
supported letters by word position and neighboring letter class rather than by
free-form glyph mutation.

## Behavioral Change

After this advance:
- folio `evo` rendering maintains a running `StyleMemory` across the page
- repeated words contribute soft priors for slant, total width, and per-glyph
  advances instead of being either exact clones or fully independent redraws
- evolution seeding can start from recent same-word genomes
- fitness uses a soft consistency term so repeated words stay recognizably in
  the same hand without collapsing into templates
- glyph memory is contextual, keyed by:
  - letter identity
  - start/middle/end/single position in the word
  - class of the previous character
  - class of the next character
- experimental `character-model deep` now uses bounded contextual allographs
  rather than unconstrained per-glyph mutation
- supported experimental allograph letters are currently `i`, `n`, `e`, `r`,
  and `s`
- `render-line` and `render-sample` can be used to evaluate these character
  variation experiments on small slices before applying them to full folios

## Planned Implementation Tasks

- [x] Add `StyleMemory` for global, same-word, same-letter, and contextual
  same-letter history
- [x] Use style priors during population initialization
- [x] Add soft style-consistency pressure to fitness evaluation
- [x] Register completed evolved words back into folio memory during line/folio
  rendering
- [x] Implement contextual glyph-memory lookup using start/middle/end and
  neighbor-class buckets
- [x] Replace the earlier free-form experimental character mutation pass with a
  bounded contextual allograph pass
- [x] Support catalog/context-driven `s` selection (`long_s` vs `round_s`) and
  small bounded variants for high-repeat letters
- [x] Add `render-sample` for two-line and multiline experiments
- [x] Test: contextual glyph memory is preferred when available and falls back
  cleanly when sparse
- [x] Test: bounded allograph pass preserves glyph count and expected contextual
  `s` behavior

## Risk + Rollback

**Risks:**
- too much contextual bias can reintroduce templating under a more subtle name
- the current allograph family is intentionally narrow and still experimental;
  over-aggressive transforms can damage letter integrity
- `character-model deep` is not yet suitable as the default public folio mode

**Rollback:**
- keep style memory but disable contextual allograph application
- force `character-model standard` on sample/line experiments
- remove the style-consistency term from fitness if it proves to over-constrain
  variation

## Evidence

- [x] `uv run pytest tests/test_evo_style.py tests/test_evo_allograph.py tests/test_scribesim_cli.py::TestExperimentalLineAndSample::test_render_line_accepts_deep_character_model`
- [x] Two-line sample renders demonstrate contextual variation without exact
  same-word reuse
- [x] Contextual glyph memory now distinguishes the same letter at word start,
  middle, and end, with neighbor classes taken into account
