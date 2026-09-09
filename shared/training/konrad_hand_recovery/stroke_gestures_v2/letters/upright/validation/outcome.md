# HANDVALIDATE-021: implementation repaired; evaluation incomplete

**No numeric pass, candidate failure verdict, actual-ink sample or new acceptance.**
The first immutable attempt stopped before scoring with
`Unsupported physical contact fields`. Its nominal adapter forwarded NumPy
`float64` coordinates to the physical contact boundary, which deliberately accepts
Python `float`/`int` scalars only. This is an evaluator implementation defect, not
evidence that the owner-approved n/u/m shapes failed.

- Frozen implementation: `495c119`.
- Preserved failed archive: `run-001/`, evidence commit `c722bd1`.
- Consumer-pinned report SHA256:
  `6f4678661d6d5103311ac88040f29ad36cd0247d03c45fb9909e0145e4685421`.
- Seed 7 first process: two charged render calls, no completed scored fixture.
  No replay or seeds 19/41 ran. The second charged render raised an exception.
- Scalar-boundary regression test fails before repair (`50b5330`).
- Repair `21151c4` converts scalar types without rounding, moving points, changing
  the nib or modifying any target/threshold. It does not modify the frozen archive.
- Eight evaluator tests plus the adjacent construction/connection/action tests:
  **49 passed**. The five older curve-tangent admission failures also reproduce
  unchanged on pre-work commit `85e3b44` (22 passed, five failed in that file).
- Plan, generated-rule and whitespace checks pass. The installed strict PR
  metadata parser still returns `ids=[]` with explicit IDs. No provider CI claim.

## What remains

The frozen protocol permits **zero automatic retries**. A request for one explicit,
bounded no-refit continuation is pending. No continuation has been run. If approved,
freeze a new continuation authorization/code identity and output directory, bind
the prior failed report hash, account for its two charged calls in the combined
seed-7 budget, and retain the same candidate, target, fixtures and numeric gates.
Do not overwrite `run-001` or pretend its failure never occurred.

Then complete seeds 7/19/41 with fresh-process replay, independent reader checks,
full-frame evidence, adversarial controls and actual-ink owner review. Until then,
HANDVALIDATE-021 remains **in progress and unmerged**, not complete or accepted.
S2, real-hand acceptance and context permission remain false.

The original nominal KEEP review and candidate/report/review hashes are unchanged.
The original approved examples remain at `../run-001/index.html`.
