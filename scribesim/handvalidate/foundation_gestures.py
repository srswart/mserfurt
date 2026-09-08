"""Independent frozen-gesture proofs; eligibility is not action or letter admission."""

import argparse
from bisect import bisect_left
import copy
from dataclasses import asdict, replace
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scribesim.curriculum import foundation_gestures as learning, gesture_refinements
from scribesim.curriculum import foundation_measurement as measurement
from scribesim.curriculum.stroke_learning import stroke_loss
from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide, validate_gestures
from scribesim.handflow.curve_tangents import retime_curve_tangents
from scribesim.handflow.planning import build_track_plan
from scribesim.handvalidate import foundation_primitives as primitives, tangent_evaluation as admission
from scribesim.handvalidate import tangent_motion as runtime
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = learning.BASE.parent / 'evaluation'
SPEC_PATH = BASE / 'spec-v1.json'
CONTINUATION_PATH = BASE / 'continuation-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
STAGE = SPEC['stage']
TOPOLOGIES = {'underturn': (['stem', 'lower-return', 'rise'], [0, 1]),
              'overturn': (['rise', 'upper-return', 'stem'], [0, 0]),
              'compound_curve': (['upper-return', 'stem', 'lower-return', 'rise'], [0, 0]),
              'terminal': (['support-terminal'], [0, 0])}


def identities():
    paths = [Path(__file__), SPEC_PATH, ROOT / 'scribesim/curriculum/pen_actions.py',
             ROOT / 'scribesim/handvalidate/pen_actions.py']
    if CONTINUATION_PATH.exists():
        paths.append(CONTINUATION_PATH)
    return {**learning.identities(), **{str(path.relative_to(ROOT)): digest(path) for path in paths}}


def require_candidate(candidate, initial):
    validate_gestures(candidate)
    if object_digest(candidate) != SPEC['candidate_object_sha256']:
        raise ValueError('Unfrozen gesture candidate')
    expected = copy.deepcopy(initial)
    roles = {'stem': 0, 'rise': 1, 'lower-return': 2, 'upper-return': 2}
    scales = [candidate['gestures']['underturn']['strokes'][index]['scale'] for index in (0, 2, 1)]
    for name in SPEC['required_gestures']:
        endpoint = None
        for reference in expected['gestures'][name]['strokes']:
            cubics = initial['primitives'][reference['primitive']]['cubics']
            start, end = np.asarray(cubics[0][0]), np.asarray(cubics[-1][-1])
            if endpoint is None:
                endpoint = start * reference['scale'] + reference['offset']
            reference['scale'] = scales[roles[reference['primitive']]]
            reference['offset'] = (endpoint - start * reference['scale']).tolist()
            endpoint = end * reference['scale'] + reference['offset']
    if expected != candidate:
        raise ValueError('Only shared reference scaling and exact attachment translation are admitted')


def load_inputs():
    directory = (BASE / SPEC['source']).resolve()
    if digest(directory / 'report.json') != SPEC['source_report_sha256']:
        raise ValueError('Unfrozen learning report')
    report = json.loads((directory / 'report.json').read_text())
    if report['code_sha256'] != learning.identities() or not report['learning_complete']:
        raise ValueError('Stale or incomplete learning lineage')
    primitives.verify_artifacts(directory, report['artifacts'])
    primitive_root = learning.BASE.parent / learning.SPEC['source']
    primitive_admission = admission.require_readiness(primitive_root,
        expected_report_sha256=learning.SPEC['source_report_sha256'], required_families=SPEC['required_families'])
    lower = admission.load_inputs()
    initial = copy.deepcopy(lower['seeds'][7]['candidate'])
    initial['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 3,
        'gestures': [primitives.contract._instance('underturn', [0, 0], True, 1)]}}
    candidates = {}
    for seed in SPEC['seeds']:
        path = directory / f'seed-{seed}/attachment/first/candidate.json'
        if digest(path) != SPEC['candidate_file_sha256']:
            raise ValueError('Unfrozen candidate bytes')
        candidates[seed] = json.loads(path.read_text())
        require_candidate(candidates[seed], initial)
        if candidates[seed]['primitives'] != lower['seeds'][seed]['candidate']['primitives']:
            raise ValueError('Primitive lineage mismatch')
    return {'candidates': candidates, 'initial': initial, 'lower': lower,
            'primitive_admission': primitive_admission, 'source': directory}


