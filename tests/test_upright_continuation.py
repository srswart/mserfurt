import copy

import pytest

from scribesim.handvalidate import upright_continuation as continuation
from scribesim.handvalidate import upright_letters as original


def test_continuation_binds_failed_attempt_without_changing_protocol():
    source = continuation.load_inputs()
    assert source['candidate'] == original.load_inputs()['candidate']
    assert {key: value for key, value in continuation.SPEC.items() if key != 'continuation'} == original.SPEC
    assert source['prior_attempt']['debits']['7']['renders'] == 2
    assert source['prior_attempt']['debits']['7']['seconds'] > 0
    assert source['prior_attempt']['report_sha256'] == continuation.AUTH['prior_report_sha256']


def test_prior_calls_and_time_reduce_the_same_seed_budget():
    debit = {'renders': 2, 'seconds': .9}
    assert continuation.remaining(debit, 100, 20) == (4898, 1779.1)
    with pytest.raises(RuntimeError, match='budget'):
        continuation.remaining(debit, 4998, 20)
    with pytest.raises(RuntimeError, match='budget'):
        continuation.remaining(debit, 1, 1799.1)


def test_no_overwrite_or_automatic_retry(tmp_path, monkeypatch):
    (tmp_path/'run-001').mkdir()
    monkeypatch.setattr(continuation, 'BASE', tmp_path)
    monkeypatch.setattr(continuation, 'load_inputs', lambda: pytest.fail('Attempted new execution'))
    with pytest.raises(ValueError, match='immutable'):
        continuation.build()


def test_reader_checks_combined_debits_not_only_new_calls():
    debits = {str(seed): {'renders': 2 if seed == 7 else 0, 'seconds': .9 if seed == 7 else 0}
              for seed in (7, 19, 41)}
    ledger = []
    for seed in (7, 19, 41):
        for index, label in enumerate(('first', 'replay'), 1):
            debit = debits[str(seed)]
            ledger.append({'seed': seed, 'process': label, 'renders': 10, 'cumulative_renders': 10*index,
                'cumulative_seconds': index, 'combined_renders': 10*index+debit['renders'],
                'combined_seconds': index+debit['seconds']})
    assert continuation.check_combined(ledger, debits) == 62
    for field in ('combined_renders', 'combined_seconds'):
        changed = copy.deepcopy(ledger)
        changed[0][field] = 0
        with pytest.raises(ValueError, match='combined'):
            continuation.check_combined(changed, debits)


def test_continuation_reader_requires_consumer_pin(tmp_path):
    (tmp_path/'report.json').write_text('{}')
    with pytest.raises(ValueError, match='pinned'):
        continuation.inspect_run(tmp_path, '0'*64)
