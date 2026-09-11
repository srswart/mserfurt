import copy

import pytest

from scripts import stroke_attachment_audit as audit


@pytest.fixture
def candidate():
    return audit.source.read_json(audit.source.CANDIDATE)


def test_cubic_evaluation_and_monotonic_height_root():
    cubic = [[0, 0], [0, 1], [0, 2], [0, 3]]
    parameter = audit.height_parameter(cubic, .75)
    assert parameter == pytest.approx(.25, abs=1e-14)
    assert audit.point(cubic, parameter) == pytest.approx([0, .75])
    assert audit.tangent(cubic, parameter) == [0, 1]


def test_height_outside_or_nonmonotonic_rejects():
    with pytest.raises(ValueError):
        audit.height_parameter([[0, 0], [0, 1], [0, 2], [0, 3]], 4)
    with pytest.raises(ValueError):
        audit.height_parameter([[0, 0], [0, 3], [0, -1], [0, 2]], 1)


def test_baseline_requires_both_ends_to_be_revisited():
    assert audit.baseline_obstruction(0, [0, -1], 'departure')
    assert audit.baseline_obstruction(0, [0, 1], 'receiving')
    assert not audit.baseline_obstruction(.1, [0, -1], 'departure')
    assert not audit.baseline_obstruction(.1, [0, 1], 'receiving')


def test_frozen_sites_and_honest_feasibility(candidate):
    before = copy.deepcopy(candidate)
    result = audit.investigate(candidate)
    assert candidate == before
    assert len(result['site_pairs']) == 27
    assert sum(row['necessary_baseline_condition'] == 'fails' for row in result['site_pairs']) == 15
    assert sum(row['necessary_baseline_condition'] == 'not_ruled_out' for row in result['site_pairs']) == 12
    assert all(row['construction_feasible'] is None and not row['site_admitted'] for row in result['site_pairs'])
    assert result['negative_control']['text'] == 'nn'
    assert result['negative_control']['status'] == 'incompatible_receiving_site_for_family_P'
    assert all(row['horizontal_gap_mm'] > result['reference_turn_width_mm'] for row in result['site_pairs'])


def test_changed_candidate_rejected(candidate):
    candidate['letter_gap'] += .01
    with pytest.raises(ValueError, match='candidate'):
        audit.investigate(candidate)


@pytest.mark.parametrize('text', ['num', 'nuu', 'nm ', 'a'])
def test_no_extra_or_reserved_texts(candidate, text):
    with pytest.raises(ValueError, match='inventory'):
        audit.canonical(candidate, text)


def test_read_only_guards_and_immutable_output(tmp_path):
    with audit.source.evidence.read_only_guard(), pytest.raises(RuntimeError):
        audit.source.physical.execute_raw(None, None)
    with pytest.raises(FileExistsError):
        audit.snapshot(tmp_path)
