"""Independent fixed-null evaluation and opt-in scoped admission; never letter approval."""

import argparse
from collections import deque
import copy
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image

from scribesim.curriculum import foundation_actions as learning
from scribesim.evo.nib_contact import ContactSample, contact_corners
from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handvalidate import foundation_gestures as foundation
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = learning.BASE.parent / 'action_evaluation'
SPEC_PATH = BASE / 'spec-v2.json'
CONTINUATION_PATH = BASE / 'continuation-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
REFINEMENTS = ('base', 'arc', 'time', 'subdivision')


def identities():
    return {**learning.identities(), str(Path(__file__).relative_to(ROOT)): digest(Path(__file__)),
            str(SPEC_PATH.relative_to(ROOT)): digest(SPEC_PATH),
            str(CONTINUATION_PATH.relative_to(ROOT)): digest(CONTINUATION_PATH),
            str((BASE / 'spec-v1.json').relative_to(ROOT)): digest(BASE / 'spec-v1.json')}


def prior_usage():
    continuation = json.loads(CONTINUATION_PATH.read_text())
    directory = BASE / continuation['source']
    if digest(directory / 'S1-actions.json') != continuation['source_report_sha256']:
        raise ValueError('Preserved failed evaluation identity changed')
    report = json.loads((directory / 'S1-actions.json').read_text())
    foundation.primitives.verify_artifacts(directory, report['artifacts'])
    freeze = json.loads((directory / 'freeze.json').read_text())
    if freeze['spec'] != json.loads((BASE / continuation['original_spec']).read_text()) or report['revision'] != 0:
        raise ValueError('Original evaluation freeze changed')
    ledger = json.loads((directory / 'execution.json').read_text())['ledger']
    if [(row['seed'], row['process']) for row in ledger] != [(seed, label) for seed in SPEC['seeds'] for label in ('first', 'replay')]:
        raise ValueError('Missing retained seed costs')
    usage = {seed: {'renders': sum(row['renders'] for row in ledger if row['seed'] == seed),
                    'seconds': max(row['cumulative_seed_seconds'] for row in ledger if row['seed'] == seed)} for seed in SPEC['seeds']}
    if report['renders'] != sum(row['renders'] for row in usage.values()):
        raise ValueError('Retained total differs')
    return usage


def require_scope(required_gestures, tool, real):
    if (not required_gestures or not set(required_gestures) <= set(SPEC['required_gestures'])
            or tool != SPEC['tool'] or real):
        raise ValueError('Explicit supported synthetic fixed-tool inventory required; no cross-tool or real admission')


def load_inputs():
    directory = (BASE / SPEC['source']).resolve()
    selected = learning.require_candidates(directory, expected_report_sha256=SPEC['source_report_sha256'])
    foundation.require_readiness(foundation.BASE / 'run-002',
        expected_report_sha256=learning.SPEC['source_report_sha256'], required_gestures=SPEC['required_gestures'])
    if SPEC['criteria']['absolute_loss_max'] != learning.SPEC['criteria']['null_actual_target_loss_max']:
        raise ValueError('Absolute target criterion changed')
    candidates = {}
    for seed in SPEC['seeds']:
        path = directory / f'seed-{seed}/first/candidate.json'
        if digest(path) != SPEC['candidate_file_sha256']:
            raise ValueError('Frozen selected candidate bytes required')
        candidates[seed] = json.loads(path.read_text())
        learning.require_candidate(candidates[seed])
        for fixture in [*SPEC['fixtures'], SPEC['counter_fixture']]:
            model = foundation.probe(candidates[seed], fixture)
            compile_gestures('i', model)
            foundation.measurement.require_containment(target(fixture), frame=SPEC['frame_mm'])
    original = (BASE / SPEC['original_control_report']).resolve()
    if digest(original) != SPEC['original_control_report_sha256']:
        raise ValueError('Historical negative evidence changed')
    return {'directory': directory, 'candidates': candidates, 'selected': selected,
            'original_controls': json.loads(original.read_text())['negative_controls']}


def target(fixture):
    return foundation.contact_trajectory((part['occurrence'], part['points']) for part in foundation.target_parts(fixture))


def finite(values):
    return bool(values) and all(type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in values)


