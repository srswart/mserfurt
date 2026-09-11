"""Bounded necessary-condition audit; never constructs a contextual candidate."""

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import signal
import time

from scripts import nu_receiving_envelope as frozen


actions = frozen.actions
source = frozen.source
ROOT = frozen.ROOT
BASE = frozen.BASE.parent/'nu-contextual-entry-v1'
OUTPUT = BASE/'port-audit-001'
PROPOSAL = ROOT/'docs/tech-direction/TD-018-contextual-entry-feasibility-proposal.md'
PINS = {
    PROPOSAL: 'f2c7ee6343ba4ffe9286936a8233058f4ba6c0856113ceaf2c91b9f4cdc39351',
    ROOT/'docs/tech-direction/TD-018-contextual-u-entry-audit.md': 'f86601c164429ae1b7022b281c7303d9ed2da6b4129e0839e7e9b4427e12b377',
    source.CANDIDATE: '01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd',
    frozen.OUTPUT/'report.json': '053aff33d2b767c622ea63614fd4727a394c1c6bce365740d007915c7e163b8f',
}
VERSION = 'nu-entry-port-audit-v1'
INVENTORY = ('lower-return', 'rise', 'upper-return')


def approval_record():
    return {'version': VERSION,
            'owner_quote': "Okay execution of CURRICULUM-016 is approved.  Let's go.",
            'scope': 'One nu-only read-only port/envelope audit; no geometry, rendering, fitting or mu',
            'proposal_sha256': PINS[PROPOSAL], 'seconds': 300, 'max_output_bytes': 10*1024**2,
            'minimum_free_bytes': 5*1024**3, 'retries': 0}


def verify(approval):
    if approval != approval_record():
        raise ValueError('Exact bounded audit approval required')
    for path, pin in PINS.items():
        if actions.digest(path) != pin:
            raise ValueError(f'Frozen audit input changed: {path}')
    report = source.read_json(frozen.OUTPUT/'report.json')
    if actions.digest(Path(frozen.__file__)) != report['code_sha256']:
        raise ValueError('Frozen receiving checker changed')
    if actions.digest(ROOT/'tests/test_nu_receiving_envelope.py') != report['tests_sha256']:
        raise ValueError('Frozen receiving tests changed')
    frozen.verify(source.read_json(frozen.APPROVAL))


def angle(vector):
    if len(vector) != 2 or not all(math.isfinite(value) for value in vector) or math.hypot(*vector) <= 1e-12:
        raise ValueError('Nonzero finite directed port required')
    return math.degrees(math.atan2(vector[1], vector[0]))


def difference(first, second):
    return (first-second+180)%360-180


def placement(scale, rotation, kind='similarity'):
    if kind != 'similarity' or not math.isfinite(scale) or not math.isfinite(rotation) or not .5 <= scale <= 1.5 or not -20 <= rotation <= 20:
        raise ValueError('Outside positive uniform similarity family')


def evaluate(coefficients, parameter):
    value = Fraction(0)
    for coefficient in reversed(coefficients):
        value = value*Fraction(parameter)+coefficient
    return float(value)


def extrema(coefficients):
    roots = frozen.bounds.interior_roots([coefficients[1], 2*coefficients[2], 3*coefficients[3]])
    probes = [0.0, *roots, 1.0]
    derivative_bound = sum(abs(float(index*coefficient)) for index, coefficient in enumerate(coefficients))
    guard = derivative_bound*1e-12+1e-9
    values = [evaluate(coefficients, parameter) for parameter in probes]
    return {'root_intervals': [[root-1e-12, root+1e-12] for root in roots],
            'values_at_probes': values, 'parameters': probes,
            'minimum_lower': min(values)-guard, 'maximum_upper': max(values)+guard,
            'numeric_guard': guard}


def projected_power(cubic, axis, rotation):
    horizontal = frozen.bounds.power(cubic, 0)
    vertical = frozen.bounds.power(cubic, 1)
    cosine, sine = math.cos(math.radians(rotation)), math.sin(math.radians(rotation))
    weights = (cosine, -sine) if axis == 0 else (sine, cosine)
    return [Fraction(3.5)*(Fraction(weights[0])*before+Fraction(weights[1])*after)
            for before, after in zip(horizontal, vertical)]


