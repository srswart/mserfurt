"""Independent derived-geometry raw-motion and saved-pixel checks; no fitting."""

from bisect import bisect_left
import argparse
import copy
from dataclasses import asdict, replace
import gzip
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from scripts import letter_context_physical as runner
from scribesim.evo.nib_contact import VERSION
from scribesim.handvalidate import upright_measurement as measurement
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.specimen import digest, object_digest, write_json


trajectory = measurement.trajectory
contained = measurement.contained


def change_kind(document):
    transforms = [row['transform'] for row in document['lineage']['occurrences']]
    stroke = any(row['width_scale'] != 1 for row in transforms)
    spacing = any(row['preceding_advance_offset'] != 0 for row in transforms)
    return 'stroke-and-spacing' if stroke and spacing else 'stroke-only' if stroke else 'spacing-only' if spacing else 'identity'


def require_change_kind(document, label):
    if label != change_kind(document):
        raise ValueError('Spacing-only or identity output mislabeled as stroke change')


def audit_document(contract, case, document, run):
    try:
        if case not in contract['cases']:
            raise ValueError('Unfrozen case')
        runner.preflight.verify_document(document, contract['candidate'], case['fixture'], case['refinement'])
        bundle, timed = runner.preflight.variants.prepare_plan(document, contract['candidate'], case['fixture'], case['refinement'])
        model = runner.preflight.variants.source_model(contract['candidate'], case['fixture'], case['refinement'])
        if (object_digest(asdict(timed)) != case['timing_sha256'] or object_digest(asdict(bundle)) != case['bundle_sha256']
                or [run['step_mm'], run['dt_s']] != contract['refinements'][case['refinement']]
                or run['model_sha256'] != object_digest(model)):
            raise ValueError('Changed cleared plan, fixed model or refinement')
        return audit_raw(document, case['fixture'], run,
            {'criteria': contract['criteria'], 'frame_mm': document['frame_mm']}, timed, bundle.owners)
    except (KeyError, TypeError, IndexError, ZeroDivisionError, OverflowError) as error:
        raise ValueError('Incomplete raw context evidence') from error


def paint(path, frame, dpi):
    if not contained(path, frame):
        raise ValueError('Incomplete finite-ink frame')
    return paint_trajectory(path, frame, dpi=dpi, contact_version=VERSION)


def case_measurements(contract, case, document, run, actual, desired, masks):
    proof = audit_document(contract, case, document, run)
    frame, windows = document['frame_mm'], contract['windows_mm'][case['fixture']['id']]
    for letter, bounds in windows.items():
        selected = {'trace': [row for row in run['trace'] if row['contact'] and row['owner']['letter'] == int(letter)]}
        if not contained(trajectory(selected), bounds):
            raise ValueError('Incomplete local actual frame')
    for pixels in (actual, desired, *masks.values()):
        expected = (math.ceil((frame[3]-frame[2])*contract['metric_dpi']/25.4),
                    math.ceil((frame[1]-frame[0])*contract['metric_dpi']/25.4))
        if pixels.shape[:2] != expected:
            raise ValueError('Wrong metric frame or DPI')
    compiled = document['compiled']['strokes']
    if set(masks) != {row['gesture_occurrence_id'] for row in compiled} or not all(np.any(mask) for mask in masks.values()):
        raise ValueError('Missing overlap mask owners')
    reference = {'status': 'not_applicable', 'quality_pass': None}
    if case['fixture']['role'] == 'known_regression' and case['refinement'] == 'base':
        placement = runner.preflight.foundation.placement
        source = {'registry': runner.preflight.foundation.read_json(placement.PREPARED/'registry.json'),
            'candidate': contract['candidate'],
            'core_identities': placement.contract.reconciliation.replay.identities()}
        reference = placement.reference_result(source, {key: value for key, value in case['fixture'].items() if key != 'role'}, actual)
    return {'case_id': case['id'], 'refinement': case['refinement'], 'change_kind': change_kind(document), 'motion': proof,
        'local_windows_mm': windows, 'nominal_levels': levels_derived(compiled, case['fixture']),
        'actual_levels': measurement.actual_levels(run, case['fixture']),
        'ports_mm': ports_derived(compiled, case['fixture'], run), 'overlap': overlap_derived(masks, compiled),
        'tracking_loss': float(measurement.stroke_loss(desired, actual)),
        'nominal_actual_losses_report_only': measurement.losses(desired, actual, windows, {'frame_mm': frame}),
        'known_reference': reference, 'comparison': None, **runner.FLAGS}


