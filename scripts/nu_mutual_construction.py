"""One approved reciprocal nu shape batch; no fitting or physical execution."""

import argparse
import copy
from fractions import Fraction
import html
import json
import math
from pathlib import Path
import shutil
import signal
import time

from scripts import nu_three_way_review as history


frozen = history.gate.previous.frozen
original = frozen.original
actions = frozen.actions
source = frozen.source
bounds = frozen.bounds
clearance = original.capability.clearance
ROOT = frozen.ROOT
BASE = history.BASE.parent/'nu-mutual-construction-v1'
OUTPUT = BASE/'batch-001'
APPROVAL = BASE/'approval.json'
BRIEF = ROOT/'docs/tech-direction/TD-018-mutual-nu-construction-briefs.md'
BRIEF_PIN = 'a4d0d564d4123bcc49e5fc070cfb827d5d6f86795a76405d5f939d9badd72eed'
CANONICAL_PIN = '01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd'
VERSION = 'nu-mutual-construction-v1'
HEIGHT = 3.5
GUARD = 1e-9
MAX_BYTES = 25*1024**2
SPECS = {
    'J1': {'source_cuts': {'0:3': '0.7648068784772746', '1:0': '0.35'},
           'foot_extension': .08, 'rise_offset': .16, 'rise_height': .45,
           'upright_top': .88, 'crown_offset': .08, 'crown_height': 1.,
           'rise_direction': [0., 1.]},
    'J2': {'source_cuts': {'0:3': '0.65', '1:0': '0.45'},
           'foot_extension': .12, 'rise_offset': .22, 'rise_height': .62,
           'upright_top': None, 'crown_offset': .10, 'crown_height': 1.02,
           'rise_direction': [.4, math.sqrt(.84)]},
}


def approval_record():
    return {'version': VERSION, 'owner_quote': 'Yes approved and proceed.',
            'brief_sha256': BRIEF_PIN, 'canonical_sha256': CANONICAL_PIN,
            'approved_briefs': ['J1', 'J2'], 'numeric_regions_and_ports': True,
            'new_splice_centers_and_window_local_turn_guard': True,
            'action_and_aggregate_length_partition': True,
            'construction_check_seconds': 300, 'render_seconds': 300,
            'candidate_limit': 2, 'batches': 1, 'retries': 0,
            'max_output_bytes': MAX_BYTES, 'minimum_free_bytes': 5*1024**3,
            'fitting': False, 'physical_runs': 0, 'mu': False, 'nib_rotation': False}


def verify():
    if source.read_json(APPROVAL) != approval_record():
        raise ValueError('Exact F2 approval required')
    if actions.digest(BRIEF) != BRIEF_PIN or actions.digest(source.CANDIDATE) != CANONICAL_PIN:
        raise ValueError('Approved brief or canonical bytes changed')
    history.verify()


def canonical(model, text):
    return original.capability.investigation.canonical(model, text)


def vector_curve(start, end, incoming, outgoing):
    if not all(math.isfinite(value) for vector in (start, end, incoming, outgoing) for value in vector):
        raise ValueError('Finite ports required')
    if any(abs(math.hypot(*direction)-1) > 1e-8 for direction in (incoming, outgoing)):
        raise ValueError('Unit directed ports required')
    handle = math.dist(start, end)/3
    if handle <= 0:
        raise ValueError('Nonzero chord required')
    return [start, [start[axis]+handle*incoming[axis] for axis in (0, 1)],
            [end[axis]-handle*outgoing[axis] for axis in (0, 1)], end]


def terminal_curve(start, end, direction, receiving=False):
    reach, drop = end[0]-start[0], start[1]-end[1]
    if reach <= 0 or drop <= 0 or direction[1] >= 0:
        raise ValueError('Forward/downward terminal ports required')
    if receiving:
        handle = .75*drop/abs(direction[1])
        return [start, [start[0]+2*reach/3, start[1]],
                [end[axis]-handle*direction[axis] for axis in (0, 1)], end]
    handle = .9*drop/abs(direction[1])
    return [start, [start[axis]+handle*direction[axis] for axis in (0, 1)],
            [end[0]-2*reach/3, end[1]], end]


