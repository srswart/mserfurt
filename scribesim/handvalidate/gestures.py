"""Independent, read-only evaluation of frozen shared construction checkpoints."""

import argparse
import copy
import gzip
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

from scribesim.curriculum import gesture_learning as learning
from scribesim.curriculum.stroke_learning import stroke_loss
from scribesim.evofit.stroke_gestures import execute_gestures, gesture_guide, validate_gestures
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json
from scribesim.handvalidate import tool_contract as oracle


SPEC_PATH = learning.BASE / 'gesture_evaluation/spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
TRAINING = learning.BASE / SPEC['training']


def load_training(root):
    root = Path(root)
    for name, checksum in SPEC['training_identities'].items():
        if digest(root / name) != checksum:
            raise ValueError('Training identity changed')
    for name, checksum in SPEC['upstream_identities'].items():
        if digest(learning.BASE / name) != checksum:
            raise ValueError('Upstream identity changed')
    freeze = json.loads((root / 'freeze.json').read_text())
    report = json.loads((root / 'report.json').read_text())
    if (freeze['code_sha256'] != learning.code_identities()
            or freeze['spec_sha256'] != digest(learning.SPEC_PATH)
            or freeze['spec'] != learning.SPEC
            or freeze['coverage_sha256'] != digest(learning.BASE / 'coverage/run-001/report.json')
            or report['freeze_sha256'] != object_digest(freeze)):
        raise ValueError('Stale code, criteria or coverage identity')
    for name, checksum in report['artifacts'].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path) != checksum:
            raise ValueError('Artifact identity changed')
    learning.verify_lower()
    return freeze, report


def verify_candidate(initial, candidate, ablation):
    validate_gestures(candidate)
    expected = copy.deepcopy(initial)
    if ablation not in learning.SPEC['ablations']:
        raise ValueError('Unknown ablation')
    if ablation != 'fixed':
        reference = candidate['gestures']['gesture-0']['strokes'][1]
        freedoms = learning.SPEC['freedoms']
        choices = freedoms['primitive_choices'] if ablation == 'composition' else ['rise']
        if (reference['primitive'] not in choices or reference['scale'] not in freedoms['scales']
                or reference['rotation_deg'] not in freedoms['rotations_deg']):
            raise ValueError('Unfrozen candidate freedom')
        expected['gestures']['gesture-0']['strokes'][1].update(
            {key: reference[key] for key in ('primitive', 'scale', 'rotation_deg')})
    if object_digest(expected) != object_digest(candidate):
        raise ValueError('Detached geometry, action, recipe or shared lineage')


def audit_trace(text, model, result, *, step_mm=.05):
    bundle = gesture_guide(text, model, step_mm=step_mm)
    points, owners, indices = result['trajectory'], result['owners'], result['plan_indices']
    errors = int(not points or len(points) != len(owners) or len(points) != len(indices))
    corridor, seen = 0.0, set()
    for point, owner, index in zip(points, owners, indices):
        if type(index) is not int or not 0 <= index < len(bundle.guide.samples):
            errors += 1
            continue
        desired = bundle.guide.samples[index]
        errors += int(point['contact'] != desired.contact or owner != bundle.metadata['owners'][index])
        if not all(math.isfinite(point[key]) for key in ('x_mm', 'y_mm', 'pressure', 'nib_angle_deg', 'width_mm')):
            errors += 1
            continue
        if point['contact']:
            seen.add(owner.get('gesture_occurrence_id'))
            corridor = max(corridor, math.dist((point['x_mm'], point['y_mm']), (desired.x_mm, desired.y_mm)))
    required = {owner['gesture_occurrence_id'] for owner in bundle.metadata['owners'] if owner['kind'] == 'stroke'}
    errors += len(required.symmetric_difference(seen))
    errors += int(indices != sorted(indices) or not indices
                  or indices[-1] != len(bundle.guide.samples) - 1)
    return {'errors': errors, 'corridor_mm': corridor, 'occurrences': sorted(seen, key=str),
            'text': text, 'model_sha256': object_digest(model)}


