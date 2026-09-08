import copy

import pytest

from scribesim.curriculum import letter_recipes as experiment
from scribesim.curriculum import letter_recipe_evidence as evidence


def selection():
    return experiment.select(lambda char, values, split: sum(abs(left - right) for left, right in zip(values, [.02, .34])),
                             seed=7, ablation='shared')


def test_saved_selection_reconstructs_without_invoking_selector(monkeypatch):
    selected = selection()
    def forbidden(*args, **kwargs):
        pytest.fail('Evidence inspection cannot fit or select')
    monkeypatch.setattr(experiment, 'select', forbidden)
    assert evidence.verify_selection(selected, seed=7, ablation='shared') is True


@pytest.mark.parametrize('mutation', ['missing_grid', 'changed_order', 'nonfinite', 'wrong_minimum', 'heldout', 'missing_dev', 'seed'])
def test_saved_selection_tampering_fails(mutation):
    selected = copy.deepcopy(selection())
    rows = selected['records']['n']
    if mutation == 'missing_grid':
        rows['training'].pop()
    elif mutation == 'changed_order':
        rows['training'].reverse()
    elif mutation == 'nonfinite':
        rows['training'][0]['loss'] = float('nan')
    elif mutation == 'wrong_minimum':
        selected['parameters']['n'] = [0, 0]
    elif mutation == 'heldout':
        selected['held_out_accessed'] = True
    elif mutation == 'missing_dev':
        rows['development'].pop()
    else:
        selected['seed'] = 19
    with pytest.raises(ValueError):
        evidence.verify_selection(selected, seed=7, ablation='shared')


def test_missing_bundle_cannot_be_inspected(tmp_path):
    with pytest.raises(ValueError):
        evidence.inspect_run(tmp_path)
