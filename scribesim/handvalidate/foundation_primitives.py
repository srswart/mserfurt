"""Independent, no-refit current-code acceptance of frozen shared return primitives."""

import argparse
from bisect import bisect_left
import copy
from dataclasses import asdict
import gzip
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image

from scribesim.curriculum import foundation_measurement as measurement
from scribesim.curriculum import foundation_primitives as learning
from scribesim.curriculum.stroke_learning import stroke_loss
from scribesim.evofit import foundation_contract as contract
from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide, validate_gestures, SCHEMA
from scribesim.handflow.planning import build_track_plan, retime_curve_timing
from scribesim.handvalidate import foundation_motion as motion, gestures, tool_contract
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = contract.BASE / 'foundation_repair/primitive_evaluation'
SPEC_PATH = BASE / 'spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
FIXTURES = copy.deepcopy(learning.SPEC['splits']['held_out'])
CONTROL_IDS = tuple(SPEC['control_ids'])
MEASUREMENT = learning.BASE / 'measurement/run-001'
HISTORICAL = contract.BASE / 'tool_contract/run-001/report.json'


def identities():
    return {**measurement.identities(), **{str(path.relative_to(ROOT)): digest(path) for path in
            (Path(__file__), SPEC_PATH, Path(tool_contract.__file__), tool_contract.SPEC, gestures.SPEC_PATH)}}


def verify_artifacts(root, artifacts):
    if not artifacts:
        raise ValueError('Missing artifact manifest')
    for name, checksum in artifacts.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path) != checksum:
            raise ValueError('Artifact mismatch: ' + name)


def load_inputs():
    try:
        if digest(MEASUREMENT / 'report.json') != SPEC['measurement_report_sha256'] or digest(HISTORICAL) != SPEC['historical_tool_report_sha256']:
            raise ValueError('Unfrozen prerequisite report')
        report = json.loads((MEASUREMENT / 'report.json').read_text())
        if report['code_sha256'] != measurement.identities() or report['status'] != 'pass' or not measurement.complete(report['seeds']):
            raise ValueError('Stale or incomplete measurement')
        verify_artifacts(MEASUREMENT, report['artifacts'])
        source = measurement.load_source()
        for seed in SPEC['seeds']:
            learning.require_lineage(source['seeds'][seed]['candidate'], source['initial'])
        source['historical_controls'] = json.loads(HISTORICAL.read_text())['negative_controls']
        return source
    except (OSError, KeyError, TypeError) as error:
        raise ValueError('Incomplete independent evaluation inputs') from error


def curve(cubic):
    parameter = np.linspace(0, 1, 257)
    weights = np.stack(((1 - parameter) ** 3, 3 * parameter * (1 - parameter) ** 2,
                        3 * parameter ** 2 * (1 - parameter), parameter ** 3), axis=1)
    return weights @ np.asarray(cubic)


def target_segments(fixture):
    segments, endpoint = [], None
    parameter = np.linspace(0, 1, 257)
    basis = np.stack((1 - 3 * parameter ** 2 + 2 * parameter ** 3,
                      parameter - 2 * parameter ** 2 + parameter ** 3,
                      3 * parameter ** 2 - 2 * parameter ** 3,
                      parameter ** 3 - parameter ** 2), axis=1)
    target = contract.SPEC['targets']
    for family in fixture['topology']:
        if family in contract.SPEC['new_families']:
            ports = contract.SPEC['new_families'][family]
            points = basis @ np.asarray([ports['start'], np.multiply(ports['entry'], target['endpoint_derivative_magnitudes'][0]),
                                        ports['end'], np.multiply(ports['exit'], target['endpoint_derivative_magnitudes'][1])])
            points[:, 1] += ports['signed_side'] * target['signed_bulge_magnitude'] * np.sin(np.pi * parameter) ** 2
        else:
            points = np.concatenate([curve(cubic) for cubic in contract.SPEC['baseline']['primitives'][family]['cubics']])
        if endpoint is not None:
            points += endpoint - points[0]
        endpoint = points[-1].copy()
        segments.append(points * fixture['scale'])
    return segments


