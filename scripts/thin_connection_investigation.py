"""Read-only canonical attachment and finite-nib width feasibility; no connectors."""

import argparse
import json
import math
from pathlib import Path
import signal
import time

from scripts import stroke_clearance_audit as clearance
from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


source = clearance.attachment.source
OUTPUT = source.BASE/'thin-connection-investigation/snapshot-001'
FEEDBACK = source.BASE/'nm-construction-v1/owner-feedback-002.json'
FEEDBACK_PIN = '554de4265a00988469a8a029252a2802d1fe6487f17bd0684c21bde9990bdd77'
CLEARANCE_PIN = 'd7dd39b61b91572d1ee3e241e0583266be9dcd9e4f0f577f74e9964820033943'
INVENTORY = ('nu', 'mu', 'um')
WIDTH = .45
THICKNESS = .02
EDGE_ANGLE_Y_UP = -40
PROPOSED_RATIO = .25


def projected_width(direction, active_fraction=1, thickness=THICKNESS):
    if not .1 <= active_fraction <= 1 or not 0 <= thickness <= THICKNESS:
        raise ValueError('Unsupported analytical contact dimensions')
    length = math.hypot(*direction)
    if not length or any(not math.isfinite(value) for value in direction):
        raise ValueError('Nonzero finite direction required')
    unit = [value/length for value in direction]
    angle = math.radians(EDGE_ANGLE_Y_UP)
    edge = [math.cos(angle), math.sin(angle)]
    cross = abs(edge[0]*unit[1]-edge[1]*unit[0])
    dot = abs(sum(before*after for before, after in zip(edge, unit)))
    return WIDTH*active_fraction*cross+thickness*dot


def canonical(candidate, text):
    if text not in INVENTORY:
        raise ValueError('Only exposed pair investigation; no sealed-word probe')
    if object_digest(candidate) != source.context.CANDIDATE_SHA256:
        raise ValueError('Frozen canonical identity changed')
    return compile_gestures(text, candidate)


def directional_case(start, end):
    displacement = [after-before for before, after in zip(start, end)]
    distance = math.hypot(*displacement)
    body_reference = projected_width([0, -1])
    threshold = PROPOSED_RATIO*body_reference
    angle = math.radians(EDGE_ANGLE_Y_UP)
    transverse_displacement = abs(math.cos(angle)*displacement[1]-math.sin(angle)*displacement[0])
    return {'displacement_mm': displacement, 'chord_length_mm': distance,
            'chord_direction_deg_y_up': math.degrees(math.atan2(displacement[1], displacement[0])),
            'straight_direction_full_contact_width_mm': projected_width(displacement),
            'straight_direction_tenth_edge_width_mm': projected_width(displacement, .1),
            'proposed_thin_limit_mm': threshold,
            'whole_path_thin_necessary_length_mm': WIDTH*transverse_displacement/threshold,
            'necessary_detour_ratio': WIDTH*transverse_displacement/(threshold*distance),
            'bound_scope': 'Integral projection necessary bound if ENTIRE connecting path is below proposed width; ignores tip thickness, so optimistic. Not a connector or bound on thin core with broad splices.'}