def validate_contract(document, canonical, contracts):
    if document != source.read_json(frozen.SAVED):
        raise ValueError('Frozen source coverage/body identity changed')
    manifest = contracts['nu']
    if document['profiles'] != manifest['profiles']:
        raise ValueError('Contact phase coverage changed')
    if canonical['gestures']['overturn']['strokes'][0]['primitive'] != 'rise':
        raise ValueError('Primitive lineage changed')
    retained = [{key: value for key, value in piece.items() if key != 'cubics_mm'} for piece in document['retained']]
    if retained != manifest['retained'] or len({piece['piece_id'] for piece in retained}) != len(retained):
        raise ValueError('Duplicate or changed source coverage')
    return {'status': 'necessary_conditions_pass', 'canonical_model_sha256': PINS[source.CANDIDATE],
            'retained_source_intervals': [{'owner': piece['canonical_owner']['occurrence_id'], 'interval': piece['source_interval']} for piece in retained],
            'replaced_source_intervals': [{'owner': piece['source_owner'], 'interval': piece['removed_interval']} for piece in manifest['boundary_slots'] if piece['removed_interval']],
            'action_partition': 'A-B full to corner; B-D constant negative10%; D-C corner to full',
            'semantic_partition': 'departure crosses B to P; rise P-Q; crown crosses D; descent to C',
            'length_partition': ['A-B', 'B-D', 'D-C']}


def require_partition(core_profile, length_partition, primitive_names):
    if core_profile != actions.PROFILES['core'] or length_partition != ['A-B', 'B-D', 'D-C']:
        raise ValueError('Contact or aggregate length partition changed')
    if primitive_names != list(INVENTORY):
        raise ValueError('Relabeled bridge is not primitive derivation')


def analyze(canonical, document, contracts):
    identity = validate_contract(document, canonical, contracts)
    require_partition(document['profiles']['core'], identity['length_partition'], list(INVENTORY))
    primitives = canonical['primitives']
    inventory = {}
    for name in INVENTORY:
        primitive = primitives[name]
        cubic = primitive['cubics'][0]
        coefficients = [Fraction(3.5)*value for value in frozen.bounds.power(cubic, 1)]
        inventory[name] = {'primitive_sha256': actions.object_digest(primitive),
                           'entry_tangent': primitive['entry'], 'exit_tangent': primitive['exit'],
                           'displacement_mm': [(cubic[-1][axis]-cubic[0][axis])*3.5 for axis in (0, 1)],
                           'y_extrema': extrema(coefficients)}
    outgoing = document['outgoing_tangent']
    rotation = difference(angle(outgoing), angle(primitives['lower-return']['entry']))
    placement(1, rotation)
    joins = []
    for before, after in zip(INVENTORY, INVENTORY[1:]):
        error = math.dist(primitives[before]['exit'], primitives[after]['entry'])
        if error > 1e-8:
            raise ValueError('Unmatched source tangent directions')
        joins.append({'from': before, 'to': after, 'unit_tangent_error': error,
                      'consequence': 'Matching directions force the same rotation on neighboring full primitives'})
    rise_entry_angle = angle(primitives['rise']['entry'])
    rise_exit_angle = angle(primitives['rise']['exit'])
    lower_rotation = max(-20, -rise_entry_angle, -rise_exit_angle)
    upper_rotation = min(20, 90-rise_entry_angle, 90-rise_exit_angle)
    port_result = {'status': 'necessary_conditions_pass' if lower_rotation < rotation < upper_rotation else 'incompatible',
                   'rotation_interval_deg': [lower_rotation, upper_rotation], 'quadrant_boundaries_open': True,
                   'forced_rotation_deg': rotation,
                   'P_angle_deg': rise_entry_angle+rotation, 'Q_angle_deg': rise_exit_angle+rotation,
                   'unrotated_rise_entry_incompatible': primitives['rise']['entry'][0] < 0,
                   'meaning': 'Positive x/y endpoint directions only, not selected P/Q coordinates or full-curve admission'}
    cubic = primitives['lower-return']['cubics'][0]
    vertical = projected_power(cubic, 1, rotation)
    horizontal = projected_power(cubic, 0, rotation)
    vertical_info = extrema(vertical)
    if len(vertical_info['root_intervals']) != 1:
        raise frozen.bounds.Unresolved('Expected one departure minimum')
    root = sum(vertical_info['root_intervals'][0])/2
    drop = evaluate(vertical, 0)-evaluate(vertical, root)
    horizontal_travel = evaluate(horizontal, root)-evaluate(horizontal, 0)
    if drop <= 1e-6:
        raise frozen.bounds.Unresolved('Departure projection numerically ill-conditioned')
    height = document['anchors_mm']['A'][1]
    required_scale = height/drop
    required_travel = document['anchors_mm']['B'][0]-document['anchors_mm']['A'][0]
    residual = required_scale*horizontal_travel-required_travel
    residual_guard = 1e-7
    if not math.isfinite(required_scale):
        raise frozen.bounds.Unresolved('Departure projection numerically ill-conditioned')
    departure = {'status': 'incompatible' if abs(residual) > residual_guard else 'unresolved',
                 'forced_rotation_deg': rotation, 'minimum_parameter_interval': vertical_info['root_intervals'][0],
                 'projected_y_extrema': vertical_info, 'unit_scale_drop_mm': drop,
                 'baseline_required_scale': required_scale, 'scale_in_family': .5 <= required_scale <= 1.5,
                 'baseline_required_horizontal_travel_mm': required_travel,
                 'projected_horizontal_travel_at_baseline_mm': required_scale*horizontal_travel,
                 'horizontal_residual_mm': residual, 'residual_guard_mm': residual_guard,
                 'reason': 'A tangent fixes rotation; B baseline fixes scale; remaining horizontal displacement must also match B',
                 'scope': 'Full lower-return only; no candidate curve or new point generated'}
    if not departure['scale_in_family']:
        departure['status'] = 'incompatible'
    crown_angle = angle(primitives['upper-return']['exit'])+rotation
    direct_error = difference(crown_angle, angle(document['incoming_tangent']))
    source_rows = frozen.original.capability.investigation.canonical(canonical, 'nu')['strokes']
    receiver = next(row for row in source_rows if row['occurrence_id'] == '1:0')
    receiver_start = frozen.original.capability.clearance.attachment.tangent(receiver['cubics'][0], 0)
    prefix_error = difference(crown_angle, angle(receiver_start))
    receiver_checks = {'direct_crown_to_C': {'status': 'incompatible' if abs(direct_error) > 1e-5 else 'unresolved', 'angle_error_deg': direct_error},
                       'crown_to_unchanged_canonical_prefix': {'status': 'incompatible' if abs(prefix_error) > 1e-5 else 'unresolved', 'angle_error_deg': prefix_error},
                       'scope': 'Necessary tangent checks only; a derived descent is not covered by these rejections'}
    return {'status': 'incompatible' if departure['status'] == 'incompatible' else 'unresolved',
            'scope': 'Exact full-primitive reuse in the approved similarity family, fixed A/B/D/C',
            'identity': identity, 'inventory': inventory, 'source_join_constraints': joins,
            'entry_port_domains': port_result, 'departure_baseline_constraint': departure,
            'independent_receiving_port_constraints': receiver_checks,
            'adaptation_requirements': [
                'Full lower-return similarity cannot be assumed: retain A/B and derive departure handles or separately propose a source cut. No handle length selected.',
                'Unrotated rise entry is leftward; a compatible common rotation can address endpoint sign only. It does not prove displacement/envelope/curvature fit.',
                'Crown exit needs direction adaptation or a derived descent to fixed C; exact canonical prefix and direct crown joins remain separate rejected cases.',
                'Changing only the lower-return entry handle cannot prove simultaneous B location and P tangent; complete derived-shape proof is required.'],
            'not_evaluated': ['adapted coordinates', 'adapted curvature', 'whole adapted envelope', 'adapted finite contact sweep', 'visual naturalness', 'physical execution'],
            'next': 'Review contradictions before a separate deterministic derivation proposal; do not enlarge the family or retry'}


