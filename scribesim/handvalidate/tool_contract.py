"""Independent investigation oracle and bounded probes, not a production nib renderer."""

import argparse
import copy
from dataclasses import fields
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.controller import GuidedHandFlowController
from scribesim.handflow.model import HandStateV2, TrackPlanSample
from scribesim.handvalidate.bridge import neutral_profile, paint_trajectory
from scribesim.handvalidate.model import TrajectorySample
from scribesim.handvalidate.specimen import ROOT, digest, write_json
from scribesim.pathguide.model import GuideSample


SPEC = ROOT / 'shared/training/konrad_hand_recovery/stroke_gestures_v2/tool_contract/spec-v1.json'
CONTRACT = json.loads(SPEC.read_text())
PPMM = 96


class ProbeBudget:
    def __init__(self, limit=100, seconds=900, clock=time.monotonic):
        if (not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100
                or not math.isfinite(seconds) or not 0 < seconds <= 900):
            raise ValueError('Invalid investigation budget')
        self.limit, self.seconds, self.clock = limit, seconds, clock
        self.started = clock()
        self.renders = 0

    def check_time(self):
        if self.clock() - self.started >= self.seconds:
            raise ValueError('Investigation time budget exhausted')

    def consume(self):
        self.check_time()
        if self.renders >= self.limit:
            raise ValueError('Investigation render budget exhausted')
        self.renders += 1


def edge_endpoints(center, angle, interval):
    if (len(center) != 2 or len(interval) != 2
            or not all(math.isfinite(value) for value in (*center, angle, *interval))
            or not -180 <= angle <= 540 or not 0 <= interval[0] < interval[1] <= 1
            or interval[1] - interval[0] < CONTRACT['tracks']['minimum_contact_fraction']):
        raise ValueError('Invalid declared contact geometry')
    radians = math.radians(angle)
    direction = math.cos(radians), math.sin(radians)
    return tuple(tuple(center[axis] + (fraction - .5) * CONTRACT['tool']['width_mm'] * direction[axis]
                       for axis in (0, 1)) for fraction in interval)


def _corners(pose):
    endpoints = edge_endpoints(pose['center'], pose['angle'], pose['edge'])
    angle = math.radians(pose['angle'])
    normal = -math.sin(angle), math.cos(angle)
    half = CONTRACT['tool']['thickness_mm'] / 2
    return [tuple(endpoint[axis] + side * half * normal[axis] for axis in (0, 1))
            for endpoint in endpoints for side in (-1, 1)]


def _hull(points):
    def cross(origin, first, second):
        return ((first[0] - origin[0]) * (second[1] - origin[1])
                - (first[1] - origin[1]) * (second[0] - origin[0]))

    ordered = sorted(set(points))
    lower, upper = [], []
    for chain, sequence in ((lower, ordered), (upper, reversed(ordered))):
        for point in sequence:
            while len(chain) >= 2 and cross(chain[-2], chain[-1], point) <= 0:
                chain.pop()
            chain.append(point)
    return lower[:-1] + upper[:-1]


def tool_fixtures():
    def line(start=(1.5, .4), end=(1.5, 2.6), angle=(40, 40), edge='full'):
        return [{'center': [start[axis] + (end[axis] - start[axis]) * step / 128 for axis in (0, 1)],
                 'angle': angle[0] + (angle[1] - angle[0]) * step / 128,
                 'edge': [0, 1 - .5 * step / 128] if edge == 'negative' else
                         [.5 * step / 128, 1] if edge == 'positive' else [0, 1]}
                for step in range(129)]

    circle = [{'center': [1.5 + .8 * math.cos(step * 2 * math.pi / 256),
                          1.5 + .8 * math.sin(step * 2 * math.pi / 256)],
               'angle': 40, 'edge': [0, 1]} for step in range(257)]
    cases = [('fixed_vertical', 'orientation', [line()]),
             ('fixed_diagonal', 'orientation', [line((.8, .4), (2.2, 2.6))]),
             ('arc_counter', 'orientation', [circle]),
             ('rotation', 'orientation', [line(angle=(40, 60))]),
             ('wrap', 'orientation', [line(angle=(179, 181))]),
             ('negative_edge_release', 'edge', [line(edge='negative')]),
             ('positive_edge_release', 'edge', [line(edge='positive')]),
             ('terminal', 'finishing', [line(end=(1.5, 2.2)), line((1.2, 1.9), (1.9, 2.35))])]
    return [{'id': identifier, 'family': family, 'runs': runs,
             'provenance': 'project-authored analytic tool exercise; no source image',
             'contact': 'one continuous run each; explicit lift between runs'}
            for identifier, family, runs in cases]


