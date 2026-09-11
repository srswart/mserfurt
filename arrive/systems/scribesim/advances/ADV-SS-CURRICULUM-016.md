---
advance:
  id: "ADV-SS-CURRICULUM-016"
  title: "Stroke Context — Bounded Deterministic n-u-m Demonstrator"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","handflow","handvalidate","tests"]
  started_at: "2026-09-10T03:54:13.857346+00:00"
  implementation_completed_at: ~
  review_time_estimate_minutes: 55
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence:
    - "docs/tech-direction/TD-018-mutual-nu-construction-briefs.md"
    - "docs/tech-direction/TD-018-addendum-f-mutual-letter-flow.md"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/owner-feedback-001.json"
    - "scripts/nu_three_way_review.py"
    - "tests/test_nu_three_way_review.py"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/nominal-approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/nominal-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/nominal-001/index.html"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/nominal-001/review.md"
    - "scripts/nu_local_contact.py"
    - "tests/test_nu_local_contact.py"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/local-contact-approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/local-contact-review-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/local-contact-review-001/README.md"
    - "docs/tech-direction/TD-018-local-contact-classification.md"
    - "scripts/nu_self_contact_review.py"
    - "tests/test_nu_self_contact_review.py"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/self-contact-approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/self-contact-review-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/self-contact-review-001/README.md"
    - "scripts/nu_derived_entry.py"
    - "tests/test_nu_derived_entry.py"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/derived-approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/derived-entry-001/candidate.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/derived-entry-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/derived-entry-001/README.md"
    - "docs/tech-direction/TD-018-nu-derived-entry-proposal.md"
    - "scripts/nu_entry_port_audit.py"
    - "tests/test_nu_entry_port_audit.py"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/port-audit-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/port-audit-001/README.md"
    - "docs/tech-direction/TD-018-contextual-entry-feasibility-proposal.md"
    - "docs/tech-direction/TD-018-contextual-u-entry-audit.md"
    - "docs/tech-direction/TD-018-contextual-u-entry.md"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/owner-feedback-001.json"
    - "scripts/nu_nominal_review.py"
    - "tests/test_nu_nominal_review.py"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/nominal-approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/nominal-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/nominal-001/index.html"
    - "scripts/nu_receiving_envelope.py"
    - "tests/test_nu_receiving_envelope.py"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/receiving-envelope-approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/receiving-envelope-review-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/receiving-envelope-review-001/README.md"
    - "docs/tech-direction/TD-018-nu-receiving-envelope-revision.md"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/geometry-approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/geometry-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/boundary-action-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/boundary-action-001/contracts.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/capability-approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/capability-001/report.json"
    - "docs/tech-direction/TD-018-nu-corner-contact-proposal.md"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/thin-connection-investigation/snapshot-001/report.json"
    - "docs/tech-direction/TD-018-thin-connection-feasibility.md"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/owner-feedback-002.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/nominal-approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/nominal-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/nominal-001/README.md"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/envelope-approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/envelope-review-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/approval.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/attempt-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/demonstrator/prepared-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/demonstrator/prepared-001/protocol.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/demonstrator/owner-feedback-001.json"
  model_usage: []
  status: in_progress
---

## Objective

### Current checkpoint — F1 reciprocal construction briefs prepared

- [Review package](../../../../docs/tech-direction/TD-018-mutual-nu-construction-briefs.md)
  specifies J1 receiving-rise-led and J2 shared accommodation as different
  fixed stroke programs, not renamed bridge variants or a search grid.
- Exact source cuts, protected bodies, directed ports, deterministic handles,
  editable envelopes, action/ownership maps and finite-nib/contact gates are
  documented. Both n and u change locally; standalone/context-off remain exact.
- Thinness and minimum radius unchanged. New ports, contact centers and
  aggregate length endpoints, plus a window-local rather than whole-core turn
  guard, are explicitly proposed changes requiring review, not measurement
  repairs or inherited admission from the old candidates.
- F2 ceiling proposed: two fixed candidates, one batch, no retries, 300s checks,
  300s rendering, 25MiB evidence, minimum 5GiB free. Numeric specifications and
  execution await approval; no new candidates, samples, fitting or mu.
- Frozen evidence verified; documentation checks pass. CURRICULUM-016 remains
  in progress, HANDVALIDATE-025/026 gated, changes uncommitted.

### Prior checkpoint — mutual letter-flow plan prepared

- Owner finds derived entry wrong and old bridge better but still wrong; requests
  reciprocal letter influence and investigation of missing nib-angle variation.
  Exact feedback preserved; both current candidates paused for promotion/tuning.
- [Addendum F](../../../../docs/tech-direction/TD-018-addendum-f-mutual-letter-flow.md)
  sequences F1 concrete joint construction briefs, F2 fixed-angle shape study,
  F3 isolated nib-angle comparison, F4 coupled program contract, F5 physical plan.
- New hypotheses may change explicitly bounded n terminal/u initial regions,
  rather than freezing T/S and bending only the bridge. Current placement remains
  the first control; spacing conflict must be surfaced, not silently repaired.
- Immediate next work: at most two purposeful deterministic specifications and
  their numeric regions/ports/budget for review. No samples or fitting this turn.
  Thinness/curvature fixed; any angle-changing contact proof must be redone.
- Documentation checks pass; mu/physical work deferred, CURRICULUM-016 remains
  in progress and uncommitted.

### Current checkpoint — three-way nominal comparison generated and reviewed

- Owner requested canonical/old-bridge/derived-entry visual comparison. One
 10.091s nominal render produces same-frame three-way SVG/PNG and old/new
  color-keyed contact detail. No geometry changes or refitting.
- Assistant visual review finds a real difference: derived entry has a flatter
  lower recovery and upright shoulder before rising. It reads more articulated
  but less fluid there than the old bridge; not a demonstrated tangent break.
  This is assistant opinion, not owner rejection or acceptance.
