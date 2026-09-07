"""Bounded current-mode motion and independent frozen-candidate reevaluation."""

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image

from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handflow import curve_tangents
from scribesim.handvalidate import foundation_primitives as evaluation, tangent_motion as runtime
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = evaluation.BASE.parent / 'tangent_evaluation'
SPEC_PATH = BASE / 'spec-v2.json'
SPEC = json.loads(SPEC_PATH.read_text())
STAGE = 'S1-foundation-primitives-tangent-v1'


def identities():
    paths = (Path(__file__), Path(runtime.__file__), Path(curve_tangents.__file__), SPEC_PATH)
    return {**evaluation.identities(), **{str(path.relative_to(ROOT)): digest(path) for path in paths}}


def load_inputs():
    prior = evaluation.BASE / 'run-001'
    if digest(prior / 'S1-primitives.json') != SPEC['prior_report_sha256']:
        raise ValueError('Unfrozen prior independent failure')
    report = json.loads((prior / 'S1-primitives.json').read_text())
    evaluation.verify_artifacts(prior, report['artifacts'])
    current = evaluation.identities()
    changed = {name for name, checksum in report['code_sha256'].items() if current.get(name) != checksum}
    if set(current) != set(report['code_sha256']) or not changed <= set(SPEC['allowed_changed_historical_code']):
        raise ValueError('Unapproved historical execution/source compatibility change')
    source = evaluation.load_inputs()
    source['compatibility'] = {'prior_report_sha256': SPEC['prior_report_sha256'], 'changed_historical_code': sorted(changed),
                                'learning_measurement_code_unchanged': True, 'fresh_new_mode_proofs_required': True}
    return source


def stripped(run):
    return {key: value for key, value in run.items() if key != 'images'}


def baseline_probe(family, language, sample):
    if sample['primitives'] != [family] or sample['offset'] != [0, 0]:
        raise ValueError('Exactly one origin-aligned baseline family required')
    model = evaluation.probe(evaluation.contract.initial_model(), {'topology': [family], 'scale': sample['scale']})
    for name, primitive in language['primitives'].items():
        if model['primitives'].get(name) != primitive:
            raise ValueError('Original baseline primitive table differs')
    for key in ('x_height_mm', 'nib_width_mm', 'nib_angle_deg'):
        if language[key] != model[key]:
            raise ValueError('Original baseline tool differs')
    original = evaluation.motion.compile_text('i', language)['strokes']
    compiled = compile_gestures('i', model)['strokes']
    if len(original) != 1 or len(compiled) != 1 or any(original[0][key] != compiled[0][key] for key in
            ('primitive', 'cubics', 'span', 'transition', 'scale', 'rotation_deg', 'offset')):
        raise ValueError('Diagnostic probe must preserve exact original compiled geometry and ownership')
    return model


def prior_usage():
    prior = BASE / 'run-001'
    if (digest(prior / 'S1-primitives.json') != SPEC['prior_attempt_report_sha256']
            or digest(prior / 'execution.json') != SPEC['prior_attempt_execution_sha256']):
        raise ValueError('Changed retained attempt accounting')
    report = json.loads((prior / 'S1-primitives.json').read_text())
    execution = json.loads((prior / 'execution.json').read_text())
    evaluation.verify_artifacts(prior, report['artifacts'])
    return {seed: {'renders': sum(row['renders'] for row in execution['ledger'] if row['seed'] == seed),
                   'seconds': max(row['cumulative_seed_seconds'] for row in execution['ledger'] if row['seed'] == seed)}
            for seed in SPEC['seeds']}


def refinements(model, text, budget, *, physical=False):
    result = {}
    for refinement in evaluation.SPEC['refinements']:
        label = refinement['id']
        if physical and label == 'subdivision':
            continue
        variant = evaluation.subdivide(model) if label == 'subdivision' else model
        result[label] = runtime.execute(variant, text, step=refinement['step'], dt=refinement['dt'], budget=budget, physical=physical)
    return result


def summarize_runs(runs):
    return {'runs': {label: {'metrics': run['metrics'], 'version': run['version']} for label, run in runs.items()},
            'comparisons': {label: evaluation.motion.compare(runs['base'], run) for label, run in runs.items() if label != 'base'}}


def comparisons_pass(comparisons, labels):
    return set(comparisons) == set(labels) and all(row['owner_match'] is True and
        all(math.isfinite(row[key]) and 0 <= row[key] <= maximum for key, maximum in
            (('endpoint_mm', .01), ('event_time_s', .0001), ('image_loss', .03))) for row in comparisons.values())


