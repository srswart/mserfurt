"""One approved primitive-derived thin nu entry; no fitting or rendering."""

import argparse
import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import signal
import time

from scripts import nu_entry_port_audit as audit


frozen = audit.frozen
original = frozen.original
actions = frozen.actions
source = frozen.source
bounds = frozen.bounds
clearance = original.capability.clearance
ROOT = frozen.ROOT
BASE = audit.BASE
OUTPUT = BASE/'derived-entry-001'
VERSION = 'nu-derived-entry-geometry-v1'
PROPOSAL = ROOT/'docs/tech-direction/TD-018-nu-derived-entry-proposal.md'
PROPOSAL_PIN = '9bc29f67ee0c1fd2a21e461b5dfe768a0dad63d6a9a9ddfbc096fea71b0cbf8f'
AUDIT_PIN = '8bf7cf5810a7e215a70086d2af1f5de1ad366af155ed6c09a37d3a3ac46fda99'


def approval_record():
    return {'version': VERSION, 'owner_quote': "Approved -- let's do it.",
            'proposal_sha256': PROPOSAL_PIN, 'audit_report_sha256': AUDIT_PIN,
            'candidate_count': 1, 'seconds': 300, 'max_output_bytes': 10*1024**2,
            'minimum_free_bytes': 5*1024**3, 'retries': 0, 'images': 0,
            'fitting': False, 'physical_runs': 0, 'mu': False}


def verify():
    if source.read_json(BASE/'derived-approval.json') != approval_record():
        raise ValueError('Exact derived-entry approval required')
    if actions.digest(PROPOSAL) != PROPOSAL_PIN or actions.digest(audit.OUTPUT/'report.json') != AUDIT_PIN:
        raise ValueError('Frozen proposal/audit changed')
    report = source.read_json(audit.OUTPUT/'report.json')
    for path, pin in ((Path(audit.__file__), report['code_sha256']), (ROOT/'tests/test_nu_entry_port_audit.py', report['tests_sha256'])):
        if actions.digest(path) != pin:
            raise ValueError('Frozen audit implementation changed')
    audit.verify(source.read_json(BASE/'approval.json'))


def rotate(vector, degrees):
    cosine, sine = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return [cosine*vector[0]-sine*vector[1], sine*vector[0]+cosine*vector[1]]


def height_port(cubic, height):
    polynomial = bounds.power(cubic, 1)
    derivative = [polynomial[1], 2*polynomial[2], 3*polynomial[3]]
    roots = bounds.quadratic_roots(derivative)
    probes = [Fraction(1,2)]
    if any(0 < root < 1 for root in roots) or audit.evaluate(derivative, probes[0]) <= 0:
        raise bounds.Unresolved('Scaffold not uniquely ascending')
    lower, upper = Fraction(0), Fraction(1)
    target = Fraction(height)
    if not cubic[0][1] < height < cubic[-1][1]:
        raise ValueError('Height outside scaffold')
    def value(parameter):
        result = Fraction(0)
        for coefficient in reversed(polynomial):
            result = result*parameter+coefficient
        return result-target
    for _ in range(60):
        middle = (lower+upper)/2
        if value(middle) < 0:
            lower = middle
        else:
            upper = middle
    if not value(lower) < 0 <= value(upper):
        raise bounds.Unresolved('Port root bracket unavailable')
    parameter = float((lower+upper)/2)
    return clearance.attachment.point(cubic, parameter), {'parameter': parameter,
            'bracket_exact': [str(lower), str(upper)], 'signs': ['negative', 'nonnegative']}


def proportions(cubic):
    chord = math.dist(cubic[0], cubic[-1])
    if not math.isfinite(chord) or chord <= 0:
        raise ValueError('Nonzero finite source chord required')
    ratios = [math.dist(cubic[0], cubic[1])/chord, math.dist(cubic[-2], cubic[-1])/chord]
    if not all(math.isfinite(value) and value > 0 for value in ratios):
        raise ValueError('Nonzero finite source handles required')
    return ratios


