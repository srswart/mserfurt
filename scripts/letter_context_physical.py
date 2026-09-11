"""Opt-in frozen context mechanics; preparation never starts a physical attempt."""

import argparse
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from scripts import letter_context_variant_evidence as preflight
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json
from scribesim.pathguide.gesture_actions import ActionController


BASE = preflight.BASE.parent/'physical-validation-v1'
PREFLIGHT_SHA256 = '190cc9975bfb307ebd60b293cb7e62bef49a137bbaf5fe5a217b9f9b88c02cfb'
APPROVAL_SHA256 = '38f6ab9a0abcd85122fed3a1538d9a2ac97562310c5b057cb8481ca4cf59684f'
VERSION = 'letter-context-physical-validation-v1'
FLAGS = {'S2_accepted': False, 'real_accepted': False, 'context_training_allowed': False,
         'fitting_authorized': False, 'optimization_evaluations': 0}


def scope_matches(record):
    return all(type(record.get(key)) is type(value) and record[key] == value for key, value in FLAGS.items())


def identities():
    return {**preflight.identities(), **{str(path.relative_to(ROOT)): digest(path) for path in
        (Path(__file__), ROOT/'scripts/letter_context_physical_evidence.py')}}


def contract_record():
    approval_file = preflight.BASE/'budget-approval-001.json'
    if digest(approval_file) != APPROVAL_SHA256:
        raise ValueError('Changed owner budget approval')
    approval = preflight.foundation.read_json(approval_file)
    preflight.compare_previous(preflight.BASE/'snapshot-003', PREFLIGHT_SHA256)
    report = preflight.foundation.read_json(preflight.BASE/'snapshot-003/report.json')
    variants = preflight.variants
    fixtures = {row['id']: row for row in variants.fixtures()}
    programs = {object_digest(row['program']): row['program'] for row in report['geometry']}
    cases = []
    for row in report['planning']:
        fixture = fixtures[row['fixture']]
        cases.append({'id': f"{row['fixture']}-{row['program_sha256']}-{row['refinement']}",
            'fixture': fixture, 'program': programs[row['program_sha256']], 'refinement': row['refinement'],
            'timing_sha256': row['timing_sha256'], 'bundle_sha256': row['bundle_sha256'],
            'presentation': fixture['role'] == 'train_pairs' and row['refinement'] == 'base'})
    return {'version': VERSION, 'code_sha256': identities(), 'preflight_report_sha256': PREFLIGHT_SHA256,
        'approval_sha256': APPROVAL_SHA256, 'budget': approval,
        'candidate': preflight.foundation.read_json(preflight.foundation.placement.evaluation.SOURCE/'candidate.json'),
        'cases': cases, 'windows_mm': report['local_windows_mm'],
        'control_case_id': next(row['id'] for row in cases if row['fixture']['role'] == 'train_pairs' and row['refinement'] == 'base'),
        'refinements': preflight.foundation.placement.SPEC['refinements'],
        'criteria': preflight.foundation.placement.SPEC['mechanical_criteria'],
        'metric_dpi': 180, 'presentation_dpi': 900, 'physical_runs_per_seed': 488,
        'renders_per_seed_upper_bound': 1588, 'renders_per_case': 3,
        'control_render_allowance_per_process': 8,
        'visible_shift_mm': preflight.foundation.placement.evaluation.SPEC['visible_shift_mm'],
        'visible_shift_detection_loss': preflight.foundation.placement.AUTH['visible_shift_detection_loss'],
        'processes': [{'label': 'first', 'hashseed': '7'}, {'label': 'replay', 'hashseed': '839'}],
        'controls': ['identity', 'bounds', 'unknown-rule', 'per-word', 'geometry', 'ports', 'overlap',
            'frame', 'trace-owner', 'trace-lift', 'clock', 'tool', 'desired-as-actual', 'visible-shift', 'spacing-mislabel'],
        'style_reference': 'Historical H024 numerical style FAIL remains diagnostic; no new context target or preference score',
        'budget_accounting': 'All first/replay work and later P2b costs debit the same seed; no reset or retry',
        'inspection_policy': 'Raw reconstruction and stored-image reading; no controller or raster calls in read-only inspection',
        'sealed_holdout_access': False, **FLAGS}


