# /arrive-phase — Pipeline-Aware ARRIVE Governance

Streamlines ARRIVE governance for the MS Erfurt three-phase pipeline (XL → ScribeSim → Weather).

## Usage

`/arrive-phase <subcommand> [args]`

### Subcommands

- `bootstrap` — Generate advances for all systems and components, plus the implementation plan
- `advance <system>` — Draft a single advance for one system (xl, scribesim, weather)
- `validate` — Check cross-phase contract alignment
- `plan` — Generate or update the implementation plan
- `cfu <ADV-ID>` — Generate pipeline-aware Check for Understanding questions

---

## Subcommand: `bootstrap`

Generate the full set of initial advances and the implementation plan in one pass.

### Instructions

1. **Read all three system files** to get pipeline context:
   - `arrive/systems/xl/system.yaml`
   - `arrive/systems/scribesim/system.yaml`
   - `arrive/systems/weather/system.yaml`

2. **Read the interface contracts** for cross-system requirements:
   - `docs/tech-direction/TD-001-interface-contracts.md`

3. **Read the project briefs and solution intents** for each system:
   - `docs/xl-project-brief.md`, `docs/xl-solution-intent.md`
   - `docs/scribesim-project-brief.md`, `docs/scribesim-solution-intent.md`
   - `docs/weather-project-brief.md`, `docs/weather-solution-intent.md`

4. **Create advance directories** if they don't exist:
   - `arrive/systems/xl/advances/`
   - `arrive/systems/scribesim/advances/`
   - `arrive/systems/weather/advances/`

5. **Generate one advance per component** in each system using the template below. The advance should reflect:
   - The component's role within its system (from system.yaml)
   - Pipeline position and dependencies (from pipeline: block)
   - Relevant interface contracts (from TD-001)
   - Implementation approach (from solution intent docs)
   - Risks specific to this component's pipeline position

6. **Generate the implementation plan** at `arrive/implementation-plan.yaml` that sequences work across all three phases, respecting pipeline dependencies.

7. **Validate cross-phase contracts** — check that every output declared in one system's `pipeline.outputs` has a corresponding input in the consuming system's `pipeline.inputs`.

### Advance Template

Each advance file goes at: `arrive/systems/<system>/advances/ADV-<COMPONENT>-001.md`

Use this structure:

```markdown
---
advance_id: ADV-<COMPONENT>-001
system_id: <system>
title: "<Component> — Initial Implementation"
status: planned
started_at: ~
implementation_completed_at: ~
review_time_estimate_minutes: <estimate>
review_time_actual_minutes: ~
components: [<component_id>]
risk_flags: [<applicable flags from registry vocabulary>]
evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
tech_direction: [TD-001]
pipeline_position: <1|2|3>
depends_on_advances: [<ADV-IDs from upstream systems if applicable>]
---

## Objective

<What this component needs to accomplish, grounded in the project brief and solution intent.>

## Behavioral Change

After this advance:
- <Observable outcome 1>
- <Observable outcome 2>
- <Observable outcome 3>

## Pipeline Context

- **Position**: Phase <N> (<system name>)
- **Upstream**: <What this component consumes and from where>
- **Downstream**: <What this component produces and who consumes it>
- **Contracts**: <Which TD-001 sections govern this component's I/O>

## Component Impact

```yaml
components: [<component_id>]
system: <system_id>
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/<system>-<component>-init`
- [ ] Tidy: <preparatory work>
- [ ] Test: <what tests to write first>
- [ ] Implement: <implementation steps>
- [ ] Validate: <how to verify against contracts>

## Risk + Rollback

**Risks:**
- <Risk 1>
- <Risk 2>

**Rollback:**
- <How to revert>

## Evidence

| Type | Status | Notes |
|------|--------|-------|
| tdd:red-green | pending | |
| tidy:preparatory | pending | |
| tests:unit | pending | |

## Changes Made

_No changes yet._

## Check for Understanding

_To be generated after implementation._
```

### Implementation Plan Template

Generate at `arrive/implementation-plan.yaml`:

