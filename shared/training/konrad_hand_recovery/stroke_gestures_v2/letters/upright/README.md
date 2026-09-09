# CURRICULUM-015 — shared upright nominal preview

**Implementation complete; owner review pending.**

[Open the before/after review sheet](run-001/index.html): n/u/m ink, full-frame
and enlarged views, shared-stroke paths and direction arrows, isolated primitives
in ink and vector form, and ordered pen-contact states. Everything is nominal
construction: **no actual controller execution, fitting, new target or acceptance
experiment**. HANDVALIDATE-021 waits for owner review and a frozen protocol.

## What changed

- Stem cubic geometry is unchanged, including its slight curvature. Port metadata
  is corrected to the actual endpoint tangents; the primitive identity changes
  and does not inherit historical admission.
- One shared rise has proposed horizontal displacement 0.08 x-height and an
  endpoint chord 5.090 degrees from vertical, versus the old 45 degrees. This is
  a design proposal, not an owner-approved tolerance. The final rise tangent
  still turns into the cap, reaching 46.193 degrees; not every tangent is upright.
- The upper return retains the old cap's complete height profile, endpoint width
  and first handle. Its second handle's horizontal coordinate changes to join
  the unrotated stem smoothly. Curvature is not identical; please confirm whether
  this preserves the n turn you liked.
- The lower return retains its height profile and endpoint width. Both horizontal
  handle coordinates change to meet the upright stem/rise tangents.
- No whole gesture/letter rotates. Uniform stem scales stay within existing
  bounds; n/u/m still expand to 4/4/6 shared primitive occurrences. Each letter
  is one pen-down run with a declared corner at the gesture reversal. Nib width,
  angle, pressure, action and advance spacing stay unchanged.

Only four primitive definitions exist: stem, rise, upper return, lower return.
All occurrences reuse them. Isolated tiles are diagnostic displays, not an extra
compound recipe bypassing the cap. Narrower letters are not a spacing/context fit.

## Measurements and limitations

| Construction | Baseline / x-height | Rise-body to adjacent stem, max horizontal separation |
| --- | --- | --- |
| n | 0 / 1 | 0.123023 mm |
| u | 0 / 1 | 0.260118 mm |
| m | 0 / 1, within floating-point precision | 0.124543 mm |

Separation is sampled at y=0.2..0.7 x-height for adjacent stem/rise pairs, **not
blank ink clearance or minimum Euclidean distance**. The first m rise has no
adjacent stem and is excluded. Its shared rise shape is identical. Full sampled
tangent ranges and primitive identities are in the [report](run-001/report.json).

Every rendered sample's finite nib corners fit its frame; the renderer sweeps
between those corners. Baseline/x-height residuals are below 1e-8 nominal numeric
precision, not an appearance threshold or actual-motion assertion. Fixed-pressure
overlap remains visible, especially in u; independent evaluation must assess ink
accumulation rather than cosmetically reducing pressure.

Old/new panels are rerendered nominal ink from their pinned programs with the
same physical-edge renderer/tool, not copied historical actual-ink panels or
independent targets. Full frames use unchanged [-3,20,2,13] mm at 900 DPI. Detail
frames contain both constructions' control bounds plus 0.6 mm padding, shared
across all letters, at 1800 DPI. No per-letter stretching or cropped pass.

## Frozen evidence

- Candidate file SHA-256: `01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd`.
- Report SHA-256: `53f5beefadd9bb3dc0000eb7f9fb730de549bcb68d4b063936eaade3821ff5fb`.
- Builder frozen at `e3631d5`; source identity hashes are in the report.
- All 21 files replay byte-for-byte in a fresh process. Each build produces 13
  raster panels and four SVG diagrams. No seed, optimization, target loss or
  actual-motion result is claimed.
- `owner-review.json` is pending and candidate-bound. It is separate from the
  immutable manifest so genuine feedback need not rewrite the preview.
- Seven new tests and 125 focused regressions pass (the latter includes the new
  tests). Desktop/mobile image loading, layout and view controls are checked;
  the optional favicon request is the sole HTTP 404.

Reproduce into a new empty directory:

```sh
.venv/bin/python -m scribesim.curriculum.upright_letters --output /tmp/upright-preview-new
.venv/bin/python -m pytest tests/test_upright_letters.py -q
```

`upright_letters.verify_preview(path)` checks artifacts, source hashes, scope
and review binding against the saved report, without writing or granting
acceptance. Consumers should additionally pin the report SHA-256 above. Old
HANDVALIDATE-020 candidates/reports and all targets remain unchanged. The earlier
GESTURE-003 live-admission invalidation still applies; this preview consumes
source bytes as explicitly unaccepted scaffolding, not through a bypassed reader.

## Requested owner review

For each n/u/m: **keep or repair**, naming the feature. Are rises close/upright
enough? Are descents and the initial u underturn acceptable? Is the n cap still
okay? Are width and fixed-tool overlap okay? No fitting or scored HANDVALIDATE-021
experiment begins before this checkpoint.
