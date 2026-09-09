"""Opt-in fixed-tool continuous connections; no learned-geometry admission."""

import math

import numpy as np


SCHEMA = 'shared-stroke-gestures-connected-v1'
LANGUAGE_SCHEMA = 'shared-stroke-language-connected-v1'
EXPANDED_CAP = 6


def validate_extensions(model):
    if (model['x_height_mm'] != 3.5 or model['nib_width_mm'] != .45
            or model['nib_angle_deg'] != 40 or model['letter_rules'] or model['word_rules']):
        raise ValueError('Connected contract requires fixed tool/scale and no context')
    if any(recipe['logical'] not in {'i', 'n', 'u', 'm'} for recipe in model['recipes'].values()):
        raise ValueError('Connected construction inventory is limited to i/n/u/m')
    if 'actions' in model:
        fixed = {'frame': 'physical-y-down', 'orientation': [[0, 40], [1, 40]],
                 'edge': [[0, 0, 1], [1, 0, 1]], 'pressure': .5, 'speed_mm_s': 12}
        if model['sampling'] != 'gesture-arc-v3' or model['actions'] != {'fixed': fixed}:
            raise ValueError('Connected contract requires boundary sampling and fixed actions')
    for primitive in model['primitives'].values():
        for before, after in zip(primitive['cubics'], primitive['cubics'][1:]):
            incoming, outgoing = np.subtract(before[-1], before[-2]), np.subtract(after[1], after[0])
            product = float(np.linalg.norm(incoming) * np.linalg.norm(outgoing))
            if math.dist(before[-1], after[0]) > 1e-10 or product <= 1e-12 or np.dot(incoming, outgoing) < (1-1e-6) * product:
                raise ValueError('Internal cubic join must be smooth; expose corners as primitive boundaries')
        for name, start, end in [('entry', primitive['cubics'][0][0], primitive['cubics'][0][1]),
                                  ('exit', primitive['cubics'][-1][-2], primitive['cubics'][-1][-1])]:
            delta = np.subtract(end, start)
            magnitude = float(np.linalg.norm(delta))
            if magnitude <= 1e-10 or not np.allclose(delta / magnitude, primitive[name], rtol=0, atol=1e-8):
                raise ValueError('Connected primitive ports must match actual tangents')


def require_joins(rows):
    for previous, current in zip(rows, rows[1:]):
        if current['transition'] in {'start', 'lift'}:
            continue
        incoming, outgoing = np.asarray(previous['cubics'][-1]), np.asarray(current['cubics'][0])
        if math.dist(incoming[-1], outgoing[0]) > 1e-10:
            raise ValueError('Connected ports must coincide')
        before, after = incoming[-1] - incoming[-2], outgoing[1] - outgoing[0]
        product = float(np.linalg.norm(before) * np.linalg.norm(after))
        if product <= 1e-12 or (current['transition'] == 'smooth' and np.dot(before, after) < (1-1e-6) * product):
            raise ValueError('Connected smooth join requires matching tangents; reversals require corner')


def _envelope(rows):
    parameters = np.linspace(0, 1, 257)[:, None]
    points, error = [], 0.0
    for row in rows:
        for cubic in np.asarray(row['cubics']):
            points.extend((1-parameters)**3*cubic[0] + 3*(1-parameters)**2*parameters*cubic[1]
                          + 3*(1-parameters)*parameters**2*cubic[2] + parameters**3*cubic[3])
            error = max(error, 3 * float(np.linalg.norm(np.diff(cubic, axis=0), axis=1).max()) / 256)
    return np.asarray(points), error


def require_overlap_owners(rows, instances, nib_extent):
    groups = [[row for row in rows if row['gesture_index'] == index] for index in range(len(instances))]
    envelopes = [_envelope(group) for group in groups]
    for current, (points, error) in enumerate(envelopes):
        for previous in range(current):
            other, other_error = envelopes[previous]
            overlap = np.linalg.norm(points[:, None] - other[None, :], axis=2) <= nib_extent + error + other_error
            if previous == current - 1 and instances[current]['transition'] == 'smooth':
                port = np.asarray(groups[current][0]['cubics'][0][0])
                local = 2 * (nib_extent + error + other_error)
                overlap &= ~((np.linalg.norm(points-port, axis=1) <= local)[:, None]
                             & (np.linalg.norm(other-port, axis=1) <= local)[None, :])
            if overlap.any() and previous not in instances[current]['overlap_with']:
                raise ValueError('Undeclared finite-width/retracing overlap contributor')


def annotate_runs(rows):
    run = -1
    for row in rows:
        if row['transition'] in {'start', 'lift'}:
            run += 1
        row['contact_run_id'] = f'contact:{run}'


def execution_metrics(strokes, owners, indices, trajectory, execution, timed):
    indexed = {row['occurrence_id']: row for row in strokes}
    seen, runs = set(), []
    errors = int(len(indices) != len(trajectory) or len(execution) != len(trajectory))
    previous_run = None
    for point, index, event in zip(trajectory, indices, execution):
        owner = owners[index]
        errors += int(point.contact != event['contact'])
        if not point.contact:
            previous_run = None
            continue
        original = indexed.get(owner.get('occurrence_id'))
        if original is None:
            errors += 1
            continue
        seen.add(original['occurrence_id'])
        keys = ('primitive_sha256', 'gesture_occurrence_id', 'gesture_sha256', 'action_profile',
                'action_sha256', 'span', 'contact_run_id', 'overlap_contributors')
        errors += int(owner.get('kind') != 'stroke' or any(owner.get(key) != original[key] for key in keys))
        run = owner.get('contact_run_id')
        if run != previous_run:
            runs.append(run)
        previous_run = run
    errors += len(set(indexed).symmetric_difference(seen))
    expected_runs = list(dict.fromkeys(row['contact_run_id'] for row in strokes))
    errors += int(runs != expected_runs)
    corner_errors, speeds, distances = 0, [], []
    for corner in timed.corners:
        matches = [(point, event) for point, index, event in zip(trajectory, indices, execution)
                   if index == corner['plan_index'] and event['time_s'] == corner['time_s']]
        if len(matches) != 1:
            corner_errors += 1
            continue
        point, event = matches[0]
        corner_errors += int(not point.contact or not event['contact'])
        speeds.append(math.hypot(*event['velocity_mm_s']))
        distances.append(math.dist((point.x_mm, point.y_mm), corner['position_mm']))
    return {'owner_errors': errors, 'corner_errors': corner_errors,
            'corner_speed_mm_s': max(speeds, default=0),
            'corner_position_error_mm': max(distances, default=0)}
