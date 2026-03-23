---
advance:
  id: ADV-WX-AICLI-001
  title: AI Weather CLI — weather-map, weather-folio, weather-codex, weather-validate
  system: weather
  primary_component: cli
  components:
  - cli
  - codexmap
  - promptgen
  - worddegrade
  - aiweather
  - aivalidation
  started_at: 2026-03-22T18:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-22T18:02:44.027295Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - public_api
  evidence:
  - tdd:red-green
  - tests:unit
  status: complete
---

## Objective

Extend `weather/cli.py` with four new subcommands wiring the TD-011 AI pipeline to the command line. The existing `apply` and `apply-batch` procedural commands are not modified — the new `weather-map`, `weather-folio`, `weather-codex`, and `weather-validate` commands are additive.

## Behavioral Change

After this advance, the `weather` CLI provides:

**`weather weather-map`**
```
weather weather-map --gathering-size 17 --clio7 output-live/manifest.json \
    --output weather/codex_map.json [--seed 1457]
```
Runs `compute_codex_weathering_map` and writes `codex_map.json`. Prints a summary table of damage per folio.

**`weather weather-folio`**
```
weather weather-folio --folio f04r --clean render-output/f04r.png \
    --map weather/codex_map.json --xml render-output/f04r.xml \
    --folio-json output-live/f04r.json --output-dir weather-output/ \
    [--model openai] [--dry-run]
```
Runs the full single-folio AI weathering pipeline: word damage map → pre-degradation → prompt generation → AI call → provenance. Prints the generated prompt before the API call.

**`weather weather-codex`**
```
weather weather-codex --clean-dir render-output/ --map weather/codex_map.json \
    --folio-json-dir output-live/ --xml-dir render-output/ \
    --output-dir weather-output/ [--model openai] [--dry-run] [--validate]
```
Processes all 34 folios in gathering order. `--validate` runs `validate_folio` after each folio and prints pass/fail status inline. Writes `weather/codex_map.json` progress log updating after each folio completes.

**`weather weather-validate`**
```
weather weather-validate --weathered-dir weather-output/ --clean-dir render-output/ \
    --map weather/codex_map.json --xml-dir render-output/
```
Runs `validate_codex` across all completed folios and writes `weather/validation_report.json`. Prints a pass/fail summary table.

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-aicli`
- [ ] Tidy: no structural changes to existing CLI commands; new commands are appended to `weather/cli.py`
- [ ] Test: `weather weather-map --gathering-size 17 --dry-run` (add dry-run flag that prints without writing): exits 0, output contains f04r and f01r entries
- [ ] Test: `weather weather-folio --folio f04r --dry-run` exits 0, prompt file written, no API call made
- [ ] Test: `weather weather-folio --folio invalid-folio-id` exits non-zero with a clear error message
- [ ] Test: `weather weather-codex --dry-run` exits 0, all 34 provenance stubs written in gathering order
- [ ] Test: `weather weather-validate` on dry_run output: V1 passes (no drift), report JSON written
- [ ] Implement: `weather-map` subcommand
- [ ] Implement: `weather-folio` subcommand
- [ ] Implement: `weather-codex` subcommand (with inline `--validate` option)
- [ ] Implement: `weather-validate` subcommand
- [ ] Validate: end-to-end dry_run — `weather weather-map` → `weather weather-codex --dry-run --validate` → `weather weather-validate`; all three complete without error

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- The `--folio-json-dir` argument requires XL output to be present; if XL hasn't been run, word damage maps will be empty and Addendum A pre-degradation is skipped silently — this should be logged as a warning not a silent skip
- The `weather weather-codex` command may run for a long time on 34 API calls; it must be interruptible (Ctrl-C) and resumable (skip already-completed folios based on provenance JSON existence)

**Rollback:**
- Revert the feat/weather-aicli branch; existing `apply` and `apply-batch` commands are unaffected

## Evidence