def quality(row, gesture=None):
    try:
        expected = {str(index) for index, instance in enumerate(row['fixture']['instances'])
                    if instance['gesture'] in SPEC['required_gestures'] and (gesture is None or instance['gesture'] == gesture)}
        if not expected or not expected <= set(row['local_actual_target']):
            return False
        losses = [row['local_actual_target'][index] for index in expected]
        if gesture is None:
            losses.append(row['actual_target'])
        return all(set(values) == set(REFINEMENTS) and finite(values.values())
                   and max(values.values()) <= SPEC['criteria']['absolute_loss_max'] for values in losses)
    except (KeyError, TypeError, ValueError):
        return False


def enclosed_blank(pixels, bounds):
    if foundation.fraction(pixels, bounds) > SPEC['criteria']['blank_fraction_max']:
        return False
    blank = np.asarray(Image.fromarray(pixels).convert('L')) >= 180
    height, width = blank.shape
    left, right, top, bottom = SPEC['frame_mm']
    column = int(((bounds[0] + bounds[1]) / 2 - left) / (right - left) * width)
    row = int(((bounds[2] + bounds[3]) / 2 - top) / (bottom - top) * height)
    if not blank[row, column]:
        return False
    pending, seen = deque([(row, column)]), {(row, column)}
    while pending:
        row, column = pending.popleft()
        if row in (0, height - 1) or column in (0, width - 1):
            return False
        for neighbor in ((row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)):
            if neighbor not in seen and blank[neighbor]:
                seen.add(neighbor)
                pending.append(neighbor)
    return True


def tool_proof(run):
    errors, maximum_angle_rate, previous = int(run['tool'] != SPEC['tool']), 0, None
    for row in run['trace']:
        if row['contact']:
            errors += sum(not math.isfinite(row[key]) or abs(row[key] - expected) > 1e-12
                          for key, expected in (('angle_deg', 40), ('width_mm', .45), ('pressure', .5)))
            if previous is not None and row['time_s'] > previous['time_s']:
                maximum_angle_rate = max(maximum_angle_rate,
                    abs(row['angle_deg'] - previous['angle_deg']) / (row['time_s'] - previous['time_s']))
            previous = row
        else:
            errors += int(row['pressure'] != 0)
            previous = None
    return {'errors': errors, 'angle_rate_deg_s': maximum_angle_rate, 'edge': [0, 1],
            'mode': SPEC['tool'], 'active_rotation': False, 'active_edge': False, 'active_finishing': False}


def measure(candidate, fixture, budget, directory, *, counter=False):
    model = foundation.probe(candidate, fixture)
    paths = [target(fixture), foundation.nominal(model)]
    target_pixels, nominal_pixels = [budget.render(foundation.paint, path) for path in paths]
    runs, motion, comparisons = foundation.execute_refinements(model, 'i', budget, SPEC['frame_mm'])
    regions, local_actual, local_nominal, blanks = foundation.regions(fixture), {}, {}, {}
    for occurrence, bounds in regions.items():
        local_target = foundation.crop(target_pixels, bounds['loss'])
        local_actual[occurrence] = {label: foundation.stroke_loss(local_target, foundation.crop(run['images']['actual'], bounds['loss']))
                                    for label, run in runs.items()}
        local_nominal[occurrence] = foundation.stroke_loss(local_target, foundation.crop(nominal_pixels, bounds['loss']))
        blanks[occurrence] = {label: [foundation.fraction(pixels, blank) for blank in bounds['blank']]
            for label, pixels in [('target', target_pixels), ('nominal', nominal_pixels),
                                 *[(label, run['images']['actual']) for label, run in runs.items()]]}
    record = {'fixture': fixture, 'probe_sha256': object_digest(model),
        'compiled_sources': compile_gestures('i', model)['strokes'], 'regions_mm': regions,
        'actual_target': {label: foundation.stroke_loss(target_pixels, run['images']['actual']) for label, run in runs.items()},
        'nominal_target': foundation.stroke_loss(target_pixels, nominal_pixels),
        'local_actual_target': local_actual, 'local_nominal_target': local_nominal, 'blank_fractions': blanks,
        'motion': motion, 'comparisons': comparisons, 'tool': {label: tool_proof(run) for label, run in runs.items()},
        'diagnostic_contact_runs': [foundation.contact_runs(path) for path in paths]}
    if counter:
        record['counter'] = {label: {'blank_fraction': foundation.fraction(pixels, SPEC['counter_bounds_mm']),
                                    'enclosed': enclosed_blank(pixels, SPEC['counter_bounds_mm'])}
            for label, pixels in [('target', target_pixels), ('nominal', nominal_pixels),
                                 *[(label, run['images']['actual']) for label, run in runs.items()]]}
    record['null_supported'] = quality(record) and mechanical(record, counter=counter)
    record['diagnosis'] = ('nominal_geometry_already_exceeds_absolute_target_limit'
        if record['nominal_target'] > SPEC['criteria']['absolute_loss_max'] else 'inspect_actual_and_local_evidence')
    tiles = []
    for label, path in zip(('target', 'nominal', 'desired', 'actual'),
                          [*paths, *[foundation.primitives.learning._trajectory(runs['base'], kind) for kind in ('desired', 'actual')]]):
        pixels = budget.render(foundation.paint, path, dpi=SPEC['presentation_dpi'])
        Image.fromarray(pixels).save(directory / f"{fixture['id']}-{label}.png")
        tiles.append(pixels)
    foundation.primitives.compressed(directory / f"{fixture['id']}-traces.json.gz",
        {label: foundation.admission.stripped(run) for label, run in runs.items()})
    write_json(directory / f"{fixture['id']}.json", record)
    return record, tiles, runs['base']