def local_controls(output=None):
    budget = oracle.ProbeBudget()
    fixtures = oracle.tool_fixtures()
    terminal = oracle._oracle(fixtures[-1], budget)
    arc = oracle._oracle(fixtures[2], budget)
    hidden = copy.deepcopy(fixtures[-1])
    hidden['runs'] = [sum(hidden['runs'], [])]
    overbuilt = copy.deepcopy(fixtures[-1])
    extra = copy.deepcopy(overbuilt['runs'][-1])
    for pose in extra:
        pose['center'][0] += .5
    overbuilt['runs'].append(extra)
    masks = {'hidden_connector': oracle._oracle(hidden, budget),
             'overbuilt_terminal': oracle._oracle(overbuilt, budget), 'erased_counter': arc.copy()}
    vertical, horizontal = np.indices(arc.shape)
    horizontal, vertical = horizontal / oracle.PPMM, vertical / oracle.PPMM
    counter = (horizontal - 1.5) ** 2 + (vertical - 1.5) ** 2 < .45 ** 2
    budget.consume()
    masks['erased_counter'][counter] = True
    result = {'scope': 'independent synthetic guard fixtures; not learned counter acceptance'}
    for name, mask in masks.items():
        baseline = arc if name == 'erased_counter' else terminal
        if name == 'erased_counter':
            region = counter
        else:
            bounds = SPEC['connector_roi_mm' if name == 'hidden_connector' else 'terminal_roi_mm']
            region = ((horizontal >= bounds[0]) & (horizontal <= bounds[1])
                      & (vertical >= bounds[2]) & (vertical <= bounds[3]) & ~baseline)
        fraction = float(mask[region].mean())
        global_loss = oracle._disagreement(baseline, mask)
        result[name] = {'global_disagreement': global_loss,
                        'global_meets_minimum': global_loss >= oracle.CONTRACT['criteria']['negative_control_disagreement_min'],
                        'baseline_local_ink_fraction': float(baseline[region].mean()),
                        'local_ink_fraction': fraction,
                        'detected_locally': fraction > SPEC['local_blank_ink_fraction_max']}
    if output is not None:
        panel = Image.new('RGB', (4 * 288, 320), 'white')
        draw = ImageDraw.Draw(panel)
        for index, (name, mask) in enumerate([('Expected terminal', terminal), *masks.items()]):
            panel.paste(Image.fromarray(np.where(mask, 0, 255).astype('uint8')).convert('RGB'), (index * 288, 32))
            draw.text((index * 288 + 4, 8), name, fill='black')
        panel.save(Path(output) / 'local-controls.png')
        budget.consume()
    result['renders'] = budget.renders
    return result


def _endpoints(result):
    groups = {}
    for point, owner in zip(result['trajectory'], result['owners']):
        if point['contact']:
            groups.setdefault(owner['gesture_occurrence_id'], []).append([point['x_mm'], point['y_mm']])
    return {key: [rows[0], rows[-1]] for key, rows in groups.items()}


def _endpoint_difference(first, second):
    before, after = _endpoints(first), _endpoints(second)
    if before.keys() != after.keys():
        raise ValueError('Endpoint contributor identity mismatch')
    return max(math.dist(point, other) for key in before for point, other in zip(before[key], after[key]))


def _subdivide(model):
    changed = copy.deepcopy(model)
    points = np.array(changed['primitives']['stem']['cubics'][0])
    middle = (points[:-1] + points[1:]) / 2
    inner = (middle[:-1] + middle[1:]) / 2
    center = (inner[0] + inner[1]) / 2
    changed['primitives']['stem']['cubics'] = [
        [points[0].tolist(), middle[0].tolist(), inner[0].tolist(), center.tolist()],
        [center.tolist(), inner[1].tolist(), middle[2].tolist(), points[-1].tolist()]]
    return changed


