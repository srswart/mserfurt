"""Recompute continuous-contact evidence from raw events, not builder verdicts."""

from bisect import bisect_left
from dataclasses import asdict
import math
import json

import numpy as np
from PIL import Image, ImageDraw

from scribesim.curriculum.stroke_learning import stroke_loss
from scribesim.evo.nib_contact import ContactSample, VERSION, contact_corners, swept_polygon
from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handflow.curve_tangents import retime_curve_tangents
from scribesim.handvalidate.specimen import object_digest
from scribesim.pathguide.gesture_actions import action_bundle


def trajectory(run, kind='actual'):
    if kind == 'actual':
        return [ContactSample(*row['to_mm'], row['contact'], row['width_mm'] if row['contact'] else .45, row['pressure'], row['angle_deg'],
                              *row['realized_edge']) for row in run['trace']]
    return [ContactSample(row['x_mm'], row['y_mm'], row['contact'], .45, row['pressure'], row['nib_angle_deg'],
                          row['edge_start'], row['edge_end']) for row in run['plan']['samples']]


def contained(path, frame):
    left, right, top, bottom = frame
    return bool(path) and all(left <= horizontal <= right and top <= vertical <= bottom
        for point in path if point.contact for horizontal, vertical in contact_corners(point))


def extrema(curves):
    values = []
    for curve in curves:
        start, first, second, end = np.asarray(curve, dtype=float)[:, 1]
        polynomial = np.polynomial.Polynomial([start, 3*(first-start), 3*(second-2*first+start), end-3*second+3*first-start])
        parameters = [0, 1, *[float(root.real) for root in polynomial.deriv().roots() if abs(root.imag) < 1e-12 and 0 < root.real < 1]]
        values.extend(float(polynomial(parameter)) for parameter in parameters)
    return min(values), max(values)


def levels(model, fixture):
    if fixture['kind'] == 'primitive':
        return {}
    rows = compile_gestures(fixture['text'], model)['strokes']
    result = {}
    for letter in range(len(fixture['text'])):
        selected = [row for row in rows if row['letter'] == letter]
        low, high = extrema([curve for row in selected for curve in row['cubics']])
        errors = [abs(low-fixture['shift'][1]), abs(high-fixture['shift'][1]-1)]
        for owner in dict.fromkeys(row['gesture_occurrence_id'] for row in selected):
            group = [row for row in selected if row['gesture_occurrence_id'] == owner]
            expected = {'stem': (1, 0), 'overturn': (0, 0), 'underturn': (1, 1)}[group[0]['gesture']]
            errors.extend([abs(group[0]['cubics'][0][0][1]-fixture['shift'][1]-expected[0]),
                           abs(group[-1]['cubics'][-1][-1][1]-fixture['shift'][1]-expected[1])])
        result[str(letter)] = max(errors)
    return result


def actual_levels(run, fixture):
    if fixture['kind'] == 'primitive':
        return {}
    baseline = 10-3.5*fixture['shift'][1]
    result = {}
    for letter in range(len(fixture['text'])):
        points = [row['to_mm'][1] for row in run['trace'] if row['contact'] and row['owner'].get('letter') == letter]
        result[str(letter)] = max(abs(max(points)-baseline), abs(min(points)-(baseline-3.5))) if points else 1e9
    return result


def port_errors(model, fixture, run):
    compiled = compile_gestures(fixture['text'], model)['strokes']
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


def slant_diagnostics(run):
    result = []
    for occurrence in dict.fromkeys(row['owner']['occurrence_id'] for row in run['trace'] if row['contact']):
        rows = [row for row in run['trace'] if row['contact'] and row['owner']['occurrence_id'] == occurrence]
        delta = np.subtract(rows[-1]['to_mm'], rows[0]['to_mm'])
        angles = [math.degrees(math.atan2(row['velocity_mm_s'][0], abs(row['velocity_mm_s'][1])))
                  for row in rows if math.hypot(*row['velocity_mm_s']) > 1e-8]
        result.append({'occurrence_id': occurrence, 'primitive': rows[0]['owner']['primitive'],
            'chord_deg_from_vertical': math.degrees(math.atan2(delta[0], abs(delta[1]))),
            'moving_tangent_deg_min': min(angles, default=0), 'moving_tangent_deg_max': max(angles, default=0)})
    return result


