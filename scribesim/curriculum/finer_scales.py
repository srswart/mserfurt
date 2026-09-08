"""Bounded shared-scale accuracy experiment, without lower-layer promotion."""

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

from scribesim.curriculum import foundation_actions as learning
from scribesim.curriculum import foundation_gestures as gestures
from scribesim.evofit.stroke_gestures import validate_gestures
from scribesim.handvalidate import foundation_actions as independent
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


foundation = learning.foundation
BASE = learning.BASE.parent / 'finer_scales'
SPEC_PATH = BASE / 'spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
CONSTRUCTIONS = ('underturn', 'overturn', 'compound_curve')
ROLES = {'stem': 0, 'rise': 1, 'lower-return': 2, 'upper-return': 2}


def identities():
    return {**independent.identities(), **{str(path.relative_to(ROOT)): digest(path)
            for path in (Path(__file__), SPEC_PATH)}}


def grids():
    return [[round(center + offset, 2) for offset in SPEC['search']['offsets']]
            for center in SPEC['search']['initial']]


def with_parameters(initial, parameters):
    if len(parameters) != 3 or any(type(value) not in (int, float) or not math.isfinite(value)
            or value not in grid for value, grid in zip(parameters, grids())):
        raise ValueError('Unfrozen shared-scale parameters')
    candidate = copy.deepcopy(initial)
    for name in CONSTRUCTIONS:
        endpoint = None
        for reference in candidate['gestures'][name]['strokes']:
            cubics = initial['primitives'][reference['primitive']]['cubics']
            start, end = np.asarray(cubics[0][0]), np.asarray(cubics[-1][-1])
            if endpoint is None:
                endpoint = start * reference['scale'] + reference['offset']
            reference['scale'] = float(parameters[ROLES[reference['primitive']]])
            reference['offset'] = (endpoint - start * reference['scale']).tolist()
            endpoint = end * reference['scale'] + reference['offset']
    validate_gestures(candidate)
    return candidate


def require_lineage(candidate, initial, parameters):
    if candidate != with_parameters(initial, parameters):
        raise ValueError('Only shared scales and derived attachments may change')


def fixtures():
    result = [copy.deepcopy(row) for row in gestures.SPEC['fixtures'] if row['split'] in ('train', 'development')]
    result.extend({**copy.deepcopy(row), 'split': 'regression'} for row in independent.SPEC['fixtures'])
    return result + copy.deepcopy(SPEC['fresh_fixtures'])


def load_inputs():
    prior = independent.inspect_evidence(independent.BASE / 'run-003',
        expected_report_sha256=SPEC['source_report_sha256'])
    source = learning.load_inputs()
    if (prior['accepted_gestures'] != ['underturn']
            or SPEC['criteria']['absolute_loss_max'] != independent.SPEC['criteria']['absolute_loss_max']
            or SPEC['criteria']['blank_fraction_max'] != independent.SPEC['criteria']['blank_fraction_max']
            or gestures.SPEC['targets'] != foundation.SPEC['targets']):
        raise ValueError('Changed source scope, targets or thresholds')
    for seed, candidate in source['candidates'].items():
        path = learning.BASE / f'run-001/seed-{seed}/first/candidate.json'
        if digest(path) != SPEC['candidate_file_sha256'] or json.loads(path.read_text()) != candidate:
            raise ValueError('Changed baseline candidate')
        require_lineage(candidate, candidate, SPEC['search']['initial'])
    return source


def scored(parameters, losses):
    if (set(losses) != set(CONSTRUCTIONS) or any(type(value) not in (int, float)
            or not math.isfinite(value) or value < 0 for value in losses.values())):
        raise ValueError('Complete finite construction-local losses required')
    return {'parameters': list(parameters), 'losses': losses, 'worst': max(losses.values()),
            'mean': sum(losses.values()) / len(losses)}


def rank(row):
    return row['worst'], row['mean'], row['parameters']


def select(score, *, seed):
    if seed not in SPEC['seeds']:
        raise ValueError('Unfrozen seed')
    proposals = list(itertools.product(*grids()))
    random.Random(seed).shuffle(proposals)
    training = [scored(parameters, score(list(parameters), 'train')) for parameters in proposals]
    shortlist = {tuple(row['parameters']) for row in sorted(training, key=rank)[:SPEC['search']['shortlist']]}
    shortlist.add(tuple(SPEC['search']['initial']))
    development = [scored(parameters, score(list(parameters), 'development')) for parameters in sorted(shortlist)]
    chosen = min(development, key=rank)
    return {'seed': seed, 'parameters': chosen['parameters'], 'training': training, 'development': development,
            'selection_split': 'development', 'held_out_accessed': False,
            'development_absolute_pass': chosen['worst'] <= SPEC['criteria']['absolute_loss_max']}


