"""HandProfile — scale-based parameter architecture (TD-002/TD-003).

Replaces the flat HandParams with a hierarchical ~45-parameter system
organized by scale: folio, line, word, glyph, nib, ink, material.

Each parameter has a range (min, max) and unit for validation and tuning.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, fields, asdict
from pathlib import Path
from typing import Any

from scribesim.hand.params import HandParams

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Scale-level parameter groups
# ---------------------------------------------------------------------------

@dataclass
class FolioParams:
    """Page-level posture and global settings."""
    page_rotation_deg: float = 0.0
    ruling_slope_variance: float = 0.003
    ruling_spacing_variance_mm: float = 0.5
    margin_left_variance_mm: float = 0.3
    base_pressure: float = 0.72
    base_tempo: float = 3.0
    tremor_amplitude: float = 0.0
    lines_per_page: int = 30


@dataclass
class LineParams:
    """Per-line trajectory parameters."""
    start_x_variance_mm: float = 0.3
    baseline_undulation_amplitude_mm: float = 0.2
    baseline_undulation_period_ratio: float = 0.5
    margin_compression_zone_ratio: float = 0.85
    line_spacing_mean_mm: float = 8.0
    line_spacing_variance_mm: float = 0.3


@dataclass
class WordParams:
    """Word-level envelope and spacing."""
    spacing_mean_ratio: float = 1.2
    spacing_variance_ratio: float = 0.15
    slant_drift_per_word_deg: float = 0.3
    speed_variance: float = 0.1
    post_punctuation_space_multiplier: float = 1.4
    slant_reset_at_line_start: bool = True


@dataclass
class GlyphParams:
    """Per-glyph shape variation."""
    size_variance: float = 0.02
    warp_amplitude_mm: float = 0.1
    warp_correlation: float = 0.7
    ascender_extra_variance: float = 1.5
    descender_extra_variance: float = 1.5
    baseline_jitter_mm: float = 0.05
    connection_lift_height_mm: float = 1.5
    entry_angle_adaptation: float = 0.7


@dataclass
class NibParams:
    """Physical nib properties."""
    width_mm: float = 1.8
    angle_deg: float = 40.0
    flexibility: float = 0.15
    cut_quality: float = 0.9
    attack_pressure_multiplier: float = 1.15
    release_taper_length: float = 0.3


@dataclass
class InkParams:
    """Ink reservoir and depletion model."""
    reservoir_capacity: float = 1.0
    depletion_rate: float = 0.02
    fresh_dip_darkness_boost: float = 0.15
    dry_threshold: float = 0.15
    raking_threshold: float = 0.08
    base_color_r: int = 45
    base_color_g: int = 35
    base_color_b: int = 25


@dataclass
class MaterialParams:
    """Vellum-ink interaction properties."""
    edge_feather_mm: float = 0.05
    grain_spread_factor: float = 0.1
    pooling_at_direction_change: float = 0.2
    overlap_darkening_factor: float = 0.7
    stroke_start_blob_size: float = 0.1


@dataclass
class DynamicsParams:
    """Hand simulator dynamics (TD-006 PD controller)."""
    # Legacy attractor params (kept for fallback)
    attraction_strength: float = 18.0
    damping_coefficient: float = 6.0
    lookahead_strength: float = 0.5
    max_speed: float = 40.0
    rhythm_strength: float = 0.1
    target_radius_mm: float = 0.15
    contact_threshold: float = 0.08
    word_lift_height_mm: float = 5.0
    # PD controller params (TD-006 Phase 2)
    position_gain: float = 20.0       # proportional correction strength
    velocity_gain: float = 8.0        # derivative correction strength
    max_acceleration: float = 500.0   # biomechanical limit (mm/s²)
    use_pd_controller: bool = True    # True = PD, False = legacy attractor


@dataclass
class LetterformParams:
    """Letterform guide proportions (TD-005)."""
    keypoint_flexibility_mm: float = 0.2
    ascender_height_ratio: float = 1.6
    descender_depth_ratio: float = 0.5
    x_height_mm: float = 3.0


@dataclass
class StrokeEffectParams:
    """Stroke foot/attack effects (TD-004)."""
    foot_width_boost: float = 0.20
    foot_ink_boost: float = 0.25
    foot_zone_start: float = 0.85
    attack_width_boost: float = 0.10
    attack_zone_end: float = 0.10
    pressure_modulation_range: float = 0.4


# ---------------------------------------------------------------------------
# Parameter range metadata
# ---------------------------------------------------------------------------

# { "scale.field": (min, max) } — used for validation and optimizer step sizing
_RANGES: dict[str, tuple[float, float]] = {
    # Folio
    "folio.page_rotation_deg": (-1.0, 1.0),
    "folio.ruling_slope_variance": (0.0, 0.01),
    "folio.ruling_spacing_variance_mm": (0.0, 2.0),
    "folio.margin_left_variance_mm": (0.0, 1.0),
    "folio.base_pressure": (0.3, 1.0),
    "folio.base_tempo": (1.0, 6.0),
    "folio.tremor_amplitude": (0.0, 0.02),
    "folio.lines_per_page": (24, 38),
    # Line
    "line.start_x_variance_mm": (0.0, 1.5),
    "line.baseline_undulation_amplitude_mm": (0.0, 0.8),
    "line.baseline_undulation_period_ratio": (0.2, 1.0),
    "line.margin_compression_zone_ratio": (0.7, 0.95),
    "line.line_spacing_mean_mm": (5.0, 12.0),
    "line.line_spacing_variance_mm": (0.0, 1.0),
    # Word
    "word.spacing_mean_ratio": (0.6, 2.0),
    "word.spacing_variance_ratio": (0.0, 0.5),
    "word.slant_drift_per_word_deg": (0.0, 1.5),
    "word.speed_variance": (0.0, 0.3),
    "word.post_punctuation_space_multiplier": (1.0, 2.5),
    # Glyph
    "glyph.size_variance": (0.0, 0.08),
    "glyph.warp_amplitude_mm": (0.0, 0.4),
    "glyph.warp_correlation": (0.0, 1.0),
    "glyph.ascender_extra_variance": (1.0, 3.0),
    "glyph.descender_extra_variance": (1.0, 3.0),
    "glyph.baseline_jitter_mm": (0.0, 0.2),
    "glyph.connection_lift_height_mm": (0.5, 4.0),
    "glyph.entry_angle_adaptation": (0.0, 1.0),
    # Nib
    "nib.width_mm": (0.8, 3.0),
    "nib.angle_deg": (25.0, 55.0),
    "nib.flexibility": (0.0, 0.5),
    "nib.cut_quality": (0.5, 1.0),
    "nib.attack_pressure_multiplier": (1.0, 1.5),
    "nib.release_taper_length": (0.0, 0.8),
    # Ink
    "ink.reservoir_capacity": (0.5, 1.5),
    "ink.depletion_rate": (0.005, 0.05),
    "ink.fresh_dip_darkness_boost": (0.0, 0.4),
    "ink.dry_threshold": (0.05, 0.3),
    "ink.raking_threshold": (0.02, 0.15),
    "ink.base_color_r": (0, 80),
    "ink.base_color_g": (0, 60),
    "ink.base_color_b": (0, 40),
    # Material
    "material.edge_feather_mm": (0.0, 0.2),
    "material.grain_spread_factor": (0.0, 0.4),
    "material.pooling_at_direction_change": (0.0, 0.6),
    "material.overlap_darkening_factor": (0.3, 1.0),
    "material.stroke_start_blob_size": (0.0, 0.3),
    # Dynamics (TD-005)
    "dynamics.attraction_strength": (1.0, 20.0),
    "dynamics.damping_coefficient": (0.5, 8.0),
    "dynamics.lookahead_strength": (0.0, 5.0),
    "dynamics.max_speed": (30.0, 200.0),
    "dynamics.rhythm_strength": (0.0, 1.0),
    "dynamics.target_radius_mm": (0.1, 1.0),
    "dynamics.contact_threshold": (0.05, 0.5),
    "dynamics.word_lift_height_mm": (1.0, 8.0),
    "dynamics.position_gain": (5.0, 50.0),
    "dynamics.velocity_gain": (2.0, 20.0),
    "dynamics.max_acceleration": (100.0, 2000.0),
    # Letterform (TD-005)
    "letterform.keypoint_flexibility_mm": (0.05, 0.6),
    "letterform.ascender_height_ratio": (1.2, 2.2),
    "letterform.descender_depth_ratio": (0.3, 1.0),
    "letterform.x_height_mm": (1.5, 5.0),
    # Stroke effects (TD-004)
    "stroke.foot_width_boost": (0.0, 0.4),
    "stroke.foot_ink_boost": (0.0, 0.5),
    "stroke.foot_zone_start": (0.75, 0.95),
    "stroke.attack_width_boost": (0.0, 0.25),
    "stroke.attack_zone_end": (0.05, 0.20),
    "stroke.pressure_modulation_range": (0.1, 0.8),
}


# ---------------------------------------------------------------------------
# HandProfile — top-level composition
# ---------------------------------------------------------------------------

_SCALE_CLASSES = {
    "folio": FolioParams,
    "line": LineParams,
    "word": WordParams,
    "glyph": GlyphParams,
    "nib": NibParams,
    "dynamics": DynamicsParams,
    "letterform": LetterformParams,
    "stroke": StrokeEffectParams,
    "ink": InkParams,
    "material": MaterialParams,
}


@dataclass
class HandProfile:
    """Hierarchical hand parameter profile (TD-002 / TD-003).

    Composes seven scale-level parameter groups plus metadata.
    """
    # Scale groups
    folio: FolioParams = None  # type: ignore[assignment]
    line: LineParams = None  # type: ignore[assignment]
    word: WordParams = None  # type: ignore[assignment]
    glyph: GlyphParams = None  # type: ignore[assignment]
    nib: NibParams = None  # type: ignore[assignment]
    ink: InkParams = None  # type: ignore[assignment]
    material: MaterialParams = None  # type: ignore[assignment]
    dynamics: DynamicsParams = None  # type: ignore[assignment]
    letterform: LetterformParams = None  # type: ignore[assignment]
    stroke: StrokeEffectParams = None  # type: ignore[assignment]

    # Metadata (not tunable)
    script: str = "bastarda"
    dialect_region: str = "thuringian"
    date_approx: int = 1457

    # V1 compatibility fields (used by existing layout/render)
    pressure_upstroke: float = 0.28
    pressure_variance: float = 0.08
    ink_density: float = 0.85
    ink_bleed_radius_px: float = 1.2
    stroke_weight: float = 1.0
    letter_spacing_norm: float = 1.0
    word_spacing_norm: float = 2.4
    line_height_norm: float = 2.5
    x_height_px: int = 38
    writing_speed: float = 1.0
    fatigue_rate: float = 0.0
    slant_deg: float = 3.5

    def __post_init__(self) -> None:
        if self.folio is None:
            self.folio = FolioParams()
        if self.line is None:
            self.line = LineParams()
        if self.word is None:
            self.word = WordParams()
        if self.glyph is None:
            self.glyph = GlyphParams()
        if self.nib is None:
            self.nib = NibParams()
        if self.ink is None:
            self.ink = InkParams()
        if self.material is None:
            self.material = MaterialParams()
        if self.dynamics is None:
            self.dynamics = DynamicsParams()
        if self.letterform is None:
            self.letterform = LetterformParams()
        if self.stroke is None:
            self.stroke = StrokeEffectParams()

    # ------------------------------------------------------------------
    # V1 compatibility
    # ------------------------------------------------------------------

    def to_v1(self) -> HandParams:
        """Produce a v1 HandParams for backward-compatible callsites.

        Maps scale-based parameters back to the flat HandParams structure
        that layout/placer.py and render/rasteriser.py expect.
        """
        return HandParams(
            nib_angle_deg=self.nib.angle_deg,
            nib_width_mm=self.nib.width_mm,
            stroke_weight=self.stroke_weight,
            pressure_base=self.folio.base_pressure,
            pressure_upstroke=self.pressure_upstroke,
            pressure_variance=self.pressure_variance,
            ink_density=self.ink_density,
            ink_bleed_radius_px=self.ink_bleed_radius_px,
            letter_spacing_norm=self.letter_spacing_norm,
            word_spacing_norm=self.word_spacing_norm,
            line_height_norm=self.line_height_norm,
            x_height_px=self.x_height_px,
            writing_speed=self.writing_speed,
            fatigue_rate=self.fatigue_rate,
            tremor_amplitude=self.folio.tremor_amplitude,
            slant_deg=self.slant_deg,
            script=self.script,
            dialect_region=self.dialect_region,
            date_approx=self.date_approx,
        )

    # ------------------------------------------------------------------
    # Delta application
    # ------------------------------------------------------------------

    def apply_delta(self, delta: dict) -> HandProfile:
        """Return a new HandProfile with delta values overlaid.

        Delta keys can be:
        - Flat v1 keys: "pressure_base", "ink_density", etc.
        - Dotted scale keys: "nib.angle_deg", "folio.tremor_amplitude"
        """
        new = copy.deepcopy(self)

        for key, val in delta.items():
            if "." in key:
                # Dotted scale path: "nib.angle_deg" -> new.nib.angle_deg
                scale_name, field_name = key.split(".", 1)
                scale_obj = getattr(new, scale_name, None)
                if scale_obj is not None and hasattr(scale_obj, field_name):
                    setattr(scale_obj, field_name, val)
            else:
                # Flat v1 key — apply to the appropriate place
                _apply_v1_key(new, key, val)

        return new

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_flat_dict(self) -> dict:
        """Flat dict of all scale parameters for display."""
        result = {}
        for scale_name in _SCALE_CLASSES:
            scale_obj = getattr(self, scale_name)
            for f in fields(scale_obj):
                result[f"{scale_name}.{f.name}"] = getattr(scale_obj, f.name)
        # Metadata
        result["script"] = self.script
        result["dialect_region"] = self.dialect_region
        result["date_approx"] = self.date_approx
        # V1 compat fields (still consumed by layout/render)
        result["v1.pressure_base"] = self.folio.base_pressure
        result["v1.pressure_upstroke"] = self.pressure_upstroke
        result["v1.pressure_variance"] = self.pressure_variance
        result["v1.ink_density"] = self.ink_density
        result["v1.ink_bleed_radius_px"] = self.ink_bleed_radius_px
        result["v1.stroke_weight"] = self.stroke_weight
        result["v1.letter_spacing_norm"] = self.letter_spacing_norm
        result["v1.word_spacing_norm"] = self.word_spacing_norm
        result["v1.line_height_norm"] = self.line_height_norm
        result["v1.x_height_px"] = self.x_height_px
        result["v1.writing_speed"] = self.writing_speed
        result["v1.fatigue_rate"] = self.fatigue_rate
        result["v1.slant_deg"] = self.slant_deg
        result["v1.tremor_amplitude"] = self.folio.tremor_amplitude
        result["v1.nib_angle_deg"] = self.nib.angle_deg
        result["v1.nib_width_mm"] = self.nib.width_mm
        return result


def _apply_v1_key(profile: HandProfile, key: str, val: Any) -> None:
    """Map a flat v1 TOML key to the appropriate field on HandProfile."""
    # Direct v1 compat fields
    v1_direct = {
        "pressure_upstroke", "pressure_variance", "ink_density",
        "ink_bleed_radius_px", "stroke_weight", "letter_spacing_norm",
        "word_spacing_norm", "line_height_norm", "x_height_px",
        "writing_speed", "fatigue_rate", "slant_deg",
        "script", "dialect_region", "date_approx",
    }
    # v1 keys that map to scale fields
    v1_to_scale = {
        "nib_angle_deg": ("nib", "angle_deg"),
        "nib_width_mm": ("nib", "width_mm"),
        "pressure_base": ("folio", "base_pressure"),
        "tremor_amplitude": ("folio", "tremor_amplitude"),
    }

    if key in v1_to_scale:
        scale_name, field_name = v1_to_scale[key]
        setattr(getattr(profile, scale_name), field_name, val)
        # Also update compat field if it exists
        if key == "pressure_base":
            pass  # no compat field; it's on folio
        elif key == "tremor_amplitude":
            pass  # no compat field; it's on folio
    if key in v1_direct:
        setattr(profile, key, val)


# ---------------------------------------------------------------------------
# TOML loading
# ---------------------------------------------------------------------------

def load_profile(toml_path: Path | None = None) -> HandProfile:
    """Load a HandProfile from TOML.

    Supports both v2 (scale-based sections) and v1 (flat [hand] section).
    Auto-detects format by checking for [folio], [nib], etc. sections.
    """
    default_path = Path(__file__).parents[2] / "shared" / "hands" / "konrad_erfurt_1457.toml"
    path = Path(toml_path) if toml_path else default_path
    if tomllib is None:
        raise ImportError("tomllib (Python 3.11+) or tomli required")
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    # Detect format: v2 has scale sections at top level
    is_v2 = any(k in raw for k in _SCALE_CLASSES)

    if is_v2:
        return _load_v2(raw)
    else:
        return _load_v1(raw)


def _load_v2(raw: dict) -> HandProfile:
    """Load from v2 scale-based TOML format."""
    kwargs: dict[str, Any] = {}

    for scale_name, cls in _SCALE_CLASSES.items():
        section = raw.get(scale_name, {})
        # Filter to known fields only
        known = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in section.items() if k in known}
        kwargs[scale_name] = cls(**filtered)

    # Metadata
    meta = raw.get("metadata", {})
    if "script" in meta:
        kwargs["script"] = meta["script"]
    if "dialect_region" in meta:
        kwargs["dialect_region"] = meta["dialect_region"]
    if "date_approx" in meta:
        kwargs["date_approx"] = meta["date_approx"]

    # V1 compat fields from [compat] section if present
    compat = raw.get("compat", {})
    for key in ("pressure_upstroke", "pressure_variance", "ink_density",
                "ink_bleed_radius_px", "stroke_weight", "letter_spacing_norm",
                "word_spacing_norm", "line_height_norm", "x_height_px",
                "writing_speed", "fatigue_rate", "slant_deg"):
        if key in compat:
            kwargs[key] = compat[key]

    return HandProfile(**kwargs)


def _load_v1(raw: dict) -> HandProfile:
    """Load from v1 flat [hand] TOML format and map to HandProfile."""
    hand = raw.get("hand", {})
    profile = HandProfile()

    # Map every v1 key
    for key, val in hand.items():
        _apply_v1_key(profile, key, val)

    return profile


# ---------------------------------------------------------------------------
# Modifier resolution
# ---------------------------------------------------------------------------

def resolve_profile(base: HandProfile, folio_id: str,
                    toml_path: Path | None = None) -> HandProfile:
    """Apply folio-specific TOML modifiers to a HandProfile.

    Loads [modifiers.<key>] section from the TOML and applies as a delta.
    """
    default_path = Path(__file__).parents[2] / "shared" / "hands" / "konrad_erfurt_1457.toml"
    path = Path(toml_path) if toml_path else default_path
    if tomllib is None:
        raise ImportError("tomllib (Python 3.11+) or tomli required")
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    raw_modifiers = raw.get("modifiers", {})

    # Normalise folio key: "f01r" → "01r", also try full id
    folio_key = folio_id.lstrip("f")
    delta = raw_modifiers.get(folio_key) or raw_modifiers.get(folio_id) or {}

    return base.apply_delta(delta)


# ---------------------------------------------------------------------------
# --set override parsing
# ---------------------------------------------------------------------------

def parse_overrides(overrides: list[str]) -> dict[str, Any]:
    """Parse CLI --set arguments into a delta dict.

    Args:
        overrides: list of "key=value" strings, e.g. ["nib.angle_deg=38"]

    Returns:
        dict mapping keys to parsed values.

    Raises:
        ValueError: if an override string is malformed.
    """
    result: dict[str, Any] = {}
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Invalid --set format: {item!r} (expected key=value)")
        key, val_str = item.split("=", 1)
        key = key.strip()
        val_str = val_str.strip()

        # Type inference
        if val_str.lower() in ("true", "false"):
            result[key] = val_str.lower() == "true"
        else:
            try:
                # Try int first, then float, then string
                if "." in val_str:
                    result[key] = float(val_str)
                else:
                    result[key] = int(val_str)
            except ValueError:
                result[key] = val_str

    return result


def validate_ranges(profile: HandProfile) -> list[str]:
    """Check all parameters against their defined ranges.

    Returns a list of error messages (empty if all valid).
    """
    errors: list[str] = []
    for key, (lo, hi) in _RANGES.items():
        scale_name, field_name = key.split(".", 1)
        scale_obj = getattr(profile, scale_name, None)
        if scale_obj is None:
            continue
        val = getattr(scale_obj, field_name, None)
        if val is None:
            continue
        if isinstance(val, bool):
            continue
        if val < lo or val > hi:
            errors.append(f"{key}={val} out of range [{lo}, {hi}]")
    return errors
