"""Frozen, admitted-input return learning; independent S1 acceptance stays separate."""

import argparse
import copy
import gzip
import itertools
import json
import math
from pathlib import Path
import random
import time

import numpy as np
from PIL import Image, ImageDraw

from scribesim.curriculum.stroke_learning import stroke_loss
from scribesim.evofit import foundation_contract as contract
from scribesim.evofit.foundation_contract import initial_model
from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures, SCHEMA as LEGACY_SCHEMA
from scribesim.handvalidate import foundation_motion as motion
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.model import TrajectorySample
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = contract.BASE / 'foundation_repair/primitives'
SPEC_PATH = BASE / 'spec-v2.json'
SPEC = json.loads(SPEC_PATH.read_text())


def identities():
    names = ('scribesim/curriculum/foundation_primitives.py',
             'shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitives/spec-v2.json',
             'shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/spec-v5.json',
             'scribesim/pathguide/model.py')
    return {**contract.identities(), **{name: digest(ROOT / name) for name in names}}


class Budget:
    def __init__(self, maximum=5000, seconds=1800):
        if type(maximum) is not int or not 1 <= maximum <= 5000:
            raise ValueError('Render budget must be within 1..5000')
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 < seconds <= 1800:
            raise ValueError('Time budget must be within 1800 seconds')
        self.maximum, self.seconds = maximum, seconds
        self.started, self.used = time.monotonic(), 0
        self.evaluations = []

    def check(self):
        if time.monotonic() - self.started >= self.seconds:
            raise RuntimeError('Learning time budget exhausted')

    def charge(self, count):
        self.check()
        if type(count) is not int or count < 0 or self.used + count > self.maximum:
            raise RuntimeError('Learning render budget exhausted')
        self.used += count

    def render(self, operation, *args, **kwargs):
        self.charge(1)
        result = operation(*args, **kwargs)
        self.check()
        return result


def require_lineage(candidate, initial):
    validate_gestures(candidate)
    expected = copy.deepcopy(initial)
    for family in SPEC['families']:
        expected['primitives'][family] = copy.deepcopy(candidate['primitives'][family])
    if expected != candidate:
        raise ValueError('Only shared return handles may change')


def with_handles(initial, family, handles):
    if family not in SPEC['families'] or len(handles) != 2:
        raise ValueError('Exactly two handles for a permitted family required')
    result = copy.deepcopy(initial)
    ports = contract.SPEC['new_families'][family]
    cubic = result['primitives'][family]['cubics'][0]
    lower, upper = ports['handle_bounds']
    for length, index, endpoint, direction, sign in ((handles[0], 1, cubic[0], ports['entry'], 1),
                                                   (handles[1], 2, cubic[3], ports['exit'], -1)):
        if type(length) not in (int, float, np.float64) or not math.isfinite(length) or not lower <= length <= upper:
            raise ValueError('Requested handle outside frozen bounds')
        effective = float(length)
        for attempt in range(16):
            point = [value + sign * effective * rate for value, rate in zip(endpoint, direction)]
            projected = float(np.dot((np.asarray(point) - endpoint) * sign, direction))
            if lower <= projected <= upper:
                cubic[index] = point
                break
            effective = math.nextafter(effective, (lower + upper) / 2)
        else:
            raise ValueError('Boundary handle could not be represented within fixed bounds')
    require_lineage(result, initial)
    return result


def _curve(cubic):
    parameter = np.linspace(0, 1, 257)[:, None]
    controls = np.asarray(cubic)
    return ((1 - parameter) ** 3 * controls[0] + 3 * (1 - parameter) ** 2 * parameter * controls[1]
            + 3 * (1 - parameter) * parameter ** 2 * controls[2] + parameter ** 3 * controls[3])


def target_segments(fixture):
    segments, endpoint = [], None
    for name in fixture['topology']:
        if name in SPEC['families']:
            points = contract.target_points(name)
        else:
            points = np.concatenate([_curve(cubic) for cubic in contract.SPEC['baseline']['primitives'][name]['cubics']])
        offset = np.zeros(2) if endpoint is None else endpoint - points[0]
        points = points + offset
        endpoint = points[-1]
        segments.append(points * fixture['scale'])
    return segments


def probe_model(model, fixture):
    validate_gestures(model)
    probe = copy.deepcopy(model)
    probe['gestures'] = {'probe': contract._chain(fixture['topology'], probe['primitives'])}
    probe['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 3,
                            'gestures': [contract._instance('probe', [0, 0], True, fixture['scale'])]}}
    validate_gestures(probe)
    return probe