def case_pass(result, contract):
    try:
        json.dumps(result, allow_nan=False)
        criteria = contract['criteria']
        if not runner.scope_matches(result):
            return False
        case = next((row for row in contract['cases'] if row['id'] == result['case_id']), None)
        if case is None or result['refinement'] != case['refinement']:
            return False
        document = runner.document_for(contract, case)
        require_change_kind(document, result['change_kind'])
        local = {str(index) for index in range(len(case['fixture']['text']))}
        ports = {row['gesture_occurrence_id'] for row in document['compiled']['strokes']}
        if (set(result['nominal_levels']) != local or set(result['actual_levels']) != local or set(result['ports_mm']) != ports
                or result['local_windows_mm'] != contract['windows_mm'][case['fixture']['id']]):
            return False
        expected_reference = 'match' if case['fixture']['role'] == 'known_regression' and case['refinement'] == 'base' else 'not_applicable'
        if result['known_reference']['status'] != expected_reference:
            return False
        if (not measurement.motion_pass(result['motion'], criteria) or result['overlap']['undeclared_pairs']
                or not 0 <= result['tracking_loss'] <= criteria['actual_tracking_loss']
                or any(not 0 <= value <= criteria['nominal_landmark_max'] for value in result['nominal_levels'].values())
                or any(not 0 <= value <= criteria['actual_landmark_mm_max'] for value in
                    [*result['actual_levels'].values(), *result['ports_mm'].values()])
                or result['known_reference']['status'] not in ('match', 'not_applicable')):
            return False
        if result['refinement'] != 'base':
            comparison = result['comparison']
            if comparison['owner_match'] is not True or any(not 0 <= comparison[key] <= criteria[gate] for key, gate in
                    [('endpoint_mm', 'endpoint_mm'), ('event_time_s', 'event_time_s'), ('image_loss', 'convergence_loss')]):
                return False
        return True
    except (ValueError, KeyError, TypeError):
        return False


def measure_case(contract, case, document, run, budget, directory):
    proof = audit_document(contract, case, document, run)
    if not measurement.motion_pass(proof, contract['criteria']):
        raise ValueError('Raw physical motion rejected before rasterization')
    frame = document['frame_mm']
    paths = {kind: trajectory(run, kind) for kind in ('actual', 'desired')}
    pixels = {kind: budget.render(paint, path, frame, contract['metric_dpi']) for kind, path in paths.items()}
    masks = budget.render(measurement.overlap_masks, run, {'frame_mm': frame, 'metric_dpi': contract['metric_dpi']})
    for kind, image in pixels.items():
        Image.fromarray(image).save(directory/(kind+'.png'))
    for owner, mask in masks.items():
        Image.fromarray(mask).save(directory/f"owner-{owner.replace(':', '_')}.png")
    if case['presentation']:
        presentation = budget.render(paint, paths['actual'], frame, contract['presentation_dpi'])
        Image.fromarray(presentation).save(directory/'actual-full.png')
    result = case_measurements(contract, case, document, run, pixels['actual'], pixels['desired'], masks)
    return result, pixels['actual']


