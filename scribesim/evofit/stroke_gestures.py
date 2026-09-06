"""Opt-in continuous gesture composition over the unchanged shared primitive engine."""

import argparse
import copy
from dataclasses import asdict
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.evofit import stroke_language as legacy
from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.controller import GuidedHandFlowController
from scribesim.handvalidate.bridge import neutral_profile, paint_trajectory
from scribesim.handvalidate.model import TrajectorySample
from scribesim.handvalidate.specimen import object_digest, write_json
from scribesim.pathguide.model import DensePathGuide, GuideSample, GuideSource
from scribesim.pathguide.repertoire import RepertoireGuide, _sample_cubic


SCHEMA = 'shared-stroke-gestures-v2'
EXTRA_FIELDS = {'gestures', 'actions', 'sampling', 'migration_source_sha256'}
INSTANCE_FIELDS = {'gesture', 'offset', 'scale', 'rotation_deg', 'transition', 'overlap_with'}
ACTION_FIELDS = {'frame', 'orientation', 'edge', 'pressure', 'speed_mm_s'}


def _lower(model):
    lowered = {key: copy.deepcopy(model[key]) for key in legacy.MODEL_FIELDS if key != 'recipes'}
    lowered['schema_version'] = legacy.SCHEMA
    lowered['recipes'], bindings = {}, {}
    for identifier, recipe in model['recipes'].items():
        if set(recipe) != {'logical', 'visible', 'advance', 'gestures'} or not 1 <= len(recipe['gestures']) <= 4:
            raise ValueError('Recipe must own bounded gesture references, not residual geometry')
        strokes, owners = [], []
        for group_index, instance in enumerate(recipe['gestures']):
            if set(instance) != INSTANCE_FIELDS or instance['gesture'] not in model['gestures']:
                raise ValueError('Unknown gesture instance')
            if (instance['transition'] != ('start' if group_index == 0 else 'lift')
                    or not isinstance(instance['overlap_with'], list)
                    or any(type(index) is not int or not 0 <= index < group_index for index in instance['overlap_with'])
                    or len(set(instance['overlap_with'])) != len(instance['overlap_with'])):
                raise ValueError('Explicit lift and earlier overlap contributors required')
            if (len(instance['offset']) != 2 or not all(legacy._number(value, -2, 2) for value in instance['offset'])
                    or not legacy._number(instance['scale'], .5, 1.5)
                    or not legacy._number(instance['rotation_deg'], -20, 20)):
                raise ValueError('Gesture placement bounds')
            angle = math.radians(instance['rotation_deg'])
            cosine, sine = math.cos(angle), math.sin(angle)
            gesture = model['gestures'][instance['gesture']]
            for local_index, stroke in enumerate(gesture['strokes']):
                if set(stroke) != legacy.STROKE_FIELDS:
                    raise ValueError('Gesture must reference shared primitives')
                horizontal, vertical = stroke['offset']
                offset = ([instance['offset'][axis] + stroke['offset'][axis] for axis in (0, 1)]
                          if instance['scale'] == 1 and instance['rotation_deg'] == 0 else
                          [instance['offset'][0] + instance['scale'] * (cosine * horizontal - sine * vertical),
                           instance['offset'][1] + instance['scale'] * (sine * horizontal + cosine * vertical)])
                strokes.append({**stroke,
                                'offset': offset,
                                'scale': instance['scale'] * stroke['scale'],
                                'rotation_deg': instance['rotation_deg'] + stroke['rotation_deg'],
                                'transition': instance['transition'] if local_index == 0 else stroke['transition']})
                owners.append({'gesture': instance['gesture'], 'gesture_index': group_index,
                               'gesture_primitive_index': local_index, 'action_profile': gesture['action'],
                               'overlap_with': instance['overlap_with']})
        lowered['recipes'][identifier] = {key: recipe[key] for key in ('logical', 'visible', 'advance')}
        lowered['recipes'][identifier].update(strokes=strokes, allow_crossings=any(row['overlap_with'] for row in owners))
        bindings[identifier] = owners
    return lowered, bindings


