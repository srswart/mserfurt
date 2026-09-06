"""Bounded, untrained return vocabulary and explicit composition-cap audit."""

import argparse
import copy
import json
import math
from pathlib import Path
import time

import numpy as np

from scribesim.evofit import stroke_language as legacy
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


SCHEMA = 'shared-stroke-gestures-foundation-v1'
LANGUAGE_SCHEMA = 'shared-stroke-language-foundation-v1'
BASE = ROOT / 'shared/training/konrad_hand_recovery/stroke_gestures_v2'
SPEC_PATH = BASE / 'foundation_repair/contract/spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
EXPANDED_CAP = 6


def validate_extensions(model):
    if set(model['primitives']) != set(SPEC['baseline']['primitives']) | set(SPEC['new_families']):
        raise ValueError('Foundation family budget and inventory are fixed')
    for name, primitive in SPEC['baseline']['primitives'].items():
        if model['primitives'][name] != primitive:
            raise ValueError('Frozen old primitive changed')
    for name, contract in SPEC['new_families'].items():
        primitive = model['primitives'][name]
        if (set(primitive) != legacy.PRIMITIVE_FIELDS or len(primitive['cubics']) != 1
                or primitive['closed'] is not False or primitive['entry'] != contract['entry']
                or primitive['exit'] != contract['exit'] or primitive['provenance'] != contract['provenance']):
            raise ValueError('New return topology and ports are fixed')
        cubic = primitive['cubics'][0]
        if len(cubic) != 4 or cubic[0] != contract['start'] or cubic[3] != contract['end']:
            raise ValueError('Return endpoints are fixed')
        for displacement, direction in ((np.subtract(cubic[1], cubic[0]), contract['entry']),
                                        (np.subtract(cubic[3], cubic[2]), contract['exit'])):
            length = float(np.dot(displacement, direction))
            if (not legacy._number(length, *contract['handle_bounds'])
                    or not np.allclose(displacement, np.asarray(direction) * length, rtol=0, atol=1e-10)):
                raise ValueError('Return interior freedom must preserve port rays and bounds')
    supported = {row['character'] for row in SPEC['characters'] if row['status'] == 'construction'}
    if any(recipe['logical'] not in supported for recipe in model['recipes'].values()):
        raise ValueError('Unsupported foundation construction; retain inventory debt')
    for key in ('x_height_mm', 'nib_width_mm', 'nib_angle_deg'):
        if model[key] != SPEC['baseline'][key]:
            raise ValueError('Foundation audit uses the fixed source tool and scale')
    if model['letter_rules'] or model['word_rules']:
        raise ValueError('Foundation context overlays are not admitted')
    if 'actions' in model and model['actions'] != {'fixed': {'frame': 'physical-y-down',
            'orientation': [[0, 40.0], [1, 40.0]], 'edge': [[0, 0, 1], [1, 0, 1]], 'pressure': .5, 'speed_mm_s': 12}}:
        raise ValueError('Foundation requires the fixed baseline action profile')


def _chain(names, primitives):
    result, endpoint = [], None
    for name in names:
        start = primitives[name]['cubics'][0][0]
        offset = [0.0, 0.0] if endpoint is None else [left - right for left, right in zip(endpoint, start)]
        result.append({'primitive': name, 'offset': offset, 'scale': 1.0, 'rotation_deg': 0.0,
                       'transition': 'start' if endpoint is None else 'smooth'})
        endpoint = [left + right for left, right in zip(primitives[name]['cubics'][-1][-1], offset)]
    return {'strokes': result, 'action': 'fixed'}


def _instance(name, offset, first=False, scale=1.0):
    return {'gesture': name, 'offset': offset, 'scale': scale, 'rotation_deg': 0.0,
            'transition': 'start' if first else 'lift', 'overlap_with': []}


