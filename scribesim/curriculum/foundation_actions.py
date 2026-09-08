"""Bounded fixed-tool null experiment; selected evidence is not S1-action admission."""

import argparse
import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures
from scribesim.handvalidate import foundation_gestures as foundation
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = foundation.BASE.parent / 'actions'
SPEC_PATH = BASE / 'spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
REFINEMENTS = ('base', 'arc', 'time', 'subdivision')
OLD_ACTION_SPEC = BASE.parent.parent / 'actions/spec-v1.json'


def identities():
    return {**foundation.identities(), **{str(path.relative_to(ROOT)): digest(path)
            for path in (Path(__file__), SPEC_PATH, OLD_ACTION_SPEC)}}


def require_candidate(candidate):
    validate_gestures(candidate)
    if object_digest(candidate) != SPEC['candidate_object_sha256']:
        raise ValueError('Frozen primitive, gesture, tool and recipe identities required')


def load_inputs():
    directory = (BASE / SPEC['source']).resolve()
    admitted = foundation.require_readiness(directory, expected_report_sha256=SPEC['source_report_sha256'],
                                             required_gestures=SPEC['required_gestures'])
    if (json.loads(OLD_ACTION_SPEC.read_text())['activation']['null_actual_loss_max']
            != SPEC['criteria']['null_actual_target_loss_max']):
        raise ValueError('The existing absolute null criterion cannot be relaxed')
    candidates = {}
    for seed in SPEC['seeds']:
        path = directory / f'seed-{seed}/first/candidate.json'
        if digest(path) != SPEC['candidate_file_sha256']:
            raise ValueError('Frozen candidate file mismatch')
        candidates[seed] = json.loads(path.read_text())
        require_candidate(candidates[seed])
    return {'admission': admitted, 'candidates': candidates, 'directory': directory}


def selection(candidate):
    require_candidate(candidate)
    return {'kind': 'predeclared-fixed-null-hypothesis', 'model_sha256': object_digest(candidate),
            'model_file_sha256': SPEC['candidate_file_sha256'], 'spec_sha256': digest(SPEC_PATH),
            'action_profile': candidate['actions']['fixed'], 'required_gestures': SPEC['required_gestures'],
            'selection_method': SPEC['selection'], 'target_pixels_accessed_at_selection': False,
            'optimization_evaluations': 0, 'S1_action_accepted': False}


def target(fixture):
    return foundation.contact_trajectory((part['occurrence'], part['points'])
                                         for part in foundation.target_parts(fixture))


def finite_losses(values):
    return bool(values) and all(type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in values)


def quality_pass(row):
    try:
        return (set(row['actual_target']) == set(REFINEMENTS) and bool(row['local_actual_target'])
            and finite_losses(row['actual_target'].values())
            and max(row['actual_target'].values()) <= SPEC['criteria']['null_actual_target_loss_max']
            and all(set(values) == set(REFINEMENTS) and finite_losses(values.values())
                    and max(values.values()) <= SPEC['criteria']['local_actual_target_loss_max']
                    for values in row['local_actual_target'].values()))
    except (KeyError, TypeError, ValueError):
        return False


def diagnose(row):
    if row['nominal_target'] > SPEC['criteria']['null_actual_target_loss_max']:
        return 'target_mismatch_already_present_in_frozen_nominal_geometry'
    if max(row['actual_target'].values()) > SPEC['criteria']['null_actual_target_loss_max']:
        return 'actual_execution_or_rendering_requires_investigation'
    return 'inspect_occurrence_local_and_scope_guards_before_any_null_claim'


def tool_errors(run):
    errors = int(run['tool'] != SPEC['tool']['contact_version'])
    for row in run['trace']:
        if row['contact']:
            errors += sum(not math.isfinite(row[key]) or abs(row[key] - expected) > 1e-12 for key, expected in
                          (('angle_deg', SPEC['tool']['angle_deg']), ('pressure', SPEC['tool']['pressure']),
                           ('width_mm', SPEC['tool']['width_mm'])))
        else:
            errors += int(row['pressure'] != 0)
    return errors