def validate_gestures(model):
    try:
        if (set(model) != legacy.MODEL_FIELDS | EXTRA_FIELDS or model['schema_version'] != SCHEMA
                or model['sampling'] not in {'legacy-v1', 'gesture-arc-v2', 'gesture-arc-v3'}
                or model['letter_rules'] or model['word_rules']):
            raise ValueError('Explicit gesture schema/sampling required; context overlays are not supported yet')
        if not isinstance(model['migration_source_sha256'], str) or len(model['migration_source_sha256']) != 64:
            raise ValueError('Migration/source identity required')
        if not 1 <= len(model['gestures']) <= 8 or not 1 <= len(model['actions']) <= 8:
            raise ValueError('Gesture/profile budget')
        for identifier, action in model['actions'].items():
            if (not isinstance(identifier, str) or not identifier or set(action) != ACTION_FIELDS
                    or action['frame'] != 'physical-y-down'
                    or action['pressure'] != .5 or action['speed_mm_s'] != 12):
                raise ValueError('Unsupported action frame/pressure/speed contract')
            for name, width in (('orientation', 2), ('edge', 3)):
                track = action[name]
                if not isinstance(track, list) or not 2 <= len(track) <= 4:
                    raise ValueError('Action knot budget')
                previous = -1
                for knot in track:
                    if (len(knot) != width or not all(legacy._number(value, -180, 540) for value in knot)
                            or not previous < knot[0] <= 1):
                        raise ValueError('Finite ordered arc-progress knots required')
                    previous = knot[0]
                    if name == 'edge' and not (0 <= knot[1] < knot[2] <= 1 and knot[2] - knot[1] >= .1):
                        raise ValueError('Invalid active edge interval')
                if track[0][0] != 0 or track[-1][0] != 1:
                    raise ValueError('Track endpoints required')
        for identifier, gesture in model['gestures'].items():
            if (not isinstance(identifier, str) or not identifier or set(gesture) != {'strokes', 'action'}
                    or gesture['action'] not in model['actions'] or not 1 <= len(gesture['strokes']) <= 4):
                raise ValueError('Flat bounded gestures and supported action IDs required')
            if any(stroke['transition'] not in ({'start'} if index == 0 else {'smooth', 'corner'})
                   for index, stroke in enumerate(gesture['strokes'])):
                raise ValueError('One continuous gesture cannot contain a hidden lift')
            probe = {key: copy.deepcopy(model[key]) for key in legacy.MODEL_FIELDS}
            probe.update(schema_version=legacy.SCHEMA, recipes={'i': {'logical': 'i', 'visible': 'i',
                         'advance': 1, 'allow_crossings': False, 'strokes': gesture['strokes']}})
            legacy.validate_language(probe)
            expanded = legacy._recipe_strokes(probe['recipes']['i'], probe)
            for previous, current in zip(expanded, expanded[1:]):
                if current['transition'] == 'smooth':
                    before = legacy._direction(previous['cubics'][-1][-2], previous['cubics'][-1][-1])
                    after = legacy._direction(current['cubics'][0][0], current['cubics'][0][1])
                    if sum(left * right for left, right in zip(before, after)) < 1 - 1e-6:
                        raise ValueError('Smooth gesture join must have matching tangent direction')
        lowered, bindings = _lower(model)
        legacy.validate_language(lowered)
        for identifier, recipe in lowered['recipes'].items():
            expanded = legacy._recipe_strokes(recipe, lowered)
            for group_index in range(len(model['recipes'][identifier]['gestures'])):
                rows = [row for row, owner in zip(expanded, bindings[identifier]) if owner['gesture_index'] == group_index]
                length = sum(math.dist(first[:2], second[:2]) for row in rows for cubic in row['cubics']
                             for first, second in zip(_sample_cubic(cubic, .02), _sample_cubic(cubic, .02)[1:])) * model['x_height_mm']
                action = model['actions'][model['gestures'][model['recipes'][identifier]['gestures'][group_index]['gesture']]['action']]
                for name, limit in (('orientation', 180), ('edge', 3)):
                    for first, second in zip(action[name], action[name][1:]):
                        duration = (second[0] - first[0]) * length / 12
                        if duration <= 0 or max(abs(right - left) for left, right in zip(first[1:], second[1:])) / duration > limit + 1e-9:
                            raise ValueError('Action rate envelope exceeded')
                for previous in range(group_index):
                    other = [row for row, owner in zip(expanded, bindings[identifier]) if owner['gesture_index'] == previous]
                    if (legacy._has_crossings(rows + other)
                            and previous not in model['recipes'][identifier]['gestures'][group_index]['overlap_with']):
                        raise ValueError('Undeclared crossing contributor')
        object_digest(model)
    except (KeyError, TypeError, AttributeError, IndexError) as error:
        raise ValueError('Malformed gesture model') from error