def evaluate_seed(root, seed):
    if seed not in SPEC['seeds']:
        raise ValueError('Unfrozen seed')
    started, renders = time.monotonic(), 0
    freeze, report = load_training(root)
    initial, target, samples = learning.experiment()
    renders += 5
    if (initial != freeze['initial'] or target != freeze['target']
            or [{key: value for key, value in sample.items() if key != 'raw'} for sample in samples] != freeze['samples']):
        raise ValueError('Experiment reconstruction mismatch')
    for sample in samples:
        path = Path(root) / (sample['id'] + '-target.png')
        if digest(path) != freeze['targets'][sample['id']] or not np.array_equal(sample['raw'], np.asarray(Image.open(path))):
            raise ValueError('Synthetic target reconstruction mismatch')
    records = []
    for ablation in learning.SPEC['ablations']:
        path = Path(root) / f'{seed}-{ablation}-first.json'
        if path.read_bytes() != (Path(root) / f'{seed}-{ablation}-replay.json').read_bytes():
            raise ValueError('Training replay identity mismatch')
        record = json.loads(path.read_text())
        verify_candidate(initial, record['model'], ablation)
        if record['model_sha256'] != object_digest(record['model']):
            raise ValueError('Candidate identity mismatch')
        before, after = {}, {}
        for sample in samples:
            before[sample['id']] = stroke_loss(sample['raw'], learning.render_exercise(initial, sample))
            after[sample['id']] = stroke_loss(sample['raw'], learning.render_exercise(record['model'], sample))
            renders += 2
        metrics = {split: {label: float(np.mean([values[sample['id']] for sample in samples if sample['split'] == split]))
                           for label, values in (('before', before), ('after', after))}
                   for split in ('train', 'development', 'test')}
        if metrics != record['metrics'] or record['status'] != 'complete':
            raise ValueError('Recomputed learning score mismatch')
        summary = {key: record[key] for key in ('seed', 'ablation', 'renders', 'status', 'metrics')}
        if summary not in report['rows']:
            raise ValueError('Learning summary mismatch')
        records.append(record)
    selected = min(records, key=lambda record: (record['metrics']['development']['after'], record['ablation']))
    if {key: selected[key] for key in ('seed', 'ablation', 'model_sha256')} not in report['selected']:
        raise ValueError('Development checkpoint selection mismatch')
    model = selected['model']
    criteria = learning.SPEC['criteria']
    traces, measurements, checks = {}, {}, {}
    checks['heldout_transfer'] = selected['metrics']['test']['after'] <= criteria['heldout_ratio_max'] * selected['metrics']['test']['before']
    saved = json.loads(gzip.decompress((Path(root) / 'actual-traces.json.gz').read_bytes()))
    for sample in (samples[0], samples[-2], samples[-1]):
        applied = learning.exercise_model(model, sample)
        executions = {}
        configurations = [('training', applied, .05, .002), ('coarse', applied, .025, .002),
                          ('step', applied, .0125, .002), ('time', applied, .025, .001),
                          ('repartition', _subdivide(applied), .025, .002)]
        for label, program, step, timestep in configurations:
            if renders + 2 > 2400 or time.monotonic() - started > 850:
                raise ValueError('Evaluation budget exhausted')
            result = execute_gestures(sample['text'], program, dpi=learning.SPEC['dpi'],
                                      frame=learning.SPEC['frame_mm'], step_mm=step, dt=timestep)
            renders += 2
            audit = audit_trace(sample['text'], program, result, step_mm=step)
            checks[sample['id'] + ':' + label + ':contact_ownership'] = audit['errors'] == 0
            checks[sample['id'] + ':' + label + ':corridor'] = audit['corridor_mm'] <= criteria['corridor_mm_max']
            checks[sample['id'] + ':' + label + ':image'] = result['metrics']['image_loss'] <= criteria['actual_image_loss_max']
            executions[label] = result
        baseline = executions['training']
        traces[sample['id']] = {label: {key: value for key, value in result.items() if key != 'images'}
                               for label, result in executions.items()}
        if seed == report['selected_seed'] and traces[sample['id']]['training'] != saved[sample['id']]:
            raise ValueError('Actual execution differs from saved training trace')
        dense = learning.render_exercise(model, sample, step_mm=SPEC['dense_step_mm'])
        renders += 1
        comparisons = {'dense_desired': {'image_loss': stroke_loss(dense, baseline['images']['desired'])}}
        checks[sample['id'] + ':dense_desired'] = comparisons['dense_desired']['image_loss'] <= criteria['convergence_image_loss_max']
        for label in ('step', 'time', 'repartition'):
            image_loss = stroke_loss(executions['coarse']['images']['actual'], executions[label]['images']['actual'])
            endpoint = _endpoint_difference(executions['coarse'], executions[label])
            comparisons[label] = {'image_loss': image_loss, 'endpoint_difference_mm': endpoint}
            checks[sample['id'] + ':' + label + ':convergence'] = (
                image_loss <= criteria['convergence_image_loss_max'] and endpoint <= criteria['convergence_endpoint_mm_max'])
        measurements[sample['id']] = {'actual': baseline['metrics'], 'endpoints_mm': _endpoints(baseline),
                                      'comparisons': comparisons}
    guard = local_controls()
    renders += guard['renders']
    for name in ('hidden_connector', 'overbuilt_terminal', 'erased_counter'):
        checks['local:' + name] = guard[name]['detected_locally'] and guard[name]['baseline_local_ink_fraction'] <= SPEC['local_blank_ink_fraction_max']
    sample = samples[-1]
    applied = learning.exercise_model(model, sample)
    clean = traces[sample['id']]['training']
    for fault in ('undeclared_lift', 'painted_air', 'overbuilt_contributor'):
        broken = copy.deepcopy(clean)
        if fault == 'undeclared_lift':
            broken['trajectory'][0]['contact'] = False
        elif fault == 'painted_air':
            index = next(index for index, point in enumerate(broken['trajectory']) if not point['contact'])
            broken['trajectory'][index]['contact'] = True
        else:
            broken['owners'][0]['overlap_contributors'] = ['undeclared-terminal']
        checks['trace_control:' + fault] = audit_trace(sample['text'], applied, broken)['errors'] > 0
    detached = copy.deepcopy(model)
    detached['recipes']['i']['gestures'][0]['scale'] = 1.1
    try:
        verify_candidate(initial, detached, selected['ablation'])
        checks['detached_geometry_rejected'] = False
    except ValueError:
        checks['detached_geometry_rejected'] = True
    return {'seed': seed, 'model_sha256': object_digest(model), 'checks': checks,
            'subset_status': 'pass' if all(checks.values()) else 'fail', 'measurements': measurements,
            'learning_metrics': {record['ablation']: record['metrics'] for record in records},
            'local_controls': guard, 'renders': renders, 'optimization_evaluations': 0,
            'traces': traces, 'S1_gesture': 'blocked', 'action_fitting_allowed': False}