def measure(candidate, fixture, budget, directory):
    model = foundation.probe(candidate, fixture)
    paths = [target(fixture), foundation.nominal(model)]
    target_pixels, nominal_pixels = [budget.render(foundation.paint, path) for path in paths]
    runs, motion, comparisons = foundation.execute_refinements(model, 'i', budget, SPEC['frame_mm'])
    regions = foundation.regions(fixture)
    local_actual, local_nominal, blanks = {}, {}, {}
    for occurrence, bounds in regions.items():
        local_target = foundation.crop(target_pixels, bounds['loss'])
        local_nominal[occurrence] = foundation.stroke_loss(local_target, foundation.crop(nominal_pixels, bounds['loss']))
        local_actual[occurrence] = {label: foundation.stroke_loss(local_target, foundation.crop(run['images']['actual'], bounds['loss']))
                                    for label, run in runs.items()}
        blanks[occurrence] = {label: [foundation.fraction(pixels, blank) for blank in bounds['blank']]
            for label, pixels in [('target', target_pixels), ('nominal', nominal_pixels),
                                  *[(label, run['images']['actual']) for label, run in runs.items()]]}
    record = {'fixture': fixture, 'probe_sha256': object_digest(model),
              'compiled_sources': compile_gestures('i', model)['strokes'],
              'nominal_target': foundation.stroke_loss(target_pixels, nominal_pixels),
              'actual_target': {label: foundation.stroke_loss(target_pixels, run['images']['actual']) for label, run in runs.items()},
              'local_actual_target': local_actual, 'local_nominal_target': local_nominal,
              'regions_mm': regions, 'blank_fractions': blanks, 'motion': motion, 'comparisons': comparisons,
              'tool_errors': {label: tool_errors(run) for label, run in runs.items()},
              'contact_runs': [foundation.contact_runs(path) for path in paths]}
    record['null_supported'] = quality_pass(record) and mechanics_pass(record)
    record['diagnosis'] = diagnose(record)
    write_json(directory / (fixture['id'] + '.json'), record)
    foundation.primitives.compressed(directory / (fixture['id'] + '-traces.json.gz'),
                                     {label: foundation.admission.stripped(run) for label, run in runs.items()})
    tiles = []
    for label, path in zip(('target', 'nominal', 'desired', 'actual'),
                           [*paths, *[foundation.primitives.learning._trajectory(runs['base'], kind) for kind in ('desired', 'actual')]]):
        pixels = budget.render(foundation.paint, path, dpi=900)
        Image.fromarray(pixels).save(directory / f"{fixture['id']}-{label}.png")
        tiles.append(pixels)
    return record, tiles, runs['base']


def mechanics_pass(record):
    try:
        expected = foundation.regions(record['fixture'])
        return (foundation.motion_pass(record) and record['contact_runs'] == [len(record['fixture']['instances'])] * 2
            and record['regions_mm'] == expected and set(record['blank_fractions']) == set(expected)
            and set(record['tool_errors']) == set(REFINEMENTS) and all(value == 0 for value in record['tool_errors'].values())
            and all(set(values) == {'target', 'nominal', *REFINEMENTS} and all(
                len(fractions) == len(expected[occurrence]['blank']) and
                all(math.isfinite(value) and 0 <= value <= .01 for value in fractions)
                for fractions in values.values()) for occurrence, values in record['blank_fractions'].items()))
    except (KeyError, ValueError, TypeError):
        return False


