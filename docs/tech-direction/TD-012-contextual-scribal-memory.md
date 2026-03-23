# Tech Direction: TD-012 — Contextual Scribal Memory and Allograph Selection

## Status
**Active** — supplements TD-007's evolutionary renderer and informs the current
`evo` folio pipeline.

## Context

TD-007 solved the largest problem first: stop trying to derive Bastarda from
unstable mechanics and instead evolve word forms toward recognizable, legible
targets. That removed the most obvious "printed font with jitter" failure mode.
But a second-order problem remained: repeated words and repeated letters still
looked too similar. The page could be legible and even plausibly handwritten,
yet still betray itself by reusing nearly identical shapes.

The wrong response is to make every occurrence fully independent. If every `und`
or every medial `i` is re-evolved with no memory, the page stops feeling like a
single disciplined scribe. A real scribe has memory and habit. The renderer
needs the same.

TD-012 defines that missing layer: contextual scribal memory plus bounded
allograph variation.

## Core Principle

```
WRONG:
  repeated word -> reuse exact cached genome
  repeated letter -> identical canonical glyph

ALSO WRONG:
  repeated word -> evolve from scratch with no memory
  repeated letter -> free-form per-glyph mutation

TD-012:
  repeated word -> evolve from soft prior informed by recent same-word history
  repeated letter -> choose among bounded contextual allographs informed by
                     position, neighbours, and recent same-letter history
```

The goal is: same hand, different act.

## Part 1: Folio-Level Style Memory

The renderer maintains a running `StyleMemory` during line and folio
composition. It stores:

- recent global genomes across the folio
- recent same-word genomes
- recent same-letter glyphs
- recent contextual same-letter glyphs

This memory is descriptive, not deterministic. It does not force the next word
to match a template. It provides a neighborhood of plausible choices for the
same hand.

### Word priors

For repeated words, memory contributes soft priors for:

- target slant
- overall word width
- per-glyph advance tendencies

These priors affect:

- population initialization
- soft consistency scoring in fitness

This replaces the older binary choice between exact reuse and full independence.

## Part 2: Contextual Glyph Memory

Glyph memory is keyed by more than letter identity.

Each glyph prior is contextualized by:

- the letter itself
- its bucket within the word: `start`, `middle`, `end`, or `single`
- the class of the previous character
- the class of the next character

Neighbor classes are coarse scribal families such as:

- minim
- round
- ascender
- descender
- other
- mark

This matters because a medial `i` after `n` is not executed the same way as an
initial `i` before `o`, even when the underlying letter is the same.

## Part 3: Bounded Allographs, Not Free Mutation

Earlier experiments with free-form character-level mutation increased variation,
but they also damaged legibility and Bastarda discipline. TD-012 rejects open
ended per-glyph mutation as the primary mechanism for character variation.

Instead, variation should come from bounded allograph families.

Each supported letter has a small legal family of variants. Selection is guided
by:

- word position
- neighboring letter classes
- recent contextual same-letter memory
- a small amount of bounded randomness

Current experimental coverage focuses on the letters that contribute the most to
clone-like repetition:

- `i`
- `n`
- `e`
- `r`
- `s`

The `s` family is contextual at the catalog level:

- medial `s` prefers `long_s`
- final `s` prefers `round_s`

Other supported letters currently use small bounded geometry variants. This is
explicitly experimental and should expand through curated Bastarda families, not
through unconstrained mutation.

## Part 4: Quality Modes

The public folio renderer has two evolution quality modes:

### `balanced`

- reuses evolved word genomes where appropriate
- still applies style memory
- favors practical runtime for full folio rendering

### `deep`

- disables word-genome reuse
- re-evolves each occurrence
- keeps style memory as a prior so the page still reads as one hand
- is intended for natural-first rendering where runtime is secondary

`deep` is not "memory off." It is "no cloning, but still one scribe."

## Part 5: Observability Requirements

Because renderer behavior is now materially different between modes, the system
must make the active strategy visible.

Every folio render should report:

- page renderer
- heatmap renderer
- evolution quality
- cache policy
- whether style memory is active
- word-shape memory policy

Long renders should also expose live progress:

- per-line in balanced mode
- per-word in deep mode

This is not a UI nicety. It is required for calibration and review because the
difference between cached reuse and per-occurrence evolution is not otherwise
obvious from the command line alone.

## Part 6: Constraints

The following constraints are mandatory:

1. Legibility remains the first priority.
2. Character variation must preserve the sense of a single disciplined Bastarda
   hand.
3. Contextual memory may bias selection, but it must not collapse repeated words
   into exact clones.
4. Allograph variation must be bounded and curated; free-form glyph mutation is
   only acceptable as an isolated experiment, not as the production default.
5. When `page_renderer = "evo"`, the pressure heatmap must be derived from the
   same evolved stroke sweep as the page image so downstream Weather effects
   target the actual writing.

## Part 7: Recommended Next Steps

1. Expand curated allograph families for the highest-frequency Bastarda letters
   and abbreviatory marks.
2. Replace simple geometry tweaks with manuscript-derived contextual variants.
3. Add evaluation fixtures that compare repeated words and repeated letters for
   "same hand, non-clone" behavior.
4. Keep `character-model deep` experimental until those curated allograph
   families are broad enough to preserve both legibility and Bastarda identity.

## Relationship to Other TDs

- **TD-007** defines the word-level evolutionary renderer.
- **TD-010** defines the continuous ink reservoir that modulates those evolved
  strokes.
- **TD-012** defines how repeated words and letters remain coherent as one hand
  without looking mechanically reused.

## Revision History

| Date | Change | Author |
|---|---|---|
| 2026-03-23 | Initial draft — contextual scribal memory, deep mode, bounded allographs | shawn + codex |
