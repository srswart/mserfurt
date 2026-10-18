import copy
from fractions import Fraction
import json

import pytest

from scripts import nu_ramp_contact_measurement as measurement


def line(start, end):
    return [[start[axis]+(end[axis]-start[axis])*part/3 for axis in (0, 1)] for part in range(4)]


def test_exact_length_enclosure():
    curve = measurement.exact.exact_curve(line([0., 0.], [3., 4.]))
    lower, upper = measurement.length_bounds(curve)
    assert lower <= 5 <= upper
    assert upper-lower < Fraction(1, 10**12)


def test_whole_domain_pair_accounting():
    curves = [line([0., 0.], [0., 1.]), line([0., 1.], [0., 2.])]
    result = measurement.measure(curves, 'receiving', 8)
    assert result['cells'] == 16
    assert result['possible_overlap_cell_pairs']+result['separated_cell_pairs'] == 16*17//2
    assert result['possible_cross_cubic_pairs'] > 0
    assert result['possible_overlap_arc_separation_upper_mm'] < 1
    assert result['classification'] == 'unresolved'


def test_no_arclength_action_reset_at_internal_join():
    curves = [line([0., 0.], [0., 1.]), line([0., 1.], [0., 2.])]
    _, points, _ = measurement.build_cells(curves, 'receiving', 8)
    assert points[8]['progress'][0] <= Fraction(1, 2) <= points[8]['progress'][1]
    assert measurement.active_bounds('receiving', points[8]['progress'])[0] > Fraction(1, 2)
    assert points[-1]['progress'] == (1, 1)


def test_boxes_contain_actual_endpoint_footprints():
    curves = [line([0., 0.], [1., 0.])]
    cells, points, _ = measurement.build_cells(curves, 'departure', 8)
    for index, cell in enumerate(cells):
        for point in points[index:index+2]:
            assert all(outer[0] <= inner[0] < inner[1] <= outer[1]
                       for outer, inner in zip(cell['box'], point['inner']))


def test_exact_revisit_witness_verifiable():
    curves = [line([0., 0.], [0., 1.]), line([0., 1.], [0., 0.])]
    result = measurement.measure(curves, 'receiving', 8)
    witness = result['point_membership_witness']
    assert witness['status'] == 'certified_disconnected_point_membership'
    paper = list(map(Fraction, witness['paper_nib_coordinates_exact']))
    rectangles = {name: [list(map(Fraction, interval)) for interval in rectangle]
                  for name, rectangle in witness['membership_rectangles_exact'].items()}
    for name in ('first_inner', 'return_inner'):
        assert all(lower < value < upper for value, (lower, upper) in zip(paper, rectangles[name]))
    assert any(value < lower or value > upper for value, (lower, upper) in zip(paper, rectangles['outside_outer']))
    assert result['classification'] == 'unresolved'


def test_no_grid_witness_is_not_continuous_pass():
    result = measurement.measure([line([0., 0.], [0., 2.])], 'departure', 8)
    assert result['point_membership_witness']['status'] == 'not_found_on_fixed_grid'
    assert result['classification'] == 'unresolved'


def test_second_cubic_is_not_ignored():
    first = line([0., 0.], [0., 1.])
    straight = measurement.measure([first, line([0., 1.], [0., 2.])], 'receiving', 8)
    returning = measurement.measure([first, line([0., 1.], [0., 0.])], 'receiving', 8)
    assert returning['possible_cross_cubic_arc_separation_upper_mm'] > straight['possible_cross_cubic_arc_separation_upper_mm']


@pytest.mark.parametrize('curves', [[], [[[0., 0.]]], [line([0., 0.], [0., 0.])],
                                  [line([0., 0.], [0., 1.]), line([0., 2.], [0., 3.])]])
def test_invalid_or_disconnected_aggregate_rejected(curves):
    with pytest.raises(ValueError):
        measurement.build_cells(curves, 'receiving', 8)


def test_boundaries_not_treated_as_separation():
    assert not measurement.disjoint(((0, 1), (0, 1)), ((1, 2), (1, 2)))
    assert measurement.disjoint(((0, 1), (0, 1)), ((2, 3), (0, 1)))


def test_no_mutation():
    curves = [line([0., 0.], [1., 1.])]
    before = copy.deepcopy(curves)
    measurement.measure(curves, 'receiving', 8)
    assert curves == before


def test_run_once_preserves_saved_input_and_never_accepts(tmp_path, monkeypatch):
    frozen = {'candidates': [{'candidate': {'boundary': [
        {'contact_profile': profile, 'cubics_mm': [line([0., 0.], [0., 1.])]}
        for profile in ('departure', 'receiving')]}}]}
    before = copy.deepcopy(frozen)
    monkeypatch.setattr(measurement, 'verify', lambda: frozen)
    monkeypatch.setattr(measurement, 'authority', lambda: {'synthetic': True})
    monkeypatch.setattr(measurement, 'OUTPUT', tmp_path/'one')
    calls = []
    monkeypatch.setattr(measurement, 'measure', lambda curves, profile: calls.append(profile) or {'classification': 'unresolved'})
    result = measurement.run()
    assert result['new_candidates'] == result['images'] == result['physical_runs'] == 0
    assert not result['accepted'] and frozen == before
    assert calls == ['departure', 'receiving']
    assert json.loads((measurement.OUTPUT/'report.json').read_text()) == result
    with pytest.raises(FileExistsError):
        measurement.run()


def test_timeout_persists_partial_measurement(tmp_path, monkeypatch):
    frozen = {'candidates': [{'candidate': {'boundary': []}}]}
    monkeypatch.setattr(measurement, 'verify', lambda: frozen)
    monkeypatch.setattr(measurement, 'authority', lambda: {})
    monkeypatch.setattr(measurement, 'OUTPUT', tmp_path/'stopped')
    def timeout(curves, profile):
        raise TimeoutError('synthetic budget')
    monkeypatch.setattr(measurement, 'measure', timeout)
    result = measurement.run()
    assert result['status'] == 'stopped' and result['error'] == 'synthetic budget'
    assert (measurement.OUTPUT/'report.json').is_file()
