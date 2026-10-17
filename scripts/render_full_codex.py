"""Parallel Full-Codex Kinematic + Hybrid Texture & 560-Year Weathering Pipeline
for MS Erfurt Aug. 12°47 (34 Folios: f01r–f17v + 16 Bound Bifolium Spreads).
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from PIL import Image, ImageDraw

from scribesim.handvalidate.tier2_bench import render_kinematic_folio
from weather.profile import load_profile
from weather.substrate.vellum import stock_for_folio, side_for_folio
from weather.compositor import composite_folio
from weather.groundtruth import apply_groundtruth

FOLIOS = [f"f{i:02d}{rv}" for i in range(1, 18) for rv in ("r", "v")]
INPUT_DIR = Path("output-live")
RENDER_DIR = Path("render-output")
WEATHER_DIR = Path("weather-output")
GALLERY_DIR = Path("shared/training/handsim/first_5_folios")


def render_one_clean(args: tuple[int, str]) -> tuple[str, dict, dict]:
    idx, fid = args
    folio_dict = json.loads((INPUT_DIR / f"{fid}.json").read_text(encoding="utf-8"))
    res = render_kinematic_folio(
        folio_dict,
        output_dir=RENDER_DIR,
        folio_id=fid,
        dpi=220.0,
        supersample=3,
        max_lines=None,
        seed=1457 + idx,
        hybrid_texture=True,
        hybrid_strength=0.22,
    )
    res.pop("page_array", None)
    res.pop("angles_deg", None)
    return fid, folio_dict, res


def weather_one_folio(args: tuple[int, str, dict, dict]) -> tuple[str, dict, list, list, list]:
    idx, fid, folio_dict, res = args
    profile = load_profile(Path("shared/profiles/ms-erfurt-560yr.toml"))
    n_lines = len(folio_dict.get("lines", []))
    page_img = Image.open(RENDER_DIR / f"{fid}.png").convert("RGB")
    heat_img = Image.open(RENDER_DIR / f"{fid}_pressure.png").convert("L")
    xml_path = RENDER_DIR / f"{fid}.xml"

    leaf_prefix = fid[:3]
    reverse_fid = f"{leaf_prefix}v" if fid.endswith("r") else f"{leaf_prefix}r"
    verso_path = RENDER_DIR / f"{reverse_fid}.png"
    verso_img = Image.open(verso_path).convert("RGB") if verso_path.exists() else None

    stock = stock_for_folio(fid)
    v_side = side_for_folio(fid)
    leaf_num = int(fid[1:3])
    comp = composite_folio(
        page_img,
        heat_img,
        fid,
        profile,
        stock=stock,
        seed=profile.seed + leaf_num * 13,
        verso_page_img=verso_img,
    )

    weathered_path = WEATHER_DIR / f"{fid}_weathered.png"
    comp.image.save(str(weathered_path), format="PNG", dpi=(220, 220))

    weathered_xml_path = WEATHER_DIR / f"{fid}_weathered.xml"
    apply_groundtruth(xml_path, weathered_xml_path, comp)

    clean_gal = GALLERY_DIR / f"{fid}_clean.png"
    weathered_gal = GALLERY_DIR / f"{fid}_weathered.png"
    page_img.save(str(clean_gal))
    comp.image.save(str(weathered_gal))

    w, h = page_img.size
    sbs = Image.new("RGB", (w * 2 + 24, h + 52), (24, 22, 20))
    d = ImageDraw.Draw(sbs)
    d.text((16, 16), f"{fid} — Clean Kinematic + Quill Dip Cycle & Emotional Affect ({n_lines} lines)", fill=(235, 225, 205))
    d.text((w + 36, 16), f"{fid} — 560-Yr {stock.value.title()} Calfskin ({v_side.value} side) & Brown Iron-Gall", fill=(235, 225, 205))
    sbs.paste(page_img, (8, 44))
    sbs.paste(comp.image, (w + 16, 44))
    sbs_path = GALLERY_DIR / f"{fid}_side_by_side.png"
    sbs.save(str(sbs_path))

    dmg_anns = res["damage_annotations"]
    hiou = res["hybrid_texture"]["centerline_iou"] if res["hybrid_texture"] else 1.0
    summary = {
        "folio_id": fid,
        "section": str(folio_dict.get("section", "")),
        "lines": n_lines,
        "size_px": [w, h],
        "vellum_stock": stock.value,
        "vellum_side": v_side.value,
        "hand_notes": folio_dict.get("hand_notes"),
        "damage_meta": folio_dict.get("damage"),
        "quill_dips_count": len(res["dip_events"]),
        "emotional_lines_count": len(res["emotional_lines"]),
        "damage_spans_count": len(dmg_anns),
        "hybrid_iou": hiou,
        "clean_path": str(clean_gal),
        "weathered_path": str(weathered_gal),
        "side_by_side_path": str(sbs_path),
        "lines_data": folio_dict.get("lines", []),
    }
    return fid, summary, dmg_anns, res["emotional_lines"], res["dip_events"]


def main() -> None:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    WEATHER_DIR.mkdir(parents=True, exist_ok=True)
    GALLERY_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Starting Pass 1: Parallel clean kinematic rendering for {len(FOLIOS)} folios...")
    clean_map: dict[str, tuple[dict, dict]] = {}
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(render_one_clean, (i, fid)) for i, fid in enumerate(FOLIOS)]
        for f in as_completed(futs):
            fid, fdict, res = f.result()
            clean_map[fid] = (fdict, res)
            lc = len(fdict.get("lines", []))
            dc = len(res["dip_events"])
            print(f"  [Clean] {fid} done ({lc} lines, {dc} dips)")

    print(f"Starting Pass 2: Parallel 560-year codex weathering for {len(FOLIOS)} folios...")
    summaries_by_id: dict[str, dict] = {}
    all_damage: list[dict] = []
    all_emotional: list[dict] = []
    all_dips: list[dict] = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = [
            ex.submit(weather_one_folio, (i, fid, clean_map[fid][0], clean_map[fid][1]))
            for i, fid in enumerate(FOLIOS)
        ]
        for f in as_completed(futs):
            fid, summary, dmg, emo, dips = f.result()
            summaries_by_id[fid] = summary
            all_damage.extend(dmg)
            all_emotional.extend(emo)
            all_dips.extend(dips)
            vst = summary["vellum_stock"]
            vsi = summary["vellum_side"]
            print(f"  [Weathered] {fid} done ({vst}/{vsi})")

    ordered_summaries = [summaries_by_id[fid] for fid in FOLIOS]

    print("Starting Pass 3: Generating 16 bound bifolium spreads (f01v|f02r .. f16v|f17r)...")
    spread_records = []
    for leaf in range(1, 17):
        left_id = f"f{leaf:02d}v"
        right_id = f"f{leaf+1:02d}r"
        l_img = Image.open(GALLERY_DIR / f"{left_id}_weathered.png").convert("RGB")
        r_img = Image.open(GALLERY_DIR / f"{right_id}_weathered.png").convert("RGB")
        l_side = side_for_folio(left_id).value
        r_side = side_for_folio(right_id).value
        l_stock = stock_for_folio(left_id).value
        r_stock = stock_for_folio(right_id).value
        h_max = max(l_img.height, r_img.height)
        w_sum = l_img.width + r_img.width + 6
        spread = Image.new("RGB", (w_sum, h_max + 48), (18, 16, 14))
        sd = ImageDraw.Draw(spread)
        sd.text(
            (20, 14),
            f"Bound Codex Opening #{leaf}: {left_id} ({l_stock} {l_side})  |  spine gutter  |  {right_id} ({r_stock} {r_side} — Gregory Rule match)",
            fill=(238, 226, 200),
        )
        spread.paste(l_img, (0, 44))
        spread.paste(r_img, (l_img.width + 6, 44))
        sd.rectangle([l_img.width, 44, l_img.width + 5, 44 + h_max], fill=(28, 22, 16))
        sp_name = f"spread_{left_id}_{right_id}.png"
        spread.save(str(GALLERY_DIR / sp_name))
        spread_records.append(
            {
                "opening_number": leaf,
                "left_folio": left_id,
                "right_folio": right_id,
                "vellum_side": l_side,
                "left_stock": l_stock,
                "right_stock": r_stock,
                "image": sp_name,
            }
        )

    catalog_out = {
        "folios": ordered_summaries,
        "spreads": spread_records,
        "damage_annotations": sorted(all_damage, key=lambda x: (x["folio_id"], x["line_number"])),
        "emotional_lines": sorted(all_emotional, key=lambda x: (x["folio_id"], x["line_number"])),
        "dip_events": all_dips,
    }
    (GALLERY_DIR / "damage_and_lacuna_catalog.json").write_text(
        json.dumps(catalog_out, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"COMPLETE: {len(ordered_summaries)} folios, {len(spread_records)} spreads, "
        f"{len(all_damage)} damage/strikethrough spans, {len(all_emotional)} emotional lines, "
        f"{len(all_dips)} quill dips!"
    )


if __name__ == "__main__":
    main()
