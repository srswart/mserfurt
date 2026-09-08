"""Independent no-refit admission for frozen finer shared-scale candidates."""

import argparse
import copy
import itertools
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import numpy as np

from scribesim.curriculum import finer_scales as learning
from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures
from scribesim.handvalidate import foundation_actions as physical
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


foundation = physical.foundation
BASE = learning.BASE.parent / 'scale_evaluation'
SPEC_PATH = BASE / 'spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
quality = physical.quality


def identities():
    return {**learning.identities(), **{str(path.relative_to(ROOT)): digest(path)
            for path in (Path(__file__), SPEC_PATH)}}


def fixtures():
    return [{**copy.deepcopy(row), 'split': 'regression'} for row in learning.fixtures()] + copy.deepcopy(SPEC['fresh_fixtures'])


def contexts():
    return copy.deepcopy(foundation.SPEC['contexts']) + copy.deepcopy(SPEC['fresh_contexts'])


def require_candidate(candidate, initial):
    validate_gestures(candidate)
    if object_digest(candidate) != SPEC['candidate_object_sha256']:
        raise ValueError('Exact frozen finer-scale candidate required')
    expected = copy.deepcopy(initial)
    roles = {'stem': 0, 'rise': 1, 'lower-return': 2, 'upper-return': 2}
    for name in SPEC['required_gestures']:
        endpoint = None
        for reference in expected['gestures'][name]['strokes']:
            cubics = initial['primitives'][reference['primitive']]['cubics']
            start, end = np.asarray(cubics[0][0]), np.asarray(cubics[-1][-1])
            if endpoint is None:
                endpoint = start * reference['scale'] + reference['offset']
            reference['scale'] = SPEC['parameters'][roles[reference['primitive']]]
            reference['offset'] = (endpoint - start * reference['scale']).tolist()
            endpoint = end * reference['scale'] + reference['offset']
    if candidate != expected:
        raise ValueError('Shared-scale lineage differs from admitted immutable lower layers')


def ranking(row):
    return row['worst'], row['mean'], row['parameters']


def verify_selection(selected, seed):
    try:
        grids = [[round(center + offset, 2) for offset in learning.SPEC['search']['offsets']]
                 for center in learning.SPEC['search']['initial']]
        proposals = list(itertools.product(*grids))
        random.Random(seed).shuffle(proposals)
        if [tuple(row['parameters']) for row in selected['training']] != proposals:
            raise ValueError('Incomplete or reordered frozen training grid')
        for row in selected['training'] + selected['development']:
            values = row['losses']
            if (set(values) != set(SPEC['required_gestures']) or not physical.finite(values.values())
                    or row != {'parameters': row['parameters'], 'losses': values,
                               'worst': max(values.values()), 'mean': sum(values.values()) / len(values)}):
                raise ValueError('Invalid recorded selection loss')
        shortlist = {tuple(row['parameters']) for row in sorted(selected['training'], key=ranking)[:learning.SPEC['search']['shortlist']]}
        shortlist.add(tuple(learning.SPEC['search']['initial']))
        if [tuple(row['parameters']) for row in selected['development']] != sorted(shortlist):
            raise ValueError('Development shortlist differs')
        chosen = min(selected['development'], key=ranking)
        expected = {'seed': seed, 'parameters': chosen['parameters'], 'training': selected['training'],
            'development': selected['development'], 'selection_split': 'development', 'held_out_accessed': False,
            'development_absolute_pass': chosen['worst'] <= SPEC['criteria']['absolute_loss_max'],
            'candidate_sha256': SPEC['candidate_object_sha256']}
        if selected != expected or chosen['parameters'] != SPEC['parameters']:
            raise ValueError('Selected checkpoint or selection scope differs')
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('Incomplete saved selection') from error


def verify_compiled(record, candidate):
    for row in [*record['fixtures'], record['counter']]:
        model = foundation.probe(candidate, row['fixture'])
        if row['probe_sha256'] != object_digest(model) or row['compiled_sources'] != compile_gestures('i', model)['strokes']:
            raise ValueError('Detached source or diagnostic proof')
    for row in record['contexts']:
        model = foundation.probe(candidate, row['fixture'])
        if row['probe_sha256'] != object_digest(model) or row['compiled'] != compile_gestures(row['fixture']['text'], model)['strokes']:
            raise ValueError('Detached context proof')


