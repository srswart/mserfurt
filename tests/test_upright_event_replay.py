import json

import pytest

from scribesim.handvalidate import upright_event_replay as replay, upright_letters as original
from scribesim.handvalidate.specimen import digest


def test_authorized_loader_preserves_candidate_and_debits_both_attempts():
    source = replay.load_inputs()
    assert source['candidate'] == json.loads((original.SOURCE/'candidate.json').read_text())
    assert digest(original.SPEC_PATH) == replay.AUTH['original_spec_sha256']
    assert {key: value for key, value in replay.SPEC.items() if key != 'continuation'} == original.SPEC
    assert source['prior_attempt']['debits']['7'] == {'renders': 149, 'seconds': 34.57516137394123}
    assert len(source['prior_attempt']['reports']) == 2
    assert replay.remaining(source['prior_attempt']['debits']['7'], 0, 0)[0] == 4851


def test_previous_readers_remain_fail_closed_after_authorized_code_change():
    from scribesim.handvalidate import upright_continuation
    for loader in (original.load_inputs, upright_continuation.load_inputs):
        with pytest.raises(ValueError, match='source identity'):
            loader()


def test_no_automatic_retry_after_authorized_attempt(tmp_path, monkeypatch):
    (tmp_path/'run-001').mkdir()
    monkeypatch.setattr(replay, 'BASE', tmp_path)
    monkeypatch.setattr(replay, 'load_inputs', lambda: pytest.fail('Retry started'))
    with pytest.raises(ValueError, match='immutable'):
        replay.build()


def test_new_reader_requires_external_pin(tmp_path):
    (tmp_path/'report.json').write_text('{}')
    with pytest.raises(ValueError, match='pinned'):
        replay.inspect_run(tmp_path, '0'*64)