def mechanical(record, *, counter=False):
    try:
        expected = foundation.regions(record['fixture'])
        if (not foundation.motion_pass(record) or record['regions_mm'] != expected
                or record['diagnostic_contact_runs'] != [len(record['fixture']['instances'])] * 2
                or set(record['tool']) != set(REFINEMENTS)):
            return False
        if any(row != {'errors': 0, 'angle_rate_deg_s': 0, 'edge': [0, 1], 'mode': SPEC['tool'],
                       'active_rotation': False, 'active_edge': False, 'active_finishing': False} for row in record['tool'].values()):
            return False
        if counter:
            return (set(record['counter']) == {'target', 'nominal', *REFINEMENTS}
                and all(row['enclosed'] is True and 0 <= row['blank_fraction'] <= .01 for row in record['counter'].values()))
        return (set(record['blank_fractions']) == set(expected) and all(
            set(values) == {'target', 'nominal', *REFINEMENTS} and all(
                len(fractions) == len(expected[occurrence]['blank']) and all(math.isfinite(value) and 0 <= value <= .01 for value in fractions)
                for fractions in values.values()) for occurrence, values in record['blank_fractions'].items()))
    except (KeyError, TypeError, ValueError):
        return False


def physical_samples(run, edge):
    return [ContactSample(*row['to_mm'], row['contact'], .45, row['pressure'], row['angle_deg'], *edge) for row in run['trace']]


def edge_error(samples, expected_edge):
    maximum = 0
    for sample in samples:
        if not sample.contact:
            continue
        corners = contact_corners(sample)
        angle = math.radians(sample.nib_angle_deg)
        for index, edge in enumerate(expected_edge):
            actual = [(corners[index * 2][axis] + corners[index * 2 + 1][axis]) / 2 for axis in (0, 1)]
            expected = [sample.x_mm + (edge - .5) * .45 * math.cos(angle),
                        sample.y_mm + (edge - .5) * .45 * math.sin(angle)]
            maximum = max(maximum, math.dist(actual, expected))
    return maximum


