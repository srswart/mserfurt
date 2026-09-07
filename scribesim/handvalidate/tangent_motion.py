"""Diagnostic execution adapter; existing compiler, controller and renderer unchanged."""

import copy
from dataclasses import asdict
import math

from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide
from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.controller import GuidedHandFlowController
from scribesim.handflow.curve_tangents import retime_curve_tangents, VERSION
from scribesim.handflow.planning import build_track_plan
from scribesim.handvalidate import foundation_motion as motion
from scribesim.handvalidate.bridge import neutral_profile, paint_trajectory
from scribesim.handvalidate.model import TrajectorySample
from scribesim.handvalidate.specimen import object_digest
from scribesim.pathguide.gesture_actions import ActionController, action_bundle
from scribesim.evo.nib_contact import ContactSample, VERSION as CONTACT_VERSION


def execute(model, text, *, step, dt, budget, physical=False, frame=None):
    model = copy.deepcopy(model)
    model['sampling'] = 'gesture-arc-v3'
    if physical:
        bundle = action_bundle(text, model, step_mm=step, include_curve_positions=True)
        original_plan, owners = bundle.plan, bundle.owners
        engine = ActionController(model, execution_version='event-time-v2')
    else:
        bundle = gesture_guide(text, model, step_mm=step, include_curve_positions=True)
        original_plan = build_track_plan(bundle.guide, base_speed_mm_s=12)
        owners = bundle.metadata['owners']
        engine = GuidedHandFlowController(neutral_profile(model), repertoire_controls=RepertoireControls(), execution_version='event-time-v2')
    compiled = compile_gestures(text, model)['strokes']
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
    if physical:
        desired = [ContactSample(point.x_mm, point.y_mm, point.contact, .45, point.pressure,
                                 point.nib_angle_deg, point.edge_start, point.edge_end) for point in plan.samples]
    else:
        desired = [TrajectorySample(point.x_mm, point.y_mm, point.contact, .45, point.pressure, point.nib_angle_deg) for point in plan.samples]
    images = {label: budget.render(paint_trajectory, path, frame or motion.SPEC['frame_mm'], dpi=180,
                                    contact_version=CONTACT_VERSION if physical else None)
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
    return {'model_sha256': object_digest(model), 'text': text, 'version': VERSION, 'step_mm': step, 'dt_s': dt,
            'tool': CONTACT_VERSION if physical else 'legacy-full-edge', 'plan': asdict(plan), 'metrics': metrics,
            'groups': groups, 'trace': trace, 'arrivals': timed.arrivals, 'corners': timed.corners, 'images': images}


def passes(result):
    metrics = result['metrics']
    return (all(type(value) in (int, float) and math.isfinite(value) for value in metrics.values())
            and metrics['owner_errors'] == 0 and metrics['time_error_s'] <= 1e-10 and metrics['max_projection_mm'] <= 1e-12
            and metrics['corridor_mm'] <= .25 and metrics['image_loss'] <= .35
            and all(check(metrics) for check in (motion.entry_pass, motion.mechanics_pass, motion.desired_pass, motion.corners_pass)))
