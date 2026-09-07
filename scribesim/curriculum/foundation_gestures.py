"""Bounded shared-attachment learning on immutable admitted primitive curves."""

import argparse
import copy
import gzip
import hashlib
import inspect
import itertools
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from dataclasses import replace

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scribesim.curriculum import foundation_primitives as primitives, foundation_measurement as measurement
from scribesim.curriculum import gesture_targets, gesture_refinements
from scribesim.curriculum.stroke_learning import stroke_loss
from scribesim.evofit import foundation_contract as contract
from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures
from scribesim.handvalidate import foundation_primitives as audit, foundation_motion as motion
from scribesim.handvalidate import tangent_evaluation as admission, tangent_motion as runtime
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = contract.BASE / 'foundation_repair/gestures'
SPEC_PATH = BASE / 'spec-v2.json'
SPEC = json.loads(SPEC_PATH.read_text())
CONTINUATION_PATH = BASE / 'continuation-v1.json'
ROLES = {'stem': 0, 'rise': 1, 'lower-return': 2, 'upper-return': 2}


def identities():
    paths = (Path(__file__), Path(gesture_targets.__file__), Path(gesture_refinements.__file__), SPEC_PATH, CONTINUATION_PATH)
    return {**admission.identities(), **{str(path.relative_to(ROOT)): digest(path) for path in paths}}


def load_source():
    directory = BASE.parent / SPEC['source']
    admitted = admission.require_readiness(directory, expected_report_sha256=SPEC['source_report_sha256'],
                                           required_families=SPEC['required_families'])
    if admitted['execution_version'] != SPEC['execution_version']:
        raise ValueError('Matching repaired execution required')
    sources = []
    for seed in SPEC['seeds']:
        path = directory / f'seed-{seed}/first/candidate.json'
        if digest(path) != SPEC['candidate_file_sha256']:
            raise ValueError('Unfrozen primitive candidate')
        sources.append(json.loads(path.read_text()))
    if any(source != sources[0] for source in sources):
        raise ValueError('No seed cherry picking: identical admitted lower layers required')
    return sources[0], admitted


def initial_model(source):
    initial = copy.deepcopy(source)
    initial['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 3,
                              'gestures': [contract._instance('underturn', [0, 0], True, 1)]}}
    validate_gestures(initial)
    return initial


def with_parameters(initial, parameters):
    if len(parameters) != 3 or any(type(value) not in (int, float) or not math.isfinite(value)
                                    or value not in SPEC['search']['values'] for value in parameters):
        raise ValueError('Unfrozen shared attachment parameters')
    result = copy.deepcopy(initial)
    for name in SPEC['constructions']:
        endpoint = None
        for reference in result['gestures'][name]['strokes']:
            geometry = initial['primitives'][reference['primitive']]['cubics']
            start, end = np.asarray(geometry[0][0]), np.asarray(geometry[-1][-1])
            if endpoint is None:
                endpoint = start * reference['scale'] + reference['offset']
            reference['scale'] = float(parameters[ROLES[reference['primitive']]])
            reference['offset'] = (endpoint - start * reference['scale']).tolist()
            endpoint = end * reference['scale'] + reference['offset']
    validate_gestures(result)
    return result


def require_lineage(candidate, initial):
    try:
        parameters = [candidate['gestures']['underturn']['strokes'][index]['scale'] for index in (0, 2, 1)]
        if candidate != with_parameters(initial, parameters):
            raise ValueError('Only exact shared gesture attachments may change')
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError('Malformed gesture lineage') from error


def probe(candidate, fixture):
    result = copy.deepcopy(candidate)
    result['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 3,
                              'gestures': [contract._instance(row['gesture'], row['offset'], index == 0, row['scale'])
                                           for index, row in enumerate(fixture['instances'])]}}
    validate_gestures(result)
    return result


