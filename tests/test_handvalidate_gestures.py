import copy
import shutil

import pytest

from scribesim.curriculum.gesture_learning import BASE, experiment, exercise_model
from scribesim.evofit.stroke_gestures import execute_gestures
from scribesim.handvalidate.gestures import audit_trace, load_training, local_controls, verify_candidate


def test_training_reconstructs_and_rejects_stale_artifacts(tmp_path):
    root = BASE / 'gestures/run-002'
    assert load_training(root)[1]['replay']
    shutil.copytree(root, tmp_path / 'training')
    (tmp_path / 'training/candidate.json').write_text('{}')
    with pytest.raises(ValueError, match='identity'):
        load_training(tmp_path / 'training')


@pytest.mark.parametrize('fault', ['detached', 'recipe', 'profile', 'out-of-grid'])
def test_candidate_rejects_unfrozen_freedom(fault):
    initial, target, _ = experiment()
    verify_candidate(initial, target, 'composition')
    changed = copy.deepcopy(target)
    if fault == 'detached':
        changed['primitives']['stem']['cubics'][0][1][0] += .01
    elif fault == 'recipe':
        changed['recipes']['i']['gestures'][0]['scale'] = 1.1
    elif fault == 'profile':
        changed['actions']['fixed']['pressure'] = .6
    else:
        changed['gestures']['gesture-0']['strokes'][1]['scale'] = 1.3
    with pytest.raises(ValueError):
        verify_candidate(initial, changed, 'composition')


def test_trace_audit_checks_actual_contact_and_contributors_not_summary():
    _, target, samples = experiment()
    sample = samples[-1]
    model = exercise_model(target, sample)
    result = execute_gestures(sample['text'], model)
    assert audit_trace(sample['text'], model, result)['errors'] == 0
    for fault in ('lift', 'owner', 'length', 'nan'):
        broken = copy.deepcopy(result)
        if fault == 'lift':
            broken['trajectory'][0]['contact'] = False
        elif fault == 'owner':
            broken['owners'][0]['overlap_contributors'] = ['invented']
        elif fault == 'length':
            broken['trajectory'].pop()
        else:
            broken['trajectory'][0]['x_mm'] = float('nan')
        assert audit_trace(sample['text'], model, broken)['errors'] > 0


def test_local_controls_preserve_failed_global_results_and_detect_locally():
    result = local_controls()
    assert not result['hidden_connector']['global_meets_minimum']
    assert not result['overbuilt_terminal']['global_meets_minimum']
    assert all(result[name]['detected_locally'] for name in ('hidden_connector', 'overbuilt_terminal', 'erased_counter'))
    assert result['scope'] == 'independent synthetic guard fixtures; not learned counter acceptance'


def test_independent_replay_does_not_optimize_or_hide_endpoint_failure(monkeypatch):
    from scribesim.curriculum import gesture_learning
    from scribesim.handvalidate.gestures import evaluate_seed

    def forbidden(*args, **kwargs):
        raise AssertionError('Evaluation must never optimize')

    monkeypatch.setattr(gesture_learning, 'fit_gestures', forbidden)
    result = evaluate_seed(BASE / 'gestures/run-002', 7)
    assert result['subset_status'] == 'fail'
    assert not result['checks']['unseen-pair:step:convergence']
    assert result['measurements']['unseen-pair']['comparisons']['step']['endpoint_difference_mm'] > .39
    assert result['S1_gesture'] == 'blocked'
    assert result['optimization_evaluations'] == 0
    assert not result['action_fitting_allowed']


def test_current_code_identity_required(monkeypatch):
    from scribesim.curriculum import gesture_learning

    monkeypatch.setattr(gesture_learning, 'code_identities', lambda: {})
    with pytest.raises(ValueError, match='Stale'):
        load_training(BASE / 'gestures/run-002')
