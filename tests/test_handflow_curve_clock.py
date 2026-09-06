import copy
from dataclasses import replace
import json
import math

import numpy as np
import pytest

from scribesim.curriculum.gesture_learning import BASE
from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide
from scribesim.handflow.planning import build_track_plan
from scribesim.handvalidate.gestures import _subdivide


def saved_source(step=.025, subdivision=False):
    model = json.loads((BASE / 'gestures/run-002/candidate.json').read_text())
    model['sampling'] = 'gesture-arc-v3'
    if subdivision:
        model = _subdivide(model)
    bundle = gesture_guide('i u', model, step_mm=step, include_curve_positions=True)
    return build_track_plan(bundle.guide, base_speed_mm_s=12), bundle.metadata['owners'], compile_gestures('i u', model)['strokes']


def test_curve_length_is_independent_of_sampling_and_cubic_subdivision():
    from scribesim.handflow.planning import cubic_arc_length

    line = [[0, 0], [1, 0], [2, 0], [3, 0]]
    assert cubic_arc_length(line) == pytest.approx(3, abs=1e-12)
    assert cubic_arc_length(line, .5) == pytest.approx(1.5, abs=1e-12)
    cubic = [[0, 0], [0, 1], [1, 1], [1, 0]]
    left, right = [[0, 0], [0, .5], [.25, .75], [.5, .75]], [[.5, .75], [.75, .75], [1, .5], [1, 0]]
    assert cubic_arc_length(cubic) == pytest.approx(2, abs=1e-10)
    assert cubic_arc_length(left) + cubic_arc_length(right) == pytest.approx(cubic_arc_length(cubic), abs=1e-10)
    assert cubic_arc_length(cubic, .5) == pytest.approx(cubic_arc_length(left), abs=1e-10)
    for broken in ([[0, 0]] * 3, [[float('nan'), 0]] * 4):
        with pytest.raises(ValueError):
            cubic_arc_length(broken)
    for parameter in (-.1, 1.1, float('nan')):
        with pytest.raises(ValueError):
            cubic_arc_length(line, parameter)


def test_curve_integral_matches_independent_high_order_reference_and_fails_on_budget():
    from scribesim.handflow.planning import cubic_arc_length

    controls = np.array([[0, 0], [-.61, 1.45], [.84, 1.29], [0, 0]])
    nodes, weights = np.polynomial.legendre.leggauss(256)
    parameters = (nodes[:, None] + 1) / 2
    derivative = 3 * ((1 - parameters) ** 2 * (controls[1] - controls[0])
                     + 2 * (1 - parameters) * parameters * (controls[2] - controls[1])
                     + parameters ** 2 * (controls[3] - controls[2]))
    expected = float(weights @ np.linalg.norm(derivative, axis=1) / 2)
    assert cubic_arc_length(controls) == pytest.approx(expected, abs=1e-10)
    with pytest.raises(ValueError, match='budget'):
        cubic_arc_length(controls, max_depth=0)


def test_opt_in_provenance_does_not_change_either_guide_geometry():
    from scribesim.evofit.stroke_language import language_guide, seed_language
    from scribesim.evofit.stroke_gestures import migrate_v1

    language = seed_language()
    gesture = migrate_v1(language)
    gesture['sampling'] = 'gesture-arc-v3'
    for builder, model in ((language_guide, language), (gesture_guide, gesture)):
        original = builder('i u', model)
        marked = builder('i u', model, include_curve_positions=True)
        assert original.guide == marked.guide
        for before, after, sample in zip(original.metadata['owners'], marked.metadata['owners'], marked.guide.samples):
            assert before == {key: value for key, value in after.items() if key != 'curve_position'}
            assert ('curve_position' in after) == sample.contact


def test_repeated_saved_clock_converges_without_changing_corner_policy_or_geometry():
    from scribesim.handflow.planning import retime_corner_timing, retime_curve_timing

    inputs = [saved_source(), saved_source(.0125), saved_source(subdivision=True)]
    old = [retime_corner_timing(*source) for source in inputs[:2]]
    assert abs(old[0].plan.total_time_s - old[1].plan.total_time_s) > .0001
    timed = [retime_curve_timing(*source) for source in inputs]
    for result in timed[1:]:
        assert result.plan.total_time_s == pytest.approx(timed[0].plan.total_time_s, abs=1e-8)
        assert [corner['time_s'] for corner in result.corners] == pytest.approx(
            [corner['time_s'] for corner in timed[0].corners], abs=1e-8)
    for source, result in zip(inputs, timed):
        assert result.version == 'curve-time-v1'
        assert [index for point, index in zip(result.plan.samples, result.source_indices) if point.contact] == [
            index for index, point in enumerate(source[0].samples) if point.contact]
        for point, index in zip(result.plan.samples, result.source_indices):
            if point.contact:
                before = source[0].samples[index]
                assert (point.x_mm, point.y_mm, point.pressure, point.nib_angle_deg) == (
                    before.x_mm, before.y_mm, before.pressure, before.nib_angle_deg)
        for before, after in zip(result.plan.samples, result.plan.samples[1:]):
            assert after.t_s >= before.t_s
            assert math.dist((before.vx_mm_s, before.vy_mm_s), (after.vx_mm_s, after.vy_mm_s)) <= 250 * (after.t_s - before.t_s) + 1e-8


def test_curve_clock_rejects_missing_malformed_or_inconsistent_provenance():
    from scribesim.handflow.planning import retime_curve_timing

    plan, owners, strokes = saved_source()
    for change in (None, {'cubic_index': -1, 'parameter': .5, 'representation': 'chord-256'},
                   {'cubic_index': 0, 'parameter': float('nan'), 'representation': 'chord-256'},
                   {'cubic_index': 0, 'parameter': .5, 'representation': 'unknown'}):
        broken = copy.deepcopy(owners)
        broken[5]['curve_position'] = change
        with pytest.raises(ValueError, match='[Pp]rovenance'):
            retime_curve_timing(plan, broken, strokes)
    samples = list(plan.samples)
    samples[5] = replace(samples[5], x_mm=samples[5].x_mm + .001)
    with pytest.raises(ValueError, match='[Pp]rovenance'):
        retime_curve_timing(replace(plan, samples=tuple(samples)), owners, strokes)
    samples = list(plan.samples)
    broken = copy.deepcopy(owners)
    samples[5], samples[6] = replace(samples[6], t_s=samples[5].t_s), replace(samples[5], t_s=samples[6].t_s)
    broken[5], broken[6] = broken[6], broken[5]
    with pytest.raises(ValueError, match='[Pp]rovenance'):
        retime_curve_timing(replace(plan, samples=tuple(samples)), broken, strokes)


def test_fixed_action_bridge_preserves_source_parameters():
    from scribesim.pathguide.gesture_actions import action_bundle
    from scribesim.handflow.planning import retime_curve_timing

    model = json.loads((BASE / 'gestures/run-002/candidate.json').read_text())
    model['sampling'] = 'gesture-arc-v3'
    original = action_bundle('i u', model)
    marked = action_bundle('i u', model, include_curve_positions=True)
    assert original.plan == marked.plan
    timed = retime_curve_timing(marked.plan, marked.owners, compile_gestures('i u', model)['strokes'])
    assert all(point.edge_start == 0 and point.edge_end == 1 for point in timed.plan.samples)
