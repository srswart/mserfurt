# TD-018 — Reference-Grounded Recovery of Konrad's Hand

**Status:** proposed implementation design; no hand or renderer promoted.  
**Date:** 2026-09-05  
**First milestone:** three convincing lines generated from reusable stroke programs, including unseen words.  
**Plan:** [Pass 15](../../arrive/implementation-plan.yaml), ten planned Advances.

## 1. Outcome and scope

Recover the letterforms, contextual variants, joins, and spacing that make one
coherent reference hand recognizable. Use that repertoire to write new text,
then execute it through the existing continuous guided hand simulation. The
first deliverable is a small specimen whose appearance the project owner can
assess directly. Full folios follow only after nominal and simulated specimens
pass separate gates.

The intended character remains Brother Konrad: a professional scribe writing
a private manuscript, with the folio-specific variations described by the
project brief. A reference hand is a visual model for this fictional character;
it is not evidence identifying a historical Konrad. Selection of the visual
target and scholarly validation of period/region remain separate decisions.

Implementation remains automatic-first. No calligrapher, manually traced
alphabet, new neural model training, or paid API is a prerequisite. Uncertain
automatic results remain visible and may block a gate. Human review concerns
concrete specimens and unresolved readings; it is not an implicit requirement
to draw every letter. Source images must never be pasted into generated text.

## 2. Current evidence and diagnosis

This assessment uses the repository and saved artifacts inspected on
2026-09-05. Existing images are saved outputs, not newly regenerated baselines.

| Evidence | Finding | Design consequence |
|---|---|---|
| `reference/konrad_word_recovery_v1/evidence/comparison.png` and `generated.png` | Fitted writing still differs visibly from the reference in proportions, loops, and word construction. Several source crops contain neighbouring-line ink. | Repair observations and permit alternative stroke structures before expressive tuning. |
| `reference/konrad_word_recovery_v1/evidence/report.json` | 14 training and 8 held-out samples; loss 0.6727 → 0.5707 and 0.6718 → 0.6355 respectively; report says `not_promoted`. | Preserve this experiment as a baseline. Similarity gain is not a readability result. |
| `scribesim/evofit/word_recovery.py` | Shared local cubics, fixed catalog stroke topology, bounded coordinate proposals, one shape per character. | Retain shared parameters and real-image evaluation; replace the fixed structural hypothesis. |
| `scribesim/cli.py`, `scripts/render_all.py`, `scribesim/render/pipeline.py` | Default CLI and bulk script use evo; ScribeState is integrated into plain. | Record the actual backend and assets in every proof. Use one explicit guided route for this track. |
| `scribesim/render/scribe_state.py`, `scribesim/ink/cycle.py` | Plain state calls word-boundary dip checks without stroke consumption; built-in `hash()` seeds are not stable between ordinary Python processes. | Test consumption and fresh-process determinism in the selected guided path; do not assume the plain implementation solves either. |
| `scribesim/handvalidate/metrics.py`, `folio_bench.py` | `ocr_proxy_score` wraps template similarity; existing organicness comparison uses pressure dynamic range. | Neither metric establishes correct reading or convincing handwriting. Separate image, motion, text, and human appearance evidence. |

Five focused `tests/test_word_recovery.py` tests passed during the preceding
inspection. They cover experiment mechanics, not historical accuracy. The
in-progress ADV-SS-EVOFIT-004 still needs its execution record reconciled with
the saved evidence; this document does not mark it complete.

## 3. Relationship to existing directions

- Retain TD-014's nominal-before-controller sequence, exact-symbol coverage,
  provenance, corridor tracking, and opt-in folio rollout.
- Extend its nominal recovery with whole-word supervision, multiple structural
  hypotheses, explicit context selection, and a small visual acceptance bench.
- Reuse TD-012's allograph/composition concepts after verifying their behavior.
  Existing variants are candidate seeds, not automatically accepted exemplars.
- Reuse TD-015's broad-edge sweep for nominal observation and the existing
  guided trajectory renderer for simulation. Their equivalence is measured at
  the bridge, rather than assumed from similar names.
- Apply TD-017's slow, coherent state principle after nominal acceptance.
  Do not add a second controller or transplant its plain-state updater wholesale.
- TD-018 gates govern promotion on this track. Existing template/OCR proxies and
  zero-self-intersection rules cannot certify it: intentional loops/crossings
  need explicit topology, and a template score cannot read a word.
- TD-001 output contracts and TD-013 private-manuscript geometry still apply.
  Resolve older conflicting page-size prose using current layout configuration
  and tests during folio integration.