def verify_execution(directory, report, baselines, *, source=False):
    ledger = json.loads((directory / 'execution.json').read_text())['ledger']
    if [(row['seed'], row['process']) for row in ledger] != [(seed, label) for seed in SPEC['seeds'] for label in ('first', 'replay')]:
        raise ValueError('Missing seed/process ledger')
    if report['renders'] != sum(row['renders'] for row in ledger):
        raise ValueError('Total render accounting differs')
    records, scoring = [], 0
    for seed in SPEC['seeds']:
        first, replay = directory / f'seed-{seed}/first', directory / f'seed-{seed}/replay'
        if foundation.primitives.manifest(first) != foundation.primitives.manifest(replay):
            raise ValueError('Seed replay differs')
        used, elapsed = 0, 0
        for receipt in [row for row in ledger if row['seed'] == seed]:
            worker_dir = directory / f"seed-{seed}/{receipt['process']}"
            record = json.loads((worker_dir / 'report.json').read_text())
            clock = json.loads((worker_dir / 'execution.json').read_text())
            if (type(receipt['renders']) is not int or receipt['renders'] <= 0
                    or receipt['renders'] != record['renders'] or receipt['renders'] != clock['renders']
                    or not physical.finite([clock['elapsed_seconds'], receipt['cumulative_seed_seconds']])):
                raise ValueError('Invalid worker accounting')
            used += receipt['renders']
            if (receipt['cumulative_seed_renders'] != used or used > 5000
                    or not elapsed + clock['elapsed_seconds'] <= receipt['cumulative_seed_seconds'] <= 1800):
                raise ValueError('Combined seed budget differs')
            elapsed = receipt['cumulative_seed_seconds']
            path = worker_dir / 'candidate.json'
            if digest(path) != SPEC['candidate_file_sha256']:
                raise ValueError('Selected candidate bytes changed')
            candidate = json.loads(path.read_text())
            require_candidate(candidate, baselines[seed])
            valid = learning.complete(record) if source else complete(record)
            if (record['seed'] != seed or record['status'] != 'complete' or not valid
                    or record['candidate_sha256'] != object_digest(candidate)
                    or any(record[key] is not False for key in ('S1_action_accepted', 'letter_training_allowed', 'real_accepted'))
                    or record['controls'] != json.loads((worker_dir / 'controls.json').read_text())):
                raise ValueError('Worker evidence is incomplete or overstated')
            verify_compiled(record, candidate)
            if source:
                selected = json.loads((worker_dir / 'selection.json').read_text())
                verify_selection(selected, seed)
                journal = [{'split': split, **row} for split, key in [('train', 'training'), ('development', 'development')]
                           for row in selected[key]]
                if (record['parameters'] != SPEC['parameters'] or record['outcomes'] != learning.outcomes(record)
                        or json.loads((worker_dir / 'search-journal.json').read_text()) != journal
                        or record['optimization_evaluations'] != len(journal)
                        or not all(quality(row) for row in record['fixtures'])):
                    raise ValueError('Learning selection or quality reconstruction differs')
            elif record['outcomes'] != outcomes(record):
                raise ValueError('Scoped outcomes differ from numeric proof')
            scoring += record['optimization_evaluations']
        records.append(json.loads((first / 'report.json').read_text()))
    if report['optimization_evaluations'] != scoring:
        raise ValueError('Scoring ledger differs')
    return records


