# TD-018 — Bounded saved-ramp contact measurement

Status: **measurement authorized; no geometry or classification change**.

Owner request: “Okay let's handle bounded self-contact measurement on the saved
candidate, keeping geometry and limits unchanged.” This scopes one diagnostic
batch on the saved J1-R1 departure and whole K→E→C receiving aggregate.
The [repair result](TD-018-j1-receiving-repair-results.md) remains frozen.

## Scope and budget

- One run, at most 300 seconds and 2MiB report output; at least 5GiB free space.
- Fixed 64 equal-parameter cells per saved cubic; no adaptive geometry, fitting,
  alternate candidates, automatic retries, images, physical execution or mu.
- Include every unordered cell pair, including the diagonal and cross-E pairs.
  Do not crop an excursion or drop nearby pairs to manufacture separation.
- Keep nib dimensions, angle, full/corner profiles, aggregate arc-length action,
  existing limits, source ownership and splice/ordinary-overlap policy fixed.
- Persist in new `nu-mutual-construction-v1/ramp-contact-measurement-001`.
  Never overwrite earlier candidate, approval, readiness or failure records.

## Measurement

Use exact rational de Casteljau restriction of saved binary floating-point
controls. Chord lower and control-polygon upper lengths, with outward square
roots, bound cumulative and total arc length over the entire ramp. Their ratio
bounds active-edge progress; E does not reset that ratio.

Project restricted control hulls onto the fixed nib edge and normal axes.
The tool's binary sine/cosine coefficients define orthogonal axes with their
actual squared norm retained in footprint offsets. A 1e-9mm accounting padding
expands outer bounds and shrinks inner bounds; it does not relax any limit.
Include the full varying active edge and finite normal thickness.

For every cell pair, exclude overlap only if conservative projected footprint
supersets are disjoint. For every remaining pair, bound the entire intervening
arc by the sum of its cell-length upper bounds. Report the maximum possible
overlap separation, a separate cross-cubic bound and worst-case source domains.
These are global coverage bounds, not sampled-only contact exclusions. A
remaining box pair indicates possible overlap, not a collision witness.

Separately inspect the fixed cell-boundary parameters for paper-point revisits.
Choose a point strictly inside the guaranteed footprint intersection at two
ordered parameters. Certify that it is outside a guaranteed enclosing footprint
at an intermediate parameter. Save exact rational paper coordinates and all
three inner/outer rectangles so the witness can be independently checked.
No witness found on this grid is **not** a continuous no-return certificate.

## Evidence and acceptance boundary

Verify saved report SHA-256
`03979c687c1fb027b383e07d0b9c176b8c7e782b08f9df351905dba43f0deda6`
and embedded candidate SHA-256
`616526b0952f02264d772508bce4342c325cc21a4648e49abd50efdaf01845f5`.
Verify each previously pinned dependency and prior repair approval, plus the
historical locality evidence chain. Freeze this isolated diagnostic, tests and
contract in a separate approval record. Do not renew runtime readiness or edit
the historical source snapshot merely because new diagnostic files exist.
No constructor or renderer is imported or invoked. Prior structural/external
results are reused as pinned evidence, not claimed as newly executed checks.

The broad ramps do not inherit the thin-core-only normal-window classification.
Even a certified disconnected paper-point membership witness is not silently
classified as prohibited nonlocal contact: it disproves uninterrupted coverage
of that point, while the ordinary/nonlocal policy distinction still matters.
Likewise, a small separation bound creates no new locality permission.

The diagnostic always leaves admission unresolved unless a separately approved
future complete certificate/classification resolves it. On timeout, preserve
partial measurements and stop. Report what was proved, what was merely possible,
and the remaining policy/proof obligation before proposing any follow-up.
