# Authorized braking follow-up — landing fixed, sharp corner still fails

**Specific braking/re-entry checks pass. Full HANDFLOW-010 acceptance does not.**
The Advance remains in progress and unmerged; the other five foundation Advances
remain planned. No new stroke, gesture or letter learning has run.

The user authorized this additional scope after the original two attempts. Its
[frozen contract](../spec-v3.json) permits one candidate, 500 renders or 1800 s,
zero optimization and no automatic revision. This run used **303 renders in
9.426154 seconds**, including high-resolution presentation and six-family baseline
revalidation. The [ledger](../ledger.json) retains all attempts separately.

## What is implemented

`retime_air_braking` in the existing planner produces an explicit `braked-air-v1`
plan plus source-owner mapping. It brakes along the departing contact velocity
while lifted, then follows a rest-to-rest quintic air path to the unchanged next
contact point. Analytic duration bounds desired air acceleration to 250 mm/s² and
speed to 16.2 mm/s; the existing controller still enforces its original 500 mm/s²
and 40 mm/s physical limits. No actual pose or velocity is reset.

Contact geometry, pressure, nib angle and owners are unchanged. Entry accelerates
from rest, with a 12 mm/s nominal ceiling. An analytic arc-distance clock also
decelerates to the existing final rest target without making duration depend on
the last sample gap. All additional time is planned before execution, never an
adaptive wait selected by image quality. Default legacy planning is unchanged.

## Measurements

| Base fixture / check | Result |
|---|---|
| Saved u actual speed at second contact | 0.001221 mm/s, versus about 16.6 mm/s upward before braking |
| Saved u position error at second contact | 0.0000603 mm |
| Every measured arrival | Passes <=0.5 mm/s speed and <=0.05 mm position error |
| All endpoint/time/image refinements | Pass; original limits unchanged |
| Actual acceleration, zero-time continuity, air ink and owners | Pass; no state reset or painted air |
| Ordinary single / repeated / overlap / gapped fixtures | Maximum base contact lag 0.091276 mm, passes 0.25 mm |
| Original six primitive families | Current-code read-only baseline passes; no refitting |
| Saved fitted u scaffold | **0.370963 mm contact lag at the stem-to-exit corner: FAIL** |
| Saved fitted i u scaffold | **0.360264 mm contact lag at the stem-to-exit corner: FAIL** |
| Separate physical-edge fixed-profile check | Arrival and convergence pass; the same corner tracking fails |
| Full motion / training admission | **Fail / false** |

The remaining peak is during continuous contact, not landing. For saved u, it
occurs at 1.186 s on the `exit` primitive after a declared `corner`, whereas
re-entry occurred at 0.831239 s. The supplied construction requests a sharp
direction change at nominal speed. Air-braking adjustments should not conceal
this separate contact-planning problem. See [shared corner-timing proposal](../corner-timing-request.md).

## Why the old examples looked pixelated and L-shaped

Evaluation uses inexpensive 180-DPI images: a 0.45 mm nib is roughly three pixels
wide. The old panel enlarged them with nearest-neighbor interpolation. These
new presentation images rerender the actual or desired geometric samples at
**900 DPI**, then only downsample with Lanczos. They are not retouched or enlarged
evaluation bitmaps. Metrics remain at the original resolution and thresholds.

The L-like mark is one stem-plus-terminal construction deliberately repeated to
test motion while holding geometry fixed. Its old i/u identifiers referred to
supplied scaffolds, not successfully learned letters or a representative alphabet.
The new gallery shows the broader existing inventory explicitly:

- [Six existing primitives: stem, rise, bowl, turn, loop and exit](primitive-gallery.png)
- [Clearly labeled stem-terminal motion comparisons](comparison.png)
- [Browsable explanation, samples and retained historical trace plot](../../index.html)

The gallery is a revalidation of old synthetic-trained geometry, not additional
training or an assertion that the six families are a complete historical vocabulary.

## Verification and reproduction

Experiment implementation: `eb10004`. `f222169` adds only fixed-input validation
afterward; it does not revise the measured candidate. Twenty-four new handflow
tests pass. The expanded clean-checkout suite has 90 passes and one unchanged
pre-existing missing-`nib_angle_deg` constructor test failure. Previously recorded
stale historical-identity failures remain separate; no old hashes were rewritten.

```sh
python -m pytest tests/test_handflow_reentry.py -q
python -m scribesim.handvalidate.foundation_motion --output /tmp/braking-verification-NEW
```

Use a new output directory. Clean-checkout replay under `PYTHONHASHSEED=839`
reproduces all measured rows, checks, baseline actual traces and PNGs. Verification
renders are separately labeled regression work, not another fitted candidate.
See [verification record](../braking-verification.json). No provider CI or human
appearance approval is claimed. No implementation merge is performed while the
required corner/corridor gate fails.