def investigate(candidate):
    cases = []
    compilations = {}
    height = candidate['primitives']['lower-return']['cubics'][0][0][1]
    for text in INVENTORY:
        compiled = canonical(candidate, text)
        compilations[text] = object_digest(compiled)
        rows = compiled['strokes']
        departure = [row for row in rows if row['letter'] == 0][-1]
        receiving = next(row for row in rows if row['letter'] == 1)
        receiver_heights = ([clearance.attachment.point(receiving['cubics'][0], parameter)[1]
                             for parameter in (0, .25, .5)] if receiving['primitive'] == 'stem'
                            else [0, height/2, height])
        for departure_height in (0, height/2, height):
            for receiving_height in receiver_heights:
                start = clearance.attachment.site(departure, departure_height, 'departure')
                end = clearance.attachment.site(receiving, receiving_height, 'receiving')
                case = {'text': text, 'departure': start, 'receiving': end}
                parts = clearance.swept_parts(rows, case)
                start_mm = [value*3.5 for value in start['position_local']]
                end_mm = [value*3.5 for value in end['position_local']]
                footprints = {role: clearance.site_clearance(case[role], parts) for role in ('departure', 'receiving')}
                for footprint in footprints.values():
                    footprint['nonowner_possible_contacts'] = [record for record in footprint['distances_to_canonical_regions']
                        if record['occurrence_id'] != footprint['site_owner'] and record['status'] != 'certified_clear'
                        and not record['region'].endswith('proposed_replacement')]
                cases.append({**case, 'directional_feasibility': directional_case(start_mm, end_mm),
                              'site_footprints': footprints, 'central_strip': clearance.central_strip(parts),
                              'receiver_kind': receiving['primitive'], 'site_admitted': False,
                              'full_rectangle_clearance_certified': False,
                              'clearance_scope': 'Existing fixed full-edge segment footprint only, not .02mm rectangle, active-corner sweep, or connector clearance'})
    angles = (-90, -40, 0, 40, 45, 90)
    return {'compiled_sha256': compilations, 'cases': cases,
            'reference_vertical_stem_rectangle_width_mm': projected_width([0, -1]),
            'proposed_thin_ratio': PROPOSED_RATIO,
            'proposed_thin_limit_mm': PROPOSED_RATIO*projected_width([0, -1]),
            'direction_table': [{'travel_angle_deg_y_up': angle,
                'ideal_full_edge_width_mm': projected_width([math.cos(math.radians(angle)), math.sin(math.radians(angle))], thickness=0),
                'rectangle_widths_mm': {str(fraction): projected_width([math.cos(math.radians(angle)), math.sin(math.radians(angle))], fraction)
                                        for fraction in (1, .2, .1)}} for angle in angles],
            'thin_limit_status': 'Prospective discussion guardrail, not owner-approved historical style metric or acceptance threshold',
            'num': {'status': 'dependency_analysis_only', 'boundaries': ['nu', 'um'],
                    'prior_protocol_status': 'num was sealed; no fresh holdout claim after owner named it and canonical topology was inspected',
                    'new_geometry_or_target_evaluation': False}}


def build_report():
    if digest(FEEDBACK) != FEEDBACK_PIN or digest(clearance.OUTPUT/'report.json') != CLEARANCE_PIN:
        raise ValueError('Changed owner feedback or frozen clearance evidence')
    with source.evidence.read_only_guard():
        if source.read_json(clearance.OUTPUT/'report.json') != clearance.build_report():
            raise ValueError('Frozen clearance reinspection mismatch')
        candidate = source.read_json(source.CANDIDATE)
        evidence_files = ('scribesim/evo/nib_contact.py', 'scribesim/evofit/stroke_gestures.py',
                          'scribesim/pathguide/gesture_actions.py', 'scripts/stroke_context_nominal.py')
        return {'version': 'thin-connection-feasibility-v1', 'status': 'investigation_only_no_construction_admission',
                'candidate_sha256': object_digest(candidate), 'feedback_sha256': FEEDBACK_PIN,
                'clearance_report_sha256': CLEARANCE_PIN, 'investigation': investigate(candidate),
                'source_files': {name: digest(ROOT/name) for name in evidence_files},
                'code_sha256': digest(Path(__file__)), 'tests_sha256': digest(ROOT/'tests/test_thin_connection_investigation.py'),
                'connector_geometries': 0, 'raster_renders': 0, 'controller_executions': 0,
                'fitting_evaluations': 0, 'accepted': False}


def snapshot():
    OUTPUT.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    def timeout_handler(signum, frame):
        raise TimeoutError('300-second local investigation ceiling')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    try:
        report = build_report()
    except Exception as error:
        report = {'status': 'stopped', 'error': f'{type(error).__name__}: {error}', 'accepted': False}
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    report['elapsed_seconds'] = time.monotonic()-started
    write_json(OUTPUT/'report.json', report)
    return {'status': report['status'], 'elapsed_seconds': report['elapsed_seconds'],
            'report_sha256': digest(OUTPUT/'report.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot'])
    parser.parse_args()
    print(json.dumps(snapshot(), indent=2))
