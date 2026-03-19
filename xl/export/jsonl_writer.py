"""JSONL writer — one record per line per folio for bulk processing."""

from __future__ import annotations

import json
from pathlib import Path

from xl.models import FolioPage


def write_jsonl(pages: list[FolioPage], output_dir: Path) -> Path:
    """Write folios.jsonl to output_dir — one JSON object per line per folio."""
    path = Path(output_dir) / "folios.jsonl"
    records = []
    for page in pages:
        for line in page.lines:
            records.append({
                "folio_id": page.id,
                "gathering_position": page.gathering_position,
                "line_number": line.number,
                "text": line.text,
                "register": line.register,
                "english": line.english,
            })
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records))
    return path