```yaml
plan_id: ms-erfurt-impl-001
name: "MS Erfurt Pipeline — Implementation Plan"
created_at: <ISO timestamp>
status: active

# Sequencing rationale: XL must produce folio JSON + manifest before
# ScribeSim can render, and ScribeSim must produce images + heatmaps
# before Weather can age them. Within each phase, components can be
# partially parallelized where they don't depend on each other.

phases:
  - phase_id: 1
    name: "XL — Reverse Translation & Folio Structuring"
    system: xl
    status: planned
    depends_on: []
    passes:
      - pass_id: 1a
        name: "Foundation"
        items:
          - advance: ADV-CLI-001
            system: xl
            status: planned
            depends_on: []
          - advance: ADV-INGEST-001
            system: xl
            status: planned
            depends_on: []
      - pass_id: 1b
        name: "Core Pipeline"
        items:
          - advance: ADV-TRANSLATE-001
            system: xl
            status: planned
            depends_on: [ADV-INGEST-001]
          - advance: ADV-REGISTER-001
            system: xl
            status: planned
            depends_on: [ADV-INGEST-001]
          - advance: ADV-FOLIO-001
            system: xl
            status: planned
            depends_on: [ADV-TRANSLATE-001, ADV-REGISTER-001]
      - pass_id: 1c
        name: "Output & Enrichment"
        items:
          - advance: ADV-ANNOTATE-001
            system: xl
            status: planned
            depends_on: [ADV-FOLIO-001]
          - advance: ADV-EXPORT-001
            system: xl
            status: planned
            depends_on: [ADV-FOLIO-001, ADV-ANNOTATE-001]
          - advance: ADV-TESTS-001
            system: xl
            status: planned
            depends_on: [ADV-EXPORT-001]

  - phase_id: 2
    name: "ScribeSim — Scribal Hand Simulation"
    system: scribesim
    status: planned
    depends_on: [1]
    passes:
      - pass_id: 2a
        name: "Foundation"
        items:
          - advance: ADV-CLI-001
            system: scribesim
            status: planned
            depends_on: []
          - advance: ADV-HAND-001
            system: scribesim
            status: planned
            depends_on: []
          - advance: ADV-GLYPHS-001
            system: scribesim
            status: planned
            depends_on: []
      - pass_id: 2b
        name: "Rendering Pipeline"
        items:
          - advance: ADV-LAYOUT-001
            system: scribesim
            status: planned
            depends_on: [ADV-GLYPHS-001, ADV-HAND-001]
          - advance: ADV-RENDER-001
            system: scribesim
            status: planned
            depends_on: [ADV-LAYOUT-001]
      - pass_id: 2c
        name: "Output & Ground Truth"
        items:
          - advance: ADV-GROUNDTRUTH-001
            system: scribesim
            status: planned
            depends_on: [ADV-RENDER-001]
          - advance: ADV-TESTS-001
            system: scribesim
            status: planned
            depends_on: [ADV-RENDER-001, ADV-GROUNDTRUTH-001]

  - phase_id: 3
    name: "Weather — Manuscript Aging & Weathering"
    system: weather
    status: planned
    depends_on: [2]
    passes:
      - pass_id: 3a
        name: "Foundation"
        items:
          - advance: ADV-CLI-001
            system: weather
            status: planned
            depends_on: []
          - advance: ADV-SUBSTRATE-001
            system: weather
            status: planned
            depends_on: []
          - advance: ADV-INK-001
            system: weather
            status: planned
            depends_on: []
      - pass_id: 3b
        name: "Effects Pipeline"
        items:
          - advance: ADV-DAMAGE-001
            system: weather
            status: planned
            depends_on: [ADV-SUBSTRATE-001, ADV-INK-001]
          - advance: ADV-AGING-001
            system: weather
            status: planned
            depends_on: [ADV-SUBSTRATE-001, ADV-INK-001]
          - advance: ADV-OPTICS-001
            system: weather
            status: planned
            depends_on: [ADV-SUBSTRATE-001]
      - pass_id: 3c
        name: "Compositing & Output"
        items:
          - advance: ADV-COMPOSITOR-001
            system: weather
            status: planned
            depends_on: [ADV-DAMAGE-001, ADV-AGING-001, ADV-OPTICS-001]
          - advance: ADV-GROUNDTRUTH-001
            system: weather
            status: planned
            depends_on: [ADV-COMPOSITOR-001]
          - advance: ADV-TESTS-001
            system: weather
            status: planned
            depends_on: [ADV-COMPOSITOR-001, ADV-GROUNDTRUTH-001]

contract_checkpoints:
  - after_phase: 1
    validate:
      - "XL outputs conform to TD-001-A (Folio JSON)"
      - "XL outputs conform to TD-001-B (Manifest JSON)"
      - "XL PAGE XML conforms to TD-001-C"
      - "All folio IDs follow TD-001-G convention"
  - after_phase: 2
    validate:
      - "ScribeSim consumes XL folio JSON without error"
      - "ScribeSim PAGE XML conforms to TD-001-C (glyph-level)"
      - "Pressure heatmaps conform to TD-001-F"
      - "Hand parameters follow TD-001-D"
  - after_phase: 3
    validate:
      - "Weather consumes ScribeSim outputs without error"
      - "Weathering profile conforms to TD-001-E"
      - "Updated PAGE XML conforms to TD-001-C (damage annotations)"
      - "Final images importable to eScriptorium"
```

### Naming Disambiguation

