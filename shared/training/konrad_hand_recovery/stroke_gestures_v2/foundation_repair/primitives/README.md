# Learning the lower and upper returns

CURRICULUM-010 consumes the GESTURE-002 contract and fits only the four permitted
handle lengths: two for each shared return. Old-six geometry, endpoints, tangent
rays, fixed tool, controller and supplied construction scaffolds cannot change.
This is synthetic primitive learning, not historical handwriting or letter learning.

## Result: fitted, but completion blocked by the comparison frame

Run-002 executes all three seeds after fresh 239/239 motion/baseline admission.
Each seed selects identical shared handles: lower return **0.23/0.37**, upper
return **0.30/0.31**, versus frozen initialization **0.28/0.28**. Exhaustive search
order differs by seed; no held-out score selects a seed or replacement candidate.

| Held-out fixture | Learned / initial full-image loss | Result, every seed |
|---|---:|---|
| Lower return, unseen scale | 0.328928 | Pass |
| Upper return, unseen scale | 0.287814 | Pass |
| Underturn attachment | 0.409520 | Pass |
| Overturn attachment | 0.232461 | Pass |
| Compound attachment | 0.289710, **cropped** | **Fail: lower-return local loss undefined** |

The measurable required family ratios are also below 0.75; the worst of the four
valid fixtures is 0.409886. These are roughly **59–77% lower losses**, not claims
of artistic quality or historical accuracy. The full compound average must not
hide its missing lower-return measurement. Its endpoint is y=13.15 mm, beyond the
frozen frame's y=13 mm edge. The candidate and actual trace contain the stroke;
the image omits it. No full-frame compound image benefit is established.

All reported motion/refinement checks pass; maximum contact lag is 0.005516 mm
and maximum refinement endpoint difference is 0.001024 mm. Image-based motion
metrics still inherit the cropped frame and cannot certify the omitted region.
Original geometry, actions, ports and scaffolds are unchanged in all candidates.

- [Seed 7 practice sheet](run-002/seed-7/practice-sheet.png), [ports](run-002/seed-7/ports.svg), [candidate](run-002/seed-7/candidate.json), [metrics](run-002/seed-7/report.json)
- [Seed 19 practice sheet](run-002/seed-19/practice-sheet.png), [candidate](run-002/seed-19/candidate.json), [metrics](run-002/seed-19/report.json)
- [Seed 41 practice sheet](run-002/seed-41/practice-sheet.png), [candidate](run-002/seed-41/candidate.json), [metrics](run-002/seed-41/report.json)
- [Failed experiment report](run-002/report.json), [budget ledger](ledger.json), [clean verification](verification.json)
- [Measurement-only follow-up proposal — approval pending](measurement-request.md)

Run-002 uses 2134/1831/1831 renders and 208.406950/193.208989/193.558916 seconds
for seeds 7/19/41; seed 7 includes all 303 fresh baseline renders. Total: 5796
renders and 5046 optimization evaluations. The stopped first attempt adds 1158
renders. Neither exceeds its per-seed cap. Clean hash-seed-839 replay reproduces
all **111 non-wall-clock artifacts byte-for-byte**, including the failures, with
5796 separately labeled verification renders. Expanded local and clean tests each
have **150 passes and one pre-existing missing-nib-angle constructor failure**.
Twelve new tests pass. ARRIVE retains ten old artifact issues and the installed
strict PR-ID parser limitation; no provider CI or human review is claimed.

**CURRICULUM-010 stays in progress and unmerged.** One automatic revision is used.
Do not repeat fitting: the proposed next work remeasures the same frozen candidates
in a complete frame, with unchanged criteria and zero optimization, only after
explicit authorization. HANDVALIDATE-015 remains a separate acceptance decision.

## Frozen experiment

- [Initial protocol](spec-v1.json), committed before target rendering or search;
  [one diagnosed numeric revision](spec-v2.json) retains the same grid, targets and gates.
- Initialization is the unchanged GESTURE-002 model, handles 0.28/0.28.
- Targets use independent analytic Hermite interpolation plus a sinusoidal bulge;
  the generator cannot access candidate handles or recipes.
- Seeds 7/19/41 each search the same predeclared two-handle grid in shuffled order.
  Training ranks eight finalists; development alone selects. Exhaustive search
  can legitimately produce identical selected models across seeds.
- Single returns train; different scales select. Two unseen single scales plus
  underturn, overturn and mixed-return compound topologies evaluate only after
  checkpoint selection. No held-out fallback is permitted.
- Fixed initialization is the null control. Placement-only is identical because
  ports and placement cannot move. Empty-image sensitivity is reported separately.

## Execution and evidence boundary

The runner first reruns the existing full motion protocol and read-only original
six-primitive revalidator under current identities. It stops before target access
if admission fails. That setup is charged to seed 7, not treated as a free run or
a new motion-repair candidate. Nested baseline metadata retains the reused motion
protocol's historical allowance name; the enclosing learning ledger owns this work.

Each seed has a maximum of 5000 renders or 1800 seconds, including targets,
baseline setup, search, selection, held-out, actual/refinement and presentation.
Fixed/null evaluation shares that same conservative budget. Unit and clean-checkout
replay are separately labeled software verification, not extra candidate searches.

Metrics apply per fixture and per participating return family, not merely to an
alphabet-wide mean. Actual traces retain contact and primitive ownership. Required
proofs compare timestep, arc density and exact cubic subdivision. The subdivision
proof uses an isolated existing-v2 execution copy, not a modified fitted model or
a relaxation of the one-cubic foundation contract.

Sheets use native 900-DPI rendering of saved geometry and actual traces, with
smooth downsampling only. The five columns are frozen initial, independent target,
learned nominal, sampled desired and actual controller. Port SVGs show saved control
geometry; they are not retouched ink. Blank probes are open interior regions, not
claims of accepted closed counters.

## Replay

Run-001 is retained as a stopped attempt: 1158 renders including 303 baseline,
842 completed optimization evaluations, 107.382996 seconds. A valid upper-return
boundary handle rounded outside the unchanged strict interval during construction.
No held-out target access occurred. Revision 1 nudges only an unrepresentable
boundary value inward by bounded floating-point steps; it does not relax the
contract or alter the search. Run-002 must rerun admission and all three seeds.

```sh
PYTHONHASHSEED=839 /absolute/path/to/.venv/bin/python -m scribesim.curriculum.foundation_primitives --output /tmp/return-learning-new
```

Never reuse an output directory or edit a frozen attempt. HANDVALIDATE-015 must
independently reconstruct candidates, check held-out transfer and run adversarial
controls before issuing any new S1 extension or gesture-learning permission.
