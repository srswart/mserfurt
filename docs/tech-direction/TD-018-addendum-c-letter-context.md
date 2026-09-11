# TD-018 Addendum C — Neighbor-conditioned stroke context

Status: **P1/P2a and bounded P2b mechanical evidence cleared; owner pauses P3 width/spacing preferences and downstream selection on 2026-09-10.**
The current direction is [Addendum D — neighbor-aware stroke forms and transitions](TD-018-addendum-d-stroke-context-transitions.md).
This document and all pinned affine-pilot artifacts remain preserved history,
not instructions to resume ranking, widen bounds or fit. Later sections record
the sampler, storage recovery and complete independent mechanical inspection;
their historical intermediate failures are not the current mechanical verdict.
Scope: CURRICULUM-006's first synthetic n/u/m experiment. This narrows its earlier
16-rule/join/word proposal; it does not authorize a broad word learner.

## 1. What we want to learn

We have approved shared strokes, n/u/m constructions and fixed placements.
Now ask: **does changing a letter's strokes in response to its neighbor produce
a preferred, still-readable result that spacing alone cannot explain?**

The first pilot conditions on the following letter only. Previous-neighbor
effects, joins, ligatures, word-boundary rules, new letters, active pen actions,
ink depletion and fatigue are deferred. A spacing-only or unchanged answer is
valid evidence; do not force visible deformation to claim learning.

[CURRICULUM-006](../../arrive/systems/scribesim/advances/ADV-SS-CURRICULUM-006.md)
tracks implementation. The [machine-readable proposal](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/preparation-001/protocol-proposal.json)
contains exact proposed grids, strings, bounds and pre-execution gates. Its
approval flags are false; null preference/objective hashes are blockers, not
defaults an implementation may fill silently.

## 2. Current-source readiness audit

The [readiness audit](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/preparation-001/readiness-audit.json)
rechecks all 1,808 H024 artifact hashes, exact inventory, current frozen execution
identities, 206 core identities and candidate/report-bound owner approval.
It reuses the pinned independent raw-reader receipt; it does not repeat the
seven-minute raw reconstruction or execute any controller/renderer.

| Layer | Evidence now | Remaining boundary |
|---|---|---|
| Primitive geometry | Four frozen primitives: stem, rise, upper-return, lower-return; used in H024 | No current-source per-primitive consumption clearance for new contextual transforms |
| Gestures/connections | Stem, overturn, underturn; continuous pen-down intra-letter topology and H024 mechanical proofs | No admitted nonidentity context alternatives |
| Pen action | Fixed full edge, 0.45 mm nib, 40 degrees, pressure 0.5, speed cap 12 mm/s | Evidence is fixed-action execution, not active-action learning or reusable historical S1 approval |
| Letters/placements | Known n/u/m/mu and six held-out pairs have mechanical/replay evidence and owner KEEP | H024 still withholds S2/real/context permission; appearance is not a clearance reader |
| Context | Empty letter/word rules; only one recipe per letter | Connected-v1 intentionally rejects even a zero-displacement context rule |

Live `finer_scales.require_readiness` and `standalone_stem.require_readiness`
both reject their pinned historical reports, using their own declared legacy
fixed-tool scopes. Three recorded sources differ from current code:
`gesture_actions.py`, `stroke_gestures.py`, and `stroke_language.py`. The older
candidate/contract also is not the approved connected-v1 candidate. Preserve
those reports and rejected readers; changing their pins is not a repair.

**First implementation work package:** define a separately versioned,
consumer-pinned current-foundation clearance contract. Audit coverage and
lineage of primitive, gesture, fixed-action and letter occurrences in the
already verified H024 traces. Reuse applicable evidence; list uncovered
requirements explicitly and measure only justified gaps under a new budget.
Do not automatically rerun the whole historical curriculum. Do not issue
clearance from a report's aggregate pass or owner approval alone.