def load_inputs():
    directory = learning.BASE / 'run-001'
    try:
        if digest(directory / 'report.json') != SPEC['source_report_sha256']:
            raise ValueError('Consumer-pinned learning report required')
        report = json.loads((directory / 'report.json').read_text())
        if (report['stage'] != learning.SPEC['stage'] or report['code_sha256'] != learning.identities()
                or json.loads((directory / 'freeze.json').read_text()) != {'spec': learning.SPEC, 'code_sha256': learning.identities()}
                or report['status'] != 'pass' or report['measurement_complete'] is not True
                or any(report[key] is not False for key in ('S1_action_accepted', 'letter_training_allowed', 'real_accepted', 'handle_repair_executed'))
                or SPEC['criteria'] != physical.SPEC['criteria']):
            raise ValueError('Stale or overstated selected evidence')
        foundation.primitives.verify_artifacts(directory, report['artifacts'])
        baselines = learning.load_inputs()['candidates']
        records = verify_execution(directory, report, baselines, source=True)
        expected = [{'seed': row['seed'], 'measured': True, 'replay_match': True,
                     'parameters': SPEC['parameters'], 'candidate_sha256': SPEC['candidate_object_sha256'],
                     'outcomes': learning.outcomes(row)} for row in records]
        if report['seeds'] != expected:
            raise ValueError('Learning seed summary differs')
        return {'directory': directory, 'report_sha256': SPEC['source_report_sha256'], 'baselines': baselines,
                'candidates': {seed: json.loads((directory / f'seed-{seed}/first/candidate.json').read_text()) for seed in SPEC['seeds']}}
    except (OSError, KeyError, TypeError, IndexError) as error:
        raise ValueError('Incomplete selected input evidence') from error


def complete(record):
    try:
        return (record['optimization_evaluations'] == 0 and record['candidate_sha256'] == SPEC['candidate_object_sha256']
            and [row['fixture'] for row in record['fixtures']] == fixtures()
            and all(physical.mechanical(row) and physical.finite([row['nominal_target']])
                and set(row['actual_target']) == set(physical.REFINEMENTS) and physical.finite(row['actual_target'].values())
                and set(row['local_actual_target']) == set(foundation.regions(row['fixture']))
                and set(row['local_nominal_target']) == set(foundation.regions(row['fixture']))
                and physical.finite(row['local_nominal_target'].values())
                and all(set(values) == set(physical.REFINEMENTS) and physical.finite(values.values())
                    for values in row['local_actual_target'].values()) for row in record['fixtures'])
            and [row['fixture'] for row in record['contexts']] == contexts()
            and all(foundation.motion_pass(row) for row in record['contexts'])
            and record['counter']['fixture'] == physical.SPEC['counter_fixture']
            and physical.mechanical(record['counter'], counter=True)
            and physical.controls_pass(record['controls']))
    except (KeyError, ValueError, TypeError):
        return False


def outcomes(record):
    result = {}
    measured = complete(record)
    for name in SPEC['required_gestures']:
        rows = [row for row in record.get('fixtures', []) if any(item['gesture'] == name for item in row['fixture']['instances'])]
        accepted = measured and bool(rows) and all(quality(row, name) for row in rows)
        result[name] = {'null_accepted': accepted, 'actions': {action: 'accepted-scoped-null' if accepted else 'unresolved'
            for action in ('rotation', 'edge', 'finishing')}, 'active_action_required': 'not established',
            'local_loss_max': max((max(row['local_actual_target'][str(index)].values()) for row in rows
                for index, item in enumerate(row['fixture']['instances']) if item['gesture'] == name), default=None)}
    return result


