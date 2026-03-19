"""xl.export — serialize annotated FolioPages to TD-001-A/B/C artifacts.

Supported formats:
    json     — per-folio JSON (TD-001-A)
    manifest — manifest.json (TD-001-B)
    xml      — per-folio PAGE XML (TD-001-C)
    jsonl    — consolidated JSONL (bulk processing)
"""

from __future__ import annotations

from pathlib import Path

from xl.export.json_writer import write_folio_json
from xl.export.manifest_writer import write_manifest
from xl.export.page_xml_writer import write_page_xml
from xl.export.jsonl_writer import write_jsonl
from xl.models import FolioPage, ManuscriptMeta

_DEFAULT_FORMATS = ("json", "manifest", "xml")


def export(
    pages: list[FolioPage],
    meta: ManuscriptMeta | None,
    output_dir: Path,
    formats: list[str] | tuple[str, ...] | None = None,
) -> None:
    """Write all requested output formats to output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    active = set(formats) if formats is not None else set(_DEFAULT_FORMATS)

    if "json" in active:
        for page in pages:
            write_folio_json(page, output_dir)

    if "manifest" in active:
        write_manifest(pages, meta, output_dir)

    if "xml" in active:
        for page in pages:
            write_page_xml(page, output_dir)

    if "jsonl" in active:
        write_jsonl(pages, output_dir)


__all__ = ["export", "write_folio_json", "write_manifest", "write_page_xml", "write_jsonl"]
