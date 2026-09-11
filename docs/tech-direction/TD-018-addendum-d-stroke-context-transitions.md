# TD-018 Addendum D — Neighbor-aware stroke forms and transitions

**Current next-step revision:** [Addendum E — Neighbor-dependent boundary
construction](TD-018-addendum-e-boundary-construction.md) replaces the next
hypothesis-selection step after the owner found the tiny terminal-handle
examples indistinguishable. Preserve this design's historical scope and all
frozen contracts; no old bounds or execution approvals are extended.

Status: **owner-approved direction; design and bounded advances prepared**.
Date: 2026-09-10. This is planning authorization, not permission to execute a new
physical experiment, alter frozen inputs, widen bounds or begin fitting.

## 1. Decision: keep the foundation, change the next question

The owner finds the ±3% width/±0.05 advance previews almost indistinguishable and
agrees that entry/body/exit stroke relationships are a better next step than a
large preference exercise over those small changes. Pause CURRICULUM-006 P3's
width/spacing rankings and subsequent selection. Do not convert this feedback
into 54 tied rankings, appearance rejection, a new target or permission to
increase deformation. Preserve any browser drafts and every frozen packet.

P1/P2a and P2b's mechanical result remain valid **within their original scope**:
1464 independent cases, 324 presentations and exact three-seed replays. These
prove reliable bounded affine changes, not meaningful contextual handwriting,
connectors, natural variability, historical style or human preference.

The next question is: **can a shared stroke program adapt its entry and exit to
both neighboring port states, while preserving the letter's body and choosing
an explicit, appropriate boundary transition?** Connection is a hypothesis, not
a universal goal. Separate lettering can be a correct outcome.

## 2. Current implementation and evidence boundary

- The frozen n/u/m candidate has shared primitives, gesture constructions and
  fixed actions. `connected_contract.py` supports explicit smooth/corner/lift
  semantics within its admitted construction scope; it rejects context rules.
- A pen-down upward return inside a letter already exists. “Upstroke” does not
  mean “lift.” Do not reintroduce the earlier artificial lifts between strokes.
- The C006 adapter applies following-entry-conditioned whole-letter horizontal
  scale and following-letter advance. It does not change a letter's form in
  response to the previous letter, or implement an admitted inter-letter join.
- Canonical geometry, tool/action settings and accepted appearance references
  remain the baseline. A new context model must preserve an exact context-off
  path; old source/report hashes may not be silently repinned.

Pinned baseline evidence, relative to `letter_context/physical-validation-v1/`:

| Evidence | SHA-256 |
|---|---|
| Original physical contract | `db909d00cd3d7c26cff021e2c9ff9ad19a6ebb8ca08bfd873bd41dd13d443eb5` |
| Original failure manifest | `adec239210591bf83b37abbe22543012e89ed5912fea2aea359be4e958fd086e` |
| Recovery contract | `1b454630045689f257ac322f1334cebf614c106d748ca00301f5edfcde01b405` |
| Recovery report | `e294db3edc76d2d22f28548e8a5f54834c61e9c3d543b6102410a274ce20dc98` |
| Complete dimension-corrected independent inspection | `251d4fd3ff6a9c11ea0162b2b73108d679e22fa6ea7fd2a82756e103fdaddb5b` |

The paused owner packet object pin is
`a928389737c6e6c0ff0c2598dc66b625e9b8e13a3dfd6ee63c61423d438a4331`.
Historical failures, local budgets, unresolved admission flags and numerical
style failures remain recorded. No new S1/S2/real-hand admission follows here.

## 3. Proposed layered representation

Use existing `gesture`, `curriculum`, `handvalidate`, `pathguide` and `handflow`
components. No new service, GPU infrastructure or LLM-in-the-loop judge is needed
for this design. New opt-in modules should initially live under
`scripts/stroke_context_*.py`; evidence under `stroke_gestures_v2/stroke_context_v1/`.
These are planned paths, not implemented interfaces or accepted checkpoints.

### Canonical stroke program → contextual occurrence → physical execution

1. **Canonical program:** immutable primitive/gesture/action/recipe IDs and bytes.
2. **Semantic spans:** entry, body and exit roles mapped to explicit canonical
   occurrences and cubic parameter ranges. They are not three arbitrary image
   crops, and need not correspond to three separate physical strokes. Any shared
   or overlapping role span needs declared ownership and an unambiguous edit rule.
3. **Context request:** current recipe, previous exit class/state or BOS,
   following entry class/state or EOS, and approved transition intent. Rule keys
   may not contain full words, fixture IDs, seed IDs or arbitrary per-instance
   residuals. A letter's identity is legitimate; word memorization is not.
4. **Derived occurrence:** named shared rule, affected span IDs, bounded parameter
   values, anchor/port changes, canonical-to-derived lineage and required overlap
   contributors. Body geometry is unchanged by default; any body exception must
   be explicitly investigated, bounded and separately approved.
