import copy

import pytest

from scripts import stroke_nm_envelope as evaluation


def test_quadratic_all_roots():
    assert evaluation.quadratic_roots([.1875, -1, 1]) == [.25, .75]
    assert evaluation.quadratic_roots([1, 0, 1]) == []
    assert evaluation.quadratic_roots([-1, 2, 0]) == [.5]


@pytest.mark.parametrize('coefficients', [[0, 0, 0], [.25, -1, 1]])
def test_degenerate_roots_unresolved(coefficients):
    with pytest.raises(evaluation.Unresolved):
        evaluation.quadratic_roots(coefficients)


def test_boundary_roots_unresolved():
    with pytest.raises(evaluation.Unresolved, match='boundary'):
        evaluation.interior_roots([0, 1, 0])


def test_two_interior_roots_are_not_lost():
    assert evaluation.interior_roots([.1875, -1, 1]) == [.25, .75]


def test_forged_approval_fails():
    approval = evaluation.approval_record()
    approval['geometry_generation'] = True
    with pytest.raises(ValueError, match='Unapproved'):
        evaluation.verify(approval)


def test_repin_fails_before_reinspection(monkeypatch):
    monkeypatch.setattr(evaluation.original, 'digest', lambda filename: 'forged')
    with pytest.raises(ValueError, match='Frozen input changed'):
        evaluation.verify(evaluation.approval_record())


def line(start, end):
    return [[start[axis]+fraction*(end[axis]-start[axis]) for axis in range(2)]
            for fraction in (0, 1/3, 2/3, 1)]


def test_nonlocal_separation():
    assert evaluation.pair_clearance(line([0, 0], [0, 1]), line([2, 0], [2, 1]))


def test_local_splice_containment():
    assert evaluation.pair_clearance(line([0, -.1], [0, 0]), line([0, 0], [0, .1]), [0, 0])


def test_small_overlap_outside_splice_not_admitted():
    first = line([1, 0], [1, .001])
    second = line([1, .0005], [1, .0015])
    assert not evaluation.pair_clearance(first, second, [0, 0])


def test_no_whole_owner_waiver():
    assert not evaluation.pair_clearance(line([0, 0], [0, 2]), line([0, 0], [0, 2]), [0, 0])


def test_uncertainty_is_not_clearance():
    curve = line([0, 0], [0, .1])
    assert not evaluation.pair_clearance(curve, curve)


def test_diagonal_edge_separation():
    edge = evaluation.original.clearance.EDGE
    first = line([0, 0], [0, .001])
    second = line([.05, .05], [.05, .051])
    assert edge[0] > 0 > edge[1]
    assert evaluation.pair_clearance(first, second)


@pytest.fixture
def synthetic_document():
    turn = [[0, 1], [-.001, .1], [.1, 0], [.3, 0]]
    transfer = [[.3, 0], [.5, 0], [.99, .25], [1, 1]]
    retained = line([.001, 1.9], [0, 1])
    pieces = [{'stroke': {'cubics': [retained]}} for _ in range(10)]
    pieces += [{'cubics_mm': [turn]}, {'cubics_mm': [transfer]}]
    return {'pieces': pieces, 'joins_mm': [[0, 1], [.3, 0], [1, 1]], 'height_mm': 1}


def test_synthetic_tangent_envelope(synthetic_document):
    assert evaluation.envelope(synthetic_document)['status'] == 'pass'


def test_locality_escape_not_admitted(synthetic_document):
    document = copy.deepcopy(synthetic_document)
    for piece in document['pieces'][-2:]:
        for control in piece['cubics_mm'][0]:
            control[1] *= 100
    for control in document['pieces'][3]['stroke']['cubics'][0]:
        control[1] *= 100
    for join in document['joins_mm']:
        join[1] *= 100
    document['height_mm'] *= 100
    result = evaluation.envelope(document)
    assert result['status'] != 'pass'
    assert result['reason'] == 'Locality not certified'


@pytest.mark.parametrize('mutation', ['excess', 'retrace', 'no_recovery', 'late_recovery', 'cusp'])
def test_adverse_envelopes_not_admitted(synthetic_document, mutation):
    document = copy.deepcopy(synthetic_document)
    turn = document['pieces'][-2]['cubics_mm'][0]
    if mutation == 'excess':
        turn[1][0] = -.1
    elif mutation == 'retrace':
        turn[2][1] = 2
    elif mutation == 'no_recovery':
        turn[-1][0] = -.2
    elif mutation == 'late_recovery':
        turn[2][0] = -.2
    else:
        turn[1] = turn[0][:]
    try:
        assert evaluation.envelope(document)['status'] != 'pass'
    except evaluation.Unresolved:
        pass