def probe(candidate, fixture):
    result = copy.deepcopy(candidate)
    instances = []
    for index, row in enumerate(fixture['instances']):
        instance = primitives.contract._instance(row['gesture'], row['offset'], index == 0, row['scale'])
        instance['overlap_with'] = row.get('overlap_with', [])
        instances.append(instance)
    result['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 3, 'gestures': instances}}
    validate_gestures(result)
    return result


def target_parts(fixture):
    parameter = np.linspace(0, 1, 257)
    basis = np.stack((parameter - 2 * parameter ** 2 + parameter ** 3,
                      3 * parameter ** 2 - 2 * parameter ** 3,
                      parameter ** 3 - parameter ** 2), axis=1)
    parts = []
    for occurrence, instance in enumerate(fixture['instances']):
        families, anchor = TOPOLOGIES[instance['gesture']]
        endpoint = np.asarray(anchor, dtype=float)
        for family in families:
            definition = SPEC['targets'][family]
            entry = (np.multiply(definition['entry_ray'], definition['magnitudes'][0])
                     if 'entry_ray' in definition else definition['entry'])
            departure = (np.multiply(definition['exit_ray'], definition['magnitudes'][1])
                         if 'exit_ray' in definition else definition['exit'])
            points = basis @ np.asarray([entry, definition['end'], departure])
            points += np.sin(np.pi * parameter[:, None]) ** 2 * definition['bulge'] + endpoint
            parts.append({'occurrence': occurrence, 'family': family, 'scale': instance['scale'],
                          'origin': endpoint * instance['scale'] + instance['offset'],
                          'points': points * instance['scale'] + instance['offset']})
            endpoint = points[-1].copy()
    return parts


def contact_trajectory(parts):
    result, previous = [], None
    for owner, points in parts:
        segment = measurement.segment_trajectory([points])
        if result and owner != previous:
            result.append(replace(segment[0], contact=False, pressure=0))
        result.extend(segment)
        previous = owner
    return result


def contact_runs(path):
    if any(point.pressure != 0 for point in path if not point.contact):
        raise ValueError('Diagnostic air ink')
    return sum(point.contact and (index == 0 or not path[index - 1].contact) for index, point in enumerate(path))


def nominal(model, text='i'):
    return contact_trajectory((row['gesture_occurrence_id'], primitives.curve(cubic))
        for row in compile_gestures(text, model)['strokes'] for cubic in row['cubics'])


def paint(path, *, frame=None, dpi=180):
    frame = SPEC['frame_mm'] if frame is None else frame
    measurement.require_containment(path, frame=frame)
    return paint_trajectory(path, frame, dpi=dpi)


def crop(pixels, bounds):
    left, right, top, bottom = SPEC['frame_mm']
    xmin, xmax, ymin, ymax = bounds
    if not all(math.isfinite(value) for value in bounds) or not (left <= xmin < xmax <= right and top <= ymin < ymax <= bottom):
        raise ValueError('Invalid independent local region; cropping is not admission')
    height, width = pixels.shape[:2]
    return pixels[math.floor((ymin - top) / (bottom - top) * height):math.ceil((ymax - top) / (bottom - top) * height),
                  math.floor((xmin - left) / (right - left) * width):math.ceil((xmax - left) / (right - left) * width)]


def regions(fixture):
    parts, result = target_parts(fixture), {}
    for occurrence, instance in enumerate(fixture['instances']):
        if instance['gesture'] not in SPEC['required_gestures']:
            continue
        selected = [part for part in parts if part['occurrence'] == occurrence]
        points = np.concatenate([part['points'] for part in selected]) * [3.5, -3.5] + [0, 10]
        low, high = points.min(axis=0) - .8, points.max(axis=0) + .8
        blanks = []
        for part in selected:
            if part['family'] not in ('lower-return', 'upper-return'):
                continue
            vertical = [.14, .20] if part['family'] == 'lower-return' else [-.20, -.14]
            corners = (part['origin'] + np.array([[.18, vertical[0]], [.25, vertical[1]]]) * part['scale']) * [3.5, -3.5] + [0, 10]
            blanks.append([float(corners[0, 0]), float(corners[1, 0]), float(corners[1, 1]), float(corners[0, 1])])
        result[str(occurrence)] = {'gesture': instance['gesture'], 'loss': [float(low[0]), float(high[0]), float(low[1]), float(high[1])], 'blank': blanks}
    return result


def fraction(pixels, bounds):
    return float(np.mean(np.asarray(Image.fromarray(crop(pixels, bounds)).convert('L')) < 180))


def ratio(before, after):
    return {'before': before, 'after': after, 'ratio': after / before if before > 0 else None}


def benefit_pass(row):
    return (all(type(row[key]) in (int, float) and math.isfinite(row[key]) for key in ('before', 'after'))
            and row['before'] > 0 and 0 <= row['after'] / row['before'] < SPEC['criteria']['heldout_ratio'])


def reconstructed(model, text, step, subdivision):
    bundle, compiled = (gesture_refinements.bundle(model, step=step) if subdivision else
        (gesture_guide(text, model, step_mm=step, include_curve_positions=True), compile_gestures(text, model)['strokes']))
    timed = retime_curve_tangents(build_track_plan(bundle.guide, base_speed_mm_s=12), bundle.metadata['owners'], compiled)
    return timed.plan, [bundle.metadata['owners'][index] for index in timed.source_indices]


def audit_trace(model, text, result, *, subdivision=False):
    plan, owners = reconstructed(model, text, result['step_mm'], subdivision)
    errors = int(object_digest(asdict(plan)) != object_digest(result['plan'])) + int(result['text'] != text)
    errors += int(result['model_sha256'] != object_digest(model) or result['version'] != runtime.VERSION)
    times, seen, previous = [sample.t_s for sample in plan.samples], set(), None
    for row in result['trace']:
        index = row['plan_index']
        if type(index) is not int or not 0 <= index < len(owners):
            errors += 1
            continue
        errors += int(row['owner'] != owners[index]) + int(row['contact'] != plan.samples[index].contact)
        numbers = [*row['to_mm'], *row['from_mm'], *row['desired_mm'], *row['velocity_mm_s'], row['time_s'], row['pressure'], row['width_mm'], row['angle_deg']]
        errors += int(not all(math.isfinite(value) for value in numbers))
        if row['contact']:
            seen.add(row['owner'].get('occurrence_id', 'undeclared'))
            errors += int(row['owner']['kind'] != 'stroke' or math.dist(row['to_mm'], row['desired_mm']) > .25)
        else:
            errors += int(row['pressure'] != 0)
        if previous is not None:
            errors += int(row['time_before'] != previous['time_s'] or row['from_mm'] != previous['to_mm'])
            errors += int(row['time_s'] < previous['time_s'] or index < previous['plan_index'])
        if row['time_s'] > row['time_before']:
            following_index = min(max(1, bisect_left(times, row['time_s'])), len(times) - 1)
            before, after = plan.samples[following_index - 1], plan.samples[following_index]
            duration = after.t_s - before.t_s
            if duration <= 0:
                errors += 1
                expected = [after.x_mm, after.y_mm]
            else:
                progress = (row['time_s'] - before.t_s) / duration
                expected = [before.x_mm + progress * (after.x_mm - before.x_mm), before.y_mm + progress * (after.y_mm - before.y_mm)]
        else:
            expected = [plan.samples[index].x_mm, plan.samples[index].y_mm]
        errors += int(math.dist(expected, row['desired_mm']) > 1e-8)
        previous = row
    required = {owner['occurrence_id'] for owner in owners if owner['kind'] == 'stroke'}
    errors += len(required.symmetric_difference(seen))
    errors += int(not result['trace'] or abs(result['trace'][-1]['time_s'] - plan.total_time_s) > 1e-10)
    return {'errors': errors, 'required_occurrences': sorted(required), 'seen_occurrences': sorted(seen)}


def boundaries(result):
    groups = []
    for row in result['trace']:
        if not row['contact']:
            continue
        owner = row['owner']['gesture_occurrence_id']
        if not groups or groups[-1]['owner'] != owner:
            groups.append({'owner': owner, 'entry': row, 'exit': row})
        groups[-1]['exit'] = row
    return [{'owner': group['owner'], **{label: {
        'position_error_mm': math.dist(group[label]['to_mm'], group[label]['desired_mm']),
        'speed_mm_s': math.hypot(*group[label]['velocity_mm_s']),
        'velocity_error_mm_s': math.dist(group[label]['velocity_mm_s'],
            [result['plan']['samples'][group[label]['plan_index']][key] for key in ('vx_mm_s', 'vy_mm_s')]),
        'time_s': group[label]['time_s'],
        'actual_mm': group[label]['to_mm'], 'desired_mm': group[label]['desired_mm']}
        for label in ('entry', 'exit')}} for group in groups]


def boundaries_pass(rows, required):
    return ([row['owner'] for row in rows] == required and bool(required) and all(
        type(row[label][key]) in (int, float) and math.isfinite(row[label][key]) and 0 <= row[label][key] <= maximum
        for row in rows for label in ('entry', 'exit') for key, maximum in
        (('position_error_mm', SPEC['criteria']['contact_endpoint_position_mm']),
        ('speed_mm_s' if label == 'entry' else 'velocity_error_mm_s', SPEC['criteria']['contact_endpoint_speed_mm_s']))))


def execute_refinements(model, text, budget, frame):
    runs, proofs = {}, {}
    for refinement in SPEC['refinements']:
        label = refinement['id']
        diagnostic = label == 'subdivision' and text == 'i'
        variant = primitives.subdivide(model) if label == 'subdivision' and text != 'i' else model
        run = (gesture_refinements.execute(variant, step=refinement['step'], dt=refinement['dt'], budget=budget, frame=frame)
               if diagnostic else runtime.execute(variant, text, step=refinement['step'], dt=refinement['dt'], budget=budget, frame=frame))
        for kind in ('desired', 'actual'):
            measurement.require_containment(primitives.learning._trajectory(run, kind), frame=frame)
        required = list(dict.fromkeys(row['gesture_occurrence_id'] for row in compile_gestures(text, model)['strokes']))
        proofs[label] = {'metrics': run['metrics'], 'version': run['version'],
                         'audit': audit_trace(variant, text, run, subdivision=diagnostic),
                         'boundaries': boundaries(run), 'required_contacts': required, 'contained': True}
        runs[label] = run
    comparisons = {label: primitives.motion.compare(runs['base'], run) for label, run in runs.items() if label != 'base'}
    return runs, proofs, comparisons


def motion_pass(record):
    try:
        return (set(record['motion']) == {row['id'] for row in SPEC['refinements']}
            and admission.comparisons_pass(record['comparisons'], ['arc', 'time', 'subdivision'])
            and all(row['version'] == runtime.VERSION and runtime.passes(row) and row['audit']['errors'] == 0
                and row['contained'] is True and boundaries_pass(row['boundaries'], row['required_contacts'])
                for row in record['motion'].values()))
    except (KeyError, TypeError, ValueError):
        return False


def fixture_pass(record):
    try:
        fixture = record['fixture']
        expected = regions(fixture)
        if (not motion_pass(record) or set(record['local']) != set(expected)
                or record['diagnostic_contact_runs'] != [len(fixture['instances'])] * 3):
            return False
        if fixture['split'] == 'held_out' and (not benefit_pass(record['benefit']) or not all(benefit_pass(row) for row in record['local'].values())):
            return False
        for occurrence, row in record['local'].items():
            if row['regions_mm'] != expected[occurrence] or set(row['blank_fractions']) != {'target', 'nominal', 'base', 'arc', 'time', 'subdivision'}:
                return False
            if not all(len(values) == len(expected[occurrence]['blank']) and all(math.isfinite(value) and 0 <= value <= .01 for value in values)
                       for values in row['blank_fractions'].values()):
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def evaluate_fixture(candidate, initial, fixture, budget, directory):
    model = probe(candidate, fixture)
    paths = [nominal(probe(initial, fixture)), contact_trajectory((part['occurrence'], part['points']) for part in target_parts(fixture)), nominal(model)]
    before, target, after = [budget.render(paint, path) for path in paths]
    runs, proofs, comparisons = execute_refinements(model, 'i', budget, SPEC['frame_mm'])
    local = {}
    for occurrence, bounds in regions(fixture).items():
        local[occurrence] = {**ratio(stroke_loss(crop(target, bounds['loss']), crop(before, bounds['loss'])),
                                    stroke_loss(crop(target, bounds['loss']), crop(after, bounds['loss']))), 'regions_mm': bounds,
            'blank_fractions': {label: [fraction(pixels, blank) for blank in bounds['blank']]
                for label, pixels in [('target', target), ('nominal', after), *[(label, run['images']['actual']) for label, run in runs.items()]]}}
    record = {'fixture': fixture, 'benefit': ratio(stroke_loss(target, before), stroke_loss(target, after)),
              'local': local, 'motion': proofs, 'comparisons': comparisons,
              'diagnostic_contact_runs': [contact_runs(path) for path in paths], 'probe_sha256': object_digest(model)}
    record['passed'] = fixture_pass(record)
    tiles = []
    for label, path in zip(('initial', 'target', 'nominal', 'desired', 'actual'),
                           [*paths, *[primitives.learning._trajectory(runs['base'], kind) for kind in ('desired', 'actual')]]):
        pixels = budget.render(paint, path, dpi=SPEC['presentation_dpi'])
        Image.fromarray(pixels).save(directory / f"{fixture['id']}-{label}.png")
        tiles.append(pixels)
    primitives.compressed(directory / f"{fixture['id']}-traces.json.gz", {label: admission.stripped(run) for label, run in runs.items()})
    write_json(directory / f"{fixture['id']}.json", record)
    return record, tiles, runs['base']


def evaluate_context(candidate, fixture, budget, directory):
    model = probe(candidate, fixture)
    runs, proofs, comparisons = execute_refinements(model, fixture['text'], budget, SPEC['context_frame_mm'])
    record = {'fixture': fixture, 'motion': proofs, 'comparisons': comparisons,
              'compiled': compile_gestures(fixture['text'], model)['strokes'], 'probe_sha256': object_digest(model)}
    record['passed'] = motion_pass(record)
    for kind in ('desired', 'actual'):
        pixels = budget.render(paint, primitives.learning._trajectory(runs['base'], kind), frame=SPEC['context_frame_mm'], dpi=900)
        Image.fromarray(pixels).save(directory / f"{fixture['id']}-{kind}.png")
    primitives.compressed(directory / f"{fixture['id']}-traces.json.gz", {label: admission.stripped(run) for label, run in runs.items()})
    write_json(directory / f"{fixture['id']}.json", record)
    return record, runs['base']


def controls(candidate, fixture, base, overlap, budget, directory):
    model, records, evidence = probe(candidate, fixture), {}, {}
    valid = audit_trace(model, 'i', base)['errors'] == 0
    for label in ('wrong-port', 'wrong-direction', 'detached-copy'):
        changed = copy.deepcopy(model)
        if label == 'wrong-port':
            changed['gestures']['underturn']['strokes'][1]['offset'][0] += .05
        elif label == 'wrong-direction':
            changed['gestures']['underturn']['strokes'][1]['rotation_deg'] = 5
        else:
            changed['primitives']['lower-return']['cubics'][0][1][0] += .05
        try:
            validate_gestures(changed)
            grammar = False
        except ValueError:
            grammar = True
        records[label] = {'source_mismatch': changed != model, 'grammar_rejected': grammar, 'detected': changed != model and grammar}
        evidence[label] = changed
    for label in ('hidden-lift', 'extra-contributor', 'wrong-owner', 'air-connector', 'missing-overlap'):
        original = overlap if label == 'missing-overlap' else base
        expected = probe(candidate, SPEC['contexts'][0]) if label == 'missing-overlap' else model
        changed = copy.deepcopy(original)
        row = next(row for row in changed['trace'] if (not row['contact'] if label == 'air-connector' else
            row['contact'] and (bool(row['owner']['overlap_contributors']) if label == 'missing-overlap' else True)))
        if label == 'hidden-lift':
            row['contact'], row['pressure'] = False, 0
        elif label == 'extra-contributor':
            row['owner']['overlap_contributors'].append('undeclared')
        elif label == 'wrong-owner':
            row['owner']['occurrence_id'] = 'detached-letter-copy'
        elif label == 'air-connector':
            row['contact'], row['pressure'] = True, .5
        else:
            row['owner']['overlap_contributors'] = []
        pixels = budget.render(paint, primitives.learning._trajectory(changed, 'actual'), frame=SPEC['context_frame_mm'] if label == 'missing-overlap' else SPEC['frame_mm'])
        loss = stroke_loss(original['images']['actual'], pixels)
        audited = audit_trace(expected, 'i', changed)
        records[label] = {'unmodified_pass': valid and audit_trace(expected, 'i', original)['errors'] == 0,
                          'audit': audited, 'detected': valid and audited['errors'] > 0,
                          'global_loss': loss, 'global_detected_at_0_1': loss >= .1}
        evidence[label] = admission.stripped(changed)
        Image.fromarray(pixels).save(directory / f'{label}.png')
    bounds = next(iter(regions(fixture).values()))['blank'][0]
    pixels = base['images']['actual'].copy()
    budget.charge(1)
    crop(pixels, bounds)[:] = 0
    loss = stroke_loss(base['images']['actual'], pixels)
    records['filled-pocket'] = {'bounds_mm': bounds, 'before': fraction(base['images']['actual'], bounds),
        'after': fraction(pixels, bounds), 'global_loss': loss, 'global_detected_at_0_1': loss >= .1,
        'detected': fraction(base['images']['actual'], bounds) <= .01 < fraction(pixels, bounds)}
    Image.fromarray(pixels).save(directory / 'filled-pocket.png')
    primitives.compressed(directory / 'gesture-control-evidence.json.gz', evidence)
    return records


def controls_pass(records):
    if set(records) != set(SPEC['controls']) or not all(row['detected'] is True for row in records.values()):
        return False
    for name, row in records.items():
        if name in ('wrong-port', 'wrong-direction', 'detached-copy'):
            if not row['source_mismatch'] or not row['grammar_rejected']:
                return False
        elif name == 'filled-pocket':
            if not 0 <= row['before'] <= .01 < row['after'] <= 1:
                return False
        elif row['unmodified_pass'] is not True or row['audit']['errors'] <= 0:
            return False
    return True


def complete(record, baseline):
    try:
        return (record['optimization_evaluations'] == 0 and record['candidate_sha256'] == SPEC['candidate_object_sha256']
            and admission.complete(record['primitive_proofs'], baseline)
            and [row['fixture'] for row in record['fixtures']] == SPEC['fixtures']
            and all(fixture_pass(row) for row in record['fixtures'])
            and [row['fixture'] for row in record['contexts']] == SPEC['contexts']
            and all(motion_pass(row) for row in record['contexts']) and controls_pass(record['controls']))
    except (KeyError, ValueError, TypeError):
        return False


def sheet(path, rows):
    width, height = rows[0][1][0].shape[1], rows[0][1][0].shape[0]
    image = Image.new('RGB', (5 * width, 75 + len(rows) * (height + 50)), 'white')
    draw, font = ImageDraw.Draw(image), ImageFont.load_default(size=20)
    for column, label in enumerate(('Frozen initial', 'Independent target', 'Frozen learned nominal', 'Sampled desired', 'Actual controller')):
        draw.text((column * width + 10, 15), label, fill='black', font=font)
    for index, (label, tiles) in enumerate(rows):
        top = 65 + index * (height + 50)
        draw.text((10, top), label, fill='black', font=font)
        for column, pixels in enumerate(tiles):
            image.paste(Image.fromarray(pixels), (column * width, top + 40))
    image.save(path)


class JournalBudget(primitives.learning.Budget):
    def __init__(self, directory, maximum, seconds):
        super().__init__(maximum, seconds)
        self.directory = directory

    def charge(self, count):
        super().charge(count)
        self.receipt()

    def receipt(self):
        write_json(self.directory / 'execution.json', {'renders': self.used, 'elapsed_seconds': time.monotonic() - self.started})


def worker(directory, seed, maximum, seconds):
    directory.mkdir(parents=True, exist_ok=False)
    budget = JournalBudget(directory, maximum, seconds)
    record = {'seed': seed, 'status': 'blocked', 'optimization_evaluations': 0, 'fixtures': [], 'contexts': [], 'controls': {}}
    try:
        source = load_inputs()
        candidate = source['candidates'][seed]
        record['candidate_sha256'] = object_digest(candidate)
        (directory / 'candidate.json').write_bytes((source['source'] / f'seed-{seed}/attachment/first/candidate.json').read_bytes())
        lower_root = directory / 'primitives'
        lower_root.mkdir()
        baseline = admission.refresh_baseline(lower_root, budget)
        primitive_candidate = source['lower']['seeds'][seed]['candidate']
        primitive_proofs = {'execution_version': runtime.VERSION, 'fixtures': []}
        for fixture in primitives.FIXTURES:
            row, runs, _ = primitives.evaluate_fixture(primitive_candidate, fixture, budget, lower_root, version=runtime.VERSION)
            row['execution_version'] = runtime.VERSION
            primitive_proofs['fixtures'].append(row)
            primitives.compressed(lower_root / (fixture['id'] + '-traces.json.gz'), {label: admission.stripped(run) for label, run in runs.items()})
        primitive_proofs['controls'] = primitives.controls(primitive_candidate, budget, lower_root, version=runtime.VERSION)
        record['primitive_proofs'] = primitive_proofs
        write_json(lower_root / 'proofs.json', primitive_proofs)
        if not admission.complete(primitive_proofs, baseline):
            raise ValueError('Fresh lower-layer proof failed')
        sheets, control_base = [], None
        for fixture in SPEC['fixtures']:
            row, tiles, base = evaluate_fixture(candidate, source['initial'], fixture, budget, directory)
            record['fixtures'].append(row)
            sheets.append((fixture['id'] + (' | PASS' if row['passed'] else ' | FAIL'), tiles))
            if fixture['id'] == 'underturn-overturn-pair':
                control_base = base
        overlap = None
        for fixture in SPEC['contexts']:
            row, base = evaluate_context(candidate, fixture, budget, directory)
            record['contexts'].append(row)
            if fixture['id'] == 'declared-overlap':
                overlap = base
        control_fixture = next(row for row in SPEC['fixtures'] if row['id'] == 'underturn-overturn-pair')
        record['controls'] = controls(candidate, control_fixture, control_base, overlap, budget, directory)
        budget.render(sheet, directory / 'practice-sheet.png', sheets)
        record['status'] = 'pass' if complete(record, baseline) else 'fail'
        budget.check()
    except (ValueError, RuntimeError, KeyError, TypeError, OSError) as error:
        record['status'], record['reason'] = 'blocked', str(error)
    record['renders'] = budget.used
    write_json(directory / 'report.json', record)
    budget.receipt()
    return record


def prior_usage():
    approval = json.loads(CONTINUATION_PATH.read_text())
    prior = BASE / 'run-001'
    if (digest(prior / 'S1-gestures.json') != approval['prior_report_sha256']
            or digest(prior / 'execution.json') != approval['prior_execution_sha256']
            or digest(SPEC_PATH) != approval['unchanged_spec_sha256']):
        raise ValueError('Retained attempt or frozen acceptance specification changed')
    report = json.loads((prior / 'S1-gestures.json').read_text())
    primitives.verify_artifacts(prior, report['artifacts'])
    current = identities()
    changed = {name for name, checksum in report['code_sha256'].items() if current.get(name) != checksum}
    if (changed != {'scribesim/handvalidate/foundation_gestures.py'}
            or set(current) - set(report['code_sha256']) != {str(CONTINUATION_PATH.relative_to(ROOT))}
            or approval['revision'] != 1 or report['S1_gesture_accepted'] is not False):
        raise ValueError('Only one diagnosed evaluator-only continuation is allowed')
    for name, checksum in approval['unchanged_functions_sha256'].items():
        if hashlib.sha256(inspect.getsource(globals()[name]).encode()).hexdigest() != checksum:
            raise ValueError('Continuation cannot change frozen proofs, targets or criteria')
    ledger = json.loads((prior / 'execution.json').read_text())['ledger']
    if [(row['seed'], row['process']) for row in ledger] != [(seed, label) for seed in SPEC['seeds'] for label in ('first', 'replay')]:
        raise ValueError('Incomplete retained accounting')
    return {seed: {'renders': sum(row['renders'] for row in ledger if row['seed'] == seed),
                   'seconds': max(row['cumulative_seed_seconds'] for row in ledger if row['seed'] == seed)} for seed in SPEC['seeds']}


def build(output, *, continuation=False):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new immutable evaluation directory; reruns require a diagnosed continuation')
    if continuation and (output != BASE / 'run-002' or (BASE / 'run-002').exists()):
        raise ValueError('One diagnosed rerun must use the immutable run-002 destination')
    if not continuation and any((BASE / name / 'S1-gestures.json').exists() for name in ('run-001', 'run-002')):
        raise ValueError('Retained attempt exists; cumulative diagnosed continuation required')
    report = {'stage': STAGE, 'status': 'blocked', 'S1_gesture_accepted': False,
              'scope_next_action_experiment': False, 'S1_action_accepted': False, 'null_action_accepted': False,
              'letter_training_allowed': False, 'real_G0_G1_G2_accepted': False, 'promoted': False,
              'execution_version': runtime.VERSION, 'scope': SPEC['scope'], 'missing_inventory': SPEC['missing_inventory'],
              'code_sha256': identities(), 'optimization_evaluations': 0, 'seeds': [], 'renders': 0,
              'revision': int(continuation), 'prior_renders': 0}
    write_json(output / 'freeze.json', {'spec': SPEC, 'code_sha256': identities()})
    ledger = []
    try:
        load_inputs()
        prior = prior_usage() if continuation else {seed: {'renders': 0, 'seconds': 0} for seed in SPEC['seeds']}
        report['prior_renders'] = sum(row['renders'] for row in prior.values())
        for seed in SPEC['seeds']:
            started, used = time.monotonic(), prior[seed]['renders']
            for label, hashseed in (('first', '0'), ('replay', '839')):
                remaining = 1800 - prior[seed]['seconds'] - (time.monotonic() - started)
                if remaining <= 0 or used >= 5000:
                    raise RuntimeError('Combined seed budget exhausted')
                directory = output / f'seed-{seed}/{label}'
                command = [sys.executable, '-m', 'scribesim.handvalidate.foundation_gestures', '--output', str(directory),
                           '--worker-seed', str(seed), '--maximum', str(5000 - used), '--seconds', str(remaining)]
                try:
                    process = subprocess.run(command, cwd=ROOT, env={**os.environ, 'PYTHONHASHSEED': hashseed},
                                             capture_output=True, text=True, timeout=remaining)
                finally:
                    receipt_path = directory / 'execution.json'
                    if receipt_path.exists():
                        receipt = json.loads(receipt_path.read_text())
                        used += receipt['renders']
                        report['renders'] += receipt['renders']
                        ledger.append({'seed': seed, 'process': label, 'renders': receipt['renders'],
                                       'cumulative_seed_renders': used,
                                       'cumulative_seed_seconds': prior[seed]['seconds'] + time.monotonic() - started})
                        write_json(output / 'execution.json', {'ledger': ledger})
                if process.returncode:
                    raise RuntimeError('Worker failed; inspect durable render journal: ' + process.stderr[-2000:])
                if not receipt_path.exists():
                    raise RuntimeError('Worker accounting absent')
            first, replay = output / f'seed-{seed}/first', output / f'seed-{seed}/replay'
            matched = primitives.manifest(first) == primitives.manifest(replay)
            record = json.loads((first / 'report.json').read_text())
            baseline_path = first / 'primitives/motion-baseline.json'
            baseline = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}
            report['seeds'].append({'seed': seed, 'replay_match': matched, 'renders': used,
                'passed': matched and record['status'] == 'pass' and used <= 5000
                          and prior[seed]['seconds'] + time.monotonic() - started <= 1800 and complete(record, baseline)})
        accepted = len(report['seeds']) == 3 and all(row['passed'] for row in report['seeds'])
        report.update(status='pass' if accepted else 'fail', S1_gesture_accepted=accepted, scope_next_action_experiment=accepted)
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
    report['decision'] = 'Eligible to scope a new bounded action/null experiment' if report['scope_next_action_experiment'] else 'STOP / REVISE; no action or letter admission'
    report['cumulative_renders'] = report['prior_renders'] + report['renders']
    write_json(output / 'execution.json', {'ledger': ledger})
    report['artifacts'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
    write_json(output / 'S1-gestures.json', report)
    return report


def require_readiness(directory, *, expected_report_sha256, required_gestures):
    directory = Path(directory).resolve()
    try:
        if not expected_report_sha256 or digest(directory / 'S1-gestures.json') != expected_report_sha256:
            raise ValueError('Consumer-pinned foundation manifest required')
        report = json.loads((directory / 'S1-gestures.json').read_text())
        if report['stage'] != STAGE or report['status'] != 'pass' or report['code_sha256'] != identities():
            raise ValueError('Stale or unaccepted foundation identities')
        if not required_gestures or not set(required_gestures) <= set(SPEC['required_gestures']):
            raise ValueError('Unsupported gesture inventory')
        if any(report[key] is not False for key in ('S1_action_accepted', 'null_action_accepted', 'letter_training_allowed', 'real_G0_G1_G2_accepted', 'promoted')):
            raise ValueError('Foundation evidence cannot promote later layers')
        if not report['S1_gesture_accepted'] or not report['scope_next_action_experiment'] or report['optimization_evaluations'] != 0:
            raise ValueError('Incomplete foundation scope')
        primitives.verify_artifacts(directory, report['artifacts'])
        if json.loads((directory / 'freeze.json').read_text()) != {'spec': SPEC, 'code_sha256': identities()}:
            raise ValueError('Acceptance freeze differs')
        source = load_inputs()
        if report['revision'] != int(CONTINUATION_PATH.exists()):
            raise ValueError('Matching diagnosed revision required')
        prior = prior_usage() if report['revision'] == 1 else {seed: {'renders': 0, 'seconds': 0} for seed in SPEC['seeds']}
        if report['prior_renders'] != sum(row['renders'] for row in prior.values()) or report['cumulative_renders'] != report['prior_renders'] + report['renders']:
            raise ValueError('Retained budget omitted')
        ledger = json.loads((directory / 'execution.json').read_text())['ledger']
        if [(row['seed'], row['process']) for row in ledger] != [(seed, label) for seed in SPEC['seeds'] for label in ('first', 'replay')]:
            raise ValueError('Missing process accounting')
        if [row['seed'] for row in report['seeds']] != SPEC['seeds'] or report['renders'] != sum(row['renders'] for row in ledger):
            raise ValueError('Incomplete seed accounting')
        for seed in SPEC['seeds']:
            receipts = [row for row in ledger if row['seed'] == seed]
            if (prior[seed]['renders'] + sum(row['renders'] for row in receipts) > 5000
                    or any(not prior[seed]['seconds'] < row['cumulative_seed_seconds'] <= 1800 for row in receipts)
                    or receipts[-1]['cumulative_seed_renders'] != prior[seed]['renders'] + sum(row['renders'] for row in receipts)):
                raise ValueError('Cumulative seed budget failed')
            first, replay = directory / f'seed-{seed}/first', directory / f'seed-{seed}/replay'
            if primitives.manifest(first) != primitives.manifest(replay):
                raise ValueError('Fresh-process proof differs')
            if digest(first / 'candidate.json') != SPEC['candidate_file_sha256']:
                raise ValueError('Candidate file identity differs')
            record = json.loads((first / 'report.json').read_text())
            baseline = json.loads((first / 'primitives/motion-baseline.json').read_text())
            require_candidate(json.loads((first / 'candidate.json').read_text()), source['initial'])
            if record['status'] != 'pass' or not complete(record, baseline) or record['renders'] != receipts[0]['renders'] or record['renders'] != receipts[1]['renders']:
                raise ValueError('Independent numeric proof failed')
        return {'stage': STAGE, 'report_sha256': expected_report_sha256, 'execution_version': runtime.VERSION,
                'required_gestures': sorted(set(required_gestures)), 'scope_next_action_experiment': True, 'scope': SPEC['scope']}
    except (OSError, KeyError, TypeError, IndexError) as error:
        raise ValueError('Incomplete foundation readiness evidence') from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker-seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    parser.add_argument('--continuation', action='store_true')
    args = parser.parse_args()
    report = build(args.output, continuation=args.continuation) if args.worker_seed is None else worker(args.output, args.worker_seed, args.maximum, args.seconds)
    print(json.dumps({key: report[key] for key in ('status', 'renders', 'optimization_evaluations')}))


if __name__ == '__main__':
    main()