def retained_pieces(program, spec):
    result = []
    for row in program['strokes']:
        owner = row['occurrence_id']
        interval = ['0', spec['source_cuts'][owner]] if owner == '0:3' else (
            [spec['source_cuts'][owner], '1'] if owner == '1:0' else ['0', '1'])
        cubics = copy.deepcopy(row['cubics'])
        if interval != ['0', '1']:
            if len(cubics) != 1:
                raise ValueError('Single cubic source required at editable occurrences')
            cubics[0] = clearance.restrict(cubics[0], *map(float, interval))
        result.append({'piece_id': owner, 'canonical_owner': copy.deepcopy(row),
                       'source_interval': interval, 'contact_profile': 'full',
                       'cubics_mm': [[[value*HEIGHT for value in point] for point in cubic] for cubic in cubics]})
    return result


def construct(model, name):
    spec = copy.deepcopy(SPECS[name])
    program = canonical(model, 'nu')
    indexed = {row['occurrence_id']: row for row in program['strokes']}
    departure, receiving = [indexed[owner]['cubics'][0] for owner in ('0:3', '1:0')]
    cut_start, cut_end = [float(spec['source_cuts'][owner]) for owner in ('0:3', '1:0')]
    foot_x, stem_x = departure[-1][0], receiving[0][0]
    ports = {
        'A': clearance.attachment.point(departure, cut_start),
        'F': [foot_x+spec['foot_extension'], 0.],
        'P': [stem_x-spec['rise_offset'], spec['rise_height']],
        'K': [stem_x-spec['crown_offset'], spec['crown_height']],
        'C': clearance.attachment.point(receiving, cut_end),
    }
    directions = {'A': clearance.attachment.tangent(departure, cut_start),
                  'F': [1., 0.], 'P': spec['rise_direction'], 'K': [1., 0.],
                  'C': clearance.attachment.tangent(receiving, cut_end)}
    order = ['A', 'F', 'P', 'K', 'C']
    if name == 'J1':
        ports['Q'] = [stem_x-spec['rise_offset'], spec['upright_top']]
        directions['Q'] = [0., 1.]
        order.insert(3, 'Q')
    ports = {key: [value*HEIGHT for value in point] for key, point in ports.items()}
    pieces = []
    for start, end in zip(order, order[1:]):
        profile = 'departure' if start == 'A' else 'receiving' if end == 'C' else 'core'
        curve = terminal_curve(ports[start], ports[end], directions['A']) if profile == 'departure' else (
            terminal_curve(ports[start], ports[end], directions['C'], True) if profile == 'receiving' else
            vector_curve(ports[start], ports[end], directions[start], directions[end]))
        owner = 'n' if start in ('A', 'F') else 'u'
        source_span = {'occurrence_id': '0:3', 'interval': [spec['source_cuts']['0:3'], '1']} if start == 'A' else (
            {'occurrence_id': '1:0', 'interval': ['0', spec['source_cuts']['1:0']]} if end == 'C' else None)
        pieces.append({'piece_id': start+'-'+end, 'ports': [start, end],
                       'contact_profile': profile, 'cubics_mm': [curve],
                       'owner': owner, 'contributors': ['n', 'u'], 'contact': 'pen-down',
                       'replacement_source_span': source_span,
                       'added_entry_travel': source_span is None})
    return {'version': VERSION, 'brief': name, 'fixture': 'nu', 'spec': spec,
            'canonical_sha256': actions.object_digest(model), 'coordinate_frame': 'physical-mm-y-up',
            'rule': 'terminal-0.9-receiving-0.75-middle-chord-thirds-v1',
            'ports_mm': ports, 'directions': directions, 'port_order': order,
            'retained': retained_pieces(program, spec), 'boundary': pieces,
            'profiles': copy.deepcopy(actions.PROFILES), 'nib_angle_deg_physical_y_down': 40.,
            'nib_dimensions_mm': [.45, .02], 'pressure': .5, 'speed_cap_mm_s': 12.,
            'spacing': {'canonical_origin_separation_H': 1.3+.15,
                        'stem_minus_foot_mm': HEIGHT*(stem_x-foot_x),
                        'thin_span_horizontal_mm': ports['K'][0]-ports['F'][0]},
            'fitting': False, 'physical_acceptance': False}


