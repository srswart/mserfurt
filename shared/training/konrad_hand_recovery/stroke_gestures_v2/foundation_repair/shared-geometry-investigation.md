# Shared geometry / target mismatch investigation

2026-09-08 · baseline `4fe4cf7` · analytical investigation only

## Decision

Repair the shared-geometry learning contract before adding pen actions or
letters. Two distinct limitations are present: the admitted scale grid misses
the target proportions, and immutable return curves retain shape differences
that uniform scaling cannot eliminate. A finer grid is a useful first bounded
experiment, **not a demonstrated complete fix**.

No candidate was fitted, selected, rendered or promoted in this investigation.
No controller, primitive, target, threshold, acceptance report or historical
artifact was changed. The current independent result remains underturn-only
fixed-tool null acceptance; overturn and compound remain unresolved.

## Evidence and scope

Inputs are the frozen [candidate](actions/run-001/seed-7/first/candidate.json),
[learning specification](gestures/spec-v2.json),
[independent target specification](evaluation/spec-v1.json), saved selections
for [seed 7](gestures/run-003/seed-7/attachment/first/selection.json),
[seed 19](gestures/run-003/seed-19/attachment/first/selection.json) and
[seed 41](gestures/run-003/seed-41/attachment/first/selection.json), and
[completed independent evaluation](action_evaluation/run-003/S1-actions.json).

The two target dictionaries are exactly equal. Moreover, the gesture return
targets are scaled versions of the earlier independent
[primitive targets](contract/spec-v1.json): endpoint `0.5 × 0.87 = 0.435`,
entry magnitude `0.66 × 0.87 = 0.5742`, exit magnitude
`0.87 × 0.87 = 0.7569`, and bulge `0.035 × 0.87 = 0.03045`.
This is not evidence of a target accidentally changing between learning and
evaluation. Independent here means candidate-independent analytic targets and
separate evaluation, not a new historical hand or new target-shape family.

### 1. Most of the failing image loss already exists in the plan

Saved scale-1 training measurements from CURRICULUM-012:

| Construction | Nominal / target | Base actual / target |
|---|---:|---:|
| [Underturn](actions/run-001/seed-7/first/train-underturn.json) | 0.044376 | 0.042522 |
| [Overturn](actions/run-001/seed-7/first/train-overturn.json) | 0.099454 | 0.100653 |
| [Compound](actions/run-001/seed-7/first/train-compound_curve.json) | 0.098227 | 0.096860 |

These are ink-normalized image differences, not millimetres or percentages of
artistic quality. `stroke_loss` divides summed absolute ink difference by summed
target-plus-candidate ink. They are not diluted simply by surrounding white
paper. The controller changes these scores only slightly; that does not
decompose every pixel error, but it establishes that execution is not the
primary explanation for these two failures.

### 2. Proportions miss the target and accumulate through attachments

For a frozen primitive endpoint displacement `d` and target displacement `e`,
endpoint-compatible uniform scale is `(d · e) / (d · d)`; all four residuals
`scale × d - e` are zero to floating precision at the diagnostic scales below.

| Family | Frozen scale | Endpoint-compatible scale | Frozen local exit gap, mm |
|---|---:|---:|---:|
| Stem | 0.85 | 0.83 | 0.070000 |
| Rise | 1.15 | 1.17 | 0.078262 |
| Lower return | 0.85 | 0.87 | 0.035000 |
| Upper return | 0.85 | 0.87 | 0.035000 |

None of `0.83`, `1.17`, `0.87` is in the frozen search grid
`[0.75, 0.85, 0.95, 1, 1.05, 1.15, 1.25]`.
These endpoint-derived numbers describe representability; they are **not a new
selected candidate** or permission to copy target parameters into one.

Attachments preserve exact source endpoint coincidence, so earlier dimensional
errors translate subsequent strokes. At fixture scale 1, final nominal-minus-
target displacement in physical page coordinates is:

| Construction | Horizontal, mm | Vertical, mm | Distance, mm |
|---|---:|---:|---:|
| Underturn | -0.070 | +0.140 | 0.156525 |
| Overturn | -0.070 | +0.140 | 0.156525 |
| Compound | -0.105 | +0.140 | 0.175000 |

These are target-relative geometric errors, not controller tracking errors or
gaps between adjoining source strokes. Underturn and overturn have the same
final displacement but very different image losses: endpoint error alone is
not an adequate quality measure. Stroke order, intermediate placement, return
shape and the fixed nib footprint affect the painted comparison.

### 3. Finer proportions alone do not remove the shape mismatch

A cubic with controls `P0..P3` has endpoint derivatives `3(P1-P0)` and
`3(P3-P2)`. Their directions agree with the independent target rays to numerical
precision (largest measured angle below `4e-15` degrees). This is not a newly
discovered wrong-port-direction bug. Their magnitudes do not all agree:

| Return | Scale needed for endpoint | Scale needed for entry derivative | Scale needed for exit derivative |
|---|---:|---:|---:|
| Lower | 0.870000 | 0.832174 | 0.681892 |
| Upper | 0.870000 | 0.638000 | 0.813871 |

No one uniform scale can satisfy those three parameterized constraints. The
target also contains a nonzero `sin(pi*t)^2` bulge, outside a single cubic's
polynomial basis. Exact parameterized target reproduction is unavailable;
adequate image approximation may still be possible and must be measured.
Derivative magnitudes are with respect to curve parameter, **not pen speed**.