def prepare():
    destination = BASE/'prepared-001'
    if destination.exists():
        raise FileExistsError('Immutable preparation already exists')
    preflight.load_inputs()
    contract = contract_record()
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/'contract.json', contract)
    return {'status': 'prepared_not_executed', 'contract_sha256': digest(destination/'contract.json'),
        'controller_executions': 0, 'raster_renders': 0, **FLAGS}


def load_contract(checksum):
    file = BASE/'prepared-001/contract.json'
    if not checksum or digest(file) != checksum:
        raise ValueError('External prepared contract pin required')
    contract = preflight.foundation.read_json(file)
    if object_digest(contract) != object_digest(contract_record()):
        raise ValueError('Changed physical contract, source or approval')
    return contract


def document_for(contract, case):
    if case not in contract['cases']:
        raise ValueError('Unfrozen physical case')
    return preflight.variants.compile_variant(contract['candidate'], case['fixture'], case['program'], case['refinement'])


def render_schedule(contract):
    schedule = []
    for case in contract['cases']:
        schedule.extend(['paint', 'paint', 'overlap_masks'])
        if case['presentation']:
            schedule.append('paint')
        if case['id'] == contract['control_case_id']:
            schedule.append('paint')
    return schedule


class Ledger:
    def __init__(self, file, maximum, seconds, *, clock=time.monotonic):
        if (type(maximum) is not int or not 0 < maximum <= 5000 or type(seconds) not in (float, int)
                or not math.isfinite(seconds) or not 0 < seconds <= 2700):
            raise ValueError('Invalid worker allowance')
        self.file, self.maximum, self.seconds, self.clock = Path(file), maximum, seconds, clock
        self.started, self.used, self.events = clock(), 0, []
        self.file.parent.mkdir(parents=True, exist_ok=True)
        with self.file.open('x') as stream:
            json.dump({'renders': 0, 'events': [], 'elapsed_seconds': 0}, stream)
        self.receipt()

    def receipt(self):
        elapsed = self.clock()-self.started
        if not math.isfinite(elapsed) or elapsed < 0:
            raise RuntimeError('Invalid monotonic clock')
        temporary = self.file.with_suffix('.pending')
        with temporary.open('w') as stream:
            json.dump({'renders': self.used, 'events': self.events, 'elapsed_seconds': elapsed,
                'maximum_renders': self.maximum, 'maximum_seconds': self.seconds}, stream, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.file)

    def check(self):
        self.receipt()
        if self.clock()-self.started >= self.seconds:
            raise RuntimeError('Combined time budget exhausted')

    def render(self, function, *args, **kwargs):
        self.check()
        if self.used >= self.maximum:
            raise RuntimeError('Combined render budget exhausted')
        self.used += 1
        event = {'ordinal': self.used, 'operation': function.__name__, 'status': 'reserved'}
        self.events.append(event)
        self.receipt()
        try:
            result = function(*args, **kwargs)
            event['status'] = 'complete'
        except BaseException:
            event['status'] = 'failed'
            raise
        finally:
            self.receipt()
        self.check()
        return result