def context_program(model, text, enabled=False, candidate=None):
    if not enabled or text != 'nu':
        return canonical(model, text)
    if candidate is None:
        raise ValueError('Explicit saved pair program required; no implicit construction')
    validate_identity(candidate, model)
    return copy.deepcopy(candidate)


def validate_identity(document, model):
    if document['version'] != VERSION or document['spec'] != SPECS[document['brief']]:
        raise ValueError('Brief/version identity changed')
    if (document['profiles'] != actions.PROFILES or document['fixture'] != 'nu'
            or document['canonical_sha256'] != actions.object_digest(model)
            or document['nib_angle_deg_physical_y_down'] != 40.
            or document['nib_dimensions_mm'] != [.45, .02] or document['pressure'] != .5
            or document['speed_cap_mm_s'] != 12. or document['fitting']
            or document['physical_acceptance']):
        raise ValueError('Frozen model or action identity changed')
    expected = retained_pieces(canonical(model, 'nu'), document['spec'])
    if document['retained'] != expected:
        raise ValueError('Protected body/action/source interval identity changed')
    indexed = {piece['piece_id']: piece['canonical_owner'] for piece in expected}
    departure, receiving = [indexed[owner]['cubics'][0] for owner in ('0:3', '1:0')]
    spec = document['spec']
    cut_start, cut_end = [float(spec['source_cuts'][owner]) for owner in ('0:3', '1:0')]
    expected_ports = {
        'A': clearance.attachment.point(departure, cut_start),
        'F': [departure[-1][0]+spec['foot_extension'], 0.],
        'P': [receiving[0][0]-spec['rise_offset'], spec['rise_height']],
        'K': [receiving[0][0]-spec['crown_offset'], spec['crown_height']],
        'C': clearance.attachment.point(receiving, cut_end),
    }
    expected_directions = {'A': clearance.attachment.tangent(departure, cut_start),
                           'F': [1., 0.], 'P': spec['rise_direction'], 'K': [1., 0.],
                           'C': clearance.attachment.tangent(receiving, cut_end)}
    order = ['A', 'F', 'P', 'K', 'C']
    if document['brief'] == 'J1':
        expected_ports['Q'] = [receiving[0][0]-spec['rise_offset'], spec['upright_top']]
        expected_directions['Q'] = [0., 1.]
        order.insert(3, 'Q')
    expected_ports = {key: [value*HEIGHT for value in point] for key, point in expected_ports.items()}
    if (document['ports_mm'] != expected_ports or document['directions'] != expected_directions
            or document['port_order'] != order or len(document['boundary']) != len(order)-1):
        raise ValueError('Approved port geometry, directions or inventory changed')
    for piece, start, end in zip(document['boundary'], order, order[1:]):
        profile = 'departure' if start == 'A' else 'receiving' if end == 'C' else 'core'
        expected_curve = terminal_curve(expected_ports[start], expected_ports[end], expected_directions['A']) if start == 'A' else (
            terminal_curve(expected_ports[start], expected_ports[end], expected_directions['C'], True) if end == 'C' else
            vector_curve(expected_ports[start], expected_ports[end], expected_directions[start], expected_directions[end]))
        if (piece['piece_id'] != start+'-'+end or piece['ports'] != [start, end]
                or piece['contact_profile'] != profile or piece['cubics_mm'] != [expected_curve]
                or piece['owner'] != ('n' if start in ('A', 'F') else 'u')):
            raise ValueError('Approved deterministic rule or boundary ownership changed')
    for owner in ('0:3', '1:0'):
        retained = next(piece for piece in document['retained'] if piece['piece_id'] == owner)
        replaced = [piece['replacement_source_span']['interval'] for piece in document['boundary']
                    if piece['replacement_source_span'] and piece['replacement_source_span']['occurrence_id'] == owner]
        if len(replaced) != 1:
            raise ValueError('Source must have one replacement owner')
        intervals = sorted([list(map(Fraction, retained['source_interval'])), list(map(Fraction, replaced[0]))])
        if intervals[0][0] != 0 or intervals[0][1] != intervals[1][0] or intervals[1][1] != 1:
            raise ValueError('Source coverage gap or double ownership')
    for piece in document['boundary']:
        if (piece['contributors'] != ['n', 'u'] or piece['contact'] != 'pen-down'
                or piece['added_entry_travel'] != (piece['replacement_source_span'] is None)):
            raise ValueError('Invalid reciprocal lineage')


