"""One approved geometry-only construction, with fail-closed pre-render checks."""

import argparse
import copy
import json
import math
import shutil
import signal
import time
from pathlib import Path

from scripts import stroke_clearance_audit as clearance
from scribesim.handvalidate.specimen import ROOT, digest, object_digest


attachment = clearance.attachment
BASE = attachment.source.BASE/'nm-construction-v1'
PROPOSAL = ROOT/'docs/tech-direction/TD-018-nm-construction-proposal.md'
PROPOSAL_PIN = 'a2a47b91654d7a3d6d5347d67c61f46ae44e158c32523c0b32d2463adf7f932f'
CLEARANCE_PIN = 'd7dd39b61b91572d1ee3e241e0583266be9dcd9e4f0f577f74e9964820033943'
CANDIDATE_PIN = '01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd'
VERSION = 'nm-turn-rise-construction-v1'
CURVATURE_LIMIT = 1/.1125
MAX_BYTES = 100*1024**2


def approval_record():
    return {'version': VERSION, 'owner_quote': 'Yes approved. Please implement.',
            'date': '2026-09-10', 'proposal_sha256': PROPOSAL_PIN,
            'candidate_file_sha256': CANDIDATE_PIN,
            'candidate_object_sha256': attachment.source.context.CANDIDATE_SHA256,
            'attachment_report_sha256': clearance.PIN, 'clearance_report_sha256': CLEARANCE_PIN,
            'geometry_attempts': 1, 'geometry_seconds': 300, 'packet_seconds': 300,
            'max_output_bytes': MAX_BYTES, 'minimum_free_bytes': 5*1024**3,
            'conditional_pngs': 10, 'physical_runs': 0, 'fitting': False, 'retries': 0}


def verify_inputs(approval):
    if approval != approval_record():
        raise ValueError('Approval differs from the recorded owner decision')
    for path, expected in ((PROPOSAL, PROPOSAL_PIN),
                           (attachment.source.CANDIDATE, CANDIDATE_PIN),
                           (attachment.OUTPUT/'report.json', clearance.PIN),
                           (clearance.OUTPUT/'report.json', CLEARANCE_PIN)):
        if digest(path) != expected:
            raise ValueError(f'Frozen input changed: {path}')
    if attachment.source.read_json(clearance.OUTPUT/'report.json') != clearance.build_report():
        raise ValueError('Frozen clearance evidence no longer reproduces')


def construction(candidate, case, policy='connection-permitted'):
    if policy != 'connection-permitted':
        raise ValueError('Explicit connection policy required')
    compiled = attachment.canonical(candidate, 'nm')
    departure, receiving = case['departure'], case['receiving']
    height = candidate['primitives']['lower-return']['cubics'][0][0][1]
    rows = compiled['strokes']
    expected_sites = (attachment.site(rows[3], height, 'departure'),
                      attachment.site(rows[4], height, 'receiving'))
    if (departure, receiving) != expected_sites:
        raise ValueError('Unadmitted attachment sites or relative layout')
    start = [value*3.5 for value in departure['position_local']]
    end = [value*3.5 for value in receiving['position_local']]
    foot = [rows[3]['cubics'][0][-1][0]*3.5+.225, 0.0]
    outgoing = departure['directed_tangent_local_y_up']
    incoming = receiving['directed_tangent_local_y_up']
    height_mm = height*3.5
    if not (outgoing[1] < 0 < incoming[1] and start[0] < foot[0] < end[0]):
        raise ValueError('Invalid directed construction geometry')
    departure_handle = .9*height_mm/abs(outgoing[1])
    turn_handle = 2*(foot[0]-start[0])/3
    transfer_handle = (end[0]-foot[0])/3
    receiving_handle = .75*height_mm/incoming[1]
    turn = [start, [start[axis]+departure_handle*outgoing[axis] for axis in range(2)],
            [foot[0]-turn_handle, 0.0], foot]
    transfer = [foot, [foot[0]+transfer_handle, 0.0],
                [end[axis]-receiving_handle*incoming[axis] for axis in range(2)], end]
    pieces = []
    for row in rows:
        retained = copy.deepcopy(row)
        interval = [0, 1]
        for site in (departure, receiving):
            if row['occurrence_id'] == site['owner']['occurrence_id']:
                interval = site['retained_interval']
                retained['cubics'][0] = clearance.restrict(row['cubics'][0], *interval)
        pieces.append({'kind': 'retained', 'canonical_owner': copy.deepcopy(row),
                       'interval': interval, 'stroke': retained})
    pieces.extend([
        {'kind': 'terminal-turn', 'owner': departure['owner'], 'contact': 'pen-down',
         'contributors': [departure['owner']], 'removed_interval': departure['proposed_replacement_interval'],
         'cubics_mm': [turn]},
        {'kind': 'boundary-transfer-receiving', 'owner': 'boundary:0:3->1:0', 'contact': 'pen-down',
         'contributors': [departure['owner'], receiving['owner']],
         'removed_interval': receiving['proposed_replacement_interval'], 'cubics_mm': [transfer]}])
    return {'version': VERSION, 'coordinates': 'physical-mm-y-up for new cubics; canonical local for retained',
            'canonical_sha256': object_digest(compiled), 'policy': policy, 'pieces': pieces,
            'joins_mm': [start, foot, end], 'height_mm': height_mm,
            'physical_execution_authorized': False}


