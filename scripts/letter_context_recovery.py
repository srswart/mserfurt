"""One owner-authorized fresh seed-41 replay; never modifies the failed attempt."""

import argparse
import gc
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

import numpy as np

from scripts import letter_context_physical as physical
from scripts import letter_context_physical_evidence as reader
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = physical.BASE
ORIGINAL = BASE/'run-001'
PREPARED = BASE/'recovery-prepared-001'
OUTPUT = BASE/'recovery-001'
CONTRACT_SHA256 = 'db909d00cd3d7c26cff021e2c9ff9ad19a6ebb8ca08bfd873bd41dd13d443eb5'
FAILURE_SHA256 = 'adec239210591bf83b37abbe22543012e89ed5912fea2aea359be4e958fd086e'
GIB = 1024**3
START_FREE = 10*GIB
STOP_FREE = 5*GIB


def require_space(minimum):
    free = shutil.disk_usage(BASE).free
    if free < minimum:
        raise RuntimeError(f'Disk headroom below guard: {free} bytes free, {minimum} required')
    return free


def verify_original():
    file = BASE/'failed-run-001-manifest.json'
    if digest(file) != FAILURE_SHA256:
        raise ValueError('Changed failure manifest')
    manifest = physical.preflight.foundation.read_json(file)
    if physical.artifact_map(ORIGINAL) != manifest['artifacts']:
        raise ValueError('Changed original attempt artifacts')
    physical.load_contract(CONTRACT_SHA256)
    return manifest


def contract_record():
    contract = physical.load_contract(CONTRACT_SHA256)
    file = BASE/'failed-run-001-manifest.json'
    if digest(file) != FAILURE_SHA256:
        raise ValueError('Changed failure manifest')
    manifest = physical.preflight.foundation.read_json(file)
    entry = manifest['ledger'][-1]
    if entry['seed'] != 41 or entry['process'] != 'replay':
        raise ValueError('Wrong recovery seed')
    return {'version': 'letter-context-storage-recovery-v1',
        'owner_request': "Yes let's see if we can recover.  Does it seem we have enough free space or should I look for more ?",
        'authorization': 'Owner approves bounded recovery with disk monitoring and unchanged candidates, targets, thresholds and budgets',
        'original_contract_sha256': CONTRACT_SHA256, 'failure_manifest_sha256': FAILURE_SHA256,
        'code_sha256': {str(file.relative_to(ROOT)): digest(file) for file in
            (Path(__file__), ROOT/'scripts/letter_context_recovery_evidence.py')},
        'mode': 'fresh-full-seed-41-replay-not-in-place-resume', 'seed': 41, 'hashseed': '839',
        'cases': len(contract['cases']), 'scheduled_renders': len(physical.render_schedule(contract)),
        'prior_seconds': entry['cumulative_seconds'], 'prior_renders': entry['cumulative_renders'],
        'remaining_seconds': 2700-entry['cumulative_seconds'], 'remaining_renders': 5000-entry['cumulative_renders'],
        'start_free_bytes': START_FREE, 'stop_free_bytes': STOP_FREE,
        'monitor_interval_seconds': 1, 'automatic_retries': 0,
        'memory_management': 'Collect unreachable Python objects after each case, outside frozen controller and measurements',
        'preservation': 'All original files including truncated trace remain untouched; recovery is a separate immutable directory',
        'accounting': 'Full recovery subprocess, comparisons and artifact sealing debit remaining seed-41 allowance; no reset',
        'inspection': 'Separate read-only raw and stored-pixel remeasurement, no physical controller or raster calls',
        'sealed_holdout_access': False, **physical.FLAGS}


def prepare():
    if PREPARED.exists() or OUTPUT.exists():
        raise FileExistsError('Immutable recovery preparation or attempt already exists')
    verify_original()
    free = require_space(START_FREE)
    record = contract_record()
    PREPARED.mkdir()
    write_json(PREPARED/'contract.json', record)
    return {'status': 'prepared_not_executed', 'contract_sha256': digest(PREPARED/'contract.json'),
            'free_bytes': free, 'controller_executions': 0, 'raster_renders': 0, **physical.FLAGS}


def load_contract(checksum):
    file = PREPARED/'contract.json'
    if not checksum or digest(file) != checksum:
        raise ValueError('External recovery contract pin required')
    record = physical.preflight.foundation.read_json(file)
    if record != contract_record():
        raise ValueError('Changed recovery source or contract')
    return record


class StorageLedger(physical.Ledger):
    def check(self):
        super().check()
        require_space(STOP_FREE)


