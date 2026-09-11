"""Finite fixed-edge site clearance against canonical swept geometry, without rendering."""

import argparse
import json
import math
from pathlib import Path

from scripts import stroke_attachment_audit as attachment
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


PIN = 'b555be20ccfc179be57b7ac701ded640741a4a9947a124ccbddef91550fe5a1e'
OUTPUT = attachment.source.BASE/'stroke_context_v1/clearance-investigation/snapshot-001'
ERROR = .00001
ROUNDING = 1e-9
EDGE = [.225*math.cos(math.radians(40)), -.225*math.sin(math.radians(40))]


def split(cubic, parameter):
    levels = [cubic]
    while len(levels[-1]) > 1:
        levels.append([[(1-parameter)*before[axis]+parameter*after[axis] for axis in range(2)]
                       for before, after in zip(levels[-1], levels[-1][1:])])
    return [level[0] for level in levels], [level[-1] for level in reversed(levels)]


def restrict(cubic, lower, upper):
    if not 0 <= lower < upper <= 1:
        raise ValueError('Nonempty canonical interval required')
    prefix = cubic if upper == 1 else split(cubic, upper)[0]
    return prefix if lower == 0 else split(prefix, lower/upper)[1]


def flatten(cubic, depth=0):
    error = max(math.dist(cubic[index], [(1-index/3)*cubic[0][axis]+index/3*cubic[3][axis]
                                         for axis in range(2)]) for index in (1, 2))
    if error <= ERROR:
        return [(cubic[0], cubic[3])]
    if depth >= 24:
        raise ValueError('Clearance flattening bound not achieved')
    before, after = split(cubic, .5)
    return flatten(before, depth+1)+flatten(after, depth+1)


def footprint(center):
    return [[center[axis]+sign*EDGE[axis] for axis in range(2)] for sign in (-1, 1)]


def cross(origin, first, second):
    return (first[0]-origin[0])*(second[1]-origin[1])-(first[1]-origin[1])*(second[0]-origin[0])


def point_segment_distance(point, start, end):
    vector = [end[axis]-start[axis] for axis in range(2)]
    length_squared = sum(value*value for value in vector)
    parameter = 0 if length_squared == 0 else max(0, min(1,
        sum((point[axis]-start[axis])*vector[axis] for axis in range(2))/length_squared))
    return math.dist(point, [start[axis]+parameter*vector[axis] for axis in range(2)])


def segment_distance(first, second):
    sides = [cross(*first, point) for point in second]
    other_sides = [cross(*second, point) for point in first]
    if sides[0]*sides[1] < 0 and other_sides[0]*other_sides[1] < 0:
        return 0.0
    return min(*(point_segment_distance(point, *second) for point in first),
               *(point_segment_distance(point, *first) for point in second))


def segment_polygon_distance(segment, polygon):
    edges = list(zip(polygon, polygon[1:]+polygon[:1]))
    area = sum(before[0]*after[1]-after[0]*before[1] for before, after in edges)
    if abs(area) > 1e-15:
        for point in segment:
            sides = [cross(before, after, point) for before, after in edges]
            if all(value >= 0 for value in sides) or all(value <= 0 for value in sides):
                return 0.0
    return min(segment_distance(segment, edge) for edge in edges)


def classify(distance):
    return {'approximate_distance_mm': distance,
            'lower_bound_mm': max(0, distance-ERROR-ROUNDING),
            'upper_bound_mm': distance+ERROR+ROUNDING,
            'status': 'certified_clear' if distance > ERROR+ROUNDING else 'possible_contact_or_overlap'}


def swept_parts(rows, case):
    parts = []
    for row in rows:
        intervals = [(0, 1, 'protected_other_occurrence')]
        for role in ('departure', 'receiving'):
            site = case[role]
            if row['occurrence_id'] == site['owner']['occurrence_id']:
                intervals = [(*site['retained_interval'], role+'_retained'),
                             (*site['proposed_replacement_interval'], role+'_proposed_replacement')]
        for lower, upper, kind in intervals:
            if lower == upper:
                continue
            cubic = restrict([[value*3.5 for value in point] for point in row['cubics'][0]], lower, upper)
            polygons = []
            for start, end in flatten(cubic):
                start_edge, end_edge = footprint(start), footprint(end)
                polygons.append([start_edge[0], start_edge[1], end_edge[1], end_edge[0]])
            parts.append({'owner': row, 'kind': kind, 'interval': [lower, upper],
                          'control_hull_mm': cubic, 'polygons': polygons})
    return parts


def overlap_relation(site_owner, other):
    if site_owner['occurrence_id'] == other['occurrence_id']:
        return 'expected_same_occurrence_attachment'
    if site_owner['gesture_occurrence_id'] == other['gesture_occurrence_id']:
        return 'same_canonical_gesture'
    if (other['gesture_occurrence_id'] in site_owner['overlap_contributors']
            or site_owner['gesture_occurrence_id'] in other['overlap_contributors']):
        return 'existing_declared_gesture_contributor'
    return 'no_declared_gesture_overlap_relation'