def quadratic_range(coefficients):
    constant, linear, quadratic = map(Fraction, coefficients)
    probes = [Fraction(0), Fraction(1)]
    if quadratic:
        vertex = -linear/(2*quadratic)
        if 0 < vertex < 1:
            probes.append(vertex)
    values = [constant+linear*parameter+quadratic*parameter*parameter for parameter in probes]
    return min(values), max(values)


def derivative_range(cubic, axis):
    polynomial = bounds.power(cubic, axis)
    return quadratic_range([polynomial[1], 2*polynomial[2], 3*polynomial[3]])


def coordinate_range(cubic, axis):
    polynomial = bounds.power(cubic, axis)
    derivative = [polynomial[1], 2*polynomial[2], 3*polynomial[3]]
    roots = [] if not any(derivative) else bounds.quadratic_roots(derivative)
    extrema = [(cubic[0][axis], 0.), (cubic[-1][axis], 1.)]
    error = GUARD+max(math.hypot(*vector) for vector in bounds.original.derivatives(cubic)[0])*1e-12
    for root in roots:
        if 0 < root < 1:
            value = clearance.attachment.point(cubic, root)[axis]
            extrema.extend([(value-error, root), (value+error, root)])
    return min(value for value, _ in extrema), max(value for value, _ in extrema)


def envelope_check(cubic, rectangle):
    for axis, (lower, upper) in enumerate(rectangle):
        actual = coordinate_range(cubic, axis)
        if actual[0] < lower-GUARD or actual[1] > upper+GUARD:
            return {'status': 'fail', 'axis': axis, 'bounded_extent': actual, 'envelope': rectangle}
    return {'status': 'pass', 'envelope': rectangle, 'method': 'Analytic cubic extrema with guarded interior bounds'}


def excursion_check(cubic, receiving=False):
    polynomial = bounds.power(cubic, 0)
    derivative = [polynomial[1], 2*polynomial[2], 3*polynomial[3]]
    stationary = bounds.interior_roots(derivative)
    crossing = [polynomial[1]+polynomial[2]+polynomial[3], polynomial[2]+polynomial[3], polynomial[3]] if receiving else polynomial[1:]
    roots = bounds.interior_roots(crossing)
    if len(stationary) != 1 or len(roots) != 1:
        return {'status': 'fail', 'reason': 'One directed excursion and recovery required'}
    topology = roots[0] < stationary[0] if receiving else stationary[0] < roots[0]
    if not topology:
        return {'status': 'fail', 'reason': 'Wrong excursion order'}
    anchor = cubic[-1] if receiving else cubic[0]
    extent = coordinate_range(cubic, 0)
    excursion = extent[1]-anchor[0] if receiving else anchor[0]-extent[0]
    local = clearance.restrict(cubic, max(0., roots[0]-1e-12), 1.) if receiving else clearance.restrict(cubic, 0., min(1., roots[0]+1e-12))
    locality = max(math.dist(point, anchor) for point in local)+GUARD
    vertical = derivative_range(cubic, 1)
    correct_signs = derivative[0] > 0 > sum(derivative) if receiving else derivative[0] < 0 < sum(derivative)
    status = 'pass' if correct_signs and vertical[1] <= 0 and excursion < .0045-GUARD and locality < .1125-GUARD else 'unresolved'
    if excursion > .0045+GUARD or not correct_signs or vertical[1] > 0:
        status = 'fail'
    return {'status': status, 'excursion_upper_mm': excursion, 'limit_mm': .0045,
            'locality_upper_mm': locality, 'locality_limit_mm': .1125,
            'stationary_parameter': stationary[0], 'recovery_parameter': roots[0]}