def controls(contract, case, document, run, pixels, budget=None, directory=None):
    result = {}
    for name in ('identity', 'bounds', 'unknown-rule', 'per-word', 'geometry', 'ports', 'overlap', 'frame'):
        changed = copy.deepcopy(document)
        if name in ('bounds', 'unknown-rule', 'per-word') and not changed['program']['rules']:
            changed['program']['rules'] = runner.preflight.variants.make_program({'n:stem-entry': (1, 0)})['rules']
        if name == 'identity':
            changed['program']['candidate_sha256'] = '0'*64
        elif name == 'bounds':
            changed['program']['rules'][0]['width_scale'] = 1.04
        elif name == 'unknown-rule':
            changed['program']['rules'][0]['id'] = 'unknown'
        elif name == 'per-word':
            changed['program']['rules'][0]['word'] = case['fixture']['text']
        elif name == 'geometry':
            changed['compiled']['strokes'][0]['cubics'][0][1][0] += .01
        elif name == 'ports':
            changed['compiled']['strokes'][1]['cubics'][0][0][0] += .01
        elif name == 'overlap':
            changed['compiled']['strokes'][-1]['overlap_contributors'] = []
        else:
            changed['frame_mm'][1] -= .1
        try:
            runner.preflight.verify_document(changed, contract['candidate'], case['fixture'], case['refinement'])
            result[name] = False
        except ValueError:
            result[name] = True
    intended = {'trace-owner': 'owner', 'trace-lift': 'contact', 'clock': 'clock', 'tool': 'tool', 'desired-as-actual': 'dynamics'}
    for name, gate in intended.items():
        changed = copy.deepcopy(run)
        selected = next(row for row in changed['trace'] if row['contact'] and row['dt_s'] > 0)
        if name == 'trace-owner':
            selected['owner']['occurrence_id'] = 'invented'
        elif name == 'trace-lift':
            selected['contact'] = False
        elif name == 'clock':
            selected['dt_s'] += .001
        elif name == 'tool':
            selected['width_mm'] = .46
        else:
            for row in changed['trace']:
                row['to_mm'] = row['desired_mm'][:]
        try:
            result[name] = audit_document(contract, case, document, changed)['errors'][gate] > 0
        except ValueError as error:
            if name != 'tool' or str(error) != 'Unsupported physical contact fields':
                raise
            result[name] = True
    if budget is not None:
        shifted = [replace(point, x_mm=point.x_mm+contract['visible_shift_mm']) for point in trajectory(run)]
        image = budget.render(paint, shifted, document['frame_mm'], contract['metric_dpi'])
        Image.fromarray(image).save(directory/'visible-shift.png')
    else:
        image = np.asarray(Image.open(directory/'visible-shift.png'))
    result['visible-shift'] = float(measurement.stroke_loss(pixels, image)) > contract['visible_shift_detection_loss']
    program = runner.preflight.variants.make_program({row['id']: (1, row['advance_delta']) for row in document['program']['rules']})
    spacing = runner.preflight.variants.compile_variant(contract['candidate'], case['fixture'], program, case['refinement'])
    try:
        require_change_kind(spacing, 'stroke-only')
        result['spacing-mislabel'] = False
    except ValueError:
        result['spacing-mislabel'] = True
    return result


def verify_worker(contract, directory, seed):
    record = runner.preflight.foundation.read_json(directory/'report.json')
    if (record['status'] != 'pass' or record['seed'] != seed
            or not runner.scope_matches(record)
            or type(record['controller_executions']) is not int or record['controller_executions'] != len(contract['cases'])
            or [row['id'] for row in record['cases']] != [row['id'] for row in contract['cases']]):
        raise ValueError('Incomplete worker case inventory or scope')
    comparisons, reconstructed = {}, []
    for case in contract['cases']:
        case_dir = directory/case['id']
        if runner.preflight.foundation.read_json(case_dir/'attempt.json') != {'case_id': case['id'], 'controller': 'complete'}:
            raise ValueError('Missing or incomplete controller reservation')
        with gzip.open(case_dir/'trace.json.gz', 'rt') as stream:
            run = json.load(stream)
        document = runner.preflight.foundation.read_json(case_dir/'document.json')
        actual = np.asarray(Image.open(case_dir/'actual.png'))
        desired = np.asarray(Image.open(case_dir/'desired.png'))
        masks = {owner: np.asarray(Image.open(case_dir/f"owner-{owner.replace(':', '_')}.png"), dtype=bool)
            for owner in dict.fromkeys(row['gesture_occurrence_id'] for row in document['compiled']['strokes'])}
        expected = case_measurements(contract, case, document, run, actual, desired, masks)
        group = (case['fixture']['id'], object_digest(case['program']))
        if case['refinement'] == 'base':
            comparisons[group] = run, actual
        else:
            baseline, baseline_pixels = comparisons[group]
            expected['comparison'] = measurement.comparison(baseline, run, baseline_pixels, actual)
            if case['refinement'] == list(contract['refinements'])[-1]:
                del comparisons[group]
        expected['passed'] = case_pass(expected, contract)
        if expected != runner.preflight.foundation.read_json(case_dir/'measurement.json') or not expected['passed']:
            raise ValueError('Stored verdict differs from independent raw measurement')
        if case['presentation']:
            frame = document['frame_mm']
            expected_size = (math.ceil((frame[1]-frame[0])*900/25.4), math.ceil((frame[3]-frame[2])*900/25.4))
            with Image.open(case_dir/'actual-full.png') as image:
                if image.size != expected_size:
                    raise ValueError('Incomplete presentation frame')
        reconstructed.append({'id': case['id'], 'passed': True})
        if case['id'] == contract['control_case_id']:
            control_result = controls(contract, case, document, run, actual, directory=directory)
            if (control_result != record['controls'] or set(control_result) != set(contract['controls'])
                    or control_result != runner.preflight.foundation.read_json(directory/'controls.json')
                    or not all(control_result.values())):
                raise ValueError('Negative controls differ or do not detect corruption')
    if reconstructed != record['cases']:
        raise ValueError('Worker decisions differ')
    return record