Since multiple systems share component names (cli, tests, groundtruth), advance IDs are scoped by system directory:
- `arrive/systems/xl/advances/ADV-CLI-001.md` — XL's CLI
- `arrive/systems/scribesim/advances/ADV-CLI-001.md` — ScribeSim's CLI
- `arrive/systems/weather/advances/ADV-CLI-001.md` — Weather's CLI

The advance_id alone (e.g., `ADV-CLI-001`) is unique **within** a system. Cross-system references use the form `<system>/ADV-<COMPONENT>-<SEQ>` (e.g., `xl/ADV-EXPORT-001`).

---

## Subcommand: `advance <system>`

Draft advances for a single system only.

### Instructions

1. Read the system's `system.yaml` to get components and pipeline context
2. Read its project brief and solution intent
3. Read TD-001 for relevant contracts
4. Generate advances for each component using the template above
5. Only generate advances that don't already exist (check the advances directory first)

---

## Subcommand: `validate`

Check cross-phase contract alignment.

### Instructions

1. Read all three system.yaml files and extract `pipeline.inputs` and `pipeline.outputs`
2. Read `docs/tech-direction/TD-001-interface-contracts.md`
3. For each system boundary (XL→ScribeSim, ScribeSim→Weather):
   - Verify every output has a matching consumer input
   - Verify contract references are consistent
   - Flag any orphaned outputs or unmet inputs
4. Report findings:

```
Pipeline Contract Validation

XL → ScribeSim:
  [OK] Folio JSON ({folio_id}.json) — consumed by ScribeSim
  [OK] manifest.json — consumed by ScribeSim
  [OK] PAGE XML — consumed by ScribeSim (text-only → glyph-level)

ScribeSim → Weather:
  [OK] Page images ({folio_id}.png) — consumed by Weather
  [OK] Pressure heatmaps ({folio_id}_pressure.png) — consumed by Weather
  [OK] PAGE XML ({folio_id}.xml) — consumed by Weather

XL → Weather (transitive):
  [OK] manifest.json — consumed by Weather for per-folio dispatch

Contract References:
  [OK] All systems reference TD-001 sections consistently
```

---

## Subcommand: `plan`

Generate or update the implementation plan.

### Instructions

1. If `arrive/implementation-plan.yaml` doesn't exist, generate it using the template above
2. If it exists, read current state and:
   - Update statuses based on which advances have been completed
   - Re-validate dependency ordering
   - Flag any blocked items
3. Show a summary:

```
Implementation Plan Status

Phase 1 (XL):      0/8 complete  [planned]
  Pass 1a (Foundation):     0/2
  Pass 1b (Core Pipeline):  0/3
  Pass 1c (Output):         0/3

Phase 2 (ScribeSim): 0/7 complete  [planned, blocked by Phase 1]
  Pass 2a (Foundation):     0/3
  Pass 2b (Rendering):      0/2
  Pass 2c (Output):         0/2

Phase 3 (Weather):   0/9 complete  [planned, blocked by Phase 2]
  Pass 3a (Foundation):     0/3
  Pass 3b (Effects):        0/3
  Pass 3c (Compositing):    0/3

Next actionable: ADV-CLI-001 (xl), ADV-INGEST-001 (xl)
```

---

## Subcommand: `cfu <ADV-ID>`

Generate pipeline-aware Check for Understanding questions.

### Instructions

1. Read the advance file to get component, system, and pipeline position
2. Read the system's `system.yaml` for pipeline context
3. Generate 3-5 questions that probe:

**Pipeline boundary questions** (primary differentiator from generic CFU):
- What happens if the upstream phase emits data that doesn't conform to the contract?
- If this component's output schema changes, which downstream components break?
- How would you validate this component's output against TD-001 before passing it downstream?

**Phase-specific questions**:
- XL: Register accuracy, period-linguistic fidelity, folio structuring
- ScribeSim: Hand variation fidelity, glyph rendering accuracy, ground truth alignment
- Weather: Aging realism, damage targeting accuracy, coordinate transform preservation

**Cross-phase integration questions**:
- How does a change in XL's folio JSON structure propagate through ScribeSim and Weather?
- If ScribeSim adds a new field to PAGE XML, does Weather need to be updated?
- What's the contract checkpoint that catches a regression here?

---

## General Principles

- **Pipeline-first**: Every advance, plan item, and CFU should be aware of where it sits in the XL → ScribeSim → Weather flow
- **Contract-grounded**: Reference TD-001 sections explicitly; don't rely on implicit assumptions about data formats
- **Phase-sequential, component-parallel**: The three phases are sequential, but components within a phase can often be developed in parallel
- **Evidence-driven**: Each advance must accumulate evidence (tdd:red-green, tests:unit) before it can be marked complete
- **Tidy → Test → Implement**: All work follows the ARRIVE commit discipline