def _paint_segments(segments, dpi):
    trajectory = [TrajectorySample(float(point[0] * 3.5), float(10 - point[1] * 3.5), True, .45, .5, 40)
                  for segment in segments for point in segment]
    return paint_trajectory(trajectory, SPEC['frame_mm'], dpi=dpi)


def render_target(fixture, *, dpi=180):
    return _paint_segments(target_segments(fixture), dpi)


def render_nominal(model, fixture, *, dpi=180):
    rows = compile_gestures('i', probe_model(model, fixture))['strokes']
    return _paint_segments([_curve(cubic) for row in rows for cubic in row['cubics']], dpi)


def search_handles(score, *, seed, values=None, shortlist=None):
    if seed not in SPEC['seeds']:
        raise ValueError('Unfrozen seed')
    values = SPEC['search']['handle_values'] if values is None else values
    shortlist = SPEC['search']['train_shortlist'] if shortlist is None else shortlist
    proposals = list(itertools.product(values, repeat=2))
    random.Random(seed).shuffle(proposals)
    training = []
    for handles in proposals:
        loss = score(list(handles), 'train')
        if not math.isfinite(loss):
            raise ValueError('Nonfinite training loss')
        training.append({'handles': list(handles), 'loss': loss})
    ranked = sorted(training, key=lambda row: (row['loss'], *row['handles']))[:shortlist]
    choices = sorted({tuple(row['handles']) for row in ranked} | {(.28, .28)})
    development = [{'handles': list(handles), 'loss': score(list(handles), 'development')} for handles in choices]
    if any(not math.isfinite(row['loss']) for row in development):
        raise ValueError('Nonfinite development loss')
    selected = min(development, key=lambda row: (row['loss'], *row['handles']))
    return {'handles': selected['handles'], 'development_loss': selected['loss'],
            'training': training, 'development': development, 'selection_split': 'development'}


def verify_admission(output):
    output = Path(output)
    try:
        report = json.loads((output / 'report.json').read_text())
        if report['code_sha256'] != motion.identities() or report['spec_sha256'] != digest(motion.SPEC_PATH):
            raise ValueError('Stale motion admission')
        for name, checksum in report['artifacts'].items():
            path = (output / name).resolve()
            if not path.is_relative_to(output.resolve()) or digest(path) != checksum:
                raise ValueError('Motion artifact mismatch')
        if 'baseline.json' not in report['artifacts'] or 'freeze.json' not in report['artifacts']:
            raise ValueError('Missing admission evidence')
        baseline = json.loads((output / 'baseline.json').read_text())
        freeze = json.loads((output / 'freeze.json').read_text())
        if freeze['code_sha256'] != motion.identities() or freeze['spec'] != motion.SPEC:
            raise ValueError('Stale baseline freeze')
        decision = motion.decide_motion(report['checks'], baseline)
        if decision != report['decision'] or not decision['primitive_training_permitted']:
            raise ValueError('Current motion and original baseline do not admit learning')
        contract.verify_prerequisites()
    except (KeyError, TypeError, OSError) as error:
        raise ValueError('Incomplete motion admission') from error
    return {'status': 'pass', 'report_sha256': digest(output / 'report.json'),
            'code_sha256': report['code_sha256'], 'required_checks': len(report['checks']),
            'baseline_candidate_sha256': baseline['candidate_sha256']}


def refresh_baseline(output, budget):
    contract.verify_prerequisites()
    report = motion.build(output)
    budget.charge(report['renders'])
    return verify_admission(output)


def benefit_pass(before, after):
    return (math.isfinite(before) and math.isfinite(after) and before > 0
            and after / before < SPEC['metrics']['heldout_ratio']
            and not math.isclose(after / before, SPEC['metrics']['heldout_ratio'], rel_tol=0, abs_tol=1e-12))


def _crop(image, bounds):
    left, right, top, bottom = SPEC['frame_mm']
    xmin, xmax, ymin, ymax = bounds
    xstart = max(0, math.floor((xmin - left) / (right - left) * image.shape[1]))
    xend = min(image.shape[1], math.ceil((xmax - left) / (right - left) * image.shape[1]))
    ystart = max(0, math.floor((ymin - top) / (bottom - top) * image.shape[0]))
    yend = min(image.shape[0], math.ceil((ymax - top) / (bottom - top) * image.shape[0]))
    if xend <= xstart or yend <= ystart:
        raise ValueError('Empty predeclared region')
    return image[ystart:yend, xstart:xend]


