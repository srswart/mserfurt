# HANDVALIDATE-019 — standalone stem

**COMPLETE: independently accepted synthetic fixed-tool standalone stem.**
The exact primitive, gesture and action bytes are unchanged. Unit scale and
zero rotation only; downstream placed occurrences retain their own physical
and full-frame checks. This is not learned historical handwriting or S2.

All seeds 7/19/41 and separate-process replays pass four translated/lifted
fixtures, four refinements, exact owner/contact boundaries, blank space and five
adversarial controls. Worst global actual/target loss is **0.0011681** and worst
local loss **0.0022967**, below unchanged **0.05**. All 22 non-clock worker
artifacts replay exactly; the live reader verifies all **140** manifest artifacts.

**312 renders**, 104 per seed including replay; maximum cumulative seed time
123.789 seconds. Zero fitting, retries or changes to prior targets/thresholds.

- [Left stem actual](run-001/seed-7/first/left-stem-actual.png)
- [Right stem actual](run-001/seed-7/first/right-stem-actual.png)
- [Lifted pair actual](run-001/seed-7/first/lifted-stems-actual.png)
- [Independent analytic target](run-001/seed-7/first/lifted-stems-target.png)
- [Immutable report](run-001/report.json) / [specification](spec-v1.json)

Native panels are 900 DPI. The diagnostic carrier uses internal text `i`; that
does not admit a letter i. Accepted coverage is only the standalone stem.

```python
from scribesim.handvalidate import standalone_stem

admission = standalone_stem.require_readiness(
    standalone_stem.BASE / 'run-001',
    expected_report_sha256='14a8ded4d6e29be259ff1dcb4c04607c44f5e7a5a9eb61727e0869150eb7dee0',
    required_gestures=['stem'],
)
```

The reader rejects other gestures/tools, real scope, stale hashes, changed
candidate geometry/actions, missing artifacts, altered physical/control proofs
or incomplete replay/budgets. Four-refinement source-subdivision preserves the
admitted candidate bytes.

Tests: 72 focused pass, including 14 new tests; the 14 also pass in a clean
committed checkout. Red tests `8b77419`, execution code `3340c3a`. No provider CI
or human appearance approval is claimed. This closes only the standalone-stem
prerequisite for the separately scoped CURRICULUM-014 assembly repair.
