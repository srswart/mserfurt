"""Generation backends.

- ``stub``: dependency-light deterministic backends for CPU dev/testing.
- ``command``: batch subprocess protocol used to drive the fine-tuned
  One-DM / DiffusionPen runners on the Mac workstation
  (see scripts/scribehand/).
"""

from __future__ import annotations

from pathlib import Path


def backend_from_config(name: str, config_path: Path | None = None):
    """Resolve a backend by name.

    ``stub-pil`` and ``stub-evo`` are built in. Any other name is looked up
    in the backends TOML (default ``shared/models/scribehand/backends.toml``)
    and constructed as a :class:`CommandBackend`.
    """
    from scribesim.scribehand.backends.stub import PILStubBackend, EvoStubBackend
    from scribesim.scribehand.backends.command import CommandBackend

    if name == "stub-pil":
        return PILStubBackend()
    if name == "stub-evo":
        return EvoStubBackend()

    import tomllib

    cfg_path = config_path or Path("shared/models/scribehand/backends.toml")
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"backend {name!r} is not built in and {cfg_path} does not exist"
        )
    cfg = tomllib.loads(cfg_path.read_text())
    entry = cfg.get("backends", {}).get(name)
    if entry is None:
        raise KeyError(f"backend {name!r} not found in {cfg_path}")
    return CommandBackend(
        name=name,
        argv=list(entry["argv"]),
        workdir=Path(entry.get("workdir", ".")),
        style_dir=Path(entry["style_dir"]) if entry.get("style_dir") else None,
        checkpoint=entry.get("checkpoint"),
    )