def migrate_v1(prior):
    legacy.validate_language(prior)
    if prior['letter_rules'] or prior['word_rules'] or any(recipe['allow_crossings'] for recipe in prior['recipes'].values()):
        raise ValueError('Explicit migration refuses unqualified context/crossings')
    model = copy.deepcopy(prior)
    model.update(schema_version=SCHEMA, sampling='legacy-v1', migration_source_sha256=object_digest(prior),
                 gestures={}, actions={'fixed': {'frame': 'physical-y-down',
                 'orientation': [[0, prior['nib_angle_deg']], [1, prior['nib_angle_deg']]],
                 'edge': [[0, 0, 1], [1, 0, 1]], 'pressure': .5, 'speed_mm_s': 12}}, recipes={})
    known = {}
    for identifier, recipe in prior['recipes'].items():
        instances, groups = [], []
        for stroke in recipe['strokes']:
            if stroke['transition'] in {'start', 'lift'}:
                groups.append([])
            groups[-1].append(copy.deepcopy(stroke))
        for group in groups:
            origin = group[0]['offset'][:]
            for stroke in group:
                stroke['offset'] = [value - start for value, start in zip(stroke['offset'], origin)]
            group[0]['transition'] = 'start'
            gesture = {'strokes': group, 'action': 'fixed'}
            checksum = object_digest(gesture)
            equivalent = next((key for key, value in model['gestures'].items() if value == gesture), None)
            if equivalent is not None:
                known[checksum] = equivalent
            if checksum not in known:
                known[checksum] = f'gesture-{len(model["gestures"])}'
                model['gestures'][known[checksum]] = gesture
            instances.append({'gesture': known[checksum], 'offset': origin, 'scale': 1.0, 'rotation_deg': 0.0,
                              'transition': 'start' if not instances else 'lift', 'overlap_with': []})
        model['recipes'][identifier] = {key: recipe[key] for key in ('logical', 'visible', 'advance')}
        model['recipes'][identifier]['gestures'] = instances
    validate_gestures(model)
    if _lower(model)[0] != prior:
        raise ValueError('Lossless legacy migration unavailable')
    return model


def compile_gestures(text, model):
    validate_gestures(model)
    lowered, bindings = _lower(model)
    plan = legacy.compile_text(text, lowered)
    for row in plan['strokes']:
        binding = bindings[row['recipe']][row['primitive_index']]
        row.update(binding)
        row['gesture_occurrence_id'] = f"{row['letter']}:{row['gesture_index']}"
        row['overlap_contributors'] = [f"{row['letter']}:{index}" for index in binding['overlap_with']]
        row['primitive_sha256'] = object_digest(model['primitives'][row['primitive']])
        row['gesture_sha256'] = object_digest(model['gestures'][row['gesture']])
        row['action_sha256'] = object_digest(model['actions'][row['action_profile']])
    plan.update(schema_version=SCHEMA, model_sha256=object_digest(model))
    return plan