def _regions(fixture):
    result = {}
    for name, segment in zip(fixture['topology'], target_segments(fixture)):
        if name not in SPEC['families']:
            continue
        origin = segment[0]
        scale = fixture['scale']

        def physical(bounds):
            xmin, xmax, ymin, ymax = bounds
            return [(origin[0] + xmin * scale) * 3.5, (origin[0] + xmax * scale) * 3.5,
                    10 - (origin[1] + ymax * scale) * 3.5, 10 - (origin[1] + ymin * scale) * 3.5]

        blank = [.2, .3, .18, .28] if name == 'lower-return' else [.2, .3, -.28, -.18]
        result[name] = {'loss': physical([-.25, .8, -.5, .5]), 'blank': physical(blank)}
    return result


def _blank_fraction(image, bounds):
    gray = np.asarray(Image.fromarray(_crop(image, bounds)).convert('L'))
    return float(np.mean(gray < 180))


def _trajectory(result, kind):
    if kind == 'actual':
        return [TrajectorySample(*row['to_mm'], row['contact'], row['width_mm'], row['pressure'], row['angle_deg'])
                for row in result['trace']]
    return [TrajectorySample(row['x_mm'], row['y_mm'], row['contact'], .45, row['pressure'], row['nib_angle_deg'])
            for row in result['plan']['samples']]


def execute_fixture(model, fixture, budget):
    probe = probe_model(model, fixture)
    runs = {}
    for refinement in SPEC['refinements']:
        executed = copy.deepcopy(probe)
        if refinement['subdivision']:
            executed['schema_version'] = LEGACY_SCHEMA
        result = motion.execute(executed, 'i', step=refinement['step'], dt=refinement['dt'],
                                version=motion.TARGET_VERSION, budget=budget, subdivision=refinement['subdivision'])
        result['foundation_source_sha256'] = object_digest(model)
        result['probe_sha256'] = object_digest(probe)
        for kind in ('desired', 'actual'):
            result['images'][kind] = budget.render(paint_trajectory, _trajectory(result, kind), SPEC['frame_mm'], dpi=SPEC['dpi'])
        metrics = result['metrics']
        metrics['image_loss'] = stroke_loss(result['images']['desired'], result['images']['actual'])
        result['passed'] = (metrics['image_loss'] <= .35 and metrics['corridor_mm'] <= .25 and metrics['owner_errors'] == 0
                            and metrics['time_error_s'] <= motion.SPEC['criteria']['duration_s']
                            and metrics['max_projection_mm'] <= 1e-12 and motion.entry_pass(metrics)
                            and motion.mechanics_pass(metrics) and motion.desired_pass(metrics) and motion.corners_pass(metrics))
        runs[refinement['id']] = result
    comparisons = {label: motion.compare(runs['base'], runs[label]) for label in ('arc', 'time', 'subdivision')}
    return runs, comparisons


def _sheet(output, rows):
    columns, width, height = 5, 430, 420
    sheet = Image.new('RGB', (columns * width, len(rows) * height + 50), 'white')
    draw = ImageDraw.Draw(sheet)
    for column, label in enumerate(('Frozen initial', 'Independent target', 'Learned nominal', 'Sampled desired', 'Actual controller')):
        draw.text((column * width + 8, 12), label, fill='black')
    for index, (label, tiles) in enumerate(rows):
        draw.text((8, index * height + 42), label, fill='black')
        for column, pixels in enumerate(tiles):
            image = Image.fromarray(pixels)
            scale = min(1, (width - 10) / image.width, (height - 36) / image.height)
            if scale < 1:
                image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
            sheet.paste(image, (column * width + 5, index * height + 65))
    sheet.save(output)