Its admissible claim is narrowly scoped synthetic approved-appearance
preservation, not independent style accuracy or historical-hand acceptance.
Any new permission requires the explicit approved contract and matching lower
layers. A new flag named 'experimental' cannot bypass missing fitting clearance.
Non-fitting scaffold work with declared unaccepted inputs remains distinct.

### P1 clearance result — 2026-09-09

The owner-authorized [readiness implementation and snapshot](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/readiness-v1/README.md)
now provide this versioned consumption contract. All 240 archived runs cover the
four primitives, three gestures, one fixed action and n/u/m recipes in every
seed/process/refinement inventory. Current compilation is compared to raw
occurrence ownership and contact samples; internal subdivision is explicitly a
derivation, not newly learned geometry. The pinned H024 physical-reader receipt
is reused, not rerun. All 1,808 source artifacts remain verified.

**Cleared:** exact unchanged baseline reuse within the ten observed fixtures,
original frame and fixed tool/refinements. **Not cleared:** arbitrary isolated
primitive use, new text or nonidentity transforms, context fitting, or general
S1/S2/real-hand admission. The consumer must pin the readiness report and request
the exact candidate, letters, tool and baseline-only purpose. Source changes,
edited authority and report-only promotion fail closed. Legacy readers still
reject their historical reports; no old pins or thresholds are changed.

No baseline inventory gaps require another experiment. Five explicit remaining
gaps concern transformed occurrences, new context coverage, preferences/objective,
execution authorization and broader layer admission. Nonidentity limits and the
experiment in sections 3–6 remain proposals; preparation-001 is an immutable preparation-time record.
P1 adds zero controller executions, renders or fitting evaluations.

## 3. Minimal context language — approved geometric bounds

The baseline library remains byte-frozen: four primitives, three gestures, one
fixed action and n/u/m recipes. The baseline file hash is
`01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd`.

Six rule slots use **current letter × following entry class**:

- Current letter: n, u or m.
- Following entry: stem-entry for n/u; rise-entry for m.
- Final letter/no matching rule: exact identity. Duplicate matches are errors.
- Unknown letters, whitespace and multiword input are outside this pilot.
- No previous-letter selector, full-word key, position-specific residual or
  per-occurrence learned parameter. Repeated letters share the same rule.

The owner approves these bounds for P2b geometric/frame validation. This is not
physical-motion or appearance acceptance and does not authorize fitting:

| Parameter | Approved discrete values | Meaning |
|---|---|---|
| Horizontal scale | 0.97, 1.00, 1.03 | Slight width adaptation of the entire composed letter |
| Advance delta | -0.05, 0, +0.05 normalized units | At 3.5 mm x-height, at most 0.175 mm placement change |

Let x0 be the letter's canonical entry x, before placement. Apply
`x' = x0 + s * (x - x0), y' = y` to every composed cubic control point.
Transform and renormalize port tangents with the same matrix. This changes
intra-letter stroke geometry while preserving exact vertical landmarks and
coincident connections. Stem/rise proximity, slant, counters, finite-ink overlap
and actual mechanical behavior must still be checked; they are not guaranteed
by the affine formula. The physical nib/ink is never stretched.

Advance is independent: do not silently compensate it for width changes.
The final letter is identity; a preceding letter's advance may translate it.
Strip this placement translation when measuring contextual stroke differences.

### Compiler and lineage boundary

This is a **new opt-in composition contract**, not use of the old nonempty
`letter_rules` path. The existing connected-v1 validator continues rejecting
context. Do not silently raise its primitive budget or duplicate twelve
width-specific canonical primitives into its eight-primitive inventory.

Create derived occurrence views after gesture composition, before physical
planning, with canonical primitive/gesture/action/recipe hashes, rule ID,
context-program hash, transform and derived-geometry hash. Keep original text
spans, occurrence IDs and declared ownership; recalculate physical overlap and
timing from the transformed geometry. The reader verifies every derivation.
No hidden per-word recipe or action cache is allowed.