def site_clearance(site, parts):
    edge = footprint([value*3.5 for value in site['position_local']])
    records = []
    for part in parts:
        distance = min(segment_polygon_distance(edge, polygon) for polygon in part['polygons'])
        owner = part['owner']
        records.append({'occurrence_id': owner['occurrence_id'], 'primitive': owner['primitive'],
            'gesture_occurrence_id': owner['gesture_occurrence_id'], 'contact_run_id': owner['contact_run_id'],
            'canonical_interval': part['interval'], 'region': part['kind'],
            'ownership_relation': overlap_relation(site['owner'], owner), **classify(distance)})
    return {'site_owner': site['owner']['occurrence_id'], 'height_mm': site['height_mm'],
            'canonical_parameter': site['canonical_parameter'], 'nib_segment_mm_y_up': edge,
            'distances_to_canonical_regions': records}


def central_strip(parts):
    retained = [part for part in parts if not part['kind'].endswith('proposed_replacement')]
    left = max(point[0] for part in retained if part['owner']['letter'] == 0 for point in part['control_hull_mm'])
    right = min(point[0] for part in retained if part['owner']['letter'] == 1 for point in part['control_hull_mm'])
    lower, upper = left+2*abs(EDGE[0])+ROUNDING, right-2*abs(EDGE[0])-ROUNDING
    return {'center_x_interval_mm': [lower, upper], 'width_mm': max(0, upper-lower),
            'status': 'certified_open_central_strip' if upper > lower else 'no_strip_proved_by_hull_bound',
            'basis': 'Retained canonical control hulls expanded by both obstacle and moving fixed-nib half-widths',
            'scope': 'Strict interior of vertical strip only; excludes proposed replacement ink and proves neither access from sites nor a connecting path'}


def load_attachment(checksum):
    if checksum != PIN or digest(attachment.OUTPUT/'report.json') != checksum:
        raise ValueError('Exact external attachment audit pin required')
    report = attachment.source.read_json(attachment.OUTPUT/'report.json')
    if (report['code_sha256'] != digest(Path(attachment.__file__))
            or report['tests_sha256'] != digest(ROOT/'tests/test_stroke_attachment_audit.py')):
        raise ValueError('Changed frozen attachment source')
    return report


def analyze(report):
    candidate = attachment.source.read_json(attachment.source.CANDIDATE)
    cases = []
    for case in report['investigation']['site_pairs']:
        if case['necessary_baseline_condition'] != 'not_ruled_out':
            continue
        rows = attachment.canonical(candidate, case['text'])['strokes']
        parts = swept_parts(rows, case)
        cases.append({'text': case['text'], 'departure': site_clearance(case['departure'], parts),
            'receiving': site_clearance(case['receiving'], parts), 'central_strip': central_strip(parts),
            'construction_feasible': None, 'new_overlap_permission': False})
    return {'cases': cases, 'excluded_baseline_obstructed_pairs': 15,
            'nib_full_edge_mm': .45, 'physical_y_down_angle_deg': 40, 'analysis_coordinates': 'physical-mm-y-up',
            'curve_to_chord_error_mm': ERROR, 'numeric_distance_allowance_mm': ROUNDING,
            'method': 'Exact canonical subinterval partition; bounded polyline swept by fixed edge; analytic segment-to-convex-polygon distance',
            'overlap_semantics': 'Zero/near-zero approximate distance is possible contact/overlap, not a certified positive overlap area',
            'own_attachment_semantics': 'Expected same-occurrence contact remains reported, never removed by ignoring the entire parent stroke',
            'limitations': ['no connector geometry exists', 'no path access or curvature feasibility proof',
                'no approved overlap area or contributor exemption for new ink', 'no actual ink, pressure or motion envelope',
                'no physical clearance/admission threshold changed']}


def build_report():
    with attachment.source.evidence.read_only_guard():
        prior = load_attachment(PIN)
        if prior != attachment.build_report():
            raise ValueError('Changed attachment derivation')
        return {'version': 'stroke-site-finite-nib-clearance-v1', 'status': 'read_only_clearance_audit_no_construction_admission',
            'attachment_report_sha256': PIN, 'sources': prior['sources'], 'analysis': analyze(prior),
            'code_sha256': digest(Path(__file__)), 'tests_sha256': digest(ROOT/'tests/test_stroke_clearance_audit.py'),
            'raster_renders': 0, 'controller_executions': 0, 'new_connector_geometries': 0,
            'optimization_evaluations': 0, 'physical_execution_authorized': False, 'S2_accepted': False, 'real_accepted': False}


def snapshot(destination=OUTPUT):
    if destination.exists():
        raise FileExistsError('Immutable clearance audit already exists')
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
            raise ValueError('External clearance report pin required')
        if attachment.source.read_json(OUTPUT/'report.json') != build_report():
            raise ValueError('Changed clearance derivation')
        result = {'status': 'exact_read_only_reinspection_pass', 'report_sha256': args.report_sha256}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
