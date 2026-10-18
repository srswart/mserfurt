"""One approved local J1 receiving replacement; historical evidence stays frozen."""

import argparse
import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import signal
import subprocess
import time

from scripts import nu_excursion_locality as locality
from scripts import nu_merge_readiness as readiness
from scripts import nu_mutual_construction as prior
from scripts import nu_mutual_resume as nominal


VERSION = 'j1-receiving-local-tail-v1'
PROPOSAL = prior.ROOT/'docs/tech-direction/TD-018-j1-receiving-local-tail-proposal.md'
OUTPUT = prior.BASE/'j1-receiving-repair-001'
APPROVAL = prior.BASE/'j1-receiving-repair-approval.json'
J1_PIN = '772fce4a7a8cd8b4e56fb9067cc869ded7c0a4b1f779910e690c5c4c68092333'
LOCALITY_PIN = '2062941e17a92d01c8daa05d10408f1a901b0ba985d125d876a02f17cc9d0c48'
ADDITIONS = {'scripts/nu_excursion_locality.py', 'tests/test_nu_excursion_locality.py',
             'scripts/nu_j1_receiving_repair.py', 'tests/test_nu_j1_receiving_repair.py'}


def frozen_candidate():
    document = readiness.read(locality.SAVED)['candidates'][0]['candidate']
    if prior.actions.object_digest(document) != J1_PIN:
        raise ValueError('Frozen J1 object changed')
    return document


def controls(document):
    start, end = [document['ports_mm'][port] for port in ('K', 'C')]
    direction = document['directions']['C']
    length = .1125/2
    handle = length/3
    internal = [end[0], end[1]+length]
    reach, drop = end[0]-start[0], start[1]-internal[1]
    if reach <= 0 or drop <= 0:
        raise ValueError('Positive receiving reach and drop required')
    prefix = [start, [start[0]+2*reach/3, start[1]],
              [internal[0], internal[1]+.75*drop], internal]
    tail = [internal, [internal[0], internal[1]-handle],
            [end[axis]-handle*direction[axis] for axis in (0, 1)], end]
    return copy.deepcopy([prefix, tail])


def construct(saved):
    document = copy.deepcopy(saved)
    document['boundary'][-1]['cubics_mm'] = controls(saved)
    document['receiving_revision'] = {'version': VERSION, 'parent_sha256': J1_PIN,
                                     'internal_port': 'E', 'action_domain': 'aggregate-arclength-K-C'}
    return document


def validate(document, saved, model):
    prior.validate_identity(saved, model)
    if document.get('receiving_revision') != {
            'version': VERSION, 'parent_sha256': J1_PIN, 'internal_port': 'E',
            'action_domain': 'aggregate-arclength-K-C'}:
        raise ValueError('Receiving revision or action domain changed')
    if document['boundary'][-1]['cubics_mm'] != controls(saved):
        raise ValueError('Approved two-cubic receiving rule changed')
    protected = copy.deepcopy(document)
    del protected['receiving_revision']
    protected['boundary'][-1]['cubics_mm'] = saved['boundary'][-1]['cubics_mm']
    if protected != saved:
        raise ValueError('Protected geometry, ownership, action or source interval changed')


def context_program(model, text, enabled=False, candidate=None):
    from scribesim.evofit.stroke_gestures import compile_gestures
    if not enabled or text != 'nu':
        return compile_gestures(text, model)
    if candidate is None:
        raise ValueError('Explicit repaired candidate required')
    validate(candidate, frozen_candidate(), model)
    return copy.deepcopy(candidate)


def local_tail_check(curves, anchor):
    prefix, tail = [locality.exact_curve(curve) for curve in curves]
    center = list(map(Fraction, anchor))
    left = all(point[0] <= center[0] for point in prefix)
    radius_squared = max(locality.squared_distance(point, center) for point in tail)
    horizontal = max(point[0]-center[0] for point in tail)
    passed = left and radius_squared < Fraction(.1125)**2 and horizontal < Fraction(.0045)
    return {'status': 'pass' if passed else 'fail', 'prefix_left_of_C': left,
            'tail_radius_upper_mm': locality.sqrt_bound(radius_squared, True),
            'tail_horizontal_upper_mm': math.nextafter(float(horizontal), math.inf),
            'locality_limit_mm': .1125, 'horizontal_limit_mm': .0045,
            'domain': 'Whole prefix and whole tail; exact-rational control hulls'}


