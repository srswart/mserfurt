"""Glyph catalog — German Bastarda letterforms as Bezier stroke sequences.

All coordinates are in x-height units:
  - x: 0.0 = left edge of glyph, positive rightward
  - y: 0.0 = baseline, 1.0 = x-height top, ascenders extend above 1.0,
       descenders below 0.0 (negative)

Control point notation per stroke: P0 (start) → P1 → P2 → P3 (end).
Pressure profile: sampled from t=0 to t=1 along the curve.
"""

from __future__ import annotations

from scribesim.glyphs.glyph import Glyph
from scribesim.glyphs.strokes import BezierStroke

# ---------------------------------------------------------------------------
# Stroke factory helpers
# ---------------------------------------------------------------------------

def _s(*pts: tuple, name: str = "", pressure: tuple = (0.4, 0.8, 0.8, 0.4)) -> BezierStroke:
    """Create a BezierStroke from exactly 4 (x,y) tuples."""
    return BezierStroke(control_points=pts, pressure_profile=pressure, stroke_name=name)


def _g(gid: str, cp: int, strokes: list, w: float, base: float = 0.0,
       entry: tuple | None = None, exit: tuple | None = None) -> Glyph:
    """Create a Glyph with strokes converted to tuple.

    entry/exit: explicit (x, y) connection point in x-height units.
    If omitted, Glyph.__post_init__ derives them from first/last stroke endpoints.
    Provide these for any letter where the last stroke is a dot, crossbar, or
    decorative element that is NOT the natural exit for inter-glyph connections.
    """
    return Glyph(id=gid, unicode_codepoint=cp, strokes=tuple(strokes),
                 advance_width=w, baseline_offset=base,
                 entry_point=entry, exit_point=exit)


# ---------------------------------------------------------------------------
# Pressure curve presets
# ---------------------------------------------------------------------------
# Pressure range scaled ×0.70 so peak is 0.63 (was 0.90).
# Direction is the primary driver of thick/thin via nib angle; pressure
# modulates darkness ±20% only (TD-004 Fix B). High pressure was producing
# near-maximum darkness on every stroke, losing the tonal range.
_ENTRY = (0.14, 0.42, 0.63, 0.56)   # hairline entry → full pressure
_BODY  = (0.49, 0.63, 0.63, 0.49)   # full-pressure body stroke
_EXIT  = (0.56, 0.49, 0.28, 0.14)   # full pressure → hairline exit
_FINE  = (0.14, 0.21, 0.21, 0.14)   # hairline superscript / fine mark
_DOWN  = (0.28, 0.56, 0.63, 0.49)   # downstroke (Bastarda characteristic)
_UP    = (0.21, 0.28, 0.21, 0.14)   # upstroke (light)


# ---------------------------------------------------------------------------
# Lowercase a-z  (German Bastarda forms)
# ---------------------------------------------------------------------------

_catalog: dict[str, Glyph] = {}

# a — two-story form with lobe and vertical right stroke
_catalog["a"] = _g("a", 0x61, [
    _s((0.3, 0.7), (0.08, 0.92), (-0.02, 0.48), (0.1, 0.0), name="lobe_left",  pressure=_DOWN),
    _s((0.1, 0.0), (0.28, -0.03), (0.42, 0.25), (0.42, 0.7), name="lobe_right", pressure=_UP),
    _s((0.42, 0.7), (0.43, 1.02), (0.41, 0.48), (0.38, 0.0), name="right_stem", pressure=_BODY),
], w=0.55)

# b — ascender + lobe
_catalog["b"] = _g("b", 0x62, [
    _s((0.1, 0.0), (0.13, 0.7), (0.08, 1.4), (0.05, 1.8), name="ascender",   pressure=_DOWN),
    _s((0.1, 0.7), (0.28, 0.95), (0.5, 0.75), (0.5, 0.4), name="lobe_top",   pressure=_BODY),
    _s((0.5, 0.4), (0.48, 0.08), (0.28, -0.03), (0.1, 0.02), name="lobe_bot",   pressure=_EXIT),
], w=0.55)

# c — open lobe, single curved stroke
_catalog["c"] = _g("c", 0x63, [
    _s((0.45, 0.72), (0.12, 0.95), (-0.03, 0.62), (0.0, 0.35), name="top",    pressure=_ENTRY),
    _s((0.0, 0.35), (-0.02, 0.08), (0.18, -0.03), (0.45, 0.02), name="bottom", pressure=_EXIT),
], w=0.48)

# d — lobe + ascender
_catalog["d"] = _g("d", 0x64, [
    _s((0.4, 0.72), (0.18, 0.95), (-0.02, 0.72), (0.0, 0.35), name="lobe_top",  pressure=_ENTRY),
    _s((0.0, 0.35), (-0.02, 0.08), (0.22, -0.02), (0.4, 0.1), name="lobe_bot",  pressure=_EXIT),
    _s((0.4, 0.1), (0.42, 0.75), (0.38, 1.35), (0.36, 1.8),  name="ascender",  pressure=_DOWN),
], w=0.55)

# e — two-stroke with mid-bar
_catalog["e"] = _g("e", 0x65, [
    _s((0.1, 0.5), (-0.02, 0.65), (-0.02, 0.92), (0.4, 0.92), name="top_arc",  pressure=_BODY),
    _s((0.4, 0.92), (0.52, 0.48), (0.38, -0.02), (0.08, 0.0), name="body",     pressure=_DOWN),
    _s((0.05, 0.5), (0.18, 0.48), (0.32, 0.48), (0.45, 0.5), name="mid_bar", pressure=_FINE),
], w=0.50)

# f — ascender with crossbar (Bastarda f sits on baseline)
# Exit: from bottom of stem, NOT from the ascender head serif.
_catalog["f"] = _g("f", 0x66, [
    _s((0.25, 0.0), (0.27, 0.45), (0.23, 1.15), (0.2, 1.8), name="stem",     pressure=_DOWN),
    _s((0.05, 0.52), (0.14, 0.48), (0.36, 0.48), (0.45, 0.52), name="crossbar", pressure=_FINE),
    _s((0.05, 1.62), (0.12, 1.74), (0.22, 1.82), (0.35, 1.75), name="head",    pressure=_ENTRY),
], w=0.42, exit=(0.25, 0.0))