def length_check(curves):
    intervals = [bounds.original.length_bounds(cubic) for cubic in curves]
    lower, upper = [sum(interval[index] for interval in intervals) for index in (0, 1)]
    limit = 1.25*math.dist(curves[0][0], curves[-1][-1])
    status = 'pass' if upper+GUARD < limit else 'fail' if lower-GUARD > limit else 'unresolved'
    return {'status': status, 'lower_mm': lower, 'upper_mm': upper, 'limit_mm': limit,
            'subdivisions_share_one_allowance': True}


def thin_window(curves, curvature_results):
    certificates = []
    for cubic in curves:
        horizontal, vertical = [derivative_range(cubic, axis) for axis in (0, 1)]
        first, _ = bounds.original.derivatives(cubic)
        speed_projection = quadratic_range([sum(first[0]), 2*(sum(first[1])-sum(first[0])),
                                            sum(first[0])-2*sum(first[1])+sum(first[2])])[0]
        if horizontal[0] < 0 or vertical[0] < 0 or speed_projection <= 0:
            return {'status': 'unresolved', 'reason': 'Positive forward quadrant/normal progress not certified'}
        certificates.append({'minimum_dx': float(horizontal[0]), 'minimum_dy': float(vertical[0]),
                             'minimum_dx_plus_dy': float(speed_projection)})
    if any(result['status'] != 'pass' for result in curvature_results):
        return {'status': 'unresolved', 'reason': 'Curvature prerequisite not certified'}
    joins = []
    for before, after in zip(curves, curves[1:]):
        outgoing, incoming = clearance.attachment.tangent(before, 1), clearance.attachment.tangent(after, 0)
        if math.dist(before[-1], after[0]) > 1e-9 or math.dist(outgoing, incoming) > 1e-8:
            return {'status': 'unresolved', 'reason': 'Discontinuous thin-core join'}
        joins.append(abs(math.atan2(outgoing[0]*incoming[1]-outgoing[1]*incoming[0], sum(left*right for left, right in zip(outgoing, incoming))))+1e-12)
    normal_lower = min(math.sin(math.radians(40)), math.cos(math.radians(40)))-1e-12
    arc_window = (.02+2*GUARD)/normal_lower
    turn_upper = arc_window/.1125+sum(joins)+GUARD
    return {'status': 'pass' if turn_upper < math.pi/2-GUARD else 'unresolved',
            'normal_progress_lower': normal_lower, 'overlap_arc_window_upper_mm': arc_window,
            'window_turn_upper_radians': turn_upper, 'turn_limit_radians': math.pi/2,
            'derivative_certificates': certificates, 'join_turn_upper_radians': sum(joins),
            'scope': 'Whole fixed-corner core; window-local turn, no inter-owner permission',
            'proof': 'Strict normal progress makes each normal window contiguous; the fixed finite rectangle spans .02mm along its normal. Integrating progress bounds every overlapping parameter pair. Curvature plus join turns bounds every such arc window.'}


