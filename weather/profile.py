"""Load and expose the TD-001-E weathering profile TOML.

Public API:
    load_profile(toml_path=None) -> WeatheringProfile
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

_DEFAULT_PROFILE = (
    Path(__file__).parents[1] / "shared" / "profiles" / "ms-erfurt-560yr.toml"
)


# ---------------------------------------------------------------------------
# Sub-section dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SubstrateParams:
    texture_roughness: float = 0.25
    color_base: list = field(default_factory=lambda: [242, 228, 196])
    color_variation: float = 0.06
    translucency: float = 0.08


@dataclass
class InkFadeParams:
    enabled: bool = True
    target_hue_shift: float = 18.0
    lightness_increase: float = 0.22
    spatial_variance: float = 0.08


@dataclass
class InkBleedParams:
    enabled: bool = True
    radius_px: float = 1.8
    pressure_weighting: bool = True


@dataclass
class InkFlakeParams:
    enabled: bool = True
    flake_probability: float = 0.035
    flake_radius_px: float = 2.5
    seed_offset: int = 7


@dataclass
class WaterDamageParams:
    direction: str = "top"
    penetration: float = 0.38
    tide_line_opacity: float = 0.55
    tide_line_blur_px: float = 6.0
    ink_dissolution: float = 0.45
    stain_color: list = field(default_factory=lambda: [200, 185, 155])


@dataclass
class MissingCornerParams:
    corner: str = "lower_outer"
    tear_depth: float = 0.22
    irregularity: float = 0.6
    backing_color: list = field(default_factory=lambda: [255, 248, 235])


@dataclass
class EdgeDarkeningParams:
    enabled: bool = True
    width_fraction: float = 0.12
    opacity: float = 0.40
    color: list = field(default_factory=lambda: [160, 130, 90])


@dataclass
class FoxingParams:
    enabled: bool = True
    spot_density: float = 0.0012
    spot_radius_range: list = field(default_factory=lambda: [2, 8])
    spot_color: list = field(default_factory=lambda: [165, 115, 70])
    seed_offset: int = 13


@dataclass
class BindingShadowParams:
    enabled: bool = True
    width_fraction: float = 0.08
    opacity: float = 0.30
    gradient_type: str = "linear"


@dataclass
class PageCurlParams:
    enabled: bool = False
    curl_amount: float = 0.04
    corner: str = "lower_outer"


@dataclass
class CameraVignetteParams:
    enabled: bool = True
    strength: float = 0.18


@dataclass
class LightingGradientParams:
    enabled: bool = True
    direction: str = "top_left"
    strength: float = 0.10


# ---------------------------------------------------------------------------
# Top-level profile
# ---------------------------------------------------------------------------

@dataclass
class WeatheringProfile:
    name: str = ""
    description: str = ""
    seed: int = 1457
    age_years: int = 560
    target_manuscript: str = ""

    substrate_standard: SubstrateParams = field(default_factory=SubstrateParams)
    substrate_irregular: SubstrateParams = field(
        default_factory=lambda: SubstrateParams(
            texture_roughness=0.42,
            color_base=[235, 215, 178],
            color_variation=0.14,
            translucency=0.15,
        )
    )

    ink_fade: InkFadeParams = field(default_factory=InkFadeParams)
    ink_bleed: InkBleedParams = field(default_factory=InkBleedParams)
    ink_flake: InkFlakeParams = field(default_factory=InkFlakeParams)

    damage_water: WaterDamageParams = field(default_factory=WaterDamageParams)
    damage_missing_corner: MissingCornerParams = field(
        default_factory=MissingCornerParams
    )

    aging_edge: EdgeDarkeningParams = field(default_factory=EdgeDarkeningParams)
    aging_foxing: FoxingParams = field(default_factory=FoxingParams)
    aging_shadow: BindingShadowParams = field(default_factory=BindingShadowParams)

    optics_curl: PageCurlParams = field(default_factory=PageCurlParams)
    optics_vignette: CameraVignetteParams = field(default_factory=CameraVignetteParams)
    optics_lighting: LightingGradientParams = field(default_factory=LightingGradientParams)


def load_profile(toml_path: Path | None = None) -> WeatheringProfile:
    """Load a weathering profile from a TOML file (TD-001-E).

    Args:
        toml_path: Path to the TOML file. Defaults to shared/profiles/ms-erfurt-560yr.toml.

    Returns:
        WeatheringProfile populated from the TOML.

    Raises:
        FileNotFoundError: if the TOML file does not exist.
        ImportError: if tomllib is unavailable (Python < 3.11 without tomli).
    """
    if tomllib is None:
        raise ImportError("tomllib (Python 3.11+) or tomli required to load profiles")

    path = Path(toml_path) if toml_path else _DEFAULT_PROFILE
    if not path.exists():
        raise FileNotFoundError(
            f"Weathering profile not found: {path}\n"
            "Expected shared/profiles/ms-erfurt-560yr.toml (TD-001-E)"
        )

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    meta = raw.get("meta", {})
    profile = WeatheringProfile(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        seed=meta.get("seed", 1457),
        age_years=meta.get("age_years", 560),
        target_manuscript=meta.get("target_manuscript", ""),
    )

    if "substrate" in raw:
        sub = raw["substrate"]
        if "vellum_standard" in sub:
            s = sub["vellum_standard"]
            profile.substrate_standard = SubstrateParams(
                texture_roughness=s.get("texture_roughness", 0.25),
                color_base=s.get("color_base", [242, 228, 196]),
                color_variation=s.get("color_variation", 0.06),
                translucency=s.get("translucency", 0.08),
            )
        if "vellum_irregular" in sub:
            s = sub["vellum_irregular"]
            profile.substrate_irregular = SubstrateParams(
                texture_roughness=s.get("texture_roughness", 0.42),
                color_base=s.get("color_base", [235, 215, 178]),
                color_variation=s.get("color_variation", 0.14),
                translucency=s.get("translucency", 0.15),
            )

    if "ink" in raw:
        ink = raw["ink"]
        if "fade" in ink:
            fd = ink["fade"]
            profile.ink_fade = InkFadeParams(
                enabled=fd.get("enabled", True),
                target_hue_shift=fd.get("target_hue_shift", 18.0),
                lightness_increase=fd.get("lightness_increase", 0.22),
                spatial_variance=fd.get("spatial_variance", 0.08),
            )
        if "bleed" in ink:
            bl = ink["bleed"]
            profile.ink_bleed = InkBleedParams(
                enabled=bl.get("enabled", True),
                radius_px=bl.get("radius_px", 1.8),
                pressure_weighting=bl.get("pressure_weighting", True),
            )
        if "flake" in ink:
            fl = ink["flake"]
            profile.ink_flake = InkFlakeParams(
                enabled=fl.get("enabled", True),
                flake_probability=fl.get("flake_probability", 0.035),
                flake_radius_px=fl.get("flake_radius_px", 2.5),
                seed_offset=fl.get("seed_offset", 7),
            )

    if "damage" in raw:
        dmg = raw["damage"]
        if "water_damage" in dmg:
            wd = dmg["water_damage"]
            profile.damage_water = WaterDamageParams(
                direction=wd.get("direction", "top"),
                penetration=wd.get("penetration", 0.38),
                tide_line_opacity=wd.get("tide_line_opacity", 0.55),
                tide_line_blur_px=wd.get("tide_line_blur_px", 6.0),
                ink_dissolution=wd.get("ink_dissolution", 0.45),
                stain_color=wd.get("stain_color", [200, 185, 155]),
            )
        if "missing_corner" in dmg:
            mc = dmg["missing_corner"]
            profile.damage_missing_corner = MissingCornerParams(
                corner=mc.get("corner", "lower_outer"),
                tear_depth=mc.get("tear_depth", 0.22),
                irregularity=mc.get("irregularity", 0.6),
                backing_color=mc.get("backing_color", [255, 248, 235]),
            )

    if "aging" in raw:
        ag = raw["aging"]
        if "edge_darkening" in ag:
            ed = ag["edge_darkening"]
            profile.aging_edge = EdgeDarkeningParams(
                enabled=ed.get("enabled", True),
                width_fraction=ed.get("width_fraction", 0.12),
                opacity=ed.get("opacity", 0.40),
                color=ed.get("color", [160, 130, 90]),
            )
        if "foxing" in ag:
            fx = ag["foxing"]
            profile.aging_foxing = FoxingParams(
                enabled=fx.get("enabled", True),
                spot_density=fx.get("spot_density", 0.0012),
                spot_radius_range=fx.get("spot_radius_range", [2, 8]),
                spot_color=fx.get("spot_color", [165, 115, 70]),
                seed_offset=fx.get("seed_offset", 13),
            )
        if "binding_shadow" in ag:
            bs = ag["binding_shadow"]
            profile.aging_shadow = BindingShadowParams(
                enabled=bs.get("enabled", True),
                width_fraction=bs.get("width_fraction", 0.08),
                opacity=bs.get("opacity", 0.30),
                gradient_type=bs.get("gradient_type", "linear"),
            )

    if "optics" in raw:
        opt = raw["optics"]
        if "page_curl" in opt:
            pc = opt["page_curl"]
            profile.optics_curl = PageCurlParams(
                enabled=pc.get("enabled", False),
                curl_amount=pc.get("curl_amount", 0.04),
                corner=pc.get("corner", "lower_outer"),
            )
        if "camera_vignette" in opt:
            cv = opt["camera_vignette"]
            profile.optics_vignette = CameraVignetteParams(
                enabled=cv.get("enabled", True),
                strength=cv.get("strength", 0.18),
            )
        if "lighting_gradient" in opt:
            lg = opt["lighting_gradient"]
            profile.optics_lighting = LightingGradientParams(
                enabled=lg.get("enabled", True),
                direction=lg.get("direction", "top_left"),
                strength=lg.get("strength", 0.10),
            )

    return profile
