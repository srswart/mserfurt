# XL ("xl") — Project Brief

## Purpose
Build **XL**: a reverse-translation and folio-structuring engine that takes the English text of *MS Erfurt Aug. 12°47* — a fictional medieval manuscript written collaboratively — and produces translations into **period German** (mid-fifteenth-century Frühneuhochdeutsch) and **Ecclesiastical Latin**, structured into the seventeen-folio gathering described in the manuscript's own fiction. XL is the first stage of a three-part pipeline (XL → ScribeSim → Weather) whose goal is to produce the physical artifact that the fictional CLIO-7 system claims to have translated from: the actual manuscript of Brother Konrad's confession, as it would have existed in 1457.

**Phase 1 outcome:** a CLI tool named `xl` that ingests the English manuscript text (excluding CLIO-7 editorial apparatus), produces a folio-structured corpus in period German with embedded Latin passages, and emits output consumable by the ScribeSim phase.

## Why this exists
The manuscript *MS Erfurt Aug. 12°47* exists as a fictional English translation of a document that never was. The CLIO-7 apparatus describes a specific physical object: seventeen folios, bound between a Breviarium and a Lectionary, written in a hybrid register of vernacular German and Ecclesiastical Latin, with water damage to folios 4r–5v, a missing corner on 4v, and pressure variations consistent with emotional intensity. XL reverse-engineers the textual layer of that object by:
- translating Brother Konrad's voice back into the language he would have written in — the educated clerical German of mid-fifteenth-century Erfurt, with Latin phrases embedded mid-sentence as the CLIO-7 preface describes
- preserving the hybrid register: theological reflection and direct address to God tend toward Latin; personal narrative and material description tend toward German; the boundaries are fluid, as the preface notes
- structuring the text into seventeen folios with recto/verso designation, respecting the folio references already embedded in the fiction (4r–5v damaged, 6r resumes, 7r–7v the Eckhart confession, 14r the final section)
- marking the passages that CLIO-7 flags as damaged, lacunose, or reconstructed, so that ScribeSim and Weather can render those folios appropriately
- producing ground truth data suitable for HTR model training in eScriptorium/Kraken

## Source material
The input is the English text of *MS Erfurt Aug. 12°47* as written collaboratively (S.R. Swart, 2025). The following sections constitute the manuscript text proper and are in scope for translation:
- The opening declaration ("Here begins what a scribe could not keep from writing…")
- The meditation on the press (die neue Kunst)
- The Peter narrative (folio 4r–5v, with CLIO-7 damage markings)
- The workshop visits and Demetrios dialogue
- The Eckhart confession (folio 7r–7v)
- The Psalter meditation and Becker visit
- The final gathering (folio 14r to finis)

The following are **out of scope** — they are CLIO-7's fictional editorial voice, not Konrad's:
- Title page and translator's preface
- All CLIO-7 editorial notes, confidence markings, and reconstruction annotations
- The closing note

However, CLIO-7's annotations are **metadata inputs**: they describe damage patterns, folio boundaries, hand characteristics, and textual confidence levels that XL must preserve as structured metadata for downstream phases.

## Phase 1 scope (MVP)
### CLI deliverable
A `xl` executable (Python, with optional Rust acceleration) with:
- `xl translate <input.md> -o <output_dir>` — translate full manuscript into folio-structured corpus
- `xl translate --folio <folio_id> -o <o>` — translate/regenerate a single folio
- `xl manifest <output_dir>` — emit JSON folio manifest with structural metadata
- `xl validate <output_dir>` — check structural integrity of translated corpus
- `xl preview <folio_id>` — display a single folio's German/Latin text with annotations
- `xl --version`, `xl --help`

### Translation scope
**Required**
- **Hybrid register translation:** Brother Konrad writes in German with Latin embedded. XL must produce text in this hybrid register, not pure German or pure Latin. The register shifts are contextually driven:
  - Direct address to God → tends Latin (*fecisti nos ad te*, *inquietum est cor nostrum*)
  - Theological reflection → mixed, heavier Latin
  - Personal narrative → predominantly German with occasional Latin terms of art
  - Material description (the workshop, the eggs, the light) → almost entirely German
  - Quotation of scripture or Eckhart → Latin, as Konrad would have known them
- **Period-accurate German:** Frühneuhochdeutsch of the mid-fifteenth century, Thuringian dialect features where appropriate (Erfurt is in Thuringia). Not Middle High German (too early) and not Early New High German in its later, more standardized form.
- **Ecclesiastical Latin:** standard clerical Latin of the period, not classical Ciceronian. Konrad is an educated scribe, not a humanist — his Latin is functional and devotional.
- **Folio structuring:** distribute the translated text across seventeen folios (recto/verso = up to 34 pages), respecting:
  - The folio references in the CLIO-7 apparatus (4r–5v, 6r, 7r, 7v, 14r)
  - Text density consistent with a professional scriptorium hand (~28–35 lines per page)
  - The CLIO-7 note that 1–3 folios may be missing between 5v and 6r
  - The final section (14r onward) uses different vellum stock, smaller and unevenly cut

**Annotation layer**
Each folio record carries structured annotations derived from CLIO-7's apparatus:
- `damage`: type (water, missing corner, moisture), extent, affected lines — from CLIO-7 damage descriptions
- `lacuna`: location and extent of text marked [—] in the English, with CLIO-7 confidence levels
- `confidence`: per-line confidence scores (passages below 80% → italic in English, mapped to "reconstructed" annotation; below 60% → bold italic, mapped to "speculative" annotation)
- `hand_notes`: CLIO-7 observations about pressure, spacing, ink density, writing speed — these become rendering instructions for ScribeSim
- `section_break`: the ✦ ✦ ✦ dividers in the English text, preserved as structural markers
- `register`: per-line language tag (German, Latin, or mixed) for ScribeSim script selection