-38 focused tests pass; unchanged bodies/T/S drawing identity and frozen pins
  verified. PNG visual QA and documentation checks pass. No browser-layout QA
  claimed. No physical run or mu. Await owner feedback before further tuning;
  CURRICULUM-016 remains in progress and uncommitted.

### Current checkpoint — approved local-contact classifier passes

- Owner approved implementation/reinspection under the explicit R-only rule.
  One9.853s saved-candidate review passes geometry/contact classification:
  residual overlap is ordinary neighboring-path coverage within the certified
  forward window; total turning upper0.276573153rad below pi/2.
- All47 external pairs pass with existing permissions. Structural measurements
  and the0.031114480mm derived overlap bound exactly match prior evidence.
  Geometry, thinness/curvature, source/actions and frozen reports unchanged.
-119 focused tests pass; documentation checks pass. No constructor, refitting,
  image, physical execution or mu. Prior unresolved reports preserved.
- Next separately approved canonical/old-bridge/derived-entry nominal comparison
  for owner review. No visual/physical acceptance inferred. CURRICULUM-016 stays
  in progress; HANDVALIDATE-025/026 gated; changes uncommitted.

### Current checkpoint — ordinary/nonlocal contact rule proposed

- [Classification proposal](../../../../docs/tech-direction/TD-018-local-contact-classification.md)
  distinguishes finite-footprint neighboring coverage within one continuous,
  forward normal-contact window from nonlocal return or other-owner contact.
- Proposed sufficient R-only rule requires fixed footprint, positive normal
  progress, derived thickness/progress arc bound, continuous tangents and total
  turning strictly below pi/2. The angular classification guard is explicitly
  new; no old unresolved report is relabeled as a pass.
- Thinness/curvature, geometry, source/action and external-contact limits unchanged.
  Saved evidence suggests compatibility, but classification execution awaits
  approval. Proposed one300s/10MiB no-refit review; no images, mu or physical runs.
- Documentation checks and pins pass; CURRICULUM-016 in progress; uncommitted.

### Current checkpoint — stronger self-contact bound, admission unresolved

- One approved10.255s saved-candidate no-refit reinspection. Identical structural
  results and external-contact checks preserved; frozen pins unchanged.
- New all-parameter-pair proof excludes overlap for entry path positions more
  than0.031114480mm apart in arc length, using finite thickness and monotone
  nib-normal progress across all three cubics and P/Q joins.
- Residual near-path overlap is not automatically permitted. No quantitative
  locality cutoff or P/Q overlap permission introduced; overall unresolved.
  Next explicitly define local versus nonlocal contact or directly certify the
  residual region before admission. Candidate unchanged; no automatic retry.
-107 focused tests pass; documentation checks pass. No new geometry, rendering,
  fitting, physical execution or mu. CURRICULUM-016 in progress; uncommitted.

### Current checkpoint — derived entry generated; self-contact unresolved

- Owner approved one candidate/check run. One11.071s invocation generated and
  preserved the three-cubic thin entry; T/S and retained bodies unchanged.
- Structural, thinness, curvature, aggregate-length and external-contact checks
  pass. Aggregate R self-contact lacks the sufficient monotone nib-axis
  certificate; this is unresolved, not a demonstrated collision or acceptance.
- No retry, fitting, image, physical execution or mu.100 focused tests pass;
  documentation and frozen pins pass. Budget consumed, candidate preserved.
- Next prepare stronger saved-candidate self-contact measurement and request a
  bounded no-refit reinspection, without changed geometry or limits. Nominal
  remains gated; CURRICULUM-016 in progress and uncommitted.

### Current checkpoint — deterministic derived-entry proposal prepared

- [One-candidate proposal](../../../../docs/tech-direction/TD-018-nu-derived-entry-proposal.md)
  keeps T/S, A/B/D/C and all retained bodies exact. Replace only R with derived
  recovery, entry-rise and crown-approach cubics using primitive handle/chord
  ratios and explicit primitive-derived P/Q directions.
- P/Q placement uses canonical gesture heights on the old frozen R scaffold.
  Source lower/upper extremum cuts and the derived-handle family are explicit
  new proposed adaptations, not exact similarity reuse or relabeling.
- Aggregate length, thinness, curvature, spatial and contact gates unchanged.
  Proposed one300s/10MiB candidate/check run,5GiB minimum free, zero retries,
  images, fitting or physical runs. Execution needs separate approval.
- Frozen audit pins verified; documentation checks pass. No new control points,
  root solves or geometry evaluation this turn. Mu deferred; in progress and
  uncommitted.

### Current checkpoint — approved bounded port audit executed

- One5.675s read-only nu audit completed. Exact full-primitive similarity reuse
  is incompatible: A's tangent fixes rotation−2.353981470°, baseline fixes scale
  0.953768823, but baseline horizontal displacement misses B by0.730208283mm.
- Rise endpoint direction conditions pass at that rotation; this is not whole
  adapted-curve feasibility. Independent direct-crown and unchanged-prefix joins
  fail receiving tangent conditions. No geometry, fitting or fallback generated.
- Source extrema, port constraints, frozen coverage and adaptation requirements
  recorded in the separate report.219 selected tests pass,48 exact-null deselected;
  documentation checks pass. All frozen pins preserved; no physical or mu run.
- Next review contradictions, then prepare one deterministic derived departure
  and crown/descent proposal under unchanged limits. Do not transplant full
  primitives or relax envelopes. CURRICULUM-016 remains in progress; uncommitted.

### Current checkpoint — bounded port/envelope proposal prepared

- [Feasibility proposal](../../../../docs/tech-direction/TD-018-contextual-entry-feasibility-proposal.md)
  fixes nu source cuts, A/B/D/C contact/evaluation anchors and existing limits.
  Semantic P/Q ports lie within the thin ascending region; no contact widening.
