import copy
import json

import pytest

from scripts import stroke_nm_construction as construction


def test_straight_curve_is_certified():
    result = construction.curvature_check([[0, 0], [1, 0], [2, 0], [3, 0]])
    assert result['status'] == 'pass'
    assert result['certified_upper_per_mm'] < 1e-6


def test_sharp_curve_is_rejected():
    result = construction.curvature_check([[0, 0], [.01, 0], [.01, .01], [.01, .02]])
    assert result['status'] == 'fail'
    assert result['curvature_per_mm'] > construction.CURVATURE_LIMIT


def test_length_bounds_enclose_straight_length():
    lower, upper = construction.length_bounds([[0, 0], [1, 0], [2, 0], [3, 0]])
    assert lower == upper == 3


def test_curved_length_bounds_are_tight():
    lower, upper = construction.length_bounds([[0, 0], [1, 0], [1, 1], [2, 1]])
    assert 2 < lower <= upper < 3
    assert upper-lower <= 1e-7


def test_forged_approval_rejected_before_source_access():
    approval = construction.approval_record()
    approval['conditional_pngs'] = 48
    with pytest.raises(ValueError, match='Approval differs'):
        construction.verify_inputs(approval)


def test_source_repin_rejected(monkeypatch):
    monkeypatch.setattr(construction, 'digest', lambda path: 'forged')
    with pytest.raises(ValueError, match='Frozen input changed'):
        construction.verify_inputs(construction.approval_record())


def test_output_immutable(tmp_path):
    construction.save(tmp_path, 'report.json', {'accepted': False})
    with pytest.raises(FileExistsError):
        construction.save(tmp_path, 'report.json', {'accepted': True})


@pytest.fixture
def frozen_attempt():
    directory = construction.BASE/'attempt-001'
    if not (directory/'candidate.json').exists():
        pytest.skip('One authorized attempt not yet made')
    document = json.loads((directory/'candidate.json').read_text())
    candidate = construction.attachment.source.read_json(construction.attachment.source.CANDIDATE)
    prior = construction.attachment.source.read_json(construction.attachment.OUTPUT/'report.json')
    cases = [case for case in prior['investigation']['site_pairs'] if case['text'] == 'nm']
    case = max(cases, key=lambda item: (item['departure']['height_mm'], item['receiving']['height_mm']))
    return document, candidate, case


def test_saved_candidate_exact(frozen_attempt):
    document, candidate, case = frozen_attempt
    construction.validate_identity(document, candidate, case)
    assert len(document['pieces']) == 12


@pytest.mark.parametrize('mutation', ['air', 'owner', 'contributor', 'duplicate', 'body', 'tangent', 'spacing'])
def test_undeclared_changes_fail(frozen_attempt, mutation):
    original, candidate, case = frozen_attempt
    document = copy.deepcopy(original)
    if mutation == 'air':
        document['pieces'][-1]['contact'] = 'air'
    elif mutation == 'owner':
        del document['pieces'][-1]['owner']
    elif mutation == 'contributor':
        document['pieces'][-1]['contributors'] = []
    elif mutation == 'duplicate':
        document['pieces'].append(document['pieces'][3])
    elif mutation == 'body':
        document['pieces'][0]['stroke']['cubics'][0][1][0] += .01
    elif mutation == 'tangent':
        document['pieces'][-1]['cubics_mm'][0][1][0] -= 2
    else:
        document['pieces'][4]['stroke']['cubics'][0][0][0] += .1
    with pytest.raises(ValueError, match='Undeclared'):
        construction.validate_identity(document, candidate, case)


@pytest.mark.parametrize('text', ['nn', 'mm', 'um'])
def test_unadmitted_sites_rejected(frozen_attempt, text):
    _, candidate, case = frozen_attempt
    rows = construction.attachment.canonical(candidate, text)['strokes']
    changed = copy.deepcopy(case)
    changed['receiving']['owner'] = rows[-1]
    with pytest.raises(ValueError, match='Unadmitted'):
        construction.construction(candidate, changed)


def test_policy_required(frozen_attempt):
    _, candidate, case = frozen_attempt
    with pytest.raises(ValueError, match='policy'):
        construction.construction(candidate, case, policy='automatic')


def test_stopped_attempt_never_renders(frozen_attempt):
    report = json.loads((construction.BASE/'attempt-001/report.json').read_text())
    assert report['status'] in ('rejected', 'unresolved')
    assert not report['accepted']
    assert report['raster_renders'] == report['controller_executions'] == report['fitting_evaluations'] == 0
    assert not list(construction.BASE.rglob('*.png'))


def test_saved_departure_has_negative_initial_horizontal_derivative(frozen_attempt):
    document, _, _ = frozen_attempt
    turn = document['pieces'][-2]['cubics_mm'][0]
    assert 3*(turn[1][0]-turn[0][0]) < 0
    assert construction.curvature_check(turn)['status'] == 'pass'
