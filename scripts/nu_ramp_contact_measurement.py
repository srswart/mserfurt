"""Bound saved ramp footprint overlap without constructing or admitting geometry."""

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import shutil
import signal
import time

from scripts import nu_excursion_locality as exact


ROOT = exact.ROOT
BASE = exact.BASE
SAVED = BASE/'j1-receiving-repair-001/report.json'
SAVED_PIN = '03979c687c1fb027b383e07d0b9c176b8c7e782b08f9df351905dba43f0deda6'
CANDIDATE_PIN = '616526b0952f02264d772508bce4342c325cc21a4648e49abd50efdaf01845f5'
OUTPUT = BASE/'ramp-contact-measurement-001'
APPROVAL = BASE/'ramp-contact-measurement-approval.json'
VERSION = 'saved-ramp-contact-measurement-v1'
CELLS = 64
GUARD = Fraction(1, 10**9)
EDGE = (Fraction(math.cos(math.radians(40))), -Fraction(math.sin(math.radians(40))))
NORMAL = (-EDGE[1], EDGE[0])
NORM_SQUARED = sum(value*value for value in EDGE)
WIDTH = Fraction(.45)
HALF_THICKNESS = Fraction(.01)


def digest_object(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def authority():
    paths = [Path(__file__), ROOT/'tests/test_nu_ramp_contact_measurement.py',
             ROOT/'docs/tech-direction/TD-018-ramp-contact-measurement.md']
    return {'version': VERSION,
            'owner_quote': "Okay let's handle bounded self-contact measurement on the saved candidate, keeping geometry and limits unchanged.",
            'saved_report_sha256': SAVED_PIN, 'candidate_sha256': CANDIDATE_PIN,
            'dependencies': {str(path.relative_to(ROOT)): exact.digest(path) for path in paths},
            'seconds': 300, 'max_output_bytes': 2*1024**2, 'minimum_free_bytes': 5*1024**3,
            'cells_per_cubic': CELLS, 'batches': 1, 'retries': 0,
            'new_candidates': 0, 'images': 0, 'fitting': False, 'physical_runs': 0,
            'geometry_limits_and_policy_unchanged': True}


def verify():
    if read(APPROVAL) != authority() or exact.digest(SAVED) != SAVED_PIN:
        raise ValueError('Exact authority and saved report required')
    report = read(SAVED)
    if (report['status'] != 'no_candidate_admitted' or report['new_candidates'] != 1
            or len(report['candidates']) != 1 or report['readiness']['status'] != 'pass'):
        raise ValueError('Wrong frozen evidence state')
    entry = report['candidates'][0]
    if entry['candidate_sha256'] != CANDIDATE_PIN or digest_object(entry['candidate']) != CANDIDATE_PIN:
        raise ValueError('Saved candidate changed')
    for name, checksum in report['readiness']['dependencies'].items():
        if exact.digest(ROOT/name) != checksum:
            raise ValueError('Previously recorded dependency changed: '+name)
    if exact.digest(BASE/'j1-receiving-repair-approval.json') != report['approval_sha256']:
        raise ValueError('Original repair approval changed')
    exact.verify()
    return report


def project(point, axis):
    return sum(value*weight for value, weight in zip(point, axis))


def distance_bounds(before, after):
    squared = exact.squared_distance(before, after)
    return tuple(Fraction(exact.sqrt_bound(squared, upper)) for upper in (False, True))


def length_bounds(curve):
    lower = distance_bounds(curve[0], curve[-1])[0]
    upper = sum(distance_bounds(before, after)[1] for before, after in zip(curve, curve[1:]))
    return lower, upper


def progress_bounds(lower, upper, total):
    if total[0] <= 0:
        raise ValueError('Positive aggregate length required')
    return max(Fraction(0), lower/total[1]), min(Fraction(1), upper/total[0])


def active_bounds(profile, progress):
    if profile == 'receiving':
        return tuple(Fraction(1, 10)+Fraction(9, 10)*value for value in progress)
    if profile == 'departure':
        return tuple(1-Fraction(9, 10)*value for value in reversed(progress))
    raise ValueError('Only saved full/corner ramps supported')


def footprint(center_edge, center_normal, profile, progress, inner=False):
    active = active_bounds(profile, progress)
    lower_edge = center_edge[1 if inner else 0]-WIDTH*NORM_SQUARED/2
    upper_edge = center_edge[0 if inner else 1]+WIDTH*NORM_SQUARED*(active[0 if inner else 1]-Fraction(1, 2))
    lower_normal = center_normal[1 if inner else 0]-HALF_THICKNESS*NORM_SQUARED
    upper_normal = center_normal[0 if inner else 1]+HALF_THICKNESS*NORM_SQUARED
    padding = GUARD if inner else -GUARD
    return ((lower_edge+padding, upper_edge-padding), (lower_normal+padding, upper_normal-padding))


def build_cells(curves, profile, divisions=CELLS):
    if type(divisions) is not int or divisions < 1 or divisions > CELLS:
        raise ValueError('Bounded positive cell count required')
    curves = [exact.exact_curve(curve) for curve in curves]
    if not curves or any(before[-1] != after[0] for before, after in zip(curves, curves[1:])):
        raise ValueError('Complete continuous aggregate required')
    cells = []
    for index, curve in enumerate(curves):
        for part in range(divisions):
            lower, upper = Fraction(part, divisions), Fraction(part+1, divisions)
            restricted = exact.restrict(curve, lower, upper)
            cells.append({'cubic': index, 'parameter': [lower, upper], 'curve': restricted,
                          'length': length_bounds(restricted)})
    total = tuple(sum(cell['length'][axis] for cell in cells) for axis in (0, 1))
    prefix = [Fraction(0), Fraction(0)]
    points = []
    for cell in cells:
        start = cell['curve'][0]
        progress = progress_bounds(*prefix, total)
        coordinates = [project(start, axis) for axis in (EDGE, NORMAL)]
        points.append({'cubic': cell['cubic'], 'parameter': cell['parameter'][0],
                       'progress': progress,
                       'inner': footprint(*[(value, value) for value in coordinates], profile, progress, True),
                       'outer': footprint(*[(value, value) for value in coordinates], profile, progress)})
        cell['arc_lower'] = prefix[0]
        end_prefix = [prefix[axis]+cell['length'][axis] for axis in (0, 1)]
        projections = [[project(point, axis) for point in cell['curve']] for axis in (EDGE, NORMAL)]
        cell['box'] = footprint(*[(min(values), max(values)) for values in projections],
                                profile, progress_bounds(prefix[0], end_prefix[1], total))
        prefix = end_prefix
    end = curves[-1][-1]
    coordinates = [project(end, axis) for axis in (EDGE, NORMAL)]
    progress = (Fraction(1), Fraction(1))
    points.append({'cubic': len(curves)-1, 'parameter': Fraction(1), 'progress': progress,
                   'inner': footprint(*[(value, value) for value in coordinates], profile, progress, True),
                   'outer': footprint(*[(value, value) for value in coordinates], profile, progress)})
    return cells, points, total


def disjoint(before, after):
    return any(first[1] < second[0] or second[1] < first[0] for first, second in zip(before, after))


def upper_float(value):
    result = float(value)
    while Fraction(result) < value:
        result = math.nextafter(result, math.inf)
    return result


def location(point):
    return {'cubic': point['cubic'], 'parameter_exact': str(point['parameter'])}


def revisit_witness(points):
    for first_index, first in enumerate(points):
        for last_index in range(first_index+2, len(points)):
            last = points[last_index]
            intersection = [(max(before[0], after[0]), min(before[1], after[1]))
                            for before, after in zip(first['inner'], last['inner'])]
            if any(upper-lower <= 2*GUARD for lower, upper in intersection):
                continue
            paper = tuple((lower+upper)/2 for lower, upper in intersection)
            for middle in points[first_index+1:last_index]:
                outside = [axis for axis, interval in enumerate(middle['outer'])
                           if paper[axis] < interval[0] or paper[axis] > interval[1]]
                if outside:
                    return {'status': 'certified_disconnected_point_membership',
                            'first': location(first), 'outside': location(middle), 'return': location(last),
                            'paper_nib_coordinates_exact': [str(value) for value in paper],
                            'membership_rectangles_exact': {
                                label: [[str(value) for value in interval] for interval in point[kind]]
                                for label, point, kind in [('first_inner', first, 'inner'),
                                                          ('outside_outer', middle, 'outer'),
                                                          ('return_inner', last, 'inner')]},
                            'outside_axes': outside,
                            'classification': 'Not automatically prohibited; no ramp ordinary-overlap policy extension'}
    return {'status': 'not_found_on_fixed_grid', 'meaning': 'Absence is not a continuous no-reentry proof'}


def measure(curves, profile, divisions=CELLS):
    cells, points, total = build_cells(curves, profile, divisions)
    possible, separated, cross_possible = 0, 0, 0
    maximum, cross_maximum = Fraction(0), Fraction(0)
    worst = None
    for first_index, first in enumerate(cells):
        arc_upper = Fraction(0)
        for last in cells[first_index:]:
            arc_upper += last['length'][1]
            if disjoint(first['box'], last['box']):
                separated += 1
                continue
            possible += 1
            if arc_upper > maximum:
                maximum = arc_upper
                worst = [{'cubic': cell['cubic'], 'parameter_exact': list(map(str, cell['parameter']))}
                         for cell in (first, last)]
            if first['cubic'] != last['cubic']:
                cross_possible += 1
                cross_maximum = max(cross_maximum, arc_upper)
    return {'status': 'measurement_complete', 'classification': 'unresolved',
            'aggregate_cubics': len(curves), 'cells': len(cells), 'domain': 'All unordered cell pairs including diagonal and cross-E',
            'separated_cell_pairs': separated, 'possible_overlap_cell_pairs': possible,
            'possible_cross_cubic_pairs': cross_possible,
            'aggregate_length_lower_mm': float(total[0]), 'aggregate_length_upper_mm': upper_float(total[1]),
            'possible_overlap_arc_separation_upper_mm': upper_float(maximum),
            'possible_cross_cubic_arc_separation_upper_mm': upper_float(cross_maximum),
            'worst_possible_pair': worst, 'point_membership_witness': revisit_witness(points),
            'proof': 'Exact-rational restricted control hulls enclose every center position; chord/control-polygon arc bounds enclose aggregate action progress. Disjoint finite-footprint slab supersets exclude pairs. Every remaining pair has intervening arc bounded by summed cell upper lengths, including complete cross-cubic travel.',
            'meaning': 'Derived separation bound, not a new locality cutoff, collision claim or ordinary-overlap permission'}


def run():
    verify()
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    report = {'version': VERSION, 'status': 'stopped', 'accepted': False, 'new_candidates': 0,
              'images': 0, 'fitting_evaluations': 0, 'physical_runs': 0, 'automatic_retries': 0,
              'approval': authority(), 'measurements': {}}
    def timeout_handler(signum, frame):
        raise TimeoutError('300-second measurement ceiling')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        frozen = verify()
        document = frozen['candidates'][0]['candidate']
        for profile in ('departure', 'receiving'):
            curves = [curve for piece in document['boundary'] if piece['contact_profile'] == profile
                      for curve in piece['cubics_mm']]
            report['measurements'][profile] = measure(curves, profile)
        verify()
        report.update(status='measurement_complete_admission_unresolved', frozen_inputs_unchanged=True,
                      saved_checks_reused_not_rerun=True,
                      scope='No source-readiness renewal, construction, rendering, limit or policy changes')
    except (ValueError, OSError, TimeoutError) as error:
        report['error'] = str(error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        report['elapsed_seconds'] = time.monotonic()-started
        payload = (json.dumps(report, indent=2, allow_nan=False)+'\n').encode()
        if len(payload) > 2*1024**2:
            raise ValueError('Measurement output ceiling')
        with (OUTPUT/'report.json').open('xb') as stream:
            stream.write(payload)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-approval', action='store_true')
    options = parser.parse_args()
    if options.record_approval:
        with APPROVAL.open('x') as stream:
            json.dump(authority(), stream, indent=2)
            stream.write('\n')
    else:
        result = run()
        print(json.dumps({'status': result['status'], 'seconds': result['elapsed_seconds']}))
