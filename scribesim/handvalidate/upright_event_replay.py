"""Authorized boundary/event repair replay; old evidence never becomes new admission."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

from scribesim.handvalidate import upright_letters as evaluation, upright_evidence as reader
from scribesim.handvalidate.upright_continuation import remaining, check_combined
from scribesim.handvalidate.specimen import ROOT, digest, write_json


BASE = evaluation.BASE/'continuation-002'
AUTH_PATH = BASE/'authorization.json'
AUTH = json.loads(AUTH_PATH.read_text())
SPEC = {**evaluation.SPEC, 'continuation': AUTH}


def identities():
    paths = [AUTH_PATH, evaluation.BASE/'continuation-001/authorization.json']
    return {**evaluation.identities(), **{str(path.relative_to(ROOT)): digest(path) for path in paths}}


def verify_existing_code(recorded):
    for name, checksum in recorded.items():
        path = (ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != AUTH['allowed_existing_code_changes'].get(name, checksum):
            raise ValueError('Code change outside authorized repair: '+name)


def load_inputs():
    if digest(evaluation.SPEC_PATH) != AUTH['original_spec_sha256']:
        raise ValueError('Original targets, fixtures or gates changed')
    debits = {str(seed): {'renders': 0, 'seconds': 0.0} for seed in SPEC['seeds']}
    source = None
    for relative, checksum in AUTH['prior_reports'].items():
        directory = evaluation.BASE/relative
        if digest(directory/'report.json') != checksum:
            raise ValueError('Changed prior report')
        report = json.loads((directory/'report.json').read_text())
        inventory = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()}-{'report.json'}
        if inventory != set(report['artifacts']) or report['status'] != 'blocked' or report['evaluation_complete'] is not False:
            raise ValueError('Changed prior attempt inventory or status')
        evaluation.protocol.foundation.primitives.verify_artifacts(directory, report['artifacts'])
        frozen = json.loads((directory/'freeze.json').read_text())
        if {key: value for key, value in frozen['spec'].items() if key != 'continuation'} != evaluation.SPEC:
            raise ValueError('Prior protocol differs')
        verify_existing_code(frozen['code_sha256'])
        payload = {key: frozen['source'][key] for key in ('candidate', 'prior', 'nominal_review_sha256')}
        if source is not None and source != payload:
            raise ValueError('Prior attempts used different frozen inputs')
        source = payload
        ledger = json.loads((directory/'execution.json').read_text())['ledger']
        if sum(row['renders'] for row in ledger) != report['renders']:
            raise ValueError('Prior render total mismatch')
        for seed in SPEC['seeds']:
            entries = [row for row in ledger if row['seed'] == seed]
            if not entries:
                continue
            if entries[-1]['cumulative_renders'] != sum(row['renders'] for row in entries):
                raise ValueError('Prior cumulative debit mismatch')
            for entry in entries:
                receipt = json.loads((directory/f"seed-{seed}/{entry['process']}/execution.json").read_text())
                if receipt['renders'] != entry['renders'] or receipt['elapsed_seconds'] > entry['cumulative_seconds']:
                    raise ValueError('Prior execution receipt mismatch')
            debits[str(seed)]['renders'] += entries[-1]['cumulative_renders']
            debits[str(seed)]['seconds'] += entries[-1]['cumulative_seconds']
    for path, key in [(evaluation.SOURCE/'candidate.json', 'candidate_file_sha256'),
                      (evaluation.SOURCE/'report.json', 'source_report_sha256'),
                      (evaluation.SOURCE/'owner-review.json', 'source_owner_review_sha256'), (evaluation.PRIOR, 'prior_file_sha256')]:
        if digest(path) != evaluation.SPEC[key]:
            raise ValueError('Changed reviewed input: '+path.name)
    if (source['candidate'] != json.loads((evaluation.SOURCE/'candidate.json').read_text())
            or source['prior'] != json.loads(evaluation.PRIOR.read_text())):
        raise ValueError('Candidate bytes differ from frozen payload')
    nominal = json.loads((evaluation.SOURCE/'report.json').read_text())
    inventory = {path.name for path in evaluation.SOURCE.iterdir() if path.is_file()}-{'report.json', 'owner-review.json'}
    if inventory != set(nominal['artifacts']):
        raise ValueError('Incomplete nominal source inventory')
    evaluation.protocol.foundation.primitives.verify_artifacts(evaluation.SOURCE, nominal['artifacts'])
    verify_existing_code(nominal['source_identities'])
    review = json.loads((evaluation.SOURCE/'owner-review.json').read_text())
    if (review['candidate_sha256'] != evaluation.SPEC['candidate_file_sha256'] or review['status'] != 'approved_nominal_preview'
            or any(review['letters'][letter]['verdict'] != 'keep' for letter in 'num')):
        raise ValueError('Candidate-bound nominal review required')
    evaluation.require_candidate(source['candidate'])
    return {**source, 'prior_attempt': {'reports': AUTH['prior_reports'], 'debits': debits}}


def evaluate(source, budget, directory):
    return evaluation.evaluate(source, budget, directory)


def passed(record):
    return reader.decision(record)['numeric_pass']


def build():
    output = BASE/'run-001'
    if list(BASE.glob('run-*')):
        raise ValueError('One immutable event-repair attempt only; no automatic retries')
    source = load_inputs()
    write_json(output/'freeze.json', {'spec': SPEC, 'code_sha256': identities(), 'source': source})
    debits = source['prior_attempt']['debits']
    report = {'stage': SPEC['stage'], 'status': 'blocked', 'seeds': [], 'renders': 0,
        'evaluation_complete': False, 'S2_accepted': False, 'real_accepted': False,
        'context_training_allowed': False, 'optimization_evaluations': 0, 'prior_attempt': source['prior_attempt']}
    ledger = []
    try:
        for seed in SPEC['seeds']:
            started, used = time.monotonic(), 0
            debit = debits[str(seed)]
            for label, hashseed in [('first', '7'), ('replay', '839')]:
                maximum, seconds = remaining(debit, used, time.monotonic()-started)
                directory = output/f'seed-{seed}/{label}'
                try:
                    process = subprocess.run([sys.executable, '-m', 'scribesim.handvalidate.upright_event_replay',
                        '--worker', str(directory), '--seed', str(seed), '--maximum', str(maximum), '--seconds', str(seconds)],
                        cwd=ROOT, env={**os.environ, 'PYTHONHASHSEED': hashseed}, capture_output=True, text=True, timeout=seconds)
                finally:
                    receipt = directory/'execution.json'
                    if receipt.exists():
                        count = json.loads(receipt.read_text())['renders']
                        used += count
                        report['renders'] += count
                        elapsed = time.monotonic()-started
                        ledger.append({'seed': seed, 'process': label, 'renders': count, 'cumulative_renders': used,
                            'cumulative_seconds': elapsed, 'combined_renders': used+debit['renders'], 'combined_seconds': elapsed+debit['seconds']})
                        write_json(output/'execution.json', {'ledger': ledger})
                if process.returncode or not receipt.exists():
                    raise ValueError('Worker failed: '+process.stdout[-1000:]+process.stderr[-1000:])
                record = json.loads((directory/'report.json').read_text())
                if record['status'] != 'complete':
                    raise ValueError(record.get('reason', 'Incomplete event-repair worker'))
            root = output/f'seed-{seed}'
            if (evaluation.protocol.foundation.primitives.manifest(root/'first') != evaluation.protocol.foundation.primitives.manifest(root/'replay')
                    or used+debit['renders'] > 5000 or time.monotonic()-started+debit['seconds'] > 1800):
                raise ValueError('Replay or combined budget failure')
            report['seeds'].append({'seed': seed, 'replay_match': True, 'passed': passed(record)})
        report['combined_renders'] = check_combined(ledger, debits)
        report['evaluation_complete'] = True
        report['status'] = 'pass' if all(row['passed'] for row in report['seeds']) else 'fail'
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
    report['artifacts'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
    write_json(output/'report.json', report)
    return report


def inspect_run(directory, expected_report_sha256):
    directory = Path(directory)
    if not expected_report_sha256 or digest(directory/'report.json') != expected_report_sha256:
        raise ValueError('Consumer-pinned report hash required')
    adapter = SimpleNamespace(SPEC=SPEC, identities=identities, load_inputs=load_inputs,
                              verify_record=reader.verify_record, passed=passed)
    result = evaluation.protocol.inspect(adapter, directory, expected_report_sha256)
    source = load_inputs()
    report = json.loads((directory/'report.json').read_text())
    combined = check_combined(json.loads((directory/'execution.json').read_text())['ledger'], source['prior_attempt']['debits'])
    if report['prior_attempt'] != source['prior_attempt'] or report['combined_renders'] != combined:
        raise ValueError('Changed combined debit')
    record = json.loads((directory/'seed-7/first/report.json').read_text())
    return {**result, **reader.decision(record), 'combined_renders': combined,
        'reader_sha256': digest(Path(reader.__file__)), 'continuation_reader_sha256': digest(Path(__file__)),
        'scope': SPEC['scope'], 'read_only': True, 'rerenders': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--maximum', type=int)
    parser.add_argument('--seconds', type=float)
    parser.add_argument('--inspect', type=Path)
    parser.add_argument('--report-sha256')
    args = parser.parse_args()
    if args.inspect:
        result = inspect_run(args.inspect, args.report_sha256)
    elif args.worker:
        result = evaluation.protocol.worker(sys.modules[__name__], args.worker, args.seed, args.maximum, args.seconds)
    else:
        result = build()
    print(json.dumps({key: value for key, value in result.items() if key not in {'artifacts', 'fixtures'}}, indent=2))


if __name__ == '__main__':
    main()
