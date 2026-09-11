import copy
from fractions import Fraction
import math

import pytest

from scripts import nu_boundary_actions as actions
from scribesim.evo.nib_contact import contact_corners


@pytest.mark.parametrize('interval', [('0', '0.1'), ('0.9', '1'), ('0.90', '1.00')])
def test_exact_tenth_contacts_accepted(interval):
    lower, upper = actions.edge_interval(*interval)
    assert upper-lower == Fraction(1, 10)
    assert len(actions.BoundaryContact((0, 0), interval).corners()) == 4


@pytest.mark.parametrize('interval', [('0', '0.09999999999999999'), ('0.90000000000000001', '1'),
                                     ('0', '0.099'), ('1', '0'), ('0', '1.00001')])
def test_no_epsilon_or_subminimum_acceptance(interval):
    with pytest.raises(ValueError):
        actions.edge_interval(*interval)


@pytest.mark.parametrize('value', [.9, True, 'NaN', 'Infinity', '1e-1', '-0.1', '0.'+'0'*65])
def test_non_authoritative_numbers_rejected(value):
    with pytest.raises(ValueError):
        actions.exact(value)


def test_ramp_endpoints_and_exact_midpoint():
    negative = actions.PROFILES['departure']
    assert actions.interpolate(negative, '0') == (0, 1)
    assert actions.interpolate(negative, '1') == (0, Fraction(1, 10))
    assert actions.interpolate(negative, '0.5') == (0, Fraction(11, 20))
    positive = [['0', '0', '1'], ['1', '0.9', '1']]
    assert actions.interpolate(positive, '1') == (Fraction(9, 10), 1)
    assert actions.interpolate(positive, '0.5') == (Fraction(9, 20), 1)


@pytest.mark.parametrize('track', [[['0', '0', '1'], ['0', '0', '1']],
                                 [['0.1', '0', '1'], ['1', '0', '1']],
                                 [['0', '0', '1'], ['1', '0.91', '1']]])
def test_bad_tracks_rejected(track):
    with pytest.raises(ValueError):
        actions.validate_track(track)


@pytest.mark.parametrize('interval', [('0', '1'), ('0', '0.1'), ('0.9', '1')])
def test_reflection_preserves_labels_and_points(interval):
    contact = actions.BoundaryContact((1, 2), interval)
    reflected = contact.reflected()
    assert reflected.interval == contact.interval
    assert reflected.reflected() == contact
    expected = sorted((horizontal, -vertical) for horizontal, vertical in contact.corners())
    assert all(math.dist(before, after) < 1e-12 for before, after in zip(sorted(reflected.corners()), expected))


@pytest.mark.parametrize('interval', [('0', '1'), ('0', '0.1')])
def test_supported_legacy_contact_coordinates_unchanged(interval):
    contact = actions.BoundaryContact((1, 2), interval, 'physical-y-up')
    legacy = actions.capability.sample([1, 2], list(map(float, interval)))
    assert all(math.dist(before, after) < 1e-12 for before, after in zip(sorted(contact.corners()), sorted(contact_corners(legacy))))


def test_legacy_numeric_bug_is_not_silently_repaired():
    with pytest.raises(ValueError):
        contact_corners(actions.capability.sample([0, 0], [.9, 1]))
    assert actions.edge_interval('0.9', '1') == (Fraction(9, 10), 1)


@pytest.fixture
def inputs():
    source = actions.capability.source
    return source.read_json(source.CANDIDATE), source.read_json(actions.capability.investigation.OUTPUT/'report.json')


@pytest.mark.parametrize('text,count', [('nu', 8), ('mu', 10)])
def test_retained_actions_exact_and_manifest_has_no_geometry(inputs, text, count):
    candidate, prior = inputs
    original = copy.deepcopy(candidate)
    document = actions.manifest(candidate, text, prior)
    actions.validate_manifest(document, candidate, prior)
    assert candidate == original
    assert len(document['retained']) == count
    assert len(document['retained'])+len(document['boundary_slots']) <= 13
    assert all(piece['canonical_action'] == candidate['actions']['fixed'] for piece in document['retained'])
    assert all(piece['boundary_override'] is None for piece in document['retained'])
    assert not document['geometry_present']
    with pytest.raises(ValueError, match='no geometry'):
        actions.require_geometry_consumer(document)


@pytest.mark.parametrize('mutation', ['body_action', 'contributor', 'source', 'air', 'corner', 'geometry', 'duplicate', 'permission'])
def test_undeclared_changes_rejected(inputs, mutation):
    candidate, prior = inputs
    document = actions.manifest(candidate, 'nu', prior)
    if mutation == 'body_action':
        document['retained'][0]['canonical_action']['edge'] = [[0, 0, .1], [1, 0, .1]]
    elif mutation == 'contributor':
        document['boundary_slots'][1]['contributors'] = []
    elif mutation == 'source':
        document['retained'][0]['canonical_geometry_sha256'] = 'forged'
    elif mutation == 'air':
        document['tool']['pressure'] = 0
    elif mutation == 'corner':
        document['profiles']['core'] = [['0', '0.9', '1'], ['1', '0.9', '1']]
    elif mutation == 'geometry':
        document['boundary_slots'][0]['cubics'] = []
    elif mutation == 'duplicate':
        document['retained'].append(document['retained'][0])
    else:
        document['physical_execution_approved'] = True
    with pytest.raises(ValueError, match='Changed'):
        actions.validate_manifest(document, candidate, prior)


@pytest.mark.parametrize('text', ['um', 'num', 'nm'])
def test_scope_rejected(inputs, text):
    candidate, prior = inputs
    with pytest.raises(ValueError):
        actions.manifest(candidate, text, prior)
