import math

import pytest

from scribesim.handvalidate.tool_contract import ProbeBudget, edge_endpoints, probe, tool_fixtures


def test_directed_half_edges_shift_footprint_center():
    negative = edge_endpoints((2, 3), 0, (0, .5))
    positive = edge_endpoints((2, 3), 0, (.5, 1))
    assert negative[0] == pytest.approx((1.775, 3))
    assert negative[1] == pytest.approx((2, 3))
    assert positive[0] == pytest.approx((2, 3))
    assert positive[1] == pytest.approx((2.225, 3))


def test_reflection_keeps_directed_edge_labels_and_wrap_is_continuous():
    original = edge_endpoints((1, 2), 40, (0, .25))
    reflected = edge_endpoints((1, -2), -40, (0, .25))
    for before, after in zip(original, reflected):
        assert after == pytest.approx((before[0], -before[1]))
    before = edge_endpoints((0, 0), 179, (0, 1))
    after = edge_endpoints((0, 0), 181, (0, 1))
    assert math.dist(before[0], after[0]) < .01


@pytest.mark.parametrize('angle,interval', [(float('nan'), (0, 1)), (0, (.8, .2)),
                                          (0, (-.1, .5)), (0, (0, 0)), (541, (0, 1))])
def test_invalid_expected_geometry_is_rejected(angle, interval):
    with pytest.raises(ValueError):
        edge_endpoints((0, 0), angle, interval)


def test_budget_counts_all_renders_and_stops_at_time_limit():
    clock = [0.0]
    budget = ProbeBudget(limit=1, seconds=1, clock=lambda: clock[0])
    budget.consume()
    with pytest.raises(ValueError, match='budget'):
        budget.consume()
    budget = ProbeBudget(limit=2, seconds=1, clock=lambda: clock[0])
    clock[0] = 1.0
    with pytest.raises(ValueError, match='budget'):
        budget.consume()


def test_fixture_contract_is_three_families_with_explicit_finishing_lift():
    fixtures = tool_fixtures()
    assert {fixture['family'] for fixture in fixtures} == {'orientation', 'edge', 'finishing'}
    assert len(fixtures) == 8
    terminal = next(fixture for fixture in fixtures if fixture['id'] == 'terminal')
    assert len(terminal['runs']) == 2


def test_probe_records_missing_contact_state_and_instantaneous_angle_without_accepting_it(tmp_path):
    report = probe(tmp_path / 'probe')
    assert report['decision'] == 'proceed-synthetic-contract-implementation-only'
    assert report['S1_action'] == 'not_evaluated'
    assert report['historical_calibration'] == 'unavailable'
    assert all(not present for present in report['active_edge_fields'].values())
    assert report['controller_angle_probe']['observed_rate_deg_s'] > 180
    assert report['controller_angle_probe']['meets_frozen_rate_bound'] is False
    assert report['budget']['renders'] <= 100
    assert report['budget']['optimization_evaluations'] == 0
    assert (tmp_path / 'probe' / 'footprints.png').exists()
    with pytest.raises(ValueError, match='empty'):
        probe(tmp_path / 'probe')


def test_budget_exhaustion_never_writes_a_success_report(tmp_path):
    with pytest.raises(ValueError, match='budget'):
        probe(tmp_path / 'probe', max_renders=1)
    assert not (tmp_path / 'probe' / 'report.json').exists()