def initial_model():
    from scribesim.evofit.stroke_gestures import migrate_v1

    model = migrate_v1(copy.deepcopy(SPEC['baseline']))
    model.update(schema_version=SCHEMA, sampling='gesture-arc-v3', scope='untrained-foundation-contract')
    for name, contract in SPEC['new_families'].items():
        start, end = contract['start'], contract['end']
        handles = contract['initial_handles']
        cubic = [start[:], [value + handles[0] * rate for value, rate in zip(start, contract['entry'])],
                 [value - handles[1] * rate for value, rate in zip(end, contract['exit'])], end[:]]
        model['primitives'][name] = {'cubics': [cubic], 'entry': contract['entry'][:], 'exit': contract['exit'][:],
                                     'closed': False, 'provenance': contract['provenance']}
    templates = {'stem': ['stem'], 'rise': ['rise'], 'underturn': ['stem', 'lower-return', 'rise'],
                 'overturn': ['rise', 'upper-return', 'stem'],
                 'compound_curve': ['upper-return', 'stem', 'lower-return', 'rise'],
                 'upper_loop': ['loop'], 'terminal': ['exit'], 'shoulder': ['upper-return']}
    model['gestures'] = {name: _chain(names, model['primitives']) for name, names in templates.items()}
    configurations = {'i': [('stem', [0, 0], 1), ('terminal', [0, 0], 1)],
                      'n': [('stem', [0, 0], 1), ('overturn', [0, 0], 1)],
                      'u': [('underturn', [0, 0], 1), ('stem', [1, 0], 1)],
                      'm': [('overturn', [0, 0], 1), ('overturn', [1, 0], 1)],
                      'h': [('stem', [0, 0], 1.5), ('overturn', [0, 0], 1)]}
    model['recipes'] = {name: {'logical': name, 'visible': name, 'advance': .65 if name == 'i' else 2.3 if name == 'm' else 1.3,
                              'gestures': [_instance(gesture, offset, index == 0, scale)
                                           for index, (gesture, offset, scale) in enumerate(rows)]}
                       for name, rows in configurations.items()}
    return model


def target_points(family, count=257):
    if family not in SPEC['new_families'] or type(count) is not int or not 2 <= count <= 4097:
        raise ValueError('Bounded independent target request required')
    contract, target = SPEC['new_families'][family], SPEC['targets']
    parameter = np.linspace(0, 1, count)[:, None]
    start, end = np.asarray(contract['start']), np.asarray(contract['end'])
    incoming = np.asarray(contract['entry']) * target['endpoint_derivative_magnitudes'][0]
    outgoing = np.asarray(contract['exit']) * target['endpoint_derivative_magnitudes'][1]
    points = ((2 * parameter ** 3 - 3 * parameter ** 2 + 1) * start
              + (parameter ** 3 - 2 * parameter ** 2 + parameter) * incoming
              + (-2 * parameter ** 3 + 3 * parameter ** 2) * end
              + (parameter ** 3 - parameter ** 2) * outgoing)
    points[:, 1] += contract['signed_side'] * target['signed_bulge_magnitude'] * np.sin(np.pi * parameter[:, 0]) ** 2
    return points


def verify_prerequisites(spec=SPEC):
    try:
        prerequisite = spec['prerequisites']
        root = BASE / 'foundation_repair' / prerequisite['motion_run']
        if not root.resolve().is_relative_to((BASE / 'foundation_repair/motion').resolve()):
            raise ValueError('Outside-root motion evidence')
        if digest(root / 'report.json') != prerequisite['motion_report_sha256']:
            raise ValueError('Motion report identity mismatch')
        report = json.loads((root / 'report.json').read_text())
        for name, checksum in report['artifacts'].items():
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()) or digest(path) != checksum:
                raise ValueError('Motion artifact identity mismatch')
        if (report['decision']['status'] != 'pass' or len(report['checks']) != 239
                or not all(value is True for value in report['checks'].values())
                or report['code_sha256'] != prerequisite['motion_code_sha256']):
            raise ValueError('Accepted pre-audit motion proof required')
        if digest(BASE / prerequisite['coverage_fixtures']) != prerequisite['coverage_sha256']:
            raise ValueError('Synthetic coverage identity mismatch')
        from scribesim.handvalidate.foundation_motion import load_historical_baseline
        if load_historical_baseline()['candidate'] != spec['baseline']:
            raise ValueError('Frozen primitive lineage mismatch')
    except (KeyError, TypeError, OSError) as error:
        raise ValueError('Incomplete prerequisite evidence') from error
    return {'status': 'pass', 'scope': 'accepted pre-audit motion and original primitive lineage',
            'fresh_post_compiler_baseline_required': True}


