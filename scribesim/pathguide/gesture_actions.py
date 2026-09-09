"""Opt-in gesture actions through the existing handflow integrator."""

import copy
from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path

import numpy as np

from scribesim.evo.nib_contact import ContactSample, VERSION
from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide, validate_gestures
from scribesim.evofit import connected_contract
from scribesim.handflow.controller import GuidedHandFlowController
from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.model import HandStateV2, TrackPlan, TrackPlanSample
from scribesim.handflow.planning import build_track_plan
from scribesim.handvalidate.bridge import neutral_profile, paint_trajectory
from scribesim.handvalidate.specimen import ROOT, digest, object_digest
from scribesim.curriculum.stroke_learning import stroke_loss


SCHEMA = 'gesture-actions-v1'
CONTRACT_PATH = ROOT / 'shared/training/konrad_hand_recovery/stroke_gestures_v2/tool_contract/spec-v1.json'
CONTRACT = json.loads(CONTRACT_PATH.read_text())


@dataclass(frozen=True)
class ActionPlanSample(TrackPlanSample):
    edge_start: float = 0.0
    edge_end: float = 1.0
    gesture_progress: float = 0.0


@dataclass
class ActionState(HandStateV2):
    edge_start: float = 0.0
    edge_end: float = 1.0


@dataclass(frozen=True)
class ActionBundle:
    schema_version: str
    model_sha256: str
    tool_sha256: str
    code_sha256: dict
    text: str
    step_mm: float
    frame_mm: list
    plan: TrackPlan
    owners: list


def code_identities():
    names = ('scribesim/pathguide/gesture_actions.py', 'scribesim/evo/nib_contact.py', 'scribesim/evo/renderer.py',
             'scribesim/evofit/stroke_gestures.py', 'scribesim/evofit/stroke_language.py',
             'scribesim/handflow/controller.py', 'scribesim/handflow/planning.py', 'scribesim/handflow/model.py',
             'scribesim/handflow/controls.py', 'scribesim/handvalidate/model.py', 'scribesim/handvalidate/bridge.py')
    names += ('scribesim/evofit/foundation_contract.py',
              'shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/contract/spec-v1.json')
    return {name: digest(ROOT / name) for name in names}


def action_bundle(text, model, *, step_mm=.025, include_curve_positions=False):
    validate_gestures(model)
    if model['sampling'] not in {'gesture-arc-v2', 'gesture-arc-v3'} or model['nib_width_mm'] != .45:
        raise ValueError('Explicit gesture-arc-v2/v3 and frozen 0.45mm tool required')
    neutral = copy.deepcopy(model)
    for action in neutral['actions'].values():
        action['orientation'] = [[0, model['nib_angle_deg']], [1, model['nib_angle_deg']]]
        action['edge'] = [[0, 0, 1], [1, 0, 1]]
    geometry = gesture_guide(text, neutral, step_mm=step_mm, include_curve_positions=include_curve_positions)
    source_plan = compile_gestures(text, model)
    indexed = {row['occurrence_id']: row for row in source_plan['strokes']}
    occurrences = {row['gesture_occurrence_id']: row for row in source_plan['strokes']}
    plan = build_track_plan(geometry.guide, base_speed_mm_s=12)
    desired, owners = [], []
    angle, edge_start, edge_end = model['nib_angle_deg'], 0, 1
    for sample, source in zip(plan.samples, geometry.metadata['owners']):
        owner = copy.deepcopy(source)
        progress = owner.get('gesture_progress', 0)
        if owner['kind'] == 'stroke':
            original = indexed[owner['occurrence_id']]
            owner.update({key: value for key, value in original.items()
                          if key not in {'cubics', 'offset', 'scale', 'rotation_deg', 'transition'}})
        else:
            original = occurrences.get(owner.get('to'))
        if original is not None:
            profile = model['actions'][model['gestures'][original['gesture']]['action']]
            angle = float(np.interp(progress, [knot[0] for knot in profile['orientation']], [knot[1] for knot in profile['orientation']]))
            edge_start = float(np.interp(progress, [knot[0] for knot in profile['edge']], [knot[1] for knot in profile['edge']]))
            edge_end = float(np.interp(progress, [knot[0] for knot in profile['edge']], [knot[2] for knot in profile['edge']]))
        physical = {key: value if key == 'contact' else float(value) for key, value in asdict(sample).items()}
        desired.append(ActionPlanSample(**{**physical, 'nib_angle_deg': angle},
                                        edge_start=edge_start, edge_end=edge_end, gesture_progress=progress))
        owners.append(owner)
    identities = code_identities()
    if model['schema_version'] == connected_contract.SCHEMA:
        for name in ('scribesim/evofit/connected_contract.py', 'scribesim/handflow/curve_tangents.py'):
            identities[name] = digest(ROOT / name)
    return ActionBundle(SCHEMA, object_digest(model), digest(CONTRACT_PATH), identities, text,
                        step_mm, geometry.metadata['frame_mm'], replace(plan, samples=tuple(desired)), owners)


