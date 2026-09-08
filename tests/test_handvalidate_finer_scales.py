import copy
import json

import pytest

from scribesim.handvalidate import finer_scales as evaluation


def candidate():
    return json.loads((evaluation.learning.BASE / 'run-001/seed-7/first/candidate.json').read_text())


def baseline():
    return json.loads((evaluation.learning.BASE.parent / 'actions/run-001/seed-7/first/candidate.json').read_text())


def selection():
    return json.loads((evaluation.learning.BASE / 'run-001/seed-7/first/selection.json').read_text())


def test_live_selected_evidence_reconstructs_without_fitting(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Independent evaluation cannot fit or invoke the selector')

    monkeypatch.setattr(evaluation.learning, 'fit', forbidden)
    monkeypatch.setattr(evaluation.learning, 'select', forbidden)
    source = evaluation.load_inputs()
    assert set(source['candidates']) == {7, 19, 41}
    assert source['report_sha256'] == evaluation.SPEC['source_report_sha256']
    assert all(model == candidate() for model in source['candidates'].values())


def test_independent_lineage_allows_only_selected_shared_scales():
    evaluation.require_candidate(candidate(), baseline())
    with pytest.raises(ValueError):
        evaluation.physical.learning.require_candidate(candidate())


@pytest.mark.parametrize('field', ['primitives', 'actions', 'recipes'])
def test_changed_lower_layers_rejected(field):
    changed = candidate()
    changed[field] = {}
    with pytest.raises(ValueError):
        evaluation.require_candidate(changed, baseline())


def test_per_occurrence_override_and_old_checkpoint_rejected():
    changed = candidate()
    changed['gestures']['overturn']['strokes'][0]['scale'] += .01
    for model in [changed, baseline()]:
        with pytest.raises(ValueError):
            evaluation.require_candidate(model, baseline())


def test_saved_selection_is_reconstructed_not_optimized():
    evaluation.verify_selection(selection(), 7)


@pytest.mark.parametrize('mutation', ['missing_grid_row', 'nonfinite', 'wrong_mean', 'wrong_checkpoint', 'heldout', 'missing_development', 'wrong_seed'])
def test_selection_tampering_rejected(mutation):
    saved = selection()
    if mutation == 'missing_grid_row':
        saved['training'].pop()
    elif mutation == 'nonfinite':
        saved['training'][0]['losses']['underturn'] = float('nan')
    elif mutation == 'wrong_mean':
        saved['training'][0]['mean'] = 0
    elif mutation == 'wrong_checkpoint':
        saved['parameters'] = [.85, 1.15, .85]
    elif mutation == 'heldout':
        saved['held_out_accessed'] = True
    elif mutation == 'missing_development':
        saved['development'].pop()
    else:
        saved['seed'] = 19
    with pytest.raises(ValueError):
        evaluation.verify_selection(saved, 7)


def test_fresh_scope_is_disjoint_and_criteria_unchanged():
    rows = evaluation.fixtures()
    assert len(rows) == 30
    old = {evaluation.object_digest(row['instances']) for row in rows if row['split'] == 'regression'}
    fresh = {evaluation.object_digest(row['instances']) for row in rows if row['split'] == 'held_out'}
    assert len(fresh) == 9 and not old & fresh
    assert len(evaluation.contexts()) == 6
    assert evaluation.SPEC['criteria'] == evaluation.physical.SPEC['criteria']
    assert evaluation.SPEC['budget']['optimization_evaluations'] == 0


def test_quality_rejects_local_failure_missing_refinement_and_nan():
    row = {'fixture': evaluation.SPEC['fresh_fixtures'][0],
           'actual_target': dict.fromkeys(evaluation.physical.REFINEMENTS, .01),
           'local_actual_target': {'0': dict.fromkeys(evaluation.physical.REFINEMENTS, .01)}}
    assert evaluation.quality(row)
    for value in [.051, float('nan')]:
        changed = copy.deepcopy(row)
        changed['local_actual_target']['0']['time'] = value
        assert not evaluation.quality(changed)
    row['actual_target'].pop('arc')
    assert not evaluation.quality(row)


@pytest.mark.parametrize('gestures,tool,real', [([], 'legacy-full-edge', False), (['upper_loop'], 'legacy-full-edge', False),
    (['underturn'], 'physical-edge-v1', False), (['underturn'], 'legacy-full-edge', True),
    (['underturn', 'underturn'], 'legacy-full-edge', False)])
def test_unsupported_admission_scope_rejected_before_read(tmp_path, gestures, tool, real):
    with pytest.raises(ValueError):
        evaluation.require_readiness(tmp_path, expected_report_sha256='unused', required_gestures=gestures, tool=tool, real=real)


def test_flag_only_report_cannot_grant_admission(tmp_path):
    evaluation.write_json(tmp_path / 'S1-actions.json', {'status': 'pass', 'S1_action_accepted': True})
    with pytest.raises(ValueError):
        evaluation.require_readiness(tmp_path, expected_report_sha256=evaluation.digest(tmp_path / 'S1-actions.json'),
            required_gestures=['underturn'])


def test_incomplete_measurement_cannot_be_accepted():
    assert not evaluation.complete({'status': 'complete', 'fixtures': [], 'optimization_evaluations': 0})


def test_missing_seed_decision_cannot_accept_an_empty_inventory_by_vacuous_truth():
    assert evaluation.decisions([]) == ([], False)


def test_scoped_reader_never_turns_all_local_passes_into_a_failed_global_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluation, 'inspect_evidence', lambda *args, **kwargs: {
        'accepted_gestures': evaluation.SPEC['required_gestures'], 'full_inventory_accepted': False})
    with pytest.raises(ValueError, match='Unresolved'):
        evaluation.require_readiness(tmp_path, expected_report_sha256='test', required_gestures=evaluation.SPEC['required_gestures'])
    admitted = evaluation.require_readiness(tmp_path, expected_report_sha256='test', required_gestures=['underturn'])
    assert admitted['S1_action_accepted']
    assert admitted['letter_training_allowed'] is False and admitted['real_accepted'] is False


def test_missing_source_blocks_before_any_render(tmp_path, monkeypatch):
    def missing():
        raise ValueError('Source not admitted')

    monkeypatch.setattr(evaluation, 'load_inputs', missing)
    row = evaluation.worker(tmp_path / 'worker', 7, 5000, 1800)
    assert row['status'] == 'blocked' and row['renders'] == 0
    assert not (tmp_path / 'worker/candidate.json').exists()


def test_run_is_immutable(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluation, 'BASE', tmp_path)
    (tmp_path / 'run-001').mkdir()
    with pytest.raises(ValueError, match='immutable'):
        evaluation.build()
