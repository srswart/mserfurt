"""Reinspect the immutable nm candidate under the approved tangent envelope."""

import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import signal
import time

from scripts import stroke_nm_construction as original


ROOT = original.ROOT
BASE = original.BASE
OUTPUT = BASE/'envelope-review-001'
REVISION = ROOT/'docs/tech-direction/TD-018-nm-attachment-envelope-revision.md'
REVISION_PIN = '2cec3eb8cf243f56a901d51d57ef5f38e318966839bd732f6a72965f164bda0b'
SAVED_PIN = '5b570b3df83e88dea38c4faf3b3c4badc121bf2055b0a0631efebf1b515b434c'
REPORT_PIN = '1f5cb5b87bb4aa6a264c09bc8a9bf0fccf6efacc24935f8b1327a3277d8f2a80'
HELPER_PIN = '1b8fa1266579ea06086af80f4300e4279eea8b098b76c8b93c49dbd90e95d303'
VERSION = 'nm-tangent-envelope-evaluation-v2'
GUARD = 1e-9


class Unresolved(ValueError):
    pass


def approval_record():
    return {'version': VERSION,
            'owner_quote': 'Okay please implement the revised checker and reinspecting the saved candidate.',
            'revision_sha256': REVISION_PIN, 'saved_candidate_sha256': SAVED_PIN,
            'original_report_sha256': REPORT_PIN, 'helper_sha256': HELPER_PIN,
            'reinspections': 1, 'verification_seconds': 300, 'conditional_nominal_seconds': 300,
            'max_output_bytes': original.MAX_BYTES, 'minimum_free_bytes': 5*1024**3,
            'geometry_generation': False, 'fitting': False, 'physical_runs': 0, 'retries': 0}


def verify(approval):
    if approval != approval_record():
        raise ValueError('Unapproved evaluation contract')
    for filename, expected in ((REVISION, REVISION_PIN), (BASE/'attempt-001/candidate.json', SAVED_PIN),
                               (BASE/'attempt-001/report.json', REPORT_PIN),
                               (Path(original.__file__), HELPER_PIN)):
        if original.digest(filename) != expected:
            raise ValueError(f'Frozen input changed: {filename}')
    original.verify_inputs(original.attachment.source.read_json(BASE/'approval.json'))


def quadratic_roots(coefficients):
    constant, linear, quadratic = map(Fraction, coefficients)
    if quadratic == 0:
        if linear == 0:
            if constant == 0:
                raise Unresolved('Identically zero polynomial')
            return []
        return [float(-constant/linear)]
    discriminant = linear*linear-4*quadratic*constant
    if discriminant < 0:
        return []
    if discriminant == 0:
        raise Unresolved('Double stationary/crossing root')
    with localcontext() as context:
        context.prec = 80
        def decimal(value):
            return Decimal(value.numerator)/Decimal(value.denominator)
        radical = decimal(discriminant).sqrt()
        return sorted(float((-decimal(linear)+sign*radical)/(2*decimal(quadratic)))
                      for sign in (-1, 1))


def power(cubic, axis):
    first, second, third, fourth = [Fraction(control[axis]) for control in cubic]
    return [first, 3*(second-first), 3*(first-2*second+third), fourth-first+3*(second-third)]


def interior_roots(coefficients):
    roots = quadratic_roots(coefficients)
    if any(abs(root) < 1e-10 or abs(root-1) < 1e-10 for root in roots):
        raise Unresolved('Root too close to domain boundary')
    interior = [root for root in roots if 0 < root < 1]
    for root in interior:
        lower, upper = Fraction(root-1e-12), Fraction(root+1e-12)
        constant, linear, quadratic = map(Fraction, coefficients)
        before = constant+lower*(linear+lower*quadratic)
        after = constant+upper*(linear+upper*quadratic)
        if before*after >= 0:
            raise Unresolved('Root enclosure cannot certify a simple crossing')
    return interior


