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
            if previous == current - 1 and instances[current]['transition'] in {'smooth', 'corner'}:
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
