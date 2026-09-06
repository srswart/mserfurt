import copy

import numpy as np
import pytest


def test_foundation_initialization_preserves_old_six_and_exact_new_ports():
    from scribesim.evofit.foundation_contract import initial_model, SPEC, validate_extensions
    from scribesim.evofit.stroke_gestures import validate_gestures

    model = initial_model()
    validate_extensions(model)
    validate_gestures(model)
    assert {key: model['primitives'][key] for key in SPEC['baseline']['primitives']} == SPEC['baseline']['primitives']
    assert len(model['primitives']) == len(model['gestures']) == 8
    assert set(model['recipes']) == {'i', 'n', 'u', 'm', 'h'}


def test_audited_six_cap_is_expanded_and_legacy_four_is_unchanged():
    from scribesim.evofit.foundation_contract import initial_model
    from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures, SCHEMA

    model = initial_model()
    result = compile_gestures('m', model)
    assert len(result['strokes']) == 6
    assert len({row['occurrence_id'] for row in result['strokes']}) == 6
    legacy = copy.deepcopy(model)
    legacy['schema_version'] = SCHEMA
    with pytest.raises(ValueError):
        validate_gestures(legacy)
    excess = copy.deepcopy(model)
    excess['recipes']['m']['gestures'].append(copy.deepcopy(excess['recipes']['m']['gestures'][-1]))
    with pytest.raises(ValueError, match='[Bb]udget|[Cc]ap|bounds'):
        validate_gestures(excess)


def test_audit_exposes_every_hypothesis_and_character_without_accepting_debt():
    from scribesim.evofit.foundation_contract import audit, initial_model
    from scribesim.evofit.stroke_gestures import compile_gestures

    report = audit(initial_model())
    assert len(report['hypotheses']) == 8 and len(report['characters']) == 12
    assert report['selected_cap'] == 6
    assert report['cap_checks'] == {'4': False, '5': False, '6': True}
    assert not report['training_permitted'] and not report['learned_primitives_accepted']
    assert all(row['port_errors'] == 0 for row in report['characters'] if row['status'] == 'construction')
    for text in ('r','o','a','d','e','l','g'):
        with pytest.raises(ValueError, match='Unsupported'):
            compile_gestures(text, initial_model())


@pytest.mark.parametrize('mutation', ['old', 'port', 'cycle', 'nan', 'reflection', 'rotation', 'detached', 'residual', 'family'])
def test_contract_rejects_invalid_or_hidden_geometry(mutation):
    from scribesim.evofit.foundation_contract import initial_model
    from scribesim.evofit.stroke_gestures import validate_gestures

    model = initial_model()
    if mutation == 'old': model['primitives']['stem']['cubics'][0][1][0] += .001
    if mutation == 'port': model['primitives']['lower-return']['cubics'][0][1][0] += .01
    if mutation == 'cycle': model['gestures']['underturn']['strokes'][0]['primitive'] = 'underturn'
    if mutation == 'nan': model['gestures']['underturn']['strokes'][0]['scale'] = float('nan')
    if mutation == 'reflection': model['gestures']['underturn']['strokes'][0]['scale'] = -1
    if mutation == 'rotation': model['recipes']['u']['gestures'][0]['rotation_deg'] = 180
    if mutation == 'detached': model['gestures']['underturn']['strokes'][1]['offset'][0] += .01
    if mutation == 'residual': model['recipes']['u']['cubics'] = []
    if mutation == 'family': model['primitives']['extra'] = copy.deepcopy(model['primitives']['stem'])
    with pytest.raises(ValueError): validate_gestures(model)


def test_independent_targets_do_not_consume_candidate_geometry():
    from scribesim.evofit.foundation_contract import target_points, SPEC, initial_model

    before = target_points('lower-return')
    model = initial_model()
    model['primitives']['lower-return']['cubics'][0][1][0] += .1
    assert np.array_equal(before, target_points('lower-return'))
    assert np.allclose(before[0], SPEC['new_families']['lower-return']['start'])
    assert np.allclose(before[-1], SPEC['new_families']['lower-return']['end'])
    assert before[:, 1].min() < 0 and target_points('upper-return')[:, 1].max() > 0
    assert {row['topology'] for row in SPEC['targets']['train']} == {'single'}
    assert all(isinstance(row['topology'], list) for row in SPEC['targets']['topology_held_out'])


def test_contract_run_is_budgeted_read_only_and_fail_closed(tmp_path):
    from scribesim.evofit.foundation_contract import build, verify_prerequisites, SPEC

    verify_prerequisites()
    with pytest.raises(ValueError): verify_prerequisites({**SPEC, 'prerequisites': {}})
    report = build(tmp_path / 'run')
    assert report['status'] == 'pass' and report['renders'] <= 100
    assert report['optimization_evaluations'] == report['training_renders'] == 0
    assert not report['training_permitted']
    with pytest.raises(ValueError): build(tmp_path / 'run')


def test_foundation_identity_survives_compilation_and_tracking_metadata():
    from scribesim.evofit.foundation_contract import initial_model, SCHEMA
    from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide
    from scribesim.pathguide.gesture_actions import code_identities

    model = initial_model()
    assert compile_gestures('m', model)['schema_version'] == SCHEMA
    assert gesture_guide('m', model).metadata['schema_version'] == SCHEMA
    assert 'scribesim/evofit/foundation_contract.py' in code_identities()
    assert any(name.endswith('contract/spec-v1.json') for name in code_identities())


def test_foundation_allows_only_port_preserving_fit_and_fixed_tool():
    from scribesim.evofit.foundation_contract import initial_model, SPEC
    from scribesim.evofit.stroke_gestures import validate_gestures

    model = initial_model()
    contract = SPEC['new_families']['lower-return']
    model['primitives']['lower-return']['cubics'][0][1] = [value + .30 * rate for value, rate in zip(contract['start'], contract['entry'])]
    validate_gestures(model)
    model['actions']['fixed']['orientation'] = [[0, 40], [1, 41]]
    with pytest.raises(ValueError, match='[Ff]ixed'):
        validate_gestures(model)