def build(output, root=TRAINING):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty output directory')
    output.mkdir(parents=True, exist_ok=True)
    load_training(root)
    started = time.monotonic()
    code = {**learning.code_identities(), **{name: digest(ROOT / name) for name in
            ('scribesim/handvalidate/gestures.py', 'scribesim/handvalidate/tool_contract.py')}}
    write_json(output / 'freeze.json', {'spec': SPEC, 'spec_sha256': digest(SPEC_PATH), 'code_sha256': code,
                                      'training_identities': SPEC['training_identities']})
    records, receipts = [], []
    for seed in SPEC['seeds']:
        seed_started = time.monotonic()
        for label, hash_seed in (('first', '7'), ('replay', '839')):
            subprocess.run([sys.executable, '-m', 'scribesim.handvalidate.gestures', 'worker',
                            '--training', str(root), '--output', str(output / f'{seed}-{label}.json'), '--seed', str(seed)],
                           check=True, timeout=890, env={**os.environ, 'PYTHONHASHSEED': hash_seed})
        if ((output / f'{seed}-first.json').read_bytes() != (output / f'{seed}-replay.json').read_bytes()
                or (output / f'{seed}-first.json.gz').read_bytes() != (output / f'{seed}-replay.json.gz').read_bytes()):
            raise ValueError('Independent fresh-process replay mismatch')
        record = json.loads((output / f'{seed}-first.json').read_text())
        elapsed = time.monotonic() - seed_started
        if record['renders'] * 2 + 6 > SPEC['max_renders_per_seed_including_replay'] or elapsed > 1790:
            raise ValueError('Combined replay budget exceeded')
        records.append(record)
        receipts.append({'seed': seed, 'seconds_including_replay': elapsed, 'renders_including_replay': record['renders'] * 2})
    controls = local_controls(output)
    receipts[0]['renders_including_replay'] += controls['renders']
    report = {'stage': 'S1-gesture', 'status': 'blocked', 'decision': 'revise fixed-tool foundations; do not fit actions',
              'scope': SPEC['scope'], 'subset_results': records, 'local_controls': controls,
              'replay': True, 'action_fitting_allowed': False, 'promoted': False, 'owner_review': 'not performed',
              'real_source': 'blocked; no source pixels opened; no reviewed live G0/real lower-layer gate',
              'coverage_debt': json.loads((Path(root) / 'report.json').read_text())['coverage_debt'],
              'optimization_evaluations': 0, 'revision': 0,
              'renders_including_replay_and_presentation': sum(row['renders_including_replay'] for row in receipts),
              'artifacts': {path.name: digest(path) for path in sorted(output.iterdir())}}
    write_json(output / 'S1-gesture.json', report)
    write_json(output / 'execution.json', {'elapsed_seconds': time.monotonic() - started, 'seeds': receipts})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'worker'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--training', type=Path, default=TRAINING)
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    if args.command == 'worker':
        result = evaluate_seed(args.training, args.seed)
        traces = result.pop('traces')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        trace_path = args.output.with_suffix('.json.gz')
        trace_path.write_bytes(gzip.compress(json.dumps(traces, sort_keys=True).encode(), mtime=0))
        result['traces_sha256'] = digest(trace_path)
        write_json(args.output, result)
    else:
        result = build(args.output, args.training)
        print(json.dumps({key: result[key] for key in ('status', 'decision', 'renders_including_replay_and_presentation')}))


if __name__ == '__main__':
    main()
