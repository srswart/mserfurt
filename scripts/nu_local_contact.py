"""Apply the approved R-only local-contact rule to the frozen derived nu."""

import argparse
import json
import math
from pathlib import Path
import shutil
import signal
import time

from scripts import nu_self_contact_review as measurement


previous = measurement.previous
actions = measurement.actions
source = measurement.source
ROOT = measurement.ROOT
BASE = measurement.BASE
OUTPUT = BASE/'local-contact-review-001'
APPROVAL = BASE/'local-contact-approval.json'
RULE = ROOT/'docs/tech-direction/TD-018-local-contact-classification.md'
VERSION = 'nu-local-contact-classification-v1'
PINS = {
    RULE: 'e749563aced409e48d53bede3094e15ed024568cc3c1cccb6a1bc6b812633860',
    measurement.OUTPUT/'report.json': '6bd3453b1ff86f7e6461ff77cecc4026f23a6cd0097a3284271b12e39dc20278',
    Path(measurement.__file__): 'ca265c4910de5bc0fbe8410d9b1ac651706b2ef00ea42e640462f1b7eb746037',
    ROOT/'tests/test_nu_self_contact_review.py': '492522f71a412a00a85791bc1bb0cb72f9e68da41268c1b1b0f3dc6035a5537d',
    **measurement.PINS,
}


def approval_record():
    return {'version': VERSION, 'owner_quote': 'I approve lets implement and re-inspect without refitting.',
            'rule_sha256': PINS[RULE], 'pins': {str(path.relative_to(ROOT)): pin for path,pin in PINS.items()},
            'seconds': 300, 'max_output_bytes': 10*1024**2, 'minimum_free_bytes': 5*1024**3,
            'reinspections': 1, 'retries': 0, 'new_geometry': False, 'fitting': False,
            'images': 0, 'physical_runs': 0, 'mu': False}


def verify():
    if source.read_json(APPROVAL) != approval_record():
        raise ValueError('Exact local-contact classification approval required')
    for path,pin in PINS.items():
        if actions.digest(path) != pin:
            raise ValueError(f'Frozen input changed: {path}')
    measurement.verify()


def turning_gate(arclength_upper, join_turn_upper):
    if not all(math.isfinite(value) and value >= 0 for value in (arclength_upper,join_turn_upper)):
        raise ValueError('Finite nonnegative turning inputs required')
    upper = arclength_upper/.1125+join_turn_upper+1e-12
    margin = math.pi/2-upper
    return {'status': 'pass' if margin > 1e-9 else 'unresolved',
            'turn_upper_radians': upper, 'classification_limit_radians': math.pi/2,
            'margin_radians': margin, 'curvature_limit_per_mm': 1/.1125,
            'includes_all_join_turns': True}


def classify(piece, profiles):
    if piece['piece_id'] != 'R' or piece['contact_profile'] != 'core' or piece['contact'] != 'pen-down' or piece['contact_run_ref'] != 'proposed-boundary-run':
        raise ValueError('Local permission applies only to the continuous R core')
    if profiles != previous.actions.PROFILES:
        raise ValueError('Fixed full/corner/full contact profiles required')
    curves = piece['cubics_mm']
    if len(curves) != 3:
        raise ValueError('Exact three-piece R inventory required')
    bound = measurement.measure(curves)
    if bound['status'] != 'bound_certified':
        return {'status': 'unresolved', 'measurement': bound}
    join_errors, join_turns = [], []
    for before,after in zip(curves,curves[1:]):
        outgoing = previous.clearance.attachment.tangent(before,1)
        incoming = previous.clearance.attachment.tangent(after,0)
        join_errors.append(math.dist(outgoing,incoming))
        cross = outgoing[0]*incoming[1]-outgoing[1]*incoming[0]
        dot = sum(left*right for left,right in zip(outgoing,incoming))
        join_turns.append(abs(math.atan2(cross,dot))+1e-12)
    if max(join_errors) > 1e-8:
        return {'status': 'unresolved','reason': 'Tangent corner exceeds unchanged continuity tolerance', 'join_errors': join_errors}
    curvature = [previous.bounds.original.curvature_check(cubic) for cubic in curves]
    if any(result['status'] != 'pass' for result in curvature):
        return {'status': 'unresolved', 'reason': 'Unchanged curvature ceiling not certified', 'curvature': curvature}
    turning = turning_gate(bound['possible_overlap_arclength_separation_upper_mm'],sum(join_turns))
    return {'status': 'pass' if turning['status']=='pass' else 'unresolved',
            'classification': 'ordinary_neighboring_path_coverage' if turning['status']=='pass' else 'unresolved',
            'scope': 'R-to-R only; no other owner/run or T/S permission', 'measurement': bound,
            'curvature': curvature, 'join_errors': join_errors, 'turning': turning,
            'rule': 'One continuous fixed-footprint run, strictly forward normal window and total turning below pi/2; within-window edge-membership changes are permitted by the approved rule'}


