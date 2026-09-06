import copy
import math

import pytest

from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide, migrate_v1
from scribesim.evofit.stroke_language import seed_language
from scribesim.handflow.planning import build_track_plan


def source(model=None, step=.025):
    model = copy.deepcopy(model or migrate_v1(seed_language()))
    model['sampling'] = 'gesture-arc-v3'
    bundle = gesture_guide('i', model, step_mm=step)
    return (build_track_plan(bundle.guide, base_speed_mm_s=12),
            bundle.metadata['owners'], compile_gestures('i', model)['strokes'])


def test_declared_corner_stops_without_lift_or_geometry_change():
    from scribesim.handflow.planning import retime_corner_timing

    original, owners, rows = source()
    timed = retime_corner_timing(original, owners, rows)
    assert timed.version == 'corner-time-v1'
    assert len(timed.corners) == 1
    assert timed.source_indices == tuple(range(len(original.samples)))
    for before, after in zip(original.samples, timed.plan.samples):
        assert (before.x_mm, before.y_mm, before.contact, before.pressure, before.nib_angle_deg) == (
            after.x_mm, after.y_mm, after.contact, after.pressure, after.nib_angle_deg)
        assert 0 <= after.speed_mm_s <= 12
    corner = timed.plan.samples[timed.corners[0]['plan_index']]
    assert corner.contact and corner.speed_mm_s == corner.vx_mm_s == corner.vy_mm_s == 0
    assert corner.x_mm == pytest.approx(rows[1]['cubics'][0][0][0] * original.x_height_mm)
    assert corner.y_mm == pytest.approx(10 - rows[1]['cubics'][0][0][1] * original.x_height_mm)
    for before, after in zip(timed.plan.samples, timed.plan.samples[1:]):
        assert after.t_s > before.t_s
        assert math.dist((before.vx_mm_s, before.vy_mm_s), (after.vx_mm_s, after.vy_mm_s)) <= 250 * (after.t_s - before.t_s) + 1e-8


def test_corner_clock_is_stable_under_arc_refinement_and_exact_subdivision():
    from scribesim.handflow.planning import retime_corner_timing
    from scribesim.handvalidate.gestures import _subdivide

    model = migrate_v1(seed_language())
    results = [retime_corner_timing(*source(model, .025)), retime_corner_timing(*source(model, .0125)),
               retime_corner_timing(*source(_subdivide(model), .025))]
    for result in results[1:]:
        assert result.plan.total_time_s == pytest.approx(results[0].plan.total_time_s, abs=.0001)
        assert result.corners[0]['time_s'] == pytest.approx(results[0].corners[0]['time_s'], abs=.0001)


def test_smooth_port_is_not_treated_as_a_corner():
    from scribesim.handflow.planning import retime_corner_timing

    original, owners, rows = source()
    rows[1]['transition'] = 'smooth'
    with pytest.raises(ValueError, match='smooth'):
        retime_corner_timing(original, owners, rows)


def test_corner_timing_rejects_missing_owner_or_exact_port():
    from dataclasses import replace
    from scribesim.handflow.planning import retime_corner_timing

    original, owners, rows = source()
    with pytest.raises(ValueError):
        retime_corner_timing(original, owners[:-1], rows)
    broken = list(original.samples)
    corner_index = next(index for index, point in enumerate(broken) if point.y_mm == 10)
    broken[corner_index] = replace(broken[corner_index], x_mm=broken[corner_index].x_mm + .001)
    with pytest.raises(ValueError, match='port'):
        retime_corner_timing(replace(original, samples=tuple(broken)), owners, rows)


def test_curvature_limit_is_geometric_and_subdivision_invariant():
    from scribesim.handflow.planning import cubic_curvature_max

    cubic = [[0, 0], [0, 1], [1, 1], [1, 0]]
    halves = [[[0, 0], [0, .5], [.25, .75], [.5, .75]],
              [[.5, .75], [.75, .75], [1, .5], [1, 0]]]
    assert cubic_curvature_max(cubic) == pytest.approx(8 / 3)
    assert max(cubic_curvature_max(part) for part in halves) == pytest.approx(cubic_curvature_max(cubic))
    assert cubic_curvature_max([[0, 0], [1, 0], [2, 0], [3, 0]]) == 0
    with pytest.raises(ValueError):
        cubic_curvature_max([[0, 0]] * 4)


def test_contact_rest_instant_is_executed_on_the_global_clock():
    from dataclasses import replace
    from scribesim.handflow.controller import GuidedHandFlowController
    from scribesim.handflow.controls import RepertoireControls
    from scribesim.handvalidate.bridge import neutral_profile

    original, _, _ = source()
    points = original.samples[:3]
    points = (points[0], replace(points[1], t_s=.0031, speed_mm_s=0, vx_mm_s=0, vy_mm_s=0),
              replace(points[2], t_s=.01))
    controller = GuidedHandFlowController(neutral_profile(seed_language()),
        repertoire_controls=RepertoireControls(), execution_version='event-time-v2')
    result = controller.follow_plan(replace(original, samples=points), dt=.002, settle_time_s=0)
    assert any(row['time_s'] == .0031 and row['contact'] for row in result.final_state.execution_trace)


def test_motion_gate_requires_independent_desired_and_corner_checks():
    from scribesim.handvalidate.foundation_motion import SPEC, decide_motion, identities, LOWER_HASHES

    checks = {f'{name}:{label}:{metric}': True for name in SPEC['fixture_families']
              for label in ('base', 'arc', 'time', 'subdivision')
              for metric in ('time', 'corridor', 'image', 'ownership', 'no_projection', 'entry', 'mechanics')}
    checks.update({f'{name}:{label}:convergence': True for name in SPEC['fixture_families']
                   for label in ('arc', 'time', 'subdivision')})
    checks.update({'physical:arc': True, 'physical:time': True, 'physical:tracking': True})
    baseline = {'status': 'pass', 'current_code_sha256': identities(), 'historical_sha256': LOWER_HASHES}
    assert not decide_motion(checks, baseline)['primitive_training_permitted']
