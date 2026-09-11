# CURRICULUM-016 — bounded demonstrator preparation

**Owner feedback: indistinguishable; current hypotheses paused for design revision.**
The owner reviewed a few unspecified examples and reported a general impression
of sameness. [Recorded feedback](owner-feedback-001.json) does not invent example
IDs, viewing mode, 48 completed reviews, ties or universal pixel equality.
This is sufficient to stop progression of the current hypotheses to physical
validation; further exhaustive ranking is not requested. Preserve the packet,
baseline and all source pins. No automatic widening, new renders or fitting.

Current design revision: `docs/tech-direction/TD-018-addendum-e-boundary-construction.md`.
The next proposed study jointly investigates departure, transfer and receiving
sites, with a concrete reason to connect and an unchanged-separate fallback.
This does not approve a connector, body exception, spacing change or new render.

The canonical [attachment-site investigation](../attachment-investigation/README.md)
is now available: both baseline endpoints obstruct the proposed smooth family;
positive-height sites remain candidates only, not proven feasible attachments.

Historical packet:
Open [the review page](nominal-001/index.html), or use the local server at
[port 8814](http://127.0.0.1:8814/shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/demonstrator/nominal-001/index.html).
No physical motion or fitting was run. Changes remain uncommitted.

The owner explicitly approved the protocol in [nominal-approval-001.json](nominal-approval-001.json).
The frozen preparation is historical: its pending/false approval fields are
superseded only for nominal generation by that separate pinned record.

## Generated results

- **48 nominal PNGs + one review page**, 8.29 seconds, 740,539 total packet bytes;
  within the approved 300-second/100-MiB limits and 5-GiB free-space guard.
- [Nominal report](nominal-001/report.json) SHA-256:
  `8a020790ea4b65fb37c00036eb745db1295bdeb4a1085e52e0511a88221626ea`.
- Approval SHA-256:
  `8ca9757e8946b35b3b0198f93231204d64a27d9352fe2e2a4b7d0334bbef86e3`.
- All 48 saved images pass pinned read-only hash, dimension, mode, nonblank and
  non-edge-clipping checks. Isolated H0–H3 PNG hashes are exactly equal.
- **105 local tests pass**, 48 unchanged exact-null tests deselected. Browser
  QA checks all image loads, desktop/mobile layout, diagnostic zoom, annotations,
  following-neighbor preset, blink and empty feedback export without generating
  fake owner labels. See [browser QA](browser-qa-001.json).

The new renderer is `scripts/stroke_context_nominal.py`; the already frozen
preparation adapter/tests and all prior evidence remain untouched. It uses a
certified cubic-to-chord bound <=0.001 mm and unions fixed-edge sweep polygons
per stroke, never joining across letters. Exactly 48 image-generation calls;
subsequent inspection reads saved pixels without rerendering.

Start with **Previous neighbor** (second n), then **Following neighbor** (first u).
Compare H0 against the selected hypothesis within each text. Try the full frame
first, then optional 4× detail/blink; the details panel names exact changed
handles and contact ownership. The same-bin and isolated presets are deliberate
unchanged/equal-effect controls. The page remains an unchanged historical packet;
its feedback prompts do not override the subsequent pause recorded here.

## What is ready

- [documents.json](prepared-001/documents.json): 48 deterministic geometry
  documents, 12 exposed strings × H0/H1/H2/H3, canonical-origin base refinement.
- [report.json](prepared-001/report.json): source pins, independently computed
  coordinate-delta checks and conservative nominal full-frame containment.
- [protocol.json](prepared-001/protocol.json): frozen proposed nominal rendering
  inventory, review questions and bounded HANDVALIDATE-025 inventory proposal.

H0 is unchanged context-off. H1 changes entry only; H2 exit only; H3 combines the
two approved local changes. Geometry is regenerated through the pinned GESTURE-005
contract; candidate, previous evidence, targets and thresholds remain unchanged.
No extra words, triples, letters, spacing variants or stochastic parameters enter.

## What the demonstrator establishes—and does not

The preparation checks coordinates, not merely the adapter's change labels:

| Contrast | Named cause | Fixed control |
|---|---|---|
| nn versus mn, second n, H1−H0 | Near versus far previous departure port | Same current n and following EOS |
| nn versus un, second n, H1−H0 | Same near previous-state bin | Expected equal local change, not arbitrary previous-letter alternates |
| un versus um, first u, H2−H0 | Following stem-entry versus rise-entry | Same current u and previous BOS |
| H3 versus H1+H2 deltas | Independent entry/exit composition | No additional interaction coefficient |
| Isolated n/u/m, all hypotheses | BOS/EOS suppress both interventions | Exact unchanged geometry |

All endpoints, undeclared body control points, advances and ownership/contact
metadata stay exactly equal. Coordinate-delta comparisons across different
placements allow only 1e-12 local arithmetic tolerance; this is not a physical
acceptance threshold. The parameter bounds remain ±1 degree and 0.04 mm maximum
handle movement, with no clipping or automatic widening.

Pairs do not contain a middle letter with both neighbors: **this does not test
two-sided within-letter interaction**. Triples remain unadmitted. Transition-only
joins/retraces and form-plus-new-transition panels are unsupported, not fabricated.
The unchanged lift-only transition arm duplicates H0. No whole-letter affine or
spacing-only variant is mislabeled stroke learning.

### Expect small differences

Each affected cubic changes only one control handle. Its centerline displacement
is bounded by 4/9 of that handle's movement. Even the full approved 0.04-mm cap
implies <=0.01778 mm, or <=0.63 pixel at 900 dpi, before any display resizing.
This is a mathematical path-displacement bound, **not** a bound on raster pixel
count, visibility or aesthetic quality. Subtle or indistinguishable normal-scale
results are plausible and valid. Diagnostic zoom cannot manufacture acceptance.

## Approved nominal rendering protocol

Approved and executed: **48 nominal geometry PNGs and one local review page**:

- One full-frame image per frozen document, no controller or physical trace.
- Fixed frame [-3,30,2,13] mm, 900 dpi, exactly **1169×390 pixels**, using the
  already pinned supersample/ceil/downsize dimension contract.
- Ideal fixed-edge 0.45-mm nib at 40 degrees swept along the canonical/derived
  cubic, flattening error <=0.001 mm. Label every panel **NOMINAL GEOMETRY — NOT
  ACTUAL INK**. The separate nominal renderer implements these specifications
  and was tested before its single authorized invocation.
- Full-frame first; synchronized zoom/blink reuses the same image assets with
  separate port, span, owner and delta annotations. No extra zoom/diff rasters,
  new targets or metric inputs. Matched advances, no silent recentering per arm.
- Show semantic pen-down/corner and lift/air/landing requirements only. There
  are no simulated durations, desired timed-motion or actual-ink panels yet.
- Proposed hard limits: **5 minutes wall time, 100 MiB output, 5 GiB minimum
  free space, zero automatic retries**. These are prospective ceilings, not
  measured runtime estimates or new physical allowances.

The preparation checks the entire Bezier control hull plus a conservative
0.225-mm nib radius and 0.001-mm flattening margin against the full frame. This
contains the proposed nominal swept shape, not any future actual-motion error.
Actual finite-nib/global/local containment remains a separate physical gate.

Owner questions after the approved images exist:

1. Can you identify the changed stroke at normal scale?
2. Is that change useful, unnecessary or less readable?
3. Would you prefer unchanged separate lettering?

“Indistinguishable,” “separate lettering preferred” and “unsupported” are valid.
No forced ranks, invented feedback, learning targets or acceptance from enlarged
views. If these bounds are uninformative, return to design rather than expanding
them automatically.

## HANDVALIDATE-025 proposal—not execution permission

The concrete upper-bound schedule is 12 texts ×4 hypotheses ×4 existing
refinements ×3 seeds ×2 processes = **1,152 physical executions**. Three metric
images each, two presentation images for every base case, plus 24 adverse-control
render calls per seed give **4,104 render calls maximum** (1,368 per seed).
This deliberately does not deduplicate identical isolated/disabled arms; exact
null checks remain useful. It grants no run or calibration allowance.

The protocol copies the existing mechanical criteria and proposes explicit
zero undeclared-control/anchor/advance changes, <=0.04-mm approved handle changes,
directed-port error <=1e-8, handle-length error <=1e-12 mm, and zero missing/
duplicate boundary events or unowned new ink segments. These extra measurement
checks require prospective review; they have not been tuned to physical outcomes.

Remaining C006 allowances stay unchanged:

| Seed | Seconds | Render calls |
|---|---:|---:|
| 7 | 582.1848200419918 | 3426 |
| 19 | 988.4159828750417 | 3426 |
| 41 | 579.0667824570555 | 3259 |

The render envelope fits those residual render counts, but **time feasibility
is unmeasured and not established**. No reset, implied extra allowance, retry or
deletion of failed evidence. New non-null planning, an independent reader,
precise local finite-nib windows, full adverse-control schedule, storage/time
estimate and explicit cumulative budget approval must be frozen before execution.
The physical proposal is therefore not yet an execution-ready protocol.

## Reproduction and status

```sh
.venv/bin/python -m pytest -q tests/test_stroke_context_preview.py
.venv/bin/python -m scripts.stroke_context_preview prepare
```

Preparation refuses to overwrite an existing directory. It runs under the old
controller/raster prohibition guard and verifies the contract report and frozen
sources/manifests before deriving documents. Structural checks are not physical
validation or historical/style acceptance.

CURRICULUM-016 remains **in progress, paused for design revision** after the
owner's indistinguishable judgment on an unspecified subset. Nominal approval,
renderer/page implementation, generation and local checks are done. HANDVALIDATE-025 does
not start automatically. No commit, merge or provider CI is claimed.

Read-only packet verification:

```sh
.venv/bin/python -m scripts.stroke_context_nominal inspect --report-sha256 8a020790ea4b65fb37c00036eb745db1295bdeb4a1085e52e0511a88221626ea
```

If the local server is no longer running, open `nominal-001/index.html` directly
or start `.venv/bin/python -m http.server 8814 --bind 127.0.0.1` from the repo root.
