import math

import pytest

from scribesim.evofit.stroke_language import seed_language
from scribesim.handflow.controller import GuidedHandFlowController
from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.model import TrackPlan, TrackPlanSample
from scribesim.handvalidate.bridge import neutral_profile


def sample(time, horizontal, contact=True):
    return TrackPlanSample(time, horizontal, horizontal, 0, 12, 0, 12,
                           .5 if contact else 0, 40, contact, .2)


def plan(samples):
    return TrackPlan('timing-fixture', tuple(samples), 3.5, 1)


def controller(version='event-time-v1'):
    return GuidedHandFlowController(neutral_profile(seed_language()),
                                    repertoire_controls=RepertoireControls(),
                                    execution_version=version)


def test_event_time_has_no_segment_floor_or_zero_settling():
    desired = plan([sample(0, 0), sample(.0005, .006), sample(.0015, .018)])
    result = controller().follow_plan(desired, dt=.002, settle_time_s=0)
    assert result.final_state.time_s == pytest.approx(.0015, abs=1e-12)
    assert all(row['time_s'] - row['time_before'] <= .002 + 1e-12
               for row in result.final_state.execution_trace)


def test_zero_duration_lift_and_reentry_preserve_pose_velocity_and_owners():
    desired = plan([sample(0, 0), sample(.01, .12), sample(.01, .12, False),
                    sample(.01, .12), sample(.02, .24)])
    result = controller().follow_plan(desired, dt=.002, settle_time_s=0)
    events = [(point, index, row) for point, index, row in
              zip(result.trajectory, result.trajectory_plan_indices, result.final_state.execution_trace)
              if row['time_s'] == row['time_before']]
    assert [index for _, index, _ in events] == [0, 2, 3]
    for point, index, row in events:
        assert [point.x_mm, point.y_mm] == row['from_mm']
        assert row['velocity_before_mm_s'] == row['velocity_mm_s']
        assert point.contact == desired.samples[index].contact
        assert row['time_s'] == pytest.approx(desired.samples[index].t_s, abs=1e-12)
    assert result.final_state.time_s == pytest.approx(.02, abs=1e-12)


def test_event_time_interpolation_is_invariant_to_exact_linear_subdivision():
    coarse = plan([sample(0, 0), sample(.02, .24), sample(.04, .48)])
    dense = plan([sample(index / 1000, index * .012) for index in range(41)])
    first = controller().follow_plan(coarse, dt=.002, settle_time_s=0)
    second = controller().follow_plan(dense, dt=.002, settle_time_s=0)
    assert math.dist((first.final_state.pos_x_mm, first.final_state.pos_y_mm),
                     (second.final_state.pos_x_mm, second.final_state.pos_y_mm)) < .001
    assert first.final_state.time_s == pytest.approx(second.final_state.time_s, abs=1e-12)


def test_event_time_never_projects_a_distant_contact_position():
    desired = plan([sample(0, 0), sample(.01, .12)])
    engine = controller()
    state = engine.initial_state(desired)
    state.pos_x_mm = -2
    engine.step(state, desired.samples[0], dt=0)
    assert state.pos_x_mm == -2
    assert state.vel_x_mm_s == 0
    assert engine.step(state, desired.samples[1], dt=.001) > .25
    assert state.pos_x_mm < -1.99


@pytest.mark.parametrize('timestep', [0, -1, float('nan'), float('inf'), True])
def test_event_time_rejects_invalid_time(timestep):
    with pytest.raises(ValueError):
        controller().follow_plan(plan([sample(0, 0), sample(.02, .24)]), dt=timestep)


def test_event_time_rejects_reversed_time_and_spatial_teleports():
    for samples in ([sample(0, 0), sample(-.01, 0)], [sample(0, 0), sample(0, 1)]):
        with pytest.raises(ValueError):
            controller().follow_plan(plan(samples), settle_time_s=0)
    with pytest.raises(ValueError):
        controller('unknown')


def test_explicit_legacy_mode_preserves_default_playback():
    desired = plan([sample(0, 0), sample(.001, .012), sample(.003, .036)])
    default = GuidedHandFlowController(neutral_profile(seed_language()),
                                      repertoire_controls=RepertoireControls())
    assert default.follow_plan(desired) == controller('legacy-v1').follow_plan(desired)


