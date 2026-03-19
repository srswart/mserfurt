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
@click.option("--dry-run", is_flag=True, default=False, help="Parse and plan without calling LLM APIs")
def translate(input_path: str, output_dir: str, folio: str | None, dry_run: bool) -> None:
    """Ingest source, translate to period German/Latin, and emit per-folio outputs."""
    # Pipeline stages will be wired here as their advances are implemented.
    # (ADV-XL-INGEST-001 → ADV-XL-TRANSLATE-001 → ADV-XL-REGISTER-001 →
    #  ADV-XL-FOLIO-001 → ADV-XL-ANNOTATE-001 → ADV-XL-EXPORT-001)
    click.echo(f"[xl translate] input={input_path} output={output_dir} folio={folio} dry_run={dry_run}")
    if dry_run:
        click.echo("[xl translate] dry-run: pipeline stages skipped")
        return
    click.echo("[xl translate] pipeline not yet wired — run with --dry-run for now")


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
