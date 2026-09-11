import copy
import json
from types import SimpleNamespace

import pytest

from scripts import letter_context_recovery as recovery


def test_preparation_preserves_original_contract_and_debits():
    record = recovery.contract_record()
    assert record['seed'] == 41
    assert record['prior_renders'] == 954
    assert record['prior_seconds'] == pytest.approx(1165.910421833978)
    assert record['remaining_renders'] == 4046
    assert record['remaining_seconds'] == pytest.approx(1534.089578166022)
    assert record['cases'] == 244
    assert record['scheduled_renders'] == 787
    assert record['automatic_retries'] == 0
    assert record['fitting_authorized'] is False


@pytest.mark.parametrize('free,minimum,passes', [(12, 10, True), (10, 10, True), (9, 10, False), (4, 5, False)])
def test_storage_guard(monkeypatch, free, minimum, passes):
    monkeypatch.setattr(recovery.shutil, 'disk_usage', lambda path: SimpleNamespace(free=free*recovery.GIB))
    if passes:
        assert recovery.require_space(minimum*recovery.GIB) == free*recovery.GIB
    else:
        with pytest.raises(RuntimeError, match='Disk headroom'):
            recovery.require_space(minimum*recovery.GIB)


def test_guarded_ledger_stops_before_render(tmp_path, monkeypatch):
    ledger = recovery.StorageLedger(tmp_path/'execution.json', 2, 10)
    monkeypatch.setattr(recovery, 'require_space', lambda minimum: (_ for _ in ()).throw(RuntimeError('Disk headroom')))
    with pytest.raises(RuntimeError, match='Disk headroom'):
        ledger.render(lambda: pytest.fail('Render after storage failure'))
    assert ledger.used == 0


def test_receipt_requires_exact_schedule():
    from scripts import letter_context_recovery_evidence as evidence
    contract = {'cases': [1], 'schedule': ['paint']}
    receipt = {'renders': 1, 'events': [{'ordinal': 1, 'operation': 'paint', 'status': 'complete'}],
               'maximum_renders': 2, 'maximum_seconds': 10, 'elapsed_seconds': 5}
    evidence.verify_receipt(receipt, contract['schedule'], 2, 10, 6)
    for field, value in [('status', 'reserved'), ('ordinal', 2), ('operation', 'invented')]:
        changed = copy.deepcopy(receipt)
        changed['events'][0][field] = value
        with pytest.raises(ValueError):
            evidence.verify_receipt(changed, contract['schedule'], 2, 10, 6)


@pytest.mark.parametrize('elapsed', [float('nan'), -1, 11])
def test_receipt_rejects_invalid_time(elapsed):
    from scripts import letter_context_recovery_evidence as evidence
    receipt = {'renders': 0, 'events': [], 'maximum_renders': 2, 'maximum_seconds': 10, 'elapsed_seconds': elapsed}
    with pytest.raises(ValueError):
        evidence.verify_receipt(receipt, [], 2, 10, 10)


def test_old_attempt_remains_immutable():
    manifest = recovery.verify_original()
    assert len(manifest['artifacts']) == 12771
    assert not (recovery.ORIGINAL/'report.json').exists()


def test_existing_recovery_cannot_be_reused(tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, 'OUTPUT', tmp_path)
    with pytest.raises(FileExistsError):
        recovery.run('not-a-contract')


def test_changed_recovery_contract_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, 'PREPARED', tmp_path)
    (tmp_path/'contract.json').write_text(json.dumps({'changed': True}))
    with pytest.raises(ValueError, match='pin'):
        recovery.load_contract('0'*64)


@pytest.mark.parametrize('failure', ['exit', 'disk', 'timeout'])
def test_supervisor_preserves_failed_attempt_and_carries_debits(tmp_path, monkeypatch, failure):
    destination = tmp_path/'recovery'
    monkeypatch.setattr(recovery, 'OUTPUT', destination)
    contract = {'prior_seconds': 1165.9, 'prior_renders': 954, 'remaining_seconds': 1534.1,
                'remaining_renders': 4046, 'hashseed': '839', 'monitor_interval_seconds': 1}
    monkeypatch.setattr(recovery, 'load_contract', lambda checksum: contract)
    monkeypatch.setattr(recovery, 'verify_original', lambda: {})
    checks = []
    def check_space(minimum):
        checks.append(minimum)
        if failure == 'disk' and len(checks) > 1:
            raise RuntimeError('Disk headroom below guard')
        return 20*recovery.GIB
    monkeypatch.setattr(recovery, 'require_space', check_space)
    instant = [0]
    def clock():
        instant[0] += 1 if failure != 'timeout' else 600
        return instant[0]
    monkeypatch.setattr(recovery.time, 'monotonic', clock)
    monkeypatch.setattr(recovery.time, 'sleep', lambda seconds: None)
    class Process:
        returncode = 3 if failure == 'exit' else None
        killed = False
        def poll(self):
            return self.returncode
        def kill(self):
            self.killed = True
            self.returncode = -9
        def wait(self):
            return self.returncode
    process = Process()
    def start(*args, **kwargs):
        (destination/'replay').mkdir()
        (destination/'replay/execution.json').write_text(json.dumps({'renders': 17}))
        return process
    monkeypatch.setattr(recovery.subprocess, 'Popen', start)
    report = recovery.run('test-pin')
    assert report['status'] == 'blocked'
    assert report['ledger']['prior_renders'] == 954
    assert report['ledger']['cumulative_renders'] == 971
    assert report['ledger']['cumulative_seconds'] > 1165.9
    assert (destination/'replay/execution.json').exists()
    assert process.killed == (failure != 'exit')
    with pytest.raises(FileExistsError):
        recovery.run('test-pin')


def test_original_budget_inspection_is_read_only(monkeypatch):
    from scripts import letter_context_recovery_evidence as evidence
    monkeypatch.setattr(recovery.physical, 'execute_raw', lambda *args: pytest.fail('Physical execution'))
    monkeypatch.setattr(recovery.reader, 'paint', lambda *args: pytest.fail('Raster render'))
    contract = recovery.physical.load_contract(recovery.CONTRACT_SHA256)
    evidence.verify_original_budgets(contract, recovery.verify_original())