def recheck_baseline(baseline):
    motion = evaluation.motion
    required = set(motion.SPEC['fixture_families']) | {'old-six:' + name for name in evaluation.contract.SPEC['baseline']['primitives']} | {'physical-fixed'}
    if (set(baseline['proofs']) != required or baseline['original_status'] != 'pass'
            or baseline['original_code_sha256'] != motion.identities() or baseline['original_historical_sha256'] != motion.LOWER_HASHES):
        return False
    for name, row in baseline['proofs'].items():
        expected = {'base', 'arc', 'time'} if name == 'physical-fixed' else {'base', 'arc', 'time', 'subdivision'}
        if set(row['runs']) != expected or not comparisons_pass(row['comparisons'], expected - {'base'}):
            return False
        if not all(run['version'] == runtime.VERSION and runtime.passes(run) for run in row['runs'].values()):
            return False
        if name.startswith('old-six:') and (not 0 <= row['nominal_actual_loss'] <= .35 or not row['compiled_geometry_equal']):
            return False
    return True


def refresh_baseline(directory, budget):
    motion = evaluation.motion
    original = motion.revalidate_baseline(budget)
    original.pop('panels')
    evaluation.compressed(directory / 'original-baseline.json.gz', original)
    if original['status'] != 'pass':
        raise ValueError('Fresh original baseline failed')
    baseline = {'original_status': original['status'], 'original_code_sha256': original['current_code_sha256'],
                'original_historical_sha256': original['historical_sha256'], 'candidate_sha256': original['candidate_sha256'], 'proofs': {}}
    traces, panels = {}, []
    frozen = motion.load_historical_baseline()
    models = motion.fixtures()
    for name in frozen['candidate']['primitives']:
        sample = next(row for row in frozen['freeze']['samples'] if row['id'] == name + '-base')
        language, text = motion.strokes.exercise_model(frozen['candidate'], sample)
        model = baseline_probe(name, language, sample)
        runs = refinements(model, text, budget)
        row = summarize_runs(runs)
        row.update(compiled_geometry_equal=True, original_exercise_sha256=object_digest(language), probe_sha256=object_digest(model))
        nominal = budget.render(motion.strokes.render_exercise, frozen['candidate'], {**sample, 'frame': motion.SPEC['frame_mm'], 'dpi': 180})
        mask = np.where(np.asarray(Image.fromarray(nominal).convert('L')) < 180, 255, 0).astype(np.uint8)
        row['nominal_actual_loss'] = motion.image_objective(nominal, mask, runs['base']['images']['actual'])['total']
        baseline['proofs']['old-six:' + name] = row
        traces['old-six:' + name] = {label: stripped(run) for label, run in runs.items()}
        paths = [evaluation.learning._trajectory(runs['base'], kind) for kind in ('desired', 'actual')]
        panels.extend((name + ' | ' + kind, budget.render(evaluation.measurement.paint, path, dpi=900)) for kind, path in zip(('sampled', 'actual'), paths))
    for name, text, model in models:
        runs = refinements(model, text, budget)
        baseline['proofs'][name] = summarize_runs(runs)
        traces[name] = {label: stripped(run) for label, run in runs.items()}
    physical = refinements(models[-1][2], 'i u', budget, physical=True)
    baseline['proofs']['physical-fixed'] = summarize_runs(physical)
    traces['physical-fixed'] = {label: stripped(run) for label, run in physical.items()}
    evaluation.compressed(directory / 'motion-traces.json.gz', traces)
    budget.render(motion.panel, directory / 'original-six-gallery.png', panels)
    baseline['passed'] = recheck_baseline(baseline)
    write_json(directory / 'motion-baseline.json', baseline)
    return baseline


def recheck_controls(controls):
    if set(controls) != set(evaluation.CONTROL_IDS) or not all(row['detected'] is True for row in controls.values()):
        return False
    for name in ('wrong-port', 'wrong-direction'):
        if set(controls[name]['families']) != set(evaluation.contract.SPEC['new_families']) or not all(controls[name]['families'].values()):
            return False
    for name in ('detached-geometry', 'hidden-lift', 'extra-contributor', 'painted-air-connector'):
        if not controls[name]['unmodified_pass'] or controls[name]['audit']['errors'] <= 0:
            return False
    if controls['painted-air-connector']['air_samples'] <= 0:
        return False
    local = controls['erased-counter']['local_controls']
    return all(0 <= local[name]['baseline_local_ink_fraction'] <= .01 < local[name]['local_ink_fraction'] <= 1
               for name in ('hidden_connector', 'overbuilt_terminal', 'erased_counter'))


