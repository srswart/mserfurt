"""XL manifest reader — parse per-folio damage and stock annotations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ManifestEntry:
    """Per-folio data extracted from the XL manifest.json."""

    folio_id: str
    vellum_stock: str = "standard"      # "standard" | "irregular"
    damage_type: Optional[str] = None   # e.g. "water_damage", None


def load_manifest(manifest_path: Path) -> dict[str, ManifestEntry]:
    """Parse an XL manifest.json and return a dict keyed by folio_id.

    Args:
        manifest_path: Path to manifest.json.

    Returns:
        Dict mapping folio_id → ManifestEntry.  Missing optional fields
        fall back to ManifestEntry defaults.
    """
    raw = json.loads(Path(manifest_path).read_text())
    result: dict[str, ManifestEntry] = {}
    for entry in raw.get("folios", []):
        fid = entry.get("id", "")
        result[fid] = ManifestEntry(
            folio_id=fid,
            vellum_stock=entry.get("vellum_stock") or "standard",
            damage_type=entry.get("damage_type"),
        )
    return result
