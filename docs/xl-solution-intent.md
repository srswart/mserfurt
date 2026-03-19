# Solution Intent — XL (Phase 1)

This document captures **how we intend to solve** Phase 1 (architecture + constraints). It is not a task plan and not an outcome record.

## Phase 1 intent
Produce an `xl` tool that takes the English text of *MS Erfurt Aug. 12°47*, reverse-translates it into the hybrid German-Latin register described by the CLIO-7 apparatus, structures it into seventeen folios, and emits per-folio records with damage/confidence/hand annotations consumable by ScribeSim and eScriptorium.

## Core decisions
### Implementation language (Stage 0)
- **Python** for the primary pipeline (ingestion, register classification, translation orchestration, folio structuring, export).
- **Rust** (via PyO3/maturin) for text processing where throughput matters: folio line-count balancing, abbreviation compression (Phase 2), and bulk validation.
- The Rust boundary is a single `xl_core` extension module.

### Translation strategy
Two LLM providers are available for translation, used in a **primary + validation** arrangement:

**Primary translator: Claude (Anthropic API)**
- Claude handles the core translation work: period German prose, Latin theological passages, and the fluid register-switching that defines Konrad's voice.
- System prompt encodes period-linguistic norms: Frühneuhochdeutsch orthographic conventions, Thuringian dialect markers, Ecclesiastical Latin register for devotional/theological passages.
- Each passage is sent with its register hint (`{de}`, `{la}`, `{mixed}`) pre-assigned in the source file. Claude translates within that constraint.
- For `{mixed}` passages, the prompt instructs Claude to determine clause-level switching: theological abstractions and direct address to God lean Latin, concrete/material/emotional content stays German, and transitions should feel organic rather than mechanical.
- Temperature fixed at 0.0 for reproducibility.

**Validation pass: GPT-4 (OpenAI API)**
- GPT-4 serves as an independent cross-check, not a co-translator.
- After Claude produces the primary translation, GPT-4 receives the English source + Claude's German/Latin output and is asked to flag: anachronistic vocabulary (words not attested before ~1460), register inconsistencies (Latin where German is more natural or vice versa), grammatical forms that belong to the wrong century (MHG forms in what should be FNHD, or ENHG forms that are too late), and Latin that reads more humanist than clerical.
- GPT-4 does **not** produce an alternative translation. It produces a structured review (JSON) with flagged lines and suggested corrections.
- Flagged lines are re-sent to Claude with the GPT-4 feedback for revision.

**Verbatim insertions (no LLM involved)**
- Passages tagged `{verbatim:la}` or `{verbatim:mhg}` are inserted directly from a curated reference table. These are known textual forms (Augustine's *Confessions*, Psalm 42, Eckhart's German sermons, the bull *In agro dominico*). No LLM touches them.
- The reference table is version-controlled and citable.

**Fallback: pre-translated golden corpus**
- For environments without API access, supply the seventeen folios as static JSON (produced once, then frozen). ScribeSim can consume the golden corpus directly.

Rationale:
- Claude excels at the nuanced register-switching and period voice — the fluid way German and Latin intermix mid-sentence is exactly the kind of contextual judgment LLMs handle well.
- GPT-4 as validator rather than co-translator avoids "committee prose" while catching anachronisms and register drift that a single model might not self-correct.
- Verbatim insertion for known texts prevents hallucinated variants and grounds the manuscript in real textual tradition.
- The golden corpus fallback ensures the pipeline works offline and provides a stable reference for testing.

### Source file format
The input is the annotated source file (`ms-erfurt-source.md`) which contains:
- Konrad's text only (CLIO-7 apparatus removed)
- Register hints inline: `{de}`, `{la}`, `{mixed}`, `{verbatim:la}`, `{verbatim:mhg}`, `{keep}`
- Structural markers: `[folio:XXr]`, `[section]`, `[lacuna:N]`, `[damage:type]`, `[hand:description]`
- HTML comments preserving CLIO-7 metadata as structured annotations

The register hints are **advisory, not absolute**. Claude may adjust within a passage if the text demands it (e.g., a `{de}` passage that contains a brief Latin phrase of address). The hints prevent wholesale register drift, not clause-level organic switching.

### Register classification
Since the source file (`ms-erfurt-source.md`) is **pre-annotated with register hints**, the register engine's role in Phase 1 is primarily validation and edge-case handling rather than classification from scratch:

1. **Parse register hints** from the source file (`{de}`, `{la}`, `{mixed}`, `{verbatim:*}`, `{keep}`)
2. **Validate consistency**: flag passages where the hint seems wrong (e.g., a `{de}` passage that is entirely theological abstraction — might warrant `{mixed}`)
3. **Resolve `{mixed}`** to clause-level tags: for `{mixed}` passages, the register engine produces a finer-grained annotation that Claude uses as guidance (not hard constraint)
4. **Handle `{keep}`**: phrases like *die neue Kunst* are kept in their original form regardless of surrounding register

The pre-annotation reflects these heuristics (already applied in the source file):

