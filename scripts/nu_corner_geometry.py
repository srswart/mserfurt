"""One fixed nu/mu geometry attempt; no search, rendering or physical consumer."""

import argparse
import copy
import json
import math
from pathlib import Path
import shutil
import signal
import time

from scripts import nu_boundary_actions as actions
from scripts import stroke_nm_envelope as bounds


capability = actions.capability
source = capability.source
ROOT = actions.ROOT
BASE = capability.BASE
OUTPUT = BASE/'geometry-001'
CONTRACT_PIN = 'f02c6105d8990616d7c74cb53ebc00030025728c6f1d90d809a65e0e649f1c14'
VERSION = 'nu-coupled-corner-geometry-v1'
GUARD = 1e-9


def approval_record():
    return {'owner_quote': "Yes implementation approved. Let's do it.", 'version': VERSION,
            'proposal_sha256': capability.PROPOSAL_PIN, 'contract_report_sha256': CONTRACT_PIN,
            'scope': 'One fixed nu and one fixed mu instance; stop on failure/unresolved; no rendering',
            'seconds': 300, 'maximum_instances': 2, 'max_output_bytes': 10*1024**2,
            'minimum_free_bytes': 5*1024**3, 'retries': 0, 'raster_renders': 0,
            'controller_executions': 0, 'fitting': False}


def verify(approval):
    if approval != approval_record():
        raise ValueError('Exact geometry-only approval required')
    if actions.digest(actions.OUTPUT/'report.json') != CONTRACT_PIN:
        raise ValueError('Frozen boundary contract report changed')
    report = source.read_json(actions.OUTPUT/'report.json')
    for filename, expected in ((Path(actions.__file__), report['code_sha256']),
                               (ROOT/'tests/test_nu_boundary_actions.py', report['tests_sha256']),
                               (actions.OUTPUT/'contracts.json', report['contracts_file_sha256'])):
        if actions.digest(filename) != expected:
            raise ValueError('Frozen boundary contract source changed')
    prior = capability.verify(source.read_json(BASE/'capability-approval.json'))
    if actions.digest(capability.OUTPUT/'report.json') != report['capability_report_sha256']:
        raise ValueError('Frozen capability evidence changed')
    return prior, source.read_json(actions.OUTPUT/'contracts.json')


def construct(candidate, manifest, prior):
    actions.validate_manifest(manifest, candidate, prior)
    rows = capability.investigation.canonical(candidate, manifest['exposed_fixture'])['strokes']
    indexed = {row['occurrence_id']: row for row in rows}
    slots = manifest['boundary_slots']
    departure = indexed[slots[0]['source_owner']]
    receiver = indexed[slots[2]['source_owner']]
    departure_parameter = float(actions.exact(slots[0]['removed_interval'][0]))
    start = [value*3.5 for value in capability.clearance.attachment.point(departure['cubics'][0], departure_parameter)]
    end = [value*3.5 for value in capability.clearance.attachment.point(receiver['cubics'][0], .25)]
    foot = [departure['cubics'][0][-1][0]*3.5+.225, 0.0]
    apex = [end[0]-.225, 3.5]
    outgoing = capability.clearance.attachment.tangent(departure['cubics'][0], departure_parameter)
    incoming = capability.clearance.attachment.tangent(receiver['cubics'][0], .25)
    if not (outgoing[1] < 0 and incoming[1] < 0 and start[0] < foot[0] < apex[0] < end[0] and 0 < end[1] < 3.5):
        raise ValueError('Proposed directed site ordering fails')
    height = candidate['primitives']['lower-return']['cubics'][0][0][1]*3.5
    departure_handle = .9*height/abs(outgoing[1])
    foot_handle = 2*(foot[0]-start[0])/3
    rise_handle = (apex[0]-foot[0])/3
    apex_handle = 2*(end[0]-apex[0])/3
    receiving_handle = .75*(3.5-end[1])/abs(incoming[1])
    cubics = [
        [start, [start[axis]+departure_handle*outgoing[axis] for axis in range(2)], [foot[0]-foot_handle, 0], foot],
        [foot, [foot[0]+rise_handle, 0], [apex[0]-rise_handle, 3.5], apex],
        [apex, [apex[0]+apex_handle, 3.5], [end[axis]-receiving_handle*incoming[axis] for axis in range(2)], end]]
    retained = []
    for piece in manifest['retained']:
        row = indexed[piece['canonical_owner']['occurrence_id']]
        lower, upper = map(float, map(actions.exact, piece['source_interval']))
        clipped = copy.deepcopy(row['cubics'])
        if [lower, upper] != [0, 1]:
            clipped[0] = capability.clearance.restrict(clipped[0], lower, upper)
        retained.append({**copy.deepcopy(piece), 'cubics_mm': [[[value*3.5 for value in control] for control in cubic] for cubic in clipped]})
    boundary = [{**copy.deepcopy(slot), 'cubics_mm': [cubic]} for slot, cubic in zip(slots, cubics)]
    return {'version': VERSION, 'fixture': manifest['exposed_fixture'], 'contract_sha256': actions.object_digest(manifest),
            'retained': retained, 'boundary': boundary, 'anchors_mm': {'A': start, 'B': foot, 'D': apex, 'C': end},
            'original_receiver_top_mm': [value*3.5 for value in receiver['cubics'][0][0]],
            'outgoing_tangent': outgoing, 'incoming_tangent': incoming,
            'profiles': copy.deepcopy(manifest['profiles']), 'coordinates': 'physical-mm-y-up',
            'geometry_accepted': False, 'physical_execution_approved': False}