class ActionController(GuidedHandFlowController):
    def __init__(self, model, *, angular_rate=180, edge_rate=3, execution_version='legacy-v1'):
        if any(type(value) not in (float, int) or not math.isfinite(value) or not 0 < value <= bound
               for value, bound in ((angular_rate, 180), (edge_rate, 3))):
            raise ValueError('Invalid frozen actuator limits')
        super().__init__(neutral_profile(model), repertoire_controls=RepertoireControls(), execution_version=execution_version)
        self.angular_rate, self.edge_rate = angular_rate, edge_rate

    def initial_state(self, plan):
        state = super().initial_state(plan)
        first = plan.samples[0]
        return ActionState(**{**state.__dict__, 'nib_angle_deg': first.nib_angle_deg},
                           edge_start=first.edge_start, edge_end=first.edge_end)

    def step(self, state, desired, *, dt):
        def advance(current, target, rate):
            return current + max(-rate * dt, min(rate * dt, target - current))

        previous = state.nib_angle_deg, state.edge_start, state.edge_end
        angle = advance(state.nib_angle_deg, desired.nib_angle_deg, self.angular_rate)
        state.edge_start = advance(state.edge_start, desired.edge_start, self.edge_rate)
        state.edge_end = advance(state.edge_end, desired.edge_end, self.edge_rate)
        error = super().step(state, replace(desired, nib_angle_deg=angle), dt=dt)
        state.trace[-1] = ContactSample(**{**asdict(state.trace[-1]), 'width_mm': self.nib.width_mm},
                                       edge_start=state.edge_start, edge_end=state.edge_end)
        state.execution_trace[-1].update(desired_angle_deg=desired.nib_angle_deg,
            desired_edge=[desired.edge_start, desired.edge_end], realized_edge=[state.edge_start, state.edge_end],
            previous_action=list(previous), dt_s=dt)
        return error