def port_overlay(output, candidate):
    require_lineage(candidate, initial_model())
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 360">',
             '<rect width="1000" height="360" fill="white"/>',
             '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#245c49"/></marker></defs>',
             '<g font-family="sans-serif" font-size="16"><text x="20" y="28">Saved geometry: gray initial / green learned / orange independent target; fixed entry and exit rays</text>']
    for index, family in enumerate(SPEC['families']):
        left = 100 + index * 490

        def position(point):
            return f'{left + point[0] * 500:.4f},{190 - point[1] * 500:.4f}'

        cubic = candidate['primitives'][family]['cubics'][0]
        parts.append(f'<text x="{left}" y="65">{family}</text>')
        for points, color in ((_curve(initial_model()['primitives'][family]['cubics'][0]), '#999'),
                              (contract.target_points(family), '#bd782b'), (_curve(cubic), '#245c49')):
            parts.append(f'<polyline points="{" ".join(position(point) for point in points)}" fill="none" stroke="{color}" stroke-width="2"/>')
        for endpoint, handle, label in ((cubic[0], cubic[1], 'entry'), (cubic[3], cubic[2], 'exit')):
            start, end = (endpoint, handle) if label == 'entry' else (handle, endpoint)
            coordinates = [float(value) for value in (position(start) + ',' + position(end)).split(',')]
            parts.append(f'<line x1="{coordinates[0]}" y1="{coordinates[1]}" x2="{coordinates[2]}" y2="{coordinates[3]}" stroke="#245c49" marker-end="url(#arrow)"/>')
            parts.append(f'<text x="{left + endpoint[0] * 500 - 16}" y="215">{label}</text>')
        parts.append(f'<text x="{left - 35}" y="315">Only handle lengths vary; anchors and rays remain fixed</text>')
    parts.append('</g></svg>')
    Path(output).write_text('\n'.join(parts) + '\n')


