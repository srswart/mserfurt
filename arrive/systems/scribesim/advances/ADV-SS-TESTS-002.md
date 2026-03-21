---
advance:
  id: ADV-SS-TESTS-002
  title: Tests v2 — Physics Hand Model, Metrics, and Tuning Validation
  system: scribesim
  primary_component: tests
  components:
  - tests
  started_at: 2026-03-20T17:30:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T14:51:29.010604Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence:
  - tdd:red-green
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Comprehensive test suite validating the TD-002 physics hand model and TD-003 parameter tuning infrastructure. Covers the new movement model, physics nib, ink-substrate filters, cumulative imprecision, 6-stage pipeline integration, comparison metrics, and parameter optimizer.

## Behavioral Change

After this advance:
- **Movement model tests**: page posture rotation measurable in output; baseline curvature non-zero; word spacing varies; left margin drifts across lines; composition of four scales produces coordinates within expected tolerance
- **Physics nib tests**: horizontal vs vertical strokes at 40° nib produce correct thick/thin ratio; flexibility increases width under pressure; cut_quality controls hairline minimum
- **Ink filter tests**: saturation varies with speed; pooling darkens stroke terminations; wicking produces directional blur; feathering softens hairlines; depletion cycle visible as periodic darkness pattern
- **Imprecision tests**: ruling lines jitter within ±0.2mm; baselines wander around ruling; left margin shows systematic drift; right margin is structured-ragged; inter-line spacing varies
- **Pipeline integration tests**: 6-stage pipeline produces valid output for f01r, f04v, f14r; output contracts maintained (PNG dimensions, PAGE XML schema, pressure heatmap format); determinism (same seed = identical output)
- **Metrics tests**: each M1-M9 metric returns 0.0 for identical images and >0 for different images; composite score is weighted sum; metric thresholds produce correct ratings
- **Tuning tests**: compare command produces formatted output; diff image highlights differences; preset loading chain works; optimizer reduces distance on synthetic target
- **Regression tests**: v2 output for f01r differs from v1 output (movement model produces visible variation); Weather pipeline accepts v2 output without errors

## Planned Implementation Tasks

- [ ] Test: movement model unit tests — each scale independently, composition, determinism
- [ ] Test: physics nib unit tests — direction-dependent width, flexibility, cut_quality, attack/release
- [ ] Test: ink filter unit tests — each of 5 filters independently, filter chain composition
- [ ] Test: imprecision unit tests — ruling, baseline, margin, spacing variation within tolerances
- [ ] Test: 6-stage pipeline integration — end-to-end render of f01r, contract validation
- [ ] Test: metric suite unit tests — each M1-M9 independently, composite score
- [ ] Test: tuning CLI tests — compare, diff, report, preview, preset loading
- [ ] Test: optimizer integration test — synthetic fitting converges
- [ ] Test: regression — v2 output differs from v1; Weather accepts v2 output
- [ ] Validate: full test suite passes; CI completes within time budget

## Risk + Rollback

**Risks:**
- Test fixtures for the new pipeline are larger (400 DPI internal buffers) — may need reduced-resolution test fixtures
- Metric tests require carefully constructed synthetic image pairs with known properties

**Rollback:**
- Revert the branch; v1 tests remain functional.

## Evidence

- [ ] 339 total tests pass across 14 test files (0 failures)
- [ ] v2 component tests: movement (26), physics nib (21), ink filters (16), imprecision (14), pipeline (11), metrics (25), tuning (15), optimizer (21), hand profile (38)
- [ ] v2 integration tests: 19 (full pipeline, weather compat, regression, coverage audit)
- [ ] Weather compatibility confirmed: composite_folio accepts v2 render without errors
- [ ] v2 regression confirmed: output differs from v1 (movement model active)