def controls(candidate, fixture, base, budget, directory):
    model = foundation.probe(candidate, fixture)
    records, evidence = {}, {}
    for name in ('wrong-angle', 'partial-edge-request'):
        changed = copy.deepcopy(candidate)
        if name == 'wrong-angle':
            changed['actions']['fixed']['orientation'] = [[0, 50], [1, 50]]
        else:
            changed['actions']['fixed']['edge'] = [[0, .5, 1], [1, .5, 1]]
        try:
            require_candidate(changed)
            detected = False
        except ValueError:
            detected = True
        records[name] = {'detected': detected, 'guard': 'frozen full-edge model contract',
                         'physical_active_action_evaluated': False}
        evidence[name] = changed
    valid = foundation.audit_trace(model, 'i', base)['errors'] == 0 and tool_errors(base) == 0
    for name in ('undeclared-lift', 'overbuilt-contributor', 'desired-only-actual'):
        changed = copy.deepcopy(base)
        row = next(row for row in changed['trace'] if row['contact'] and math.dist(row['to_mm'], row['desired_mm']) > .0001)
        if name == 'undeclared-lift':
            row['contact'], row['pressure'] = False, 0
        elif name == 'overbuilt-contributor':
            row['owner']['overlap_contributors'].append('unfrozen-finishing-pass')
        else:
            for row in changed['trace']:
                row['to_mm'] = row['desired_mm'][:]
        audit = foundation.audit_trace(model, 'i', changed)
        pixels = budget.render(foundation.paint, foundation.primitives.learning._trajectory(changed, 'actual'))
        loss = foundation.stroke_loss(base['images']['actual'], pixels)
        records[name] = {'unmodified_pass': valid, 'errors': audit['errors'], 'detected': valid and audit['errors'] > 0,
                         'global_loss': loss, 'global_detected_at_0_1': loss >= .1}
        evidence[name] = foundation.admission.stripped(changed)
        Image.fromarray(pixels).save(directory / f'{name}.png')
    changed = copy.deepcopy(base)
    for row in changed['trace']:
        if row['contact']:
            row['angle_deg'] += 10
    pixels = budget.render(foundation.paint, foundation.primitives.learning._trajectory(changed, 'actual'))
    loss = foundation.stroke_loss(base['images']['actual'], pixels)
    records['wrong-angle'].update(actual_tool_errors=tool_errors(changed), unmodified_pass=valid,
                                  global_loss=loss, global_detected_at_0_1=loss >= .1)
    records['wrong-angle']['detected'] &= valid and tool_errors(changed) > 0
    evidence['wrong-angle-trace'] = foundation.admission.stripped(changed)
    Image.fromarray(pixels).save(directory / 'wrong-angle.png')
    bounds = next(iter(foundation.regions(fixture).values()))['blank'][0]
    pixels = base['images']['actual'].copy()
    budget.charge(1)
    foundation.crop(pixels, bounds)[:] = 0
    before, after = foundation.fraction(base['images']['actual'], bounds), foundation.fraction(pixels, bounds)
    loss = foundation.stroke_loss(base['images']['actual'], pixels)
    records['filled-open-pocket'] = {'before': before, 'after': after, 'bounds_mm': bounds,
        'detected': 0 <= before <= .01 < after, 'global_loss': loss, 'global_detected_at_0_1': loss >= .1}
    Image.fromarray(pixels).save(directory / 'filled-open-pocket.png')
    foundation.primitives.compressed(directory / 'control-evidence.json.gz', evidence)
    return records


def controls_pass(records):
    try:
        return (set(records) == set(SPEC['controls']) and all(row['detected'] is True for row in records.values())
            and records['wrong-angle']['unmodified_pass'] and records['wrong-angle']['actual_tool_errors'] > 0
            and all(records[name]['unmodified_pass'] and records[name]['errors'] > 0
                    for name in ('undeclared-lift', 'overbuilt-contributor', 'desired-only-actual'))
            and 0 <= records['filled-open-pocket']['before'] <= .01 < records['filled-open-pocket']['after'] <= 1)
    except (KeyError, TypeError, ValueError):
        return False


def measurement_complete(record):
    try:
        return (record['optimization_evaluations'] == 0 and record['candidate_sha256'] == SPEC['candidate_object_sha256']
            and [row['fixture'] for row in record['fixtures']] == SPEC['fixtures']
            and all(set(row['actual_target']) == set(REFINEMENTS) and finite_losses(row['actual_target'].values())
                and math.isfinite(row['nominal_target']) and row['nominal_target'] >= 0 and mechanics_pass(row)
                and set(row['local_actual_target']) == set(foundation.regions(row['fixture']))
                and set(row['local_nominal_target']) == set(row['local_actual_target'])
                and finite_losses(row['local_nominal_target'].values())
                and all(set(values) == set(REFINEMENTS) and finite_losses(values.values()) for values in row['local_actual_target'].values())
                for row in record['fixtures'])
            and [row['fixture'] for row in record['contexts']] == foundation.SPEC['contexts']
            and all(foundation.motion_pass(row) for row in record['contexts']) and controls_pass(record['controls']))
    except (KeyError, TypeError, ValueError):
        return False


def null_supported(record):
    return measurement_complete(record) and all(quality_pass(row) for row in record['fixtures'])


def dispositions(record):
    result = {}
    for gesture in SPEC['required_gestures']:
        occurrences = [(row, str(index)) for row in record['fixtures'] for index, instance in enumerate(row['fixture']['instances'])
                       if instance['gesture'] == gesture]
        supported = measurement_complete(record) and bool(occurrences) and all(
            max(row['local_actual_target'][index].values()) <= SPEC['criteria']['local_actual_target_loss_max'] for row, index in occurrences)
        result[gesture] = {'actions': {name: 'null-hypothesis-supported' if supported else 'unresolved'
                                      for name in ('rotation', 'edge', 'finishing')},
                           'active_action_required': 'not established', 'S1_action_accepted': False,
                           'local_loss_max': max((max(row['local_actual_target'][index].values()) for row, index in occurrences), default=None)}
    return result


