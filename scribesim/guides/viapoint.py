"""Declarative nib-normalized Via-Point recipes for Bastarda letters (TD-019 Pillar 2).

All spatial coordinates (x_wnib, y_wnib) and tolerance standard deviations
(sigma_x_wnib, sigma_y_wnib) are expressed in multiples of the physical broad-nib
width w_nib (where x_height H = 4.2 * w_nib).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ViaPoint:
    """A kinematic target point with spatial tolerance covariance Sigma_k."""

    x_wnib: float
    y_wnib: float
    sigma_x_wnib: float = 0.04
    sigma_y_wnib: float = 0.04
    vx_pref_wnib: float | None = None
    vy_pref_wnib: float | None = None
    velocity_weight: float = 0.0
    contact: bool = True
    pressure: float = 0.78
    role: str = "body"  # "entry", "body", "turn", "peak", "loop", "exit"


@dataclass(frozen=True)
class ViaPointRecipe:
    """Sequence of via-points defining a letter allograph in w_nib units."""

    letter: str
    via_points: tuple[ViaPoint, ...]
    advance_wnib: float
    ascender: bool = False
    descender: bool = False
    variants: dict[str, tuple[ViaPoint, ...]] = field(default_factory=dict)


_V = ViaPoint


def _build_starter_catalog() -> dict[str, ViaPointRecipe]:
    """Construct the starter Bastarda inventory: i, n, u, m, d, e, r.

    x_height H = 4.2 w_nib; interior minim counter ≈ 1.2 w_nib;
    40° hairline joins rise with dy/dx = tan(40°) ≈ 0.84.
    """
    cat: dict[str, ViaPointRecipe] = {}

    # i — single minim + 40° hairline exit turn
    cat["i"] = ViaPointRecipe(
        letter="i",
        via_points=(
            _V(0.05, 4.15, sigma_x_wnib=0.16, sigma_y_wnib=0.18, pressure=0.72, role="entry"),
            _V(0.08, 2.20, sigma_x_wnib=0.02, sigma_y_wnib=0.04, pressure=0.82, role="body"),
            _V(0.12, 0.10, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.78, role="turn"),
            _V(0.95, 0.80, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.28, role="exit"),
        ),
        advance_wnib=1.45,
    )

    # n — minim 1 -> 40° upstroke arch -> minim 2 -> 40° exit foot
    cat["n"] = ViaPointRecipe(
        letter="n",
        via_points=(
            _V(0.05, 4.15, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.74, role="entry"),
            _V(0.08, 2.10, sigma_x_wnib=0.015, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(0.12, 0.08, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.76, role="turn"),
            _V(1.15, 0.95, sigma_x_wnib=0.06, sigma_y_wnib=0.08, pressure=0.28, role="peak"),
            _V(1.30, 4.10, sigma_x_wnib=0.05, sigma_y_wnib=0.06, pressure=0.68, role="peak"),
            _V(1.34, 2.10, sigma_x_wnib=0.02, sigma_y_wnib=0.03, pressure=0.82, role="body"),
            _V(1.38, 0.08, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.75, role="turn"),
            _V(2.25, 0.82, sigma_x_wnib=0.22, sigma_y_wnib=0.26, pressure=0.28, role="exit"),
        ),
        advance_wnib=2.55,
    )

    # u — minim 1 -> baseline underturn + 40° rise -> minim 2 -> 40° exit foot
    cat["u"] = ViaPointRecipe(
        letter="u",
        via_points=(
            _V(0.05, 4.18, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.72, role="entry"),
            _V(0.09, 2.10, sigma_x_wnib=0.02, sigma_y_wnib=0.03, pressure=0.84, role="body"),
            _V(0.15, 0.08, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.72, role="turn"),
            _V(1.25, 1.00, sigma_x_wnib=0.06, sigma_y_wnib=0.08, pressure=0.28, role="turn"),
            _V(1.32, 4.15, sigma_x_wnib=0.05, sigma_y_wnib=0.06, pressure=0.74, role="peak"),
            _V(1.36, 2.10, sigma_x_wnib=0.02, sigma_y_wnib=0.03, pressure=0.82, role="body"),
            _V(1.40, 0.08, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.75, role="turn"),
            _V(2.25, 0.82, sigma_x_wnib=0.22, sigma_y_wnib=0.26, pressure=0.28, role="exit"),
        ),
        advance_wnib=2.55,
    )

    # m — three minims connected by two 40° arches; starts with a lower rising approach
    cat["m"] = ViaPointRecipe(
        letter="m",
        via_points=(
            _V(0.00, 2.35, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.32, role="entry"),
            _V(0.12, 4.15, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.74, role="peak"),
            _V(0.15, 2.10, sigma_x_wnib=0.02, sigma_y_wnib=0.03, pressure=0.84, role="body"),
            _V(0.18, 0.08, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(1.20, 0.94, sigma_x_wnib=0.06, sigma_y_wnib=0.08, pressure=0.28, role="peak"),
            _V(1.35, 4.10, sigma_x_wnib=0.05, sigma_y_wnib=0.06, pressure=0.72, role="peak"),
            _V(1.38, 2.10, sigma_x_wnib=0.02, sigma_y_wnib=0.03, pressure=0.82, role="body"),
            _V(1.42, 0.08, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(2.42, 0.94, sigma_x_wnib=0.06, sigma_y_wnib=0.08, pressure=0.28, role="peak"),
            _V(2.58, 4.10, sigma_x_wnib=0.05, sigma_y_wnib=0.06, pressure=0.72, role="peak"),
            _V(2.62, 2.10, sigma_x_wnib=0.02, sigma_y_wnib=0.03, pressure=0.82, role="body"),
            _V(2.66, 0.08, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.75, role="turn"),
            _V(3.50, 0.80, sigma_x_wnib=0.22, sigma_y_wnib=0.26, pressure=0.28, role="exit"),
        ),
        advance_wnib=3.80,
    )

    # d — bowl + Bastarda looped ascender + descending stem + exit turn
    cat["d"] = ViaPointRecipe(
        letter="d",
        via_points=(
            _V(1.10, 3.40, sigma_x_wnib=0.18, sigma_y_wnib=0.20, pressure=0.42, role="entry"),
            _V(0.15, 2.60, sigma_x_wnib=0.03, sigma_y_wnib=0.04, pressure=0.82, role="body"),
            _V(0.18, 0.12, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.78, role="turn"),
            _V(1.25, 1.05, sigma_x_wnib=0.06, sigma_y_wnib=0.08, pressure=0.28, role="turn"),
            _V(1.55, 6.50, sigma_x_wnib=0.10, sigma_y_wnib=0.12, pressure=0.35, role="loop"),
            _V(1.28, 6.80, sigma_x_wnib=0.10, sigma_y_wnib=0.12, pressure=0.68, role="loop"),
            _V(1.35, 2.20, sigma_x_wnib=0.02, sigma_y_wnib=0.03, pressure=0.85, role="body"),
            _V(1.40, 0.08, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(2.22, 0.78, sigma_x_wnib=0.22, sigma_y_wnib=0.26, pressure=0.28, role="exit"),
        ),
        advance_wnib=2.50,
        ascender=True,
    )

    # e — mid-entry -> top eye loop -> left bowl descent -> baseline turn -> 40° exit
    cat["e"] = ViaPointRecipe(
        letter="e",
        via_points=(
            _V(0.20, 2.20, sigma_x_wnib=0.18, sigma_y_wnib=0.22, pressure=0.32, role="entry"),
            _V(1.15, 3.05, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.30, role="loop"),
            _V(0.95, 4.10, sigma_x_wnib=0.05, sigma_y_wnib=0.05, pressure=0.68, role="peak"),
            _V(0.12, 2.20, sigma_x_wnib=0.02, sigma_y_wnib=0.03, pressure=0.84, role="body"),
            _V(0.18, 0.08, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(1.35, 0.90, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.28, role="exit"),
        ),
        advance_wnib=1.70,
    )

    # r — minim stem + 40° hairline rise + Bastarda shoulder + exit
    cat["r"] = ViaPointRecipe(
        letter="r",
        via_points=(
            _V(0.05, 4.15, sigma_x_wnib=0.16, sigma_y_wnib=0.18, pressure=0.74, role="entry"),
            _V(0.08, 2.10, sigma_x_wnib=0.02, sigma_y_wnib=0.03, pressure=0.84, role="body"),
            _V(0.12, 0.08, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(1.05, 0.88, sigma_x_wnib=0.06, sigma_y_wnib=0.08, pressure=0.28, role="turn"),
            _V(1.18, 4.10, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.68, role="peak"),
            _V(1.65, 3.45, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.30, role="exit"),
        ),
        advance_wnib=1.85,
    )

    return cat


VIAPOINT_STARTER_CATALOG: dict[str, ViaPointRecipe] = _build_starter_catalog()


def lookup_viapoint_recipe(letter: str) -> ViaPointRecipe:
    """Return the ViaPointRecipe for `letter` (falls back to 'n' only if unknown before ADV-SS-GUIDES-002)."""
    if letter in VIAPOINT_STARTER_CATALOG:
        return VIAPOINT_STARTER_CATALOG[letter]
    raise KeyError(f"ViaPointRecipe for {letter!r} not in starter catalog")
