---
advance:
  id: ADV-SS-TRANSCRIBE-001
  title: Manuscript Transcription CLI — Few-Shot Prompt, Retry Pass, Pipeline Integration
  system: scribesim
  primary_component: transcribe
  components:
  - transcribe
  - cli
  started_at: 2026-03-21T23:30:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T18:22:05.635297Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  status: complete
---

## Objective

Promote the one-off `transcribe_words.py` script into a first-class `scribesim transcribe-words` CLI subcommand, and raise transcription quality from ~75% recognition to a target of ≥88%.

Three improvements shipped together:

**Part A — Few-shot image examples in the prompt:**
The current system prompt describes Bastarda script in text only.  Claude vision performs significantly better when shown concrete glyph→letter mappings.  The improved prompt will include 4–5 example word crop images (drawn from `reference/letters_alpha/` or a curated `scripts/transcription_examples/` directory) as image content blocks before the target crop, with their known transcriptions.  This grounds the model in the specific hand style rather than relying on general Bastarda knowledge.

**Part B — Second-pass retry on unknowns:**
After the main batch completes, crops that returned `?` are re-sent in a second batch with a more permissive prompt: "Give your best guess even if uncertain — prefix uncertain readings with ~".  Soft results (prefixed with `~`) are accepted into the transcription file and passed to `extract-letters`, which treats `~`-prefixed labels the same as certain ones for letter-crop assignment (the tilde prefix is stripped).  This handles cases where the first-pass system prompt's high-confidence requirement causes unnecessary refusals.

**Part C — CLI integration (`scribesim transcribe-words`):**
`transcribe_words.py` becomes `scribesim/transcribe/batch.py` with a proper module structure.  The CLI gains:

```
scribesim transcribe-words \
    --words reference/fullres_words \
    --output reference/transcription.txt \
    --examples scripts/transcription_examples/ \
    --retry-unknowns \
    --poll-interval 15
```

The full TD-008 pipeline sequence becomes:
```
extract-lines → extract-words → transcribe-words → extract-letters --transcription
```

## Behavioral Change

- `scribesim transcribe-words` is a new CLI subcommand (no existing command changed)
- `transcribe_words.py` at repo root remains but is superseded; can be removed post-advance
- `extract-letters --transcription` unchanged — still reads one-word-per-line text file
- The `~` soft-confidence prefix is stripped by `extract-letters` before labeling (new behaviour added there)

## Planned Implementation Tasks

1. Create `scribesim/transcribe/` module with `__init__.py`, `batch.py`, `examples.py`
2. Move and refactor `transcribe_words.py` → `batch.py`:
   - `build_requests(crops, examples, model)` — constructs `Request` list with few-shot images
   - `clean_response(raw)` — first-line extraction + alpha/space filter (existing logic)
   - `collect_results(batch_id, crops, client)` — poll + collect in crop order
3. Add `examples.py`:
   - `load_examples(examples_dir)` — reads `{letter}.png` + `{letter}.txt` pairs from a directory
   - `build_few_shot_content(examples)` — interleaves image blocks and known-transcription text blocks for the system message
4. Create `scripts/transcription_examples/` with 5 curated example crops + transcription text files (hand-picked clear Bastarda words from BSB 95r)
5. Add retry pass in `batch.py`:
   - `retry_unknowns(unknowns, examples, client, model)` — second batch with permissive prompt, `~` prefix instruction
   - Merge retry results back: replace `?` entries only; keep `~word` soft labels
6. Add `extract-letters` support for `~` prefix: strip `~` from word before character-by-character labeling (soft confidence is invisible to downstream processing)
7. Add `transcribe-words` subcommand to `scribesim/cli.py`
8. Tests:
   - `test_clean_response_strips_reasoning` — reasoning bleed-through → `?`
   - `test_clean_response_soft_prefix_preserved` — `~der` survives cleaning
   - `test_build_few_shot_content_image_count` — N examples → 2N content blocks (image + text each)
   - `test_retry_unknowns_merges_results` — known results preserved; `?` entries replaced by retry output
   - `test_extract_letters_strips_tilde` — `~der` → same labeling as `der`
   - `test_transcribe_words_cli_invokes_batch` — CLI smoke test with mocked API client

## Risk + Rollback

- **API cost**: two batches (main + retry on ~25% unknowns) ≈ 1.25× original cost. Batches API 50% discount applies to both.
- **Few-shot image selection**: curated examples must be representative of the specific hand. Poor example selection could mislead the model. Mitigated by using real crops from the manuscript being processed, and keeping example count small (4–5).
- **Soft labels (`~`)**: if the retry pass produces bad soft labels, letter crops will be misfiled under wrong characters. Impact: dilutes DTW averaging for those characters but doesn't corrupt existing good data. Mitigated by keeping soft-label crops separate in `extract-letters` output (`{char}/soft/` subdir) so they can be inspected.
- **Rollback**: `transcribe_words.py` remains functional. CLI subcommand is additive.

## Evidence