# g — lobe + descender loop
_catalog["g"] = _g("g", 0x67, [
    _s((0.4, 0.72), (0.18, 0.95), (-0.02, 0.72), (0.0, 0.35), name="lobe_top",    pressure=_ENTRY),
    _s((0.0, 0.35), (-0.02, 0.08), (0.22, -0.02), (0.4, 0.02), name="lobe_bot",    pressure=_EXIT),
    _s((0.4, 0.02), (0.42, -0.35), (0.18, -0.62), (-0.02, -0.48), name="desc_loop", pressure=_DOWN),
    _s((-0.02, -0.48), (-0.12, -0.28), (0.02, -0.08), (0.22, 0.02), name="desc_close", pressure=_UP),
], w=0.52)

# h — stem + arch
# Entry: connection arrives at x-height level on left stem, not baseline.
_catalog["h"] = _g("h", 0x68, [
    _s((0.1, 0.0), (0.13, 0.7), (0.08, 1.35), (0.06, 1.8), name="stem",         pressure=_DOWN),
    _s((0.1, 0.82), (0.22, 1.02), (0.42, 1.02), (0.5, 0.82), name="arch_top",     pressure=_BODY),
    _s((0.5, 0.82), (0.52, 0.38), (0.48, 0.08), (0.47, 0.0), name="right_stroke", pressure=_DOWN),
], w=0.60, entry=(0.1, 0.75))

# i — dot + minim
# Exit: from baseline of minim (not from dot above x-height).
# Entry: connection arrives near x-height top of minim, not at baseline.
_catalog["i"] = _g("i", 0x69, [
    _s((0.15, 0.0), (0.17, 0.28), (0.14, 0.72), (0.13, 1.0), name="minim",   pressure=_DOWN),
    _s((0.1, 1.22), (0.14, 1.26), (0.2, 1.26), (0.25, 1.22), name="dot",     pressure=_FINE),
], w=0.32, entry=(0.15, 0.8), exit=(0.15, 0.0))

# j — dot + minim with descender
# Exit: from end of hook (not from dot above x-height).
_catalog["j"] = _g("j", 0x6A, [
    _s((0.2, 1.0), (0.22, 0.28), (0.18, -0.28), (0.08, -0.5), name="minim_desc", pressure=_DOWN),
    _s((0.08, -0.5), (-0.02, -0.62), (-0.02, -0.48), (0.1, -0.38), name="hook",     pressure=_EXIT),
    _s((0.1, 1.22), (0.18, 1.26), (0.25, 1.26), (0.3, 1.22), name="dot",       pressure=_FINE),
], w=0.32, entry=(0.2, 1.0), exit=(0.1, -0.38))

# k — stem + kick strokes
_catalog["k"] = _g("k", 0x6B, [
    _s((0.1, 0.0), (0.13, 0.7), (0.08, 1.35), (0.06, 1.8), name="stem",     pressure=_DOWN),
    _s((0.1, 0.72), (0.22, 0.85), (0.38, 0.95), (0.5, 1.0), name="upper_arm", pressure=_UP),
    _s((0.1, 0.58), (0.22, 0.48), (0.32, 0.28), (0.5, 0.0), name="lower_leg", pressure=_DOWN),
], w=0.53)

# l — single ascender stroke
_catalog["l"] = _g("l", 0x6C, [
    _s((0.15, 0.0), (0.18, 0.7), (0.13, 1.35), (0.1, 1.8), name="stem", pressure=_DOWN),
], w=0.30)

# m — three minims
# Entry arrives at x-height level, not at the baseline where stem1 is stored.
_catalog["m"] = _g("m", 0x6D, [
    _s((0.1, 0.0), (0.13, 0.45), (0.11, 0.78), (0.1, 1.0), name="stem1",     pressure=_DOWN),
    _s((0.1, 0.92), (0.22, 1.04), (0.36, 1.02), (0.4, 0.9), name="arch1",    pressure=_BODY),
    _s((0.4, 0.9), (0.42, 0.38), (0.39, 0.08), (0.38, 0.0), name="stem2",     pressure=_DOWN),
    _s((0.4, 0.92), (0.52, 1.04), (0.66, 1.02), (0.7, 0.9), name="arch2",    pressure=_BODY),
    _s((0.7, 0.9), (0.72, 0.38), (0.69, 0.08), (0.68, 0.0), name="stem3",     pressure=_DOWN),
], w=0.80, entry=(0.1, 0.75))

# n — two minims
# Entry arrives at x-height level, not at the baseline where stem1 is stored.
_catalog["n"] = _g("n", 0x6E, [
    _s((0.1, 0.0), (0.13, 0.45), (0.11, 0.78), (0.1, 1.0), name="stem1",   pressure=_DOWN),
    _s((0.1, 0.92), (0.22, 1.04), (0.36, 1.02), (0.4, 0.9), name="arch",   pressure=_BODY),
    _s((0.4, 0.9), (0.42, 0.38), (0.39, 0.08), (0.38, 0.0), name="stem2",   pressure=_DOWN),
], w=0.55, entry=(0.1, 0.75))

# o — two-part oval
_catalog["o"] = _g("o", 0x6F, [
    _s((0.25, 1.0), (-0.02, 0.95), (-0.02, 0.05), (0.25, 0.0), name="left_arc",  pressure=_DOWN),
    _s((0.25, 0.0), (0.52, 0.05), (0.52, 0.95), (0.25, 1.0), name="right_arc", pressure=_UP),
], w=0.53)

# p — stem with descender + lobe
_catalog["p"] = _g("p", 0x70, [
    _s((0.1, 1.0), (0.13, 0.28), (0.08, -0.35), (0.06, -0.6), name="stem_desc",  pressure=_DOWN),
    _s((0.1, 0.82), (0.3, 1.02), (0.5, 0.82), (0.5, 0.5),   name="lobe_top",   pressure=_BODY),
    _s((0.5, 0.5), (0.48, 0.18), (0.28, -0.02), (0.1, 0.08),   name="lobe_bot",   pressure=_EXIT),
], w=0.58)

