---
advance:
  id: "ADV-SITE-COLOPHON-001"
  title: "Sealed/Unsealed Colophon ('Behind the Work') & Fly.io Production Packaging (ms-erfurt)"
  system: "site"
  primary_component: "colophon-and-fly"
  components: ["colophon-and-fly"]
  started_at: "2026-10-17T11:46:00Z"
  implementation_completed_at: 2026-10-17T13:04:37.500Z
  review_time_estimate_minutes: 15
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 18
  risk_flags: []
  evidence: ["tests:unit"]
  model_usage: []
  status: complete
---

## Objective

Implement the Sealed and Unsealed Colophon views (`/colophon`, `colophon.html`) matching the `Colophon — sealed` and `Colophon — behind the work` artboards, and prepare production hosting on Fly.io (`app = "ms-erfurt"`) with `site_app/server.py`, `Dockerfile`, `fly.toml`, and `.dockerignore`.

## Behavioral Change

After this advance:
- `/colophon` displays the `CLAUSUM` wax-seal gate with live reading-progress pips (`X of 7 sections read`) and a two-step early-unlock confirmation (`Break the seal now` → `Break it` / `Keep it sealed`), or opens automatically once Section VII (`f17v`) has been read.
- Unsealing `/colophon` reveals the Closing Note (*"They are not the source of this translation. This translation is their source."*), the pipeline (`Edition` → `01 · XL` → `02 · ScribeSim` → `03 · Weather`), the water-severity chart (`0.4^distance`), corpus metrics (`34`, `88`, `254`, `180`), and a copyable CLI terminal block.
- `site_app/server.py`, `Dockerfile`, and `fly.toml` (`app = "ms-erfurt"`, port `8080`, `/healthz`) serve the site for local preview and `fly deploy --app ms-erfurt`.

## Planned Implementation Tasks

- [x] branch: confirmed on the current working branch
- [ ] tidy: no preparatory refactor; the server and packaging are new
- [x] test: `tests/test_site.py` verifies the routes and `fly.toml` (`app = "ms-erfurt"`, port 8080)
- [x] feat: `/colophon` in `site_app/generator.py`, plus `site_app/server.py`, `Dockerfile`, `fly.toml`, and `.dockerignore`

## Bug Fixes

- [x] Unhashed CSS and JS were briefly marked immutable. HTML, CSS, and JS are now `Cache-Control: no-cache`. Images and fonts under `assets/` stay `public, max-age=31536000, immutable`.

## Risk + Rollback

- Risk: Container image size if unnecessary training artifacts are copied into the Docker build context.
- Rollback: `.dockerignore` admits only `site/dist/` and the server module. Revert `fly.toml` and `Dockerfile` to drop the app from a deploy.

## Evidence

- [ ] tidy:preparatory
- [x] tdd:red-green
- [x] tests:unit

## CI Evidence Notes

- `python3 -m pytest tests/test_site.py -q` — 3 passed (2026-10-17).
- Local server: `/healthz` returns `ok`, `/reader` and `/Reader.dc.html` resolve, and `/` is gzip-compressed.
- Browser check: “Keep it sealed” returns to the first button; “Break it” hides the seal, shows the work view, and sets `ms_erfurt_unsealed` to `1`.
- The Docker image has not been built. `fly deploy` is not part of this advance.

## Changes Made

### 2026-10-17 - feat: initial advance scaffold
- `arrive/systems/site/advances/ADV-SITE-COLOPHON-001.md`: authored advance specification.

### 2026-10-17 - feat: seal the colophon and package the Fly app
- `site_app/generator.py`: writes `colophon.html` with both the sealed gate and the hidden “Behind the work” view. Corpus figures come from the manuscript record (34, 88, 254, 180).
- `site_app/static/site.js`: arms the seal, confirms or cancels, and opens the work view when `ms_erfurt_unsealed` is set or Section VII has been read.
- `site_app/server.py`: clean URLs, design aliases, gzip for text over 800 bytes, and `GET /healthz`.
- `fly.toml`: app `ms-erfurt`, internal port 8080, region `fra`, health check `GET /healthz`.
- `Dockerfile` and `.dockerignore`: runtime image contains the built `site/dist` and the server module, run as `nobody` on port 8080. Generate the site before building the image.

## Check for Understanding

1. Early unseal takes two clicks, and “Keep it sealed” must not set `ms_erfurt_unsealed`. Which click writes that key, and what else can set it without visiting `/colophon`?
2. Why are HTML, CSS, and JS sent `no-cache` while folio JPEGs under `assets/` are immutable for a year? What goes stale if a rebuilt folio JPEG keeps the same path?
3. The runtime image does not contain `site_app/generator.py` or the training corpus. What has to be true of `site/dist` before `docker build`, and what does `.dockerignore` keep out?
