import copy
import gzip
import json

import pytest

from scribesim.handvalidate import upright_event_replay as replay, upright_letters as evaluation
from scripts import handvalidate_upright_events as inspector


def saved_control():
    directory = replay.BASE/'run-001/seed-7/first'
    fixture = evaluation.SPEC['fixtures'][-1]
    model = evaluation.probe(replay.load_inputs()['candidate'], fixture)
    run = json.loads(gzip.decompress((directory/'placed-mu-traces.json.gz').read_bytes()))['base']
    return directory, fixture, model, run


def test_saved_control_restores_runtime_aliases_without_changing_values():
    directory, fixture, model, run = saved_control()
    before = copy.deepcopy(run)
    expected = json.loads((directory/'controls.json').read_text())
    assert evaluation.trace_controls(model, fixture, run)['trace-owner']['errors']['owner'] == 1
    restored = inspector.restore_owner_aliases(model, fixture, run)
    assert restored == before
    assert run == before
    assert evaluation.trace_controls(model, fixture, restored)['trace-owner'] == expected['trace-owner']
    assert expected['trace-owner']['errors']['owner'] == 8


def test_alias_restoration_rejects_changed_owner_instead_of_replacing_evidence():
    _, fixture, model, run = saved_control()
    next(row for row in run['trace'] if row['contact'])['owner']['overlap_contributors'] = ['invented']
    with pytest.raises(ValueError, match='owner'):
        inspector.restore_owner_aliases(model, fixture, run)


def test_new_reader_checks_saved_worker_without_execution_or_render(monkeypatch):
    directory, _, _, _ = saved_control()
    def forbidden(*args, **kwargs):
        pytest.fail('Saved reader attempted execution or rendering')
    monkeypatch.setattr(evaluation, 'paint', forbidden)
    monkeypatch.setattr(evaluation.runtime, 'execute', forbidden)
    inspector.verify_record(replay.load_inputs(), json.loads((directory/'report.json').read_text()), directory)


def test_event_reader_requires_external_pin(tmp_path):
    (tmp_path/'report.json').write_text('{}')
    with pytest.raises(ValueError, match='pinned'):
        inspector.inspect_run(tmp_path, '0'*64)