- First analyze necessary port/envelope conditions for full existing primitives
  under bounded similarity placement, then identify required adaptation types
  without generating curves. No shear, free handles, arbitrary cut search or fitting.
- Proposed one300s read-only invocation,10MiB,5GiB free, zero retries/images/new
  geometry. Incompatible or unresolved results stop the bounded case; a necessary
  condition pass is not geometry admission. Execution awaits separate approval.
- Subsequent deterministic derivation proposal and candidate each remain gated.
  Mu/fine-tuning deferred; CURRICULUM-016 in progress; changes uncommitted.

### Current checkpoint — entry vocabulary and source contract audited

- Read canonical gesture definitions, compiled nu owners and frozen boundary
  pieces; verified frozen pins. No new geometry, admission rerun or render.
- Reusable grammar: lower-return-derived n departure, then u entry built from
  rise→upper-return→descent. Their existing internal tangents match, but their
  attachment tangents and extents differ from the saved bridge; direct transplant
  or T/R/S relabeling is not established reuse.
- Audit defines exact canonical stem coverage, contextual added-span lineage,
  semantic/action partition separation, immutable controls and adverse tests.
  Current thinness, curvature and other limits remain unchanged.
- Next prepare bounded port/envelope feasibility and one deterministic derivation
  proposal before coordinates. Mu/fine-tuning remain deferred; no fitting or
  physical authorization. CURRICULUM-016 in progress; changes uncommitted.

### Current checkpoint — contextual u entry direction confirmed

- Owner considers nu acceptable as a nominal demonstration, but wants natural
  n departure into an upward entry of u, then a turn and descent. Fine-tuning
  details remain unspecified and deferred; this is not final or physical acceptance.
- [Contextual entry design](../../../../docs/tech-direction/TD-018-contextual-u-entry.md)
  defines the semantic program and next read-only construction-contract audit.
  Existing T/R/S already rises/turns/descends; merely renaming R is insufficient.
- Preserve frozen nu as evidence. Thinness, curvature and undeclared body/action
  identities unchanged. No new geometry, images, fitting or physical execution;
  mu deferred. CURRICULUM-016 remains in progress; changes uncommitted.

### Current checkpoint — nominal nu visual review ready

- Owner approved a frozen-nu visual comparison before mu authorization.
  One7.371s packet: same-frame canonical/unconnected versus connected nu,
  enlarged color-keyed vector detail, PNG and local review page.
- Independent nominal renderer uses finite rectangular contact with exact-decimal
  full/corner/full profiles, including negative-corner offset; arc progress is
  approximated by flattened chord length. No legacy full-edge-only substitution.
- No geometry changes, fitting, motion/controller execution or ink simulation.
  All frozen input hashes preserved.200 selected tests pass;48 exact-null cases
  deselected. PNG visually inspected; HTTP assets, SVG frame/identity tests and
  documentation checks pass. Browser UI unavailable; no browser-layout QA claimed.
- Owner visual acceptance pending. Mu remains unstarted; CURRICULUM-016 remains
  in progress and HANDVALIDATE-025/026 remain gated. Changes uncommitted.

### Current checkpoint — saved-nu receiving reinspection passes

- Owner approved the revised checker and one saved-nu no-refit reinspection.
  Implemented `nu-receiving-envelope-evaluation-v2` separately from the frozen
  original checker, proposal, candidate and rejection. All frozen pins verified.
- One5.228s review passes every structural gate and all27 finite-contact pairs.
  Receiving excursion upper0.000137103mm; locality upper0.055851813mm against
  unchanged0.1125mm radius. Thinness/curvature and all geometry/actions unchanged.
- 195 selected tests pass;48 exact-null tests deselected. Documentation checks
  pass. No constructor calls, new geometry, images, fitting or physical runs.
- This passes only the revised geometric/contact criteria, not visual or physical
  acceptance. Next review this evidence before separately authorizing pending mu
  geometry under the same receiving policy. Nominal remains separately gated.
  CURRICULUM-016 stays in progress; HANDVALIDATE-025/026 gated; uncommitted.

Build a small deterministic entry/exit and transition demonstrator whose examples answer a meaningful contextual question, without fitting owner preferences or widening the old affine grid.

Follows [TD-018 Addendum D](../../../../docs/tech-direction/TD-018-addendum-d-stroke-context-transitions.md).
Preparation and the separately approved nominal renderer/page are implemented.
The 48-image packet is generated and checked. The owner reviewed a few examples
and found them indistinguishable; current hypotheses are paused for design
revision. No physical execution, fitting, provider CI or acceptance is claimed.

## Behavioral Change

At most four approved hypotheses including context-off are compared over a provenance-audited shortlist. The demonstrator explains changed spans, body invariants, contact intent and previous-versus-following causality, rather than treating larger deformation as success.

## Component Impact

- `scripts/nu_corner_geometry.py`
- `tests/test_nu_corner_geometry.py`
- `scripts/nu_boundary_actions.py`
- `tests/test_nu_boundary_actions.py`
- `docs/tech-direction/TD-018-boundary-local-action-contract.md`
- `scripts/nu_corner_contact.py`
- `tests/test_nu_corner_contact.py`
- `docs/tech-direction/TD-018-nu-corner-capability-findings.md`
- `docs/tech-direction/TD-018-nu-corner-contact-proposal.md`
- `scripts/thin_connection_investigation.py`
- `tests/test_thin_connection_investigation.py`
- `docs/tech-direction/TD-018-thin-connection-feasibility.md`
- `scripts/stroke_nm_nominal.py`
- `scripts/templates/stroke_nm_review.html`
- `tests/test_stroke_nm_nominal.py`
- `scripts/stroke_nm_envelope.py`
- `tests/test_stroke_nm_envelope.py`
- `docs/tech-direction/TD-018-nm-attachment-envelope-revision.md`
- `scripts/stroke_nm_construction.py`
- `tests/test_stroke_nm_construction.py`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/`
- `scripts/stroke_context_preview.py`
- `scripts/stroke_attachment_audit.py`
- `scripts/stroke_clearance_audit.py`
- `tests/test_stroke_attachment_audit.py`
- `tests/test_stroke_clearance_audit.py`
- `scripts/stroke_context_nominal.py`
- `scripts/templates/stroke_context_nominal.html`
- `tests/test_stroke_context_preview.py`
- `tests/test_stroke_context_nominal.py`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/demonstrator/`

