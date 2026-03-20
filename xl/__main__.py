"""Entry point for the xl CLI."""

import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def main() -> None:
    """XL — reverse-translate and structure MS Erfurt Aug. 12°47."""


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True), help="Annotated source manuscript (.md)")
@click.option("--output", "output_dir", required=True, type=click.Path(), help="Directory to write folio JSON, manifest, and PAGE XML")
@click.option("--folio", default=None, help="Restrict to a single folio, e.g. 7r")
@click.option("--sections", default=None, help="Only translate these section numbers, e.g. 1,2 (skips the rest — use with --folio for fast dev runs)")
@click.option("--dry-run", is_flag=True, default=False, help="Parse and plan without calling LLM APIs")
@click.option("--formats", default="json,manifest,xml", show_default=True, help="Comma-separated output formats: json,manifest,xml,jsonl")
def translate(input_path: str, output_dir: str, folio: str | None, sections: str | None, dry_run: bool, formats: str) -> None:
    """Ingest source, translate to period German/Latin, and emit per-folio outputs."""
    from pathlib import Path
    from xl.ingest import parse
    from xl.register import build_register_map
    from xl.translate.dispatcher import translate_section
    from xl.folio.structurer import structure
    from xl.annotate.annotator import annotate
    from xl.export import export

    fmt_list = [f.strip() for f in formats.split(",") if f.strip()]

    click.echo(f"[xl] input      : {input_path}")
    click.echo(f"[xl] output     : {output_dir}")
    click.echo(f"[xl] dry-run    : {dry_run}")
    click.echo(f"[xl] formats    : {fmt_list}")
    if folio:
        click.echo(f"[xl] folio filter: {folio}")
    section_filter = {int(n.strip()) for n in sections.split(",")} if sections else None
    if section_filter:
        click.echo(f"[xl] section filter: {sorted(section_filter)}")

    # Stage 1 — Ingest
    click.echo("\n[1/5] ingest ...")
    result = parse(Path(input_path))
    if section_filter:
        result.sections = [s for s in result.sections if s.number in section_filter]
    click.echo(f"      {len(result.sections)} section(s), shelfmark={result.metadata.shelfmark!r}")

    # Stage 2 — Register
    click.echo("[2/5] register ...")
    register_map = build_register_map(result)
    if register_map.errors:
        click.echo(f"      {len(register_map.errors)} register error(s):", err=True)
        for e in register_map.errors:
            click.echo(f"        {e.error_type}: {e.message}", err=True)
    else:
        click.echo(f"      {len(register_map.entries)} passage register entries, 0 errors")

    # Stage 3 — Translate
    from xl.models import TranslatedSection as _TS
    from xl.translate.dispatcher import translate_passage
    click.echo(f"[3/5] translate ({'dry-run' if dry_run else 'live'}) ...")
    translated_sections = []
    total_passages = sum(len(s.passages) for s in result.sections)
    done = 0
    for section in result.sections:
        translated_passages = []
        for passage in section.passages:
            done += 1
            preview = passage.text[:50].replace("\n", " ")
            click.echo(f"      [{done:3d}/{total_passages}] s{section.number} {passage.register:6s}  {preview!r}", nl=False)
            tp = translate_passage(passage, dry_run=dry_run)
            translated_passages.append(tp)
            click.echo(f"  ✓ ({tp.method})")
        translated_sections.append(_TS(section=section, passages=translated_passages))
    click.echo(f"      {done} passages translated")

    # Stage 4 — Folio structure
    click.echo("[4/5] folio structuring ...")
    pages = structure(translated_sections, register_map)
    if folio:
        import re as _re
        _m = _re.match(r"f?(\d+)([rv])", folio)
        folio_id = f"f{int(_m.group(1)):02d}{_m.group(2)}" if _m else folio
        pages = [p for p in pages if p.id == folio_id]
        if not pages:
            click.echo(f"      warning: no pages matched folio filter {folio!r}", err=True)
    click.echo(f"      {len(pages)} page(s) structured")

    # Stage 5 — Annotate
    click.echo("[5/5] annotate ...")
    pages = annotate(pages)
    total_annotations = sum(len(ln.annotations) for p in pages for ln in p.lines)
    click.echo(f"      {total_annotations} annotation(s) applied")

    # Export
    click.echo(f"\n[out] writing {fmt_list} → {output_dir}")
    out = Path(output_dir)
    export(pages, result.metadata, out, formats=fmt_list)
    written = sorted(out.rglob("*"))
    for f in written:
        if f.is_file():
            size = f.stat().st_size
            click.echo(f"      {f.relative_to(out)}  ({size:,} bytes)")

    click.echo(f"\n[xl] done — {len(pages)} folio(s) exported to {output_dir}")


@main.command()
@click.argument("output_dir", type=click.Path(exists=True))
def manifest(output_dir: str) -> None:
    """Regenerate manifest.json from existing folio JSON outputs without re-translating."""
    click.echo(f"[xl manifest] output_dir={output_dir}")
    click.echo("[xl manifest] not yet implemented (ADV-XL-EXPORT-001)")


@main.command()
@click.argument("output_dir", type=click.Path(exists=True))
def validate(output_dir: str) -> None:
    """Validate all artifacts in OUTPUT_DIR against TD-001-A, TD-001-B, and TD-001-C."""
    click.echo(f"[xl validate] output_dir={output_dir}")
    click.echo("[xl validate] not yet implemented (ADV-XL-EXPORT-001)")


@main.command()
@click.argument("folio_json", type=click.Path(exists=True))
def preview(folio_json: str) -> None:
    """Render a terminal preview of a single folio JSON file."""
    click.echo(f"[xl preview] folio_json={folio_json}")
    click.echo("[xl preview] not yet implemented (ADV-XL-FOLIO-001)")


if __name__ == "__main__":
    main()
