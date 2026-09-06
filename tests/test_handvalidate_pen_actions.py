import json
import shutil

import pytest

from scribesim.handvalidate.nib_contact import BASE
from scribesim.handvalidate.pen_actions import evaluate_seed, build, require_letter_readiness


def test_independent_stop_has_no_rendering_or_optimization(monkeypatch):
    from scribesim.curriculum import pen_actions
    from scribesim.pathguide import gesture_actions

    def forbidden(*args, **kwargs):
        raise AssertionError('Evaluation cannot fit or render before prerequisites pass')

    monkeypatch.setattr(pen_actions, 'run_actions', forbidden)
    monkeypatch.setattr(pen_actions, '_fit_lesson', forbidden)
    monkeypatch.setattr(gesture_actions, 'execute_actions', forbidden)
    result = evaluate_seed(7)
    assert result['status'] == 'blocked'
    assert result['renders'] == result['optimization_evaluations'] == 0
    assert not result['letter_training_allowed']
    assert result['candidate_evaluation'] == 'not_run_prerequisites_failed'
    assert not result['original_global_controls']['hidden_connector']['meets_frozen_minimum']


def test_fabricated_learning_status_fails_identity(tmp_path):
    shutil.copytree(BASE / 'actions/run-002', tmp_path / 'learning')
    path = tmp_path / 'learning/report.json'
    report = json.loads(path.read_text())
    report['status'] = 'complete'
    path.write_text(json.dumps(report))
    result = evaluate_seed(7, learning_root=path.parent)
    assert result['status'] == 'blocked'
    assert any('identity' in reason for reason in result['reasons'])


def test_three_fresh_processes_cannot_turn_blocked_into_readiness(tmp_path):
    report = build(tmp_path / 'proof')
    assert report['status'] == 'blocked'
    assert report['replay']
    assert [row['seed'] for row in report['seeds']] == [7, 19, 41]
    assert report['renders'] == 0
    with pytest.raises(ValueError):
        require_letter_readiness(tmp_path / 'proof')
    path = tmp_path / 'proof/S1-action.json'
    report['status'] = 'pass'
    report['letter_training_allowed'] = True
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        require_letter_readiness(tmp_path / 'proof')
