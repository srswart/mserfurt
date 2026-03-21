---
advance:
  id: ADV-SS-TUNING-001
  title: Parameter Tuning CLI — Compare, Diff, Report, Presets
  system: scribesim
  primary_component: tuning
  components:
  - tuning
  - cli
  - metrics
  started_at: 2026-03-20T16:10:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T12:45:06.923720Z
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
  status: complete
---

## Objective

Implement the manual tuning workflow from TD-003 Part 3 and Part 5: CLI commands for comparing rendered output against real manuscript samples, producing visual diff reports, and managing parameter presets.

## Behavioral Change

After this advance:
- `scribesim compare <rendered.png> --target <real.png> --metrics all` runs the full metric suite and prints a scored report (M1-M9 + composite distance)
- `scribesim diff <v1.png> <v2.png> -o diff.png` produces a visual difference image highlighting where two renders diverge
- `scribesim report <rendered.png> --target <real.png> -o comparison.html` produces an HTML report with side-by-side images, per-metric scores with color indicators, histogram overlays, and heatmaps of spatial differences
- `scribesim preview <folio.json> --set nib.angle_deg=38` renders a quick preview at reduced DPI (150) for rapid iteration
- `scribesim render <folio.json> --preset bastarda_formal` loads a named parameter preset from `shared/hands/presets/`
- Presets are TOML files in `shared/hands/presets/` — named profiles representing different hand states (formal, hasty, fatigued)
- The `--set` override flag works with `render`, `preview`, and `compare` subcommands

## Planned Implementation Tasks

- [ ] Tidy: define preset file format and directory structure (`shared/hands/presets/*.toml`)
- [ ] Test: write tests for compare output format, diff image generation, preset loading, --set override chain
- [ ] Implement: `scribesim compare` subcommand — loads two images, runs MetricSuite, formats output
- [ ] Implement: `scribesim diff` subcommand — pixel-level difference with colormap visualization
- [ ] Implement: `scribesim report` subcommand — HTML report generator with embedded images and metric visualizations
- [ ] Implement: `scribesim preview` subcommand — reduced-DPI render for rapid iteration
- [ ] Implement: `--preset` flag — loads named TOML preset as base profile, then applies `--set` overrides on top
- [ ] Implement: create initial presets: `bastarda_formal.toml` (careful, slow), `bastarda_hasty.toml` (fast, more variation), `bastarda_fatigued.toml` (tremor, drift)
- [ ] Validate: run full comparison workflow against a real manuscript sample; verify HTML report renders correctly; test preset → override → render chain

## Risk + Rollback

**Risks:**
- HTML report generation adds complexity; may need a templating library (jinja2) as a new dependency
- Preview mode at 150 DPI may miss artifacts only visible at 300 DPI — should warn the user

**Rollback:**
- Revert the branch; tuning CLI is additive, existing subcommands are unchanged.

## Evidence

- [ ] 15 tests in `tests/test_tuning.py` covering compare, diff, report, and preset loading
- [ ] 299 total ScribeSim tests pass (0 failures)
- [ ] CLI demo: compare/diff/report all functional against historical samples
- [ ] HTML report and diff PNG copied to ~/Desktop/scribesim/ for review
