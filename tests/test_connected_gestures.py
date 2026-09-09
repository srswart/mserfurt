import copy
from dataclasses import asdict
import math

import pytest

from scribesim.evofit import connected_contract as contract
from scribesim.evofit.stroke_language import seed_language
from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide, migrate_v1, validate_gestures
from scribesim.handvalidate.specimen import object_digest
from scribesim.pathguide.gesture_actions import action_bundle, execute_actions, load_actions


def connected_model(transition='corner'):
    model = migrate_v1(seed_language())
    model.update(schema_version=contract.SCHEMA, sampling='gesture-arc-v3', scope='synthetic contact contract only')
    model['primitives'] = {}
    model['gestures'] = {}
    for name, start, end in [('down', [0, 1], [0, 0]), ('up', [0, 0], [0, 1])]:
        direction = [end[axis] - start[axis] for axis in (0, 1)]
        model['primitives'][name] = {'cubics': [[start,
            [start[axis] + direction[axis] / 3 for axis in (0, 1)],
            [start[axis] + 2 * direction[axis] / 3 for axis in (0, 1)], end]],
            'entry': direction, 'exit': direction, 'closed': False, 'provenance': 'synthetic contract fixture'}
        model['gestures'][name] = {'action': 'fixed', 'strokes': [{'primitive': name,
            'offset': [0, 0], 'scale': 1, 'rotation_deg': 0, 'transition': 'start'}]}
    instances = [{'gesture': 'down', 'offset': [0, 0], 'scale': 1, 'rotation_deg': 0,
                  'transition': 'start', 'overlap_with': []},
                 {'gesture': 'up', 'offset': [0, 0], 'scale': 1, 'rotation_deg': 0,
                  'transition': transition, 'overlap_with': [0]}]
    if transition == 'smooth':
        instances[1].update(gesture='down', offset=[0, -1], overlap_with=[])
    model['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 1, 'gestures': instances}}
    return model


@pytest.mark.parametrize('transition', ['smooth', 'corner', 'lift'])
def test_contact_runs_are_distinct_from_gesture_ownership(transition):
    model = connected_model(transition)
    plan = compile_gestures('ii', model)
    assert len({row['gesture_occurrence_id'] for row in plan['strokes']}) == 4
    assert len({row['contact_run_id'] for row in plan['strokes']}) == (4 if transition == 'lift' else 2)
    bundle = gesture_guide('ii', model, include_curve_positions=True)
    owners = bundle.metadata['owners']
    for identifier in {row['contact_run_id'] for row in plan['strokes']}:
        indices = [index for index, owner in enumerate(owners) if owner.get('contact_run_id') == identifier]
        assert indices == list(range(min(indices), max(indices) + 1))
        assert all(bundle.guide.samples[index].contact for index in indices)
    assert any(not sample.contact for sample in bundle.guide.samples)


def test_connected_boundary_has_one_sample_and_explicit_action_progress():
    bundle = gesture_guide('i', connected_model(), include_curve_positions=True)
    assert all(sample.contact and sample.pressure_nominal == .5 for sample in bundle.guide.samples)
    boundaries = [(sample, owner) for sample, owner in zip(bundle.guide.samples, bundle.metadata['owners'])
                  if owner.get('boundary_contributors')]
    assert len(boundaries) == 1
    sample, owner = boundaries[0]
    assert (sample.x_mm, sample.y_mm) == (0, 10)
    assert owner['gesture_occurrence_id'] == '0:1'
    assert owner['gesture_progress'] == 0
    assert [(row['gesture_occurrence_id'], row['gesture_progress']) for row in owner['boundary_contributors']] == [('0:0', 1), ('0:1', 0)]
    assert owner['overlap_contributors'] == ['0:0']
    assert bundle.metadata['owners'][-1]['gesture_progress'] == 1


@pytest.mark.parametrize('fault', ['gap', 'smooth-reversal', 'missing-overlap', 'port', 'tool', 'action', 'sampling', 'legacy', 'cap', 'gesture-cap'])
def test_connected_contract_rejects_unsafe_or_implicit_changes(fault):
    model = connected_model()
    instances = model['recipes']['i']['gestures']
    if fault == 'gap':
        instances[1]['offset'][0] = .00001
    elif fault == 'smooth-reversal':
        instances[1]['transition'] = 'smooth'
    elif fault == 'missing-overlap':
        instances[1]['overlap_with'] = []
    elif fault == 'port':
        model['primitives']['up']['entry'] = [.1, .99498743710662]
    elif fault == 'tool':
        model['nib_width_mm'] = .46
    elif fault == 'action':
        model['actions']['fixed']['edge'][1] = [1, 0, .5]
    elif fault == 'sampling':
        model['sampling'] = 'gesture-arc-v2'
    elif fault == 'legacy':
        model['schema_version'] = 'shared-stroke-gestures-v2'
    elif fault == 'gesture-cap':
        model['gestures']['down']['strokes'] *= 5
    else:
        model['gestures']['down']['strokes'] = [
            {'primitive': 'down' if index % 2 == 0 else 'up', 'offset': [0, 0], 'scale': 1,
             'rotation_deg': 0, 'transition': 'start' if index == 0 else 'corner'} for index in range(4)]
        instances[1].update(gesture='down', transition='corner')
    with pytest.raises(ValueError):
        validate_gestures(model)


def test_parallel_finite_width_overlap_requires_owner_without_crossing():
    model = connected_model('lift')
    model['recipes']['i']['gestures'][1].update(offset=[.04, 0], overlap_with=[])
    with pytest.raises(ValueError, match='overlap'):
        validate_gestures(model)
    model['recipes']['i']['gestures'][1]['overlap_with'] = [0]
    validate_gestures(model)


@pytest.mark.parametrize('transition', ['smooth', 'corner', 'lift'])
def test_actual_controller_preserves_contact_and_corner_clock(transition):
    result = execute_actions('i', connected_model(transition), dpi=72)
    assert result['execution_version'] == 'event-time-v2'
    assert result['clock_version'] == 'curve-tangent-v1'
    assert result['metrics']['contact_errors'] == 0
    assert result['metrics']['time_error_s'] <= 1e-10
    assert result['metrics']['corridor_error_mm'] <= .25
    assert len({row['gesture_occurrence_id'] for row in result['owners'] if row['kind'] == 'stroke'}) == 2
    assert all(point['contact'] for point in result['trajectory']) == (transition != 'lift')
    assert len(result['corners']) == (1 if transition == 'corner' else 0)
    for corner in result['corners']:
        point = result['desired_plan']['samples'][corner['plan_index']]
        assert point['contact'] and point['speed_mm_s'] == 0
        realized = [row for row in result['execution'] if row['time_s'] == corner['time_s']]
        assert realized and all(row['contact'] for row in realized)
    assert result['S1_action_accepted'] is False


def test_connected_bundle_pins_new_code_and_rejects_changed_identity(tmp_path, monkeypatch):
    import scribesim.pathguide.gesture_actions as bridge
    model = connected_model()
    bundle = action_bundle('i', model)
    assert 'scribesim/evofit/connected_contract.py' in bundle.code_sha256
    from scribesim.handvalidate.specimen import write_json
    path = tmp_path / 'bundle.json'
    payload = asdict(bundle)
    write_json(path, {'payload': payload, 'sha256': object_digest(payload)})
    assert load_actions(path, model) == bundle
    original = bridge.code_identities
    monkeypatch.setattr(bridge, 'code_identities', lambda: {**original(), 'changed-source': '0' * 64})
    with pytest.raises(ValueError, match='Stale'):
        load_actions(path, model)


@pytest.mark.parametrize('sampling,expected', [
    ('legacy-v1', 'f13ac5105bdbf1aaa718b9fc6bf0311dcb329a4595c656f4fbd3f0f60a55b900'),
    ('gesture-arc-v3', '93aa7085585314d51e50ba5b466344e9b450c6ce923ca548ab8cf2d8c7456a9e')])
def test_legacy_guide_bytes_are_unchanged(sampling, expected):
    model = migrate_v1(seed_language())
    model['sampling'] = sampling
    assert object_digest(asdict(gesture_guide('i u', model))) == expected


def test_boundary_names_the_last_incoming_primitive_not_the_first():
    model = connected_model()
    source = model['gestures']['down']['strokes'][0]
    model['gestures']['down']['strokes'] = [
        {**source, 'scale': .5, 'offset': [0, .5]},
        {**source, 'scale': .5, 'offset': [0, 0], 'transition': 'smooth'}]
    compiled = compile_gestures('i', model)['strokes']
    bundle = gesture_guide('i', model)
    owner = next(owner for owner in bundle.metadata['owners'] if owner.get('boundary_contributors'))
    assert owner['boundary_contributors'][0]['occurrence_id'] == compiled[1]['occurrence_id']


def test_six_references_remain_supported_without_a_macro_cap_bypass():
    model = connected_model()
    for name, sequence in [('down', ['down', 'up', 'down']), ('up', ['up', 'down', 'up'])]:
        model['gestures'][name]['strokes'] = [
            {'primitive': primitive, 'offset': [0, 0], 'scale': 1, 'rotation_deg': 0,
             'transition': 'start' if index == 0 else 'corner'} for index, primitive in enumerate(sequence)]
    assert len(compile_gestures('i', model)['strokes']) == 6


def test_undeclared_internal_cubic_corner_is_rejected_before_execution():
    model = connected_model()
    model['primitives']['up']['cubics'] = [
        [[0, 0], [0, .2], [0, .4], [.1, .5]],
        [[.1, .5], [.1, .6], [0, .8], [0, 1]]]
    with pytest.raises(ValueError, match='Internal cubic'):
        validate_gestures(model)


@pytest.mark.parametrize('fault', ['actual-lift', 'owner'])
def test_actual_contact_and_owner_controls_cannot_report_tracking_pass(monkeypatch, fault):
    import scribesim.pathguide.gesture_actions as bridge
    if fault == 'actual-lift':
        from dataclasses import replace
        original = bridge.ActionController.step
        def wrong_contact(controller, state, desired, *, dt):
            result = original(controller, state, desired, dt=dt)
            if desired.contact and desired.progress_ratio > .5:
                state.trace[-1] = replace(state.trace[-1], contact=False, pressure=0)
            return result
        monkeypatch.setattr(bridge.ActionController, 'step', wrong_contact)
    else:
        original = bridge.action_bundle
        def wrong_owner(*args, **kwargs):
            bundle = original(*args, **kwargs)
            for owner in bundle.owners:
                if owner.get('gesture_occurrence_id') == '0:1':
                    owner['contact_run_id'] = 'forged'
            return bundle
        monkeypatch.setattr(bridge, 'action_bundle', wrong_owner)
    result = execute_actions('i', connected_model(), dpi=72)
    assert not result['tracking_pass']
    assert result['metrics']['contact_errors'] + result['metrics']['owner_errors'] > 0


def test_actual_corner_and_clock_survive_refinement_without_fitting():
    results = [execute_actions('i', connected_model(), step_mm=step, dt=timestep, dpi=72)
               for step, timestep in [(.025, .002), (.0125, .002), (.025, .001)]]
    for result in results:
        assert result['tracking_pass']
        assert result['metrics']['owner_errors'] == 0
        assert result['metrics']['corner_errors'] == 0
        assert result['metrics']['corner_speed_mm_s'] <= .5
        assert result['metrics']['corner_position_error_mm'] <= .05
        assert result['desired_plan']['samples'][-1]['t_s'] == pytest.approx(
            results[0]['desired_plan']['samples'][-1]['t_s'], abs=1e-10)
        for row in result['execution']:
            if row['dt_s'] == 0:
                assert row['from_mm'] == row['to_mm']
                assert row['velocity_before_mm_s'] == row['velocity_mm_s']
            else:
                assert math.dist(row['velocity_before_mm_s'], row['velocity_mm_s']) / row['dt_s'] <= 250 + 1e-6
