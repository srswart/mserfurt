# TD-018 — Bounded J1 receiving-span repair proposal

Status: **proposal only; new geometry execution requires approval**.

Version: `j1-receiving-local-tail-v1`. Part of CURRICULUM-016, not a new
training phase. No new candidate, sample, fitting or physical run is produced
by this document. Historical candidates, checkers, approvals and receipts remain
unchanged; this proposes new geometry, not a measurement-only reinterpretation.

## 1. Problem and decision

[Saved-span measurement](TD-018-saved-excursion-locality-results.md) proves
that J1's receiving curve goes right of its canonical attachment C too early:
an interior witness is 0.146453mm from C, outside the unchanged 0.1125mm
locality disk. Its full excursion supremum is approximately 0.191386mm.
This is a real violation, not merely a loose control-hull bound.

Repair only J1's K→C receiving span. Keep its earlier descent on the permitted
side of C and reserve the slight rightward excursion needed by C's canonical
tangent for a short terminal segment entirely inside the existing disk.
J1 is prioritized because it has one measured locality failure; this does not
establish a visual preference or imply that its remaining contact checks pass.
J2, mu and nib-angle studies remain deferred.

## 2. One deterministic construction

Coordinates are physical millimetres, y up. Take K, C and their unit directions
from the frozen J1 object, not rounded transcription of this table:

| Port | Position | Direction |
| --- | --- | --- |
| K | (4.095, 3.5) | (1, 0) |
| C | (4.385773979306343, 2.7479394102999484) | (−0.027464231629556135, −0.9996227868456172) |

Replace the single receiving cubic with two cubics, still **one K→C receiving
aggregate**. Define, without optimization or parameter search:

```text
r = 0.1125
L = r / 2 = 0.05625
h = L / 3 = 0.01875
E = (C.x, C.y + L)
dE = (0, -1)
reach = C.x - K.x
drop = K.y - E.y

K→E controls = [K, K + (2*reach/3, 0), E - (0.75*drop)*dE, E]
E→C controls = [E, E + h*dE, C - h*dC, C]
```

Require positive reach and drop, exact saved endpoints and the existing tangent
tolerances. No alternate handle rule, port relocation or automatic retry.

The K→E control polygon stays at or left of C.x and between E.y and K.y.
Every E→C control lies within L of C, so convexity confines the entire tail
to half the existing locality radius. Its only rightward control offset is
`h*abs(dC.x)`, less than 0.000516mm, below the unchanged 0.0045mm horizontal
allowance. These are algebraic design bounds, **not an executed candidate pass**.
The implementation must certify the saved floating-point result conservatively.

Both sides of E have downward vertical tangents; C keeps its slightly leftward
canonical downward tangent. This is positional and directed-tangent continuity,
not a claim of acceleration continuity. Nonzero speed and curvature must be
checked on both cubics and at their one-sided limits. A small containment disk
does not prove an adequate radius of curvature.

## 3. Protected geometry and unchanged limits

- Keep A/F/P/Q/K/C, all other J1 boundary pieces, retained n/u geometry,
  canonical models, placement, baseline and x-height unchanged.
- Replace only the contextual u source occurrence `1:0`, interval `[0, 0.35]`,
  as before; retain `[0.35, 1]` exactly. Preserve n's existing cut and lineage.
- Keep the receiving envelope `[K.x, C.x + 0.0045] × [C.y, K.y]`, with any
  right-of-C excursion confined to the existing radius-0.1125mm disk about C.
- Keep minimum radius 0.1125mm, including the tail; curvature must not exceed
  `1/0.1125` per mm. Keep all existing thinness limits on F→K.
- Apply the existing receiving length cap to **the sum of both cubic lengths**:
  `length(K→E) + length(E→C) <= 1.25*distance(K,C)` (approximately 1.00789434mm).
  Subdivision does not grant another allowance.
- Keep endpoint tolerance 1e-9mm and unit-direction tolerance 1e-8; no numeric
  epsilon may turn a failed or unresolved enclosure into acceptance.
- Keep the 0.45×0.02mm nib, 40° y-down angle convention, pressure 0.5 and
  12mm/s speed cap. The cap is not a physical motion schedule.

## 4. Ownership, action and contact contract

Keep piece ID `K-C` with a versioned construction and internal port E. It remains
one contextual-u receiving aggregate, with the existing n/u contributors and
one replaced source interval. E is not a new source occurrence, lift or owner.

