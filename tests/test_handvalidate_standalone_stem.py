import copy
import json

import pytest

from scribesim.handvalidate import standalone_stem as evaluation


def candidate():
    return json.loads((evaluation.prior.BASE / 'run-001/seed-7/first/candidate.json').read_text())


def test_stem_probe_retains_exact_primitive_gesture_action_and_contact():
    model = evaluation.probe(candidate(), evaluation.SPEC['fixtures'][0])
    plan = evaluation.compile_gestures('i', model)
    assert len(plan['strokes']) == 1
    assert plan['strokes'][0]['gesture'] == 'stem'
    assert model['primitives'] == candidate()['primitives']
    assert model['gestures'] == candidate()['gestures']
    assert model['actions'] == candidate()['actions']
    assert evaluation.foundation.contact_runs(evaluation.target(evaluation.SPEC['fixtures'][0])) == 1


@pytest.mark.parametrize('field', ['primitives', 'gestures', 'actions', 'sampling', 'nib_width_mm'])
def test_changed_frozen_source_fails(field):
    changed = candidate()
    changed[field] = None
    with pytest.raises(ValueError):
        evaluation.require_candidate(changed)


def test_admission_never_accepts_empty_or_missing_records():
    assert evaluation.passed({}) is False
    assert evaluation.passed({'fixtures': [], 'controls': {}}) is False


@pytest.mark.parametrize('kwargs', [dict(required_gestures=[]), dict(required_gestures=['overturn']),
    dict(required_gestures=['stem'], real=True), dict(required_gestures=['stem'], tool='other'),
    dict(required_gestures=['stem', 'stem'])])
def test_unsupported_admission_scope_fails_before_reading(tmp_path, kwargs):
    with pytest.raises(ValueError):
        evaluation.require_readiness(tmp_path, expected_report_sha256='0' * 64, **kwargs)


def test_live_measurement_preserves_stem_and_detects_owner_corruption(tmp_path):
    budget = evaluation.foundation.JournalBudget(tmp_path, 100, 60)
    row, run = evaluation.measure(candidate(), evaluation.SPEC['fixtures'][0], budget, tmp_path)
    assert evaluation.fixture_pass(row)
    changed = copy.deepcopy(run)
    next(point for point in changed['trace'] if point['contact'])['owner']['primitive'] = 'invented'
    model = evaluation.probe(candidate(), evaluation.SPEC['fixtures'][0])
    assert evaluation.foundation.audit_trace(model, 'i', changed)['errors'] > 0


def test_immutable_attempt_cannot_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluation, 'BASE', tmp_path)
    (tmp_path / 'run-001').mkdir()
    with pytest.raises(ValueError):
        evaluation.protocol.build(evaluation)
