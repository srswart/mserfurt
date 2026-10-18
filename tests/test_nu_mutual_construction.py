import copy
from fractions import Fraction
import math

import pytest

from scripts import nu_mutual_construction as mutual


@pytest.fixture
def synthetic(monkeypatch):
    model = {'test_fixture': 'not-the-frozen-canonical-model'}
    rows = []
    for letter in range(2):
        for stroke in range(4):
            horizontal = .4 if letter == 0 else 1.8
            rows.append({'occurrence_id': f'{letter}:{stroke}', 'action_profile': 'fixed',
                         'cubics': [[[horizontal, 1.], [horizontal, .7],
                                     [horizontal, .4], [horizontal, 0.]]]})
    monkeypatch.setattr(mutual, 'canonical', lambda supplied, text: {'text': text, 'strokes': copy.deepcopy(rows)})
    return model


def test_approval_and_unchanged_limits():
    record = mutual.approval_record()
    assert record['approved_briefs'] == ['J1', 'J2']
    assert record['candidate_limit'] == 2 and record['retries'] == 0
    assert record['new_splice_centers_and_window_local_turn_guard']
    assert record['construction_check_seconds'] == record['render_seconds'] == 300
    assert not record['fitting'] and not record['mu'] and not record['nib_rotation']
    assert mutual.bounds.original.CURVATURE_LIMIT == pytest.approx(1/.1125)


def test_fixed_hermite_handle_rule():
    curve = mutual.vector_curve([0., 0.], [3., 4.], [1., 0.], [0., 1.])
    assert curve[1] == pytest.approx([5/3, 0.])
    assert curve[2] == pytest.approx([3., 4.-5/3])
    with pytest.raises(ValueError):
        mutual.vector_curve([0., 0.], [0., 0.], [1., 0.], [0., 1.])
    with pytest.raises(ValueError):
        mutual.vector_curve([0., 0.], [1., 1.], [0., 0.], [0., 1.])


def test_terminal_rules():
    departure = mutual.terminal_curve([0., 1.], [1., 0.], [0., -1.])
    receiving = mutual.terminal_curve([0., 1.], [1., 0.], [0., -1.], True)
    assert departure[1] == pytest.approx([0., .1])
    assert departure[2] == pytest.approx([1/3, 0.])
    assert receiving[1] == pytest.approx([2/3, 1.])
    assert receiving[2] == pytest.approx([1., .75])


def test_programs_are_different_and_source_is_unchanged(synthetic):
    before = copy.deepcopy(synthetic)
    first = mutual.construct(synthetic, 'J1')
    second = mutual.construct(synthetic, 'J2')
    assert first['port_order'] == ['A', 'F', 'P', 'Q', 'K', 'C']
    assert second['port_order'] == ['A', 'F', 'P', 'K', 'C']
    assert first['ports_mm']['P'][0] == first['ports_mm']['Q'][0]
    assert first['ports_mm']['K'][1] == 3.5
    assert second['ports_mm']['K'][1] == pytest.approx(3.57)
    assert synthetic == before
    for document in (first, second):
        mutual.validate_identity(document, synthetic)
        assert document['boundary'][0]['owner'] == 'n'
        assert document['boundary'][-1]['owner'] == 'u'
        assert all(piece['contributors'] == ['n', 'u'] for piece in document['boundary'])


@pytest.mark.parametrize('text', ['n', 'u', 'm', 'nu', 'nm', 'num'])
def test_context_off_is_exact_and_other_pairs_unchanged(synthetic, text):
    assert mutual.context_program(synthetic, text) == mutual.canonical(synthetic, text)
    if text != 'nu':
        assert mutual.context_program(synthetic, text, enabled=True) == mutual.canonical(synthetic, text)


