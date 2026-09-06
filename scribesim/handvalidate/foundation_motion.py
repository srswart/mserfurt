"""Read-only, budgeted motion diagnosis and current-code primitive revalidation."""

import argparse
import copy
from dataclasses import asdict
import gzip
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageDraw

from scribesim.curriculum import stroke_learning as strokes
from scribesim.curriculum.gesture_learning import LOWER, LOWER_HASHES, BASE
from scribesim.evofit.stroke_gestures import gesture_guide, migrate_v1
from scribesim.evofit.stroke_language import language_guide, seed_language, validate_language
from scribesim.evofit.recovery import image_objective
from scribesim.handflow.controller import GuidedHandFlowController
from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.planning import build_track_plan
from scribesim.handvalidate.bridge import neutral_profile, paint_trajectory
from scribesim.handvalidate.gestures import _subdivide
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json
from scribesim.pathguide.gesture_actions import ActionController, action_bundle, code_identities
from scribesim.evo.nib_contact import ContactSample, VERSION


SPEC_PATH = BASE / 'foundation_repair/motion/spec-v2.json'
SPEC = json.loads(SPEC_PATH.read_text())


class Budget:
    def __init__(self, maximum=500, seconds=1800):
        if type(maximum) is not int or not 1 <= maximum <= 500:
            raise ValueError('Motion render budget must be 1..500')
        if type(seconds) not in (float, int) or not math.isfinite(seconds) or not 0 < seconds <= 1800:
            raise ValueError('Motion time budget must be within 1800 seconds')
        self.maximum, self.seconds = maximum, seconds
        self.started, self.used = time.monotonic(), 0

    def check(self):
        if time.monotonic() - self.started >= self.seconds:
            raise RuntimeError('Motion time budget exhausted')

    def render(self, operation, *args, **kwargs):
        self.check()
        if self.used >= self.maximum:
            raise RuntimeError('Motion render budget exhausted')
        self.used += 1
        result = operation(*args, **kwargs)
        self.check()
        return result


def load_historical_baseline(root=LOWER):
    root = Path(root)
    for name, checksum in LOWER_HASHES.items():
        if digest(root / name) != checksum:
            raise ValueError('Historical baseline identity mismatch')
    freeze = json.loads((root / 'freeze.json').read_text())
    report = json.loads((root / 'report.json').read_text())
    if report['freeze_sha256'] != object_digest(freeze) or freeze['limits'] != strokes.LIMITS:
        raise ValueError('Historical contract identity mismatch')
    for name, checksum in report['artifacts'].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path) != checksum:
            raise ValueError('Historical artifact identity mismatch')
    records = []
    for seed in freeze['seeds']:
        if (root / f'{seed}-first.json').read_bytes() != (root / f'{seed}-replay.json').read_bytes():
            raise ValueError('Historical replay identity mismatch')
        record = json.loads((root / f'{seed}-first.json').read_text())
        expected = copy.deepcopy(freeze['initial'])
        for name, primitive in record['model']['primitives'].items():
            expected['primitives'][name]['cubics'] = primitive['cubics']
        if expected != record['model'] or record['model_sha256'] != object_digest(record['model']):
            raise ValueError('Historical primitive lineage identity mismatch')
        validate_language(record['model'])
        records.append(record)
    selected = min(records, key=lambda row: row['metrics']['development']['after'])
    candidate = json.loads((root / 'candidate.json').read_text())
    if selected['model'] != candidate or selected['seed'] != report['selected_seed']:
        raise ValueError('Historical selection identity mismatch')
    return {'freeze': freeze, 'candidate': candidate, 'records': records,
            'historical_sha256': dict(LOWER_HASHES),
            'historical_code_sha256': freeze['code_sha256']}


def identities():
    names = ('scribesim/handvalidate/foundation_motion.py', 'scribesim/curriculum/stroke_learning.py',
             'scribesim/curriculum/gesture_learning.py', 'scribesim/handvalidate/gestures.py',
             'scribesim/evofit/recovery.py', 'scribesim/evofit/repertoire.py',
             'scribesim/pathguide/repertoire.py', 'scribesim/hand/profile.py',
             'scribesim/handvalidate/specimen.py', 'scribesim/render/nib.py')
    return {**code_identities(), **{name: digest(ROOT / name) for name in names}}