def external_contacts(document):
    pieces = document['boundary']
    pairs = []
    for piece in pieces:
        for cubic_index,cubic in enumerate(piece['cubics_mm']):
            for retained in document['retained']:
                join = None
                if piece['source_owner'] == retained['canonical_owner']['occurrence_id']:
                    join = document['anchors_mm']['A' if piece['piece_id']=='T' else 'C']
                for retained_index,other in enumerate(retained['cubics_mm']):
                    passed = previous.original.contact_pair(cubic,piece['contact_profile'],other,'full',join)
                    pairs.append({'pieces': [piece['piece_id'],retained['piece_id']],
                                  'cubic_indices': [cubic_index,retained_index], 'splice_center': join,
                                  'status': 'pass' if passed else 'unresolved'})
                    if not passed:
                        return {'status': 'unresolved', 'pairs': pairs}
    for index,before in enumerate(pieces):
        for after in pieces[index+1:]:
            names = (before['piece_id'],after['piece_id'])
            join = document['anchors_mm']['B'] if names==('T','R') else document['anchors_mm']['D'] if names==('R','S') else None
            for before_index,first in enumerate(before['cubics_mm']):
                for after_index,second in enumerate(after['cubics_mm']):
                    passed = previous.original.contact_pair(first,before['contact_profile'],second,after['contact_profile'],join)
                    pairs.append({'pieces': list(names), 'cubic_indices': [before_index,after_index],
                                  'splice_center': join, 'status': 'pass' if passed else 'unresolved'})
                    if not passed:
                        return {'status': 'unresolved', 'pairs': pairs}
    return {'status': 'pass', 'pairs': pairs, 'method': 'Unchanged finite-rectangle enclosure/separation and existing A/B/D/C splice disks; local R permission not used'}


def run():
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    report = {'version': VERSION, 'status': 'stopped', 'accepted': False,
              'revised_geometry_contact_pass': False, 'new_geometries': 0,
              'fitting_evaluations': 0, 'images': 0, 'physical_runs': 0, 'mu_started': False}
    def timeout_handler(signum,frame):
        raise TimeoutError('300-second reinspection ceiling')
    handler = signal.signal(signal.SIGALRM,timeout_handler)
    signal.alarm(300)
    try:
        with source.evidence.read_only_guard():
            verify()
            report.update(approval=approval_record(), approval_sha256=actions.digest(APPROVAL),
                          code_sha256=actions.digest(Path(__file__)), tests_sha256=actions.digest(ROOT/'tests/test_nu_local_contact.py'))
            document = source.read_json(measurement.CANDIDATE)
            checks = previous.checks(document,source.read_json(previous.frozen.SAVED))
            baseline = source.read_json(measurement.OUTPUT/'report.json')
            if checks != baseline['unchanged_structural_checks'] or any(check['status']!='pass' for check in checks.values()):
                raise ValueError('Unchanged structural prerequisite differs or fails')
            report['unchanged_structural_checks'] = checks
            report['external_contact'] = external_contacts(document)
            if report['external_contact']['status']=='pass':
                report['local_contact'] = classify(document['boundary'][1],document['profiles'])
            else:
                report['local_contact'] = {'status':'not_evaluated'}
            if report['local_contact']['status']=='pass':
                if report['local_contact']['measurement'] != baseline['self_contact_measurement']:
                    raise ValueError('Frozen separation measurement differs')
                report.update(status='revised_geometry_contact_pass_nominal_gated',revised_geometry_contact_pass=True)
            else:
                report['status']='unresolved'
            for path,pin in {**PINS,**previous.frozen.PINS,**previous.audit.PINS}.items():
                if actions.digest(path)!=pin:
                    raise ValueError('Frozen input changed during review')
            report['frozen_inputs_unchanged']=True
    except Exception as error:
        report.update(status='stopped',revised_geometry_contact_pass=False,error=f'{type(error).__name__}: {error}')
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM,handler)
        report['elapsed_seconds']=time.monotonic()-started
        payload=(json.dumps(report,indent=2,allow_nan=False)+'\n').encode()
        if len(payload)>10*1024**2:
            raise ValueError('Output ceiling')
        with (OUTPUT/'report.json').open('xb') as stream:
            stream.write(payload)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['run'])
    parser.parse_args()
    print(json.dumps(run(),indent=2))
