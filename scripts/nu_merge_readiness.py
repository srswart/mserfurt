"""Verify historical bytes in isolation and separately gate merged nominal use."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1'
STOP = BASE/'batch-001/report.json'
STOP_PIN = '648a8d28cd411426af260fa0cc451eaf2876cf39127bbacf8610b5f8676b0156'
CONTRACT = ROOT/'docs/tech-direction/TD-018-merge-aware-nominal-readiness.md'
CONTRACT_PIN = '48c027b47aa249b4622bcf75841713f61c34c6f02b9aab62dba0c5c603081e85'
HISTORICAL_COMMIT = '374445028025f517b14919d00d12812ec6128c42'
APPROVAL = BASE/'continuation-approval.json'
OUTPUT = BASE/'readiness-001'
VERSION = 'nu-merge-aware-readiness-v1'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def approval_record():
    return {'version': VERSION,
            'owner_quote': "Let's go ahead and repair merge-aware source verification without weakening historical evidence pins, then resume the unchanged two-candidate study.",
            'contract_sha256': CONTRACT_PIN, 'stopped_report_sha256': STOP_PIN,
            'original_approval_sha256': 'f7cde5ac9bbe3170d527ce6227ef412d4d1fcb1aa7cab0485b90cee83bf964f2',
            'historical_source_commit': HISTORICAL_COMMIT,
            'historical_pins_unchanged': True, 'current_runtime_gate_required': True,
            'continuation_directory': 'continuation-001', 'remaining_candidates': 2,
            'remaining_construction_check_seconds': 300, 'remaining_render_seconds': 300,
            'max_evidence_bytes': 25*1024**2, 'minimum_free_bytes': 5*1024**3,
            'automatic_retries': 0, 'fitting': False, 'physical_runs': 0,
            'mu': False, 'nib_rotation': False, 'geometry_or_limits_changed': False}


def verify_authority():
    if read(APPROVAL) != approval_record() or digest(CONTRACT) != CONTRACT_PIN or digest(STOP) != STOP_PIN:
        raise ValueError('Pinned continuation authority or stopped record changed')
    from scripts import nu_mutual_construction as program
    stopped = read(STOP)
    if (digest(BASE/'approval.json') != approval_record()['original_approval_sha256']
            or read(BASE/'approval.json') != program.approval_record()
            or digest(program.BRIEF) != program.BRIEF_PIN
            or digest(program.source.CANDIDATE) != program.CANONICAL_PIN
            or digest(Path(program.__file__)) != stopped['code_sha256']
            or digest(ROOT/'tests/test_nu_mutual_construction.py') != stopped['tests_sha256']
            or stopped['new_candidates'] != 0 or stopped['renders'] != 0):
        raise ValueError('Original study authority, geometry rules, tests or budget changed')
    for name, expected in stopped['direct_saved_pins_verified'].items():
        if digest(BASE.parent/name) != expected:
            raise ValueError('Historical candidate/report changed: '+name)
    return stopped


def historical_freeze(stopped):
    location = ROOT/stopped['source_inventory']['frozen_record_path']
    if digest(location) != stopped['source_inventory']['frozen_record_sha256']:
        raise ValueError('Historical freeze bytes changed')
    return read(location)


def check_current_freeze(saved, current, delta):
    expected = dict(saved['code_sha256'])
    if delta['removed']:
        raise ValueError('No removed source identities authorized')
    if set(delta['changed']) != {'scribesim/cli.py', 'scribesim/pathguide/io.py'} or len(delta['added']) != 22:
        raise ValueError('Unexpected merge review scope')
    for name, hashes in delta['changed'].items():
        if expected.get(name) != hashes['frozen']:
            raise ValueError('Historical source pin substituted')
        expected[name] = hashes['current']
    for name, checksum in delta['added'].items():
        if name in expected:
            raise ValueError('Added source replaces old identity')
        expected[name] = checksum
    if current != {**saved, 'code_sha256': expected}:
        raise ValueError('Unreviewed current source, candidate, criteria or authority change')
    return expected


def recovered_bytes(name, expected, root=ROOT):
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe historical source path')
    present = root/relative
    if present.is_file() and digest(present) == expected:
        return present.read_bytes(), 'matching-current-bytes'
    result = subprocess.run(['git', 'show', HISTORICAL_COMMIT+':'+name], cwd=root,
                            capture_output=True, check=False)
    if result.returncode or hashlib.sha256(result.stdout).hexdigest() != expected:
        raise ValueError('Historical source unavailable or pin mismatch: '+name)
    return result.stdout, 'hash-verified-pre-merge-object'


def dependencies():
    from scripts import letter_context_variant_evidence as preflight
    paths = list((ROOT/'scripts').rglob('*.py'))+list((ROOT/'tests').rglob('*.py'))
    return {**preflight.identities(), **{str(path.relative_to(ROOT)): digest(path) for path in paths}}


def module_name(name):
    return name.removesuffix('.py').replace('/', '.').removesuffix('.__init__')


def forbidden_modules(stopped):
    return {'scribesim.cli', *[module_name(name) for name in stopped['source_inventory']['added']]}


def check_imports(forbidden, loaded=None):
    loaded = sys.modules if loaded is None else loaded
    overlap = set(loaded)&set(forbidden)
    if overlap:
        raise ValueError('Excluded upstream module entered nominal execution: '+', '.join(sorted(overlap)))


def read_only_audit(event, arguments):
    if event == 'open':
        _, mode, flags = arguments
        if (isinstance(mode, str) and any(character in mode for character in 'wax+')) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            raise RuntimeError('Historical/readiness worker is read-only')
    if event in ('os.remove', 'os.rename', 'os.rmdir', 'os.mkdir', 'os.symlink', 'os.link',
                 'os.chmod', 'os.truncate', 'socket.connect', 'socket.bind', 'subprocess.Popen', 'os.system'):
        raise RuntimeError('Worker writes, external execution and network are forbidden')


def canonical_fingerprints():
    from scripts import nu_mutual_construction as program
    from scribesim.evofit.stroke_gestures import compile_gestures
    candidate = program.source.read_json(program.source.CANDIDATE)
    if digest(program.source.CANDIDATE) != program.CANONICAL_PIN:
        raise ValueError('Canonical source changed')
    compiled = {text: compile_gestures(text, candidate) for text in ('n', 'u', 'nu')}
    if compiled['nu'] != program.canonical(candidate, 'nu'):
        raise ValueError('Direct pair wrapper differs from canonical compiler')
    return {text: program.actions.object_digest(value) for text, value in compiled.items()}


def worker(historical):
    sys.addaudithook(read_only_audit)
    from scripts import nu_mutual_construction as program
    if historical:
        with program.source.evidence.read_only_guard():
            program.history.verify()
        result = {'historical_recursive_verifier': 'pass', 'historical_pins_rewritten': False}
    else:
        stopped = verify_authority()
        check_imports(forbidden_modules(stopped))
        from scripts import letter_context_variant_evidence as preflight
        check_current_freeze(historical_freeze(stopped), preflight.freeze_record(), stopped['source_inventory'])
        check_imports(forbidden_modules(stopped))
        result = {'current_exact_inventory_gate': 'pass', 'excluded_modules_imported': []}
    result['canonical_compiled_sha256'] = canonical_fingerprints()
    if not historical:
        check_imports(forbidden_modules(read(STOP)))
    result['loaded_scribesim_sources'] = {
        str(Path(module.__file__).relative_to(ROOT)): digest(Path(module.__file__))
        for name, module in list(sys.modules.items())
        if name.startswith('scribesim') and getattr(module, '__file__', None)
        and Path(module.__file__).is_relative_to(ROOT) and Path(module.__file__).suffix == '.py'}
    result['python'] = sys.version
    print(json.dumps(result, sort_keys=True))


def invoke_worker(directory, historical):
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    environment.pop('PYTHONPATH', None)
    result = subprocess.run([sys.executable, '-B', '-m', 'scripts.nu_merge_readiness',
                             '--historical-worker' if historical else '--runtime-worker'],
                            cwd=directory, env=environment, capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise ValueError(('Historical' if historical else 'Runtime')+' verifier failed:\n'+result.stderr[-12000:])
    return json.loads(result.stdout)


def historical_probe(saved):
    provenance = {}
    with tempfile.TemporaryDirectory(prefix='nu-historical-source-') as directory:
        capsule = Path(directory)
        for name in ('scripts', 'tests'):
            shutil.copytree(ROOT/name, capsule/name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in ('shared', 'reference', 'docs'):
            (capsule/name).symlink_to(ROOT/name, target_is_directory=True)
        for name, checksum in saved['code_sha256'].items():
            if not name.startswith('scribesim/'):
                if digest(capsule/name) != checksum:
                    raise ValueError('Historical non-core dependency changed: '+name)
                continue
            payload, origin = recovered_bytes(name, checksum)
            destination = capsule/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
            provenance[name] = {'sha256': checksum, 'origin': origin}
        actual = {str(path.relative_to(capsule)): digest(path) for path in (capsule/'scribesim').rglob('*.py')}
        expected = {name: checksum for name, checksum in saved['code_sha256'].items() if name.startswith('scribesim/')}
        if actual != expected:
            raise ValueError('Historical capsule inventory differs')
        result = invoke_worker(capsule, True)
    return {**result, 'source_capsule': provenance, 'temporary_source_only': True,
            'existing_evidence_read_in_place': True, 'capsule_removed': True}


def save_new(path, value):
    payload = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    if len(payload) > 1024**2:
        raise ValueError('Readiness receipt exceeds 1 MiB')
    with path.open('xb') as stream:
        stream.write(payload)


def prepare():
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    report = {'version': VERSION, 'status': 'stopped', 'new_candidates': 0, 'fitting': False,
              'physical_runs': 0, 'images': 0, 'approval': approval_record()}
    try:
        stopped = verify_authority()
        saved = historical_freeze(stopped)
        from scripts import letter_context_variant_evidence as preflight
        expected = check_current_freeze(saved, preflight.freeze_record(), stopped['source_inventory'])
        old_io, _ = recovered_bytes('scribesim/pathguide/io.py', saved['code_sha256']['scribesim/pathguide/io.py'])
        if ast.dump(ast.parse(old_io)) != ast.dump(ast.parse((ROOT/'scribesim/pathguide/io.py').read_bytes())):
            raise ValueError('Pathguide IO change is not AST-equivalent')
        before = dependencies()
        report.update(dependencies=before, current_source_inventory=expected, pathguide_io_ast_equal=True)
        report['historical'] = historical_probe(saved)
        report['runtime'] = invoke_worker(ROOT, False)
        if report['historical']['canonical_compiled_sha256'] != report['runtime']['canonical_compiled_sha256']:
            raise ValueError('Canonical compiled behavior differs across runtimes')
        if before != dependencies():
            raise ValueError('Source changed during readiness verification')
        verify_authority()
        report['status'] = 'pass'
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        report['error'] = str(error)
    report['seconds'] = time.monotonic()-started
    save_new(OUTPUT/'report.json', report)
    return report


def verify_receipt(expected_sha256):
    if digest(OUTPUT/'report.json') != expected_sha256:
        raise ValueError('External readiness receipt pin required')
    receipt = read(OUTPUT/'report.json')
    stopped = verify_authority()
    if (receipt['status'] != 'pass' or receipt['historical']['historical_recursive_verifier'] != 'pass'
            or receipt['runtime']['current_exact_inventory_gate'] != 'pass'
            or receipt['historical']['canonical_compiled_sha256'] != receipt['runtime']['canonical_compiled_sha256']
            or receipt['dependencies'] != dependencies()):
        raise ValueError('Both verification claims and unchanged dependencies required')
    check_imports(forbidden_modules(stopped))
    from scripts import letter_context_variant_evidence as preflight
    check_current_freeze(historical_freeze(stopped), preflight.freeze_record(), stopped['source_inventory'])
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument('--prepare', action='store_true')
    options.add_argument('--historical-worker', action='store_true')
    options.add_argument('--runtime-worker', action='store_true')
    arguments = parser.parse_args()
    if arguments.prepare:
        prepared = prepare()
        print(json.dumps({'status': prepared['status'], 'seconds': prepared['seconds'], 'error': prepared.get('error')}))
    else:
        worker(arguments.historical_worker)