def _oracle(fixture, budget, *, refine=False):
    budget.consume()
    mask = Image.new('1', (3 * PPMM, 3 * PPMM))
    draw = ImageDraw.Draw(mask)
    for run in fixture['runs']:
        poses = []
        for first, second in zip(run, run[1:]):
            poses.append(first)
            if refine:
                poses.append({'center': [(left + right) / 2 for left, right in zip(first['center'], second['center'])],
                              'angle': (first['angle'] + second['angle']) / 2,
                              'edge': [(left + right) / 2 for left, right in zip(first['edge'], second['edge'])]})
        poses.append(run[-1])
        for first, second in zip(poses, poses[1:]):
            hull = _hull(_corners(first) + _corners(second))
            draw.polygon([(point[0] * PPMM, point[1] * PPMM) for point in hull], fill=1)
    return np.asarray(mask).copy()


def _legacy_approximation(fixture, budget):
    budget.consume()
    trajectory = []
    for run in fixture['runs']:
        trajectory.extend(TrajectorySample(*pose['center'], True,
                                           CONTRACT['tool']['width_mm'] * (pose['edge'][1] - pose['edge'][0]),
                                           .5, pose['angle']) for pose in run)
        trajectory.append(TrajectorySample(0, 0, False))
    image = paint_trajectory(trajectory, (0, 3, 0, 3), dpi=PPMM * 25.4)
    return np.asarray(Image.fromarray(image).convert('L')) < 180


def _disagreement(first, second):
    return float(np.count_nonzero(first != second) / max(1, np.count_nonzero(first | second)))


def _controller_probe():
    hand = {'nib_width_mm': .45, 'nib_angle_deg': 40, 'x_height_mm': 3.5}
    controller = GuidedHandFlowController(neutral_profile(hand), repertoire_controls=RepertoireControls())
    observed = []
    for pressure in (.25, .5, .75):
        state = HandStateV2(1.5, 1.5, nib_angle_deg=40, nib_contact=True)
        desired = TrackPlanSample(.01, 0, 1.5, 1.5, 0, 0, 12, pressure, 60, True, .2)
        controller.step(state, desired, dt=.01)
        observed.append({'pressure': state.nib_pressure, 'width_mm': state.trace[-1].width_mm,
                         'angle_deg': state.nib_angle_deg, 'ink_consumed': state.consumed_ink})
    rate = abs(observed[1]['angle_deg'] - 40) / .01
    return {'desired_step_deg': 20, 'dt_s': .01, 'observed_rate_deg_s': rate,
            'meets_frozen_rate_bound': rate <= CONTRACT['tracks']['angular_rate_deg_s'],
            'interpretation': 'instantaneous desired-angle assignment is not bounded realized actuation',
            'pressure_controls': observed,
            'pressure_scope': 'diagnostic coupling controls only; nonconstant pressure excluded from action fitting'}


