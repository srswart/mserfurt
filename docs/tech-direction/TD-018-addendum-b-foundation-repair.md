# TD-018 Addendum B — Reliable Stroke Foundations Before Further Layers

**Status:** HANDFLOW-010 motion repair and GESTURE-002 return-contract audit are
complete; four Advances remain planned. The audit freezes two untrained returns,
actual-tangent ports, a six-expanded-occurrence opt-in cap and explicit inventory
debt. Run-005 retains its accepted pre-audit motion result; compiler identities
have changed, so CURRICULUM-010 must refresh motion/baseline admission before
fitting. No new learning, S1-action, real-hand or owner appearance approval is claimed.
See [findings and samples](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/index.html)
and the [executed vocabulary audit](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/contract/README.md).
**Date:** 2026-09-06
**Parent:** [TD-018](TD-018-reference-grounded-hand-recovery.md) and
[Addendum A](TD-018-addendum-a-stroke-gestures.md).

## 1. Decision

Keep the layered stroke-language architecture. Change the immediate priority
from downstream infrastructure to stable execution, adequate primitive coverage
and visible learning on genuinely unseen constructions. Do not start more action
fitting, learned letters/words, fatigue or ink-depletion work during this phase.

The previous phase implemented useful infrastructure, but its learning attempt
performed zero renders because prerequisites failed. An Advance completion is
not evidence that a stroke was learned. The new learning Advances must remain
in progress if only their runner is implemented; a blocked evaluation may finish
with an explicit blocked outcome, but it cannot discharge an unexecuted learning
experiment or permit later training.

## 2. Evidence and diagnosis boundary

- [Gesture evaluation](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/gesture_evaluation/README.md)
  records a 0.399871 mm lifted-pair contact-entry shift under arc refinement.
- [Realized action diagnostics](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/action_bridge/README.md)
  record approximately 0.399742 mm arc-refinement and 0.399462 mm timestep shifts,
  despite passing aggregate image differences. The endpoint limit is 0.01 mm.
- The controller currently floors each guide-segment duration at `dt`, rounds its
  substep count, holds the next desired sample and projects contact positions onto
  a corridor. These are **hypotheses to isolate**, not an already proved diagnosis.
  Do not prescribe snapping the pen to the desired entry as the solution.
- [Primitive-extension request](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/gestures/primitive-extension-request.md)
  identifies missing lower/upper returns and potentially restrictive four-primitive
  letter expansion. The six existing families are not a complete gesture inventory.
- Older whole-file renderer/bridge identities are stale. Legacy pixel equality
  alone cannot refresh acceptance; retained failures and old freezes are immutable.

## 3. Ordered Advances and deliverables

| Order | Advance | Required output |
|---|---|---|
| 1 | [HANDFLOW-010](../../arrive/systems/scribesim/advances/ADV-SS-HANDFLOW-010.md) | Root-cause evidence, opt-in temporal/contact repair, stable actual contact entries and replayable existing-primitive baseline validation |
| 2 | [GESTURE-002](../../arrive/systems/scribesim/advances/ADV-SS-GESTURE-002.md) | Stroke/port and letter-expansion audit; explicit bounded return-primitive/composition contract; compiler support only for the justified versioned change |
| 3 | [CURRICULUM-010](../../arrive/systems/scribesim/advances/ADV-SS-CURRICULUM-010.md) | Actually fitted lower/upper return primitives with old six primitives fixed; enlarged practice and unseen attachment proofs |
| 4 | [HANDVALIDATE-015](../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-015.md) | Independent current-code S1 primitive-extension decision; no gesture fitting until the required inventory passes |
| 5 | [CURRICULUM-011](../../arrive/systems/scribesim/advances/ADV-SS-CURRICULUM-011.md) | Actually learned fixed-tool underturn, overturn and compound constructions using accepted shared primitives |
| 6 | [HANDVALIDATE-016](../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-016.md) | Independent S1-gesture transfer/continuity decision and precise next-experiment eligibility |