@pytest.mark.parametrize('mutation', ['body', 'action', 'source_gap', 'source_duplicate', 'lineage', 'angle'])
def test_protected_identity_and_coverage_reject_mutation(synthetic, mutation):
    document = mutual.construct(synthetic, 'J1')
    if mutation == 'body':
        document['retained'][0]['cubics_mm'][0][0][0] += .01
    elif mutation == 'action':
        document['profiles']['core'] = copy.deepcopy(document['profiles']['full'])
    elif mutation == 'source_gap':
        document['boundary'][0]['replacement_source_span']['interval'][0] = '.9'
    elif mutation == 'source_duplicate':
        document['boundary'][1]['replacement_source_span'] = copy.deepcopy(document['boundary'][0]['replacement_source_span'])
    elif mutation == 'lineage':
        document['boundary'][1]['added_entry_travel'] = False
    else:
        document['nib_angle_deg_physical_y_down'] = 41.
    with pytest.raises(ValueError):
        mutual.validate_identity(document, synthetic)


def test_quadratic_range_includes_interior_extremum():
    assert mutual.quadratic_range([1, -4, 4]) == (Fraction(0), Fraction(1))
    assert mutual.quadratic_range([-1, 0, 0]) == (Fraction(-1), Fraction(-1))


@pytest.mark.parametrize('mutation', ['port', 'direction', 'handle', 'inventory', 'profile', 'owner'])
def test_numeric_program_cannot_be_silently_changed(synthetic, mutation):
    document = mutual.construct(synthetic, 'J1')
    if mutation == 'port':
        document['ports_mm']['F'][0] += .01
    elif mutation == 'direction':
        document['directions']['P'] = [1., 0.]
    elif mutation == 'handle':
        document['boundary'][1]['cubics_mm'][0][1][0] += .01
    elif mutation == 'inventory':
        document['boundary'].pop()
    elif mutation == 'profile':
        document['boundary'][1]['contact_profile'] = 'full'
    else:
        document['boundary'][1]['owner'] = 'u'
    with pytest.raises(ValueError):
        mutual.validate_identity(document, synthetic)


def test_uncertain_measurement_is_not_admission(synthetic, monkeypatch):
    document = mutual.construct(synthetic, 'J1')
    def uncertain(*args):
        raise mutual.bounds.Unresolved('Synthetic repeated-root ambiguity')
    monkeypatch.setattr(mutual, 'structural_checks', uncertain)
    result = mutual.inspect(document, synthetic)
    assert result['status'] == 'unresolved' and not result['render_eligible']


def test_envelope_and_curvature_failures_are_not_sampled_acceptance():
    escaped = [[0., 0.], [1., 2.], [2., 2.], [3., 0.]]
    assert mutual.envelope_check(escaped, [[0., 3.], [0., 1.]])['status'] == 'fail'
    assert mutual.bounds.original.curvature_check([[0., 0.], [.01, 0.], [.01, .01], [.01, .02]])['status'] == 'fail'


def test_length_allowance_does_not_reset_at_subdivisions():
    curves = [[[0., 0.], [0., 1/3], [0., 2/3], [0., 1.]],
              [[0., 1.], [1/3, 1.], [2/3, 1.], [1., 1.]]]
    result = mutual.length_check(curves)
    assert result['status'] == 'fail'
    assert result['limit_mm'] == pytest.approx(1.25*math.sqrt(2))


def test_vertical_entry_gets_positive_normal_progress():
    curve = [[0., 0.], [0., 1/3], [0., 2/3], [0., 1.]]
    result = mutual.thin_window([curve], [{'status': 'pass'}])
    assert result['status'] == 'pass'
    assert result['normal_progress_lower'] > .64
    assert result['overlap_arc_window_upper_mm'] < .032
    assert result['window_turn_upper_radians'] < math.pi/2


@pytest.mark.parametrize('curves', [
    [[[0., 1.], [0., 2/3], [0., 1/3], [0., 0.]]],
    [[[0., 0.], [1., 0.], [-1., 0.], [0., 0.]]],
    [[[0., 0.]]*4],
])
def test_reversed_progress_nonlocal_return_and_zero_speed_unresolved(curves):
    assert mutual.thin_window(curves, [{'status': 'pass'}])['status'] == 'unresolved'