Proposed implementation starts in opt-in scripts/adapters owned by the existing
curriculum, gesture and handvalidate components. No new component is needed.
Freeze an explicit compiled-geometry-to-plan interface and independent reader
before physical use; current `action_bundle` cannot be assumed to consume these
derived views. Avoid editing frozen core modules merely to switch on rules.
If a core change proves necessary, plan fresh identity-specific evidence rather
than modifying old source manifests.

Identity context must reproduce canonical geometry, ownership, timing and
saved known-base pixels exactly. Test this before considering nonidentity rules.
Short-circuit identity transforms rather than round-tripping coordinates through
affine arithmetic; metadata for the context contract belongs in a separate
manifest when necessary to preserve the original null trace representation.

### P2a implemented contract — identity only

The owner authorizes the context/lineage contract and exact unchanged-output
checks, with all changes left uncommitted. This implements the null-contract
portion of P2, not its nonidentity mechanical experiment. No new frame, physical
run, preview budget or training target is authorized by this work.

`scripts/letter_context_contract.py` defines `letter-context-null-v1`. A program
contains only `schema_version`, the exact canonical candidate object hash and
`rules`. Each rule contains a deterministic `id`, `current_letter`,
`following_entry_class`, `width_scale=1.0` and `advance_delta=0.0`. The six cells
in this section define legal selectors; duplicate cells, unknown fields,
per-word keys, nonfinite/boolean parameters and nonidentity values are rejected.
Rules are normalized into ID order. Empty or absent matching rules and the final
letter use identity. No nonempty rules are added to connected-v1 itself.

`compile_context(candidate, fixture, program, refinement)` returns the exact
canonical compiled document plus a separate lineage sidecar. The sidecar binds
each occurrence's original owner/span/contact-run metadata, canonical and
execution primitive hashes, gesture/action hashes, canonical and placed recipe
hashes, resolved rule, identity transform and source/derived geometry hashes.
The root binds the whole context program, fixture, refinement and execution
model. Internal subdivision preserves its canonical parent hash while naming
the exact derived primitive hash. No coordinate arithmetic is performed for
identity, and sidecar metadata never changes physical owner dictionaries.

`scripts/letter_context_evidence.verify_document` reconstructs the expected
geometry and lineage from the frozen candidate without calling the new context
compiler. `prepare_null_plan` requires that verification before passing the
unchanged compiled strokes to the existing curve-tangent planner. Its outputs
are the retimed action bundle and timing record, not an executed trace. Any
future nonidentity compiled-geometry-to-plan adapter needs a new approved
contract; this adapter cannot consume transformed geometry.

Both context-off and six-identity modes are compared to the direct existing
compiler/planner for every original H024 fixture/refinement. The read-only
evidence reader then binds these exact plans, corners/arrivals and owner maps
to all archived traces, checks archived first/replay pixel/trace identity and
compares known-base pixels to the approved registry. This proves exact null
**input equivalence and archived-output binding**, not a fresh physical null
replay or newly rendered image equality. No output is copied and relabeled as
new. All six rule cells have resolver tests; n followed by m is not in H024's
archive and gains no physical coverage from its schema test.

The [null-contract snapshot and usage guide](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/null-contract-v1/README.md)
record the externally pinned P1 dependency, complete comparison inventory,
source/code identities and explicit permissions. Historical P1 and preparation
snapshots are unchanged. P2b's nonidentity variants/frame mechanics, then P3's
preferences/objective and execution freeze remain prerequisites for fitting.
All 80 mode/fixture/refinement comparisons pass; 240 archived runs and 480 image
bindings verify, with 24 exact known-base reference matches. A fresh-process
read-only reinspection matches the full pinned report. All 97 focused tests pass.

### P2b bounded geometry and frame preflight

The next owner request approves the listed width/advance grid and context frame
`[-3, 30, 2, 13]` mm. `letter-context-bounded-geometry-v1` is a separate version;
P1/P2a code and snapshots are unchanged. The old nonempty-rule rejection remains.
No canonical primitive, gesture, fixed action or letter recipe is modified.

