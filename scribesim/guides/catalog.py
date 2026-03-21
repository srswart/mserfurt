"""Letterform guide catalog — keypoint definitions for Bastarda letters.

Starting with 5 core letters (n, u, d, e, r) that cover:
  - Minim (n, u): the basic vertical stroke
  - Arch (n): the connecting curve at top
  - Ascender (d): tall stroke above x-height
  - Bowl (d, e): curved enclosure
  - Shoulder (r): partial arch

Coordinates: x-height units (x=0 left, y=0 baseline, y=1.0 x-height top).
"""

from __future__ import annotations

from scribesim.guides.keypoint import Keypoint, LetterformGuide

# Shorthand
_K = Keypoint


def _guide(letter: str, kps: list[Keypoint], w: float,
           asc: bool = False, desc: bool = False) -> LetterformGuide:
    return LetterformGuide(
        letter=letter, keypoints=tuple(kps),
        x_advance=w, ascender=asc, descender=desc,
    )


# ---------------------------------------------------------------------------
# Core 5 letters
# ---------------------------------------------------------------------------

GUIDE_CATALOG: dict[str, LetterformGuide] = {}

# n — two minims connected by an arch
# Ductus: down-up-over-down
GUIDE_CATALOG["n"] = _guide("n", [
    _K(0.05, 0.95, "peak",     True,  270, 0.15),  # top of first minim
    _K(0.08, 0.0,  "base",     True,  270, 0.1),   # base of first minim
    _K(0.12, 0.3,  "junction", True,  45,  0.3),   # hairline up from base
    _K(0.3,  1.0,  "peak",     True,  0,   0.25),  # top of arch
    _K(0.5,  0.95, "peak",     True,  270, 0.15),  # start of second minim
    _K(0.52, 0.0,  "base",     True,  270, 0.1),   # base of second minim
], w=0.6)

# u — two minims connected at the base
# Ductus: down-curve-up
GUIDE_CATALOG["u"] = _guide("u", [
    _K(0.05, 0.95, "peak",     True,  270, 0.15),  # top of first minim
    _K(0.08, 0.05, "base",     True,  270, 0.1),   # near base
    _K(0.15, 0.0,  "base",     True,  0,   0.2),   # bottom curve
    _K(0.35, 0.05, "junction", True,  90,  0.2),   # start rising
    _K(0.5,  0.95, "peak",     True,  90,  0.15),  # top of second stroke
    _K(0.52, 0.0,  "base",     True,  270, 0.1),   # exit base
], w=0.6)

# d — bowl + tall ascender
# Ductus: bowl left, bowl right, ascender up, back down
GUIDE_CATALOG["d"] = _guide("d", [
    _K(0.35, 0.7,  "peak",      True,  180, 0.2),   # top of bowl
    _K(0.05, 0.6,  "peak",      True,  270, 0.2),   # left side of bowl
    _K(0.0,  0.35, "junction",  True,  270, 0.15),  # bowl mid-left
    _K(0.05, 0.05, "base",      True,  0,   0.15),  # bottom of bowl
    _K(0.35, 0.1,  "junction",  True,  90,  0.2),   # bowl closes right
    _K(0.4,  0.8,  "junction",  True,  90,  0.2),   # rising to ascender
    _K(0.38, 1.6,  "peak",      True,  90,  0.3),   # ascender top
    _K(0.32, 1.8,  "loop_apex", True,  180, 0.3),   # Bastarda loop at top
    _K(0.4,  0.5,  "junction",  True,  270, 0.2),   # descending back
    _K(0.42, 0.0,  "base",      True,  270, 0.1),   # exit at baseline
], w=0.55, asc=True)

# e — bowl with mid-bar
# Ductus: curve up, over, down, mid-bar
GUIDE_CATALOG["e"] = _guide("e", [
    _K(0.1,  0.5,  "junction",  True,  90,  0.2),   # start mid-left
    _K(0.05, 0.7,  "peak",      True,  90,  0.2),   # upper curve
    _K(0.1,  0.9,  "peak",      True,  0,   0.2),   # top
    _K(0.4,  0.9,  "peak",      True,  0,   0.2),   # top right
    _K(0.45, 0.5,  "junction",  True,  270, 0.15),  # right side descending
    _K(0.4,  0.05, "base",      True,  180, 0.15),  # bottom
    _K(0.1,  0.0,  "base",      True,  180, 0.15),  # bottom left
], w=0.5)

# r — minim + shoulder
# Ductus: down, then short arch right
GUIDE_CATALOG["r"] = _guide("r", [
    _K(0.05, 0.95, "peak",     True,  270, 0.15),  # top of minim
    _K(0.08, 0.0,  "base",     True,  270, 0.1),   # base of minim
    _K(0.12, 0.5,  "junction", True,  45,  0.3),   # hairline up
    _K(0.15, 0.9,  "peak",     True,  0,   0.2),   # top of shoulder
    _K(0.35, 0.85, "peak",     True,  315, 0.2),   # shoulder curves down
], w=0.4)


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------

def lookup_guide(letter: str) -> LetterformGuide | None:
    """Look up a letterform guide by character."""
    return GUIDE_CATALOG.get(letter)