Keep new adapters opt-in and outside frozen core identity scans. Exact paths and
any required migration must be frozen before implementation, not inferred as
permission to change canonical sources or add identity-scanned spec files.

## Dependencies

- [ADV-SS-GESTURE-005](ADV-SS-GESTURE-005.md)

Owner scope/protocol approvals in Addendum D are independent gates, not implied
by a dependency's implementation status. C006's full completion is not a
prerequisite for consuming its specifically pinned P2 mechanical evidence.

## Planned Implementation Tasks

- [x] workflow: preserve all existing uncommitted work; no branches, commits or merges without explicit later authorization.
- [x] tidy: assess narrowly required preparation; do not refactor frozen sources or unrelated components.
- [x] Freeze owner-approved local parameter ranges and at-most-15-string inventory from the investigation; no free-form search, new alphabet, active actions, randomness or fatigue.
- [x] Add failing tests for isolated/null, previous-only and following-only interventions, body/anchor preservation, legal transitions and unchanged legacy fixtures.
- [x] Construct deterministic context-off, form-only and combined entry/exit geometry contrasts only where supported; mark transition-only/form-plus-new-transition arms unsupported. Nominal packet generated under separate approval.
- [x] Separate matched-advance shape effects from spacing and label whole-letter affine controls honestly; no new affine/spacing-only variants generated.
- [x] Prepare full-frame synchronized diagnostic specifications, exact renderer dimensions and conservative nominal finite-nib control-hull containment. Actual-ink containment and timed contact evidence remain physical-validation work.
- [x] Freeze and obtain approval for nominal rendering before generating previews; packet explicitly labels nominal geometry, with no desired timed-motion or actual-ink substitution.
- [x] Collect a bounded owner judgment: indistinguishable from a few unspecified examples, not an exhaustive 48-example review. No ranks or targets invented.
- [ ] Freeze the demonstrator, diagnostic inventory and concrete physical-validation proposal for HANDVALIDATE-025; do not run a controller or optimize parameters.

## Bug Fixes

- [x] No frozen code fix was needed; earlier clock/contact/measurement behavior and failed artifacts remain unchanged.

## Risk + Rollback

- Risk: Nominally attractive examples could hide impossible contact dynamics or make a larger change look automatically better.
- Rollback: Keep all unsuccessful hypotheses and owner feedback; return to GESTURE-004's scope decision without changing the accepted baseline or expanding bounds automatically.
- Keep fixed tool/action, no-fatigue and no-fitting constraints. Proposed new
  geometry, frames or criteria require prospective approval; no phase-level
  reset of the old time/render debit is permitted.

## Evidence

- [x] Each difference has a named canonical cause and approved bound; unchanged body/contact claims are tested structurally.
- [x] Owner reported no meaningful visible distinction in the examples reviewed; return to design without forced preferences or extrapolated per-example labels.
- [ ] The exact physical inventory, metrics, frames and resource proposal exist before physical execution.
- [x] Record test-first evidence where code changes, exact commands, source/report
  pins and local results; do not fabricate tidy/test/physical success during planning.
- [x] Run plan, generated-rule, local-link and whitespace checks for the preparation scope.

## CI Evidence Notes

Local checks are not provider CI. Before any separately authorized merge, run
`arrive pr check --strict --json` and record provider/tool limitations honestly.
No branch, commit or merge is part of the current planning authorization.

## Changes Made

### 2026-09-10 — planned from the owner-approved stroke-context direction

- Defined a bounded deliverable and stop gates; implementation and evaluation
  remain unstarted. See Addendum D for retained baseline pins and budget limits.

### 2026-09-10 — preparation complete; separate nominal-render approval pending

- Template-first: `arrive template render --kind advance --json`. No frozen
  refactor required; pre-existing changes remain uncommitted.
- Test-first `.venv/bin/python -m pytest -q tests/test_stroke_context_preview.py`
  failed collection before the adapter existed, then passed **10 tests**.
- Regression `.venv/bin/python -m pytest -q tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null'`
  passed **88 tests**, with 48 unchanged exact-null tests deselected. Those 48
  passed in GESTURE-005; no new full physical measurement is implied here.
- `.venv/bin/python -m scripts.stroke_context_preview prepare` verifies frozen
  contract/report/source manifests, freezes 48 base geometry documents and checks
  local causal deltas, exact body anchors/advances/contact owners, H3 composition
  and conservative nominal full-frame finite-nib containment. Zero raster,
  controller or optimizer calls; no owner feedback fabricated.
- Report SHA-256:
  `8e25b685591f3cb9c52f05bcd1220f5f8ddb62038b9c2119078e3c9158ba8329`.
  Proposed nominal protocol SHA-256:
  `66a9984b2584c2278b11aa5e36675ba6d51a658a522fb2c9a5174ee3cea17274`.
- Approval request: 48 nominal-only PNGs, one local review page, fixed
  1169×390 full-frame dimensions; 5-minute/100-MiB ceilings, 5-GiB free-space
  guard and no automatic retries. Renderer/page implementation and invocation
  follow explicit protocol approval, not this advance's general authorization.
- Physical proposal enumerates 1,152 executions and at most 4,104 render calls,
  retaining old debit/remaining budgets. Time feasibility, non-null planner,
  independent reader, exact local windows and adverse-control schedule are
  unresolved; no execution-ready physical protocol or allowance is claimed.