5. **Execution contract:** exact contact-run, timing, ownership and tool states,
   including any transition segment. Compilation is not physical acceptance.

The audit must discover span boundaries and port classes from the actual n/u/m
programs; it must not infer them solely from screenshots or hard-code a font-like
alternate glyph table. BOS/EOS are explicit null neighbors, not hidden rules.

### Entry and exit port state

Each relevant port describes position, directed tangent, contact intent,
fixed nib/action state, feasible approach/departure region and continuity kind.
Keep positional continuity distinct from tangent continuity and velocity timing.
An intentional reversal is not a smooth join just because its endpoints coincide.
Zero-length tangents, duplicate exact events and undocumented contact changes
must fail closed. Investigation must identify unsupported port combinations.

### Boundary transition is an explicit decision

| Kind | Meaning | Required evidence |
|---|---|---|
| Pen-down join | A declared path connects compatible exit/entry states | Full finite-nib containment, truthful continuity/timing, cross-letter ownership |
| Pen-down retrace | Motion deliberately returns along existing ink | Contact retained, bounded overlap, both contributors, reversal/corner timing |
| Pen-up transfer | The pen actually leaves the page before the next stroke | Explicit lift/air/landing events; no painted connector or hidden contact |
| Unresolved/unsupported | No approved transition exists | Reject or retain the approved baseline; never silently bridge the gap |

Retracing is not an automatic substitute for a connector. A connector is not an
unowned decoration added after rendering. Letter ownership remains separate from
contact-run identity even if one contact run spans two letters. The legacy
context-off separation must remain exactly reproducible.

## 4. Bounded n/u/m investigation and demonstrator

### Initial scope

- Only the frozen n/u/m construction and fixed tool: x-height 3.5 mm, full-edge
  0.45 mm nib, 40-degree angle, pressure 0.5 and existing 12 mm/s speed cap.
  Preserve existing action/timing limits, baseline/x-height and primitive IDs.
- Inventory existing spans and boundary states first. At most **three transition
  families** (join, retrace, lift), with unsupported outcomes recorded explicitly.
- After owner review of that inventory, freeze at most **four deterministic
  hypotheses including context-off**, each with a finite list of allowed local
  parameters. No stochastic fitting, autonomous search or large alternative table.
- At most **15 distinct strings** in the initial diagnostic shortlist: isolated
  n/u/m; nine already exposed pairs nn/nm/un/um/mn/mm/nu/uu/mu; and proposed
  diagnostic triples nuu/uuu/muu to compare the same middle u and following u
  against different preceding letters. The audit must verify provenance and
  reservations before admitting any new triple. They are design/training probes,
  never subsequently relabeled unseen tests.
- Following-neighbor effects can first be isolated using the paired first-letter
  controls (e.g. un versus um), with the previous boundary fixed at BOS. Previous
  effects use the triple controls with the following neighbor fixed. This pilot
  does not claim exhaustive two-sided interactions for all letters or neighbors.

The audit may narrow the shortlist; enlarging it needs explicit scope/budget
review. The number of strings is not an execution allowance: hypothesis ×
refinement × arm × seed × replay × image/control costs must be enumerated.
The paused C006 sealed set remains reserved and may not be opened for design,
tuning or preference elicitation. Any later held-out transfer protocol must
freeze its provenance/split before hypothesis selection or new image inspection.

### What an informative comparison must show

For each admitted contrast, distinguish:

1. context off;
2. entry/exit form adaptation without a connector;
3. transition-only behavior with unchanged form, where geometrically valid;
4. their combined behavior, where both are supported.

These are proposed diagnostic arms, not a demand to fabricate all combinations.
An impossible transition-only arm must be explained, not repaired by changing
its supposedly unchanged body. Match advances when isolating shape and remove
only declared overall placement when computing canonical control-point deltas.
Show previous-only and following-only interventions separately before claiming
their interaction. Do not substitute whole-letter width changes for local forms.

Use fixed-scale full-frame actual/desired views, a labeled stroke/ownership
breakdown, contact/lift timeline and canonical/derived port display. Optional
synchronized zoom, blink and difference overlays are **diagnostic views only**,
clearly labeled and always paired with untouched full-frame evidence. They may
not become metric inputs, acceptance from cropped content or replacement targets.
Preserve the exact renderer dimension contract; do not repeat independent
ceil/downsize assumptions in another reader.

“Visibly meaningful” means the owner can identify the changed stroke or boundary
and explain its relevance at normal review scale. Record “indistinguishable,”
“unnecessary,” “less readable” and “separate lettering preferred” as valid outcomes.
Do not optimize a difference heatmap, reward maximum deformation or invent a
pixel-count aesthetic threshold. If the model cannot yield informative examples
within approved bounds, return to design rather than expanding them automatically.

## 5. Evaluation and stop gates

Keep five decisions separate:

- **Representation:** truthful spans, ports, rules, contact intent and lineage.
- **Mechanical validity:** motion, exact-event timing, full finite-nib/global/local
  containment, baseline/x-height, collision/overlap contributors and fixed actions.
- **Causal context effect:** changing the selected neighbor changes only approved
  spans/transition behavior; wrong-neighbor, no-context and identity controls do
  not leak the effect. Spacing-only and matched-advance ablations remain explicit.
- **Owner appearance/usefulness:** concrete judgments bound to exact examples and
  source identities, without forced ranks or automatic admission.
- **Transfer:** frozen rule reuse on composition-disjoint, provenance-audited
  fixtures, not seed changes or previously seen pairs presented as novelty.

Required adverse controls include unowned connector, fake lift, pen-down motion
mislabeled air, false smooth reversal, invalid port, missing retrace contributor,
undeclared body change, previous/next selector swap, word/fixture-keyed rule,
cropped image, changed DPI/frame, duplicate exact boundary and forged provenance.
Null geometry/planning/action outputs and saved baseline pixels remain exact.
No aggregate improvement may override a failed local/contact/ownership gate.

HANDVALIDATE-025 must freeze the full physical inventory, independent reader,
numeric criteria and resource budget **before** any physical run. Existing
numeric thresholds remain unchanged; missing transition-specific metrics are
proposed and owner-approved before outcomes, never calibrated from failures.
HANDVALIDATE-026 separates readable/useful, no meaningful effect, separate
lettering preferred, unsupported and failed outcomes. Completion is not fitting
authorization, broad contextual acceptance or proof of historical scribal behavior.

## 6. Budget, evidence and implementation gates

This revision performs **zero new simulations, physical renders or fitting**.
All existing source, candidate, image, owner packet and receipt pins stay intact.
Do not add identity-scanned `spec-*.json` files or change `scribesim/**/*.py`
under the old contract as part of this planning work. Any necessary future core
change needs an explicit migration/baseline-validation plan, not a hash refresh.

Existing remaining C006 allowances are unchanged:

| Seed | Seconds remaining | Render calls remaining |
|---|---:|---:|
| 7 | 582.1848200419918 | 3426 |
| 19 | 988.4159828750417 | 3426 |
| 41 | 579.0667824570555 | 3259 |

A new phase name does not reset those costs. The new transition inventory has
no measured timing estimate yet and inherits **no fresh execution allowance**.
Preflight must enumerate work and storage headroom and propose explicit cumulative
or separately approved accounting. No automatic retries, geometry changes,
threshold relaxation or deletion of failed evidence is permitted.

## 7. Advances and order

New phase: **td018-stroke-context**. Existing components own the work; no new
component is necessary. New advances are planned, not implemented or accepted.

| Order | Advance | Deliverable / gate |
|---|---|---|
| 1 | [GESTURE-004](../../arrive/systems/scribesim/advances/ADV-SS-GESTURE-004.md) | Read-only entry/body/exit and contact/port investigation; owner reviews supported hypotheses |
| 2 | [GESTURE-005](../../arrive/systems/scribesim/advances/ADV-SS-GESTURE-005.md) | Opt-in contextual-span and transition contract with exact null and adverse tests |
| 3 | [CURRICULUM-016](../../arrive/systems/scribesim/advances/ADV-SS-CURRICULUM-016.md) | Bounded deterministic demonstrator and informative nominal comparison protocol; no fitting |
| 4 | [HANDVALIDATE-025](../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-025.md) | Independently verified, explicitly budgeted actual-motion and boundary evidence |
| 5 | [HANDVALIDATE-026](../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-026.md) | Owner usefulness/appearance review and separately gated frozen-rule transfer assessment |

The first advance consumes C006's specifically pinned **P2 mechanical evidence**,
not completion of the whole C006 umbrella; otherwise the dependencies would form
a deadlock. C006 remains in progress with its old P3/P4/P5 exercise paused.
Later word-context work remains downstream of an explicit contextual checkpoint
and owner decision, not merely the completion of these planning documents.

Natural correlated variation is deliberately later: first distinguish purposeful
context adaptation from execution error. Pressure/angle modulation, rhythm,
ink depletion, fatigue, new alphabets and unconstrained allographs are not part
of this pilot. Precise deterministic replay remains a diagnostic capability even
if a later, separately approved stochastic model produces varied handwriting.

## 8. Planning validation

The five new template-derived frontmatters parse as planned, with empty execution
evidence and unset implementation-completion timestamps. Plan validation,
generated-rule checks and whitespace checks pass; the new dependency graph is
acyclic, all local document links resolve, and word context explicitly depends
on the new owner/transfer checkpoint. Original/recovery artifact maps, frozen
source contracts, the old owner packet and all 54 review images are reverified
unchanged. This revision changes documentation/governance only; it does not run
behavioral tests, simulations or fitting, and claims no provider CI or merge.
All changes remain uncommitted.