def select(score, *, seed, ablation):
    if seed not in SPEC['seeds'] or ablation not in SPEC['ablations']:
        raise ValueError('Unfrozen seed or ablation')
    values = SPEC['search']['values']
    proposals = ([tuple(SPEC['search']['initial'])] if ablation == 'fixed' else
                 [(value, value, value) for value in values] if ablation == 'placement-only' else
                 list(itertools.product(values, repeat=3)))
    random.Random(seed).shuffle(proposals)
    scores = []
    for parameters in proposals:
        loss = score(list(parameters), 'train')
        if not math.isfinite(loss):
            raise ValueError('Nonfinite training loss')
        scores.append({'parameters': list(parameters), 'loss': loss})
    ranked = sorted(scores, key=lambda row: (row['loss'], row['parameters']))[:SPEC['search']['shortlist']]
    shortlist = sorted({tuple(row['parameters']) for row in ranked} | {tuple(SPEC['search']['initial'])})
    development = []
    for parameters in shortlist:
        loss = score(list(parameters), 'development')
        if not math.isfinite(loss):
            raise ValueError('Nonfinite development loss')
        development.append({'parameters': list(parameters), 'loss': loss})
    chosen = min(development, key=lambda row: (row['loss'], row['parameters']))
    return {'parameters': chosen['parameters'], 'selection_split': 'development', 'held_out_accessed': False,
            'training': scores, 'development': development, 'seed': seed, 'ablation': ablation}


def paint(trajectory, *, dpi=180):
    measurement.require_containment(trajectory, frame=SPEC['frame_mm'])
    return paint_trajectory(trajectory, SPEC['frame_mm'], dpi=dpi)


def crop(pixels, bounds):
    left, right, top, bottom = SPEC['frame_mm']
    xmin, xmax, ymin, ymax = bounds
    if not all(math.isfinite(value) for value in bounds) or not (left <= xmin < xmax <= right and top <= ymin < ymax <= bottom):
        raise ValueError('Invalid local region outside measurement frame')
    height, width = pixels.shape[:2]
    return pixels[math.floor((ymin - top) / (bottom - top) * height):math.ceil((ymax - top) / (bottom - top) * height),
                  math.floor((xmin - left) / (right - left) * width):math.ceil((xmax - left) / (right - left) * width)]


def contact_trajectory(parts):
    trajectory, previous = [], None
    for owner, points in parts:
        samples = measurement.segment_trajectory([points])
        if trajectory and owner != previous:
            trajectory.append(replace(samples[0], contact=False, pressure=0))
        trajectory.extend(samples)
        previous = owner
    return trajectory


def require_contact_runs(trajectory, fixture):
    runs = sum(point.contact and (index == 0 or not trajectory[index - 1].contact)
               for index, point in enumerate(trajectory))
    if runs != len(fixture['instances']) or any(point.pressure != 0 for point in trajectory if not point.contact):
        raise ValueError('Diagnostic contact runs must preserve every explicit gesture lift')
    return runs


def nominal(candidate, fixture):
    rows = compile_gestures('i', probe(candidate, fixture))['strokes']
    return contact_trajectory((row['gesture_occurrence_id'], primitives._curve(cubic)) for row in rows for cubic in row['cubics'])


def target(fixture):
    return contact_trajectory((part['occurrence'], part['points']) for part in gesture_targets.parts(SPEC['targets'], fixture))


def regions(fixture):
    parts = gesture_targets.parts(SPEC['targets'], fixture)
    result = {}
    for occurrence, instance in enumerate(fixture['instances']):
        if instance['gesture'] not in SPEC['constructions']:
            continue
        selected = [part for part in parts if part['occurrence'] == occurrence]
        points = np.concatenate([part['points'] for part in selected]) * [3.5, -3.5] + [0, 10]
        low, high = points.min(axis=0) - .8, points.max(axis=0) + .8
        blanks = []
        for part in selected:
            if part['family'] not in ('lower-return', 'upper-return'):
                continue
            lower = part['family'] == 'lower-return'
            vertical = [.14, .20] if lower else [-.20, -.14]
            first = (part['origin'] + np.array([.18, vertical[0]]) * part['scale']) * [3.5, -3.5] + [0, 10]
            last = (part['origin'] + np.array([.25, vertical[1]]) * part['scale']) * [3.5, -3.5] + [0, 10]
            blanks.append([float(first[0]), float(last[0]), float(last[1]), float(first[1])])
        result[str(occurrence)] = {'gesture': instance['gesture'], 'loss': [float(low[0]), float(high[0]), float(low[1]), float(high[1])],
                                   'blank': blanks}
    return result