# q — lobe + descender on right
_catalog["q"] = _g("q", 0x71, [
    _s((0.4, 0.72), (0.18, 0.95), (-0.02, 0.72), (0.0, 0.35), name="lobe_top",   pressure=_ENTRY),
    _s((0.0, 0.35), (-0.02, 0.08), (0.22, -0.02), (0.4, 0.1), name="lobe_bot",   pressure=_EXIT),
    _s((0.4, 0.92), (0.42, 0.28), (0.38, -0.35), (0.36, -0.6), name="stem_desc", pressure=_DOWN),
], w=0.55)

# r — stem + shoulder
_catalog["r"] = _g("r", 0x72, [
    _s((0.1, 0.0), (0.13, 0.45), (0.11, 0.78), (0.1, 1.0), name="stem",     pressure=_DOWN),
    _s((0.1, 0.92), (0.22, 1.04), (0.32, 1.02), (0.4, 0.82), name="shoulder", pressure=_BODY),
], w=0.43)

# round_s — terminal/final s (round form)
_catalog["round_s"] = _g("round_s", 0x73, [
    _s((0.35, 0.88), (0.08, 0.98), (-0.03, 0.72), (0.0, 0.5), name="upper_arc", pressure=_ENTRY),
    _s((0.0, 0.5), (-0.02, 0.18), (0.22, -0.02), (0.42, 0.12),   name="lower_arc", pressure=_DOWN),
    _s((0.42, 0.12), (0.52, 0.22), (0.5, 0.62), (0.38, 0.82),   name="right_arc", pressure=_EXIT),
], w=0.48)

# t — stem with crossbar
# Exit: from bottom of stem, NOT from crossbar end.
# Entry: connection arrives at crossbar level (typical 't' entry from left).
_catalog["t"] = _g("t", 0x74, [
    _s((0.2, -0.1), (0.22, 0.45), (0.19, 1.05), (0.17, 1.5), name="stem",     pressure=_DOWN),
    _s((0.0, 0.72), (0.1, 0.68), (0.3, 0.68), (0.4, 0.72),  name="crossbar", pressure=_FINE),
], w=0.42, entry=(0.2, 0.72), exit=(0.2, -0.1))

# u — two downstrokes with connecting arch at bottom
# Entry arrives at x-height level where the left stem begins physically.
_catalog["u"] = _g("u", 0x75, [
    _s((0.1, 1.0), (0.12, 0.48), (0.09, 0.18), (0.08, 0.0), name="left_stem",  pressure=_DOWN),
    _s((0.08, 0.0), (0.18, -0.04), (0.35, -0.04), (0.42, 0.02), name="base_arch", pressure=_BODY),
    _s((0.42, 0.02), (0.41, 0.22), (0.43, 0.52), (0.42, 1.0), name="right_stem", pressure=_UP),
], w=0.55, entry=(0.1, 0.75))

# v — two diagonal strokes
_catalog["v"] = _g("v", 0x76, [
    _s((0.0, 1.0), (0.08, 0.58), (0.14, 0.28), (0.2, 0.0), name="left_diagonal",  pressure=_DOWN),
    _s((0.2, 0.0), (0.28, 0.32), (0.36, 0.62), (0.45, 1.0), name="right_diagonal", pressure=_UP),
], w=0.48)

# w — three-stroke German Bastarda w
_catalog["w"] = _g("w", 0x77, [
    _s((0.0, 1.0), (0.08, 0.48), (0.1, 0.18), (0.15, 0.0), name="left_v",    pressure=_DOWN),
    _s((0.15, 0.0), (0.22, 0.48), (0.28, 0.82), (0.35, 1.0), name="mid_v",   pressure=_UP),
    _s((0.35, 1.0), (0.38, 0.48), (0.4, 0.18), (0.45, 0.0), name="right_v1", pressure=_DOWN),
    _s((0.45, 0.0), (0.52, 0.38), (0.58, 0.72), (0.65, 1.0), name="right_v2", pressure=_UP),
], w=0.70)

# x — two crossing diagonals
_catalog["x"] = _g("x", 0x78, [
    _s((0.0, 1.0), (0.12, 0.68), (0.28, 0.32), (0.45, 0.0), name="diag_left",  pressure=_DOWN),
    _s((0.45, 1.0), (0.32, 0.68), (0.15, 0.32), (0.0, 0.0), name="diag_right", pressure=_DOWN),
], w=0.48)

# y — two strokes, right with descender
_catalog["y"] = _g("y", 0x79, [
    _s((0.0, 1.0), (0.08, 0.58), (0.14, 0.28), (0.2, 0.0), name="left_arm",    pressure=_DOWN),
    _s((0.45, 1.0), (0.32, 0.48), (0.2, -0.02), (0.12, -0.5), name="right_desc", pressure=_DOWN),
    _s((0.12, -0.5), (0.02, -0.62), (-0.02, -0.48), (0.05, -0.38), name="hook",   pressure=_EXIT),
], w=0.50)

# z — three strokes
_catalog["z"] = _g("z", 0x7A, [
    _s((0.0, 1.0), (0.12, 1.02), (0.32, 0.98), (0.45, 1.0), name="top_bar",    pressure=_FINE),
    _s((0.45, 1.0), (0.32, 0.68), (0.15, 0.32), (0.0, 0.0), name="diagonal", pressure=_DOWN),
    _s((0.0, 0.0), (0.12, -0.02), (0.32, 0.02), (0.45, 0.0),   name="bot_bar",  pressure=_FINE),
], w=0.47)

# ---------------------------------------------------------------------------
# German-specific forms
# ---------------------------------------------------------------------------

# long_s — U+017F — tall ascending s without loop, used medially in German
_catalog["long_s"] = _g("long_s", 0x17F, [
    _s((0.18, 1.8), (0.14, 1.38), (0.11, 0.95), (0.12, 0.5), name="ascender",    pressure=_DOWN),
    _s((0.12, 0.5), (0.13, 0.18), (0.11, 0.02), (0.1, -0.05), name="descender",  pressure=_DOWN),
    _s((0.08, 1.62), (0.18, 1.74), (0.33, 1.72), (0.4, 1.6),  name="head_serif", pressure=_ENTRY),
], w=0.35)

