# TD-018 Addendum E — Neighbor-dependent boundary construction

Status: **design revision requested; construction hypotheses require review**.
Date: 2026-09-10. Supersedes the next-step hypothesis selection in
[Addendum D](TD-018-addendum-d-stroke-context-transitions.md), not its frozen
evidence, exact-null requirements or execution gates. Documentation only: no
new geometry, rendering, contact changes, fitting or physical allowance.

## 1. What we learned and what changes

The owner reviewed a few unspecified CURRICULUM-016 nominal examples and found
them indistinguishable. Preserve [that feedback](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/demonstrator/owner-feedback-001.json)
without inventing a complete 48-example review or numerical ties.

The old hypotheses rotated terminal handles by ±1 degree while retaining the
same construction and inter-letter lifts. Their selector assigned a sign from
a distance bin or following entry class; it did **not** establish a task that
the changed stroke solved. The infrastructure passed structural checks, but
that does not establish useful contextual lettering. Enlarging those rotations
is not the next experiment. H1–H3 remain paused; do not send them to physical
validation or fit their outputs.

**New question:** given two neighboring stroke programs, is there a useful,
admissible boundary construction that requires a different departure from the
left letter and/or approach into the right one? If not, preserve both letters.

The construction needs an explicit purpose, not simply visible variation:

- Maintain the canonical separate-letter boundary when it already works.
- Where the intended lettering permits it, continue into a compatible receiving
  stroke without an unnecessary lift, while preserving recognizable letters.
- Later, investigate optical clearance independently if a measured crowded
  boundary calls for it. Do not invent crowding in the widely separated pilot.

These are proposed design purposes, not proof of historical scribal behavior.
Connection is a stylistic option requiring owner review, not a universal rule.

## 2. Why the boundary must be designed jointly

The frozen programs end with a descending stem at the baseline. n/u begin with
a descending stroke at the x-height; m begins with a rising stroke at the
baseline. The [port audit](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/investigation/README.md)
records separated endpoint gaps of 3.3924–6.2764 mm. Existing boundaries lift.
These are not already coincident ports that can be joined by changing a flag.

A boundary solution must therefore describe three coordinated pieces:

1. The left letter's **departure construction**, possibly replacing a declared
   terminal subspan rather than rotating its last control handle.
2. The **transfer**, explicitly pen-up or an owned pen-down path.
3. The right letter's **receiving construction**, possibly replacing a declared
   prefix while retaining its continuation into the canonical body.

The same boundary decision informs both letters. Independent left/right edits
must not produce mismatched meeting points or incompatible tangent directions.
Nor may a connector be an unowned shape painted over completed glyph images.

With a real lift and no identified clearance or style requirement, a previous
letter does not automatically require a different visible next letter. Thus
unchanged lettering is an explicit successful resolution, not a missing feature.
Later natural variation is a different layer from purposeful context selection.

## 3. Layered abstraction and proposed contract

Keep the stroke-language approach:

**canonical strokes → letter skeleton + construction sites → boundary request
→ shared construction family → derived stroke program → motion → ink**.

### Letter skeleton and construction sites

Preserve the upright n/u/m reference and canonical bytes. Identify protected
body anchors, stem corridors, baseline/x-height constraints and existing internal
joins. For each proposed construction site, inventory:

- Canonical occurrence and cubic parameter interval to retain or replace.
- Attachment position and directed tangent into the retained body.
- Whether an extremum, stem foot or internal corner belongs to the editable
  site; semantic entry/exit labels alone grant no permission.
- Admissible incoming/outgoing contact state and fixed action identity.
- Region available for the new path and finite-nib clearance/overlap ownership.

Replacing a suffix/prefix requires an exact canonical split and a shared attach
point. It does not authorize moving the entire stem or silently omitting part
of the letter. The site's numeric parameter ranges and spatial envelope must
be audited and approved before implementing any non-null construction.

### Boundary request and result

Proposed request fields (not a released schema):