def structural_checks(document, model):
    validate_identity(document, model)
    ports = document['ports_mm']
    retained = {piece['piece_id']: piece for piece in document['retained']}
    foot_x = retained['0:3']['canonical_owner']['cubics'][0][-1][0]*HEIGHT
    rectangles = {'departure': [[foot_x-.02*HEIGHT, foot_x+.15*HEIGHT], [0., ports['A'][1]]],
                  'core': [[ports['F'][0], ports['K'][0]], [0., ports['K'][1]]],
                  'receiving': [[ports['K'][0], ports['C'][0]+.0045], [ports['C'][1], ports['K'][1]]]}
    checks = {'identity': {'status': 'pass', 'scope': 'Canonical model, protected source spans and actions'}}
    pieces = document['boundary']
    for piece in pieces:
        cubic = piece['cubics_mm'][0]
        if not all(math.isfinite(value) for point in cubic for value in point):
            raise ValueError('Nonfinite curve')
        name, profile = piece['piece_id'], piece['contact_profile']
        checks[name+'_curvature'] = bounds.original.curvature_check(cubic)
        checks[name+'_envelope'] = envelope_check(cubic, rectangles[profile])
        expected_start, expected_end = [ports[key] for key in piece['ports']]
        directions = [document['directions'][key] for key in piece['ports']]
        errors = [math.dist(cubic[0], expected_start), math.dist(cubic[-1], expected_end)]
        tangent_errors = [math.dist(clearance.attachment.tangent(cubic, index), directions[index]) for index in (0, 1)]
        checks[name+'_joins'] = {'status': 'pass' if max(errors) <= 1e-9 and max(tangent_errors) <= 1e-8 else 'fail',
                                'position_errors_mm': errors, 'unit_tangent_errors': tangent_errors}
        if profile == 'core':
            horizontal, vertical = [derivative_range(cubic, axis) for axis in (0, 1)]
            upright = document['brief'] == 'J1' and name == 'P-Q'
            passed = vertical[0] >= 0 and horizontal[0] >= 0 and (upright or horizontal[1] > 0)
            checks[name+'_progress'] = {'status': 'pass' if passed else 'fail', 'upright_interval': upright}
        else:
            try:
                checks[name+'_excursion'] = excursion_check(cubic, profile == 'receiving')
            except bounds.Unresolved as error:
                checks[name+'_excursion'] = {'status': 'unresolved', 'reason': str(error)}
    chains = {profile: [piece['cubics_mm'][0] for piece in pieces if piece['contact_profile'] == profile]
              for profile in ('departure', 'core', 'receiving')}
    for profile, curves in chains.items():
        checks[profile+'_aggregate_length'] = length_check(curves)
    attachments = [(retained['0:3']['cubics_mm'][0], chains['departure'][0]),
                   (chains['receiving'][0], retained['1:0']['cubics_mm'][0])]
    passed = all(math.dist(before[-1], after[0]) <= 1e-9 and
                 math.dist(clearance.attachment.tangent(before, 1), clearance.attachment.tangent(after, 0)) <= 1e-8
                 for before, after in attachments)
    checks['protected_attachments'] = {'status': 'pass' if passed else 'fail'}
    width_upper = math.hypot(.045, .02)+GUARD
    limit = .25*(.45*math.cos(math.radians(40))+.02*math.sin(math.radians(40)))
    checks['thin_width'] = {'status': 'pass' if width_upper < limit else 'fail',
                            'width_upper_mm': width_upper, 'limit_mm': limit,
                            'domain': 'Entire F-K, excluding neither P nor Q; ramps reported separately'}
    checks['thin_self_contact'] = thin_window(chains['core'], [checks[piece['piece_id']+'_curvature'] for piece in pieces if piece['contact_profile'] == 'core'])
    return checks


def ramp_self_contact(cubic, profile):
    length_lower, length_upper = bounds.original.length_bounds(cubic)
    first, _ = bounds.original.derivatives(cubic)
    edge = [math.cos(math.radians(40)), -math.sin(math.radians(40))]
    normal = [-edge[1], edge[0]]
    certificates = []
    for axis in (edge, normal):
        projections = [sum(component*weight for component, weight in zip(vector, axis)) for vector in first]
        speed_upper = max(math.hypot(*vector) for vector in first)
        minimum, maximum = quadratic_range([projections[0], 2*(projections[1]-projections[0]),
                                            projections[0]-2*projections[1]+projections[2]])
        if minimum > GUARD:
            sign, progress = 1, float(minimum)/speed_upper
        elif maximum < -GUARD:
            sign, progress = -1, -float(maximum)/speed_upper
        else:
            return {'status': 'unresolved', 'reason': 'Ramp footprint-boundary monotonicity not certified',
                    'axis': axis, 'projection_range': [float(minimum), float(maximum)]}
        adverse_rate = .405/length_lower if axis == edge and ((profile == 'departure' and sign > 0) or (profile == 'receiving' and sign < 0)) else 0.
        if progress <= adverse_rate+GUARD:
            return {'status': 'unresolved', 'reason': 'Moving active-edge endpoint can reverse its projection'}
        certificates.append({'axis': axis, 'sign': sign, 'progress_lower': progress,
                             'adverse_edge_rate_upper': adverse_rate})
    return {'status': 'pass', 'certificates': certificates, 'length_upper_mm': length_upper,
            'proof': 'Both footprint boundaries on each fixed nib axis are monotone with the same sign. Each point membership is an intersection of parameter intervals, so leaving and returning to that point is excluded. Variable edge rate uses aggregate arclength, not cubic parameter.'}