def inspect(directory, expected_report_sha256, contract_sha256):
    directory = Path(directory)
    if not expected_report_sha256 or digest(directory/'report.json') != expected_report_sha256:
        raise ValueError('External physical report pin required')
    contract = runner.load_contract(contract_sha256)
    report = runner.preflight.foundation.read_json(directory/'report.json')
    if (digest(directory/'contract.json') != contract_sha256 or report['status'] != 'pass'
            or not runner.scope_matches(report)
            or report['artifacts'] != runner.artifact_map(directory, {'report.json'})):
        raise ValueError('Incomplete physical result, artifact inventory or scope')
    ledger = runner.preflight.foundation.read_json(directory/'execution.json')['ledger']
    required = [(seed, process['label']) for seed in contract['budget']['seeds'] for process in contract['processes']]
    if ledger != report['ledger'] or [(row['seed'], row['process']) for row in ledger] != required:
        raise ValueError('Incomplete combined seed ledger')
    summaries = []
    for seed in contract['budget']['seeds']:
        root = directory/f'seed-{seed}'
        if runner.artifact_map(root/'first', {'execution.json'}) != runner.artifact_map(root/'replay', {'execution.json'}):
            raise ValueError('Fresh replay differs')
        used, elapsed = 0, 0
        for entry in [row for row in ledger if row['seed'] == seed]:
            worker_dir = root/entry['process']
            record = verify_worker(contract, worker_dir, seed)
            receipt = runner.preflight.foundation.read_json(worker_dir/'execution.json')
            permit = runner.preflight.foundation.read_json(root/f"{entry['process']}-permit.json")
            expected_renders = 3*len(contract['cases'])+sum(row['presentation'] for row in contract['cases'])+1
            if (type(receipt['renders']) is not int or receipt['renders'] != expected_renders
                    or record['renders'] != expected_renders or entry['renders'] != expected_renders
                    or len(receipt['events']) != expected_renders
                    or [event['operation'] for event in receipt['events']] != runner.render_schedule(contract)
                    or any(event['ordinal'] != index or event['status'] != 'complete'
                           for index, event in enumerate(receipt['events'], 1))
                    or permit['maximum'] != 5000-used or receipt['maximum_renders'] != permit['maximum']
                    or permit['seconds'] != receipt['maximum_seconds'] or permit['contract_sha256'] != contract_sha256
                    or permit['seed'] != seed or permit['label'] != entry['process']
                    or not 0 < permit['seconds'] <= 2700-elapsed
                    or not 0 <= receipt['elapsed_seconds'] <= permit['seconds']
                    or receipt['elapsed_seconds'] > entry['cumulative_seconds']-elapsed
                    or not math.isfinite(entry['cumulative_seconds']) or not elapsed <= entry['cumulative_seconds'] <= 2700):
                raise ValueError('Render journal, allowance or combined time mismatch')
            used += expected_renders
            if used != entry['cumulative_renders'] or used > 5000:
                raise ValueError('Combined render ledger mismatch')
            elapsed = entry['cumulative_seconds']
        summaries.append({'seed': seed, 'replay_match': True})
    if summaries != report['seeds']:
        raise ValueError('Incomplete seed decision')
    return {'status': 'pass', 'read_only': True, 'report_sha256': expected_report_sha256,
        'contract_sha256': contract_sha256, 'cases_verified': len(contract['cases'])*6,
        'historical_style_numeric_pass': False, 'appearance_review': 'pending', **runner.FLAGS}


def overlap_derived(masks, compiled):
    rows = compiled
    declarations = {row['gesture_occurrence_id']: row['overlap_contributors'] for row in rows}
    pairs = []
    names = list(masks)
    for index, current in enumerate(names):
        for previous in names[:index]:
            area = int(np.count_nonzero(masks[current] & masks[previous]))
            pairs.append({'previous': previous, 'current': current, 'intersection_pixels': area,
                          'declared': previous in declarations[current]})
    coverage = sum(mask.astype(int) for mask in masks.values())
    return {'pairs': pairs, 'repeated_pixels': int(np.count_nonzero(coverage > 1)),
            'union_pixels': int(np.count_nonzero(coverage)),
            'undeclared_pairs': sum(row['intersection_pixels'] > 0 and not row['declared'] for row in pairs)}