def _ports(expanded):
    errors, rows = 0, []
    for before, after in zip(expanded, expanded[1:]):
        incoming = legacy._direction(before['cubics'][-1][-2], before['cubics'][-1][-1])
        outgoing = legacy._direction(after['cubics'][0][0], after['cubics'][0][1])
        gap = math.dist(before['cubics'][-1][-1], after['cubics'][0][0])
        alignment = sum(left * right for left, right in zip(incoming, outgoing))
        required = after['transition'] in ('smooth', 'corner')
        error = required and (gap > 1e-8 or after['transition'] == 'smooth' and alignment < 1 - 1e-6)
        errors += int(error)
        rows.append({'from': before['primitive'], 'to': after['primitive'], 'transition': after['transition'],
                     'gap_xheight': gap, 'tangent_dot': alignment, 'contact_port_required': required, 'pass': not error})
    return errors, rows


def audit(model):
    from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures

    validate_gestures(model)
    references = {row['id']: row for row in json.loads((BASE / SPEC['prerequisites']['coverage_fixtures']).read_text())}
    hypotheses = []
    for specification in SPEC['hypotheses']:
        row = copy.deepcopy(specification)
        reference = references[row['id']]
        row.update(reference_entry_direction=legacy._direction(reference['segments'][0][0], reference['segments'][0][1]),
                   reference_exit_direction=legacy._direction(reference['segments'][-1][-2], reference['segments'][-1][-1]),
                   reference_closed=reference['closed'], reference_match_claimed=False)
        if row['gesture'] is not None:
            recipe = {'strokes': model['gestures'][row['gesture']]['strokes']}
            expanded = legacy._recipe_strokes(recipe, model)
            errors, joins = _ports(expanded)
            row.update(expanded_count=len(expanded), expansion=[item['primitive'] for item in expanded],
                       entry=expanded[0]['cubics'][0][0], exit=expanded[-1]['cubics'][-1][-1],
                       entry_direction=legacy._direction(expanded[0]['cubics'][0][0], expanded[0]['cubics'][0][1]),
                       exit_direction=legacy._direction(expanded[-1]['cubics'][-1][-2], expanded[-1]['cubics'][-1][-1]),
                       contact_topology='one continuous gesture', port_errors=errors, joins=joins)
        else:
            row.update(expanded_count=None, expansion=[], port_errors=None, contact_topology='unsupported')
        hypotheses.append(row)
    characters = []
    for specification in SPEC['characters']:
        row = copy.deepcopy(specification)
        if row['status'] == 'construction':
            expanded = compile_gestures(row['character'], model)['strokes']
            errors, joins = _ports(expanded)
            if len(expanded) != row['expanded']:
                raise ValueError('Frozen construction count changed')
            row.update(port_errors=errors, joins=joins, expansion=[item['primitive'] for item in expanded],
                       occurrences=[item['occurrence_id'] for item in expanded])
        else:
            row.update(port_errors=None, joins=[], expansion=[])
        characters.append(row)
    port_table = {name: {'declared_entry': primitive['entry'], 'declared_exit': primitive['exit'],
                        'actual_entry': legacy._direction(primitive['cubics'][0][0], primitive['cubics'][0][1]),
                        'actual_exit': legacy._direction(primitive['cubics'][-1][-2], primitive['cubics'][-1][-1]),
                        'start': primitive['cubics'][0][0], 'end': primitive['cubics'][-1][-1], 'closed': primitive['closed']}
                  for name, primitive in model['primitives'].items()}
    largest = max(row['expanded'] for row in characters if row['status'] == 'construction')
    return {'hypotheses': hypotheses, 'characters': characters, 'primitive_ports': port_table,
            'selected_cap': largest, 'cap_checks': {str(cap): largest <= cap for cap in range(4, 7)},
            'cap_basis': SPEC['cap_basis'], 'training_permitted': False, 'learned_primitives_accepted': False,
            'S1_action_accepted': False, 'real_hand_accepted': False,
            'next_required': 'CURRICULUM-010 must first rerun matching current-code motion/baseline validation within its new budget'}