def probe(model, fixture):
    result = copy.deepcopy(model)
    strokes, endpoint = [], None
    for family in fixture['topology']:
        cubics = result['primitives'][family]['cubics']
        offset = [0., 0.] if endpoint is None else np.subtract(endpoint, cubics[0][0]).tolist()
        strokes.append({'primitive': family, 'offset': offset, 'scale': 1., 'rotation_deg': 0.,
                        'transition': 'start' if endpoint is None else 'smooth'})
        endpoint = np.add(cubics[-1][-1], offset).tolist()
    result['gestures'] = {'probe': {'strokes': strokes, 'action': 'fixed'}}
    result['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 3,
                              'gestures': [{'gesture': 'probe', 'offset': [0, 0], 'scale': fixture['scale'],
                                            'rotation_deg': 0., 'transition': 'start', 'overlap_with': []}]}}
    validate_gestures(result)
    return result


def subdivide(model):
    result = copy.deepcopy(model)
    result['schema_version'] = SCHEMA
    for primitive in result['primitives'].values():
        pieces = []
        for cubic in primitive['cubics']:
            controls = np.asarray(cubic)
            first = (controls[:-1] + controls[1:]) / 2
            second = (first[:-1] + first[1:]) / 2
            middle = (second[0] + second[1]) / 2
            pieces.extend(([controls[0].tolist(), first[0].tolist(), second[0].tolist(), middle.tolist()],
                           [middle.tolist(), second[1].tolist(), first[2].tolist(), controls[3].tolist()]))
        primitive['cubics'] = pieces
    validate_gestures(result)
    return result


def execute(model, *, step, dt, budget, version=motion.TARGET_VERSION):
    if version == motion.TARGET_VERSION:
        result = motion.execute(model, 'i', step=step, dt=dt, version=version, budget=budget)
    elif version == 'curve-tangent-v1':
        from scribesim.handvalidate.tangent_motion import execute as execute_tangents
        result = execute_tangents(model, 'i', step=step, dt=dt, budget=budget)
    else:
        raise ValueError('Unsupported independent execution version')
    result['images'] = {kind: budget.render(measurement.paint, learning._trajectory(result, kind)) for kind in ('desired', 'actual')}
    result['metrics']['image_loss'] = stroke_loss(result['images']['desired'], result['images']['actual'])
    return result


def audit_trace(model, result):
    bundle = gesture_guide('i', model, step_mm=result['step_mm'], include_curve_positions=True)
    plan = build_track_plan(bundle.guide, base_speed_mm_s=12)
    if result['version'] == 'curve-tangent-v1':
        from scribesim.handflow.curve_tangents import retime_curve_tangents
        retimed = retime_curve_tangents(plan, bundle.metadata['owners'], compile_gestures('i', model)['strokes'])
    elif result['version'] == motion.TARGET_VERSION:
        retimed = retime_curve_timing(plan, bundle.metadata['owners'], compile_gestures('i', model)['strokes'])
    else:
        raise ValueError('Unsupported audited execution version')
    plan = retimed.plan
    owners = [bundle.metadata['owners'][index] for index in retimed.source_indices]
    errors = int(asdict(plan) != result['plan']) + int(result['text'] != 'i')
    errors += int(result['model_sha256'] != object_digest(model))
    times = [sample.t_s for sample in plan.samples]
    previous, seen = None, set()
    for row in result['trace']:
        index = row['plan_index']
        if type(index) is not int or not 0 <= index < len(owners):
            errors += 1
            continue
        errors += int(row['owner'] != owners[index]) + int(row['contact'] != plan.samples[index].contact)
        errors += int(not all(math.isfinite(value) for value in [*row['to_mm'], *row['desired_mm'], row['time_s'], row['pressure'], row['width_mm'], row['angle_deg']]))
        if row['contact']:
            seen.add(row['owner'].get('occurrence_id', 'undeclared'))
            errors += int(row['owner']['kind'] != 'stroke' or math.dist(row['to_mm'], row['desired_mm']) > SPEC['criteria']['corridor_mm'])
        else:
            errors += int(row['pressure'] != 0)
        if previous is not None:
            errors += int(row['time_before'] != previous['time_s'] or row['from_mm'] != previous['to_mm'])
            errors += int(row['time_s'] < previous['time_s'] or index < previous['plan_index'])
        if row['time_s'] > row['time_before']:
            target_index = min(max(1, bisect_left(times, row['time_s'])), len(times) - 1)
            prior, following = plan.samples[target_index - 1], plan.samples[target_index]
            interval = following.t_s - prior.t_s
            if interval <= 0:
                errors += 1
                expected = (following.x_mm, following.y_mm)
            else:
                fraction = (row['time_s'] - prior.t_s) / interval
                expected = (prior.x_mm + fraction * (following.x_mm - prior.x_mm), prior.y_mm + fraction * (following.y_mm - prior.y_mm))
        else:
            expected = (plan.samples[index].x_mm, plan.samples[index].y_mm)
        errors += int(math.dist(expected, row['desired_mm']) > 1e-8)
        previous = row
    required = {owner['occurrence_id'] for owner in owners if owner['kind'] == 'stroke'}
    errors += len(required.symmetric_difference(seen))
    errors += int(not result['trace'] or abs(result['trace'][-1]['time_s'] - plan.total_time_s) > SPEC['criteria']['duration_error_s'])
    return {'errors': errors, 'required_occurrences': sorted(required), 'seen_occurrences': sorted(seen)}


