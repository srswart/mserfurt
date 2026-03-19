"""Load base hand parameters from TOML and resolve per-folio variants.

Public API (unchanged from CLI's perspective):
    load_base(toml_path=None) -> HandParams
    resolve(base, folio_id) -> HandParams
"""

from __future__ import annotations

from pathlib import Path

from scribesim.hand.params import HandParams

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

_DEFAULT_TOML = Path(__file__).parents[2] / "shared" / "hands" / "konrad_erfurt_1457.toml"


def load_base(toml_path: Path | None = None) -> HandParams:
    """Load base hand parameters from TOML and return a typed HandParams."""
    path = Path(toml_path) if toml_path else _DEFAULT_TOML
    if tomllib is None:
        raise ImportError("tomllib (Python 3.11+) or tomli required")
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return HandParams.from_dict(raw.get("hand", {}))


def resolve(base: HandParams | dict, folio_id: str,
            toml_path: Path | None = None) -> HandParams:
    """Apply folio-specific TOML modifier delta to base and return HandParams.

    If base is a dict (legacy), it is converted to HandParams first.
    The TOML [modifiers.<key>] section is loaded from toml_path (or the
    default) and applied as a delta — only differing values need listing.
    """
    if isinstance(base, dict):
        # Legacy: called with raw TOML dict from old load_base()
        raw_modifiers = base.get("modifiers", {})
        params = HandParams.from_dict(base.get("hand", {}))
    else:
        params = base
        path = Path(toml_path) if toml_path else _DEFAULT_TOML
        if tomllib is None:
            raise ImportError("tomllib (Python 3.11+) or tomli required")
        with open(path, "rb") as f:
            raw = tomllib.load(f)
        raw_modifiers = raw.get("modifiers", {})

    # Normalise folio key: "f01r" → "01r", also try full id
    folio_key = folio_id.lstrip("f")
    delta = raw_modifiers.get(folio_key) or raw_modifiers.get(folio_id) or {}

    return params.apply_delta(delta)
