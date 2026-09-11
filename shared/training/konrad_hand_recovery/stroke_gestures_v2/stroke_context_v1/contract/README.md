# GESTURE-005 — opt-in contextual span contract

The owner approved the GESTURE-004 proposal and requested the next advance.
[contract.json](contract.json) records that approval and freezes the bounded
scope. The older investigation README/report remain unchanged historical bytes;
their pending-review wording is superseded by this separate approval record.

Consumer contract SHA-256:
`f438dc9f8d4e9c8464dfe183346117b21c3a5f97da60e34fe5539d402b25fd3b`.
Investigation report pin:
`d7eb422948f7de6696221d2f026559ca603fb84a95e713e9e6cdce5aa95a6b75`.
Reviewed proposal pin:
`9f0076010c4fdf9d539527e0333bb0d8c36982a458bb493391645201592dad87`.

## API and invariants

The adapter is `scripts/stroke_context_contract.py`; it is not imported by
production paths and changes no frozen core or prior evidence code.

```python
from scripts import stroke_context_contract as context

document = context.compile_context(
    candidate, "un", context.request("H3"), "base",
    "f438dc9f8d4e9c8464dfe183346117b21c3a5f97da60e34fe5539d402b25fd3b",
)
context.verify_document(document, candidate, document["contract_sha256"])
```

Consumers must use the externally frozen pin, not accept a caller-provided new
hash as approval. The adapter also hard-checks that approved pin, candidate
identity, investigation bytes, proposal bytes and exact bounded values.

- Request fields are exactly `version`, `hypothesis`, `transition_intent`.
  Unknown fields, word/fixture/seed keys, arbitrary ports, bounds or permission
  overrides reject. Ports and selector state are derived from the candidate.
- Only the 12 previously exposed n/u/m isolated/pair strings are admitted.
  nuu/uuu/muu and sealed strings remain excluded; this approval did not admit
  triples or arbitrary words. Canonical-origin placement is explicit; no caller
  placement override or reuse of a shifted specimen under an origin label.
- The version is `stroke-context-spans-v1`. H0 preserves the frozen compiled
  schema exactly. H1–H3 use a distinct `stroke-context-spans-v1-geometry-only`
  schema and `canonical_model_sha256`, not an execution-model identity.
- Canonical state is computed before any edits: previous exit class and relative
  horizontal gap (near <=1.2 x-height, far >1.2), following stem/rise entry class,
  and BOS/EOS. No order-dependent feedback from already-derived neighbors.
- H1 rotates first-occurrence C1 +1 degree near/-1 far; H2 rotates last-occurrence
  C2 +1 for a following stem/-1 for a rise; H3 combines them. BOS/EOS suppress
  the respective edit. H0 makes none. Endpoint-relative vectors, fixed length,
  canonical y-up, 0.04-mm maximum displacement; reject rather than clip.
- All other canonical control points, internal join anchors, letter advances,
  actions, primitive/gesture/recipe IDs and overlap contributors remain intact.
  Entry/exit exceptions affect the entire cubic and are explicitly recorded as
  protected-body exceptions, not falsely labeled endpoint-only crops.
- Every occurrence has source/derived/output geometry hashes, original ownership,
  cubic parameter spans and directed derived ports. The original owner hashes
  identify canonical definitions, not a claim that edited geometry is canonical.
- Base/arc/time share canonical derived geometry. For non-null subdivision,
  derive first, then split each cubic at t=0.5 with de Casteljau; lineage keeps
  [0,0.5]/[0.5,1] ranges. H0 instead short-circuits through the frozen subdivision
  implementation, preserving its exact floating-point operation order.

`verify_document` regenerates expected geometry/state/lineage and compares the
complete document, rejecting rehashed body edits, fake ports, changed contact
intent, ownership or permission. It does not trust the public compiler return,
but shares the internal derivation implementation: this is a structural verifier,
**not an independent mechanical measurement implementation**.

## Contact, ownership and execution boundary

Contact-run IDs remain separate from letter, gesture and action ownership.
Existing intra-letter smooth joins and explicit corners/reversals remain intact
and are checked with the frozen join validator. Upward pen-down motion is not
rewritten as a lift.

Every inter-letter boundary explicitly declares `pen_up_transfer`, departure and
landing gesture/letter owners, separate contact runs and required lift/air/landing
events. Air has **no ink owners, new ink segments or overlap allowance**. These
are event requirements, not invented physical event timestamps.

Pen-down joins/retraces reject rather than synthesizing paths. Thus there is no
accepted new ink transition lacking ownership or finite-width overlap bounds.
Inherited overlap contributor metadata is retained, but new finite-nib overlap
and containment have **not** been measured; the flag remains false. No physical
validity is implied by preserving the ownership structure.

Only H0 can call `prepare_null_plan`, which returns the unmodified frozen action
bundle with exact-event retiming. H1–H3 are geometry-only: no planner, controller,
optimizer, renderer or default activation is provided. New consumer/planning and
physical measurement work must follow the later advances, without bypassing old
validators or refreshing frozen source pins.

## Generalization boundary

The contract distinguishes semantic roles, canonical spans, derived ports and
ownership rather than relying on three arbitrary letter crops. Nevertheless,
**this version supports only the audited n/u/m topology** and its existing cap.
It does not claim support for closed bowls, ascenders/descenders, detached marks,
multiple contact runs within a letter, or unusual ports. Unsupported inputs fail.

Before word-level expansion, investigate contrasting letter families and approve
new topology-specific mappings/port classes. Do not force them into this pilot's
one-cubic terminal exceptions, invent whole-letter alternates or bypass expansion
limits. Any core migration requires a separate version/fresh-baseline decision.

## Evidence and next gate

The immutable [snapshot report](snapshot-001/report.json) records geometry-only
document hashes for 12 strings ×4 hypotheses ×4 refinements and exact archived
null bindings where origin-aligned C006 identity traces exist. Missing nu/uu and
placed mu are not relabeled as origin-aligned physical evidence.

Tests compare exact H0 compiled geometry, plans, owners, actions and timing to
the frozen functions for all 48 string/refinement combinations. Adverse tests
cover forbidden keys/transitions/texts, body/port/owner/lineage/selector tampering,
false smooth corners, permission forgery, bounds and pin replacement.

Final local results: **261 tests pass** (129 new contract tests plus 132 existing
audit/context/evidence regressions). The snapshot contains 192 structural cases
and 36 exact saved null bindings; report SHA-256:
`8af42ea3bcec6ac97546856798f1aec970dd96a6cd59a01a1822ef45761f42e4`.
Current adapter/test pins, ARRIVE plan, generated-rule, local-link and whitespace
checks pass. Contract artifacts occupy approximately 132 KiB, not a new trace or
image collection. Local results are not provider CI or a merge.

```sh
.venv/bin/python -m pytest -q tests/test_stroke_context_contract.py
```

Snapshot command (refuses overwrite):

```sh
.venv/bin/python -m scripts.stroke_context_contract snapshot --contract-sha256 f438dc9f8d4e9c8464dfe183346117b21c3a5f97da60e34fe5539d402b25fd3b
```

All execution/physical/style/training acceptance flags remain false. No new
images, simulations or fitting; C006's old rankings remain paused, old budgets
are not spent/reset and changes remain uncommitted. CURRICULUM-016 is next:
prepare the bounded demonstrator and its explicit visual-generation protocol,
not an automatic physical run or authorization to increase the bounds.