# a_umlaut — Bastarda ä = base 'a' + two superscript-e dots above
_catalog["a_umlaut"] = _g("a_umlaut", 0xE4, [
    *_catalog["a"].strokes,  # inherit base 'a' strokes
    _s((0.1, 1.15), (0.15, 1.2), (0.2, 1.2), (0.25, 1.15), name="umlaut_dot1", pressure=_FINE),
    _s((0.3, 1.15), (0.35, 1.2), (0.4, 1.2), (0.45, 1.15), name="umlaut_dot2", pressure=_FINE),
], w=0.55)

# o_umlaut
_catalog["o_umlaut"] = _g("o_umlaut", 0xF6, [
    *_catalog["o"].strokes,
    _s((0.05, 1.15), (0.1, 1.2), (0.15, 1.2), (0.2, 1.15),  name="umlaut_dot1", pressure=_FINE),
    _s((0.3, 1.15), (0.35, 1.2), (0.4, 1.2), (0.45, 1.15),  name="umlaut_dot2", pressure=_FINE),
], w=0.53)

# u_umlaut
_catalog["u_umlaut"] = _g("u_umlaut", 0xFC, [
    *_catalog["u"].strokes,
    _s((0.05, 1.15), (0.1, 1.2), (0.15, 1.2), (0.2, 1.15),  name="umlaut_dot1", pressure=_FINE),
    _s((0.3, 1.15), (0.35, 1.2), (0.4, 1.2), (0.45, 1.15),  name="umlaut_dot2", pressure=_FINE),
], w=0.55)

# esszett — ß — composed as long_s body + z strokes
_catalog["esszett"] = _g("esszett", 0xDF, [
    _s((0.2, 1.8), (0.15, 1.4), (0.1, 1.0), (0.1, 0.5), name="ls_ascender",    pressure=_DOWN),
    _s((0.1, 0.5), (0.1, 0.2), (0.1, 0.0), (0.1, -0.05), name="ls_stem",       pressure=_DOWN),
    _s((0.1, 1.6), (0.2, 1.7), (0.35, 1.7), (0.4, 1.6),  name="ls_head",       pressure=_ENTRY),
    # z body attached on right
    _s((0.1, 1.4), (0.25, 1.45), (0.4, 1.35), (0.45, 1.1), name="z_top_arc",   pressure=_BODY),
    _s((0.45, 1.1), (0.45, 0.8), (0.35, 0.6), (0.2, 0.5), name="z_diagonal",   pressure=_DOWN),
    _s((0.2, 0.5), (0.35, 0.5), (0.45, 0.4), (0.45, 0.1), name="z_lower_arc",  pressure=_EXIT),
], w=0.52)

# ---------------------------------------------------------------------------
# Uppercase Bastarda capitals A-Z
# ---------------------------------------------------------------------------

def _cap_stub(ch: str, cp: int, w: float = 0.70) -> Glyph:
    """Bastarda majuscule — simplified two-stroke capital form."""
    return _g(ch, cp, [
        _s((0.1, 1.8), (0.2, 1.4), (0.3, 1.0), (0.35, 0.0), name="left_main",  pressure=_DOWN),
        _s((0.35, 0.0), (0.5, 0.7), (0.6, 1.4), (0.65, 1.8), name="right_main", pressure=_UP),
    ], w=w)


_catalog["A"] = _g("A", 0x41, [
    _s((0.0, 0.0), (0.15, 0.8), (0.2, 1.4), (0.3, 1.8),  name="left_stem",  pressure=_DOWN),
    _s((0.3, 1.8), (0.4, 1.4), (0.5, 0.8), (0.65, 0.0),  name="right_stem", pressure=_DOWN),
    _s((0.1, 0.8), (0.25, 0.8), (0.4, 0.8), (0.55, 0.8), name="crossbar",   pressure=_FINE),
], w=0.65)

_catalog["B"] = _g("B", 0x42, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),  name="stem",        pressure=_DOWN),
    _s((0.1, 1.8), (0.45, 1.8), (0.55, 1.5), (0.45, 1.1), name="upper_lobe_top", pressure=_BODY),
    _s((0.45, 1.1), (0.35, 0.9), (0.1, 0.9), (0.1, 0.9),  name="upper_lobe_bot", pressure=_EXIT),
    _s((0.1, 0.9), (0.5, 0.9), (0.6, 0.6), (0.5, 0.2),   name="lower_lobe_top", pressure=_BODY),
    _s((0.5, 0.2), (0.4, 0.0), (0.2, 0.0), (0.1, 0.0),   name="lower_lobe_bot", pressure=_EXIT),
], w=0.65)

for _ch, _cp in [("C", 0x43), ("G", 0x47), ("O", 0x4F), ("Q", 0x51)]:
    _catalog[_ch] = _g(_ch, _cp, [
        _s((0.5, 1.7), (0.1, 1.9), (0.0, 1.3), (0.0, 0.9),   name="top",    pressure=_ENTRY),
        _s((0.0, 0.9), (0.0, 0.4), (0.1, 0.0), (0.5, 0.0),   name="bottom", pressure=_EXIT),
    ], w=0.60)

_catalog["D"] = _g("D", 0x44, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),   name="stem",     pressure=_DOWN),
    _s((0.1, 1.8), (0.5, 1.8), (0.65, 1.2), (0.65, 0.9), name="arc_top",  pressure=_BODY),
    _s((0.65, 0.9), (0.65, 0.4), (0.5, 0.0), (0.1, 0.0), name="arc_bot",  pressure=_EXIT),
], w=0.68)

_catalog["E"] = _g("E", 0x45, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),    name="stem",      pressure=_DOWN),
    _s((0.1, 1.8), (0.3, 1.8), (0.5, 1.8), (0.6, 1.8),    name="top_bar",   pressure=_FINE),
    _s((0.1, 0.9), (0.25, 0.9), (0.4, 0.9), (0.5, 0.9),   name="mid_bar",   pressure=_FINE),
    _s((0.1, 0.0), (0.3, 0.0), (0.5, 0.0), (0.6, 0.0),    name="bot_bar",   pressure=_FINE),
], w=0.60)