| Passage type | Primary register | Notes |
|---|---|---|
| Direct address to God ("You who…") | Latin | Augustinian confessional convention |
| Theological reflection (Eckhart, grace, the soul) | Mixed, Latin-heavy | Latin for technical terms, German for Konrad's own reasoning |
| Scripture quotation (Psalms, Augustine) | Latin verbatim | Inserted from known texts, not translated |
| Eckhart quotation (German sermons) | MHG verbatim | Eckhart's *German* sermons are in Middle High German |
| Personal narrative (Peter, the workshop, the eggs) | German | Konrad's lived experience is in his vernacular |
| Material description (light, vellum, the desk) | German | Concrete, sensory language stays vernacular |
| Dialogue (Demetrios, Becker) | German | Conversations happen in the shared vernacular |
| Demetrios speaking Latin | Latin | Demetrios is noted as speaking Latin in the workshop scene |
| The *wirt* crux | MHG/Latin | The Eckhart variant is in Middle High German; Konrad's analysis moves between German and Latin |

The register engine validates these assignments and resolves `{mixed}` passages to clause-level language tags. Future phases may support automatic register classification for unannotated input.

## Data model (Phase 1)
### Folio record
```
Folio {
  id:              String          // e.g. "f04r", "f07v"
  recto_verso:     "recto" | "verso"
  gathering_position: Int          // 1–17
  lines: [
    Line {
      number:       Int
      text:         String          // period German/Latin as written
      register:     "de" | "la" | "mixed"
      annotations:  [Annotation]
    }
  ]
  damage:          Option<Damage>
  hand_notes:      Option<HandNotes>
  section_breaks:  [Int]           // line numbers where ✦ ✦ ✦ occurs
  vellum_stock:    "standard" | "irregular"  // f14r onward is irregular
  metadata: {
    text_density:   Float           // chars per line, average
    line_count:     Int
    register_ratio: { de: Float, la: Float, mixed: Float }
  }
}
```

### Damage model (from CLIO-7 apparatus)
```
Damage {
  type:            "water" | "missing_corner" | "moisture" | "age"
  affected_lines:  [Range]
  extent:          "partial" | "severe" | "total"
  corner:          Option<"top_left" | "top_right" | "bottom_left" | "bottom_right">
  notes:           String           // CLIO-7's description
}
```

### Hand notes (from CLIO-7 apparatus)
```
HandNotes {
  pressure:        "normal" | "increased_lateral" | "lighter" | "variable"
  spacing:         "standard" | "wider" | "compressed"
  ink_density:     "consistent" | "variable_multi_sitting" | "fresh"
  speed:           "deliberate" | "rapid" | "compensating"
  notes:           String           // CLIO-7's description
}
```

### Confidence model
```
Confidence {
  level:           Float            // 0.0–1.0
  category:        "clear" | "reconstructed" | "speculative"
  original_markup: String           // how CLIO-7 rendered it (italic, bold italic, [—])
}
```

## Pipeline stages (Phase 1)
### 1. Ingest
- Parse the English manuscript text (Markdown/PDF input)
- Separate Konrad's text from CLIO-7 editorial apparatus using structural markers (the editorial notes are clearly delineated with distinct formatting)
- Segment Konrad's text into passages by section breaks (✦ ✦ ✦) and natural paragraph boundaries
- Extract CLIO-7 metadata: damage descriptions, confidence markings, hand notes, folio references

### 2. Register classification
- For each passage: assign primary register (German, Latin, mixed)
- For known quotations: tag as verbatim-insert with source reference
- For dialogue: tag speakers and their register (Demetrios sometimes speaks Latin)
- Output: annotated passage list with register tags

### 3. Translate (Claude primary, GPT-4 validation)
- For each passage, by register hint:
  - `{de}` → send to Claude with FNHD translation prompt
  - `{la}` → send to Claude with Ecclesiastical Latin prompt
  - `{mixed}` → send to Claude with register-switching prompt + clause-level guidance from register engine
  - `{verbatim:*}` → insert from reference table (no API call)
  - `{keep}` → preserve original phrase, translate surrounding context
- One Claude API call per passage (batch with rate limiting; ~100 passages total)
- After primary pass: send all Claude output to GPT-4 for validation review
- GPT-4 returns structured JSON: `{ flagged_lines: [{ line_id, issue_type, suggestion }] }`
- Re-send flagged lines to Claude with GPT-4 feedback for revision (typically ≤ 15% of lines)
- Validation: translated text length within 0.7–1.4× English length

### 4. Folio structuring
- Distribute translated passages across seventeen folios
- Respect hard constraints from CLIO-7 apparatus:
  - Folios 4r–5v: Peter narrative, water damage
  - Folio 4v: missing bottom-right corner
  - Folio 6r: resumes after possible 1–3 missing folios (the workshop visits)
  - Folio 7r: Eckhart confession begins, written across multiple sittings
  - Folio 7v lower half: return to Psalter, smaller hand
  - Folio 14r: final section, different vellum stock
- Target density: 28–35 lines per page (adjustable)
- Balance text across pages to avoid orphan lines or extreme density variation
- The Knuth-Plass-like line-breaking algorithm from ScribeSim will do final line fitting; XL assigns text to folios at the passage level