To separate inherited translation from local shape, subtract each primitive's
own start and compare it to its local analytic target at the same parameter.
The second column below uses the frozen scale. The third substitutes only the
endpoint-compatible scale mathematically, without constructing or rendering a
replacement candidate:

| Family | Frozen local maximum, mm | Endpoint-normalized local maximum, mm |
|---|---:|---:|
| Stem | 0.070000 | 0.014000 |
| Rise | 0.078262 | 0.014000 |
| Lower return | 0.072407 | 0.062256 |
| Upper return | 0.055946 | 0.067533 |

Maxima use 4097 uniform parameter samples; a separate 257-sample calculation
differs by less than `0.000005 mm`. These are same-parameter diagnostics, not
Hausdorff distances, rendered-image scores, continuous maximum certificates or
acceptance thresholds. In particular, the upper return's local diagnostic
gets worse when its endpoint is corrected. Do not promise a fine-grid pass.

### 4. The optimizer selected correctly for its declared objective

All three saved searches contain all 343 unique grid triples. Their minimum
training mean is `0.0806856944283797`, at `[0.85, 1.15, 0.85]`.
The same triple wins the development shortlist at `0.07263735435829184`.
There is no evidence of a lost best proposal, seed-dependent selection or a
shortlist bug. The seeds reproduce the same solution, not three learned hands.

Because even the minimum training mean exceeds `0.05`, **no recorded grid
triple made all three training nominal image losses at most 0.05**. Changing
the selector alone cannot make that particular grid satisfy this condition.
This statement does not assert an unmeasured actual-controller result for
every proposal.

The contract nevertheless needs adjustment for future work: CURRICULUM-011
selects by mean nominal train/development loss and gates relative improvement
(`<0.75`). CURRICULUM-012/HANDVALIDATE-017 require absolute actual/target loss
`<=0.05`, including every occurrence and refinement. A relative learning pass
was valid for its stated scope but was not an absolute-accuracy admission.

## Recommended next bounded work — not executed

1. **Specify a new geometry-accuracy learning/evaluation pair.** Preserve old
   reports, candidates and targets. Freeze splits, budgets, controls and failure
   policy before scoring; require absolute per-construction/local criteria as
   well as motion, blank-region and lineage checks. Means remain diagnostics,
   not substitutes for a failing construction. Permit an explicit no-pass result.
2. **First isolate scale resolution.** Compare the frozen baseline with a
   predeclared uniformly refined neighborhood around its three shared scales,
   retaining immutable primitives, exact attachment offsets and the fixed tool.
   Select only on train/development. Do not install the endpoint-derived triple
   directly or select from the already inspected independent fixtures.
3. **If absolute residuals remain, return to the shared primitive layer.**
   Investigate bounded return-handle accuracy under the same ports and endpoint
   constraints, then independently readmit the changed primitives before gesture
   relearning. Share each primitive across all constructions; do not hide the
   problem in per-occurrence copies, per-letter warps or pen-action compensation.
   Reassess the existing handle parameterization before adding a new curve basis.
4. **Independently evaluate frozen replacements.** Retain the `0.05` limit and
   full-frame/contact/refinement/ownership/blank/counter checks. Old independent
   fixtures are now regression evidence, not untouched holdouts; freeze additional
   withheld fixtures for a new claim. Publish native target/nominal/desired/actual
   sheets and component-local geometry diagnostics. Readmit the complete changed
   chain, including the currently accepted underturn, rather than transferring its
   acceptance to different candidate bytes.

No letters, words, fatigue, dynamic nib actions or historical-hand acceptance
are opened by this investigation. No new Advance is marked complete, and no
new fitting budget or protocol continuation is implied.

## Reproduction and integrity

This analysis reads JSON and evaluates analytic arrays only. For each primitive:

- `B(t) = (1-t)^3 P0 + 3(1-t)^2 t P1 + 3(1-t)t^2 P2 + t^3 P3`.
- `T(t) = (t-2t^2+t^3) entry + (3t^2-2t^3) end
  + (t^3-t^2) exit + sin(pi*t)^2 bulge`.
- Local diagnostic: `3.5 * max(norm(scale*(B(t)-P0)-T(t)))`.
- Attachment displacement: transform source endpoints by their saved reference
  scale and offset; subtract cumulatively assembled target endpoints; multiply
  by `[3.5,-3.5]` for page millimetres. Common page translation cancels.

Read-only checks verified equality of the learning/evaluation target dictionaries,
343 unique proposals and the selected train minimum for every seed, exact
endpoint-scale compatibility, and the two sampling densities above. No runtime
test suite or new physical rendering was run for this documentation-only change.

| Input | SHA-256 |
|---|---|
| Frozen candidate | `d8b26fba2655b0bba961865fb74b543829cb1b11ac850afd672dd02ba0822e5a` |
| Learning specification | `030bc8c36399d153b0917cecab6af1e610f3a97e3d84d9691261230ae3db6c8f` |
| Independent target specification | `71a857879bafe4e3c6f2c84ea13f6d57c0f6d6fe67a69c080e5ad836917cf35d` |
| Seed-7 selection | `83d262854699b57f42522bb24bfc753226ce57b00b7586e168e3845e70748035` |
| HANDVALIDATE-017 report | `90f26d501d8860717bf8c40d394c7a25df679c8e63d4b58995ecba3e61fba2ef` |