def _panel(fixtures, expected, legacy, output, budget):
    budget.consume()
    image = Image.new('RGB', (1000, 1090), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=16)
    draw.text((14, 12), 'Synthetic tool contract: independent expected footprint vs legacy approximation', fill='black', font=font)
    draw.text((14, 36), 'Not a new renderer, learned action, historical pen or accepted actual trajectory.', fill='black', font=font)
    for index, fixture in enumerate(fixtures):
        left, top = 12 + index % 2 * 500, 70 + index // 2 * 250
        draw.text((left, top), fixture['id'], fill='black', font=font)
        for offset, label, mask in [(0, 'Expected geometry', expected[fixture['id']]),
                                    (240, 'Legacy / centered shrink', legacy[fixture['id']])]:
            draw.text((left + offset, top + 25), label, fill='black', font=font)
            tile = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8)).convert('RGB')
            image.paste(tile.resize((192, 192), Image.Resampling.NEAREST), (left + offset, top + 46))
    image.save(output)


def probe(output, *, max_renders=100, seconds=900):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty output directory')
    budget = ProbeBudget(max_renders, seconds)
    fixtures = tool_fixtures()
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / 'contract.json', CONTRACT)
    write_json(output / 'fixtures.json', fixtures)
    expected, legacy, metrics = {}, {}, []
    for fixture in fixtures:
        identifier = fixture['id']
        expected[identifier] = _oracle(fixture, budget)
        legacy[identifier] = _legacy_approximation(fixture, budget)
        refined = _oracle(fixture, budget, refine=True)
        metrics.append({'fixture': identifier,
                        'legacy_disagreement': _disagreement(expected[identifier], legacy[identifier]),
                        'oracle_midpoint_refinement_disagreement': _disagreement(expected[identifier], refined),
                        'endpoints_mm': [edge_endpoints(run[-1]['center'], run[-1]['angle'], run[-1]['edge'])
                                         for run in fixture['runs']]})
    wrong = copy.deepcopy(fixtures[0])
    for pose in wrong['runs'][0]:
        pose['angle'] = 80
    hidden = copy.deepcopy(fixtures[-1])
    hidden['runs'] = [sum(hidden['runs'], [])]
    overbuilt = copy.deepcopy(fixtures[-1])
    extra = copy.deepcopy(overbuilt['runs'][-1])
    for pose in extra:
        pose['center'][0] += .5
    overbuilt['runs'].append(extra)
    controls = {
        'wrong_orientation': _disagreement(expected['fixed_vertical'], _oracle(wrong, budget)),
        'swapped_edge': _disagreement(expected['negative_edge_release'], expected['positive_edge_release']),
        'centered_shrink': _disagreement(expected['negative_edge_release'], legacy['negative_edge_release']),
        'hidden_connector': _disagreement(expected['terminal'], _oracle(hidden, budget)),
        'overbuilt_terminal': _disagreement(expected['terminal'], _oracle(overbuilt, budget)),
    }
    budget.consume()
    filled = expected['arc_counter'].copy()
    vertical, horizontal = np.indices(filled.shape)
    filled[(horizontal / PPMM - 1.5) ** 2 + (vertical / PPMM - 1.5) ** 2 < .45 ** 2] = True
    controls['filled_counter'] = _disagreement(expected['arc_counter'], filled)
    _panel(fixtures, expected, legacy, output / 'footprints.png', budget)
    report = {
        'schema_version': 'pen-contact-investigation-report-v1', 'contract_sha256': digest(SPEC),
        'decision': 'proceed-synthetic-contract-implementation-only', 'historical_calibration': 'unavailable',
        'S1_action': 'not_evaluated', 'promoted': False,
        'code_sha256': {name: digest(ROOT / name) for name in
                       ('scribesim/handvalidate/tool_contract.py', 'scribesim/evo/renderer.py',
                        'scribesim/handvalidate/bridge.py', 'scribesim/handvalidate/model.py',
                        'scribesim/handflow/model.py', 'scribesim/handflow/planning.py',
                        'scribesim/handflow/controller.py', 'scribesim/handflow/controls.py',
                        'scribesim/pathguide/model.py')},
        'active_edge_fields': {record.__name__: {'edge_start', 'edge_end'} <= {field.name for field in fields(record)}
                               for record in (GuideSample, TrackPlanSample, HandStateV2, TrajectorySample)},
        'controller_angle_probe': _controller_probe(), 'fixtures': metrics,
        'negative_controls': {name: {'disagreement': value,
                                     'meets_frozen_minimum': value >= CONTRACT['criteria']['negative_control_disagreement_min']}
                              for name, value in controls.items()},
        'criterion_scope': 'geometry/control diagnostics only; failed controls require local ownership/contact criteria, not lowered thresholds',
        'gaps': [
            'No active-edge interval in desired guide, plan, controller state or actual samples.',
            'Controller step copies desired contact/angle without bounded actuator state.',
            'Canonical sweep accepts symmetric half-vectors; partial contact cannot shift from pen center.',
            'Legacy caps have pixel-derived thickness; new physical thickness needs explicit new-mode semantics.',
            'Neutral repertoire pressure still scales width; bridge pressure also changes darkness.',
            'Planner progress spans an entire guide, including air; gesture-local arc progress is absent.',
            'Unwrapped orientation, endpoint-side reflection, tracking and convergence need versioned tests.'],
        'deferred_validation': ['new actuator dt refinement', 'new renderer/controller acceptance',
                                'physical tool calibration', 'source/letter appearance and real G0-G2'],
        'budget': {'fixture_families': 3, 'renders': budget.renders, 'render_limit': max_renders,
                   'seconds_limit': seconds, 'optimization_evaluations': 0, 'revision': 0},
    }
    budget.check_time()
    write_json(output / 'report.json', report)
    (output / 'README.md').write_text(
        '# Intentional pen-contact investigation\n\n'
        '**Decision: proceed with declared synthetic contract implementation only. S1-action is not evaluated.**\n\n'
        '[Frozen contract](contract.json) was committed before probes. Width 0.45 mm, edge thickness 0.02 mm, '
        'pressure 0.5, speed 12 mm/s, adequate constant ink; these are synthetic assumptions, not quill calibration.\n\n'
        '[Footprint comparison](footprints.png) shows independent rectangular-footprint expectations against the '
        'unchanged legacy sweep. Partial contact in the legacy column is an explicitly wrong centered-shrink '
        'approximation, not claimed actual execution. All panels use the same physical scale.\n\n'
        '[Report](report.json) freezes code/tool identities, numeric results, three fixture families, six negative '
        'controls and the implementation gap table. The instantaneous 20-degree controller step at 0.01s gives '
        '2000 degrees/s, exceeding the frozen 180 degrees/s actuator bound. Active-edge state is absent at every layer.\n\n'
        'Pressure probes diagnose existing mechanical-width and optical-darkness coupling; they do not enable '
        'pressure learning or ink repair. Physical calibration, dabs, deformation, fatigue and depletion remain deferred.\n\n'
        'The global image metric may miss a small hidden connector: inspect the negative-control result, retain '
        'the failed bound and add local contact/ownership checks in the later evaluator. No threshold was relaxed. '
        'Midpoint oracle refinement is not controller timestep acceptance.\n\n'
        'Implement NIBCONTACT-002 geometry and PATHGUIDE-006 realized state before any action training. '
        'Do not use this investigation oracle as production code or as both implementation and test oracle.\n\n'
        '```sh\n.venv/bin/python -m scribesim.handvalidate.tool_contract --output /tmp/td018-tool-replay\n```\n\n'
        'Fresh runs reproduce semantic artifacts; execution.json contains measured wall time and is not byte-stable.\n')
    write_json(output / 'freeze.json', {'contract_sha256': digest(SPEC),
                                       'artifacts': {file.name: digest(file) for file in sorted(output.iterdir())}})
    write_json(output / 'execution.json', {'elapsed_seconds': budget.clock() - budget.started,
                                          'renders': budget.renders, 'optimization_evaluations': 0})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = probe(args.output)
    print(json.dumps({'decision': report['decision'], 'budget': report['budget'],
                      'negative_controls': report['negative_controls']}))


if __name__ == '__main__':
    main()
