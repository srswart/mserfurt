"""Exact-rational measurement of saved excursion spans; no construction or fitting."""

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import signal
import time


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1'
SAVED = BASE/'continuation-001/report.json'
SAVED_PIN = '06072aa101288038217bcfe7afcedb563bf41572c2b28de2a38b0bea71938bf2'
READY_PIN = 'c4f2f1fdc6ad4883ae9c6be358669005876dd1042b3c197fb4e12c3f580d8915'
OUTPUT = BASE/'locality-001'
VERSION = 'nu-saved-excursion-locality-v1'
RADIUS = Fraction(.1125)
HORIZONTAL = Fraction(.0045)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def approval():
    return {'version': VERSION, 'owner_quote': "Let's measure the saved excursion spans more precisely, without refitting or changing limits.",
            'saved_report_sha256': SAVED_PIN, 'readiness_report_sha256': READY_PIN,
            'seconds': 300, 'max_output_bytes': 1024**2, 'automatic_retries': 0,
            'new_candidates': 0, 'images': 0, 'fitting': False, 'physical_runs': 0,
            'radius_mm': .1125, 'horizontal_limit_mm': .0045,
            'full_excursion_domains': True}


def verify():
    if digest(SAVED) != SAVED_PIN or digest(BASE/'readiness-001/report.json') != READY_PIN:
        raise ValueError('Saved study or historical readiness receipt changed')
    if json.loads((BASE/'locality-approval.json').read_text()) != approval():
        raise ValueError('Exact measurement-only approval required')
    report = json.loads(SAVED.read_text())
    ready = json.loads((BASE/'readiness-001/report.json').read_text())
    if ready['status'] != 'pass' or report['status'] != 'no_candidate_admitted':
        raise ValueError('Wrong saved evidence state')
    for name, checksum in ready['dependencies'].items():
        if digest(ROOT/name) != checksum:
            raise ValueError('Previously recorded dependency changed: '+name)
    for entry in report['candidates']:
        checksum = hashlib.sha256(json.dumps(entry['candidate'], sort_keys=True, allow_nan=False).encode()).hexdigest()
        if checksum != entry['candidate_sha256']:
            raise ValueError('Frozen candidate controls changed')
    return report


def exact_curve(cubic):
    if len(cubic) != 4 or any(len(point) != 2 or any(not math.isfinite(value) for value in point) for point in cubic):
        raise ValueError('Finite cubic required')
    return [[Fraction(value) for value in point] for point in cubic]


def split(cubic, parameter):
    levels = [cubic]
    while len(levels[-1]) > 1:
        levels.append([[(1-parameter)*before[axis]+parameter*after[axis] for axis in (0, 1)]
                       for before, after in zip(levels[-1], levels[-1][1:])])
    return [level[0] for level in levels], [level[-1] for level in reversed(levels)]


def restrict(cubic, lower, upper):
    if not 0 <= lower < upper <= 1:
        raise ValueError('Full nonempty source interval required')
    prefix = split(cubic, upper)[0] if upper < 1 else cubic
    return split(prefix, lower/upper)[1] if lower > 0 else prefix


def point(cubic, parameter):
    return split(cubic, parameter)[0][-1]


def squared_distance(location, anchor):
    return sum((value-origin)**2 for value, origin in zip(location, anchor))


def sqrt_bound(squared, upper):
    value = math.sqrt(float(squared))
    while (Fraction(value)**2 < squared if upper else Fraction(value)**2 > squared):
        value = math.nextafter(value, math.inf if upper else -math.inf)
    return value


def crossing_bracket(cubic, root, receiving):
    root = Fraction(root)
    lower, upper = root-Fraction(1, 10**12), root+Fraction(1, 10**12)
    if not 0 < lower < upper < 1:
        raise ValueError('Crossing root bracket outside source domain')
    anchor = cubic[-1] if receiving else cubic[0]
    horizontal = [control[0]-anchor[0] for control in cubic]
    coefficients = [horizontal[0], 3*(horizontal[1]-horizontal[0]),
                    3*(horizontal[0]-2*horizontal[1]+horizontal[2]),
                    horizontal[3]-horizontal[0]+3*(horizontal[1]-horizontal[2])]
    factor = [sum(coefficients[1:]), coefficients[2]+coefficients[3], coefficients[3]] if receiving else coefficients[1:]
    def evaluate(parameter):
        return sum(value*parameter**index for index, value in enumerate(factor))
    if evaluate(lower)*evaluate(upper) >= 0:
        raise ValueError('Saved root lacks an exact sign-changing bracket')
    linear, quadratic = factor[1:]
    if quadratic:
        discriminant = linear**2-4*quadratic*factor[0]
        if discriminant <= 0:
            raise ValueError('Ambiguous crossing topology')
        other_lower, other_upper = -linear/quadratic-upper, -linear/quadratic-lower
        if not (other_upper <= 0 or other_lower >= 1):
            raise ValueError('Additional or unresolved interior crossing')
    elif linear == 0:
        raise ValueError('Degenerate crossing polynomial')
    polarity = 1 if receiving else -1
    signs = [polarity*(point(cubic, parameter)[0]-anchor[0]) for parameter in (lower, upper)]
    if not (signs[0] < 0 < signs[1] if receiving else signs[0] > 0 > signs[1]):
        raise ValueError('Wrong directed excursion crossing')
    return lower, upper


