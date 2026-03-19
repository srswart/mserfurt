"""TD-001-B serializer — list[FolioPage] → manifest.json."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from xl.models import FolioPage, ManuscriptMeta

# Known gap between f05v and f06r per CLIO-7
_KNOWN_GAPS = [
    {
        "after_folio": "f05v",
        "estimated_missing": "1-3 folios",
        "notes": "CLIO-7 assesses 1-3 folios missing between f05v and f06r",
    }
]


def build_manifest_dict(
    pages: list[FolioPage],
    meta: ManuscriptMeta | None,
) -> dict:
    """Serialize all FolioPages to a TD-001-B–conformant manifest dict."""
    manuscript = _build_manuscript(meta, len(pages))
    folios = [_build_folio_entry(p) for p in pages]

    return {
        "manuscript": manuscript,
        "folios": folios,
        "gaps": _KNOWN_GAPS,
    }


def write_manifest(
    pages: list[FolioPage],
    meta: ManuscriptMeta | None,
    output_dir: Path,
) -> Path:
    """Write manifest.json to output_dir."""
    path = Path(output_dir) / "manifest.json"
    data = build_manifest_dict(pages, meta)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_manuscript(meta: ManuscriptMeta | None, folio_count: int) -> dict:
    if meta is None:
        return {
            "shelfmark": "unknown",
            "author": "unknown",
            "date": 0,
            "folio_count": folio_count,
        }
    return {
        "shelfmark": meta.shelfmark,
        "author": meta.author,
        "date": meta.date,
        "folio_count": folio_count,
        "language_primary": meta.language_primary,
        "language_secondary": meta.language_secondary,
    }


def _build_folio_entry(page: FolioPage) -> dict:
    # Dominant register
    counts = Counter(ln.register for ln in page.lines)
    dominant = counts.most_common(1)[0][0] if counts else "de"

    # Damage fields
    damage_type = None
    damage_extent = None
    if page.damage:
        damage_type = page.damage.get("type")
        damage_extent = page.damage.get("extent")

    # Hand fields
    hand = page.hand_notes or {}

    return {
        "id": page.id,
        "file": f"{page.id}.json",
        "line_count": len(page.lines),
        "damage_type": damage_type,
        "damage_extent": damage_extent,
        "hand_pressure": hand.get("pressure", "normal"),
        "hand_spacing": hand.get("spacing", "standard"),
        "hand_ink": hand.get("ink_density", "consistent"),
        "hand_speed": hand.get("speed", "deliberate"),
        "hand_scale": hand.get("scale", "standard"),
        "vellum_stock": page.vellum_stock,
        "register_dominant": dominant,
        "has_section_break": bool(page.section_breaks),
    }