def external_contacts(document):
    groups = []
    for profile in ('departure', 'core', 'receiving'):
        groups.append({'name': profile, 'profile': profile, 'curves': [piece['cubics_mm'][0] for piece in document['boundary'] if piece['contact_profile'] == profile]})
    pairs = []
    permissions = {('departure', '0:3'): 'A', ('receiving', '1:0'): 'C',
                   ('departure', 'core'): 'F', ('core', 'receiving'): 'K'}
    others = [{'name': piece['piece_id'], 'profile': 'full', 'curves': piece['cubics_mm']} for piece in document['retained']]
    for index, group in enumerate(groups):
        for other in others+groups[index+1:]:
            port = permissions.get((group['name'], other['name']))
            join = document['ports_mm'][port] if port else None
            passed = all(original.contact_pair(first, group['profile'], second, other['profile'], join)
                         for first in group['curves'] for second in other['curves'])
            pairs.append({'owners': [group['name'], other['name']], 'splice_port': port,
                          'status': 'pass' if passed else 'unresolved'})
            if not passed:
                return {'status': 'unresolved', 'pairs': pairs, 'reason': 'Finite swept enclosures not certified separated or in the named adjacent splice disk'}
    ramps = {group['name']: ramp_self_contact(group['curves'][0], group['profile']) for group in groups if group['profile'] != 'core'}
    return {'status': 'pass' if all(check['status'] == 'pass' for check in ramps.values()) else 'unresolved',
            'pairs': pairs, 'ramp_self_contact': ramps,
            'method': 'Finite rectangle hull separation, full-contact supersets for ramps, exact corner core; no new P/Q permissions'}


def inspect(document, model):
    try:
        checks = structural_checks(document, model)
    except bounds.Unresolved as error:
        return {'status': 'unresolved', 'render_eligible': False,
                'checks': {'structural_measurement': {'status': 'unresolved', 'reason': str(error)}}}
    structural_pass = all(check['status'] == 'pass' for check in checks.values())
    checks['external_and_ramp_contact'] = external_contacts(document) if structural_pass else {
        'status': 'not_run', 'reason': 'Structural admission failed; no contact or rendering acceptance inferred'}
    status = 'admitted' if all(check['status'] == 'pass' for check in checks.values()) else (
        'rejected' if any(check['status'] == 'fail' for check in checks.values()) else 'unresolved')
    return {'status': status, 'checks': checks, 'render_eligible': status == 'admitted'}


def write_report(report):
    payload = (json.dumps(report, indent=2, allow_nan=False)+'\n').encode()
    other_bytes = sum(path.stat().st_size for path in OUTPUT.iterdir() if path.name not in ('report.json', '.report.tmp'))
    if other_bytes+len(payload) > MAX_BYTES-65536:
        raise ValueError('Evidence size ceiling exceeded')
    temporary = OUTPUT/'.report.tmp'
    with temporary.open('wb') as stream:
        stream.write(payload)
        stream.flush()
    temporary.replace(OUTPUT/'report.json')