`scripts/letter_context_variants.py` derives composed occurrence views using the
specified horizontal affine map, with exact vertical coordinates and separately
accumulated preceding advances. Identity avoids coordinate arithmetic. The final
letter has no local width change but may inherit preceding placement. Sidecars
bind original owners, source and derived cubics, canonical primitive/recipe
hashes, rule resolution, anchor, displacement and normalized entry/exit tangents.
The independent reader reconstructs this map before the new planning adapter
samples derived curves and recomputes action plans and curve-tangent timing.
The null path still returns the original action bundle exactly.

Preflight enumerates all shared-rule assignments on unsealed texts: 54 pair
variants, 342 development-triple assignments, 27 prior pair probes, three isolated
controls and four original-frame known regressions. Repeated selectors share
parameters: mmm has nine assignments, not 81 independently adjustable occurrences.
No sealed triple is compiled, rendered or scored. Known regressions stay identity.

The finite-nib proof uses the Bezier control hull plus the unchanged physical nib
rectangle. Per-letter local windows are the union across every permitted
assignment and internal subdivision, plus the original 0.8 mm padding, frozen
before evaluation. Connected-port, tangent, declared finite-overlap and vertical
landmark checks use the existing contracts. Desired motion uses unchanged speed,
acceleration and discontinuity limits. These are geometric/planned proofs, not
actual tracking, actual overlap pixels, physical replay or preference evidence.

The proposed next physical gate contains 244 cases per process: 54 training pair
variants × four refinements, three isolated controls × four, and four original
known regressions × four. First/replay gives 488 runs per seed (7/19/41). Actual,
desired and overlap renders, 54 actual presentations per process and an eight
render control allowance give a 1,588-render planning bound per seed. Development
and probe physical checks follow one frozen selection; they are not silently
admitted by this pair gate. The concrete runner, independent reader and controls
must freeze before the first physical run.

The original 30-minute combined seed proposal has not demonstrated capacity:
H024's slowest 80-run seed took 351.94 seconds; scaling by run count gives
2,146.86 seconds (35.78 minutes), before headroom. This is a planning estimate,
not a new benchmark or an actual timeout. A 25% reserve rounded to five minutes
suggests **45 minutes per seed**, keeping the 5,000-render ceiling and zero retries
or revisions. **The owner approved this cap on 2026-09-09**, for seeds 7/19/41
including first/replay; see the [separate approval record](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/bounded-geometry-v1/budget-approval-001.json).
This grants budget approval only: the concrete runner, independent reader,
negative controls and ledger must still freeze before execution. All P2b validation/
preview debits must carry into the combined C006 seed accounting, not reset per
arm. The preflight cannot grant itself this budget by changing a report flag.

Evidence and the exact proposal live in [bounded-geometry-v1](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/bounded-geometry-v1/README.md).
The complete preflight passes all 860 canonical/subdivision geometry/frame checks
and 238 of 244 desired plans. The six rejections are mn/mm at width 0.97, all three
advances, under internal subdivision. A read-only diagnostic finds two samples
at the first m corner, 1.42e-14 mm apart; the unchanged 1e-8 mm uniqueness check
correctly refuses them. Fix derived corner sampling before physical budgeting or
execution; do not alter geometry, narrow the grid, or relax the corner threshold.
The aborted first report and original reader are preserved. A collector-only
repair records every rejection in snapshot-002 without changing the sampler.
P2b remains incomplete until actual mechanics and replay are independently
validated. P3 preference labels/objective and all fitting gates remain closed.

#### Approved corner-sampling repair

The follow-up authorizes only repairing corner sampling and rerunning the same
grid without changing geometry or thresholds. Preserve snapshot-002 and archive
its exact sampler/reader sources; a new snapshot binds the repaired code. Frozen
core, candidate, P1/P2a readers, targets and prior evidence pins do not change.