def fixtures():
    seed = migrate_v1(seed_language())
    seed['sampling'] = 'gesture-arc-v2'
    saved_path = BASE / SPEC['saved_candidate']
    if digest(saved_path) != SPEC['saved_candidate_sha256']:
        raise ValueError('Saved failure model identity mismatch')
    saved = json.loads(saved_path.read_text())
    overlap = copy.deepcopy(seed)
    overlap['recipes']['u']['gestures'][1].update(offset=[0, 0], overlap_with=[0])
    return [('continuous', 'i', seed), ('separated', 'u', seed), ('coincident-overlap', 'u', overlap),
            ('word-space', 'i u', seed), ('saved-u', 'u', saved), ('saved-i-u', 'i u', saved)]


def execute(model, text, *, step, dt, version, budget, physical=False, subdivision=False):
    if version == 'event-time-v2':
        model = copy.deepcopy(model)
        model['sampling'] = 'gesture-arc-v3'
    if subdivision:
        model = _subdivide(model)
    if physical:
        bundle = action_bundle(text, model, step_mm=step)
        plan, owners = bundle.plan, bundle.owners
        engine = ActionController(model, execution_version=version)
        playback = [ContactSample(sample.x_mm, sample.y_mm, sample.contact, .45, sample.pressure,
                                 sample.nib_angle_deg, sample.edge_start, sample.edge_end)
                    for sample in plan.samples]
    else:
        bundle = gesture_guide(text, model, step_mm=step)
        plan, owners = build_track_plan(bundle.guide, base_speed_mm_s=12), bundle.metadata['owners']
        engine = GuidedHandFlowController(neutral_profile(model), repertoire_controls=RepertoireControls(),
                                          execution_version=version)
        from scribesim.handvalidate.model import TrajectorySample
        playback = [TrajectorySample(sample.x_mm, sample.y_mm, sample.contact, .45,
                                     sample.pressure, sample.nib_angle_deg) for sample in plan.samples]
    observations = []
    original = engine.step

    def observe(state, desired, *, dt):
        before = [state.vel_x_mm_s, state.vel_y_mm_s]
        position = [state.pos_x_mm, state.pos_y_mm]
        error = original(state, desired, dt=dt)
        velocity = [before[0] + state.acc_x_mm_s2 * dt, before[1] + state.acc_y_mm_s2 * dt]
        speed = math.hypot(*velocity)
        if speed > engine.dyn.max_speed:
            velocity = [value * engine.dyn.max_speed / speed for value in velocity]
        unconstrained = [value + (prior + rate) * dt / 2 for value, prior, rate in zip(position, before, velocity)] if version == 'event-time-v2' else [value + rate * dt for value, rate in zip(position, velocity)]
        observations.append({'velocity_before_mm_s': before, 'velocity_mm_s': [state.vel_x_mm_s, state.vel_y_mm_s],
                             'unconstrained_mm': unconstrained,
                             'projection_mm': math.dist(unconstrained, [state.pos_x_mm, state.pos_y_mm])})
        return error

    engine.step = observe
    result = engine.follow_plan(plan, dt=dt, settle_time_s=0)
    rendered = {label: budget.render(paint_trajectory, trajectory, SPEC['frame_mm'], dpi=SPEC['dpi'],
                                     contact_version=VERSION if physical else None)
                for label, trajectory in (('desired', playback), ('actual', result.trajectory))}
    trace = []
    contact_groups = []
    errors = 0
    for point, index, execution, observed in zip(result.trajectory, result.trajectory_plan_indices,
                                                result.final_state.execution_trace, observations):
        owner = owners[index]
        errors += int(point.contact != plan.samples[index].contact or
                      (point.contact and owner['kind'] != 'stroke'))
        row = {**execution, **observed, 'owner': owner, 'plan_index': index}
        if point.contact:
            key = owner['gesture_occurrence_id']
            if not contact_groups or contact_groups[-1]['owner'] != key:
                contact_groups.append({'owner': key, 'first': row, 'last': row})
            contact_groups[-1]['last'] = row
        trace.append(row)
    required = list(dict.fromkeys(owner['gesture_occurrence_id'] for owner in owners if owner['kind'] == 'stroke'))
    errors += int([group['owner'] for group in contact_groups] != required)
    durations = [following.t_s - prior.t_s for prior, following in zip(plan.samples, plan.samples[1:])]
    metrics = {'planned_time_s': plan.total_time_s, 'executed_time_s': result.final_state.time_s,
               'floor_excess_s': sum(max(dt, duration) - duration for duration in durations),
               'rounded_largest_step_s': max((max(dt, duration) / max(1, round(max(dt, duration) / dt))
                                            for duration in durations), default=0),
               'time_error_s': abs(result.final_state.time_s - plan.total_time_s),
               'max_projection_mm': max(row['projection_mm'] for row in trace),
               'corridor_mm': max((math.dist(row['to_mm'], row['desired_mm']) for row in trace if row['contact']), default=0),
               'image_loss': strokes.stroke_loss(rendered['desired'], rendered['actual']), 'owner_errors': errors}
    return {'model_sha256': object_digest(model), 'text': text, 'version': version, 'step_mm': step, 'dt_s': dt,
            'tool': VERSION if physical else 'legacy-full-edge', 'plan': asdict(plan), 'metrics': metrics,
            'groups': contact_groups, 'trace': trace, 'images': rendered}


