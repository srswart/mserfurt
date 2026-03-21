---
advance:
  id: ADV-SS-HAND-002
  title: Hand Parameters v2 — Scale-Based Architecture (~45 Parameters)
  system: scribesim
  primary_component: hand
  components:
  - hand
  - cli
  started_at: 2026-03-20T12:50:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T09:04:21.307263Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - breaking_change
  - public_api
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Restructure the hand parameter system from a flat ~20-field `HandParams` dataclass to a hierarchical ~45-parameter architecture organized by scale (folio, line, word, glyph, nib, ink, material) as specified in TD-002 and TD-003. Update the TOML format, add `--set` CLI overrides, and ensure backward compatibility during migration.

## Behavioral Change

After this advance:
- `HandParams` is replaced by `HandProfile` containing nested scale groups: `FolioParams`, `LineParams`, `WordParams`, `GlyphParams`, `NibParams`, `InkParams`, `MaterialParams`
- Each parameter carries metadata: type, range (min/max), default, unit, description, sensitivity — enabling the tuning infrastructure in TD-003
- `shared/hands/konrad_erfurt_1457.toml` is restructured into scale-based `[folio]`, `[line]`, `[word]`, `[glyph]`, `[nib]`, `[ink]`, `[material]` sections with per-parameter range metadata
- Per-folio CLIO-7 modifiers (`[modifiers.f04r]`, etc.) continue to work, applying deltas to the new scale-based structure
- The CLI accepts `--set folio.ruling_slope_variance=0.005` overrides that apply after TOML load + modifier resolution
- The resolver chain is: TOML defaults → per-folio modifiers → CLI `--set` overrides
- All existing tests continue to pass (the v1 TOML format is auto-migrated or both formats are supported during transition)

## Planned Implementation Tasks

- [ ] Tidy: extract parameter metadata schema (range, unit, description, sensitivity) into a reusable pattern
- [ ] Tidy: design the new `HandProfile` dataclass hierarchy — frozen dataclasses per scale, composed into a top-level `HandProfile`
- [ ] Test: write tests for TOML loading with the new format, modifier application, `--set` override parsing, range validation (out-of-range values raise clear errors)
- [ ] Implement: new `HandProfile` with all ~45 parameters from TD-003 Part 1, organized by scale
- [ ] Implement: TOML loader for the new `[folio]`, `[line]`, `[word]`, `[glyph]`, `[nib]`, `[ink]`, `[material]` format
- [ ] Implement: modifier resolver — per-folio overrides applied as deltas to any parameter in any scale group
- [ ] Implement: `--set` CLI override parsing — dotted key paths (`nib.angle_deg=38`) applied after modifier resolution
- [ ] Implement: migrate `shared/hands/konrad_erfurt_1457.toml` to the new format, preserving all existing per-folio modifier semantics
- [ ] Implement: `scribesim hand --show` updated to display parameters grouped by scale with ranges
- [ ] Validate: all existing ScribeSim tests pass; new parameter tests pass; hand --show displays correct resolved values for f01r, f04v, f14r
- [ ] Checkpoint: run `./snapshot.sh hand-002` — renders f01r, f04v, f14r to confirm NO VISUAL REGRESSION (output should look identical to v1; this proves the parameter migration preserved semantics)

## Risk + Rollback

**Risks:**
- Breaking change to the TOML format — existing modifier sections need migration
- ~45 parameters is a large surface area for validation; missing range checks could allow nonsensical values
- Layout and render components depend on `HandParams` — all callsites must be updated to the new `HandProfile` interface

**Rollback:**
- Revert the branch; restore `shared/hands/konrad_erfurt_1457.toml` from git history

## Evidence

- [ ] 38 new tests in `tests/test_hand_profile.py` covering profile construction, to_v1() mapping, TOML loading, modifier resolution, override parsing, range validation, flat dict serialization
- [ ] 171 total tests pass (0 failures)
- [ ] Snapshot `hand-002` is byte-identical to `v1-baseline` (MD5 match on f01r.png)