def envelope(document):
    turn, transfer = [piece['cubics_mm'][0] for piece in document['pieces'][-2:]]
    start, foot, end = document['joins_mm']
    height = document['height_mm']
    retained = document['pieces'][3]['stroke']['cubics'][0]
    direction = original.attachment.tangent(retained, 1)
    delta = max(0, -.9*height/abs(direction[1])*direction[0])
    report = {'status': 'unresolved', 'delta_mm': delta, 'cap_mm': .0045,
              'cap_margin_mm': .0045-delta, 'original_negative_dx': 3*(turn[1][0]-turn[0][0])}
    if delta > .0045+GUARD:
        return {**report, 'status': 'fail', 'reason': 'Departure allowance exceeds cap'}
    if .0045-delta <= GUARD:
        return {**report, 'reason': 'Cap boundary unresolved'}
    horizontal = power(turn, 0)
    stationary = interior_roots([horizontal[1], 2*horizontal[2], 3*horizontal[3]])
    recovery = interior_roots(horizontal[1:])
    report.update(stationary_parameters=stationary, recovery_parameters=recovery,
                  stationary_intervals=[[root-1e-12, root+1e-12] for root in stationary],
                  recovery_intervals=[[root-1e-12, root+1e-12] for root in recovery])
    if len(stationary) != 1 or len(recovery) != 1:
        return {**report, 'status': 'fail', 'reason': 'Expected one minimum and one recovery'}
    if not 0 < stationary[0] < recovery[0] < 1:
        return {**report, 'status': 'fail', 'reason': 'Incorrect departure/recovery ordering'}
    first, _ = original.derivatives(turn)
    rise, _ = original.derivatives(transfer)
    if not (first[0][0] < -GUARD and first[-1][0] > GUARD
            and first[0][1] < -GUARD and first[1][1] < -GUARD and first[2][1] == 0
            and rise[0][1] == 0 and rise[1][1] > GUARD and rise[2][1] > GUARD
            and min(vector[0] for vector in rise) > GUARD):
        return {**report, 'status': 'fail', 'reason': 'Directed progress or baseline derivative violation'}
    minimum = original.attachment.point(turn, stationary[0])[0]
    speed_bound = max(math.hypot(*vector) for vector in first)
    extremum_error = speed_bound*1e-12+GUARD
    report['minimum_x_interval_mm'] = [minimum-extremum_error, minimum+extremum_error]
    report['maximum_left_excursion_upper_mm'] = start[0]-minimum+extremum_error
    report['envelope_margin_mm'] = minimum-extremum_error-(start[0]-delta)
    bounds_ok = minimum-extremum_error >= start[0]-delta and turn[-1][0] == foot[0]
    bounds_ok &= all(foot[0] <= control[0] <= end[0] for control in transfer)
    bounds_ok &= all(0 <= control[1] <= height+1e-12 for cubic in (turn, transfer) for control in cubic)
    if not bounds_ok:
        return {**report, 'reason': 'Envelope not certified'}
    local = original.clearance.restrict(turn, 0, min(1, recovery[0]+1e-12))
    locality_upper = max(math.dist(control, start) for control in local)+GUARD
    report.update(locality_radius_upper_mm=locality_upper, locality_limit_mm=.1125,
                  locality_margin_mm=.1125-locality_upper,
                  method='Exact-rational polynomial coefficients, 80-digit quadratic roots, guarded extrema; restricted Bezier convex hull locality')
    if locality_upper >= .1125:
        return {**report, 'reason': 'Locality not certified'}
    return {**report, 'status': 'pass'}


def swept_box(cubic):
    edge = original.clearance.EDGE
    return [(min(control[axis] for control in cubic)-abs(edge[axis])-GUARD,
             max(control[axis] for control in cubic)+abs(edge[axis])+GUARD) for axis in range(2)]