def compare(first, second):
    if [group['owner'] for group in first['groups']] != [group['owner'] for group in second['groups']]:
        return {'owner_match': False, 'pass': False}
    pairs = [(before[label], after[label]) for before, after in zip(first['groups'], second['groups'])
             for label in ('first', 'last')]
    endpoint = max(math.dist(before['to_mm'], after['to_mm']) for before, after in pairs)
    timing = max(abs(before['time_s'] - after['time_s']) for before, after in pairs)
    loss = strokes.stroke_loss(first['images']['actual'], second['images']['actual'])
    return {'owner_match': True, 'endpoint_mm': endpoint, 'event_time_s': timing, 'image_loss': loss,
            'pass': endpoint <= SPEC['criteria']['endpoint_mm'] and timing <= SPEC['criteria']['event_time_s']
                    and loss <= SPEC['criteria']['convergence_loss']}


def revalidate_baseline(budget, *, root=LOWER, version='event-time-v2'):
    baseline = load_historical_baseline(root)
    freeze = baseline['freeze']
    initial, candidate, samples = freeze['initial'], baseline['candidate'], freeze['samples']
    before, targets, rows, failures = {}, {}, [], []
    for sample in samples:
        targets[sample['id']] = budget.render(strokes.render_exercise, freeze['target'], sample)
        before[sample['id']] = strokes.stroke_loss(targets[sample['id']], budget.render(strokes.render_exercise, initial, sample))
    for record in baseline['records']:
        after = {sample['id']: strokes.stroke_loss(targets[sample['id']],
                 budget.render(strokes.render_exercise, record['model'], sample)) for sample in samples}
        metrics = {split: {label: float(np.mean([values[sample['id']] for sample in samples if sample['split'] == split]))
                          for label, values in (('before', before), ('after', after))}
                   for split in ('train', 'development', 'test')}
        if metrics != record['metrics']:
            failures.append(f"seed-{record['seed']}:current_nominal_changed")
        if metrics['test']['after'] >= metrics['test']['before'] * strokes.LIMITS['heldout_improvement_ratio']:
            failures.append(f"seed-{record['seed']}:original_transfer")
        families = {}
        for name in initial['primitives']:
            selected = [sample['id'] for sample in samples if sample['split'] == 'test' and name in sample['primitives']]
            families[name] = {'before': float(np.mean([before[key] for key in selected])),
                              'after': float(np.mean([after[key] for key in selected]))}
            movement = sum(math.dist(first, second) for prior, learned in
                           zip(initial['primitives'][name]['cubics'], record['model']['primitives'][name]['cubics'])
                           for first, second in zip(prior, learned))
            if movement < strokes.LIMITS['minimum_parameter_change']:
                failures.append(f"seed-{record['seed']}:{name}:inactive_original_fit")
        rows.append({'seed': record['seed'], 'metrics': metrics, 'per_family': families})
    actual = {}
    panels = []
    for name in initial['primitives']:
        sample = next(sample for sample in samples if sample['id'] == name + '-base')
        model, text = strokes.exercise_model(candidate, sample)
        bundle = language_guide(text, model, step_mm=.025)
        engine = GuidedHandFlowController(neutral_profile(model), repertoire_controls=RepertoireControls(),
                                          execution_version=version)
        result = engine.simulate_guide(bundle.guide, base_speed_mm_s=12, dt=.002, settle_time_s=0)
        frame = bundle.metadata['frame_mm']
        nominal = budget.render(strokes.render_exercise, candidate, {**sample, 'frame': frame})
        image = budget.render(paint_trajectory, result.trajectory, frame, dpi=strokes.DPI)
        mask = np.where(np.asarray(Image.fromarray(nominal).convert('L')) < 180, 255, 0).astype(np.uint8)
        metrics = {'image_loss': image_objective(nominal, mask, image)['total'],
                   'corridor_mm': max((math.dist(row['to_mm'], row['desired_mm'])
                                      for row in result.final_state.execution_trace if row['contact']), default=0),
                   'contact_errors': sum(point.contact != result.plan.samples[index].contact
                                         for point, index in zip(result.trajectory, result.trajectory_plan_indices))}
        if metrics['image_loss'] > .35 or metrics['corridor_mm'] > .25 or metrics['contact_errors']:
            failures.append(name + ':actual_baseline')
        actual[name] = {'metrics': metrics, 'trace': result.final_state.execution_trace,
                        'owners': [bundle.metadata['owners'][index] for index in result.trajectory_plan_indices]}
        panels.extend([(name + ' frozen nominal', nominal), (name + ' actual ' + version, image)])
    return {'status': 'fail' if failures else 'pass', 'reasons': failures, 'scope': 'current synthetic six-primitive baseline only',
            'execution_version': version, 'historical_sha256': baseline['historical_sha256'],
            'historical_code_sha256': baseline['historical_code_sha256'], 'current_code_sha256': identities(),
            'candidate_sha256': object_digest(candidate), 'rows': rows, 'actual': actual, 'panels': panels,
            'optimization_evaluations': 0, 'real_hand_accepted': False}