def regions(fixture):
    result = {}
    for family, segment in zip(fixture['topology'], target_segments(fixture)):
        if family not in contract.SPEC['new_families']:
            continue
        origin, scale = segment[0], fixture['scale']

        def physical(bounds):
            xmin, xmax, ymin, ymax = bounds
            return [(origin[0] + xmin * scale) * 3.5, (origin[0] + xmax * scale) * 3.5,
                    10 - (origin[1] + ymax * scale) * 3.5, 10 - (origin[1] + ymin * scale) * 3.5]

        blank = [.2, .3, .18, .28] if family == 'lower-return' else [.2, .3, -.28, -.18]
        result[family] = {'loss': physical([-.25, .8, -.5, .5]), 'blank': physical(blank)}
    return result


def benefit(before, after):
    ratio = after / before if before > 0 else None
    return {'before': before, 'after': after, 'ratio': ratio,
            'passed': ratio is not None and math.isfinite(ratio) and ratio < SPEC['criteria']['heldout_ratio'] - 1e-12}


def evaluate_fixture(candidate, fixture, budget, directory, *, version=motion.TARGET_VERSION):
    model = probe(candidate, fixture)
    initial = probe(contract.initial_model(), fixture)
    nominal = lambda source: measurement.segment_trajectory([curve(cubic) for row in compile_gestures('i', source)['strokes'] for cubic in row['cubics']])
    paths = [nominal(initial), measurement.segment_trajectory(target_segments(fixture)), nominal(model)]
    before, target, after, empty = [budget.render(measurement.paint, path) for path in [*paths, []]]
    runs, audits = {}, {}
    for refinement in SPEC['refinements']:
        label = refinement['id']
        executed = subdivide(model) if label == 'subdivision' else model
        result = execute(executed, step=refinement['step'], dt=refinement['dt'], budget=budget, version=version)
        audits[label] = audit_trace(executed, result)
        metrics = result['metrics']
        result['passed'] = (audits[label]['errors'] == 0 and metrics['image_loss'] <= SPEC['criteria']['actual_desired_loss']
                            and metrics['corridor_mm'] <= SPEC['criteria']['corridor_mm'] and metrics['owner_errors'] == 0
                            and metrics['time_error_s'] <= SPEC['criteria']['duration_error_s'] and metrics['max_projection_mm'] <= 1e-12
                            and motion.entry_pass(metrics) and motion.mechanics_pass(metrics) and motion.desired_pass(metrics) and motion.corners_pass(metrics))
        runs[label] = result
    comparisons = {label: motion.compare(runs['base'], runs[label]) for label in ('arc', 'time', 'subdivision')}
    families = {}
    for family, bounds in regions(fixture).items():
        fractions = {label: float(np.mean(np.asarray(Image.fromarray(measurement.crop(pixels, bounds['blank'])).convert('L')) < 180))
                     for label, pixels in [('target', target), ('nominal', after), *[(label, run['images']['actual']) for label, run in runs.items()]]}
        families[family] = {**benefit(stroke_loss(measurement.crop(target, bounds['loss']), measurement.crop(before, bounds['loss'])),
                                    stroke_loss(measurement.crop(target, bounds['loss']), measurement.crop(after, bounds['loss']))),
                            'regions_mm': bounds, 'blank_fractions': fractions,
                            'blank_pass': all(value <= SPEC['criteria']['local_blank_fraction'] for value in fractions.values())}
    record = {'id': fixture['id'], 'fixture': fixture, 'full': benefit(stroke_loss(target, before), stroke_loss(target, after)),
              'families': families, 'audits': audits, 'comparisons': comparisons,
              'motion': {label: {'metrics': run['metrics'], 'passed': run['passed']} for label, run in runs.items()},
              'empty_control_loss': stroke_loss(target, empty), 'footprint_contained': True,
              'shared_parameter_propagation': all(row['primitive_sha256'] == object_digest(candidate['primitives'][row['primitive']]) for row in compile_gestures('i', model)['strokes'])}
    record['passed'] = (record['full']['passed'] and record['shared_parameter_propagation'] and record['empty_control_loss'] >= .1
                        and all(row['passed'] and row['blank_pass'] for row in families.values())
                        and all(run['passed'] for run in runs.values()) and all(row['pass'] for row in comparisons.values()))
    tiles = [budget.render(measurement.paint, path, dpi=SPEC['presentation_dpi'])
             for path in [*paths, *[learning._trajectory(runs['base'], kind) for kind in ('desired', 'actual')]]]
    for label, pixels in zip(('initial', 'target', 'candidate', 'sampled', 'actual'), tiles):
        Image.fromarray(pixels).save(directory / (fixture['id'] + '-' + label + '-900dpi.png'))
    return record, runs, tiles


