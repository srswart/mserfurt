import copy

import pytest

from scripts import letter_context_review as review


@pytest.fixture(scope='module')
def packet():
    return review.manifest_record()


def test_packet_contains_only_complete_training_grid(packet):
    assert len(packet['rows']) == 54
    assert {row['text'] for row in packet['rows']} == {'nn', 'nm', 'un', 'um', 'mn', 'mm'}
    for text in packet['training_pairs']:
        rows = [row for row in packet['rows'] if row['text'] == text]
        assert {(row['width_scale'], row['advance_delta']) for row in rows} == {
            (width, advance) for width in (.97, 1., 1.03) for advance in (-.05, 0., .05)}
        assert sum(row['identity'] for row in rows) == 1
        assert all(row['image_size'] == [1169, 390] for row in rows)


def test_budget_carries_failure_and_recovery_forward(packet):
    budgets = packet['budget']['seeds']
    assert [row['remaining_renders'] for row in budgets] == [3426, 3426, 3259]
    assert [row['remaining_seconds'] for row in budgets] == pytest.approx([582.1848200419918, 988.4159828750417, 579.0667824570555])
    assert packet['budget']['p3_new_physical_runs_authorized'] == 0
    assert packet['budget']['p3_new_renders_authorized'] == 0
    assert packet['fitting_authorized'] is False
    inventory = packet['budget']['future_conservative_inventory']
    cases = (4*(6+3+6)+3+4)*4*2
    assert inventory['controller_runs_per_seed_without_reuse'] == cases == 536
    assert inventory['render_calls_per_seed_without_reuse'] == cases*3+(4*15+3+4)*2+2 == 1744


def complete_response(packet):
    return {'version': review.REVIEW_VERSION, 'packet_sha256': review.object_digest(packet),
            'author': 'Test reviewer', 'objective_approved': True,
            'reviews': {row['id']: {'rank': 1, 'excluded': False, 'note': ''} for row in packet['rows']}}


def test_blank_preferences_cannot_release_fitting(packet):
    response = complete_response(packet)
    response['objective_approved'] = False
    response['reviews'][packet['rows'][0]['id']]['rank'] = None
    result = review.validate_review(response, packet)
    assert not result['labels_complete']
    assert not result['objective_approved']
    assert not result['fitting_authorized']


def test_ties_are_valid_but_do_not_authorize_fitting(packet):
    result = review.validate_review(complete_response(packet), packet)
    assert result['labels_complete'] and result['objective_approved']
    assert result['fitting_authorized'] is False
    assert result['budget_ready_for_fitting'] is False


@pytest.mark.parametrize('rank', [True, 0, 10, 1.5, '1'])
def test_reject_malformed_ranks(packet, rank):
    response = complete_response(packet)
    response['reviews'][packet['rows'][0]['id']]['rank'] = rank
    with pytest.raises(ValueError):
        review.validate_review(response, packet)


def test_reject_wrong_packet_unknown_row_and_excluded_rank(packet):
    response = complete_response(packet)
    changed = copy.deepcopy(response)
    changed['packet_sha256'] = '0'*64
    with pytest.raises(ValueError):
        review.validate_review(changed, packet)
    changed = copy.deepcopy(response)
    changed['reviews']['unknown'] = {'rank': 1, 'excluded': False, 'note': ''}
    with pytest.raises(ValueError):
        review.validate_review(changed, packet)
    response['reviews'][packet['rows'][0]['id']]['excluded'] = True
    with pytest.raises(ValueError):
        review.validate_review(response, packet)


def test_all_excluded_cell_blocks_readiness(packet):
    response = complete_response(packet)
    for row in packet['rows']:
        if row['text'] == 'nn':
            response['reviews'][row['id']] = {'rank': None, 'excluded': True, 'note': 'Not usable'}
    result = review.validate_review(response, packet)
    assert not result['labels_complete']
    assert result['cells_without_admissible_variant'] == ['nn']


def test_frozen_images_and_dimensions_are_verified(packet):
    review.verify_images(packet)


def test_existing_packet_not_overwritten(tmp_path, monkeypatch):
    monkeypatch.setattr(review, 'OUTPUT', tmp_path)
    with pytest.raises(FileExistsError):
        review.prepare()
