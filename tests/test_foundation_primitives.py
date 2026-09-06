import copy
import json

import numpy as np
import pytest


def test_learning_protocol_is_frozen_and_topology_disjoint():
    from scribesim.curriculum.foundation_primitives import SPEC, initial_model, identities

    assert SPEC['seeds'] == [7, 19, 41]
    assert len(SPEC['ablations']) <= 3
    assert all(len(row['topology']) == 1 for split in ('train', 'development') for row in SPEC['splits'][split])
    assert any(len(row['topology']) == 4 for row in SPEC['splits']['held_out'])
    assert 'scribesim/curriculum/foundation_primitives.py' in identities()
    assert initial_model()['primitives']['lower-return']['cubics'][0][0] == [0, 0]


def test_handle_fit_preserves_every_nonpermitted_parameter():
    from scribesim.curriculum.foundation_primitives import initial_model, with_handles, require_lineage

    initial = initial_model()
    candidate = with_handles(initial, 'lower-return', [.21, .31])
    require_lineage(candidate, initial)
    expected = copy.deepcopy(initial)
    expected['primitives']['lower-return'] = candidate['primitives']['lower-return']
    assert expected == candidate and initial != candidate
    for handles in ([.1, .3], [float('nan'), .3], [.2, .5]):
        with pytest.raises(ValueError):
            with_handles(initial, 'lower-return', handles)
    changed = copy.deepcopy(candidate)
    changed['recipes']['i']['advance'] += .01
    with pytest.raises(ValueError):
        require_lineage(changed, initial)


def test_target_generator_does_not_take_candidate_and_ports_match():
    from scribesim.curriculum.foundation_primitives import target_segments, probe_model, initial_model, SPEC
    from scribesim.evofit.stroke_gestures import compile_gestures

    fixture = SPEC['splits']['held_out'][-1]
    target = target_segments(fixture)
    compiled = compile_gestures('i', probe_model(initial_model(), fixture))['strokes']
    assert len(target) == len(compiled) == 4
    for points, row in zip(target, compiled):
        assert np.allclose(points[0], row['cubics'][0][0])
        assert np.allclose(points[-1], row['cubics'][-1][-1])
    for before, after in zip(target, target[1:]):
        assert np.allclose(before[-1], after[0])


def test_search_never_reads_heldout_and_development_selects():
    from scribesim.curriculum.foundation_primitives import search_handles

    calls = []

    def score(handles, split):
        calls.append(split)
        optimum = [.2, .2] if split == 'train' else [.3, .3]
        return sum((value - expected) ** 2 for value, expected in zip(handles, optimum))

    result = search_handles(score, seed=7, values=[.2, .3], shortlist=4)
    assert result['handles'] == [.3, .3]
    assert set(calls) == {'train', 'development'}
    assert result == search_handles(score, seed=7, values=[.2, .3], shortlist=4)


def test_budget_counts_all_render_operations_and_rejects_overrun():
    from scribesim.curriculum.foundation_primitives import Budget

    budget = Budget(maximum=2, seconds=5)
    assert budget.render(lambda: 7) == 7
    budget.charge(1)
    with pytest.raises(RuntimeError):
        budget.render(lambda: 9)
    for maximum in (True, 0, 5001):
        with pytest.raises(ValueError):
            Budget(maximum=maximum)


def test_failed_baseline_stops_before_any_target_or_search(tmp_path, monkeypatch):
    from scribesim.curriculum import foundation_primitives as learning

    monkeypatch.setattr(learning, 'refresh_baseline', lambda output, budget: {'status': 'fail', 'reason': 'fixture failure'})
    monkeypatch.setattr(learning, 'render_target', lambda *args, **kwargs: pytest.fail('Target access after failed admission'))
    monkeypatch.setattr(learning, 'search_handles', lambda *args, **kwargs: pytest.fail('Search after failed admission'))
    report = learning.build(tmp_path / 'run')
    assert report['status'] == 'blocked' and report['optimization_evaluations'] == 0
    assert not report['S1_accepted']
    assert json.loads((tmp_path / 'run' / 'report.json').read_text()) == report
    with pytest.raises(ValueError):
        learning.build(tmp_path / 'run')


def test_admission_rejects_fabricated_status_or_stale_code(tmp_path):
    from scribesim.curriculum.foundation_primitives import verify_admission

    (tmp_path / 'report.json').write_text(json.dumps({'decision': {'status': 'pass'}, 'artifacts': {}}))
    with pytest.raises(ValueError):
        verify_admission(tmp_path)


def test_one_failed_family_or_fixture_cannot_average_into_pass():
    from scribesim.curriculum.foundation_primitives import benefit_pass

    assert benefit_pass(.2, .1)
    assert not benefit_pass(.2, .15)
    assert not benefit_pass(0, 0)
    assert not benefit_pass(.2, float('nan'))


def test_direction_overlay_is_saved_model_geometry_not_pixel_touchup(tmp_path):
    import xml.etree.ElementTree as ET
    from scribesim.curriculum.foundation_primitives import port_overlay, initial_model, with_handles

    candidate = with_handles(initial_model(), 'lower-return', [.21, .31])
    destination = tmp_path / 'ports.svg'
    port_overlay(destination, candidate)
    ET.parse(destination)
    content = destination.read_text()
    assert 'lower-return' in content and 'upper-return' in content
    assert 'entry' in content and 'exit' in content


def test_failed_seed_is_retained_and_never_grants_acceptance(tmp_path, monkeypatch):
    from scribesim.curriculum import foundation_primitives as learning

    monkeypatch.setattr(learning, 'refresh_baseline', lambda output, budget: {'status': 'pass'})

    def fake_seed(output, seed, budget):
        record = {'status': 'fail' if seed == 19 else 'pass', 'renders_including_setup': 1,
                  'candidate_sha256': str(seed), 'optimization_evaluations': 1}
        (output / 'report.json').write_text(json.dumps(record))
        return record

    monkeypatch.setattr(learning, 'fit_seed', fake_seed)
    report = learning.build(tmp_path / 'run')
    assert report['status'] == 'fail' and len(report['seeds']) == 3
    assert not report['S1_accepted'] and not report['gesture_training_permitted']
