# Intentional pen-contact investigation

**Decision: proceed with declared synthetic contract implementation only. S1-action is not evaluated.**

[Frozen contract](contract.json) was committed before probes. Width 0.45 mm, edge thickness 0.02 mm, pressure 0.5, speed 12 mm/s, adequate constant ink; these are synthetic assumptions, not quill calibration.

[Footprint comparison](footprints.png) shows independent rectangular-footprint expectations against the unchanged legacy sweep. Partial contact in the legacy column is an explicitly wrong centered-shrink approximation, not claimed actual execution. All panels use the same physical scale.

[Report](report.json) freezes code/tool identities, numeric results, three fixture families, six negative controls and the implementation gap table. The instantaneous 20-degree controller step at 0.01s gives 2000 degrees/s, exceeding the frozen 180 degrees/s actuator bound. Active-edge state is absent at every layer.

Pressure probes diagnose existing mechanical-width and optical-darkness coupling; they do not enable pressure learning or ink repair. Physical calibration, dabs, deformation, fatigue and depletion remain deferred.

The global image metric may miss a small hidden connector: inspect the negative-control result, retain the failed bound and add local contact/ownership checks in the later evaluator. No threshold was relaxed. Midpoint oracle refinement is not controller timestep acceptance.

Implement NIBCONTACT-002 geometry and PATHGUIDE-006 realized state before any action training. Do not use this investigation oracle as production code or as both implementation and test oracle.

```sh
.venv/bin/python -m scribesim.handvalidate.tool_contract --output /tmp/td018-tool-replay
```

Fresh runs reproduce semantic artifacts; execution.json contains measured wall time and is not byte-stable.