def join_check(before, after):
    position = math.dist(before[-1], after[0])
    tangent = math.dist(prior.clearance.attachment.tangent(before, 1),
                        prior.clearance.attachment.tangent(after, 0))
    return {'status': 'pass' if position <= 1e-9 and tangent <= 1e-8 else 'fail',
            'position_error_mm': position, 'unit_tangent_error': tangent}


def structural_checks(document, saved, model):
    validate(document, saved, model)
    checks = prior.structural_checks(saved, model)
    checks = {name: value for name, value in checks.items() if not name.startswith('K-C_')}
    checks['identity'] = {'status': 'pass', 'scope': 'Exact parent protection and approved receiving-only replacement'}
    curves = document['boundary'][-1]['cubics_mm']
    ports = document['ports_mm']
    rectangle = [[ports['K'][0], ports['C'][0]+.0045], [ports['C'][1], ports['K'][1]]]
    for label, cubic in zip(('K-E', 'E-C'), curves):
        checks[label+'_curvature'] = prior.bounds.original.curvature_check(cubic)
        checks[label+'_envelope'] = prior.envelope_check(cubic, rectangle)
    checks['receiving_locality'] = local_tail_check(curves, ports['C'])
    checks['receiving_aggregate_length'] = prior.length_check(curves)
    checks['E_join'] = join_check(*curves)
    checks['K_join'] = join_check(document['boundary'][-2]['cubics_mm'][-1], curves[0])
    retained = next(piece for piece in document['retained'] if piece['piece_id'] == '1:0')
    checks['C_join'] = join_check(curves[-1], retained['cubics_mm'][0])
    checks['protected_attachments'] = {
        'status': checks['C_join']['status'], 'departure': 'unchanged from validated parent',
        'receiving': checks['C_join']}
    return checks


def ramp_self_contact(curves, profile):
    length_lower = sum(prior.bounds.original.length_bounds(curve)[0] for curve in curves)
    if length_lower <= 0:
        return {'status': 'unresolved', 'reason': 'No positive aggregate length bound'}
    edge = [math.cos(math.radians(40)), -math.sin(math.radians(40))]
    normal = [-edge[1], edge[0]]
    certificates = []
    for axis in (edge, normal):
        common_sign = None
        for cubic in curves:
            first, _ = prior.bounds.original.derivatives(cubic)
            projections = [sum(component*weight for component, weight in zip(vector, axis)) for vector in first]
            minimum, maximum = prior.quadratic_range([
                projections[0], 2*(projections[1]-projections[0]),
                projections[0]-2*projections[1]+projections[2]])
            speed_upper = max(math.hypot(*vector) for vector in first)
            if minimum > prior.GUARD:
                sign, progress = 1, float(minimum)/speed_upper
            elif maximum < -prior.GUARD:
                sign, progress = -1, -float(maximum)/speed_upper
            else:
                return {'status': 'unresolved', 'reason': 'Whole-ramp footprint monotonicity not certified',
                        'axis': axis, 'projection_range': [float(minimum), float(maximum)]}
            if common_sign is not None and sign != common_sign:
                return {'status': 'unresolved', 'reason': 'Cross-cubic footprint reversal'}
            common_sign = sign
            adverse = .405/length_lower if axis == edge and (
                (profile == 'departure' and sign > 0) or (profile == 'receiving' and sign < 0)) else 0.
            if progress <= adverse+prior.GUARD:
                return {'status': 'unresolved', 'reason': 'Active-edge boundary progress not certified'}
            certificates.append({'sign': sign, 'progress_lower': progress, 'adverse_rate_upper': adverse})
    if any(join_check(before, after)['status'] != 'pass' for before, after in zip(curves, curves[1:])):
        return {'status': 'unresolved', 'reason': 'Discontinuous ramp join'}
    return {'status': 'pass', 'certificates': certificates, 'aggregate_length_lower_mm': length_lower,
            'scope': 'Whole ramp including cross-cubic pairs; no E exemption',
            'proof': 'Continuous footprint boundaries share strict monotonicity on both nib axes across every cubic. Point membership is one interval; aggregate arc length bounds the moving edge rate.'}