_catalog["F"] = _g("F", 0x46, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),    name="stem",    pressure=_DOWN),
    _s((0.1, 1.8), (0.3, 1.8), (0.5, 1.8), (0.6, 1.8),    name="top_bar", pressure=_FINE),
    _s((0.1, 0.9), (0.25, 0.9), (0.4, 0.9), (0.5, 0.9),   name="mid_bar", pressure=_FINE),
], w=0.55)

_catalog["H"] = _g("H", 0x48, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),   name="left_stem",  pressure=_DOWN),
    _s((0.6, 0.0), (0.63, 0.75), (0.58, 1.35), (0.56, 1.8),   name="right_stem", pressure=_DOWN),
    _s((0.1, 0.9), (0.25, 0.9), (0.45, 0.9), (0.6, 0.9), name="crossbar",   pressure=_FINE),
], w=0.72)

_catalog["I"] = _g("I", 0x49, [
    _s((0.2, 0.0), (0.23, 0.75), (0.18, 1.35), (0.16, 1.8), name="stem",     pressure=_DOWN),
    _s((0.0, 1.8), (0.1, 1.8), (0.3, 1.8), (0.4, 1.8), name="top_ser",  pressure=_FINE),
    _s((0.0, 0.0), (0.1, 0.0), (0.3, 0.0), (0.4, 0.0), name="bot_ser",  pressure=_FINE),
], w=0.40)

_catalog["J"] = _g("J", 0x4A, [
    _s((0.4, 1.8), (0.4, 0.8), (0.4, 0.2), (0.3, -0.1),  name="stem_desc", pressure=_DOWN),
    _s((0.3, -0.1), (0.1, -0.2), (0.0, 0.0), (0.1, 0.2), name="hook",      pressure=_EXIT),
    _s((0.2, 1.8), (0.3, 1.8), (0.5, 1.8), (0.6, 1.8),   name="top_ser",   pressure=_FINE),
], w=0.50)

_catalog["K"] = _g("K", 0x4B, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),  name="stem",      pressure=_DOWN),
    _s((0.1, 1.0), (0.25, 1.2), (0.45, 1.5), (0.6, 1.8), name="upper_arm", pressure=_UP),
    _s((0.1, 0.9), (0.25, 0.6), (0.4, 0.3), (0.6, 0.0),  name="lower_leg", pressure=_DOWN),
], w=0.62)

_catalog["L"] = _g("L", 0x4C, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),  name="stem",    pressure=_DOWN),
    _s((0.1, 0.0), (0.25, 0.0), (0.45, 0.0), (0.6, 0.0), name="foot",   pressure=_FINE),
], w=0.55)

_catalog["M"] = _g("M", 0x4D, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),   name="left_stem",  pressure=_DOWN),
    _s((0.1, 1.8), (0.2, 1.4), (0.35, 0.9), (0.4, 0.0),  name="left_diag",  pressure=_DOWN),
    _s((0.4, 0.0), (0.5, 0.9), (0.6, 1.4), (0.7, 1.8),   name="right_diag", pressure=_UP),
    _s((0.7, 1.8), (0.7, 1.2), (0.7, 0.5), (0.7, 0.0),   name="right_stem", pressure=_DOWN),
], w=0.80)

_catalog["N"] = _g("N", 0x4E, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),   name="left_stem",  pressure=_DOWN),
    _s((0.1, 1.8), (0.25, 1.2), (0.45, 0.6), (0.6, 0.0), name="diagonal",   pressure=_DOWN),
    _s((0.6, 0.0), (0.6, 0.6), (0.6, 1.2), (0.6, 1.8),   name="right_stem", pressure=_DOWN),
], w=0.72)

_catalog["P"] = _g("P", 0x50, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),   name="stem",        pressure=_DOWN),
    _s((0.1, 1.8), (0.5, 1.8), (0.6, 1.5), (0.6, 1.2),   name="lobe_top",    pressure=_BODY),
    _s((0.6, 1.2), (0.6, 0.9), (0.5, 0.7), (0.1, 0.7),   name="lobe_bot",    pressure=_EXIT),
], w=0.62)

_catalog["R"] = _g("R", 0x52, [
    _s((0.1, 0.0), (0.13, 0.75), (0.08, 1.35), (0.06, 1.8),   name="stem",      pressure=_DOWN),
    _s((0.1, 1.8), (0.5, 1.8), (0.6, 1.5), (0.6, 1.2),   name="lobe_top",  pressure=_BODY),
    _s((0.6, 1.2), (0.6, 0.9), (0.5, 0.7), (0.1, 0.7),   name="lobe_bot",  pressure=_EXIT),
    _s((0.3, 0.7), (0.4, 0.5), (0.5, 0.3), (0.6, 0.0),   name="leg",       pressure=_DOWN),
], w=0.65)

_catalog["S"] = _g("S", 0x53, [
    _s((0.55, 1.6), (0.2, 1.9), (0.0, 1.5), (0.05, 1.1), name="top_arc",   pressure=_ENTRY),
    _s((0.05, 1.1), (0.1, 0.9), (0.5, 0.9), (0.55, 0.7), name="mid_stroke", pressure=_BODY),
    _s((0.55, 0.7), (0.6, 0.4), (0.5, 0.0), (0.1, 0.0),  name="bot_arc",   pressure=_EXIT),
], w=0.58)

_catalog["T"] = _g("T", 0x54, [
    _s((0.35, 0.0), (0.38, 0.75), (0.33, 1.35), (0.31, 1.8), name="stem",    pressure=_DOWN),
    _s((0.0, 1.8), (0.15, 1.8), (0.5, 1.8), (0.7, 1.8),    name="top_bar", pressure=_FINE),
], w=0.70)

_catalog["U"] = _g("U", 0x55, [
    _s((0.1, 1.8), (0.1, 0.8), (0.1, 0.2), (0.1, 0.0), name="left_stem",    pressure=_DOWN),
    _s((0.1, 0.0), (0.3, -0.1), (0.5, -0.1), (0.6, 0.0), name="base_arch",  pressure=_BODY),
    _s((0.6, 0.0), (0.6, 0.5), (0.6, 1.2), (0.6, 1.8),   name="right_stem", pressure=_UP),
], w=0.72)

