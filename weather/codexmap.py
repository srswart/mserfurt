"""Codex Weathering Map — physical damage propagation model.

Implements TD-011 Part 2: generates a deterministic per-folio weathering
specification for the full 17-leaf (34-side) gathering.

Public API:
    compute_water_propagation(folio_num, side, source_folio, decay_rate, verso_attenuation) -> float
    compute_edge_darkening(folio_num, gathering_size) -> float
    generate_foxing_clusters(n_clusters, gathering_size, seed) -> dict[int, list[FoxingSpot]]
    compute_codex_weathering_map(gathering_size, seed, clio7_path, clio7_annotations) -> dict[str, FolioWeatherSpec]
    save_codex_map(weathering_map, output_path) -> None
    load_codex_map(path) -> dict[str, FolioWeatherSpec]
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional

from weather.promptgen import (
    FolioWeatherSpec,
    FoxingSpot,
    MissingCornerSpec,
    TextDegradationZone,
    WaterDamageSpec,
)

# ---------------------------------------------------------------------------
# Constants (TD-011 Part 2)
# ---------------------------------------------------------------------------

_EPICENTER_LEAF = 4
_EPICENTER_RECTO_SEVERITY = 1.0
_EPICENTER_VERSO_SEVERITY = 0.85
_DEFAULT_DECAY_RATE = 0.4
_WATER_THRESHOLD = 0.03   # severity below this → no water damage applied
_N_FOXING_CLUSTERS = 5


# ---------------------------------------------------------------------------
# compute_water_propagation
# ---------------------------------------------------------------------------

def compute_water_propagation(
    folio_num: int,
    side: str,
    source_folio: int = _EPICENTER_LEAF,
    decay_rate: float = _DEFAULT_DECAY_RATE,
    verso_attenuation: float = _EPICENTER_VERSO_SEVERITY,
) -> float:
    """Compute water damage severity for a given folio and side.

    Physics (TD-011 §2.1):
    - Source recto (folio_num==source_folio, side=='r') returns 1.0.
    - Source verso (folio_num==source_folio, side=='v') returns verso_attenuation.
    - Other folios: severity = decay_rate^|folio_num - source_folio|.
      No extra verso attenuation is applied to non-epicenter leaves —
      the attenuation is only for the same-leaf verso (through-the-vellum path).
    - Returns 0.0 if computed severity falls below _WATER_THRESHOLD.

    Args:
        folio_num:          Leaf number (1-based).
        side:               'r' (recto) or 'v' (verso).
        source_folio:       The epicenter leaf number (default 4).
        decay_rate:         Severity multiplier per leaf of distance (default 0.4).
        verso_attenuation:  Attenuation for the source's verso side (default 0.85).

    Returns:
        Severity in [0.0, 1.0].
    """
    if folio_num == source_folio:
        return 1.0 if side == "r" else verso_attenuation

    dist = abs(folio_num - source_folio)
    severity = _EPICENTER_RECTO_SEVERITY * (decay_rate ** dist)
    return severity if severity >= _WATER_THRESHOLD else 0.0


# ---------------------------------------------------------------------------
# compute_edge_darkening
# ---------------------------------------------------------------------------

def compute_edge_darkening(folio_num: int, gathering_size: int) -> float:
    """Edge darkening intensity (TD-011 §2.2).

    Outermost leaves (1 and gathering_size) receive 0.9;
    the innermost leaf receives 0.6; linear interpolation between.

    Args:
        folio_num:      Leaf number (1-based).
        gathering_size: Total number of leaves in the gathering.

    Returns:
        Darkening intensity in [0.6, 0.9].
    """
    outer_dist = min(folio_num - 1, gathering_size - folio_num)  # 0 = outermost
    center = (gathering_size - 1) / 2.0
    frac = outer_dist / center if center > 0 else 0.0
    return round(0.9 - frac * 0.3, 6)   # 0.9 → 0.6


# ---------------------------------------------------------------------------
# generate_foxing_clusters
# ---------------------------------------------------------------------------

def generate_foxing_clusters(
    n_clusters: int,
    gathering_size: int,
    seed: int,
) -> dict[int, list[FoxingSpot]]:
    """Generate foxing clusters at seed-determined leaf positions (TD-011 §2.3).

    Each cluster spans 2-4 adjacent leaves. Recto positions are stored with
    positive leaf keys; verso positions are stored with negative leaf keys and
    have their x-coordinate mirrored: verso_x = 1.0 - recto_x.

    Args:
        n_clusters:     Number of clusters to generate.
        gathering_size: Total number of leaves in the gathering.
        seed:           RNG seed for deterministic placement.

    Returns:
        {leaf_key: [FoxingSpot, ...]} where leaf_key > 0 = recto, < 0 = verso.
    """
    rng = random.Random(seed)
    clusters: dict[int, list[FoxingSpot]] = {}

    for _ in range(n_clusters):
        center_leaf = rng.randint(1, gathering_size)
        span = rng.randint(2, 4)
        cx = rng.uniform(0.1, 0.9)
        cy = rng.uniform(0.1, 0.9)
        intensity = rng.uniform(0.3, 0.7)
        radius = rng.uniform(0.006, 0.015)

        for offset in range(span):
            leaf = center_leaf + offset
            if leaf > gathering_size:
                break
            spot_r = FoxingSpot(
                position=(cx + rng.gauss(0, 0.02), cy + rng.gauss(0, 0.02)),
                intensity=intensity * rng.uniform(0.8, 1.2),
                radius=radius * rng.uniform(0.8, 1.3),
            )
            # Verso: mirror x position (spine symmetry)
            spot_v = FoxingSpot(
                position=(1.0 - spot_r.position[0], spot_r.position[1]),
                intensity=spot_r.intensity * 0.9,
                radius=spot_r.radius,
            )
            clusters.setdefault(leaf, []).append(spot_r)
            clusters.setdefault(-leaf, []).append(spot_v)

    return clusters


# ---------------------------------------------------------------------------
# CLIO-7 merge helpers
# ---------------------------------------------------------------------------

_CLIO7_DEGRADATION_THRESHOLD = 0.8  # lines with confidence < this become zones


def _annotations_to_degradation_zone(
    line_num: int,
    annotations: list[dict],
    text: str,
) -> Optional[TextDegradationZone]:
    """Convert a line's annotations to a TextDegradationZone if warranted."""
    for ann in annotations:
        ann_type = ann.get("type", "")
        if ann_type == "lacuna":
            return TextDegradationZone(
                lines=(line_num, line_num),
                confidence=0.0,
                description=f"Lacuna at line {line_num}: {ann.get('detail', {}).get('note', 'text lost')}",
            )
        if ann_type == "confidence":
            score = float(ann.get("detail", {}).get("score", 1.0))
            if score < _CLIO7_DEGRADATION_THRESHOLD:
                cat = "trace" if score < 0.6 else "partial"
                return TextDegradationZone(
                    lines=(line_num, line_num),
                    confidence=score,
                    description=f"Line {line_num}: {cat} ({score:.2f}) — \"{text[:40]}\"",
                )
    return None


