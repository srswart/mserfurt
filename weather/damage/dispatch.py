"""Folio-to-damage mapping derived from CLIO-7 historical analysis."""

from __future__ import annotations

import re

_FOLIO_RE = re.compile(r"^f?(\d+)[rv]$")
_WATER_DAMAGED = frozenset(range(4, 6))   # folios 4 and 5 (f04r–f05v)
_MISSING_CORNER = frozenset({4})           # f04v only — but side checked separately


def _folio_num(folio_id: str) -> int:
    m = _FOLIO_RE.match(folio_id)
    return int(m.group(1)) if m else -1


def folio_is_water_damaged(folio_id: str) -> bool:
    """Return True if folio has water damage (f04r–f05v)."""
    return _folio_num(folio_id) in _WATER_DAMAGED


def folio_has_missing_corner(folio_id: str) -> bool:
    """Return True only for f04v (physical loss of lower-outer corner)."""
    m = _FOLIO_RE.match(folio_id)
    if not m:
        return False
    num = int(m.group(1))
    side = m.group(0)[-1]   # 'r' or 'v'
    return num == 4 and side == "v"