def rejected(model):
    try:
        validate_gestures(model)
    except ValueError:
        return True
    return False


def controls(candidate, budget, directory, *, version=motion.TARGET_VERSION):
    result, evidence = {}, {}
    for name in ('wrong-port', 'wrong-direction'):
        detected = {}
        for family in contract.SPEC['new_families']:
            changed = copy.deepcopy(candidate)
            cubic = changed['primitives'][family]['cubics'][0]
            cubic[1] = [2 * anchor - handle for anchor, handle in zip(cubic[0], cubic[1])] if name == 'wrong-direction' else [cubic[1][0] + .1, cubic[1][1]]
            detected[family] = rejected(changed)
        result[name] = {'families': detected, 'detected': all(detected.values())}
    fixture = next(row for row in FIXTURES if row['topology'] == ['stem', 'lower-return', 'rise'])
    model = probe(candidate, fixture)
    detached = copy.deepcopy(model)
    detached['gestures']['probe']['strokes'][1]['offset'][0] += .1
    base = execute(model, step=.025, dt=.002, budget=budget, version=version)
    valid = audit_trace(model, base)['errors'] == 0
    for name in ('detached-geometry', 'hidden-lift', 'extra-contributor'):
        changed = copy.deepcopy(base)
        row = changed['trace'][len(changed['trace']) // 2]
        if name == 'detached-geometry':
            row['to_mm'][0] += .5
        elif name == 'hidden-lift':
            row['contact'], row['pressure'] = False, 0
        else:
            row = copy.deepcopy(changed['trace'][-1])
            row['owner']['occurrence_id'] = 'undeclared'
            changed['trace'].append(row)
        audit = audit_trace(model, changed)
        evidence[name] = {'model': model, 'trace': changed['trace'], 'plan': changed['plan']}
        pixels = budget.render(measurement.paint, learning._trajectory(changed, 'actual'))
        loss = stroke_loss(base['images']['actual'], pixels)
        result[name] = {'audit': audit, 'unmodified_pass': valid, 'global_disagreement': loss,
                        'global_meets_minimum': loss >= SPEC['criteria']['global_negative_minimum'],
                        'detected': valid and audit['errors'] > 0 and (name != 'detached-geometry' or rejected(detached))}
    lifted = probe(candidate, FIXTURES[0])
    lifted['recipes']['i']['gestures'][0]['scale'] = 1.
    second = copy.deepcopy(lifted['recipes']['i']['gestures'][0])
    second.update(offset=[1.2, 0], transition='lift')
    lifted['recipes']['i']['gestures'].append(second)
    base = execute(lifted, step=.025, dt=.002, budget=budget, version=version)
    changed = copy.deepcopy(base)
    air_count = 0
    for row in changed['trace']:
        if not row['contact']:
            row['contact'], row['pressure'] = True, .5
            air_count += 1
    audit = audit_trace(lifted, changed)
    evidence['painted-air-connector'] = {'model': lifted, 'plan': base['plan'], 'original_trace': base['trace'], 'mutated_trace': changed['trace']}
    pixels = budget.render(measurement.paint, learning._trajectory(changed, 'actual'))
    loss = stroke_loss(base['images']['actual'], pixels)
    result['painted-air-connector'] = {'audit': audit, 'air_samples': air_count,
                                      'unmodified_pass': audit_trace(lifted, base)['errors'] == 0,
                                      'global_disagreement': loss, 'global_meets_minimum': loss >= .1,
                                      'detected': air_count > 0 and audit['errors'] > 0 and audit_trace(lifted, base)['errors'] == 0}
    local = gestures.local_controls(directory)
    budget.charge(local['renders'])
    result['erased-counter'] = {'local_controls': local, 'detected': all(local[name]['detected_locally'] and local[name]['baseline_local_ink_fraction'] <= .01
                                                                 for name in ('hidden_connector', 'overbuilt_terminal', 'erased_counter'))}
    compressed(directory / 'control-traces.json.gz', evidence)
    return result


def decide_seed(rows, control_results, baseline_pass):
    return (baseline_pass is True and len(rows) == len(FIXTURES) and {row['id'] for row in rows} == {fixture['id'] for fixture in FIXTURES}
            and all(row['passed'] is True for row in rows) and set(control_results) == set(CONTROL_IDS)
            and all(row['detected'] is True for row in control_results.values()))


def recheck_fixture(record):
    criteria = SPEC['criteria']
    fixture = next((fixture for fixture in FIXTURES if fixture['id'] == record['id']), None)
    if fixture is None or fixture != record['fixture'] or not record['footprint_contained'] or not record['shared_parameter_propagation']:
        return False
    families = set(fixture['topology']) & set(contract.SPEC['new_families'])
    if set(record['families']) != families or record['empty_control_loss'] < criteria['global_negative_minimum']:
        return False
    for row in [record['full'], *record['families'].values()]:
        if not benefit(row['before'], row['after'])['passed']:
            return False
    for family, row in record['families'].items():
        if row['regions_mm'] != regions(fixture)[family] or set(row['blank_fractions']) != {'target', 'nominal', 'base', 'arc', 'time', 'subdivision'}:
            return False
        if not all(math.isfinite(value) and 0 <= value <= criteria['local_blank_fraction'] for value in row['blank_fractions'].values()):
            return False
    if set(record['motion']) != {'base', 'arc', 'time', 'subdivision'} or set(record['audits']) != set(record['motion']):
        return False
    for label, row in record['motion'].items():
        metrics = row['metrics']
        if (record['audits'][label]['errors'] != 0 or metrics['owner_errors'] != 0
                or not all(math.isfinite(metrics[key]) and 0 <= metrics[key] <= limit for key, limit in
                           (('image_loss', criteria['actual_desired_loss']), ('corridor_mm', criteria['corridor_mm']),
                            ('time_error_s', criteria['duration_error_s']), ('max_projection_mm', 1e-12)))
                or not all(check(metrics) for check in (motion.entry_pass, motion.mechanics_pass, motion.desired_pass, motion.corners_pass))):
            return False
    if set(record['comparisons']) != {'arc', 'time', 'subdivision'}:
        return False
    return all(row['owner_match'] is True and all(math.isfinite(row[key]) and 0 <= row[key] <= limit for key, limit in
               (('endpoint_mm', criteria['endpoint_mm']), ('event_time_s', criteria['event_time_s']), ('image_loss', criteria['refinement_loss'])))
               for row in record['comparisons'].values())


def manifest(directory):
    return {str(path.relative_to(directory)): digest(path) for path in sorted(directory.rglob('*'))
            if path.is_file() and path.name != 'execution.json'}


def compressed(path, value):
    path.write_bytes(gzip.compress(json.dumps(value, sort_keys=True, allow_nan=False).encode(), mtime=0))


def worker(directory, seed, maximum, seconds):
    budget = learning.Budget(maximum, seconds)
    directory.mkdir(parents=True, exist_ok=False)
    report = {'seed': seed, 'status': 'blocked', 'fixtures': [], 'controls': {}, 'optimization_evaluations': 0}
    try:
        source = load_inputs()
        candidate = source['seeds'][seed]['candidate']
        (directory / 'candidate.json').write_bytes((source['seeds'][seed]['directory'] / 'candidate.json').read_bytes())
        report['candidate_sha256'] = object_digest(candidate)
        baseline = motion.revalidate_baseline(budget)
        baseline.pop('panels')
        compressed(directory / 'baseline.json.gz', baseline)
        report['baseline_pass'] = baseline['status'] == 'pass'
        if not report['baseline_pass']:
            raise ValueError('Fresh original baseline failed')
        traces, sheets = {}, []
        for fixture in FIXTURES:
            record, runs, tiles = evaluate_fixture(candidate, fixture, budget, directory)
            record['passed'] = record['passed'] and recheck_fixture(record)
            report['fixtures'].append(record)
            write_json(directory / (fixture['id'] + '-metrics.json'), record)
            sheets.append((fixture['id'] + (' | PASS' if record['passed'] else ' | FAIL'), tiles))
            traces[fixture['id']] = {label: {key: value for key, value in run.items() if key != 'images'} for label, run in runs.items()}
        compressed(directory / 'traces.json.gz', traces)
        budget.render(learning._sheet, directory / 'practice-sheet.png', sheets)
        report['controls'] = controls(candidate, budget, directory)
        report['historical_controls'] = source['historical_controls']
        report['status'] = 'pass' if decide_seed(report['fixtures'], report['controls'], report['baseline_pass']) else 'fail'
        budget.check()
    except (ValueError, RuntimeError, KeyError) as error:
        report['reason'] = str(error)
    report['renders'] = budget.used
    write_json(directory / 'report.json', report)
    write_json(directory / 'execution.json', {'renders': budget.used, 'elapsed_seconds': time.monotonic() - budget.started})
    return report


def build(output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new immutable evaluation directory')
    write_json(output / 'freeze.json', {'spec': SPEC, 'code_sha256': identities()})
    report = {'stage': 'S1-foundation-primitives-v1', 'status': 'blocked', 'seeds': [], 'renders': 0,
              'optimization_evaluations': 0, 'S1_accepted': False, 'gesture_training_permitted': False,
              'real_hand_accepted': False, 'letters_accepted': False, 'actions_accepted': False,
              'code_sha256': identities(), 'missing_inventory': SPEC['missing_inventory']}
    ledger = []
    try:
        source = load_inputs()
        report['supported_families'] = sorted(source['initial']['primitives'])
        report['measurement_report_sha256'] = SPEC['measurement_report_sha256']
        for seed in SPEC['seeds']:
            started, used = time.monotonic(), 0
            outcomes = []
            for label, hashseed in (('first', '0'), ('replay', '839')):
                seconds = SPEC['max_seconds_per_seed_including_replay'] - (time.monotonic() - started)
                directory = output / f'seed-{seed}' / label
                command = [sys.executable, '-m', 'scribesim.handvalidate.foundation_primitives', '--output', str(directory),
                           '--worker-seed', str(seed), '--maximum', str(5000 - used), '--seconds', str(seconds)]
                process = subprocess.run(command, cwd=ROOT, env={**os.environ, 'PYTHONHASHSEED': hashseed}, capture_output=True, text=True, timeout=seconds)
                if process.returncode:
                    raise ValueError('Worker failed: ' + process.stderr[-2000:])
                outcome = json.loads((directory / 'report.json').read_text())
                used += outcome['renders']
                report['renders'] += outcome['renders']
                outcomes.append(outcome)
                ledger.append({'seed': seed, 'process': label, 'renders': outcome['renders'], 'cumulative_seed_renders': used,
                               'cumulative_seed_seconds': time.monotonic() - started})
            first, replay = output / f'seed-{seed}/first', output / f'seed-{seed}/replay'
            matching = manifest(first) == manifest(replay)
            within_budget = used <= SPEC['max_renders_per_seed_including_replay'] and time.monotonic() - started <= SPEC['max_seconds_per_seed_including_replay']
            report['seeds'].append({'seed': seed, 'status': outcomes[0]['status'], 'replay_match': matching,
                                    'candidate_sha256': outcomes[0].get('candidate_sha256'), 'renders': used,
                                    'budget_pass': within_budget, 'passed': matching and within_budget and all(row['status'] == 'pass' for row in outcomes)})
        accepted = len(report['seeds']) == 3 and all(row['passed'] for row in report['seeds'])
        report.update(status='pass' if accepted else 'fail', S1_accepted=accepted, gesture_training_permitted=accepted)
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
    report['artifacts'] = manifest(output)
    write_json(output / 'S1-primitives.json', report)
    write_json(output / 'execution.json', {'ledger': ledger, 'renders': report['renders'], 'optimization_evaluations': 0})
    return report


def require_primitive_readiness(directory, *, expected_report_sha256, required_families):
    directory = Path(directory)
    try:
        if digest(directory / 'S1-primitives.json') != expected_report_sha256:
            raise ValueError('Consumer must pin the exact independent report')
        report = json.loads((directory / 'S1-primitives.json').read_text())
        if report['code_sha256'] != identities() or report['stage'] != 'S1-foundation-primitives-v1' or report['status'] != 'pass':
            raise ValueError('Stale or unaccepted primitive extension')
        source = load_inputs()
        verify_artifacts(directory, report['artifacts'])
        if not required_families or not set(required_families) <= set(source['initial']['primitives']):
            raise ValueError('Unsupported primitive inventory')
        if [row['seed'] for row in report['seeds']] != SPEC['seeds'] or not report['S1_accepted'] or not report['gesture_training_permitted']:
            raise ValueError('Missing complete S1 decision')
        if not all(row['budget_pass'] and row['renders'] <= SPEC['max_renders_per_seed_including_replay'] for row in report['seeds']):
            raise ValueError('Independent seed budget failed')
        for seed in SPEC['seeds']:
            first, replay = directory / f'seed-{seed}/first', directory / f'seed-{seed}/replay'
            if manifest(first) != manifest(replay):
                raise ValueError('Fresh replay differs')
            record = json.loads((first / 'report.json').read_text())
            if record['candidate_sha256'] != object_digest(source['seeds'][seed]['candidate']) or not decide_seed(record['fixtures'], record['controls'], record['baseline_pass']):
                raise ValueError('Independent seed decision failed')
            if not all(recheck_fixture(row) for row in record['fixtures']):
                raise ValueError('Primitive metrics do not meet current frozen criteria')
        return {'stage': report['stage'], 'report_sha256': expected_report_sha256, 'required_families': sorted(set(required_families)),
                'gesture_training_permitted': True, 'scope': 'bounded synthetic fixed-tool shared gestures only'}
    except (OSError, KeyError, TypeError) as error:
        raise ValueError('Incomplete primitive acceptance evidence') from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--worker-seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args()
    result = build(args.output) if args.worker_seed is None else worker(args.output, args.worker_seed, args.maximum, args.seconds)
    print(json.dumps({key: result[key] for key in ('status', 'renders', 'optimization_evaluations')}))


if __name__ == '__main__':
    main()