def _build_degradation_zones(
    folio_lines: list[dict],
) -> list[TextDegradationZone]:
    """Build TextDegradationZone list from XL per-folio line data."""
    zones: list[TextDegradationZone] = []
    for line in folio_lines:
        line_num = line.get("number", 0)
        annotations = line.get("annotations", [])
        text = line.get("text", "")
        zone = _annotations_to_degradation_zone(line_num, annotations, text)
        if zone is not None:
            zones.append(zone)
    return zones


def _load_clio7_from_path(clio7_path: Path) -> dict[str, list[dict]]:
    """Load CLIO-7 per-folio line annotations from XL manifest JSON.

    Expects the XL manifest format:
        {manifest: {...}, folios: [{id, file, ...}, ...]}
    where each folio file is a JSON with a `lines` list.

    Returns:
        {folio_id: [line_dict, ...]}
    """
    manifest_path = Path(clio7_path)
    manifest_dir = manifest_path.parent

    if not manifest_path.exists():
        return {}

    manifest = json.loads(manifest_path.read_text())
    result: dict[str, list[dict]] = {}

    for entry in manifest.get("folios", []):
        fid = entry.get("id")
        file_ref = entry.get("file")
        if not fid or not file_ref:
            continue
        folio_path = manifest_dir / file_ref
        if not folio_path.exists():
            continue
        try:
            folio_data = json.loads(folio_path.read_text())
            result[fid] = folio_data.get("lines", [])
        except (json.JSONDecodeError, OSError):
            continue

    return result


def _merge_clio7_annotations(
    weathering_map: dict[str, FolioWeatherSpec],
    clio7_annotations: dict[str, list[dict]],
) -> None:
    """Merge CLIO-7 line annotations into the weathering map in-place."""
    for fid, lines in clio7_annotations.items():
        if fid not in weathering_map:
            continue
        zones = _build_degradation_zones(lines)
        if zones:
            weathering_map[fid].text_degradation = zones


# ---------------------------------------------------------------------------
# compute_codex_weathering_map
# ---------------------------------------------------------------------------

