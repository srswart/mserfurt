"""Unit and integration tests for Pass 17 (TD-020):
MS Erfurt Aug. 12°47 Edition & Manuscript Showcase Site (`site` system)
and Fly.io production packaging (`app = "ms-erfurt"`).

Covers:
  - ADV-SITE-DATA-001: Asset extraction (Möbius hero art, WOFF2 fonts, folio/spread images)
    and `site_data.json` schema across all 34 folios and 7 sections.
  - ADV-SITE-EDITION-001: Landing (`/`, `index.html`) and 7-Section Scholarly Edition Reader
    (`/reader`, `reader.html`) with confidence marks and `stolz`/`verloren` contested reading switcher.
  - ADV-SITE-VIEWER-001: Interactive Pan/Zoom Folio Viewer (`/viewer`, `viewer.html`) with
    4 CLIO-7 layers (`Lacunae & losses`, `Line confidence`, `Pressure analysis`, `Quill re-dips`),
    Leaf/Opening modes, FNHD Transcription tab, and 34-page Index of Leaves (`/folios`, `folios.html`).
  - ADV-SITE-COLOPHON-001: Sealed (`CLAUSUM`) and Unsealed ("Behind the work") Colophon
    (`/colophon`, `colophon.html`), `site/server.py` HTTP routes (`/healthz`, clean URLs),
    `fly.toml` (`app = "ms-erfurt"`), and `Dockerfile`.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest


def test_adv_site_data_001_bundle_and_site_data_json() -> None:
    """`build_site` populates `site/dist/assets` and `site/dist/data/site_data.json` for all 34 folios & 8 sections."""
    from site_app.build_site_data import build_site_assets_and_data

    dist_dir = Path("site/dist")
    data = build_site_assets_and_data(dist_dir=dist_dir)

    # 1. Extracted Claude Design assets exist
    assert (dist_dir / "assets" / "mobius.jpg").exists()
    assert (dist_dir / "assets" / "fonts" / "eb-garamond-normal.woff2").exists()
    assert (dist_dir / "assets" / "fonts" / "eb-garamond-italic.woff2").exists()

    # 2. All 34 folios and 16 spreads exist in site_data.json and assets/folios/
    assert len(data["folios"]) == 34
    assert data["folios"][0]["id"] == "f01r"
    assert data["folios"][-1]["id"] == "f17v"
    assert len(data["spreads"]) == 16

    f04r = next(f for f in data["folios"] if f["id"] == "f04r")
    assert len(f04r["conf_lines"]) == 21
    assert len(f04r["dmg_boxes"]) >= 2
    assert len(f04r["dip_markers"]) >= 3
    assert len(f04r["transcription"]) == 21

    # 3. All 8 reading sections (Preface + Sections I..VII) exist in edition data
    assert len(data["sections"]) == 8
    sec3 = next(s for s in data["sections"] if s["roman"] == "III")
    assert sec3["title"] == "Peter"
    assert sec3["has_contested_reading"] is True


def test_adv_site_edition_viewer_colophon_html_generation() -> None:
    """`generate_site_html` builds index.html, reader.html, viewer.html, folios.html, and colophon.html."""
    from site_app.generator import build_full_site

    dist_dir = Path("site/dist")
    build_full_site(dist_dir=dist_dir)

    for page in ("index.html", "reader.html", "viewer.html", "folios.html", "colophon.html"):
        p = dist_dir / page
        assert p.exists(), f"Missing generated page: {page}"

    # Verify Landing (index.html)
    landing = (dist_dir / "index.html").read_text(encoding="utf-8")
    assert "MS ERFURT" in landing
    assert "AUG. 12°47" in landing
    assert "S. R. SWART" in landing
    assert "Seventeen folios, bound between two liturgical texts." in landing
    assert "Where the vellum is damaged, the type changes its face." in landing
    assert "CLAUSUM" in landing
    assert "unwritten journal" in landing
    assert "what of us remains in the ideas we pass on?" in landing
    assert "There is more below" in landing
    assert 'href="/colophon">Colophon</a>' in landing

    # Verify Edition Reader (reader.html)
    reader = (dist_dir / "reader.html").read_text(encoding="utf-8")
    assert "Confidence marks" in reader
    assert "stolz · proud" in reader
    assert "verloren · lost" in reader
    assert "The current of belief" in reader
    assert "The final gathering" in reader
    assert 'href="/colophon">Colophon</a>' in reader

    # Verify Folio Viewer (viewer.html) and Index of Leaves (folios.html)
    viewer = (dist_dir / "viewer.html").read_text(encoding="utf-8")
    assert "Lacunae &amp; losses" in viewer or "Lacunae & losses" in viewer
    assert "Line confidence" in viewer
    assert "Pressure analysis" in viewer
    assert "Quill re-dips" in viewer
    assert "Transcription" in viewer
    assert 'href="/colophon">Colophon</a>' in viewer

    folios_idx = (dist_dir / "folios.html").read_text(encoding="utf-8")
    assert "Seventeen folios, thirty-four pages." in folios_idx
    assert "Water-damaged" in folios_idx
    assert "Hand under strain" in folios_idx
    assert "Offcut stock" in folios_idx
    assert 'href="/colophon">Colophon</a>' in folios_idx

    # Verify Colophon (colophon.html — behind-the-work, without the seal gate)
    colophon = (dist_dir / "colophon.html").read_text(encoding="utf-8")
    assert "Sealed until the last folio." not in colophon
    assert 'id="work-view"' in colophon
    assert "This translation is their source." in colophon
    aside = colophon.split('class="stack note-aside"', 1)[1].split("</div>", 1)[0]
    assert 'class="note-callout"' in aside
    assert aside.index("synthetic reconstructions") < aside.index("They are not the source of this translation.")
    assert "synthetic reconstructions" not in colophon.split("note-aside", 1)[0]
    assert colophon.count("Whether anything was lost in translation") == 1
    assert colophon.index("Whether anything was lost in translation") > colophon.index("Spill some ink.")
    assert colophon.count("S. R. Swart") == 1
    assert "The narrator is called Konrad once" in colophon
    assert "one Cologne witness" in colophon
    assert "surviving transmission" in colophon
    assert "surviving ink" not in colophon
    assert "Spill some ink." in colophon
    assert "A stroke across the nib goes broad" in colophon
    assert "minimum-jerk quadratic program" in colophon
    assert "Bastarda hand recovery is the letter" in colophon
    assert "Kinematic coarticulation is the motion" in colophon
    assert "The same solve writes every pair." in colophon
    assert 'src="/assets/hand-nu.jpg"' in colophon
    assert 'src="/assets/hand-nu-kinematic.jpg"' in colophon
    assert (dist_dir / "assets" / "hand-nu.jpg").is_file()
    assert (dist_dir / "assets" / "hand-nu-kinematic.jpg").is_file()
    assert "A manuscript written from its own translation." in colophon
    assert "01 · XL" in colophon
    assert "02 · ScribeSim" in colophon
    assert "03 · Weather" in colophon


def test_adv_site_colophon_001_fly_config_and_http_server() -> None:
    """Verify `fly.toml` targets app `ms-erfurt`, `Dockerfile` exists, and `site_app.server` serves all routes."""
    fly_path = Path("fly.toml")
    assert fly_path.exists()
    fly_cfg = tomllib.loads(fly_path.read_text(encoding="utf-8"))
    assert fly_cfg["app"] == "ms-erfurt"
    assert fly_cfg["http_service"]["internal_port"] == 8080

    assert Path("Dockerfile").exists()

    from site_app.server import resolve_route_file

    dist_dir = Path("site/dist")
    assert resolve_route_file("/", dist_dir).name == "index.html"
    assert resolve_route_file("/reader", dist_dir).name == "reader.html"
    assert resolve_route_file("/Reader.dc.html", dist_dir).name == "reader.html"
    assert resolve_route_file("/viewer", dist_dir).name == "viewer.html"
    assert resolve_route_file("/Viewer.dc.html", dist_dir).name == "viewer.html"
    assert resolve_route_file("/folios", dist_dir).name == "folios.html"
    assert resolve_route_file("/Folios.dc.html", dist_dir).name == "folios.html"
    assert resolve_route_file("/colophon", dist_dir).name == "colophon.html"
    assert resolve_route_file("/ColophonSealed.dc.html", dist_dir).name == "colophon.html"
    assert resolve_route_file("/Colophon.dc.html", dist_dir).name == "colophon.html"
