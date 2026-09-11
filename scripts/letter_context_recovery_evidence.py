"""Read-only composite inspection of preserved first runs and the recovered replay."""

import argparse
import json
import math
from pathlib import Path

from scripts import letter_context_physical as physical
from scripts import letter_context_physical_evidence as reader
from scripts import letter_context_recovery as recovery
from scribesim.handvalidate.specimen import digest


def verify_receipt(receipt, schedule, maximum, seconds, elapsed):
    if (type(receipt['renders']) is not int or receipt['renders'] != len(schedule)
            or receipt['maximum_renders'] != maximum or receipt['maximum_seconds'] != seconds
            or not all(math.isfinite(value) for value in (seconds, elapsed, receipt['elapsed_seconds']))
            or not 0 <= receipt['elapsed_seconds'] <= min(seconds, elapsed)
            or not 0 < seconds <= 2700 or not 0 < maximum <= 5000
            or receipt['events'] != [{'ordinal': index, 'operation': name, 'status': 'complete'}
                                     for index, name in enumerate(schedule, 1)]):
        raise ValueError('Render journal or time allowance mismatch')


def verify_original_budgets(contract, manifest):
    ledger = physical.preflight.foundation.read_json(recovery.ORIGINAL/'execution.json')['ledger']
    if ledger != manifest['ledger']:
        raise ValueError('Changed original ledger')
    required = [(seed, label) for seed in (7, 19, 41) for label in ('first', 'replay')]
    if [(row['seed'], row['process']) for row in ledger] != required:
        raise ValueError('Incomplete original ledger')
    schedule = physical.render_schedule(contract)
    for seed in (7, 19, 41):
        used, elapsed = 0, 0
        for entry in [row for row in ledger if row['seed'] == seed]:
            root = recovery.ORIGINAL/f'seed-{seed}'
            label = entry['process']
            receipt = physical.preflight.foundation.read_json(root/label/'execution.json')
            permit = physical.preflight.foundation.read_json(root/f'{label}-permit.json')
            if (permit['seed'] != seed or permit['label'] != label
                    or permit['contract_sha256'] != recovery.CONTRACT_SHA256
                    or permit['maximum'] != 5000-used or not 0 < permit['seconds'] <= 2700-elapsed
                    or not math.isfinite(entry['cumulative_seconds'])
                    or not elapsed <= entry['cumulative_seconds'] <= 2700):
                raise ValueError('Original seed permit or time mismatch')
            expected = schedule if (seed, label) != (41, 'replay') else schedule[:167]
            verify_receipt(receipt, expected, permit['maximum'], permit['seconds'], entry['cumulative_seconds']-elapsed)
            used += receipt['renders']
            if entry['renders'] != receipt['renders'] or used != entry['cumulative_renders'] or used > 5000:
                raise ValueError('Original cumulative render mismatch')
            elapsed = entry['cumulative_seconds']


def inspect(directory, report_sha256, contract_sha256):
    directory = Path(directory).resolve()
    if directory != recovery.OUTPUT.resolve() or digest(directory/'report.json') != report_sha256:
        raise ValueError('External recovery report pin and fixed directory required')
    frozen = recovery.load_contract(contract_sha256)
    manifest = recovery.verify_original()
    contract = physical.load_contract(recovery.CONTRACT_SHA256)
    report = physical.preflight.foundation.read_json(directory/'report.json')
    if (report['status'] != 'pass' or not physical.scope_matches(report) or report.get('replay_match') is not True
            or report.get('worker_exit_code') != 0 or report['recovery_contract_sha256'] != contract_sha256
            or report['original_contract_sha256'] != recovery.CONTRACT_SHA256
            or report['failure_manifest_sha256'] != recovery.FAILURE_SHA256
            or digest(directory/'contract.json') != contract_sha256
            or report['artifacts'] != physical.artifact_map(directory, {'report.json'})):
        raise ValueError('Incomplete recovery report, scope or artifact inventory')
    verify_original_budgets(contract, manifest)
    ledger = physical.preflight.foundation.read_json(directory/'execution.json')
    if (ledger != report['ledger'] or ledger['prior_seconds'] != frozen['prior_seconds']
            or ledger['prior_renders'] != frozen['prior_renders']
            or not math.isfinite(ledger['recovery_seconds']) or not 0 <= ledger['recovery_seconds'] <= frozen['remaining_seconds']
            or ledger['recovery_renders'] != frozen['scheduled_renders']
            or ledger['cumulative_seconds'] != ledger['prior_seconds']+ledger['recovery_seconds']
            or ledger['cumulative_renders'] != ledger['prior_renders']+ledger['recovery_renders']
            or ledger['cumulative_seconds'] > 2700 or ledger['cumulative_renders'] > 5000):
        raise ValueError('Recovery resets or exceeds cumulative seed budget')
    permit = physical.preflight.foundation.read_json(directory/'permit.json')
    if (permit['contract_sha256'] != contract_sha256 or permit['maximum'] != frozen['remaining_renders']
            or not 0 < permit['seconds'] <= frozen['remaining_seconds']):
        raise ValueError('Changed recovery allowance')
    receipt = physical.preflight.foundation.read_json(directory/'replay/execution.json')
    verify_receipt(receipt, physical.render_schedule(contract), permit['maximum'], permit['seconds'], ledger['recovery_seconds'])
    summaries = []
    for seed in (7, 19, 41):
        first = recovery.ORIGINAL/f'seed-{seed}/first'
        replay = directory/'replay' if seed == 41 else recovery.ORIGINAL/f'seed-{seed}/replay'
        if physical.artifact_map(first, {'execution.json'}) != physical.artifact_map(replay, {'execution.json'}):
            raise ValueError('Fresh-process replay differs')
        for label, worker_dir in [('first', first), ('replay', replay)]:
            record = reader.verify_worker(contract, worker_dir, seed)
            if record['renders'] != frozen['scheduled_renders']:
                raise ValueError('Worker render count differs')
            print(f'Independently verified seed {seed} {label}: {len(record["cases"])} cases', flush=True)
        summaries.append({'seed': seed, 'replay_match': True})
    recovery.verify_original()
    recovery.load_contract(contract_sha256)
    if digest(directory/'report.json') != report_sha256 or report['artifacts'] != physical.artifact_map(directory, {'report.json'}):
        raise ValueError('Recovery changed during inspection')
    return {'status': 'pass', 'read_only': True, 'report_sha256': report_sha256,
        'recovery_contract_sha256': contract_sha256, 'original_contract_sha256': recovery.CONTRACT_SHA256,
        'failure_manifest_sha256': recovery.FAILURE_SHA256, 'cases_verified': len(contract['cases'])*6,
        'seeds': summaries, 'seed_41_cumulative_ledger': ledger, 'raster_renders': 0, 'controller_executions': 0,
        'historical_style_numeric_pass': False, 'appearance_review': 'pending', **physical.FLAGS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', type=Path, required=True)
    parser.add_argument('--report-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.inspect, args.report_sha256, args.contract_sha256), indent=2), flush=True)


if __name__ == '__main__':
    main()
