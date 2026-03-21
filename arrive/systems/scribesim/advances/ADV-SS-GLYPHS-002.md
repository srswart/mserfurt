---
advance:
  id: ADV-SS-GLYPHS-002
  title: Glyph Curvature — Organic Bezier Shapes From Musteralphabet Reference
  system: scribesim
  primary_component: glyphs
  components:
  - glyphs
  started_at: 2026-03-20T20:10:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T16:22:58.872676Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - public_api
  evidence:
  - tdd:red-green
  - tests:unit
  status: complete
---

## Objective

Rework the glyph Bezier control points to produce organic, curved strokes that match the Musteralphabet GK 1438 reference (docs/samples/_Musteralphabet_GK_1438_sw_text.png). Current glyph definitions use collinear control points for stems (e.g. b ascender: all x=0.1), producing perfectly straight lines that look mechanical. Real Bastarda strokes have subtle curvature from the hand's natural arc movement — even "straight" downstrokes bow slightly.

## Behavioral Change

After this advance:
- All ~90 glyphs have curved, organic Bezier strokes that match the Musteralphabet reference
- Stems bow slightly (not perfectly vertical) — the natural arc of a hand-held pen
- Lobes are round and full (not angular or polygonal)
- Ascender/descender strokes have characteristic Bastarda curves (leftward lean at top of ascender, rightward loop at bottom of descender)
- The overall visual impression shifts from "computer-generated" to "hand-drawn"
- All strokes remain cubic Beziers — the change is in control point positions only, no structural changes

## Planned Implementation Tasks

- [ ] Analyze the Musteralphabet reference image for each letter's characteristic curves
- [ ] Tidy: document the ductus principles — which direction each stroke type should curve
- [ ] Test: measure "straightness" of catalog strokes — ratio of max deviation from chord to chord length; all strokes should have deviation > 0
- [ ] Implement: rework control points for stems (b, d, f, h, i, j, k, l, p, q, t) — introduce subtle bow
- [ ] Implement: rework lobes (a, b, c, d, e, g, o, p, q) — round out curves to match reference
- [ ] Implement: rework ascender heads (b, d, f, h, k, l) — add characteristic Bastarda looping
- [ ] Implement: rework descender tails (g, j, p, q, y) — add rightward loops
- [ ] Implement: rework connecting strokes (m, n, u, w) — flowing arch shapes
- [ ] Validate: render f01r — all letterforms visually organic, no straight-line artifacts
- [ ] Checkpoint: `./snapshot.sh glyphs-002` — side-by-side with Musteralphabet

## Risk + Rollback

**Risks:**
- Changing all 90 glyphs at once is a large diff; hard to review incrementally
- Over-curving produces wobbly, unstable letterforms — curvature must be subtle
- Pressure profiles may need rebalancing after control points change (different stroke directions = different physics nib widths)

**Rollback:**
- Revert the catalog.py; glyph definitions are self-contained

## Evidence