def fit(initial, seed, budget, directory):
    lessons = [row for row in fixtures() if row['split'] in ('train', 'development')]
    targets = {row['id']: budget.render(foundation.paint, independent.target(row)) for row in lessons}
    journal = []

    def score(parameters, split):
        candidate = with_parameters(initial, parameters)
        losses = {}
        for fixture in lessons:
            if fixture['split'] == split:
                pixels = budget.render(foundation.paint, foundation.nominal(foundation.probe(candidate, fixture)))
                bounds = foundation.regions(fixture)['0']['loss']
                losses[fixture['instances'][0]['gesture']] = foundation.stroke_loss(
                    foundation.crop(targets[fixture['id']], bounds), foundation.crop(pixels, bounds))
        journal.append({'split': split, **scored(parameters, losses)})
        write_json(directory / 'search-journal.json', journal)
        return losses

    selected = select(score, seed=seed)
    candidate = with_parameters(initial, selected['parameters'])
    selected['candidate_sha256'] = object_digest(candidate)
    write_json(directory / 'selection.json', selected)
    write_json(directory / 'candidate.json', candidate)
    return candidate, selected


def complete(record):
    try:
        return ([row['fixture'] for row in record['fixtures']] == fixtures()
            and all(independent.mechanical(row) and independent.finite([row['nominal_target']])
                and set(row['actual_target']) == set(independent.REFINEMENTS)
                and independent.finite(row['actual_target'].values())
                and set(row['local_actual_target']) == set(foundation.regions(row['fixture']))
                and all(set(values) == set(independent.REFINEMENTS) and independent.finite(values.values())
                    for values in row['local_actual_target'].values()) for row in record['fixtures'])
            and [row['fixture'] for row in record['contexts']] == foundation.SPEC['contexts']
            and all(foundation.motion_pass(row) for row in record['contexts'])
            and record['counter']['fixture'] == independent.SPEC['counter_fixture']
            and independent.mechanical(record['counter'], counter=True)
            and independent.controls_pass(record['controls']))
    except (KeyError, ValueError, TypeError):
        return False


def outcomes(record):
    return {name: {'actual_local_max': max((max(row['local_actual_target'][str(index)].values())
        for row in record['fixtures'] for index, instance in enumerate(row['fixture']['instances'])
        if instance['gesture'] == name), default=None),
        'quality_pass': complete(record) and all(independent.quality(row, name) for row in record['fixtures']
            if any(instance['gesture'] == name for instance in row['fixture']['instances']))} for name in CONSTRUCTIONS}


def worker(directory, seed, maximum, seconds):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    budget = foundation.JournalBudget(directory, maximum, seconds)
    record = {'seed': seed, 'status': 'blocked', 'fixtures': [], 'contexts': [], 'controls': {},
              'S1_action_accepted': False, 'letter_training_allowed': False, 'real_accepted': False}
    try:
        source = load_inputs()
        frozen = json.loads((directory.parent.parent / 'freeze.json').read_text())
        if frozen != {'spec': SPEC, 'code_sha256': identities()}:
            raise ValueError('Stale pre-render experiment freeze')
        initial = source['candidates'][seed]
        candidate, selected = fit(initial, seed, budget, directory)
        record['candidate_sha256'] = object_digest(candidate)
        record['parameters'] = selected['parameters']
        sheets, control_base, overlap = [], None, None
        for fixture in fixtures():
            row, tiles, actual = independent.measure(candidate, fixture, budget, directory)
            record['fixtures'].append(row)
            sheets.append((row, tiles))
            write_json(directory / 'progress.json', record)
            if not independent.mechanical(row):
                raise ValueError('Mechanical or blank-pocket failure: ' + fixture['id'])
            if fixture['id'] == independent.SPEC['fixtures'][6]['id']:
                control_base = actual
        for fixture in foundation.SPEC['contexts']:
            row, actual = foundation.evaluate_context(candidate, fixture, budget, directory)
            record['contexts'].append(row)
            if not foundation.motion_pass(row):
                raise ValueError('Mechanical context failure: ' + fixture['id'])
            if fixture == foundation.SPEC['contexts'][0]:
                overlap = actual
        record['counter'], _, counter_run = independent.measure(candidate, independent.SPEC['counter_fixture'], budget, directory, counter=True)
        if not independent.mechanical(record['counter'], counter=True):
            raise ValueError('Closed-counter mechanical failure')
        record['controls'] = independent.controls(candidate, independent.SPEC['fixtures'][6], control_base,
            overlap, counter_run, budget, directory)
        for split in ('train', 'development', 'regression', 'held_out'):
            budget.render(learning.sheet, directory / f'{split}-sheet.png',
                [(row, tiles) for row, tiles in sheets if row['fixture']['split'] == split])
        require_lineage(candidate, initial, selected['parameters'])
        if frozen != {'spec': SPEC, 'code_sha256': identities()}:
            raise ValueError('Experiment identities changed during execution')
        record['outcomes'] = outcomes(record)
        record['status'] = 'complete' if complete(record) else 'blocked'
        budget.check()
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        record['reason'] = str(error)
    record['renders'] = budget.used
    record['optimization_evaluations'] = len(json.loads((directory / 'search-journal.json').read_text())) if (directory / 'search-journal.json').exists() else 0
    write_json(directory / 'report.json', record)
    budget.receipt()
    return record