The two independent evaluation records prevent primitive and gesture fitting
from being collapsed into one self-certified experiment. No new component or
parallel renderer/controller is needed. Existing `handflow`, `gesture`, `evo`,
`curriculum`, `pathguide`, `nibcontact`, `handvalidate` and `tests` own the work.

## 4. Execution and baseline contract

Freeze the failing `u` / `i u` cases before repair. Include a continuous gesture,
two separated contacts, coincident lifted overlap, word space and exact cubic
subdivision. Compare physical contact-event time, total planned/executed duration,
first/last contact positions, velocities and owners—not merely final images.

Use an explicit new execution version in the existing controller if positional
semantics change; retain legacy playback and fixtures. No second integrator,
painted air connector, instantaneous pose reset, erased owner or post-hoc image
touch-up may turn the test green. Fix sampling-dependent elapsed time and contact
events if demonstrated; preserve measured lag rather than reporting desired pose
as actual. If another cause is found, record the evidence before changing course.

Freeze one fixed-angle/full-edge, pressure-0.5, speed-12 mm/s, adequate-ink tool
mode for learning. Prefer the explicit legacy full-edge footprint initially to
avoid changing both motion and nib geometry in the same experiment. Validate
`physical-edge-v1` fixed-profile bridge replay separately; its acceptance cannot
be inferred from legacy pixels. Never switch modes within a fit or comparison.

HANDFLOW-010 must supply a **read-only baseline revalidator**, not a copied old
pass: verify historical artifact provenance, rerender the six frozen primitive
models against their original independent synthetic targets under current code,
and recompute applicable original S1/image/actual metrics. It may emit a fresh
scope-qualified baseline admission only when those checks pass. No fitting or
editing historical hashes is allowed. If that baseline fails, stop before new
primitive fitting and explicitly scope the required baseline repair.

After GESTURE-002 changes compiler identities, rerun this baseline revalidator
before CURRICULUM-010. Charge that work to the new run's budget. This avoids the
circular dependency of requiring a new-primitive acceptance gate before those
new primitives can be trained, without treating stale lower-layer evidence as valid.

### 4.1 Accepted curve-clock implementation

Motion admission is now supplied by run-005, not by retroactively changing the
prior failures. Its `curve-time-v1` planner integrates the frozen cubic derivative
magnitude with deterministic adaptive 16/32-point quadrature (estimated absolute
error 1e-10 mm per integral, depth <= 12 and <= 4096 panels; exhaustion rejects).
Opt-in source metadata retains cubic identity, parameter and representation so
each unchanged guide point maps into geometric arc progress without nearest-point
search. Reconstruction, complete endpoints and monotonicity are checked. The
existing corner/curvature/air rules and controller limits remain unchanged.
Numerical integration estimates are not a proof of arbitrary-curve accuracy;
analytic, independent high-order, subdivision and full actual-motion checks
establish this bounded fixture scope. New shapes still require fresh validation.

## 5. Vocabulary and composition audit

Audit the six existing primitives against the eight existing gesture hypotheses.
Use `i, n, u, m, r, o, a, d, e, l, h, g` as a bounded **construction-feasibility
checklist**, not an admitted alphabet, historical ductus assertion or letter fit.
For each hypothesis record direction, entry/exit port, curvature, contact/lift
topology, counter needs, minimum expanded primitive count and unresolved options.

Prioritize no more than two new shared families: lower return and upper return,
keeping at most eight primitive families overall. Freeze independent targets,
ports and allowed interior-control-point freedoms before any optimization. Do
not relabel existing turns, add letter-specific cubics or borrow later pen actions
to hide missing geometry. Loops/opposite bowls remain explicit debt if unsupported.

The old four-primitive-per-letter cap is a prototype bound, not a calligraphic
law. GESTURE-002 may introduce a **new opt-in contract with the smallest audited
sufficient cap, at most eight expanded primitive occurrences per letter recipe**.
Keep at most four references per gesture, two alternative recipes per character,
eight named gestures, acyclic references and finite transform envelopes. Retain
old readers/caps; expose actual expansion counts. No silent macro bypass, reflection,
180-degree rotation or unbounded residuals. If the audit needs more than these
bounds or incompatible ports, stop and revise this design before implementing it.