def radius_bounds(cubic, anchor, lower, upper, receiving, tolerance=Fraction(1, 10**10), max_splits=4096):
    clipped = restrict(cubic, lower, upper)
    cells = [(clipped, lower, upper)]
    best = Fraction(0)
    witness = None
    polarity = 1 if receiving else -1
    for iteration in range(max_splits+1):
        upper_bounds = [max(squared_distance(control, anchor) for control in curve) for curve, _, _ in cells]
        for curve, start, end in cells:
            for parameter in (start, (start+end)/2, end):
                location = point(cubic, parameter)
                distance = squared_distance(location, anchor)
                if polarity*(location[0]-anchor[0]) > 0 and distance > best:
                    best, witness = distance, parameter
        maximum = max(upper_bounds)
        if maximum-best <= tolerance:
            return {'status': 'bounded', 'lower_squared': best, 'upper_squared': maximum,
                    'witness_parameter': witness, 'splits': iteration}
        if iteration == max_splits:
            return {'status': 'unresolved', 'lower_squared': best, 'upper_squared': maximum,
                    'witness_parameter': witness, 'splits': iteration}
        index = upper_bounds.index(maximum)
        curve, start, end = cells.pop(index)
        before, after = split(curve, Fraction(1, 2))
        middle = (start+end)/2
        cells.extend([(before, start, middle), (after, middle, end)])


def measure(cubic, check, receiving):
    cubic = exact_curve(cubic)
    anchor = cubic[-1] if receiving else cubic[0]
    bracket = crossing_bracket(cubic, check['recovery_parameter'], receiving)
    lower, upper = (bracket[0], Fraction(1)) if receiving else (Fraction(0), bracket[1])
    bound = radius_bounds(cubic, anchor, lower, upper, receiving)
    parameter = (Fraction(check['recovery_parameter'])+Fraction(check['stationary_parameter']))/2
    location = point(cubic, parameter)
    excursion = (1 if receiving else -1)*(location[0]-anchor[0])
    distance = squared_distance(location, anchor)
    violation = excursion > 0 and distance > RADIUS**2
    classification = 'proven_outside_disk' if violation or bound['lower_squared'] > RADIUS**2 else (
        'contained' if bound['upper_squared'] <= RADIUS**2 else 'unresolved')
    return {'status': classification, 'radius_limit_mm': float(RADIUS),
            'horizontal_limit_mm': float(HORIZONTAL), 'saved_horizontal_upper_mm': check['excursion_upper_mm'],
            'saved_locality_upper_mm': check['locality_upper_mm'],
            'crossing_bracket_exact': [str(value) for value in bracket],
            'covering_interval_exact': [str(lower), str(upper)],
            'supremum_distance_lower_mm': sqrt_bound(bound['lower_squared'], False),
            'supremum_distance_upper_mm': sqrt_bound(bound['upper_squared'], True),
            'bound_status': bound['status'], 'subdivisions': bound['splits'],
            'bound_squared_exact': [str(bound['lower_squared']), str(bound['upper_squared'])],
            'interior_witness': {'parameter_exact': str(parameter), 'parameter': float(parameter),
                'point_mm': [float(value) for value in location], 'horizontal_excursion_mm': float(excursion),
                'distance_lower_mm': sqrt_bound(distance, False), 'distance_squared_exact': str(distance),
                'strictly_inside_excursion': excursion > 0, 'proves_outside_disk': violation,
                'excess_over_radius_lower_mm': sqrt_bound(distance, False)-float(RADIUS)},
            'method': 'Exact-rational de Casteljau; certified full crossing bracket; convex-hull radius upper bounds and actual in-excursion point lower bounds. Decimal displays do not decide admission.'}


def run():
    OUTPUT.mkdir(exist_ok=False)
    report = {'version': VERSION, 'approval': approval(), 'status': 'stopped', 'measurements': [],
              'new_candidates': 0, 'images': 0, 'fitting': False, 'physical_runs': 0,
              'code_sha256': digest(Path(__file__)), 'tests_sha256': digest(ROOT/'tests/test_nu_excursion_locality.py')}
    started = time.monotonic()
    def expired(signum, frame):
        raise TimeoutError('300-second measurement ceiling')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        saved = verify()
        for entry in saved['candidates']:
            for piece in entry['candidate']['boundary']:
                key = piece['piece_id']+'_excursion'
                check = entry['evaluation']['checks'].get(key)
                if check and check['status'] == 'unresolved':
                    report['measurements'].append({'candidate': entry['brief'], 'piece': piece['piece_id'],
                        'candidate_sha256': entry['candidate_sha256'],
                        **measure(piece['cubics_mm'][0], check, piece['contact_profile'] == 'receiving')})
        verify()
        report['saved_inputs_unchanged_after'] = True
        report['status'] = 'measurement_complete'
    except (ValueError, OSError, TimeoutError) as error:
        report['error'] = str(error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        report['seconds'] = time.monotonic()-started
        payload = (json.dumps(report, indent=2, allow_nan=False)+'\n').encode()
        if len(payload) > 1024**2:
            raise ValueError('Measurement evidence size ceiling')
        with (OUTPUT/'report.json').open('xb') as stream:
            stream.write(payload)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--measure-approved-saved-spans', action='store_true', required=True)
    parser.parse_args()
    result = run()
    print(json.dumps({'status': result['status'], 'seconds': result['seconds'], 'error': result.get('error')}))