def worker(checksum):
    recovery = load_contract(checksum)
    contract = physical.load_contract(CONTRACT_SHA256)
    if os.environ.get('PYTHONHASHSEED') != recovery['hashseed']:
        raise ValueError('Wrong replay hash seed')
    permit = physical.preflight.foundation.read_json(OUTPUT/'permit.json')
    if (permit['contract_sha256'] != checksum or permit['maximum'] != recovery['remaining_renders']
            or not 0 < permit['seconds'] <= recovery['remaining_seconds']):
        raise ValueError('Changed recovery permit')
    directory = OUTPUT/'replay'
    directory.mkdir(exist_ok=False)
    budget = StorageLedger(directory/'execution.json', permit['maximum'], permit['seconds'])
    record = {'seed': 41, 'status': 'blocked', 'cases': [], 'controller_executions': 0, **physical.FLAGS}
    try:
        np.random.seed(41)
        comparisons = {}
        for case in contract['cases']:
            budget.check()
            document = physical.document_for(contract, case)
            case_dir = directory/case['id']
            case_dir.mkdir()
            write_json(case_dir/'document.json', document)
            write_json(case_dir/'attempt.json', {'case_id': case['id'], 'controller': 'reserved'})
            record['controller_executions'] += 1
            raw = physical.execute_raw(contract, case, document, budget)
            physical.preflight.foundation.placement.evaluation.compressed(case_dir/'trace.json.gz', raw)
            write_json(case_dir/'attempt.json', {'case_id': case['id'], 'controller': 'complete'})
            result, pixels = reader.measure_case(contract, case, document, raw, budget, case_dir)
            group = (case['fixture']['id'], object_digest(case['program']))
            if case['refinement'] == 'base':
                comparisons[group] = raw, pixels
            else:
                baseline, baseline_pixels = comparisons[group]
                result['comparison'] = reader.measurement.comparison(baseline, raw, baseline_pixels, pixels)
                if case['refinement'] == list(contract['refinements'])[-1]:
                    del comparisons[group]
            result['passed'] = reader.case_pass(result, contract)
            write_json(case_dir/'measurement.json', result)
            record['cases'].append({'id': case['id'], 'passed': result['passed']})
            if case['id'] == contract['control_case_id']:
                record['controls'] = reader.controls(contract, case, document, raw, pixels, budget, directory)
                write_json(directory/'controls.json', record['controls'])
            gc.collect()
            budget.check()
            write_json(OUTPUT/'progress.json', {'measured_cases': len(record['cases']), 'renders': budget.used,
                'elapsed_seconds': time.monotonic()-budget.started, 'free_bytes': require_space(STOP_FREE),
                'process_peak_rss': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                'process_peak_rss_unit': 'bytes' if sys.platform == 'darwin' else 'KiB'})
            if not result['passed']:
                raise ValueError('Physical mechanical failure: '+case['id'])
        if set(record.get('controls', {})) != set(contract['controls']) or not all(record['controls'].values()):
            raise ValueError('Negative controls failed or missing')
        load_contract(checksum)
        record['status'] = 'pass'
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, IndexError) as error:
        record['reason'] = str(error)
    record['renders'] = budget.used
    budget.receipt()
    write_json(directory/'report.json', record)
    return record


def run(checksum):
    if OUTPUT.exists():
        raise FileExistsError('One immutable recovery attempt only; no automatic retry')
    recovery = load_contract(checksum)
    verify_original()
    initial_free = require_space(START_FREE)
    started = time.monotonic()
    OUTPUT.mkdir(exist_ok=False)
    write_json(OUTPUT/'contract.json', recovery)
    report = {'status': 'blocked', 'recovery_contract_sha256': checksum,
              'original_contract_sha256': CONTRACT_SHA256, 'failure_manifest_sha256': FAILURE_SHA256,
              'initial_free_bytes': initial_free, 'minimum_free_bytes': initial_free, **physical.FLAGS}
    process = None
    try:
        seconds = recovery['remaining_seconds']-(time.monotonic()-started)
        write_json(OUTPUT/'permit.json', {'maximum': recovery['remaining_renders'], 'seconds': seconds,
                                        'contract_sha256': checksum})
        with (OUTPUT/'worker.log').open('x') as log:
            process = subprocess.Popen([sys.executable, '-m', 'scripts.letter_context_recovery',
                '--worker', '--contract-sha256', checksum], cwd=ROOT,
                env={**os.environ, 'PYTHONHASHSEED': recovery['hashseed']}, stdout=log, stderr=subprocess.STDOUT)
            while process.poll() is None:
                free = require_space(STOP_FREE)
                report['minimum_free_bytes'] = min(report['minimum_free_bytes'], free)
                if time.monotonic()-started >= recovery['remaining_seconds']:
                    raise RuntimeError('Combined seed budget exhausted')
                time.sleep(recovery['monitor_interval_seconds'])
        report['worker_exit_code'] = process.returncode
        if process.returncode or physical.preflight.foundation.read_json(OUTPUT/'replay/report.json')['status'] != 'pass':
            raise ValueError('Recovery worker failed; preserved without retry')
        if physical.artifact_map(ORIGINAL/'seed-41/first', {'execution.json'}) != physical.artifact_map(OUTPUT/'replay', {'execution.json'}):
            raise ValueError('Fresh seed-41 replay differs')
        verify_original()
        load_contract(checksum)
        report['replay_match'] = True
        report['status'] = 'pass'
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        report['reason'] = str(error)
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
            report['worker_exit_code'] = process.returncode
    receipt_file = OUTPUT/'replay/execution.json'
    receipt = physical.preflight.foundation.read_json(receipt_file) if receipt_file.exists() else {'renders': 0}
    report['artifacts'] = physical.artifact_map(OUTPUT, {'report.json', 'execution.json'})
    elapsed = time.monotonic()-started
    report['ledger'] = {'prior_seconds': recovery['prior_seconds'], 'prior_renders': recovery['prior_renders'],
        'recovery_seconds': elapsed, 'recovery_renders': receipt['renders'],
        'cumulative_seconds': recovery['prior_seconds']+elapsed,
        'cumulative_renders': recovery['prior_renders']+receipt['renders']}
    if report['ledger']['cumulative_seconds'] > 2700 or report['ledger']['cumulative_renders'] > 5000:
        report.update(status='blocked', reason='Combined seed budget exhausted during recovery or sealing')
    write_json(OUTPUT/'execution.json', report['ledger'])
    report['artifacts']['execution.json'] = digest(OUTPUT/'execution.json')
    write_json(OUTPUT/'report.json', report)
    return {key: value for key, value in report.items() if key != 'artifacts'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--run', action='store_true')
    mode.add_argument('--worker', action='store_true')
    parser.add_argument('--contract-sha256')
    args = parser.parse_args()
    result = prepare() if args.prepare else run(args.contract_sha256) if args.run else worker(args.contract_sha256)
    print(json.dumps({key: value for key, value in result.items() if key != 'cases'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
