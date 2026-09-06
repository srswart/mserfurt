import copy

import numpy as np
import pytest

from scribesim.curriculum.gesture_learning import experiment, fit_gestures, run_learning
from scribesim.handvalidate.specimen import object_digest


def test_shared_composition_is_fitted_without_mutating_primitives_profiles_or_letters():
    initial, target, samples = experiment()
    result = fit_gestures(initial, samples, ablation='composition', seed=7)
    assert result['status'] == 'complete'
    assert result['metrics']['test']['after'] < result['metrics']['test']['before'] * .75
    assert result['model']['gestures'] == target['gestures']
    for key in ('primitives', 'actions', 'recipes'):
        assert result['model'][key] == initial[key]
    assert result['ledger'] and result['renders'] <= 5000


def test_test_images_cannot_select_the_checkpoint():
    initial, _, samples = experiment()
    changed = copy.deepcopy(samples)
    for sample in changed:
        if sample['split'] == 'test':
            sample['raw'] = np.zeros_like(sample['raw'])
    first = fit_gestures(initial, samples, ablation='composition', seed=19)
    second = fit_gestures(initial, changed, ablation='composition', seed=19)
    assert first['model'] == second['model']
    assert first['ledger'] == second['ledger']


def test_budget_exhaustion_does_not_create_an_accepted_candidate():
    initial, _, samples = experiment()
    result = fit_gestures(initial, samples, ablation='composition', seed=41, max_evaluations=1)
    assert result['status'] == 'blocked' and result['renders'] <= 1
    assert not result['promoted']


def test_real_run_stops_before_source_pixels_or_fitting(tmp_path, monkeypatch):
    from PIL import Image

    def forbidden(*args, **kwargs):
        raise AssertionError('Real source pixels must remain sealed')

    monkeypatch.setattr(Image, 'open', forbidden)
    report = run_learning(tmp_path / 'real', real=True)
    assert report['status'] == 'blocked' and report['renders'] == 0
    assert not (tmp_path / 'real' / 'candidate.json').exists()


def test_fixed_ablation_is_a_baseline_not_learning_and_output_is_immutable(tmp_path):
    initial, _, samples = experiment()
    result = fit_gestures(initial, samples, ablation='fixed', seed=7)
    assert object_digest(result['model']) == object_digest(initial)
    assert result['ledger'] == []
    (tmp_path / 'keep').write_text('preserve')
    with pytest.raises(ValueError, match='empty'):
        run_learning(tmp_path)
