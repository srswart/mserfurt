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