### 5. Annotate
- Attach damage annotations from CLIO-7 apparatus to affected folios
- Map CLIO-7 confidence markings to per-line confidence scores
- Map CLIO-7 hand notes to per-folio hand descriptions
- For lacunae ([—] in English): generate plausible lacuna extent in the German/Latin (character count estimate)

### 6. Export
- Per-folio JSON (primary output)
- Consolidated JSONL (for ScribeSim batch processing)
- PAGE XML (for eScriptorium: each folio → one PAGE XML page, German/Latin text as primary transcription layer, English as secondary)
- Manifest JSON (folio index with all metadata)

## Known textual insertions (verbatim, not translated)
These passages appear in Konrad's text as quotations and must be inserted in their known forms:

| Source | Text | Language | Folio (approx.) |
|---|---|---|---|
| Augustine, *Confessions* I.1 | *fecisti nos ad te, et inquietum est cor nostrum donec requiescat in te* | Latin | Workshop section |
| Augustine (truncated) | *fecisti nos ad te* | Latin | Workshop section |
| Psalm 42:1 | *Quemadmodum desiderat cervus ad fontes aquarum* | Latin | Psalter meditation |
| Psalm 42:2 | *Sic desiderat anima mea ad te, Deus* | Latin | Psalter meditation |
| Eckhart, Sermon 12 (original) | *In sînem grunde: diu sêle ist daz wort* | MHG | Eckhart confession |
| Eckhart (Konrad's reading) | *In sînem grunde: diu sêle wirt daz wort* | MHG (modified) | Eckhart confession |
| Bull *In agro dominico* (reference) | Referenced, not quoted | Latin | Eckhart confession |

## Folio map (preliminary)
Based on the CLIO-7 apparatus and section structure:

| Folio | Content | Damage | Hand notes |
|---|---|---|---|
| f01r–f03v | Opening declaration, meditation on the press | None noted | Standard scriptorium hand |
| f04r–f05v | Peter narrative | Water damage from above; f04v missing bottom-right corner | — |
| [gap: 1–3 folios missing] | Lost or removed | — | — |
| f06r–f06v | Workshop visits (first and second) | None | Increased lateral pressure on downstrokes |
| f07r–f07v (upper) | Eckhart confession | None, "wanted this one legible" | Multiple sittings (variable ink density) |
| f07v (lower) | Psalter return | None | Smaller, more economical hand |
| f08r–f13v | Demetrios dialogue, Psalter meditation, Becker visit | None noted | Standard |
| f14r–f17v | Final gathering: Psalter finished, Ulrich letter, workshop return, finis | None, but different vellum stock | Slower, wider spacing, compensating |

Note: exact folio assignments will be determined during the structuring phase based on text volume and target density.

## Testing strategy (Phase 1)
- **Ingest tests:** English manuscript → correctly separated Konrad text vs. CLIO-7 apparatus
- **Register tests:** known passages (Augustine quotes, workshop dialogue, Eckhart reflection) → correct register tags
- **Verbatim insertion tests:** Latin/MHG quotations appear exactly as specified, not translated
- **Folio structure tests:** seventeen folios, all CLIO-7 folio references land on correct folios
- **Damage annotation tests:** folios 4r–5v carry water damage, f04v has missing corner
- **Round-trip conceptual test:** XL output → inspect English back-translation → meaning preserved
- **Integration test:** PAGE XML imports into eScriptorium without error

Development discipline:
- default commit sequence: tidy → test → implement

## Repository layout (suggested)
- `xl/` (Python package)
  - `cli.py` — entry point
  - `ingest/` — manuscript parsing, CLIO-7 extraction
  - `register/` — hybrid register classification
  - `translate/` — LLM orchestration, period-linguistic constraints
  - `folio/` — folio structuring, density balancing
  - `annotate/` — damage, confidence, hand-note attachment
  - `export/` — JSON, JSONL, PAGE XML, manifest writers
  - `models/` — data classes (Folio, Line, Damage, HandNotes, etc.)
  - `verbatim/` — known textual insertions (Augustine, Psalms, Eckhart)
- `xl-core/` (Rust crate, PyO3)
  - `src/folio_balance.rs` — line-count balancing
  - `src/validate.rs` — structural validation
- `source/` (input manuscript)
  - `ms-erfurt.md` — English text of MS Erfurt Aug. 12°47
- `golden/` (pre-translated golden corpus)
  - `f01r.json` through `f17v.json`
- `reference/` (period-linguistic resources)
  - `fnhd-orthography.md` — Frühneuhochdeutsch conventions
  - `thuringian-markers.md` — dialect features
  - `register-decisions.md` — German/Latin boundary heuristics
- `tests/` (fixtures + golden outputs)
- `docs/` (source material guide, output format spec)

## Out of scope (Phase 1)
- Image processing or rendering (ScribeSim's domain)
- Physical damage simulation (Weather's domain)
- Interactive translation editing UI
- Abbreviation compression (Phase 2 — scribes abbreviated heavily; XL Phase 1 produces expanded forms)
- Diplomatic transcription conventions (Phase 2)
- Translation of CLIO-7 editorial apparatus
