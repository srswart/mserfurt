"""Evolutionary engine — selection, crossover, mutation, main loop (TD-007 Part 3).

Evolves word genomes through generations of selection, crossover, and
layer-specific mutation. The population is seeded from letterform guides
and refined by the multi-criteria fitness function.
"""

from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from scribesim.evo.genome import WordGenome, GlyphGenome, BezierSegment, genome_from_guides
from scribesim.evo.fitness import evaluate_fitness, FitnessResult
from scribesim.evo.style import StylePrior


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class EvolutionConfig:
    """Configuration for an evolution run."""
    pop_size: int = 50
    generations: int = 100
    elite_count: int = 3
    tournament_size: int = 5
    crossover_rate: float = 0.7
    early_stop_fitness: float = 0.90
    eval_dpi: float = 900.0
    nib_width_mm: float = 1.0


# ---------------------------------------------------------------------------
# Baseline placement
# ---------------------------------------------------------------------------

def initial_baseline_y_mm(x_height_mm: float) -> float:
    """Return a safe baseline placement for evolved words.

    The original evo seed baseline was hard-coded to 6mm, which leaves tall
    Bastarda capitals and ascenders above the top of the word canvas at common
    x-heights. Use the same more conservative headroom as the non-evo seed path.
    """
    return max(10.0, x_height_mm * 2.25 + 0.4)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def initialize_population(
    word_text: str,
    pop_size: int = 50,
    x_height_mm: float = 3.8,
    guides_path=None,
    seed_genomes: list[WordGenome] | None = None,
    style_prior: StylePrior | None = None,
) -> list[WordGenome]:
    """Seed the population from letterform guides with perturbation."""
    population = []
    seed_pool = list(seed_genomes or [])

    def _reflow_offsets(genome: WordGenome) -> None:
        x_cursor = 0.0
        for glyph in genome.glyphs:
            delta_x = x_cursor - glyph.x_offset
            glyph.x_offset = x_cursor
            for seg in glyph.segments:
                seg.p0 = (seg.p0[0] + delta_x, seg.p0[1])
                seg.p1 = (seg.p1[0] + delta_x, seg.p1[1])
                seg.p2 = (seg.p2[0] + delta_x, seg.p2[1])
                seg.p3 = (seg.p3[0] + delta_x, seg.p3[1])
            if glyph.connection_exit_mm is not None:
                glyph.connection_exit_mm = (glyph.connection_exit_mm[0] + delta_x, glyph.connection_exit_mm[1])
            if glyph.connection_entry_mm is not None:
                glyph.connection_entry_mm = (glyph.connection_entry_mm[0] + delta_x, glyph.connection_entry_mm[1])
            x_cursor += glyph.x_advance
        genome.word_width_mm = x_cursor

    def _seed_from_prior(base: WordGenome, sigma: float) -> WordGenome:
        genome = copy.deepcopy(base)
        if style_prior is not None and style_prior.target_slant_deg is not None:
            genome.global_slant_deg = (
                genome.global_slant_deg * 0.7
                + style_prior.target_slant_deg * 0.3
                + random.gauss(0, 0.18 * sigma)
            )
        if style_prior is not None and style_prior.avg_advances is not None and len(style_prior.avg_advances) == len(genome.glyphs):
            for idx, glyph in enumerate(genome.glyphs):
                target_adv = style_prior.avg_advances[idx]
                glyph.x_advance = max(0.25, glyph.x_advance * 0.65 + target_adv * 0.35 + random.gauss(0, 0.04 * sigma))
            _reflow_offsets(genome)
        genome.baseline_drift = [
            drift + random.gauss(0, 0.03 * sigma) for drift in genome.baseline_drift
        ]
        genome.slant_drift = [
            drift + random.gauss(0, 0.08 * sigma) for drift in genome.slant_drift
        ]
        for glyph in genome.glyphs:
            for seg in glyph.segments:
                seg.nib_angle_drift += random.gauss(0, 0.3 * sigma)
                seg.pressure_curve = [
                    max(0.1, min(1.0, p + random.gauss(0, 0.02 * sigma)))
                    for p in seg.pressure_curve
                ]
        genome.word_width_mm *= random.uniform(0.985, 1.015)
        return genome

    for i in range(pop_size):
        if seed_pool and i < max(2, min(len(seed_pool) * 2, pop_size // 2)):
            base = seed_pool[i % len(seed_pool)]
            sigma = 0.18 + (i / max(pop_size, 1)) * 0.25
            genome = _seed_from_prior(base, sigma)
        else:
            genome = genome_from_guides(
                word_text,
                baseline_y_mm=initial_baseline_y_mm(x_height_mm),
                x_height_mm=x_height_mm,
                guides_path=guides_path,
            )

            # Perturb each layer (more perturbation = more diversity)
            sigma = 0.3 + (i / pop_size) * 0.5  # first individuals are closer to guides

            # Layer 1: word envelope — small perturbation
            genome.baseline_y += random.gauss(0, 0.1 * sigma)
            genome.global_slant_deg += random.gauss(0, 0.5 * sigma)
            if style_prior is not None and style_prior.target_slant_deg is not None:
                genome.global_slant_deg = genome.global_slant_deg * 0.6 + style_prior.target_slant_deg * 0.4
            genome.baseline_drift = [random.gauss(0, 0.05 * sigma) for _ in genome.glyphs]
            genome.slant_drift = [random.gauss(0, 0.2 * sigma) for _ in genome.glyphs]

            # Layer 2: glyph shapes — anisotropic perturbation (x wider, y tiny)
            for glyph in genome.glyphs:
                for seg in glyph.segments:
                    if random.random() < 0.4:
                        dx = random.gauss(0, 0.08 * sigma)
                        dy = random.gauss(0, 0.02 * sigma)
                        seg.p1 = (seg.p1[0] + dx, seg.p1[1] + dy)
                        seg.p2 = (seg.p2[0] + dx * 0.7, seg.p2[1] + dy * 0.7)

            # Layer 3: stroke details — small perturbation
            for glyph in genome.glyphs:
                for seg in glyph.segments:
                    seg.pressure_curve = [
                        max(0.1, min(1.0, p + random.gauss(0, 0.03 * sigma)))
                        for p in seg.pressure_curve
                    ]

        population.append(genome)

    return population


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def select(
    population: list[WordGenome],
    fitnesses: list[float],
    tournament_size: int = 5,
    elite_count: int = 3,
) -> list[WordGenome]:
    """Tournament selection with elitism."""
    paired = list(zip(population, fitnesses))
    paired.sort(key=lambda x: -x[1])

    # Keep elites
    selected = [copy.deepcopy(p) for p, f in paired[:elite_count]]

    # Tournament for the rest
    while len(selected) < len(population):
        tournament = random.sample(paired, min(tournament_size, len(paired)))
        winner = max(tournament, key=lambda x: x[1])[0]
        selected.append(copy.deepcopy(winner))

    return selected


# ---------------------------------------------------------------------------
# Crossover (layer-aware)
# ---------------------------------------------------------------------------

def crossover(parent_a: WordGenome, parent_b: WordGenome) -> WordGenome:
    """Layer-aware crossover between two parents."""
    child = copy.deepcopy(parent_a)

    # Layer 1: blend word envelope
    child.baseline_y = (parent_a.baseline_y + parent_b.baseline_y) / 2
    child.global_slant_deg = (parent_a.global_slant_deg + parent_b.global_slant_deg) / 2
    child.tempo = (parent_a.tempo + parent_b.tempo) / 2

    # Layer 2: per-glyph selection
    n = min(len(parent_a.glyphs), len(parent_b.glyphs))
    for i in range(n):
        if random.random() < 0.5:
            child.glyphs[i] = copy.deepcopy(parent_b.glyphs[i])

    # Layer 3: per-segment stroke detail swap
    for i in range(min(len(child.glyphs), len(parent_b.glyphs))):
        for j in range(min(len(child.glyphs[i].segments), len(parent_b.glyphs[i].segments))):
            if random.random() < 0.3:
                src = parent_b.glyphs[i].segments[j]
                child.glyphs[i].segments[j].pressure_curve = list(src.pressure_curve)
                child.glyphs[i].segments[j].speed_curve = list(src.speed_curve)

    return child


# ---------------------------------------------------------------------------
# Mutation (layer-specific rates)
# ---------------------------------------------------------------------------

def mutate(
    genome: WordGenome,
    generation: int = 0,
    fatigue: float = 0.0,
    emotional_state: str = "normal",
) -> WordGenome:
    """Apply layer-specific mutations with contextual modifiers."""
    g = genome  # mutate in place

    # Layer 1: word envelope — rare, small (10% chance)
    if random.random() < 0.1:
        g.baseline_y += random.gauss(0, 0.1)
        g.global_slant_deg += random.gauss(0, 0.3)

    # Layer 2: glyph shapes — tiny steps on control points to preserve stroke crispness
    # Larger x-shifts allowed (changes stroke width via angle) but y kept tight (no waviness)
    for glyph in g.glyphs:
        if random.random() < 0.3:
            seg = random.choice(glyph.segments)
            dx = random.gauss(0, 0.10)   # horizontal: shifts stroke angle → thick/thin
            dy = random.gauss(0, 0.03)   # vertical: tiny only, keeps strokes straight
            seg.p1 = (seg.p1[0] + dx, seg.p1[1] + dy)

        if random.random() < 0.2:
            seg = random.choice(glyph.segments)
            dx = random.gauss(0, 0.10)
            dy = random.gauss(0, 0.03)
            seg.p2 = (seg.p2[0] + dx, seg.p2[1] + dy)

        # Small endpoint x-drift — allows evolution to close inter-glyph gaps (10% per glyph)
        if random.random() < 0.1 and glyph.segments:
            dx = random.gauss(0, 0.1)
            seg = glyph.segments[-1]
            seg.p3 = (seg.p3[0] + dx, seg.p3[1])
        if random.random() < 0.1 and glyph.segments:
            dx = random.gauss(0, 0.1)
            seg = glyph.segments[0]
            seg.p0 = (seg.p0[0] + dx, seg.p0[1])

    # Layer 3: stroke details — frequent (50% per segment)
    for glyph in g.glyphs:
        for seg in glyph.segments:
            if random.random() < 0.5:
                seg.pressure_curve = [
                    max(0.1, min(1.0, p + random.gauss(0, 0.05)))
                    for p in seg.pressure_curve
                ]
            if random.random() < 0.3:
                seg.nib_angle_drift += random.gauss(0, 0.5)

    # --- Contextual modifiers ---

    if fatigue > 0:
        boost = 1.0 + fatigue * 0.5
        for glyph in g.glyphs:
            for seg in glyph.segments:
                if random.random() < fatigue * 0.2:
                    seg.p1 = (seg.p1[0] + random.gauss(0, 0.15 * boost),
                              seg.p1[1] + random.gauss(0, 0.15 * boost))

    if emotional_state == "agitated":
        for glyph in g.glyphs:
            for seg in glyph.segments:
                seg.pressure_curve = [
                    max(0.1, min(1.0, p * random.uniform(0.9, 1.2)))
                    for p in seg.pressure_curve
                ]
        g.global_slant_deg += random.gauss(0, 0.5)

    elif emotional_state == "compensating":
        g.word_width_mm *= random.uniform(1.0, 1.08)
        g.baseline_drift = [d + random.gauss(0, 0.08) for d in g.baseline_drift]

    return g


# ---------------------------------------------------------------------------
# Main evolution loop
# ---------------------------------------------------------------------------

@dataclass
class EvolutionResult:
    """Result of an evolution run."""
    best_genome: WordGenome
    best_fitness: float
    generations_run: int
    fitness_history: list[float] = field(default_factory=list)


def evolve_word(
    word_text: str,
    target_crop: np.ndarray | None = None,
    config: EvolutionConfig | None = None,
    fatigue: float = 0.0,
    emotional_state: str = "normal",
    verbose: bool = True,
    guides_path=None,
    x_height_mm: float = 3.8,
    exemplar_root=None,
    style_prior: StylePrior | None = None,
) -> EvolutionResult:
    """Evolve a word genome through generations.

    Args:
        word_text: The word to evolve (e.g., "und").
        target_crop: Optional target manuscript word image.
        config: Evolution configuration.
        fatigue: CLIO-7 fatigue level [0, 1].
        emotional_state: CLIO-7 emotional state.
        verbose: Print progress.

    Returns:
        EvolutionResult with the best genome found.
    """
    if config is None:
        config = EvolutionConfig()

    population = initialize_population(
        word_text,
        config.pop_size,
        x_height_mm=x_height_mm,
        guides_path=guides_path,
        seed_genomes=style_prior.same_word_genomes if style_prior is not None else None,
        style_prior=style_prior,
    )

    best_ever = None
    best_fitness_ever = 0.0
    history = []

    for gen in range(config.generations):
        # Evaluate fitness
        results = [evaluate_fitness(ind, target_crop, dpi=config.eval_dpi,
                                    nib_width_mm=config.nib_width_mm,
                                    exemplar_root=exemplar_root,
                                    style_prior=style_prior)
                   for ind in population]
        fitnesses = [r.total for r in results]

        # Track best
        gen_best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
        if fitnesses[gen_best_idx] > best_fitness_ever:
            best_fitness_ever = fitnesses[gen_best_idx]
            best_ever = copy.deepcopy(population[gen_best_idx])

        history.append(best_fitness_ever)

        if verbose:
            mean_f = sum(fitnesses) / len(fitnesses)
            r = results[gen_best_idx]
            improved = "↑" if fitnesses[gen_best_idx] >= best_fitness_ever else " "
            print(f"  gen {gen:3d}{improved} best={best_fitness_ever:.3f} mean={mean_f:.3f} "
                  f"[recog={r.f1:.2f} thick_thin={r.f2:.2f} connect={r.f3:.2f} continuity={r.f7:.2f}]",
                  flush=True)

        # Early stopping
        if best_fitness_ever >= config.early_stop_fitness:
            if verbose:
                print(f"  converged at gen {gen} (fitness={best_fitness_ever:.3f})", flush=True)
            break

        # Select
        selected = select(population, fitnesses,
                          config.tournament_size, config.elite_count)

        # Crossover + mutation
        next_gen = []
        for i in range(0, len(selected) - 1, 2):
            if random.random() < config.crossover_rate:
                child = crossover(selected[i], selected[i + 1])
                next_gen.append(child)
            else:
                next_gen.append(copy.deepcopy(selected[i]))
            next_gen.append(copy.deepcopy(selected[i + 1]))

        # Pad if odd
        while len(next_gen) < config.pop_size:
            next_gen.append(copy.deepcopy(selected[0]))

        # Mutate (except elites)
        for i in range(config.elite_count, len(next_gen)):
            next_gen[i] = mutate(next_gen[i], gen, fatigue, emotional_state)

        population = next_gen[:config.pop_size]

    return EvolutionResult(
        best_genome=best_ever or population[0],
        best_fitness=best_fitness_ever,
        generations_run=gen + 1 if 'gen' in dir() else 0,
        fitness_history=history,
    )
