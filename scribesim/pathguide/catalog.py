"""Dense path guide catalogs for TD-014 proof and active-folio datasets."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from scribesim.guides.catalog import GUIDE_CATALOG
from scribesim.pathguide.io import (
    guide_from_letterform_guide,
    guide_from_waypoints,
    load_legacy_guides_toml_as_dense,
    load_pathguides_toml,
)
from scribesim.pathguide.model import DensePathGuide, GuideSource


STARTER_PROOF_PATH = Path("shared/hands/pathguides/starter_proof.toml")
STARTER_ALPHABET_V1_PATH = Path("shared/hands/pathguides/starter_alphabet_v1.toml")
ACTIVE_FOLIO_ALPHABET_V1_PATH = Path("shared/hands/pathguides/active_folio_alphabet_v1.toml")
EXTRACTED_GUIDES_PATH = Path("shared/hands/guides_extracted.toml")
_DEFAULT_X_HEIGHT_MM = 3.5
_DEFAULT_SOURCE_RESOLUTION_PPMM = 16.0

STARTER_ALPHABET_V1_GLYPHS = ("u", "n", "d", "e", "r", "i", "m", "a", "o", "t", "h")
STARTER_ALPHABET_V1_JOINS = (
    "u->n",
    "n->d",
    "d->e",
    "e->r",
    "i->n",
    "m->i",
    "r->space",
    "space->d",
)
STARTER_ALPHABET_V1_REQUIRED_SYMBOLS = STARTER_ALPHABET_V1_GLYPHS + STARTER_ALPHABET_V1_JOINS
STARTER_ALPHABET_V1_JOIN_SCHEDULES = {
    "u->n": "contact_only",
    "n->d": "contact_only",
    "d->e": "contact_only",
    "e->r": "contact_only",
    "i->n": "contact_only",
    "m->i": "contact_only",
    "r->space": "contact_then_lift",
    "space->d": "lift_then_contact",
}
STARTER_ALPHABET_V1_SOURCE_MODES = {
    "u": "legacy_fallback",
    "n": "legacy_fallback",
    "d": "curated_fallback",
    "e": "automatic",
    "r": "automatic",
    "i": "automatic",
    "m": "automatic",
    "a": "automatic",
    "o": "automatic",
    "t": "automatic",
    "h": "automatic",
    "u->n": "curated_join",
    "n->d": "curated_join",
    "d->e": "curated_join",
    "e->r": "curated_join",
    "i->n": "curated_join",
    "m->i": "curated_join",
    "r->space": "curated_join",
    "space->d": "curated_join",
}
STARTER_ALPHABET_V1_SPLITS = {
    "u": "train",
    "n": "train",
    "d": "train",
    "e": "train",
    "r": "train",
    "m": "train",
    "t": "train",
    "a": "validation",
    "i": "validation",
    "o": "test",
    "h": "test",
    "u->n": "train",
    "n->d": "train",
    "d->e": "train",
    "e->r": "train",
    "i->n": "validation",
    "m->i": "validation",
    "r->space": "test",
    "space->d": "test",
}
STARTER_ALPHABET_V1_PROOF_WORDS = {
    "train": ("under", "ad", "to"),
    "validation": ("in", "mir"),
    "test": ("he", "or"),
}
ACTIVE_FOLIO_ALPHABET_V1_REVIEW_FOLIOS = (
    {
        "folio_id": "f01r",
        "folio_path": "tests/golden/f01r/folio.json",
        "line_numbers": (1, 2, 3),
    },
)
ACTIVE_FOLIO_ALPHABET_V1_GLYPHS = (
    "E",
    "H",
    "a",
    "b",
    "c",
    "d",
    "e",
    "g",
    "h",
    "i",
    "k",
    "l",
    "m",
    "n",
    "o",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "z",
    "ů",
)
ACTIVE_FOLIO_ALPHABET_V1_NEW_GLYPHS = ("E", "H", "s", "u", "v", "z", "ů")
ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS = ACTIVE_FOLIO_ALPHABET_V1_GLYPHS
ACTIVE_FOLIO_ALPHABET_V1_SOURCE_MODES = {
    "E": "capital_exact",
    "H": "capital_exact",
    "a": "automatic",
    "b": "automatic",
    "c": "automatic",
    "d": "starter_reuse",
    "e": "automatic",
    "g": "automatic",
    "h": "automatic",
    "i": "automatic",
    "k": "automatic",
    "l": "automatic",
    "m": "automatic",
    "n": "starter_reuse",
    "o": "automatic",
    "r": "automatic",
    "s": "curated_fallback",
    "t": "automatic",
    "u": "starter_reuse",
    "v": "curated_fallback",
    "w": "automatic",
    "z": "curated_fallback",
    "ů": "curated_variant",
}
ACTIVE_FOLIO_ALPHABET_V1_SPLITS = {
    "E": "test",
    "H": "validation",
    "a": "train",
    "b": "train",
    "c": "train",
    "d": "train",
    "e": "train",
    "g": "train",
    "h": "train",
    "i": "train",
    "k": "test",
    "l": "train",
    "m": "train",
    "n": "train",
    "o": "train",
    "r": "train",
    "s": "validation",
    "t": "train",
    "u": "train",
    "v": "validation",
    "w": "test",
    "z": "test",
    "ů": "validation",
}
ACTIVE_FOLIO_ALPHABET_V1_PROOF_WORDS = {
    "train": ("hebet", "meister", "unsers", "und"),
    "validation": ("Hie", "sich", "von"),
    "test": ("bůch", "Eckehart", "daz", "volkommenheit"),
}


def _with_source_updates(
    guide: DensePathGuide,
    *,
    split: str | None = None,
    confidence_tier: str | None = None,
    source_path: str | None = None,
) -> DensePathGuide:
    sources = tuple(
        replace(
            source,
            split=split if split is not None else source.split,
            confidence_tier=confidence_tier if confidence_tier is not None else source.confidence_tier,
            source_path=source_path if source_path is not None else source.source_path,
        )
        for source in guide.sources
    )
    return replace(guide, sources=sources)


def _clone_guide_with_symbol(
    guide: DensePathGuide,
    symbol: str,
    *,
    source_id: str,
    source_path: str,
    split: str,
    confidence_tier: str = "accepted",
) -> DensePathGuide:
    return replace(
        guide,
        symbol=symbol,
        sources=(
            GuideSource(
                source_id=source_id,
                source_path=source_path,
                confidence_tier=confidence_tier,
                split=split,
                source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
            ),
        ),
    )


def build_active_folio_review_inventory() -> tuple[str, ...]:
    """Collect the exact glyph inventory required by the active review folios."""

    symbols: set[str] = set()
    for spec in ACTIVE_FOLIO_ALPHABET_V1_REVIEW_FOLIOS:
        data = json.loads(Path(spec["folio_path"]).read_text())
        line_numbers = set(spec["line_numbers"])
        for line in data.get("lines", []):
            if int(line["number"]) not in line_numbers:
                continue
            symbols.update(char for char in line["text"] if char != " ")
    return tuple(sorted(symbols))


def build_starter_proof_guides(*, x_height_mm: float = _DEFAULT_X_HEIGHT_MM):
    """Build starter proof glyphs and joins for TD-014."""

    guides = {
        letter: guide_from_letterform_guide(
            GUIDE_CATALOG[letter],
            x_height_mm=x_height_mm,
            source_id=f"legacy-guide:{letter}",
            source_path="scribesim/guides/catalog.py",
            confidence_tier="accepted",
            split="train",
            source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
        )
        for letter in ("u", "n", "e", "r")
    }

    guides["d"] = guide_from_waypoints(
        "d",
        [
            (0.36, 1.70, True),
            (0.40, 1.10, True),
            (0.44, 0.30, True),
            (0.34, 0.05, True),
            (0.15, 0.04, True),
            (0.03, 0.25, True),
            (0.07, 0.65, True),
            (0.20, 0.85, True),
            (0.38, 0.95, True),
        ],
        x_height_mm=x_height_mm,
        x_advance_xh=0.55,
        kind="glyph",
        source_id="starter-proof:d",
        source_path="shared/hands/pathguides/starter_proof.toml",
        confidence_tier="accepted",
        split="train",
        source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
    )

    joins = {
        "u->n": [(0.00, 0.00, True), (0.22, 0.18, True), (0.42, 0.92, True)],
        "n->d": [(0.00, 0.00, True), (0.26, 0.16, True), (0.48, 0.72, True)],
        "d->e": [(0.00, 0.00, True), (0.18, 0.20, True), (0.38, 0.50, True)],
        "e->r": [(0.00, 0.52, True), (0.16, 0.72, True), (0.30, 0.86, True)],
    }
    x_advances = {
        "u->n": 0.42,
        "n->d": 0.48,
        "d->e": 0.38,
        "e->r": 0.30,
    }

    for symbol, waypoints in joins.items():
        guides[symbol] = guide_from_waypoints(
            symbol,
            waypoints,
            x_height_mm=x_height_mm,
            x_advance_xh=x_advances[symbol],
            kind="join",
            default_pressure=0.35,
            corridor_half_width_mm=0.15,
            source_id=f"starter-proof:{symbol}",
            source_path="shared/hands/pathguides/starter_proof.toml",
            confidence_tier="accepted",
            split="train",
            source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
        )

    return guides


def load_starter_proof_guides(path: Path | str = STARTER_PROOF_PATH):
    """Load the committed starter proof dense guides."""

    return load_pathguides_toml(path)


def build_starter_alphabet_v1_guides(*, x_height_mm: float = _DEFAULT_X_HEIGHT_MM):
    """Build the starter alphabet dataset used for Level 1 curriculum work."""

    extracted = load_legacy_guides_toml_as_dense(
        EXTRACTED_GUIDES_PATH,
        x_height_mm=x_height_mm,
        split="train",
        source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
    )
    proof_guides = build_starter_proof_guides(x_height_mm=x_height_mm)

    guides: dict[str, DensePathGuide] = {}
    for symbol in STARTER_ALPHABET_V1_GLYPHS:
        if symbol in extracted:
            guide = extracted[symbol]
        elif symbol in proof_guides:
            guide = proof_guides[symbol]
        else:
            guide = guide_from_letterform_guide(
                GUIDE_CATALOG[symbol],
                x_height_mm=x_height_mm,
                source_id=f"legacy-guide:{symbol}",
                source_path="scribesim/guides/catalog.py",
                confidence_tier="accepted",
                split="train",
                source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
            )
        guides[symbol] = _with_source_updates(guide, split=STARTER_ALPHABET_V1_SPLITS[symbol])

    join_waypoints = {
        "i->n": [(0.00, 0.00, True), (0.16, 0.10, True), (0.34, 0.78, True)],
        "m->i": [(0.00, 0.00, True), (0.12, 0.12, True), (0.26, 0.84, True)],
        "r->space": [
            (0.00, 0.58, True),
            (0.10, 0.54, True),
            (0.12, 0.54, False),
            (0.28, 0.48, False),
            (0.42, 0.44, False),
        ],
        "space->d": [
            (0.00, 0.42, False),
            (0.14, 0.48, False),
            (0.24, 0.72, True),
            (0.32, 0.88, True),
        ],
    }
    join_x_advances = {
        "u->n": 0.42,
        "n->d": 0.48,
        "d->e": 0.38,
        "e->r": 0.30,
        "i->n": 0.34,
        "m->i": 0.26,
        "r->space": 0.42,
        "space->d": 0.32,
    }

    for symbol in STARTER_ALPHABET_V1_JOINS:
        if symbol in proof_guides:
            guide = proof_guides[symbol]
        else:
            default_pressure = 0.35
            corridor_half_width_mm = 0.15
            if STARTER_ALPHABET_V1_JOIN_SCHEDULES[symbol] == "lift_then_contact":
                default_pressure = 0.25
                corridor_half_width_mm = 0.14
            guide = guide_from_waypoints(
                symbol,
                join_waypoints[symbol],
                x_height_mm=x_height_mm,
                x_advance_xh=join_x_advances[symbol],
                kind="join",
                default_pressure=default_pressure,
                corridor_half_width_mm=corridor_half_width_mm,
                source_id=f"starter-alphabet-v1:{symbol}",
                source_path=STARTER_ALPHABET_V1_PATH.as_posix(),
                confidence_tier="accepted",
                split="train",
                source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
            )
        guides[symbol] = _with_source_updates(guide, split=STARTER_ALPHABET_V1_SPLITS[symbol])

    return guides


def build_starter_alphabet_v1_confidence_manifest() -> dict[str, dict[str, object]]:
    """Return confidence-tier counts and metadata for the starter alphabet dataset."""

    guides = build_starter_alphabet_v1_guides()
    manifest: dict[str, dict[str, object]] = {}
    for symbol in STARTER_ALPHABET_V1_REQUIRED_SYMBOLS:
        counts = {"accepted": 0, "soft_accepted": 0, "rejected": 0}
        for source in guides[symbol].sources:
            counts[source.confidence_tier] = counts.get(source.confidence_tier, 0) + 1
        manifest[symbol] = {
            "kind": guides[symbol].kind,
            "split": STARTER_ALPHABET_V1_SPLITS[symbol],
            "source_mode": STARTER_ALPHABET_V1_SOURCE_MODES[symbol],
            "contact_schedule": STARTER_ALPHABET_V1_JOIN_SCHEDULES.get(symbol),
            "counts": counts,
        }
    return manifest


def load_starter_alphabet_v1_guides(path: Path | str = STARTER_ALPHABET_V1_PATH):
    """Load the committed starter alphabet dense guides."""

    return load_pathguides_toml(path)


def _build_active_folio_curated_guides(
    *,
    x_height_mm: float,
    starter_guides: dict[str, DensePathGuide],
    extracted_guides: dict[str, DensePathGuide],
) -> dict[str, DensePathGuide]:
    active_path = ACTIVE_FOLIO_ALPHABET_V1_PATH.as_posix()
    guides: dict[str, DensePathGuide] = {}

    guides["H"] = _clone_guide_with_symbol(
        extracted_guides["h"],
        "H",
        source_id="active-folio-alphabet-v1:H",
        source_path=active_path,
        split=ACTIVE_FOLIO_ALPHABET_V1_SPLITS["H"],
    )
    guides["E"] = _clone_guide_with_symbol(
        extracted_guides["e"],
        "E",
        source_id="active-folio-alphabet-v1:E",
        source_path=active_path,
        split=ACTIVE_FOLIO_ALPHABET_V1_SPLITS["E"],
    )

    guides["s"] = guide_from_waypoints(
        "s",
        [
            (0.34, 0.98, True),
            (0.18, 0.84, True),
            (0.12, 0.62, True),
            (0.18, 0.42, True),
            (0.34, 0.24, True),
            (0.22, 0.10, True),
            (0.10, 0.02, True),
        ],
        x_height_mm=x_height_mm,
        x_advance_xh=0.42,
        kind="glyph",
        default_pressure=0.42,
        corridor_half_width_mm=0.18,
        source_id="active-folio-alphabet-v1:s",
        source_path=active_path,
        confidence_tier="accepted",
        split=ACTIVE_FOLIO_ALPHABET_V1_SPLITS["s"],
        source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
    )
    guides["v"] = guide_from_waypoints(
        "v",
        [
            (0.02, 0.94, True),
            (0.16, 0.10, True),
            (0.28, 0.28, True),
            (0.46, 0.96, True),
        ],
        x_height_mm=x_height_mm,
        x_advance_xh=0.56,
        kind="glyph",
        default_pressure=0.44,
        corridor_half_width_mm=0.18,
        source_id="active-folio-alphabet-v1:v",
        source_path=active_path,
        confidence_tier="accepted",
        split=ACTIVE_FOLIO_ALPHABET_V1_SPLITS["v"],
        source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
    )
    guides["z"] = guide_from_waypoints(
        "z",
        [
            (0.02, 0.94, True),
            (0.42, 0.94, True),
            (0.12, 0.46, True),
            (0.02, 0.04, True),
            (0.44, 0.04, True),
        ],
        x_height_mm=x_height_mm,
        x_advance_xh=0.52,
        kind="glyph",
        default_pressure=0.40,
        corridor_half_width_mm=0.18,
        source_id="active-folio-alphabet-v1:z",
        source_path=active_path,
        confidence_tier="accepted",
        split=ACTIVE_FOLIO_ALPHABET_V1_SPLITS["z"],
        source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
    )
    guides["ů"] = guide_from_waypoints(
        "ů",
        [
            (0.05, 0.95, True),
            (0.08, 0.05, True),
            (0.15, 0.00, True),
            (0.35, 0.05, True),
            (0.50, 0.95, True),
            (0.52, 0.00, True),
            (0.54, 0.00, False),
            (0.24, 1.16, False),
            (0.24, 1.22, True),
            (0.30, 1.36, True),
            (0.36, 1.22, True),
        ],
        x_height_mm=x_height_mm,
        x_advance_xh=starter_guides["u"].x_advance_mm / x_height_mm,
        kind="glyph",
        default_pressure=0.44,
        corridor_half_width_mm=0.18,
        source_id="active-folio-alphabet-v1:ů",
        source_path=active_path,
        confidence_tier="accepted",
        split=ACTIVE_FOLIO_ALPHABET_V1_SPLITS["ů"],
        source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
    )
    return guides


def build_active_folio_alphabet_v1_guides(*, x_height_mm: float = _DEFAULT_X_HEIGHT_MM):
    """Build the exact glyph inventory required by the active folio review slice."""

    extracted = load_legacy_guides_toml_as_dense(
        EXTRACTED_GUIDES_PATH,
        x_height_mm=x_height_mm,
        split="train",
        source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
    )
    starter_guides = build_starter_alphabet_v1_guides(x_height_mm=x_height_mm)
    curated = _build_active_folio_curated_guides(
        x_height_mm=x_height_mm,
        starter_guides=starter_guides,
        extracted_guides=extracted,
    )

    guides: dict[str, DensePathGuide] = {}
    for symbol in ACTIVE_FOLIO_ALPHABET_V1_GLYPHS:
        if symbol in curated:
            guide = curated[symbol]
        elif symbol in extracted:
            guide = extracted[symbol]
        elif symbol in starter_guides:
            guide = starter_guides[symbol]
        else:
            raise KeyError(f"missing active folio guide for symbol: {symbol}")
        guides[symbol] = _with_source_updates(guide, split=ACTIVE_FOLIO_ALPHABET_V1_SPLITS[symbol])
    return guides


def build_active_folio_alphabet_v1_confidence_manifest() -> dict[str, dict[str, object]]:
    """Return confidence-tier counts and metadata for the active folio alphabet dataset."""

    guides = build_active_folio_alphabet_v1_guides()
    manifest: dict[str, dict[str, object]] = {}
    for symbol in ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS:
        counts = {"accepted": 0, "soft_accepted": 0, "rejected": 0}
        for source in guides[symbol].sources:
            counts[source.confidence_tier] = counts.get(source.confidence_tier, 0) + 1
        manifest[symbol] = {
            "kind": guides[symbol].kind,
            "split": ACTIVE_FOLIO_ALPHABET_V1_SPLITS[symbol],
            "source_mode": ACTIVE_FOLIO_ALPHABET_V1_SOURCE_MODES[symbol],
            "contact_schedule": None,
            "counts": counts,
        }
    return manifest


def load_active_folio_alphabet_v1_guides(path: Path | str = ACTIVE_FOLIO_ALPHABET_V1_PATH):
    """Load the committed active folio alphabet dense guides."""

    return load_pathguides_toml(path)
