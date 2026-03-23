"""Contextual allograph selection for repeat-heavy Bastarda letters.

This is a bounded alternative to free-form per-glyph mutation. Each supported
letter has a small family of legal variants, and selection is driven by
position, neighbours, and contextual style memory.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass

import numpy as np

from scribesim.evo.genome import GlyphGenome, WordGenome, BezierSegment
from scribesim.evo.style import GlyphPrior, StyleMemory
from scribesim.glyphs.catalog import GLYPH_CATALOG


@dataclass
class AllographConfig:
    randomness: float = 0.10


def _glyph_signature(glyph: GlyphGenome) -> np.ndarray:
    dims: list[float] = [glyph.x_advance]
    span = max(glyph.x_advance, 0.4)
    for seg in glyph.segments[:6]:
        for pt in (seg.p0, seg.p1, seg.p2, seg.p3):
            dims.append((pt[0] - glyph.x_offset) / span)
            dims.append(pt[1] / 4.0)
    if len(dims) < 48:
        dims.extend([0.0] * (48 - len(dims)))
    return np.array(dims[:48], dtype=np.float32)


def _shift_segment(seg: BezierSegment, dx: float = 0.0, dy: float = 0.0) -> None:
    seg.p0 = (seg.p0[0] + dx, seg.p0[1] + dy)
    seg.p1 = (seg.p1[0] + dx, seg.p1[1] + dy)
    seg.p2 = (seg.p2[0] + dx, seg.p2[1] + dy)
    seg.p3 = (seg.p3[0] + dx, seg.p3[1] + dy)


def _reflow_from(genome: WordGenome, start_idx: int) -> None:
    x_cursor = genome.glyphs[0].x_offset if genome.glyphs else 0.0
    for idx, glyph in enumerate(genome.glyphs):
        if idx == 0:
            x_cursor = glyph.x_offset
        elif idx >= start_idx:
            dx = x_cursor - glyph.x_offset
            glyph.x_offset += dx
            for seg in glyph.segments:
                _shift_segment(seg, dx=dx)
            if glyph.connection_entry_mm is not None:
                glyph.connection_entry_mm = (glyph.connection_entry_mm[0] + dx, glyph.connection_entry_mm[1])
            if glyph.connection_exit_mm is not None:
                glyph.connection_exit_mm = (glyph.connection_exit_mm[0] + dx, glyph.connection_exit_mm[1])
        x_cursor = glyph.x_offset + glyph.x_advance
    genome.word_width_mm = x_cursor


def _catalog_glyph(letter: str, glyph_id: str, x_offset: float, baseline_y_mm: float, x_height_mm: float) -> GlyphGenome:
    glyph = GLYPH_CATALOG[glyph_id]
    segments: list[BezierSegment] = []
    for stroke in glyph.strokes:
        pts = stroke.control_points
        segments.append(BezierSegment(
            p0=(x_offset + pts[0][0] * x_height_mm, baseline_y_mm - pts[0][1] * x_height_mm),
            p1=(x_offset + pts[1][0] * x_height_mm, baseline_y_mm - pts[1][1] * x_height_mm),
            p2=(x_offset + pts[2][0] * x_height_mm, baseline_y_mm - pts[2][1] * x_height_mm),
            p3=(x_offset + pts[3][0] * x_height_mm, baseline_y_mm - pts[3][1] * x_height_mm),
            contact=True,
            pressure_curve=list(stroke.pressure_profile),
        ))
    raw_exit = glyph.strokes[-1].control_points[-1]
    raw_entry = glyph.strokes[0].control_points[0]
    conn_exit = None
    conn_entry = None
    if glyph.exit_point != raw_exit:
        conn_exit = (x_offset + glyph.exit_point[0] * x_height_mm, baseline_y_mm - glyph.exit_point[1] * x_height_mm)
    if glyph.entry_point != raw_entry:
        conn_entry = (x_offset + glyph.entry_point[0] * x_height_mm, baseline_y_mm - glyph.entry_point[1] * x_height_mm)
    return GlyphGenome(
        letter=letter,
        segments=segments,
        x_offset=x_offset,
        x_advance=glyph.advance_width * x_height_mm,
        connection_exit_mm=conn_exit,
        connection_entry_mm=conn_entry,
    )


def _variant_names(letter: str, is_final: bool, prev_letter: str | None, next_letter: str | None) -> list[str]:
    ch = letter.lower()
    if ch == "s":
        return ["round_final"] if is_final else ["long_medial"]
    if ch == "i":
        names = ["plain", "lean", "compact"]
        if prev_letter and prev_letter.lower() in {"m", "n", "u", "v"}:
            names = ["compact", "plain", "lean"]
        return names
    if ch == "n":
        names = ["plain", "tight", "open"]
        if next_letter and next_letter.lower() in {"i", "r", "t"}:
            names = ["tight", "plain", "open"]
        return names
    if ch == "e":
        names = ["plain", "closed", "open"]
        if next_letter and next_letter.lower() in {"r", "n", "m"}:
            names = ["closed", "plain", "open"]
        return names
    if ch == "r":
        names = ["plain", "hooked", "flat"]
        if is_final:
            names = ["flat", "plain", "hooked"]
        return names
    return ["plain"]


def _apply_variant(glyph: GlyphGenome, letter: str, variant: str, x_height_mm: float, baseline_y_mm: float) -> GlyphGenome:
    g = copy.deepcopy(glyph)
    ch = letter.lower()
    u = x_height_mm

    if ch == "s":
        if variant == "round_final":
            return _catalog_glyph(letter, "round_s", glyph.x_offset, baseline_y_mm, x_height_mm)
        if variant == "long_medial":
            return _catalog_glyph(letter, "long_s", glyph.x_offset, baseline_y_mm, x_height_mm)

    if ch == "i":
        if variant == "lean":
            g.segments[0].p2 = (g.segments[0].p2[0] + 0.012 * u, g.segments[0].p2[1])
            g.segments[0].p3 = (g.segments[0].p3[0] + 0.008 * u, g.segments[0].p3[1])
            if len(g.segments) > 1:
                _shift_segment(g.segments[1], dx=0.010 * u)
        elif variant == "compact":
            g.x_advance = max(0.24 * u, g.x_advance - 0.015 * u)
            if len(g.segments) > 1:
                _shift_segment(g.segments[1], dy=0.015 * u)

    elif ch == "n":
        if variant == "tight":
            g.segments[1].p1 = (g.segments[1].p1[0] - 0.012 * u, g.segments[1].p1[1])
            g.segments[1].p2 = (g.segments[1].p2[0] - 0.010 * u, g.segments[1].p2[1] - 0.008 * u)
            _shift_segment(g.segments[2], dx=-0.015 * u)
            g.x_advance = max(0.34 * u, g.x_advance - 0.020 * u)
        elif variant == "open":
            g.segments[1].p1 = (g.segments[1].p1[0], g.segments[1].p1[1] - 0.010 * u)
            g.segments[1].p2 = (g.segments[1].p2[0] + 0.012 * u, g.segments[1].p2[1] - 0.010 * u)
            _shift_segment(g.segments[2], dx=0.010 * u)
            g.x_advance += 0.010 * u

    elif ch == "e":
        if variant == "closed":
            g.segments[1].p1 = (g.segments[1].p1[0] - 0.008 * u, g.segments[1].p1[1])
            g.segments[1].p2 = (g.segments[1].p2[0] - 0.012 * u, g.segments[1].p2[1] + 0.008 * u)
            g.segments[2].p3 = (g.segments[2].p3[0] - 0.015 * u, g.segments[2].p3[1])
            g.x_advance = max(0.32 * u, g.x_advance - 0.012 * u)
        elif variant == "open":
            g.segments[0].p2 = (g.segments[0].p2[0] + 0.008 * u, g.segments[0].p2[1])
            g.segments[1].p1 = (g.segments[1].p1[0] + 0.015 * u, g.segments[1].p1[1])
            g.segments[2].p3 = (g.segments[2].p3[0] + 0.008 * u, g.segments[2].p3[1])
            g.x_advance += 0.010 * u

    elif ch == "r":
        if variant == "hooked":
            g.segments[1].p1 = (g.segments[1].p1[0], g.segments[1].p1[1] - 0.010 * u)
            g.segments[1].p2 = (g.segments[1].p2[0] + 0.010 * u, g.segments[1].p2[1] - 0.008 * u)
            g.segments[1].p3 = (g.segments[1].p3[0] + 0.008 * u, g.segments[1].p3[1] - 0.006 * u)
        elif variant == "flat":
            g.segments[1].p1 = (g.segments[1].p1[0] - 0.006 * u, g.segments[1].p1[1] + 0.006 * u)
            g.segments[1].p2 = (g.segments[1].p2[0], g.segments[1].p2[1] + 0.010 * u)
            g.segments[1].p3 = (g.segments[1].p3[0], g.segments[1].p3[1] + 0.006 * u)

    return g


def _prior_score(candidate: GlyphGenome, prior: GlyphPrior) -> float:
    if not prior.same_letter_glyphs:
        return 0.60
    sig = _glyph_signature(candidate)
    prior_sigs = [_glyph_signature(g) for g in prior.same_letter_glyphs]
    mean_sig = np.mean(prior_sigs, axis=0)
    dist = float(np.linalg.norm(sig - mean_sig))
    shape_score = max(0.0, 1.0 - dist / 0.55)
    if prior.advance_mean_mm is None:
        return shape_score
    sigma = max(prior.advance_sigma_mm or 0.08, 0.08)
    adv_score = max(0.0, 1.0 - abs(candidate.x_advance - prior.advance_mean_mm) / (sigma * 2.0))
    return 0.75 * shape_score + 0.25 * adv_score


def apply_contextual_allographs(
    genome: WordGenome,
    word_text: str,
    style_memory: StyleMemory,
    x_height_mm: float,
    config: AllographConfig | None = None,
) -> WordGenome:
    cfg = config or AllographConfig()
    out = copy.deepcopy(genome)
    total = len(out.glyphs)

    for idx, glyph in enumerate(out.glyphs):
        ch = glyph.letter.lower()
        if ch not in {"i", "n", "e", "r", "s"}:
            continue
        prev_letter = word_text[idx - 1] if idx > 0 else None
        next_letter = word_text[idx + 1] if idx + 1 < len(word_text) else None
        is_final = idx == total - 1 or (next_letter is not None and not next_letter.isalpha())
        prior = style_memory.glyph_prior_for(
            glyph.letter,
            index=idx,
            total=total,
            prev_letter=prev_letter,
            next_letter=next_letter,
        )
        variants = _variant_names(glyph.letter, is_final, prev_letter, next_letter)
        candidates = [
            _apply_variant(glyph, glyph.letter, variant, x_height_mm, out.baseline_y)
            for variant in variants
        ]
        scored = []
        for variant, candidate in zip(variants, candidates):
            jitter = random.uniform(-cfg.randomness, cfg.randomness)
            scored.append((_prior_score(candidate, prior) + jitter, variant, candidate))
        scored.sort(key=lambda item: item[0], reverse=True)
        out.glyphs[idx] = scored[0][2]
        _reflow_from(out, idx)

    return out