def compute_codex_weathering_map(
    gathering_size: int = 17,
    seed: int = 1457,
    clio7_path: Optional[Path] = None,
    clio7_annotations: Optional[dict[str, list[dict]]] = None,
) -> dict[str, FolioWeatherSpec]:
    """Generate the complete codex weathering map (TD-011 Part 2).

    Args:
        gathering_size:    Number of leaves (default 17 → 34 folios).
        seed:              RNG seed for foxing cluster placement.
        clio7_path:        Path to XL manifest JSON for CLIO-7 annotation merging.
        clio7_annotations: Per-folio line annotation dict for direct injection
                           (used in tests; takes precedence over clio7_path).

    Returns:
        {folio_id: FolioWeatherSpec} for all 2×gathering_size folios.
        Output is byte-identical for the same arguments.
    """
    foxing_by_leaf = generate_foxing_clusters(_N_FOXING_CLUSTERS, gathering_size, seed)
    result: dict[str, FolioWeatherSpec] = {}

    for leaf in range(1, gathering_size + 1):
        for side in ("r", "v"):
            fid = f"f{leaf:02d}{side}"
            severity = compute_water_propagation(leaf, side)

            water_spec: Optional[WaterDamageSpec] = None
            if severity > 0.0:
                penetration = round(min(0.60, severity * 0.60), 3)
                water_spec = WaterDamageSpec(
                    severity=severity,
                    origin="top_right" if side == "r" else "top_left",
                    penetration=penetration,
                )

            # Missing corner: f04r (bottom-left) and f04v (bottom-right) only
            corner: Optional[MissingCornerSpec] = None
            if leaf == _EPICENTER_LEAF:
                corner = MissingCornerSpec(
                    corner="bottom_left" if side == "r" else "bottom_right",
                    depth_fraction=0.08,
                    width_fraction=0.07,
                )

            foxing_key = leaf if side == "r" else -leaf
            foxing_spots = foxing_by_leaf.get(foxing_key, [])

            result[fid] = FolioWeatherSpec(
                folio_id=fid,
                vellum_stock="irregular" if leaf >= 14 else "standard",
                edge_darkening=round(compute_edge_darkening(leaf, gathering_size), 3),
                gutter_side="left" if side == "r" else "right",
                water_damage=water_spec,
                missing_corner=corner,
                foxing_spots=foxing_spots,
            )

    # Merge CLIO-7 annotations if provided
    annotations: Optional[dict[str, list[dict]]] = clio7_annotations
    if annotations is None and clio7_path is not None:
        annotations = _load_clio7_from_path(Path(clio7_path))
    if annotations:
        _merge_clio7_annotations(result, annotations)

    return result


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _spec_to_dict(spec: FolioWeatherSpec) -> dict:
    return {
        "folio_id": spec.folio_id,
        "vellum_stock": spec.vellum_stock,
        "edge_darkening": spec.edge_darkening,
        "gutter_side": spec.gutter_side,
        "water_damage": (
            {
                "severity": spec.water_damage.severity,
                "origin": spec.water_damage.origin,
                "penetration": spec.water_damage.penetration,
            }
            if spec.water_damage
            else None
        ),
        "missing_corner": (
            {
                "corner": spec.missing_corner.corner,
                "depth_fraction": spec.missing_corner.depth_fraction,
                "width_fraction": spec.missing_corner.width_fraction,
            }
            if spec.missing_corner
            else None
        ),
        "foxing_spots": [
            {
                "position": list(s.position),
                "intensity": s.intensity,
                "radius": s.radius,
            }
            for s in spec.foxing_spots
        ],
        "text_degradation": (
            [
                {
                    "lines": list(z.lines),
                    "confidence": z.confidence,
                    "description": z.description,
                }
                for z in spec.text_degradation
            ]
            if spec.text_degradation
            else None
        ),
    }


def _dict_to_spec(d: dict) -> FolioWeatherSpec:
    wd = d.get("water_damage")
    mc = d.get("missing_corner")
    td = d.get("text_degradation")
    foxing = [
        FoxingSpot(
            position=tuple(s["position"]),
            intensity=s["intensity"],
            radius=s["radius"],
        )
        for s in d.get("foxing_spots", [])
    ]
    text_deg = (
        [
            TextDegradationZone(
                lines=tuple(z["lines"]),
                confidence=z["confidence"],
                description=z["description"],
            )
            for z in td
        ]
        if td
        else None
    )
    return FolioWeatherSpec(
        folio_id=d["folio_id"],
        vellum_stock=d["vellum_stock"],
        edge_darkening=d["edge_darkening"],
        gutter_side=d["gutter_side"],
        water_damage=(
            WaterDamageSpec(
                severity=wd["severity"],
                origin=wd["origin"],
                penetration=wd["penetration"],
            )
            if wd
            else None
        ),
        missing_corner=(
            MissingCornerSpec(
                corner=mc["corner"],
                depth_fraction=mc["depth_fraction"],
                width_fraction=mc["width_fraction"],
            )
            if mc
            else None
        ),
        foxing_spots=foxing,
        text_degradation=text_deg,
    )


def save_codex_map(
    weathering_map: dict[str, FolioWeatherSpec],
    output_path: Path | str,
) -> None:
    """Write codex map to JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {fid: _spec_to_dict(spec) for fid, spec in weathering_map.items()}
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load_codex_map(path: Path | str) -> dict[str, FolioWeatherSpec]:
    """Load codex map from JSON."""
    path = Path(path)
    data = json.loads(path.read_text())
    return {fid: _dict_to_spec(d) for fid, d in data.items()}
