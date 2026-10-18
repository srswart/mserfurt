import copy
import hashlib
from types import SimpleNamespace

import pytest

from scripts import nu_merge_readiness as readiness


def records():
    saved = {'code_sha256': {'scribesim/cli.py': 'old-cli', 'scribesim/pathguide/io.py': 'old-io',
                             'critical.py': 'critical', 'candidate.json': 'candidate'},
             'criteria': {'radius': .1125}, 'authority': 'frozen'}
    delta = {'removed': {}, 'changed': {
        'scribesim/cli.py': {'frozen': 'old-cli', 'current': 'new-cli'},
        'scribesim/pathguide/io.py': {'frozen': 'old-io', 'current': 'new-io'}},
        'added': {f'scribesim/added-{index}.py': str(index) for index in range(22)}}
    current = copy.deepcopy(saved)
    current['code_sha256'].update({'scribesim/cli.py': 'new-cli', 'scribesim/pathguide/io.py': 'new-io', **delta['added']})
    return saved, current, delta


def test_exact_reviewed_merge_is_separate_from_unchanged_history():
    saved, current, delta = records()
    original = copy.deepcopy(saved)
    assert readiness.check_current_freeze(saved, current, delta) == current['code_sha256']
    assert saved == original


@pytest.mark.parametrize('mutation', ['critical', 'candidate', 'criteria', 'authority', 'added', 'deleted', 'reviewed_file'])
def test_unreviewed_dependency_or_evidence_change_fails(mutation):
    saved, current, delta = records()
    if mutation == 'critical':
        current['code_sha256']['critical.py'] = 'changed'
    elif mutation == 'candidate':
        current['code_sha256']['candidate.json'] = 'changed'
    elif mutation == 'criteria':
        current['criteria']['radius'] = .1
    elif mutation == 'authority':
        current['authority'] = 'different'
    elif mutation == 'added':
        current['code_sha256']['scribesim/another.py'] = 'new'
    elif mutation == 'deleted':
        del current['code_sha256']['critical.py']
    else:
        current['code_sha256']['scribesim/cli.py'] = 'future-cli'
    with pytest.raises(ValueError):
        readiness.check_current_freeze(saved, current, delta)


def test_substituted_historical_pin_fails():
    saved, current, delta = records()
    delta['changed']['scribesim/cli.py']['frozen'] = 'substituted'
    with pytest.raises(ValueError, match='Historical source pin'):
        readiness.check_current_freeze(saved, current, delta)


def test_recovery_uses_current_only_if_exact(tmp_path):
    location = tmp_path/'source.py'
    location.write_bytes(b'original bytes')
    checksum = hashlib.sha256(location.read_bytes()).hexdigest()
    payload, origin = readiness.recovered_bytes('source.py', checksum, tmp_path)
    assert payload == b'original bytes' and origin == 'matching-current-bytes'


def test_recovered_git_bytes_still_require_old_pin(tmp_path, monkeypatch):
    monkeypatch.setattr(readiness.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=b'wrong bytes'))
    with pytest.raises(ValueError, match='pin mismatch'):
        readiness.recovered_bytes('source.py', hashlib.sha256(b'correct').hexdigest(), tmp_path)
    with pytest.raises(ValueError, match='Unsafe'):
        readiness.recovered_bytes('../escape.py', 'unused', tmp_path)


@pytest.mark.parametrize('event,arguments', [('open', ('file', 'w', 0)), ('open', ('file', None, 1)),
                                          ('os.remove', ('file', -1)), ('socket.connect', ()), ('subprocess.Popen', ())])
def test_worker_cannot_modify_evidence_or_execute(event, arguments):
    with pytest.raises(RuntimeError):
        readiness.read_only_audit(event, arguments)
    readiness.read_only_audit('open', ('file', 'r', 0))


def test_neural_cli_cannot_enter_nominal_import_scope():
    forbidden = {'scribesim.cli', 'scribesim.scribehand'}
    readiness.check_imports(forbidden, ['scribesim.evofit.stroke_gestures'])
    with pytest.raises(ValueError):
        readiness.check_imports(forbidden, ['scribesim.cli'])


@pytest.mark.parametrize('historical,runtime', [('fail', 'pass'), ('pass', 'fail')])
def test_one_verification_claim_cannot_replace_the_other(monkeypatch, historical, runtime):
    monkeypatch.setattr(readiness, 'digest', lambda path: 'pin')
    monkeypatch.setattr(readiness, 'verify_authority', lambda: {})
    monkeypatch.setattr(readiness, 'read', lambda path: {
        'status': 'pass', 'historical': {'historical_recursive_verifier': historical},
        'runtime': {'current_exact_inventory_gate': runtime}})
    with pytest.raises(ValueError, match='Both verification claims'):
        readiness.verify_receipt('pin')


def test_wrong_receipt_pin_blocks_use(monkeypatch):
    monkeypatch.setattr(readiness, 'digest', lambda path: 'actual')
    with pytest.raises(ValueError, match='External readiness'):
        readiness.verify_receipt('wrong')


def test_failed_preparation_preserved_without_overwrite(monkeypatch, tmp_path):
    monkeypatch.setattr(readiness, 'OUTPUT', tmp_path/'preparation')
    def stopped():
        raise ValueError('Synthetic source mismatch')
    monkeypatch.setattr(readiness, 'verify_authority', stopped)
    result = readiness.prepare()
    assert result['status'] == 'stopped' and result['new_candidates'] == 0
    assert (readiness.OUTPUT/'report.json').exists()
    with pytest.raises(FileExistsError):
        readiness.prepare()


def test_real_canonical_fingerprints_use_standalone_compiler_not_pair_only_wrapper():
    fingerprints = readiness.canonical_fingerprints()
    assert set(fingerprints) == {'n', 'u', 'nu'}
    assert len(set(fingerprints.values())) == 3
    assert all(len(value) == 64 for value in fingerprints.values())
