"""One explicitly authorized upright replay, charging the preserved failed attempt."""

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

from scribesim.handvalidate import upright_letters as evaluation, upright_evidence as reader
from scribesim.handvalidate.specimen import ROOT, digest, write_json


BASE = evaluation.BASE/'continuation-001'
AUTH_PATH = BASE/'authorization.json'
AUTH = json.loads(AUTH_PATH.read_text())
SPEC = {**evaluation.SPEC, 'continuation': AUTH}


def identities():
    return {**evaluation.identities(), str(AUTH_PATH.relative_to(ROOT)): digest(AUTH_PATH)}


def load_inputs():
    prior = evaluation.BASE/'run-001'
    if digest(evaluation.SPEC_PATH) != AUTH['original_spec_sha256'] or digest(prior/'report.json') != AUTH['prior_report_sha256']:
        raise ValueError('Changed frozen protocol or prior failed report')
    report = json.loads((prior/'report.json').read_text())
    inventory = {str(path.relative_to(prior)) for path in prior.rglob('*') if path.is_file()}-{'report.json'}
    if inventory != set(report['artifacts']) or report['evaluation_complete'] is not False or report['renders'] != 2:
        raise ValueError('Changed failed attempt inventory or debit')
    evaluation.protocol.foundation.primitives.verify_artifacts(prior, report['artifacts'])
    frozen = json.loads((prior/'freeze.json').read_text())
    source = evaluation.load_inputs()
    if frozen['spec'] != evaluation.SPEC or frozen['source'] != source:
        raise ValueError('Candidate, targets or original scope changed')
    for name, checksum in frozen['code_sha256'].items():
        expected = AUTH['allowed_existing_code_changes'].get(name, checksum)
        if digest(ROOT/name) != expected:
            raise ValueError('Existing code drift outside authorized scalar repair: '+name)
    ledger = json.loads((prior/'execution.json').read_text())['ledger']
    if len(ledger) != 1 or ledger[0]['seed'] != 7 or ledger[0]['process'] != 'first' or ledger[0]['renders'] != 2:
        raise ValueError('Unrecognized prior attempt ledger')
    debits = {str(seed): {'renders': 0, 'seconds': 0.0} for seed in SPEC['seeds']}
    debits['7'] = {'renders': ledger[0]['cumulative_renders'], 'seconds': ledger[0]['cumulative_seconds']}
    return {**source, 'prior_attempt': {'report_sha256': AUTH['prior_report_sha256'], 'debits': debits}}


def remaining(debit, used, elapsed):
    renders = SPEC['budget']['renders_per_seed_including_replay']-debit['renders']-used
    seconds = SPEC['budget']['seconds_per_seed_including_replay']-debit['seconds']-elapsed
    if type(renders) is not int or renders <= 0 or not math.isfinite(seconds) or seconds <= 0:
        raise RuntimeError('Combined continuation budget exhausted')
    return renders, seconds


def evaluate(source, budget, directory):
    return evaluation.evaluate(source, budget, directory)


def passed(record):
    return reader.decision(record)['numeric_pass']


def build():
    output = BASE/'run-001'
    if list(BASE.glob('run-*')):
        raise ValueError('One immutable continuation only; no overwrite or automatic retries')
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
                    process = subprocess.run([sys.executable, '-m', 'scribesim.handvalidate.upright_continuation',
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
                            'cumulative_seconds': elapsed, 'combined_renders': used+debit['renders'],
                            'combined_seconds': elapsed+debit['seconds']})
                        write_json(output/'execution.json', {'ledger': ledger})
                if process.returncode or not receipt.exists():
                    raise ValueError('Worker failed: '+process.stdout[-1000:]+process.stderr[-1000:])
                record = json.loads((directory/'report.json').read_text())
                if record['status'] != 'complete':
                    raise ValueError(record.get('reason', 'Incomplete continuation worker'))
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


def check_combined(ledger, debits):
    if [(row['seed'], row['process']) for row in ledger] != [(seed, label) for seed in SPEC['seeds'] for label in ('first', 'replay')]:
        raise ValueError('Incomplete combined ledger')
    total = 0
    for seed in SPEC['seeds']:
        debit, used, previous = debits[str(seed)], 0, 0.0
        for row in [entry for entry in ledger if entry['seed'] == seed]:
            used += row['renders']
            seconds = row['cumulative_seconds']+debit['seconds']
            if (row['combined_renders'] != used+debit['renders'] or row['cumulative_renders'] != used
                    or row['combined_seconds'] != seconds or used+debit['renders'] > 5000
                    or not math.isfinite(seconds) or not previous <= row['cumulative_seconds'] or seconds > 1800):
                raise ValueError('Changed combined budget accounting')
            previous = row['cumulative_seconds']
        total += used+debit['renders']
    return total


def inspect_run(directory, expected_report_sha256):
    directory = Path(directory)
    if not expected_report_sha256 or digest(directory/'report.json') != expected_report_sha256:
        raise ValueError('Consumer-pinned report hash required')
    adapter = SimpleNamespace(SPEC=SPEC, identities=identities, load_inputs=load_inputs,
                              verify_record=reader.verify_record, passed=passed)
    result = evaluation.protocol.inspect(adapter, directory, expected_report_sha256)
    source = load_inputs()
    report = json.loads((directory/'report.json').read_text())
    ledger = json.loads((directory/'execution.json').read_text())['ledger']
    combined = check_combined(ledger, source['prior_attempt']['debits'])
    if report['prior_attempt'] != source['prior_attempt'] or report['combined_renders'] != combined:
        raise ValueError('Changed prior debit or combined total')
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
