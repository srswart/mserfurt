import copy
import json

import numpy as np
import pytest


def test_evaluation_sources_are_pinned_and_current():
    from scribesim.handvalidate.foundation_primitives import load_inputs, SPEC, identities

    source = load_inputs()
    assert set(source['seeds']) == {7, 19, 41}
    assert SPEC['criteria']['global_negative_minimum'] == .1
    assert 'scribesim/handvalidate/foundation_primitives.py' in identities()


def test_target_generation_is_independent_of_training_helpers(monkeypatch):
    from scribesim.handvalidate.foundation_primitives import target_segments, FIXTURES
    from scribesim.curriculum import foundation_primitives as learning

    monkeypatch.setattr(learning, 'target_segments', lambda *args: pytest.fail('Trainer target helper called'))
    monkeypatch.setattr(learning.contract, 'target_points', lambda *args: pytest.fail('Trainer target helper called'))
    points = target_segments(FIXTURES[-1])
    assert len(points) == 4
    assert all(np.isfinite(segment).all() for segment in points)
    assert all(np.allclose(before[-1], after[0]) for before, after in zip(points, points[1:]))


def test_subdivision_really_splits_both_return_families():
    from scribesim.handvalidate.foundation_primitives import subdivide, probe, FIXTURES
    from scribesim.curriculum.foundation_primitives import initial_model, _curve

    model = probe(initial_model(), FIXTURES[-1])
    before = copy.deepcopy(model)
    divided = subdivide(model)
    assert model == before
    for family in ('lower-return', 'upper-return'):
        assert len(divided['primitives'][family]['cubics']) == 2
        original = _curve(model['primitives'][family]['cubics'][0])
        pieces = divided['primitives'][family]['cubics']
        joined = np.vstack((_curve(pieces[0])[:-1], _curve(pieces[1])))
        assert np.allclose(original, joined[::2], atol=1e-12)


def test_trace_audit_detects_hidden_contact_and_extra_owner():
    from scribesim.handvalidate.foundation_primitives import execute, audit_trace, probe, FIXTURES
    from scribesim.curriculum.foundation_primitives import initial_model, Budget

    model = probe(initial_model(), FIXTURES[0])
    result = execute(model, step=.025, dt=.002, budget=Budget())
    assert audit_trace(model, result)['errors'] == 0
    altered = copy.deepcopy(result)
    altered['trace'][len(altered['trace']) // 2]['contact'] = False
    assert audit_trace(model, altered)['errors'] > 0
    altered = copy.deepcopy(result)
    altered['trace'][-1]['owner']['occurrence_id'] = 'undeclared'
    assert audit_trace(model, altered)['errors'] > 0


def test_required_keys_and_failed_controls_cannot_be_averaged_away():
    from scribesim.handvalidate.foundation_primitives import decide_seed, CONTROL_IDS, FIXTURES

    rows = [{'id': fixture['id'], 'passed': True} for fixture in FIXTURES]
    controls = {name: {'detected': True} for name in CONTROL_IDS}
    assert decide_seed(rows, controls, True)
    controls['extra-contributor']['detected'] = False
    assert not decide_seed(rows, controls, True)
    controls['extra-contributor']['detected'] = True
    assert not decide_seed(rows[:-1], controls, True)
    assert not decide_seed(rows, controls, False)


def test_readiness_rejects_fabricated_or_unpinned_pass(tmp_path):
    from scribesim.handvalidate.foundation_primitives import require_primitive_readiness

    (tmp_path / 'S1-primitives.json').write_text(json.dumps({'status': 'pass', 'gesture_training_permitted': True}))
    with pytest.raises(ValueError):
        require_primitive_readiness(tmp_path, expected_report_sha256='0' * 64, required_families=['lower-return'])


def test_invalid_source_stops_without_optimizer_or_evaluation(tmp_path, monkeypatch):
    from scribesim.handvalidate import foundation_primitives as evaluation

    monkeypatch.setattr(evaluation, 'load_inputs', lambda: (_ for _ in ()).throw(ValueError('Changed input')))
    report = evaluation.build(tmp_path / 'run')
    assert report['status'] == 'blocked' and report['renders'] == 0
    assert report['optimization_evaluations'] == 0 and not report['gesture_training_permitted']


def test_fresh_fixture_and_controls_do_not_call_training_execution(tmp_path, monkeypatch):
    from scribesim.handvalidate import foundation_primitives as evaluation

    forbidden = lambda *args, **kwargs: pytest.fail('Training execution or measurement called')
    for name in ('execute_fixture', 'target_segments', 'search_handles', 'build'):
        monkeypatch.setattr(evaluation.learning, name, forbidden)
    monkeypatch.setattr(evaluation.measurement, 'measure_fixture', forbidden)
    budget = evaluation.learning.Budget()
    model = evaluation.contract.initial_model()
    record, runs, tiles = evaluation.evaluate_fixture(model, evaluation.FIXTURES[-1], budget, tmp_path)
    assert set(runs) == {'base', 'arc', 'time', 'subdivision'}
    assert record['shared_parameter_propagation']
    assert all(row['errors'] == 0 for row in record['audits'].values())
    assert record['full']['ratio'] == 1 and not record['passed']
    controls = evaluation.controls(model, budget, tmp_path)
    assert all(row['detected'] for row in controls.values())
    assert not controls['extra-contributor']['global_meets_minimum']
    assert len(tiles) == 5


def test_retained_subdivision_failure_never_grants_readiness():
    from scribesim.handvalidate import foundation_primitives as evaluation

    directory = evaluation.BASE / 'run-001'
    report = json.loads((directory / 'S1-primitives.json').read_text())
    assert report['status'] == 'fail' and not report['gesture_training_permitted']
    assert all(row['replay_match'] for row in report['seeds'])
    with pytest.raises(ValueError, match='unaccepted'):
        evaluation.require_primitive_readiness(directory, expected_report_sha256=evaluation.digest(directory / 'S1-primitives.json'),
                                               required_families=['lower-return', 'upper-return'])


def test_metric_reader_does_not_trust_fabricated_fixture_pass():
    from scribesim.handvalidate import foundation_primitives as evaluation

    path = evaluation.BASE / 'run-001/seed-7/first/compound-attachment-metrics.json'
    record = json.loads(path.read_text())
    record['passed'] = True
    record['motion']['subdivision']['passed'] = True
    assert record['motion']['subdivision']['metrics']['desired_acceleration_mm_s2'] > 250
    assert not evaluation.recheck_fixture(record)


def test_metric_reader_rejects_missing_families_and_nonfinite_metrics():
    from scribesim.handvalidate import foundation_primitives as evaluation

    path = evaluation.BASE / 'run-001/seed-7/first/lower-unseen-scale-metrics.json'
    record = json.loads(path.read_text())
    assert evaluation.recheck_fixture(record)
    changed = copy.deepcopy(record)
    changed['families'] = {}
    assert not evaluation.recheck_fixture(changed)
    record['motion']['base']['metrics']['image_loss'] = float('nan')
    assert not evaluation.recheck_fixture(record)
