"""Verbatim reference table lookup.

Verbatim passages are inserted directly from the critical-edition reference
table — no LLM involvement. The table lives in xl/verbatim/references.toml.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

if hasattr(__import__("sys"), "version_info") and __import__("sys").version_info >= (3, 11):
    import tomllib
else:
    import tomllib  # type: ignore[no-redef]

_REFERENCES_PATH = Path(__file__).parent.parent / "verbatim" / "references.toml"


class VerbatimNotFound(KeyError):
    """Raised when a verbatim_source key has no entry in the reference table."""


@lru_cache(maxsize=1)
def _load_table() -> dict:
    return tomllib.loads(_REFERENCES_PATH.read_text(encoding="utf-8"))


def lookup(verbatim_source: str) -> str:
    """Return the reference-table text for the given source key.

    Raises VerbatimNotFound if the key is not in the table.
    """
    table = _load_table()
    entry = table.get(verbatim_source)
    if entry is None:
        # Case-insensitive fallback
        for key, val in table.items():
            if key.lower() == verbatim_source.lower():
                return val["text"]
        raise VerbatimNotFound(
            f"No verbatim entry for {verbatim_source!r}. "
            f"Available keys: {list(table.keys())}"
        )
    return entry["text"]


def known_keys() -> list[str]:
    """Return all keys in the reference table."""
    return list(_load_table().keys())
