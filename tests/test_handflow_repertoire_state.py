import json
import os
import subprocess
import sys
from dataclasses import asdict, replace

import pytest

from scribesim.evofit.repertoire import seed_repertoire
from scribesim.handflow.execution import PersistentRepertoireSession, require_g2
from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.planning import build_track_plan
from scribesim.pathguide.repertoire import convert_word


def test_contact_distance_is_the_only_consumption_point_and_dip_is_explicit():
    hand = seed_repertoire("in")
    session = PersistentRepertoireSession(hand, seed=7, controls=RepertoireControls(ink=True, ink_per_mm=.01))
    session.write_text("in in")
    state = session.state
    assert state.consumed_ink > 0
    assert state.ink_reservoir < 1
    for row in state.execution_trace:
        expected = min(row["ink_before"], row["contact_mm"] * .01 * row["pressure"] / .5)
        assert row["consumed"] == pytest.approx(expected)
        if not row["contact"] or not row["previous_contact"]:
            assert row["consumed"] == 0
    before = (state.time_s, state.fatigue, state.rhythm_phase, state.habit_phase)
    session.boundary(force_dip=True)
    assert state.ink_reservoir == 1
    assert (state.time_s, state.fatigue, state.rhythm_phase, state.habit_phase) == before
    assert state.events[-1]["kind"] == "dip"
    assert 1 - state.consumed_ink + state.refilled_ink == pytest.approx(state.ink_reservoir)


def test_plan_container_splits_do_not_reset_state_or_add_consumption():
    hand = seed_repertoire("in")
    plan = build_track_plan(convert_word("in", hand).guide, base_speed_mm_s=12, stop_at_end=False)
    whole = PersistentRepertoireSession(hand, seed=9, controls=RepertoireControls(ink=True))
    whole.write_plan(plan)
    split = PersistentRepertoireSession(hand, seed=9, controls=RepertoireControls(ink=True))
    midpoint = len(plan.samples) // 2
    split.write_plan(replace(plan, samples=plan.samples[:midpoint + 1]))
    split.write_plan(replace(plan, samples=plan.samples[midpoint:]))
    for field in ("time_s", "fatigue", "ink_reservoir", "consumed_ink", "rhythm_phase", "habit_phase"):
        assert getattr(split.state, field) == pytest.approx(getattr(whole.state, field))
    assert split.state.trace == whole.state.trace


def test_pause_line_return_and_sitting_break_preserve_motor_identity():
    hand = seed_repertoire("in")
    session = PersistentRepertoireSession(hand, seed=11, controls=RepertoireControls(ink=True))
    session.write_text("in\nin")
    state = session.state
    ink, phase, time = state.ink_reservoir, state.habit_phase, state.time_s
    session.pause(3, kind="sitting_break")
    assert state.ink_reservoir == ink
    assert state.habit_phase == phase
    assert state.time_s == pytest.approx(time + 3)
    assert {row["kind"] for row in state.events} >= {"word_boundary", "line_return", "sitting_break"}
    before = state.consumed_ink
    session.pause(0)
    assert state.consumed_ink == before


def test_hash_seed_independent_replay_and_bounded_changed_seed():
    script = """
import json,sys
from scribesim.evofit.repertoire import seed_repertoire
from scribesim.handflow.execution import PersistentRepertoireSession
from scribesim.handflow.controls import RepertoireControls
from scribesim.handvalidate.specimen import object_digest
session=PersistentRepertoireSession(seed_repertoire('in'),seed=int(sys.argv[1]),controls=RepertoireControls(ink=True,pressure=.1,angle_deg=3,rhythm=.1))
session.write_text('in in')
print(object_digest(session.export()))
"""
    hashes = [subprocess.check_output([sys.executable, "-c", script, "17"], env={**os.environ, "PYTHONHASHSEED": value})
              for value in ("1", "839")]
    assert hashes[0] == hashes[1]
    changed = subprocess.check_output([sys.executable, "-c", script, "19"])
    assert changed != hashes[0]
    with pytest.raises(ValueError):
        RepertoireControls(angle_deg=30)


def test_g2_summary_is_not_an_execution_authorization(tmp_path):
    (tmp_path / "G2.json").write_text('{"gate":"G2","status":"pass"}')
    with pytest.raises(ValueError, match="G2"):
        require_g2(tmp_path, nominal_root=tmp_path)


def test_neutral_repertoire_nib_contract_and_air_tangents():
    from scribesim.handvalidate.bridge import compare_bridge
    hand = seed_repertoire("in")
    bundle = convert_word("in", hand)
    session = PersistentRepertoireSession(hand, seed=1)
    result = session.write_plan(build_track_plan(bundle.guide, base_speed_mm_s=12, stop_at_end=False))
    measured = compare_bridge(bundle, hand, result=result)["metrics"]
    assert measured["width_delta_mm"] == 0
    assert measured["actual_image_loss"] < .2
    session._air_to((-10, 20), kind="line_return")
    assert session.state.pos_x_mm < 0
    assert session.state.ink_reservoir == 1
