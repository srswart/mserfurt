---
advance:
  id: ADV-XL-TESTS-001
  title: Tests — Initial Implementation
  system: xl
  primary_component: tests
  components:
  - tests
  started_at: 2026-03-19T10:00:00Z
  started_by: null
  implementation_completed_at: 2026-03-19T15:27:27.078984Z
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
  - tidy:preparatory
  - tests:unit
  status: in_progress
---

## Objective

Build golden tests for 5 representative folios covering the key manuscript variants — clean text, damaged text, Eckhart passage, Psalter citation, and finis section — plus round-trip validation (ingest -> translate -> folio -> export -> re-ingest produces equivalent structure) and register consistency checks across the full 17-folio output.

## Behavioral Change

After this advance:
- Golden test fixtures exist for 5 folios: 1r (clean homiletic text, high confidence, single register {de}), 4v (damaged, water_damage + ink_fade annotations, reduced line count, confidence < 0.5 on affected lines), 7r (Eckhart *Reden der Unterweisung*, {de} with embedded {la} citations, {verbatim:eckhart} passages), 10r (Psalter citations, {verbatim:psalms} register, Latin text), 14r (finis section, final homily, clean text)
- Round-trip validation confirms that exporting folios to JSON and re-parsing them produces structurally identical `Folio` objects (line counts, language tags, annotation positions all match)
- Register consistency checks verify that no folio contains unresolved {mixed} tags, all {verbatim:*} sections match their reference table entries exactly, and language transitions between adjacent lines are plausible (no German-to-Latin switch mid-sentence)
- All golden tests run in CI without API calls (using cached/mocked translation fixtures)

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/xl-tests-init`
- [ ] Tidy: Create `tests/golden/` directory structure with subdirectories per folio (1r, 4v, 7r, 10r, 14r); create fixture generation script that runs the pipeline once with live API calls and snapshots the output as golden files; create mock translation fixtures for CI
- [ ] Test: Write golden comparison tests — each test loads the golden fixture, runs the pipeline with mocked APIs, and asserts structural equality (line count, language tags, annotation types, confidence ranges); write round-trip test; write register consistency test that scans all 17 folios for violations
- [ ] Implement: Build golden test framework with snapshot comparison (JSON diff for folio files, XML structural diff for PAGE XML); build round-trip validator that re-ingests exported JSON and compares to original `Folio` objects; build register consistency scanner that checks cross-folio language coherence; build CI configuration that runs all tests without API credentials
- [ ] Validate: Run full test suite against a fresh pipeline execution and verify all 5 golden tests pass, round-trip validation passes, and register consistency finds no violations on well-formed input

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- Golden fixtures become stale if upstream components change their output format; the fixture generation script must be re-run after any schema change
- Mocked translation fixtures may not capture edge cases that only appear with live API calls; periodic live-API test runs are needed to catch drift

**Rollback:**
- Revert the `feat/xl-tests-init` branch; tests have no production side effects

## Evidence

