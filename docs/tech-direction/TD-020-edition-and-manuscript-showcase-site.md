# Tech Direction: TD-020 — MS Erfurt Aug. 12°47 Edition & Manuscript Showcase Site (`site` System & Fly.io Hosting)

## Status
**Accepted** — governs Pass 17 (`pass-17`: `ADV-SITE-DATA-001`, `ADV-SITE-EDITION-001`, `ADV-SITE-VIEWER-001`, `ADV-SITE-COLOPHON-001`).

## Context & Design Reference
With the completion of the 34-folio (`f01r–f17v`) kinematic Bastarda rendering (`TD-019`) and 560-year calfskin/offcut weathering pipeline (`TD-011`), MS Erfurt Aug. 12°47 is ready for public presentation as a dual scholarly edition and interactive manuscript showcase.

The visual and interaction design is defined in:
- Local design bundle: `docs/site/MS Erfurt Aug. 12°47 — Edition & Manuscript.html`
- Claude Design artboards: [Claude Artifact (`31QV3MNXN1tLPPBqhxvUbR`)](https://claude.ai/artifact/31QV3MNXN1tLPPBqhxvUbR#artboard-ee8253017927)

The design comprises 6 desktop views and 3 mobile/phone viewports (`390×844` responsive adaptation):
1. **Landing — Introduction (`/`)**: Hero with the aged-vellum Möbius strip (`das blat wuste es. wirt`), archival provenance (*"Seventeen folios, bound between two liturgical texts. Never indexed."*), scrollable 34-folio strip, CLIO-7 confidence typography key (`≥ 80%` Roman, `60–80%` Italic, `< 60%` Bold Italic, `[—]` Lacuna), pull quote, and Sealed Colophon (`CLAUSUM`) wax-seal teaser.
2. **The Edition — Scholarly Reader (`/reader`)**: Warm vellum-paper (`#F2EBDD`) reading environment for all 7 manuscript sections (`I · The current of belief` through `VII · The final gathering`) plus the Translator's Preface, with left Contents rail, sticky reading-progress bar, `A−` / `A+` font-size controls (`17px–27px`), toggleable `Confidence marks`, hoverable `[—]` lacuna tooltips, right-margin Apparatus rail with `"On the vellum"` folio deep-links, and the interactive **Contested Reading** switcher (`stolz · proud` vs. `verloren · lost`) in Section III.
3. **The Folios — Interactive Manuscript Viewer (`/viewer`)**: Full-viewport dark (`#0B0B0B`) pan-and-zoom inspection stage (`50%–500%` zoom, pointer drag, wheel zoom, mini-map navigator) supporting both **Single Leaf (`Leaf`)** and **Bound Bifolium (`Opening`)** modes across all 34 folios, with 4 toggleable CLIO-7 overlay layers (`Lacunae & losses`, `Line confidence`, `Pressure analysis`, `Quill re-dips`), a 2-tab inspector (`Apparatus` & line-by-line FNHD `Transcription`), and a 34-leaf bottom filmstrip with Roman numeral section dividers.
4. **Index of Leaves — All 34 Pages (`/folios`)**: Complete 17-folio / 34-page visual index grouped by Sections `I–VII` with interactive filter chips (`All leaves 34`, `Water-damaged 5`, `Hand under strain 12`, `Offcut stock 8`) and status indicators.
5. **Colophon — Sealed (`/colophon` default)**: Red wax seal (`✦ CLAUSUM`) protecting the narrative twist until the reader finishes Section VII (`f17v`), displaying live reading-progress pips (`X of 7 sections read`) and a two-step early-unlock confirmation (`Break the seal now` → `Break it` / `Keep it sealed`).
6. **Colophon — Behind the Work (`/colophon` unsealed)**: Reveals the closing note (*"They are not the source of this translation. This translation is their source."* — S. R. Swart) followed by the 4-stage pipeline loop (`Edition` → `01 · XL` → `02 · ScribeSim` → `03 · Weather`), psychomotor state table, water-severity exponential decay chart ($0.4^{\text{distance}}$), clean-vs-weathered comparison, corpus statistics (`34` pages, `88` damage spans, `254` emotional lines, `180` quill dips), and a copyable CLI terminal block.

---

## Architecture & Component Breakdown (`site` System)

### 1. `data-assets` (`ADV-SITE-DATA-001`)
- Unpacks embedded visual and typographic assets from `docs/site/MS Erfurt Aug. 12°47 — Edition & Manuscript.html` (`mobius.jpg`, self-hosted `EB Garamond` normal/italic WOFF2 fonts) into `site/dist/assets/`.
- Generates web-optimized folio images (`f01r`–`f17v` weathered, clean, side-by-side, thumbnails, and `spread_f01v_f02r`–`spread_f16v_f17r`) and diagnostic callout graphics (`scribal_and_material_callouts.png`, `f01r_side_by_side.png`).
- Compiles `site/dist/data/site_data.json` containing:
  - All 34 folios with normalized `%` bounding-box coordinates for `Lacunae & losses`, per-line `Line confidence` scores, `Pressure analysis` emotional/psychomotor states, `Quill re-dips` positions, and line-by-line FNHD/Latin/MHG transcriptions.
  - All 7 English narrative sections + Translator's Preface parsed from `source/ms-erfurt-source-annotated.md` with confidence span markup (`.c2`, `.c1`, `.lac`), contested reading state (`proud` / `lost`), and marginal apparatus cards.

### 2. `edition-reader` (`ADV-SITE-EDITION-001`)
- Implements the Landing view (`/`) and the 7-section Edition Reader (`/reader`, `/reader.html`) with responsive desktop and phone layouts (`< 768px` mobile bottom bar & floating `"On the vellum"` pill).
- Tracks section reading progress in `localStorage` (`ms_erfurt_read_sections`) so completing Section VII automatically unseals the Colophon.

### 3. `folio-viewer` (`ADV-SITE-VIEWER-001`)
- Implements the Pan-and-Zoom Manuscript Viewer (`/viewer`, `/viewer.html`) and the 34-page Index of Leaves (`/folios`, `/folios.html`).
- Drives all 4 CLIO-7 overlay layers (`Lacunae & losses`, `Line confidence`, `Pressure analysis`, `Quill re-dips`) dynamically for **every** folio `f01r–f17v` using real coordinates from `site_data.json`.

### 4. `colophon-and-fly` (`ADV-SITE-COLOPHON-001`)
- Implements the Sealed and Unsealed Colophon views (`/colophon`, `/colophon.html`) with interactive two-step seal breaking, pipeline diagrams, and clipboard copy.
- Provides a lightweight, zero-dependency Python ASGI/WSGI/HTTP production server (`site/server.py`) with clean URL routing (`/`, `/reader`, `/viewer`, `/folios`, `/colophon`, `/healthz`), gzip compression, and immutable asset caching, packaged via `Dockerfile` and `fly.toml` (`app = "ms-erfurt"`, internal port `8080`, `auto_stop_machines = "stop"`, `auto_start_machines = true`).