- State the pilot limitation: pairs do not test one letter with both neighbors;
  triples remain unadmitted. The 0.04-mm handle cap bounds a single-handle cubic
  centerline change to at most 0.63 pixel at 900 dpi. Indistinguishable outcomes
  are valid; no automatic widening or invented preference labels.
- Owner-facing review: `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/demonstrator/README.md`.
  Advance stays in progress for nominal approval, rendering/review and physical
  proposal completion. No commit, merge, provider CI or acceptance claimed.

### 2026-09-10 — owner-approved nominal packet generated

- Owner: "Yes approved -- let's do it." Separate approval record SHA-256:
  `8ca9757e8946b35b3b0198f93231204d64a27d9352fe2e2a4b7d0334bbef86e3`.
  Scope is exactly the pinned 48-image/one-page nominal protocol; no physical
  execution, fitting, extra raster diagnostics or automatic retries.
- New adapter/template/tests preserve the frozen preparation sources. Added
  curriculum selectors for these files. Test-first collection failed before
  the renderer existed, then 7 renderer unit tests passed without image output.
- Generation command:
  `.venv/bin/python -m scripts.stroke_context_nominal generate --approval-sha256 8ca9757e8946b35b3b0198f93231204d64a27d9352fe2e2a4b7d0334bbef86e3`.
  **48 images**, **8.29 seconds**, **740,539 bytes**, no retry. Disk free space
  was approximately18 GiB before generation, above the 5-GiB guard.
- Report SHA-256:
  `8a020790ea4b65fb37c00036eb745db1295bdeb4a1085e52e0511a88221626ea`.
  Read-only `inspect --report-sha256` verifies all48 images without rerendering.
  Isolated H0–H3 hashes match exactly; all frames are1169×390 and not edge-clipped.
- `.venv/bin/python -m pytest -q tests/test_stroke_context_nominal.py tests/test_stroke_context_preview.py tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null'`
  passes **105 tests**, 48 unchanged exact-null cases deselected. JS syntax,
  ARRIVE plan, generated-rule and whitespace checks pass.
- Playwright CLI and CUA browser/native control were unavailable; local headless
  Chrome CDP checks all48 loads, 1440px desktop/390px mobile layout, full-frame
  cards, 4× detail, annotations, following preset, blink and empty feedback export.
  No runtime errors, no horizontal mobile overflow, no owner labels invented.
  Existing nn-H1 and um-H2 images were visually inspected without new rasters.
- Review page: `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/demonstrator/nominal-001/index.html`.
  Advance remains in progress for owner review and physical-proposal gates;
  all physical/acceptance flags false, budgets retained, changes uncommitted.

### 2026-09-10 — owner feedback: indistinguishable; return to design

- Recorded the verbatim response in `demonstrator/owner-feedback-001.json`, bound
  to the nominal packet/protocol pins. Owner reviewed "a few"; exact examples,
  count and viewing mode are unknown. No 48-way ties, universal pixel equality,
  full rejection or mechanical failure are inferred.
- Pause H1–H3 progression to HANDVALIDATE-025. This is the planned usefulness
  stop gate, not permission to increase angles, refit, render again or alter
  targets/thresholds. No further exhaustive ranking requested.
- Preserve the useful span/ownership/null infrastructure and upright n/u/m
  baseline. Next proposed design question: meaningful construction-level
  entry/exit alternatives and an explicit neighbor-dependent reason for them,
  rather than larger versions of the same tiny terminal-handle perturbation.
  No new hypothesis, body exception or transition is approved by this feedback.
- Advance stays in progress, paused for design revision; physical proposal
  completion is deferred rather than falsely marking physical readiness.

### 2026-09-10 — boundary-construction design revision documented

- Owner requested design revision toward meaningful neighbor-dependent entry/exit
  construction. [Addendum E](../../../../docs/tech-direction/TD-018-addendum-e-boundary-construction.md)
  replaces arbitrary terminal-handle perturbations with a proposed shared
  departure/transfer/receiving construction and an exact separate-letter fallback.
- First proposed read-only study: canonical separate boundary and one candidate
  terminal-turn/receiving-rise family on nm/nn/um/mm plus isolated n/u/m. No
  connecting geometry, new sites, bounds, topology or spacing is admitted yet.
- Require concrete attachment intervals, protected body constraints, reachable
  regions, ownership and finite-nib limits before owner review and implementation.
  A large gap or incompatible receiver must reject, not force a connector.
- Existing H0–H3 identities and packet remain unchanged. New B0–B3 comparison
  arms are proposed only where valid; no new images or word/triple exposure.
  Re-enumerate physical work after a useful demonstrator; the old1152-run schedule
  is not permission or an applicable inventory for a new construction.
- This is design/governance work, not a new implementation or physical pass.
  Follow-up advances can be generated for the scoped investigation/contract work;
  CURRICULUM-016 remains in progress and HANDVALIDATE-025 is gated.

### 2026-09-10 — canonical attachment-site investigation implemented

- Owner requested read-only investigation before new geometry approval.
  Template-first preparation retained. New script/test/gesture selectors only;
  frozen code, Addendum E input, candidates and old packets remain untouched.
- Test-first collection failed before the module existed, then
  `.venv/bin/python -m pytest -q tests/test_stroke_attachment_audit.py` passed10 tests.
- `.venv/bin/python -m scripts.stroke_attachment_audit snapshot` evaluates
  existing canonical points/tangents at baseline and half/full existing
  lower-return entry height, without generating replacement or connector curves.
- Seven exposed strings only;27 site pairs over nm/um/mm, nn negative control,
  isolated n/u/m unchanged.15 pairs fail the smooth above-baseline necessary
  condition at one/both endpoints;12 are not ruled out, **none proven feasible**.
- Proposed positive-height attachment regions are0.434496/0.868992mm above
  baseline. Retained/replaced canonical intervals and ownership are recorded;
  these are inspection probes, not approved body exceptions or chosen winners.
