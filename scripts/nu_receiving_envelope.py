"""One frozen-nu reinspection under the canonical-tangent receiving envelope."""

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import signal
import time

from scripts import nu_corner_geometry as original


actions = original.actions
source = original.source
bounds = original.bounds
ROOT = original.ROOT
BASE = original.BASE
OUTPUT = BASE/'receiving-envelope-review-001'
APPROVAL = BASE/'receiving-envelope-approval.json'
VERSION = 'nu-receiving-envelope-evaluation-v2'
REVISION = ROOT/'docs/tech-direction/TD-018-nu-receiving-envelope-revision.md'
SAVED = original.OUTPUT/'nu-candidate.json'
PINS = {
    REVISION: '9abc82e845aa7e07c3c62c52354614a84f53f2828fa44ad2c1c1eecca65b0457',
    SAVED: '7268952cd29fc7737c726838107e25f6bf0deeb4537992a8b415713150b0db97',
    original.OUTPUT/'report.json': '773ecfc7684284cf01354a18aed4a54a40354c8150c8a6c34ba91b883de27eaa',
    Path(original.__file__): '1d8042685f5854749876de4a8a213d004a64555ce90e00210d817645c29b9c0e',
    ROOT/'tests/test_nu_corner_geometry.py': 'e6fad3a4d144e31d7058fa2c67f15e1632fff65adc6f34af1194f521e1ba6193',
    Path(bounds.__file__): 'e9e31cff349a8caba796982d2c751a2571c3c7ae7544da936aa1f840e8cb66e7',
    Path(bounds.original.__file__): '1b8fa1266579ea06086af80f4300e4279eea8b098b76c8b93c49dbd90e95d303',
}
GUARD = 1e-9


def approval_record():
    return {'version': VERSION,
            'owner_quote': "Okay let's implement the revised checker and reinspect the saved nu candidate **without refitting**.",
            'pins': {str(path.relative_to(ROOT)): pin for path, pin in PINS.items()},
            'reinspections': 1, 'verification_seconds': 300, 'max_output_bytes': 10*1024**2,
            'minimum_free_bytes': 5*1024**3, 'retries': 0, 'geometry_generation': False,
            'fitting': False, 'physical_runs': 0, 'images': 0, 'mu_authorized': False}


def verify(approval):
    if approval != approval_record():
        raise ValueError('Exact receiving-envelope approval required')
    for path, pin in PINS.items():
        if actions.digest(path) != pin:
            raise ValueError(f'Frozen input changed: {path}')
    return original.verify(source.read_json(BASE/'geometry-approval.json'))


def receiving_check(cubic, incoming):
    result = {'status': 'unresolved'}
    try:
        if not all(math.isfinite(value) for point in cubic for value in point):
            raise ValueError('Nonfinite geometry')
        if not all(math.isfinite(value) for value in incoming) or incoming[1] >= 0:
            raise ValueError('Invalid receiving tangent')
        direction = original.capability.clearance.attachment.tangent(cubic, 1)
        if math.dist(direction, incoming) > 1e-8:
            raise ValueError('Receiving tangent mismatch')
        end = cubic[-1]
        delta = max(0, -.75*(3.5-end[1])/abs(incoming[1])*incoming[0])
        result.update(delta_mm=delta, cap_mm=.0045, cap_margin_mm=.0045-delta)
        if delta > .0045:
            raise ValueError('Receiving allowance exceeds unchanged cap')
        horizontal = bounds.power(cubic, 0)
        derivative = [horizontal[1], 2*horizontal[2], 3*horizontal[3]]
        crossing_polynomial = [horizontal[1]+horizontal[2]+horizontal[3],
                               horizontal[2]+horizontal[3], horizontal[3]]
        if sum(horizontal)-Fraction(end[0]) != 0:
            raise ValueError('Exact endpoint accounting failed')
        maxima = bounds.interior_roots(derivative)
        crossings = bounds.interior_roots(crossing_polynomial)
        result.update(stationary_intervals=[[root-1e-12, root+1e-12] for root in maxima],
                      crossing_intervals=[[root-1e-12, root+1e-12] for root in crossings],
                      endpoint_crossing_factored=True,
                      original_negative_endpoint_dx=float(sum(derivative)))
        if not (len(maxima) == len(crossings) == 1 and
                0 < crossings[0]-1e-12 < crossings[0]+1e-12 < maxima[0]-1e-12 < maxima[0]+1e-12 < 1):
            raise ValueError('Expected one crossing before one horizontal maximum')
        first, _ = bounds.original.derivatives(cubic)
        if not (derivative[0] > 0 > sum(derivative) and cubic[0][0] < end[0]
                and first[0][1] == 0 and first[1][1] < 0 and first[-1][1] < 0
                and all(end[1] <= point[1] <= 3.5 for point in cubic)):
            raise ValueError('Directed progress, nonzero derivative or vertical envelope failed')
        error = max(math.hypot(*vector) for vector in first)*1e-12+GUARD
        maximum = original.capability.clearance.attachment.point(cubic, maxima[0])[0]+error
        local = original.capability.clearance.restrict(cubic, crossings[0]-1e-12, 1)
        radius = max(math.dist(point, end) for point in local)+GUARD
        result.update(maximum_x_upper_mm=maximum, excursion_upper_mm=maximum-end[0],
                      envelope_margin_mm=end[0]+delta-maximum, locality_upper_mm=radius,
                      locality_limit_mm=.1125, locality_margin_mm=.1125-radius,
                      horizontal_signs=['positive', 'zero at maximum', 'negative through endpoint'],
                      method='Exact-rational quadratic coefficients, sign-certified root enclosures; endpoint factored; guarded restricted Bezier hull bounds entire overshoot interval')
        if delta < .0045-GUARD and maximum < end[0]+delta and radius < .1125:
            result['status'] = 'pass'
        else:
            result['reason'] = 'Envelope or locality bound not certified'
    except bounds.Unresolved as error:
        result['reason'] = str(error)
    except (ValueError, ZeroDivisionError) as error:
        result.update(status='fail', reason=str(error))
    return result