The subdivided narrow m has an ordinary arc midpoint 1.5099e-14 mm beyond its
exact corner boundary, just outside the original sampler's 1.4211e-14 mm
roundoff suppression. Both survive and match the unchanged 1e-8 mm corner gate.
The derived-only adapter now preserves the explicit exact corner sample and
its two boundary contributors, removing only immediately adjacent ordinary
interior samples on the incoming last or outgoing first cubic within 16
coordinate ULPs, capped at the existing corner tolerance. This numerical
coalescing distance is 2.8422e-14 mm for the diagnosed corner; it is not a relaxed
acceptance threshold. Endpoints, distinct events, unrelated owners and ambiguous
or missing exact anchors are never silently merged. No coordinates, tangents,
ownership or progress values on retained samples are rewritten. The null path
still bypasses this adapter entirely.

The unchanged-grid comparison must bind the old external report pin, archived
source hashes and the new report pin, verify all 860 geometry records and every
frozen window exactly, and require all 238 previously passing timing hashes and
52 null action bundles to remain exact. All six formerly rejected plans must be
present and pass the original criteria. A separate fresh-process reconstruction
must reproduce the new complete report; the before/after comparison alone is
not independent physical validation. Actual runs, rendering and fitting remain
outside this repair authorization.

The unchanged-grid rerun in snapshot-003 passes **860/860 geometry checks and
244/244 desired plans**. Its pinned before/after comparison confirms all 238
previous passing timings and 52 null bundles are exact; all six earlier
rejections are resolved without deleting their historical evidence. The focused
suite passes 167 tests. This clears the sampler prerequisite, not physical P2b
validation, preference fitting or C006 completion. Next is
the concrete runner/reader/control and budget-accounting freeze; the owner has
now approved the 45-minute combined seed cap. No physical run or fitting starts
with the approval-only update. Old snapshots retain their historical pending
budget flags and source identities; a new execution contract must bind the
separate approval instead of altering those frozen reports or readers.

## 4. Training signal and ablations

H024 has no evidence that a particular context deformation is desirable. Its
approved baseline pixels are not new context targets, and minimizing distance
to them would merely select identity.

Before fitting, obtain owner rankings of the bounded **training** preview grid
after mechanical feasibility is established. Six training pairs cover all six
rule cells, with nine width/advance combinations each: at most 54 rows. Label
generated previews honestly: subjective owner preferences over derived
candidates, not independent historical exemplar images. Freeze the labels,
invalid-variant exclusions, objective formula, tie handling and hashes before
selection. No desired contextual target or aesthetic threshold is invented here.

Proposed learning is separable finite enumeration of the six shared cells,
not an unconstrained optimizer. Minimize frozen preference disagreement. Ties
favor fewer nonidentity parameters, then smaller normalized deformation, then
lexical IDs. Identity remains admissible. The development set is a safety/reading
check only; no parameter or hyperparameter retuning in the first attempt.

Compare three arms under the same labels, budgets and measurement contract:

1. Context off: approved letter geometry and original advances.
2. Spacing only: scale exactly 1; select only advance deltas.
3. Stroke context: select width and advance from the proposed grid.

For a mechanistic comparison, also compare each selected width change with
scale 1 at **exactly the same advance delta**. Remove overall placement before
computing primitive control-point deltas. Preference against only the unchanged
baseline is insufficient: compare to the best spacing-only arm as well.

## 5. Exact text partitions and honest novelty

| Role | Texts |
|---|---|
| Isolated controls | n, u, m |
| Training pairs | nn, nm, un, um, mn, mm |
| Development triples | nnu, unu, mnu, nmm, umm, mmm |
| Sealed contextual holdouts | num, mun, umn, nmn, umu, mum |
| Previously reviewed pair probes | nu, uu, mu |

Several pairs were already inspected as context-off H024 samples. They are not
pristine unseen text; pair probes test rule sharing across the n/u entry class.
Only the six sealed triples support new composition-disjoint context evidence.
All selected parameters, labels, code, references and development outcome freeze
before test scoring or test-image inspection. Test failure is retained, not
folded back into training. Seed changes do not constitute text generalization.