**Output format**
- Primary: JSON-per-folio (one file per folio, named by folio ID: `f01r.json` through `f17v.json`)
- Consolidated: single JSONL for bulk processing
- Manifest: JSON mapping folio IDs to metadata (line count, text density, damage type, hand notes, register distribution)
- PAGE XML: one file per folio, for eScriptorium import as transcription ground truth

### Integration with eScriptorium
- PAGE XML output importable as transcription layers
- Folio IDs align with eScriptorium document/page numbering
- Latin and German text layers can be represented as separate transcription versions in eScriptorium

### Developer experience (Phase 1)
- Deterministic output for the same input text
- Folio preview mode for rapid review of translation quality
- Validation report as structured JSON

## Non-goals (Phase 1)
- Image processing or rendering (ScribeSim's domain)
- Physical damage simulation (Weather's domain)
- Interactive translation editing UI
- Full diplomatic transcription apparatus
- Multi-witness collation (there is only one "witness" — we are creating it)
- Translation of CLIO-7 editorial apparatus

## Design principles (project constraints)
- **Register fidelity:** the hybrid German-Latin register is the manuscript's most distinctive feature. XL must reproduce it convincingly, not default to pure German or pure Latin.
- **Folio-first structure:** the folio is the atomic unit. Every operation respects the seventeen-folio gathering.
- **Fiction-consistent:** every structural decision must be defensible against the CLIO-7 apparatus. If CLIO-7 says folio 4v has a missing corner, the folio record must encode that.
- **Annotation over lossy transformation:** CLIO-7's damage and confidence metadata is never discarded — it becomes structured annotations for downstream phases.
- **Reproducibility:** same input always produces identical output.

## ARRIVE governance plan
We run XL development with outcome-first discipline:
- work as a sequence of small, reviewable Advances
- keep changes within the reviewability budget
- follow **Tidy First → Test First → Implement** as default execution order

### XL system + components (initial)
System: `xl`

Components (all **incubating** initially):
- `cli` — command-line driver, argument parsing, orchestration
- `ingest` — English manuscript parsing, CLIO-7 apparatus extraction, section segmentation
- `translate` — reverse-translation engine (LLM-assisted with period-linguistic constraints)
- `register` — hybrid register engine: determines German/Latin distribution per passage
- `folio` — folio structuring: text distribution across seventeen folios, line counting, density balancing
- `annotate` — damage, lacuna, confidence, and hand-note annotation from CLIO-7 apparatus
- `export` — JSON, JSONL, PAGE XML writers, manifest generation
- `tests` — golden tests for representative folios, round-trip validation, register consistency checks
- `docs` — source material guide, output format spec, period-linguistic reference

## Phase plan
### Phase 1 — "Konrad's voice in Konrad's language"
Deliver the minimal end-to-end pipeline:
1. Parse English manuscript text, separating Konrad's voice from CLIO-7 apparatus
2. Determine hybrid register distribution (German/Latin) per passage
3. Translate into period German with embedded Ecclesiastical Latin
4. Structure into seventeen folios with recto/verso designation
5. Extract and attach CLIO-7 damage/confidence/hand annotations
6. Export as per-folio JSON + PAGE XML
7. Provide golden tests for at least 5 representative folios: clean text (opening), damaged (4r–5v), the Eckhart confession (7r), the Psalter meditation, and the final folio (finis)

### Phase 2 (preview)
- Interactive register tuning (adjust German/Latin balance per passage)
- Period vocabulary verification against Frühneuhochdeutsch corpora
- Diplomatic transcription mode (abbreviation-compressed forms for ScribeSim)

### Phase 3 (preview)
- Full diplomatic apparatus generation
- Variant apparatus for the Eckhart *wirt*/*ist*/*enpfêhet* crux

## Definition of Done (Phase 1)
- `xl translate ms-erfurt.md -o out/` produces seventeen folio JSON files
- `xl manifest out/` produces valid manifest JSON with correct folio count, damage annotations, and register distribution
- `xl validate out/` passes with zero errors
- Folio 7r contains the Eckhart confession with the *wirt* crux in period German
- Folio 4r–5v carries damage and lacuna annotations matching CLIO-7's description
- Latin quotations (Augustine, Psalms, Eckhart) appear in Latin, not German
- Output imports cleanly into eScriptorium as transcription layer
- Automated tests cover: section parsing, register classification, folio structuring, annotation extraction, PAGE XML export
- Repo includes period-linguistic reference notes and register decision log

## Key risks + mitigations
- **Period German accuracy:** Frühneuhochdeutsch is not a standardized language; use LLM-assisted translation with post-editing guided by reference corpora (Erfurt municipal records, Thuringian devotional texts of the period). Accept that perfection is impossible — the goal is "convincing to a non-specialist, defensible to a specialist."
- **Register boundary decisions:** where German ends and Latin begins is a judgment call. Document the heuristics explicitly; allow per-passage override.
- **Folio distribution:** fitting the text into exactly seventeen folios at plausible text density requires careful balancing. If the text is too long or too short, adjust line density within the historical range (28–35 lines/page) rather than adding or removing folios.
- **eScriptorium format drift:** pin to PAGE XML schema 2019; validate against eScriptorium import.

## Success metrics (Phase 1)
- Can translate and structure the full manuscript in ≤ 5 minutes on commodity hardware
- Golden test suite catches regressions in folio structuring, register classification, and annotation extraction
- At least one reader with German proficiency confirms the hybrid register reads naturally (informal qualitative check)
- Latin passages (Augustine, Psalms, Eckhart) are recognizable as their known textual forms
- Output imports into eScriptorium without manual fixup
