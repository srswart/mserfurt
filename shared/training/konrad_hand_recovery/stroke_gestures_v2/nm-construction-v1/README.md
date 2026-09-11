# Approved n→m construction — stopped before rendering

**Owner feedback:** This connected nm looks unnatural and its connector is too
thick. [Recorded feedback](owner-feedback-002.json) redirects investigation toward
nib-thin nu/mu connections and compositional num. This candidate does not pass
the intended-style usefulness gate; generated evidence remains unchanged.

**Latest:** [The conditional nominal comparison](nominal-001/index.html) is now
generated, with [assistant visual review and validation](nominal-001/README.md).
Only nm changes; four controls remain pixel-identical. Owner feedback is recorded above.
No physical runs or fitting. Earlier statuses below are preserved chronologically.

**Current follow-up:** The approved revised checker and saved-candidate
reinspection now [pass all geometry and finite-nib gates](envelope-review-001/README.md).
Geometry is unchanged; no nominal images, fitting or physical runs. The original
stopped attempt below remains historical evidence, not overwritten acceptance.

Owner approval on 2026-09-10: “Yes approved. Please implement.”
[Approval record](approval.json) binds the unchanged proposal and frozen inputs.

## Outcome

Implemented the isolated twelve-piece geometry and initial hard gates. The single
approved attempt took18.821 seconds. Frozen source and clearance reinspection
passed. The attempt stopped with an **unresolved extent/direction gate**; no
nominal samples, fitting or physical runs started.

- [Saved candidate](attempt-001/candidate.json): exact retained canonical pieces,
  declared replacement intervals, explicit contributors and two new cubics.
- [Original report](attempt-001/report.json): preserved as emitted, not rewritten
  to substitute the subsequent diagnosis below.
- Length upper bound4.432965778mm, below4.797308244mm ceiling.
- Curvature upper bounds8.806225098/mm (turn) and5.518955270/mm (transfer), both
  below8.888888889/mm. These are conservative bounds, not measured maxima.
- Attachment positions/tangent directions and exact body/ownership/placement
  pass. Finite-nib intersection admission was **not evaluated**.

## Diagnosis from the saved control points

The terminal turn starts at x=0.9672599986155733mm; its first handle is at
x=0.9640810792475758mm. Its Bezier endpoint derivative is therefore
3×(handle.x−start.x)=**−0.0095367581039925mm per unit parameter**.
By continuity, the curve initially travels left of its starting point.

This contradicts strictly increasing x and no centerline left of A. It is not a
raster or finite-nib uncertainty. The generic control-hull gate reported
unresolved rather than an analytic failure witness; the saved values establish
the contradiction without another candidate or bounded attempt. Flipping this
handle would violate the approved canonical tangent/geometry contract.

**No automatic repair or relaxation.** Next is a prospective design decision:
retain the strict rightward constraint and investigate a compatible attachment,
or explicitly propose a tightly bounded canonical-tangent-following leftward
excursion. Either needs a revised proposal and approval before another attempt.

## Implementation boundary and validation

At the owner's subsequent request, the
[tangent-compatible envelope revision](../../../../../docs/tech-direction/TD-018-nm-attachment-envelope-revision.md)
now specifies a local departure allowance derived from the unchanged canonical
tangent, capped at0.0045mm, with a separate locality bound. This is a documented
criterion revision, not a passing remeasurement. Implementation/reinspection
has not started; the original attempt and diagnosis above remain unchanged.

`scripts/stroke_nm_construction.py` implements frozen-input/approval verification,
deterministic geometry and lineage, exact identity checks, conservative length
and curvature checks, bounded execution and immutable evidence. Its CLI refuses
an existing attempt directory; do not delete it to retry.

Conditional finite-nib intersection admission and the nominal renderer/review
page remain unimplemented behind the stop gate; there is no render entrypoint.
This is not a completed or admitted demonstrator. CURRICULUM-016 stays in
progress; HANDVALIDATE-025/026 stay gated. No default compiler or frozen source
was changed, and no independently rerun exact-null planning is claimed.

Local regression:126 passed,48 exact-null cases deselected. Covers frozen
attachment/clearance/context regressions, approval/source rejection, exact
saved geometry, ownership/contact/body/spacing mutations, unsupported sites,
curvature/length and no-render assertions. Tests were extended after the attempt
to check its saved endpoint contradiction; the original report's test hash
identifies the pre-attempt test file, not the extended suite.
No provider CI, acceptance, commits or merges are claimed.

```sh
.venv/bin/python -m pytest -q tests/test_stroke_nm_construction.py tests/test_stroke_clearance_audit.py tests/test_stroke_attachment_audit.py tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null'
```

The conditional10-PNG allowance was not consumed. The output cap was100MiB,
the geometry ceiling300s, and preflight free space approximately47GiB
(minimum5GiB). All older physical budgets, approvals and artifacts remain intact.
