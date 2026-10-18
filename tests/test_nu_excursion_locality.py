from fractions import Fraction
import math

import pytest

from scripts import nu_excursion_locality as locality


def test_exact_split_and_restriction_preserve_curve():
    curve = locality.exact_curve([[0, 0], [1, 2], [2, 1], [3, 0]])
    clipped = locality.restrict(curve, Fraction(1, 4), Fraction(3, 4))
    assert clipped[0] == locality.point(curve, Fraction(1, 4))
    assert clipped[-1] == locality.point(curve, Fraction(3, 4))
    assert locality.point(clipped, Fraction(1, 2)) == locality.point(curve, Fraction(1, 2))


def test_refinement_removes_conservative_control_hull_excess():
    curve = locality.exact_curve([[0, 0], [1, 0], [1, 0], [0, 0]])
    result = locality.radius_bounds(curve, curve[0], Fraction(0), Fraction(1), True)
    assert result['status'] == 'bounded'
    assert result['lower_squared'] == result['upper_squared'] == Fraction(9, 16)
    assert result['splits'] > 0


def test_real_outside_point_is_distinct_from_upper_bound():
    curve = locality.exact_curve([[0, 0], [0, 1], [1, 1], [1, 0]])
    result = locality.radius_bounds(curve, curve[0], Fraction(0), Fraction(1), True)
    assert result['lower_squared'] > locality.RADIUS**2
    assert result['witness_parameter'] is not None


def test_outward_square_root_rounding():
    squared = Fraction(2, 3)
    assert Fraction(locality.sqrt_bound(squared, False))**2 <= squared
    assert Fraction(locality.sqrt_bound(squared, True))**2 >= squared


def test_ambiguous_root_and_nonfinite_curve_fail_closed():
    curve = locality.exact_curve([[0, 0], [1, 0], [2, 0], [3, 0]])
    with pytest.raises(ValueError):
        locality.crossing_bracket(curve, .5, False)
    with pytest.raises(ValueError):
        locality.exact_curve([[0, 0], [1, math.inf], [2, 0], [3, 0]])


def test_subdivision_budget_does_not_fabricate_containment():
    curve = locality.exact_curve([[0, 0], [1, 0], [1, 0], [0, 0]])
    result = locality.radius_bounds(curve, curve[0], Fraction(0), Fraction(1), True, max_splits=0)
    assert result['status'] == 'unresolved'
    assert result['upper_squared'] > result['lower_squared']


def test_historical_dependency_mutation_is_not_whitelisted(monkeypatch):
    monkeypatch.setattr(locality, 'digest', lambda path: 'changed')
    with pytest.raises(ValueError, match='Saved study'):
        locality.verify()


def test_authority_preserves_limits_and_prohibits_new_geometry():
    record = locality.approval()
    assert record['new_candidates'] == record['images'] == record['physical_runs'] == 0
    assert not record['fitting'] and record['automatic_retries'] == 0
    assert record['radius_mm'] == .1125 and record['horizontal_limit_mm'] == .0045