def benefit(before, after):
    ratio = after / before if before > 0 else None
    return {'before': before, 'after': after, 'ratio': ratio,
            'passed': ratio is not None and math.isfinite(ratio) and ratio < SPEC['criteria']['heldout_ratio']}


def fraction(pixels, bounds):
    return float(np.mean(np.asarray(Image.fromarray(crop(pixels, bounds)).convert('L')) < 180))


def controls(candidate, fixture, result, budget):
    records = {}
    model = probe(candidate, fixture)
    for label in SPEC['controls'][:5]:
        changed = copy.deepcopy(model)
        strokes = changed['gestures']['underturn']['strokes']
        if label == 'hidden-lift':
            strokes[1]['transition'] = 'lift'
        elif label == 'wrong-port':
            strokes[1]['offset'][0] += .05
        elif label == 'wrong-direction':
            strokes[1]['rotation_deg'] = 5
        elif label == 'detached-copy':
            changed['primitives']['lower-return']['cubics'][0][0][0] += .05
        else:
            changed['recipes']['i']['gestures'].append(contract._instance('terminal', [0, 0], False, 1))
        try:
            validate_gestures(changed)
            detected = False
        except ValueError:
            detected = True
        records[label] = {'detected': detected, 'guard': 'audited grammar', 'global_loss': None}
    for label in ('wrong-owner', 'air-connector'):
        changed = copy.deepcopy(result)
        row = next(row for row in changed['trace'] if row['contact'] == (label == 'wrong-owner'))
        if label == 'wrong-owner':
            row['owner']['occurrence_id'] = 'undeclared-copy'
        else:
            row['contact'], row['pressure'] = True, .5
        pixels = budget.render(paint, primitives._trajectory(changed, 'actual'))
        loss = stroke_loss(result['images']['actual'], pixels)
        records[label] = {'detected': audit.audit_trace(model, changed)['errors'] > 0,
                          'guard': 'exact realized ownership/contact', 'global_loss': loss, 'global_detected': loss >= .1}
    bounds = next(iter(regions(fixture).values()))['blank'][0]
    pixels = result['images']['actual'].copy()
    budget.charge(1)
    crop(pixels, bounds)[:] = 0
    loss = stroke_loss(result['images']['actual'], pixels)
    records['filled-pocket'] = {'detected': fraction(pixels, bounds) > .01, 'guard': 'frozen open-return pocket',
                                 'global_loss': loss, 'global_detected': loss >= .1, 'bounds_mm': bounds}
    return records