- Both departing downstroke and receiving upstroke require reconsidering their
  baseline endpoints. Fixed gaps remain about3.4mm for nm/um and5.2mm for mm;
  compare with1.378902mm existing lower-return span, without inventing a threshold.
- Report SHA-256:
  `b555be20ccfc179be57b7ac701ded640741a4a9947a124ccbddef91550fe5a1e`.
  Findings: `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/attachment-investigation/README.md`.
- No new connector geometry, raster samples, fitting or physical runs. Remaining
  work: style/body-exception review, finite-nib corridor/overlap constraints,
  approved bounds and versioned consumer before any new preview. Advance stays
  in progress; current H1–H3 physical progression remains paused.
- Exact pinned read-only reinspection passes. Regression command
  `.venv/bin/python -m pytest -q tests/test_stroke_attachment_audit.py tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null'`
  passes98 tests in8.39 seconds;48 unchanged exact-null cases deselected.
  ARRIVE plan, generated-rule, changed local-link and whitespace checks pass.

### 2026-09-10 — finite-nib attachment clearance/overlap audit

- Owner requested clearance/overlap investigation. New read-only script/tests
  and gesture selectors preserve all frozen sources and reports. Template-first
  preparation retained; test-first collection failed before the module existed,
  then7 unit tests passed.
- `.venv/bin/python -m scripts.stroke_clearance_audit snapshot` examines all12
  surviving site pairs with a0.45-mm fixed edge at40 degrees. Existing canonical
  intervals are measured, not replaced; no new connector or raster geometry.
- Bounded swept-polyline polygons use0.00001-mm curve error plus1e-9-mm numerical
  guard. Positive distance lower bounds certify nominal clearance under this
  approximation; zero/near-zero flags possible contact, not proven overlap area.
- nm/mm attachment footprints clear other occurrences; um's departure footprint
  flags contact/overlap with retained rise0:2 at both heights. The existing
  contributor relation is recorded, not converted into new overlap permission.
- Retained-geometry central strips are2.65–2.68mm (nm),2.67–2.69mm (um),4.47–4.49mm
  (mm), accounting for both nib footprints. Access from/to sites and future
  connector self-overlap/curvature remain unproved. No construction is admitted.
- Recommend nm first, defer um pending retained-rise overlap policy, retain nn
  and mm as incompatibility/larger-gap controls. New construction bounds and
  preview protocol require owner review; no automatic spacing or geometry change.
- Report SHA-256:
  `d7dd39b61b91572d1ee3e241e0583266be9dcd9e4f0f577f74e9964820033943`.
  Findings: `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/clearance-investigation/README.md`.
  No samples, fitting, physical execution, new budget, merge or acceptance.
- Exact pinned read-only reinspection passes. Regression command
  `.venv/bin/python -m pytest -q tests/test_stroke_clearance_audit.py tests/test_stroke_attachment_audit.py tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null'`
  passes105 tests in8.29 seconds,48 unchanged exact-null cases deselected.
  Report/source pins,12-case inventory and explicit retained/replacement own
  contacts verified; ARRIVE plan, generated-rule, local-link and whitespace
  checks pass. These are local geometric checks, not physical acceptance.

### 2026-09-10 — n→m-only construction proposal prepared

- Owner requested a proposal, deferring u→m. See
  [n→m construction proposal](../../../../docs/tech-direction/TD-018-nm-construction-proposal.md).
  No new geometry, renders, fitting or physical work performed or approved.
- Proposes one deterministic two-cubic turn/transfer construction using the
  higher matched attachment sites, chosen for vertical turning room rather than
  optimized clearance. Old H0–H3, canonical sources and evidence stay frozen.
- Explicit proposed exceptions: rebuild the final n stem suffix, shift its
  baseline foot0.225mm right, replace the initial m rise prefix and remove its
  separate baseline start only in the connected pair. All other body/advances
  exact. These are owner review items, not implied clearance permissions.
- Fixed construction equations plus whole-curve length, curvature, baseline,
  direction, finite-nib and join-region ownership gates. Any failed/unresolved
  constraint stops the single attempt; no tuning, alternate site or retry.
- Proposed scope: nm active; n/m/nn/mm unchanged controls; um deferred.
  Conditional10 PNGs/one page only after a full geometry pass, with separate
  proposed300s preparation and300s nominal ceilings,100MiB combined output,
  5GiB disk guard. No physical budget reset or execution permission.
- Await owner approval of construction/body/overlap and nominal scope before
  implementation. CURRICULUM-016 remains in progress; HANDVALIDATE-025 gated.

### 2026-09-10 — approved single construction attempted; stopped before images

- Owner approved the exact proposal with “Yes approved. Please implement.”
  Separate approval binds proposal SHA-256
  `a2a47b91654d7a3d6d5347d67c61f46ae44e158c32523c0b32d2463adf7f932f`.
  Proposal and all prior evidence remain unchanged.
- Implemented isolated twelve-piece geometry, immutable lineage, source and
  approval gates, conservative length/curvature checks and bounded attempt.
  One attempt completed in18.821s; source/clearance reinspection passes.
- Generic extent/direction gate returned unresolved and stopped admission.
  Saved controls establish a negative initial x derivative of−0.009536758104:
  canonical tangent matching conflicts with strict rightward/no-left-of-A rules.
  No candidate change or second attempt made; original report preserved.
- Body/ownership/placement, attachments, length and curvature checks pass.
  Finite-nib intersection admission not evaluated. Conditional overlap checker,
  nominal renderer and page remain deferred; no PNGs, fitting or physical runs.
- Findings: `shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/README.md`.
  126 regression tests pass;48 exact-null cases deselected. A new prospective
  attachment/envelope decision is required, not automatic tuning or rerunning.
  CURRICULUM-016 remains in progress; HANDVALIDATE-025/026 gated, um deferred,
  changes uncommitted. This is not completed nominal or physical validation.