def worker(directory, seed, maximum, seconds):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    budget = foundation.JournalBudget(directory, maximum, seconds)
    record = {'seed': seed, 'status': 'blocked', 'optimization_evaluations': 0, 'fixtures': [], 'contexts': [],
              'controls': {}, 'S1_action_accepted': False, 'letter_training_allowed': False, 'real_accepted': False}
    try:
        source = load_inputs()
        frozen = json.loads((directory.parent.parent / 'freeze.json').read_text())
        if frozen != {'spec': SPEC, 'code_sha256': identities()}:
            raise ValueError('Stale pre-render independent freeze')
        candidate = source['candidates'][seed]
        record['candidate_sha256'] = object_digest(candidate)
        (directory / 'candidate.json').write_bytes((source['directory'] / f'seed-{seed}/first/candidate.json').read_bytes())
        sheets, control_base, overlap = [], None, None
        for fixture in fixtures():
            row, tiles, actual = physical.measure(candidate, fixture, budget, directory)
            record['fixtures'].append(row)
            sheets.append((row, tiles))
            write_json(directory / 'progress.json', record)
            if not physical.mechanical(row):
                raise ValueError('Mechanical or pocket failure: ' + fixture['id'])
            if fixture['id'] == physical.SPEC['fixtures'][6]['id']:
                control_base = actual
        for fixture in contexts():
            row, actual = foundation.evaluate_context(candidate, fixture, budget, directory)
            record['contexts'].append(row)
            if not foundation.motion_pass(row):
                raise ValueError('Context mechanics failed: ' + fixture['id'])
            if fixture == foundation.SPEC['contexts'][0]:
                overlap = actual
        record['counter'], _, counter_run = physical.measure(candidate, physical.SPEC['counter_fixture'], budget, directory, counter=True)
        if not physical.mechanical(record['counter'], counter=True):
            raise ValueError('Counter mechanics failed')
        record['controls'] = physical.controls(candidate, physical.SPEC['fixtures'][6], control_base, overlap, counter_run, budget, directory)
        for label in ('held_out', 'regression'):
            budget.render(physical.learning.sheet, directory / f'{label}-sheet.png',
                [(row, tiles) for row, tiles in sheets if row['fixture']['split'] == label])
        require_candidate(candidate, source['baselines'][seed])
        if frozen != {'spec': SPEC, 'code_sha256': identities()}:
            raise ValueError('Evaluation identities changed')
        record['outcomes'] = outcomes(record)
        record['status'] = 'complete' if complete(record) else 'blocked'
        budget.check()
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        record['reason'] = str(error)
        if (directory / 'controls.json').exists():
            record['controls'] = json.loads((directory / 'controls.json').read_text())
    record['renders'] = budget.used
    write_json(directory / 'report.json', record)
    budget.receipt()
    return record


def decisions(records):
    accepted = [name for name in SPEC['required_gestures'] if all(outcomes(row)[name]['null_accepted'] for row in records)]
    full = len(records) == len(SPEC['seeds']) and accepted == SPEC['required_gestures'] and all(quality(row) for record in records for row in record['fixtures'])
    return accepted, full


