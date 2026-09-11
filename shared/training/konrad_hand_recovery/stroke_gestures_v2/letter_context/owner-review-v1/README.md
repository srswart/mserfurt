# CURRICULUM-006 P3 — owner review and pre-fitting contract preparation

## Paused by owner — no further width/spacing rankings requested

On 2026-09-10 the owner agrees to keep this grid as validated foundation evidence,
not continue a preference exercise over almost indistinguishable changes. The
current plan is [TD-018 Addendum D](../../../../../../docs/tech-direction/TD-018-addendum-d-stroke-context-transitions.md):
investigate neighbor-conditioned entry/body/exit forms and explicit boundary
transitions first. The [pause record](review-pause-001.json) is separate from the
immutable packet. Preserve any browser drafts; do not infer tied ranks or replace
them. The historical page still displays its original instructions but is **not
an active request to rank or approve the old objective**. No fitting or wider
deformation is authorized by this pause.

## Historical review instructions and proposal (preserved)

Open [the review page](packet-001/index.html). It is also served locally at
`http://127.0.0.1:8813/shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/owner-review-v1/packet-001/index.html`.
The HTML works directly from this checkout, with relative image links and no
external dependencies. Keep the source image directories in place.

Only a loopback static-file server is left running for the review, not a
simulation or fitting process. If it stops, open the HTML directly, or from the
repository root run `.venv/bin/python -m http.server 8813 --bind 127.0.0.1`.

The owner authorizes P3 preparation, comparison presentation, preference
collection and definition of the objective and remaining budget before fitting.
**No owner preferences have been supplied or fabricated.** The objective is a
proposal, not approved by the act of opening the page. No budget increase,
physical execution, rerendering, rule selection or fitting is authorized.

## What to review

- Six training pairs: **nn, nm, un, um, mn, mm**. Each covers one shared rule cell.
- Nine options per pair: widths 0.97/1/1.03 crossed with advances -0.05/0/+0.05.
  The first letter's constituent strokes are horizontally scaled together;
  the advance shifts the following letter. This is not independent per-stroke
  shape learning, fatigue or word-specific lookup.
- All 54 images are existing, pinned seed-7/base actual-ink presentations.
  The three-seed mechanical clearance remains separate from owner preference.
  No development or sealed-holdout previews are read or displayed.
- Full-frame 1169×390 images are neither cropped nor rewritten. Desktop tiles
  use the same scale. “Compare larger” shows the chosen tile, unchanged context
  and width-1 at exactly the chosen advance, all at one larger display scale.
  On narrow screens cards wrap; follow each card's explicit parameter labels.
- Rank within each pair, **1 best through 9 worst**. Ties are allowed and rank
  gaps have no meaning. If differences are indistinguishable, use the same rank;
  do not invent preferences. Exclude an unacceptable option, or leave uncertain
  options unreviewed with a note. Unreviewed rows block completion.

Enter your name and optionally approve the proposed objective using its separate
checkbox. Export the completed review JSON and return it in the conversation.
Draft export and JSON copying are available even if you disagree with the
objective or cannot finish. Browser storage is only convenience, not submission,
backup or authoritative approval. There are no preselected ranks or approvals.

## Proposed objective and decision rules

For each cell c, let A(c) be its owner-admissible variants. For a candidate v:

`loss(c, v) = count(w in A(c) with rank(w) < rank(v)) / max(1, |A(c)| - 1)`.

Table loss is the unweighted mean of its six cell losses. This uses only ordinal
order, not arbitrary numerical gaps. Equal ranks incur no disagreement with
each other. Owner exclusions are appearance labels, not retroactive mechanical
failures. An unreviewed row or no admissible variant in a cell blocks selection.

Ties favor, in order: fewer nonidentity width/advance parameters; smaller total
normalized deformation `abs(width-1)/0.03 + abs(advance)/0.05`; lexical stable row
IDs. Identity remains admissible unless the owner explicitly excludes it. If
identity or every spacing-only option in a cell is excluded, resolve the
three-arm comparison policy with the owner before making any preference claim.

Future selection compares context off, best spacing-only (width exactly 1), and
joint width/advance stroke context. A fourth matched-advance control holds
width at 1 while using the selected stroke-context advances. It isolates shape
effects from placement. The page does not select any arm or compute a fitted
table. Human training labels are not independent historical-style ground truth.

Before selection, validate the exported packet binding, exact row inventory,
rank types, exclusions, notes and reviewer identity; obtain explicit owner
confirmation and freeze the original export hash, accepted labels, objective,
tie policy, exclusions and approval hashes. The current validator reports label
completeness separately from objective approval and **always leaves fitting
blocked**. It neither imports labels silently nor declares P3 complete.

