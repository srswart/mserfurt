"""Style anchor — the frozen exemplar set that defines Konrad's hand.

A style anchor directory contains ``style.json`` plus the exemplar images::

    style.json   {"id", "description", "exemplars": [...], "source": {...}}
    ex1.png ...

All folios condition on the same anchor so the codex reads as one scribe
(TD-018 §2.4).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StyleAnchor:
    id: str
    exemplar_paths: list[Path]
    description: str = ""
    source: dict = field(default_factory=dict)
    root: Path | None = None


def load_style_anchor(path: Path) -> StyleAnchor:
    root = Path(path)
    meta = json.loads((root / "style.json").read_text())
    exemplars: list[Path] = []
    for name in meta.get("exemplars", []):
        p = root / name
        if not p.exists():
            raise FileNotFoundError(f"style anchor exemplar missing: {p}")
        exemplars.append(p)
    return StyleAnchor(
        id=meta["id"],
        exemplar_paths=exemplars,
        description=meta.get("description", ""),
        source=meta.get("source", {}),
        root=root,
    )
