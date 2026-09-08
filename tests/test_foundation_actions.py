import copy
import inspect
import json

import pytest

from scribesim.curriculum import foundation_actions as experiment


def test_live_admission_and_predeclared_null_do_not_optimize(monkeypatch):
    from scribesim.curriculum import foundation_gestures, pen_actions

    def forbidden(*args, **kwargs):
        pytest.fail('No fitting in a predeclared null experiment')

    monkeypatch.setattr(foundation_gestures, 'select', forbidden)
    monkeypatch.setattr(pen_actions, '_fit_lesson', forbidden)
    source = experiment.load_inputs()
    assert source['admission']['scope_next_action_experiment']
    assert set(source['candidates']) == {7, 19, 41}
    for candidate in source['candidates'].values():
        assert experiment.object_digest(candidate) == experiment.SPEC['candidate_object_sha256']


@pytest.mark.parametrize('field', ['actions', 'primitives', 'gestures', 'recipes'])
def test_any_change_to_frozen_candidate_is_rejected(field):
    source = experiment.load_inputs()
    candidate = copy.deepcopy(source['candidates'][7])
    candidate[field] = {}
    with pytest.raises(ValueError):
        experiment.require_candidate(candidate)


def test_null_threshold_is_absolute_target_error_not_tracking_or_relative_gain():
    assert experiment.SPEC['criteria']['null_actual_target_loss_max'] == .05
    row = {'actual_target': {name: .06 for name in experiment.REFINEMENTS},
           'local_actual_target': {'0': {name: .04 for name in experiment.REFINEMENTS}},
           'motion_pass': True, 'relative_improvement': .1, 'actual_desired_loss': .001, 'null_supported': True}
    assert not experiment.quality_pass(row)
    row['actual_target'] = {name: .04 for name in experiment.REFINEMENTS}
    assert experiment.quality_pass(row)
    row['local_actual_target']['0']['time'] = .051
    assert not experiment.quality_pass(row)
    row['local_actual_target']['0']['time'] = float('nan')
    assert not experiment.quality_pass(row)


def test_missing_measurements_cannot_count_as_null_success():
    assert not experiment.quality_pass({'actual_target': {}, 'local_actual_target': {}})
    assert not experiment.measurement_complete({'status': 'complete', 'fixtures': []})
    assert not experiment.null_supported({'status': 'complete', 'null_supported': True})


def test_target_splits_and_scope_are_frozen_before_measurement():
    fixtures = experiment.SPEC['fixtures']
    assert {row['split'] for row in fixtures} == {'train', 'development', 'held_out'}
    assert len(fixtures) == 11
    assert len({experiment.object_digest(row['instances']) for row in fixtures}) == 11
    assert 'candidate' not in inspect.signature(experiment.target).parameters
    assert experiment.SPEC['budget']['optimization_evaluations'] == 0


def test_current_frozen_nominal_residual_is_not_proof_that_rotation_is_needed():
    fixture = experiment.SPEC['fixtures'][1]
    assert fixture['instances'][0]['gesture'] == 'overturn'
    row = {'nominal_target': .099, 'actual_target': {'base': .10}}
    assert experiment.diagnose(row) == 'target_mismatch_already_present_in_frozen_nominal_geometry'
    assert experiment.diagnose({'nominal_target': .01, 'actual_target': {'base': .06}}) == 'actual_execution_or_rendering_requires_investigation'


def test_missing_source_blocks_before_any_render_or_candidate_write(tmp_path, monkeypatch):
    def missing():
        raise ValueError('Stale foundation')

    monkeypatch.setattr(experiment, 'load_inputs', missing)
    record = experiment.worker(tmp_path / 'worker', 7, 5000, 1800)
    assert record['status'] == 'blocked'
    assert record['renders'] == 0
    assert not (tmp_path / 'worker/candidate.json').exists()


def test_reader_cannot_turn_flag_only_report_into_selected_candidate_evidence(tmp_path):
    experiment.write_json(tmp_path / 'report.json', {'status': 'complete', 'null_supported': True})
    with pytest.raises(ValueError):
        experiment.require_candidates(tmp_path, expected_report_sha256=experiment.digest(tmp_path / 'report.json'))


def test_outputs_are_immutable(tmp_path):
    with pytest.raises(ValueError, match='immutable'):
        experiment.build(tmp_path)


def test_completed_negative_hypothesis_is_reviewable_but_not_admitted():
    root = experiment.BASE / 'run-001'
    evidence = experiment.require_candidates(root, expected_report_sha256=experiment.digest(root / 'report.json'))
    assert evidence['candidate_evaluation_permitted']
    assert not evidence['null_hypothesis_supported']
    assert not evidence['S1_action_accepted']
    assert not evidence['letter_training_allowed']


def test_observed_motion_pass_does_not_override_overturn_target_failure():
    root = experiment.BASE / 'run-001/seed-7/first'
    row = json.loads((root / 'held_out-overturn.json').read_text())
    assert experiment.mechanics_pass(row)
    row['null_supported'] = True
    assert not experiment.quality_pass(row)
    assert row['nominal_target'] > .05


def test_missing_actual_refinement_invalidates_completed_evidence():
    record = json.loads((experiment.BASE / 'run-001/seed-7/first/report.json').read_text())
    assert experiment.measurement_complete(record)
    del record['fixtures'][0]['actual_target']['subdivision']
    assert not experiment.measurement_complete(record)