_catalog["V"] = _g("V", 0x56, [
    _s((0.0, 1.8), (0.1, 1.1), (0.2, 0.5), (0.3, 0.0), name="left_arm",     pressure=_DOWN),
    _s((0.3, 0.0), (0.4, 0.5), (0.5, 1.1), (0.6, 1.8),  name="right_arm",   pressure=_UP),
], w=0.62)

_catalog["W"] = _g("W", 0x57, [
    _s((0.0, 1.8), (0.1, 1.0), (0.15, 0.4), (0.2, 0.0),  name="v1_left",  pressure=_DOWN),
    _s((0.2, 0.0), (0.3, 0.7), (0.35, 1.3), (0.4, 1.8),  name="v1_right", pressure=_UP),
    _s((0.4, 1.8), (0.5, 1.0), (0.55, 0.4), (0.6, 0.0),  name="v2_left",  pressure=_DOWN),
    _s((0.6, 0.0), (0.7, 0.7), (0.75, 1.3), (0.8, 1.8),  name="v2_right", pressure=_UP),
], w=0.85)

_catalog["X"] = _g("X", 0x58, [
    _s((0.0, 1.8), (0.2, 1.2), (0.4, 0.6), (0.6, 0.0), name="diag_left",   pressure=_DOWN),
    _s((0.6, 1.8), (0.4, 1.2), (0.2, 0.6), (0.0, 0.0), name="diag_right",  pressure=_DOWN),
], w=0.62)

_catalog["Y"] = _g("Y", 0x59, [
    _s((0.0, 1.8), (0.15, 1.3), (0.25, 0.9), (0.3, 0.6), name="left_arm",   pressure=_DOWN),
    _s((0.6, 1.8), (0.45, 1.3), (0.35, 0.9), (0.3, 0.6), name="right_arm",  pressure=_DOWN),
    _s((0.3, 0.6), (0.3, 0.2), (0.3, -0.2), (0.3, -0.5), name="stem_desc",  pressure=_DOWN),
], w=0.62)

_catalog["Z"] = _g("Z", 0x5A, [
    _s((0.0, 1.8), (0.2, 1.8), (0.4, 1.8), (0.6, 1.8),    name="top_bar",   pressure=_FINE),
    _s((0.6, 1.8), (0.4, 1.2), (0.2, 0.6), (0.0, 0.0),    name="diagonal",  pressure=_DOWN),
    _s((0.0, 0.0), (0.2, 0.0), (0.4, 0.0), (0.6, 0.0),    name="bot_bar",   pressure=_FINE),
], w=0.60)

# ---------------------------------------------------------------------------
# Latin-specific forms
# ---------------------------------------------------------------------------

# ae digraph — a + e connected
_catalog["ae"] = _g("ae", 0xE6, [
    *_catalog["a"].strokes,
    # e portion offset to the right
    _s((0.6, 0.5), (0.55, 0.6), (0.55, 0.9), (0.85, 0.9),  name="e_top_arc", pressure=_BODY),
    _s((0.85, 0.9), (0.95, 0.5), (0.85, 0.0), (0.6, 0.0),  name="e_body",    pressure=_DOWN),
    _s((0.57, 0.5), (0.65, 0.5), (0.75, 0.5), (0.88, 0.5), name="e_mid_bar", pressure=_FINE),
], w=0.95)

# oe digraph — o + e connected
_catalog["oe"] = _g("oe", 0x153, [
    *_catalog["o"].strokes,
    _s((0.58, 0.5), (0.55, 0.6), (0.55, 0.9), (0.85, 0.9),  name="e_top_arc", pressure=_BODY),
    _s((0.85, 0.9), (0.95, 0.5), (0.85, 0.0), (0.58, 0.0),  name="e_body",    pressure=_DOWN),
    _s((0.57, 0.5), (0.65, 0.5), (0.75, 0.5), (0.88, 0.5),  name="e_mid_bar", pressure=_FINE),
], w=0.92)

# s — alias for round_s (default non-positional form; lookup() handles register-aware routing)
_catalog["s"] = _g("s", 0x73, [
    _s((0.35, 0.88), (0.08, 0.98), (-0.03, 0.72), (0.0, 0.5), name="upper_arc", pressure=_ENTRY),
    _s((0.0, 0.5), (-0.02, 0.18), (0.22, -0.02), (0.42, 0.12),   name="lower_arc", pressure=_DOWN),
    _s((0.42, 0.12), (0.52, 0.22), (0.5, 0.62), (0.38, 0.82),   name="right_arc", pressure=_EXIT),
], w=0.48)

# section mark §
_catalog["section"] = _g("section", 0xA7, [
    _s((0.45, 1.75), (0.1, 1.85), (0.0, 1.6), (0.1, 1.4), name="top_arc",   pressure=_ENTRY),
    _s((0.1, 1.4), (0.4, 1.2), (0.5, 1.0), (0.4, 0.8),    name="upper_s",   pressure=_BODY),
    _s((0.4, 0.8), (0.1, 0.6), (0.0, 0.4), (0.1, 0.2),    name="lower_s",   pressure=_BODY),
    _s((0.1, 0.2), (0.4, 0.0), (0.5, -0.2), (0.2, -0.3),  name="bot_arc",   pressure=_EXIT),
], w=0.52)

# paragraph mark ¶ (pilcrow)
_catalog["pilcrow"] = _g("pilcrow", 0xB6, [
    _s((0.3, 0.0), (0.3, 0.5), (0.3, 1.0), (0.3, 1.8), name="right_stem",  pressure=_DOWN),
    _s((0.2, 0.0), (0.2, 0.5), (0.2, 1.0), (0.2, 1.8), name="left_stem",   pressure=_DOWN),
    _s((0.2, 1.8), (0.3, 1.9), (0.5, 1.9), (0.6, 1.7), name="bowl_top",    pressure=_BODY),
    _s((0.6, 1.7), (0.65, 1.4), (0.5, 1.1), (0.2, 1.1), name="bowl_bot",   pressure=_EXIT),
], w=0.55)