def complete(record, baseline):
    return (record['execution_version'] == runtime.VERSION and recheck_baseline(baseline)
            and evaluation.decide_seed(record['fixtures'], record['controls'], True)
            and all(row['execution_version'] == runtime.VERSION and evaluation.recheck_fixture(row) for row in record['fixtures'])
            and recheck_controls(record['controls']))


def worker(directory, seed, maximum, seconds):
    budget = evaluation.learning.Budget(maximum, seconds)
    directory.mkdir(parents=True, exist_ok=False)
    record = {'seed': seed, 'status': 'blocked', 'execution_version': runtime.VERSION, 'fixtures': [], 'controls': {}, 'optimization_evaluations': 0}
    try:
        source = load_inputs()
        candidate = source['seeds'][seed]['candidate']
        record['candidate_sha256'] = object_digest(candidate)
        record['compatibility'] = source['compatibility']
        (directory / 'candidate.json').write_bytes((source['seeds'][seed]['directory'] / 'candidate.json').read_bytes())
        baseline = refresh_baseline(directory, budget)
        if not baseline['passed']:
            raise ValueError('New-mode baseline or required motion refinements failed')
        sheets, traces = [], {}
        for fixture in evaluation.FIXTURES:
            row, runs, tiles = evaluation.evaluate_fixture(candidate, fixture, budget, directory, version=runtime.VERSION)
            if not all(run['version'] == runtime.VERSION for run in runs.values()):
                raise ValueError('Unexpected legacy candidate execution')
            row['execution_version'] = runtime.VERSION
            row['passed'] = row['passed'] and evaluation.recheck_fixture(row)
            record['fixtures'].append(row)
            write_json(directory / (fixture['id'] + '-metrics.json'), row)
            traces[fixture['id']] = {label: stripped(run) for label, run in runs.items()}
            sheets.append((fixture['id'] + (' | PASS' if row['passed'] else ' | FAIL'), tiles))
        evaluation.compressed(directory / 'traces.json.gz', traces)
        budget.render(evaluation.learning._sheet, directory / 'practice-sheet.png', sheets)
        record['controls'] = evaluation.controls(candidate, budget, directory, version=runtime.VERSION)
        record['historical_controls'] = source['historical_controls']
        record['status'] = 'pass' if complete(record, baseline) else 'fail'
        budget.check()
    except (ValueError, RuntimeError, KeyError) as error:
        record['status'], record['reason'] = 'blocked', str(error)
    record['renders'] = budget.used
    write_json(directory / 'report.json', record)
    write_json(directory / 'execution.json', {'renders': budget.used, 'elapsed_seconds': time.monotonic() - budget.started})
    return record


