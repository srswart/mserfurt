"""Experimental character-deep refinement for evo rendering.

This pass runs after word-level evolution. It nudges each glyph occurrence away
from exact guide-like sameness while keeping it within the current folio hand.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass

import numpy as np

from scribesim.evo.fitness import evaluate_fitness
from scribesim.evo.genome import GlyphGenome, WordGenome
from scribesim.evo.style import GlyphPrior, StyleMemory


@dataclass
class CharacterModelConfig:
    rounds: int = 2
    candidates_per_round: int = 6
    eval_dpi: float = 180.0


def _glyph_signature(glyph: GlyphGenome) -> np.ndarray:
    dims: list[float] = [glyph.x_advance]
    span = max(glyph.x_advance, 0.4)
    for seg in glyph.segments[:6]:
        for pt in (seg.p0, seg.p1, seg.p2, seg.p3):
            dims.append((pt[0] - glyph.x_offset) / span)
            dims.append(pt[1] / 4.0)
        dims.append(seg.nib_angle_drift / 8.0)
        dims.append(sum(seg.pressure_curve) / max(len(seg.pressure_curve), 1))
    if len(dims) < 64:
        dims.extend([0.0] * (64 - len(dims)))
    return np.array(dims[:64], dtype=np.float32)


def _shift_glyph(glyph: GlyphGenome, dx: float) -> None:
    glyph.x_offset += dx
    for seg in glyph.segments:
        seg.p0 = (seg.p0[0] + dx, seg.p0[1])
        seg.p1 = (seg.p1[0] + dx, seg.p1[1])
        seg.p2 = (seg.p2[0] + dx, seg.p2[1])
        seg.p3 = (seg.p3[0] + dx, seg.p3[1])
    if glyph.connection_exit_mm is not None:
        glyph.connection_exit_mm = (glyph.connection_exit_mm[0] + dx, glyph.connection_exit_mm[1])
    if glyph.connection_entry_mm is not None:
        glyph.connection_entry_mm = (glyph.connection_entry_mm[0] + dx, glyph.connection_entry_mm[1])


def _reflow_from(genome: WordGenome, start_idx: int) -> None:
    x_cursor = genome.glyphs[0].x_offset if genome.glyphs else 0.0
    for idx, glyph in enumerate(genome.glyphs):
        if idx == 0:
            x_cursor = glyph.x_offset
        elif idx >= start_idx:
            dx = x_cursor - glyph.x_offset
            _shift_glyph(glyph, dx)
        x_cursor = glyph.x_offset + glyph.x_advance
    genome.word_width_mm = x_cursor


def _blend_from_prior(glyph: GlyphGenome, prior: GlyphPrior, intensity: float) -> None:
    compatible = [
        g for g in prior.same_letter_glyphs
        if len(g.segments) == len(glyph.segments)
    ]
    if not compatible:
        return
    source = random.choice(compatible)
    for seg, src in zip(glyph.segments, source.segments):
        mix = 0.06 + 0.06 * intensity
        seg.p1 = (
            seg.p1[0] * (1.0 - mix) + src.p1[0] * mix,
            seg.p1[1] * (1.0 - mix) + src.p1[1] * mix,
        )
        seg.p2 = (
            seg.p2[0] * (1.0 - mix) + src.p2[0] * mix,
            seg.p2[1] * (1.0 - mix) + src.p2[1] * mix,
        )
        seg.nib_angle_drift = seg.nib_angle_drift * (1.0 - mix) + src.nib_angle_drift * mix


def _mutate_glyph(glyph: GlyphGenome, prior: GlyphPrior, intensity: float) -> None:
    if prior.same_letter_glyphs:
        _blend_from_prior(glyph, prior, intensity)

    sigma_x = 0.035 + 0.035 * intensity
    sigma_y = 0.010 + 0.010 * intensity
    for seg in glyph.segments:
        if random.random() < 0.80:
            seg.p1 = (seg.p1[0] + random.gauss(0, sigma_x), seg.p1[1] + random.gauss(0, sigma_y))
        if random.random() < 0.80:
            seg.p2 = (seg.p2[0] + random.gauss(0, sigma_x), seg.p2[1] + random.gauss(0, sigma_y))
        if random.random() < 0.55:
            seg.nib_angle_drift += random.gauss(0, 0.35 + 0.25 * intensity)
        if random.random() < 0.55:
            seg.pressure_curve = [
                max(0.08, min(1.0, p + random.gauss(0, 0.022 + 0.010 * intensity)))
                for p in seg.pressure_curve
            ]

    if prior.advance_mean_mm is not None:
        target = prior.advance_mean_mm + random.gauss(0, max(prior.advance_sigma_mm or 0.08, 0.08))
        glyph.x_advance = max(0.22, glyph.x_advance * 0.65 + target * 0.35)
    else:
        glyph.x_advance = max(0.22, glyph.x_advance + random.gauss(0, 0.03 + 0.02 * intensity))


def _novelty_score(glyph: GlyphGenome, prior: GlyphPrior) -> float:
    if not prior.same_letter_glyphs:
        return 0.55
    sig = _glyph_signature(glyph)
    dists = [
        float(np.linalg.norm(sig - _glyph_signature(prev)))
        for prev in prior.same_letter_glyphs
    ]
    min_dist = min(dists)
    target = 0.10
    tolerance = 0.10
    return max(0.0, 1.0 - abs(min_dist - target) / tolerance)


def _family_score(glyph: GlyphGenome, prior: GlyphPrior) -> float:
    if prior.advance_mean_mm is None:
        return 0.55
    sigma = max(prior.advance_sigma_mm or 0.08, 0.08)
    return max(0.0, 1.0 - abs(glyph.x_advance - prior.advance_mean_mm) / (sigma * 2.5))


def _score_candidate(genome: WordGenome, glyph_idx: int, prior: GlyphPrior, dpi: float, nib_width_mm: float) -> float:
    base = evaluate_fitness(genome, dpi=dpi, nib_width_mm=nib_width_mm).total
    glyph = genome.glyphs[glyph_idx]
    novelty = _novelty_score(glyph, prior)
    family = _family_score(glyph, prior)
    return 0.76 * base + 0.18 * family + 0.06 * novelty


def refine_word_characters(
    genome: WordGenome,
    style_memory: StyleMemory,
    nib_width_mm: float,
    config: CharacterModelConfig | None = None,
) -> WordGenome:
    cfg = config or CharacterModelConfig()
    best = copy.deepcopy(genome)

    for glyph_idx, glyph in enumerate(best.glyphs):
        prev_letter = best.glyphs[glyph_idx - 1].letter if glyph_idx > 0 else None
        next_letter = best.glyphs[glyph_idx + 1].letter if glyph_idx + 1 < len(best.glyphs) else None
        prior = style_memory.glyph_prior_for(
            glyph.letter,
            index=glyph_idx,
            total=len(best.glyphs),
            prev_letter=prev_letter,
            next_letter=next_letter,
        )
        compatible = [
            g for g in prior.same_letter_glyphs
            if len(g.segments) == len(glyph.segments)
        ]
        if len(compatible) < 2:
            continue
        prior.same_letter_glyphs = compatible
        best_score = _score_candidate(best, glyph_idx, prior, cfg.eval_dpi, nib_width_mm)
        for round_idx in range(cfg.rounds):
            for _ in range(cfg.candidates_per_round):
                candidate = copy.deepcopy(best)
                intensity = 0.7 + round_idx * 0.35
                _mutate_glyph(candidate.glyphs[glyph_idx], prior, intensity)
                if glyph_idx < len(candidate.baseline_drift):
                    candidate.baseline_drift[glyph_idx] += random.gauss(0, 0.03 * intensity)
                if glyph_idx < len(candidate.slant_drift):
                    candidate.slant_drift[glyph_idx] += random.gauss(0, 0.10 * intensity)
                _reflow_from(candidate, glyph_idx)
                score = _score_candidate(candidate, glyph_idx, prior, cfg.eval_dpi, nib_width_mm)
                if score > best_score:
                    best = candidate
                    best_score = score
    return best
