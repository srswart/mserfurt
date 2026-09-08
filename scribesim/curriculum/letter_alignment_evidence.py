"""Read-only numeric adjudication of the preserved alignment type-check failure."""

import argparse
import copy
import json
import math
from pathlib import Path
from types import SimpleNamespace

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


def inspect_run(directory, *, expected_report_sha256):
    directory = Path(directory).resolve()
    adapter = SimpleNamespace(SPEC=experiment.SPEC, identities=experiment.identities,
        load_inputs=experiment.load_inputs, verify_record=experiment.verify_record,
        passed=runtime_decision)
    original = experiment.protocol.inspect(adapter, directory, expected_report_sha256)
    if original['status'] != 'fail':
        raise ValueError('This reader only adjudicates the preserved runtime type-check failure')
    decisions = []
    for seed in experiment.SPEC['seeds']:
        for label in ('first', 'replay'):
            path = directory / f'seed-{seed}/{label}/report.json'
            record = json.loads(path.read_text())
            if record['passed'] is not False or runtime_decision(record) is not False:
                raise ValueError('Original decision does not reproduce the diagnosed defect')
            decisions.append({'seed': seed, 'process': label, 'numeric_pass': numeric_decision(record)})
    return {'source_report_sha256': expected_report_sha256, 'source_status': original['status'],
        'status': 'pass' if all(row['numeric_pass'] for row in decisions) else 'fail',
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
