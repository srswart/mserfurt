import copy
import inspect

import numpy as np
import pytest

from scribesim.curriculum import foundation_gestures as learning
from scribesim.curriculum import gesture_targets as targets
from scribesim.evofit.stroke_gestures import compile_gestures


def test_matching_repaired_admission_and_unchanged_initial_geometry():
    source, admission = learning.load_source()
    initial = learning.initial_model(source)
    assert admission['execution_version'] == 'curve-tangent-v1'
    assert initial['primitives'] == source['primitives']
    assert initial['gestures'] == source['gestures']
    assert initial['actions'] == source['actions']


def test_shared_attachment_scales_preserve_ports_and_all_lower_parameters():
    initial = learning.initial_model(learning.load_source()[0])
    candidate = learning.with_parameters(initial, [.85, 1.15, .85])
    learning.require_lineage(candidate, initial)
    assert candidate['primitives'] == initial['primitives']
    for fixture in learning.SPEC['fixtures']:
        rows = compile_gestures('i', learning.probe(candidate, fixture))['strokes']
        for previous, current in zip(rows, rows[1:]):
            if current['transition'] == 'smooth':
                assert np.linalg.norm(np.subtract(previous['cubics'][-1][-1], current['cubics'][0][0])) < 1e-12
        for row in rows:
            assert row['primitive_sha256'] == learning.object_digest(initial['primitives'][row['primitive']])


@pytest.mark.parametrize('mutation', ['primitive', 'action', 'recipe', 'gesture', 'nan'])
def test_lineage_rejects_every_unfrozen_freedom(mutation):
    initial = learning.initial_model(learning.load_source()[0])
    candidate = learning.with_parameters(initial, [.85, 1.15, .85])
    if mutation == 'primitive':
        candidate['primitives']['lower-return']['cubics'][0][1][0] += .01
    elif mutation == 'action':
        candidate['actions']['fixed']['pressure'] = .4
    elif mutation == 'recipe':
        candidate['recipes']['i']['advance'] = 2
    elif mutation == 'gesture':
        candidate['gestures']['overturn']['strokes'][1]['offset'][0] += .01
    else:
        candidate['gestures']['underturn']['strokes'][0]['scale'] = float('nan')
    with pytest.raises(ValueError):
        learning.require_lineage(candidate, initial)


def test_target_generator_has_no_candidate_or_search_access():
    source = inspect.getsource(targets)
    assert 'foundation_gestures' not in source
    assert 'compile_gestures' not in source
    assert 'candidate' not in inspect.signature(targets.segments).parameters
    fixture = learning.SPEC['fixtures'][0]
    curves = targets.segments(learning.SPEC['targets'], fixture)
    assert len(curves) == 3
    assert all(np.isfinite(curve).all() for curve in curves)
    assert learning.SPEC['targets']['stem']['end'][1] not in learning.SPEC['search']['values']
    assert learning.SPEC['targets']['lower-return']['bulge'][1] != 0


def test_selection_never_reads_heldout_and_fixed_control_does_not_search():
    calls = []

    def score(parameters, split):
        calls.append(split)
        return sum((value - .85) ** 2 for value in parameters)

    selected = learning.select(score, seed=7, ablation='attachment')
    assert set(calls) == {'train', 'development'}
    assert selected['held_out_accessed'] is False
    assert selected['parameters'] == [.85, .85, .85]
    calls.clear()
    fixed = learning.select(score, seed=7, ablation='fixed')
    assert fixed['parameters'] == [1., 1., 1.]
    assert len(calls) == 2


def test_topology_pairings_are_disjoint_and_cannot_exceed_six():
    fixtures = learning.SPEC['fixtures']
    training = {tuple(instance['gesture'] for instance in row['instances']) for row in fixtures if row['split'] != 'held_out'}
    heldout = {tuple(instance['gesture'] for instance in row['instances']) for row in fixtures if row['split'] == 'held_out'}
    assert not training & heldout
    assert {name for pairing in heldout for name in pairing} >= set(learning.SPEC['constructions'])


def test_frame_rejects_cropped_ink_and_regions():
    from scribesim.handvalidate.model import TrajectorySample
    with pytest.raises(ValueError, match='frame'):
        learning.paint([TrajectorySample(100, 10, True, .45, .5, 40)])
    with pytest.raises(ValueError, match='region'):
        learning.crop(np.zeros((10, 10, 3), dtype=np.uint8), [-10, 0, 1, 2])


def test_acceptance_requires_all_families_seeds_motion_and_controls():
    assert not learning.complete([])
    assert not learning.complete([{'seed': 7, 'passed': True}])
    assert not learning.benefit(1, .75)['passed']
    assert not learning.benefit(0, 0)['passed']
    assert learning.benefit(1, .749)['passed']


def test_reject_unknown_ablation_seed_and_nonfinite_score():
    for seed, ablation in [(8, 'attachment'), (7, 'extra')]:
        with pytest.raises(ValueError):
            learning.select(lambda *_: 0, seed=seed, ablation=ablation)
    with pytest.raises(ValueError, match='finite'):
        learning.select(lambda *_: float('nan'), seed=7, ablation='fixed')


def test_complete_rejects_forged_summary_flags_without_numeric_proofs():
    rows = [{'seed': seed, 'ablation': 'attachment', 'passed': True,
             'fixtures': [{'fixture': fixture, 'passed': True} for fixture in learning.SPEC['fixtures']
                          if fixture['split'] != 'development'],
             'controls': {name: {'detected': True} for name in learning.SPEC['controls']}}
            for seed in learning.SPEC['seeds']]
    assert not learning.complete(rows)


def test_worker_command_uses_importable_module_not_main(monkeypatch, tmp_path):
    def launch(command, **kwargs):
        assert command[2] == 'scribesim.curriculum.foundation_gestures'
        raise RuntimeError('verified command before any target rendering')

    monkeypatch.setattr(learning.subprocess, 'run', launch)
    monkeypatch.setattr(learning, '__name__', '__main__')
    with pytest.raises(RuntimeError, match='verified command'):
        learning.build(tmp_path / 'run')