def departure_check(cubic, outgoing, height):
    delta = max(0, -.9*height/abs(outgoing[1])*outgoing[0])
    horizontal = bounds.power(cubic, 0)
    minimum = bounds.interior_roots([horizontal[1], 2*horizontal[2], 3*horizontal[3]])
    recovery = bounds.interior_roots(horizontal[1:])
    result = {'status': 'unresolved', 'delta_mm': delta, 'cap_margin_mm': .0045-delta,
              'stationary_roots': minimum, 'recovery_roots': recovery}
    if delta > .0045+GUARD:
        return {**result, 'status': 'fail', 'reason': 'Departure allowance exceeds cap'}
    if not (len(minimum) == len(recovery) == 1 and 0 < minimum[0] < recovery[0] < 1):
        return {**result, 'status': 'fail', 'reason': 'Departure horizontal topology'}
    first, _ = bounds.original.derivatives(cubic)
    if not (first[0][0] < 0 < first[-1][0] and first[0][1] < 0 and first[1][1] < 0 and first[-1][1] == 0):
        return {**result, 'status': 'fail', 'reason': 'Departure directed progress'}
    error = max(math.hypot(*vector) for vector in first)*1e-12+GUARD
    left = capability.clearance.attachment.point(cubic, minimum[0])[0]-error
    local = capability.clearance.restrict(cubic, 0, recovery[0]+1e-12)
    radius = max(math.dist(point, cubic[0]) for point in local)+GUARD
    margin = left-(cubic[0][0]-delta)
    result.update(envelope_margin_mm=margin, locality_upper_mm=radius, locality_margin_mm=.1125-radius)
    if margin > 0 and radius < .1125 and delta < .0045-GUARD and all(0 <= point[1] <= height+1e-12 for point in cubic):
        result['status'] = 'pass'
    return result


def increasing_x(cubic):
    polynomial = bounds.power(cubic, 0)
    coefficients = [polynomial[1], 2*polynomial[2], 3*polynomial[3]]
    probes = [0, 1]
    if coefficients[2] != 0:
        vertex = float(-coefficients[1]/(2*coefficients[2]))
        if 0 < vertex < 1:
            probes.append(vertex)
    values = [float(coefficients[0]+parameter*(coefficients[1]+parameter*coefficients[2])) for parameter in probes]
    minimum = min(values)
    return {'status': 'pass' if minimum > GUARD else 'fail' if minimum < -GUARD else 'unresolved',
            'minimum_dx': minimum, 'parameters_checked': probes, 'method': 'Analytic quadratic minimum including endpoints'}


