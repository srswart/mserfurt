"""ADV-SITE-EDITION-001, ADV-SITE-VIEWER-001, ADV-SITE-COLOPHON-001.

Generate the public MS Erfurt pages into ``site/dist`` from the compiled
folio catalogue and the Claude Design artboards.
"""

from __future__ import annotations

import html
import shutil
from pathlib import Path

from site_app.build_site_data import build_site_assets_and_data

STATIC_DIR = Path(__file__).resolve().parent / "static"

_ARROW = (
    '<svg aria-hidden="true" width="16" height="10" viewBox="0 0 16 10" fill="none" '
    'stroke="currentColor" stroke-width="1.4"><path d="M0 5h14M10 1l4 4-4 4"></path></svg>'
)
_MENU = (
    '<svg aria-hidden="true" width="18" height="12" viewBox="0 0 18 12" stroke="currentColor" '
    'stroke-width="1.4"><path d="M0 1h18M0 6h18M0 11h18"></path></svg>'
)
_CHEVRON_L = (
    '<svg aria-hidden="true" width="8" height="12" viewBox="0 0 8 12" fill="none" '
    'stroke="currentColor" stroke-width="1.5"><path d="M7 1L2 6l5 5"></path></svg>'
)
_CHEVRON_R = (
    '<svg aria-hidden="true" width="8" height="12" viewBox="0 0 8 12" fill="none" '
    'stroke="currentColor" stroke-width="1.5"><path d="M1 1l5 5-5 5"></path></svg>'
)


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _shell(title: str, page: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<meta name="description" content="MS Erfurt Aug. 12°47 — a scribal confession in seventeen folios, with the CLIO-7 edition and the leaves themselves.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css?v=12">
</head>
<body data-page="{_esc(page)}">
<a class="skip" href="#content">Skip to content</a>
{body}
<script src="/assets/site.js?v=3" defer></script>
</body>
</html>
"""


def _menu_button() -> str:
    return f'<button class="menu-btn" type="button" aria-label="Open menu" aria-expanded="false">{_MENU}</button>'


def _nav(active: str) -> str:
    items = [
        ("/reader", "The Edition", "reader"),
        ("/viewer", "The Folios", "viewer"),
        ("/folios", "Index of Leaves", "folios"),
        ("/colophon", "Colophon", "colophon"),
    ]
    parts = []
    for href, label, key in items:
        current = ' aria-current="page"' if key == active else ""
        parts.append(f'<a href="{href}"{current}>{label}</a>')
    return f'<nav class="primary-nav" aria-label="Primary">{"".join(parts)}</nav>'


def _header(active: str) -> str:
    return (
        '<header class="site-header">'
        '<a class="wordmark" href="/">MS ERFURT · AUG. 12°47</a>'
        f"{_menu_button()}{_nav(active)}"
        "</header>"
    )


def _strip_note(folio: dict) -> str:
    if folio["cond"] == "corner":
        return "corner lost"
    if folio["cond"] == "water":
        return "water"
    if folio["id"] == "f07r":
        return "no lacunae"
    return ""


def _landing(data: dict) -> str:
    cards = []
    for folio in data["folios"]:
        note = _strip_note(folio)
        cards.append(
            "<a class=\"thumb\" href=\"/viewer?folio={fid}\">"
            "<img src=\"{thumb}\" alt=\"Folio {label}\">"
            "<span><strong>f. {label}</strong><span>{note}</span></span></a>".format(
                fid=_esc(folio["id"]),
                thumb=_esc(folio["thumb"]),
                label=_esc(folio["label"]),
                note=_esc(note),
            )
        )
    body = f"""
<div class="landing">
  <div class="wrap">{_header("landing")}</div>
  <section class="wrap hero" id="content">
    <div class="hero-copy">
      <p class="kicker">A scribal confession · Erfurt · 1457</p>
      <h1>MS ERFURT<span>AUG. 12°47</span></h1>
      <p class="byline">S. R. SWART</p>
      <p class="lede">This site gives an unwritten journal a visible form.</p>
      <div class="hero-actions">
        <a class="cta" href="/reader">Begin reading {_ARROW}</a>
        <a class="ghost" href="/viewer">Turn the folios</a>
        <a class="ghost" href="/ms-erfurt-edition.pdf" download>Download the PDF</a>
      </div>
      <p class="more-cue"><a href="#document">There is more below</a></p>
    </div>
    <div style="display:flex;justify-content:center">
      <img class="mobius" src="/assets/mobius.jpg" alt="A Möbius strip of aged vellum, written over and over in a scribal hand: das blat wuste es. wirt — one stroke in red.">
    </div>
  </section>
  <section class="band" id="document">
    <div class="wrap split">
      <div>
        <p class="kicker">The document</p>
        <h2>Seventeen folios, bound between two liturgical texts. Never indexed.</h2>
      </div>
      <div class="prose">
        <p>Recovered in 2019 while cataloguing the Augustinian archive at Erfurt: a private manuscript in a professional scriptorium hand of the mid-to-late fifteenth century, several passages damaged by moisture. The author does not fully identify himself.</p>
        <p>He writes to God in the second person — and, at times, to someone else. This edition presents the leaves themselves alongside CLIO-7’s translation, with every uncertainty left visible.</p>
        <dl class="facts">
          <div><dt>Extent</dt><dd>17 folios · 34 pages</dd></div>
          <div><dt>Language</dt><dd>German, with Latin</dd></div>
          <div><dt>Support</dt><dd>Calfskin, then offcuts</dd></div>
        </dl>
      </div>
    </div>
  </section>
  <section class="strip-section">
    <div class="wrap">
      <div class="strip-head">
        <div>
          <p class="kicker">The folios</p>
          <h2>Every page, as it survives. Zoom to the stroke.</h2>
        </div>
        <a class="strip-link" href="/folios">All 34 pages {_ARROW}</a>
      </div>
      <div class="strip">{"".join(cards)}</div>
    </div>
  </section>
  <section>
    <div class="wrap split">
      <div>
        <p class="kicker">How to read this edition</p>
        <h2>Where the vellum is damaged, the type changes its face.</h2>
        <p class="prose">CLIO-7 reconstructs what water and age have taken, and marks how sure it is. Nothing reconstructed is presented as certain. Readers should treat it as interpretive rather than authoritative.</p>
        <div class="accent-picker" role="group" aria-label="Accent color">
          <span class="kicker" style="margin-right:8px">Mark</span>
          <button type="button" data-accent="#E0644B" style="background:#E0644B" aria-label="Cinnabar"></button>
          <button type="button" data-accent="#C9A45C" style="background:#C9A45C" aria-label="Gold"></button>
          <button type="button" data-accent="#8FB3D1" style="background:#8FB3D1" aria-label="Blue"></button>
        </div>
      </div>
      <div class="key-card">
        <div class="key-row"><span class="pct">≥ 80%</span><span>He stayed six years.</span></div>
        <div class="key-row"><span class="pct">60–80%</span><span style="font-style:italic">precise, almost courtly curiosity</span></div>
        <div class="key-row"><span class="pct">&lt; 60%</span><span style="font-style:italic;font-weight:700">He told me on a Thursday.</span></div>
        <div class="key-row"><span class="pct">lacuna</span><span><span style="font-style:italic;font-weight:700">I said</span> <span style="color:var(--accent)">[—]</span>.</span></div>
      </div>
    </div>
  </section>
  <section class="band">
    <figure class="pull">
      <span class="stars" aria-hidden="true">✦ ✦ ✦</span>
      <blockquote>The slight thickening of a stroke when my attention deepened … Readers did not see it. But it was there. The page knew.</blockquote>
      <figcaption>From the manuscript</figcaption>
    </figure>
  </section>
  <section>
    <div class="wrap split" style="align-items:center">
      <div style="display:flex;justify-content:center">
        <div class="seal" aria-hidden="true"><span class="mark">✦</span><span class="word">CLAUSUM</span></div>
      </div>
      <div class="stack">
        <p class="kicker">Colophon</p>
        <h2>A closing note follows the final folio.</h2>
        <p class="prose">It changes what you have read, and how these pages came to be in front of you.</p>
        <div class="hero-actions">
          <a class="cta" href="/reader">Begin reading</a>
          <a class="strip-link" href="/colophon">Read the closing note</a>
        </div>
      </div>
    </div>
  </section>
  <footer class="site-footer">
    <div class="wrap">
      <span>Translated and annotated by CLIO-7 Manuscript Intelligence System · Institut für Digitale Paläographie, Erfurt</span>
      <span>© S. R. Swart · <a href="mailto:info@mserfurt.com">info@mserfurt.com</a></span>
    </div>
  </footer>
</div>
"""
    return _shell("MS Erfurt Aug. 12°47 — Introduction", "landing", body)


def _paragraph(text: str) -> str:
    if text.strip() == "✦ ✦ ✦":
        return '<p class="ornament" aria-hidden="true">✦ ✦ ✦</p>'
    return f"<p>{text}</p>"


def _apparatus(item: dict) -> str:
    kind = item.get("type")
    if kind == "vellum":
        folio = _esc(item["folio"])
        return (
            f'<a class="vellum-card" href="/viewer?folio={folio}">'
            f'<img src="{_esc(item["thumb"])}" alt="">'
            '<span><span class="eyebrow">On the vellum</span>'
            f'<span class="label">{_esc(item["label"])}</span>'
            f'<span class="go">Open in viewer {_ARROW}</span></span></a>'
        )
    if kind == "contested":
        return (
            '<div class="note"><span class="eyebrow">Contested reading</span>'
            f"<p>{item['body']}</p>"
            '<div class="picks" role="group" aria-label="Reading">'
            '<button class="pick on" type="button" data-pick="proud" aria-pressed="true">stolz · proud</button>'
            '<button class="pick" type="button" data-pick="lost" aria-pressed="false">verloren · lost</button>'
            "</div></div>"
        )
    return (
        '<div class="note">'
        f'<span class="eyebrow">{_esc(item.get("heading", ""))}</span>'
        f"<p>{item.get('body', '')}</p></div>"
    )


def _reader(data: dict) -> str:
    sections = data["sections"]
    toc = [
        '<p>Contents</p>',
        '<button class="tbtn" type="button" id="close-contents" style="align-self:flex-start">Close</button>',
    ]
    blocks = []
    for index, section in enumerate(sections):
        sid = section["id"]
        start = section.get("start_folio") or "f01r"
        short = start.replace("f0", "").replace("f", "")
        current = ' aria-current="true"' if sid == "sec-3" else ""
        toc.append(
            f'<a href="#{_esc(sid)}"{current}><span>{_esc(section["nav_title"])}</span>'
            f"<span>{_esc(short if sid != 'preface' else '')}</span></a>"
        )
        prev_s = sections[index - 1] if index else None
        next_s = sections[index + 1] if index + 1 < len(sections) else None
        if prev_s:
            prev_link = f'<a href="#{_esc(prev_s["id"])}">← {_esc(prev_s["nav_title"])}</a>'
        else:
            prev_link = "<span></span>"
        if next_s:
            next_link = f'<a href="#{_esc(next_s["id"])}">{_esc(next_s["nav_title"])} →</a>'
        else:
            next_link = '<a href="/colophon">Closing note →</a>'
        banner_title, banner_body = section["banner"]
        kicker = "Translator’s Preface" if sid == "preface" else f"The Manuscript · Section {section['roman']}"
        blocks.append(
            f'<section class="edition-section" id="{_esc(sid)}" data-progress="{int(section["progress_pct"])}" '
            f'data-folio="{_esc(start)}" data-short="{_esc(short)}">'
            f'<p class="section-kicker">{_esc(kicker)}</p>'
            f'<h1>{_esc(section["title"])}</h1>'
            f'<p class="folio-range">{_esc(section["folio_range"])}</p>'
            '<div class="section-grid"><article class="reading">'
            f'<div class="banner"><strong>{_esc(banner_title)}</strong><p>{_esc(banner_body)}</p></div>'
            + "".join(_paragraph(p) for p in section["paragraphs"])
            + '</article><aside class="apparatus" aria-label="Apparatus">'
            + "".join(_apparatus(item) for item in section["apparatus"])
            + f'</aside></div><nav class="section-nav" aria-label="Section navigation">{prev_link}{next_link}</nav></section>'
        )
    toc.append(
        '<a class="sealed-link" href="/colophon">Closing Note</a>'
    )
    body = f"""
<div class="reader marks" style="--read-size:21px">
  <header class="reader-bar">
    <div class="inner site-header">
      <div style="display:flex;flex-wrap:wrap;align-items:center;gap:28px">
        <a class="wordmark" href="/">MS ERFURT · AUG. 12°47</a>
        {_menu_button()}
        {_nav("reader")}
      </div>
      <div class="reader-tools" role="toolbar" aria-label="Reading settings">
        <button class="tbtn" id="smaller" type="button" aria-label="Smaller text">A−</button>
        <button class="tbtn" id="larger" type="button" aria-label="Larger text">A+</button>
        <button class="tbtn on" id="marks-btn" data-marks-toggle type="button" aria-pressed="true">Confidence marks</button>
      </div>
    </div>
    <div class="progress" aria-hidden="true"><div id="read-progress"></div></div>
  </header>
  <div class="reader-wrap" id="content">
    <aside class="toc" aria-label="Contents">{"".join(toc)}</aside>
    <main class="reader-main">{"".join(blocks)}</main>
  </div>
  <a class="vellum-pill" id="vellum-pill" href="/viewer?folio=f04r">
    <img src="/assets/folios/f04r_thumb.jpg" alt="">
    <span>On the vellum · 4r</span>
  </a>
  <nav class="reader-bottom" aria-label="Reading tools">
    <button class="bb" id="open-contents" type="button">Contents</button>
    <button class="bb" id="smaller-mobile" type="button" onclick="document.getElementById('smaller').click()">A−</button>
    <button class="bb" id="larger-mobile" type="button" onclick="document.getElementById('larger').click()">A+</button>
    <button class="bb on" data-marks-toggle type="button" aria-pressed="true">Marks</button>
    <a class="bb" href="/viewer">Folio</a>
  </nav>
</div>
"""
    return _shell("The Edition — MS Erfurt Aug. 12°47", "reader", body)


def _viewer() -> str:
    body = f"""
<div class="viewer-app">
  <header class="site-header viewer-top">
    <div style="display:flex;flex-wrap:wrap;align-items:center;gap:24px">
      <a class="wordmark" href="/">MS ERFURT · AUG. 12°47</a>
      {_menu_button()}
      {_nav("viewer")}
    </div>
    <div class="viewer-title">
      <button class="ib" id="prev-folio" type="button" aria-label="Previous page">{_CHEVRON_L}</button>
      <div>
        <div class="folio-name" id="folio-title">Folio 4r</div>
        <div class="folio-sub" id="folio-sub">recto · 7 of 34</div>
      </div>
      <button class="ib" id="next-folio" type="button" aria-label="Next page">{_CHEVRON_R}</button>
    </div>
    <div class="seg-group" role="group" aria-label="View mode">
      <button class="seg on" id="mode-leaf" type="button" aria-pressed="true">Leaf</button>
      <button class="seg" id="mode-opening" type="button" aria-pressed="false">Opening</button>
      <button class="seg on" id="mode-weathered" type="button" aria-pressed="true">Weathered</button>
      <button class="seg" id="mode-clean" type="button" aria-pressed="false">Clean</button>
      <a class="seg" href="/folios">All leaves</a>
    </div>
  </header>
  <div class="viewer-body" id="content">
    <div class="stage" id="stage">
      <div class="stage-transform" id="stage-transform"><div class="leaf-frame" id="leaf-frame"></div></div>
      <p class="stage-hint">Drag to pan · scroll or ± to zoom</p>
      <button class="panel-show" id="show-panel" type="button">Notes</button>
      <div class="zoombar" role="toolbar" aria-label="Zoom">
        <button class="ib" id="zoom-out" type="button" aria-label="Zoom out">−</button>
        <span id="zoom-label">100%</span>
        <button class="ib" id="zoom-in" type="button" aria-label="Zoom in">+</button>
        <button class="ib" id="zoom-fit" type="button">Fit</button>
      </div>
      <div class="minimap" aria-hidden="true">
        <div class="minimap-frame">
          <img id="minimap-img" alt="">
          <div id="minimap-rect"></div>
        </div>
      </div>
    </div>
    <aside class="viewer-panel" aria-label="Leaf details">
      <div class="tabs" role="tablist">
        <button class="tab on" id="tab-apparatus" role="tab" type="button" aria-selected="true">Apparatus</button>
        <button class="tab" id="tab-transcription" role="tab" type="button" aria-selected="false">Transcription</button>
        <button class="panel-hide" id="hide-panel" type="button">Hide</button>
      </div>
      <div id="panel-apparatus">
        <p class="kicker">CLIO-7 layers</p>
        <button class="layer" id="ly-dmg" type="button" aria-pressed="false">
          <span aria-hidden="true" style="width:16px;height:12px;border:1.5px solid #E0644B"></span>
          <span>Lacunae &amp; losses<small id="dmg-count">damage spans on this leaf</small></span>
          <span class="sw"></span>
        </button>
        <button class="layer" id="ly-conf" type="button" aria-pressed="false">
          <span aria-hidden="true" style="width:16px;height:6px;background:#D9A441"></span>
          <span>Line confidence<small id="conf-count">lines read</small></span>
          <span class="sw"></span>
        </button>
        <button class="layer" id="ly-hand" type="button" aria-pressed="false">
          <span aria-hidden="true" style="width:16px;border-bottom:2px dotted #8FB3D1"></span>
          <span>Pressure analysis<small id="hand-count">lines where the hand changes</small></span>
          <span class="sw"></span>
        </button>
        <button class="layer" id="ly-dips" type="button" aria-pressed="false">
          <span aria-hidden="true" style="width:8px;height:8px;border-radius:50%;background:#231D17;box-shadow:0 0 0 2px #E8C77A"></span>
          <span>Quill re-dips<small id="dip-count">on this leaf</small></span>
          <span class="sw"></span>
        </button>
        <div class="legend">
          <span><i style="background:#8E8577"></i>≥ 80%</span>
          <span><i style="background:#D9A441"></i>60–80%</span>
          <span><i style="background:#E0644B"></i>&lt; 60%</span>
        </div>
        <dl class="meta">
          <dt>Section</dt><dd id="meta-section"></dd>
          <dt>Support</dt><dd id="meta-stock"></dd>
          <dt>Side</dt><dd id="meta-side"></dd>
          <dt>Lines</dt><dd id="meta-lines"></dd>
          <dt>Condition</dt><dd id="meta-condition"></dd>
        </dl>
        <p class="hand-note" id="hand-note"></p>
        <a class="read-link" id="read-leaf" href="/reader">Read this leaf in translation {_ARROW}</a>
      </div>
      <div id="panel-transcription" hidden>
        <p class="trans-intro">Frühneuhochdeutsch, as read by CLIO-7. Low-confidence lines in bold italic.</p>
        <ol class="trans" id="transcription"></ol>
      </div>
    </aside>
  </div>
  <nav class="filmstrip" id="filmstrip" aria-label="All pages"></nav>
</div>
"""
    return _shell("The Folios — manuscript viewer", "viewer", body)


def _folio_runs(folios: list[dict]) -> list[dict]:
    runs: list[dict] = []
    for folio in folios:
        if not runs or runs[-1]["sec"] != folio["sec"]:
            name = folio["section_name"]
            short = name.split(" · ", 1)[1] if " · " in name else folio["section_short"]
            runs.append({"sec": folio["sec"], "roman": folio["roman"], "name": short, "items": [folio]})
        else:
            runs[-1]["items"].append(folio)
    return runs


def _folios(data: dict) -> str:
    folios = data["folios"]
    water_n = sum(1 for f in folios if f["cond"] in {"water", "corner"})
    hand_n = sum(1 for f in folios if f["hand"] >= 10)
    offcut_n = sum(1 for f in folios if f["sec"] == 7)
    chips = [
        ("all", "All leaves", "#ECE4D6", len(folios), True),
        ("water", "Water-damaged", "#E0644B", water_n, False),
        ("hand", "Hand under strain", "#8FB3D1", hand_n, False),
        ("offcut", "Offcut stock", "#C9A45C", offcut_n, False),
    ]
    chip_html = []
    for key, label, dot, count, on in chips:
        cls = "chip on" if on else "chip"
        pressed = "true" if on else "false"
        chip_html.append(
            f'<button class="{cls}" type="button" data-filter="{key}" aria-pressed="{pressed}">'
            f'<span aria-hidden="true" class="status-dot" style="background:{dot}"></span>'
            f"{label} <span class=\"count\">{count}</span></button>"
        )
    sections = []
    for run in _folio_runs(folios):
        first = run["items"][0]["label"]
        last = run["items"][-1]["label"]
        span = first if first == last else f"{first} – {last}"
        leaves = []
        for folio in run["items"]:
            water = "1" if folio["cond"] in {"water", "corner"} else "0"
            hand = "1" if folio["hand"] >= 10 else "0"
            offcut = "1" if folio["sec"] == 7 else "0"
            d1 = "#E0644B" if water == "1" else "transparent"
            d2 = "#8FB3D1" if hand == "1" else ("#C9A45C" if offcut == "1" else "transparent")
            leaves.append(
                f'<a class="leaf" href="/viewer?folio={_esc(folio["id"])}" '
                f'data-water="{water}" data-hand="{hand}" data-offcut="{offcut}" '
                f'aria-label="Folio {_esc(folio["label"])}">'
                f'<img src="{_esc(folio["thumb"])}" alt="">'
                f'<span class="cap"><b>{_esc(folio["label"])}</b>'
                f'<span><i class="status-dot" style="background:{d1}"></i>'
                f'<i class="status-dot" style="background:{d2}"></i></span></span></a>'
            )
        sections.append(
            "<section class=\"folio-section\">"
            f'<div><span class="range">{_esc(run["roman"])}</span>'
            f'<h2>{_esc(run["name"])}</h2>'
            f'<span class="range">f. {_esc(span)}</span></div>'
            f'<div class="leaf-grid">{"".join(leaves)}</div></section>'
        )
    body = f"""
<div class="folios">
  <header><div class="wrap site-header">{_header("folios")}</div></header>
  <main class="wrap" id="content">
    <div class="intro-grid">
      <div>
        <p class="kicker">Index of leaves</p>
        <h1>Seventeen folios, thirty-four pages.</h1>
      </div>
      <p class="prose">Standard calfskin through folio 13. From folio 14 the vellum is a different stock — smaller, cut unevenly, as though taken from a sheet intended for something else.</p>
    </div>
    <div class="chips" role="group" aria-label="Filter leaves" data-folio-filters>{"".join(chip_html)}</div>
    {"".join(sections)}
  </main>
</div>
"""
    return _shell("Index of Leaves — all 34 pages", "folios", body)


def _colophon(data: dict) -> str:
    ms = data["manuscript"]
    stats = [
        (ms["folios_count"], "pages rendered and aged"),
        (ms["damage_spans_count"], "word-level damage annotations honoured"),
        (ms["emotional_lines_count"], "lines where the writer’s state shapes the hand"),
        (ms["quill_dips_count"], "times the quill was re-dipped"),
    ]
    stat_html = "".join(
        f"<div><dt>{_esc(label)}</dt><dd>{_esc(value)}</dd></div>" for value, label in stats
    )
    bars = []
    labels = []
    for index, distance in enumerate((3, 2, 1, 0, 1, 2, 3)):
        severity = 0.4 ** distance
        height = max(3.0, severity * 100)
        color = "#E0644B" if index == 3 else "#8FB3D1"
        bars.append(
            f'<div><em>{round(severity * 100)}%</em><b style="height:{height:.1f}%;background:{color}"></b></div>'
        )
        labels.append(f"<span>f{index + 1}</span>")
    states = [
        "sacred steadiness",
        "deepened attention",
        "tremor, agitation",
        "grief, hesitation",
        "Latin, formal",
        "compensating eyesight",
    ]
    pills = "".join(f"<span>{_esc(name)}</span>" for name in states)
    body = f"""
<div class="colophon">
  <div id="work-view">
    <header style="border-bottom:1px solid #2B2825"><div class="wrap" style="padding-top:20px;padding-bottom:20px">{_header("colophon")}</div></header>
    <section class="paper-note">
      <div class="wrap split">
        <div class="stack note-head">
          <p class="kicker" style="color:#6A5E50">MS Erfurt Aug. 12°47 — Closing Note</p>
          <p class="note-credit">CLIO-7 Manuscript Intelligence System · Institut für Digitale Paläographie, Erfurt</p>
        </div>
        <div class="stack note-body">
          <p>The manuscript described in this edition was found in 2019 in the historical library of the Augustinian monastery at Erfurt, shelved between a breviary and a lectionary. It consists of a small bound booklet of seventeen folios, uncatalogued and materially intact, though abraded, stained, and split by age. If the account of its origin is correct, it may have remained there, unexamined, for approximately five hundred and sixty years.</p>
          <p>The narrator is called Konrad once, when another man addresses him in the workshop. Konrad was among the most common given names in fifteenth-century Germany. No person matching the narrator’s circumstances has been identified with certainty in the surviving records.</p>
          <p>At the damaged Eckhart sentence, the three readings do not possess equal material authority. Among the surviving witnesses to Eckhart’s German sermons, the line most readily supports <em>ist — is</em>. A later hand supplies <em>enpfêhet — receives</em> — in the margin of one Cologne witness. <em>Wirt — becomes</em> appears nowhere in the surviving transmission.</p>
        </div>
        <div class="stack note-aside">
          <p class="note-callout">The folios reproduced before this note are not photographs of Konrad’s manuscript. They are synthetic reconstructions. The English words attributed to Konrad were extracted from this edition, translated back into a conjectural form of mid-fifteenth-century German, passed to a custom scribe simulator to write them in a hand Konrad might have used, and subjected to simulated age and damage with a weathering simulation. Konrad’s journal, CLIO-7, and the Institut für Digitale Paläographie are fictional elements of this work.</p>
          <p class="twist">They are not the source of this translation.</p>
          <p class="twist"><em>This translation is their source.</em></p>
        </div>
      </div>
    </section>
    <section class="stage-block">
      <div class="wrap" style="padding-top:112px;padding-bottom:112px;display:flex;flex-direction:column;gap:48px">
        <div class="stack" style="max-width:760px">
          <p class="kicker">Behind the work</p>
          <h2>A manuscript written from its own translation.</h2>
          <p class="prose">Three programs, run in order. Each one hands the next exactly what a real manuscript would have handed a scholar — and the scholar’s apparatus is where it started.</p>
        </div>
        <div class="loop">
          <article><span class="step">Edition</span><strong>The English</strong><span>CLIO-7’s translation, with its confidence and its lacunae.</span></article>
          <article><span class="step">01 · XL</span><strong>Back into 1457</strong><span>Thuringian German and Latin, cut into seventeen folios.</span></article>
          <article><span class="step">02 · ScribeSim</span><strong>Into a hand</strong><span>Bastarda, stroke by stroke, shaped by the writer’s state.</span></article>
          <article><span class="step">03 · Weather</span><strong>Into time</strong><span>Water, foxing, oxidised ink</span></article>
        </div>
        <div class="loop-return" aria-hidden="true"></div>
        <p class="loop-caption">CLIO-7’s confidence scores and lacunae are written into the folios before the hand ever touches them</p>
      </div>
    </section>
    <section class="stage-block">
      <div class="wrap stage-grid">
        <div class="stack">
          <p class="kicker">01 · XL — authoring</p>
          <h3>The English, put back into 1457.</h3>
          <p>The text is rewritten in Late Middle High German in a Thuringian register, then cut into folios. Every line carries its register — German or mixed with Latin — a CLIO-7 confidence score, and any damage the edition says it suffered.</p>
          <p>Calfskin folios 1–13 hold 22–24 lines in a 130 × 180 mm text block; the smaller offcuts from folio 14 hold 16–18.</p>
        </div>
        <figure>
          <pre class="specimen">{{
  "id": "f04r",
  "recto_verso": "recto",
  "vellum_stock": "standard",
  "lines": [
    {{ "number": 12,
      "text": "beiden Wochen — daß Peter nicht solde [—] in dem",
      "register": "de",
      "annotations": [
        {{ "type": "confidence", "detail": {{ "score": 0.45 }} }},
        {{ "type": "lacuna", "detail": {{ "reason": "water" }} }}
      ] }}
  ]
}}</pre>
          <figcaption>output-live/f04r.json · line 12, where Lacuna #1 begins</figcaption>
        </figure>
      </div>
    </section>
    <section class="stage-block">
      <div class="wrap stage-grid">
        <div class="stack hand-figures">
          <figure class="callout">
            <img src="/assets/scribal_and_material_callouts.jpg" alt="Annotated detail of the rendered hand: scribal and material features called out.">
            <figcaption>Scribal and material call-outs from the render</figcaption>
          </figure>
          <figure class="callout hand-plate">
            <img src="/assets/hand-nu.jpg" alt="The letters n and u written by the chisel nib, joined by one continuous stroke.">
            <figcaption>nu, as the pen writes it. The hairline between the letters belongs to the same motion as the stems. X-height 3.5 mm, nib 0.83 mm.</figcaption>
          </figure>
          <figure class="callout hand-plate">
            <img src="/assets/hand-nu-kinematic.jpg" alt="The same nu opened into its path: blue points on the letter bodies, red points at the soft joins, a teal path where the letters yield, and orange ticks for the 40 degree chisel.">
            <figcaption>The same word, opened. Blue points hold the letter. Red points are the soft joins, and they are allowed to move. Teal is where the path yields. Orange is the 40° chisel.</figcaption>
          </figure>
        </div>
        <div class="stack">
          <p class="kicker">02 · ScribeSim — the hand</p>
          <h3>A Bastarda hand that feels what the text says.</h3>
          <p>Each folio is a pen path, drawn stroke by stroke at 300 dpi, with the gutter on the correct side for recto and verso. A letter is a few via-points. The word is solved as one motion, so the turn leaving one letter and the turn entering the next are planned together. A chisel nib 0.83 mm wide, held at 40°, sweeps that path. A stroke across the nib goes broad; a stroke along it goes fine. Pressure splays the edge, a slow turn pools ink at the foot, and the quill thins until the next dip. Konrad’s state scales pressure, width, and tempo on that motion. The x-height is 3.5 mm.</p>
          <p>Those strokes are five methods, run in order. Each letter is a contextual via-point recipe, measured in nib-widths and chosen for the letters beside it. The word is one minimum-jerk quadratic program: a banded solve draws the path through every point at once, and the boundary points are soft, so neighbouring letters yield to each other. A 40° chisel is swept as quadrilaterals, with tine splay under pressure and ink pooling where the pen slows. An ink-cycle state empties the quill by the distance travelled and refills it at a dip. A scribe-state model drifts tempo, nib angle, and the via-points, and the line’s emotional state scales pressure, width, and speed.</p>
          <p>Two of those methods have names. Bastarda hand recovery is the letter: a short recipe of via-points, measured in nib-widths and chosen for the letters beside it. Kinematic coarticulation is the motion: one minimum-jerk solve for the whole word. Points in the body of a letter stay put. Points at the joins are soft, so the exit of one letter and the entry of the next draw toward each other. The same solve writes every pair.</p>
          <div class="state-table">
            <span>state</span><span>pressure</span><span>width</span><span>tempo</span>
            <span>deepened attention</span><span>×1.22</span><span>×1.13</span><span>×0.80</span>
            <span>grief, hesitation</span><span>×0.90</span><span>×0.94</span><span>×0.76</span>
          </div>
          <div class="pills">{pills}</div>
        </div>
      </div>
    </section>
    <section class="stage-block">
      <div class="wrap" style="padding-top:96px;padding-bottom:96px;display:flex;flex-direction:column;gap:48px">
        <div class="stage-grid" style="padding:0">
          <div class="stack">
            <p class="kicker">03 · Weather — five hundred years</p>
            <h3>Damage from first principles, then from a model — never on the letters.</h3>
            <p>A codex map models the gathering physically: water spreading from folio 4r and decaying by leaf distance, edges darkening by position, foxing mirrored recto to verso. The edition’s word-level damage is applied in pixel space first, exactly as specified.</p>
            <p>Only then does an image model age a blank parchment, informed by neighbours already weathered. The background is darkened into the hand, and the ink is shifted from black toward the warm brown of oxidised iron gall.</p>
          </div>
          <div class="chart">
            <p class="kicker">Water severity = 0.4<sup>distance</sup> from the epicentre</p>
            <div class="bars" role="img" aria-label="Water severity by leaf: folio 4 at 100 percent, falling to 6 percent at folios 1 and 7.">{"".join(bars)}</div>
            <div class="bar-labels">{"".join(labels)}</div>
          </div>
        </div>
        <figure class="compare">
          <img src="/assets/f01r_side_by_side.jpg" alt="Folio 1r side by side: the clean render on the left, the weathered leaf on the right.">
          <figcaption>Folio 1r — as rendered, and after weathering</figcaption>
        </figure>
      </div>
    </section>
    <section class="stage-block"><dl class="stats wrap">{stat_html}</dl></section>
    <footer class="site-footer">
      <div class="closing">
        <span class="stars" aria-hidden="true">✦ ✦ ✦</span>
        <p>Whether anything was lost in translation, CLIO-7 cannot determine. That determination, if it can be made at all, belongs to You.</p>
        <p class="kicker">S. R. Swart</p>
        <p class="kicker"><a href="mailto:info@mserfurt.com">info@mserfurt.com</a></p>
      </div>
    </footer>
  </div>
</div>
"""
    return _shell("Colophon — MS Erfurt Aug. 12°47", "colophon", body)


def build_full_site(dist_dir: Path = Path("site/dist")) -> dict:
    """Build assets, ``site_data.json``, and the five public HTML pages."""
    dist_dir = Path(dist_dir)
    data = build_site_assets_and_data(dist_dir=dist_dir)
    assets = dist_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STATIC_DIR / "site.css", assets / "site.css")
    shutil.copyfile(STATIC_DIR / "site.js", assets / "site.js")
    edition_pdf = Path("web-assets/ms-erfurt-edition.pdf")
    if edition_pdf.is_file():
        shutil.copyfile(edition_pdf, dist_dir / edition_pdf.name)
    for specimen in ("hand-nu.jpg", "hand-nu-kinematic.jpg"):
        src = Path("web-assets") / specimen
        if src.is_file():
            shutil.copyfile(src, assets / specimen)
    pages = {
        "index.html": _landing(data),
        "reader.html": _reader(data),
        "viewer.html": _viewer(),
        "folios.html": _folios(data),
        "colophon.html": _colophon(data),
    }
    for name, content in pages.items():
        (dist_dir / name).write_text(content, encoding="utf-8")
    return data


if __name__ == "__main__":
    built = build_full_site()
    print(
        f"Wrote site/dist pages for {len(built['folios'])} folios "
        f"and {len(built['sections'])} edition sections."
    )