def controls(candidate, fixture, base, overlap, counter_run, budget, directory):
    model, records, evidence = foundation.probe(candidate, fixture), {}, {}
    for name in ('wrong-angle', 'undeclared-lift', 'overbuilt-terminal', 'desired-only-actual', 'missing-overlap', 'air-connector'):
        original = overlap if name == 'missing-overlap' else base
        expected = foundation.probe(candidate, foundation.SPEC['contexts'][0]) if name == 'missing-overlap' else model
        changed = copy.deepcopy(original)
        if name == 'wrong-angle':
            for row in changed['trace']:
                if row['contact']:
                    row['angle_deg'] += 15
        elif name == 'desired-only-actual':
            for row in changed['trace']:
                row['to_mm'] = row['desired_mm'][:]
        elif name == 'overbuilt-terminal':
            contact = [row for row in changed['trace'] if row['contact']]
            for row in contact[-20:]:
                row['to_mm'][0] += .3
                row['owner']['overlap_contributors'].append('undeclared-terminal-pass')
        else:
            row = next(row for row in changed['trace'] if (not row['contact'] if name == 'air-connector'
                else row['contact'] and (bool(row['owner']['overlap_contributors']) if name == 'missing-overlap' else True)))
            if name == 'undeclared-lift':
                row['contact'], row['pressure'] = False, 0
            elif name == 'air-connector':
                row['contact'], row['pressure'] = True, .5
            else:
                row['owner']['overlap_contributors'] = []
        frame = SPEC['context_frame_mm'] if name == 'missing-overlap' else SPEC['frame_mm']
        pixels = budget.render(foundation.paint, foundation.primitives.learning._trajectory(changed, 'actual'), frame=frame)
        loss = foundation.stroke_loss(original['images']['actual'], pixels)
        unmodified = foundation.audit_trace(expected, 'i', original)['errors'] + tool_proof(original)['errors']
        errors = foundation.audit_trace(expected, 'i', changed)['errors'] + tool_proof(changed)['errors']
        records[name] = {'unmodified_errors': unmodified, 'errors': errors, 'detected': unmodified == 0 and errors > 0,
                         'global_loss': loss, 'global_detected_at_0_1': loss >= .1}
        evidence[name] = foundation.admission.stripped(changed)
        Image.fromarray(pixels).save(directory / f'{name}.png')
    expected_edge = SPEC['edge_control']['expected']
    expected_path, swapped_path = [physical_samples(base, edge) for edge in (expected_edge, SPEC['edge_control']['swapped'])]
    edge_images = [budget.render(paint_trajectory, path, SPEC['frame_mm'], dpi=180, contact_version='physical-edge-v1')
                   for path in (expected_path, swapped_path)]
    before, after = edge_error(expected_path, expected_edge), edge_error(swapped_path, expected_edge)
    loss = foundation.stroke_loss(*edge_images)
    records['swapped-edge'] = {'expected_endpoint_error_mm': before, 'swapped_endpoint_error_mm': after,
        'detected': before <= 1e-10 < after, 'global_loss': loss, 'global_detected_at_0_1': loss >= .1,
        'candidate_action_activation': False, 'mode': 'physical-edge-v1', 'scope': 'asymmetric physical diagnostic on selected actual path only'}
    evidence['swapped-edge'] = {'expected': [asdict(row) for row in expected_path], 'swapped': [asdict(row) for row in swapped_path]}
    for label, pixels in zip(('expected-edge', 'swapped-edge'), edge_images):
        Image.fromarray(pixels).save(directory / f'{label}.png')
    for name, original, bounds in (('erased-counter', counter_run, SPEC['counter_bounds_mm']),
            ('filled-open-pocket', base, next(iter(foundation.regions(fixture).values()))['blank'][0])):
        pixels = original['images']['actual'].copy()
        budget.charge(1)
        foundation.crop(pixels, bounds)[:] = 0
        before, after = foundation.fraction(original['images']['actual'], bounds), foundation.fraction(pixels, bounds)
        loss = foundation.stroke_loss(original['images']['actual'], pixels)
        enclosed = enclosed_blank(original['images']['actual'], bounds) if name == 'erased-counter' else None
        records[name] = {'before': before, 'after': after, 'bounds_mm': bounds, 'enclosed_before': enclosed,
            'detected': 0 <= before <= .01 < after and (enclosed is True if name == 'erased-counter' else True),
            'global_loss': loss, 'global_detected_at_0_1': loss >= .1}
        Image.fromarray(pixels).save(directory / f'{name}.png')
    foundation.primitives.compressed(directory / 'control-evidence.json.gz', evidence)
    return records