## 6. Measurement, execution and outcomes

Preparation compiles 21 baseline strings and confirms one contact run per letter.
It checks nominal containment for the twelve triples: **mmm clips the old frame**.
All twelve unchanged nominal triples fit `[-3, 30, 2, 13]` mm, now approved for P2b.
This is not variant, actual-motion or full timing-plan preflight.

Keep old known-base regressions in their original `[-3, 20, 2, 13]` frame. Use
the approved wider frame for all new context arms. Never crop or rescale one
frame into the other's exact-reference comparison. Freeze fixed per-occurrence
windows from the union of all allowed geometry/placement combinations plus
0.8 mm padding before scoring; prove full finite-nib containment for every
admitted variant. Do not move windows after seeing a score.

Retain 180 DPI metric / 900 DPI presentation output and H024's four refinements.
Use unchanged mechanical criteria for motion, clock, contacts, ports, vertical
levels, overlap and exact-event convergence. The original analytic comparator
stays diagnostic in this new scope, with old numerical FAIL unchanged.
Nominal/actual losses remain report-only; no 0.05 regression tolerance is copied.

Before execution, enumerate the full fixture/arm/refinement/first-replay inventory
and render-call upper bound. All isolated controls, sealed test triples and
known-base regressions require four refinements and fresh-process replay;
training/development/cross-neighbor probes require at least base actual evidence
and fresh replay, with no missing arm. Final inventory approval cannot be skipped.

Approved **combined** cap is 5,000 renders / 2,700 seconds per seed 7/19/41,
covering all arms, first/replay, references, masks, presentations and controls;
it is not a separate allowance per arm. Zero automatic revisions or retries.
Human-review preview generation needs its own explicitly authorized, journaled
debit carried into these budgets. Operator waiting is not controller execution
time, but compute/render work is never free. Check feasibility before starting;
stop and seek a revised proposal if the full inventory cannot fit.

Negative controls cover identity tampering, unapproved bounds, unknown rules,
per-word memorization, broken ports/tangents, hidden lifts, owner/overlap forgery,
action changes, desired-as-actual traces, clock drift, crop/frame misuse,
ineffective image-shift controls and spacing-only results mislabeled as stroke
changes. The independent reader must reconstruct these proofs from raw evidence.

Separate outcomes: blocked prerequisites; mechanical failure; spacing alone
suffices; stroke changes exist but are not preferred; or bounded synthetic
context support. Owner reading/preference of unseen triples is required for
the last outcome. No automatic statistical, S3 or real-hand claim follows.

## 7. Implementation order and release gates

**Owner revision, 2026-09-10:** the old P3–P5 preference/selection route below is
paused, not completed or failed. Continue through Addendum D's bounded
stroke-context investigation before reconsidering any fitting objective.

1. **P1 complete:** current-source baseline-only clearance and gap inventory, using pinned H024 evidence.
2. **P2a complete; P2b preflight cleared:** approved bounded geometry/frame,
   derived planning and 45-minute combined seed budget. The opt-in physical
   runner, independent reader, controls and ledger are implemented in
   [physical-validation-v1](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/README.md).
   **Bounded mechanical gate cleared:** after retaining the original disk failure,
   approved seed-41 recovery and a separately versioned measurement-only dimension
   correction, all 1464 saved cases and 324 presentations independently pass,
   with exact first/replay equality for all three seeds. All debits and failed
   evidence remain preserved; no further physical run or fitting is performed.
3. **P3 review packet prepared; owner input pending:** authorized read-only reuse
   of 54 training previews with rank/tie/exclude export, proposed ordinal objective
   and carried-forward budget ledger. Freeze actual owner labels/approval and a
   feasible exact staged inventory/reuse plan before fitting; the conservative
   no-reuse proposal exceeds remaining time. No budget increase is implied.
4. One bounded rule-selection attempt; freeze its result and development outcome.
5. Sealed holdout evaluation, three-arm proofs, independent verification and
   separately recorded owner appearance/reading verdicts.

