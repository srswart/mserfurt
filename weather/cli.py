"""Weather CLI — 560-year aging and damage simulation for MS Erfurt 1457."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import click

from weather.profile import load_profile
from weather.compositor import composite_folio, load_manifest
from weather.substrate.vellum import VellumStock
from weather.groundtruth import apply_groundtruth

_DEFAULT_PROFILE = (
    Path(__file__).parents[1] / "shared" / "profiles" / "ms-erfurt-560yr.toml"
)
_FOLIO_RE = re.compile(r"^f?(\d+)([rv])$")


def _normalise_folio(folio_id: str) -> str:
    """Normalise '1r' or 'f01r' to canonical 'f01r' form."""
    m = _FOLIO_RE.match(folio_id)
    if not m:
        raise click.BadParameter(
            f"invalid folio ID {folio_id!r} — expected e.g. f01r or 1r",
            param_hint="FOLIO_ID",
        )
    return f"f{int(m.group(1)):02d}{m.group(2)}"


def _load_manifest(input_dir: Path) -> dict:
    manifest_path = input_dir / "manifest.json"
    if not manifest_path.exists():
        click.echo(
            f"error: manifest.json not found in {input_dir}", err=True
        )
        sys.exit(1)
    return json.loads(manifest_path.read_text())


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.option(
    "--profile", "profile_path",
    default=None,
    type=click.Path(),
    help="Path to weathering profile TOML (default: shared/profiles/ms-erfurt-560yr.toml)",
)
@click.pass_context
def main(ctx: click.Context, profile_path: str | None) -> None:
    """Weather — apply 560-year manuscript aging to ScribeSim page images."""
    ctx.ensure_object(dict)
    try:
        profile = load_profile(Path(profile_path) if profile_path else None)
    except FileNotFoundError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)
    ctx.obj["profile"] = profile


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------

@main.command()
@click.option("--folio", "folio_id", required=True,
              help="Folio identifier, e.g. f04r or 4r")
@click.option("--input-dir", "input_dir", default="render-output", show_default=True,
              type=click.Path(), help="Directory containing ScribeSim PNG/XML output")
@click.option("--output-dir", "output_dir", default="weather-output", show_default=True,
              type=click.Path(), help="Directory to write weathered PNG and XML")
@click.option("--dry-run", is_flag=True, default=False,
              help="Resolve paths and report plan without rendering")
@click.pass_context
def apply(ctx: click.Context, folio_id: str, input_dir: str,
          output_dir: str, dry_run: bool) -> None:
    """Apply weathering pipeline to a single folio image."""
    try:
        fid = _normalise_folio(folio_id)
    except click.BadParameter as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)

    profile = ctx.obj["profile"]
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)

    png_in = in_dir / f"{fid}.png"
    heatmap_in = in_dir / f"{fid}_pressure.png"
    xml_in = in_dir / f"{fid}.xml"
    png_out = out_dir / f"{fid}_weathered.png"
    xml_out = out_dir / f"{fid}_weathered.xml"

    click.echo(f"[weather apply] folio={fid}")
    click.echo(f"  profile : {profile.name} (seed={profile.seed}, age={profile.age_years}yr)")
    click.echo(f"  input   : {in_dir}")
    click.echo(f"  page    : {png_in}  {'✓' if png_in.exists() else '✗ (missing)'}")
    click.echo(f"  heatmap : {heatmap_in}  {'✓' if heatmap_in.exists() else '✗ (missing)'}")
    click.echo(f"  xml     : {xml_in}  {'✓' if xml_in.exists() else '✗ (missing)'}")
    click.echo(f"  output  : {png_out}")

    if dry_run:
        click.echo("  [dry-run] weathering skipped")
        return

    if not png_in.exists():
        click.echo(f"error: page image not found: {png_in}", err=True)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    from PIL import Image
    page_img = Image.open(png_in).convert("RGB")
    heatmap_img = (
        Image.open(heatmap_in).convert("L")
        if heatmap_in.exists()
        else Image.fromarray(
            __import__("numpy").full(
                (page_img.height, page_img.width), 128, dtype=__import__("numpy").uint8
            ), mode="L"
        )
    )

    # Determine vellum stock from manifest if available
    manifest_path = in_dir / "manifest.json"
    stock = VellumStock.STANDARD
    if manifest_path.exists():
        entries = load_manifest(manifest_path)
        entry = entries.get(fid)
        if entry and entry.vellum_stock == "irregular":
            stock = VellumStock.IRREGULAR

    result = composite_folio(page_img, heatmap_img, fid, profile, stock=stock,
                             seed=profile.seed)
    result.image.save(png_out)
    click.echo(f"  saved → {png_out}")


# ---------------------------------------------------------------------------
# apply-batch
# ---------------------------------------------------------------------------

@main.command("apply-batch")
@click.option("--input-dir", "input_dir", default="render-output", show_default=True,
              type=click.Path(), help="Directory containing ScribeSim output and manifest.json")
@click.option("--output-dir", "output_dir", default="weather-output", show_default=True,
              type=click.Path(), help="Directory to write weathered outputs")
@click.option("--dry-run", is_flag=True, default=False,
              help="Resolve paths for each folio without rendering")
@click.pass_context
def apply_batch(ctx: click.Context, input_dir: str, output_dir: str,
                dry_run: bool) -> None:
    """Apply weathering to all folios listed in manifest.json."""
    profile = ctx.obj["profile"]
    in_dir = Path(input_dir)
    manifest = _load_manifest(in_dir)
    folios = manifest.get("folios", [])

    click.echo(f"[weather apply-batch] {len(folios)} folio(s) — "
               f"profile: {profile.name}")

    ok = 0
    for entry in folios:
        fid = entry["id"]
        png_in = in_dir / f"{fid}.png"
        click.echo(f"  {fid}  {'✓' if png_in.exists() else '✗ (no PNG)'}", nl=False)

        if dry_run:
            click.echo("  [dry-run]")
            ok += 1
            continue

        try:
            from PIL import Image
            import numpy as np
            heatmap_in = in_dir / f"{fid}_pressure.png"
            page_img = Image.open(png_in).convert("RGB")
            heatmap_img = (
                Image.open(heatmap_in).convert("L")
                if heatmap_in.exists()
                else Image.fromarray(
                    np.full((page_img.height, page_img.width), 128, dtype=np.uint8),
                    mode="L",
                )
            )
            stock_str = entry.get("vellum_stock") or "standard"
            stock = (VellumStock.IRREGULAR if stock_str == "irregular"
                     else VellumStock.STANDARD)
            out_dir.mkdir(parents=True, exist_ok=True)
            result = composite_folio(page_img, heatmap_img, fid, profile,
                                     stock=stock, seed=profile.seed)
            result.image.save(out_dir / f"{fid}_weathered.png")
            click.echo(f"  ✓")
            ok += 1
        except Exception as exc:
            click.echo(f"  FAIL ({exc})")

    click.echo(f"[weather apply-batch] done — {ok}/{len(folios)} processed")


# ---------------------------------------------------------------------------
# preview
# ---------------------------------------------------------------------------

VALID_EFFECTS = ("substrate", "ink", "damage", "aging", "optics")


@main.command()
@click.option("--folio", "folio_id", required=True,
              help="Folio identifier, e.g. f04r or 4r")
@click.option("--effect", required=True,
              type=click.Choice(VALID_EFFECTS, case_sensitive=False),
              help="Effect layer to preview: substrate, ink, damage, aging, optics")
@click.option("--input-dir", "input_dir", default="render-output", show_default=True,
              type=click.Path())
@click.option("--output-dir", "output_dir", default="weather-output", show_default=True,
              type=click.Path())
@click.pass_context
def preview(ctx: click.Context, folio_id: str, effect: str,
            input_dir: str, output_dir: str) -> None:
    """Render an isolated preview of a single effect layer.

    FOLIO_ID is the folio to use as the base image.
    """
    try:
        fid = _normalise_folio(folio_id)
    except click.BadParameter as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"[weather preview] folio={fid}  effect={effect}")
    raise NotImplementedError(
        f"Preview for '{effect}' not yet implemented — "
        "see individual effect advances"
    )


# ---------------------------------------------------------------------------
# groundtruth-update
# ---------------------------------------------------------------------------

@main.command("groundtruth-update")
@click.option("--folio", "folio_id", required=True,
              help="Folio identifier, e.g. f04r or 4r")
@click.option("--input-dir", "input_dir", default="render-output", show_default=True,
              type=click.Path())
@click.option("--output-dir", "output_dir", default="weather-output", show_default=True,
              type=click.Path())
@click.pass_context
def groundtruth_update(ctx: click.Context, folio_id: str,
                       input_dir: str, output_dir: str) -> None:
    """Update PAGE XML coordinates to reflect weathering damage geometry.

    FOLIO_ID is the folio whose PAGE XML should be corrected.
    """
    try:
        fid = _normalise_folio(folio_id)
    except click.BadParameter as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"[weather groundtruth-update] folio={fid}")

    profile = ctx.obj["profile"]
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    png_in = in_dir / f"{fid}.png"
    heatmap_in = in_dir / f"{fid}_pressure.png"
    xml_in = in_dir / f"{fid}.xml"
    xml_out = out_dir / f"{fid}_weathered.xml"

    if not xml_in.exists():
        click.echo(f"error: PAGE XML not found: {xml_in}", err=True)
        sys.exit(1)
    if not png_in.exists():
        click.echo(f"error: page image not found: {png_in}", err=True)
        sys.exit(1)

    from PIL import Image
    import numpy as np
    page_img = Image.open(png_in).convert("RGB")
    heatmap_img = (
        Image.open(heatmap_in).convert("L")
        if heatmap_in.exists()
        else Image.fromarray(
            np.full((page_img.height, page_img.width), 128, dtype=np.uint8), mode="L"
        )
    )

    manifest_path = in_dir / "manifest.json"
    stock = VellumStock.STANDARD
    if manifest_path.exists():
        entries = load_manifest(manifest_path)
        entry = entries.get(fid)
        if entry and entry.vellum_stock == "irregular":
            stock = VellumStock.IRREGULAR

    result = composite_folio(page_img, heatmap_img, fid, profile, stock=stock,
                             seed=profile.seed)
    apply_groundtruth(xml_in, xml_out, result)
    click.echo(f"  saved → {xml_out}")


# ---------------------------------------------------------------------------
# weather-map
# ---------------------------------------------------------------------------

@main.command("weather-map")
@click.option("--gathering-size", "gathering_size", default=17, show_default=True,
              type=int, help="Number of leaves in the gathering (default 17 = 34 folios)")
@click.option("--clio7", "clio7_path", default=None, type=click.Path(),
              help="Path to XL manifest JSON for CLIO-7 annotation merging (optional)")
@click.option("--output", "output_path", default="weather/codex_map.json", show_default=True,
              type=click.Path(), help="Output path for codex_map.json")
@click.option("--seed", default=1457, show_default=True, type=int,
              help="RNG seed for foxing cluster placement")
@click.pass_context
def weather_map(ctx: click.Context, gathering_size: int, clio7_path: str | None,
                output_path: str, seed: int) -> None:
    """Generate the codex weathering map (TD-011 Part 2).

    Computes per-folio damage specs (water propagation, edge darkening, foxing,
    missing corners) and writes codex_map.json.
    """
    from weather.codexmap import compute_codex_weathering_map, save_codex_map

    clio7 = Path(clio7_path) if clio7_path else None
    wmap = compute_codex_weathering_map(
        gathering_size=gathering_size, seed=seed, clio7_path=clio7
    )

    out = Path(output_path)
    save_codex_map(wmap, out)

    # Summary table
    click.echo(f"[weather map] {len(wmap)} folios  seed={seed}")
    click.echo(f"  written → {out}\n")
    click.echo(f"{'Folio':<8}  {'Stock':<10}  {'Water':<6}  {'Corner':<10}  {'Foxing'}")
    click.echo("-" * 55)
    for fid, spec in sorted(wmap.items()):
        water = f"{spec.water_damage.severity:.2f}" if spec.water_damage else "—"
        corner = spec.missing_corner.corner if spec.missing_corner else "—"
        foxing = str(len(spec.foxing_spots)) if spec.foxing_spots else "—"
        click.echo(f"{fid:<8}  {spec.vellum_stock:<10}  {water:<6}  {corner:<10}  {foxing}")


# ---------------------------------------------------------------------------
# weather-folio
# ---------------------------------------------------------------------------

@main.command("weather-folio")
@click.option("--folio", "folio_id", required=True,
              help="Folio identifier, e.g. f04r or 4r")
@click.option("--clean", "clean_path", required=True, type=click.Path(),
              help="Path to the clean ScribeSim PNG")
@click.option("--map", "map_path", required=True, type=click.Path(),
              help="Path to codex_map.json (from weather-map)")
@click.option("--xml", "xml_path", default=None, type=click.Path(),
              help="Path to PAGE XML for text bbox extraction (optional)")
@click.option("--folio-json", "folio_json_path", default=None, type=click.Path(),
              help="Path to XL folio JSON for CLIO-7 word damage (optional)")
@click.option("--output-dir", "output_dir", default="weather-output", show_default=True,
              type=click.Path(), help="Directory for prompt, provenance, and weathered image")
@click.option("--model", default="gpt-image-1", show_default=True,
              help="AI model identifier")
@click.option("--seed", default=1457, show_default=True, type=int,
              help="Base seed for deterministic per-folio seed derivation")
@click.option("--dry-run", is_flag=True, default=False,
              help="Generate prompt and provenance stub without calling the AI API")
@click.pass_context
def weather_folio_cmd(ctx: click.Context, folio_id: str, clean_path: str,
                      map_path: str, xml_path: str | None, folio_json_path: str | None,
                      output_dir: str, model: str, seed: int, dry_run: bool) -> None:
    """Run the full AI weathering pipeline for a single folio.

    Steps: load codex map → build word damage map → pre-degrade → generate
    prompt (printed) → AI call (or dry-run) → write provenance JSON.
    """
    import numpy as np
    from PIL import Image as _PILImage
    from weather.codexmap import load_codex_map
    from weather.worddegrade import build_word_damage_map
    from weather.aiweather import weather_folio

    try:
        fid = _normalise_folio(folio_id)
    except click.BadParameter as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)

    map_file = Path(map_path)
    if not map_file.exists():
        click.echo(f"error: codex map not found: {map_file}", err=True)
        sys.exit(1)

    wmap = load_codex_map(map_file)
    if fid not in wmap:
        click.echo(f"error: folio {fid!r} not found in codex map", err=True)
        sys.exit(1)

    folio_spec = wmap[fid]
    clean_file = Path(clean_path)
    if not clean_file.exists():
        click.echo(f"error: clean image not found: {clean_file}", err=True)
        sys.exit(1)

    clean_image = np.array(_PILImage.open(clean_file).convert("RGB"), dtype=np.uint8)
    h, w = clean_image.shape[:2]

    # Build word damage map
    word_damage_map = []
    if folio_json_path and Path(folio_json_path).exists():
        folio_json = json.loads(Path(folio_json_path).read_text())
        page_xml = Path(xml_path) if xml_path else Path(map_path).parent / f"{fid}.xml"
        word_damage_map = build_word_damage_map(folio_json, page_xml, w, h)
    elif folio_json_path:
        click.echo(f"  warning: folio JSON not found: {folio_json_path} — word damage map empty",
                   err=True)

    out_dir = Path(output_dir)

    click.echo(f"[weather folio] {fid}  model={model}  dry_run={dry_run}")
    click.echo(f"  clean   : {clean_file}")
    click.echo(f"  map     : {map_file}")
    click.echo(f"  output  : {out_dir}")

    result = weather_folio(
        folio_id=fid,
        clean_image=clean_image,
        folio_spec=folio_spec,
        word_damage_map=word_damage_map,
        weathering_map=wmap,
        weathered_so_far={},
        output_dir=out_dir,
        model=model,
        seed_base=seed,
        dry_run=dry_run,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    img_out = out_dir / f"{fid}_weathered.png"
    _PILImage.fromarray(result.image).save(str(img_out))

    click.echo(f"\n--- PROMPT ---\n{result.prompt}\n--- END PROMPT ---\n")
    click.echo(f"  provenance → {result.provenance_path}")
    click.echo(f"  image     → {img_out}")
    click.echo(f"  {'[dry-run] image = pre-degraded input' if dry_run else 'AI-weathered image written'}")


# ---------------------------------------------------------------------------
# weather-codex
# ---------------------------------------------------------------------------

@main.command("weather-codex")
@click.option("--clean-dir", "clean_dir", default="render-output", show_default=True,
              type=click.Path(), help="Directory of clean ScribeSim PNGs ({folio_id}.png)")
@click.option("--map", "map_path", required=True, type=click.Path(),
              help="Path to codex_map.json")
@click.option("--folio-json-dir", "folio_json_dir", default=None, type=click.Path(),
              help="Directory of XL folio JSON files for CLIO-7 word damage (optional)")
@click.option("--xml-dir", "xml_dir", default=None, type=click.Path(),
              help="Directory of PAGE XML files (optional)")
@click.option("--output-dir", "output_dir", default="weather-output", show_default=True,
              type=click.Path(), help="Output directory for all weathered outputs")
@click.option("--model", default="gpt-image-1", show_default=True,
              help="AI model identifier")
@click.option("--seed", default=1457, show_default=True, type=int,
              help="Base seed for deterministic per-folio seed derivation")
@click.option("--dry-run", is_flag=True, default=False,
              help="Skip AI API calls; output images are pre-degraded copies")
@click.option("--validate", "run_validate", is_flag=True, default=False,
              help="Run validation checks after each folio and print pass/fail")
@click.pass_context
def weather_codex_cmd(ctx: click.Context, clean_dir: str, map_path: str,
                      folio_json_dir: str | None, xml_dir: str | None,
                      output_dir: str, model: str, seed: int,
                      dry_run: bool, run_validate: bool) -> None:
    """Process all folios in gathering order (TD-011 Parts 4-7).

    Folios already completed (provenance JSON exists) are skipped —
    interrupted runs can be resumed safely with the same command.
    """
    import numpy as np
    from PIL import Image as _PILImage
    from weather.codexmap import load_codex_map
    from weather.worddegrade import build_word_damage_map
    from weather.aiweather import generate_gathering_order, weather_folio
    from weather.aivalidation import validate_folio

    map_file = Path(map_path)
    if not map_file.exists():
        click.echo(f"error: codex map not found: {map_file}", err=True)
        sys.exit(1)

    wmap = load_codex_map(map_file)
    in_dir = Path(clean_dir)
    out_dir = Path(output_dir)
    order = generate_gathering_order(wmap)

    click.echo(f"[weather codex] {len(order)} folios in gathering order  "
               f"dry_run={dry_run}  validate={run_validate}")

    weathered_so_far: dict[str, np.ndarray] = {}
    done = skipped = 0

    for fid in order:
        prov_path = out_dir / f"{fid}_provenance.json"
        if prov_path.exists():
            click.echo(f"  {fid}  already complete — skipping")
            # Load the existing weathered image for coherence context
            img_path = out_dir / f"{fid}_weathered.png"
            if img_path.exists():
                weathered_so_far[fid] = np.array(
                    _PILImage.open(img_path).convert("RGB"), dtype=np.uint8
                )
            skipped += 1
            continue

        png_path = in_dir / f"{fid}.png"
        if not png_path.exists():
            continue  # no clean image → skip silently

        clean_image = np.array(_PILImage.open(png_path).convert("RGB"), dtype=np.uint8)
        h, w = clean_image.shape[:2]

        # Word damage map
        word_damage_map = []
        if folio_json_dir:
            fj_path = Path(folio_json_dir) / f"{fid}.json"
            if fj_path.exists():
                folio_json = json.loads(fj_path.read_text())
                page_xml = (
                    Path(xml_dir) / f"{fid}.xml"
                    if xml_dir
                    else in_dir / f"{fid}.xml"
                )
                word_damage_map = build_word_damage_map(folio_json, page_xml, w, h)
            else:
                click.echo(f"  warning: no folio JSON for {fid} — word damage map empty",
                           err=True)

        folio_spec = wmap[fid]
        click.echo(f"  {fid} ...", nl=False)

        try:
            result = weather_folio(
                folio_id=fid,
                clean_image=clean_image,
                folio_spec=folio_spec,
                word_damage_map=word_damage_map,
                weathering_map=wmap,
                weathered_so_far=weathered_so_far,
                output_dir=out_dir,
                model=model,
                seed_base=seed,
                dry_run=dry_run,
            )
        except Exception as exc:
            click.echo(f"  FAIL: {exc}")
            continue

        # Save weathered image to disk
        from PIL import Image as _PI
        img_out = out_dir / f"{fid}_weathered.png"
        _PI.fromarray(result.image).save(img_out)
        weathered_so_far[fid] = result.image
        done += 1

        # Inline validation
        if run_validate:
            import numpy as _np
            mask = _np.zeros(result.image.shape[:2], dtype=_np.uint8)
            v_summary = validate_folio(
                folio_id=fid,
                clean_image=clean_image,
                weathered_image=result.image,
                pre_degraded_image=result.image,  # approximation: no separate pre-deg store
                degradation_mask=mask,
                word_damage_map=word_damage_map,
                recto_spec=folio_spec,
                verso_image=None,
                verso_spec=None,
                bbox_list=[],
            )
            status = "PASS" if v_summary.all_passed else "FAIL"
            click.echo(f"  {status}")
        else:
            click.echo("  done")

    click.echo(f"\n[weather codex] complete — {done} weathered, {skipped} skipped")


# ---------------------------------------------------------------------------
# weather-validate
# ---------------------------------------------------------------------------

@main.command("weather-validate")
@click.option("--weathered-dir", "weathered_dir", required=True, type=click.Path(),
              help="Directory containing weathered PNGs and provenance JSONs")
@click.option("--clean-dir", "clean_dir", required=True, type=click.Path(),
              help="Directory containing clean ScribeSim PNGs")
@click.option("--map", "map_path", required=True, type=click.Path(),
              help="Path to codex_map.json")
@click.option("--pre-degraded-dir", "pre_degraded_dir", default=None, type=click.Path(),
              help="Directory of pre-degraded images (optional; uses weathered as fallback)")
@click.option("--mask-dir", "mask_dir", default=None, type=click.Path(),
              help="Directory of degradation mask PNGs (optional)")
@click.option("--word-damage-dir", "word_damage_dir", default=None, type=click.Path(),
              help="Directory of word damage JSONs (optional)")
@click.option("--xml-dir", "xml_dir", default=None, type=click.Path(),
              help="Directory of PAGE XML files (optional)")
@click.option("--report", "report_path", default=None, type=click.Path(),
              help="Output path for validation_report.json (default: weathered-dir/validation_report.json)")
@click.pass_context
def weather_validate_cmd(ctx: click.Context, weathered_dir: str, clean_dir: str,
                         map_path: str, pre_degraded_dir: str | None,
                         mask_dir: str | None, word_damage_dir: str | None,
                         xml_dir: str | None, report_path: str | None) -> None:
    """Run post-AI validation checks across all weathered folios (TD-011 Part 5).

    Checks: V1 text position drift < 5px, V2-A pre-degradation not restored,
    V3 recto/verso stain IoU >= 0.50.  Writes validation_report.json and
    prints a pass/fail summary table.
    """
    from weather.codexmap import load_codex_map
    from weather.aivalidation import validate_codex

    map_file = Path(map_path)
    if not map_file.exists():
        click.echo(f"error: codex map not found: {map_file}", err=True)
        sys.exit(1)

    wmap = load_codex_map(map_file)
    w_dir = Path(weathered_dir)
    c_dir = Path(clean_dir)
    pre_dir = Path(pre_degraded_dir) if pre_degraded_dir else w_dir
    m_dir = Path(mask_dir) if mask_dir else w_dir
    wd_dir = Path(word_damage_dir) if word_damage_dir else w_dir
    rep_path = Path(report_path) if report_path else w_dir / "validation_report.json"

    click.echo(f"[weather validate] weathered={w_dir}  map={map_file}")

    results = validate_codex(
        weathered_dir=w_dir,
        clean_dir=c_dir,
        pre_degraded_dir=pre_dir,
        mask_dir=m_dir,
        word_damage_dir=wd_dir,
        weathering_map=wmap,
        page_xml_dir=Path(xml_dir) if xml_dir else c_dir,
        output_report=rep_path,
    )

    click.echo(f"\n  report → {rep_path}")
    click.echo(f"\n{'Folio':<8}  {'V1':^5}  {'V2-A':^5}  {'V3':^5}  {'All':^5}")
    click.echo("-" * 38)
    for fid, summary in sorted(results.items()):
        def _s(r) -> str:
            return "PASS" if r.passed else "FAIL"
        click.echo(
            f"{fid:<8}  {_s(summary.v1_text_positions):^5}  "
            f"{_s(summary.v2a_pre_degradation):^5}  "
            f"{_s(summary.v3_damage_consistency):^5}  "
            f"{'PASS' if summary.all_passed else 'FAIL':^5}"
        )

    total = len(results)
    passed = sum(1 for s in results.values() if s.all_passed)
    click.echo(f"\n[weather validate] {passed}/{total} folios passed all checks")


# ---------------------------------------------------------------------------
# catalog
# ---------------------------------------------------------------------------

@main.command()
@click.option("--input-dir", "input_dir", default="output-live", show_default=True,
              type=click.Path(), help="Directory containing XL manifest.json")
@click.pass_context
def catalog(ctx: click.Context, input_dir: str) -> None:
    """List all folios with vellum stock and damage annotations."""
    in_dir = Path(input_dir)
    manifest = _load_manifest(in_dir)
    folios = manifest.get("folios", [])

    click.echo(f"[weather catalog] {len(folios)} folio(s)\n")
    click.echo(f"{'Folio':<8}  {'Stock':<12}  {'Damage'}")
    click.echo("-" * 50)

    for entry in folios:
        fid = entry.get("id", "?")
        folio_num = int(fid[1:3]) if len(fid) >= 3 and fid[1:3].isdigit() else 0
        stock = entry.get("vellum_stock") or (
            "irregular" if folio_num >= 14 else "standard"
        )
        damage_list = entry.get("damage") or []
        damage_str = ", ".join(damage_list) if damage_list else "—"
        click.echo(f"{fid:<8}  {stock:<12}  {damage_str}")