### 5.1 Executed vocabulary decision

GESTURE-002 spec-v1 and run-001 retain all six original primitives byte-for-byte.
New lower-return ports match actual stem-exit/rise-entry tangents; upper-return
ports match rise-exit/stem-entry. Stored old directions differ from those actual
tangents and are reported, not rewritten. The older vertical analytic hypotheses
are not claimed as exact matches: the frozen rise exit cannot reach vertical
within the existing ±20-degree envelope. This does not require broader transforms;
the new return interface is explicitly compatible with the actual frozen strokes.

Each new return has fixed endpoints [0,0] and [0.5,0], one cubic, and two control
handle lengths bounded to 0.12–0.40 along the fixed tangent rays. Generic untrained
initial lengths are 0.28. Independent future targets use endpoint/tangent Hermite
interpolation plus a signed sinusoidal bulge, with no candidate handles, recipe
geometry or search-grid access. Single returns define train/development fixtures;
underturn, overturn and mixed-return attachments are topology-held-out specs.
No target pixels or fitting were used in this audit.

The smallest sufficient cap for the frozen supplied subset is six: i=2, n/u/h=4,
m=6 from two explicit lifted three-piece overturns. Caps four/five cannot contain
that m scaffold. This is not a universal minimum or a claim that all twelve forms
are supported. r/l remain partial; o/a/d/e/g, opposite bowls and lower loops remain
debt. A present upper-loop primitive is not an o/l alias or proof of ink counters.
The new foundation reader rejects unsupported forms, nonfinite/detached geometry,
extra families, recursive/macro references, changed old primitives or dynamic tools.
Legacy readers keep their four-occurrence cap. A failed or missing current-code
baseline still blocks training, regardless of the completed contract Advance.

## 6. Learning, held-out evidence and acceptance

Train only the new return geometry in CURRICULUM-010; freeze the original six
primitive parameters, tool, controller and supplied assembly scaffolds. After
HANDVALIDATE-015 accepts the needed primitive inventory, CURRICULUM-011 may fit
only shared gesture choices/attachments/transforms. No primitive reshaping,
independent letter curves, profile learning or context learning at that stage.

Before targets are rendered or evaluated, freeze independent project-authored
target specifications, train/development/held-out splits, initializations, metrics
and selection rules. Hold out attachment pairings or construction topologies as
well as scales. Merely resizing a known recipe is not the sole transfer test.
Targets must not be emitted by the candidate grammar or copied from the exact
finite search grid. An independent analytic target generator is permitted;
optimizer control points/recipes must not be available to that generator.

Train proposes; development selects; held-out evaluates once after selection.
Include fixed initial/null and placement-only controls where applicable, with at
most three named ablations. No cherry-picking seeds or test-driven fallback to a
different candidate. Report initialization quality; do not deliberately degrade
an existing baseline solely to manufacture relative improvement. Numeric success
never substitutes for documented topology.

Retain established engineering limits: held-out image loss must improve by at
least 25% over nontrivial frozen initialization (ratio < 0.75), actual/desired
loss <= 0.35, contact corridor <= 0.25 mm, convergence image difference <= 0.03
and first/last contact endpoint difference <= 0.01 mm. Use `dt` 0.002/0.001 s and
arc steps 0.025/0.0125 mm, exact subdivision, zero contact/text/owner errors and
local blank/counter ink fraction <= 0.01. Apply required learning/geometry checks
per family and seed; averages cannot hide an absent or failed required family.

Preserve the old global negative-control minimum 0.1 and its known failures.
Also test undeclared lift/air connector, wrong port/direction, detached copied
geometry, extra terminal/overlap contributor and erased counter using predeclared
local regions and exact ownership. A required control not detected blocks that
scope. If inherited metrics are inapplicable, predeclare a justified replacement
before new results; do not relax a failed criterion after observing it.