# ---------------------------------------------------------------------------
# Uppercase umlauts Ä Ö Ü
# ---------------------------------------------------------------------------

_catalog["A_umlaut"] = _g("A_umlaut", 0xC4, [
    *_catalog["A"].strokes,
    _s((0.15, 2.05), (0.2, 2.1), (0.25, 2.1), (0.3, 2.05), name="umlaut_dot1", pressure=_FINE),
    _s((0.35, 2.05), (0.4, 2.1), (0.45, 2.1), (0.5, 2.05), name="umlaut_dot2", pressure=_FINE),
], w=0.65)

_catalog["O_umlaut"] = _g("O_umlaut", 0xD6, [
    *_catalog["O"].strokes,
    _s((0.1, 2.05), (0.15, 2.1), (0.2, 2.1), (0.25, 2.05),  name="umlaut_dot1", pressure=_FINE),
    _s((0.35, 2.05), (0.4, 2.1), (0.45, 2.1), (0.5, 2.05),  name="umlaut_dot2", pressure=_FINE),
], w=0.60)

_catalog["U_umlaut"] = _g("U_umlaut", 0xDC, [
    *_catalog["U"].strokes,
    _s((0.15, 2.05), (0.2, 2.1), (0.25, 2.1), (0.3, 2.05),  name="umlaut_dot1", pressure=_FINE),
    _s((0.4, 2.05), (0.45, 2.1), (0.5, 2.1), (0.55, 2.05),  name="umlaut_dot2", pressure=_FINE),
], w=0.72)

# ---------------------------------------------------------------------------
# Arabic digits 0-9 (used for folio numbers, dates)
# ---------------------------------------------------------------------------

_catalog["0"] = _g("0", 0x30, [
    _s((0.25, 1.0), (0.0, 1.0), (0.0, 0.0), (0.25, 0.0), name="left_arc",  pressure=_DOWN),
    _s((0.25, 0.0), (0.5, 0.0), (0.5, 1.0), (0.25, 1.0), name="right_arc", pressure=_UP),
], w=0.50)

_catalog["1"] = _g("1", 0x31, [
    _s((0.1, 0.8), (0.15, 0.9), (0.2, 1.0), (0.25, 1.0), name="serif_in", pressure=_ENTRY),
    _s((0.25, 1.0), (0.25, 0.5), (0.25, 0.2), (0.25, 0.0), name="stem",   pressure=_DOWN),
], w=0.35)

_catalog["2"] = _g("2", 0x32, [
    _s((0.05, 0.75), (0.05, 1.0), (0.25, 1.1), (0.45, 0.9), name="top_arc",  pressure=_ENTRY),
    _s((0.45, 0.9), (0.45, 0.7), (0.3, 0.5), (0.0, 0.0),   name="diagonal", pressure=_DOWN),
    _s((0.0, 0.0), (0.2, 0.0), (0.4, 0.0), (0.5, 0.0),     name="foot",     pressure=_FINE),
], w=0.50)

_catalog["3"] = _g("3", 0x33, [
    _s((0.05, 1.0), (0.2, 1.1), (0.45, 1.0), (0.45, 0.65), name="top_arc",  pressure=_BODY),
    _s((0.45, 0.65), (0.45, 0.5), (0.3, 0.5), (0.2, 0.5),  name="mid_bar",  pressure=_FINE),
    _s((0.2, 0.5), (0.4, 0.5), (0.5, 0.35), (0.5, 0.15),   name="bot_arc1", pressure=_BODY),
    _s((0.5, 0.15), (0.5, 0.0), (0.3, -0.05), (0.05, 0.1), name="bot_arc2", pressure=_EXIT),
], w=0.50)

_catalog["4"] = _g("4", 0x34, [
    _s((0.4, 0.0), (0.4, 0.4), (0.4, 0.8), (0.4, 1.0), name="stem",      pressure=_DOWN),
    _s((0.4, 0.5), (0.3, 0.7), (0.15, 0.9), (0.0, 1.0), name="arm",       pressure=_UP),
    _s((0.0, 0.5), (0.15, 0.5), (0.3, 0.5), (0.5, 0.5), name="crossbar",  pressure=_FINE),
], w=0.52)

_catalog["5"] = _g("5", 0x35, [
    _s((0.45, 1.0), (0.25, 1.0), (0.1, 1.0), (0.05, 1.0), name="top_bar",  pressure=_FINE),
    _s((0.05, 1.0), (0.05, 0.7), (0.05, 0.5), (0.05, 0.5), name="stem",    pressure=_DOWN),
    _s((0.05, 0.5), (0.2, 0.6), (0.45, 0.55), (0.5, 0.35), name="bow_top", pressure=_BODY),
    _s((0.5, 0.35), (0.5, 0.1), (0.35, -0.02), (0.1, 0.0), name="bow_bot", pressure=_EXIT),
], w=0.50)

_catalog["6"] = _g("6", 0x36, [
    _s((0.45, 1.0), (0.1, 1.1), (0.0, 0.7), (0.0, 0.4),   name="top_arc",  pressure=_ENTRY),
    _s((0.0, 0.4), (0.0, 0.1), (0.2, 0.0), (0.4, 0.1),    name="lower_arc", pressure=_DOWN),
    _s((0.4, 0.1), (0.5, 0.3), (0.5, 0.55), (0.35, 0.7),  name="lobe_arc", pressure=_BODY),
    _s((0.35, 0.7), (0.15, 0.65), (0.02, 0.55), (0.0, 0.4), name="lobe_close", pressure=_EXIT),
], w=0.50)

_catalog["7"] = _g("7", 0x37, [
    _s((0.0, 1.0), (0.2, 1.0), (0.4, 1.0), (0.5, 1.0), name="top_bar",  pressure=_FINE),
    _s((0.5, 1.0), (0.4, 0.65), (0.3, 0.35), (0.2, 0.0), name="stroke", pressure=_DOWN),
], w=0.48)

