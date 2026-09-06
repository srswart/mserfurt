import hashlib

import numpy as np
import pytest

from scribesim.evo.nib_contact import ContactSample, contact_corners, reflect_sample
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.model import TrajectorySample
from scribesim.handvalidate import tool_contract as oracle


def test_partial_contact_translates_endpoints_and_reflection_keeps_edge_identity():
    sample = ContactSample(1, 2, width_mm=.45, pressure=.5, nib_angle_deg=40,
                           edge_start=0, edge_end=.5)
    corners = contact_corners(sample)
    expected = oracle._corners({'center': [1, 2], 'angle': 40, 'edge': [0, .5]})
    assert np.allclose(sorted(corners), sorted(expected))
    reflected = reflect_sample(sample)
    assert reflected.edge_start == 0 and reflected.edge_end == .5
    assert np.allclose(sorted(contact_corners(reflected)), sorted((point[0], -point[1]) for point in corners))


@pytest.mark.parametrize('change', [{'edge_end': 0}, {'edge_start': -.1}, {'edge_end': float('nan')},
                                    {'pressure': .7}, {'width_mm': .6}, {'nib_angle_deg': 541}])
def test_invalid_contact_fails_closed(change):
    values = dict(x_mm=1, y_mm=1, width_mm=.45, pressure=.5, nib_angle_deg=40, edge_start=0, edge_end=1)
    with pytest.raises(ValueError):
        contact_corners(ContactSample(**{**values, **change}))


def test_legacy_pixels_and_explicit_reader_version():
    rows = [TrajectorySample(1, 1, True, .45, .5, 40), TrajectorySample(1, 2, True, .45, .5, 40),
            TrajectorySample(2, 1, False, .45, 0, 40), TrajectorySample(2, 1, True, .45, .5, 40),
            TrajectorySample(2, 2, True, .45, .5, 40)]
    assert hashlib.sha256(paint_trajectory(rows, [0, 3, 0, 3], dpi=180).tobytes()).hexdigest() == 'df5fc8c496d4831529751ba339c76bc2bb0ed2785b5e0f7f740a52a0a8136cb2'
    with pytest.raises(ValueError):
        paint_trajectory([ContactSample(1, 1, width_mm=.45, pressure=.5, nib_angle_deg=40)], [0, 3, 0, 3])
    with pytest.raises(ValueError):
        paint_trajectory(rows, [0, 3, 0, 3], contact_version='physical-edge-v1')


def test_canonical_sweep_matches_independent_fixtures():
    for fixture in oracle.tool_fixtures():
        rows = []
        for run in fixture['runs']:
            if rows:
                rows.append(ContactSample(0, 0, False, .45, 0, 40))
            rows.extend(ContactSample(*pose['center'], width_mm=.45, pressure=.5, nib_angle_deg=pose['angle'],
                                      edge_start=pose['edge'][0], edge_end=pose['edge'][1]) for pose in run)
        image = paint_trajectory(rows, [0, 3, 0, 3], dpi=oracle.PPMM * 25.4, contact_version='physical-edge-v1')
        actual = np.asarray(image).mean(axis=2) < 180
        expected = oracle._oracle(fixture, oracle.ProbeBudget())
        assert oracle._disagreement(expected, actual) <= .05, fixture['id']


def test_stationary_dab_is_not_silently_painted():
    sample = ContactSample(1, 1, width_mm=.45, pressure=.5, nib_angle_deg=40)
    with pytest.raises(ValueError, match='stationary'):
        paint_trajectory([sample, sample], [0, 3, 0, 3], contact_version='physical-edge-v1')
