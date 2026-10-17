"""Build the interactive Full-Codex Page-Turner & Apparatus Explorer HTML app
for MS Erfurt Aug. 12°47 (all 34 folios f01r–f17v + 16 bound bifolium openings).
"""

from __future__ import annotations

import json
from pathlib import Path

GALLERY_DIR = Path("shared/training/handsim/first_5_folios")

SECTION_TITLES = {
    "1": "Section 1–2: Opening Declaration & The Current of Belief",
    "2": "Section 2: Die neue Kunst (The Mainz Press Meditation)",
    "3": "Section 3: The Peter Narrative (Water-Damaged & Torn Corner)",
    "4": "Section 4: Workshop Visits, Demetrios & The Truncated Augustine",
    "5": "Section 5: The 1435 Cologne Eckhart Confession ('Wirt')",
    "5-6": "Section 5 → 6 Transition: Eckhart Confession to Psalter Working Register",
    "6": "Section 6: Psalm 42 ('Desiderat'), Strikethrough & Bavarian Calfskin",
    "7": "Section 7: Final Gathering (Irregular Offcut Stock, Father Ulrich & Colophon)",
}


def build_viewer() -> None:
    cat_path = GALLERY_DIR / "damage_and_lacuna_catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8"))

    # Enrich each folio entry with its emotional lines, damage annotations, and dip events
    emo_by_folio: dict[str, dict[int, dict]] = {}
    for e in cat.get("emotional_lines", []):
        emo_by_folio.setdefault(e["folio_id"], {})[e["line_number"]] = e

    dmg_by_folio: dict[str, list[dict]] = {}
    for d in cat.get("damage_annotations", []):
        dmg_by_folio.setdefault(d["folio_id"], []).append(d)

    dips_by_folio: dict[str, list[dict]] = {}
    for dp in cat.get("dip_events", []):
        dips_by_folio.setdefault(dp["folio_id"], []).append(dp)

    for f in cat["folios"]:
        fid = f["folio_id"]
        sec_key = str(f.get("section") or ("1" if int(fid[1:3]) <= 3 else "3"))
        f["section_title"] = SECTION_TITLES.get(sec_key, f"Section {sec_key}")
        f["emotional_map"] = emo_by_folio.get(fid, {})
        f["damage_list"] = dmg_by_folio.get(fid, [])
        f["dips_list"] = dips_by_folio.get(fid, [])

    payload_json = json.dumps(cat, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>MS Erfurt Aug. 12°47 (1457) — Interactive Full-Codex Viewer (34 Folios, f01r–f17v)</title>
<style>
  :root {{
    --bg: #141210;
    --panel: #1e1b18;
    --panel-alt: #26221e;
    --border: #3b342c;
    --gold: #e6c88a;
    --amber: #d49b54;
    --text: #eee5d8;
    --muted: #b5a795;
    --badge-bg: #322b24;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Georgia, serif;
    background: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 0;
  }}
  header {{
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(24, 21, 18, 0.96);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }}
  .brand h1 {{
    font-size: 18px;
    margin: 0;
    color: var(--gold);
    letter-spacing: 0.3px;
  }}
  .brand p {{
    margin: 2px 0 0 0;
    font-size: 12px;
    color: var(--muted);
  }}
  .controls {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }}
  button, select {{
    background: var(--panel-alt);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  button:hover, select:hover {{
    border-color: var(--gold);
  }}
  button.active {{
    background: var(--gold);
    color: #181410;
    font-weight: 600;
    border-color: var(--gold);
  }}
  main {{
    max-width: 1760px;
    margin: 0 auto;
    padding: 20px 24px 60px;
  }}
  .folio-strip {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 18px;
    background: var(--panel);
    padding: 10px;
    border-radius: 8px;
    border: 1px solid var(--border);
  }}
  .folio-pill {{
    padding: 4px 8px;
    font-size: 12px;
    border-radius: 4px;
    background: #28231e;
    border: 1px solid transparent;
    color: var(--muted);
    cursor: pointer;
  }}
  .folio-pill.damaged {{ border-bottom: 2px solid #c96a4b; }}
  .folio-pill.irregular {{ border-top: 2px solid #8ba888; }}
  .folio-pill.active {{
    background: var(--gold);
    color: #161310;
    font-weight: 700;
  }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 22px;
  }}
  .card h2 {{
    margin-top: 0;
    color: var(--gold);
    font-size: 18px;
  }}
  .meta-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 14px;
  }}
  .badge {{
    background: var(--badge-bg);
    border: 1px solid var(--border);
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    color: #e4d6c3;
  }}
  .badge.emo {{ border-color: #7c9a6d; color: #b8dca8; }}
  .badge.dmg {{ border-color: #b5654d; color: #f2b49f; }}
  .badge.mat {{ border-color: #b39758; color: #f3deaa; }}
  .viewer-grid {{
    display: grid;
    grid-template-columns: 1.25fr 1fr;
    gap: 20px;
    align-items: start;
  }}
  @media (max-width: 1200px) {{
    .viewer-grid {{ grid-template-columns: 1fr; }}
  }}
  .img-box {{
    background: #100e0c;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    text-align: center;
  }}
  .img-box img {{
    width: 100%;
    height: auto;
    border-radius: 4px;
    display: block;
  }}
  .spread-dual-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 16px;
  }}
  .line-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}
  .line-table th, .line-table td {{
    border-bottom: 1px solid #302a24;
    padding: 6px 8px;
    text-align: left;
    vertical-align: top;
  }}
  .line-table th {{
    color: var(--gold);
    font-weight: 600;
    background: #191614;
    position: sticky;
    top: 0;
  }}
  .line-num {{
    color: var(--muted);
    font-family: monospace;
    white-space: nowrap;
  }}
  .fnhd-text {{
    font-family: Georgia, "Times New Roman", serif;
    font-size: 14px;
    color: #f6efe4;
  }}
  .eng-text {{
    font-size: 12px;
    color: #a89a88;
    font-style: italic;
    margin-top: 2px;
  }}
  .tag {{
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-family: monospace;
    margin-right: 4px;
    margin-top: 2px;
  }}
  .tag.emo-sacred_steadiness {{ background: #223b32; color: #9ce6c6; }}
  .tag.emo-deepened_attention {{ background: #362e1c; color: #f5d487; }}
  .tag.emo-tremor_agitation {{ background: #422020; color: #f7a6a6; }}
  .tag.emo-grief_hesitation {{ background: #2c263d; color: #cbb8f7; }}
  .tag.emo-latin_formal {{ background: #1e3142; color: #9ecbf2; }}
  .tag.emo-compensating_eyesight {{ background: #382c22; color: #e6bfa0; }}
  .tag.dmg-tag {{ background: #4a2319; color: #ffbfa8; }}
  .tag.strike-tag {{ background: #45381a; color: #ffe08a; text-decoration: line-through; }}
  .scroll-box {{
    max-height: 780px;
    overflow-y: auto;
    border: 1px solid var(--border);
    border-radius: 6px;
  }}
  .overview-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }}
  .thumb-card {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    cursor: pointer;
    transition: transform 0.12s ease, border-color 0.12s ease;
  }}
  .thumb-card:hover {{
    transform: translateY(-2px);
    border-color: var(--gold);
  }}
  .thumb-card img {{
    width: 100%;
    height: auto;
    border-radius: 4px;
  }}
  .thumb-card h4 {{
    margin: 8px 0 4px 0;
    color: var(--gold);
    font-size: 14px;
  }}
  .thumb-card p {{
    margin: 0;
    font-size: 12px;
    color: var(--muted);
  }}
</style>
</head>
<body>

<header>
  <div class="brand">
    <h1>MS Erfurt Aug. 12°47 (1457) — Brother Konrad Complete Codex Explorer</h1>
    <p>34 Folios (f01r–f17v) &bull; 16 Bound Bifolium Openings &bull; Calfskin (Hair/Flesh Gregory's Rule) &amp; Irregular Offcut Stock &bull; Use <b>&larr; / &rarr;</b> arrow keys to turn pages</p>
  </div>
  <div class="controls">
    <button id="mode-folio" class="active" onclick="setMode('folio')">Single Folio Inspector (34)</button>
    <button id="mode-spread" onclick="setMode('spread')">Bound Codex Openings (18)</button>
    <button id="mode-overview" onclick="setMode('overview')">All 34 Folios &amp; Benchmarks Grid</button>
    <span style="border-left:1px solid var(--border); height:24px; margin:0 4px;"></span>
    <button onclick="stepItem(-1)">&larr; Prev</button>
    <select id="item-select" onchange="jumpToSelect(this.value)"></select>
    <button onclick="stepItem(1)">Next &rarr;</button>
  </div>
</header>

<main>
  <div id="folio-strip" class="folio-strip"></div>
  <div id="view-container"></div>
</main>

<script>
const CODEX = {payload_json};
let currentMode = 'folio'; // 'folio' | 'spread' | 'overview'
let currentFolioIdx = 0;   // 0..33
let currentSpreadIdx = 0;  // 0 = f01r cover, 1..16 = spreads, 17 = f17v back
let imageSubMode = 'sbs';  // 'sbs' | 'weathered' | 'clean'

function buildSpreadList() {{
  const items = [
    {{ type: 'single', label: 'Outer Front Recto: f01r (Hair Side)', folio_id: 'f01r' }}
  ];
  for (const sp of CODEX.spreads) {{
    items.push({{
      type: 'spread',
      label: `Opening #${{sp.opening_number}}: ${{sp.left_folio}} | ${{sp.right_folio}} (${{sp.vellum_side}} facing ${{sp.vellum_side}})`,
      spread: sp
    }});
  }}
  items.push({{ type: 'single', label: 'Outer Back Verso: f17v (Flesh Side Colophon)', folio_id: 'f17v' }});
  return items;
}}
const SPREAD_ITEMS = buildSpreadList();

function renderFolioStrip() {{
  const strip = document.getElementById('folio-strip');
  strip.innerHTML = CODEX.folios.map((f, idx) => {{
    const isAct = (currentMode === 'folio' && idx === currentFolioIdx) ||
                  (currentMode === 'spread' && (
                    (currentSpreadIdx === 0 && f.folio_id === 'f01r') ||
                    (currentSpreadIdx === 17 && f.folio_id === 'f17v') ||
                    (currentSpreadIdx >= 1 && currentSpreadIdx <= 16 &&
                     (f.folio_id === CODEX.spreads[currentSpreadIdx-1].left_folio ||
                      f.folio_id === CODEX.spreads[currentSpreadIdx-1].right_folio))
                  ));
    const dmgClass = f.damage_spans_count > 1 ? 'damaged' : '';
    const stockClass = f.vellum_stock === 'irregular' ? 'irregular' : '';
    return `<div class="folio-pill ${{isAct ? 'active' : ''}} ${{dmgClass}} ${{stockClass}}"
                 title="${{f.folio_id}}: ${{f.section_title}} (${{f.vellum_stock}} ${{f.vellum_side}})"
                 onclick="selectFolioFromStrip(${{idx}})">${{f.folio_id}}</div>`;
  }}).join('');
}}

function selectFolioFromStrip(idx) {{
  if (currentMode === 'spread') {{
    const fid = CODEX.folios[idx].folio_id;
    if (fid === 'f01r') currentSpreadIdx = 0;
    else if (fid === 'f17v') currentSpreadIdx = 17;
    else {{
      const found = CODEX.spreads.findIndex(s => s.left_folio === fid || s.right_folio === fid);
      if (found >= 0) currentSpreadIdx = found + 1;
    }}
  }} else {{
    currentMode = 'folio';
    currentFolioIdx = idx;
  }}
  updateUI();
}}

function setMode(m) {{
  currentMode = m;
  document.getElementById('mode-folio').classList.toggle('active', m === 'folio');
  document.getElementById('mode-spread').classList.toggle('active', m === 'spread');
  document.getElementById('mode-overview').classList.toggle('active', m === 'overview');
  updateUI();
}}

function setImageSubMode(sm) {{
  imageSubMode = sm;
  updateUI();
}}

function stepItem(delta) {{
  if (currentMode === 'folio') {{
    currentFolioIdx = (currentFolioIdx + delta + CODEX.folios.length) % CODEX.folios.length;
  }} else if (currentMode === 'spread') {{
    currentSpreadIdx = (currentSpreadIdx + delta + SPREAD_ITEMS.length) % SPREAD_ITEMS.length;
  }}
  updateUI();
}}

function jumpToSelect(val) {{
  const n = parseInt(val, 10);
  if (currentMode === 'folio') currentFolioIdx = n;
  else if (currentMode === 'spread') currentSpreadIdx = n;
  updateUI();
}}

function renderLineTable(f) {{
  const dmgByLine = {{}};
  for (const d of f.damage_list) {{
    if (!dmgByLine[d.line_number]) dmgByLine[d.line_number] = [];
    dmgByLine[d.line_number].push(d);
  }}
  const rows = f.lines_data.map(l => {{
    const ln = l.number;
    const emo = f.emotional_map[ln];
    const dmgs = dmgByLine[ln] || [];
    let badges = `<span class="tag">${{l.register}}</span>`;
    if (emo) {{
      badges += `<span class="tag emo-${{emo.state_name}}" title="${{emo.rationale}}">${{emo.state_name}}</span>`;
    }}
    for (const d of dmgs) {{
      const cls = d.damage_type === 'strikethrough' ? 'strike-tag' : 'dmg-tag';
      badges += `<span class="tag ${{cls}}" title="${{d.note}}">${{d.damage_type}}: ${{d.word}}</span>`;
    }}
    const isStruck = dmgs.some(d => d.damage_type === 'strikethrough');
    const txtStyle = isStruck ? 'text-decoration: line-through; color: #d8b98a;' : '';
    return `<tr>
      <td class="line-num">L${{String(ln).padStart(2, '0')}}</td>
      <td>
        <div class="fnhd-text" style="${{txtStyle}}">${{l.text}}</div>
        ${{l.english ? `<div class="eng-text">${{l.english}}</div>` : ''}}
      </td>
      <td>${{badges}}</td>
    </tr>`;
  }}).join('');
  return `<div class="scroll-box">
    <table class="line-table">
      <thead><tr><th>Line</th><th>1457 Thuringian FNHD / Latin / MHG &amp; Translation</th><th>State &amp; Apparatus</th></tr></thead>
      <tbody>${{rows}}</tbody>
    </table>
  </div>`;
}}

function updateUI() {{
  renderFolioStrip();
  const sel = document.getElementById('item-select');
  if (currentMode === 'folio') {{
    sel.innerHTML = CODEX.folios.map((f, i) =>
      `<option value="${{i}}" ${{i === currentFolioIdx ? 'selected' : ''}}>${{f.folio_id}} — ${{f.section_title}} (${{f.vellum_stock}}/${{f.vellum_side}})</option>`
    ).join('');
  }} else if (currentMode === 'spread') {{
    sel.innerHTML = SPREAD_ITEMS.map((it, i) =>
      `<option value="${{i}}" ${{i === currentSpreadIdx ? 'selected' : ''}}>${{it.label}}</option>`
    ).join('');
  }} else {{
    sel.innerHTML = `<option value="0">Full 34-Folio Codex Overview</option>`;
  }}

  const container = document.getElementById('view-container');

  if (currentMode === 'folio') {{
    const f = CODEX.folios[currentFolioIdx];
    const imgSrc = imageSubMode === 'sbs' ? `${{f.folio_id}}_side_by_side.png`
                 : imageSubMode === 'weathered' ? `${{f.folio_id}}_weathered.png`
                 : `${{f.folio_id}}_clean.png`;
    container.innerHTML = `
      <div class="card">
        <h2>Folio ${{f.folio_id}} — ${{f.section_title}}</h2>
        <div class="meta-bar">
          <span class="badge mat">Vellum Stock: <b>${{f.vellum_stock}}</b> (${{f.vellum_side}} side)</span>
          <span class="badge">Lines: <b>${{f.lines}}</b> (${{f.size_px[0]}}&times;${{f.size_px[1]}} px)</span>
          <span class="badge">Quill Dips: <b>${{f.quill_dips_count}}</b></span>
          <span class="badge emo">Emotional/Affect Lines: <b>${{f.emotional_lines_count}}</b></span>
          <span class="badge dmg">Damage/Lacuna/Strike Spans: <b>${{f.damage_spans_count}}</b></span>
          <span class="badge">Hybrid Centerline IoU: <b>${{f.hybrid_iou.toFixed(4)}}</b></span>
        </div>
        <div style="margin-bottom: 12px; display:flex; gap:8px;">
          <button class="${{imageSubMode === 'sbs' ? 'active' : ''}}" onclick="setImageSubMode('sbs')">Side-by-Side (Clean vs. Weathered)</button>
          <button class="${{imageSubMode === 'weathered' ? 'active' : ''}}" onclick="setImageSubMode('weathered')">560-Yr Weathered Only</button>
          <button class="${{imageSubMode === 'clean' ? 'active' : ''}}" onclick="setImageSubMode('clean')">Clean Kinematic Only</button>
        </div>
        <div class="viewer-grid">
          <div class="img-box">
            <img src="${{imgSrc}}" alt="${{f.folio_id}}" />
          </div>
          <div>
            ${{renderLineTable(f)}}
          </div>
        </div>
      </div>
    `;
  }} else if (currentMode === 'spread') {{
    const item = SPREAD_ITEMS[currentSpreadIdx];
    if (item.type === 'single') {{
      const f = CODEX.folios.find(x => x.folio_id === item.folio_id);
      container.innerHTML = `
        <div class="card">
          <h2>${{item.label}} — ${{f.section_title}}</h2>
          <div class="viewer-grid">
            <div class="img-box"><img src="${{f.folio_id}}_weathered.png" /></div>
            <div>${{renderLineTable(f)}}</div>
          </div>
        </div>
      `;
    }} else {{
      const sp = item.spread;
      const fl = CODEX.folios.find(x => x.folio_id === sp.left_folio);
      const fr = CODEX.folios.find(x => x.folio_id === sp.right_folio);
      container.innerHTML = `
        <div class="card">
          <h2>${{item.label}}</h2>
          <div class="meta-bar">
            <span class="badge mat">Gregory's Rule: <b>${{sp.vellum_side.toUpperCase()}} facing ${{sp.vellum_side.toUpperCase()}}</b></span>
            <span class="badge">Left (${{fl.folio_id}}): ${{fl.section_title}} (${{fl.vellum_stock}})</span>
            <span class="badge">Right (${{fr.folio_id}}): ${{fr.section_title}} (${{fr.vellum_stock}})</span>
          </div>
          <div class="img-box">
            <img src="${{sp.image}}" alt="Spread ${{sp.left_folio}} ${{sp.right_folio}}" />
          </div>
          <div class="spread-dual-grid">
            <div>
              <h3 style="color:var(--gold); margin:8px 0;">Left Verso: ${{fl.folio_id}} (${{fl.lines}} lines, ${{fl.quill_dips_count}} dips)</h3>
              ${{renderLineTable(fl)}}
            </div>
            <div>
              <h3 style="color:var(--gold); margin:8px 0;">Right Recto: ${{fr.folio_id}} (${{fr.lines}} lines, ${{fr.quill_dips_count}} dips)</h3>
              ${{renderLineTable(fr)}}
            </div>
          </div>
        </div>
      `;
    }}
  }} else {{
    const thumbs = CODEX.folios.map((f, i) => `
      <div class="thumb-card" onclick="currentMode='folio'; currentFolioIdx=${{i}}; setMode('folio');">
        <img src="${{f.folio_id}}_weathered.png" loading="lazy" />
        <h4>${{f.folio_id}} — ${{f.vellum_stock}} (${{f.vellum_side}})</h4>
        <p>${{f.section_title}}<br/>${{f.lines}} lines &bull; ${{f.quill_dips_count}} dips &bull; ${{f.emotional_lines_count}} affect &bull; ${{f.damage_spans_count}} dmg</p>
      </div>
    `).join('');
    container.innerHTML = `
      <div class="card">
        <h2>4-Pillar Zoomed Inspection: Deepened Attention &amp; Dip Cycle, Tremor, Sacred Steadiness, and Intra-Letter Brown Iron-Gall</h2>
        <div class="img-box"><img src="scribal_and_material_callouts.png" /></div>
      </div>
      <div class="card">
        <h2>Full-Page Weathering Benchmark Comparison</h2>
        <div class="img-box"><img src="weathering_benchmark_comparison.png" /></div>
      </div>
      <div class="card">
        <h2>All 34 Weathered Folios (f01r–f17v) — Click Any Leaf to Inspect Side-by-Side &amp; Line Apparatus</h2>
        <div class="overview-grid">${{thumbs}}</div>
      </div>
    `;
  }}
}}

window.addEventListener('keydown', (e) => {{
  if (e.key === 'ArrowLeft') stepItem(-1);
  else if (e.key === 'ArrowRight') stepItem(1);
}});

updateUI();
</script>
</body>
</html>
"""
    out_file = GALLERY_DIR / "index.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"Wrote interactive 34-folio Codex Explorer to {out_file}")


if __name__ == "__main__":
    build_viewer()
