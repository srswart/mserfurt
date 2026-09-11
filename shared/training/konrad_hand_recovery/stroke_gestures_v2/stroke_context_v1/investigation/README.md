# GESTURE-004 — investigated spans and boundary proposal

Status: read-only investigation complete; **owner review pending**. This is not
permission for GESTURE-005, physical runs, fitting, or acceptance. C006's old
width/spacing rankings remain paused. Existing changes remain uncommitted.

## Findings

The pinned [audit report](snapshot-001/report.json) verifies 12,771 original
artifacts and 2,455 recovery artifacts against their saved manifests, plus the
frozen source contracts and independent C006 inspection. Its SHA-256 is
`d7eb422948f7de6696221d2f026559ca603fb84a95e713e9e6cdce5aa95a6b75`.
The full 1,464-case independent measurement is **reused**, not repeated here.

### Canonical spans, not arbitrary thirds

Each listed occurrence contains cubic 0, parameter range [0,1]. Coordinates and
all four control points, directed endpoint tangents, canonical hashes, gesture
owners and overlap contributors are recorded per occurrence in the report.

| Letter | Ordered primitive occurrences | Proposed semantic overlap |
|---|---|---|
| n | 0 stem; 1 rise; 2 upper-return; 3 stem | Entry: 0; exit: 3; protected body: 0–3 |
| u | 0 stem; 1 lower-return; 2 rise; 3 stem | Entry: 0; exit: 3; protected body: 0–3 |
| m | 0 rise; 1 upper-return; 2 stem; 3 rise; 4 upper-return; 5 stem | Entry: 0; exit: 5; protected body: 0–5 |

These are anatomical labels, **not independently editable pieces**. Every span
also contributes to the body. A cubic handle influences its entire cubic;
changing a terminal handle is not a change confined to a small endpoint crop.
Default permission is therefore zero edits. Baseline/x-height endpoints, internal
join anchors, all canonical body control points, actions and advances are frozen.
Any future exception must name a derived occurrence and control point explicitly.

Each letter has one continuous contact run. The internal stem-to-rise reversal
in n, rise-to-stem corner in u, and between-overturn corner in m keep contact.
Their existing gesture overlap ownership remains authoritative; it is not
cross-letter connector ownership. Smooth boundaries retain directed tangents;
corners must not be mislabeled smooth merely because endpoints coincide.

### Actual contact and gaps

Ten identity saved seed-7 traces were read: isolated n/u/m, six training pairs,
and the placed mu regression. Isolated letters have **zero lifts**; each pair
has exactly **one lift and one landing**. All ten contain upward pen-down
events. Upward movement is therefore not evidence of lifting the pen.
nu and uu have canonical geometry evidence here, but no identity case in this
C006 physical contract; no substitute trace or new execution was manufactured.
The mu trace retains its recorded placement shift, rather than being silently
treated as an origin-aligned fixture.

Air events identify the departure/arrival gesture at lift. Some intermediate
air events have `from: null`, with the landing owner retained. The audit exposes
both forms; it does not infer continuous cross-letter ink ownership from them.
This existing air representation is not an acceptable implicit ownership model
for a future pen-down connector.

| Previous letter | Following n/u: endpoint gap | Following m: endpoint gap |
|---|---:|---:|
| n | 4.8743 mm | 3.3924 mm |
| u | 4.8941 mm | 3.4208 mm |
| m | 6.2764 mm | 5.2099 mm |

These are canonical endpoint distances at 3.5 mm x-height, not measured ink
clearances or mechanical feasibility scores. All endpoints are separated; none
is an already-compatible coincident join. n/u start at the x-height with a
descending stem; m starts at the baseline with an ascending rise. All three
finish with a descending stem at the baseline, sharing the same exit direction.
Consequently a previous-letter **class alone cannot distinguish n/u/m**.

## Scope proposed for owner review

Recommend a first **lift-preserving local-form contract**, not forced joins.
Investigated transition families: pen-up transfer (existing baseline), pen-down
join (unsupported), pen-down retrace (unsupported across letters). Keep the last
two as explicit rejected intents until a separately reviewed path/ownership and
measurement design exists. Intra-letter return motion is already supported and
must not be replaced by a lift.

### Context key and state

Use current recipe + previous exit class/state or BOS + following entry
class/state or EOS + explicit transition intent. State includes relative port
position, directed tangent, contact intent and fixed action identity. Never use
word, fixture, seed, or occurrence residuals as rule selectors. Occurrence IDs
are provenance, not selector keys. Unknown letters, word/line boundaries,
unresolved states, or unsupported intents reject or explicitly retain baseline.

For a bounded first test, propose a geometric previous-state bin: baseline
departure-to-current-entry horizontal distance <=1.2 x-height versus >1.2.
This separates the more distant m departure from n/u without naming a previous
letter. It deliberately does **not** create arbitrary n-versus-u alternatives.
The bin is a proposed design choice, not a learned threshold or acceptance metric.
Following state distinguishes stem-entry from rise-entry. BOS/EOS disable the
corresponding intervention. Fixed-action states must match exactly.

Because the baseline lifts, any resulting form change is a hypothesis about
anticipatory construction, not an established mechanical necessity or historic
scribal practice. If it is unhelpful, retain separate lettering rather than
forcing perceptible deformation.

### Four deterministic hypotheses maximum — not yet approved