def test_baseline_revalidator_is_read_only_and_rejects_tampering(tmp_path):
    import shutil
    from scribesim.handvalidate.foundation_motion import load_historical_baseline, LOWER

    copied = tmp_path / 'lower'
    shutil.copytree(LOWER, copied)
    expected = load_historical_baseline(copied)
    assert len(expected['candidate']['primitives']) == 6
    path = copied / 'candidate.json'
    path.write_text(path.read_text().replace('3.5', '3.6'))
    with pytest.raises(ValueError, match='identity'):
        load_historical_baseline(copied)


def test_actual_motion_gate_does_not_admit_a_good_image_with_bad_geometry():
    from scribesim.handvalidate.foundation_motion import decide_motion

    checks = {'time': True, 'images': True, 'endpoints': False, 'corridor': True}
    decision = decide_motion(checks, {'status': 'pass'})
    assert decision['status'] == 'fail'
    assert not decision['baseline_admitted']
    assert not decision['primitive_training_permitted']


def test_motion_gate_rejects_partial_or_stale_check_sets():
    from scribesim.handvalidate.foundation_motion import decide_motion

    for checks in ({}, {'time': True}, {'time': True, 'images': True, 'endpoints': True, 'corridor': True}):
        decision = decide_motion(checks, {'status': 'pass'})
        assert not decision['primitive_training_permitted']


def test_new_time_modes_reject_impractically_large_step_schedules():
    with pytest.raises(ValueError, match='budget'):
        controller('event-time-v2').follow_plan(plan([sample(0, 0), sample(1, 12)]), dt=1e-12)


def test_revision_servo_remains_acceleration_limited_without_projection():
    desired = plan([sample(0, 0), sample(.1, 1.2), sample(.2, 2.4)])
    result = controller('event-time-v2').follow_plan(desired, dt=.002, settle_time_s=0)
    for row in result.final_state.execution_trace:
        duration = row['time_s'] - row['time_before']
        acceleration = math.dist(row['velocity_before_mm_s'], row['velocity_mm_s'])
        assert acceleration <= 500 * duration + 1e-9
        assert math.dist(row['to_mm'], row['desired_mm']) <= .25
        expected = [position + (before + after) * duration / 2 for position, before, after in
                    zip(row['from_mm'], row['velocity_before_mm_s'], row['velocity_mm_s'])]
        assert row['to_mm'] == pytest.approx(expected, abs=1e-12)


def test_corner_preserving_sampling_stabilizes_saved_contact_duration():
    import json
    from scribesim.curriculum.gesture_learning import BASE
    from scribesim.evofit.stroke_gestures import gesture_guide
    from scribesim.handflow.planning import build_track_plan

    model = json.loads((BASE / 'gestures/run-002/candidate.json').read_text())
    model['sampling'] = 'gesture-arc-v3'
    coarse = build_track_plan(gesture_guide('i u', model, step_mm=.025).guide, base_speed_mm_s=12)
    refined = build_track_plan(gesture_guide('i u', model, step_mm=.0125).guide, base_speed_mm_s=12)
    assert abs(coarse.total_time_s - refined.total_time_s) <= .0001
    first = controller('event-time-v2').follow_plan(coarse, dt=.002, settle_time_s=0)
    second = controller('event-time-v2').follow_plan(coarse, dt=.001, settle_time_s=0)
    assert math.dist([first.final_state.pos_x_mm, first.final_state.pos_y_mm],
                     [second.final_state.pos_x_mm, second.final_state.pos_y_mm]) <= .01


def test_physical_bridge_accepts_explicit_corner_sampling_and_execution():
    from scribesim.evofit.stroke_gestures import migrate_v1
    from scribesim.pathguide.gesture_actions import ActionController, action_bundle

    model = migrate_v1(seed_language())
    model['sampling'] = 'gesture-arc-v3'
    desired = action_bundle('u', model)
    engine = ActionController(model, execution_version='event-time-v2')
    result = engine.follow_plan(desired.plan, settle_time_s=0)
    assert all(point.contact_version == 'physical-edge-v1' for point in result.trajectory)
