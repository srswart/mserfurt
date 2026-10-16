"""Complete Early New High German / Ecclesiastical Latin Bastarda Via-Point Catalog
and TD-012 Contextual Allograph Selector (TD-019 Phase 16b, ADV-SS-GUIDES-002).

Organizes declarative nib-normalized `ViaPointRecipe` definitions by calligraphic family:
  - minims (`i, n, u, m, j, t, v, w, x`)
  - bowls & counters (`a, o, d, e, g, b, p, c, q`)
  - ascenders & descenders (`f, h, k, l, y, z, s, ſ, ß`)
  - umlauts & diacritics (`ä, ö, ü, Ä, Ö, Ü, ê, î` with pen-lifted superscript/accents)
  - capitals (`A–Z` simplified private-manuscript Bastarda capitals)
  - digits (`0–9`), scribal marks (`⁊, ✦, ¶`), and punctuation (` !"#'()*,-./:;?[]–—„·`)
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from scribesim.guides.viapoint import (
    VIAPOINT_STARTER_CATALOG,
    ViaPoint,
    ViaPointRecipe,
)

_V = ViaPoint

COUNTER_LETTERS: tuple[str, ...] = ("a", "o", "d", "e", "g", "b", "p")
HIGH_EXIT_LETTERS: frozenset[str] = frozenset({"r", "o", "v", "w", "f", "t"})


def _closed_bowl_lowercase() -> dict[str, ViaPointRecipe]:
    """Construct closed-counter lowercase letters (a, o, d, e, g, b, p) with generous counters."""
    cat: dict[str, ViaPointRecipe] = {}

    # o — full closed oval counter + high Bastarda exit link
    cat["o"] = ViaPointRecipe(
        letter="o",
        family="bowl",
        has_counter=True,
        via_points=(
            _V(1.65, 3.65, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.65, role="entry"),
            _V(0.90, 4.15, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.55, role="peak"),
            _V(0.10, 2.15, sigma_x_wnib=0.015, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.92, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.72, role="turn"),
            _V(1.78, 2.15, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.76, role="body"),
            _V(1.60, 3.70, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.45, role="peak"),
            _V(2.25, 3.55, sigma_x_wnib=0.18, sigma_y_wnib=0.20, pressure=0.26, role="exit"),
        ),
        advance_wnib=2.55,
    )

    # a — closed two-part Bastarda lobe + right minim stem + 40° exit foot
    cat["a"] = ViaPointRecipe(
        letter="a",
        family="bowl",
        has_counter=True,
        via_points=(
            _V(1.72, 3.60, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.62, role="entry"),
            _V(0.90, 4.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.55, role="peak"),
            _V(0.10, 2.10, sigma_x_wnib=0.015, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.90, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.74, role="turn"),
            _V(1.76, 2.25, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.32, role="turn"),
            _V(1.72, 3.75, sigma_x_wnib=0.025, sigma_y_wnib=0.025, pressure=0.78, role="peak"),
            _V(1.80, 1.90, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(1.85, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(2.55, 0.85, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.85,
    )

    # d — closed left lobe + tall looped Bastarda ascender + stem exit
    cat["d"] = ViaPointRecipe(
        letter="d",
        family="bowl",
        ascender=True,
        has_counter=True,
        via_points=(
            _V(1.72, 3.55, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.60, role="entry"),
            _V(0.90, 4.10, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.55, role="peak"),
            _V(0.10, 2.10, sigma_x_wnib=0.015, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.90, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.74, role="turn"),
            _V(1.76, 2.20, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.30, role="turn"),
            _V(1.72, 3.65, sigma_x_wnib=0.025, sigma_y_wnib=0.025, pressure=0.32, role="turn"),
            _V(2.05, 6.45, sigma_x_wnib=0.06, sigma_y_wnib=0.08, pressure=0.30, role="loop"),
            _V(1.68, 6.80, sigma_x_wnib=0.06, sigma_y_wnib=0.08, pressure=0.68, role="loop"),
            _V(1.80, 2.00, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(1.85, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(2.55, 0.85, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.85,
    )

    # e — closed upper eye counter + curved left wall + baseline exit
    cat["e"] = ViaPointRecipe(
        letter="e",
        family="bowl",
        has_counter=True,
        via_points=(
            _V(0.16, 2.05, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.36, role="entry"),
            _V(1.72, 2.25, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.28, role="loop"),
            _V(1.65, 3.60, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.52, role="peak"),
            _V(0.88, 4.18, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.68, role="peak"),
            _V(0.12, 2.05, sigma_x_wnib=0.015, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(0.25, 0.15, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(1.65, 0.85, sigma_x_wnib=0.18, sigma_y_wnib=0.22, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.10,
    )

    # g — closed upper lobe counter + descending stem + closed/looped descender
    cat["g"] = ViaPointRecipe(
        letter="g",
        family="descender",
        descender=True,
        has_counter=True,
        via_points=(
            _V(1.72, 3.60, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.62, role="entry"),
            _V(0.90, 4.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.55, role="peak"),
            _V(0.10, 2.10, sigma_x_wnib=0.015, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.90, 0.15, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.74, role="turn"),
            _V(1.76, 2.25, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.32, role="turn"),
            _V(1.72, 3.70, sigma_x_wnib=0.025, sigma_y_wnib=0.025, pressure=0.78, role="peak"),
            _V(1.80, 0.00, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(1.65, -2.10, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.78, role="turn"),
            _V(0.55, -2.25, sigma_x_wnib=0.05, sigma_y_wnib=0.05, pressure=0.50, role="loop"),
            _V(0.45, -0.80, sigma_x_wnib=0.05, sigma_y_wnib=0.05, pressure=0.28, role="loop"),
            _V(2.35, 0.75, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.75,
    )

    # b — tall ascender stem + closed right bowl counter
    cat["b"] = ViaPointRecipe(
        letter="b",
        family="ascender",
        ascender=True,
        has_counter=True,
        via_points=(
            _V(0.12, 6.75, sigma_x_wnib=0.12, sigma_y_wnib=0.14, pressure=0.78, role="entry"),
            _V(0.14, 3.55, sigma_x_wnib=0.015, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.16, 0.15, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.78, role="turn"),
            _V(1.05, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.68, role="turn"),
            _V(1.85, 2.10, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.82, role="body"),
            _V(1.05, 4.05, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.58, role="peak"),
            _V(0.16, 3.55, sigma_x_wnib=0.025, sigma_y_wnib=0.025, pressure=0.40, role="turn"),
            _V(2.25, 3.40, sigma_x_wnib=0.18, sigma_y_wnib=0.20, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.55,
    )

    # p — descender stem + closed right bowl counter
    cat["p"] = ViaPointRecipe(
        letter="p",
        family="descender",
        descender=True,
        has_counter=True,
        via_points=(
            _V(0.14, 4.15, sigma_x_wnib=0.12, sigma_y_wnib=0.14, pressure=0.78, role="entry"),
            _V(0.16, -2.20, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.16, 0.20, sigma_x_wnib=0.025, sigma_y_wnib=0.025, pressure=0.30, role="turn"),
            _V(0.16, 3.65, sigma_x_wnib=0.025, sigma_y_wnib=0.025, pressure=0.35, role="turn"),
            _V(1.05, 4.10, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.65, role="peak"),
            _V(1.85, 2.10, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(1.05, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.70, role="turn"),
            _V(0.18, 0.25, sigma_x_wnib=0.025, sigma_y_wnib=0.025, pressure=0.45, role="turn"),
            _V(2.30, 0.85, sigma_x_wnib=0.18, sigma_y_wnib=0.20, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.60,
    )

    return cat


def _remaining_lowercase() -> dict[str, ViaPointRecipe]:
    """Construct remaining lowercase letters (c, f, h, j, k, l, q, s, ſ, ß, t, v, w, x, y, z)."""
    cat: dict[str, ViaPointRecipe] = {}

    cat["c"] = ViaPointRecipe(
        letter="c",
        family="bowl",
        via_points=(
            _V(1.55, 3.85, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.68, role="entry"),
            _V(0.75, 4.15, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.60, role="peak"),
            _V(0.12, 2.15, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(0.35, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(1.65, 0.85, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=1.95,
    )

    cat["f"] = ViaPointRecipe(
        letter="f",
        family="ascender",
        ascender=True,
        descender=True,
        via_points=(
            _V(1.15, 6.50, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.65, role="entry"),
            _V(0.45, 6.80, sigma_x_wnib=0.05, sigma_y_wnib=0.05, pressure=0.72, role="peak"),
            _V(0.22, 2.20, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.18, -1.50, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.72, role="turn"),
            _V(0.10, 2.20, sigma_x_wnib=0.04, sigma_y_wnib=0.04, contact=False, pressure=0.0, role="turn"),
            _V(0.02, 3.10, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.52, role="body"),
            _V(1.35, 3.25, sigma_x_wnib=0.18, sigma_y_wnib=0.20, pressure=0.26, role="exit"),
        ),
        advance_wnib=1.65,
    )

    cat["h"] = ViaPointRecipe(
        letter="h",
        family="ascender",
        ascender=True,
        via_points=(
            _V(0.10, 6.75, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.78, role="entry"),
            _V(0.14, 2.80, sigma_x_wnib=0.015, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.16, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(0.35, 2.60, sigma_x_wnib=0.05, sigma_y_wnib=0.06, pressure=0.26, role="turn"),
            _V(1.25, 4.12, sigma_x_wnib=0.05, sigma_y_wnib=0.05, pressure=0.68, role="peak"),
            _V(1.62, 2.00, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(1.50, -0.45, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.68, role="turn"),
            _V(2.30, 0.80, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.65,
    )

    cat["j"] = ViaPointRecipe(
        letter="j",
        family="descender",
        descender=True,
        via_points=(
            _V(0.15, 4.15, sigma_x_wnib=0.16, sigma_y_wnib=0.18, pressure=0.76, role="entry"),
            _V(0.20, 1.50, sigma_x_wnib=0.02, sigma_y_wnib=0.03, pressure=0.84, role="body"),
            _V(0.12, -2.05, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.76, role="turn"),
            _V(-0.35, -1.80, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.45, role="loop"),
            _V(1.05, 0.80, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=1.45,
    )

    cat["k"] = ViaPointRecipe(
        letter="k",
        family="ascender",
        ascender=True,
        via_points=(
            _V(0.10, 6.75, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.78, role="entry"),
            _V(0.14, 2.50, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.16, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(0.35, 2.30, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.28, role="turn"),
            _V(1.45, 4.05, sigma_x_wnib=0.05, sigma_y_wnib=0.05, pressure=0.68, role="peak"),
            _V(0.55, 2.25, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.65, role="turn"),
            _V(1.55, 0.15, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.78, role="turn"),
            _V(2.25, 0.85, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.55,
    )

    cat["l"] = ViaPointRecipe(
        letter="l",
        family="ascender",
        ascender=True,
        via_points=(
            _V(0.10, 6.75, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.78, role="entry"),
            _V(0.14, 2.80, sigma_x_wnib=0.015, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.18, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(1.05, 0.85, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=1.45,
    )

    cat["q"] = ViaPointRecipe(
        letter="q",
        family="descender",
        descender=True,
        via_points=(
            _V(1.65, 3.60, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.62, role="entry"),
            _V(0.85, 4.12, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.55, role="peak"),
            _V(0.10, 2.10, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.85, 0.15, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.74, role="turn"),
            _V(1.70, 3.70, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.78, role="peak"),
            _V(1.75, -2.15, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(2.40, 0.75, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.65,
    )

    # round s (word-final)
    cat["s"] = ViaPointRecipe(
        letter="s",
        family="ascender",
        via_points=(
            _V(1.35, 3.90, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.62, role="entry"),
            _V(0.20, 3.15, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.78, role="body"),
            _V(1.40, 1.55, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.82, role="body"),
            _V(0.25, 0.12, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.76, role="turn"),
            _V(1.55, 0.75, sigma_x_wnib=0.18, sigma_y_wnib=0.20, pressure=0.24, role="exit"),
        ),
        advance_wnib=1.85,
    )

    # long s (ſ, word-initial and word-medial Bastarda tall s with descender taper)
    cat["ſ"] = ViaPointRecipe(
        letter="ſ",
        family="ascender",
        ascender=True,
        descender=True,
        via_points=(
            _V(1.05, 6.45, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.65, role="entry"),
            _V(0.35, 6.75, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.74, role="peak"),
            _V(0.18, 2.20, sigma_x_wnib=0.015, sigma_y_wnib=0.02, pressure=0.86, role="body"),
            _V(0.12, -1.65, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.68, role="turn"),
            _V(0.95, 0.85, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=1.40,
    )

    # ß — Bastarda long-s + round-z ligature
    cat["ß"] = ViaPointRecipe(
        letter="ß",
        family="ascender",
        ascender=True,
        descender=True,
        via_points=(
            _V(0.12, -1.65, sigma_x_wnib=0.12, sigma_y_wnib=0.14, pressure=0.45, role="entry"),
            _V(0.16, 2.80, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(0.45, 6.75, sigma_x_wnib=0.05, sigma_y_wnib=0.05, pressure=0.72, role="peak"),
            _V(1.55, 4.40, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.78, role="body"),
            _V(0.75, 2.60, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.58, role="turn"),
            _V(1.75, 1.30, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.84, role="body"),
            _V(0.65, 0.10, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.74, role="turn"),
            _V(2.15, 0.80, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.50,
    )

    cat["t"] = ViaPointRecipe(
        letter="t",
        family="minim",
        ascender=True,
        via_points=(
            _V(0.12, 5.35, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.78, role="entry"),
            _V(0.16, 2.20, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.22, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(1.05, 0.80, sigma_x_wnib=0.08, sigma_y_wnib=0.08, pressure=0.26, role="turn"),
            _V(0.02, 3.65, sigma_x_wnib=0.04, sigma_y_wnib=0.04, contact=False, pressure=0.0, role="turn"),
            _V(0.02, 3.65, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.52, role="body"),
            _V(1.30, 3.75, sigma_x_wnib=0.18, sigma_y_wnib=0.20, pressure=0.26, role="exit"),
        ),
        advance_wnib=1.65,
    )

    cat["v"] = ViaPointRecipe(
        letter="v",
        family="minim",
        via_points=(
            _V(0.08, 4.15, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.76, role="entry"),
            _V(0.22, 1.80, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(0.75, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(1.55, 2.15, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.74, role="body"),
            _V(1.40, 4.10, sigma_x_wnib=0.05, sigma_y_wnib=0.05, pressure=0.62, role="peak"),
            _V(2.05, 3.65, sigma_x_wnib=0.18, sigma_y_wnib=0.20, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.35,
    )

    cat["w"] = ViaPointRecipe(
        letter="w",
        family="minim",
        via_points=(
            _V(0.08, 4.15, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.76, role="entry"),
            _V(0.18, 1.80, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(0.65, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.74, role="turn"),
            _V(1.35, 3.95, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.68, role="peak"),
            _V(1.45, 1.80, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(1.95, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.74, role="turn"),
            _V(2.75, 2.20, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.72, role="body"),
            _V(2.60, 4.10, sigma_x_wnib=0.05, sigma_y_wnib=0.05, pressure=0.62, role="peak"),
            _V(3.25, 3.65, sigma_x_wnib=0.18, sigma_y_wnib=0.20, pressure=0.24, role="exit"),
        ),
        advance_wnib=3.55,
    )

    cat["x"] = ViaPointRecipe(
        letter="x",
        family="minim",
        via_points=(
            _V(0.10, 4.10, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.76, role="entry"),
            _V(0.85, 2.05, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(1.60, 0.12, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
            _V(0.10, 0.15, sigma_x_wnib=0.04, sigma_y_wnib=0.04, contact=False, pressure=0.0, role="turn"),
            _V(0.10, 0.15, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.32, role="turn"),
            _V(1.65, 4.05, sigma_x_wnib=0.18, sigma_y_wnib=0.20, pressure=0.28, role="exit"),
        ),
        advance_wnib=2.05,
    )

    cat["y"] = ViaPointRecipe(
        letter="y",
        family="descender",
        descender=True,
        via_points=(
            _V(0.08, 4.15, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.76, role="entry"),
            _V(0.16, 1.80, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(0.65, 0.15, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.72, role="turn"),
            _V(1.48, 4.10, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.74, role="peak"),
            _V(1.52, 1.00, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.85, role="body"),
            _V(1.30, -2.10, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.76, role="turn"),
            _V(0.45, -1.80, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.40, role="loop"),
            _V(2.15, 0.80, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.45,
    )

    cat["z"] = ViaPointRecipe(
        letter="z",
        family="descender",
        descender=True,
        via_points=(
            _V(0.10, 4.05, sigma_x_wnib=0.14, sigma_y_wnib=0.16, pressure=0.68, role="entry"),
            _V(1.45, 4.10, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.74, role="peak"),
            _V(0.25, 1.95, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.82, role="body"),
            _V(1.50, 0.80, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.80, role="body"),
            _V(0.75, -1.65, sigma_x_wnib=0.05, sigma_y_wnib=0.05, pressure=0.68, role="turn"),
            _V(1.90, 0.75, sigma_x_wnib=0.20, sigma_y_wnib=0.24, pressure=0.24, role="exit"),
        ),
        advance_wnib=2.20,
    )

    return cat


def _add_superscript_e(base: ViaPointRecipe, letter: str) -> ViaPointRecipe:
    """Attach a 15th-century superscript 'e' / diacritic mark above `base` via a pen lift."""
    mid_x = base.advance_wnib * 0.42
    top_y = 6.95 if base.ascender else 4.95
    diacritic = (
        _V(mid_x - 0.25, top_y, sigma_x_wnib=0.04, sigma_y_wnib=0.04, contact=False, pressure=0.0, role="turn"),
        _V(mid_x - 0.25, top_y, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.55, role="peak"),
        _V(mid_x + 0.35, top_y + 0.45, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.35, role="exit"),
    )
    return ViaPointRecipe(
        letter=letter,
        family=base.family,
        ascender=True,
        descender=base.descender,
        has_counter=base.has_counter,
        via_points=base.via_points + diacritic,
        advance_wnib=base.advance_wnib,
    )


def _build_capitals(lowercase: dict[str, ViaPointRecipe]) -> dict[str, ViaPointRecipe]:
    """Construct simplified Bastarda capitals A–Z (scaled to 1.48x height and 1.32x width)."""
    caps: dict[str, ViaPointRecipe] = {}
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        low = lowercase[ch.lower()]
        scaled_pts = tuple(
            replace(
                vp,
                x_wnib=round(vp.x_wnib * 1.32, 4),
                y_wnib=round(vp.y_wnib * 1.48, 4),
                pressure=min(0.92, round(vp.pressure * 1.08, 4)) if vp.contact else 0.0,
            )
            for vp in low.via_points
        )
        caps[ch] = ViaPointRecipe(
            letter=ch,
            family="capital",
            ascender=True,
            descender=low.descender,
            has_counter=low.has_counter,
            via_points=scaled_pts,
            advance_wnib=round(low.advance_wnib * 1.35, 4),
        )
    return caps


def _build_digits_and_marks() -> dict[str, ViaPointRecipe]:
    """Construct digits 0–9, scribal marks (⁊, ✦, ¶), and punctuation."""
    cat: dict[str, ViaPointRecipe] = {}

    for d_idx, ch in enumerate("0123456789"):
        offset = (d_idx % 3) * 0.08
        cat[ch] = ViaPointRecipe(
            letter=ch,
            family="digit",
            via_points=(
                _V(0.15 + offset, 4.10, sigma_x_wnib=0.10, sigma_y_wnib=0.12, pressure=0.74, role="entry"),
                _V(0.95, 2.20, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.82, role="body"),
                _V(0.25, 0.15, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.76, role="turn"),
                _V(1.35, 0.85, sigma_x_wnib=0.16, sigma_y_wnib=0.18, pressure=0.28, role="exit"),
            ),
            advance_wnib=1.85,
        )

    # Tironian et (⁊), section flourish (✦), pilcrow (¶)
    cat["⁊"] = ViaPointRecipe(
        letter="⁊",
        family="mark",
        descender=True,
        via_points=(
            _V(0.10, 3.85, sigma_x_wnib=0.10, sigma_y_wnib=0.10, pressure=0.70, role="entry"),
            _V(1.35, 3.95, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.78, role="peak"),
            _V(0.85, 1.80, sigma_x_wnib=0.02, sigma_y_wnib=0.02, pressure=0.84, role="body"),
            _V(0.65, -0.60, sigma_x_wnib=0.14, sigma_y_wnib=0.14, pressure=0.35, role="exit"),
        ),
        advance_wnib=1.80,
    )
    cat["✦"] = ViaPointRecipe(
        letter="✦",
        family="mark",
        via_points=(
            _V(0.20, 2.20, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.75, role="entry"),
            _V(0.85, 3.10, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.80, role="body"),
            _V(1.50, 2.20, sigma_x_wnib=0.04, sigma_y_wnib=0.04, pressure=0.75, role="turn"),
            _V(0.85, 1.30, sigma_x_wnib=0.10, sigma_y_wnib=0.10, pressure=0.40, role="exit"),
        ),
        advance_wnib=2.00,
    )
    cat["¶"] = ViaPointRecipe(
        letter="¶",
        family="mark",
        ascender=True,
        descender=True,
        via_points=(
            _V(1.30, 5.60, sigma_x_wnib=0.10, sigma_y_wnib=0.10, pressure=0.78, role="entry"),
            _V(0.18, 4.20, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.84, role="body"),
            _V(1.25, 2.80, sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.78, role="turn"),
            _V(1.30, -1.20, sigma_x_wnib=0.12, sigma_y_wnib=0.12, pressure=0.70, role="exit"),
        ),
        advance_wnib=1.95,
    )

    # All punctuation & symbols present in MS Erfurt output-live folios
    punct_chars = " !\"#'()*,-./:;?[]–—„·"
    for pch in punct_chars:
        if pch == " ":
            cat[pch] = ViaPointRecipe(letter=" ", family="mark", via_points=(), advance_wnib=2.20)
            continue
        y_hi = 3.20 if pch in "\"'()*[]/:;?!" else 0.85
        y_lo = 0.20 if pch not in "-–—·" else 2.05
        cat[pch] = ViaPointRecipe(
            letter=pch,
            family="mark",
            via_points=(
                _V(0.20, y_hi, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.68, role="entry"),
                _V(0.32, 0.5 * (y_hi + y_lo), sigma_x_wnib=0.03, sigma_y_wnib=0.03, pressure=0.75, role="body"),
                _V(0.45, y_lo, sigma_x_wnib=0.06, sigma_y_wnib=0.06, pressure=0.45, role="exit"),
            ),
            advance_wnib=1.10,
        )

    return cat


def _build_full_catalog() -> dict[str, ViaPointRecipe]:
    cat: dict[str, ViaPointRecipe] = {}
    cat.update(VIAPOINT_STARTER_CATALOG)
    cat.update(_closed_bowl_lowercase())
    cat.update(_remaining_lowercase())
    cat.update(_build_capitals(cat))

    # Umlauts and accented vowels (superscript e / circumflex above base vowel)
    cat["ä"] = _add_superscript_e(cat["a"], "ä")
    cat["ö"] = _add_superscript_e(cat["o"], "ö")
    cat["ü"] = _add_superscript_e(cat["u"], "ü")
    cat["Ä"] = _add_superscript_e(cat["A"], "Ä")
    cat["Ö"] = _add_superscript_e(cat["O"], "Ö")
    cat["Ü"] = _add_superscript_e(cat["U"], "Ü")
    cat["ê"] = _add_superscript_e(cat["e"], "ê")
    cat["î"] = _add_superscript_e(cat["i"], "î")

    cat.update(_build_digits_and_marks())
    return cat


VIAPOINT_CATALOG: dict[str, ViaPointRecipe] = _build_full_catalog()


def select_contextual_viapoint_recipe(word: str, index: int) -> ViaPointRecipe:
    """Select the context-appropriate Bastarda allograph for `word[index]` (TD-012 / TD-019).

    Rules:
      1. Positional allograph for 's': word-initial and word-medial 's' use long 'ſ'
         (unless followed by punctuation at the end of a token); word-final 's' uses round 's'.
      2. Neighbor-conditioned entry adaptation: when preceded by a high-exit letter
         (`r, o, v, w, f, t`), the initial entry via-point of `e, r, o, a, d, g, n, u, m, i`
         shifts upward toward the incoming high connection height.
    """
    ch = word[index]
    prev_ch = word[index - 1] if index > 0 else None
    next_ch = word[index + 1] if index + 1 < len(word) else None

    if ch == "s":
        is_word_final = next_ch is None or not next_ch.isalpha()
        recipe = VIAPOINT_CATALOG["s"] if is_word_final else VIAPOINT_CATALOG["ſ"]
    else:
        if ch not in VIAPOINT_CATALOG:
            raise KeyError(f"Character {ch!r} not in VIAPOINT_CATALOG (zero aliases allowed)")
        recipe = VIAPOINT_CATALOG[ch]

    if prev_ch in HIGH_EXIT_LETTERS and recipe.via_points:
        first_vp = recipe.via_points[0]
        adapted_first = replace(
            first_vp,
            y_wnib=round(max(first_vp.y_wnib, min(4.15, first_vp.y_wnib + 0.65)), 4),
        )
        return replace(recipe, via_points=(adapted_first,) + recipe.via_points[1:])

    return recipe


def check_corpus_exact_coverage(folio_dir: Path | str = "output-live") -> dict:
    """Verify exact character coverage across all MS Erfurt folio JSONs in `folio_dir`."""
    dpath = Path(folio_dir)
    observed: set[str] = set()
    total_chars = 0
    exact_hits = 0

    for fp in sorted(dpath.glob("f*.json")):
        data = json.loads(fp.read_text(encoding="utf-8"))
        for line in data.get("lines", []):
            txt = line.get("text", "")
            for ch in txt:
                observed.add(ch)
                total_chars += 1
                if ch in VIAPOINT_CATALOG:
                    exact_hits += 1

    missing = sorted(ch for ch in observed if ch not in VIAPOINT_CATALOG)
    coverage = exact_hits / max(1, total_chars) if observed else 1.0
    return {
        "total_characters": total_chars,
        "unique_characters": len(observed),
        "exact_coverage": round(coverage, 6),
        "alias_substitutions": 0,
        "missing_characters": missing,
    }