def contacts(document):
    groups = [{'name': profile, 'profile': profile,
               'curves': [curve for piece in document['boundary'] if piece['contact_profile'] == profile
                          for curve in piece['cubics_mm']]}
              for profile in ('departure', 'core', 'receiving')]
    permissions = {('departure', '0:3'): 'A', ('receiving', '1:0'): 'C',
                   ('departure', 'core'): 'F', ('core', 'receiving'): 'K'}
    others = [{'name': piece['piece_id'], 'profile': 'full', 'curves': piece['cubics_mm']}
              for piece in document['retained']]
    ramps = {group['name']: ramp_self_contact(group['curves'], group['profile'])
             for group in groups if group['profile'] != 'core'}
    pairs = []
    for index, group in enumerate(groups):
        for other in others+groups[index+1:]:
            port = permissions.get((group['name'], other['name']))
            join = document['ports_mm'][port] if port else None
            results = [prior.original.contact_pair(first, group['profile'], second, other['profile'], join)
                       for first in group['curves'] for second in other['curves']]
            pairs.append({'owners': [group['name'], other['name']], 'splice_port': port,
                          'cubic_pairs': len(results), 'status': 'pass' if all(results) else 'unresolved'})
    return {'status': 'pass' if all(check['status'] == 'pass' for check in list(ramps.values())+pairs) else 'unresolved',
            'ramp_self_contact': ramps, 'pairs': pairs,
            'method': 'Whole aggregate self-contact; all external cubic pairs use conservative full-nib ramp supersets'}


def inspect(document, saved, model):
    checks = structural_checks(document, saved, model)
    checks['external_and_ramp_contact'] = contacts(document) if all(
        check['status'] == 'pass' for check in checks.values()) else {
            'status': 'not_run', 'reason': 'Structural admission incomplete'}
    status = 'admitted' if all(check['status'] == 'pass' for check in checks.values()) else (
        'rejected' if any(check['status'] == 'fail' for check in checks.values()) else 'unresolved')
    return {'status': status, 'render_eligible': status == 'admitted', 'checks': checks}


def authority_record():
    return {'version': VERSION, 'owner_quote': "Okay let's proceed with implementation.",
            'proposal_sha256': readiness.digest(PROPOSAL), 'parent_sha256': J1_PIN,
            'candidate_limit': 1, 'automatic_retries': 0, 'check_seconds': 300, 'render_seconds': 300,
            'max_output_bytes': 25*1024**2, 'minimum_free_bytes': 5*1024**3,
            'fitting': False, 'physical_runs': 0, 'mu': False, 'nib_rotation': False,
            'dependencies': readiness.dependencies()}


def verify():
    if readiness.read(APPROVAL) != authority_record():
        raise ValueError('Exact new authority and source snapshot required')
    locality.verify()
    if readiness.digest(locality.OUTPUT/'report.json') != LOCALITY_PIN:
        raise ValueError('Historical locality evidence changed')
    ready = readiness.read(readiness.OUTPUT/'report.json')
    if set(readiness.dependencies())-set(ready['dependencies']) != ADDITIONS:
        raise ValueError('Unexpected source additions outside isolated adapter and prior diagnostic')
    readiness.verify_authority()
    return ready


def write(name, value, replace=False):
    payload = value if isinstance(value, bytes) else value.encode()
    destination = OUTPUT/name
    total = sum(path.stat().st_size for path in OUTPUT.iterdir() if path.is_file() and path != destination)
    if total+len(payload) > 25*1024**2-65536:
        raise ValueError('New evidence budget exceeded')
    if replace:
        temporary = OUTPUT/'.report.tmp'
        with temporary.open('xb') as stream:
            stream.write(payload)
        temporary.replace(destination)
    else:
        with destination.open('xb') as stream:
            stream.write(payload)


def save(report):
    write('report.json', json.dumps(report, indent=2, allow_nan=False)+'\n', replace=True)


def status_page(report):
    page = prior.status_page(report).replace('Reciprocal nu: J1 / J2', 'J1-R1 receiving repair')
    if report['new_candidates']:
        page = page.replace('No study candidate was constructed.', 'The constructed candidate is preserved in report.json.')
    if report.get('renders'):
        page = page.replace('This is a technical status board, not a visual comparison or owner acceptance.',
                            'Nominal review only; owner preference and physical acceptance remain open.')
    return page