| Hypothesis | Derived exception | Deterministic intervention |
|---|---|---|
| H0 context off | None | Exact existing compiler/plan path; no rebuilt approximation |
| H1 entry only | First occurrence, cubic 0, control point 1 | Rotate entry handle +1 degree for the near previous-state bin, -1 degree for far; zero at BOS |
| H2 exit only | Last occurrence, cubic 0, control point 2 | Rotate terminal handle +1 degree for following stem-entry, -1 degree for rise-entry; zero at EOS |
| H3 entry + exit | Union of H1 and H2 | Apply both independently; no additional interaction coefficient |

Angles use canonical y-up coordinates and endpoint-relative handle vectors.
Keep handle length fixed, endpoints fixed, and maximum handle displacement
**0.04 mm** at the fixed x-height; exceeding the cap rejects, never clips or
retunes. Only the finite angle set {-1,0,+1} is proposed. No changes to interior
occurrences, other handles, advances, baseline/x-height anchors, pressure, nib,
speed cap, target images or existing mechanical thresholds. These are explicit
**body exceptions requiring approval** because the entire first/last cubic is
affected. Preserve canonical primitives; derive occurrence geometry with lineage.

The sign choices are hypotheses, not preferred handwriting. There is no promise
these small upright-preserving changes will look meaningfully different. If
owner review again finds them indistinguishable, stop and revise the design—do
not automatically increase angles, fit the old grid, or award acceptance.

## Exposure and examples

The read-only geometry shortlist is narrowed to **12**: n/u/m plus all nine
existing pairs. A hash-pinned scan of 32 spec/metadata files finds no nuu/uuu/muu
mentions, but cannot establish complete historical non-exposure or all possible
reservations. Those three triples remain **unadmitted** and were not compiled,
rendered or opened. Before using them, approve their designation as design-only
probes; never subsequently call them unseen transfer tests. The separate six
sealed C006 strings remain reserved; their pixels/traces were not opened.

Planned annotation specifications, not generated examples:

- Isolated n/u/m: label every canonical occurrence, cubic index/range, protected
  anchor, internal corner, overlap contributor and continuous contact run.
- nn versus mn, with the second n aligned: previous-state intervention with
  following EOS fixed. nuu versus muu is a later design-only middle-u test with
  following u fixed, only after triple admission. nuu versus uuu is an expected
  same-bin negative control, not a forced difference.
- un versus um, with the first u aligned: following-state intervention with
  previous BOS fixed. Separate H1/H2 before considering H3.
- Pair boundary: show exit/entry arrows and actual lift/air/landing timeline.
  No transition-only connector panel: that arm is geometrically unsupported.
- Future displays retain fixed-scale full-frame actual/desired images and use
  synchronized zoom/difference solely as labeled diagnostics, never metrics.
  Geometry-only sketches must be explicitly distinguished from physical ink.

## Required evaluation contract and resources

GESTURE-005 should first provide exact null checks: compiled control points,
owners, contact runs, action bundle, event timing and unchanged outputs under the
existing four refinements. Numerical closeness is insufficient for H0. No fresh
physical run is authorized merely to establish this adapter contract.

Before physical evaluation, freeze new measurement definitions for handle/whole-
cubic displacement after declared placement removal, body/anchor preservation,
directed port changes and two-sided selector causality. For any future connector
also define full finite-nib containment, ownership of the complete cross-letter
path, retrace overlap bounds and exact boundary event accounting. Missing metrics
are design work, not waived gates. Existing targets and criteria stay unchanged.

Adverse controls must reject body edits outside the exception, wrong/degenerate
ports, swapped previous/following state, word-keyed rules, forged lineage, fake
lifts, false smooth reversals, unowned connectors/retraces, missing contributors,
duplicate events, changed frame/DPI/crops and desired pixels presented as actual.
Assess representation, mechanics, causal effect, owner usefulness and held-out
transfer separately. No new physical or appearance acceptance is claimed here.

Resource inventory (estimates, **not allowances**):

- Next contract work: <=12 strings ×4 hypotheses =48 base geometry documents;
  <=192 documents across four refinements, zero raster/controller calls.
- If triples are later admitted: <=15×4×4×3 seeds×2 processes =1,440 physical
  executions. Up to five images each gives 7,200 image calls before controls;
  reserving 24 explicit control images would make 7,224. A protocol must replace
  this conservative envelope with an exact valid-arm schedule and time estimate.
- No time estimate for new geometry is measured yet; do not infer that the old
  allowance will suffice. A small separately budgeted calibration would itself
  require prospective authorization. No remote GPU/provider run is introduced.
- Old remaining seed allowances are unchanged: seed7 582.1848200419918 seconds/
  3,426 renders; seed19 988.4159828750417 seconds/3,426 renders; seed41
  579.0667824570555 seconds/3,259 renders. No reset or automatic spending.

## Reproduction and review gate

Run from the repository root:

```sh
.venv/bin/python -m pytest -q tests/test_stroke_context_audit.py
.venv/bin/python -m scripts.stroke_context_audit inspect --report-sha256 d7eb422948f7de6696221d2f026559ca603fb84a95e713e9e6cdce5aa95a6b75
```

The inspector re-derives the same audit under the execution/raster guard and
compares exact report content; it is a reproducibility check, not an independent
second implementation of the physical checker. Snapshots refuse overwrite.

Local results: exact pinned reinspection passes; 132 tests pass across the new
audit and existing context-contract/dimension/recovery/physical test modules.
ARRIVE plan, generated-rule, local-link and whitespace checks pass. No provider
CI or merge is claimed. The report is approximately 84 KiB; no new trace/image
collection was generated.

**Owner decision needed:** approve or revise the overlapping span/body model,
lift-only initial scope, geometric state selector and explicit bounded handle
exceptions/H0–H3 before GESTURE-005. Triple admission and any physical/visual
generation protocol remain separate decisions. No approval is inferred from
authorizing this investigation.
