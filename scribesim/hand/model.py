"""Load base hand parameters from TOML and apply per-folio modifiers."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

_DEFAULT_TOML = Path(__file__).parents[2] / "shared" / "hands" / "konrad_erfurt_1457.toml"


def load_base(toml_path: Path | None = None) -> dict:
    """Load base hand parameters from TOML file."""
    path = Path(toml_path) if toml_path else _DEFAULT_TOML
    if tomllib is None:
        raise ImportError("tomllib (Python 3.11+) or tomli required to load hand parameters")
    with open(path, "rb") as f:
        return tomllib.load(f)


def resolve(base: dict, folio_id: str) -> dict:
    """Apply folio-specific modifiers to base hand parameters.

    Modifiers are declared under [modifiers.<folio_id>] in the TOML.
    Returns a flat dict of resolved parameter values.
    """
    params = dict(base.get("hand", {}))
    modifiers = base.get("modifiers", {})
    folio_key = folio_id.lstrip("f").replace("r", "r").replace("v", "v")

    # Try exact match first (e.g. "01r"), then without leading zero (e.g. "1r")
    folio_mod = modifiers.get(folio_id) or modifiers.get(folio_key) or {}
    params.update(folio_mod)
    return params