def ports_derived(compiled, fixture, run):
    groups, previous = {}, None
    for row in run['trace']:
        if row['contact']:
            owner = row['owner']['gesture_occurrence_id']
            if previous is not None and previous != owner:
                groups[previous][-1] = row
            groups.setdefault(owner, [row, row])[-1] = row
            previous = owner
        else:
            previous = None
    result = {}
    for owner in dict.fromkeys(row['gesture_occurrence_id'] for row in compiled):
        selected = [row for row in compiled if row['gesture_occurrence_id'] == owner]
        endpoints = [selected[0]['cubics'][0][0], selected[-1]['cubics'][-1][-1]]
        expected = np.asarray(endpoints)*[3.5, -3.5]+[0, 10]
        result[owner] = max(math.dist(event['to_mm'], position) for event, position in zip(groups[owner], expected)) if owner in groups else 1e9
    return result


def levels_derived(compiled, fixture):
    if fixture['kind'] == 'primitive':
        return {}
    rows = compiled
    result = {}
    for letter in range(len(fixture['text'])):
        selected = [row for row in rows if row['letter'] == letter]
        low, high = measurement.extrema([curve for row in selected for curve in row['cubics']])
        errors = [abs(low-fixture['shift'][1]), abs(high-fixture['shift'][1]-1)]
        for owner in dict.fromkeys(row['gesture_occurrence_id'] for row in selected):
            group = [row for row in selected if row['gesture_occurrence_id'] == owner]
            expected = {'stem': (1, 0), 'overturn': (0, 0), 'underturn': (1, 1)}[group[0]['gesture']]
            errors.extend([abs(group[0]['cubics'][0][0][1]-fixture['shift'][1]-expected[0]),
                           abs(group[-1]['cubics'][-1][-1][1]-fixture['shift'][1]-expected[1])])
        result[str(letter)] = max(errors)
    return result


