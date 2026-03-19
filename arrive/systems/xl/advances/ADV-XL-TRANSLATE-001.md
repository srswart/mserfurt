---
advance:
  id: ADV-XL-TRANSLATE-001
  title: Translate — Initial Implementation
  system: xl
  primary_component: translate
  components:
  - translate
  started_at: 2026-03-19T00:00:00Z
  started_by: null
  implementation_completed_at: 2026-03-19T06:41:21.282302Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  - public_api
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Reverse-translate the English editorial text of the MS Erfurt manuscript back into period-appropriate German and Latin, using Claude API (temperature 0.0) as the primary translation engine, GPT-4 as a validation reviewer, and a verbatim reference table for known liturgical and philosophical texts (Augustine quotations, Psalm citations, Eckhart passages). The output must be plausible 14th-century Thuringian German and scholastic Latin, not modern equivalents.

## Behavioral Change

After this advance:
- Each `Section` from ingest is translated into period German ({de}), scholastic Latin ({la}), or left as-is ({keep}), respecting the register hints attached by ingest
- Verbatim passages (Augustine's *Confessiones*, Psalm citations, Eckhart's *Reden der Unterweisung*) are inserted directly from the reference table rather than machine-translated, preserving exact critical-edition wording
- Claude API calls use temperature 0.0 for deterministic output; each translated section is cross-checked by a GPT-4 validation pass that flags anachronisms, modern idioms, or register violations
- Mixed-register sections ({mixed}) are split at clause boundaries and each clause is translated according to its clause-level language tag

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/xl-translate-init`
- [ ] Tidy: Build the verbatim reference table mapping known text identifiers ({verbatim:augustine}, {verbatim:psalms}, {verbatim:eckhart}) to their critical-edition source texts; define `TranslatedSection` data class with fields for original text, translated text, language, translation_method (api/verbatim/kept), and confidence score
- [ ] Test: Write tests for each translation path — pure German section produces MHG-plausible output, pure Latin section produces scholastic Latin, verbatim Augustine passage matches reference table exactly, {keep} section passes through unchanged, {mixed} section splits correctly at clause boundary; mock Claude and GPT-4 API calls in tests
- [ ] Implement: Build translation dispatcher that routes sections by register hint; implement Claude API client with system prompt specifying 14th-century Thuringian German and scholastic Latin conventions; implement GPT-4 validation reviewer that returns pass/flag/fail per section; implement verbatim lookup from reference table; implement {mixed} clause splitter that identifies Latin/German clause boundaries using punctuation and transitional markers
- [ ] Validate: Run translate on the Eckhart section (folio 7r) with live API calls and verify the output contains recognizable Middle High German; run on a Psalm citation and verify verbatim match

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- Claude API may produce anachronistic German (e.g., modern Hochdeutsch instead of MHG); the GPT-4 validation pass must catch these, but both models have limited MHG training data
- Verbatim reference table must use critical-edition texts, not modernized versions; wrong source editions would propagate through the entire pipeline
- API rate limits and costs scale with manuscript length; the full 17-folio manuscript may require batching

**Rollback:**
- Revert the `feat/xl-translate-init` branch; no persisted translations outside the output directory

## Evidence