The planned tremor/warp work in ADV-SS-HANDFLOW-007 and broad sensitivity work in
ADV-SS-HANDVALIDATE-006 are not prerequisites for this track. Defer them until
the specimen works; their statuses and IDs remain intact. Reuse their useful
bench machinery without creating duplicate competing state implementations.

## 4. Architecture and ownership

| Stage | Existing home and proposed additions | Output |
|---|---|---|
| Target and observation preparation | `scribesim/evofit/reference_dataset.py` (new); reuse refextract/annotation helpers where verified | Versioned source, mask, label, split, and coverage manifest |
| Repertoire representation | `scribesim/evofit/repertoire.py` (new); reuse genome/allograph primitives | Shared stroke programs and explicit contextual choices |
| Image-based recovery | `scribesim/evofit/recovery.py` (new); keep `word_recovery.py` as v1 baseline | Reusable fitted repertoire plus full run record |
| Nominal evaluation | `scribesim/handvalidate/specimen.py` (new) | Comparison panels, metrics, review record, gate decision |
| Guided bridge | `scribesim/pathguide/repertoire.py` (new) | Dense paths, contact schedule, occurrence ownership sidecar |
| Continuous execution | Existing `scribesim/handflow/` controller, planning, session, render | Actual trajectory and persistent state/event trace |
| Folio integration | Existing CLI, guided folio/layout and groundtruth paths | PNG, pressure map, PAGE XML, backend/asset provenance |

New filenames and CLI commands below are proposed interfaces, not currently
available features. New recovery code belongs under the tracked `evofit/`
directory: the current `.gitignore` ignores `scribesim/refextract/` even though
local helper code exists there. Do not accidentally ship an implementation
that depends on untracked local modules; each Advance checks clean-checkout
imports and adds focused selector coverage for new tests/assets.

## 5. Observation and benchmark contract

### Source selection and cleaning

Begin with a visibly coherent hand from the current source collection. Prefer
additional pages from that same apparent hand when available. Record source
resolution and apparent-hand grouping without converting appearance into
verified attribution. Use native images; enlarged low-resolution crops do not
count as new evidence.

Detect lines before words. Estimate line baselines and envelopes, assign ink
components using neighbouring-line context, and retain ambiguous touching
strokes as uncertainty regions. Preserve raw pixels and emit an independent
mask with `target_ink`, `background`, and `unknown` pixels. Never erase an
ambiguous component simply because it reduces fitting loss. Show raw, mask
overlay, and cleaned views together. Penalize generated extra ink on known
background; ignore only declared unknown pixels. Limit and report unknown
coverage so masking cannot remove most of a difficult word.

Every sample records:

- source URL/local identity, source SHA256, page/line IDs, native word bounds;
- raw crop hash, mask hash, extraction version, source-to-normalized transform;
- baseline/x-height estimates and uncertainty, with aspect ratio preserved;
- diplomatic label hypotheses, logical text, transcription origin and status;
- explicit logical-character-to-visible-form mapping, including long s,
  diacritics, abbreviations and multi-character ligatures when admitted;
- apparent-hand group, split, exclusion reason and actual human interventions.

Automatic confidence is a ranking signal, not a probability or expert approval.
Do not settle ambiguous transcription by whichever label the current renderer
fits best. Missing or ambiguous symbols are excluded and counted as coverage
debt. Where an abbreviation mapping is unsupported, reject that sample for the
first specimen rather than normalize it silently into different visible text.

### Splits and visual target

Freeze train/development/test membership before fitting. Group by source line
at minimum, and by page when the source volume permits; forbid overlapping
source pixels across splits. A same-page test supports only within-page
generalization. Previously inspected v1 held-out examples are now development
material, never relabeled as a fresh locked test.

Initial collection target: 30–60 usable word instances, with repeated forms in
different contexts. This is a planning allowance, not an adequacy guarantee.
Require at least three training occurrences per starter symbol, at least two
word contexts where available, and enough independent material for development
and test. Missing coverage blocks the affected specimen; it does not authorize
aliases or unrelated-hand backfill.

Freeze a target sheet and a three-line proof manifest:

1. A reconstruction line assembled from admitted reference words.
2. A line of unseen word strings composed from the learned inventory; include
   at least five unseen strings across the evaluation bundle, with independently
   sourced test instances where available.
3. A project-text line exercising repeated letters, joins and spacing, selected
   before fitting. Later full-folio coverage cannot be inferred from this subset.