def derive(start, end, incoming, outgoing, ratios):
    if any(abs(math.hypot(*direction)-1) > 1e-8 for direction in (incoming,outgoing)):
        raise ValueError('Unit directed ports required')
    length = math.dist(start,end)
    if length <= 0:
        raise ValueError('Nonzero derived chord required')
    return [start, [start[axis]+length*ratios[0]*incoming[axis] for axis in (0,1)],
            [end[axis]-length*ratios[1]*outgoing[axis] for axis in (0,1)], end]


def construct(saved, canonical):
    theta = audit.difference(audit.angle(saved['outgoing_tangent']), audit.angle(canonical['primitives']['lower-return']['entry']))
    rise = canonical['primitives']['rise']
    directions = [rotate(rise[key],theta) for key in ('entry','exit')]
    if any(value <= 0 for direction in directions for value in direction):
        raise ValueError('Backward entry ports')
    heights = [3.5*canonical['primitives'][name]['cubics'][0][-1][1] for name in ('lower-return','rise')]
    ports = [height_port(saved['boundary'][1]['cubics_mm'][0],height) for height in heights]
    anchors = saved['anchors_mm']
    points = [anchors['B'],ports[0][0],ports[1][0],anchors['D']]
    if not all(before[0] < after[0] and before[1] < after[1] for before,after in zip(points,points[1:])):
        raise ValueError('Port order failed')
    sources, provenance = [], []
    for name in audit.INVENTORY:
        primitive = canonical['primitives'][name]
        cubic = primitive['cubics'][0]
        interval = [0.0,1.0]
        brackets = []
        if name != 'rise':
            polynomial = audit.projected_power(cubic,1,theta)
            roots = bounds.interior_roots([polynomial[1],2*polynomial[2],3*polynomial[3]])
            if len(roots) != 1:
                raise bounds.Unresolved('Unique source extremum required')
            derivative = [polynomial[1],2*polynomial[2],3*polynomial[3]]
            expected = -1 if name == 'lower-return' else 1
            if expected*audit.evaluate(derivative,0) <= 0 or expected*audit.evaluate(derivative,1) >= 0:
                raise ValueError('Wrong source extremum signs')
            interval = [roots[0],1.0] if name == 'lower-return' else [0.0,roots[0]]
            brackets = [[roots[0]-1e-12,roots[0]+1e-12]]
            cubic = clearance.restrict(cubic,*interval)
        ratios = proportions(cubic)
        sources.append(ratios)
        provenance.append({'primitive':name,'primitive_sha256':actions.object_digest(primitive),
                           'source_interval':interval,'extremum_brackets':brackets,'handle_chord_ratios':ratios})
    tangents = [[1.0,0.0],*directions,[1.0,0.0]]
    curves = [derive(points[index],points[index+1],tangents[index],tangents[index+1],ratios) for index,ratios in enumerate(sources)]
    document = copy.deepcopy(saved)
    document['version'] = VERSION
    document['boundary'][1]['cubics_mm'] = curves
    document['derivation'] = {'family':'source-handle-chord-ratios-v1','theta_deg':theta,
                              'ports':ports,'tangents':tangents,'source_spans':provenance,
                              'semantics':['n departure T plus recovery','u entry-rise','u crown approach plus S'],
                              'contact_partition':['A-B','B-D','D-C'],'derived_not_exact_reuse':True}
    return document


def unchanged(document, saved):
    restored = copy.deepcopy(document)
    restored.pop('derivation')
    restored['version'] = saved['version']
    restored['boundary'][1]['cubics_mm'] = saved['boundary'][1]['cubics_mm']
    if restored != saved or len(document['boundary'][1]['cubics_mm']) != 3:
        raise ValueError('Frozen body/contact/source identity changed')


