# Tech Direction: TD-013 — Private Manuscript Layout

## Status
**Active**

## Context
The original XL and ScribeSim contracts assumed a large-format codex and a
fixed 17-folio envelope. That produced pages that were too expansive and too
regular for the manuscript we actually want: a modest private confession with a
comfortable text block and visible breathing room around the writing.

## Decision

MS Erfurt now uses the following physical layout model:

- Standard folios `f01`-`f13`: `185mm × 250mm`
- Standard text block: approximately `130mm × 180mm`
- Standard margins: `20mm` top, `50mm` bottom, `20mm` inner, `35mm` outer
- Standard ruling density: target `22-24` lines per page
- Final-stock folios from `f14` onward: smaller, irregularly cut vellum
- Final-stock target density: `16-18` lines per page
- Folio allocation is dynamic: XL may emit folios beyond `f17v` when the text
  does not fit comfortably at this density

## Consequences

- XL can no longer assume the manuscript must terminate at `f17v`
- Section pins become earliest-start constraints rather than exact fixed slots
- ScribeSim page geometry must follow the smaller private-manuscript dimensions
- Later overflow folios continue to inherit the final-stock geometry and hand
  behavior rather than reverting to the standard layout

## Notes

The goal is not maximum economy of vellum. The page should feel personal and
legible, with room for the hand to breathe. When density pressure appears,
prefer additional folios over cramming more lines into a page.
