"""Line and folio composition for the evolutionary scribe (TD-007 Part 5+7).

Chains evolved words into lines and folios with context passing:
- Exit state from one word → starting condition for the next
- Ink depletion with dip cycles
- CLIO-7 per-folio modifiers (fatigue, emotional state)
- Warm-start caching for common words
"""

from __future__ import annotations

import copy
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scribesim.evo.genome import WordGenome, genome_from_guides
from scribesim.evo.engine import evolve_word, EvolutionConfig, EvolutionResult
from scribesim.evo.renderer import render_word_from_genome


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

@dataclass
class WordContext:
    """Context passed between consecutive words."""
    cursor_x_mm: float = 0.0
    baseline_y_mm: float = 0.0
    ink_reservoir: float = 0.85
    preceding_exit_angle: float = 0.0
    fatigue: float = 0.0
    emotional_state: str = "normal"


@dataclass
class FolioState:
    """Per-folio state from CLIO-7."""
    folio_id: str = "f01r"
    lines: list[str] = field(default_factory=list)
    margin_left_mm: float = 3.0
    margin_top_mm: float = 5.0
    line_spacing_mm: float = 9.5
    x_height_mm: float = 3.8
    page_width_mm: float = 70.0
    page_height_mm: float = 100.0
    ink_reservoir: float = 0.85
    fatigue: float = 0.0
    emotional_state: str = "normal"
    dip_cycle_words: int = 35

    @classmethod
    def from_folio_json(cls, folio_path: Path) -> "FolioState":
        """Load folio state from XL folio JSON."""
        data = json.loads(Path(folio_path).read_text())
        lines = [line.get("text", "") for line in data.get("lines", [])]
        return cls(
            folio_id=data.get("id", "f01r"),
            lines=lines,
        )


# ---------------------------------------------------------------------------
# Genome cache for common words
# ---------------------------------------------------------------------------

_GENOME_CACHE: dict[str, WordGenome] = {}


def _get_or_evolve(
    word: str,
    context: WordContext,
    config: EvolutionConfig,
    target_crop: np.ndarray | None = None,
    use_cache: bool = True,
) -> WordGenome:
    """Get a cached genome for common words, or evolve a new one."""
    cache_key = f"{word}_{context.emotional_state}"

    if use_cache and cache_key in _GENOME_CACHE:
        # Return a perturbed copy of the cached genome
        cached = copy.deepcopy(_GENOME_CACHE[cache_key])
        # Small perturbation for instance variation
        cached.baseline_y = context.baseline_y_mm
        for i in range(len(cached.baseline_drift)):
            cached.baseline_drift[i] += random.gauss(0, 0.03)
        return cached

    result = evolve_word(
        word,
        target_crop=target_crop,
        config=config,
        fatigue=context.fatigue,
        emotional_state=context.emotional_state,
        verbose=False,
    )

    if use_cache:
        _GENOME_CACHE[cache_key] = copy.deepcopy(result.best_genome)

    return result.best_genome


# ---------------------------------------------------------------------------
# Line composition
# ---------------------------------------------------------------------------

@dataclass
class EvolvedLine:
    """A composed line of evolved words."""
    line_index: int
    words: list[WordGenome]
    baseline_y_mm: float
    total_width_mm: float
    best_fitness: float = 0.0


def evolve_line(
    line_text: str,
    line_index: int,
    folio_state: FolioState,
    config: EvolutionConfig | None = None,
    target_line_crop: np.ndarray | None = None,
    verbose: bool = True,
) -> EvolvedLine:
    """Evolve all words in a line with context passing."""
    if config is None:
        config = EvolutionConfig(pop_size=30, generations=50, eval_dpi=72.0)

    words = line_text.split()
    if not words:
        return EvolvedLine(line_index, [], 0.0, 0.0)

    baseline_y = folio_state.margin_top_mm + line_index * folio_state.line_spacing_mm
    word_spacing_mm = folio_state.x_height_mm * 0.8

    context = WordContext(
        cursor_x_mm=folio_state.margin_left_mm,
        baseline_y_mm=baseline_y,
        ink_reservoir=folio_state.ink_reservoir,
        fatigue=folio_state.fatigue,
        emotional_state=folio_state.emotional_state,
    )

    evolved_words = []
    word_count = 0

    for i, word in enumerate(words):
        genome = _get_or_evolve(word, context, config)

        # Adjust position: shift all segment coordinates to the correct baseline and x
        dy = context.baseline_y_mm - genome.baseline_y
        genome.baseline_y = context.baseline_y_mm
        for g in genome.glyphs:
            g.x_offset += context.cursor_x_mm
            for seg in g.segments:
                seg.p0 = (seg.p0[0] + context.cursor_x_mm, seg.p0[1] + dy)
                seg.p1 = (seg.p1[0] + context.cursor_x_mm, seg.p1[1] + dy)
                seg.p2 = (seg.p2[0] + context.cursor_x_mm, seg.p2[1] + dy)
                seg.p3 = (seg.p3[0] + context.cursor_x_mm, seg.p3[1] + dy)

        evolved_words.append(genome)

        # Update context
        context.cursor_x_mm += genome.word_width_mm + word_spacing_mm
        context.ink_reservoir -= 0.01 * len(word)

        # Dip check
        word_count += 1
        if word_count % folio_state.dip_cycle_words == 0:
            context.ink_reservoir = 0.85  # refill

        if context.ink_reservoir < 0.15:
            context.ink_reservoir = 0.85  # emergency dip

    if verbose:
        print(f"  line {line_index}: {len(words)} words, "
              f"width={context.cursor_x_mm:.1f}mm, ink={context.ink_reservoir:.2f}")

    return EvolvedLine(
        line_index=line_index,
        words=evolved_words,
        baseline_y_mm=baseline_y,
        total_width_mm=context.cursor_x_mm,
    )