def execute_raw(contract, case, document, budget):
    budget.check()
    bundle, timed = preflight.variants.prepare_plan(document, contract['candidate'], case['fixture'], case['refinement'])
    if object_digest(asdict(timed)) != case['timing_sha256'] or object_digest(asdict(bundle)) != case['bundle_sha256']:
        raise ValueError('Desired plan differs from cleared preflight')
    model = preflight.variants.source_model(contract['candidate'], case['fixture'], case['refinement'])
    engine = ActionController(model, execution_version='event-time-v2')
    observations, original_step = [], engine.step

    def observe(state, desired, *, dt):
        before_velocity = [state.vel_x_mm_s, state.vel_y_mm_s]
        before_position = [state.pos_x_mm, state.pos_y_mm]
        error = original_step(state, desired, dt=dt)
        velocity = [before_velocity[0]+state.acc_x_mm_s2*dt, before_velocity[1]+state.acc_y_mm_s2*dt]
        speed = math.hypot(*velocity)
        if speed > engine.dyn.max_speed:
            velocity = [value*engine.dyn.max_speed/speed for value in velocity]
        unconstrained = [position+(before+after)*dt/2 for position, before, after in zip(before_position, before_velocity, velocity)]
        observations.append({'velocity_before_mm_s': before_velocity,
            'velocity_mm_s': [state.vel_x_mm_s, state.vel_y_mm_s], 'unconstrained_mm': unconstrained,
            'projection_mm': math.dist(unconstrained, [state.pos_x_mm, state.pos_y_mm])})
        return error

    engine.step = observe
    step, interval = contract['refinements'][case['refinement']]
    executed = engine.follow_plan(bundle.plan, dt=interval, settle_time_s=0)
    budget.check()
    if len({len(executed.trajectory), len(executed.trajectory_plan_indices),
            len(executed.final_state.execution_trace), len(observations)}) != 1:
        raise ValueError('Truncated controller observations')
    trace = [{**event, **observation, 'owner': bundle.owners[index], 'plan_index': index}
        for event, observation, index in zip(executed.final_state.execution_trace, observations, executed.trajectory_plan_indices)]
    return {'document_sha256': object_digest(document), 'model_sha256': object_digest(model),
        'text': case['fixture']['text'], 'version': timed.version, 'tool': 'physical-edge-v1',
        'step_mm': step, 'dt_s': interval, 'plan': asdict(bundle.plan),
        'trace': trace, 'arrivals': timed.arrivals, 'corners': timed.corners}


def worker(checksum, directory, seed, label, maximum, seconds):
    from scripts import letter_context_physical_evidence as reader
    directory = Path(directory).resolve()
    if seed not in (7, 19, 41) or label not in ('first', 'replay') or directory != (BASE/'run-001'/f'seed-{seed}'/label).resolve():
        raise ValueError('Unfrozen worker destination or seed')
    directory.mkdir(parents=True, exist_ok=False)
    budget = Ledger(directory/'execution.json', maximum, seconds)
    record = {'seed': seed, 'status': 'blocked', 'cases': [], 'controller_executions': 0, **FLAGS}
    try:
        contract = load_contract(checksum)
        if digest(BASE/'run-001/contract.json') != checksum:
            raise ValueError('Attempt contract differs')
        permit = preflight.foundation.read_json(directory.parent/f'{label}-permit.json')
        if (permit != {'seed': seed, 'label': label, 'maximum': maximum, 'seconds': seconds, 'contract_sha256': checksum}
                or os.environ.get('PYTHONHASHSEED') != next(row['hashseed'] for row in contract['processes'] if row['label'] == label)):
            raise ValueError('Worker allowance differs from supervisor permit')
        np.random.seed(seed)
        comparisons = {}
        for case in contract['cases']:
            document = document_for(contract, case)
            case_dir = directory/case['id']
            case_dir.mkdir()
            write_json(case_dir/'document.json', document)
            write_json(case_dir/'attempt.json', {'case_id': case['id'], 'controller': 'reserved'})
            record['controller_executions'] += 1
            run = execute_raw(contract, case, document, budget)
            preflight.foundation.placement.evaluation.compressed(case_dir/'trace.json.gz', run)
            write_json(case_dir/'attempt.json', {'case_id': case['id'], 'controller': 'complete'})
            result, pixels = reader.measure_case(contract, case, document, run, budget, case_dir)
            group = (case['fixture']['id'], object_digest(case['program']))
            if case['refinement'] == 'base':
                comparisons[group] = run, pixels
            else:
                baseline, baseline_pixels = comparisons[group]
                result['comparison'] = reader.measurement.comparison(baseline, run, baseline_pixels, pixels)
                if case['refinement'] == list(contract['refinements'])[-1]:
                    del comparisons[group]
            result['passed'] = reader.case_pass(result, contract)
            write_json(case_dir/'measurement.json', result)
            record['cases'].append({'id': case['id'], 'passed': result['passed']})
            if case['id'] == contract['control_case_id']:
                record['controls'] = reader.controls(contract, case, document, run, pixels, budget, directory)
                write_json(directory/'controls.json', record['controls'])
            budget.check()
            if not result['passed']:
                raise ValueError('Physical mechanical failure: '+case['id'])
        if set(record.get('controls', {})) != set(contract['controls']) or not all(record['controls'].values()):
            raise ValueError('Negative controls failed or missing')
        if contract['code_sha256'] != identities():
            raise ValueError('Code changed during physical execution')
        record['status'] = 'pass'
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, IndexError) as error:
        record['reason'] = str(error)
    record['renders'] = budget.used
    budget.receipt()
    write_json(directory/'report.json', record)
    return record


