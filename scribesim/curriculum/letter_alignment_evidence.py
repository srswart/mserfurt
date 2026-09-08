"""Read-only numeric adjudication of the preserved alignment type-check failure."""

import argparse
import copy
import json
import math
from pathlib import Path

import numpy as np

from scribesim.curriculum import letter_alignment as experiment
from scribesim.handvalidate.specimen import digest


def numeric_decision(record):
    normalized = copy.deepcopy(record)
    try:
        for row in normalized['fixtures']:
            value = row['ratio']
            if type(value) not in (int, float, np.float64) or not math.isfinite(value):
                return False
            row['ratio'] = float(value)
        return experiment.passed(normalized)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def runtime_decision(record):
    runtime = copy.deepcopy(record)
    for row in runtime['fixtures']:
        row['ratio'] = np.float64(row['ratio'])
    return experiment.passed(runtime)


def verify_source(directory, expected_report_sha256):
    if not expected_report_sha256 or digest(directory / 'report.json') != expected_report_sha256:
        raise ValueError('Consumer-pinned report hash required')
    report = json.loads((directory / 'report.json').read_text())
    frozen = json.loads((directory / 'freeze.json').read_text())
    source = experiment.load_inputs()
    if (frozen != {'spec': experiment.SPEC, 'code_sha256': experiment.identities(), 'source': source}
            or report['stage'] != experiment.SPEC['stage'] or report['evaluation_complete'] is not True
            or report['optimization_evaluations'] != 0
            or any(report[key] is not False for key in ('S2_accepted', 'real_accepted', 'context_training_allowed'))):
        raise ValueError('Stale, incomplete or overstated evidence')
    inventory = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()} - {'report.json'}
    if inventory != set(report['artifacts']):
        raise ValueError('Incomplete artifact inventory')
    experiment.foundation.primitives.verify_artifacts(directory, report['artifacts'])
    ledger = json.loads((directory / 'execution.json').read_text())['ledger']
    if [(row['seed'], row['process']) for row in ledger] != [(seed, label) for seed in experiment.SPEC['seeds'] for label in ('first', 'replay')]:
        raise ValueError('Incomplete seed ledger')
    total = 0
    for seed in experiment.SPEC['seeds']:
        root = directory / f'seed-{seed}'
        if experiment.foundation.primitives.manifest(root / 'first') != experiment.foundation.primitives.manifest(root / 'replay'):
            raise ValueError('Replay differs')
        used, elapsed = 0, 0
        for entry in [row for row in ledger if row['seed'] == seed]:
            worker = root / entry['process']
            record = json.loads((worker / 'report.json').read_text())
            receipt = json.loads((worker / 'execution.json').read_text())
            used += receipt['renders']
            if (record['seed'] != seed or record['status'] != 'complete' or record['renders'] != receipt['renders']
                    or entry['renders'] != receipt['renders'] or entry['cumulative_renders'] != used or used > 5000
                    or not elapsed <= entry['cumulative_seconds'] <= 1800):
                raise ValueError('Worker or cumulative budget mismatch')
            elapsed = entry['cumulative_seconds']
            experiment.verify_record(source, record, worker)
        total += used
    if report['renders'] != total:
        raise ValueError('Changed root render count')
    return {**report, 'artifacts_verified': len(inventory)}


def inspect_run(directory, *, expected_report_sha256):
    directory = Path(directory).resolve()
    original = verify_source(directory, expected_report_sha256)
    decisions = []
    for seed in experiment.SPEC['seeds']:
        for label in ('first', 'replay'):
            path = directory / f'seed-{seed}/{label}/report.json'
            record = json.loads(path.read_text())
            if record['passed'] is not False or runtime_decision(record) is not False:
                raise ValueError('Original decision does not reproduce the diagnosed defect')
            decisions.append({'seed': seed, 'process': label, 'numeric_pass': numeric_decision(record)})
    summaries = [{'seed': seed, 'replay_match': True,
                  'passed': all(row['numeric_pass'] for row in decisions if row['seed'] == seed)}
                 for seed in experiment.SPEC['seeds']]
    status = 'pass' if all(row['passed'] for row in summaries) else 'fail'
    if original['status'] != status or original['seeds'] != summaries:
        raise ValueError('Root decision differs from post-serialization numeric evidence')
    return {'source_report_sha256': expected_report_sha256, 'source_status': original['status'],
        'source_worker_decisions': 'false before JSON serialization', 'status': status,
        'reason': 'Normalize finite NumPy float64 ratios to JSON scalar floats; all numerical criteria unchanged',
        'reader_sha256': digest(Path(__file__)), 'artifacts_verified': original['artifacts_verified'],
        'original_renders': original['renders'], 'additional_renders': 0, 'optimization_evaluations': 0,
        'decisions': decisions, 'S2_accepted': False, 'real_accepted': False,
        'context_training_allowed': False,
        'scope': 'Synthetic assembly numeric adjudication only; original failed receipts remain immutable. Independent rotated-gesture evaluation and appearance review are still required.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, nargs='?', default=experiment.BASE / 'run-001')
    parser.add_argument('--report-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_run(args.directory, expected_report_sha256=args.report_sha256), indent=2))


if __name__ == '__main__':
    main()
