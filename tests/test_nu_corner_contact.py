from fractions import Fraction

import pytest

from scripts import nu_corner_contact as capability


def test_negative_corner_offset_and_reflection():
    result = capability.rectangle_probe([0, .1])
    assert result['status'] == 'pass'
    assert result['center_offset_length_mm'] == pytest.approx(.2025)
    assert result['reflected_interval'] == [0, .1]
    assert result['reflection_error_mm'] < 1e-12


def test_positive_corner_exposes_existing_numeric_rejection():
    result = capability.rectangle_probe([.9, 1])
    assert result['status'] == 'rejected_by_current_contact_api'
    assert result['float_fraction'] < .1
    assert Fraction(result['decimal_fraction']) == Fraction(1, 10)


def test_full_control_is_centered():
    result = capability.rectangle_probe([0, 1])
    assert result['status'] == 'pass'
    assert result['center_offset_length_mm'] == pytest.approx(0)


def test_too_small_contact_not_admitted():
    assert capability.rectangle_probe([0, .099])['status'] == 'rejected_by_current_contact_api'


def test_polygon_containment_distance():
    outside = [[0, 0], [2, 0], [2, 2], [0, 2]]
    inside = [[.5, .5], [1, .5], [1, 1], [.5, 1]]
    assert capability.polygon_distance(outside, inside) == 0
    assert capability.polygon_distance(inside, outside) == 0


def test_polygon_separation_distance():
    first = [[0, 0], [1, 0], [1, 1], [0, 1]]
    second = [[2, 0], [3, 0], [3, 1], [2, 1]]
    assert capability.polygon_distance(first, second) == pytest.approx(1)


def test_shrunk_rectangles_are_inside_full_contact():
    full = capability.hull(capability.contact_corners(capability.sample([0, 0], [0, 1])))
    for endpoint in (.1, .3, .7, 1):
        partial = capability.hull(capability.contact_corners(capability.sample([0, 0], [0, endpoint])))
        assert capability.hull(full+partial) == full


def test_approval_cannot_activate_geometry():
    approval = capability.approval_record()
    approval['geometry_generation'] = True
    with pytest.raises(ValueError, match='Capability-only'):
        capability.verify(approval)


def test_frozen_proposal_required(monkeypatch):
    monkeypatch.setattr(capability, 'digest', lambda filename: 'wrong')
    with pytest.raises(ValueError, match='Frozen input'):
        capability.verify(capability.approval_record())