def execute_actions(text, model, *, step_mm=.025, dt=.002, dpi=180, frame=None, angular_rate=180, edge_rate=3):
    if type(dt) not in (float, int) or not math.isfinite(dt) or not .001 <= dt <= .004:
        raise ValueError('Unsupported controller timestep')
    bundle = action_bundle(text, model, step_mm=step_mm)
    continuous = model['schema_version'] == connected_contract.SCHEMA
    timed = None
    if continuous:
        from scribesim.handflow.curve_tangents import retime_curve_tangents
        timed = retime_curve_tangents(bundle.plan, bundle.owners, compile_gestures(text, model)['strokes'])
        bundle = replace(bundle, plan=timed.plan, owners=[bundle.owners[index] for index in timed.source_indices])
    controller = ActionController(model, angular_rate=angular_rate, edge_rate=edge_rate,
                                  execution_version='event-time-v2' if continuous else 'legacy-v1')
    result = controller.follow_plan(bundle.plan, dt=dt, **({'settle_time_s': 0} if continuous else {}))
    playback = [ContactSample(sample.x_mm, sample.y_mm, sample.contact, .45, sample.pressure, sample.nib_angle_deg,
                              sample.edge_start, sample.edge_end) for sample in bundle.plan.samples]
    desired = paint_trajectory(playback, frame or bundle.frame_mm, dpi=dpi, contact_version=VERSION)
    actual = paint_trajectory(result.trajectory, frame or bundle.frame_mm, dpi=dpi, contact_version=VERSION)
    indices = result.trajectory_plan_indices
    angular, edge, corridor, contact_errors, angular_rates, edge_rates = [], [], [], 0, [], []
    for point, index, execution in zip(result.trajectory, indices, result.final_state.execution_trace):
        target = bundle.plan.samples[index]
        contact_errors += int(point.contact != target.contact)
        angular_delta = abs(point.nib_angle_deg - execution['previous_action'][0])
        edge_delta = max(abs(point.edge_start - execution['previous_action'][1]),
                         abs(point.edge_end - execution['previous_action'][2]))
        duration = execution['dt_s']
        if duration == 0 and (angular_delta != 0 or edge_delta != 0):
            raise ValueError('Zero-time actuator discontinuity')
        angular_rates.append(angular_delta / duration if duration else 0)
        edge_rates.append(edge_delta / duration if duration else 0)
        if point.contact:
            angular.append(abs(point.nib_angle_deg - target.nib_angle_deg))
            edge.append(max(abs(point.edge_start - target.edge_start), abs(point.edge_end - target.edge_end)))
            corridor.append(math.dist((point.x_mm, point.y_mm), (target.x_mm, target.y_mm)))
    metrics = {'orientation_error_deg': max(angular), 'edge_error_fraction': max(edge),
               'corridor_error_mm': max(corridor), 'contact_errors': contact_errors,
               'realized_angular_rate_deg_s': max(angular_rates), 'realized_edge_rate_s': max(edge_rates),
               'image_loss': stroke_loss(desired, actual)}
    if continuous:
        metrics['time_error_s'] = abs(result.final_state.time_s - bundle.plan.total_time_s)
        metrics.update(connected_contract.execution_metrics(compile_gestures(text, model)['strokes'],
            bundle.owners, indices, result.trajectory, result.final_state.execution_trace, timed))
    tracking_pass = (metrics['orientation_error_deg'] <= 2 and metrics['edge_error_fraction'] <= .02
                     and metrics['corridor_error_mm'] <= .25 and contact_errors == 0)
    if continuous:
        tracking_pass = (tracking_pass and metrics['time_error_s'] <= 1e-10 and metrics['owner_errors'] == 0
                         and metrics['corner_errors'] == 0 and metrics['corner_speed_mm_s'] <= .5
                         and metrics['corner_position_error_mm'] <= .05)
    return {'schema_version': SCHEMA, 'model_sha256': bundle.model_sha256, 'tool_sha256': bundle.tool_sha256,
            **({'execution_version': 'event-time-v2', 'clock_version': timed.version, 'corners': list(timed.corners)} if continuous else {}),
            'code_sha256': bundle.code_sha256, 'text': text, 'step_mm': step_mm, 'dt_s': dt,
            'actuator_limits': {'angular_rate': angular_rate, 'edge_rate': edge_rate},
            'metrics': metrics, 'tracking_pass': tracking_pass, 'S1_action_accepted': False,
            'trajectory': [asdict(point) for point in result.trajectory], 'execution': result.final_state.execution_trace,
            'owners': [copy.deepcopy(bundle.owners[index]) for index in indices], 'plan_indices': list(indices),
            'desired_plan': asdict(bundle.plan), 'images': {'desired': desired, 'actual': actual}}


def load_actions(path, model):
    try:
        document = json.loads(Path(path).read_text())
        payload = document['payload']
        expected = action_bundle(payload['text'], model, step_mm=payload['step_mm'])
        if (set(document) != {'payload', 'sha256'} or object_digest(payload) != document['sha256']
                or object_digest(asdict(expected)) != document['sha256']):
            raise ValueError('Stale, missing or unsupported action bundle fields')
        return expected
    except (KeyError, TypeError) as error:
        raise ValueError('Malformed action bundle') from error
