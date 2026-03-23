from __future__ import annotations

from scribesim.evo.fitness import evaluate_fitness
from scribesim.evo.genome import genome_from_guides
from scribesim.evo.style import StyleMemory


def test_style_memory_builds_same_word_prior():
    memory = StyleMemory()
    g1 = genome_from_guides("und", x_height_mm=1.0)
    g1.global_slant_deg = 4.5
    g2 = genome_from_guides("und", x_height_mm=1.0)
    g2.global_slant_deg = 5.0
    memory.register("und", g1)
    memory.register("und", g2)

    prior = memory.prior_for("und")
    assert prior.target_slant_deg is not None
    assert 4.6 < prior.target_slant_deg < 4.9
    assert len(prior.same_word_genomes) == 2
    assert prior.avg_advances is not None
    assert len(prior.avg_advances) == len(g1.glyphs)


def test_evaluate_fitness_accepts_style_prior():
    memory = StyleMemory()
    seed = genome_from_guides("und", x_height_mm=1.0)
    memory.register("und", seed)
    prior = memory.prior_for("und")

    candidate = genome_from_guides("und", x_height_mm=1.0)
    result = evaluate_fitness(candidate, style_prior=prior)
    assert 0.0 <= result.f4 <= 1.0
    assert 0.0 <= result.total <= 1.0


def test_glyph_prior_prefers_contextual_history():
    memory = StyleMemory()
    g1 = genome_from_guides("lich", x_height_mm=1.0)
    g2 = genome_from_guides("mich", x_height_mm=1.0)
    memory.register("lich", g1)
    memory.register("mich", g2)

    prior = memory.glyph_prior_for("i", index=1, total=4, prev_letter="l", next_letter="c")
    assert len(prior.same_letter_glyphs) >= 2


def test_glyph_prior_falls_back_to_generic_letter_history():
    memory = StyleMemory()
    g1 = genome_from_guides("ein", x_height_mm=1.0)
    g2 = genome_from_guides("nit", x_height_mm=1.0)
    memory.register("ein", g1)
    memory.register("nit", g2)

    prior = memory.glyph_prior_for("i", index=0, total=3, prev_letter=None, next_letter="x")
    assert len(prior.same_letter_glyphs) >= 2