### 2026-09-10 — tangent-compatible attachment/envelope requirement revised

- Owner requested revision of the conflicting requirement. See
  [tangent-compatible envelope](../../../../docs/tech-direction/TD-018-nm-attachment-envelope-revision.md).
  This is a documented criterion change, not retroactive acceptance or a retry.
- Keep canonical sites, tangents and saved geometry exact. Permit only the
  initial T departure implied by delta=max(0,−a*dA.x), with delta<=W/100=0.0045mm
  and the left-of-A interval confined to a W/4-radius disk around A. One
  horizontal minimum and recovery only; T descends, R remains strictly rightward.
- All other body, length, curvature, finite-nib/overlap and ownership constraints
  stay unchanged. Prospective v2 evaluation must isolate roots/extrema and reject
  unresolved boundaries; the missing finite-nib admission still precedes images.
- Implementation and one saved-candidate reinspection require separate approval
  binding the revision hash. Proposed300s verification/conditional300s nominal,
  100MiB output/5GiB free/zero retries; old geometry attempt remains consumed.
  No candidate generation, behavioral rerun, fitting, images or physical runs.
  CURRICULUM-016 stays in progress; HANDVALIDATE-025/026 gated; um deferred.

### 2026-09-10 — revised checker implemented; saved candidate passes

- Owner approved revised checker implementation and saved-candidate reinspection.
  Separate approval pins revision, immutable candidate/report and frozen helper.
- Implemented rational polynomial root checks, guarded extrema, local hull bounds
  and conservative fixed-nib separating-axis/intersection-containment checks.
  No construction/refit/selection call; geometry is read directly from attempt-001.
- Single reinspection completed in9.172s. All geometry and21 finite-nib pair
  checks pass. Leftward excursion upper bound0.000087725mm; allowed canonical
  departure envelope0.003178919368mm. Locality upper radius0.083590119mm is below
  0.1125mm. Existing attachment, length, curvature and identity gates pass.
- Original unresolved result remains unchanged: this passes revised criteria,
  not the original horizontal rule.146 regression tests pass,48 exact-null cases
  deselected. No new geometry, PNGs, fitting, physical execution or acceptance.
- Results: `shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/envelope-review-001/README.md`.
  Next is the conditional nominal comparison and owner usefulness review.
  CURRICULUM-016 remains in progress; HANDVALIDATE-025/026 gated; um deferred.
  Reinspection allowance consumed, nominal allowance unspent, changes uncommitted.

### 2026-09-10 — conditional nominal packet generated and visually reviewed

- Owner requested the conditional comparison for assistant visual review.
  Separate nominal approval pins passing report, saved geometry and renderer.
  Implemented ten-image renderer/page outside frozen sources; no geometry change.
- Generated10 PNGs/one page in9.839s. Full1169×390 frame at900dpi; no clipping.
  n/m/nn/mm are pixel-identical across modes; nm differs at2806 pixels.
- Assistant review: n/m remain readable and the connection is plainly visible,
  but the long shallow connector looks somewhat underline-like. This is an
  inspectable prototype, not a declared style success or owner preference.
- Browser QA passes image decoding, desktop/mobile overflow, selectors, zoom and
  empty-review guard.157 tests pass with49 deselected:48 exact-null cases and one
  preserved historical root-wide no-PNG assertion conflicting with this new
  authorized packet. Unfiltered selection has that one known failure; old attempt
  and reinspection directories remain image-free. See nominal-001/README.md.
- Owner usefulness review is next; CURRICULUM-016 remains in progress and
  HANDVALIDATE-025/026 gated. Nominal allowance consumed. No fitting, physical
  runs, new candidate, automatic retry, commits or merges.

### Owner feedback — reject this nm construction; prioritize thin nu/mu/num

- Owner finds the connected nm unnatural and its connector too thick. Record
  failure of this candidate's intended-style usefulness gate; do not progress
  to physical validation. Not a universal ban on every possible nm construction.
- Desired connections are nib-thin; preferred contexts are nu, num and mu.
  Pair investigations should start with nu/mu; num must compose n→u and u→m,
  with the existing u→m clearance concern still unresolved, not waived.
- See [feedback/design direction](../../../../docs/tech-direction/TD-018-thin-connection-feedback.md).
  Define plausible attachment/motion/contact and quantitative thinness before
  another bounded proposal; do not cosmetically narrow the old connector.
- No geometry, images, fitting, physical work or new budget authorized or started.
  Frozen packet retained; CURRICULUM-016 in progress, HANDVALIDATE-025/026 gated.

### Thin-connection feasibility investigation completed

- Owner approved the four-point read-only investigation.27 canonical site pairs
  inspected for nu/mu/um in16.497s; no connector geometry, raster, fitting or
  physical execution. Prior source/clearance pins reproduce unchanged.
- nu/mu receive u's descending first stem, not a rising entry. Smooth baseline
  departure and x-height arrival cannot preserve both endpoints inside the band;
  an explicitly bounded coupled departure/receiving construction is required.
- Current full-edge orientation is broad for up-right motion. Existing finite
  contact/action machinery can represent10% active corner contact analytically
  below0.05mm at representative angles, but this is not admitted execution.
  Corner offset/rate transitions and full-contact clearance must be addressed.
- Full-edge nu/mu site screens have no nonowner contacts; um departure still has
  possible retained lower-return/rise contact. No clearance/body waiver. Num
  stays dependency-only; previously sealed status cannot support a fresh-unseen
  claim after owner naming and canonical topology inspection.
- 116 tests pass,48 exact-null cases deselected. Next: corner-contact capability
  and coupled nu entry/exit proposal, mu comparator. Proposed thinness reference
  is not an approved threshold; no new run/render allowance or fitting approval.
  CURRICULUM-016 in progress; HANDVALIDATE-025/026 gated; changes uncommitted.

