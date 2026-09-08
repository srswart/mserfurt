import copy
import itertools
import json

import pytest

from scribesim.curriculum import finer_scales as experiment


def source():
    return json.loads((experiment.BASE.parent / 'actions/run-001/seed-7/first/candidate.json').read_text())


def test_grid_is_uniform_bounded_and_contains_unchanged_baseline():
    grids = experiment.grids()
    assert grids == [[.82, .83, .84, .85, .86, .87, .88],
                     [1.12, 1.13, 1.14, 1.15, 1.16, 1.17, 1.18],
                     [.82, .83, .84, .85, .86, .87, .88]]
    assert len(list(itertools.product(*grids))) == 343
    assert experiment.with_parameters(source(), [.85, 1.15, .85]) == source()


def test_only_three_shared_scales_and_derived_attachments_can_change():
    initial = source()
    candidate = experiment.with_parameters(initial, [.84, 1.16, .86])
    experiment.require_lineage(candidate, initial, [.84, 1.16, .86])
    assert candidate['primitives'] == initial['primitives']
    assert candidate['actions'] == initial['actions']
    assert candidate['recipes'] == initial['recipes']
    assert initial == source()
    for name in experiment.CONSTRUCTIONS:
        for reference in candidate['gestures'][name]['strokes']:
            assert reference['scale'] == [.84, 1.16, .86][experiment.ROLES[reference['primitive']]]
    candidate['gestures']['overturn']['strokes'][0]['scale'] += .01
    with pytest.raises(ValueError):
        experiment.require_lineage(candidate, initial, [.84, 1.16, .86])


@pytest.mark.parametrize('parameters', [[.81, 1.15, .85], [.85, 1.19, .85], [True, 1.15, .85], [.85], [.85, float('nan'), .85]])
def test_unfrozen_parameters_rejected(parameters):
    with pytest.raises(ValueError):
        experiment.with_parameters(source(), parameters)


def test_selector_protects_worst_construction_and_never_reads_holdouts():
    calls = []

    def score(parameters, split):
        calls.append(split)
        if parameters == [.84, 1.16, .86]:
            return dict.fromkeys(experiment.CONSTRUCTIONS, .04)
        return dict(zip(experiment.CONSTRUCTIONS, [.001, .001, .06]))

    selected = experiment.select(score, seed=7)
    assert selected['parameters'] == [.84, 1.16, .86]
    assert selected['development_absolute_pass'] is True
    assert calls.count('train') == 343
    assert set(calls) == {'train', 'development'}
    assert selected['held_out_accessed'] is False


@pytest.mark.parametrize('losses', [{}, {'underturn': .01}, dict.fromkeys(['underturn', 'overturn', 'compound_curve'], float('nan'))])
def test_incomplete_or_nonfinite_scoring_fails_closed(losses):
    with pytest.raises(ValueError):
        experiment.select(lambda parameters, split: losses, seed=7)


def test_complete_negative_selection_does_not_become_absolute_pass():
    selected = experiment.select(lambda parameters, split: dict.fromkeys(experiment.CONSTRUCTIONS, .051), seed=19)
    assert selected['development_absolute_pass'] is False


def test_targets_limits_and_fresh_scope_are_unchanged_and_disjoint():
    assert experiment.SPEC['criteria']['absolute_loss_max'] == experiment.independent.SPEC['criteria']['absolute_loss_max'] == .05
    fixtures = experiment.fixtures()
    assert len(fixtures) == 21
    assert {row['split'] for row in fixtures} == {'train', 'development', 'regression', 'held_out'}
    old = {experiment.object_digest(row['instances']) for row in fixtures if row['split'] != 'held_out'}
    assert not old & {experiment.object_digest(row['instances']) for row in fixtures if row['split'] == 'held_out'}


def test_lineage_rejects_return_handle_or_action_mutation():
    initial = source()
    for field in ['primitives', 'actions', 'recipes']:
        changed = copy.deepcopy(initial)
        changed[field] = {}
        with pytest.raises(ValueError):
            experiment.require_lineage(changed, initial, [.85, 1.15, .85])


def test_immutable_run_cannot_be_overwritten(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment, 'BASE', tmp_path)
    (tmp_path / 'run-001').mkdir()
    with pytest.raises(ValueError, match='immutable'):
        experiment.build()


def test_missing_source_stops_before_render_or_candidate_write(tmp_path, monkeypatch):
    def missing():
        raise ValueError('Stale source')

    monkeypatch.setattr(experiment, 'load_inputs', missing)
    directory = tmp_path / 'worker'
    result = experiment.worker(directory, 7, 5000, 1800)
    assert result['status'] == 'blocked'
    assert result['renders'] == 0
    assert not (directory / 'candidate.json').exists()
