import copy
import json

import numpy as np
import pytest

from scribesim.curriculum import letter_alignment as experiment


def source():
    return json.loads((experiment.stem.prior.BASE / 'run-001/seed-7/first/candidate.json').read_text())


def test_exact_cubic_extrema_are_not_control_polygon_extrema():
    curves = np.array([[[0, 0], [1, 2], [2, 2], [3, 0]]], dtype=float)
    low, high = experiment.extrema(curves, 1)
    assert low == 0
    assert high == pytest.approx(1.5)


def test_level_assembly_freezes_lower_layers_and_preserves_caps():
    model, transforms = experiment.make_model(source())
    experiment.require_lineage(model, source())
    assert all(model[key] == source()[key] for key in model if key != 'recipes')
    assert all(-20 <= row['rotation_deg'] < -18 for row in transforms.values())
    assert all(.9 < row['scale'] < 1 for row in transforms.values())
    proof = experiment.landmarks(model)
    assert all(row['residual'] < 1e-8 for row in proof.values())
    assert [row['expanded'] for row in proof.values()] == [4, 4, 6]
    assert model['recipes']['m']['gestures'][0]['offset'][1] == pytest.approx(model['recipes']['m']['gestures'][1]['offset'][1])


def test_old_climbing_recipe_fails_level_gate():
    path = experiment.prior.BASE / 'run-001/seed-7/shared/first/candidate.json'
    old = json.loads(path.read_text())
    assert experiment.landmarks(old)['m']['residual'] > .3


@pytest.mark.parametrize('mutation', ['primitive', 'action', 'scale', 'rotation', 'offset', 'extra', 'alias'])
def test_detached_or_unfrozen_assembly_is_rejected(mutation):
    model, _ = experiment.make_model(source())
    if mutation == 'primitive':
        model['primitives']['stem']['cubics'][0][1][0] += .01
    elif mutation == 'action':
        model['actions']['fixed']['pressure'] = .6
    elif mutation == 'alias':
        model['recipes']['m']['visible'] = 'n'
    elif mutation == 'extra':
        model['recipes']['m']['gestures'].append(copy.deepcopy(model['recipes']['m']['gestures'][0]))
    elif mutation == 'offset':
        model['recipes']['m']['gestures'][1]['offset'][1] += .01
    else:
        model['recipes']['m']['gestures'][1]['scale' if mutation == 'scale' else 'rotation_deg'] += .01
    with pytest.raises(ValueError):
        experiment.require_lineage(model, source())


def test_target_normalizes_itself_without_candidate_compilation(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Independent target cannot inspect a candidate or use candidate extrema')
    monkeypatch.setattr(experiment, 'make_model', forbidden)
    monkeypatch.setattr(experiment, 'normalization', forbidden)
    monkeypatch.setattr(experiment, 'compile_gestures', forbidden)
    for fixture in experiment.SPEC['fixtures']:
        path = experiment.target(fixture)
        experiment.foundation.measurement.require_containment(path, frame=experiment.SPEC['frame_mm'])
        assert experiment.foundation.contact_runs(path) == 2 * len(fixture['text'])


def test_invalid_or_outside_contract_normalization_fails():
    for curves in [np.zeros((1, 4, 2)), [[[0, 0], [0, 1], [0, 2], [0, 3]]], [[[0, 0], [1, float('nan')], [2, 1], [3, 0]]]]:
        with pytest.raises(ValueError):
            experiment.normalization(curves)


def test_partial_or_empty_evidence_cannot_pass():
    assert experiment.passed({}) is False
    assert experiment.passed({'fixtures': []}) is False


def test_exact_inventory_and_shared_primitive_reuse():
    model, _ = experiment.make_model(source())
    with pytest.raises(ValueError):
        experiment.compile_gestures('o', model)
    proof = experiment.prior.reuse_proof(model, source())
    assert proof['changed_letters'] == ['n', 'u', 'm']
    assert proof['all_changed_rows_share_identity'] is True


def test_new_pairs_were_not_old_holdouts():
    old = {row['text'] for row in experiment.prior.fixtures() if row['split'] == 'unseen'}
    fresh = {row['text'] for row in experiment.SPEC['fixtures'] if row['split'] == 'fresh_pair'}
    assert fresh == {'un', 'mu', 'nm'}
    assert fresh.isdisjoint(old)
