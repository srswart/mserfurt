import copy
import json

import pytest

from scribesim.curriculum import letter_recipes as experiment
from scribesim.evofit.stroke_gestures import compile_gestures


def source():
    return json.loads((experiment.admission.BASE / 'run-001/seed-7/first/candidate.json').read_text())


def test_recipe_inventory_uses_audited_references_and_exact_text():
    initial = experiment.initial_model(source())
    assert set(initial['recipes']) == {'n', 'u', 'm'}
    assert [len(compile_gestures(char, initial)['strokes']) for char in 'num'] == [4, 4, 6]
    assert initial['gestures'] == source()['gestures']
    assert initial['primitives'] == source()['primitives']
    with pytest.raises(ValueError):
        experiment.compile_recipe('o', initial, source())
    with pytest.raises(ValueError):
        experiment.compile_recipe('i', initial, source())


def test_only_second_instance_placement_is_learned():
    initial = experiment.initial_model(source())
    parameters = {'n': [.08, 0], 'u': [.02, .34], 'm': [.02, .34]}
    fitted = experiment.with_parameters(source(), parameters)
    experiment.require_lineage(fitted, source())
    assert all(fitted[key] == initial[key] for key in initial if key != 'recipes')
    assert fitted['recipes']['u']['gestures'][1]['offset'] == [1.02, .34]
    assert initial['recipes']['u']['gestures'][1]['offset'] == [1, 0]
    assert experiment.compile_recipe('num', fitted, source())['coverage'] == 1


@pytest.mark.parametrize('field', ['primitives', 'gestures', 'actions', 'letter_rules', 'word_rules', 'nib_width_mm'])
def test_lower_layer_or_context_changes_fail(field):
    candidate = experiment.initial_model(source())
    candidate[field] = None
    with pytest.raises(ValueError):
        experiment.require_lineage(candidate, source())


@pytest.mark.parametrize('mutation', ['curve', 'alias', 'hidden_lift', 'overlap', 'extra_instance', 'advance', 'scale', 'rotation'])
def test_recipe_cannot_bypass_geometry_mapping_or_cap(mutation):
    candidate = experiment.initial_model(source())
    recipe = candidate['recipes']['m']
    if mutation == 'curve':
        recipe['cubics'] = []
    elif mutation == 'alias':
        recipe['visible'] = 'n'
    elif mutation == 'hidden_lift':
        recipe['gestures'][1]['transition'] = 'smooth'
    elif mutation == 'overlap':
        recipe['gestures'][1]['overlap_with'] = [0]
    elif mutation == 'extra_instance':
        recipe['gestures'].append(copy.deepcopy(recipe['gestures'][1]))
    elif mutation == 'advance':
        recipe['advance'] += .1
    elif mutation == 'scale':
        recipe['gestures'][1]['scale'] = .9
    else:
        recipe['gestures'][1]['rotation_deg'] = 1
    with pytest.raises(ValueError):
        experiment.require_lineage(candidate, source())


@pytest.mark.parametrize('parameters', [{}, {'n': [True, 0], 'u': [0, 0], 'm': [0, 0]},
    {'n': [float('nan'), 0], 'u': [0, 0], 'm': [0, 0]},
    {'n': [.5, 0], 'u': [0, 0], 'm': [0, 0]}])
def test_parameter_bounds_fail_closed(parameters):
    with pytest.raises(ValueError):
        experiment.with_parameters(source(), parameters)


def test_selection_never_reads_holdouts_and_development_selects():
    calls = []
    def score(character, parameters, split):
        calls.append(split)
        return sum(abs(left - right) for left, right in zip(parameters, [.02, .34]))
    selected = experiment.select(score, seed=7, ablation='shared')
    assert set(calls) == {'train', 'development'}
    assert selected['parameters'] == dict.fromkeys('num', [.02, .34])
    assert selected['held_out_accessed'] is False
    assert selected == experiment.select(score, seed=7, ablation='shared')
    with pytest.raises(ValueError):
        experiment.select(lambda *args: float('nan'), seed=7, ablation='shared')


def test_prior_arm_cannot_fit_and_unknown_seed_rejected():
    selected = experiment.select(lambda *args: .5, seed=7, ablation='prior')
    assert selected['parameters'] == dict.fromkeys('num', [0, 0])
    with pytest.raises(ValueError):
        experiment.select(lambda *args: .5, seed=9, ablation='shared')


def test_admission_does_not_become_alphabet_permission(monkeypatch):
    calls = []
    def admit(directory, **kwargs):
        calls.append(kwargs)
        return {'S1_action_accepted': True, 'letter_training_allowed': False, 'real_accepted': False}
    monkeypatch.setattr(experiment.admission, 'require_readiness', admit)
    result = experiment.load_inputs()
    assert calls[0]['required_gestures'] == ['underturn', 'overturn']
    assert result['unresolved_gestures'] == ['stem']
    assert result['S2_accepted'] is False
    with pytest.raises(ValueError, match='reference'):
        experiment.load_inputs(real=True)


def test_repeat_and_unseen_combinations_are_separate_and_frozen():
    fixtures = experiment.fixtures()
    assert len({row['id'] for row in fixtures}) == len(fixtures)
    assert {row['text'] for row in fixtures if row['split'] == 'train'} == set('num')
    assert {row['text'] for row in fixtures if row['split'] == 'unseen'} == {'nu', 'um', 'mn'}
    assert {row['text'] for row in fixtures if row['split'] == 'repeat'} == set('num')


def test_no_empty_or_nonfinite_report_passes():
    assert experiment.evaluation_pass([]) is False
    assert experiment.evaluation_pass([{'status': 'complete'}]) is False


def test_shared_substitution_propagates_without_detached_letters():
    proof = experiment.reuse_proof(experiment.initial_model(source()), source())
    assert proof['changed_letters'] == ['n', 'u', 'm']
    assert proof['all_changed_rows_share_identity'] is True
    assert proof['substitution_admitted'] is False


def test_existing_run_is_never_overwritten(tmp_path):
    output = tmp_path / 'run-001'
    output.mkdir()
    with pytest.raises(ValueError):
        experiment.build(output)