def validate_identity(document, candidate, case):
    if document != construction(candidate, case):
        raise ValueError('Undeclared geometry, topology, contact, ownership or placement edit')


def derivatives(cubic):
    first = [[3*(after[axis]-before[axis]) for axis in range(2)]
             for before, after in zip(cubic, cubic[1:])]
    second = [[2*(after[axis]-before[axis]) for axis in range(2)]
              for before, after in zip(first, first[1:])]
    return first, second


def curvature_at(cubic, parameter):
    first, second = derivatives(cubic)
    velocity = [(1-parameter)**2*first[0][axis]+2*parameter*(1-parameter)*first[1][axis]
                +parameter**2*first[2][axis] for axis in range(2)]
    acceleration = [(1-parameter)*second[0][axis]+parameter*second[1][axis] for axis in range(2)]
    speed = math.hypot(*velocity)
    return math.inf if speed == 0 else abs(velocity[0]*acceleration[1]-velocity[1]*acceleration[0])/speed**3


def curvature_check(cubic, lower=0.0, upper=1.0, depth=0):
    for parameter in (0.0, .5, 1.0):
        observed = curvature_at(cubic, parameter)
        if observed > CURVATURE_LIMIT+1e-7:
            return {'status': 'fail', 'witness_parameter': lower+(upper-lower)*parameter,
                    'curvature_per_mm': observed, 'limit_per_mm': CURVATURE_LIMIT,
                    'margin_per_mm': CURVATURE_LIMIT-observed}
    first, second = derivatives(cubic)
    bounds = [(min(vector[axis] for vector in first), max(vector[axis] for vector in first))
              for axis in range(2)]
    speed_lower = math.sqrt(sum((min(abs(low), abs(high)) if low*high > 0 else 0)**2
                                for low, high in bounds))
    numerator_upper = max(abs(velocity[0]*acceleration[1]-velocity[1]*acceleration[0])
                          for velocity in first for acceleration in second)
    bound = math.inf if speed_lower == 0 else numerator_upper/speed_lower**3
    if bound+1e-7 <= CURVATURE_LIMIT:
        return {'status': 'pass', 'certified_upper_per_mm': bound+1e-7,
                'margin_per_mm': CURVATURE_LIMIT-bound-1e-7}
    if depth >= 20:
        return {'status': 'unresolved', 'interval': [lower, upper]}
    before, after = clearance.split(cubic, .5)
    middle = (lower+upper)/2
    results = [curvature_check(before, lower, middle, depth+1),
               curvature_check(after, middle, upper, depth+1)]
    return next((result for result in results if result['status'] != 'pass'),
                {'status': 'pass', 'certified_upper_per_mm': max(
                    result.get('certified_upper_per_mm', 0) for result in results)})


def length_bounds(cubic, tolerance=1e-7, depth=0):
    lower = math.dist(cubic[0], cubic[-1])
    upper = sum(math.dist(before, after) for before, after in zip(cubic, cubic[1:]))
    if upper-lower <= tolerance:
        return lower, upper
    if depth >= 24:
        raise ValueError('Unresolved arc-length bound')
    before, after = clearance.split(cubic, .5)
    first = length_bounds(before, tolerance/2, depth+1)
    second = length_bounds(after, tolerance/2, depth+1)
    return first[0]+second[0], first[1]+second[1]