| Input | Purpose |
|---|---|
| Left departure site / right receiving site | Canonical identities and allowed subspans, not arbitrary word keys |
| Relative port geometry and reachable regions | Decide geometric feasibility rather than classify by letter name alone |
| Protected bodies and finite-nib obstacles | Reject collisions, damage or unsupported overlap |
| Boundary policy | Separate required, connection permitted, BOS/EOS; no implicit join |
| Fixed tool/action state | Preserve current nib, pressure, angle and speed limits |

Return either `unchanged_separate`, `candidate_construction`, or
`unsupported_with_reason`. A candidate records the family, both substitutions,
transfer path, attach ports, contact runs, letter/gesture/action owners, overlap
contributors, bounded parameters and the specific requirement it addresses.
Only an approved consumer may later turn it into execution.

No full words, fixture/seed IDs, per-instance residuals or hidden alternate-glyph
lookup tables in selectors. Recipe/site identities remain legitimate provenance.
Finite families replace finite spans; no recursive expansion or bypass of the
old six-occurrence cap. A needed cap/topology change requires a versioned migration
decision, not an exception hidden in an adapter.

### A letter with both neighbors

Resolve incident boundary proposals against one immutable skeleton, then check
their replacement intervals and constraints together. Disjoint valid changes
may compose; competing edits on one span reject or use an explicitly approved
joint construction. Do not let a left-to-right mutation order decide the result.
Pairs can establish one boundary only. A provenance-approved triple is required
before claiming two-sided interaction within one letter; none is admitted here.

## 4. First proposed construction study

Narrow the design study to **one possible connecting family and one null family**.
Do not build a new alphabet or a large visual preference grid.

### Family S — canonical separate boundary

Complete the existing left stroke, lift, transfer in air, and begin the canonical
right stroke. Geometry and event behavior remain exactly reproducible. Use this
for BOS/EOS, mandatory separation, incompatible sites and any rejected candidate.
Unsupported requests must report why they fell back, not silently look connected.

### Family P — terminal turn into a receiving rise (investigation only)

Candidate situation: the left letter finishes with a descending stem and the
right construction offers a rising prefix. Investigate a coordinated terminal
turn, owned connecting path and receiving-rise prefix. The intended purpose is
continuous approach into an existing upward construction—not random slant.

Important geometric constraint: simply appending a smooth turn to a downward
stem **after it reaches the baseline** can drive the curve below that baseline.
The investigation must instead locate a permitted terminal suffix before the
foot, determine whether a turn can preserve the required baseline extremum,
and attach to a permitted prefix of the receiving rise. Both are explicit body
exceptions, not already approved edits. If preserving the recognizable foot,
upright body and receiving gesture is impossible, this family is unsupported.

The substantial existing gaps may make this family unsuitable at the frozen
advances. Check that first. Do not span the gap with a long decorative connector
just to make the change visible. Do not compress spacing secretly to help it fit.
If only a changed layout could support it, stop and propose a separately reviewed
layout study with unchanged-form spacing controls; it is not the current pilot.

### Minimal causal examples

| Existing exposed example | Purpose, not a rule keyed to the string |
|---|---|
| nm | Candidate descending departure → rising receiver |
| nn | Same left n, but descending receiver at x-height: negative control for Family P |
| um | Reuse the family with another descending departure; inspect the different terminal context |
| mm | Same rising-receiver class but a larger gap: feasibility control, not guaranteed reuse |
| isolated n/u/m | Exact reference controls, no boundary adaptation |

Seven existing strings suffice for this investigation. A matching entry class
alone is insufficient: relative geometry, attachment sites and protected regions
must also permit the construction. No sealed text inspection or new triple use.

## 5. What must be frozen before a new demonstrator

The investigation must produce a site/feasibility table, not an executable
connector guessed from this document. For each admitted family freeze:

1. Exact replacement intervals, retained anchors and directed attach tangents.
2. Maximum excursion, length, curvature/reversal policy, allowed overlap area
   and finite-nib clearance envelope; justify these from construction constraints.
3. Baseline/x-height behavior, protected stem/shoulder corridors and all allowed
   body exceptions. Preserve existing thresholds; propose additional metrics
   prospectively rather than fit limits to failed samples.