def controls_pass(records):
    try:
        if set(records) != set(SPEC['controls']) or any(row['detected'] is not True or not finite([row['global_loss']])
                or row['global_detected_at_0_1'] is not (row['global_loss'] >= .1) for row in records.values()):
            return False
        for name, row in records.items():
            if name == 'swapped-edge':
                if not (0 <= row['expected_endpoint_error_mm'] <= 1e-10 < row['swapped_endpoint_error_mm'] < 1
                        and row['mode'] == 'physical-edge-v1' and row['candidate_action_activation'] is False):
                    return False
            elif name in ('erased-counter', 'filled-open-pocket'):
                if not 0 <= row['before'] <= .01 < row['after'] <= 1 or (name == 'erased-counter' and row['enclosed_before'] is not True):
                    return False
            elif not (row['unmodified_errors'] == 0 and row['errors'] > 0):
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def complete(record):
    try:
        return (record['optimization_evaluations'] == 0 and record['candidate_sha256'] == SPEC['candidate_object_sha256']
            and [row['fixture'] for row in record['fixtures']] == SPEC['fixtures']
            and all(set(row['actual_target']) == set(REFINEMENTS) and finite(row['actual_target'].values())
                and finite([row['nominal_target']]) and mechanical(row)
                and set(row['local_actual_target']) == set(foundation.regions(row['fixture']))
                and all(set(values) == set(REFINEMENTS) and finite(values.values()) for values in row['local_actual_target'].values())
                for row in record['fixtures'])
            and [row['fixture'] for row in record['contexts']] == foundation.SPEC['contexts']
            and all(foundation.motion_pass(row) for row in record['contexts'])
            and record['counter']['fixture'] == SPEC['counter_fixture'] and mechanical(record['counter'], counter=True)
            and controls_pass(record['controls']))
    except (KeyError, TypeError, ValueError):
        return False


def outcomes(record):
    result = {}
    measured = complete(record)
    for gesture in SPEC['required_gestures']:
        rows = [row for row in record.get('fixtures', []) if any(instance['gesture'] == gesture for instance in row['fixture']['instances'])]
        accepted = measured and bool(rows) and all(quality(row, gesture) for row in rows)
        result[gesture] = {'null_accepted': accepted, 'actions': {action: 'accepted-scoped-null' if accepted else 'unresolved'
            for action in ('rotation', 'edge', 'finishing')}, 'active_action_required': 'not established',
            'local_loss_max': max((max(row['local_actual_target'][str(index)].values()) for row in rows
                for index, instance in enumerate(row['fixture']['instances']) if instance['gesture'] == gesture), default=None)}
    return result


def worker(directory, seed, maximum, seconds):
    directory.mkdir(parents=True, exist_ok=False)
    budget = foundation.JournalBudget(directory, maximum, seconds)
    record = {'seed': seed, 'status': 'blocked', 'optimization_evaluations': 0, 'fixtures': [], 'contexts': [],
              'controls': {}, 'letter_training_allowed': False, 'real_accepted': False}
    try:
        source = load_inputs()
        candidate = source['candidates'][seed]
        record['candidate_sha256'] = object_digest(candidate)
        (directory / 'candidate.json').write_bytes((source['directory'] / f'seed-{seed}/first/candidate.json').read_bytes())
        record['original_controls'] = source['original_controls']
        sheets, control_base, overlap = [], None, None
        for fixture in SPEC['fixtures']:
            row, tiles, actual = measure(candidate, fixture, budget, directory)
            record['fixtures'].append(row)
            sheets.append((row, tiles))
            if fixture == SPEC['fixtures'][6]:
                control_base = actual
        for fixture in foundation.SPEC['contexts']:
            row, actual = foundation.evaluate_context(candidate, fixture, budget, directory)
            record['contexts'].append(row)
            if fixture == foundation.SPEC['contexts'][0]:
                overlap = actual
        record['counter'], _, counter_run = measure(candidate, SPEC['counter_fixture'], budget, directory, counter=True)
        record['controls'] = controls(candidate, SPEC['fixtures'][6], control_base, overlap, counter_run, budget, directory)
        budget.render(learning.sheet, directory / 'practice-sheet.png', sheets)
        record['outcomes'] = outcomes(record)
        record['status'] = 'complete' if complete(record) else 'blocked'
        learning.require_candidate(candidate)
        budget.check()
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        record['reason'] = str(error)
    record['renders'] = budget.used
    write_json(directory / 'report.json', record)
    budget.receipt()
    return record


