import pytest

from scribesim.evofit.stroke_gestures import migrate_v1
from scribesim.evofit.stroke_language import seed_language
from scribesim.curriculum.pen_actions import candidate_models, run_actions, select_by_development


@pytest.mark.parametrize('ablation', ['rotation', 'edge', 'finishing'])
def test_proposals_preserve_lower_geometry_and_isolate_freedoms(ablation):
    model = migrate_v1(seed_language())
    model['sampling'] = 'gesture-arc-v2'
    candidates = candidate_models(model, ablation)
    assert candidates[0] == model
    assert len(candidates) > 1
    for candidate in candidates:
        assert candidate['primitives'] == model['primitives']
        assert candidate['gestures'] == model['gestures']
        if ablation == 'finishing':
            assert candidate['actions'] == model['actions']
        else:
            assert candidate['recipes'] == model['recipes']
            track = 'edge' if ablation == 'rotation' else 'orientation'
            assert candidate['actions']['fixed'][track] == model['actions']['fixed'][track]


def test_development_selection_cannot_use_test_or_force_activation():
    rows = [{'candidate': 0, 'development': .1, 'test': 1}, {'candidate': 1, 'development': .1, 'test': 0}]
    assert select_by_development(rows)['candidate'] == 0
    rows[1]['development'] = .05
    assert select_by_development(rows)['candidate'] == 1


def test_blocked_prerequisites_prevent_all_pixels_and_optimization(tmp_path, monkeypatch):
    from scribesim.curriculum import pen_actions

    def forbidden(*args, **kwargs):
        raise AssertionError('No rendering or candidate search before acceptance')

    monkeypatch.setattr(pen_actions, 'execute_actions', forbidden)
    monkeypatch.setattr(pen_actions, 'candidate_models', forbidden)
    report = run_actions(tmp_path / 'blocked')
    assert report['status'] == 'blocked'
    assert report['renders'] == report['optimization_evaluations'] == 0
    assert not report['candidates']
    assert 'gesture_gate_not_passed' in report['reasons']
    assert 'bridge_convergence_not_passed' in report['reasons']
    with pytest.raises(ValueError):
        run_actions(tmp_path / 'blocked')


def test_real_mode_cannot_reuse_synthetic_admission(tmp_path):
    report = run_actions(tmp_path / 'real', real=True)
    assert report['status'] == 'blocked'
    assert 'live_real_G0_and_real_lower_layers_required' in report['reasons']


def test_midtrack_motion_is_not_a_fixed_baseline():
    model = migrate_v1(seed_language())
    model['sampling'] = 'gesture-arc-v2'
    model['actions']['fixed']['orientation'] = [[0, 40], [.5, 42], [1, 40]]
    with pytest.raises(ValueError, match='fixed'):
        candidate_models(model, 'edge')


def test_changed_tool_contract_invalidates_admission(monkeypatch):
    from scribesim.curriculum import pen_actions

    original = pen_actions.digest
    monkeypatch.setattr(pen_actions, 'digest', lambda path: 'changed' if path.name == 'spec-v1.json'
                        and path.parent.name == 'tool_contract' else original(path))
    assert 'tool_identity_stale' in pen_actions.prerequisites()['reasons']


def test_bound_checkpoint_cannot_be_swapped(monkeypatch):
    from scribesim.curriculum import pen_actions

    original = pen_actions.object_digest
    monkeypatch.setattr(pen_actions, 'object_digest', lambda value: 'wrong-model' if 'primitives' in value else original(value))
    assert 'gesture_candidate_identity_mismatch' in pen_actions.prerequisites()['reasons']


def test_search_core_keeps_null_on_ties_without_real_rendering(monkeypatch):
    import numpy as np
    from scribesim.curriculum import pen_actions

    pixels = np.full((4, 4, 3), 255, dtype=np.uint8)
    monkeypatch.setattr(pen_actions, 'execute_actions', lambda *args, **kwargs:
                        {'tracking_pass': True, 'images': {'actual': pixels, 'desired': pixels}})
    model = migrate_v1(seed_language())
    model['sampling'] = 'gesture-arc-v2'
    samples = [{'id': split, 'split': split, 'text': 'i', 'scale': 1, 'offset': [0, 0], 'raw': pixels}
               for split in ('train', 'development', 'test')]
    result = pen_actions._fit_lesson(model, samples, 'rotation', 7)
    assert result['selected']['candidate'] == 0
    assert result['status'] == 'null'
    assert result['heldout']['sensitivity'] == 0