def run(checksum):
    contract = load_contract(checksum)
    if list(BASE.glob('run-*')):
        raise FileExistsError('One immutable physical attempt only; no automatic retries')
    output = BASE/'run-001'
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'contract.json', contract)
    report = {'status': 'blocked', 'seeds': [], 'ledger': [], **FLAGS}
    try:
        for seed in contract['budget']['seeds']:
            started, used = time.monotonic(), 0
            for process in contract['processes']:
                remaining = 2700-(time.monotonic()-started)
                if remaining <= 0 or used >= 5000:
                    raise RuntimeError('Combined seed budget exhausted')
                directory = output/f'seed-{seed}'/process['label']
                write_json(directory.parent/f"{process['label']}-permit.json", {'seed': seed, 'label': process['label'],
                    'maximum': 5000-used, 'seconds': remaining, 'contract_sha256': checksum})
                outcome = None
                try:
                    outcome = subprocess.run([sys.executable, '-m', 'scripts.letter_context_physical',
                        '--worker', str(directory), '--contract-sha256', checksum, '--seed', str(seed),
                        '--label', process['label'], '--maximum', str(5000-used), '--seconds', str(remaining)],
                        cwd=ROOT, env={**os.environ, 'PYTHONHASHSEED': process['hashseed']},
                        capture_output=True, text=True, timeout=remaining)
                finally:
                    receipt = directory/'execution.json'
                    count = preflight.foundation.read_json(receipt)['renders'] if receipt.exists() else 0
                    used += count
                    report['ledger'].append({'seed': seed, 'process': process['label'], 'renders': count,
                        'cumulative_renders': used, 'cumulative_seconds': time.monotonic()-started})
                    write_json(output/'execution.json', {'ledger': report['ledger']})
                if outcome.returncode or not (directory/'report.json').exists():
                    raise RuntimeError('Worker failed; no retry')
                if preflight.foundation.read_json(directory/'report.json')['status'] != 'pass':
                    raise ValueError('Worker mechanical or evidence failure; retained without retry')
            first, replay = output/f'seed-{seed}/first', output/f'seed-{seed}/replay'
            if artifact_map(first, {'execution.json'}) != artifact_map(replay, {'execution.json'}):
                raise ValueError('Fresh-process replay differs')
            if used > 5000 or time.monotonic()-started > 2700:
                raise RuntimeError('Combined seed budget exhausted')
            report['ledger'][-1]['cumulative_seconds'] = time.monotonic()-started
            write_json(output/'execution.json', {'ledger': report['ledger']})
            report['seeds'].append({'seed': seed, 'replay_match': True})
        report['status'] = 'pass'
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
    report['artifacts'] = artifact_map(output, {'report.json', 'execution.json'})
    if report['ledger']:
        report['ledger'][-1]['cumulative_seconds'] = time.monotonic()-started
        if report['ledger'][-1]['cumulative_seconds'] > 2700:
            report.update(status='blocked', reason='Combined seed budget exhausted during artifact sealing')
        write_json(output/'execution.json', {'ledger': report['ledger']})
        report['artifacts']['execution.json'] = digest(output/'execution.json')
    write_json(output/'report.json', report)
    return report


def artifact_map(directory, excluded=()):
    return {str(file.relative_to(directory)): digest(file) for file in sorted(directory.rglob('*'))
        if file.is_file() and str(file.relative_to(directory)) not in excluded}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--run', action='store_true')
    mode.add_argument('--worker', type=Path)
    parser.add_argument('--contract-sha256')
    parser.add_argument('--seed', type=int)
    parser.add_argument('--label')
    parser.add_argument('--maximum', type=int)
    parser.add_argument('--seconds', type=float)
    args = parser.parse_args()
    result = prepare() if args.prepare else run(args.contract_sha256) if args.run else worker(
        args.contract_sha256, args.worker, args.seed, args.label, args.maximum, args.seconds)
    print(json.dumps({key: value for key, value in result.items() if key not in ('artifacts', 'cases')}, indent=2))


if __name__ == '__main__':
    main()
