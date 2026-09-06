# Return vocabulary and port audit

**Nominal synthetic feasibility only. No new training or actual-motion acceptance.**

## Primitive direction and port table

Angles are degrees in local x-height coordinates, y up. Actual endpoint tangents govern attachment;
the old stored declarations are retained, not silently rewritten. New return handles may move only on frozen rays.

| Primitive | Start → end | Actual entry / exit | Stored entry / exit | Closed |
|---|---|---|---|---|
| stem | [0, 1] → [0, 0] | -86.186 / -87.879 | -45.000 / -59.036 | False |
| rise | [0, 0] → [0.5, 1] | 72.255 / 62.241 | 111.801 / 26.565 | False |
| bowl | [0, 1] → [0.65, 0] | -12.665 / -119.055 | -4.764 / -167.471 | False |
| turn | [0, 0] → [0.5, 1] | 69.228 / 86.228 | 108.435 / 105.524 | False |
| loop | [0, 0] → [0, 0] | 112.816 / -123.071 | 100.620 / -122.005 | True |
| exit | [0, 0] → [0.45, 0.15] | 8.130 / -33.690 | -60.945 / -53.130 | False |
| lower-return | [0, 0] → [0.5, 0] | -87.879 / 72.255 | -87.879 / 72.255 | False |
| upper-return | [0, 0] → [0.5, 0] | 62.241 / -86.186 | 62.241 / -86.186 | False |

[Eight primitive shapes, including two untrained returns](primitive-ports.png)

## Eight gesture hypotheses

These are role/topology hypotheses, not exact reproductions of the older analytic centerlines.
In particular, the frozen rise exit cannot reach vertical with only ±20° rotation. Return ports
therefore match actual stem/rise tangents; no reflection, larger rotation or old-geometry fit is introduced.

| Hypothesis | Expansion / count | Contact and counter | Status / debt |
|---|---|---|---|
| stem | stem / 1 | one continuous gesture; none | existing: Declared directions differ from actual frozen tangents; actual ports govern attachment |
| rise | rise / 1 | one continuous gesture; none | existing: No claim of arbitrary vertical rise under existing rotations |
| underturn | stem + lower-return + rise / 3 | one continuous gesture; open channel | untrained-extension: New lower return requires fitting and independent acceptance |
| overturn | rise + upper-return + stem / 3 | one continuous gesture; open arch | untrained-extension: New upper return requires fitting and independent acceptance |
| compound_curve | upper-return + stem + lower-return + rise / 4 | one continuous gesture; open channels | untrained-extension: Shared four-piece hypothesis, not an accepted m recipe |
| left_bowl | missing / None | unsupported; open left-side bowl | unsupported: Existing bowl bulges in the opposite direction; reflection/180-degree rotation forbidden |
| upper_loop | loop / 1 | one continuous gesture; requires ink-level evaluation | existing-primitive-only: Primitive topology exists; l attachment and counter preservation remain unaccepted |
| lower_loop | missing / None | unsupported; closed lower counter | unsupported: Existing upper loop cannot become a descender through allowed transforms |

[Six representable gesture hypotheses](gesture-expansions.png)

## Twelve-character feasibility checklist

| Character | Expansion / count | Topology | Status / debt |
|---|---|---|---|
| i | stem + exit / 2 | two explicit contacts; supplied stem-terminal scaffold | construction: Not trained letter construction or historical reading |
| n | stem + rise + upper-return + stem / 4 | stem plus lifted three-piece arch | construction: Upper return untrained |
| u | stem + lower-return + rise + stem / 4 | continuous three-piece lower return plus lifted downstroke | construction: Lower return untrained |
| m | rise + upper-return + stem + rise + upper-return + stem / 6 | two explicit lifted arches | construction: Not a continuous seven-piece alternative; no claim of learned m |
| r | not admitted / 2 | stem/shoulder fragment only | partial: Shoulder-to-terminal form and reading unresolved; no r recipe admitted |
| o | not admitted / None | closed counter required | unsupported: Opposite-bowl/closure pairing missing; upper loop is not an o alias |
| a | not admitted / None | counter plus downstroke required | unsupported: Counter construction/attachment missing |
| d | not admitted / None | counter plus ascender required | unsupported: Counter construction/attachment missing |
| e | not admitted / None | eye and entry/crossing required | unsupported: Eye/counter and ordered crossing unresolved |
| l | not admitted / 2 | loop/downstroke fragment | partial: Loop attachment and preserved ink counter unproven; no l recipe admitted |
| h | stem + rise + upper-return + stem / 4 | 1.5-scale ascender plus lifted arch | construction: Untrained upper return; existing scale bound retained |
| g | not admitted / None | body and descender loop required | unsupported: Lower loop and counter inventory missing |

[Five supplied construction scaffolds, not learned letters](construction-checklist.png)

## Composition decision

Minimum sufficient among these frozen supplied constructions, not a universal calligraphic lower bound: m uses two explicit lifted three-primitive overturns, total six. Caps 4 and 5 reject it; 6 suffices. No macro collapse, hidden returns or requirement to accept all twelve characters.

Four references per gesture, eight primitive families, eight named gestures and two alternatives
per character remain bounded. The new reader accepts six actual primitive occurrences per recipe;
the old reader still rejects more than four. Unsupported forms fail rather than aliasing a loop or bowl.

## Attachments

| Construction | From → to | Transition | Gap (x-height) | Tangent dot |
|---|---|---|---|---|
| i | stem → exit | lift | 0.00000000 | -0.10468478 |
| n | stem → rise | lift | 0.00000000 | -0.94049132 |
| n | rise → upper-return | smooth | 0.00000000 | 1.00000000 |
| n | upper-return → stem | smooth | 0.00000000 | 1.00000000 |
| u | stem → lower-return | smooth | 0.00000000 | 1.00000000 |
| u | lower-return → rise | smooth | 0.00000000 | 1.00000000 |
| u | rise → stem | lift | 0.00000000 | -0.85197728 |
| m | rise → upper-return | smooth | 0.00000000 | 1.00000000 |
| m | upper-return → stem | smooth | 0.00000000 | 1.00000000 |
| m | stem → rise | lift | 0.00000000 | -0.94049132 |
| m | rise → upper-return | smooth | 0.00000000 | 1.00000000 |
| m | upper-return → stem | smooth | 0.00000000 | 1.00000000 |
| h | stem → rise | lift | 0.00000000 | -0.94049132 |
| h | rise → upper-return | smooth | 0.00000000 | 1.00000000 |
| h | upper-return → stem | smooth | 0.00000000 | 1.00000000 |

A lift does not require tangent continuity; every lift remains explicit. Continuous smooth joins
require coincident ports and matching tangents. Ink counters and actual dynamics are not evaluated here.

## Independent targets and next step

[Frozen target specifications](target-specs.json) define analytic endpoint/tangent targets with an
additional sinusoidal bulge. The generator consumes no candidate handles, recipes or search grid.
Targets are not rendered or scored in this audit. Initialization is a generic 0.28-handle return,
not deliberately degraded from a previously accepted return (none exists).

Single returns form train/development fixtures; underturn, overturn and mixed-return attachments
are topology-held-out specifications. Before fitting, CURRICULUM-010 must freeze its full learning
protocol and rerun current-code motion/baseline checks within its own budget. The pre-audit motion
proof is historical provenance after this compiler change, not fresh admission.

[Initial untrained model](initial-model.json) · [Machine-readable audit](report.json) · [Freeze](freeze.json)