def geometry_checks(document):
    turn, transfer = [piece['cubics_mm'][0] for piece in document['pieces'][-2:]]
    start, foot, end = document['joins_mm']
    height = document['height_mm']
    checks = {}
    monotonic = True
    for cubic, sign in ((turn, -1), (transfer, 1)):
        first, _ = derivatives(cubic)
        monotonic &= all(vector[0] > 0 and sign*vector[1] >= 0 for vector in first)
        monotonic &= any(sign*vector[1] > 0 for vector in first)
    bounded = all(start[0] <= control[0] <= end[0] and 0 <= control[1] <= height+1e-12
                  for cubic in (turn, transfer) for control in cubic)
    checks['extent_direction_baseline'] = {'status': 'pass' if monotonic and bounded else 'unresolved',
        'method': 'Bernstein control hull and derivative signs; positive interior height; sole baseline join B'}
    retained = document['pieces']
    before = retained[3]['stroke']['cubics'][0]
    after = retained[4]['stroke']['cubics'][0]
    tangent_errors = [math.dist(attachment.tangent(left, 1), attachment.tangent(right, 0))
                      for left, right in ((before, turn), (turn, transfer), (transfer, after))]
    position_errors = [math.dist([value*3.5 for value in before[-1]], start),
                       math.dist([value*3.5 for value in after[0]], end)]
    checks['attachments'] = {'status': 'pass' if max(tangent_errors) <= 1e-8 and max(position_errors) <= 1e-9 else 'fail',
                             'tangent_errors': tangent_errors, 'position_errors_mm': position_errors}
    bounds = [length_bounds(cubic) for cubic in (turn, transfer)]
    upper = sum(bound[1] for bound in bounds)+1e-9
    limit = 1.25*math.hypot(end[0]-start[0], 2*height)
    checks['length'] = {'status': 'pass' if upper <= limit else 'fail', 'upper_mm': upper,
                        'lower_mm': sum(bound[0] for bound in bounds)-1e-9, 'limit_mm': limit, 'margin_mm': limit-upper}
    checks['turn_curvature'] = curvature_check(turn)
    checks['transfer_curvature'] = curvature_check(transfer)
    checks['finite_nib_overlap'] = {'status': 'not_evaluated',
        'reason': 'Downstream admission is blocked until every preceding geometry gate passes; no rendering entrypoint'}
    return checks


def save(directory, name, value):
    payload = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    used = sum(path.stat().st_size for path in directory.rglob('*') if path.is_file())
    if used+len(payload) > MAX_BYTES-65536:
        raise ValueError('Output budget exhausted')
    with (directory/name).open('xb') as handle:
        handle.write(payload)


def run():
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    destination = BASE/'attempt-001'
    destination.mkdir(exist_ok=False)
    started = time.monotonic()
    report = {'version': VERSION, 'status': 'stopped', 'raster_renders': 0,
              'controller_executions': 0, 'fitting_evaluations': 0, 'accepted': False}
    def timeout_handler(signum, frame):
        raise TimeoutError('300-second geometry budget exhausted')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    try:
        with attachment.source.evidence.read_only_guard():
            approval = attachment.source.read_json(BASE/'approval.json')
            verify_inputs(approval)
            report['approval_sha256'] = digest(BASE/'approval.json')
            report['code_sha256'] = digest(Path(__file__))
            report['tests_sha256'] = digest(ROOT/'tests/test_stroke_nm_construction.py')
            candidate = attachment.source.read_json(attachment.source.CANDIDATE)
            prior = attachment.source.read_json(attachment.OUTPUT/'report.json')
            cases = [case for case in prior['investigation']['site_pairs'] if case['text'] == 'nm']
            case = max(cases, key=lambda item: (item['departure']['height_mm'], item['receiving']['height_mm']))
            document = construction(candidate, case)
            save(destination, 'candidate.json', document)
            validate_identity(document, candidate, case)
            report['candidate_sha256'] = digest(destination/'candidate.json')
            report['checks'] = {'exact_body_ownership_placement': {'status': 'pass'}, **geometry_checks(document)}
            report['status'] = 'rejected' if any(check['status'] == 'fail' for check in report['checks'].values()) else 'unresolved'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report['elapsed_seconds'] = time.monotonic()-started
        save(destination, 'report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run'])
    parser.parse_args()
    print(json.dumps(run(), indent=2))
