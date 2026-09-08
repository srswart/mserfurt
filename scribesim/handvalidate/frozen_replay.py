"""Immutable bounded first/replay receipts for opt-in synthetic evaluations."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from scribesim.handvalidate import foundation_gestures as foundation
from scribesim.handvalidate.specimen import ROOT, digest, write_json


def worker(module, directory, seed, maximum, seconds):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    budget = foundation.JournalBudget(directory, maximum, seconds)
    record = {'seed': seed, 'status': 'blocked'}
    try:
        if seed not in module.SPEC['seeds']:
            raise ValueError('Unfrozen seed')
        source = module.load_inputs()
        frozen = json.loads((directory.parents[1] / 'freeze.json').read_text())
        if frozen != {'spec': module.SPEC, 'code_sha256': module.identities(), 'source': source}:
            raise ValueError('Changed pre-render source or specification')
        record.update(module.evaluate(source, budget, directory))
        if frozen['code_sha256'] != module.identities():
            raise ValueError('Code changed during execution')
        record.update(status='complete', passed=module.passed(record))
        budget.check()
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        record['reason'] = str(error)
    record['renders'] = budget.used
    write_json(directory / 'report.json', record)
    budget.receipt()
    return record


def build(module):
    output = module.BASE / 'run-001'
    if list(module.BASE.glob('run-*')):
        raise ValueError('One immutable attempt only; no overwrite or automatic retries')
    source = module.load_inputs()
    write_json(output / 'freeze.json', {'spec': module.SPEC, 'code_sha256': module.identities(), 'source': source})
    report = {'stage': module.SPEC['stage'], 'status': 'blocked', 'seeds': [], 'renders': 0,
              'evaluation_complete': False, 'S2_accepted': False, 'real_accepted': False,
              'context_training_allowed': False, 'optimization_evaluations': 0}
    ledger = []
    try:
        for seed in module.SPEC['seeds']:
            started, used = time.monotonic(), 0
            for label, hashseed in [('first', '7'), ('replay', '839')]:
                remaining = 1800 - (time.monotonic() - started)
                if remaining <= 0 or used >= 5000:
                    raise RuntimeError('Combined seed budget exhausted')
                directory = output / f'seed-{seed}/{label}'
                try:
                    process = subprocess.run([sys.executable, '-m', module.__name__, '--worker', str(directory),
                        '--seed', str(seed), '--maximum', str(5000 - used), '--seconds', str(remaining)],
                        cwd=ROOT, env={**os.environ, 'PYTHONHASHSEED': hashseed}, capture_output=True, text=True, timeout=remaining)
                finally:
                    receipt = directory / 'execution.json'
                    if receipt.exists():
                        count = json.loads(receipt.read_text())['renders']
                        used += count
                        report['renders'] += count
                        ledger.append({'seed': seed, 'process': label, 'renders': count, 'cumulative_renders': used,
                                       'cumulative_seconds': time.monotonic() - started})
                        write_json(output / 'execution.json', {'ledger': ledger})
                if process.returncode or not receipt.exists():
                    raise ValueError('Worker failed: ' + process.stdout[-1000:] + process.stderr[-1000:])
                record = json.loads((directory / 'report.json').read_text())
                if record['status'] != 'complete':
                    raise ValueError(record.get('reason', 'Incomplete worker'))
            root = output / f'seed-{seed}'
            if (foundation.primitives.manifest(root / 'first') != foundation.primitives.manifest(root / 'replay')
                    or used > 5000 or time.monotonic() - started > 1800):
                raise ValueError('Replay or cumulative budget failure')
            report['seeds'].append({'seed': seed, 'replay_match': True, 'passed': module.passed(record)})
        report['evaluation_complete'] = True
        report['status'] = 'pass' if all(row['passed'] for row in report['seeds']) else 'fail'
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
    report['artifacts'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
    write_json(output / 'report.json', report)
    return report


def inspect(module, directory, expected_report_sha256):
    directory = Path(directory).resolve()
    try:
        report = json.loads((directory / 'report.json').read_text())
        frozen = json.loads((directory / 'freeze.json').read_text())
        if not expected_report_sha256 or digest(directory / 'report.json') != expected_report_sha256:
            raise ValueError('Consumer-pinned report hash required')
        source = module.load_inputs()
        if (frozen != {'spec': module.SPEC, 'code_sha256': module.identities(), 'source': source}
                or report['stage'] != module.SPEC['stage'] or report['evaluation_complete'] is not True
                or report['optimization_evaluations'] != 0
                or any(report[key] is not False for key in ('S2_accepted', 'real_accepted', 'context_training_allowed'))):
            raise ValueError('Stale, incomplete or overstated evidence')
        inventory = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()} - {'report.json'}
        if inventory != set(report['artifacts']):
            raise ValueError('Incomplete artifact inventory')
        foundation.primitives.verify_artifacts(directory, report['artifacts'])
        ledger = json.loads((directory / 'execution.json').read_text())['ledger']
        if [(row['seed'], row['process']) for row in ledger] != [(seed, label) for seed in module.SPEC['seeds'] for label in ('first', 'replay')]:
            raise ValueError('Incomplete seed ledger')
        summaries, total = [], 0
        for seed in module.SPEC['seeds']:
            root = directory / f'seed-{seed}'
            if foundation.primitives.manifest(root / 'first') != foundation.primitives.manifest(root / 'replay'):
                raise ValueError('Replay differs')
            used, elapsed = 0, 0
            for entry in [row for row in ledger if row['seed'] == seed]:
                worker_dir = root / entry['process']
                record = json.loads((worker_dir / 'report.json').read_text())
                receipt = json.loads((worker_dir / 'execution.json').read_text())
                used += receipt['renders']
                if (record['seed'] != seed or record['status'] != 'complete' or record['renders'] != receipt['renders']
                        or entry['renders'] != receipt['renders'] or entry['cumulative_renders'] != used or used > 5000
                        or not elapsed <= entry['cumulative_seconds'] <= 1800):
                    raise ValueError('Worker or cumulative budget mismatch')
                elapsed = entry['cumulative_seconds']
                module.verify_record(source, record, worker_dir)
                if record['passed'] is not module.passed(record):
                    raise ValueError('Worker decision differs from measured evidence')
            total += used
            summaries.append({'seed': seed, 'replay_match': True, 'passed': module.passed(record)})
        status = 'pass' if all(row['passed'] for row in summaries) else 'fail'
        if report['seeds'] != summaries or report['renders'] != total or report['status'] != status:
            raise ValueError('Root decision differs')
        return {'report_sha256': expected_report_sha256, 'status': status, 'renders': total,
                'artifacts_verified': len(inventory), 'S2_accepted': False, 'real_accepted': False}
    except (OSError, KeyError, TypeError, IndexError) as error:
        raise ValueError('Incomplete frozen evidence') from error
