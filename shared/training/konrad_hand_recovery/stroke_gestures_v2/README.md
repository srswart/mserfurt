# TD-018 gesture investigation evidence

**Phase td018-gesture-investigation is complete.** These are synthetic
specifications and engineering probes, not newly trained strokes or a recovered
historical hand. The new gesture/action schema and acceptance remain pending.

## View the samples

- [Eight gesture centerline hypotheses](coverage/run-001/synthetic-fixtures.png):
  colored segments show how one pen-down gesture can contain multiple pieces.
  Right-hand examples specify smaller lifted-pair transfer, not fitted results.
- [Expected versus legacy nib footprints](tool_contract/run-001/footprints.png):
  angle/direction, arcs, rotation, directed edge release and a lifted finishing
  pass. Legacy partial contact is deliberately approximated by an incorrect
  centered shrink to expose the missing geometry; it is not actual new actuation.
- [Earlier learned primitive practice](../stroke_language_v1/strokes/synthetic/practice-sheet.png)
  remains the training evidence. Do not confuse these new specifications with it.

## Findings and replay

| Investigation | Evidence | Outcome |
|---|---|---|
| EXEMPLAR-009 | [Coverage workbook and replay](coverage/run-001/README.md) | 52 non-test records, zero real admitted inventory; eight analytic gesture hypotheses |
| NIBCONTACT-001 | [Tool contract, results and replay](tool_contract/run-001/README.md) | Three fixture families, 29 renders in 0.2034s; no fitting or physical calibration |

G0 remains blocked on source support and genuine review. The coverage audit does
not decode sealed source/test images; full dataset integrity is explicitly
unverified, not replaced by a shortcut pass. No labels, masks, reservations or
old primitive evidence changed. Proposed review/source work needs a new budget.

The controller copies desired angles instantly and lacks active-edge state.
The synthetic 180deg/s bound is exceeded by a 2000deg/s diagnostic step. Local
contact/ownership checks are necessary: hidden connectors and overbuilt terminals
fall below the unchanged 0.1 global image-sensitivity threshold. Failed controls
are retained, not converted into passes or hidden by a threshold change.

Focused/regression validation: 44 tests pass locally and in a clean local clone.
Fresh-process replay reproduces semantic artifacts exactly; the tool probe's
separate execution receipt records variable wall time. No provider CI, owner
appearance approval or S1-gesture/S1-action pass is claimed.

Next is **td018-gestures**. Start with versioned composition and explicit v1
compatibility; new primitive geometry or expansion-limit needs require separately
scoped work before fitting. Ink depletion, fatigue and other session effects
remain deferred. Immutable run directories and their freezes retain all results.
