# n→m nominal comparison and assistant visual review

Open [the full-frame comparison](index.html). It starts on nm: B0 unchanged
separation above B3 joint construction. The n/m/nn/mm selector entries are
unchanged controls, not additional connected variants. Optional4× zoom reuses
the same images. The page works from disk or a local HTTP server.

**NOMINAL CONSTRUCTION — NOT ACTUAL INK.** No physical execution, fitting,
candidate generation or owner acceptance is represented here.

## Assistant visual review

I inspected the full-frame nm B0/B3 images and nn/mm controls. The new connection
is clearly visible, unlike the earlier tiny-handle perturbations. The n arch,
m humps and upright stems remain recognizable; the departure and receiving
curve visually form a continuous low connection without an obvious sharp kink.
The four controls are verified pixel-identical across B0/B3.

My reservation is stylistic: the long, shallow connector occupies much of the
inter-letter gap and reads somewhat like an underline or extended foot. It
makes the change meaningful and inspectable, but does not establish that joining
is preferable to separation. I would keep this as a reviewable prototype rather
than automatically promote it to the default style or physical validation.
This is my qualitative assessment, **not the owner's preference** or a
historical-ductus claim. No geometry was adjusted following this review.

Next owner decision: does the connection look purposeful while still reading as
n followed by m, or is separation preferable? The page starts with “Not reviewed”
and can export your selected preference and notes locally. It does not submit
acceptance or silently record an agent choice as an owner response.

## Packet evidence

- [Generation report](report.json), [approval](../nominal-approval.json),
  [passing geometry report](../envelope-review-001/report.json).
- Exactly10 PNGs and one page; five exposed strings × B0/B3. Same fixed nib,
  full33×11mm frame,900dpi,1169×390px. No cropped replacement evidence.
- Saved candidate hash remains
  `5b570b3df83e88dea38c4faf3b3c4badc121bf2055b0a0631efebf1b515b434c`.
  B3 nominal conversion renders each of ten retained pieces plus T/R once.
- n/m/nn/mm PNG and pixel hashes match across modes. nm differs at2806 pixels;
  difference box[132,167,279,291]. Pixel difference is visibility evidence, not
  an attractiveness score. All full-frame ink bounds are nonblank and unclipped.
- Generation and verification9.839s within300s. Packet was88KiB before this
  review note, well below100MiB combined allowance. Minimum5GiB disk guard passed.
- Original approval, stopped attempt and passing reinspection remain unchanged.
  Ten-image allowance is now consumed; generation refuses overwrite. No retries.

## Validation

Browser QA: all10 images decode at the expected dimensions; desktop1440px and
mobile390px pages have no horizontal page overflow. Zoom stays inside scrollable
panels; specimen selectors and the empty-review export guard work. Direct
headless Chrome/CDP was used after the Playwright CLI was unavailable. No extra
diagnostic raster files were generated. Successful preference export was not
exercised with a fabricated owner judgment.

Local regression:157 tests pass with49 deselected.48 are the existing exact-null
cases. The additional excluded historical test,
`test_stopped_attempt_never_renders`, passed its stopped-report assertions but
failed its final root-wide “no PNG anywhere” assertion now that a separately
approved nominal packet exists. Its source remains unchanged to preserve prior
evidence. Both stopped-attempt and reinspection directories still contain zero
PNGs; all ten images belong to this approved nominal directory. The unfiltered
selection therefore has one known lifecycle-scope failure, not a clean pass.

```sh
.venv/bin/python -m pytest -q tests/test_stroke_nm_nominal.py tests/test_stroke_nm_envelope.py tests/test_stroke_nm_construction.py tests/test_stroke_clearance_audit.py tests/test_stroke_attachment_audit.py tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null and not test_stopped_attempt_never_renders'
```

CURRICULUM-016 remains in progress pending usefulness review. HANDVALIDATE-025/026
remain gated. No physical budget reset, provider CI, commits or merges claimed.