def evaluate(candidate, initial, fixture, budget, directory, *, heldout):
    paths = [nominal(initial, fixture), target(fixture), nominal(candidate, fixture)]
    contact_runs = {label: require_contact_runs(path, fixture) for label, path in zip(('initial', 'target', 'fitted'), paths)}
    before, desired_target, after = [budget.render(paint, path) for path in paths]
    model = probe(candidate, fixture)
    runs, audits = {}, {}
    for refinement in SPEC['refinements']:
        label = refinement['id']
        if label == 'subdivision':
            result = gesture_refinements.execute(model, step=refinement['step'], dt=refinement['dt'], budget=budget, frame=SPEC['frame_mm'])
            audits[label] = gesture_refinements.audit_trace(model, result)
        else:
            result = runtime.execute(model, 'i', step=refinement['step'], dt=refinement['dt'], budget=budget, frame=SPEC['frame_mm'])
            audits[label] = audit.audit_trace(model, result)
        for kind in ('desired', 'actual'):
            measurement.require_containment(primitives._trajectory(result, kind), frame=SPEC['frame_mm'])
        result['passed'] = runtime.passes(result) and audits[label]['errors'] == 0
        runs[label] = result
    comparisons = {label: motion.compare(runs['base'], runs[label]) for label in ('arc', 'time', 'subdivision')}
    local = {}
    for occurrence, bounds in regions(fixture).items():
        local[occurrence] = {**benefit(stroke_loss(crop(desired_target, bounds['loss']), crop(before, bounds['loss'])),
                                          stroke_loss(crop(desired_target, bounds['loss']), crop(after, bounds['loss']))),
                             'regions_mm': bounds,
                             'blank_fractions': {label: [fraction(pixels, blank) for blank in bounds['blank']]
                                                for label, pixels in [('target', desired_target), ('nominal', after),
                                                                     *[(label, run['images']['actual']) for label, run in runs.items()]]}}
    record = {'fixture': fixture, 'benefit': benefit(stroke_loss(desired_target, before), stroke_loss(desired_target, after)),
              'local': local, 'audits': audits, 'comparisons': comparisons,
              'motion': {label: {'metrics': run['metrics'], 'passed': run['passed']} for label, run in runs.items()},
              'candidate_sha256': object_digest(candidate), 'probe_sha256': object_digest(model), 'footprint_contained': True,
              'diagnostic_contact_runs': contact_runs,
              'compiled_owners': [{key: row[key] for key in ('primitive', 'primitive_sha256', 'gesture', 'gesture_sha256',
                                                            'action_sha256', 'gesture_occurrence_id', 'transition', 'span')}
                                  for row in compile_gestures('i', model)['strokes']]}
    record['motion_pass'] = all(run['passed'] for run in runs.values()) and all(row['pass'] for row in comparisons.values())
    record['blank_pass'] = all(value <= .01 for row in local.values() for values in row['blank_fractions'].values() for value in values)
    record['learning_pass'] = record['benefit']['passed'] and all(row['passed'] for row in local.values())
    record['passed'] = record['motion_pass'] and record['blank_pass'] and (record['learning_pass'] or not heldout)
    tiles = []
    for label, path in zip(('initial', 'target', 'fitted', 'sampled', 'actual'),
                           [*paths, *[primitives._trajectory(runs['base'], kind) for kind in ('desired', 'actual')]]):
        pixels = budget.render(paint, path, dpi=900)
        Image.fromarray(pixels).save(directory / f"{fixture['id']}-{label}.png")
        tiles.append(pixels)
    write_json(directory / f"{fixture['id']}.json", record)
    traces = {label: {key: value for key, value in run.items() if key != 'images'} for label, run in runs.items()}
    (directory / f"{fixture['id']}-traces.json.gz").write_bytes(gzip.compress(json.dumps(traces, sort_keys=True).encode(), mtime=0))
    return record, tiles, runs['base']


def presentation(directory, rows, candidate, budget):
    width, height = rows[0][1][0].shape[1], rows[0][1][0].shape[0]
    budget.charge(2)
    sheet = Image.new('RGB', (5 * width, len(rows) * (height + 55) + 90), 'white')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=20)
    draw.text((12, 8), 'Shared gesture learning / fixed primitive curves and tool / synthetic, not letters / native 900 DPI', fill='black', font=font)
    for index, label in enumerate(('Unchanged initial', 'Independent target', 'Fitted nominal', 'Sampled desired', 'Actual controller')):
        draw.text((index * width + 10, 48), label, fill='black', font=font)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{len(rows) * 480}">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<defs><marker id="arrow" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5" fill="#222"/></marker></defs>']
    colors = {'stem': '#265bb1', 'rise': '#248257', 'lower-return': '#c34a3c', 'upper-return': '#8e51b2', 'exit': '#bc7c21'}
    for index, (record, tiles) in enumerate(rows):
        fixture = record['fixture']
        offset = 90 + index * (height + 55)
        draw.text((10, offset), f"{fixture['id']} | {fixture['split']} | loss ratio {record['benefit']['ratio']:.4f} | motion {'PASS' if record['motion_pass'] else 'FAIL'}", fill='black', font=font)
        for column, tile in enumerate(tiles):
            sheet.paste(Image.fromarray(tile), (column * width, offset + 45))
        svg.append(f'<g transform="translate(20,{index * 480 + 28})"><text font-family="sans-serif" font-size="16">{fixture["id"]}: directions, joins and shared reference owners</text>')
        for row in compile_gestures('i', probe(candidate, fixture))['strokes']:
            for cubic in row['cubics']:
                points = np.asarray(cubic) * [75, -75] + [60, 160]
                coordinates = ' '.join(f'{point[0]:.5f},{point[1]:.5f}' for point in points)
                first, rest = coordinates.split(' ', 1)
                svg.append(f'<path d="M{first} C{rest}" fill="none" stroke="{colors[row["primitive"]]}" stroke-width="3"/>')
                for point in (points[0], points[-1]):
                    svg.append(f'<circle cx="{point[0]}" cy="{point[1]}" r="3" fill="white" stroke="black"/>')
                direction = points[1] - points[0]
                end = points[0] + direction / np.linalg.norm(direction) * 18
                svg.append(f'<path d="M{points[0][0]},{points[0][1]} L{end[0]},{end[1]}" stroke="#222" marker-end="url(#arrow)"/>')
        for line, row in enumerate(compile_gestures('i', probe(candidate, fixture))['strokes']):
            svg.append(f'<text x="280" y="{35 + line * 25}" font-family="monospace" font-size="14" fill="{colors[row["primitive"]]}">{row["gesture_occurrence_id"]} {row["gesture"]}: {row["primitive"]} / {row["transition"]}</text>')
        svg.append('</g>')
    sheet.save(directory / 'practice-sheet.png')
    (directory / 'ports.svg').write_text(''.join(svg) + '</svg>')


