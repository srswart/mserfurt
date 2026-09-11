# TD-018 — Corner-contact capability findings

Status: **read-only capability inspection complete; contract work required**.
This follows the capability-only approval of section6.1 of the
[nu corner-contact proposal](TD-018-nu-corner-contact-proposal.md). The proposal,
canonical model, tool contract and earlier reports are unchanged.

[Saved evidence and validation](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/README.md)
records one13.638s inspection, no connector geometry or images and no physical
execution. The proposed sites were read from the existing investigation, not
searched or refitted. Both full rectangles and their finite0.02mm thickness were
included in the stationary-site clearance screen.

## What works

The selected negative corner [0,0.1] is representable in `physical-edge-v1`.
Its coordinate reflection preserves directed labels; the0.2025mm center offset
is real and accounted for, rather than using a centered narrow brush. Its
direction-independent rectangular width is bounded by0.049244289mm.

All four selected nu/mu sites clear nonowner canonical strokes even with the
full contact rectangle. The complete shrinking/restoring ramp at a fixed site
is contained in that full rectangle, so continuous-ramp containment follows
analytically rather than from a sampled action grid. Own retained/replaced-span
contacts are still reported; neither the future swept path nor splice overlap
permissions follow from these fixed-site results.

## Two distinct blockers

### Connected-letter contract is fixed-action only

The canonical model rejects negative and positive partial-contact profiles with
`Connected contract requires boundary sampling and fixed actions`.
`scribesim/evofit/connected_contract.py` explicitly requires the fixed profile.
That is an existing intentional boundary, not a validation check to disable.

The underlying action bridge can interpolate active-edge tracks, but chooses
profiles through a model's shared gesture/action mapping. In these fixtures the
`fixed` profile is shared by every body occurrence. The outgoing gesture itself
also covers multiple primitive occurrences. Changing either globally would
change more than the proposed terminal piece.

Consequently a new boundary-local derived-piece/action representation is required.
It must retain immutable canonical source actions and identify the contributors
of T/R/S separately from contact-run identity. No anonymous bridge, global
profile mutation or six-occurrence-cap bypass can stand in for that contract.

### Decimal10% and binary threshold validation disagree

The positive corner [0.9,1] has decimal extent0.1, but binary subtraction yields
0.09999999999999998. The current `contact_corners` validator compares the extent
directly with0.1 and rejects it. The negative interval [0,0.1] passes. The same
extent-comparison idiom also appears in the generic action-track validation;
the canonical connected-schema rejection occurs earlier in the current probe.

This is a numeric representability issue, not a reason to widen the physical
interval or switch corners. No core repair was made in this read-only package.
The follow-up must specify consistent boundary handling across schema, contact
and interpolation while rejecting genuinely subminimum intervals. It must not
silently relax contact limits or repin old accepted evidence after a core edit.

## Recommended next bounded work

Prepare the **boundary-local action contract and numeric-edge handling design**
before constructing the proposed curves:

1. Version the derived piece/action document outside the frozen executing model.
   Separate source lineage, boundary contributor identity and execution contact
   state. Require exact canonical actions on every retained body piece.
2. Specify10%-minimum validation and interpolation endpoint semantics once; test
   both directed corners, reflected labels, exact endpoints, near-threshold
   rejection and full-contact restoration. No epsilon-driven geometry widening.
3. Preserve current connected-v1 behavior and all pinned core files. If a shared
   core fix is chosen instead of a new opt-in implementation, explicitly plan
   fresh identity validation; never present the old frozen pass as covering it.
4. Test schema/ownership and contact conversion without controllers or new paths.
   Only then return for explicit nu/mu geometry approval. Moving ramp rate and
   physical tracking still require separately approved later work.

The0.3s minimum for each endpoint ramp is a necessary rate bound only; there is
no schedule, dwell or physical run here. um/num remain excluded, and the old nm
rejection remains intact. CURRICULUM-016 is in progress, not completed or admitted.