def identities():
    from scribesim.handvalidate.foundation_motion import identities as motion_identities
    return {**motion_identities(), 'scribesim/evofit/foundation_contract.py': digest(Path(__file__))}


def _markdown(report):
    lines = ['# Return vocabulary and port audit', '',
             '**Nominal synthetic feasibility only. No new training or actual-motion acceptance.**', '',
             '## Primitive direction and port table', '',
             'Angles are degrees in local x-height coordinates, y up. Actual endpoint tangents govern attachment;',
             'the old stored declarations are retained, not silently rewritten. New return handles may move only on frozen rays.', '',
             '| Primitive | Start → end | Actual entry / exit | Stored entry / exit | Closed |',
             '|---|---|---|---|---|']

    def angle(vector):
        return f'{math.degrees(math.atan2(vector[1], vector[0])):.3f}'

    for name, row in report['primitive_ports'].items():
        lines.append(f"| {name} | {row['start']} → {row['end']} | {angle(row['actual_entry'])} / {angle(row['actual_exit'])} | "
                     f"{angle(row['declared_entry'])} / {angle(row['declared_exit'])} | {row['closed']} |")
    lines += ['', '[Eight primitive shapes, including two untrained returns](primitive-ports.png)', '',
              '## Eight gesture hypotheses', '',
              'These are role/topology hypotheses, not exact reproductions of the older analytic centerlines.',
              'In particular, the frozen rise exit cannot reach vertical with only ±20° rotation. Return ports',
              'therefore match actual stem/rise tangents; no reflection, larger rotation or old-geometry fit is introduced.', '',
              '| Hypothesis | Expansion / count | Contact and counter | Status / debt |', '|---|---|---|---|']
    for row in report['hypotheses']:
        lines.append(f"| {row['id']} | {' + '.join(row['expansion']) or 'missing'} / {row['expanded_count']} | "
                     f"{row['contact_topology']}; {row['counter']} | {row['status']}: {row['debt']} |")
    lines += ['', '[Six representable gesture hypotheses](gesture-expansions.png)', '',
              '## Twelve-character feasibility checklist', '',
              '| Character | Expansion / count | Topology | Status / debt |', '|---|---|---|---|']
    for row in report['characters']:
        lines.append(f"| {row['character']} | {' + '.join(row['expansion']) or 'not admitted'} / {row['expanded']} | "
                     f"{row['topology']} | {row['status']}: {row['debt']} |")
    lines += ['', '[Five supplied construction scaffolds, not learned letters](construction-checklist.png)', '',
              '## Composition decision', '', report['cap_basis'], '',
              'Four references per gesture, eight primitive families, eight named gestures and two alternatives',
              'per character remain bounded. The new reader accepts six actual primitive occurrences per recipe;',
              'the old reader still rejects more than four. Unsupported forms fail rather than aliasing a loop or bowl.', '',
              '## Attachments', '', '| Construction | From → to | Transition | Gap (x-height) | Tangent dot |',
              '|---|---|---|---|---|']
    for row in report['characters']:
        for join in row['joins']:
            lines.append(f"| {row['character']} | {join['from']} → {join['to']} | {join['transition']} | "
                         f"{join['gap_xheight']:.8f} | {join['tangent_dot']:.8f} |")
    lines += ['', 'A lift does not require tangent continuity; every lift remains explicit. Continuous smooth joins',
              'require coincident ports and matching tangents. Ink counters and actual dynamics are not evaluated here.', '',
              '## Independent targets and next step', '',
              '[Frozen target specifications](target-specs.json) define analytic endpoint/tangent targets with an',
              'additional sinusoidal bulge. The generator consumes no candidate handles, recipes or search grid.',
              'Targets are not rendered or scored in this audit. Initialization is a generic 0.28-handle return,',
              'not deliberately degraded from a previously accepted return (none exists).', '',
              'Single returns form train/development fixtures; underturn, overturn and mixed-return attachments',
              'are topology-held-out specifications. Before fitting, CURRICULUM-010 must freeze its full learning',
              'protocol and rerun current-code motion/baseline checks within its own budget. The pre-audit motion',
              'proof is historical provenance after this compiler change, not fresh admission.', '',
              '[Initial untrained model](initial-model.json) · [Machine-readable audit](report.json) · [Freeze](freeze.json)', '']
    return '\n'.join(lines)