def status_page(report):
    sections = []
    if report.get('error'):
        sections.append('<section><h2>Preflight stopped</h2><p>'+html.escape(report['error'])+'</p><p>No study candidate was constructed. The frozen identity guard was not bypassed.</p></section>')
    for entry in report['candidates']:
        failures = [(name, check) for name, check in entry.get('evaluation', {}).get('checks', {}).items() if check['status'] != 'pass']
        rows = ''.join('<li><strong>'+html.escape(name)+'</strong>: '+html.escape(json.dumps(check))+'</li>' for name, check in failures)
        sections.append('<section><h2>'+html.escape(entry['brief'])+' — '+html.escape(entry['status'])+'</h2><ul>'+rows+'</ul></section>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Reciprocal nu — bounded batch status</title><style>body{max-width:1000px;margin:40px auto;padding:0 24px;font:17px/1.6 system-ui;background:#faf8f2;color:#26322e}section{background:white;border:1px solid #ccc;padding:18px;margin:24px 0}li{overflow-wrap:anywhere;margin:12px 0}a{color:#126a66}</style>'
            '<h1>Reciprocal nu: J1 / J2</h1><p>No failed or unresolved candidate is rendered. This is a technical status board, not a visual comparison or owner acceptance.</p>'
            +''.join(sections)+'<p><a href="report.json">Frozen candidate controls and full checks</a></p>'
            '<p><a href="../../nu-contextual-entry-v1/nominal-001/index.html">Historical canonical / old bridge / derived comparison</a> — old and derived are owner-rejected, not targets.</p>'
            '<p>No fitting, physical runs, mu, nib rotation, spacing changes or automatic retries.</p></html>')


def run():
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    report = {'version': VERSION, 'status': 'stopped', 'approval': approval_record(),
              'code_sha256': actions.digest(Path(__file__)),
              'tests_sha256': actions.digest(ROOT/'tests/test_nu_mutual_construction.py'),
              'candidates': [], 'new_candidates': 0, 'renders': 0, 'fitting_evaluations': 0,
              'physical_runs': 0, 'mu_started': False, 'nib_rotation': False}
    started = time.monotonic()
    def timeout_handler(signum, frame):
        raise TimeoutError('Approved 300-second construction/check ceiling reached')
    previous_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        write_report(report)
        verify()
        model = source.read_json(source.CANDIDATE)
        before = actions.object_digest(model)
        for name in ('J1', 'J2'):
            entry = {'brief': name, 'status': 'construction_started'}
            report['candidates'].append(entry)
            write_report(report)
            document = construct(model, name)
            entry.update(candidate=document, candidate_sha256=actions.object_digest(document), status='constructed')
            report['new_candidates'] += 1
            write_report(report)
            evaluation = inspect(document, model)
            entry.update(evaluation=evaluation, status=evaluation['status'])
            write_report(report)
        if actions.object_digest(model) != before:
            raise ValueError('Canonical model mutated')
        verify()
        report['frozen_inputs_verified_after'] = True
        report['status'] = 'admitted_awaiting_nominal' if any(entry['status'] == 'admitted' for entry in report['candidates']) else 'no_candidate_admitted'
    except (ValueError, OSError, TimeoutError, bounds.Unresolved) as error:
        report.update(status='stopped', error=str(error))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        report['construction_check_seconds'] = time.monotonic()-started
        write_report(report)
    if report['status'] != 'admitted_awaiting_nominal':
        render_started = time.monotonic()
        page = status_page(report).encode()
        if sum(path.stat().st_size for path in OUTPUT.iterdir())+len(page) > MAX_BYTES-65536:
            raise ValueError('Evidence size ceiling exceeded')
        with (OUTPUT/'index.html').open('xb') as stream:
            stream.write(page)
        report['status_board_seconds'] = time.monotonic()-render_started
        report['status_board_sha256'] = actions.digest(OUTPUT/'index.html')
        write_report(report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-approved-batch', action='store_true', required=True)
    parser.parse_args()
    result = run()
    print(json.dumps({'status': result['status'], 'new_candidates': result['new_candidates'],
                      'seconds': result['construction_check_seconds'], 'report': str(OUTPUT/'report.json')}))