def complete(rows):
    required = {row['id'] for row in SPEC['fixtures'] if row['split'] == 'held_out'}
    return (len(rows) == 3 and {row.get('seed') for row in rows} == set(SPEC['seeds'])
            and all(row.get('passed') is True and row.get('ablation') == 'attachment'
                    and {fixture['fixture']['id'] for fixture in row.get('fixtures', []) if fixture['fixture']['split'] == 'held_out'} == required
                    and all(fixture_passes(fixture) for fixture in row.get('fixtures', []))
                    and set(row.get('controls', {})) == set(SPEC['controls'])
                    and all(control['detected'] for control in row['controls'].values()) for row in rows))


def fixture_passes(record):
    try:
        expected = regions(record['fixture'])
        if record['diagnostic_contact_runs'] != {label: len(record['fixture']['instances']) for label in ('initial', 'target', 'fitted')}:
            return False
        if set(record['local']) != set(expected) or set(record['motion']) != {row['id'] for row in SPEC['refinements']}:
            return False
        if record['fixture']['split'] == 'held_out':
            if not benefit(record['benefit']['before'], record['benefit']['after'])['passed']:
                return False
            if not all(benefit(row['before'], row['after'])['passed'] for row in record['local'].values()):
                return False
        for occurrence, row in record['local'].items():
            if row['regions_mm'] != expected[occurrence] or set(row['blank_fractions']) != {'target', 'nominal', 'base', 'arc', 'time', 'subdivision'}:
                return False
            if not all(len(values) == len(expected[occurrence]['blank']) and all(math.isfinite(value) and 0 <= value <= .01 for value in values)
                       for values in row['blank_fractions'].values()):
                return False
        if set(record['comparisons']) != {'arc', 'time', 'subdivision'} or set(record['audits']) != set(record['motion']):
            return False
        return (record['footprint_contained'] is True and all(runtime.passes(row) for row in record['motion'].values())
                and all(row['errors'] == 0 for row in record['audits'].values())
                and all(row['owner_match'] is True and 0 <= row['endpoint_mm'] <= .01 and 0 <= row['event_time_s'] <= .0001
                        and 0 <= row['image_loss'] <= .03 for row in record['comparisons'].values()))
    except (KeyError, TypeError, ValueError):
        return False


