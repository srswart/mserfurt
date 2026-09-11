"""Read-only corner representation, fixed-site ramp clearance and ownership audit."""

import argparse
import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import signal
import time

import numpy as np

from scripts import thin_connection_investigation as investigation
from scribesim.evo.nib_contact import ContactSample, contact_corners, reflect_sample
from scribesim.evofit.stroke_gestures import validate_gestures
from scribesim.handvalidate.specimen import ROOT, digest, object_digest


source = investigation.source
clearance = investigation.clearance
BASE = source.BASE/'nu-corner-contact-v1'
OUTPUT = BASE/'capability-001'
PROPOSAL = ROOT/'docs/tech-direction/TD-018-nu-corner-contact-proposal.md'
PROPOSAL_PIN = '7f8aff72c7769e5c28eb8eaec4ec3d41251d97320a6ac997c5fdaf6c7a74821c'
INVESTIGATION_PIN = '0b8b2f84474ef80cd37e94085483e5e312f52d348f46a32a07d972e83bd28aa3'
TOOL = source.BASE/'tool_contract/spec-v1.json'
TOOL_PIN = 'f267680ed6313862ab4bd8771fb52c4937a7f20c3b711988b5d746cc6ca924b7'
INTERVALS = {'full': [0, 1], 'negative': [0, .1], 'positive': [.9, 1]}
MAX_BYTES = 10*1024**2


def approval_record():
    return {'version': 'nu-corner-capability-v1', 'owner_quote': "Let's do the next",
            'scope': 'Read-only capability package, section 6.1 only',
            'proposal_sha256': PROPOSAL_PIN, 'investigation_sha256': INVESTIGATION_PIN,
            'tool_contract_sha256': TOOL_PIN, 'seconds': 300, 'max_output_bytes': MAX_BYTES,
            'minimum_free_bytes': 5*1024**3, 'retries': 0, 'geometry_generation': False,
            'raster_renders': 0, 'controller_executions': 0, 'fitting': False}


def verify(approval):
    if approval != approval_record():
        raise ValueError('Capability-only approval required')
    for filename, expected in ((PROPOSAL, PROPOSAL_PIN), (TOOL, TOOL_PIN),
                               (investigation.OUTPUT/'report.json', INVESTIGATION_PIN)):
        if digest(filename) != expected:
            raise ValueError(f'Frozen input changed: {filename}')
    prior = source.read_json(investigation.OUTPUT/'report.json')
    identities = {**prior['source_files'], 'scripts/thin_connection_investigation.py': prior['code_sha256'],
                  'tests/test_thin_connection_investigation.py': prior['tests_sha256']}
    for filename, expected in identities.items():
        if digest(ROOT/filename) != expected:
            raise ValueError(f'Frozen source changed: {filename}')
    source.verify_sources()
    return prior


def sample(center, interval):
    return ContactSample(center[0], center[1], True, .45, .5, -40,
                         edge_start=interval[0], edge_end=interval[1])


def hull(points):
    points = sorted(set(tuple(point) for point in points))
    lower, upper = [], []
    for chain, ordered in ((lower, points), (upper, reversed(points))):
        for point in ordered:
            while len(chain) > 1 and clearance.cross(chain[-2], chain[-1], point) <= 0:
                chain.pop()
            chain.append(point)
    return lower[:-1]+upper[:-1]


def polygon_distance(first, second):
    return min(*(clearance.segment_polygon_distance(edge, second)
                 for edge in zip(first, first[1:]+first[:1])),
               *(clearance.segment_polygon_distance(edge, first)
                 for edge in zip(second, second[1:]+second[:1])))


def rectangle_probe(interval):
    record = {'interval': interval, 'float_fraction': interval[1]-interval[0],
              'decimal_fraction': str(Fraction(str(interval[1]))-Fraction(str(interval[0])))}
    try:
        current = sample([0, 0], interval)
        corners = contact_corners(current)
        reflected = reflect_sample(current)
        actual = sorted(contact_corners(reflected))
        expected = sorted((horizontal, -vertical) for horizontal, vertical in corners)
        error = max(math.dist(before, after) for before, after in zip(actual, expected))
        center = [sum(point[axis] for point in corners)/4 for axis in range(2)]
        record.update(status='pass' if error <= 1e-12 else 'fail', reflection_error_mm=error,
                      reflected_interval=[reflected.edge_start, reflected.edge_end],
                      center_offset_mm=center, center_offset_length_mm=math.hypot(*center),
                      corners_mm_y_up=corners)
    except ValueError as error:
        record.update(status='rejected_by_current_contact_api', error=str(error))
    return record


def schema_probe(candidate, interval):
    changed = copy.deepcopy(candidate)
    identifier = next(iter(changed['actions']))
    changed['actions'][identifier]['edge'] = [[0, *interval], [1, *interval]]
    try:
        validate_gestures(changed)
        return {'status': 'pass', 'action_profile': identifier, 'geometry_changed': False}
    except ValueError as error:
        return {'status': 'rejected_by_current_schema', 'error': str(error), 'geometry_changed': False}


def obstacles(rows, case):
    result = []
    for part in clearance.swept_parts(rows, case):
        polygons = []
        for start, end in clearance.flatten(part['control_hull_mm']):
            polygons.append(hull(contact_corners(sample(start, [0, 1]))+contact_corners(sample(end, [0, 1]))))
        result.append({'owner': part['owner']['occurrence_id'], 'region': part['kind'],
                       'interval': part['interval'], 'polygons': polygons})
    return result