### Boundary-local action contract and exact edge handling implemented

- Owner requested addressing the contract and numeric handling. Added isolated
  nu-boundary-actions-v1 and boundary-contact-decimal-v1; no frozen core changes.
- Exact decimal/rational endpoint validation accepts both true10% corners and
  rejects genuinely narrower intervals without epsilon, clamping or widening.
  Interpolation is exact; finite-contact reflection and legacy-supported coordinate
  equivalence pass. Legacy positive-corner rejection remains intentionally intact.
- Geometry-free nu/mu manifests preserve every canonical body action/source,
  declare T/R/S profiles/contributors/contact states and four continuity joins,
  and reject extra geometry or execution permission. No legacy-cap bypass or
  global action mutation; no geometry/controller consumer is enabled.
- Snapshot10.874s;163 tests pass,48 exact-null deselected. Prior capability/source
  identities preserved. See TD-018-boundary-local-action-contract.md.
- Next explicit geometry approval binding proposal and new contract report. No
  new connector, image, fitting or physical run; CURRICULUM-016 in progress and
  HANDVALIDATE-025/026 gated. Changes uncommitted; no old budget reset.

### Fixed nu/mu geometry implemented; nu rejected before mu or images

- Owner approved fixed geometry implementation/checking. Separate approval binds
  the proposal and new boundary contract. One nu candidate generated in5.709s;
  no fitting, corner switch or source/parameter/threshold change.
- S receiving turn fails the strictly-rightward requirement: minimum x derivative
  −0.011663354102562806 at its canonical receiving tangent. The required tangent
  points left, so this is an analytic incompatibility, not pixel uncertainty.
- Departure envelope, T/R/S lengths and curvature, attachments, receiver-top shift,
  vertical band, R direction and thin-core bound pass. Finite-contact sweep not
  evaluated because the structural gate failed; mu not started by stop policy.
- Saved candidate/report at nu-corner-contact-v1/geometry-001, immutable.173 tests
  pass,48 exact-null deselected. Next receiving-tangent/envelope compatibility
  revision, not a flipped handle or automatic rerun. No image/style judgment,
  physical run or admission. CURRICULUM-016 remains in progress; HANDVALIDATE-025/026
  gated, changes uncommitted and old evidence/budgets unchanged.

### Receiving envelope revised; thinness and curvature unchanged

- Owner requested canonical-tangent-compatible receiving bounds, explicitly
  preserving thinness and curvature. See
  [receiving revision](../../../../docs/tech-direction/TD-018-nu-receiving-envelope-revision.md).
- S may have one interior horizontal maximum and one interior crossing of C.x,
  then arrive from the right along unchanged dC. Rightward allowance is the
  fixed receiving-handle projection delta_C=max(0,−c*dC.x), capped at0.0045mm;
  the entire right-of-C interval must lie within0.1125mm of C. No overlap waiver.
- Saved geometry, source intervals, contact ramps and all other limits remain
  unchanged, especially whole-R thinness0.089393938mm and curvature8.888888889/mm.
  Original rejected report remains valid under its original horizontal rule.
- Proposed next: revised checker and one saved-nu no-refit reinspection, followed
  by finite-contact gates only on structural pass.300s/10MiB/5GiB free/zero
  retries; separate approval required. No geometry generation, rerun or images
  in this documentation turn. Mu remains unstarted; CURRICULUM-016 in progress.

### Corner-contact capability and coupled nu proposal prepared

- Owner requested the recommended proposal. See
  [corner-contact and nu design](../../../../docs/tech-direction/TD-018-nu-corner-contact-proposal.md).
  No capability execution, connector construction or rendering started.
- Proposes fixed orientation with negative-corner10% contact, full/corner ramps,
  and separate capability comparison of both corner identities. Opposite corner
  is not an automatic fallback; no centered cosmetic thin-line substitute.
- Defines one three-cubic family: departure turn, thin rising core and receiving
  turn into u. Exact higher departure site and receiver t=0.25; explicit outgoing
  foot shift0.225mm and moved u top anchor, with undeclared body/spacing exact.
  nu primary, mu same-family larger-gap comparator; um/num still excluded.
- Prospective thin-core limit0.089394mm, finite-thickness contact/ramps, whole-curve
  direction/length/curvature gates and four bounded splice regions. Body and
  corner choices are review items, not inferred permissions or computed success.
- Next approval:300s read-only capability inspection,10MiB output,5GiB free,
  zero images/geometry/controller/fitting/retries. Geometry and subsequent ten-image
  finite-contact packet need separately bound approvals. No old budget reset.
- Documentation/governance checks only; no behavioral rerun or new measurements.
  CURRICULUM-016 in progress, HANDVALIDATE-025/026 gated, changes uncommitted.

### Read-only corner capability completed; boundary contract required

- Owner approved capability section6.1 only. One13.638s snapshot; no connector,
  raster, controller or fitting. Proposed negative corner reflects correctly,
  width upper0.049244289mm, center offset0.2025mm.
- Full fixed-site ramp envelopes clear all nonowner canonical strokes at the
  four selected nu/mu sites. Own retained/replaced contacts remain explicit;
  no moving-path clearance or new splice permission inferred.
- Both partial profiles fail the canonical connected fixed-action schema. Shared
  actions affect all body occurrences; independent boundary lineage/consumer is
  not admitted. Positive [0.9,1] also fails raw contact minimum-width validation
  because binary subtraction falls below0.1. No core fix or widening performed.
- See [capability findings](../../../../docs/tech-direction/TD-018-nu-corner-capability-findings.md).
  Next boundary-local action/numeric-edge contract, preserving frozen core;
  geometry and rendering stay gated.125 tests pass,48 exact-null deselected,
  including tests that document the existing positive-corner rejection.
- Capability budget consumed; no new allowance or old physical reset.
  CURRICULUM-016 in progress; HANDVALIDATE-025/026 gated; changes uncommitted.
