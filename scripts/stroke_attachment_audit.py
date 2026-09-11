"""Evaluate existing canonical attachment sites; never construct or execute a connector."""

import argparse
import json
import math
from pathlib import Path

from scripts import stroke_context_audit as source
from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


TEXTS = ('n', 'u', 'm', 'nm', 'nn', 'um', 'mm')
OUTPUT = source.BASE/'stroke_context_v1/attachment-investigation/snapshot-001'
DESIGN = ROOT/'docs/tech-direction/TD-018-addendum-e-boundary-construction.md'
DESIGN_SHA256 = '32df0e82832cf3f2defef651a51673af58785f0764fc1c9ab340b9df6cace0b3'


def point(cubic, parameter):
    weights = ((1-parameter)**3, 3*(1-parameter)**2*parameter,
               3*(1-parameter)*parameter**2, parameter**3)
    return [sum(weight*control[axis] for weight, control in zip(weights, cubic)) for axis in range(2)]


def tangent(cubic, parameter):
    weights = (3*(1-parameter)**2, 6*(1-parameter)*parameter, 3*parameter**2)
    vector = [sum(weight*(after[axis]-before[axis]) for weight, before, after in zip(weights, cubic, cubic[1:]))
              for axis in range(2)]
    return source.direction([0, 0], vector)


def height_parameter(cubic, height):
    if not math.isfinite(height) or any(not math.isfinite(value) for control in cubic for value in control):
        raise ValueError('Finite height and cubic required')
    increments = [after[1]-before[1] for before, after in zip(cubic, cubic[1:])]
    if not (all(value > 0 for value in increments) or all(value < 0 for value in increments)):
        raise ValueError('Strictly monotonic height control polygon required')
    if not min(cubic[0][1], cubic[3][1]) <= height <= max(cubic[0][1], cubic[3][1]):
        raise ValueError('Height outside canonical span')
    if height == cubic[0][1]:
        return 0.0
    if height == cubic[3][1]:
        return 1.0
    lower, upper = 0.0, 1.0
    increasing = increments[0] > 0
    for _ in range(60):
        middle = (lower+upper)/2
        if (point(cubic, middle)[1] < height) == increasing:
            lower = middle
        else:
            upper = middle
    return (lower+upper)/2


def baseline_obstruction(height, direction, role):
    if role not in ('departure', 'receiving'):
        raise ValueError('Unknown attachment role')
    return height == 0 and (direction[1] < 0 if role == 'departure' else direction[1] > 0)


def canonical(candidate, text):
    if text not in TEXTS:
        raise ValueError('Text outside seven-string investigation inventory')
    if object_digest(candidate) != source.context.CANDIDATE_SHA256:
        raise ValueError('Changed canonical candidate')
    return compile_gestures(text, candidate)


def site(row, height, role):
    cubic = row['cubics'][0]
    parameter = height_parameter(cubic, height)
    direction = tangent(cubic, parameter)
    return {'owner': {key: value for key, value in row.items() if key != 'cubics'},
        'canonical_geometry_sha256': object_digest(row['cubics']), 'cubic_index': 0,
        'canonical_parameter': parameter, 'height_local': height, 'height_mm': height*3.5,
        'position_local': point(cubic, parameter), 'directed_tangent_local_y_up': direction,
        'proposed_replacement_interval': [parameter, 1] if role == 'departure' else [0, parameter],
        'retained_interval': [0, parameter] if role == 'departure' else [parameter, 1],
        'intervals_are': 'Canonical domain descriptions only; no split/replacement geometry generated or admitted',
        'baseline_smooth_obstruction': baseline_obstruction(height, direction, role),
        'proposed_removed_baseline_anchor': cubic[3] if role == 'departure' else cubic[0],
        'body_exception_approved': False}


