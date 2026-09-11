# Thin-connection feasibility — read-only evidence

Follow-up: [corner-contact capability and coupled nu proposal](../../../../../docs/tech-direction/TD-018-nu-corner-contact-proposal.md)
is prepared. It declares contact ramps, source/body exceptions and staged gates;
capability implementation and all later geometry/images await approval.

Read the [technical findings and proposed next step](../../../../../docs/tech-direction/TD-018-thin-connection-feasibility.md)
and [machine-readable report](snapshot-001/report.json).

27 canonical site pairs inspected: nine each for nu, mu and um. No connector
geometry, nominal image, controller execution or fitting evaluation generated.
The run took16.497s under a local300s safety ceiling; it grants no future budget.

Key findings:
- nu/mu receive a descending u stem, unlike nm's rising m entry. Preserve that
  distinction; endpoint tangent/baseline requirements need a new coupled design.
- At the current orientation, full-edge up-right motion is broad. A10% active
  edge is analytically thin in the existing finite-contact model, but corner
  offset, contact transitions and boundary admission remain unresolved.
- Full-edge site footprints for nu/mu have no detected nonowner contacts in this
  screen. This is not a clearance certificate for a thick contact or new path.
- um departure still has possible retained-stroke contact. Num remains dependent
  on separately supported nu/um and has no construction admission.
- The proposed0.089394mm thin-width reference is a discussion limit, not an
  approved target. Existing geometry, action tracks and thresholds are unchanged.

The report pins prior owner feedback, canonical candidate, frozen clearance and
relevant code. Prior clearance/source reinspection passed. Local validation:
116 tests pass,48 exact-null cases deselected. No fresh exact-null planning or
physical acceptance is claimed. ARRIVE, changed-link and whitespace checks pass.

```sh
.venv/bin/python -m pytest -q tests/test_thin_connection_investigation.py tests/test_stroke_clearance_audit.py tests/test_stroke_attachment_audit.py tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null'
```

Snapshot creation refuses overwrite. No unchanged source, prior failed artifact,
approval, nominal packet, target or physical budget was changed. Changes remain
uncommitted; no merge or provider CI claimed.