def geometry_checks(document):
    cubics = [piece['cubics_mm'][0] for piece in document['boundary']]
    checks = {}
    start = document['anchors_mm']['A']
    checks['departure_envelope'] = departure_check(cubics[0], document['outgoing_tangent'], start[1])
    for piece, cubic in zip(document['boundary'], cubics):
        name = piece['piece_id']
        lower, upper = bounds.original.length_bounds(cubic)
        limit = 1.25*math.dist(cubic[0], cubic[-1])
        checks[name+'_length'] = {'status': 'pass' if upper+GUARD < limit else 'fail' if lower-GUARD > limit else 'unresolved',
                                 'lower_mm': lower-GUARD, 'upper_mm': upper+GUARD,
                                 'limit_mm': limit, 'margin_mm': limit-upper-GUARD}
        checks[name+'_curvature'] = bounds.original.curvature_check(cubic)
        if name != 'T':
            checks[name+'_rightward'] = increasing_x(cubic)
    apex_shift = math.dist(document['anchors_mm']['D'], document['original_receiver_top_mm'])
    checks['receiver_top_shift'] = {'status': 'pass' if apex_shift < .45-GUARD else 'unresolved',
                                    'shift_mm': apex_shift, 'limit_mm': .45}
    tangent_errors = [math.dist(capability.clearance.attachment.tangent(cubics[0], 0), document['outgoing_tangent']),
                      math.dist(capability.clearance.attachment.tangent(cubics[2], 1), document['incoming_tangent'])]
    tangent_errors += [math.dist(capability.clearance.attachment.tangent(before, 1), capability.clearance.attachment.tangent(after, 0))
                       for before, after in zip(cubics, cubics[1:])]
    indexed = {piece['canonical_owner']['occurrence_id']: piece for piece in document['retained']}
    attachment_errors = [math.dist(indexed[document['boundary'][0]['source_owner']]['cubics_mm'][0][-1], cubics[0][0]),
                         math.dist(indexed[document['boundary'][2]['source_owner']]['cubics_mm'][0][0], cubics[2][-1])]
    checks['attachments'] = {'status': 'pass' if max(tangent_errors) <= 1e-8 and max(attachment_errors) <= 1e-9 else 'fail',
                            'tangent_errors': tangent_errors, 'position_errors_mm': attachment_errors}
    rise_first, _ = bounds.original.derivatives(cubics[1])
    receiving_first, _ = bounds.original.derivatives(cubics[2])
    vertical = (rise_first[0][1] == rise_first[-1][1] == 0 and rise_first[1][1] > 0
                and receiving_first[0][1] == 0 and receiving_first[1][1] < 0 and receiving_first[-1][1] < 0
                and all(0 <= point[1] <= 3.5 for cubic in cubics[1:] for point in cubic))
    checks['vertical_band'] = {'status': 'pass' if vertical else 'unresolved', 'method': 'Bernstein derivative signs and control hull'}
    maximum = math.hypot(.045, .02)
    limit = .25*(.45*math.cos(math.radians(40))+.02*math.sin(math.radians(40)))
    checks['thin_core'] = {'status': 'pass' if maximum+GUARD < limit else 'unresolved',
                           'width_upper_mm': maximum+GUARD, 'limit_mm': limit,
                           'method': 'Direction-independent rectangular support bound over exact constant negative-corner R profile'}
    return checks


def contact_enclosure(cubic, profile):
    interval = ('0', '0.1') if profile == 'core' else ('0', '1')
    offsets = actions.BoundaryContact((0, 0), interval, 'physical-y-up').corners()
    return [[control[axis]+offset[axis] for axis in range(2)] for control in cubic for offset in offsets]


def contact_pair(first, first_profile, second, second_profile, join=None, depth=0):
    first_hull = contact_enclosure(first, first_profile)
    second_hull = contact_enclosure(second, second_profile)
    overlap = [(max(min(point[axis] for point in first_hull), min(point[axis] for point in second_hull))-GUARD,
                min(max(point[axis] for point in first_hull), max(point[axis] for point in second_hull))+GUARD)
               for axis in range(2)]
    if any(lower > upper for lower, upper in overlap):
        return True
    edge = capability.clearance.EDGE
    vectors = [edge, [-edge[1], edge[0]]]
    for cubic in (first, second):
        vectors += [[after[axis]-before[axis] for axis in range(2)]
                    for index, before in enumerate(cubic) for after in cubic[index+1:]]
    for vector in vectors:
        magnitude = math.hypot(*vector)
        if magnitude <= GUARD:
            continue
        normal = [-vector[1]/magnitude, vector[0]/magnitude]
        projections = [[sum(value*axis for value, axis in zip(point, normal)) for point in polygon]
                       for polygon in (first_hull, second_hull)]
        if max(projections[0])+2*GUARD < min(projections[1]) or max(projections[1])+2*GUARD < min(projections[0]):
            return True
    if join is not None:
        radius = math.hypot(*(max(abs(lower-center), abs(upper-center)) for (lower, upper), center in zip(overlap, join)))
        if radius+GUARD < .45:
            return True
    if depth >= 24:
        return False
    sizes = [max(max(point[axis] for point in cubic)-min(point[axis] for point in cubic) for axis in range(2))
             for cubic in (first, second)]
    if sizes[0] >= sizes[1]:
        return all(contact_pair(part, first_profile, second, second_profile, join, depth+1)
                   for part in capability.clearance.split(first, .5))
    return all(contact_pair(first, first_profile, part, second_profile, join, depth+1)
               for part in capability.clearance.split(second, .5))


