import copy
from dataclasses import asdict

import numpy as np
import pytest

from scribesim.evofit import stroke_language as legacy
from scribesim.evofit.stroke_gestures import (
    compile_gestures, execute_gestures, gesture_guide, load_bundle, migrate_v1,
    render_gestures, validate_gestures,
)
from scribesim.handvalidate.specimen import object_digest, write_json


def test_explicit_migration_preserves_legacy_pixels_contact_and_spans():
    prior = legacy.seed_language()
    model = migrate_v1(prior)
    assert len(model['gestures']) == 1
    old = legacy.language_guide('i u ii\nui', prior)
    new = gesture_guide('i u ii\nui', model)
    assert asdict(old.guide) == asdict(new.guide)
    assert np.array_equal(legacy.render_language('i u', prior), render_gestures('i u', model))
    assert {row['gesture_occurrence_id'] for row in new.metadata['owners'] if row['kind'] == 'stroke'}
    assert all(row['span'] == old.metadata['owners'][index]['span']
               for index, row in enumerate(new.metadata['owners']) if row['kind'] == 'stroke')
    with pytest.raises(ValueError):
        legacy.validate_language(model)


@pytest.mark.parametrize('fault', ['cycle', 'missing', 'residual', 'budget', 'track', 'nan',
                                 'pressure', 'speed', 'frame', 'port', 'overlap', 'profile_budget'])
def test_rejects_invalid_new_contracts(fault):
    model = migrate_v1(legacy.seed_language())
    gesture = model['gestures']['gesture-0']
    if fault == 'cycle':
        gesture['gestures'] = ['gesture-0']
    elif fault == 'missing':
        gesture['strokes'][0]['primitive'] = 'missing'
    elif fault == 'residual':
        model['recipes']['i']['cubics'] = []
    elif fault == 'budget':
        model['recipes']['u']['gestures'].append(copy.deepcopy(model['recipes']['u']['gestures'][1]))
    elif fault == 'track':
        model['actions']['fixed']['orientation'] = [[0, 40], [0, 40], [1, 40]]
    elif fault == 'nan':
        model['actions']['fixed']['edge'][0][1] = float('nan')
    elif fault == 'pressure':
        model['actions']['fixed']['pressure'] = .7
    elif fault == 'speed':
        model['actions']['fixed']['speed_mm_s'] = 9
    elif fault == 'frame':
        model['actions']['fixed']['frame'] = 'unspecified'
    elif fault == 'port':
        gesture['strokes'][1]['offset'][0] = 1
    elif fault == 'overlap':
        model['recipes']['u']['gestures'][1]['overlap_with'] = [1]
    else:
        for index in range(9):
            model['actions'][str(index)] = copy.deepcopy(model['actions']['fixed'])
    with pytest.raises(ValueError):
        validate_gestures(model)


def test_dynamic_action_is_represented_but_execution_is_unsupported():
    model = migrate_v1(legacy.seed_language())
    model['actions']['fixed']['orientation'] = [[0, 40], [1, 45]]
    validate_gestures(model)
    with pytest.raises(ValueError, match='unsupported'):
        gesture_guide('i', model)


def test_gesture_sampling_has_no_internal_lifts_or_pressure_resets():
    model = migrate_v1(legacy.seed_language())
    model['sampling'] = 'gesture-arc-v2'
    bundle = gesture_guide('i u', model)
    owners = bundle.metadata['owners']
    for identifier in {owner['gesture_occurrence_id'] for owner in owners if owner['kind'] == 'stroke'}:
        indices = [index for index, owner in enumerate(owners) if owner.get('gesture_occurrence_id') == identifier]
        assert indices == list(range(min(indices), max(indices) + 1))
        assert all(bundle.guide.samples[index].contact and bundle.guide.samples[index].pressure_nominal == .5
                   for index in indices)
        assert owners[indices[0]]['gesture_progress'] == 0
        assert owners[indices[-1]]['gesture_progress'] == 1
    actual = execute_gestures('i u', model)
    assert actual['metrics']['contact_schedule_preserved']
    assert all(owner['kind'] != 'air' for owner, point in zip(actual['owners'], actual['trajectory']) if point['contact'])


def test_shared_identity_and_stale_bundle_rejection(tmp_path):
    model = migrate_v1(legacy.seed_language())
    bundle = gesture_guide('i u', model)
    payload = asdict(bundle)
    path = tmp_path / 'bundle.json'
    write_json(path, {'payload': payload, 'sha256': object_digest(payload)})
    assert load_bundle(path, model).metadata == bundle.metadata
    model['gestures']['gesture-0']['strokes'][1]['scale'] = 1.1
    assert compile_gestures('i u', model)['model_sha256'] != bundle.metadata['model_sha256']
    with pytest.raises(ValueError):
        load_bundle(path, model)


def test_migration_refuses_unqualified_context_or_crossings():
    model = legacy.seed_language()
    model['recipes']['i']['allow_crossings'] = True
    with pytest.raises(ValueError, match='migration'):
        migrate_v1(model)


def test_repartitioned_cubic_preserves_contact_path_without_boundary_pauses():
    model = migrate_v1(legacy.seed_language())
    model['sampling'] = 'gesture-arc-v2'
    before = gesture_guide('i', model)
    points = np.array(model['primitives']['stem']['cubics'][0])
    middle = (points[:-1] + points[1:]) / 2
    inner = (middle[:-1] + middle[1:]) / 2
    center = (inner[0] + inner[1]) / 2
    model['primitives']['stem']['cubics'] = [
        [points[0].tolist(), middle[0].tolist(), inner[0].tolist(), center.tolist()],
        [center.tolist(), inner[1].tolist(), middle[2].tolist(), points[-1].tolist()]]
    after = gesture_guide('i', model)
    assert len(before.guide.samples) == len(after.guide.samples)
    assert all(first.contact == second.contact for first, second in zip(before.guide.samples, after.guide.samples))
    assert max(np.hypot(first.x_mm - second.x_mm, first.y_mm - second.y_mm)
               for first, second in zip(before.guide.samples, after.guide.samples)) < .001


def test_declared_overlap_retains_two_lifted_contributors():
    model = migrate_v1(legacy.seed_language())
    model['sampling'] = 'gesture-arc-v2'
    model['recipes']['u']['gestures'][1].update(offset=[0, 0], overlap_with=[0])
    bundle = gesture_guide('u', model)
    assert any(not sample.contact for sample in bundle.guide.samples)
    assert any(owner.get('overlap_contributors') == ['0:0'] for owner in bundle.metadata['owners'])


def test_action_rate_and_falsely_smooth_corner_are_rejected():
    model = migrate_v1(legacy.seed_language())
    model['actions']['fixed']['orientation'] = [[0, 40], [.001, 50], [1, 50]]
    with pytest.raises(ValueError, match='rate'):
        validate_gestures(model)


def test_actual_contact_corridor_excludes_pen_up_travel():
    model = migrate_v1(legacy.seed_language())
    model['sampling'] = 'gesture-arc-v2'
    result = execute_gestures('i u', model)
    assert result['metrics']['corridor_error_mm'] <= .25
    model = migrate_v1(legacy.seed_language())
    model['gestures']['gesture-0']['strokes'][1]['transition'] = 'smooth'
    with pytest.raises(ValueError, match='Smooth'):
        validate_gestures(model)