def build():
    output = BASE / 'run-001'
    if output.exists() or list(BASE.glob('run-*')):
        raise ValueError('Use an immutable single experiment; no automatic retries')
    write_json(output / 'freeze.json', {'spec': SPEC, 'code_sha256': identities()})
    report = {'stage': SPEC['stage'], 'status': 'blocked', 'measurement_complete': False, 'seeds': [],
        'code_sha256': identities(), 'renders': 0, 'optimization_evaluations': 0, 'S1_action_accepted': False,
        'letter_training_allowed': False, 'real_accepted': False, 'handle_repair_executed': False}
    ledger, records = [], []
    try:
        load_inputs()
        for seed in SPEC['seeds']:
            started, used = time.monotonic(), 0
            for label, hashseed in (('first', '7'), ('replay', '839')):
                remaining = SPEC['budget']['seconds_per_seed_including_replay'] - (time.monotonic() - started)
                maximum = SPEC['budget']['renders_per_seed_including_replay'] - used
                if remaining <= 0 or maximum <= 0:
                    raise RuntimeError('Combined seed budget exhausted')
                directory = output / f'seed-{seed}/{label}'
                try:
                    process = subprocess.run([sys.executable, '-m', 'scribesim.curriculum.finer_scales',
                        '--worker', str(directory), '--seed', str(seed), '--maximum', str(maximum), '--seconds', str(remaining)],
                        cwd=ROOT, env={**os.environ, 'PYTHONHASHSEED': hashseed}, capture_output=True, text=True, timeout=remaining)
                finally:
                    receipt_path = directory / 'execution.json'
                    if receipt_path.exists():
                        receipt = json.loads(receipt_path.read_text())
                        used += receipt['renders']
                        report['renders'] += receipt['renders']
                        ledger.append({'seed': seed, 'process': label, 'renders': receipt['renders'],
                            'cumulative_seed_renders': used, 'cumulative_seed_seconds': time.monotonic() - started})
                        write_json(output / 'execution.json', {'ledger': ledger})
                    worker_report = directory / 'report.json'
                    if worker_report.exists():
                        report['optimization_evaluations'] += json.loads(worker_report.read_text())['optimization_evaluations']
                if process.returncode or not receipt_path.exists():
                    raise RuntimeError('Worker failed: ' + process.stdout[-1000:] + process.stderr[-1000:])
            first, replay = output / f'seed-{seed}/first', output / f'seed-{seed}/replay'
            record = json.loads((first / 'report.json').read_text())
            matching = foundation.primitives.manifest(first) == foundation.primitives.manifest(replay)
            measured = complete(record) and record['status'] == 'complete' and matching and used <= 5000 and time.monotonic() - started <= 1800
            report['seeds'].append({'seed': seed, 'measured': measured, 'replay_match': matching,
                'parameters': record['parameters'], 'candidate_sha256': record['candidate_sha256'], 'outcomes': outcomes(record)})
            if not measured:
                raise ValueError('Incomplete measurement or replay')
            records.append(record)
        report['measurement_complete'] = len(records) == len(SPEC['seeds'])
        passed = report['measurement_complete'] and all(independent.quality(row) for record in records for row in record['fixtures'])
        report['status'] = 'pass' if passed else 'fail'
        report['next_step'] = ('Independent evaluation of frozen scale-only candidates; no handle repair needed for measured scope'
            if passed else 'Diagnose remaining nominal residuals before a separately frozen shared-return-handle repair')
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
        report['next_step'] = 'Stop: diagnose incomplete mechanical/runtime/budget evidence; no automatic retry or handle fit'
    write_json(output / 'execution.json', {'ledger': ledger})
    report['artifacts'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
    write_json(output / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args()
    result = worker(args.worker, args.seed, args.maximum, args.seconds) if args.worker else build()
    print(json.dumps({key: value for key, value in result.items() if key in ('status', 'reason', 'next_step', 'renders')}))
    return 1 if result['status'] == 'blocked' else 0


if __name__ == '__main__':
    raise SystemExit(main())