Read-only validation once the owner returns a file:

```sh
.venv/bin/python -m scripts.letter_context_review --validate-review /path/to/c006-owner-review.json
```

## Remaining physical budget — no reset

| Seed | Charged seconds | Remaining seconds | Charged renders | Remaining renders |
|---|---:|---:|---:|---:|
| 7 | 2117.8151799580082 | 582.1848200419918 | 1574 | 3426 |
| 19 | 1711.5840171249583 | 988.4159828750417 | 1574 | 3426 |
| 41 | 2120.9332175429445 | 579.0667824570555 | 1741 | 3259 |

Caps remain 2700 seconds and 5000 render calls per seed, including the failed
original seed-41 replay and its recovery. P3 allocates **zero new controller
runs and zero new simulation render calls**: it indexes saved files and lets
the browser display them. Packaging takes 8.358257250045426 seconds, journaled
separately as read-only preparation, not hidden physical work or a cap reset.

### Proposed downstream inventory and feasibility gate

This is a conservative no-reuse planning inventory, not permission to execute:

| Stage/role | Texts | Arms | Refinements | First/replay | Executions per seed |
|---|---:|---:|---:|---:|---:|
| Development triples | 6 | 4 | 4 | 2 | 192 |
| Previously reviewed pair probes | 3 | 4 | 4 | 2 | 96 |
| Sealed contextual triples, only after selection/development freeze | 6 | 4 | 4 | 2 | 192 |
| Isolated controls, shared unchanged baseline | 3 | 1 | 4 | 2 | 24 |
| Known-base regressions in their original frame, including placed mu | 4 | 1 | 4 | 2 | 32 |
| **Total** | | | | | **536** |

Four arms mean context-off, spacing-only, stroke-context and matched-advance
width-1 control. If arms collapse to the same selected program, any reuse must
be explicit and hash-proven, not assumed. The exact texts/roles are those in
TD-018 Addendum C; this packet does not access sealed examples. Known-base
regressions retain their four original fixture identities and old frame.

At three charged metric/mask calls per execution, one 900-DPI actual image per
base case (134), and one visible-shift control per process (2), the proposal is
`536*3 + 134 + 2 = 1744` additional render calls per seed. It retains the fifteen
existing negative controls; separately needed review panels or new controls
must be added to the exact inventory before execution, not treated as free.

Using prior completed process averages (roughly 3.5–4.33 seconds per case), the
unreused work is approximately **1876–2320 seconds (31–39 minutes) per seed**,
before a safety margin. This is an extrapolation, not a measured runtime bound;
selected triples may differ in cost. It exceeds the remaining 9.7–16.5 minutes.
Render ceilings appear adequate; **time feasibility is not cleared**.

After labels and proposed selections can be specified, freeze an exact staged
inventory with any legitimate archived reuse and safe timing estimate. Seek
explicit approval for a revised budget if necessary. No larger cap, shortened
inventory, fewer seeds, relaxed thresholds or fitting permission is inferred.

## Evidence and validation

- [Manifest](packet-001/manifest.json): packet object SHA-256
  `a928389737c6e6c0ff0c2598dc66b625e9b8e13a3dfd6ee63c61423d438a4331`;
  file SHA-256 `87c8a8ad97544a3ebf7a985143bc6dad92baf02478a6b52a67891b6f2db20980`.
- [Preparation receipt](packet-001/preparation.json): original/recovery pins and
  all 54 image/document bindings verified; no controller/raster/optimizer calls.
- Generated HTML SHA-256:
  `8e5bcab5d40f34891b34af8f7b7dd50733fc634fa41d34495457d90b872f737a`.
- The P3 tests first fail before implementation; **88 tests pass in 45.72s**
  (13 new review tests plus 75 existing dimension/recovery/physical tests).
  Coverage includes training-only grids, exact image dimensions/hashes, failure
  debits, future-inventory arithmetic, malformed ranks, missing labels, ties,
  exclusions, wrong packet IDs and refusal to overwrite the review packet.
- JavaScript syntax checks pass. Native Chrome inspection verifies the grid,
  full-frame comparison modal, correct labels/budget display and blank final
  rankings with completed export disabled. No owner labels or approval are
  entered during testing. Export payload validation is covered by Python tests;
  a complete browser ranking/download round trip is not claimed.
- The bundled Playwright CLI is unavailable (`playwright-cli: command not
  found`); browser extension/IAB surfaces are unavailable. Native Chrome via
  CUA is used instead. The draft preview remains separate from the final packet.

P3 remains **waiting for owner rankings, objective confirmation and a feasible
approved downstream budget**. C006 is in progress, changes uncommitted, and all
S2/real-hand/context-training/fitting acceptance flags remain false.