Generated strings without a real reference receive structural/text and visual
evaluation, not fabricated image-similarity scores. Document unsupported
project characters explicitly. Record owner acceptance of the intended visual
target before declaring an appearance milestone passed; preparation can proceed
while that review remains pending.

## 6. Reusable stroke programs and recovery

### Representation

A versioned `HandRepertoire` contains units in local x-height coordinates,
physical nib parameters, spacing parameters and context rules. Each form has:

- stable `form_id`, logical text span and supported visible-symbol identity;
- one or more ordered cubic stroke chains, explicit pen lifts, endpoint/tangent
  constraints, and permitted crossings/loops;
- advance, baseline/ascender/descender landmarks, entry/exit ports;
- pressure and speed priors, provenance, support count and uncertainty;
- a bounded deformation envelope learned only from training examples.

Allographs share a logical character while retaining distinct visible forms.
Ligatures own an explicit text span and character attribution map. A
`WordPlan` selects form IDs, places them, and inserts legal contact joins or
air transitions. It records every requested character, selected form, text
span, and advance. There is no unrestricted per-word drawing cache in the
learned model. Render caches are derived artifacts keyed by all model inputs.

### How alternative structures are obtained

Use existing catalog/allograph forms as one seed family. Add automatic
proposals from cleaned word ink: skeleton graphs supply possible chains,
branches and loops; a monotone character-alignment lattice proposes allocations
to labeled text spans. Shared evidence from repeated words/contexts constrains
those allocations. Skeletons are proposal geometry only, since a broad nib's
ink skeleton is not necessarily its pen trajectory.

Permit bounded split/merge of cubic chains, addition/removal of a short branch,
loop alternatives, and contact/lift alternatives. Re-render every candidate
through the nib model. Start with at most three forms per symbol, eight contact
chains and 32 cubics per form; record limit hits. These are configurable search
bounds, not historical claims. If the automatic proposals cannot explain a
symbol, emit an unresolved-symbol result and its diagnostic panel.

### Search and objective

Alternate bounded steps: (1) choose training-word form assignments and legal
joins, (2) refine shared geometry/advances/nib, (3) propose a limited structural
change. Reuse contextual dynamic-programming ideas with an explicit beam cap
of 32 states per text position. A word instance may carry limited nuisance
alignment (translation and one isotropic scale); it may not freely warp its
letters or change aspect ratio. At generation time form selection uses text
context and the frozen model only, never a target image.

Score separately and report each term:

- multiscale ink overlap and symmetric contour distance;
- extra/missing ink on known mask regions and counter/loop preservation;
- baseline-relative proportions, word advance and inter-form spacing;
- complexity, unsupported forms and deviation from supported shared geometry;
- illegal joins, broken endpoint constraints and invalid text mappings.

Hard mapping/topology violations reject candidates before scalar scoring.
Calibrate term weights and nuisance bounds on training/development evidence;
freeze them before locked-test evaluation. Include deliberate wrong-letter,
filled-counter, extra-stroke and distorted-aspect controls so a convenient
objective cannot manufacture success. Increasing stroke width alone must not
beat a correct control by filling its counters.

Initial pilot budget: three recorded seeds, at most 5,000 rendered word
evaluations per seed and 30 minutes per seed, whichever is reached first.
Profile a smaller smoke run first. Report evaluations, wall time, best
checkpoint and stop reason; cache hits do not count as new evaluations.
Compare alternatives at matched budgets. Development selects checkpoints;
test runs only after checkpoint/configuration freeze. A failed test becomes
disclosed development evidence for the next version, requiring a new test set.

This is inverse rendering of a plausible reusable writing program. A scanned
word does not uniquely determine historical stroke order, pressure or speed.
Those remain explicit simulation priors unless independently evidenced.

## 7. Nominal-to-guided bridge and state

Keep the existing `DensePathGuide` contract compatible. The adapter samples
selected stroke programs by arc length in millimetres, inserts explicit air
travel, and preserves nib angle, nominal pressure, tangents and corridors.
Add a versioned sidecar mapping sample intervals to word/form/stroke IDs and
logical text spans. A symbol-to-single-guide dictionary cannot silently discard
contextual variants. Resolve the word's forms first, then build its guide.

Compare direct nominal sweep against guide playback at matching physical scale,
nib and sampling tolerance before running dynamics. Fail conversion if contact,
orientation, baseline transform or form attribution changes. Render controller
output from `SimulationResult.trajectory`; aligned trajectories are diagnostic
only and cannot conceal tracking errors.

