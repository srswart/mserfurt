# TD-018 — Merge-aware nominal readiness and unchanged F2 continuation

Status: repair and continuation authorized by the owner: “Let's go ahead and
repair merge-aware source verification without weakening historical evidence
pins, then resume the unchanged two-candidate study.”

## Two independent claims

The [stopped preflight](TD-018-mutual-nu-preflight-stop.md) remains immutable.
It correctly rejects the merged runtime as byte-identical historical source.
Do not update any old source/evidence pin or change an old verifier to pass.

1. **Historical evidence integrity:** build a temporary source capsule containing
   exactly the recorded historical `scribesim` Python inventory. Use current
   bytes only when their hash matches the historical pin; otherwise recover
   bytes from pre-merge commit `374445028025f517b14919d00d12812ec6128c42` and
   verify the same old pin. Missing/unrecoverable bytes stop verification.
   Copy supporting scripts/tests without altering them. Link the existing data
   and documents read-only in effect, enforce a worker write/network/process
   guard, and invoke the original recursive verifier unchanged. No constructors,
   rasterizers or physical execution are allowed in this worker. This proves
   historical integrity, not compatibility with the merged runtime.
2. **Current nominal compatibility:** compare the complete current freeze record
   against the old record plus only the exact two changed and 22 added source
   hashes recorded in the pinned stop report. All other source/data identities,
   fixtures, targets, criteria and authority fields must remain exact. No broad
   filename/directory exception is introduced. A future added file fails too.

The two changes are reviewed separately. `scribesim/pathguide/io.py` differs
only by a blank line; require AST equality with its hash-verified historical
bytes. `scribesim/cli.py` adds neural rendering/commands and is not equivalent:
exclude it from the direct nominal execution path, not from source accounting.
The 22 additions are handcorpus, scribehand and neural-bench modules. They remain
available in the merged project but must not be imported by the readiness probe
or the resumed direct construction/checking path. Enforce that exclusion in an
isolated runtime probe and before/after the batch; do not infer their safety
from being newly added files. No provider, GPU, training or neural CLI is invoked.

Additionally, compare exact canonical n, u and nu compiled-object hashes between
the historical worker and merged runtime. This is a context-off regression
check, not generation of new J1/J2 candidates. Pin the new readiness source/test
inventory and helper code, record loaded runtime sources and Python environment,
and fail if any recorded dependency changes before execution.

## Preservation, tests and execution

The old construction brief, approval, constructor/checker and tests, stop report,
and saved canonical/old/derived candidates remain byte-identical. Implement the
repair and continuation in new modules. Test incorrect historical recovery,
candidate/criteria/critical-source mutation, newly added sources, excluded imports,
unverified readiness receipts and accidental retries. A historical-only pass
cannot grant runtime compatibility, and a runtime-only pass cannot bypass
historical integrity.

The capsule is temporary source storage, not a new evidence archive. It reads
existing evidence in place and does not copy multi-gigabyte traces. Its automatic
cleanup applies only to its own temporary source files, never the linked data.
Readiness preparation has no physical or fitting budget. Bound each verification
worker to 300 seconds; timeouts fail closed. Preserve preparation failures.

Use a new exclusive continuation directory and separate approval referencing
the stopped attempt. Reuse the old constructor and checker unchanged, at most
one J1 and one J2, and preserve each candidate before measuring it. This is the
first construction attempt for each: the old stop created zero candidates.

Remaining limits: 300 seconds total construction/checking, 300 seconds nominal
rendering, two total study candidates, no automatic retries, 25MiB total new
study evidence (including preparation/old stop), at least 5GiB free. Keep the
original source cuts, ports, deterministic handles, action/contact partition,
window-local turn guard, thinness and curvature limits unchanged. All approval
and dependency checks remain mandatory; repeat integrity checks after the run.

Render only admitted candidates, retaining textual rejection/uncertainty panels
otherwise. If admitted, complete the specified common-frame plain comparison,
source-change overlays and normalized-progress sequence within the render budget.
No nib-angle variation, mu, fitting, spacing changes, physical runs or automatic
extension of an unresolved proof. Geometry rejection is a valid bounded outcome,
not an invitation to tune until it passes. CURRICULUM-016 remains in progress
until its subsequent owner-review and implementation gates are actually met.