def fit_seed(output, seed, budget):
    initial, candidate = initial_model(), initial_model()
    targets, searches, setup_renders = {}, {}, budget.used
    for split in ('train', 'development'):
        for fixture in SPEC['splits'][split]:
            targets[fixture['id']] = budget.render(render_target, fixture)
            Image.fromarray(targets[fixture['id']]).save(output / (fixture['id'] + '-target.png'))
    for family in SPEC['families']:
        fixtures = {split: next(row for row in SPEC['splits'][split] if row['topology'] == [family])
                    for split in ('train', 'development')}

        def score(handles, split):
            budget.check()
            fixture = fixtures[split]
            loss = stroke_loss(targets[fixture['id']], budget.render(render_nominal, with_handles(initial, family, handles), fixture))
            budget.evaluations.append({'family': family, 'handles': handles, 'split': split, 'loss': loss})
            return loss

        searches[family] = search_handles(score, seed=seed)
        candidate = with_handles(candidate, family, searches[family]['handles'])
        write_json(output / (family + '-selection.json'), searches[family])
        write_json(output / (family + '-checkpoint.json'), candidate)
    require_lineage(candidate, initial)
    write_json(output / 'candidate.json', candidate)
    write_json(output / 'selection.json', {'seed': seed, 'candidate_sha256': object_digest(candidate),
                                         'selection_split': 'development', 'held_out_accessed': False,
                                         'families': {name: {key: value for key, value in row.items() if key not in ('training', 'development')}
                                                      for name, row in searches.items()}})
    search_renders = budget.used - setup_renders
    held_out, traces, sheet_rows = [], {}, []
    for fixture in SPEC['splits']['held_out']:
        target = budget.render(render_target, fixture)
        before = budget.render(render_nominal, initial, fixture)
        after = budget.render(render_nominal, candidate, fixture)
        null = budget.render(paint_trajectory, [], SPEC['frame_mm'], dpi=SPEC['dpi'])
        for label, pixels in (('target', target), ('initial', before), ('learned', after)):
            Image.fromarray(pixels).save(output / (fixture['id'] + '-' + label + '.png'))
        initial_loss, learned_loss = stroke_loss(target, before), stroke_loss(target, after)
        runs, comparisons = execute_fixture(candidate, fixture, budget)
        regions = _regions(fixture)
        families = {}
        for family, bounds in regions.items():
            prior = stroke_loss(_crop(target, bounds['loss']), _crop(before, bounds['loss']))
            learned = stroke_loss(_crop(target, bounds['loss']), _crop(after, bounds['loss']))
            fractions = {label: _blank_fraction(pixels, bounds['blank'])
                         for label, pixels in [('target', target), ('nominal', after),
                                               *[(name, result['images']['actual']) for name, result in runs.items()]]}
            families[family] = {'before': prior, 'after': learned, 'ratio': learned / prior if prior > 0 else None,
                                'benefit_pass': benefit_pass(prior, learned), 'blank_fractions': fractions,
                                'blank_pass': all(value <= .01 for value in fractions.values()), 'regions_mm': bounds,
                                'motion': {name: result['metrics'] for name, result in runs.items()}}
        record = {'fixture': fixture, 'before': initial_loss, 'after': learned_loss,
                  'ratio': learned_loss / initial_loss if initial_loss > 0 else None,
                  'benefit_pass': benefit_pass(initial_loss, learned_loss), 'families': families,
                  'fixed_null': {'loss': initial_loss, 'ratio': 1.0},
                  'empty_control_loss': stroke_loss(target, null), 'comparisons': comparisons,
                  'motion_pass': all(result['passed'] for result in runs.values()) and all(row['pass'] for row in comparisons.values())}
        record['passed'] = (record['benefit_pass'] and record['motion_pass'] and record['empty_control_loss'] >= .1
                            and all(row['benefit_pass'] and row['blank_pass'] for row in families.values()))
        held_out.append(record)
        write_json(output / (fixture['id'] + '-metrics.json'), record)
        traces[fixture['id']] = {name: {key: value for key, value in result.items() if key != 'images'} for name, result in runs.items()}
        tiles = [budget.render(render_nominal, initial, fixture, dpi=900), budget.render(render_target, fixture, dpi=900),
                 budget.render(render_nominal, candidate, fixture, dpi=900)]
        tiles += [budget.render(paint_trajectory, _trajectory(runs['base'], kind), SPEC['frame_mm'], dpi=900)
                  for kind in ('desired', 'actual')]
        sheet_rows.append((fixture['id'] + (' | PASS' if record['passed'] else ' | FAIL'), tiles))
    budget.render(_sheet, output / 'practice-sheet.png', sheet_rows)
    budget.render(port_overlay, output / 'ports.svg', candidate)
    (output / 'traces.json.gz').write_bytes(gzip.compress(json.dumps(traces, sort_keys=True).encode(), mtime=0))
    budget.check()
    record = {'seed': seed, 'status': 'pass' if all(row['passed'] for row in held_out) else 'fail',
              'candidate_sha256': object_digest(candidate), 'old_six_unchanged': True, 'only_handles_changed': True,
              'held_out': held_out, 'search_and_target_renders': search_renders,
              'optimization_evaluations': sum(len(row['training']) for row in searches.values()),
              'renders_including_setup': budget.used, 'S1_accepted': False, 'gesture_training_permitted': False,
              'artifacts': {path.name: digest(path) for path in sorted(output.iterdir()) if path.is_file()}}
    write_json(output / 'report.json', record)
    write_json(output / 'execution.json', {'renders': budget.used, 'elapsed_seconds': time.monotonic() - budget.started})
    return record


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError('Use a new immutable learning directory')
    budget = Budget()
    write_json(output / 'freeze.json', {'spec': SPEC, 'spec_sha256': digest(SPEC_PATH), 'code_sha256': identities(),
                                       'contract_sha256': digest(contract.SPEC_PATH), 'initial': initial_model()})
    report = {'status': 'blocked', 'scope': SPEC['scope'], 'S1_accepted': False, 'gesture_training_permitted': False,
              'optimization_evaluations': 0, 'seeds': [], 'code_sha256': identities(), 'revision': SPEC['revision']}
    try:
        report['admission'] = refresh_baseline(output / 'baseline', budget)
        if report['admission']['status'] != 'pass':
            raise ValueError('Current baseline admission failed')
        report['baseline_renders_charged_to_seed_7'] = budget.used
        for seed in SPEC['seeds']:
            if seed != SPEC['seeds'][0]:
                budget = Budget()
            directory = output / f'seed-{seed}'
            directory.mkdir()
            record = fit_seed(directory, seed, budget)
            report['seeds'].append({'seed': seed, 'status': record['status'], 'report_sha256': digest(directory / 'report.json'),
                                    'renders': record['renders_including_setup'], 'candidate_sha256': record['candidate_sha256']})
            report['optimization_evaluations'] += record['optimization_evaluations']
        report['status'] = 'pass' if all(row['status'] == 'pass' for row in report['seeds']) else 'fail'
    except (RuntimeError, ValueError) as error:
        report['reason'] = str(error)
        report['optimization_evaluations'] += sum(row['split'] == 'train' for row in budget.evaluations)
        write_json(output / 'stopped-evaluations.json', budget.evaluations)
        write_json(output / 'stopped-execution.json', {'renders_current_seed': budget.used,
                                                      'elapsed_seconds': time.monotonic() - budget.started})
    report['artifacts'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*'))
                           if path.is_file() and path.name != 'execution.json'}
    write_json(output / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build(args.output)
    print(json.dumps({key: report[key] for key in ('status', 'seeds', 'optimization_evaluations', 'S1_accepted')}, indent=2))


if __name__ == '__main__':
    main()
