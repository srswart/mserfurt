"""Charset contract — XL character inventory vs. training charset.

TD-018 §2.3: every character XL can emit must map into the training charset
before generation is trusted. Unmappable characters fail loudly — no silent
alias substitution (the TD-014 lesson).
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CharsetTable:
    """Mapping from XL characters to training-charset strings.

    Characters not present in ``map`` are expected to appear verbatim in the
    training charset.
    """

    map: dict[str, str] = field(default_factory=dict)
    schema: int = 1


def load_charset_map(path: Path) -> CharsetTable:
    data = tomllib.loads(Path(path).read_text())
    return CharsetTable(map=dict(data.get("map", {})), schema=int(data.get("schema", 1)))


def xl_character_inventory(folio_dir: Path) -> set[str]:
    """Every character (excluding space) appearing in XL folio JSON line text."""
    inventory: set[str] = set()
    for fp in sorted(Path(folio_dir).glob("f*.json")):
        data = json.loads(fp.read_text())
        for line in data.get("lines", []):
            inventory.update(line.get("text", ""))
    inventory.discard(" ")
    return inventory


@dataclass
class CoverageReport:
    ok: bool
    missing: list[str]          # XL chars with no route into the training charset
    mapped: dict[str, str]      # applied mappings
    inventory_size: int

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "missing": self.missing,
            "mapped": self.mapped,
            "inventory_size": self.inventory_size,
        }


def check_charset_coverage(
    inventory: set[str],
    table: CharsetTable,
    training_charset: str,
) -> CoverageReport:
    """Verify every inventory character reaches the training charset.

    A character is covered if it is in the training charset verbatim, or if
    the charset table maps it to a string whose every character is covered.
    """
    covered = set(training_charset)
    missing: list[str] = []
    mapped: dict[str, str] = {}

    for ch in sorted(inventory):
        if ch in covered:
            continue
        target = table.map.get(ch)
        if target is not None and all(c in covered or c == " " for c in target):
            mapped[ch] = target
            continue
        missing.append(ch)

    return CoverageReport(
        ok=not missing,
        missing=missing,
        mapped=mapped,
        inventory_size=len(inventory),
    )


def normalize_text(text: str, table: CharsetTable) -> str:
    """Apply the charset table mapping to *text* (unmapped chars pass through)."""
    return "".join(table.map.get(ch, ch) for ch in text)