def sheet(path, rows):
    width, height = rows[0][1][0].shape[1], rows[0][1][0].shape[0]
    image = Image.new('RGB', (4 * width, 70 + len(rows) * (height + 50)), 'white')
    draw, font = ImageDraw.Draw(image), ImageFont.load_default(size=18)
    for column, label in enumerate(('Independent target', 'Frozen null nominal', 'Sampled desired', 'Actual controller')):
        draw.text((column * width + 8, 15), label, fill='black', font=font)
    for index, (record, tiles) in enumerate(rows):
        top = 60 + index * (height + 50)
        label = f"{record['fixture']['id']} | actual/target {record['actual_target']['base']:.4f} / cap 0.0500 | {'supported' if record['null_supported'] else 'UNRESOLVED'}"
        draw.text((8, top), label, fill='black', font=font)
        for column, tile in enumerate(tiles):
            image.paste(Image.fromarray(tile), (column * width, top + 38))
    image.save(path)


def worker(directory, seed, maximum, seconds):
    directory.mkdir(parents=True, exist_ok=False)
    budget = foundation.JournalBudget(directory, maximum, seconds)
    record = {'seed': seed, 'status': 'blocked', 'optimization_evaluations': 0, 'fixtures': [], 'contexts': [],
              'controls': {}, 'S1_action_accepted': False, 'letter_training_allowed': False, 'null_supported': False}
    try:
        source = load_inputs()
        candidate = source['candidates'][seed]
        record['candidate_sha256'] = object_digest(candidate)
        (directory / 'candidate.json').write_bytes((source['directory'] / f'seed-{seed}/first/candidate.json').read_bytes())
        write_json(directory / 'selection.json', selection(candidate))
        sheets, control_base = [], None
        for fixture in SPEC['fixtures']:
            row, tiles, base = measure(candidate, fixture, budget, directory)
            record['fixtures'].append(row)
            sheets.append((row, tiles))
            if fixture['id'] == 'held_out-forward-pair':
                control_base = base
        for fixture in foundation.SPEC['contexts']:
            row, _ = foundation.evaluate_context(candidate, fixture, budget, directory)
            record['contexts'].append(row)
        control_fixture = next(row for row in SPEC['fixtures'] if row['id'] == 'held_out-forward-pair')
        record['controls'] = controls(candidate, control_fixture, control_base, budget, directory)
        budget.render(sheet, directory / 'practice-sheet.png', sheets)
        require_candidate(candidate)
        record['status'] = 'complete' if measurement_complete(record) else 'blocked'
        record['null_supported'] = null_supported(record)
        record['dispositions'] = dispositions(record)
        budget.check()
    except (ValueError, RuntimeError, KeyError, TypeError, OSError) as error:
        record['status'], record['reason'] = 'blocked', str(error)
    record['renders'] = budget.used
    write_json(directory / 'report.json', record)
    budget.receipt()
    return record