## 7. Budgets and stop rules

- Motion repair: at most six fixture families, 500 diagnostic renders or 1800 s
  per attempt; zero optimization, one diagnosed revision. Baseline revalidation
  shares the budget, including its actual renders and replay.
- Subsequent user-authorized air-braking follow-up: separate spec-v3 allowance,
  one candidate, 500 renders or 1800 s, zero optimization and no automatic revision.
  It explicitly permits prescribed air braking and acceleration/deceleration around
  contact rest targets, retaining the 12 mm/s nominal ceiling, fixed angle/pressure
  and unchanged acceptance limits. It used 303 renders and retained its sharp-corner
  failure. Presentation rerenders at 900 DPI are charged to this allowance
  and do not replace 180-DPI evaluation or introduce fitted geometry.
- Subsequent user-authorized corner-timing follow-up: separate spec-v4 allowance,
  one candidate, 500 renders or 1800 s, zero optimization and no automatic revision.
  Shared compiled corner/smooth ports, curvature-limited section speeds and planned
  contact rest use unchanged geometry and physical limits. Run-004 used 303 renders
  in 49.002829 s. Corner tracking passes; arc-refinement contact-time convergence
  fails. Another candidate needs separate authorization, not a relaxed timing gate.
- Subsequent user-authorized curve-clock follow-up: separate spec-v5 allowance,
  one candidate, 500 renders or 1800 s, zero optimization and no automatic revision.
  Run-005 uses 303 renders in 22.987616 s and passes. Clean-checkout regression
  separately uses 303 verification renders in 19.227469 s; it is not another
  candidate or allowance for extra search. Existing timing/geometry gates remain unchanged.
- Vocabulary/contract audit: at most eight gesture hypotheses, twelve feasibility
  characters, two proposed families and 100 diagnostic renders or 900 s per
  attempt; zero optimization, one diagnosed revision.
- Each learning Advance: seeds 7/19/41, at most three ablations, 5000 total renders
  or 1800 s per ablation/seed per attempt; one diagnosed revision. Count targets,
  baseline checks, direct/sampled/actual proofs, selection and presentation.
- Each independent evaluation: 5000 renders or 1800 s **per seed including all
  first/replay/control/refinement work**, not a new allowance for each replay;
  zero optimization, at most one diagnosed rerun.
- Preserve every attempt and a cumulative ledger. Unit/clean-checkout regression
  replay is separately labeled verification, never extra candidate exploration.
  A larger budget, more families or another revision needs a new explicit scope.

Stop at the first unmet runtime prerequisite. A learning runner without an
executed accepted-input experiment does not complete its learning Advance.
Failures remain findings, not passes. Do not invent source assignments, reviews,
metrics or model acceptance to keep the phase moving.

## 8. Visible deliverable and exit decision

Write immutable bundles under
`shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/` with
motion, contract, primitives, primitive evaluation, gestures and final evaluation
subdirectories. Publish one browsable index linking enlarged initial / independent
target / learned nominal / sampled desired / actual panels at equal physical scale.
Overlay direction, ports, contact events and constituent identities separately
from clean ink. Show unseen attachment failures as prominently as successes.

Success means stable actual contacts plus learned return primitives and shared
underturn/overturn/compound transfer—not a recovered historical hand or a learned
alphabet. The final report must name accepted and missing inventory, code/model/
tool identities, per-seed failures and the exact permissible next experiment.

Wire an explicit new manifest reader to verified current foundation evidence;
retain replay of old pinned reports without granting them admission. A JSON
`pass` label, edited hash or completed Advance cannot bypass independent checks.
Foundation success alone does **not** supply S1-action or authorize CURRICULUM-005.
Then scope fresh action/null-profile validation only for named required forms;
use new records/evidence for the unexecuted candidate work, rather than reopening
or treating HANDVALIDATE-014's early-stop record as a pass. Real fitting additionally
requires live G0 and accepted real layers; G1 reading/appearance and G2 actual
fidelity remain mandatory. Fatigue, depletion and folios stay deferred.
