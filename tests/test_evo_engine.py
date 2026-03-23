from scribesim.evo.engine import initial_baseline_y_mm, initialize_population


def test_initial_baseline_y_mm_leaves_headroom_for_tall_caps():
    assert initial_baseline_y_mm(3.8) >= 10.0


def test_initialize_population_seeds_words_above_canvas_top():
    population = initialize_population("Ich", pop_size=1, x_height_mm=3.8)
    genome = population[0]
    top_y = min(
        pt[1]
        for glyph in genome.glyphs
        for seg in glyph.segments
        for pt in (seg.p0, seg.p1, seg.p2, seg.p3)
    )
    assert top_y >= 0.0