def build():
    output = BASE / 'run-001'
    if output.exists() or list(BASE.glob('run-*')):
        raise ValueError('Single immutable evaluation; additional attempts need authorization')
    write_json(output / 'freeze.json', {'spec': SPEC, 'code_sha256': identities()})
    report = {'stage': SPEC['stage'], 'status': 'blocked', 'evaluation_complete': False, 'code_sha256': identities(),
        'seeds': [], 'renders': 0, 'optimization_evaluations': 0, 'accepted_gestures': [], 'S1_action_accepted': False,
        'letter_training_allowed': False, 'real_accepted': False, 'promoted': False}
    ledger, records = [], []
    try:
        load_inputs()
        for seed in SPEC['seeds']:
            started, used = time.monotonic(), 0
            for label, hashseed in (('first', '7'), ('replay', '839')):
                remaining = 1800 - (time.monotonic() - started)
                if remaining <= 0 or used >= 5000:
                    raise RuntimeError('Combined seed budget exhausted')
                directory = output / f'seed-{seed}/{label}'
                try:
                    process = subprocess.run([sys.executable, '-m', 'scribesim.handvalidate.finer_scales', '--worker', str(directory),
                        '--seed', str(seed), '--maximum', str(5000 - used), '--seconds', str(remaining)], cwd=ROOT,
                        env={**os.environ, 'PYTHONHASHSEED': hashseed}, capture_output=True, text=True, timeout=remaining)
                finally:
                    receipt_path = directory / 'execution.json'
                    if receipt_path.exists():
                        receipt = json.loads(receipt_path.read_text())
                        used += receipt['renders']
                        report['renders'] += receipt['renders']
                        ledger.append({'seed': seed, 'process': label, 'renders': receipt['renders'],
                            'cumulative_seed_renders': used, 'cumulative_seed_seconds': time.monotonic() - started})
                        write_json(output / 'execution.json', {'ledger': ledger})
                if process.returncode or not receipt_path.exists():
                    raise RuntimeError('Worker failed: ' + process.stdout[-1000:] + process.stderr[-1000:])
            first, replay = output / f'seed-{seed}/first', output / f'seed-{seed}/replay'
            record = json.loads((first / 'report.json').read_text())
            matching = foundation.primitives.manifest(first) == foundation.primitives.manifest(replay)
            measured = record['status'] == 'complete' and complete(record) and matching and used <= 5000 and time.monotonic() - started <= 1800
            report['seeds'].append({'seed': seed, 'measured': measured, 'replay_match': matching, 'outcomes': outcomes(record)})
            if not measured:
                raise ValueError('Incomplete measurement or replay')
            records.append(record)
        report['evaluation_complete'] = len(records) == len(SPEC['seeds'])
        report['accepted_gestures'], report['S1_action_accepted'] = decisions(records)
        report['status'] = 'pass' if report['S1_action_accepted'] else 'fail'
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
    report['missing_inventory'] = ['unresolved:' + name for name in SPEC['required_gestures'] if name not in report['accepted_gestures']]
    report['missing_inventory'] += ['unmeasured gesture families and seven-stroke compound/return carriers',
        'active actions and cross-tool transfer', 'learned letters and words', 'real-hand G0/G1/G2 and human appearance review']
    write_json(output / 'execution.json', {'ledger': ledger})
    report['artifacts'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
    write_json(output / 'S1-actions.json', report)
    return report


def inspect_evidence(directory, *, expected_report_sha256):
    directory = Path(directory).resolve()
    try:
        if not expected_report_sha256 or digest(directory / 'S1-actions.json') != expected_report_sha256:
            raise ValueError('Consumer-pinned independent manifest required')
        report = json.loads((directory / 'S1-actions.json').read_text())
        if (report['stage'] != SPEC['stage'] or report['code_sha256'] != identities()
                or json.loads((directory / 'freeze.json').read_text()) != {'spec': SPEC, 'code_sha256': identities()}
                or report['evaluation_complete'] is not True or report['optimization_evaluations'] != 0
                or any(report[key] is not False for key in ('letter_training_allowed', 'real_accepted', 'promoted'))):
            raise ValueError('Stale, incomplete or overstated independent evidence')
        foundation.primitives.verify_artifacts(directory, report['artifacts'])
        source = load_inputs()
        records = verify_execution(directory, report, source['baselines'])
        accepted, full = decisions(records)
        expected_seeds = [{'seed': row['seed'], 'measured': True, 'replay_match': True, 'outcomes': outcomes(row)} for row in records]
        if (report['seeds'] != expected_seeds or report['accepted_gestures'] != accepted
                or report['S1_action_accepted'] is not full or report['status'] != ('pass' if full else 'fail')):
            raise ValueError('Independent admission flags differ from numeric evidence')
        return {'report_sha256': expected_report_sha256, 'accepted_gestures': accepted,
                'full_inventory_accepted': full, 'records': records, 'letter_training_allowed': False, 'real_accepted': False}
    except (OSError, KeyError, TypeError, IndexError) as error:
        raise ValueError('Incomplete independent evidence') from error


def require_readiness(directory, *, expected_report_sha256, required_gestures, tool='legacy-full-edge', real=False):
    if (not isinstance(required_gestures, (list, tuple)) or not required_gestures
            or len(set(required_gestures)) != len(required_gestures)
            or not set(required_gestures) <= set(SPEC['required_gestures']) or tool != SPEC['tool'] or real is not False):
        raise ValueError('Explicit supported synthetic fixed-tool scope required')
    evidence = inspect_evidence(directory, expected_report_sha256=expected_report_sha256)
    if (not set(required_gestures) <= set(evidence['accepted_gestures'])
            or set(required_gestures) == set(SPEC['required_gestures']) and not evidence['full_inventory_accepted']):
        raise ValueError('Unresolved requested inventory')
    return {'stage': SPEC['stage'], 'report_sha256': expected_report_sha256, 'tool': tool,
        'candidate_file_sha256': SPEC['candidate_file_sha256'], 'required_gestures': sorted(required_gestures),
        'S1_action_accepted': True, 'kind': 'scoped-fixed-null', 'letter_training_allowed': False, 'real_accepted': False,
        'scope': 'Frozen finer-scale synthetic constructions only; not universal null, active actions, letters or historical handwriting'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args()
    report = worker(args.worker, args.seed, args.maximum, args.seconds) if args.worker else build()
    print(json.dumps({key: report[key] for key in ('status', 'renders', 'reason', 'accepted_gestures') if key in report}))
    return 1 if report['status'] == 'blocked' else 0


if __name__ == '__main__':
    raise SystemExit(main())