Use `HandStateV2` and the existing guided session as the persistent state owner.
An explicit session seed and stable digest of model/folio/session IDs initialize
local RNG streams; never use Python's process-salted `hash()` for reproducibility.
Preserve state through glyphs, words and lines. Air travel, pauses, line returns
and sitting breaks are explicit events; layout must not recreate a fresh hand
for each line.

Consume ink on contact arc length with bounded pressure dependence. Air motion
does not consume ink. Word boundaries check for a dip; they do not stand in for
stroke consumption. A dip refills the reservoir without resetting motor habits.
Pressure, nib angle, speed and baseline drift evolve slowly with elapsed writing
and explicit profile inputs. Fatigue and passage variation use bounded,
documented controls; do not infer historical emotional state from keywords.

Begin with neutral execution, then activate ink consumption/dips and a small set
of pressure, angle and rhythm controls. Each control must visibly and measurably
affect the selected path while preserving symbol identity. Warp/tremor expansion
is deferred. Preserve intended crossings rather than imposing zero intersections
on every letter.

## 8. Evaluation and decisions

Each gate returns `pass`, `fail`, or `blocked`, with reasons and artifact paths.
Missing required readings, absent metrics, unavailable assets and empty test
sets produce `blocked`, never a default pass. Completing an experiment Advance
can mean recording a failed hypothesis. It does not pass a downstream runtime
gate or promote a model.

| Gate | Required evidence and decision |
|---|---|
| G0: benchmark ready | Source/label/mask provenance; disjoint splits; coverage report; frozen proof texts, target sheet, rubric and gate configuration. Unreviewed target may be prepared but appearance acceptance remains pending. |
| G1: nominal specimen | Exact mapping coverage 1.0, zero aliases or undeclared normalization; replay succeeds in fresh processes; adverse controls fail; repeated and unseen test words reported separately; three-line proof passes the appearance rubric. |
| G2: guided equivalence | Same selected forms/contact/text ownership; direct versus sampled playback inside development-calibrated contour/width bounds; actual neutral-controller trajectory retains G1 quality. |
| G3: expressive specimen | G1/G2 retained; ink drops only during contact except explicit refill, dips/pause events logged; activated controls produce intended deltas; three seeds show bounded coherent variation; fresh-process same-seed replay matches. |
| G4: folio candidate | Exact complete text and coverage on four representative cases; actual-trajectory image/XML/pressure agreement; no silent overflow/truncation; downstream dry acceptance; owner specimen/folio review recorded. |

Numerical image, corridor and spacing tolerances are calibrated on repeated
source examples and deliberately damaged controls in G0/development, versioned,
then frozen. Do not choose thresholds after inspecting the candidate's test
score. Report per-word failures and worst cases as well as means. Existing
TD-014 thresholds remain diagnostics until their semantics are validated for
this repertoire. Pressure-map contrast is reported as pressure range, not as
an organicness verdict. Optional HTR output must identify its recognizer and
reference labels; no HTR or expert score is invented when unavailable.

The owner-facing rubric compares equal-scale, randomized candidate/baseline
panels with a fixed reference sheet. Assess letterform identity, proportions,
word joins/spacing, coherence of one hand and unwanted distortions separately.
Record `acceptable`, `revise`, or `unresolved` per category with concrete word
examples. G1/G3 appearance passes require all categories acceptable and a clear
preference over the baseline overall. Reviewer identity, date, labels shown or
hidden, and assistance must be recorded. This is project appearance acceptance,
not an expert paleographic endorsement. Pixel coverage of requested text and
independent correct reading remain distinct fields in the report.

Every run bundle includes manifest/model/config/commit hashes, dirty-tree patch
identity when applicable, seed, environment versions, actual backend, raw/masked
source panels, baseline/candidate/unseen proofs, component losses, exclusions,
state traces where applicable, runtime, interventions and gate/review records.
Retain negative results. Use immutable versioned directories under
`reference/konrad_hand_recovery_v2/` for source bundles and
`shared/training/konrad_hand_recovery/` for run evidence, with explicit tracked
manifests and storage/reproduction instructions for binaries. Update scoped
ignore exceptions during implementation; do not unignore the whole reference tree.

## 9. Folio integration and release boundary

The three-line nominal milestone is the first decision point, followed by an
expressive three-line milestone. Only then expand exact inventory to clean,
pressure-heavy, multi-sitting and late/failing-eyes folio cases (initial IDs
f01r, f06r, f07r and f14r). Verify current hand-note/line locations against XL
records rather than assuming old prose line numbers survived refoliation.

