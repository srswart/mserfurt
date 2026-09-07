"""Cap-preserving diagnostic source subdivision; the admitted model stays immutable."""

from bisect import bisect_left
import copy
from dataclasses import asdict, replace
import math

import numpy as np

from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide, _arc_samples
from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.controller import GuidedHandFlowController
from scribesim.handflow.curve_tangents import retime_curve_tangents, VERSION
from scribesim.handflow.planning import build_track_plan
from scribesim.handvalidate import foundation_motion as motion
from scribesim.handvalidate.bridge import neutral_profile, paint_trajectory
from scribesim.handvalidate.model import TrajectorySample
from scribesim.handvalidate.specimen import object_digest
from scribesim.pathguide.model import GuideSample
from scribesim.pathguide.repertoire import RepertoireGuide, _sample_cubic


def bundle(model, *, step, subdivision=True):
    original = gesture_guide('i', model, step_mm=step, include_curve_positions=True)
    compiled = compile_gestures('i', model)['strokes']
    if not subdivision:
        return original, compiled
    rows = copy.deepcopy(compiled)
    for row in rows:
        divided = []
        for cubic in row['cubics']:
            controls = np.asarray(cubic)
            edges = (controls[:-1] + controls[1:]) / 2
            inner = (edges[:-1] + edges[1:]) / 2
            midpoint = (inner[0] + inner[1]) / 2
            divided.extend(([controls[0].tolist(), edges[0].tolist(), inner[0].tolist(), midpoint.tolist()],
                            [midpoint.tolist(), inner[1].tolist(), edges[2].tolist(), controls[3].tolist()]))
        row['cubics'] = divided
    groups = {}
    for row in rows:
        groups.setdefault(row['gesture_occurrence_id'], []).append(row)
    samples, owners = [], []
    for group in groups.values():
        contact = list(_arc_samples(group, model['x_height_mm'], step, preserve_boundaries=True, include_curve_positions=True))
        if samples:
            start, end = [samples[-1].x_mm, samples[-1].y_mm], list(contact[0][0][:2])
            for point in _sample_cubic([start, start, end, end], step):
                samples.append(GuideSample(*point, contact=False, pressure_nominal=0, nib_angle_deg=model['nib_angle_deg']))
                owners.append({'kind': 'air', 'spans': [], 'from': owners[-1].get('gesture_occurrence_id'),
                               'to': group[0]['gesture_occurrence_id']})
        for point, row, progress in contact:
            samples.append(GuideSample(*point, pressure_nominal=.5, nib_angle_deg=model['nib_angle_deg']))
            owners.append({**{key: value for key, value in row.items() if key != 'cubics'}, 'kind': 'stroke',
                           'spans': [row['span']], 'gesture_progress': progress})
    if len(samples) > 100000:
        raise ValueError('Guide sample budget')
    guide = replace(original.guide, samples=tuple(samples), entry_tangent=(samples[0].tangent_dx, samples[0].tangent_dy),
                    exit_tangent=(samples[-1].tangent_dx, samples[-1].tangent_dy))
    return RepertoireGuide(guide, {**original.metadata, 'owners': owners, 'compiled_subdivision_sha256': object_digest(rows),
                                   'guide_sha256': object_digest(asdict(guide))}), rows


