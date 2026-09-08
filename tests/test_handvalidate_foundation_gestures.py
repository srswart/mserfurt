import copy
import inspect
import json

import numpy as np
import pytest

from scribesim.handvalidate import foundation_gestures as evaluation
from scribesim.curriculum import foundation_gestures as learning
from scribesim.evofit.stroke_gestures import compile_gestures


@pytest.fixture(scope='module')
def source():
    return evaluation.load_inputs()


def test_frozen_candidates_and_lower_admission_are_reconstructed_without_search(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Independent evaluation must not run learning evaluation or search')

    for name in ('select', 'acquire_candidate', 'evaluate', 'controls', 'target', 'regions'):
        monkeypatch.setattr(learning, name, forbidden)
    loaded = evaluation.load_inputs()
    assert set(loaded['candidates']) == {7, 19, 41}
    assert all(evaluation.object_digest(model) == evaluation.SPEC['candidate_object_sha256']
               for model in loaded['candidates'].values())
    assert loaded['primitive_admission']['gesture_training_permitted']


def test_independent_target_and_complete_frame(source):
    fixture = evaluation.SPEC['fixtures'][-1]
    assert 'candidate' not in inspect.signature(evaluation.target_parts).parameters
    parts = evaluation.target_parts(fixture)
    assert len(parts) == 6
    path = evaluation.contact_trajectory((part['occurrence'], part['points']) for part in parts)
    assert evaluation.contact_runs(path) == 2
    evaluation.measurement.require_containment(path, frame=evaluation.SPEC['frame_mm'])
    assert len(evaluation.regions(fixture)) == 2
    with pytest.raises(ValueError, match='region'):
        evaluation.crop(np.zeros((20, 20, 3), dtype=np.uint8), [-3, 1, 0, 2])


@pytest.mark.parametrize('mutation', ['primitive', 'action', 'recipe', 'gesture'])
def test_independent_source_contract_rejects_unfrozen_changes(source, mutation):
    model = copy.deepcopy(source['candidates'][7])
    if mutation == 'primitive':
        model['primitives']['lower-return']['cubics'][0][1][0] += .01
    elif mutation == 'action':
        model['actions']['fixed']['pressure'] = .4
    elif mutation == 'recipe':
        model['recipes']['i']['advance'] = 2
    else:
        model['gestures']['underturn']['strokes'][1]['offset'][0] += .01
    with pytest.raises(ValueError):
        evaluation.require_candidate(model, source['initial'])


def test_overlap_and_space_are_explicit_diagnostic_contexts(source):
    candidate = source['candidates'][7]
    overlap, adjacent, spaced = evaluation.SPEC['contexts']
    model = evaluation.probe(candidate, overlap)
    rows = compile_gestures('i', model)['strokes']
    assert len(rows) == 6
    assert rows[-1]['overlap_contributors']
    assert evaluation.probe(candidate, adjacent) == evaluation.probe(candidate, spaced)
    assert [row['span'] for row in compile_gestures('i i', evaluation.probe(candidate, spaced))['strokes']] == [[0, 1]] * 3 + [[2, 3]] * 3


def test_contact_boundaries_cannot_be_hidden_by_pass_flag():
    endpoints = [{'owner': '0:0', 'entry': {'position_error_mm': 0, 'speed_mm_s': 0},
                  'exit': {'position_error_mm': .051, 'speed_mm_s': 0}, 'passed': True}]
    assert not evaluation.boundaries_pass(endpoints, ['0:0'])
    endpoints[0]['exit']['position_error_mm'] = float('nan')
    assert not evaluation.boundaries_pass(endpoints, ['0:0'])
    assert not evaluation.boundaries_pass([], ['0:0'])


def test_flag_only_manifest_and_unpinned_input_cannot_admit(tmp_path):
    report = {'stage': evaluation.STAGE, 'status': 'pass', 'S1_gesture_accepted': True}
    evaluation.write_json(tmp_path / 'S1-gestures.json', report)
    with pytest.raises(ValueError):
        evaluation.require_readiness(tmp_path, expected_report_sha256=evaluation.digest(tmp_path / 'S1-gestures.json'),
                                     required_gestures=['underturn'])
    with pytest.raises(ValueError):
        evaluation.require_readiness(tmp_path, expected_report_sha256=None, required_gestures=['underturn'])


@pytest.mark.parametrize('module_name', ['scribesim.curriculum.pen_actions', 'scribesim.handvalidate.pen_actions'])
def test_explicit_foundation_input_does_not_promote_null_actions_or_letters(monkeypatch, module_name):
    import importlib
    module = importlib.import_module(module_name)
    monkeypatch.setattr(evaluation, 'require_readiness', lambda *args, **kwargs: {
        'stage': evaluation.STAGE, 'scope_next_action_experiment': True, 'report_sha256': 'a' * 64})
    result = module.foundation_prerequisites('evidence', expected_report_sha256='a' * 64, required_gestures=['underturn'])
    assert result['scope_next_action_experiment']
    assert result['status'] == 'blocked'
    assert result['S1_action_accepted'] is False
    assert result['letter_training_allowed'] is False
    assert result['legacy_action_fitting_allowed'] is False
    assert not module.foundation_prerequisites('evidence', expected_report_sha256='a' * 64,
                                               required_gestures=['underturn'], real=True)['scope_next_action_experiment']


def test_budget_and_final_acceptance_require_complete_numeric_proofs():
    assert evaluation.SPEC['budget']['optimization_evaluations'] == 0
    assert not evaluation.complete({'status': 'pass', 'fixtures': []}, {})
    assert {fixture['id'] for fixture in evaluation.SPEC['fixtures'] if fixture['split'] == 'held_out'} >= {
        'underturn-overturn-pair', 'overturn-underturn-pair', 'compound-terminal-pair',
        'underturn-repeat-pair', 'independent-scaled-attachment'}