def checks(document, saved):
    unchanged(document,saved)
    canonical = source.read_json(source.CANDIDATE)
    derivation = document['derivation']
    expected_theta = audit.difference(audit.angle(saved['outgoing_tangent']),audit.angle(canonical['primitives']['lower-return']['entry']))
    if derivation['theta_deg'] != expected_theta or derivation['contact_partition'] != ['A-B','B-D','D-C']:
        raise ValueError('Derivation/contact partition changed')
    expected_tangents = [[1.0,0.0],*[rotate(canonical['primitives']['rise'][key],expected_theta) for key in ('entry','exit')],[1.0,0.0]]
    if derivation['tangents'] != expected_tangents or len(derivation['source_spans']) != 3:
        raise ValueError('Derived directed ports changed')
    expected_ports = [height_port(saved['boundary'][1]['cubics_mm'][0],3.5*canonical['primitives'][name]['cubics'][0][-1][1]) for name in ('lower-return','rise')]
    if actions.object_digest(derivation['ports']) != actions.object_digest(expected_ports):
        raise ValueError('Semantic port placement changed')
    points = [saved['anchors_mm']['B'],expected_ports[0][0],expected_ports[1][0],saved['anchors_mm']['D']]
    for index,(name,row) in enumerate(zip(audit.INVENTORY,derivation['source_spans'])):
        primitive = canonical['primitives'][name]
        cubic = primitive['cubics'][0]
        interval = [0.0,1.0]
        if name != 'rise':
            polynomial = audit.projected_power(cubic,1,expected_theta)
            roots = bounds.interior_roots([polynomial[1],2*polynomial[2],3*polynomial[3]])
            if len(roots)!=1:
                raise ValueError('Ambiguous derivation extremum')
            interval = [roots[0],1.0] if name=='lower-return' else [0.0,roots[0]]
            cubic = clearance.restrict(cubic,*interval)
        ratios = proportions(cubic)
        if row['primitive']!=name or row['primitive_sha256']!=actions.object_digest(primitive) or row['source_interval']!=interval or row['handle_chord_ratios']!=ratios:
            raise ValueError('Primitive/cut/ratio lineage changed')
        if document['boundary'][1]['cubics_mm'][index] != derive(points[index],points[index+1],expected_tangents[index],expected_tangents[index+1],ratios):
            raise ValueError('Derived formula geometry changed')
    baseline, _ = frozen.inspect(saved)
    result = {key:value for key,value in baseline.items() if key not in ('R_curvature','R_length','R_rightward','vertical_band')}
    curves = document['boundary'][1]['cubics_mm']
    length_bounds = [bounds.original.length_bounds(cubic) for cubic in curves]
    limit = 1.25*math.dist(saved['anchors_mm']['B'],saved['anchors_mm']['D'])
    lower, upper = [sum(values[index] for values in length_bounds) for index in (0,1)]
    result['R_aggregate_length'] = {'status':'pass' if upper+1e-9 < limit else 'fail' if lower-1e-9 > limit else 'unresolved',
                                    'lower_mm':lower,'upper_mm':upper,'limit_mm':limit}
    directions = document['derivation']['tangents']
    for index,cubic in enumerate(curves):
        result[f'R{index}_curvature'] = bounds.original.curvature_check(cubic)
        result[f'R{index}_rightward'] = original.increasing_x(cubic)
        first,_ = bounds.original.derivatives(cubic)
        vertical = all(vector[1] >= 0 for vector in first) and first[1][1] > 0
        result[f'R{index}_vertical'] = {'status':'pass' if vertical else 'unresolved','method':'Bernstein derivative sign bound'}
        errors = [math.dist(clearance.attachment.tangent(cubic,parameter),directions[index+parameter]) for parameter in (0,1)]
        result[f'R{index}_ports'] = {'status':'pass' if max(errors)<=1e-8 else 'fail','unit_errors':errors}
    result['R_position_joins'] = {'status':'pass' if all(before[-1]==after[0] for before,after in zip(curves,curves[1:])) and curves[0][0]==saved['anchors_mm']['B'] and curves[-1][-1]==saved['anchors_mm']['D'] else 'fail'}
    return result