_catalog["8"] = _g("8", 0x38, [
    _s((0.25, 0.5), (0.0, 0.6), (0.0, 1.0), (0.25, 1.0), name="upper_l",  pressure=_ENTRY),
    _s((0.25, 1.0), (0.5, 1.0), (0.5, 0.6), (0.25, 0.5), name="upper_r",  pressure=_EXIT),
    _s((0.25, 0.5), (0.0, 0.45), (0.0, 0.0), (0.25, 0.0), name="lower_l", pressure=_DOWN),
    _s((0.25, 0.0), (0.5, 0.0), (0.5, 0.45), (0.25, 0.5), name="lower_r", pressure=_UP),
], w=0.50)

_catalog["9"] = _g("9", 0x39, [
    _s((0.25, 0.5), (0.0, 0.5), (0.0, 1.0), (0.25, 1.0), name="lobe_l",  pressure=_ENTRY),
    _s((0.25, 1.0), (0.5, 1.0), (0.5, 0.5), (0.25, 0.5), name="lobe_r",  pressure=_EXIT),
    _s((0.5, 0.5), (0.5, 0.2), (0.4, 0.0), (0.1, -0.05), name="tail",    pressure=_DOWN),
], w=0.50)

# ---------------------------------------------------------------------------
# Common punctuation
# ---------------------------------------------------------------------------

_catalog["period"] = _g("period", 0x2E, [
    _s((0.1, 0.1), (0.15, 0.15), (0.2, 0.15), (0.25, 0.1), name="dot", pressure=_FINE),
], w=0.25)

_catalog["comma"] = _g("comma", 0x2C, [
    _s((0.1, 0.1), (0.15, 0.15), (0.15, 0.0), (0.1, -0.1), name="comma", pressure=_FINE),
], w=0.25)

_catalog["colon"] = _g("colon", 0x3A, [
    _s((0.1, 0.7), (0.15, 0.75), (0.2, 0.75), (0.25, 0.7), name="upper_dot", pressure=_FINE),
    _s((0.1, 0.1), (0.15, 0.15), (0.2, 0.15), (0.25, 0.1), name="lower_dot", pressure=_FINE),
], w=0.28)

_catalog["hyphen"] = _g("hyphen", 0x2D, [
    _s((0.0, 0.5), (0.12, 0.5), (0.25, 0.5), (0.35, 0.5), name="dash", pressure=_FINE),
], w=0.38)

_catalog["semicolon"] = _g("semicolon", 0x3B, [
    _s((0.1, 0.7), (0.15, 0.75), (0.2, 0.75), (0.25, 0.7), name="upper_dot",  pressure=_FINE),
    _s((0.1, 0.1), (0.15, 0.15), (0.15, 0.0), (0.1, -0.1), name="lower_comma", pressure=_FINE),
], w=0.28)

_catalog["exclamation"] = _g("exclamation", 0x21, [
    _s((0.2, 1.0), (0.2, 0.6), (0.2, 0.4), (0.2, 0.2), name="stem",   pressure=_DOWN),
    _s((0.15, 0.1), (0.2, 0.12), (0.25, 0.12), (0.3, 0.1), name="dot", pressure=_FINE),
], w=0.30)

_catalog["question"] = _g("question", 0x3F, [
    _s((0.05, 0.8), (0.05, 1.0), (0.3, 1.1), (0.5, 0.9),  name="top_arc",    pressure=_ENTRY),
    _s((0.5, 0.9), (0.5, 0.65), (0.35, 0.5), (0.25, 0.3), name="hook",       pressure=_DOWN),
    _s((0.2, 0.1), (0.25, 0.12), (0.3, 0.12), (0.35, 0.1), name="dot",       pressure=_FINE),
], w=0.48)

# macron (abbreviation mark — horizontal line above word)
_catalog["macron"] = _g("macron", 0x305, [
    _s((0.0, 1.3), (0.15, 1.3), (0.35, 1.3), (0.5, 1.3), name="macron", pressure=_FINE),
], w=0.50)

# con-ligature (Tironian con — abbreviation for Latin 'con-')
_catalog["con"] = _g("con", 0x204B, [
    _s((0.0, 0.7), (0.0, 1.0), (0.3, 1.0), (0.4, 0.7),   name="top_arc",  pressure=_ENTRY),
    _s((0.4, 0.7), (0.4, 0.3), (0.3, 0.0), (0.0, 0.0),   name="bot_arc",  pressure=_EXIT),
    _s((0.1, 0.5), (0.25, 0.5), (0.35, 0.5), (0.4, 0.5), name="crossbar", pressure=_FINE),
], w=0.45)

# et-ligature (Tironian et &-equivalent)
_catalog["et"] = _g("et", 0x204A, [
    _s((0.3, 1.0), (0.1, 1.1), (0.0, 0.8), (0.0, 0.5),  name="top_loop",   pressure=_ENTRY),
    _s((0.0, 0.5), (0.0, 0.2), (0.1, 0.0), (0.3, 0.0),  name="lower_loop", pressure=_DOWN),
    _s((0.3, 0.0), (0.5, 0.0), (0.55, 0.2), (0.5, 0.5), name="right_arc",  pressure=_UP),
    _s((0.5, 0.5), (0.4, 0.6), (0.35, 0.5), (0.3, 0.0), name="cross",      pressure=_DOWN),
], w=0.55)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Canonical catalog (the public GLYPH_CATALOG export)
GLYPH_CATALOG: dict[str, Glyph] = dict(_catalog)


def lookup(char: str, register: str = "german") -> Glyph:
    """Resolve a character + register to the correct Glyph variant.

    German register: medial 's' → long_s; Latin register: 's' → round_s.
    Uppercase is looked up by the character directly.

    Args:
        char:     Single Unicode character or digraph string (e.g. "ae").
        register: "german" or "latin".

    Returns:
        The matching Glyph.

    Raises:
        KeyError: If no glyph is defined for the character.
    """
    # German-specific remaps
    if register == "german" and char == "s":
        return GLYPH_CATALOG["long_s"]
    if register == "latin" and char == "s":
        return GLYPH_CATALOG["round_s"]

    if char in GLYPH_CATALOG:
        return GLYPH_CATALOG[char]

    raise KeyError(f"No glyph defined for character {char!r} (register={register!r})")
