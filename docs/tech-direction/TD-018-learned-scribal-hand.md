# Tech Direction: TD-018 — Learned Scribal Hand Synthesis

## Status

**Proposed** — new primary track for scribal hand rendering. Replaces the procedural
letterform generation paradigm (TD-002 → TD-017) with a learned generative model,
while keeping the XL authoring, layout, ground-truth, and Weather systems intact.

## Summary

Seventeen tech directions and ~99 ScribeSim advances have tried to make a
*procedural* pen simulator write like a 15th-century scribe. The output still reads
as one of two failure modes: **mechanical/font-like** (fixed or lightly-jittered
Bézier catalogs) or **unrecognizable** (freeform dynamics, sparse-keypoint recovery).
TD-018's position is that this is not an implementation deficiency — it is a
**paradigm ceiling**. The project should stop trying to author or optimize the
generative *process* (trajectories, nib physics, corridor controllers) and instead
learn the visual *distribution* of real Bastarda writing directly from manuscript
images, using a style-conditioned latent diffusion handwriting-generation model
fine-tuned on medieval script corpora.

This is the same architectural decision the project already made for aging: TD-011
replaced procedural weathering with `gpt-image-1` compositing because parchment
realism was a distribution-learning problem. Letterform realism is the same class
of problem, one level down.

---

## Part 1 — Evaluation of the Current Approach

### 1.1 What has been tried (evidence from the repo)