def build(output):
    from scribesim.handvalidate.foundation_motion import Budget, panel
    from scribesim.evofit.stroke_gestures import gesture_guide
    from scribesim.handvalidate.bridge import paint_trajectory
    from scribesim.handvalidate.model import TrajectorySample

    output = Path(output)
    if output.exists():
        raise ValueError('Use a new immutable contract output directory')
    budget = Budget(maximum=100, seconds=900)
    prerequisites = verify_prerequisites()
    model = initial_model()
    write_json(output / 'freeze.json', {'spec': SPEC, 'spec_sha256': digest(SPEC_PATH),
                                       'code_sha256': identities(), 'initial_model': model, 'prerequisites': prerequisites})
    report = audit(model)
    tiles = []
    for name in model['primitives']:
        cubics = model['primitives'][name]['cubics']
        points = [point for cubic in cubics for point in legacy._sample_cubic(cubic, .01)]
        trajectory = [TrajectorySample(point[0] * 3.5, 10 - point[1] * 3.5, True, .45, .5, 40) for point in points]
        image = budget.render(paint_trajectory, trajectory, [-1, 5, 4, 12], dpi=900)
        tiles.append((name + (' | UNTRAINED' if name in SPEC['new_families'] else ' | frozen'), image))
    budget.render(panel, output / 'primitive-ports.png', tiles)
    tiles = []
    for row in report['hypotheses']:
        if row['gesture'] is None:
            continue
        probe = copy.deepcopy(model)
        probe['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 2,
                                  'gestures': [_instance(row['gesture'], [0, 0], True)]}}
        bundle = gesture_guide('i', probe)
        trajectory = [TrajectorySample(point.x_mm, point.y_mm, point.contact, .45, .5, 40) for point in bundle.guide.samples]
        tiles.append((row['id'] + ' | supplied', budget.render(paint_trajectory, trajectory, [-1, 6, 4, 15], dpi=900)))
    budget.render(panel, output / 'gesture-expansions.png', tiles)
    tiles = []
    for letter in model['recipes']:
        bundle = gesture_guide(letter, model)
        trajectory = [TrajectorySample(point.x_mm, point.y_mm, point.contact, .45, point.pressure_nominal, 40)
                      for point in bundle.guide.samples]
        tiles.append((letter + ' | feasibility, not learned', budget.render(paint_trajectory, trajectory, [-1, 9, 4, 12], dpi=900)))
    budget.render(panel, output / 'construction-checklist.png', tiles)
    write_json(output / 'initial-model.json', model)
    write_json(output / 'target-specs.json', SPEC['targets'])
    (output / 'audit.md').write_text(_markdown(report))
    budget.check()
    passed = (report['selected_cap'] == EXPANDED_CAP and len(report['hypotheses']) == 8 and len(report['characters']) == 12
              and all(row['port_errors'] == 0 for row in report['hypotheses'] if row['gesture'] is not None)
              and all(row['port_errors'] == 0 for row in report['characters'] if row['status'] == 'construction'))
    report.update(status='pass' if passed else 'fail', code_sha256=identities(), spec_sha256=digest(SPEC_PATH),
                  prerequisites=prerequisites, renders=budget.used, max_renders=100, max_seconds=900,
                  optimization_evaluations=0, training_renders=0, target_renders=0,
                  scope='nominal synthetic construction audit, not actual motion or learned acceptance',
                  artifacts={path.name: digest(path) for path in sorted(output.iterdir()) if path.is_file()})
    write_json(output / 'report.json', report)
    write_json(output / 'execution.json', {'renders': budget.used, 'elapsed_seconds': time.monotonic() - budget.started})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({key: result[key] for key in ('status', 'selected_cap', 'renders', 'training_permitted')}, indent=2))


if __name__ == '__main__':
    main()