def run():
    if shutil.disk_usage(BASE.parent).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = {'version': VERSION, 'status': 'stopped', 'new_geometries': 0, 'renders': 0,
              'physical_runs': 0, 'fitting_evaluations': 0, 'mu_started': False}
    def timeout_handler(signum, frame):
        raise TimeoutError('300-second audit ceiling')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    try:
        with source.evidence.read_only_guard():
            approval = source.read_json(BASE/'approval.json')
            verify(approval)
            report.update(approval=approval, code_sha256=actions.digest(Path(__file__)),
                          tests_sha256=actions.digest(ROOT/'tests/test_nu_entry_port_audit.py'),
                          input_pins={str(path.relative_to(ROOT)): pin for path, pin in {**frozen.PINS, **PINS}.items()},
                          family={'scale': [.5, 1.5], 'rotation_deg': [-20, 20], 'reflection': False, 'shear': False, 'inventory': list(INVENTORY)})
            result = analyze(source.read_json(source.CANDIDATE), source.read_json(frozen.SAVED),
                             source.read_json(frozen.original.actions.OUTPUT/'contracts.json'))
            report.update(status=result['status'], analysis=result)
            for path, pin in {**frozen.PINS, **PINS}.items():
                if actions.digest(path) != pin:
                    raise ValueError('Frozen evidence changed during audit')
            report['frozen_inputs_unchanged'] = True
    except frozen.bounds.Unresolved as error:
        report.update(status='unresolved', error=str(error))
    except Exception as error:
        report.update(status='stopped', error=f'{type(error).__name__}: {error}')
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report['elapsed_seconds'] = time.monotonic()-started
        payload = (json.dumps(report, indent=2, allow_nan=False)+'\n').encode()
        if len(payload) > 10*1024**2:
            raise ValueError('Audit output ceiling')
        with (OUTPUT/'report.json').open('xb') as stream:
            stream.write(payload)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run'])
    parser.parse_args()
    print(json.dumps(run(), indent=2))