def contacts(document):
    pieces = document['boundary']
    rows = []
    for piece in pieces:
        for cubic in piece['cubics_mm']:
            for retained in document['retained']:
                join = None
                if piece['source_owner'] == retained['canonical_owner']['occurrence_id']:
                    join = document['anchors_mm']['A' if piece['piece_id']=='T' else 'C']
                for other in retained['cubics_mm']:
                    passed = original.contact_pair(cubic,piece['contact_profile'],other,'full',join)
                    rows.append({'pieces':[piece['piece_id'],retained['piece_id']],'status':'pass' if passed else 'unresolved'})
                    if not passed:
                        return {'status':'unresolved','pairs':rows}
    for index,before in enumerate(pieces):
        for after in pieces[index+1:]:
            key = (before['piece_id'],after['piece_id'])
            join = document['anchors_mm']['B'] if key==('T','R') else document['anchors_mm']['D'] if key==('R','S') else None
            for first in before['cubics_mm']:
                for second in after['cubics_mm']:
                    if not original.contact_pair(first,before['contact_profile'],second,after['contact_profile'],join):
                        return {'status':'unresolved','pairs':rows,'reason':'Boundary pair not certified'}
    direction = [math.cos(math.radians(40)),-math.sin(math.radians(40))]
    normal = [-direction[1],direction[0]]
    certificates = []
    for axis in (direction,normal):
        values = [sum(component*weight for component,weight in zip(vector,axis))
                  for cubic in pieces[1]['cubics_mm'] for vector in bounds.original.derivatives(cubic)[0]]
        certificates.append(min(values)>1e-9 or max(values)<-1e-9)
    if all(certificates):
        return {'status':'pass','pairs':rows,'self_contact':'Both fixed rectangle-axis projections strictly monotone: membership in any footprint point is one connected parameter interval, with no leave-and-reenter contact'}
    return {'status':'unresolved','pairs':rows,
            'reason':'External pairs separated/confined; sufficient monotone rectangle-axis certificate for aggregate R self-contact unavailable. No additional P/Q overlap permissions granted.'}


def run():
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    report = {'version':VERSION,'status':'stopped','accepted':False,'new_candidates':0,'fitting_evaluations':0,'renders':0,'physical_runs':0,'mu_started':False}
    def save(name,value):
        payload = (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
        if sum(path.stat().st_size for path in OUTPUT.iterdir())+len(payload)>10*1024**2:
            raise ValueError('Output ceiling')
        with (OUTPUT/name).open('xb') as stream:
            stream.write(payload)
    def timeout_handler(signum,frame):
        raise TimeoutError('300-second construction/check ceiling')
    previous = signal.signal(signal.SIGALRM,timeout_handler)
    signal.alarm(300)
    try:
        with source.evidence.read_only_guard():
            verify()
            report.update(approval=approval_record(),code_sha256=actions.digest(Path(__file__)),tests_sha256=actions.digest(ROOT/'tests/test_nu_derived_entry.py'))
            saved = source.read_json(frozen.SAVED)
            document = construct(saved,source.read_json(source.CANDIDATE))
            save('candidate.json',document)
            report.update(new_candidates=1,candidate_sha256=actions.digest(OUTPUT/'candidate.json'))
            results = checks(document,saved)
            report['checks'] = results
            if all(check['status']=='pass' for check in results.values()):
                results['finite_contact'] = contacts(document)
            else:
                results['finite_contact'] = {'status':'not_evaluated','reason':'Structural gate failure or uncertainty'}
            report['status'] = ('geometry_pass_nominal_gated' if all(check['status']=='pass' for check in results.values()) else
                                'rejected' if any(check['status']=='fail' for check in results.values()) else 'unresolved')
            for path,pin in {**frozen.PINS,**audit.PINS}.items():
                if actions.digest(path)!=pin:
                    raise ValueError('Frozen input changed during run')
            report['frozen_inputs_unchanged'] = True
    except Exception as error:
        report.update(status='stopped',error=f'{type(error).__name__}: {error}')
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM,previous)
        report['elapsed_seconds'] = time.monotonic()-started
        save('report.json',report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['run'])
    parser.parse_args()
    print(json.dumps(run(),indent=2))