def build(output):
    started = time.monotonic()
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new immutable tangent evaluation directory')
    report = {'stage': STAGE, 'execution_version': runtime.VERSION, 'status': 'blocked', 'S1_accepted': False,
              'gesture_training_permitted': False, 'actions_accepted': False, 'letters_accepted': False, 'real_hand_accepted': False,
              'code_sha256': identities(), 'renders': 0, 'optimization_evaluations': 0, 'seeds': [], 'revision': SPEC['revision'],
              'missing_inventory': evaluation.SPEC['missing_inventory']}
    write_json(output / 'freeze.json', {'spec': SPEC, 'primitive_criteria': evaluation.SPEC, 'motion_criteria': evaluation.motion.SPEC,
                                        'code_sha256': identities(), 'prior_report_sha256': SPEC['prior_report_sha256']})
    ledger = []
    try:
        source = load_inputs()
        prior = prior_usage()
        report['prior_renders'] = sum(row['renders'] for row in prior.values())
        report['supported_families'] = sorted(source['initial']['primitives'])
        report['compatibility'] = source['compatibility']
        for seed in SPEC['seeds']:
            if seed != SPEC['seeds'][0]:
                started = time.monotonic()
            used, records = prior[seed]['renders'], []
            for label, hashseed in (('first', '0'), ('replay', '839')):
                remaining = SPEC['max_seconds_per_seed_including_replay'] - prior[seed]['seconds'] - (time.monotonic() - started)
                if remaining <= 0 or used >= SPEC['max_renders_per_seed_including_replay']:
                    raise RuntimeError('Shared first/replay allowance exhausted')
                directory = output / f'seed-{seed}' / label
                command = [sys.executable, '-m', 'scribesim.handvalidate.tangent_evaluation', '--output', str(directory),
                           '--worker-seed', str(seed), '--maximum', str(SPEC['max_renders_per_seed_including_replay'] - used), '--seconds', str(remaining)]
                process = subprocess.run(command, cwd=ROOT, env={**os.environ, 'PYTHONHASHSEED': hashseed}, capture_output=True, text=True, timeout=remaining)
                if process.returncode:
                    raise RuntimeError('Worker accounting incomplete: ' + process.stderr[-2000:])
                record = json.loads((directory / 'report.json').read_text())
                used += record['renders']
                report['renders'] += record['renders']
                records.append(record)
                ledger.append({'seed': seed, 'process': label, 'renders': record['renders'], 'cumulative_seed_renders': used,
                               'cumulative_seed_seconds': prior[seed]['seconds'] + time.monotonic() - started})
            matching = evaluation.manifest(output / f'seed-{seed}/first') == evaluation.manifest(output / f'seed-{seed}/replay')
            within = used <= SPEC['max_renders_per_seed_including_replay'] and prior[seed]['seconds'] + time.monotonic() - started <= SPEC['max_seconds_per_seed_including_replay']
            report['seeds'].append({'seed': seed, 'replay_match': matching, 'budget_pass': within, 'renders': used,
                                    'attempt_renders': used - prior[seed]['renders'],
                                    'candidate_sha256': records[0].get('candidate_sha256'),
                                    'passed': matching and within and all(row['status'] == 'pass' for row in records)})
        accepted = len(report['seeds']) == 3 and all(row['passed'] for row in report['seeds'])
        report.update(status='pass' if accepted else 'fail', S1_accepted=accepted, gesture_training_permitted=accepted)
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
    report['cumulative_renders'] = report.get('prior_renders', 0) + report['renders']
    report['artifacts'] = evaluation.manifest(output)
    write_json(output / 'S1-primitives.json', report)
    write_json(output / 'execution.json', {'ledger': ledger, 'renders': report['renders'], 'prior_renders': report.get('prior_renders', 0),
                                          'cumulative_renders': report['cumulative_renders'], 'optimization_evaluations': 0})
    return report


def require_readiness(directory, *, expected_report_sha256, required_families):
    directory = Path(directory)
    try:
        if digest(directory / 'S1-primitives.json') != expected_report_sha256:
            raise ValueError('Consumer must pin the independent tangent report')
        report = json.loads((directory / 'S1-primitives.json').read_text())
        if report['stage'] != STAGE or report['execution_version'] != runtime.VERSION or report['status'] != 'pass' or report['code_sha256'] != identities():
            raise ValueError('Stale, failed or wrong-mode S1 extension')
        source = load_inputs()
        evaluation.verify_artifacts(directory, report['artifacts'])
        if not required_families or not set(required_families) <= set(source['initial']['primitives']):
            raise ValueError('Unsupported required primitive inventory')
        if not report['S1_accepted'] or not report['gesture_training_permitted'] or [row['seed'] for row in report['seeds']] != SPEC['seeds']:
            raise ValueError('Incomplete tangent acceptance')
        for row in report['seeds']:
            seed = row['seed']
            first, replay = directory / f'seed-{seed}/first', directory / f'seed-{seed}/replay'
            if not row['budget_pass'] or row['renders'] > SPEC['max_renders_per_seed_including_replay'] or evaluation.manifest(first) != evaluation.manifest(replay):
                raise ValueError('Missing replay or budget proof')
            record = json.loads((first / 'report.json').read_text())
            baseline = json.loads((first / 'motion-baseline.json').read_text())
            if record['candidate_sha256'] != object_digest(source['seeds'][seed]['candidate']) or not complete(record, baseline):
                raise ValueError('Required current-mode numeric proof failed')
        return {'stage': STAGE, 'report_sha256': expected_report_sha256, 'execution_version': runtime.VERSION,
                'required_families': sorted(set(required_families)), 'gesture_training_permitted': True,
                'scope': 'synthetic fixed-tool shared gestures using curve-tangent-v1 only'}
    except (KeyError, TypeError, OSError) as error:
        raise ValueError('Incomplete tangent readiness evidence') from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker-seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args()
    result = build(args.output) if args.worker_seed is None else worker(args.output, args.worker_seed, args.maximum, args.seconds)
    print(json.dumps({key: result[key] for key in ('status', 'renders', 'optimization_evaluations')}))


if __name__ == '__main__':
    main()