Apply one corner-to-full receiving action profile over **aggregate arc length**
K→E→C. Do not restart pressure/contact interpolation or normalize it separately
for either cubic. The fixed-angle thin F→K construction is unchanged.

Keep the existing A/F/K/C inter-owner splice disks and their 0.45mm radii.
**E grants no new splice disk or contact exemption.** Ordinary neighboring-path
overlap and prohibited nonlocal contact retain their approved meanings.

Certify finite-nib external contacts and self-contact for the entire receiving
aggregate, including cross-cubic pairs spanning E. A proof for one cubic is not
automatically a proof for the aggregate. The original departure ramp also still
needs its complete contact check: earlier structural failure prevented those
checks from running. Unresolved contact or exhausted subdivision is a stop,
not permission to render. This proposal adds no new overlap classification.

## 5. Implementation and regression gates

After approval, add an isolated, opt-in repair adapter and aggregate-aware
checker. Do not edit receipt-pinned historical construction/checker code or
rewrite original evidence to make this revision pass.

1. Verify historical file and candidate-object pins; freeze the new adapter,
   tests, proposal and dependencies in a separate approval/readiness record.
   Revalidate current canonical n/u/nu and context-off equality. The old
   merge-aware receipt is historical evidence, not a current source-inventory
   clearance after adding code.
2. Test two-cubic consumption end to end: inspection, arc-length action,
   finite footprints, lineage, serialization and conditional rendering must
   all consume both cubics, not merely the first.
3. Add regressions for a mutated second cubic; broken E tangent or cusp;
   per-cubic action/length resets; cross-E nonlocal contact; failed locality,
   radius and exact attachment; and unchanged protected geometry/context-off.
   Require conservative full-domain bounds, not sampled-only acceptance.
4. Construct the one fixed J1-R1 once, persist it before checking, then run all
   existing structural and contact gates under the aggregate rules above.
   Include protected-subobject equality and old evidence hash checks.
5. Only after every gate passes, render canonical-unconnected versus repaired
   nu at equal scale, with source-change/action overlays and a clear receiving
   detail. Represent failed frozen J1 with its measurements/text, not a newly
   admitted ink sample. A numeric pass permits owner review, not promotion.

## 6. Proposed execution budget and stop rules

This is a **new one-candidate authorization**, not reuse of the exhausted
two-candidate study allowance. Proposed budget: one deterministic candidate,
one batch, no search/refit/retry; at most 300 seconds construction/checking and
300 seconds conditional nominal rendering, at most 25MiB new evidence, and at
least 5GiB free space before execution. Record implementation/test time
separately from these execution budgets.

Use a new exclusive directory beneath `nu-mutual-construction-v1`, proposed
`j1-receiving-repair-001`; never overwrite `batch-001`, `continuation-001` or
`locality-001`. Record source hashes, approval, candidate hash, protected-object
comparisons, full-domain bounds, all failures, timing and storage use.

Stop and preserve evidence on any failed/unresolved gate or budget exhaustion.
Do not lengthen the tail, move C, alter other geometry, rotate the nib, relax a
limit or try J2 automatically. Any such follow-up requires a new proposal.
No fitting, physical execution, fatigue or mu is included.

## 7. Frozen evidence anchors

Paths below are relative to
`shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/`.

| Evidence | SHA-256 |
| --- | --- |
| `continuation-001/report.json` | `06072aa101288038217bcfe7afcedb563bf41572c2b28de2a38b0bea71938bf2` |
| Saved J1 object in that report | `772fce4a7a8cd8b4e56fb9067cc869ded7c0a4b1f779910e690c5c4c68092333` |
| `locality-001/report.json` | `2062941e17a92d01c8daa05d10408f1a901b0ba985d125d876a02f17cc9d0c48` |
| `readiness-001/report.json` | `c4f2f1fdc6ad4883ae9c6be358669005876dd1042b3c197fb4e12c3f580d8915` |

The [original briefs](TD-018-mutual-nu-construction-briefs.md),
[continuation result](TD-018-mutual-nu-continuation-results.md) and
[merge-aware readiness contract](TD-018-merge-aware-nominal-readiness.md)
remain historical records. Approval of this proposal would authorize only the
bounded local replacement and gates described here; it would not accept J1's
style or supersede any prior rejection.