# ---------------------------------------------------------------------------
# Folio composition
# ---------------------------------------------------------------------------

@dataclass
class EvolvedFolio:
    """A complete folio of evolved lines."""
    folio_id: str
    lines: list[EvolvedLine]
    page_width_mm: float
    page_height_mm: float


def evolve_folio(
    folio_state: FolioState,
    config: EvolutionConfig | None = None,
    target_folio: np.ndarray | None = None,
    verbose: bool = True,
) -> EvolvedFolio:
    """Evolve all lines in a folio."""
    if config is None:
        config = EvolutionConfig(pop_size=20, generations=30, eval_dpi=72.0)

    evolved_lines = []

    for li, line_text in enumerate(folio_state.lines):
        if not line_text.strip():
            continue

        line = evolve_line(
            line_text, li, folio_state,
            config=config, verbose=verbose,
        )
        evolved_lines.append(line)

        # Update folio state for next line
        folio_state.ink_reservoir -= 0.02 * len(line_text.split())
        if folio_state.ink_reservoir < 0.15:
            folio_state.ink_reservoir = 0.85

    if verbose:
        print(f"Folio {folio_state.folio_id}: {len(evolved_lines)} lines evolved")

    return EvolvedFolio(
        folio_id=folio_state.folio_id,
        lines=evolved_lines,
        page_width_mm=folio_state.page_width_mm,
        page_height_mm=folio_state.page_height_mm,
    )


# ---------------------------------------------------------------------------
# Render composed folio to image
# ---------------------------------------------------------------------------

def render_folio(folio: EvolvedFolio, dpi: float = 200.0) -> np.ndarray:
    """Render an evolved folio to an RGB image.

    Each word is rendered directly onto the page canvas at its absolute
    mm coordinates (set during line composition).
    """
    from scribesim.evo.renderer import _PARCHMENT, _INK
    from scribesim.render.nib import PhysicsNib, mark_width, stroke_foot_effect, stroke_attack_effect
    import math

    px_per_mm = dpi / 25.4
    w_px = int(folio.page_width_mm * px_per_mm)
    h_px = int(folio.page_height_mm * px_per_mm)

    img = Image.new("RGB", (w_px, h_px), (245, 238, 220))
    draw = ImageDraw.Draw(img)
    nib = PhysicsNib(width_mm=0.6, angle_deg=35.0)

    for line in folio.lines:
        for genome in line.words:
            ink = genome.ink_state_start
            for gi, glyph in enumerate(genome.glyphs):
                slant_rad = math.radians(
                    genome.global_slant_deg +
                    (genome.slant_drift[gi] if gi < len(genome.slant_drift) else 0.0)
                )
                bl_off = genome.baseline_drift[gi] if gi < len(genome.baseline_drift) else 0.0

                for seg in glyph.segments:
                    if not seg.contact:
                        continue
                    for si in range(31):
                        t = si / 30.0
                        pos = seg.evaluate(t)
                        x_mm = pos[0]
                        y_mm = pos[1] + bl_off
                        y_from_base = y_mm - genome.baseline_y
                        x_mm += y_from_base * math.tan(slant_rad)

                        direction = seg.direction_deg(t)
                        pressure = seg.pressure_at(t)
                        width = mark_width(nib, direction, pressure, t)
                        fw, _ = stroke_foot_effect(t)
                        aw, _ = stroke_attack_effect(t)
                        width *= fw * aw

                        darkness = min(1.0, pressure * 0.9 * ink)
                        if darkness < 0.05:
                            continue

                        x_px = x_mm * px_per_mm
                        y_px = y_mm * px_per_mm
                        r = max(0.3, width * 0.5 * px_per_mm * 0.4)

                        c = (int(18*darkness + 245*(1-darkness)),
                             int(12*darkness + 238*(1-darkness)),
                             int(8*darkness + 220*(1-darkness)))
                        draw.ellipse([x_px-r, y_px-r, x_px+r, y_px+r], fill=c)

                    ink = max(0.0, ink - 0.002)

    return np.array(img)