def build(output):
    output = Path(output).resolve()
    if output.exists() or any(path.parent.name != 'run-001' for path in BASE.glob('run-*/S1-actions.json')):
        raise ValueError('Use an immutable single continuation; further retries need new authorization')
    write_json(output / 'freeze.json', {'spec': SPEC, 'code_sha256': identities()})
    report = {'stage': SPEC['stage'], 'status': 'blocked', 'evaluation_complete': False, 'code_sha256': identities(),
        'seeds': [], 'renders': 0, 'optimization_evaluations': 0, 'revision': 1, 'accepted_gestures': [],
        'S1_action_accepted': False, 'letter_training_allowed': False, 'real_accepted': False, 'promoted': False}
    ledger, records = [], []
    try:
        prior = prior_usage()
        report['prior_renders'] = sum(row['renders'] for row in prior.values())
        load_inputs()
        for seed in SPEC['seeds']:
            started, used = time.monotonic() - prior[seed]['seconds'], prior[seed]['renders']
            for label, hashseed in (('first', '7'), ('replay', '839')):
                remaining = 1800 - (time.monotonic() - started)
                if remaining <= 0 or used >= 5000:
                    raise RuntimeError('Combined seed budget exhausted')
                directory = output / f'seed-{seed}/{label}'
                try:
                    process = subprocess.run([sys.executable, '-m', 'scribesim.handvalidate.foundation_actions',
                        '--output', str(directory), '--worker-seed', str(seed), '--maximum', str(5000 - used), '--seconds', str(remaining)],
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
                if process.returncode or not receipt_path.exists():
                    raise RuntimeError('Worker failed: ' + process.stderr[-2000:])
            first, replay = output / f'seed-{seed}/first', output / f'seed-{seed}/replay'
            row = json.loads((first / 'report.json').read_text())
            matching = foundation.primitives.manifest(first) == foundation.primitives.manifest(replay)
            measured = row['status'] == 'complete' and complete(row) and matching and used <= 5000 and time.monotonic() - started <= 1800
            report['seeds'].append({'seed': seed, 'measured': measured, 'replay_match': matching, 'renders': used, 'outcomes': outcomes(row)})
            records.append(row)
        report['cumulative_renders'] = report['prior_renders'] + report['renders']
        report['evaluation_complete'] = len(records) == 3 and all(row['measured'] for row in report['seeds'])
        if report['evaluation_complete']:
            report['accepted_gestures'] = [gesture for gesture in SPEC['required_gestures'] if all(outcomes(row)[gesture]['null_accepted'] for row in records)]
            report['S1_action_accepted'] = report['accepted_gestures'] == SPEC['required_gestures'] and all(quality(row) for record in records for row in record['fixtures'])
            report['status'] = 'pass' if report['S1_action_accepted'] else 'fail'
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
    report['decision'] = 'Scoped fixed-null evidence only; letters remain blocked' if report['S1_action_accepted'] else 'STOP / REVISE unresolved scope; diagnose nominal target geometry before action fitting'
    report['missing_inventory'] = ['unresolved:' + gesture for gesture in SPEC['required_gestures'] if gesture not in report['accepted_gestures']]
    report['missing_inventory'] += ['seven-stroke compound/return carriers exceed unchanged grammar',
        'active physical actions not fitted or accepted', 'remaining gesture and letter/reference coverage', 'real G0/G1/G2 and owner review']
    write_json(output / 'execution.json', {'ledger': ledger})
    report['artifacts'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
    write_json(output / 'S1-actions.json', report)
    return report


def inspect_evidence(directory, *, expected_report_sha256):
    directory = Path(directory).resolve()
    try:
        if not expected_report_sha256 or digest(directory / 'S1-actions.json') != expected_report_sha256:
            raise ValueError('Consumer-pinned independent action manifest required')
        report = json.loads((directory / 'S1-actions.json').read_text())
        if report['stage'] != SPEC['stage'] or report['code_sha256'] != identities():
            raise ValueError('Stale independent action identities')
        if any(report[key] is not False for key in ('letter_training_allowed', 'real_accepted', 'promoted')):
            raise ValueError('Independent null evidence cannot approve letters or real scope')
        foundation.primitives.verify_artifacts(directory, report['artifacts'])
        if json.loads((directory / 'freeze.json').read_text()) != {'spec': SPEC, 'code_sha256': identities()}:
            raise ValueError('Independent evaluation freeze changed')
        source = load_inputs()
        prior = prior_usage()
        ledger = json.loads((directory / 'execution.json').read_text())['ledger']
        if ([(row['seed'], row['process']) for row in ledger] != [(seed, label) for seed in SPEC['seeds'] for label in ('first', 'replay')]
                or report['optimization_evaluations'] != 0 or report['revision'] != 1
                or report['prior_renders'] != sum(row['renders'] for row in prior.values())
                or report['cumulative_renders'] != report['prior_renders'] + report['renders']
                or report['renders'] != sum(row['renders'] for row in ledger)
                or [row['seed'] for row in report['seeds']] != SPEC['seeds']):
            raise ValueError('Incomplete independent seed accounting')
        records = []
        for seed in SPEC['seeds']:
            receipts = [row for row in ledger if row['seed'] == seed]
            used = prior[seed]['renders']
            for receipt in receipts:
                used += receipt['renders']
                if (type(receipt['renders']) is not int or receipt['renders'] <= 0 or used > 5000
                        or receipt['cumulative_seed_renders'] != used or not prior[seed]['seconds'] < receipt['cumulative_seed_seconds'] <= 1800):
                    raise ValueError('Independent seed budget invalid')
            first, replay = directory / f'seed-{seed}/first', directory / f'seed-{seed}/replay'
            if foundation.primitives.manifest(first) != foundation.primitives.manifest(replay):
                raise ValueError('Independent fresh-process proofs differ')
            if digest(first / 'candidate.json') != SPEC['candidate_file_sha256']:
                raise ValueError('Selected candidate bytes changed')
            record = json.loads((first / 'report.json').read_text())
            if (record['seed'] != seed or record['status'] != 'complete' or not complete(record)
                    or any(receipt['renders'] != record['renders'] for receipt in receipts)
                    or record['original_controls'] != source['original_controls']):
                raise ValueError('Independent numeric, control or enclosure proof failed')
            for row in [*record['fixtures'], record['counter']]:
                model = foundation.probe(source['candidates'][seed], row['fixture'])
                if row['probe_sha256'] != object_digest(model) or row['compiled_sources'] != compile_gestures('i', model)['strokes']:
                    raise ValueError('Detached compiled source proof')
            for row in record['contexts']:
                model = foundation.probe(source['candidates'][seed], row['fixture'])
                if row['probe_sha256'] != object_digest(model) or row['compiled'] != compile_gestures(row['fixture']['text'], model)['strokes']:
                    raise ValueError('Detached context proof')
            records.append(record)
        accepted = [gesture for gesture in SPEC['required_gestures'] if all(outcomes(row)[gesture]['null_accepted'] for row in records)]
        full = accepted == SPEC['required_gestures'] and all(quality(row) for record in records for row in record['fixtures'])
        if (report['evaluation_complete'] is not True or report['accepted_gestures'] != accepted
                or report['S1_action_accepted'] is not full or report['status'] != ('pass' if full else 'fail')):
            raise ValueError('Action admission flags disagree with numeric evidence')
        return {'report_sha256': expected_report_sha256, 'accepted_gestures': accepted, 'full_inventory_accepted': full,
                'letter_training_allowed': False, 'real_accepted': False, 'records': records}
    except (KeyError, TypeError, OSError, IndexError) as error:
        raise ValueError('Incomplete independent action evidence') from error


def require_readiness(directory, *, expected_report_sha256, required_gestures, tool='legacy-full-edge', real=False):
    require_scope(required_gestures, tool, real)
    evidence = inspect_evidence(directory, expected_report_sha256=expected_report_sha256)
    if not set(required_gestures) <= set(evidence['accepted_gestures']):
        raise ValueError('Unresolved required gesture/action scope blocks letter inventory')
    return {'stage': SPEC['stage'], 'report_sha256': expected_report_sha256, 'tool': tool,
        'required_gestures': sorted(set(required_gestures)), 'S1_action_accepted': True, 'kind': 'scoped-fixed-null',
        'letter_training_allowed': False, 'real_accepted': False,
        'scope': 'Only requested constructions under frozen independent transformations; no active action or universal null claim'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker-seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args()
    report = build(args.output) if args.worker_seed is None else worker(args.output, args.worker_seed, args.maximum, args.seconds)
    print(json.dumps({key: report[key] for key in ('status', 'renders', 'optimization_evaluations')}))


if __name__ == '__main__':
    main()
