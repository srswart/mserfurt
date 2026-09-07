# TD-018 Addendum A — Stroke Gestures and Intentional Pen Actions

**Status:** all nine supporting Advance outcomes recorded, including opt-in contact/realized-action infrastructure and guarded learning/readiness tooling. S1-gesture/S1-action remain blocked; action fitting and selected-candidate acceptance are unexecuted. No real promotion.

**Date:** 2026-09-06

**Parent:** [TD-018 — Reference-Grounded Recovery of Konrad's Hand](TD-018-reference-grounded-hand-recovery.md)

**Current next work:** [Addendum B — foundation repair](TD-018-addendum-b-foundation-repair.md)
adds six planned Advances for stable contact, audited vocabulary/limits and
actual primitive/gesture learning with independent acceptance before later layers.

## 1. Decision and scope

Extend the shared stroke language with a continuous **gesture** layer between
geometric primitives and letter recipes. A path describes where the pen travels;
a gesture also describes how its edge contacts the page along that path.

The hierarchy is:

**Geometric primitives → stroke gestures → letter recipes → word programs → line programs.**

Intentional nib orientation, edge contact and finishing actions belong to the
construction of a gesture when evidence requires them. They are not equivalent
to fatigue, random variation or depleted ink. Retain fixed-angle, full-edge,
constant-pressure execution as the first baseline, not as a permanent restriction
on all future letters. Fatigue, depletion/dips, stochastic rhythm, tremor, warp
and speculative semantic/emotional effects remain deferred.

This is a design amendment, not another completed implementation phase. Existing
synthetic S0/S1 results remain valid only for their frozen fixed-tool scope. No
new gesture gate, real-source training or owner appearance approval is claimed.
Existing Advance IDs and completion records remain unchanged. The planning
follow-up added nine prerequisites; Addendum B adds six foundation repairs to
Pass 15, now thirty-four Advances: twenty-three outcomes complete and eleven planned.
Blocked action experiments remain unexecuted. Section 10
records the new phases and downstream dependency changes, not gate passes.

## 2. Resources and evidence boundaries

- [Jake Rainis — Broad Edge Calligraphy Technique](https://jakerainis.com/blog/broad-edge-calligraphy-technique-a-comprehensive-guide-to-stroke-control-and-pen-manipulation/)
  describes direction/angle-dependent broad-edge marks, deliberate rotation,
  edge-pressure/release techniques, and overlapping strokes used to construct
  terminals and letter bodies. Use it to propose tool exercises and construction
  hypotheses. It is contemporary practitioner guidance, not verification of our
  manuscript's historical ductus or a calibrated mechanical model of its pen.
- [Heinen Designs — Eight Basic Calligraphy Strokes](https://www.heinendesigns.com/blog/8-basic-calligraphy-strokes)
  supplies a useful gesture vocabulary: upstroke, downstroke, overturn, underturn,
  ascending loop, descending loop, compound curve and oval. Its examples largely
  concern brush lettering. Borrow continuous-movement organization, not a universal
  rule that upward travel is thin and downward travel thick for every broad-edge
  orientation. Its list is not an exhaustive historical stroke inventory.
- [Wizsutraa — Stages of Calligraphy](https://medium.com/@wizsutraa/stages-of-calligraphy-a75c1981c547)
  emphasizes consistent foundational practice and appropriate tools before copying
  alphabets. Use this as curriculum motivation, not quantitative evidence of
  simulation quality or historical accuracy.

The contracts below are project engineering proposals informed by these guides,
not claims made by their authors. Link to the resources; do not import their
illustrations as repository assets or training targets without suitable rights.
Repository-generated synthetic exercises must declare their independent origin.

Manuscript appearance remains authoritative for selecting forms. A plausible
modern technique does not establish that the reference scribe used it. Static
pixels cannot uniquely separate trajectory, nib angle, contact fraction,
pressure, ink spread, retouching or stroke order. Record competing hypotheses
and uncertainty rather than claiming exact recovery of historical actions.

## 3. Current implementation and the missing contract

`scribesim/evofit/stroke_language.py` implements `shared-stroke-language-v1`:
six shared cubic primitive families, bounded primitive references inside
recipes, explicit transitions, layered text context and attributed guide output.
`scribesim/curriculum/stroke_learning.py` fits shared interior control points
against synthetic images while keeping endpoints, tool settings and recipes
fixed. The supplied i/u recipes demonstrate reuse, not learned letter forms.

It does not yet provide a first-class gesture identity, continuous action tracks,
partial-edge geometry, calibrated contact-pressure behavior or stationary dabs.
An arc assembled from multiple primitives is not automatically multiple pen-down
strokes; conversely, an overlapping finishing pass is not the same gesture as
the stroke it touches. These distinctions need explicit representation.

The current `turn` and `loop` examples are starting hypotheses, not complete
underturn/overturn or ascending/descending-loop families. A practice sheet must
not hide that coverage gap by relabeling an existing curve.

## 4. Data model and ownership

| Record | Owns | Must not own |
|---|---|---|
| `StrokePrimitive` | Shared local geometry, ports, transform/curvature constraints, provenance | Independent per-letter copies of fitted curves |
| `StrokeGesture` | Ordered primitive references, continuous contact topology, entry/exit actions, action-profile references | Arbitrary word-specific geometry or hidden lifts |
| `PenActionProfile` | Bounded orientation/contact tracks and explicitly supported force/speed tracks | Fatigue, reservoir state or image-driven runtime corrections |
| `LetterRecipe` | Gesture instances, bounded placement, lifts, permitted overlaps/crossings, counters and landmarks | Unrestricted residual curves or unrecorded touch-up painting |
| `WordProgram` | Exact letter instances and supported adjacent-letter context overlays | A cached drawing for each word |
| `LineProgram` | Exact words, boundaries, spacing and supported word-edge effects | Silent cross-space contact or hidden global distortion |

Records use immutable versioned identities; changing a shared record creates a
new model hash and invalidates all dependent compiled caches and checkpoints.
Nominal cubics and sampled poses are derived artifacts, not competing sources
of letter geometry. Nested gesture references are initially forbidden; a flat
ordered primitive list avoids recursive macros and makes expansion budgets clear.

### Continuous gestures and separate passes

An underturn may reference a descending segment, a turning segment and a rising
segment, but the pen remains in contact throughout. Segment boundaries retain
identity without inserting settling steps, lifts or pressure resets. Entry/exit
ports enforce the declared positional and tangent continuity. A sharp corner is
permitted only when the gesture declares it; smooth joins cannot silently kink.

A constructed terminal can instead use a main gesture, an explicit lift/air
transition, and a short finishing gesture whose ink intentionally overlaps it.
Record both occurrences and their overlap. Never merge them merely because their
pixels touch, and never add an unrecorded renderer-only repair stroke.

Conceptual notation, not an implemented syntax:

```text
gesture underturn:
    primitives = descend → lower_turn → rise
    contact = continuous
    pen_action = fixed_edge_baseline

letter construction:
    place(main_gesture)
    lift_and_reposition
    place(finishing_gesture, declared_overlap_with=main_gesture)
```

Repeated gestures can form reusable construction patterns, but the compiler must
retain every primitive occurrence. A phrase/macro must not bypass parameter
sharing, text attribution, constraints or the expanded-program size budget.

## 5. Intentional pen-action contract

### Tracks and parameterization

Parameterize a moving gesture by normalized contact arc length `progress ∈ [0,1]`.
Geometric progress is independent of timestep and segmentation. Use finite,
ordered knots with explicit interpolation; reject duplicate/decreasing progress,
NaNs, missing endpoints and out-of-envelope values.

| Track | Units and initial semantics |
|---|---|
| Orientation | Unwrapped degrees in a declared physical coordinate frame; bounded angle and angular rate |
| Active edge interval | Ordered fractions `[edge_start, edge_end]` within the actual nib edge `[0,1]`; full contact is `[0,1]` |
| Mechanical pressure | Existing dimensionless controller units, explicitly not newtons; constant initially |
| Speed | Millimetres/second under the existing planner; constant baseline initially |
| Contact | Explicit approach, pen-down interval, terminal action and lift events |

The first action experiments alter only one track at a time. A subsequent
pressure-dependent deformation model requires tool calibration; do not assume
brush, metal broad nib and quill respond alike. Do not interpret the Rainis
examples as numerical force laws for our simulation.

A stationary dab cannot use arc length as its clock. It requires a separately
versioned finite-duration contact action and actual footprint, or remains
unsupported. Do not turn a zero-length path into a fabricated tiny stroke just
to evade the present degenerate-port guardrail.

### Footprint, direction and width

The nominal renderer sweeps the actual active nib footprint along the path.
Orientation is independent of travel direction: changing path direction at a
fixed angle can already change apparent width. A direction label alone must
not select a thick or thin painted line.

Partial-edge contact changes both the contacting width and its position relative
to the pen center. A left-edge release and right-edge release cannot be modeled
as identical centered width reductions. Specify the surviving edge interval and
derive its shifted physical footprint. Keep an explicit finite edge thickness
where required by the calibrated tool model; no arbitrary hairline opacity fix.

Rotation/release must change swept geometry, not simply darkness. Mechanical
pressure, contact footprint and optical deposition remain separate quantities.
Use constant adequate ink supply for these exercises; intentional edge release
must not be implemented by starving the reservoir. Do not apply a
direction-dependent apparent width a second time as the nib's physical width.

### Compiler and execution boundary

Compile desired poses/actions by physical arc length into the existing guided
controller. The y-up language to y-down physical transform must also transform
tangents, nib orientation and left/right edge conventions consistently.

Validate direct nominal sweep, sampled desired playback and **actual** executed
footprint separately. The actual renderer consumes realized pose/contact fields
from controller state, not the intended action profile disguised as an achieved
result. If the controller or renderer cannot express partial contact, fail with
an explicit unsupported-action diagnostic rather than approximate it silently.

Every sample records primitive, gesture, action-profile, letter, word and line
identity, exact logical spans and actual contact state. Multiple contributors
to an intentional overlap remain explicit, including shared ligature spans.
Future pressure maps and PAGE XML must refer to the same realized marks.

## 6. Vocabulary and reference-coverage workbook

First classify the existing families into directional and topological variants:
stems of different lengths, rising approaches, left/right bowls, upper/lower
turns, open/closed forms, upper/lower loops and entry/exit terminals. Rotation,
mirroring or scaling is allowed only within that family's declared semantics;
it is not a universal way to synthesize historical variants.

Construct and test continuous overturns, underturns and compound curves from
shared primitives. Investigate cross-strokes and short marks where the covered
reference letters require them. Diamonds, hooks and built terminals may be
bounded gesture combinations rather than independent learned path families.
Capitals, flourishes and abbreviations are not silently added to the starter set.

The workbook has one row per proposed capability, with:

- Source observation IDs, native crop coordinates, split and reading status.
- Primitive decomposition, gesture boundaries, travel direction and proposed
  tool action; competing hypotheses and support counts remain visible.
- Initial, fitted nominal, sampled desired and actual pen images at equal
  physical scale, alongside path/action overlays and shared parameter changes.
- At least one supported letter construction using the capability and a
  held-out transfer exercise; unsupported target symbols remain coverage debt.
- Outcome: supported, unresolved, unnecessary/null action or rejected.

Use source-admitted train/development observations for historical fitting, not
the locked test reservations. Synthetic controls test mechanics and learning
independently but cannot settle uncertain manuscript readings. Do not add a new
primitive solely because an isolated demonstration looks attractive.

## 7. Curriculum and gate amendment

Preserve S0–S4 and G0–G4 names and historical results. Introduce two **proposed**
scope-qualified checks between primitive S1 and letter S2; they are not existing
CLI commands or recorded passes:

| Check | Required outcome |
|---|---|
| `S1-gesture` | Reusable continuous gestures compile from shared primitives; segmented versus unsegmented execution agrees; lifts and overlaps are explicit; held-out construction transfer meets frozen criteria |
| `S1-action` | Each activated tool action has calibrated or declared synthetic semantics, bounded actual execution, meaningful activation and equal-scale shape/footprint evidence; real acceptance is separately qualified |

The sequence is:

1. Retain the completed fixed-tool primitive experiments as the baseline.
2. Audit reference coverage and define gesture fixtures before fitting more
   families; demonstrate continuous composition without changing tool tracks.
3. Freeze path geometry and evaluate fixed angle versus controlled rotation,
   then full edge versus intentional edge release. Test explicit finishing
   overlaps independently. Do not optimize all freedoms at once.
4. Freeze the accepted gesture/action checkpoint before learning letter recipes.
5. Learn within-word and inter-word context on those frozen lower layers.
6. Only later evaluate fatigue, reservoir dynamics and other session effects.

The constant-tool profile is an explicit valid action mode; not every letter
must manipulate the nib. A nonconstant action is activated only when a named
shape/attachment failure motivates it and held-out evidence supports it. A
claimed inactive action does not pass; a justified null action is reported as null.

Start with at most eight named gesture recipes, four primitive references per
gesture and four knots per active track. These are proposed experiment caps,
not a claim of vocabulary completeness. Existing v1 primitive/letter expansion
limits remain enforced until explicitly revised: nesting gestures must not
silently multiply the allowed primitives per letter. Record limit hits and
scope any expansion through new or revised Advances before implementation.

For each bounded experiment freeze at most three ablations, seeds 7/19/41,
and a cap of 5000 rendered targets or 1800 seconds per ablation/seed. Freeze
objective terms, numeric action/rate bounds, fitting freedoms, development
selection and disjoint evaluation cases before trials. Permit one diagnosed
revision, then issue stop/revise/proceed; a further search needs a new budget.
Count nominal, sampled and actual renders against the declared evaluation work.

All real fitting still requires live G0. Accepted gesture profiles do not
replace G1 appearance/reading or G2 execution fidelity. A changed tool footprint,
schema, geometry or profile invalidates affected lower/downstream identities.
G3 continues to govern the later session-expression experiments; it is not a
reason to postpone an intentional action essential to constructing a letter.

## 8. Validation and failure controls

- **Representation:** reject cycles, unbounded expansion, missing IDs, illegal
  topology, stale dependent hashes and residual per-letter/per-word geometry.
- **Contact continuity:** repartitioning a gesture does not add a lift, settling
  pause or pressure reset; a declared lift paints no connector. Word spaces
  cannot become ink joins through a gesture macro.
- **Tool geometry:** test fixed-angle lines in several directions, arcs,
  left/right partial-edge contacts, terminal release, orientation wrap and
  y-axis conversion. Verify translated edge endpoints, not just total width.
- **Actual execution:** compare pose/action tracking, contact schedule, swept
  footprint, endpoints, counter preservation and exact coverage. An accurate
  nominal image cannot hide an inaccurate controller result.
- **Negative controls:** use wrong orientation, swapped active edge, an
  undeclared lift, an overbuilt terminal and an erased counter. The objective
  must distinguish these from the intended exercise.
- **Learning:** compare fixed geometry/action baselines with the fitted layer;
  freeze lower layers and evaluate unseen scales, placements and combinations.
  A good image score alone cannot establish true historical motor behavior.
- **Reproducibility:** same inputs replay across fresh processes; timestep and
  arc-length refinement satisfy predeclared convergence tolerances. Persist
  code/model/tool/split identities, actual traces and negative results.

If fixed-tool paths explain the observation, do not add action complexity. If a
nominal action helps but actual execution fails, repair the supported execution
contract while holding the target fixed. If only unbounded action freedoms or
unrecorded touch-ups improve the image, reject the candidate. Do not lower the
acceptance threshold after observing the failure.

## 9. Integration, compatibility and follow-up planning

Proposed implementation homes (no new modules or APIs are created by this document):

- `scribesim/evofit/stroke_language.py` or a focused sibling: gesture/action
  schema, constraints, compilation and explicit legacy migration.
- `scribesim/curriculum/`: coverage workbook, continuous-gesture learning and
  single-action ablations; retain the current primitive experiment unchanged.
- `scribesim/pathguide/` and `scribesim/handflow/`: versioned desired/actual
  pose/contact fields using the existing planner and controller.
- `scribesim/handvalidate/` and the broad-edge sweep: direct/sampled/actual
  footprint comparisons, ownership and scope-qualified gate evaluation.

A new model schema is required. Explicit migration can wrap a continuous v1
primitive chain in a fixed-action gesture; lifts split gestures. It must
preserve v1 pixels/contact/ownership in regression tests or refuse migration.
Migration does not confer gesture-learning or historical acceptance. Old guide
readers must reject unsupported required fields rather than drop them.

Extend the canonical swept-nib implementation instead of adding an unrelated
renderer. Keep the nominal and actual paths auditable. Any future state-machine
modulation is a separate overlay on intended actions, not a rewrite of recipes
or a second owner of pressure/contact/ink accounting.

The gesture/compiler, tool-footprint, coverage/learning and evaluation work is
now scoped in Section 10 and the implementation plan. `CURRICULUM-005` depends
on the new letter-readiness evaluation; completion of an Advance is still not
evidence that its candidate passed the required runtime gates.
Later `CURRICULUM-006/007` and `HANDVALIDATE-011` must consume matching new
gesture identities; `HANDFLOW-009` retains its separate deferred ink-repair scope.

Rollback keeps `shared-stroke-language-v1`, its fixed-tool renderer mode and all
saved S0/S1 evidence. No production default changes, reference relabeling or
deletion of unsuccessful experiments is authorized by this design.

## 10. Planned Advances and delivery contract

All nine supporting records have implementation/investigation/evaluation
outcomes recorded; fitting and selected-action evaluation stop at failed
prerequisites, with unexecuted tasks explicitly unchecked. Completion is not layer acceptance. The current repository
template capability does not support typed investigation/evaluation profiles;
each record states its work kind explicitly in its Objective without upgrading
governance or inventing unsupported frontmatter. Existing completed records and
their negative outcomes are retained.

### Components and ownership

- New incubating `gesture` data-contract component: versioned shared gesture
  and action representation, compilation, ownership and explicit migration.
  It uses a focused `evofit/stroke_gestures.py` sibling as its proposed home;
  it does not take over optimization or gate evaluation.
- New incubating `nibcontact` library component: active-edge geometry and tool
  semantics integrated into the existing canonical sweep, with a proposed
  `evo/nib_contact.py` helper. This is not a separate rendering engine.
- Existing `refextract` owns source readiness; `curriculum` owns coverage and
  learning tooling; `pathguide` and `handflow` own desired/realized execution;
  `handvalidate` owns independent evaluation and acceptance records.
- Shared selectors on existing `evo` and `handvalidate` files intentionally
  identify cross-component impact. No source files move and no new runtime
  modules, APIs or component promotions are created by this planning change.

### Ordered work

| Phase | Advance | Kind | Outcome required |
|---|---|---|---|
| `td018-gesture-investigation` | [EXEMPLAR-009](../../arrive/systems/scribesim/advances/ADV-SS-EXEMPLAR-009.md) | Investigation | Source-bound vocabulary/ductus workbook, coverage debt and upstream G0 readiness decision |
| `td018-gesture-investigation` | [NIBCONTACT-001](../../arrive/systems/scribesim/advances/ADV-SS-NIBCONTACT-001.md) | Investigation | Frozen tool/actuator semantics, independent geometry fixtures, numeric bounds and feasibility decision |
| `td018-gestures` | [GESTURE-001](../../arrive/systems/scribesim/advances/ADV-SS-GESTURE-001.md) | Implementation | Versioned continuous composition, bounded action tracks, ownership and explicit legacy migration |
| `td018-gestures` | [CURRICULUM-008](../../arrive/systems/scribesim/advances/ADV-SS-CURRICULUM-008.md) | Implementation | Fixed-tool shared gesture fitting and visible held-out transfer |
| `td018-gestures` | [HANDVALIDATE-013](../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-013.md) | Evaluation | Independent S1-gesture decision with actual execution and negative controls |
| `td018-pen-actions` | [NIBCONTACT-002](../../arrive/systems/scribesim/advances/ADV-SS-NIBCONTACT-002.md) | Implementation | Shifted partial-edge footprints through the canonical sweep |
| `td018-pen-actions` | [PATHGUIDE-006](../../arrive/systems/scribesim/advances/ADV-SS-PATHGUIDE-006.md) | Implementation | Versioned desired/actual actions through the existing controller |
| `td018-pen-actions` | [CURRICULUM-009](../../arrive/systems/scribesim/advances/ADV-SS-CURRICULUM-009.md) | Implementation | Isolated frozen-path action ablations and separate finishing-pass comparison |
| `td018-pen-actions` | [HANDVALIDATE-014](../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-014.md) | Evaluation | S1-action and scope-qualified letter-readiness decision |

The implementation dependency graph is authoritative in
[Pass 15](../../arrive/implementation-plan.yaml). Investigations may finish with
unresolved real-source questions while permitting declared synthetic fixtures.
Infrastructure may be built against synthetic contracts without real G0, but
action fitting requires an accepted matching S1-gesture checkpoint. Letter
fitting requires the matching S1-gesture/S1-action readiness decision as well as
the accepted primitive checkpoint. Real fitting at every layer additionally
requires live G0 and accepted real lower-layer evidence.

`CURRICULUM-005` now depends on `HANDVALIDATE-014` as well as `CURRICULUM-004`.
`CURRICULUM-006/007` inherit the new hierarchy and preserve frozen gesture/action
identities, rather than learning new pen-action tracks as context effects.
`HANDVALIDATE-011` directly depends on `HANDVALIDATE-014` and revalidates both
new checks along with S0–S4/G0–G2. Intentional accepted actions are allowed in
these later proofs; **neutral means session effects disabled**, not erasing the
deliberate actions that construct the letter. `HANDFLOW-009` remains deferred
reservoir/optical-ink work after real layered acceptance and explicit go-ahead.

### Bounded investigations and experiments

- `EXEMPLAR-009` is one new coverage/annotation audit of at most 52 existing
  non-test reservations. It does not reopen the exhausted mask-repair search,
  acquire new sources or expose the eight locked test reservations. Import
  genuine supplied reviews only; unavailable reviewers, readings or calibration
  yield blocked G0 and a separately budgeted follow-up request, not guessed
  approvals. This upstream work prevents a circular reliance on final G0 review.
- `NIBCONTACT-001` is a code audit plus at most three fixture families and
  100 diagnostic renders or 900 seconds of automated probes, whichever comes
  first. No fitting. Its output freezes numeric action/rate, geometry/tracking
  and convergence bounds before implementation/evaluation results are examined.
  Physical calibration must be supplied or honestly replaced by declared
  synthetic semantics; historical force recovery is not an implied deliverable.
- `CURRICULUM-008/009` each use at most three predeclared ablations and seeds
  7/19/41, capped at 5000 rendered targets or 1800 seconds per ablation/seed,
  whichever comes first. Count direct, sampled and actual renders. One diagnosed
  revision is allowed under the same per-run limits, with both attempts in the
  total ledger; another revision or expanded vocabulary requires a new budget.
- `HANDVALIDATE-013/014` evaluate frozen selected candidates without optimization.
  For each evaluator, cap all replay, negative-control and convergence work at
  5000 renders or 1800 seconds per seed across the selected ablations, not a new
  cap for each replay. Recompute in fresh processes; budget exhaustion is an
  incomplete evaluation, never a pass. At most one diagnosed rerun records a new attempt
  under the same bounds; no retuning or threshold relaxation is permitted.
- For the initial action scope, pressure and speed remain constant; stationary
  dabs and pressure-dependent deformation are explicitly unsupported. A finding
  that they are necessary triggers a design/Advance revision, not a fabricated
  tiny stroke or hidden extra knob. The same applies to additional primitive
  families or expanded-letter limits identified by the coverage audit.

### Evidence delivery and decision rules

New evidence uses `shared/training/konrad_hand_recovery/stroke_gestures_v2/`
(an artifact namespace, not a claim that the gesture schema is implemented).
Each stage publishes immutable run subdirectories and a README with exact
replay commands and clickable equal-scale sample panels:

| Stage directory | Required visible/evidence product |
|---|---|
| `coverage/` | Source/decomposition workbook, hypotheses and unresolved inventory |
| `tool_contract/` | Independent expected footprints, assumptions, numeric bounds and controls |
| `language/` | Continuous segmentation, explicit lifts/overlaps and migration comparisons |
| `gestures/` | Initial/target/fitted/actual gesture practice and held-out construction transfer |
| `gesture_evaluation/` | S1-gesture checks, negative controls and scoped decision |
| `contact/` | Left/right footprint shifts and legacy full-contact regression |
| `action_bridge/` | Desired versus realized pose/contact and forced tracking-failure comparisons |
| `actions/` | Frozen-path rotation/release and separately labeled finishing-pass comparisons |
| `action_evaluation/` | S1-action report and combined letter-readiness sample index |

Later letter/context/acceptance bundles also use this new namespace; retain the
original `stroke_language_v1/` snapshots byte-for-byte. Each bundle records
code/model/tool/controller/source/split identities, permitted freedoms, numeric
criteria, actual spent budget, all failed/null outcomes and the exact accepted
scope. New evaluation code must not silently bless changed frozen dependencies.

All implementation work follows Tidy First and red-before-green tests, focused
regressions and clean-checkout replay. Read-only investigations may explicitly
record TDD as not applicable; any new investigation/evaluation tooling still
requires tests. Completion records must distinguish implementation, experiment
execution, gate outcome and genuine human review; no unobserved CI or review
evidence belongs in frontmatter.

The visible progression is practice → continuous construction → intentional
action comparison → later letter assembly. A justified null action is acceptable
for its covered inventory. A needed but unsupported action, failed actual
tracking, missing reference support or unreviewed appearance stays blocked.
Neither a completed evaluation nor a synthetic pass authorizes real letters,
fatigue, folios or a renderer-default change.

### Investigation outcomes — 2026-09-06

Both `td018-gesture-investigation` Advances are complete with local clean-clone
replay, not real-hand acceptance. The [sample and evidence index](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/README.md)
separates analytic fixtures from trained strokes and executed actions.

- **EXEMPLAR-009:** 52 non-test metadata/mask records audited, no new visual
  reading or annotation; zero admitted real inventory. Eight synthetic gesture
  hypotheses and composition/scale transfer specifications are frozen. They
  do not establish v1 primitive compatibility. Two overturns for m exceed the
  existing four-primitive letter cap; missing families/compatibility must be
  resolved or separately scoped before CURRICULUM-008 fits anything.
- **G0:** sufficient blockers were recomputed with the benchmark evaluator;
  full dataset integrity is explicitly unverified because its current validator
  decodes locked source/test pixels. This investigation does not open them.
  Missing reviews, mappings and admitted repeat calibration remain blocked;
  follow-up annotation/acquisition is proposed, not silently performed.
- **NIBCONTACT-001:** a declared synthetic tool contract was committed before
  trials. Three fixture families required 29 renders, 0.2034 seconds and no
  optimization. The existing controller copies an angle step at 2000deg/s
  rather than enforcing the frozen 180deg/s bound; active-edge state is absent
  throughout the guide/plan/controller/trajectory chain. Renderer thickness
  and pressure/optical coupling also need the already planned versioned work.
- **Evaluation finding:** the frozen global image-sensitivity minimum is 0.1.
  Hidden-connector and overbuilt-terminal controls score only 0.0102 and 0.0966.
  Preserve those failures. Later evaluation must additionally reject undeclared
  contacts/contributors and test local attachment/counter regions with criteria
  frozen before new candidates, not lower this threshold after the result.
- **Next at that investigation snapshot:** `td018-gestures`, starting with versioned representation and explicit
  compatibility. These investigations authorize neither action learning nor
  reference-grounded fitting. Physical tool calibration and all session effects
  remain outside the completed scope.

### Gesture-phase outcome — 2026-09-06

GESTURE-001, CURRICULUM-008 and HANDVALIDATE-013 are implemented and locally
merged. The compiler preserves explicit v1 compatibility and adds shared
continuous gestures, bounded action representation and owner identities.
At that snapshot dynamic actions remained non-executable; the later opt-in
realized-action bridge below adds diagnostic execution, not learned acceptance.

The bounded lesson freezes all six learned primitives and fits one shared
stem-terminal construction, choosing rise versus exit and bounded placement.
Supplied i/u recipes are probes, not learned letters. Three seeds and three
ablations yield held-out loss 0.4424 fixed, 0.3116 placement-only and 0.0 with
composition; the project-authored target is exactly in the search grid. This
does not supply the missing underturn/overturn/compound-return/loop inventory.

Independent evaluation reconstructs the frozen experiment and replays selected
checkpoints without optimization. Actual image loss, contact corridor, owner
checks, exact subdivision and timestep refinement pass in the narrow scope.
**Arc-step refinement fails:** the lifted pair's second contact entry changes
by 0.399871 mm against the frozen 0.01 mm endpoint limit, despite image change
0.022739 passing its 0.03 limit. The same failure occurs for all three seeds.
444 renders including replay/presentation, 21.39 seconds, zero evaluation
optimization/revisions; no thresholds relaxed or failed evidence replaced.

Original global negative-control failures are retained; predeclared local
blank-region and exact realized-contact/contributor checks detect them.
Synthetic oracle counter guards are not acceptance of learned counters.

**Decision: STOP / REVISE fixed-tool foundations.** Scope missing primitive
coverage and a lift/re-entry convergence repair, preserving legacy identities.
Do not start action fitting or learned letters from Advance completion alone.
Real G0/lower-layer admission and owner review remain blocked/unperformed.
See [samples, identities, measurements and replay](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/gesture_evaluation/README.md).

### Pen-action phase outcome — 2026-09-06

- **NIBCONTACT-002:** opt-in `physical-edge-v1` contact uses the existing canonical
  sweep and one physical width/thickness/shifted-edge helper. Eight independent
  fixtures pass frozen geometry/refinement criteria in 25 renders. Legacy pixels
  remain identical; changed whole-file renderer/bridge hashes make old accepted
  evidence stale for current admission. Old freezes are not rewritten.
- **PATHGUIDE-006:** versioned action plans/state subclass existing types and the
  existing controller; no second positional simulator. Actual angle/edge updates
  are bounded to 180 degrees/s and 3 fractions/s, including lifts. Forced-lag
  controls fail tracking as intended. Both arc and timestep endpoint refinement
  still fail at about 0.40 mm against 0.01 mm. Two 51-render diagnostic attempts
  retain an export/presentation repair; motion and thresholds do not change.
- **CURRICULUM-009:** bounded isolated proposal/selection/fitting infrastructure
  is implemented, but admitted rendered-lesson execution is untested/unexecuted.
  Synthetic and real attempts stop before pixels or fitting: zero renders, zero
  candidates and no justified null profile. Registration of a matching accepted
  baseline and frozen named-failure lesson remains necessary.
- **HANDVALIDATE-014:** independent pinned-identity/actual-failure admission
  evaluation repeats seeds 7/19/41 in fresh processes. Zero renders, no optimizer,
  no selected-action metric/control claims. The unexecuted candidate tasks stay
  unchecked; the only current readiness outcome is **STOP / REVISE**.

Synthetic tool diagnostics do not replace missing learned returns/loops, repair
lift/re-entry, refresh S1-gesture, or authorize real G0/G1/G2. Scope those fixed-tool
repairs first, then run action experiments and freeze a new candidate evaluation.
See [layered sample index, boundaries and reproduction](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/action_evaluation/README.md).