CURRICULUM-006 is **in progress**. P2b preflight and its bounded mechanical
evidence gate are cleared; P3–P5 remain pending. Preparation, P1, P2a and P2b preflight use zero controller
calls, raster renders and optimizer evaluations. S2, real-hand and context
training flags remain false. Geometric clearance is not actual-motion or fitting
clearance. Changes remain uncommitted.

### Physical runner preparation

The prepared contract binds the existing 244-case process inventory, not a new
grid or objective. The concrete renderer schedule is 787 calls per process,
1574 per seed including replay, within the unchanged 1588 planning bound.
Fifteen controls cover structural/trace corruption and misleading spacing or
image comparisons. Every controller invocation and render is reserved before
execution; atomic receipts and supervisor deadlines preserve failed debits.
Fresh workers cannot claim larger allowances than their supervisor permits.
Any existing attempt blocks an automatic retry, and later work must carry these
debits forward. Original source files and preflight reports remain immutable.

Raw evidence is measured against the derived plan and ports rather than a
canonical-geometry fallback. The independent reader rechecks dynamics, clocks,
finite-nib/local frames, event convergence, overlap and known-base pixel identity
without trusting saved passing flags. Read-only consumption uses stored raster
artifacts and their hashes; it does not secretly rerender. Software validation
uses archived H024 data and controller stubs, not new experiment runs. The
historical runtime estimate is not a guarantee that the concrete workload fits;
any actual overrun stops the attempt without a retry or relaxed limit.

### First physical attempt: retained storage failure

The owner starts the frozen three-seed attempt. Seeds 7 and 19 record passing
244-case first/replay pairs with exact artifact equality. Seed 41's first pass
also passes all 244 cases, but its replay stops after 52 measured cases with
`[Errno 28] No space left on device`; the next case has an incomplete trace.
The supervisor exits 120 before sealing a root report. A separately pinned
[failure manifest](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/failed-run-001-manifest.json)
preserves 12771 files and the original ledger, without manufacturing a successful
root report. The overall gate remains blocked despite passing worker checks.

No automatic retry or cleanup is allowed. Investigate storage headroom and obtain
approval for a bounded no-refit recovery of the unfinished replay, preserving
all completed evidence and the seed-41 debit of 1165.910 seconds/954 renders.
Geometry, target, frame and threshold changes are not authorized by this failure.

### Owner-authorized bounded storage recovery

The owner subsequently approves a guarded recovery. The separate
[recovery protocol](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/RECOVERY.md)
defines one fresh seed-41 replay, preservation of every original artifact,
carried-forward time/render costs, 10-GiB start/5-GiB stop storage guards,
between-case memory collection and a separately pinned composite raw-evidence
inspection. This is not an in-place resume, budget reset, automatic retry,
geometry/target/threshold adjustment or fitting authorization. The immutable
original runner and reader remain unchanged. Preparation alone grants no
physical or appearance clearance; changes remain uncommitted.

The authorized recovery subsequently completes all 244 replay worker checks and
exact artifact equality. Seed 41's total including the failed replay and recovery
is 2120.933 seconds and 1741 renders, within the unchanged 2700-second/5000 cap.
Saved output is 272 MiB; minimum free space is 6.13 GiB, and the worker records
about 448 MiB peak resident memory. Original and recovery source pins and all
original artifacts remain unchanged.

Final composite inspection is **blocked**, not accepted: the frozen reader
expects 1170×390 presentation images, whereas the frozen renderer's
supersample-and-downsize formula produces 1169×390. All 324 saved presentation
images match the renderer. This metadata result is not a full raw-evidence
inspection. The [recovery result](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/RECOVERY.md)
pins both the successful execution report and failed-inspection diagnostic.
Next is an explicitly approved, separately versioned measurement-only reader
correction using the exact pinned renderer dimensions, retaining containment
and crop rejection, followed by reinspection of the existing artifacts. No
rerendering, refitting, target/frame/threshold change or further physical run is
needed merely to correct this checker mismatch. No overall physical clearance,
appearance approval, S2 or context-training acceptance is granted yet.

