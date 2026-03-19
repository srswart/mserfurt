"""ScribeSim CLI — orchestrate scribal hand rendering for MS Erfurt 1457."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from scribesim.hand import load_base, resolve


@click.group()
def main() -> None:
    """ScribeSim — render Brother Konrad's Bastarda hand from XL folio JSON."""


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

@main.command()
@click.argument("folio_id")
@click.option("--input-dir", "input_dir", default="output-live", show_default=True,
              type=click.Path(), help="Directory containing per-folio JSON from XL")
@click.option("--output-dir", "output_dir", default="render-output", show_default=True,
              type=click.Path(), help="Directory to write PNG and heatmap")
@click.option("--hand-toml", "hand_toml", default=None, type=click.Path(exists=True),
              help="Path to hand parameter TOML (defaults to shared/hands/konrad_erfurt_1457.toml)")
@click.option("--dry-run", is_flag=True, default=False,
              help="Resolve hand params and report plan without rendering")
def render(folio_id: str, input_dir: str, output_dir: str,
           hand_toml: str | None, dry_run: bool) -> None:
    """Render a single folio to PNG + pressure heatmap.

    FOLIO_ID is the folio identifier, e.g. f01r or 1r.
    """
    import re
    m = re.match(r"f?(\d+)([rv])", folio_id)
    if not m:
        click.echo(f"error: invalid folio ID {folio_id!r} — expected e.g. f01r or 1r", err=True)
        sys.exit(1)
    fid = f"f{int(m.group(1)):02d}{m.group(2)}"

    folio_path = Path(input_dir) / f"{fid}.json"
    if not folio_path.exists():
        click.echo(f"error: folio JSON not found: {folio_path}", err=True)
        sys.exit(1)

    manifest_path = Path(input_dir) / "manifest.json"
    if not manifest_path.exists():
        click.echo(f"error: manifest.json not found in {input_dir}", err=True)
        sys.exit(1)

    folio_dict = json.loads(folio_path.read_text())
    base = load_base(Path(hand_toml) if hand_toml else None)
    params = resolve(base, fid)

    click.echo(f"[scribesim render] folio={fid}")
    click.echo(f"  input : {folio_path}")
    click.echo(f"  lines : {folio_dict['metadata']['line_count']}")
    click.echo(f"  hand  : pressure={params.get('pressure_base')} "
               f"ink={params.get('ink_density')} "
               f"speed={params.get('writing_speed')}")

    if dry_run:
        click.echo("  [dry-run] render skipped")
        return

    from scribesim.layout import place
    from scribesim.render import render_page, render_heatmap

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    layout = place(folio_dict, params)
    png_path = render_page(layout, params, out / f"{fid}.png")
    heatmap_path = render_heatmap(layout, params, out / f"{fid}_pressure.png")

    click.echo(f"  page    → {png_path}")
    click.echo(f"  heatmap → {heatmap_path}")


# ---------------------------------------------------------------------------
# render-batch
# ---------------------------------------------------------------------------

@main.command("render-batch")
@click.option("--input-dir", "input_dir", default="output-live", show_default=True,
              type=click.Path(), help="Directory containing manifest.json and folio JSONs")
@click.option("--output-dir", "output_dir", default="render-output", show_default=True,
              type=click.Path(), help="Directory to write PNGs and heatmaps")
@click.option("--dry-run", is_flag=True, default=False,
              help="Resolve hand params for each folio without rendering")
def render_batch(input_dir: str, output_dir: str, dry_run: bool) -> None:
    """Render all folios listed in manifest.json."""
    manifest_path = Path(input_dir) / "manifest.json"
    if not manifest_path.exists():
        click.echo(f"error: manifest.json not found in {input_dir}", err=True)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text())
    folios = manifest.get("folios", [])
    click.echo(f"[scribesim render-batch] {len(folios)} folio(s) in manifest")

    base = load_base()
    ok = 0
    for entry in folios:
        fid = entry["id"]
        folio_path = Path(input_dir) / entry["file"]
        if not folio_path.exists():
            click.echo(f"  {fid}  SKIP (file not found: {folio_path})")
            continue
        params = resolve(base, fid)
        click.echo(f"  {fid}  lines={entry['line_count']}  "
                   f"pressure={params.get('pressure_base'):.2f}  "
                   f"ink={params.get('ink_density'):.2f}", nl=False)
        if dry_run:
            click.echo("  [dry-run]")
            ok += 1
            continue
        try:
            from scribesim.layout import place
            from scribesim.render import render_page, render_heatmap
            folio_dict = json.loads(folio_path.read_text())
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            layout = place(folio_dict, params)
            render_page(layout, params, out / f"{fid}.png")
            render_heatmap(layout, params, out / f"{fid}_pressure.png")
            click.echo("  ✓")
            ok += 1
        except NotImplementedError as exc:
            click.echo(f"  SKIP ({exc})")

    click.echo(f"[scribesim render-batch] done — {ok}/{len(folios)} processed")


# ---------------------------------------------------------------------------
# hand
# ---------------------------------------------------------------------------

@main.command()
@click.option("--show", is_flag=True, default=True, help="Print resolved hand parameters")
@click.option("--folio", "folio_id", default=None,
              help="Apply folio-specific modifiers, e.g. f01r")
@click.option("--hand-toml", "hand_toml", default=None, type=click.Path(exists=True),
              help="Path to hand parameter TOML")
def hand(show: bool, folio_id: str | None, hand_toml: str | None) -> None:
    """Inspect resolved hand parameters for a folio."""
    base = load_base(Path(hand_toml) if hand_toml else None)
    params = resolve(base, folio_id) if folio_id else dict(base.get("hand", {}))

    label = f"folio {folio_id}" if folio_id else "base (no folio modifier)"
    click.echo(f"# Resolved hand parameters — {label}")
    for key, val in sorted(params.items()):
        click.echo(f"{key} = {val!r}")


# ---------------------------------------------------------------------------
# groundtruth
# ---------------------------------------------------------------------------

@main.command()
@click.argument("folio_id")
@click.option("--input-dir", "input_dir", default="render-output", show_default=True,
              type=click.Path(), help="Directory containing rendered layout data")
@click.option("--output-dir", "output_dir", default="render-output", show_default=True,
              type=click.Path(), help="Directory to write PAGE XML")
def groundtruth(folio_id: str, input_dir: str, output_dir: str) -> None:
    """Emit PAGE XML ground truth for a rendered folio."""
    from scribesim.groundtruth import generate
    import re
    m = re.match(r"f?(\d+)([rv])", folio_id)
    fid = f"f{int(m.group(1)):02d}{m.group(2)}" if m else folio_id

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    xml_path = generate({}, out / f"{fid}.xml")
    click.echo(f"[scribesim groundtruth] {fid} → {xml_path}")
