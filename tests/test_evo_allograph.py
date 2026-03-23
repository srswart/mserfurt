from __future__ import annotations

from scribesim.evo.allograph import apply_contextual_allographs
from scribesim.evo.genome import genome_from_guides
from scribesim.evo.style import StyleMemory


def _glyph_height_mm(genome, idx: int) -> float:
    pts = []
    for seg in genome.glyphs[idx].segments:
        pts.extend([seg.p0, seg.p1, seg.p2, seg.p3])
    top = min(p[1] for p in pts)
    return genome.baseline_y - top


def test_contextual_allograph_uses_round_s_at_word_end():
    memory = StyleMemory()
    genome = genome_from_guides("das", baseline_y_mm=10.0, x_height_mm=3.8)

    out = apply_contextual_allographs(genome, "das", memory, x_height_mm=3.8)

    assert _glyph_height_mm(out, 2) < 5.0


def test_contextual_allograph_preserves_glyph_count_and_reflows_width():
    memory = StyleMemory()
    genome = genome_from_guides("sines", baseline_y_mm=10.0, x_height_mm=3.8)

    out = apply_contextual_allographs(genome, "sines", memory, x_height_mm=3.8)

    assert len(out.glyphs) == len(genome.glyphs)
    assert out.word_width_mm > 0.0
    assert out.glyphs[-1].x_offset + out.glyphs[-1].x_advance <= out.word_width_mm + 1e-6