def load_continuation():
    approval = json.loads(CONTINUATION_PATH.read_text())
    stop_path = BASE / 'validation-stop.json'
    if digest(stop_path) != approval['stop_sha256'] or approval['seed7_mode'] != 'frozen-no-refit' or approval['remaining_learning_seeds'] != [19, 41]:
        raise ValueError('Matching explicit continuation approval required')
    stop = json.loads(stop_path.read_text())
    audit.verify_artifacts(BASE, stop['artifacts'])
    prior_freeze = json.loads((BASE / 'run-002/freeze.json').read_text())
    if SPEC != prior_freeze['spec']:
        raise ValueError('Approved continuation cannot change the frozen protocol')
    current = identities()
    for name, checksum in stop['code_sha256'].items():
        if name != 'scribesim/curriculum/foundation_gestures.py' and current.get(name) != checksum:
            raise ValueError('Approved continuation cannot change lower layers or targets')
    for name, checksum in approval['unchanged_functions_sha256'].items():
        if hashlib.sha256(inspect.getsource(globals()[name]).encode()).hexdigest() != checksum:
            raise ValueError('Approved continuation cannot change search or criteria')
    for frozen in approval['frozen_candidates'].values():
        directory = BASE / frozen['directory']
        if digest(directory / 'candidate.json') != frozen['candidate_sha256'] or digest(directory / 'selection.json') != frozen['selection_sha256']:
            raise ValueError('Frozen seed-7 candidate or selection changed')
    return approval, stop['ledger']


def acquire_candidate(initial, seed, ablation, budget):
    if seed not in SPEC['seeds'] or ablation not in SPEC['ablations']:
        raise ValueError('Unfrozen seed or ablation')
    if seed == 7:
        approval, _ = load_continuation()
        frozen = approval['frozen_candidates'][ablation]
        directory = BASE / frozen['directory']
        candidate = json.loads((directory / 'candidate.json').read_text())
        selection = json.loads((directory / 'selection.json').read_text())
        require_lineage(candidate, initial)
        if selection['held_out_accessed'] or selection['selection_split'] != 'development' or selection['candidate_sha256'] != object_digest(candidate):
            raise ValueError('Invalid frozen seed-7 selection')
        return candidate, selection, {'refitted': False, 'source': frozen}
    targets = {row['id']: budget.render(paint, target(row)) for row in SPEC['fixtures'] if row['split'] != 'held_out'}

    def score(parameters, split):
        candidate = with_parameters(initial, parameters)
        return float(np.mean([stroke_loss(targets[row['id']], budget.render(paint, nominal(candidate, row)))
                              for row in SPEC['fixtures'] if row['split'] == split]))

    selection = select(score, seed=seed, ablation=ablation)
    candidate = with_parameters(initial, selection['parameters'])
    selection['candidate_sha256'] = object_digest(candidate)
    return candidate, selection, {'refitted': ablation != 'fixed', 'source': 'Original untouched seed search protocol'}


def worker(directory, freeze, seed, ablation, maximum, seconds):
    budget = primitives.Budget(maximum, seconds)
    directory.mkdir(parents=True, exist_ok=False)
    status, error = 'blocked', None
    try:
        if freeze['code_sha256'] != identities() or freeze['spec'] != SPEC:
            raise ValueError('Stale pre-render freeze')
        source, admitted = load_source()
        initial = initial_model(source)
        if initial != freeze['initial'] or admitted != freeze['admission']:
            raise ValueError('Changed pre-render initialization or admission')
        approval, _ = load_continuation()
        if freeze['continuation'] != approval:
            raise ValueError('Changed continuation approval')
        candidate, selection, provenance = acquire_candidate(initial, seed, ablation, budget)
        require_lineage(candidate, initial)
        write_json(directory / 'candidate.json', candidate)
        write_json(directory / 'selection.json', selection)
        records, sheets, adversarial = [], [], {}
        for fixture in SPEC['fixtures']:
            if fixture['split'] == 'development':
                continue
            record, tiles, result = evaluate(candidate, initial, fixture, budget, directory, heldout=fixture['split'] == 'held_out')
            records.append(record)
            sheets.append((record, tiles))
            if fixture['id'] == 'underturn-overturn-pair':
                adversarial = controls(candidate, fixture, result, budget)
        presentation(directory, sheets, candidate, budget)
        passed = all(fixture_passes(row) for row in records) and all(row['detected'] for row in adversarial.values())
        status = 'pass' if passed else 'fail'
        write_json(directory / 'report.json', {'seed': seed, 'ablation': ablation, 'status': status, 'passed': passed,
                   'parameters': selection['parameters'], 'candidate_sha256': object_digest(candidate), 'fixtures': records,
                   'controls': adversarial, 'renders': budget.used, 'acquisition': provenance,
                   'S1_gesture_accepted': False, 'scope': SPEC['promotion']})
    except (ValueError, RuntimeError, OSError) as failure:
        error = str(failure)
        write_json(directory / 'failure.json', {'seed': seed, 'ablation': ablation, 'status': status, 'error': error})
    finally:
        write_json(directory / 'execution.json', {'seed': seed, 'ablation': ablation, 'status': status, 'error': error,
                   'renders': budget.used, 'seconds': time.monotonic() - budget.started, 'maximum': maximum, 'seconds_cap': seconds})