def decide_motion(checks, baseline):
    required = {f'{name}:{label}:{metric}' for name in SPEC['fixture_families']
                for label in ('base', 'arc', 'time', 'subdivision')
                for metric in ('time', 'corridor', 'image', 'ownership', 'no_projection')}
    required.update(f'{name}:{label}:convergence' for name in SPEC['fixture_families']
                    for label in ('arc', 'time', 'subdivision'))
    required.update(('physical:arc', 'physical:time', 'physical:tracking'))
    passed = set(checks) == required and all(value is True for value in checks.values())
    current_baseline = (baseline.get('status') == 'pass' and baseline.get('current_code_sha256') == identities()
                        and baseline.get('historical_sha256') == LOWER_HASHES)
    return {'status': 'pass' if passed and current_baseline else 'fail',
            'failed_checks': sorted(key for key, value in checks.items() if value is not True),
            'complete_check_set': set(checks) == required,
            'baseline_admitted': passed and current_baseline,
            'primitive_training_permitted': passed and current_baseline,
            'S1_action_accepted': False, 'real_hand_accepted': False}


def panel(path, tiles):
    output = Image.new('RGB', (1200, 280 * math.ceil(len(tiles) / 4)), 'white')
    draw = ImageDraw.Draw(output)
    scale = min(290 / max(pixels.shape[1] for _, pixels in tiles),
                240 / max(pixels.shape[0] for _, pixels in tiles))
    for index, (label, pixels) in enumerate(tiles):
        left, top = index % 4 * 300, index // 4 * 280
        draw.text((left + 4, top + 4), label, fill='black')
        image = Image.fromarray(pixels)
        image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.NEAREST)
        output.paste(image, (left + 4, top + 30))
    output.save(path)


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError('Use a new immutable motion output directory')
    budget = Budget()
    models = fixtures()
    write_json(output / 'freeze.json', {'spec': SPEC, 'spec_sha256': digest(SPEC_PATH), 'code_sha256': identities(),
                                        'fixtures': models, 'profile': asdict(neutral_profile(models[0][2]))})
    traces, rows, checks, tiles = {}, [], {}, []
    baseline = {'status': 'blocked', 'reasons': ['not executed']}
    try:
        for name, text, model in models:
            executions = {}
            for version in ('legacy-v1', 'event-time-v2'):
                runs = {}
                for label, step, dt, subdivision in [('base', .025, .002, False), ('arc', .0125, .002, False),
                                                      ('time', .025, .001, False), ('subdivision', .025, .002, True)]:
                    runs[label] = execute(model, text, step=step, dt=dt, version=version, budget=budget,
                                          subdivision=subdivision)
                comparisons = {label: compare(runs['base'], runs[label]) for label in ('arc', 'time', 'subdivision')}
                rows.append({'fixture': name, 'version': version, 'metrics': runs['base']['metrics'],
                             'comparisons': comparisons})
                if version == 'event-time-v2':
                    for label, result in runs.items():
                        metrics = result['metrics']
                        checks[f'{name}:{label}:time'] = metrics['time_error_s'] <= SPEC['criteria']['duration_s']
                        checks[f'{name}:{label}:corridor'] = metrics['corridor_mm'] <= .25
                        checks[f'{name}:{label}:image'] = metrics['image_loss'] <= .35
                        checks[f'{name}:{label}:ownership'] = metrics['owner_errors'] == 0
                        checks[f'{name}:{label}:no_projection'] = metrics['max_projection_mm'] <= 1e-12
                    for label, comparison in comparisons.items():
                        checks[f'{name}:{label}:convergence'] = comparison['pass']
                executions[version] = runs
            tiles.extend([(name + ' desired', executions['event-time-v2']['base']['images']['desired']),
                          (name + ' legacy actual', executions['legacy-v1']['base']['images']['actual']),
                          (name + ' timed actual', executions['event-time-v2']['base']['images']['actual']),
                          (name + ' refined actual', executions['event-time-v2']['time']['images']['actual'])])
            traces[name] = {version: {label: {key: value for key, value in result.items() if key != 'images'}
                                     for label, result in runs.items()} for version, runs in executions.items()}
        physical = {}
        model = models[-1][2]
        for label, step, dt in (('base', .025, .002), ('arc', .0125, .002), ('time', .025, .001)):
            physical[label] = execute(model, 'i u', step=step, dt=dt, version='event-time-v2', budget=budget, physical=True)
        for label in ('arc', 'time'):
            checks['physical:' + label] = compare(physical['base'], physical[label])['pass']
        checks['physical:tracking'] = all(result['metrics']['corridor_mm'] <= .25 and result['metrics']['owner_errors'] == 0
                                           and result['metrics']['image_loss'] <= .35 for result in physical.values())
        traces['physical-fixed'] = {label: {key: value for key, value in result.items() if key != 'images'}
                                     for label, result in physical.items()}
        budget.render(panel, output / 'comparison.png', tiles)
        baseline = revalidate_baseline(budget)
        budget.render(panel, output / 'baseline.png', baseline.pop('panels'))
    except RuntimeError as error:
        checks['budget'] = False
        baseline = {'status': 'blocked', 'reasons': [str(error)]}
    write_json(output / 'baseline.json', baseline)
    (output / 'traces.json.gz').write_bytes(gzip.compress(json.dumps(traces, sort_keys=True).encode(), mtime=0))
    decision = decide_motion(checks, baseline)
    report = {'scope': SPEC['scope'], 'decision': decision, 'checks': checks, 'rows': rows,
              'renders': budget.used, 'max_renders': budget.maximum, 'optimization_evaluations': 0,
              'attempt': 1, 'revision': 1, 'code_sha256': identities(), 'spec_sha256': digest(SPEC_PATH),
              'artifacts': {path.name: digest(path) for path in sorted(output.iterdir()) if path.is_file()}}
    write_json(output / 'report.json', report)
    write_json(output / 'execution.json', {'elapsed_seconds': time.monotonic() - budget.started, 'renders': budget.used})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output)['decision'], indent=2))


if __name__ == '__main__':
    main()