def audit(model, fixture, run, spec):
    try:
        json.dumps(run, allow_nan=False)
    except ValueError as error:
        raise ValueError('Nonfinite raw evidence') from error
    bundle = action_bundle(fixture['text'], model, step_mm=run['step_mm'], include_curve_positions=True)
    compiled = compile_gestures(fixture['text'], model)['strokes']
    timed = retime_curve_tangents(bundle.plan, bundle.owners, compiled)
    owners = [bundle.owners[index] for index in timed.source_indices]
    plan, trace = timed.plan, run['trace']
    errors = {name: 0 for name in ('identity', 'owner', 'contact', 'clock', 'desired', 'dynamics', 'tool', 'corner')}
    errors['identity'] += int(run['model_sha256'] != object_digest(model) or run['text'] != fixture['text']
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


def motion_pass(proof, criteria):
    metrics = proof['metrics']
    return (not any(proof['errors'].values()) and proof['contained'] and
        all(math.isfinite(value) for value in metrics.values()) and metrics['desired_discontinuities'] == 0 and
        all(metrics[key] <= criteria[key]+(1e-8 if 'acceleration' in key else 0) for key in
            ('projection_mm', 'corridor_mm', 'actual_acceleration_mm_s2', 'desired_acceleration_mm_s2', 'contact_speed_mm_s', 'corner_speed_mm_s')) and
        max(metrics['corner_error_mm'], metrics['entry_error_mm']) <= criteria['actual_landmark_mm_max'] and
        metrics['entry_speed_mm_s'] <= criteria['corner_speed_mm_s'] and metrics['clock_error_s'] <= criteria['clock_s'])


def crop(pixels, bounds, frame):
    left, right, top, bottom = frame
    xmin, xmax, ymin, ymax = bounds
    if not left <= xmin < xmax <= right or not top <= ymin < ymax <= bottom:
        raise ValueError('Incomplete local frame')
    height, width = pixels.shape[:2]
    return pixels[math.floor((ymin-top)/(bottom-top)*height):math.ceil((ymax-top)/(bottom-top)*height),
                  math.floor((xmin-left)/(right-left)*width):math.ceil((xmax-left)/(right-left)*width)]


def losses(target, pixels, regions, spec):
    return {'global': float(stroke_loss(target, pixels)), 'local': {name: float(stroke_loss(
        crop(target, bounds, spec['frame_mm']), crop(pixels, bounds, spec['frame_mm']))) for name, bounds in regions.items()}}


def overlap_masks(run, spec):
    left, right, top, bottom = spec['frame_mm']
    resolution = spec['metric_dpi']/25.4
    size = math.ceil((right-left)*resolution), math.ceil((bottom-top)*resolution)
    masks, previous = {}, None
    path = trajectory(run)
    for row, sample in zip(run['trace'], path):
        if not row['contact']:
            previous = None
            continue
        owner = row['owner']['gesture_occurrence_id']
        contributors = [owner]
        polygon = swept_polygon(sample, sample)
        if previous is not None:
            before, before_sample = previous
            polygon = swept_polygon(before_sample, sample)
            contributors.append(before['owner']['gesture_occurrence_id'])
        mapped = [((horizontal-left)*resolution, (vertical-top)*resolution) for horizontal, vertical in polygon]
        for contributor in set(contributors):
            mask = masks.setdefault(contributor, Image.new('1', size))
            ImageDraw.Draw(mask).polygon(mapped, fill=1)
        previous = row, sample
    return {name: np.array(mask, dtype=bool) for name, mask in masks.items()}


def overlap_proof(masks, model, text):
    rows = compile_gestures(text, model)['strokes']
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


def exact_events(run):
    plan, trace = run['plan']['samples'], run['trace']
    if not plan or not trace:
        raise ValueError('Complete event source required')
    required = {}
    for index, point in enumerate(plan):
        if not point['contact']:
            continue
        if index == 0 or not plan[index-1]['contact']:
            required[index] = 'entry'
        if index == len(plan)-1 or not plan[index+1]['contact']:
            if index in required:
                raise ValueError('Degenerate contact run')
            required[index] = 'end'
    stops = {index for index, point in enumerate(plan) if point['contact'] and point['speed_mm_s'] == 0}-required.keys()
    corners = {row['plan_index']: row for row in run['corners']}
    if len(corners) != len(run['corners']) or stops != corners.keys():
        raise ValueError('Incomplete or duplicate declared corner events')
    for index, corner in corners.items():
        point = plan[index]
        if (index in required or not point['contact'] or abs(corner['time_s']-point['t_s']) > 1e-12
                or math.dist(corner['position_mm'], [point['x_mm'], point['y_mm']]) > 1e-8):
            raise ValueError('Changed declared corner')
        required[index] = 'corner'
    events = []
    for index, kind in sorted(required.items()):
        instant = plan[index]['t_s']
        matches = [row for row in trace if row['plan_index'] == index and row['contact']
                   and abs(row['time_s']-instant) <= 1e-12]
        if len(matches) != 1:
            raise ValueError('Exact unique actual event required')
        row = matches[0]
        owner = row['owner']
        if kind == 'corner' and owner['occurrence_id'] != corners[index]['occurrence_id']:
            raise ValueError('Corner event owner mismatch')
        events.append({'kind': kind, 'contact_run_id': owner['contact_run_id'],
            'occurrence_id': owner['occurrence_id'], 'gesture_occurrence_id': owner['gesture_occurrence_id'],
            'boundary_contributors': owner.get('boundary_contributors', []),
            'time_s': row['time_s'], 'position_mm': row['to_mm']})
    return events


def comparison(first, second, first_pixels, second_pixels):
    version = 'declared-contact-events-v1'
    try:
        before, after = exact_events(first), exact_events(second)
        identities = lambda events: [{key: value for key, value in event.items() if key not in {'time_s', 'position_mm'}} for event in events]
        if identities(before) != identities(after):
            raise ValueError('Event inventory or ownership differs')
        pairs = list(zip(before, after))
        return {'owner_match': True, 'event_version': version, 'event_ids': identities(before),
            'endpoint_mm': max(math.dist(left['position_mm'], right['position_mm']) for left, right in pairs),
            'event_time_s': max(abs(left['time_s']-right['time_s']) for left, right in pairs),
            'image_loss': float(stroke_loss(first_pixels, second_pixels))}
    except (ValueError, KeyError, IndexError, TypeError) as error:
        return {'owner_match': False, 'event_version': version, 'reason': str(error),
                'endpoint_mm': 1e9, 'event_time_s': 1e9, 'image_loss': 1e9}