def investigate(candidate):
    compiled = {text: canonical(candidate, text) for text in TEXTS}
    reference = candidate['primitives']['lower-return']['cubics'][0]
    reference_height = reference[0][1]
    reference_width = abs(reference[3][0]-reference[0][0])*3.5
    heights = [0.0, reference_height/2, reference_height]
    site_pairs = []
    for text in ('nm', 'um', 'mm'):
        rows = compiled[text]['strokes']
        departure = [row for row in rows if row['letter'] == 0][-1]
        receiving = next(row for row in rows if row['letter'] == 1)
        if departure['primitive'] != 'stem' or receiving['primitive'] != 'rise':
            raise ValueError('Unexpected canonical attachment topology')
        for departure_height in heights:
            for receiving_height in heights:
                start = site(departure, departure_height, 'departure')
                end = site(receiving, receiving_height, 'receiving')
                horizontal = (end['position_local'][0]-start['position_local'][0])*3.5
                vertical_sum = (departure_height+receiving_height)*3.5
                fails = start['baseline_smooth_obstruction'] or end['baseline_smooth_obstruction']
                site_pairs.append({'text': text, 'departure': start, 'receiving': end,
                    'horizontal_gap_mm': horizontal, 'gap_in_reference_turn_widths': horizontal/reference_width,
                    'path_length_lower_bound_if_touching_baseline_mm': math.hypot(horizontal, vertical_sum),
                    'length_bound_basis': 'Reflection bound via any centerline baseline touch; no tangent/curvature/obstacle sufficiency',
                    'necessary_baseline_condition': 'fails' if fails else 'not_ruled_out',
                    'construction_feasible': None, 'site_admitted': False,
                    'unresolved': ['protected body and baseline-foot replacement approval',
                        'actual connector construction and smooth attach feasibility',
                        'finite-nib clearance and overlap ownership', 'length/curvature/excursion limits',
                        'letter identity and style usefulness', 'versioned topology and physical validation']})
    negative_rows = compiled['nn']['strokes']
    negative_entry = next(row for row in negative_rows if row['letter'] == 1)
    return {'coordinate_frame': 'canonical local-xheight-y-up; 3.5 mm per unit',
        'inventory': list(TEXTS), 'compiled_sha256': {text: object_digest(document) for text, document in compiled.items()},
        'existing_lower_return_reference_sha256': object_digest(candidate['primitives']['lower-return']),
        'reference_turn_width_mm': reference_width, 'reference_turn_entry_height_local': reference_height,
        'site_height_levels_local': heights,
        'site_level_reason': 'Baseline obstruction control, half and full existing lower-return entry height; finite inspection grid, not permitted bounds or optimization',
        'site_pairs': site_pairs, 'negative_control': {'text': 'nn', 'entry': source.port(negative_entry, True),
            'status': 'incompatible_receiving_site_for_family_P',
            'reason': 'First occurrence is a descending stem at x-height, not a baseline rising prefix; do not skip into a later internal rise'},
        'isolated_controls': {text: {'compiled_sha256': object_digest(compiled[text]),
            'occurrences': len(compiled[text]['strokes']), 'boundary_substitution': 'none'} for text in 'num'},
        'family_S': 'canonical separate letters retained exactly',
        'gap_ratio_interpretation': 'Scale comparison with an existing turn, not a maximum admissible gap or a failure threshold',
        'conclusion': 'Both baseline endpoints fail a smooth above-baseline construction; positive-height sites remain unproven, not admitted'}


def build_report():
    with source.evidence.read_only_guard():
        if digest(DESIGN) != DESIGN_SHA256:
            raise ValueError('Changed investigation design pin')
        sources = source.verify_sources()
        candidate = source.read_json(source.CANDIDATE)
        return {'version': 'stroke-attachment-investigation-v1', 'status': 'necessary_conditions_audited_no_geometry_admitted',
            'sources': sources, 'design_sha256': DESIGN_SHA256, 'investigation': investigate(candidate),
            'code_sha256': digest(Path(__file__)), 'tests_sha256': digest(ROOT/'tests/test_stroke_attachment_audit.py'),
            'read_only': True, 'new_connector_geometries': 0, 'raster_renders': 0,
            'controller_executions': 0, 'optimization_evaluations': 0, 'physical_execution_authorized': False,
            'site_or_body_exception_approved': False, 'S2_accepted': False, 'real_accepted': False}


def snapshot(destination=OUTPUT):
    if destination.exists():
        raise FileExistsError('Immutable attachment audit already exists')
    report = build_report()
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/'report.json', report)
    return {'report_sha256': digest(destination/'report.json'), 'status': report['status']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot', 'inspect'])
    parser.add_argument('--report-sha256')
    args = parser.parse_args()
    if args.command == 'snapshot':
        result = snapshot()
    else:
        if not args.report_sha256 or digest(OUTPUT/'report.json') != args.report_sha256:
            raise ValueError('External audit report pin required')
        if source.read_json(OUTPUT/'report.json') != build_report():
            raise ValueError('Changed attachment audit derivation')
        result = {'status': 'exact_read_only_reinspection_pass', 'report_sha256': args.report_sha256}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
