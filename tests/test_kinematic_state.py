"""Unit tests for ADV-SS-STATE-002: Coarticulated ScribeState, Word-Initial
Attack & Cross-Word Air Momentum Carryover, Continuous Ink Cycle (TD-010),
CLIO-7 Folio Modifiers, and Tier-1 A5-ANTI-CLONE Gate.
"""

from __future__ import annotations

import math
import pytest

from scribesim.handflow.coarticulate import compose_line_kinematic_Stateful
from scribesim.handvalidate.kinematic_gates import evaluate_a5_anti_clone
from scribesim.render.scribe_state import (
    KinematicScribeSession,
    resolve_clio7_kinematic_profile,
)


def test_word_initial_attack_and_cross_word_momentum_variation() -> None:
    """Words starting with the same letter have distinct word-initial nuances from air carryover & ScribeState."""
    session = KinematicScribeSession(folio_id="f01r", seed=1457)
    line_res = compose_line_kinematic_Stateful(
        "alle der alleine an",
        session=session,
        line_index=0,
    )
    assert len(line_res.word_results) == 4

    # Compare the first letter 'a' trajectory (normalized to its word origin) across "alle", "alleine", "an"
    a_words = [line_res.word_results[0], line_res.word_results[2], line_res.word_results[3]]
    initial_traces: list[list[tuple[float, float]]] = []
    for w_res in a_words:
        x0 = w_res.placed_via_points[0].x_wnib
        # Collect solved via-points of the first letter (letter_index == 0)
        pts = [
            (
                float(w_res.solved_x_wnib[vp.sample_index]) - x0,
                float(w_res.solved_y_wnib[vp.sample_index]),
            )
            for vp in w_res.placed_via_points
            if vp.letter_index == 0
        ]
        initial_traces.append(pts)

    # Every pair of word-initial 'a' occurrences must differ measurably (not formulaic clones)
    for i in range(len(initial_traces)):
        for j in range(i + 1, len(initial_traces)):
            diffs = [
                math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                for p1, p2 in zip(initial_traces[i], initial_traces[j])
            ]
            max_diff = max(diffs)
            assert 0.05 <= max_diff <= 0.95, f"Pair ({i},{j}) max_diff={max_diff:.4f} w_nib"


def test_tier1_a5_anti_clone_gate_and_determinism() -> None:
    """Tier-1 A5-ANTI-CLONE proves repeated words and word-initial letters vary organically and deterministically."""
    verdict = evaluate_a5_anti_clone(
        text="und der und wir und\nalle seines alle alleine",
        folio_id="f01r",
        seed=1457,
    )
    assert verdict["gate"] == "A5-ANTI-CLONE"
    assert verdict["passed"] is True, f"A5 failed: {verdict}"
    assert verdict["min_word_dtw_wnib"] >= 0.06
    assert verdict["max_word_dtw_wnib"] <= 0.95
    assert verdict["min_initial_letter_delta_wnib"] >= 0.06

    # Determinism check: running again with the same folio_id and seed produces identical verdict
    verdict2 = evaluate_a5_anti_clone(
        text="und der und wir und\nalle seines alle alleine",
        folio_id="f01r",
        seed=1457,
    )
    assert verdict == verdict2


def test_continuous_ink_depletion_and_f07r_sitting_boundaries() -> None:
    """Ink depletes by contact arc length, stays above the 0.38 darkness floor, and reloads at f07r sittings."""
    session = KinematicScribeSession(folio_id="f07r", seed=1457)
    start_ink = session.state.ink_level
    assert start_ink == pytest.approx(1.0)

    line0 = compose_line_kinematic_Stateful(
        "in seines wercks alle der heiligen kirchen",
        session=session,
        line_index=0,
    )
    after_line0_ink = session.state.ink_level
    assert after_line0_ink < start_ink
    assert min(s.pressure for s in line0.samples if s.contact) > 0.15
    assert session.state.darkness_scale() >= 0.38

    # Advance to sitting boundary line 8 on f07r -> ink reloads for new sitting
    session.advance_to_line(8)
    assert session.state.ink_level >= 0.95
    assert session.sitting_reloads >= 1


def test_clio7_folio_modifiers_f06r_f07v_f14r() -> None:
    """CLIO-7 folio modifiers produce measurable pressure, scale, and spacing deltas."""
    p_01r = resolve_clio7_kinematic_profile("f01r", line_index=5)
    p_06r = resolve_clio7_kinematic_profile("f06r", line_index=5)
    p_07v_top = resolve_clio7_kinematic_profile("f07v", line_index=5)
    p_07v_bot = resolve_clio7_kinematic_profile("f07v", line_index=18)
    p_14r = resolve_clio7_kinematic_profile("f14r", line_index=10)

    # f06r has increased lateral pressure on downstrokes
    assert p_06r.folio.base_pressure > p_01r.folio.base_pressure

    # f07v lower half (line >= 16) shifts to smaller, more economical working register
    assert p_07v_bot.letterform.x_height_mm < p_07v_top.letterform.x_height_mm
    assert p_07v_bot.letter_spacing_norm < p_07v_top.letter_spacing_norm

    # f14r onward compensates for failing eyes with wider spacing and slower tempo
    assert p_14r.letter_spacing_norm > p_01r.letter_spacing_norm
    assert p_14r.word.spacing_mean_ratio > p_01r.word.spacing_mean_ratio
    assert p_14r.writing_speed < p_01r.writing_speed
