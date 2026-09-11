# CURRICULUM-006 P1 — Current-foundation baseline readiness

Owner-authorized readiness implementation, 2026-09-09. **Baseline reuse PASS;
context fitting BLOCKED.** This is a read-only evidence/coverage check, not a
new learning or physical experiment. P1 is complete; CURRICULUM-006 P2–P5 remain
planned. No component stage or S1/S2/real-hand acceptance is promoted.

## What is cleared

The exact approved connected-v1 n/u/m candidate can be consumed as an unchanged
baseline reference with explicit letter/tool/purpose scope. The evidence covers
the original ten H024 fixtures (n/u/m, placed-mu, un/nu/um/nn/uu/mm), their exact
placements, original `[-3, 20, 2, 13]` mm frame, physical-edge-v1 tool and four
refinements. It does not authorize any controller execution or geometry change.

| Evidence | Result |
|---|---|
| Original H024 artifact inventory and hashes | All 1,808 verified |
| Frozen current core identities | All 206 unchanged |
| New raw occurrence/lineage scans | 240 archived runs: 10 fixtures × 4 refinements × 3 seeds × first/replay |
| Primitive coverage | stem, rise, upper-return, lower-return in each seed/process/refinement inventory |
| Gesture coverage | stem, overturn, underturn |
| Fixed action | Full edge, 0.45 mm nib, 40 degrees, pressure 0.5, speed cap 12 mm/s; no depletion/fatigue |
| Recipe coverage | n, u, m; canonical and exact internal subdivision distinguished |
| Missing baseline inventory | None |
| New controller executions / renders / fitting evaluations | 0 / 0 / 0 |

The checker newly compares compiled primitive/gesture/action/recipe ownership,
placement, occurrence IDs, curve positions and fixed-state contact coverage to
saved raw traces. Existing H024 mechanical/replay results are reused through its
consumer-pinned independent raw-inspection receipt and unchanged artifact hashes.
This does **not** claim another independent physical reconstruction. The original
style-target numerical FAIL stays unchanged and diagnostic under the approved
appearance-preservation contract. Owner KEEP covers the reviewed geometry only.

## What still blocks context

1. **Transformed occurrences:** approve and implement opt-in derivation/lineage,
   exact null replay and independently checked nonidentity mechanical limits.
2. **New context coverage:** new pair/triple, frame and local-window evidence;
   the ten existing placements do not cover arbitrary combinations.
3. **Preferences/objective:** owner training labels and immutable objective,
   tie rules and train/development/test protocol.
4. **Execution authorization:** explicit experiment/fitting approval and combined
   inventory/budget; baseline reuse does not grant it.
5. **Broader layer admission:** arbitrary isolated primitive use, reusable S1/S2
   or historical-hand scope requires its own matching-source quality contract.

Old finer-scale and standalone-stem readiness readers still reject their original
reports. They were neither repaired nor repinned. No repeat of the historical
curriculum is justified merely to close the already complete baseline inventory.
S2, real-hand and context-training flags remain false.

## Frozen evidence and use

- [Snapshot report](snapshot-001/report.json): per-run coverage, canonical catalog hashes, explicit scope and gaps.
- [Freeze](snapshot-001/freeze.json): source identities, source pins and P1-only authority; written before scanning.
- [Read-only reinspection](inspection.json): fresh coverage recomputation against the externally pinned report.
- [Design and remaining proposals](../../../../../../docs/tech-direction/TD-018-addendum-c-letter-context.md).

Consumer-pinned report SHA-256:
`af4e70fc3c1b61c4e69ff46f0a9a3e70ecf5d737659901d0d5730edb976181aa`.

Candidate file SHA-256:
`01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd`.

Source report / independent inspection / owner review SHA-256 respectively:

```text
25b0e886ab643ff5dee969d1393b1f3f1e235e75f945e3c94025aedcfffe36b4
bda0a94c03a4d8a870cf398137e29c1e093349c0b8f1345a71a4da0caa3c499d
cf890ca88e8295c1a3e66a7ae71545ba7806e3159600b13274f241d1ce06a076
```

From the repository root, recheck without writing or executing the scribe:

```sh
.venv/bin/python -m scripts.current_foundation_readiness \
  --inspect shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/readiness-v1/snapshot-001 \
  --report-sha256 af4e70fc3c1b61c4e69ff46f0a9a3e70ecf5d737659901d0d5730edb976181aa
```

Consumers use `scripts.current_foundation_readiness.require_readiness` with
the snapshot path, this external `expected_report_sha256`, the exact decoded
candidate, explicit nonempty `required_letters` subset of n/u/m,
`tool='physical-edge-v1'` and `purpose='frozen-baseline-reuse'`. The returned scope
is mandatory; it is not permission for arbitrary strings made from those letters.
Changed candidate geometry, context-fitting purpose or unknown scope is rejected.
The API returns `execution_authorized=false` and `geometry_changes_authorized=false`.

Inspection verifies the complete source inventory and recomputes occurrence
coverage instead of trusting saved pass flags. Repinning forged permissions does
not authorize them. `--build` only permits a new directory; existing snapshots
are never overwritten. Do not generate a new snapshot to disguise stale inputs.

## Validation and next step

Red test collection preceded module implementation. Then this focused suite passed
all **47 tests** in 159.61 seconds:

```sh
.venv/bin/python -m pytest -q tests/test_current_foundation_readiness.py \
  tests/test_upright_reference_contract.py tests/test_upright_event_replay.py
```

Tests include altered raw lineage/actions, missing occurrence coverage, exact
subdivision provenance, changed/escaped artifacts, consumer scope escalation,
repinned forged authority and continued rejection by both legacy readers.
Plan, generated-rule and whitespace checks pass. The installed strict ARRIVE PR
parser returns no IDs despite explicit title/body/label IDs; no successful strict
PR check, provider CI, commit or merge is claimed.

Next is P2's opt-in context/lineage and exact-null contract, followed by separately
approved bounded transform/frame mechanics. Proposed width/advance limits and the
wider frame are not approved by P1. No new visual samples were needed or generated;
the [existing H024 actual samples](../../letters/upright/validation/placement-validation-v1/index.html)
remain the baseline gallery.
