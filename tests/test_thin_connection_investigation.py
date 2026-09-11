import math

import pytest

from scripts import thin_connection_investigation as audit


def test_parallel_motion_has_tip_thickness_floor():
    direction = [math.cos(math.radians(-40)), math.sin(math.radians(-40))]
    assert audit.projected_width(direction) == pytest.approx(.02)
    assert audit.projected_width(direction, thickness=0) == pytest.approx(0)


def test_up_right_is_broad_under_current_orientation():
    assert audit.projected_width([1, 1]) > .44
    assert audit.projected_width([1, 1], .1) < .05


def test_reverse_motion_has_same_transverse_width():
    assert audit.projected_width([2, 1]) == audit.projected_width([-2, -1])


@pytest.mark.parametrize('direction', [[0, 0], [float('nan'), 1], [1, float('inf')]])
def test_invalid_direction(direction):
    with pytest.raises(ValueError):
        audit.projected_width(direction)


def test_partial_edge_below_supported_floor_rejected():
    with pytest.raises(ValueError):
        audit.projected_width([1, 1], .01)


def test_no_sealed_word_probe():
    with pytest.raises(ValueError, match='sealed'):
        audit.canonical({}, 'num')


def test_frozen_candidate_required():
    with pytest.raises(ValueError, match='identity'):
        audit.canonical({}, 'nu')


def test_length_bound_requires_long_detour_for_thin_up_right():
    result = audit.directional_case([0, 0], [3, 3])
    assert result['necessary_detour_ratio'] > 4
    assert result['straight_direction_full_contact_width_mm'] > result['proposed_thin_limit_mm']


def test_geometry_generation_not_used(monkeypatch):
    monkeypatch.setattr(audit, 'digest', lambda path: 'wrong')
    with pytest.raises(ValueError, match='Changed'):
        audit.build_report()