def audit_raw(document, fixture, run, spec, timed, owners):
    try:
        json.dumps(run, allow_nan=False)
    except ValueError as error:
        raise ValueError('Nonfinite raw evidence') from error
    compiled = document['compiled']['strokes']
    plan, trace = timed.plan, run['trace']
    errors = {name: 0 for name in ('identity', 'owner', 'contact', 'clock', 'desired', 'dynamics', 'tool', 'corner')}
    errors['identity'] += int(run['document_sha256'] != object_digest(document) or run['text'] != fixture['text']
        or run['tool'] != VERSION or run['version'] != timed.version or object_digest(run['plan']) != object_digest(asdict(plan))
        or object_digest(run['corners']) != object_digest(timed.corners) or object_digest(run['arrivals']) != object_digest(timed.arrivals))
    times = [point.t_s for point in plan.samples]
    previous, seen, runs = None, set(), []
    projection, corridor, acceleration, corner_speed, corner_error, entry_speed, entry_error = (0.0,)*7
    for row in trace:
        index = row['plan_index']
        if type(index) is not int or not 0 <= index < len(owners):
            errors['owner'] += 1
            continue
        expected_owner, point = owners[index], plan.samples[index]
        errors['owner'] += int(row['owner'] != expected_owner)
        errors['contact'] += int(row['contact'] != point.contact)
        duration = row['time_s']-row['time_before']
        errors['clock'] += int(duration < 0 or abs(duration-row['dt_s']) > 1e-12 or duration > run['dt_s']+1e-12)
        if previous is not None:
            errors['clock'] += int(row['time_before'] != previous['time_s'] or index < previous['plan_index'])
            errors['dynamics'] += int(row['from_mm'] != previous['to_mm'] or row['velocity_before_mm_s'] != previous['velocity_mm_s'])
            errors['contact'] += int(row['previous_contact'] != previous['contact'])
        elif row['time_before'] != 0:
            errors['clock'] += 1
        if duration > 0:
            target_index = min(max(1, bisect_left(times, row['time_s'])), len(times)-1)
            before, after = plan.samples[target_index-1], plan.samples[target_index]
            fraction = (row['time_s']-before.t_s)/(after.t_s-before.t_s)
            expected_position = [before.x_mm+fraction*(after.x_mm-before.x_mm), before.y_mm+fraction*(after.y_mm-before.y_mm)]
            acceleration = max(acceleration, math.dist(row['velocity_before_mm_s'], row['velocity_mm_s'])/duration)
        else:
            expected_position = [point.x_mm, point.y_mm]
            errors['dynamics'] += int(row['from_mm'] != row['to_mm'] or row['velocity_before_mm_s'] != row['velocity_mm_s'])
        errors['desired'] += int(math.dist(expected_position, row['desired_mm']) > 1e-8)
        unconstrained = [position+(before+after)*duration/2 for position, before, after in
                         zip(row['from_mm'], row['velocity_before_mm_s'], row['velocity_mm_s'])]
        residual = math.dist(unconstrained, row['to_mm'])
        projection = max(projection, residual)
        errors['dynamics'] += int(math.dist(unconstrained, row['unconstrained_mm']) > 1e-10
                                  or abs(residual-row['projection_mm']) > 1e-10)
        errors['tool'] += int(row['width_mm'] != (.45 if row['contact'] else 0) or abs(row['angle_deg']-40) > 1e-10 or row['realized_edge'] != [0, 1]
            or row['pressure'] != (.5 if row['contact'] else 0) or row['fatigue'] != 0 or row['ink_before'] != row['ink_after'])
        if row['contact']:
            seen.add(expected_owner.get('occurrence_id'))
            corridor = max(corridor, math.dist(row['to_mm'], row['desired_mm']))
            contact_run = expected_owner.get('contact_run_id')
            if previous is None or not previous['contact'] or contact_run != runs[-1]:
                runs.append(contact_run)
        previous = row
    required = {row['occurrence_id'] for row in compiled}
    errors['owner'] += len(required.symmetric_difference(seen))
    expected_runs = list(dict.fromkeys(row['contact_run_id'] for row in compiled))
    errors['contact'] += int(runs != expected_runs)
    errors['clock'] += int(not trace or abs(trace[-1]['time_s']-plan.total_time_s) > spec['criteria']['clock_s'])
    for label, events in [('corner', timed.corners), ('entry', timed.arrivals)]:
        for event in events:
            matches = [row for row in trace if row['plan_index'] == event['plan_index'] and
                       abs(row['time_s']-plan.samples[event['plan_index']].t_s) <= 1e-12]
            if len(matches) != 1 or not matches[0]['contact']:
                errors['corner'] += 1
                continue
            row = matches[0]
            speed, error = math.hypot(*row['velocity_mm_s']), math.dist(row['to_mm'], row['desired_mm'])
            if label == 'corner':
                corner_speed, corner_error = max(corner_speed, speed), max(corner_error, error)
            else:
                entry_speed, entry_error = max(entry_speed, speed), max(entry_error, error)
    desired_acceleration, desired_discontinuities = 0.0, 0
    for before, after in zip(plan.samples, plan.samples[1:]):
        duration = after.t_s-before.t_s
        change = math.dist((before.vx_mm_s, before.vy_mm_s), (after.vx_mm_s, after.vy_mm_s))
        if duration > 0:
            desired_acceleration = max(desired_acceleration, change/duration)
        else:
            desired_discontinuities += int(change > 1e-9 or math.dist((before.x_mm, before.y_mm), (after.x_mm, after.y_mm)) > 1e-9)
    metrics = {'projection_mm': projection, 'corridor_mm': corridor, 'actual_acceleration_mm_s2': acceleration,
        'desired_acceleration_mm_s2': desired_acceleration, 'desired_discontinuities': desired_discontinuities,
        'contact_speed_mm_s': max(point.speed_mm_s for point in plan.samples if point.contact),
        'corner_speed_mm_s': corner_speed, 'corner_error_mm': corner_error, 'entry_speed_mm_s': entry_speed,
        'entry_error_mm': entry_error, 'clock_error_s': abs(trace[-1]['time_s']-plan.total_time_s) if trace else 1e9}
    return {'errors': errors, 'metrics': metrics, 'contact_runs': runs, 'expected_contact_runs': expected_runs,
            'contained': all(contained(trajectory(run, kind), spec['frame_mm']) for kind in ('actual', 'desired'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', type=Path, required=True)
    parser.add_argument('--report-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.inspect, args.report_sha256, args.contract_sha256), indent=2))


if __name__ == '__main__':
    main()
