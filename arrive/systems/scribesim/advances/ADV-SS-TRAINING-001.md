---
advance:
  id: ADV-SS-TRAINING-001
  title: Training CLI — Extract-Word, Train, Train-Extend, Train-Folio
  system: scribesim
  primary_component: training
  components:
  - training
  - cli
  - tuning
  started_at: 2026-03-20T22:40:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T18:43:52.550858Z
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
  status: complete
---

## Objective

Implement TD-003-A S3. Add CLI commands for the incremental training workflow: scribesim extract-word (extract training targets from manuscripts), scribesim train (word-level CMA-ES training), scribesim train-extend (incremental extension with quality gates), scribesim train-folio (folio rendering with line checkpoints and revert mechanism).

## Behavioral Change



## Planned Implementation Tasks

- [ ] Implement scribesim extract-word command (crop word images from manuscript folios)
- [ ] Implement scribesim train command (word-level CMA-ES fitting against extracted targets)
- [ ] Implement scribesim train-extend command (incremental vocabulary extension with quality gates)
- [ ] Implement scribesim train-folio command (full folio rendering with line checkpoints)
- [ ] Add revert mechanism for train-folio (per-line quality check, revert to last good checkpoint)
- [ ] Wire CLI commands into existing scribesim CLI entry point
- [ ] Test: extract-word produces valid word images from test folio

## Risk + Rollback

New dependency on training infrastructure. CLI commands are additive — rollback by removing commands from CLI registration.

## Evidence

- [ ] tdd:red-green — write CLI argument parsing tests and mock training tests before implementation
- [ ] tidy:preparatory — extract training workflow interfaces before wiring CLI
- [ ] tests:unit — unit tests for each CLI command's argument handling and core logic
