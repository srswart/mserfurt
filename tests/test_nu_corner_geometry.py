import pytest

from scripts import nu_corner_geometry as geometry


def line(start, end):
    return [[start[axis]+fraction*(end[axis]-start[axis]) for axis in range(2)]
            for fraction in (0, 1/3, 2/3, 1)]


def test_exact_geometry_approval_required():
    approval = geometry.approval_record()
    approval['maximum_instances'] = 3
    with pytest.raises(ValueError, match='approval'):
        geometry.verify(approval)


def test_contract_repin_rejected(monkeypatch):
    monkeypatch.setattr(geometry.actions, 'digest', lambda filename: 'forged')
    with pytest.raises(ValueError, match='contract report changed'):
        geometry.verify(geometry.approval_record())


def test_rightward_minimum_includes_interior():
    assert geometry.increasing_x([[0, 0], [1, 0], [-1, 1], [0, 1]])['status'] == 'fail'
    assert geometry.increasing_x(line([0, 0], [1, 1]))['status'] == 'pass'


def test_zero_derivative_is_not_admitted():
    assert geometry.increasing_x([[0, 0], [0, 1], [0, 2], [0, 3]])['status'] == 'unresolved'


def test_contact_thickness_and_corner_offset_are_present():
    curve = [[0, 0]]*4
    full = geometry.contact_enclosure(curve, 'full')
    corner = geometry.contact_enclosure(curve, 'core')
    assert max(point[0] for point in corner) < 0
    assert max(point[1] for point in full) > abs(geometry.capability.clearance.EDGE[1])


def test_contact_clearance_far_apart():
    assert geometry.contact_pair(line([0, 0], [0, 1]), 'full', line([2, 0], [2, 1]), 'full')


def test_splice_contact_is_bounded_not_whole_owner_waiver():
    assert geometry.contact_pair(line([0, -.1], [0, 0]), 'departure', line([0, 0], [0, .1]), 'core', [0, 0])
    assert not geometry.contact_pair(line([0, 0], [0, 2]), 'full', line([0, 0], [0, 2]), 'full', [0, 0])


def test_nonlocal_contact_unresolved():
    assert not geometry.contact_pair(line([0, 0], [0, .1]), 'full', line([0, 0], [0, .1]), 'full')


def test_curvature_peak_is_rejected():
    result = geometry.bounds.original.curvature_check([[0, 0], [.01, 0], [.01, .01], [.01, .02]])
    assert result['status'] == 'fail'


def test_unknown_fixture_cannot_construct():
    with pytest.raises(ValueError):
        geometry.construct({}, {'exposed_fixture': 'num'}, {})