def test_unknown_curvature_and_disconnected_join_block_contact():
    curve = [[0., 0.], [0., 1/3], [0., 2/3], [0., 1.]]
    assert mutual.thin_window([curve], [{'status': 'unresolved'}])['status'] == 'unresolved'
    assert mutual.thin_window([curve, curve], [{'status': 'pass'}]*2)['status'] == 'unresolved'


def test_corner_contact_reflection_and_no_action_reset():
    contact = mutual.actions.BoundaryContact((1., 2.), ('0', '0.1'), 'physical-y-up')
    assert sorted(contact.reflected().corners()) == pytest.approx(sorted((horizontal, -vertical) for horizontal, vertical in contact.corners()))
    for progress in (Fraction(0), Fraction(1, 3), Fraction(1)):
        assert mutual.actions.interpolate(mutual.actions.PROFILES['core'], progress) == (Fraction(0), Fraction(1, 10))


def test_finite_contact_requires_separation_or_named_local_join():
    curve = [[0., 0.], [1/3, 0.], [2/3, 0.], [1., 0.]]
    remote = [[horizontal, vertical+2] for horizontal, vertical in curve]
    assert mutual.original.contact_pair(curve, 'core', remote, 'full')
    assert not mutual.original.contact_pair(curve, 'core', curve, 'core', depth=24)


def test_ramp_self_contact_does_not_inherit_core_permission():
    straight = [[0., 1.], [0., 2/3], [0., 1/3], [0., 0.]]
    assert mutual.ramp_self_contact(straight, 'departure')['status'] == 'pass'
    returning = [[0., 0.], [1., 1.], [-1., 1.], [0., 0.]]
    assert mutual.ramp_self_contact(returning, 'departure')['status'] == 'unresolved'


def test_run_stops_without_retry_and_preserves_partial_evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(mutual, 'BASE', tmp_path)
    monkeypatch.setattr(mutual, 'OUTPUT', tmp_path/'batch')
    monkeypatch.setattr(mutual, 'verify', lambda: None)
    calls = []
    def stopped(model, name):
        calls.append(name)
        raise ValueError('Synthetic technical prerequisite failure')
    monkeypatch.setattr(mutual, 'construct', stopped)
    report = mutual.run()
    assert report['status'] == 'stopped' and calls == ['J1']
    assert (mutual.OUTPUT/'report.json').exists()
    assert (mutual.OUTPUT/'index.html').exists()
    with pytest.raises(FileExistsError):
        mutual.run()


def test_two_synthetic_rejections_do_not_trigger_rendering_or_retry(monkeypatch, tmp_path):
    monkeypatch.setattr(mutual, 'BASE', tmp_path)
    monkeypatch.setattr(mutual, 'OUTPUT', tmp_path/'batch')
    monkeypatch.setattr(mutual, 'verify', lambda: None)
    calls = []
    def stub(model, name):
        calls.append(name)
        return {'synthetic': name}
    monkeypatch.setattr(mutual, 'construct', stub)
    monkeypatch.setattr(mutual, 'inspect', lambda document, model: {'status': 'rejected', 'render_eligible': False, 'checks': {}})
    report = mutual.run()
    assert calls == ['J1', 'J2'] and report['new_candidates'] == 2
    assert report['status'] == 'no_candidate_admitted' and report['renders'] == 0
    assert not list(mutual.OUTPUT.glob('*.png')) and not list(mutual.OUTPUT.glob('*.svg'))


def test_wrong_approval_blocks_execution(monkeypatch):
    monkeypatch.setattr(mutual.source, 'read_json', lambda path: {'version': 'wrong'})
    with pytest.raises(ValueError, match='approval'):
        mutual.verify()


def test_status_board_exposes_preflight_failure_without_candidate_images():
    page = mutual.status_page({'error': 'Changed source <guard>', 'candidates': []})
    assert 'Changed source &lt;guard&gt;' in page
    assert 'No study candidate was constructed' in page
    assert '<img' not in page and '<svg' not in page