Proposed CLI surface: extend `--approach guided` with an explicit versioned
`--repertoire` path and `--seed`, plus a small `hand-proof` command for nominal
and guided specimens. Diagnostics must name the selected backend, model hash,
resolution mode and missing symbols. No implicit fallback to evo/plain.

Preserve each input character, line and folio ID. Reject overflow with useful
diagnostics rather than slicing the input or clipping off-canvas strokes.
Generate PAGE XML and pressure maps from the same actual positioned trajectory
that paints the image. Carry ownership through joins and ligatures; mark shared
ink explicitly rather than inventing independent character boxes. If the current
contract cannot express a proposed multi-character form accurately, keep that
form unpromoted until a compatible attribution/export rule is validated.

Run local Weather loading/compositing contract checks without making paid image
generation a gate. A clean specimen must already work before aging. The default
renderer remains evo throughout implementation and evaluation. G4 produces a
reviewable opt-in release candidate; a future default switch is a separate
explicit release decision. Rollback selects the existing renderer/assets and
retains failed evidence; no reference or production output is overwritten.

## 10. Advances and execution sequence

All records below are planned; their checklists and evidence are prospective.
Draft timestamps record document creation, not completed implementation work.

| Advance | Reviewable outcome | Depends on |
|---|---|---|
| [ADV-SS-HANDVALIDATE-007](../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-007.md) | Target sheet, benchmark contract and honest baseline | Existing EVOFIT-004 evidence (reconcile, do not assume completion) |
| [ADV-SS-EXEMPLAR-007](../../arrive/systems/scribesim/advances/ADV-SS-EXEMPLAR-007.md) | Clean word observations, explicit labels and frozen splits | HANDVALIDATE-007 |
| [ADV-SS-EVOFIT-005](../../arrive/systems/scribesim/advances/ADV-SS-EVOFIT-005.md) | Reusable alternative stroke programs and exact composition | EXEMPLAR-007 |
| [ADV-SS-EVOFIT-006](../../arrive/systems/scribesim/advances/ADV-SS-EVOFIT-006.md) | Bounded image-based recovery and context selection | EVOFIT-005 |
| [ADV-SS-HANDVALIDATE-008](../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-008.md) | G1 decision on the nominal three-line specimen | EVOFIT-006 |
| [ADV-SS-PATHGUIDE-005](../../arrive/systems/scribesim/advances/ADV-SS-PATHGUIDE-005.md) | Loss-bounded guided bridge and G2 evidence | HANDVALIDATE-008; G1 pass |
| [ADV-SS-HANDFLOW-008](../../arrive/systems/scribesim/advances/ADV-SS-HANDFLOW-008.md) | Persistent, seeded stroke/word/line state | PATHGUIDE-005; G2 pass |
| [ADV-SS-HANDVALIDATE-009](../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-009.md) | G3 expressive specimen and control sensitivity decision | HANDFLOW-008 |
| [ADV-SS-RENDER-006](../../arrive/systems/scribesim/advances/ADV-SS-RENDER-006.md) | Opt-in folio rendering and actual-trajectory exports | HANDVALIDATE-009; G3 pass |
| [ADV-SS-HANDVALIDATE-010](../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-010.md) | G4 four-folio evaluation and rollout recommendation | RENDER-006 |

The first Advance reconciles prior results as evidence, without changing
EVOFIT-004's status unless its own completion criteria have actually been met.
Plan dependencies express implementation order; model gate records separately
control whether downstream integration may execute with a given candidate.

## 11. Failure decisions

- Dirty crops or unresolved labels: repair the observation set; do not spend
  more fitting budget or claim a trusted alphabet.
- Clean observations but poor nominal forms: inspect topology proposals,
  alignment and loss ablations; do not advance to the controller.
- Good reconstruction but poor unseen words: reduce per-instance freedom,
  improve shared/context coverage and test again on a newly locked set.
- Good nominal but degraded guided output: correct conversion, sampling, nib
  equivalence or controller tracking while holding the repertoire fixed.
- Good neutral but poor expressive output: disable the offending activated
  control, retain the neutral candidate and diagnose the state trace.
- Good specimens but failed folios: address coverage, layout or ownership
  exports in bounded follow-up work. Do not hide the failure with Weather.

After the initial bounded recovery run and one diagnosed revision, issue a
written stop/revise/proceed decision. Further search, larger datasets or manual
annotation must be motivated by a named unresolved failure and a new budget.
