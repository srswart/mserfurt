import copy
import json

import pytest

from scripts import stroke_context_audit as audit


@pytest.fixture
def candidate():
    return json.loads(audit.CANDIDATE.read_text())


def test_canonical_roles_and_shared_body(candidate):
    result = audit.geometry(candidate)
    assert [len(result['letters'][letter]['spans']) for letter in 'num'] == [4, 4, 6]
    for letter in result['letters'].values():
        assert letter['spans'][0]['roles'] == ['body', 'entry']
        assert letter['spans'][-1]['roles'] == ['body', 'exit']
        assert all(span['editable'] is False for span in letter['spans'])
        assert len(letter['contact_runs']) == 1
    assert all(row['baseline'] == 'pen_up_transfer' for row in result['boundaries'])
    assert all(row['endpoint_gap_mm'] > 0 for row in result['boundaries'])


def test_candidate_mutation_rejected(candidate):
    candidate['letter_gap'] += .01
    with pytest.raises(ValueError, match='candidate'):
        audit.geometry(candidate)


def test_directed_port_reversal():
    assert audit.direction([0, 0], [0, 1]) == [0, 1]
    assert audit.direction([0, 1], [0, 0]) == [0, -1]
    with pytest.raises(ValueError, match='Degenerate'):
        audit.direction([0, 0], [0, 0])


def test_reserved_or_unknown_probe_rejected():
    for text in (*audit.SEALED, 'a', 'nuu', 'uuu', 'muu'):
        with pytest.raises(ValueError, match='admitted'):
            audit.require_probe(text)


def test_trace_contact_is_not_inferred_from_upward_motion():
    event = {'contact': True, 'previous_contact': True, 'from_mm': [0, 1],
             'to_mm': [0, 0], 'owner': {'kind': 'stroke', 'primitive': 'rise',
             'occurrence_id': '0:1', 'contact_run_id': 'contact:0'}}
    result = audit.trace_summary({'trace': [event]}, {'0:1': 'contact:0'})
    assert result['pen_down_upward_events'] == 1
    assert result['lift_events'] == 0
    bad = copy.deepcopy(event)
    bad['owner']['kind'] = 'air'
    with pytest.raises(ValueError, match='contact'):
        audit.trace_summary({'trace': [bad]}, {'0:1': 'contact:0'})
    bad = copy.deepcopy(event)
    bad['owner']['contact_run_id'] = 'contact:9'
    with pytest.raises(ValueError, match='owner'):
        audit.trace_summary({'trace': [bad]}, {'0:1': 'contact:0'})


def test_read_only_guard_blocks_execution():
    with audit.evidence.read_only_guard(), pytest.raises(RuntimeError, match='forbidden'):
        audit.physical.execute_raw(None, None)


def test_snapshot_requires_external_pin_and_never_overwrites(tmp_path):
    destination = tmp_path/'snapshot'
    destination.mkdir()
    with pytest.raises(FileExistsError):
        audit.snapshot(destination)
    with pytest.raises(ValueError, match='pin'):
        audit.inspect(destination, '')
