import copy
from fractions import Fraction

import pytest

from scripts import nu_receiving_envelope as review


def saved():
    return review.source.read_json(review.SAVED)


def test_saved_receiving_envelope_and_unchanged_limits():
    document = saved()
    checks, historical = review.inspect(document)
    before = review.original.geometry_checks(document)
    assert historical['status'] == 'fail'
    assert checks['receiving_envelope_v2']['status'] == 'pass'
    for name, result in before.items():
        if name != 'S_rightward':
            assert checks[name] == result
    assert checks['thin_core']['limit_mm'] == pytest.approx(.08939393789931772)
    assert all(checks[name+'_curvature']['status'] == 'pass' for name in ('T', 'R', 'S'))


def test_crossing_is_interior_and_precedes_maximum():
    document = saved()
    result = review.receiving_check(document['boundary'][2]['cubics_mm'][0], document['incoming_tangent'])
    assert result['endpoint_crossing_factored']
    assert len(result['crossing_intervals']) == len(result['stationary_intervals']) == 1
    assert result['crossing_intervals'][0][1] < result['stationary_intervals'][0][0]
    assert result['original_negative_endpoint_dx'] < 0
    assert 0 < result['excursion_upper_mm'] < result['delta_mm'] < .0045
    assert result['locality_upper_mm'] < .1125


@pytest.mark.parametrize('field', ['retained', 'boundary', 'profiles', 'incoming_tangent', 'anchors_mm'])
def test_any_frozen_identity_mutation_rejected(field):
    document = saved()
    document[field] = None
    with pytest.raises(ValueError, match='identity changed'):
        review.inspect(document)


def test_forged_tangent_rejected():
    document = saved()
    result = review.receiving_check(document['boundary'][2]['cubics_mm'][0], [0, -1])
    assert result['status'] == 'fail'
    assert 'tangent mismatch' in result['reason']


@pytest.mark.parametrize('controls', [
    [[0, 3.5], [.1, 3.5], [.2, 3.2], [.3, 3]],
    [[0, 3.5], [0, 3.5], [.301, 3.2], [.3, 3]],
    [[0, 3.5], [-.1, 3.5], [.301, 3.2], [.3, 3]],
    [[0, 3.5], [.2, 3.5], [.4, 3.2], [.3, 3]],
    [[0, 3.5], [.2, 3.5], [.301, 2.9], [.3, 3]],
])
def test_missing_crossing_cusp_retrace_extra_stationary_or_excess_cap(controls):
    incoming = review.original.capability.clearance.attachment.tangent(controls, 1)
    assert review.receiving_check(controls, incoming)['status'] != 'pass'


def test_locality_escape_not_admitted():
    controls = [[0, 3.5], [.2, 3.5], [.304, 3.4], [.3, 0]]
    incoming = review.original.capability.clearance.attachment.tangent(controls, 1)
    result = review.receiving_check(controls, incoming)
    assert result['status'] != 'pass'
    assert result['locality_upper_mm'] > .1125


@pytest.mark.parametrize('coefficients', [[1, -2, 1], [0, 0, 0], [0, -1, 1]])
def test_double_zero_or_endpoint_roots_unresolved(coefficients):
    with pytest.raises(review.bounds.Unresolved):
        review.bounds.interior_roots(coefficients)


def test_root_helper_exposes_extra_roots_and_no_crossing():
    assert len(review.bounds.interior_roots([Fraction(3, 16), -1, 1])) == 2
    assert review.bounds.interior_roots([1, 0, 1]) == []


def test_approval_cannot_relax_limits_or_scope():
    approval = review.approval_record()
    approval['thinness_limit'] = 1
    with pytest.raises(ValueError, match='approval required'):
        review.verify(approval)


def test_frozen_file_mutation_rejected(monkeypatch):
    monkeypatch.setattr(review.actions, 'digest', lambda path: 'changed')
    with pytest.raises(ValueError, match='Frozen input changed'):
        review.verify(review.approval_record())


def test_review_never_constructs_and_gates_sweep(monkeypatch, tmp_path):
    monkeypatch.setattr(review, 'OUTPUT', tmp_path/'review')
    monkeypatch.setattr(review, 'APPROVAL', tmp_path/'approval.json')
    review.APPROVAL.write_text('{}')
    monkeypatch.setattr(review, 'verify', lambda approval: None)
    def forbidden(*args, **kwargs):
        raise AssertionError('Construction or contact sweep must not run')
    monkeypatch.setattr(review.original, 'construct', forbidden)
    monkeypatch.setattr(review.original, 'contact_checks', forbidden)
    monkeypatch.setattr(review, 'inspect', lambda document: ({'receiving': {'status': 'fail'}}, {}))
    report = review.run()
    assert report['status'] == 'rejected'
    assert report['checks']['finite_contact_sweep']['status'] == 'not_evaluated'
    assert report['geometry_generations'] == report['fitting_evaluations'] == 0
    with pytest.raises(FileExistsError):
        review.run()


def test_structural_pass_reaches_contact_without_constructor(monkeypatch, tmp_path):
    monkeypatch.setattr(review, 'OUTPUT', tmp_path/'review')
    monkeypatch.setattr(review, 'APPROVAL', tmp_path/'approval.json')
    review.APPROVAL.write_text('{}')
    monkeypatch.setattr(review, 'verify', lambda approval: None)
    def forbidden(*args, **kwargs):
        raise AssertionError('Constructor must never run')
    monkeypatch.setattr(review.original, 'construct', forbidden)
    monkeypatch.setattr(review, 'inspect', lambda document: ({'receiving': {'status': 'pass'}}, {}))
    seen = []
    def contact(document):
        seen.append(copy.deepcopy(document))
        return {'status': 'unresolved', 'reason': 'Synthetic nonlocal contact'}
    monkeypatch.setattr(review.original, 'contact_checks', contact)
    report = review.run()
    assert report['status'] == 'unresolved'
    assert seen == [saved()]
    assert not report['revised_geometry_pass']
    assert not report['accepted']
