import copy
import json

import numpy as np
import pytest

from scribesim.curriculum import letter_alignment_evidence as evidence


def record():
    labels = ('base', 'arc', 'time')
    tool = {'errors': 0, 'angle_rate_deg_s': 0, 'fixed_angle_error_deg': 0,
            'edge': [0, 1], 'mode': 'legacy-full-edge', 'active_rotation': False,
            'active_edge': False, 'active_finishing': False}
    rows = []
    for fixture in evidence.experiment.SPEC['fixtures']:
        owners = [str(index) for index in range(len(fixture['text']))]
        rows.append({'fixture': fixture, 'ratio': np.float64(.02), 'after': .01,
            'landmarks': {char: {'residual': 0, 'expanded': 4 if char != 'm' else 6} for char in 'num'},
            'motion': {label: {'pass': True} for label in labels},
            'comparisons': {label: {'pass': True} for label in ('arc', 'time')},
            'actual_target': {label: .01 for label in labels},
            'local_actual_target': {owner: {label: .01 for label in labels} for owner in owners},
            'local_nominal_target': {owner: .01 for owner in owners},
            'actual_landmarks_mm': {label: {owner: .0001 for owner in owners} for label in labels},
            'tool': {label: tool for label in labels}})
    return {'fixtures': rows, 'passed': False}


def test_numeric_decision_survives_json_round_trip_without_mutating_evidence():
    original = record()
    saved = json.loads(json.dumps(original))
    assert evidence.experiment.passed(original) is False
    assert evidence.experiment.passed(saved) is True
    assert evidence.runtime_decision(saved) is False
    assert evidence.numeric_decision(original) is True
    assert evidence.numeric_decision(saved) is True
    assert type(original['fixtures'][0]['ratio']) is np.float64
    assert original['passed'] is False


@pytest.mark.parametrize('value', [True, '0.02', None, float('nan'), float('inf'), -.1, .75])
def test_normalization_does_not_admit_invalid_or_outside_limit_ratios(value):
    candidate = record()
    candidate['fixtures'][0]['ratio'] = value
    assert evidence.numeric_decision(candidate) is False


@pytest.mark.parametrize('mutation', ['loss', 'landmark', 'motion', 'missing'])
def test_numeric_correction_does_not_bypass_other_gates(mutation):
    candidate = record()
    if mutation == 'loss':
        candidate['fixtures'][0]['actual_target']['base'] = .051
    elif mutation == 'landmark':
        candidate['fixtures'][0]['actual_landmarks_mm']['base']['0'] = .051
    elif mutation == 'motion':
        candidate['fixtures'][0]['motion']['base']['pass'] = False
    else:
        candidate['fixtures'].pop()
    assert evidence.numeric_decision(candidate) is False


def test_inspection_requires_pinned_source_before_numeric_correction(monkeypatch, tmp_path):
    def reject(adapter, directory, expected_report_sha256):
        assert expected_report_sha256 == 'pinned'
        assert adapter.identities() == evidence.experiment.identities()
        assert adapter.passed(json.loads(json.dumps(record()))) is False
        raise ValueError('Changed manifest')
    monkeypatch.setattr(evidence.experiment.protocol, 'inspect', reject)
    with pytest.raises(ValueError, match='Changed manifest'):
        evidence.inspect_run(tmp_path, expected_report_sha256='pinned')


def test_incomplete_evidence_fails_closed():
    assert evidence.numeric_decision({}) is False
    assert evidence.numeric_decision({'fixtures': []}) is False
