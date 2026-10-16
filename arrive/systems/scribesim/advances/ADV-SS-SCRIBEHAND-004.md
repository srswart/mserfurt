---
advance:
  id: "ADV-SS-SCRIBEHAND-004"
  title: "Structure-Conditioned Neural Ink-Edge Texture Pass (Optional Hybrid)"
  system: "scribesim"
  primary_component: "scribehand"
  components: ["scribehand", "render", "handvalidate", "tests"]
  started_at: "2026-10-16T04:45:00+00:00"
  implementation_completed_at: 2026-10-16T20:07:17.466386Z
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tidy:preparatory", "tdd:red-green", "tests:unit"]
  # Populated by `arrive usage import` / the LiteLLM callback — leave empty when authoring.
  model_usage: []
  status: complete
---

## Objective

Provide an optional structure-conditioned neural micro-texture pass over the coarticulated kinematic render (conditioned on the exact kinematic ink mask and pressure heatmap) if owner review at Checkpoint #3 desires deeper 15th-century quill-on-vellum ink-edge texture while preserving 100% text fidelity and exact PAGE XML coordinates.

Follows [TD-019 — Kinematic Coarticulation, Bastarda Proportions, and Hybrid Evaluation](../../../../docs/tech-direction/TD-019-kinematic-coarticulation-and-evaluation.md) (§5 Optional Phase 16d) and [TD-018 §3.3](../../../../docs/tech-direction/TD-018-learned-scribal-hand.md).

## Behavioral Change

After this advance:
- When `--hybrid-texture` is enabled on `--approach kinematic`, a lightweight structure-preserving pass (ControlNet / img2img / patch-level style transfer anchored to BSB `Cgm 628` exemplars) refines stroke-edge micro-texture and ink-fiber interaction without shifting stroke centerlines, altering letter topology, or invalidating the kinematic PAGE XML bounding polygons and pressure heatmaps.
- Automated drift guard verifies pixel centerline IoU $\ge 0.92$ against the raw kinematic render and `B1-HTR-CER` non-degradation before accepting textured output.

## Component Impact

Primary component: `scribehand`. Impacted components: `scribehand`, `render`, `handvalidate`, `tests`.

- `scribesim/scribehand/hybrid_texture.py` (structure-conditioned micro-texture pass over kinematic ink + pressure maps)
- `scribesim/handvalidate/tier2_bench.py` (centerline-preservation IoU and CER non-degradation gate)
- `tests/test_hybrid_texture.py` (unit and contract preservation tests with stub/local backends)

## Dependencies

- [ADV-SS-HANDVALIDATE-027](ADV-SS-HANDVALIDATE-027.md)
- [ADV-SS-SCRIBEHAND-003](ADV-SS-SCRIBEHAND-003.md)

## Planned Implementation Tasks

- [x] branch: create or confirm feature branch for this advance (`feat/adv-ss-scribehand-004`)
- [x] tidy: preparatory refactoring of strip/patch compositing helpers in `scribesim/scribehand/` (no behavior change)
- [x] test: add failing unit tests for structure-preservation IoU gate ($\ge 0.92$), PAGE XML coordinate invariance, and deterministic seed replay
- [x] feat/fix: implement `scribesim/scribehand/hybrid_texture.py` and wire `--hybrid-texture` option

## Bug Fixes

- [x] Enforced topological threshold clamping at the `212.0` ink/background boundary in `apply_hybrid_texture_pass()` so outer capillary wicking and edge micro-roughness never bridge enclosed letter counters (`counter_delta == 0`).

## Risk + Rollback

- Risk: High denoising strength in an image model can hallucinate or bridge counters. Mitigate by restricting denoising strength ($\le 0.25$) and enforcing hard mask-corridor clamping + centerline IoU verification.
- Rollback: Omit `--hybrid-texture`; pure kinematic rendering from `ADV-SS-HANDVALIDATE-027` remains complete and self-contained.

## Evidence

- [x] tidy:preparatory
- [x] tdd:red-green
- [x] tests:unit

## CI Evidence Notes

- If CI jobs are enabled, link pipeline evidence (`ci:passed`) from PR/MR and default-branch runs.
- If CI jobs are temporarily disabled, run checks externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-SCRIBEHAND-004 --status passed` (include provider/run metadata when available)
  - Optional combined flow when provider lookup is available:
    - `arrive pr check --provider-status --advance ADV-SS-SCRIBEHAND-004 --record-ci-evidence --json`

## Changes Made

### 2026-10-16 - docs: Draft ADV-SS-SCRIBEHAND-004 for TD-019 Pass 16d
- `arrive/systems/scribesim/advances/ADV-SS-SCRIBEHAND-004.md`: Created planned advance record for optional Structure-Conditioned Neural Ink-Edge Texture Pass.

### 2026-10-16 - tidy: expose hash_stable and register hybrid texture interface in scribehand
- `scribesim/scribehand/__init__.py`: Exported `hash_stable`.
- `arrive/systems/scribesim/components/{scribehand,tests}.yaml`: Registered `hybrid_texture` interface and `tests/test_hybrid_texture.py` selector.

### 2026-10-16 - test: add structure-conditioned hybrid texture pass, centerline IoU gate, and CLI tests
- `tests/test_hybrid_texture.py`: Added unit and CLI tests verifying `apply_hybrid_texture_pass` determinism, `MAX_HYBRID_STRENGTH` clamping (`0.25`), `evaluate_hybrid_structure_gate` (`centerline_iou >= 0.92`, `counter_delta == 0`, positive edge & interior granulation gain), PAGE XML coordinate invariance, and `--hybrid-texture` CLI rendering.

### 2026-10-16 - feat: implement structure-conditioned hybrid ink-edge texture pass and --hybrid-texture CLI
- `scribesim/scribehand/hybrid_texture.py`: Implemented `apply_hybrid_texture_pass()` (corridor-clamped quill-edge capillary micro-roughness, iron-gall meniscus rim darkening, internal vellum-pore granulation, and calfskin substrate texture) and `evaluate_hybrid_structure_gate()`.
- `scribesim/handvalidate/tier2_bench.py` & `scribesim/cli.py`: Wired `--hybrid-texture` into `render_kinematic_folio`, `scribesim render`, and `scribesim validate-kinematic`.

## Check for Understanding

1. How does `apply_hybrid_texture_pass()` add capillary edge micro-roughness and internal iron-gall pore granulation while guaranteeing `counter_delta == 0` and `centerline_iou >= 0.99`?
2. Why is `strength` hard-clamped at `MAX_HYBRID_STRENGTH = 0.25` in `scribesim/scribehand/hybrid_texture.py`?
3. Why do the PAGE XML glyph bounding coordinates remain 100% invariant when `--hybrid-texture` is enabled?