def inspect(document):
    if actions.object_digest(document) != actions.object_digest(source.read_json(SAVED)):
        raise ValueError('Saved geometry/body/action identity changed')
    if actions.digest(SAVED) != PINS[SAVED]:
        raise ValueError('Frozen candidate bytes changed')
    checks = original.geometry_checks(document)
    old_direction = checks.pop('S_rightward')
    checks['receiving_envelope_v2'] = receiving_check(document['boundary'][2]['cubics_mm'][0], document['incoming_tangent'])
    checks['frozen_identity'] = {'status': 'pass', 'candidate_sha256': PINS[SAVED],
                               'scope': 'All control points, retained bodies, sites, tangents, profiles and contact identities byte-pinned'}
    return checks, old_direction


def save_report(report):
    payload = (json.dumps(report, indent=2, allow_nan=False)+'\n').encode()
    if len(payload) > 10*1024**2-65536:
        raise ValueError('Output ceiling exceeded')
    with (OUTPUT/'report.json').open('xb') as handle:
        handle.write(payload)


def run():
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    report = {'version': VERSION, 'status': 'stopped', 'accepted': False,
              'structural_pass': False, 'revised_geometry_pass': False, 'not_started': ['mu', 'nominal', 'physical'],
              'geometry_generations': 0, 'raster_renders': 0, 'controller_executions': 0, 'fitting_evaluations': 0}
    def timeout_handler(signum, frame):
        raise TimeoutError('300-second reinspection ceiling')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    try:
        with source.evidence.read_only_guard():
            approval = source.read_json(APPROVAL)
            verify(approval)
            report.update(approval=approval, approval_sha256=actions.digest(APPROVAL),
                          code_sha256=actions.digest(Path(__file__)),
                          tests_sha256=actions.digest(ROOT/'tests/test_nu_receiving_envelope.py'))
            document = source.read_json(SAVED)
            checks, old_direction = inspect(document)
            report.update(checks=checks, original_S_rightward=old_direction)
            report['structural_pass'] = all(check['status'] == 'pass' for check in checks.values())
            checks['finite_contact_sweep'] = {'status': 'not_evaluated'}
            if report['structural_pass']:
                checks['finite_contact_sweep'] = original.contact_checks(document)
            report['revised_geometry_pass'] = all(check['status'] == 'pass' for check in checks.values())
            report['status'] = ('revised_geometry_pass_nominal_gated' if report['revised_geometry_pass'] else
                                'rejected' if any(check['status'] == 'fail' for check in checks.values()) else 'unresolved')
            for path, pin in PINS.items():
                if actions.digest(path) != pin:
                    raise ValueError(f'Frozen input changed during review: {path}')
            report['frozen_inputs_unchanged'] = True
    except Exception as error:
        report.update(status='stopped', revised_geometry_pass=False, error=f'{type(error).__name__}: {error}')
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report['elapsed_seconds'] = time.monotonic()-started
        save_report(report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run'])
    parser.parse_args()
    print(json.dumps(run(), indent=2))