def contact_checks(document):
    results = []
    for piece in document['boundary']:
        for retained in document['retained']:
            join = None
            if retained['canonical_owner']['occurrence_id'] == piece['source_owner']:
                join = document['anchors_mm']['A' if piece['piece_id'] == 'T' else 'C']
            for cubic_index, cubic in enumerate(retained['cubics_mm']):
                passed = contact_pair(piece['cubics_mm'][0], piece['contact_profile'], cubic, 'full', join)
                results.append({'pieces': [piece['piece_id'], retained['piece_id']], 'retained_cubic': cubic_index,
                                'join': join, 'status': 'pass' if passed else 'unresolved'})
                if not passed:
                    return {'status': 'unresolved', 'pairs': results, 'reason': 'Swept contact enclosure not separated or confined to its splice disk'}
    for first_index, first in enumerate(document['boundary']):
        for second in document['boundary'][first_index+1:]:
            join = document['anchors_mm']['B'] if (first['piece_id'], second['piece_id']) == ('T', 'R') else (
                document['anchors_mm']['D'] if (first['piece_id'], second['piece_id']) == ('R', 'S') else None)
            passed = contact_pair(first['cubics_mm'][0], first['contact_profile'], second['cubics_mm'][0], second['contact_profile'], join)
            results.append({'pieces': [first['piece_id'], second['piece_id']], 'join': join,
                            'status': 'pass' if passed else 'unresolved'})
            if not passed:
                return {'status': 'unresolved', 'pairs': results, 'reason': 'New-piece contact not certified'}
    return {'status': 'pass', 'pairs': results,
            'method': 'Finite .02mm rectangle Minkowski/control-hull enclosures, guarded separating axes and whole intersection containment; full-contact supersets bound every T/S ramp phase, exact negative corner on R',
            'ramp_bound': 'Conservative envelope proof, not a static-width render or sampled acceptance. Actual ink accumulation is not measured.'}


def save(name, value):
    payload = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    used = sum(filename.stat().st_size for filename in OUTPUT.rglob('*') if filename.is_file())
    if used+len(payload) > 10*1024**2-65536:
        raise ValueError('Local output ceiling')
    with (OUTPUT/name).open('xb') as handle:
        handle.write(payload)


def run():
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    report = {'version': VERSION, 'status': 'stopped', 'accepted': False, 'cases': {},
              'connector_instances': 0, 'raster_renders': 0, 'controller_executions': 0, 'fitting_evaluations': 0}
    def timeout_handler(signum, frame):
        raise TimeoutError('300-second geometry ceiling')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    try:
        with source.evidence.read_only_guard():
            approval = source.read_json(BASE/'geometry-approval.json')
            prior, contracts = verify(approval)
            report.update(approval=approval, approval_sha256=actions.digest(BASE/'geometry-approval.json'),
                          code_sha256=actions.digest(Path(__file__)), tests_sha256=actions.digest(ROOT/'tests/test_nu_corner_geometry.py'))
            candidate = source.read_json(source.CANDIDATE)
            for text in ('nu', 'mu'):
                document = construct(candidate, contracts[text], prior)
                report['connector_instances'] += 1
                save(text+'-candidate.json', document)
                checks = geometry_checks(document)
                checks['finite_contact_sweep'] = {'status': 'not_evaluated',
                    'reason': 'Downstream continuous-contact and nonlocal overlap admission stays gated until structural checks pass'}
                report['cases'][text] = {'candidate_sha256': actions.digest(OUTPUT/(text+'-candidate.json')), 'checks': checks}
                if any(check['status'] != 'pass' for name, check in checks.items() if name != 'finite_contact_sweep'):
                    report['status'] = 'rejected' if any(check['status'] == 'fail' for check in checks.values()) else 'unresolved'
                    report['not_started'] = ['mu'] if text == 'nu' else []
                    break
                checks['finite_contact_sweep'] = contact_checks(document)
                if checks['finite_contact_sweep']['status'] != 'pass':
                    report['status'] = 'unresolved'
                    report['not_started'] = ['mu'] if text == 'nu' else []
                    break
            else:
                report['status'] = 'geometry_checks_pass_nominal_gated'
                report['not_started'] = []
    except Exception as error:
        report.update(status='stopped', error=f'{type(error).__name__}: {error}')
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report['elapsed_seconds'] = time.monotonic()-started
        save('report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run'])
    parser.parse_args()
    print(json.dumps(run(), indent=2))