def render(report):
    entry = report['candidates'][0]
    if entry['status'] != 'admitted':
        write('index.html', status_page(report))
        return
    renderer = prior.history.renderer
    document = entry['candidate']
    if prior.actions.object_digest(document) != entry['candidate_sha256']:
        raise ValueError('Candidate changed before nominal rendering')
    model = prior.source.read_json(prior.source.CANDIDATE)
    canonical, _ = renderer.drawings(prior.source.read_json(prior.frozen.SAVED), model)
    drawing = nominal.candidate_drawing(document)
    frame = renderer.frame([canonical, drawing])
    receiving = [{'profile': 'receiving', 'polygons': renderer.polygons(
        document['boundary'][-1]['cubics_mm'], 'receiving', document['profiles'])}]
    boards = {
        'comparison': ([{'label': 'Canonical — unconnected', 'drawing': canonical},
                        {'label': 'Frozen J1', 'status': 'proven locality failure'},
                        {'label': 'J1-R1 — nominal geometry, owner review required', 'drawing': drawing}], frame),
        'overlays': ([{'label': 'Faint canonical / repaired stroke colors', 'drawing': drawing,
                      'ghost': canonical, 'colored': True}], frame),
        'receiving-detail': ([{'label': 'K→E→C — one receiving action, enlarged',
                              'drawing': receiving, 'colored': True}], renderer.frame([receiving]))}
    converter = shutil.which('rsvg-convert')
    if not converter:
        raise ValueError('PNG converter unavailable')
    for name, (rows, bounds) in boards.items():
        write(name+'.svg', nominal.svg_board(rows, bounds))
        result = subprocess.run([converter, str(OUTPUT/(name+'.svg'))], capture_output=True, check=True, timeout=300)
        write(name+'.png', result.stdout)
        report['renders'] += 1
    write('index.html', status_page(report).replace('</html>', ''.join(
        f'<h2>{name}</h2><img style="width:100%" src="{name}.svg" alt="{name}">' for name in boards)+'</html>'))


def run():
    ready = verify()
    if shutil.disk_usage(prior.BASE).free < 5*1024**3:
        raise ValueError('At least 5GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    report = {'version': VERSION, 'status': 'stopped', 'candidates': [], 'new_candidates': 0,
              'renders': 0, 'fitting_evaluations': 0, 'physical_runs': 0, 'mu_started': False,
              'automatic_retries': 0, 'approval_sha256': readiness.digest(APPROVAL)}
    def timeout_handler(signum, frame):
        raise TimeoutError('Approved phase budget exhausted')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        save(report)
        runtime = readiness.invoke_worker(prior.ROOT, False)
        if runtime['canonical_compiled_sha256'] != ready['historical']['canonical_compiled_sha256']:
            raise ValueError('Current canonical differs from historical evidence')
        model = prior.source.read_json(prior.source.CANDIDATE)
        fingerprints = {text: prior.actions.object_digest(context_program(model, text)) for text in ('n', 'u', 'nu')}
        if fingerprints != runtime['canonical_compiled_sha256']:
            raise ValueError('Context-off output changed')
        report['readiness'] = {'status': 'pass', 'runtime': runtime, 'context_off_sha256': fingerprints,
                               'historical_receipt_sha256': locality.READY_PIN, 'dependencies': readiness.dependencies()}
        verify()
        saved = frozen_candidate()
        candidate = construct(saved)
        entry = {'brief': 'J1-R1', 'status': 'constructed', 'candidate': candidate,
                 'candidate_sha256': prior.actions.object_digest(candidate)}
        report['candidates'].append(entry)
        report['new_candidates'] = 1
        save(report)
        evaluation = inspect(candidate, saved, model)
        entry.update(status=evaluation['status'], evaluation=evaluation)
        verify()
        report['status'] = 'geometry_checked' if evaluation['render_eligible'] else 'no_candidate_admitted'
    except (ValueError, OSError, TimeoutError, subprocess.SubprocessError, prior.bounds.Unresolved) as error:
        report.update(status='stopped', error=str(error))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        report['construction_check_seconds'] = time.monotonic()-started
        save(report)
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        if report['status'] in ('geometry_checked', 'no_candidate_admitted'):
            render(report)
            if report['status'] == 'geometry_checked':
                report['status'] = 'nominal_review_ready'
        else:
            write('index.html', status_page(report))
        verify()
    except (ValueError, OSError, TimeoutError, subprocess.SubprocessError) as error:
        report.update(status='stopped', error=str(error))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        report['render_seconds'] = time.monotonic()-started
        report['artifacts'] = {path.name: readiness.digest(path) for path in OUTPUT.iterdir() if path.name != 'report.json'}
        save(report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-approval', action='store_true')
    options = parser.parse_args()
    if options.record_approval:
        readiness.save_new(APPROVAL, authority_record())
    else:
        result = run()
        print(json.dumps({'status': result['status'], 'new_candidates': result['new_candidates'],
                          'renders': result['renders'], 'error': result.get('error')}))