def execute(model, *, step, dt, budget, frame, subdivision=True):
    source_bundle, compiled = bundle(model, step=step, subdivision=subdivision)
    original_plan = build_track_plan(source_bundle.guide, base_speed_mm_s=12)
    owners = source_bundle.metadata['owners']
    engine = GuidedHandFlowController(neutral_profile(model), repertoire_controls=RepertoireControls(), execution_version='event-time-v2')
    timed = retime_curve_tangents(original_plan, owners, compiled)
    plan = timed.plan
    mapped = [owners[index] for index in timed.source_indices]
    observations = []
    original_step = engine.step

    def observe(state, desired, *, dt):
        velocity_before = [state.vel_x_mm_s, state.vel_y_mm_s]
        position_before = [state.pos_x_mm, state.pos_y_mm]
        error = original_step(state, desired, dt=dt)
        velocity = [velocity_before[0] + state.acc_x_mm_s2 * dt, velocity_before[1] + state.acc_y_mm_s2 * dt]
        speed = math.hypot(*velocity)
        if speed > engine.dyn.max_speed:
            velocity = [value * engine.dyn.max_speed / speed for value in velocity]
        unconstrained = [position + (before + after) * dt / 2 for position, before, after in zip(position_before, velocity_before, velocity)]
        observations.append({'velocity_before_mm_s': velocity_before, 'velocity_mm_s': [state.vel_x_mm_s, state.vel_y_mm_s],
                             'unconstrained_mm': unconstrained, 'projection_mm': math.dist(unconstrained, [state.pos_x_mm, state.pos_y_mm])})
        return error

    engine.step = observe
    executed = engine.follow_plan(plan, dt=dt, settle_time_s=0)
    trace, groups, errors = [], [], 0
    for point, index, execution, observation in zip(executed.trajectory, executed.trajectory_plan_indices,
                                                    executed.final_state.execution_trace, observations):
        owner = mapped[index]
        errors += int(point.contact != plan.samples[index].contact or (point.contact and owner['kind'] != 'stroke'))
        row = {**execution, **observation, 'owner': owner, 'plan_index': index}
        trace.append(row)
        if point.contact:
            key = owner['gesture_occurrence_id']
            if not groups or groups[-1]['owner'] != key:
                groups.append({'owner': key, 'first': row, 'last': row})
            groups[-1]['last'] = row
    errors += int([group['owner'] for group in groups] != list(dict.fromkeys(owner['gesture_occurrence_id'] for owner in mapped if owner['kind'] == 'stroke')))
    required = {owner['occurrence_id'] for owner in mapped if owner['kind'] == 'stroke'}
    seen = {row['owner']['occurrence_id'] for row in trace if row['contact']}
    errors += len(required.symmetric_difference(seen))
    entry_rows = [next(row for row in trace if row['plan_index'] == arrival['plan_index']) for arrival in timed.arrivals]
    corner_rows = [next((row for row in trace if row['time_s'] == corner['time_s'] and row['plan_index'] == corner['plan_index']), None) for corner in timed.corners]
    corner_errors = sum(row is None or not row['contact'] for row in corner_rows)
    corner_errors += int([row['occurrence_id'] for row in timed.corners] != [row['occurrence_id'] for row in compiled if row['transition'] == 'corner'])
    for corner in timed.corners:
        point = plan.samples[corner['plan_index']]
        corner_errors += int(not point.contact or point.speed_mm_s != 0 or point.vx_mm_s != 0 or point.vy_mm_s != 0
                             or math.dist((point.x_mm, point.y_mm), corner['position_mm']) > 1e-8)
    contact_indices = [index for point, index in zip(plan.samples, timed.source_indices) if point.contact]
    geometry_errors = int(contact_indices != [index for index, point in enumerate(original_plan.samples) if point.contact])
    geometry_errors += sum(any(getattr(point, key) != getattr(original_plan.samples[index], key) for key in
                              ('x_mm', 'y_mm', 'contact', 'pressure', 'nib_angle_deg')) for point, index in zip(plan.samples, timed.source_indices) if point.contact)
    desired = [TrajectorySample(point.x_mm, point.y_mm, point.contact, .45, point.pressure, point.nib_angle_deg) for point in plan.samples]
    images = {label: budget.render(paint_trajectory, path, frame or motion.SPEC['frame_mm'], dpi=180,
                                    contact_version=None)
              for label, path in (('desired', desired), ('actual', executed.trajectory))}
    metrics = {'planned_time_s': plan.total_time_s, 'executed_time_s': executed.final_state.time_s,
               'time_error_s': abs(executed.final_state.time_s - plan.total_time_s),
               'original_plan_time_s': original_plan.total_time_s, 'retiming_delta_s': plan.total_time_s - original_plan.total_time_s,
               'max_projection_mm': max(row['projection_mm'] for row in trace),
               'corridor_mm': max((math.dist(row['to_mm'], row['desired_mm']) for row in trace if row['contact']), default=0),
               'image_loss': motion.strokes.stroke_loss(images['desired'], images['actual']), 'owner_errors': errors,
               'entry_speed_mm_s': max((math.hypot(*row['velocity_mm_s']) for row in entry_rows), default=0),
               'entry_position_error_mm': max((math.dist(row['to_mm'], row['desired_mm']) for row in entry_rows), default=0),
               'actual_acceleration_mm_s2': max((math.dist(row['velocity_before_mm_s'], row['velocity_mm_s']) /
                                                (row['time_s'] - row['time_before']) for row in trace if row['time_s'] > row['time_before']), default=0),
               'zero_time_discontinuities': sum(row['to_mm'] != row['from_mm'] or row['velocity_mm_s'] != row['velocity_before_mm_s'] for row in trace if row['time_s'] == row['time_before']),
               'air_ink_errors': sum(row['pressure'] != 0 for row in trace if not row['contact']),
               **motion.desired_motion_metrics(plan), 'geometry_errors': geometry_errors, 'corner_errors': corner_errors,
               'corner_speed_mm_s': max((math.hypot(*row['velocity_mm_s']) for row in corner_rows if row), default=0),
               'corner_position_error_mm': max((math.dist(row['to_mm'], row['desired_mm']) for row in corner_rows if row), default=0)}
    return {'model_sha256': object_digest(model), 'text': 'i', 'version': VERSION, 'step_mm': step, 'dt_s': dt,
            'tool': 'legacy-full-edge', 'subdivision': subdivision, 'plan': asdict(plan), 'metrics': metrics,
            'groups': groups, 'trace': trace, 'arrivals': timed.arrivals, 'corners': timed.corners, 'images': images}


def audit_trace(model, result, *, subdivision=True):
    source_bundle, compiled = bundle(model, step=result['step_mm'], subdivision=subdivision)
    plan = build_track_plan(source_bundle.guide, base_speed_mm_s=12)
    retimed = retime_curve_tangents(plan, source_bundle.metadata['owners'], compiled)
    plan = retimed.plan
    owners = [source_bundle.metadata['owners'][index] for index in retimed.source_indices]
    errors = int(result.get('subdivision') is not subdivision) + int(result['version'] != VERSION) + int(asdict(plan) != result['plan']) + int(result['text'] != 'i')
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
            errors += int(row['owner']['kind'] != 'stroke' or math.dist(row['to_mm'], row['desired_mm']) > .25)
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
    errors += int(not result['trace'] or abs(result['trace'][-1]['time_s'] - plan.total_time_s) > 1e-10)
    return {'errors': errors, 'required_occurrences': sorted(required), 'seen_occurrences': sorted(seen)}