The owner subsequently approves the measurement-only correction and existing-file
reinspection. The [dimension-check-v1 reader](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/dimension-check-v1/README.md)
derives exact dimensions from the pinned renderer's supersample-ceil/downsize
contract and decodes saved images fully. It preserves all numerical mechanical
criteria, raw finite-ink containment, metric image checks and controls; it does
not introduce a one-pixel tolerance or rescale evidence. Separate source/test
pins and runtime no-controller/no-raster guards bound the inspection. Frozen
prior readers and failed evidence are retained. Clearance depends on complete
six-dataset inspection, not preparation or the metadata audit alone.

On 2026-09-10 that complete inspection **passes**: 1464 independent case checks,
324 exact-size fully decoded presentations and all three exact replay pairs.
Dimension contract SHA-256 is
`56e3ed722e086ec1415ea54c179070985c8d4841c19368a7c666db56d4f31f11`;
[inspection report](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/dimension-check-v1/inspection-001/report.json)
SHA-256 is `251d4fd3ff6a9c11ea0162b2b73108d679e22fa6ea7fd2a82756e103fdaddb5b`.
Runtime guards prohibit controller/raster calls throughout. Original/recovery
sources, evidence, targets, frames, thresholds and physical ledgers remain
unchanged. This clears only the bounded mechanical gate; appearance review,
preference/objective freeze and fitting authorization remain separate. Next is
P3 preparation with remaining-budget feasibility, not an automatic fitting run.

## 8. P3 owner-review packet and proposed fitting prerequisites

**Paused by subsequent owner decision.** Preserve this packet, any browser drafts
and its unapproved objective/budget proposal. Difficulty seeing differences is
not a submitted rank table, an appearance rejection or permission to exaggerate
deformation. See [Addendum D](TD-018-addendum-d-stroke-context-transitions.md).

The owner authorizes P3 preparation on 2026-09-10. The
[training-only packet](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/owner-review-v1/README.md)
reuses all 54 existing seed-7 actual/base presentations without image generation
or manipulation. It shows the nine alternatives for each of the six training
pairs, plus enlarged unchanged-context and same-advance width-1 comparisons.
This is the current ±3% whole-letter horizontal transformation applied to
constituent strokes, not independent primitive learning or historical exemplar
supervision. No development or sealed-holdout images enter preference collection.

Owner ranks 1–9 are ordinal, ties permitted, with explicit appearance exclusions
and unresolved rows. Proposed cell loss is the fraction of other admissible
variants ranked strictly above a candidate; table loss is the mean over six
cells. Ties prefer fewer nonidentity parameters, smaller normalized deformation,
then stable IDs. Neither labels nor objective approval are prefilled. The export
binds the pinned packet and requires owner confirmation before labels/objective
are frozen. Any excluded baseline or unavailable spacing-only comparison must
be resolved explicitly before a three-arm preference claim.

P3 uses zero new controller runs, simulation renders or fitting evaluations.
Remaining seed7/19/41 allowances are respectively 582.185/988.416/579.067 seconds
and3426/3426/3259 renders. The detailed proposal retains four arms (including
matched-advance control), six development triples, three known pair probes, six
sealed triples, three isolated controls and four old-frame known regressions,
with four refinements and first/replay. Without proven reuse this is536 physical
executions and1744 render calls per seed. A rough prior-runtime extrapolation is
31–39 minutes additional per seed, before safety margin—not a guarantee. Current
remaining time is insufficient for that proposal, so budget readiness is false.

Before fitting, receive owner labels and objective confirmation, freeze exact
selected-program inventory/reuse rules and staged development/holdout gates,
and obtain any necessary explicit budget revision. Development must remain
safety-only with no retuning and sealed evaluation must follow selection and
development freeze. Do not silently shrink inventory, reset costs, increase caps,
or treat P3 preparation as fitting authorization. C006 remains in progress.