4. Explicit contributor ownership and contact events at both splice points.
5. A finite deterministic parameter choice and reject conditions—no search.
6. Exact-null comparison and complete representation/refinement/renderer policy.

No new numeric geometry allowances are granted here. The old ±1-degree/0.04-mm
contract remains frozen for its historical H1–H3 experiment; it is neither widened
nor falsely reused as authorization for a new construction.

## 6. Comparison and evaluation design

At most four **newly named** arms; do not redefine the old H0–H3 identities:

- B0: canonical forms and canonical pen-up transfer.
- B1: admitted departure/receiving substitutions with pen-up transfer, only if
  both independently complete legible letter constructions without the connector.
- B2: transfer-only with canonical forms, only if their unchanged ports permit
  that transfer. The present audit does not establish this; unsupported is valid.
- B3: jointly constructed departure, owned transfer and receiving prefix.

Missing arms are informative. Do not invent an incomplete form-only letter or
change the supposedly unchanged body to make a transition-only panel possible.
Use matched advances; any later layout intervention must be separately labeled.

Each example should state: **what the neighbor permits/requires, which canonical
spans change, which body anchors remain, and why separation was retained or
replaced**. Show the original whole letters and nominal construction side by side
before any path/port overlay. Zoom explains the mechanism; it cannot be the sole
source of perceived usefulness. If no arm is both feasible and useful, stop.

Evaluation stays layered:

| Gate | Required evidence |
|---|---|
| Representation | Exact source lineage, legal splices, truthful ports/contact/ownership, no body leakage |
| Causal explanation | Same boundary sites/state give the same construction; incompatible receiver or region rejects it |
| Nominal usefulness | Owner can identify a relevant construction change and still recognizes the upright letters; no forced ranking |
| Mechanics | Independent full finite-nib, local body, event, speed and acceleration checks on actual motion |
| Transfer | Reuse frozen families on separately admitted compositions, not renamed training examples |

No-contact-change, wrong receiver, oversized gap, invalid tangent, false smooth
reversal, missing contributor, overlapping substitutions and word-keyed rules are
required negative controls. Removing a lift is not automatically a quality win;
readability, restraint and owner style preference remain decisive.

## 7. Workflow, preservation and generalization

CURRICULUM-016 stays in progress on a design-revision path. The next work package
is **read-only construction-site and reachability investigation** for S/P and the
seven examples above. Owner review of the sites, proposed bounds and connection
style is required before contract implementation or any new preview protocol.
Generate scoped follow-up advances when implementation planning is requested;
do not pretend this design revision implements or accepts Family P.

Use a new versioned construction contract/artifact namespace if the investigation
supports it. Do not mutate `stroke-context-spans-v1`, its prepared documents,
the nominal packet or either owner feedback record. The current physical schedule
of 1,152 runs/4,104 renders is **not applicable to a new construction**: re-enumerate
and approve only after a useful new demonstrator exists. HANDVALIDATE-025/026
remain gated, with no inherited new time/render allowance.

Before word-level work, audit contrasting families such as a closed bowl,
an ascender/descender and a detached mark. They may need different sites and
construction families; reject rather than force them into n/u/m's topology.
The transferable abstraction is shared construction with explicit constraints,
not a claim that one turn-to-rise family writes every letter.

Keep fixed tool/actions and existing accepted foundations. Pressure modulation,
fatigue, correlated natural variation, ink depletion and fitting remain later.
This revision changes documentation/governance only; no new samples or execution
are authorized, and no commit or merge is requested.

## 8. Validation of this revision

`arrive plan check`, `arrive sync agent-rules --check`, changed local document
links and `git diff --check` pass. Exact read-only reinspection of GESTURE-004
report `d7eb422948f7de6696221d2f026559ca603fb84a95e713e9e6cdce5aa95a6b75`
passes, including the frozen original/recovery source and artifact checks.
No behavioral tests, geometry generation, nominal images, controller runs or
fitting were performed for this documentation revision. Changes are uncommitted.