def _arc_samples(rows, scale, step, *, preserve_boundaries=False, include_curve_positions=False):
    points, owners = [], []
    source_positions = []
    boundaries = []
    parameters = np.linspace(0, 1, 257)[:, None]
    for row in rows:
        for cubic_index, cubic in enumerate(row['cubics']):
            controls = np.asarray(cubic) * [scale, -scale] + [0, 10]
            curve = ((1 - parameters) ** 3 * controls[0] + 3 * (1 - parameters) ** 2 * parameters * controls[1]
                     + 3 * (1 - parameters) * parameters ** 2 * controls[2] + parameters ** 3 * controls[3])
            selected = curve[1:] if points else curve
            source_positions.extend((cubic_index, index) for index in range(257 - len(selected), 257))
            points.extend(selected.tolist())
            owners.extend([row] * len(selected))
            boundaries.append(len(points) - 1)
    points = np.asarray(points)
    distance = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    if distance[-1] < .001:
        raise ValueError('Stationary contact action unsupported')
    targets = np.linspace(0, distance[-1], math.ceil(distance[-1] / step) + 1)
    if preserve_boundaries:
        targets = np.unique(np.r_[targets, distance[boundaries]])
    for target in targets:
        index = min(len(points) - 1, max(1, int(np.searchsorted(distance, target, side='right'))))
        ratio = (target - distance[index - 1]) / max(1e-12, distance[index] - distance[index - 1])
        point = points[index - 1] + ratio * (points[index] - points[index - 1])
        tangent = points[index] - points[index - 1]
        tangent /= max(1e-12, np.linalg.norm(tangent))
        owner = owners[index]
        if include_curve_positions:
            cubic_index, vertex = source_positions[index]
            owner = {**owner, 'curve_position': {'cubic_index': cubic_index,
                     'parameter': min(1.0, max(0.0, float((vertex - 1 + ratio) / 256))), 'representation': 'chord-256'}}
        yield (*point, *tangent), owner, float(target / distance[-1])


def gesture_guide(text, model, *, step_mm=.05, include_curve_positions=False):
    if not legacy._number(step_mm, .005, .2):
        raise ValueError('Physical sampling bound')
    plan = compile_gestures(text, model)
    if any(action['orientation'] != [[0, model['nib_angle_deg']], [1, model['nib_angle_deg']]]
           or action['edge'] != [[0, 0, 1], [1, 0, 1]] for action in model['actions'].values()):
        raise ValueError('Dynamic/nonbaseline action execution unsupported until the realized action bridge')
    lowered, _ = _lower(model)
    if model['sampling'] == 'legacy-v1':
        bundle = legacy.language_guide(text, lowered, step_mm=step_mm, include_curve_positions=include_curve_positions)
        indexed = {row['occurrence_id']: row for row in plan['strokes']}
        for owner in bundle.metadata['owners']:
            if owner['kind'] == 'stroke':
                owner.update({key: value for key, value in indexed[owner['occurrence_id']].items()
                              if key not in {'cubics', 'offset', 'scale', 'rotation_deg', 'transition'}})
    else:
        groups = {}
        for row in plan['strokes']:
            groups.setdefault(row['gesture_occurrence_id'], []).append(row)
        samples, owners = [], []
        for rows in groups.values():
            contact = list(_arc_samples(rows, model['x_height_mm'], step_mm,
                                       preserve_boundaries=model['sampling'] == 'gesture-arc-v3',
                                       include_curve_positions=include_curve_positions))
            if samples:
                start, end = [samples[-1].x_mm, samples[-1].y_mm], list(contact[0][0][:2])
                for point in _sample_cubic([start, start, end, end], step_mm):
                    samples.append(GuideSample(*point, contact=False, pressure_nominal=0, nib_angle_deg=model['nib_angle_deg']))
                    owners.append({'kind': 'air', 'spans': [], 'from': owners[-1].get('gesture_occurrence_id'),
                                   'to': rows[0]['gesture_occurrence_id']})
            for point, row, progress in contact:
                samples.append(GuideSample(*point, pressure_nominal=.5, nib_angle_deg=model['nib_angle_deg']))
                owners.append({**{key: value for key, value in row.items() if key != 'cubics'},
                               'kind': 'stroke', 'spans': [row['span']], 'gesture_progress': progress})
        if len(samples) > 100000:
            raise ValueError('Guide sample budget')
        points = np.array([point for row in plan['strokes'] for cubic in row['cubics'] for point in cubic])
        physical = points * [model['x_height_mm'], -model['x_height_mm']] + [0, 10]
        margin = model['nib_width_mm'] + .5
        frame = [float(physical[:, 0].min() - margin), float(physical[:, 0].max() + margin),
                 float(physical[:, 1].min() - margin), float(physical[:, 1].max() + margin)]
        guide = DensePathGuide(text, tuple(samples), max(line['width'] for line in plan['lines']) * model['x_height_mm'],
                               model['x_height_mm'], kind='word', entry_tangent=(samples[0].tangent_dx, samples[0].tangent_dy),
                               exit_tangent=(samples[-1].tangent_dx, samples[-1].tangent_dy),
                               sources=(GuideSource(object_digest(model), confidence_tier='soft_accepted', split='synthetic-gesture'),))
        bundle = RepertoireGuide(guide, {'owners': owners, 'frame_mm': frame})
    bundle.metadata.update(schema_version=SCHEMA, model_sha256=object_digest(model), plan=plan,
                           step_mm=step_mm, sampling=model['sampling'], guide_sha256=object_digest(asdict(bundle.guide)),
                           acceptance='compiler mechanics only; no gesture/action or real hand acceptance')
    return bundle


