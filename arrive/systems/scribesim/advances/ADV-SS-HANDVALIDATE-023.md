---
advance:
  id: "ADV-SS-HANDVALIDATE-023"
  title: "Approved Appearance — Versioned Reference Contract"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "tests"]
  started_at: "2026-09-09T08:34:53Z"
  implementation_completed_at: "2026-09-09T08:47:09Z"
  review_time_estimate_minutes: 121
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 71
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration"]
  model_usage: []
  status: complete
---

## Objective

Implement the owner-approved TD-018 Addendum B section 14 reference contract.
Keep candidate-derived approved appearance, independent style provenance and
mechanical evidence distinct without changing historical numerical decisions.

## Behavioral Change

Version and pin approved actual-ink regression references and their fixture/tool
scope. Expose separate construction, motion, appearance, style and regression
results. Exact deterministic replay is an identity check, never new quality,
generalization or layer admission. Prepare a held-out placement protocol without
starting an unbudgeted physical experiment or borrowing old render allowances.

## Planned Implementation Tasks

- [x] branch: `advance/ss-handvalidate-023`.
- [x] tidy: new opt-in script API preserves all frozen evaluator source identities.
- [x] test: provenance/identity, scope, frame/tool, corruption, fail-closed decisions and independent report verification.
- [x] feat/fix: registry, replay comparison, five-channel report, immutable build and consumer-pinned read-only inspector.
- [x] protocol: freeze current zero-execution validation and prepare held-out placements, controls and explicit execution-authorization boundary.
- [x] evidence: validate saved first/replay samples and adversarial mutations; no re-render or fitting.
- [ ] docs/merge: publish contract state, update plan and merge locally.

## Bug Fixes

- [x] Prevent derived reference relabeling, out-of-scope owner approval and mechanical success laundering a failed style gate into overall acceptance.

## Risk + Rollback

- Risk: dropping a failed gate by renaming it, treating self-comparison as transfer, or using candidate-derived pixels as independent ground truth.
- Rollback: withhold the new contract output; never mutate old archives, targets, numerical limits or source hashes. All S2/real/context flags remain false.
- Budget: this implementation validation performs zero controller executions, raster renders and optimization evaluations. New held-out physical runs require their own concrete authorization and execution freeze.
- Existing handvalidate component is incubating; no new component or dependency is necessary.

## Evidence

- [x] tidy:preparatory unnecessary; new script API deliberately avoids old source drift.
- [x] tdd:red-green; tests:unit; tests:integration.
- [x] Consumer-pinned registry/report inspection and original artifact integrity.
- [x] Separate first/replay baseline identity and non-admitting held-out protocol state.

## CI Evidence Notes

Run focused tests, plan/rules/whitespace and strict PR metadata checks. Record
installed parser limitations separately from provider CI. Implementation
completion is not a held-out experiment, owner approval of unseen output or S2.

16 new contract tests pass in 47.71 s; the combined contract/reconciliation/event
reader/replay/measurement suite passes 50 tests in 93.90 s. Tests prohibit physical
execution/rendering and exercise consumer pins, changed provenance, incomplete/
nonfinite evidence, replay identity, frame/tool/fixture binding and immutable
snapshot inspection. Plan/rules/whitespace checks pass. The installed strict PR
metadata parser still returns `ids=[]` despite explicit title/body/label IDs; no
provider CI is claimed. Earlier unrelated admission failures are not repaired.

Reviewability is red 71, estimated 120.9 minutes (rounded to 121), dominated by
the frozen registry/protocol/report JSON and new API. Scope, red tests, implementation,
immutable evidence and documentation are separate commits. This estimate is not
completed human review. Component metadata now explicitly routes the script/API
and focused tests to the existing incubating handvalidate component.

## Changes Made

### 2026-09-09 - implemented and validated approved reference contract

Red `a0f7ffb` precedes green `f31ea48`. New reusable script API
`scripts/upright_reference_contract.py` leaves all frozen core evaluators and
readers untouched. Consumer-pinned registry loading rejects changed roles/scope/
bindings. Candidate-derived actual anchors for n/u/m/mu carry owner, candidate,
code, fixture, frame, DPI, fixed tool/action and base-refinement hashes. Analytic
style provenance stays separate, with the unchanged historical 0.05/0.75 gates.
Exact replay equality is explicitly not a quality or generalization verdict;
variant tolerance remains null. No numeric criterion is invented or relaxed.

Snapshot evidence `6d91bdf` is in the training tree's
`letters/upright/validation/reference-contract-v1/snapshot-001`. Report SHA256:
`1beef87d098b7287de99cfa848cd5299a93d9e04d8cdd77744a28d46170d478f`.
The separate read-only inspection receipt verifies all three frozen snapshot
artifacts, current source/approval bindings and all 1,256 original artifacts;
it reconstructs the new protocol and decisions without execution or rendering.
Archived motion proofs are reclassified from previously independently verified
evidence, not newly reconstructed raw-motion checks.

All six archived workers show construction/motion PASS, scoped appearance KEEP,
style FAIL and exact reference MATCH. All 24 reference comparisons match. Eight
new in-memory pixel/metadata mutation controls detect their intended violations;
these are not new physical versions of H021's eleven controls. Overall admission
is withheld, historical numeric failure persists, and S2/real/context stay false.

The prepared protocol declares four known fixtures and six text-disjoint fixed
placements (un, nu, um, nn, uu, mm), translated by [0.017, -0.011] in normalized
construction coordinates. All 24 held-out refinement plans preflight successfully
with unchanged caps and declared interletter air. No held-out actual ink, appearance
approval or contextual stroke learning is claimed. New nominal references are
explicitly derived and unreviewed. Physical execution requires a separate owner-
bound authorization and execution-code/reference/reader freeze. Proposed allowance
is 5,000 renders/1,800 seconds per seed including replay, zero retries and fitting;
it is not an authorized budget or a reuse of prior debits.

TD-018 section 14 and the contract README document implemented APIs, sample scopes,
consumer-pin commands and the exact execution boundary. The immutable contract
approval retains its historical pending-implementation value; this Advance and
snapshot record completed implementation. No repeat review of the design is needed.

### 2026-09-09 - implementation scope

Owner says “Okay go ahead with implemetation.” The approved design record is
immutable and remains an at-review snapshot. Implement versioned reference roles,
fail-closed consumers and a concrete next-protocol boundary; do not refit shapes,
invent aesthetic tolerances or silently move 0.05 to a new reference. Registry
and evidence live outside old run directories. ARRIVE template 0.1.24.

## Check for Understanding

1. Why does an exact approved-reference match establish replay identity but not independent style accuracy?
2. Which reference, candidate, fixture, frame and tool bindings must a consumer verify?
3. Why does a prepared held-out protocol not authorize execution or inherit owner approval for unseen combinations?