def pair_clearance(first, second, join=None, depth=0):
    first_box, second_box = swept_box(first), swept_box(second)
    overlap = [(max(before[0], after[0]), min(before[1], after[1]))
               for before, after in zip(first_box, second_box)]
    if any(lower > upper for lower, upper in overlap):
        return True
    edge = original.clearance.EDGE
    vectors = [edge]
    for cubic in (first, second):
        vectors.extend([after[axis]-before[axis] for axis in range(2)]
                       for index, before in enumerate(cubic) for after in cubic[index+1:])
    for vector in vectors:
        magnitude = math.hypot(*vector)
        if magnitude <= GUARD:
            continue
        normal = [-vector[1]/magnitude, vector[0]/magnitude]
        extent = abs(sum(value*axis for value, axis in zip(edge, normal)))+GUARD
        projections = [[sum(value*axis for value, axis in zip(control, normal)) for control in cubic]
                       for cubic in (first, second)]
        if (max(projections[0])+2*extent < min(projections[1]) or
                max(projections[1])+2*extent < min(projections[0])):
            return True
    if join is not None:
        radius_upper = math.hypot(*(max(abs(lower-center), abs(upper-center))
                                   for (lower, upper), center in zip(overlap, join)))
        if radius_upper+GUARD < .45:
            return True
    if depth >= 24:
        return False
    first_size = max(upper-lower for lower, upper in first_box)
    second_size = max(upper-lower for lower, upper in second_box)
    if first_size >= second_size:
        halves = original.clearance.split(first, .5)
        return all(pair_clearance(part, second, join, depth+1) for part in halves)
    halves = original.clearance.split(second, .5)
    return all(pair_clearance(first, part, join, depth+1) for part in halves)


def finite_nib(document):
    pieces = document['pieces']
    turn, transfer = [piece['cubics_mm'][0] for piece in pieces[-2:]]
    start, foot, end = document['joins_mm']
    checks = []
    for label, cubic in (('T', turn), ('R', transfer)):
        for index, piece in enumerate(pieces[:10]):
            join = start if label == 'T' and index == 3 else end if label == 'R' and index == 4 else None
            for cubic_index, retained in enumerate(piece['stroke']['cubics']):
                physical = [[value*3.5 for value in control] for control in retained]
                passed = pair_clearance(cubic, physical, join)
                checks.append({'new': label, 'retained': index, 'cubic': cubic_index,
                               'splice_center_mm': join, 'status': 'pass' if passed else 'unresolved'})
                if not passed:
                    return {'status': 'unresolved', 'pairs': checks,
                            'reason': 'Possible nonlocal finite-nib contact; bounded subdivision cannot certify separation/containment'}
    passed = pair_clearance(turn, transfer, foot)
    checks.append({'new': 'T/R', 'splice_center_mm': foot, 'status': 'pass' if passed else 'unresolved'})
    return {'status': 'pass' if passed else 'unresolved', 'pairs': checks,
            'method': 'Conservative control-hull swept boxes; recursive de Casteljau; full intersection enclosure inside splice disk or disjoint boxes',
            'coordinate_guard_mm': GUARD, 'max_subdivision_depth': 24,
            'nib_full_edge_mm': .45, 'nib_y_down_angle_deg': 40}


def run():
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    report = {'version': VERSION, 'status': 'stopped', 'accepted': False,
              'new_geometries': 0, 'raster_renders': 0, 'physical_runs': 0, 'fitting_evaluations': 0}
    def timeout_handler(signum, frame):
        raise TimeoutError('300-second reinspection ceiling exhausted')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    try:
        with original.attachment.source.evidence.read_only_guard():
            approval = original.attachment.source.read_json(BASE/'envelope-approval.json')
            verify(approval)
            report.update(approval=approval, approval_sha256=original.digest(BASE/'envelope-approval.json'),
                          checker_sha256=original.digest(Path(__file__)),
                          tests_sha256=original.digest(ROOT/'tests/test_stroke_nm_envelope.py'))
            document = original.attachment.source.read_json(BASE/'attempt-001/candidate.json')
            checks = original.geometry_checks(document)
            report['original_extent_check'] = checks.pop('extent_direction_baseline')
            checks['revised_envelope'] = envelope(document)
            checks['saved_identity'] = {'status': 'pass', 'sha256': SAVED_PIN,
                                        'method': 'Exact file pin; no construction function called'}
            if all(check['status'] == 'pass' for name, check in checks.items() if name != 'finite_nib_overlap'):
                checks['finite_nib_overlap'] = finite_nib(document)
            report['checks'] = checks
            report['status'] = ('rejected' if any(check['status'] == 'fail' for check in checks.values()) else
                                'geometry_pass' if all(check['status'] == 'pass' for check in checks.values()) else 'unresolved')
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report['elapsed_seconds'] = time.monotonic()-started
        original.save(OUTPUT, 'report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['reinspect'])
    parser.parse_args()
    print(json.dumps(run(), indent=2))
