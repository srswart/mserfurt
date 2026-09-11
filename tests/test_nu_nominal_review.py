import copy
import math
import xml.etree.ElementTree as ET

import pytest

from scripts import nu_nominal_review as nominal


def line():
    return [[0, fraction] for fraction in (0, 1/3, 2/3, 1)]


def test_corner_is_offset_thin_rectangle_not_centered_line():
    profiles = nominal.actions.PROFILES
    corner = nominal.polygons([line()], 'core', profiles)[0]
    assert max(point[0] for point in corner) < 0
    assert max(point[0] for point in corner)-min(point[0] for point in corner) == pytest.approx(.045*math.cos(math.radians(40))+.02*math.sin(math.radians(40)))


def test_full_corner_endpoints_and_restore():
    assert nominal.actions.interpolate(nominal.actions.PROFILES['departure'], '0') == (0, 1)
    assert nominal.actions.interpolate(nominal.actions.PROFILES['departure'], '1') == nominal.actions.edge_interval('0', '0.1')
    assert nominal.actions.interpolate(nominal.actions.PROFILES['receiving'], '1') == (0, 1)


def test_saved_drawings_are_distinct_complete_and_immutable():
    saved = nominal.source.read_json(nominal.evaluation.SAVED)
    untouched = copy.deepcopy(saved)
    before, after = nominal.drawings(saved, nominal.source.read_json(nominal.source.CANDIDATE))
    assert saved == untouched
    assert len(before) == 8 and len(after) == 11
    assert nominal.paths(before) != nominal.paths(after)
    assert [piece['profile'] for piece in after[-3:]] == ['departure', 'core', 'receiving']
    left, top, right, bottom = nominal.frame([before, after])
    for drawing in (before, after):
        for piece in drawing:
            for polygon in piece['polygons']:
                assert all(left < point[0] < right and top < -point[1] < bottom for point in polygon)
    document = ET.fromstring(nominal.svg(before, after))
    panels = document.findall('{http://www.w3.org/2000/svg}svg')
    assert len(panels) == 2
    assert panels[0].attrib['viewBox'] == panels[1].attrib['viewBox']


def test_mutated_candidate_rejected():
    saved = nominal.source.read_json(nominal.evaluation.SAVED)
    saved['profiles'] = {}
    with pytest.raises(ValueError, match='identity'):
        nominal.drawings(saved, {})


def test_zero_path_rejected():
    with pytest.raises(ValueError, match='Zero-length'):
        nominal.polygons([[[0, 0]]*4], 'full', nominal.actions.PROFILES)
