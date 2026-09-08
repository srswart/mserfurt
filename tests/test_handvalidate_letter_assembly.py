import copy
import json

import numpy as np
import pytest

from scribesim.handvalidate import letter_assembly as validation


def candidate():
    return json.loads((validation.alignment.BASE / 'run-001/seed-7/first/candidate.json').read_text())


def test_exact_candidate_and_no_detached_lower_layers():
    model = candidate()
    validation.require_candidate(model)
    for key in ('primitives', 'actions', 'gestures', 'recipes'):
        changed = copy.deepcopy(model)
        changed[key] = {}
        with pytest.raises(ValueError):
            validation.require_candidate(changed)


def test_isolated_rotated_occurrences_copy_the_frozen_instances():
    model = candidate()
    for fixture in validation.SPEC['fixtures'][:2]:
        probe = validation.probe(model, fixture)
        assert probe['recipes']['i']['gestures'] == [model['recipes'][fixture['from_letter']]['gestures'][0]]
        assert all(probe[key] == model[key] for key in model if key != 'recipes')
        assert len(validation.compile_gestures('i', probe)['strokes']) == 3


def test_full_letters_keep_exact_recipes_and_caps():
    model = candidate()
    for fixture in validation.SPEC['fixtures'][2:5]:
        assert validation.probe(model, fixture) == model
        assert len(validation.compile_gestures(fixture['text'], model)['strokes']) == (6 if fixture['text'] == 'm' else 4)


def test_level_checker_is_independent_of_curriculum_decisions(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Independent validation must not use assembly solver or its verdict')
    for name in ('make_model', 'normalization', 'landmarks', 'passed', 'measure'):
        monkeypatch.setattr(validation.alignment, name, forbidden)
    for fixture in validation.SPEC['fixtures']:
        model = validation.probe(candidate(), fixture)
        assert max(validation.levels(model, fixture).values()) < 1e-8


def test_climbing_second_arch_is_rejected_by_levels():
    fixture = validation.SPEC['fixtures'][4]
    model = candidate()
    model['recipes']['m']['gestures'][1]['offset'][1] += .08
    assert max(validation.levels(model, fixture).values()) > .079


def test_targets_are_candidate_free_and_every_full_frame_is_contained(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Target must not inspect candidate or compile geometry')
    monkeypatch.setattr(validation.alignment, 'make_model', forbidden)
    monkeypatch.setattr(validation.alignment, 'compile_gestures', forbidden)
    for fixture in validation.SPEC['fixtures']:
        path, regions = validation.target(fixture)
        validation.foundation.measurement.require_containment(path, frame=validation.SPEC['frame_mm'])
        model = validation.probe(candidate(), fixture)
        validation.foundation.measurement.require_containment(validation.foundation.nominal(model, fixture['text']), frame=validation.SPEC['frame_mm'])
        assert len(regions) == len(fixture['text'])
        assert validation.foundation.contact_runs(path) == (1 if fixture['kind'] == 'gesture' else 2*len(fixture['text']))


@pytest.mark.parametrize('value, expected', [(np.float64(.02), True), (.02, True), (.05, True), (.051, False),
                                          (float('nan'), False), (float('inf'), False), (True, False), ('0.02', False), (-.1, False)])
def test_numeric_gate_is_serialization_stable_and_fail_closed(value, expected):
    assert validation.below([value], .05) is expected
    if isinstance(value, (float, np.float64)) and np.isfinite(value):
        assert validation.below(json.loads(json.dumps([value])), .05) is expected


def test_blank_or_partial_records_cannot_pass():
    assert validation.passed({}) is False
    assert validation.passed({'fixtures': [], 'controls': {}}) is False


def test_request_cannot_promote_context_real_or_unreviewed_letters(monkeypatch):
    monkeypatch.setattr(validation.protocol, 'inspect', lambda *args: {'status': 'pass', 'S2_accepted': False, 'real_accepted': False})
    result = validation.inspect_run('unused', expected_report_sha256='pin')
    assert result['mechanical_validation_pass'] is True
    assert result['appearance_review'] == 'pending'
    assert result['S2_accepted'] is result['context_training_allowed'] is False


def test_wrong_report_hash_fails_before_source_or_trace_access(tmp_path, monkeypatch):
    (tmp_path / 'report.json').write_text('{}')
    def forbidden(*args, **kwargs):
        pytest.fail('Unpinned evidence must fail before source access')
    monkeypatch.setattr(validation, 'load_inputs', forbidden)
    with pytest.raises(ValueError):
        validation.inspect_run(tmp_path, expected_report_sha256='wrong')