def site_probe(site, parts):
    center = [value*3.5 for value in site['position_local']]
    full = hull(contact_corners(sample(center, [0, 1])))
    records = []
    for part in parts:
        distance = min(polygon_distance(full, polygon) for polygon in part['polygons'])
        lower = max(0, distance-clearance.ERROR-1e-9)
        records.append({'occurrence': part['owner'], 'region': part['region'], 'interval': part['interval'],
                        'same_owner': part['owner'] == site['owner']['occurrence_id'],
                        'lower_distance_mm': lower, 'upper_distance_mm': distance+clearance.ERROR+1e-9,
                        'status': 'certified_clear' if lower > 0 else 'possible_contact'})
    return {'owner': site['owner']['occurrence_id'], 'canonical_parameter': site['canonical_parameter'],
            'center_mm': center, 'full_ramp_envelope_mm': full, 'regions': records,
            'nonowner_possible_contacts': [record for record in records if not record['same_owner'] and record['status'] != 'certified_clear'],
            'method': 'At a fixed center/orientation every full-to-corner or reverse-ramp rectangle is a subset of full contact; union equals full rectangle. Exact continuous-ramp envelope, not samples.',
            'scope': 'Stationary canonical site only; no moving ramp, connector or splice permission'}


def ownership_probe(candidate):
    result = []
    for text in ('nu', 'mu'):
        rows = investigation.canonical(candidate, text)['strokes']
        departure = [row for row in rows if row['letter'] == 0][-1]
        receiver = next(row for row in rows if row['letter'] == 1)
        result.append({'text': text, 'departure': departure['occurrence_id'], 'receiver': receiver['occurrence_id'],
                       'shared_departure_gesture_occurrences': [row['occurrence_id'] for row in rows if row['gesture'] == departure['gesture']],
                       'shared_departure_action_occurrences': [row['occurrence_id'] for row in rows if row['action_profile'] == departure['action_profile']],
                       'receiver_action': receiver['action_profile']})
    return {'status': 'boundary_consumer_not_admitted', 'canonical_rows': result,
            'finding': 'action_bundle resolves profiles through model.actions[model.gestures[original.gesture].action]; changing shared gesture/profile affects other occurrences. No isolated T/R/S boundary consumer exists in this capability package.',
            'required': 'New opt-in derived piece/action lineage retaining canonical source and contributor identities; no existing profile mutation or legacy-cap bypass.'}


def build_report(prior):
    candidate = source.read_json(source.CANDIDATE)
    sites = []
    for text in ('nu', 'mu'):
        candidates = [case for case in prior['investigation']['cases'] if case['text'] == text
                      and abs(case['receiving']['canonical_parameter']-.25) < 1e-12]
        case = max(candidates, key=lambda item: item['departure']['height_mm'])
        rows = investigation.canonical(candidate, text)['strokes']
        parts = obstacles(rows, case)
        sites.append({'text': text, 'departure': site_probe(case['departure'], parts),
                      'receiving': site_probe(case['receiving'], parts)})
    representations = {name: {'contact': rectangle_probe(interval), 'schema': schema_probe(candidate, interval)}
                       for name, interval in INTERVALS.items()}
    interpolated_end = float(np.interp(1, [0, 1], [1, .1]))
    return {'version': 'nu-corner-capability-v1', 'status': 'capability_review_required',
            'representations': representations, 'sites': sites, 'ownership': ownership_probe(candidate),
            'ramp_contract': {'negative': [[0, 1], [0, .1]], 'positive': [[0, 1], [.9, 1]],
                              'full_corner_return_union': 'Full rectangle at fixed site for both corners; mathematical containment, not positive-corner API acceptance',
                              'endpoint_rate_limit_per_s': 3, 'minimum_one_way_seconds': .9/3,
                              'minimum_roundtrip_seconds': 2*.9/3, 'moving_ramp_rate_validated': False,
                              'action_bridge_interpolation_endpoint': interpolated_end,
                              'endpoint_contact_accepted': rectangle_probe([0, interpolated_end])['status'] == 'pass'},
            'negative_corner_width_upper_mm': math.hypot(.045, .02),
            'accepted': False, 'connector_geometries': 0, 'controller_executions': 0,
            'raster_renders': 0, 'fitting_evaluations': 0,
            'code_sha256': digest(Path(__file__)), 'tests_sha256': digest(ROOT/'tests/test_nu_corner_contact.py'),
            'candidate_sha256': object_digest(candidate), 'proposal_sha256': PROPOSAL_PIN,
            'investigation_sha256': INVESTIGATION_PIN, 'tool_contract_sha256': TOOL_PIN,
            'bridge_sha256': digest(ROOT/'scribesim/pathguide/gesture_actions.py'),
            'contact_source_sha256': digest(ROOT/'scribesim/evo/nib_contact.py')}


def snapshot():
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    def timeout_handler(signum, frame):
        raise TimeoutError('300-second capability ceiling')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    try:
        with source.evidence.read_only_guard():
            approval = source.read_json(BASE/'capability-approval.json')
            prior = verify(approval)
            report = build_report(prior)
            report.update(approval=approval, approval_sha256=digest(BASE/'capability-approval.json'))
    except Exception as error:
        report = {'status': 'stopped', 'error': f'{type(error).__name__}: {error}', 'accepted': False}
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    report['elapsed_seconds'] = time.monotonic()-started
    payload = (json.dumps(report, indent=2, allow_nan=False)+'\n').encode()
    used = sum(filename.stat().st_size for filename in BASE.rglob('*') if filename.is_file())
    if used+len(payload) > MAX_BYTES:
        payload = (json.dumps({'status': 'stopped', 'error': '10MiB output ceiling', 'accepted': False})+'\n').encode()
    with (OUTPUT/'report.json').open('xb') as handle:
        handle.write(payload)
    return {'status': report['status'], 'elapsed_seconds': report['elapsed_seconds'],
            'report_sha256': digest(OUTPUT/'report.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot'])
    parser.parse_args()
    print(json.dumps(snapshot(), indent=2))