def render_gestures(text, model, *, dpi=180, frame=None, step_mm=.05):
    bundle = gesture_guide(text, model, step_mm=step_mm)
    trajectory = [TrajectorySample(sample.x_mm, sample.y_mm, sample.contact, model['nib_width_mm'],
                                   sample.pressure_nominal, sample.nib_angle_deg) for sample in bundle.guide.samples]
    return paint_trajectory(trajectory, frame or bundle.metadata['frame_mm'], dpi=dpi)


def execute_gestures(text, model, *, dpi=180, frame=None, step_mm=.05, dt=.002):
    from scribesim.curriculum.stroke_learning import stroke_loss

    bundle = gesture_guide(text, model, step_mm=step_mm)
    result = GuidedHandFlowController(neutral_profile(model), repertoire_controls=RepertoireControls()).simulate_guide(
        bundle.guide, base_speed_mm_s=12, dt=dt)
    owners = [copy.deepcopy(bundle.metadata['owners'][index]) for index in result.trajectory_plan_indices]
    desired = render_gestures(text, model, dpi=dpi, frame=frame, step_mm=step_mm)
    actual = paint_trajectory(result.trajectory, frame or bundle.metadata['frame_mm'], dpi=dpi)
    contact_error = max((math.dist((sample.x_mm, sample.y_mm),
                                  (result.plan.samples[index].x_mm, result.plan.samples[index].y_mm))
                         for sample, index in zip(result.trajectory, result.trajectory_plan_indices) if sample.contact), default=0)
    return {'metrics': {'image_loss': stroke_loss(desired, actual), 'corridor_error_mm': contact_error,
                        'contact_schedule_preserved': all(sample.contact == result.plan.samples[index].contact
                            for sample, index in zip(result.trajectory, result.trajectory_plan_indices))},
            'owners': owners, 'trajectory': [asdict(sample) for sample in result.trajectory],
            'plan_indices': list(result.trajectory_plan_indices), 'images': {'desired': desired, 'actual': actual}}


def load_bundle(path, model):
    try:
        document = json.loads(Path(path).read_text())
        payload = document['payload']
        expected = gesture_guide(payload['guide']['symbol'], model, step_mm=payload['metadata']['step_mm'])
        if (set(document) != {'payload', 'sha256'} or object_digest(payload) != document['sha256']
                or object_digest(asdict(expected)) != document['sha256']):
            raise ValueError('Stale or altered gesture bundle')
        return expected
    except (KeyError, TypeError) as error:
        raise ValueError('Malformed gesture bundle') from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use a new empty directory')
    args.output.mkdir(parents=True, exist_ok=True)
    prior = legacy.seed_language()
    model = migrate_v1(prior)
    write_json(args.output / 'migration.json', model)
    Image.fromarray(render_gestures('i u ii ui', model)).save(args.output / 'legacy-equivalent.png')
    model['sampling'] = 'gesture-arc-v2'
    bundle = gesture_guide('i u ii ui', model)
    write_json(args.output / 'model.json', model)
    write_json(args.output / 'guide.json', {'payload': asdict(bundle), 'sha256': object_digest(asdict(bundle))})
    Image.fromarray(render_gestures('i u ii ui', model)).save(args.output / 'continuous-gestures.png')
    write_json(args.output / 'report.json', {'scope': 'synthetic compiler mechanics; not learned gestures',
                'legacy_pixel_equivalence': bool(np.array_equal(legacy.render_language('i u ii ui', prior),
                                                  render_gestures('i u ii ui', migrate_v1(prior)))),
                'new_model_sha256': object_digest(model), 'real_hand': 'blocked', 'promoted': False})


if __name__ == '__main__':
    main()
