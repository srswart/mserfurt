"""ADV-SITE-DATA-001: Extract design bundle assets, optimize 34 folio & 16 spread
images for fast web delivery, and compile `site/dist/data/site_data.json` containing
all 34 folios' CLIO-7 overlay coordinates and the complete 7-section English edition.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import shutil
from pathlib import Path
from PIL import Image

DESIGN_BUNDLE_PATH = Path("docs/site/MS Erfurt Aug. 12°47 — Edition & Manuscript.html")
CATALOG_PATH = Path("shared/training/handsim/first_5_folios/damage_and_lacuna_catalog.json")
GALLERY_DIR = Path("shared/training/handsim/first_5_folios")

SECTION_META = {
    1: ("I", "The current of belief", "I · The current of belief", "1r–3r"),
    2: ("II", "Die neue Kunst", "II · Die neue Kunst", "3v"),
    3: ("III", "Peter", "III · Peter", "4r–5v"),
    4: ("IV", "The workshop", "IV · The workshop", "6r–6v, 8r–9r"),
    5: ("V", "Wirt", "V · The Eckhart commentary", "7r–7v, 9v–10v"),
    6: ("VI", "Psalm 42", "VI · Psalm 42", "7v, 11r–13v"),
    7: ("VII", "The final gathering", "VII · The final gathering", "14r–17v"),
}

FOLIO_SECTION_MAP = {
    "f01r": 1, "f01v": 1, "f02r": 1, "f02v": 1, "f03r": 1,
    "f03v": 2,
    "f04r": 3, "f04v": 3, "f05r": 3, "f05v": 3,
    "f06r": 4, "f06v": 4,
    "f07r": 5, "f07v": 5,
    "f08r": 4, "f08v": 4, "f09r": 4,
    "f09v": 5, "f10r": 5, "f10v": 5,
    "f11r": 6, "f11v": 6, "f12r": 6, "f12v": 6, "f13r": 6, "f13v": 6,
    "f14r": 7, "f14v": 7, "f15r": 7, "f15v": 7, "f16r": 7, "f16v": 7, "f17r": 7, "f17v": 7,
}

HAND_NOTES_BY_FOLIO = {
    "f01r": "CLIO-7: standard scriptorium Bastarda hand on selected calfskin (hair side); opening incipit rubric formula.",
    "f01v": "CLIO-7: localized moisture smudge over line 3 ('beschädigten Texte'); deepened attention on lines 7–9.",
    "f02r": "CLIO-7: slight vellum crease at line 20 ('gerissenen Pergament'); pressure deepens at line 14 ('Ich bin froh, daß es meine hand gewesen ist').",
    "f02v": "CLIO-7: hand shows slight agitation and heavier lateral attack from line 18 where the Mainz press is first described.",
    "f03r": "CLIO-7: physiological tremor at line 12 ('zu zittern, zu irren'); deliberate stroke thickening on lines 21–23 ('die leise Verdickung des Striches').",
    "f03v": "CLIO-7: outer edge of upper water propagation from folio 4r; Lacuna #0 before 'bestohn' on line 9.",
    "f04r": "CLIO-7: the hand slows and lightens where the account of Peter resumes; pressure ×0.90, tempo ×0.76. Water ingress from above; Lacunae #1 and #2.",
    "f04v": "CLIO-7: severe water damage from above and physical loss of the lower-right corner. Lacunae #3–#9; contested reading 'stoltz' vs. 'verloren' on line 18.",
    "f05r": "CLIO-7: garden blessing passage (lines 4–9) — 'the folio is clean here, the ink unsmeared, the hand steady' (fresh quill dip at line 4, zero tremor).",
    "f05v": "CLIO-7: Lacunae #10–#11 in morning-light clause; verbatim Latin quotation from Augustine Confessions I.1 before 1–3 missing folios gap.",
    "f06r": "CLIO-7: increased lateral pressure on downstrokes, consistent with either agitation or fatigue at time of writing.",
    "f06v": "CLIO-7: increased lateral pressure persists across the leaf; upright formal shift on Latin Confessions Book III crux.",
    "f07r": "CLIO-7: written across multiple sittings — ink density changes after lines 8, 17 and 23. No damage. No lacunae. The author wanted this one legible.",
    "f07v": "CLIO-7: Middle High German verb crux ('Ist — Enpfêhet — Wirt') on lines 5–9; from line 17 the hand returns to the smaller, economical working register (85% scale).",
    "f08r": "CLIO-7: Demetrios alley-window dialogue and the 1280 Bruges reader reflection.",
    "f08v": "CLIO-7: Canon Hartmann's house dialogue on Eckhart's condemnation ('Every copyist a theologian. Every scriptorium a council').",
    "f09r": "CLIO-7: account of Ibrahim the Cairo calligrapher in Constantinople ('The sacred text requires the sacred hand').",
    "f09v": "CLIO-7: detailed reflection on Pope John XXII's 1329 bull In agro dominico and the twenty-eight condemned propositions.",
    "f10r": "CLIO-7: analysis of how a scribe reconstructs a cracked calfskin manuscript ('Ist — Enpfêhet — Wirt').",
    "f10v": "CLIO-7: confession of the sin of replacement ('between the human mind and the truth there must be a gap').",
    "f11r": "CLIO-7: vocabulary meditation on Psalm 42 ('desiderat — a word with the body in it, always in the place of not-yet').",
    "f11v": "CLIO-7: fresh quill dip at line 12 ('Ich tauche die Feder ein') before 'Sic desiderat anima mea ad te, Deus'.",
    "f12r": "CLIO-7: line 1 ('Vielleicht ist das alles, was wir sint') crossed out by the scribe with a 4-sweep wavy quill cancellation yet left legible; Bavarian calfskin ('baierisch Kalbfell') noted at line 21.",
    "f12v": "CLIO-7: reflection on Becker's sons and the transmission of Augustine and Eckhart.",
    "f13r": "CLIO-7: final leaf of the standard calfskin gathering before switching to the uneven offcut sheets at the back of the chest.",
    "f13v": "CLIO-7: closing verse of Becker's Psalter ('Omnis spiritus laudet Dominum') before the four-month autumn-to-winter pause.",
}

STATE_SHORT_LABELS = {
    "sacred_steadiness": "steady · ×0.88",
    "deepened_attention": "deepened · ×1.22",
    "tremor_agitation": "tremor · ×1.18",
    "grief_hesitation": "slowed · ×0.76",
    "latin_formal": "Latin · formal",
    "compensating_eyesight": "wider · ×0.82",
}


def _extract_design_bundle_assets(dist_dir: Path) -> None:
    """Extract `mobius.jpg` and `EB Garamond` WOFF2 fonts from the Claude Design HTML bundle."""
    assets_dir = dist_dir / "assets"
    fonts_dir = assets_dir / "fonts"
    assets_dir.mkdir(parents=True, exist_ok=True)
    fonts_dir.mkdir(parents=True, exist_ok=True)

    html = DESIGN_BUNDLE_PATH.read_text(encoding="utf-8")
    m_man = re.search(r'<script type="__bundler/manifest">(.*?)</script>', html, re.S)
    if not m_man:
        return
    root_man = json.loads(m_man.group(1))
    landing_entry = root_man.get("fd53524a-8d15-453c-a6ec-419580c81edb")
    if not landing_entry:
        return

    raw = base64.b64decode(landing_entry["data"])
    if landing_entry.get("compressed"):
        raw = gzip.decompress(raw)
    landing_html = raw.decode("utf-8")
    sub_man_match = re.search(r'<script type="__bundler/manifest">(.*?)</script>', landing_html, re.S)
    if not sub_man_match:
        return
    sub_man = json.loads(sub_man_match.group(1))

    # 1. Möbius vellum hero image (`b70aeaff-b187-4eec-9840-8fdd4df55f77`)
    mob_entry = sub_man.get("b70aeaff-b187-4eec-9840-8fdd4df55f77")
    if mob_entry:
        mob_bytes = base64.b64decode(mob_entry["data"])
        if mob_entry.get("compressed"):
            mob_bytes = gzip.decompress(mob_bytes)
        (assets_dir / "mobius.jpg").write_bytes(mob_bytes)

    # 2. EB Garamond WOFF2 fonts (`f3313302...` italic, `f9575078...` normal)
    for uuid, fname in [
        ("f3313302-dbf5-4a92-a93a-8d3ae35b2515", "eb-garamond-italic.woff2"),
        ("f9575078-80ef-4bc6-84ba-2962d7e6e0bb", "eb-garamond-normal.woff2"),
    ]:
        f_entry = sub_man.get(uuid)
        if f_entry:
            f_bytes = base64.b64decode(f_entry["data"])
            if f_entry.get("compressed"):
                f_bytes = gzip.decompress(f_bytes)
            (fonts_dir / fname).write_bytes(f_bytes)


def _export_web_folio_images(dist_dir: Path, cat: dict) -> None:
    """Convert weathered/clean folios, spreads, and callout sheets to optimized web JPEGs."""
    folios_dir = dist_dir / "assets" / "folios"
    folios_dir.mkdir(parents=True, exist_ok=True)

    for f in cat["folios"]:
        fid = f["folio_id"]
        w_src = GALLERY_DIR / f"{fid}_weathered.png"
        c_src = GALLERY_DIR / f"{fid}_clean.png"
        out_jpg = folios_dir / f"{fid}.jpg"
        out_clean_jpg = folios_dir / f"{fid}_clean.jpg"
        out_thumb = folios_dir / f"{fid}_thumb.jpg"

        if w_src.exists() and not out_jpg.exists():
            im = Image.open(w_src).convert("RGB")
            im.save(str(out_jpg), format="JPEG", quality=88, optimize=True)
            th_w = round(im.width * (340.0 / im.height))
            im.resize((th_w, 340), Image.LANCZOS).save(str(out_thumb), format="JPEG", quality=84, optimize=True)
        if c_src.exists() and not out_clean_jpg.exists():
            im_c = Image.open(c_src).convert("RGB")
            im_c.save(str(out_clean_jpg), format="JPEG", quality=86, optimize=True)

    for sp in cat.get("spreads", []):
        sp_png = GALLERY_DIR / sp["image"]
        sp_jpg = folios_dir / sp["image"].replace(".png", ".jpg")
        if sp_png.exists() and not sp_jpg.exists():
            im_sp = Image.open(sp_png).convert("RGB")
            im_sp.save(str(sp_jpg), format="JPEG", quality=86, optimize=True)

    for extra_png, extra_jpg in [
        ("scribal_and_material_callouts.png", "scribal_and_material_callouts.jpg"),
        ("f01r_side_by_side.png", "f01r_side_by_side.jpg"),
        ("edge_and_corner_curl_callouts.png", "edge_and_corner_curl_callouts.jpg"),
        ("f12r_strikethrough_after.png", "f12r_strikethrough_after.jpg"),
    ]:
        src_p = GALLERY_DIR / extra_png
        dst_p = dist_dir / "assets" / extra_jpg
        if src_p.exists():
            Image.open(src_p).convert("RGB").save(str(dst_p), format="JPEG", quality=88, optimize=True)


def _build_edition_sections() -> list[dict]:
    """Build the 8 scholarly reading sections (Preface + Sections I–VII) with CLIO-7 apparatus."""
    return [
        {
            "id": "preface",
            "roman": "Preface",
            "nav_title": "Translator’s Preface",
            "title": "Translator’s Preface",
            "folio_range": "MS Erfurt Aug. 12°47",
            "start_folio": "f01r",
            "progress_pct": 8,
            "banner": (
                "CLIO-7 Critical Edition — Institut für Digitale Paläographie, Erfurt",
                "Recovered in 2019 during the cataloguing of the Augustinian archive at Erfurt: seventeen unindexed folios bound between a fifteenth-century Breviarium and an older Lectionary. Written in a professional Thuringian Bastarda hand dated 1457.",
            ),
            "paragraphs": [
                'The manuscript catalogued as <em>MS Erfurt Aug. 12°47</em> consists of a single gathering of seventeen vellum leaves (thirty-four written sides), measuring approximately 148 × 204 mm in its standard calfskin stock (folios 1–13) and slightly smaller, unevenly trimmed dimensions in its final four leaves (folios 14–17).',
                'The author identifies himself in the text only as Brother Konrad, the third scribe from the window in the Augustinian scriptorium at Erfurt, writing in the forty-third year of his life and the thirtieth year of his service at the desk. He addresses his account in the second person to God — and, as he admits in the final gathering, to whoever may eventually find the leaves between the two liturgical volumes where he concealed them.',
                'Folios 4r through 5v suffered liquid ingress from above at an undetermined point prior to modern recovery, accompanied by the physical loss of the lower-right corner of folio 4v. In accordance with CLIO-7 editorial protocol, words and phrases reconstructed at 60–80% confidence are set in <span class="c2">italics</span>; passages below 60% confidence are set in <span class="c1">bold italics</span>; and lacunae of four words or more are marked <abbr class="lac" title="Lacuna of four or more words">[—]</abbr>. Nothing reconstructed is presented as certain.',
            ],
            "apparatus": [
                {
                    "type": "vellum",
                    "folio": "f01r",
                    "label": "Folio 1r, lines 1–23",
                    "thumb": "/assets/folios/f01r_thumb.jpg",
                },
                {
                    "type": "note",
                    "heading": "Archival Provenance",
                    "body": "Bound without shelfmark entry between a Breviarium and a Lectionary in the Erfurt Augustinian house. First digitized and transcribed by CLIO-7 in 2019.",
                },
                {
                    "type": "note",
                    "heading": "Collation & Support",
                    "body": "Folios 1r–13v: fine Bavarian/Thuringian calfskin collated according to Gregory’s Rule (hair facing hair, flesh facing flesh). Folios 14r–17v: rougher offcut remnant stock.",
                },
            ],
            "has_contested_reading": False,
        },
        {
            "id": "sec-1",
            "roman": "I",
            "nav_title": "I · The current of belief",
            "title": "The current of belief",
            "folio_range": "Folios 1r–2v · standard calfskin",
            "start_folio": "f01r",
            "progress_pct": 18,
            "banner": (
                "CLIO-7 Reconstruction — MS Erfurt Aug. 12°47, Folios 1r–2v",
                "Standard scriptorium hand. Minor outer-margin rub on folio 1r line 1 and localized damp spot over 'beschädigten Texte' on folio 1v line 3.",
            ),
            "paragraphs": [
                'Here begins what a scribe could not keep from writing, in the forty-third year of his life, in the year of Our Lord 1457, in the city of Erfurt, <em>sine licentia et sine excusatione</em> — without permission and without excuse.',
                '✦ ✦ ✦',
                'The current of belief is not mine. I want to say that first, before anything else, because everything that follows depends on understanding that I know this.',
                'I have been a scribe for thirty years. I have copied the Word as it passed through — Psalms, Gospels, the great commentators, the minor ones — and I understood early that my role in this was what a pebble’s role is in a river. The current moves. The pebble does not direct it. The pebble is <span class="c2">carried, shaped, worn smooth</span> in the places the water finds, and this is not a small thing, to be shaped by what passes through you, but it is not the same as choosing.',
                'And yet.',
                'In the winter of 1435, the current moved through my particular hand in a way it has not moved before or since. I was alone at a desk with a <span class="c2">damaged text</span> and a question the text could not answer for itself, and something — I will not call it inspiration, that is not mine to claim — something arrived in the specific pressure of my fingers on the quill, in the particular quality of attention I had that morning, and I made a choice that was not mine to make, and the choice was right, and I have been doing penance for it ever since.',
                'I want to be honest about the penance. It is real. I do not perform it.',
                'I also want to be honest about the other thing, the thing beneath the penance, which I have not said to anyone and am now saying to You because You already know it and I am tired of carrying it alone:',
                'I am glad it was my hand.',
                'Not proud. I want that distinction to be clear, though I am aware it may not survive scrutiny. The gladness is not in the having done it. It is in the having been — for one morning, in one cold room, with one <span class="c2">cracked manuscript</span> — the place where the current needed to go. A pebble does not boast of the water that moved through it. But a pebble might, in its silence, know what it carried. And that knowing is what I am trying to write toward.',
                'Everything else — the press, the student I lost, <span class="c2">the eyes that are failing</span> — is the river explaining itself to me now. I am trying to understand what I was used for before the water moves on entirely and I am left dry on the bank, which is coming, which is perhaps already here.',
            ],
            "apparatus": [
                {
                    "type": "vellum",
                    "folio": "f01r",
                    "label": "Folio 1r, lines 1–23",
                    "thumb": "/assets/folios/f01r_thumb.jpg",
                },
                {
                    "type": "note",
                    "heading": "Opening Rubric · f. 1r · l. 1–5",
                    "body": "Konrad opens with a formal Latin/German incipit formula ('Hie hebt sich an... sine licentia et sine excusatione') before shifting to personal Thuringian vernacular.",
                },
                {
                    "type": "note",
                    "heading": "Material Echo · f. 1v · l. 3",
                    "body": "A small damp stain on folio 1v coincides directly with the words 'mit einem beschädigten Texte' (with a damaged text). Line confidence 74%.",
                },
            ],
            "has_contested_reading": False,
        },
        {
            "id": "sec-2",
            "roman": "II",
            "nav_title": "II · Die neue Kunst",
            "title": "Die neue Kunst",
            "folio_range": "Folios 2v–3v · standard calfskin",
            "start_folio": "f03r",
            "progress_pct": 30,
            "banner": (
                "CLIO-7 Reconstruction — MS Erfurt Aug. 12°47, Folios 2v–3v",
                "Hand exhibits brief physiological tremor on folio 3r line 12 ('zu zittern') and deliberate downstroke thickening on lines 21–23 ('die leise Verdickung des Striches').",
            ),
            "paragraphs": [
                'I have been writing to You my whole life. I have never written this.',
                'I will begin with <em>die neue Kunst</em> — the press, as it is beginning to be called. Not because it is where the story ends, but because it is what shook the story loose. And because approaching the harder thing directly is not yet possible. I am a scribe. I approach from the margin and work inward.',
                'There is a machine now in Mainz — a machine that can produce in one day what I produce in four months. It sets letters in metal and stamps them onto the page with a force I felt in my feet when I stood next to it. I have stood next to it. I will tell you about that later. I will tell you why I told Brother Anselm I was going to the apothecary.',
                'The men who operate it are devout. Several of them, I think, more devout than I am. This is the problem.',
                'The pages were consistent. Letter after letter, identical, the same pressure, the same depth. A thing I have never achieved and never will achieve, not in forty more years of work. You can say this is because God made human hands <span class="c2">to tremble, to err</span>, to be particular — and that is what I tell myself walking home — but I stood there and I thought: whoever reads one of those pages will never know that a man made it. They will read only what it says.',
                'I have spent my life leaving myself in the pages. Not obviously. Not with vanity. I mean something smaller: the slight thickening of a stroke when my attention deepened, the places where I slowed because the meaning <span class="c2">entered my hands before it entered my mind</span>. Readers did not see it. But it was there. The page knew.',
                'Those pages knew nothing. They were clean in a way that struck me as a new kind of silence — not the silence of the monastery, which is full of unspoken prayer, but an empty silence in which no one had ever stood.',
                'I need certain sentences <abbr class="lac" title="Lacuna · f. 3v, line 9 · dissolved modifier before bestohn">[—]</abbr> to exist. When I am finished I will put this vellum where it may or may not be found. I am leaving that to whatever governs such things — God, if you like, or the simple persistence of matter, which has its own fidelity and does not require an explanation.',
                'I do not have that explanation yet. That is also what this is for.',
                'It is early. The Lauds bell has not yet rung. I have perhaps an hour before the house stirs and I must become Brother Konrad again, who is the third scribe from the window and does not tremble.',
            ],
            "apparatus": [
                {
                    "type": "vellum",
                    "folio": "f03r",
                    "label": "Folio 3r, lines 1–23",
                    "thumb": "/assets/folios/f03r_thumb.jpg",
                },
                {
                    "type": "note",
                    "heading": "Psychomotor Self-Reference · f. 3r · l. 21–23",
                    "body": "Where Konrad writes of 'the slight thickening of a stroke when my attention deepened', the physical stroke width increases by ×1.13 and pressure by ×1.22 as his tempo slows to ×0.80.",
                },
                {
                    "type": "note",
                    "heading": "Upper Water Precursor · f. 3v · l. 1–2, 9",
                    "body": "Folio 3v faces folio 4r in the gathering and absorbed the outer margin of the water event that struck leaf 4.",
                },
            ],
            "has_contested_reading": False,
        },
        {
            "id": "sec-3",
            "roman": "III",
            "nav_title": "III · Peter",
            "title": "Peter",
            "folio_range": "Folios 4r–5v · reconstructed",
            "start_folio": "f04r",
            "progress_pct": 41,
            "banner": (
                "CLIO-7 Reconstruction — MS Erfurt Aug. 12°47, Folio 4r–5v",
                "Confidence variable throughout. Words and phrases below 80% confidence appear in italics. Passages below 60% confidence appear in bold italics. Lacunae of four words or more are marked [—]. Readers should treat reconstructed passages as interpretive rather than authoritative.",
            ),
            "paragraphs": [
                'Peter came to me first in the autumn of his fourteenth year. This part I can write without difficulty because I have written it many times in my head, the way you return to a place you love before it is taken from you, memorizing.',
                '<span class="c2">He was small for his age, dark-haired</span>, and he held himself with a stillness that I recognized because I had felt it in myself at that age — the stillness of a person whose soul was moving very fast within him and who had learned to keep it hidden. His father was a cloth merchant. The father wanted him to have letters for the purpose of contracts and correspondence. The father was a practical man.',
                'Within three weeks I knew that Peter was <span class="c2">not going to be</span> <abbr class="lac" title="Lacuna #1 · f. 4r, line 12 · about four words washed out">[—]</abbr> the cloth trade. Within three months I knew he was the finest student I had ever taught. By spring I had stopped thinking of myself as his teacher in any meaningful sense and begun thinking of myself as the person who was <span class="c2">currently standing between him and what he was going to become</span>.',
                'I want to be careful here. I want You to see that I am being careful.',
                'I did not love Peter the way a man should not love a boy. I want that said plainly because I am aware of how this kind of account can be misread, and because the Confessions themselves have been misread in this way, and Augustinus deserved better than that and so does Peter and so, with Your permission, do I. What I felt was something I do not have a clean word for. He was the closest I ever came to having a son. He was the closest I ever came to having a successor. He was the closest I ever came to believing that what I know will not die with me.',
                'You understand why I am saying was.',
                'He stayed six years. He learned everything I could teach him and some things I did not know I knew until he asked the question that made me find out. His script by his twentieth year was <span class="c2">better than mine had been</span> <span class="c1">at thirty, which I noted in my records and told</span> <abbr class="lac" title="Lacuna #2 · f. 4r, line 21 · four words or more">[—]</abbr>. I told him he was gifted. I did not tell him how gifted, because I was afraid of what that knowledge would do to him. I think now that was wrong. I think I was protecting something that was mine, not something that was his.',
                '✦ ✦ ✦',
                '<span class="c1">He told me on a Thursday. I remember</span> <abbr class="lac" title="Lacuna #3 · f. 4v, line 7">[—]</abbr> <span class="c1">the light. There is a particular light in the scriptorium in late</span> <abbr class="lac" title="Lacuna #4 · f. 4v, line 8">[—]</abbr> <span class="c1">that I have always</span> <abbr class="lac" title="Lacuna #5 · f. 4v, line 8">[—]</abbr>. He asked if we could speak privately and I said yes and we walked to the garden and he told me that Fust’s man had come through Erfurt and that he had been offered a position in the Frankfurt workshop and that he had decided to accept it.',
                '<span class="c1">I said</span> <abbr class="lac" title="Lacuna #6 · f. 4v, line 17">[—]</abbr>.',
                '<span class="c1">He said</span> <abbr class="lac" title="Lacuna #7 · f. 4v, line 18">[—]</abbr>.',
                '<span class="c1">I said that I was</span> <abbr class="lac" title="Lacuna #8 · f. 4v, line 18">[—]</abbr> <button class="variant c1" type="button" id="inline-variant-btn" onclick="window.toggleContestedVariant()">proud</button> <abbr class="lac" title="Lacuna #9 · f. 4v, line 18 · torn lower-right corner">[—]</abbr>.',
                'He asked me then for my blessing.',
                'This part is not damaged. I want you to notice that. The folio is clean here, the ink unsmeared, the hand steady. Some things a man writes carefully because he intends them to last.',
                'He knelt in the garden, in the cold, on the stone path, and he asked me to bless his going. I put my hand on his head — he had very thick hair, the color of beech bark in rain — and I said the words one says, and then he stood and went out through the small gate in the west wall, and I went back inside and washed my pens.',
                'When you give a man your knowledge, you do not keep a copy. This is unlike the press, which keeps every copy, which is perhaps why the press does not understand what transmission costs. Now he is in Leipzig and I am <abbr class="lac" title="Lacuna #10 · f. 5v, line 12 · age count washed out">[—]</abbr> years older and my eyes, in the morning light, are <abbr class="lac" title="Lacuna #11 · f. 5v, line 13">[—]</abbr> and I think of the Krämerbrücke and the rosemary.',
                '<em>Augustinus scribit: fecisti nos ad te, Domine, et inquietum est cor nostrum donec requiescat in te.</em> I believe this. I have believed it for thirty years.',
            ],
            "apparatus": [
                {
                    "type": "vellum",
                    "folio": "f04r",
                    "label": "Folio 4r, lines 1–21",
                    "thumb": "/assets/folios/f04r_thumb.jpg",
                },
                {
                    "type": "note",
                    "heading": "Editorial note",
                    "body": "Damage consistent with liquid exposure from above; the manuscript was stored open, or read in conditions of moisture. The lower right corner of folio 4v is missing entirely. The absence is noted.",
                },
                {
                    "type": "note",
                    "heading": "Lacuna #1 · f. 4r · l. 12",
                    "body": "About four words washed out after <em>solde</em>. Line confidence 45%.",
                },
                {
                    "type": "contested",
                    "heading": "Contested reading",
                    "body": "The word rendered here is partially obscured. CLIO-7 has selected <em>stolz</em> (pride) as the more contextually coherent rendering; the alternative <em>verloren</em> (lost) cannot be ruled out.",
                },
            ],
            "has_contested_reading": True,
        },
        {
            "id": "sec-4",
            "roman": "IV",
            "nav_title": "IV · The workshop",
            "title": "The workshop",
            "folio_range": "Folios 6r–6v, 8r–9r · lateral pressure",
            "start_folio": "f06r",
            "progress_pct": 56,
            "banner": (
                "CLIO-7 Reconstruction — MS Erfurt Aug. 12°47, Folios 6r–6v & 8r–9r",
                "CLIO-7 assesses 1–3 folios missing between 5v and 6r. Hand on 6r–6v exhibits increased lateral pressure on downstrokes, consistent with agitation or fatigue.",
            ),
            "paragraphs": [
                '— and so I went back a third time.',
                'I will tell you the first two visits quickly because they are not the story, they are only what the story required before it could happen. The first time I stood in the street outside and looked at the door for a while and then went to buy eggs. I am not proud of this. The second time I went in and the foreman, a broad Flemish man named Wilhelm, showed me the type cases and explained the matrix and the punch.',
                'The third time — this time, the time that made this folio necessary — I went because I had heard from Brother Anselm that a Greek scholar was advising the printer Richter here in Erfurt on texts. There is only one Greek scholar in Erfurt, and his name is Demetrios Chrysoloras. He escaped Constantinople four years ago carrying three manuscripts in a satchel and grief I cannot imagine. I went to disprove that he was there. He was there.',
                'The workshop was louder than I remembered. A press run was in progress — two hundred copies of a canon law summary — and the sound was rhythmic and heavy, the arm of the press descending and the platen striking and the whole building absorbing the impact like a struck bell that does not ring but only thickens.',
                'Demetrios showed me the forme prepared for tomorrow’s run, locked in its chase: a page of Augustine, Book Three of the <em>Confessions</em>. I leaned close and read the Latin in the set type, letter by reversed letter: <em>fecisti nos ad te.</em>',
                'The standard text — the text I have copied fourteen times — reads: <em>fecisti nos ad te, et inquietum est cor nostrum donec requiescat in te.</em> The compositor had set only the first clause! I said: “He cut the sentence. <em>Inquietum est cor nostrum</em> — the restlessness, the incompletion, the <em>donec</em> — the until — remove the until and you have a statement about direction. Keep it and you have a statement about what it means to be human.”',
                'Demetrios said: “You understand that this will happen. Not the truncation — I mean the other thing. Where five hundred people read Augustine tomorrow and not one of them will know that a man spent six months with this text, that the man wept at a particular sentence, that the man’s changed hand copied it with a different pressure than the lines before and after, and that a reader in Bruges in 1280 noticed the pressure changing and slowed down because of it. There is a library in Constantinople that is ash. I watched it burn for two days. I would like there to be too many copies to burn. <em>Haec est theologia mea.</em>”',
                'Later, at Canon Hartmann’s house over wine, Demetrios told me of his colleague Ibrahim from Cairo, who showed him a page of the Quran in his own hand and explained that the letter formed by a trained and devoted hand carries something a block of metal cannot — that the sacred text requires the sacred hand.',
            ],
            "apparatus": [
                {
                    "type": "vellum",
                    "folio": "f06r",
                    "label": "Folio 6r, lines 1–23",
                    "thumb": "/assets/folios/f06r_thumb.jpg",
                },
                {
                    "type": "note",
                    "heading": "Gathering Gap · before f. 6r",
                    "body": "Folio 6r begins mid-sentence ('— und also gieng ich zum dritten male widerumb'). Physical sewing evidence indicates 1–3 leaves were removed before binding.",
                },
                {
                    "type": "note",
                    "heading": "Agitation & Lateral Pressure · f. 6r–6v",
                    "body": "Downstroke pressure rises to ×1.18 with +3.4° forward slant shear across folios 6r and 6v as Konrad recounts confronting the composed metal forme.",
                },
            ],
            "has_contested_reading": False,
        },
        {
            "id": "sec-5",
            "roman": "V",
            "nav_title": "V · Wirt",
            "title": "Wirt",
            "folio_range": "Folios 7r–7v, 9v–10v · multiple sittings",
            "start_folio": "f07r",
            "progress_pct": 72,
            "banner": (
                "CLIO-7 Reconstruction — MS Erfurt Aug. 12°47, Folios 7r–7v & 9v–10v",
                "Written across multiple sittings (ink reloads at lines 9 and 18 on folio 7r). The hand remains deliberate throughout. No damage. No lacunae. The author, it appears, wanted this one legible.",
            ),
            "paragraphs": [
                'Here is what I want to ask You, <em>Domine</em>, and cannot ask anyone else: if a man tends a damaged text — if he mends what was broken in it — and then a machine fixes the lesser version into permanence, which one of them has done the greater violence to the Word?',
                'In the winter of 1435 I was given a commission by a canon in Cologne who had acquired an old manuscript of Meister Eckhart’s German sermons, the vellum cracking at the folds, brown at the edges from being hidden in damp places since Pope John’s bull <em>In agro dominico</em> of 1329.',
                'I copied for three weeks before I found the passage in the twelfth sermon, on the birth of the Word in the soul (<em>nativitas Verbi in anima</em>). The passage in the manuscript read:',
                '<em>In sînem grunde: diu sêle ist daz wort.</em> — In its ground: the soul is the Word.',
                'I set down my pen. I sat for a long time. <em>Is.</em> Not receives. Not reflects. Not participates in. Not even becomes. A flat declarative identity that made the condemned propositions look cautious by comparison.',
                'The word <em>ist</em> was partially obscured. The calfskin vellum was cracked precisely at the verb, the ink lifting at the fold. Three Middle High German words were compatible with the surviving letters:',
                '<em>Ist</em> (is — heretical, condemned). <em>Enpfêhet</em> (receives — orthodox, safe, and in my judgment a frightened flattening of Eckhart). <em>Wirt</em> (becomes — mine. Not in the manuscript, but what I believed Eckhart meant: the living act in which the soul in contemplation becomes what it beholds).',
                'I wrote <em>wirt</em>. I wrote it in a clean hand with no marginal gloss, no <em>sic</em>, as though it had always been there.',
                'It was an act of love. And it was a sin. Not because I was wrong. Because the text was not mine. Because between the human mind and the truth there must be a gap, a declared uncertainty. If there had been a press in 1435, I could not have done what I did. The press would have taken my capacity to sin. I do not know if that is salvation or diminishment.',
            ],
            "apparatus": [
                {
                    "type": "vellum",
                    "folio": "f07r",
                    "label": "Folio 7r, lines 1–23",
                    "thumb": "/assets/folios/f07r_thumb.jpg",
                },
                {
                    "type": "note",
                    "heading": "Multi-Sitting Ink Shifts · f. 7r",
                    "body": "Spectroscopic and optical density shifts occur after lines 8 and 17 on folio 7r, showing Konrad set the pen down and returned in three separate sittings.",
                },
                {
                    "type": "note",
                    "heading": "The MHG Verb Crux · f. 7v · l. 5–9",
                    "body": "Konrad writes the three Middle High German readings ('Ist — Enpfêhet — Wirt') with heightened pressure (×1.22) and slowed tempo (×0.78).",
                },
            ],
            "has_contested_reading": False,
        },
        {
            "id": "sec-6",
            "roman": "VI",
            "nav_title": "VI · Psalm 42",
            "title": "Psalm 42",
            "folio_range": "Folios 7v (lower), 11r–13v · working register",
            "start_folio": "f12r",
            "progress_pct": 86,
            "banner": (
                "CLIO-7 Reconstruction — MS Erfurt Aug. 12°47, Folios 7v (l. 17–23) & 11r–13v",
                "Hand returns to the author's standard scriptorium working register (85% scale on 7v lower half). Folio 12r line 1 bears an intentional four-sweep quill strikethrough left legible by the author.",
            ),
            "paragraphs": [
                'The Psalter is due in six weeks. I write that here because it is the truest sentence I know how to produce this morning. The merchant Becker has paid half already and my eyes are better in morning light through the east window.',
                'Psalm 42 this morning: <em>Quemadmodum desiderat cervus ad fontes aquarum.</em> As the deer longs for the water-brooks. Eleven times I have copied this psalm. This morning the word that stopped me was <em>desiderat</em> — longs, desires, thirsts. A word with the body in it. Not <em>quaerit</em>, seeks. Not <em>amat</em>, loves. <em>Desiderat</em>, a wanting that knows where the thing it wants is located but cannot get there, always in the place of not-yet.',
                '<em>Inquietum est cor nostrum donec requiescat in te.</em> I set down the pen for a moment. Then I picked it up. The work is still the work. I dip the pen. <em>Sic desiderat anima mea ad te, Deus.</em> The soul is constitutively the animal that is on the way.',
                '<span style="text-decoration: line-through wavy #A8321F; color: #5E5246">Perhaps that is all any of us are.</span>',
                'I wrote that and then I crossed it out because it is the kind of sentence that sounds wise and is actually just tired. But I am leaving the crossing-out because You saw me write it and You saw me cross it out and the crossing-out is also true.',
                'Becker came yesterday to check the progress. He looked at the completed folios and said they were very fine, and then he said his cousin in Frankfurt had told him you could get a printed Book of Hours now for less than the cost of the bare vellum alone, and he laughed in a way that was not comfortable.',
                'I said the vellum in his Psalter was Bavarian calfskin (<em>baierisch Kalbfell</em>), very fine, I had selected it myself. He nodded. There was a silence. He said: “It will be something my sons can hold.” I said: “Yes.” He said: “And their sons.” I said: “<em>Deo volente.</em> God willing.”',
            ],
            "apparatus": [
                {
                    "type": "vellum",
                    "folio": "f12r",
                    "label": "Folio 12r, lines 1–23",
                    "thumb": "/assets/folios/f12r_thumb.jpg",
                },
                {
                    "type": "note",
                    "heading": "Scribal Cancellation · f. 12r · l. 1",
                    "body": "Line 1 ('Vielleicht ist das alles, was wir sint') is cancelled with four undulating 40°-nib quill sweeps, leaving the underlying letterforms intentionally legible.",
                },
                {
                    "type": "note",
                    "heading": "Bavarian Calfskin · f. 12r · l. 20–21",
                    "body": "Konrad explicitly names his preferred writing support ('baierisch Kalbfell, gar fein'), matching the standard calfskin stock of folios 1–13.",
                },
            ],
            "has_contested_reading": False,
        },
        {
            "id": "sec-7",
            "roman": "VII",
            "nav_title": "VII · The final gathering",
            "title": "The final gathering",
            "folio_range": "Folios 14r–17v · irregular offcut stock",
            "start_folio": "f14r",
            "progress_pct": 100,
            "banner": (
                "CLIO-7 Reconstruction — MS Erfurt Aug. 12°47, Folios 14r–17v",
                "Written ~4 months after folio 13v on a different vellum stock — smaller, cut unevenly, as though taken from an offcut sheet (17 lines per page). Hand is slower and more widely spaced, compensating for failing eyesight.",
            ),
            "paragraphs": [
                'The Psalter is finished. I delivered it to Becker on the feast of Saint Nicholas. He held it close, the spine resting in his palm, and opened it to the middle and read for a moment in silence and looked up and said nothing, which was the right response. His eight-year-old son was there. I thought about Peter.',
                'The letter from Strasbourg arrived eleven days later. It was from Father Ulrich at the Augustinian house there, who had traced a variant reading in Meister Eckhart’s twelfth sermon back to an Erfurt copy made in the winter of 1435, and finally to me. He was not writing to accuse me. He wrote because Richter’s press had recently completed an edition of selected Eckhart sermons — set from a Strasbourg manuscript descending from mine — and had printed the twelfth sermon with the variant reading: <em>Wirt.</em>',
                'He enclosed a single printed leaf. Three hundred copies had already been distributed in four cities. I held the leaf for a long time. The type was clean, the impression even. My word sat in the middle of Eckhart’s sentence, indistinguishable from the rest. I wrote back to Father Ulrich and told him the truth: that the selection was mine, not Eckhart’s, and that I had not annotated it in the margin.',
                'It is evening now. My eyes are worse. I have been intending to burn this manuscript since September. I want to be honest about why I have not: I could not, because it is good. Not holy, but good in the way a thing is good when the man who made it was fully present in the making. I made this for You — and I also made it for whoever finds it.',
                'I am not going to burn it. I am going to put it here, between the Breviarium on my left and the old Lectionary on my right, where they will remain when I leave this room.',
                'I went to the workshop again this week. They were running the Eckhart. One of the pages slipped from the stack onto the floor between Hans and the press. I picked it up. I read the passage: <em>Wirt.</em> My word in Eckhart’s sentence, Eckhart’s sentence in the press’s type, the chain of transmission running back twenty-two years to a winter morning in 1435. I handed it back to Hans. I walked home through the cold. I came here. I picked up the pen.',
                '<em>Quemadmodum desiderat cervus ad fontes aquarum.</em> As the deer longs for the water-brooks. So.',
                '✦ ✦ ✦',
                '<em>Finis. Scriptum Erfordiae, anno aetatis meae quadragesimo tertio, anno Domini MCCCCLVII, sine licentia, sine excusatione, et sine, in fine, combustione.</em> — Written in Erfurt, in the forty-third year of my life, in the year of Our Lord 1457, without permission, without excuse, and without, in the end, burning.',
            ],
            "apparatus": [
                {
                    "type": "vellum",
                    "folio": "f14r",
                    "label": "Folio 14r, lines 1–17",
                    "thumb": "/assets/folios/f14r_thumb.jpg",
                },
                {
                    "type": "note",
                    "heading": "Irregular Offcut Stock · f. 14r–17v",
                    "body": "From folio 14r onward the support shifts to a darker, rougher remnant hide with uneven hand-knife trim (17 lines per page; 12 lines on 17v).",
                },
                {
                    "type": "vellum",
                    "folio": "f17v",
                    "label": "Folio 17v · Colophon (lines 1–12)",
                    "thumb": "/assets/folios/f17v_thumb.jpg",
                },
            ],
            "has_contested_reading": False,
        },
    ]


def build_site_assets_and_data(dist_dir: Path = Path("site/dist")) -> dict:
    """Build all static assets and `site_data.json` for the MS Erfurt web showcase."""
    dist_dir = Path(dist_dir)
    data_dir = dist_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    _extract_design_bundle_assets(dist_dir)

    cat = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    _export_web_folio_images(dist_dir, cat)

    dmg_by_folio: dict[str, list[dict]] = {}
    for d in cat.get("damage_annotations", []):
        dmg_by_folio.setdefault(d["folio_id"], []).append(d)

    emo_by_folio: dict[str, list[dict]] = {}
    for e in cat.get("emotional_lines", []):
        emo_by_folio.setdefault(e["folio_id"], []).append(e)

    dips_by_folio: dict[str, list[dict]] = {}
    for dp in cat.get("dip_events", []):
        dips_by_folio.setdefault(dp["folio_id"], []).append(dp)

    folios_out: list[dict] = []
    lac_counter = 0

    for f in cat["folios"]:
        fid = f["folio_id"]
        w_px, h_px = f["size_px"]
        n_lines = f["lines"]
        sec_num = FOLIO_SECTION_MAP.get(fid, 1)
        roman, sec_short, sec_full, _ = SECTION_META[sec_num]
        v_side = "h" if f["vellum_side"] == "hair" else "f"
        v_stock = f["vellum_stock"]

        if fid == "f04v":
            cond = "corner"
            cond_label = "Water; lower-right corner lost"
        elif fid in ("f03v", "f04r", "f05r", "f05v"):
            cond = "water"
            cond_label = "Water from above"
        else:
            cond = ""
            cond_label = "Sound"

        # Line top % helper
        def _line_top_pct(ln: int, total_ln: int = n_lines) -> float:
            span_pct = 80.0 if total_ln >= 20 else (66.0 if total_ln >= 16 else 48.0)
            step = span_pct / max(1, total_ln - 1)
            return round(8.4 + (ln - 1) * step, 2)

        conf_lines = []
        trans_lines = []
        for l_obj in f.get("lines_data", []):
            ln = int(l_obj.get("number", 1))
            anns = l_obj.get("annotations", []) or []
            c_score = 0.96
            for a in anns:
                if a.get("type") == "confidence":
                    c_score = float((a.get("detail") or {}).get("score", 0.96))
            col = "#E0644B" if c_score < 0.6 else ("#D9A441" if c_score < 0.8 else "#8E8577")
            top_p = _line_top_pct(ln, n_lines)
            conf_lines.append({
                "n": ln,
                "top": round(top_p + 0.4, 2),
                "w": round(c_score * 7.0, 2),
                "col": col,
                "pct": f"{round(c_score * 100)}%",
                "band": "rgba(224,100,75,0.13)" if c_score < 0.6 else "transparent",
            })
            style_str = (
                "font-style: italic; font-weight: 700;"
                if c_score < 0.6
                else ("font-style: italic;" if c_score < 0.8 else "")
            )
            if any(a.get("type") == "strikethrough" for a in anns):
                style_str += " text-decoration: line-through wavy #E0644B;"
            trans_lines.append({
                "n": ln,
                "text": l_obj.get("text", ""),
                "english": l_obj.get("english", ""),
                "register": l_obj.get("register", "de"),
                "pct": f"{round(c_score * 100)}%",
                "col": col,
                "style": style_str,
            })

        dmg_boxes = []
        lac_labels = []
        for d in dmg_by_folio.get(fid, []):
            bx0, by0, bx1, by1 = d["bbox_px"]
            xp = round((bx0 / max(1, w_px)) * 100.0, 2)
            yp = round((by0 / max(1, h_px)) * 100.0, 2)
            bwp = round(max(1.8, ((bx1 - bx0) / max(1, w_px)) * 100.0), 2)
            bhp = round(max(1.6, ((by1 - by0) / max(1, h_px)) * 100.0), 2)
            dtype = d["damage_type"]
            is_lac = dtype == "lacuna"
            if is_lac:
                lac_counter += 1
                lbl = f"L{lac_counter}"
                lac_labels.append({"t": lbl, "x": round(xp + bwp + 0.4, 2), "y": round(max(1.0, yp - 2.2), 2)})
                border = "2px solid #E0644B"
                title = f"{lbl} · {d.get('note') or 'Lacuna'}"
            elif dtype == "strikethrough":
                border = "1.5px solid #C9A45C"
                title = f"Scribal strikethrough · {d.get('note') or d['word']}"
            else:
                border = "1.5px dashed rgba(224,100,75,0.85)"
                title = f"{dtype.replace('_', ' ').title()} · {d['word']} ({d.get('note') or ''})"
            dmg_boxes.append({
                "n": title,
                "x": xp,
                "y": yp,
                "bw": bwp,
                "bh": bhp,
                "border": border,
                "is_lacuna": is_lac,
            })

        hand_lines = []
        for e in emo_by_folio.get(fid, []):
            ln = int(e["line_number"])
            sname = e["state_name"]
            hand_lines.append({
                "n": ln,
                "top": _line_top_pct(ln, n_lines),
                "t": STATE_SHORT_LABELS.get(sname, sname),
                "state": sname,
                "rationale": e["rationale"],
            })

        dip_markers = []
        for dp in dips_by_folio.get(fid, []):
            ln = int(dp.get("line_index", 0)) + 1
            dip_markers.append({
                "n": ln,
                "top": round(_line_top_pct(min(n_lines, max(1, ln)), n_lines) + 1.0, 2),
                "w": dp.get("word") or dp.get("reason", "dip"),
            })

        folios_out.append({
            "id": fid,
            "label": fid.replace("f0", "").replace("f", ""),
            "sec": sec_num,
            "roman": roman,
            "section_short": sec_short,
            "section_name": sec_full,
            "side": v_side,
            "side_label": "Hair side" if v_side == "h" else "Flesh side",
            "stock": v_stock,
            "stock_label": "Irregular offcut · smaller, cut unevenly" if sec_num == 7 else "Calfskin · 148 × 204 mm",
            "lines": n_lines,
            "dmg": len(dmg_boxes),
            "hand": len(hand_lines),
            "dips": len(dip_markers),
            "cond": cond,
            "condition_label": cond_label,
            "hand_note": HAND_NOTES_BY_FOLIO.get(
                fid,
                "CLIO-7: letterforms remain precise but more widely spaced, consistent with a writer compensating for some physical difficulty. The ink is fresh.",
            ),
            "img": f"/assets/folios/{fid}.jpg",
            "clean_img": f"/assets/folios/{fid}_clean.jpg",
            "thumb": f"/assets/folios/{fid}_thumb.jpg",
            "conf_lines": conf_lines,
            "dmg_boxes": dmg_boxes,
            "lac_labels": lac_labels,
            "hand_lines": hand_lines,
            "dip_markers": dip_markers,
            "transcription": trans_lines,
        })

    spreads_out = []
    for sp in cat.get("spreads", []):
        l_id = sp["left_folio"]
        r_id = sp["right_folio"]
        spreads_out.append({
            "key": f"{l_id}|{r_id}",
            "opening_number": sp["opening_number"],
            "left_folio": l_id,
            "right_folio": r_id,
            "vellum_side": sp["vellum_side"],
            "img": "/assets/folios/" + sp["image"].replace(".png", ".jpg"),
        })

    site_data = {
        "manuscript": {
            "shelfmark": "MS Erfurt Aug. 12°47",
            "author": "S. R. Swart",
            "scribe": "Brother Konrad",
            "date": 1457,
            "discovery": 2019,
            "folios_count": 34,
            "leaves_count": 17,
            "damage_spans_count": len(cat.get("damage_annotations", [])),
            "emotional_lines_count": len(cat.get("emotional_lines", [])),
            "quill_dips_count": len(cat.get("dip_events", [])),
        },
        "folios": folios_out,
        "spreads": spreads_out,
        "sections": _build_edition_sections(),
    }

    (data_dir / "site_data.json").write_text(
        json.dumps(site_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return site_data


if __name__ == "__main__":
    res = build_site_assets_and_data()
    print(f"Built site_data.json with {len(res['folios'])} folios, {len(res['spreads'])} spreads, and {len(res['sections'])} edition sections.")
