# MS Erfurt Aug. 12°47 — Manuscript Simulation Pipeline

A three-phase pipeline for producing the physical manuscript artifact described in the fictional *MS Erfurt Aug. 12°47*: Brother Konrad's 1457 confession, reverse-translated into period German and Ecclesiastical Latin, rendered in his scribal hand, and aged 560 years.

## Pipeline

```
English source → [XL] → German/Latin folios → [ScribeSim] → page images → [Weather] → weathered manuscript
```

**XL** — Reverse-translation and folio structuring. Takes the English manuscript text, translates into Frühneuhochdeutsch with embedded Ecclesiastical Latin, structures into 17 folios.

**ScribeSim** — Scribal hand simulation. Renders Brother Konrad's Bastarda hand with per-folio emotional and physical variation onto page images, producing pressure heatmaps and PAGE XML ground truth.

**Weather** — Manuscript aging. Applies 560 years of archival storage, targeted water damage (f04r–f05v), missing corner (f04v), and general aging. Output is a complete eScriptorium-ready document.

## Repository structure

```
ms-erfurt/
├── arrive/                          # ARRIVE governance (umbrella)
│   └── systems/
│       ├── xl/                      # XL system artifacts
│       │   ├── components/          # component YAMLs
│       │   └── advances/            # outcome records
│       ├── scribesim/               # ScribeSim system artifacts
│       │   ├── components/
│       │   └── advances/
│       └── weather/                 # Weather system artifacts
│           ├── components/
│           └── advances/
├── docs/
│   ├── tech-direction/              # Cross-system architectural decisions
│   │   └── TD-001-interface-contracts.md
│   ├── xl-project-brief.md
│   ├── xl-solution-intent.md
│   ├── scribesim-project-brief.md
│   ├── scribesim-solution-intent.md
│   ├── weather-project-brief.md
│   └── weather-solution-intent.md
├── source/                          # Input: annotated English manuscript
│   └── ms-erfurt-source-annotated.md
├── golden/                          # Pre-translated golden corpus (API-free fallback)
├── shared/                          # Cross-system contracts
│   └── schemas/
│       ├── folio.schema.json        # Folio JSON schema (XL → ScribeSim)
│       ├── manifest.schema.json     # Manifest schema (XL → Weather)
│       └── hand-params.schema.json  # Hand parameter schema (ScribeSim)
├── xl/                              # XL implementation (Python + Rust)
├── scribesim/                       # ScribeSim implementation (Python + Rust)
├── weather/                         # Weather implementation (Python + Rust)
└── README.md
```

## Governance

This project uses ARRIVE for outcome-first development discipline. The three systems (xl, scribesim, weather) are governed at the umbrella level. All components start as **incubating**. Development follows **Tidy First → Test First → Implement**.

Cross-system decisions live in `docs/tech-direction/`. Per-system outcomes live in `arrive/systems/<system>/advances/`.

## Getting started

```bash
# TODO: setup instructions after Phase 1 scaffolding
```
