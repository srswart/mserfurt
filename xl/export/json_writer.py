"""TD-001-A serializer — FolioPage → per-folio JSON file."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from xl.models import Annotation, FolioPage


def build_folio_dict(page: FolioPage) -> dict:
    """Serialize a FolioPage to a TD-001-A–conformant dict."""
    lines = [_serialize_line(line) for line in page.lines]
    return {
        "id": page.id,
        "recto_verso": page.recto_verso,
        "gathering_position": page.gathering_position,
        "lines": lines,
        "damage": page.damage if page.damage else None,
        "hand_notes": page.hand_notes if page.hand_notes else None,
        "section_breaks": list(page.section_breaks),
        "vellum_stock": page.vellum_stock,
        "metadata": _build_metadata(page),
    }


def write_folio_json(page: FolioPage, output_dir: Path) -> Path:
    """Write a folio JSON file to output_dir/{folio_id}.json."""
    path = Path(output_dir) / f"{page.id}.json"
    path.write_text(json.dumps(build_folio_dict(page), ensure_ascii=False, indent=2))
    return path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _serialize_line(line) -> dict:
    d: dict = {
        "number": line.number,
        "text": line.text,
        "register": line.register,
    }
    if line.english is not None:
        d["english"] = line.english
    d["annotations"] = [_serialize_annotation(a) for a in line.annotations]
    return d


def _serialize_annotation(ann: Annotation) -> dict:
    d: dict = {"type": ann.type}
    if ann.span is not None:
        d["span"] = {"char_start": ann.span[0], "char_end": ann.span[1]}
    if ann.detail:
        d["detail"] = ann.detail
    return d


def _build_metadata(page: FolioPage) -> dict:
    lines = page.lines
    line_count = len(lines)

    if line_count == 0:
        return {
            "line_count": 0,
            "text_density_chars_per_line": 0.0,
            "register_ratio": {"de": 0.0, "la": 0.0, "mhg": 0.0, "mixed": 0.0},
        }

    total_chars = sum(len(ln.text) for ln in lines)
    density = total_chars / line_count

    counts = Counter(ln.register for ln in lines)
    registers = ("de", "la", "mhg", "mixed")
    ratio = {r: counts.get(r, 0) / line_count for r in registers}

    return {
        "line_count": line_count,
        "text_density_chars_per_line": round(density, 2),
        "register_ratio": ratio,
    }