| Era | Tech direction | Approach | Observed failure |
|-----|----------------|----------|------------------|
| Typeface model | TD-002 (pass 2) | ~90 hand-authored Bézier glyphs, nib sweep, layout | "Like a very good typeface" (TD-005's own words) |
| Physics v2 | TD-002/003/004 | Multi-scale movement, physics nib, ink filters, CMA-ES parameter fitting | Better *process* realism; letterforms still retrieved, not written |
| Generative hand | TD-005/006 | Hand state machine + sparse keypoints + PD control | Chaos when loose, "precise, almost mechanical" when clamped |
| Evolutionary scribe | TD-007 | Word/glyph/stroke genomes, F1–F7 fitness, Rust batch eval | Letters improve in isolation; words lack gesture; smoothness terms fight character |
| Reference extraction | TD-008/009 | BSB IIIF harvest, segmentation, centerline tracing, exemplar corpora | Auto segmentation unreliable → reviewed annotation workbench required |
| Guided recovery | TD-014 (current) | Dense path guides + corridor controller + curriculum + gates | Legible but still corridor-tracking a fixed nominal path; expressive parameters largely inert (TD-014 "Parameter Activation Recovery") |

Concrete evidence of the gap, side by side: compare any current render
(`render-output/f01r.png`) with the target exemplars in `docs/samples/`
(e.g. `v2_bsb00061176_00030_full_full_0_default.jpg`). The render shows uniform
stroke weight, identical repeated letterforms, evenly spaced upright words, and
clean edges. The target shows continuous ink-weight modulation within single
strokes, no two identical instances of the same letter, word-level slant and
rhythm variation, join ligatures that reshape adjacent letters, and stroke edges
textured by ink-parchment interaction.

### 1.2 Why the procedural paradigm has a ceiling

The system is solving an **inverse problem with the wrong observables**. We have
*images* of the target distribution (BSB manuscripts) but the engine's degrees of
freedom are *process parameters* (control points, corridor widths, pressure curves,
tremor amplitudes). Every track so far attempts to recover process from product:

1. **Authoring** (TD-002): a human guesses the process. Result: a font.
2. **Optimization** (TD-003/004/007): CMA-ES/GA search process-space against image
   metrics (NCC, thick/thin ratio, DTW). These metrics are weak proxies for
   "looks written"; optimizers exploit them (F6 curvature smoothness actively
   *removes* character). Result: polished font.
3. **Control theory** (TD-005/006/014): simulate the hand. But a corridor-following
   PD controller reproduces its nominal guide by construction — variation must be
   injected as bounded noise, which is exactly the "font + jitter" signature the
   eye detects. TD-014's own findings confirm most expressive parameters are inert.

The missing ingredient in all three is a **learned prior over what real writing
looks like**. Human perception of "written vs. typeset" keys on high-order
correlations (how entry strokes anticipate the next letter, how ink load decays
across a word, how allograph choice depends on position and neighbors, how
baseline, slant, and letter width co-vary under speed). These correlations are
present in the ~35–38k LOC of ScribeSim only insofar as someone hand-coded them.
A generative image model absorbs them from data.

### 1.3 What the current codebase gets right (and must be kept)

The investment is not wasted. The following subsystems are exactly what the
learned track needs and would otherwise have to be built:

- **XL** — text authoring, folio JSON, register/CLIO-7 annotations. Unchanged.
- **Layout** (`scribesim/layout/`) — page geometry, ruling, Knuth-Plass breaking,
  lacunae. The learned model generates *word/line images*; layout still decides
  *where they go*. Unchanged in role.
- **Movement/imprecision** (`scribesim/movement/`) — baseline wander, ruling
  drift, margin drift operate at placement level and compose cleanly with
  generated word images.
- **Reference pipeline** (TD-008/009: `refselect`, `refextract`, `annotate`) —
  IIIF harvest with provenance, line/word segmentation, the reviewed annotation
  workbench, and the transcription CLI become the **training-corpus builder** for
  the anchor hand.
- **Validation discipline** (TD-014 `handvalidate` gates, `metrics/`) — the
  gate-based promotion culture transfers directly; only the metrics change.
- **Ground truth** (`groundtruth/page_xml.py`) — PAGE XML emission stays; the
  polygon source changes (see §2.6).
- **Weather** — consumes PNG + folio JSON; untouched.

What gets **demoted to fallback**: the glyph catalog, evo as a folio renderer,
handflow/curriculum as the primary hand model. None are deleted; TD-014 remains
the non-ML fallback path and its corridor render can serve as structural
conditioning for a hybrid mode (§3.3).

---

## Part 2 — Recommended Architecture

### 2.1 Core decision

Adopt a **style-conditioned latent diffusion handwriting generation (HTG) model**,
fine-tuned on transcribed medieval script line/word images, as the letterform
engine. Generation is conditioned on (a) the target text string from XL folio JSON
and (b) a fixed set of style exemplar images from one real anchor hand, so the
whole codex is "written" by one consistent scribe.

```
XL folio JSON ─────────────────────────────┐
                                           ▼
shared anchor-style exemplars ──▶  ScribeHand (fine-tuned LDM)
                                           │  word/line strips (ink alpha)
                                           ▼
             layout.place() ──▶  page compositor (+ movement model)
                                           │
                              HTR fidelity gate (reject/regenerate)
                                           │
                                           ▼
                      {fid}.png + {fid}.xml (word-level PAGE XML)
                                           │
                                           ▼
                                       Weather (unchanged)
```

### 2.2 Model selection

| Candidate | Paradigm | Granularity | Style input | Fit |
|-----------|----------|-------------|-------------|-----|
| **One-DM** (ECCV 2024) | Latent diffusion | word | 1 style sample, high-frequency style module | **Primary candidate** — one-shot style suits a single anchor hand; open PyTorch code + weights |
| **DiffusionPen** (ECCV 2024) | Latent diffusion (SD-1.5 VAE) | word | 5-shot metric-learning style encoder | **Co-primary** — style mixing/noising gives controlled per-folio drift; open code + HF weights |
| DiffBrush (ICCV 2025) | Latent diffusion | full line | style samples | Phase-2 upgrade for inter-word rhythm once word-level works |
| VATr++ | GAN/transformer | word | visual archetypes | Fallback if diffusion fine-tune underperforms; cheaper inference |
| Graves-RNN / DiffInk (trajectory) | online-trajectory models | stroke | pen traces | **Rejected** — requires online trajectory data that does not exist for medieval hands |
| `gpt-image-1` / hosted image APIs | prompt-only | page | prompt text | **Rejected for letterforms** — no verbatim text control, no reproducible style anchor (fine for Weather backgrounds, as today) |

Decision: start with **One-DM and DiffusionPen in parallel bring-up** (both are
small enough to fine-tune on one 24 GB GPU), select by the gate metrics in §2.7.

### 2.3 Training data plan

Two tiers, both flowing through existing ARRIVE-governed tooling:

**Tier 1 — script-family corpus (breadth).**
[CATMuS Medieval](https://huggingface.co/datasets/CATMuS/medieval) (ICDAR 2024):
200+ manuscripts, 160k+ transcribed lines, 8th–16th c., with per-line metadata
including script family (Textualis, **Cursiva, Bastarda, Hybrida**), century, and
language. Filter to cursiva/bastarda/hybrida, 14th–16th c., German + Latin →
an estimated 10–40k lines. Optionally add TRIDIS (diplomatic charters, same
families). This teaches the model the *script*, including MUFI special characters
and abbreviation marks.

**Tier 2 — anchor hand corpus (identity).**
One BSB manuscript selected through the existing TD-009 `refselect` pipeline
(the provenance chain already points at Cgm 628 and the harvested sample set of
ADV-SS-REFSELECT-008). Segment lines with existing `extract-lines`/`extract-words`,
transcribe with `transcribe-words` + workbench review, freeze as
`shared/training/scribehand/anchor_v1`. Target 300–1,000 reviewed line/word pairs.
Fine-tune sequence: base HTG weights → Tier 1 → Tier 2 (low LR), so the model is
first a Bastarda writer, then specifically Konrad.

**Charset contract.** XL output (Frühneuhochdeutsch with ß, umlauts, long s,
interpuncts, roman numerals) must map into the training charset (CATMuS uses MUFI
diplomatic conventions). A normalization table lives with the corpus manifest and
is validated by the corpus gate (unmappable characters fail loudly, mirroring
TD-014's exact-character-coverage lesson — no silent alias substitution).

### 2.4 Style anchoring and CLIO-7 modifiers

- **Codex consistency:** a fixed exemplar set (5–10 word images from the anchor
  hand) is frozen as `shared/models/scribehand/style_anchor_v1/`. All folios
  condition on it. Determinism policy: fixed seeds per (folio, line, word index).
- **Narrative drift:** the CLIO-7 modifier stack (`[modifiers.f06r]` pressure,
  fatigue, smaller hand…) maps to generation-time controls instead of physics
  parameters: style-embedding interpolation/noise magnitude (DiffusionPen supports
  this natively), guidance scale, x-height scaling at composition, ink darkness in
  the compositing pass, and exemplar subset selection (e.g. hastier exemplars for
  fatigued folios). This preserves the manuscript's emotional arc contract without
  a physics engine.

### 2.5 Page composition

Generated word strips are grayscale ink masks. Composition reuses the existing
stack: `layout.place()` computes word slots (Knuth-Plass, kerning norms replaced
by measured strip advances); the movement model applies baseline wander, word
envelope offsets, and ruling imprecision; strips are alpha-composited with the
existing sepia ink blending and (optionally) the TD-010 ink-cycle darkness curve
applied as a per-word tone modulation. Lacuna opacity handling is unchanged.

Because generation is word-granular, **word bounding boxes are known exactly at
composition time**, which is what Weather's word-level pre-degradation
(`weather/worddegrade.py`) consumes.

### 2.6 Ground truth contract change

Current PAGE XML claims glyph-level polygons derived from Bézier geometry. With a
learned renderer, exact glyph polygons are no longer free. Contract amendment
(requires a TD-001 addendum):

- **Word-level** PAGE XML (word bbox + baseline + transcription) is emitted by
  construction — this is what eScriptorium/Kraken import and Weather actually need.
- **Glyph-level** polygons become optional, recoverable by forced alignment
  (Kraken CTC alignment of the known text against the generated strip) where a
  downstream consumer genuinely needs them.

### 2.7 Text-fidelity and style gates (the new `handvalidate`)

The TD-011 invariant "letterforms are never touched by AI" is replaced by
**"every AI-generated word is verified to read as its source text"**:

1. **HTR-in-the-loop rejection sampling.** Fine-tune a Bastarda HTR model
   (Kraken or TrOCR-base on the same Tier-1/Tier-2 corpus — reference models
   trained on CATMuS already exist) and score every generated word. Words failing
   CER/confidence thresholds are regenerated with a new seed (bounded retries,
   then flagged for review). Provenance JSON records seed, retries, and scores per
   word — same pattern as Weather's provenance sidecars.
2. **Style-distance gate.** Writer-identification embedding distance (the
   DiffusionPen style encoder, or a writer-ID net trained on Tier 1) between
   generated words and the anchor exemplars; plus FID/KID on line crops
   generated-vs-anchor. Catches style drift and mode collapse.
3. **Distributional realism checks.** The existing `metrics/` suite (stroke-width
   distributions, slant, spacing CV) compares generated pages against anchor
   manuscript pages — now used as *acceptance* metrics, not optimization targets,
   which removes the metric-gaming failure mode of TD-003/007.
4. **Human review.** The annotation workbench gains a side-by-side
   generated-vs-anchor review mode; promotion to default renderer requires a
   reviewed folio set, mirroring TD-014's promotion discipline.

### 2.8 Compute requirements

- **Fine-tuning:** single 24 GB GPU (RTX 4090 / A10G class) is sufficient for
  One-DM/DiffusionPen-scale LDMs; A100 shortens iteration. This is a rented-hours
  workload, not standing infrastructure. The current dev VM (4 CPU cores, no GPU)
  **cannot train**; it can run corpus assembly, gates, composition, and CPU
  inference smoke tests.
- **Inference:** the codex is ~34 folios × ~20 lines × ~8 words ≈ 5–6k word
  generations plus rejection-sampling overhead. Minutes-to-hours on one GPU;
  impractical on CPU for iteration. Batch generation with cached word images
  (same text + same style + same seed → reuse) keeps re-render cost low.
- **Artifacts:** model weights and corpora are large binaries — store outside git
  (HF hub private repo or object storage), referenced by manifest + checksum in
  `shared/models/scribehand/` the same way `dist-public/` pins the CLI tarball.

---

## Part 3 — Alternatives Considered

### 3.1 Continue TD-014 parameter activation (rejected as primary)

Activating tremor/warp/pressure in the corridor controller produces "font +
bounded noise" by construction. It cannot learn join anticipation, allograph
statistics, or ink-load correlation because those are not in the corridor
representation. Keep as fallback path and for structural conditioning (§3.3).

### 3.2 Full-page prompt-based generation (rejected)

Asking a hosted image model to write the page directly gives no verbatim text
control, no stable hand identity across 34 folios, and no ground-truth geometry.

### 3.3 Hybrid: neural texture over procedural render (kept as complement)

An img2img/ControlNet pass conditioned on the TD-014 guided render (structure
preserved, texture learned) would fix ink-edge realism but **not** letterform
rigidity — the conditioning *is* the font-like geometry. Worth keeping as a
low-risk enhancement for the fallback path, not as the primary track.

### 3.4 Trajectory-learning models (rejected)

No online pen-trajectory data exists for medieval hands, and centerline
extraction from ink (TD-008) proved too noisy to serve as trajectory supervision.

---

## Part 4 — Rollout

### Feature flag and fallback

- New approach lands as `scribesim render --approach neural` behind the same
  A/B bench used by TD-014 (`handvalidate` folio regression bench).
- `evo` remains the default until the neural path passes gates §2.7 on the
  proof-folio set; TD-014 guided remains the non-ML fallback.
- Rollback = flip the approach flag; no contracts break (PNG out, folio JSON in).

### Implementation sequence (ARRIVE advances)

1. **ADV-SS-HANDCORPUS-001** — corpus assembly: CATMuS filter + anchor-hand
   freeze + charset normalization + corpus gates.
2. **ADV-SS-SCRIBEHAND-001** — model bring-up: fine-tune One-DM and DiffusionPen,
   word-generation CLI, style anchor freeze, seed policy.
3. **ADV-SS-SCRIBEHAND-002** — HTR fidelity gate: Bastarda HTR fine-tune,
   rejection-sampling loop, per-word provenance.
4. **ADV-SS-SCRIBEHAND-003** — page composition: layout integration, movement
   composition, ink tone pass, word-level PAGE XML, `--approach neural`.
5. **ADV-SS-HANDVALIDATE-007** — promotion gates: style distance, FID, metrics
   suite acceptance bands, A/B bench vs evo/guided, reviewed folio promotion.

Component additions: `handcorpus` (training corpus assembly) and `scribehand`
(model, inference, composition integration), both `incubating`.

### Definition of success

TD-018 succeeds when a reviewed proof-folio set renders with:

- word CER ≤ 0.05 under the Bastarda HTR gate (readable as the intended text),
- style-embedding distance to anchor within the calibrated same-writer band,
- no two same-text words on a folio pixel-identical (anti-font check),
- metrics-suite acceptance bands met against anchor manuscript pages,
- human review preferring the neural folio over the evo baseline,
- Weather consuming the output unmodified.

If the fine-tuned models cannot meet the CER gate after Tier-2 tuning, the track
stops and TD-014 resumes as primary — with the corpus and HTR assets retained,
since they benefit any future attempt.

## License and provenance notes

- CATMuS Medieval: research dataset (per-subset CC licensing; cite ICDAR 2024).
- BSB IIIF images: NoC-NC / CC-BY-NC-SA depending on shelfmark — compatible with
  this project's non-commercial artistic use; provenance JSON (TD-009) already
  records shelfmark and canvas IDs and must be retained for the training corpus.
- One-DM / DiffusionPen: MIT-licensed code; base VAE weights (SD-1.5) under
  CreativeML OpenRAIL-M — permissible for this use.
