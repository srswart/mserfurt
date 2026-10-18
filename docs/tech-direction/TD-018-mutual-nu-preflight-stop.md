# TD-018 F2 — Approved construction blocked by merged-source identity

Status: **implementation/tests prepared; preflight stopped before either study
candidate was constructed**. CURRICULUM-016 remains in progress.

## Approval and result

The owner approved the [two construction briefs](TD-018-mutual-nu-construction-briefs.md)
with “Yes approved and proceed.” The unchanged brief is pinned in the
[approval record](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/approval.json).
Its historical “await approval” heading is not edited because those exact bytes
are the approved specification; the separate approval record supplies authority.

New opt-in implementation: `scripts/nu_mutual_construction.py` and
`tests/test_nu_mutual_construction.py`. This adds the fixed J1/J2 construction
rules, exact protected-source/lineage checks, aggregate length accounting,
envelope/curvature checks, the approved thin-core window-local contact rule,
conservative finite-nib/ramp checks, exclusive batch output and stop handling.
It does not alter the canonical model, core compiler or pinned old checkers.

123 focused tests pass: new constructor/checker tests use synthetic inputs, not
the frozen J1/J2 study candidates. Existing boundary-action, geometry, receiving,
local-contact and nominal-review regressions are also included. This is software
evidence, not admission of the proposed constructions. Admitted-candidate nominal
rendering/overlays remain unfinished because the prerequisite gate stopped work.

The recursive frozen-evidence check fails at
`letter_context_variant_evidence.compare_previous`, with:

`Changed repaired preflight identities or authority`

See the [saved stop report](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/batch-001/report.json)
and [text-only status board](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/batch-001/index.html).
No actual batch constructor was invoked. The stop is preserved at `batch-001`
so the executable cannot silently retry under the same output identity.

## Cause, not a candidate failure

At merged source commit `3e0e687`, the historical source inventory grows from
217 to 239 files. Two existing pinned files differ: `scribesim/cli.py` and
`scribesim/pathguide/io.py`. Twenty-two source files were added for upstream
handcorpus, neural bench and scribehand functionality. None of the old inventory
entries is missing. All non-code fields of the compared freeze record agree.

The source guard binds the complete inventory, not only the functions used by
this nominal experiment. Therefore a successful merge and passing unit tests
do not satisfy its byte-identity requirement. That failure is real; it must not
be hidden by silently updating expected hashes or dropping upstream features.

Six directly checked candidate/report pins still match: canonical upright model,
old nu candidate and receiving report, derived candidate, local-contact report
and three-way nominal report. This does **not** assert that the entire recursive
evidence chain passed: its source-identity gate remains blocked.

## Budget and preservation

- One preflight verification attempt; zero automatic retries.
- Zero J1/J2 study candidates, new ink samples, fitting evaluations or physical runs.
- Zero construction or nominal-render budget spent; no mu or nib rotation.
- Existing geometry, thresholds, approvals and saved evidence are unchanged.
- Approval and stop report remain Git-visible; the HTML status board is ignored
  under the external-backup policy. No traces or image sequences were generated.
- No commits or merges made in this work package.

## Recommended next gate

Prepare a bounded **merge-aware readiness repair** before authorizing continuation:

1. Preserve the old source inventory and artifact pins as historical evidence.
   Verify the saved evidence against its recorded source, not a substituted hash.
2. Explicitly enumerate and review the two changed and 22 added source files.
   Establish current-runtime compatibility separately from historical byte identity.
3. Propose a versioned verification contract that distinguishes those two claims,
   including tests proving changed candidates, targets, limits and critical
   compiler/checker dependencies still fail closed. Do not broadly whitelist
   future source changes or assume source additions are behaviorally harmless.
4. Review that contract before implementation/continuation. Then use a new,
   explicitly authorized continuation record with the same two-candidate ceiling,
   geometry choices, thinness/curvature limits and remaining budget. Keep this
   stopped attempt intact rather than deleting it to reuse its directory.

This is a prerequisite repair, not another geometry hypothesis, a refit, an
acceptance decision or permission to change the nib/spacing study.