def build(output):
    source, admitted = load_source()
    approval, previous_ledger = load_continuation()
    output.mkdir(parents=True, exist_ok=False)
    freeze = {'spec': SPEC, 'code_sha256': identities(), 'initial': initial_model(source), 'admission': admitted,
              'target_pixels_accessed': False, 'selection_split': 'development', 'held_out_accessed': False,
              'continuation': approval, 'retained_ledger': previous_ledger}
    write_json(output / 'freeze.json', freeze)
    ledger, primary, results = [], [], []
    status = 'pass'
    for seed in SPEC['seeds']:
        for ablation in SPEC['ablations']:
            prior_rows = [row for row in previous_ledger if row['seed'] == seed and row['ablation'] == ablation]
            used = sum(row['renders'] for row in prior_rows)
            elapsed = sum(row['seconds'] for row in prior_rows)
            manifests = []
            for attempt in ('first', 'replay'):
                directory = output / f'seed-{seed}' / ablation / attempt
                environment = {**os.environ, 'PYTHONHASHSEED': '0' if attempt == 'first' else '839'}
                command = [sys.executable, '-m', 'scribesim.curriculum.foundation_gestures', '--worker', str(directory), '--freeze', str(output / 'freeze.json'),
                           '--seed', str(seed), '--ablation', ablation, '--maximum', str(5000 - used), '--seconds', str(1800 - elapsed)]
                subprocess.run(command, check=True, env=environment)
                execution = json.loads((directory / 'execution.json').read_text())
                used += execution['renders']
                elapsed += execution['seconds']
                ledger.append({**execution, 'attempt': attempt, 'cumulative_renders': used, 'cumulative_seconds': elapsed})
                write_json(output / 'ledger.json', ledger)
                manifests.append({str(path.relative_to(directory)): digest(path) for path in directory.rglob('*')
                                  if path.is_file() and path.name != 'execution.json'})
                if execution['status'] == 'blocked':
                    status = 'blocked'
                    break
            replay_match = len(manifests) == 2 and manifests[0] == manifests[1]
            results.append({'seed': seed, 'ablation': ablation, 'replay_match': replay_match,
                            'artifact_count': len(manifests[0]), 'renders': used, 'seconds': elapsed})
            if status == 'blocked' or not replay_match:
                status = 'blocked'
                break
            record = json.loads((output / f'seed-{seed}/{ablation}/first/report.json').read_text())
            if ablation == 'attachment':
                primary.append(record)
                if not record['passed']:
                    status = 'fail'
                    break
        if status != 'pass':
            break
    passed = status == 'pass' and complete(primary)
    if status == 'pass' and not passed:
        status = 'fail'
    artifacts = {str(path.relative_to(output)): digest(path) for path in output.rglob('*') if path.is_file()}
    write_json(output / 'report.json', {'status': 'pass' if passed else status, 'learning_complete': passed,
               'S1_gesture_accepted': False, 'next': 'HANDVALIDATE-016' if passed else 'Diagnose retained failure; no automatic extra fitting',
               'code_sha256': identities(), 'results': results, 'primary': primary, 'artifacts': artifacts,
               'scope': SPEC['promotion']})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--ablation')
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, json.loads(args.freeze.read_text()), args.seed, args.ablation, args.maximum, args.seconds)
    elif args.output:
        build(args.output)
    else:
        parser.error('--output or --worker required')


if __name__ == '__main__':
    main()