def build(output):
    output = Path(output).resolve()
    if output.exists() or any(BASE.glob('run-*/report.json')):
        raise ValueError('Use an immutable first attempt; a rerun requires a diagnosed cumulative continuation')
    report = {'version': SPEC['version'], 'status': 'blocked', 'code_sha256': identities(),
              'renders': 0, 'optimization_evaluations': 0, 'seeds': [], 'null_supported': False,
              'S1_action_accepted': False, 'letter_training_allowed': False, 'promoted': False, 'real_accepted': False}
    write_json(output / 'freeze.json', {'spec': SPEC, 'code_sha256': identities()})
    ledger = []
    try:
        load_inputs()
        for seed in SPEC['seeds']:
            started, used = time.monotonic(), 0
            for label, hashseed in (('first', '0'), ('replay', '839')):
                remaining = 1800 - (time.monotonic() - started)
                if remaining <= 0 or used >= 5000:
                    raise RuntimeError('Combined seed allowance exhausted')
                directory = output / f'seed-{seed}/{label}'
                try:
                    process = subprocess.run([sys.executable, '-m', 'scribesim.curriculum.foundation_actions',
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
                    raise RuntimeError('Worker accounting failure: ' + process.stderr[-2000:])
            first, replay = output / f'seed-{seed}/first', output / f'seed-{seed}/replay'
            record = json.loads((first / 'report.json').read_text())
            matching = foundation.primitives.manifest(first) == foundation.primitives.manifest(replay)
            complete = record['status'] == 'complete' and matching and used <= 5000 and time.monotonic() - started <= 1800 and measurement_complete(record)
            report['seeds'].append({'seed': seed, 'replay_match': matching, 'renders': used, 'complete': complete,
                                    'null_supported': complete and null_supported(record), 'dispositions': record.get('dispositions', {})})
        complete = len(report['seeds']) == 3 and all(row['complete'] for row in report['seeds'])
        report['status'] = 'complete' if complete else 'blocked'
        report['null_supported'] = complete and all(row['null_supported'] for row in report['seeds'])
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
    report['decision'] = ('Freeze supported null hypothesis for independent HANDVALIDATE-017; no S1-action yet'
                          if report['null_supported'] else 'Null sufficiency unresolved; preserve candidates and diagnose target-versus-nominal error before any action fitting')
    write_json(output / 'execution.json', {'ledger': ledger})
    report['artifacts'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
    write_json(output / 'report.json', report)
    return report


def require_candidates(directory, *, expected_report_sha256):
    directory = Path(directory).resolve()
    try:
        if not expected_report_sha256 or digest(directory / 'report.json') != expected_report_sha256:
            raise ValueError('Consumer-pinned selected-candidate report required')
        report = json.loads((directory / 'report.json').read_text())
        if report['status'] != 'complete' or report['version'] != SPEC['version'] or report['code_sha256'] != identities():
            raise ValueError('Stale or incomplete selected evidence')
        if any(report[key] is not False for key in ('S1_action_accepted', 'letter_training_allowed', 'promoted', 'real_accepted')):
            raise ValueError('Learning evidence cannot promote a layer')
        foundation.primitives.verify_artifacts(directory, report['artifacts'])
        if json.loads((directory / 'freeze.json').read_text()) != {'spec': SPEC, 'code_sha256': identities()}:
            raise ValueError('Changed experiment freeze')
        source = load_inputs()
        ledger = json.loads((directory / 'execution.json').read_text())['ledger']
        if [(row['seed'], row['process']) for row in ledger] != [(seed, label) for seed in SPEC['seeds'] for label in ('first', 'replay')]:
            raise ValueError('Incomplete fresh-process ledger')
        if report['renders'] != sum(row['renders'] for row in ledger) or report['optimization_evaluations'] != 0:
            raise ValueError('Incomplete render/optimization accounting')
        supported, candidates = [], {}
        if [row['seed'] for row in report['seeds']] != SPEC['seeds']:
            raise ValueError('Missing required seed')
        for seed in SPEC['seeds']:
            receipts = [row for row in ledger if row['seed'] == seed]
            if (sum(row['renders'] for row in receipts) > 5000 or any(not 0 < row['cumulative_seed_seconds'] <= 1800 for row in receipts)
                    or receipts[-1]['cumulative_seed_renders'] != sum(row['renders'] for row in receipts)):
                raise ValueError('Combined seed budget failed')
            first, replay = directory / f'seed-{seed}/first', directory / f'seed-{seed}/replay'
            if foundation.primitives.manifest(first) != foundation.primitives.manifest(replay):
                raise ValueError('Fresh-process artifacts differ')
            if digest(first / 'candidate.json') != SPEC['candidate_file_sha256'] or json.loads((first / 'selection.json').read_text()) != selection(source['candidates'][seed]):
                raise ValueError('Selection or candidate lineage changed')
            record = json.loads((first / 'report.json').read_text())
            if record['status'] != 'complete' or not measurement_complete(record) or any(record['renders'] != row['renders'] for row in receipts):
                raise ValueError('Missing numeric measurement proof')
            for row in record['fixtures']:
                model = foundation.probe(source['candidates'][seed], row['fixture'])
                if row['probe_sha256'] != object_digest(model) or row['compiled_sources'] != compile_gestures('i', model)['strokes']:
                    raise ValueError('Detached compiled source evidence')
            supported.append(null_supported(record))
            candidates[seed] = str(first / 'candidate.json')
        if report['null_supported'] is not all(supported):
            raise ValueError('Null outcome disagrees with absolute measurements')
        return {'candidate_evaluation_permitted': True, 'null_hypothesis_supported': all(supported),
                'S1_action_accepted': False, 'letter_training_allowed': False, 'report_sha256': expected_report_sha256,
                'candidates': candidates, 'scope': SPEC['hypothesis']}
    except (KeyError, OSError, TypeError) as error:
        raise ValueError('Incomplete selected-candidate evidence') from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker-seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args()
    result = build(args.output) if args.worker_seed is None else worker(args.output, args.worker_seed, args.maximum, args.seconds)
    print(json.dumps({key: result[key] for key in ('status', 'renders', 'optimization_evaluations', 'null_supported')}))


if __name__ == '__main__':
    main()
