"""Frozen-entry measurement: bound all possible self-contact parameter separation."""

import argparse
import json
import math
from pathlib import Path
import shutil
import signal
import time

from scripts import nu_derived_entry as previous


source = previous.source
actions = previous.actions
ROOT = previous.ROOT
BASE = previous.BASE
OUTPUT = BASE/'self-contact-review-001'
VERSION = 'nu-self-contact-measurement-v2'
CANDIDATE = previous.OUTPUT/'candidate.json'
PINS = {
    CANDIDATE: '16872e32eb44d15c2b226a4327a75851bf6a286ba08568930f856c554e97c433',
    previous.OUTPUT/'report.json': '8123f6684aaf0dd01ea384defa97e8547ddcaa259ba0ec149ce00bf8c759f30c',
    Path(previous.__file__): '94c9fee35678948c421be2495a6285dbcbb945673c0b6e9987baa10fff5918fa',
    ROOT/'tests/test_nu_derived_entry.py': '80ca5e1fd1e3fc8d77745bfda8777146dfe485f4f53cdbd6a826f67e0a48f3c8',
}


def approval_record():
    return {'version':VERSION,
            'owner_quote': "Okay let's strengthen self-contact measurement and reinspect this saved candidate **without changing geometry or limits**.",
            'pins':{str(path.relative_to(ROOT)):pin for path,pin in PINS.items()},
            'seconds':300,'max_output_bytes':10*1024**2,'minimum_free_bytes':5*1024**3,
            'reinspections':1,'retries':0,'new_geometry':False,'fitting':False,'images':0,'physical_runs':0}


def verify():
    if source.read_json(BASE/'self-contact-approval.json') != approval_record():
        raise ValueError('Exact measurement-only approval required')
    for path,pin in PINS.items():
        if actions.digest(path)!=pin:
            raise ValueError('Frozen candidate/evidence changed')
    previous.verify()


def measure(curves):
    if not curves or any(len(cubic)!=4 or any(len(point)!=2 or not all(math.isfinite(value) for value in point) for point in cubic) for cubic in curves):
        raise ValueError('Finite cubic chain required')
    if any(before[-1]!=after[0] for before,after in zip(curves,curves[1:])):
        raise ValueError('Continuous chain required')
    certificates=[]
    edge=[math.cos(math.radians(40)),-math.sin(math.radians(40))]
    for index,cubic in enumerate(curves):
        horizontal=previous.original.increasing_x(cubic)
        first,_=previous.bounds.original.derivatives(cubic)
        vertical=min(vector[1] for vector in first)
        if horizontal['status']!='pass' or vertical<0:
            return {'status':'unresolved','reason':'Forward quadrant not certified; no projection/arc bound admitted','piece':index}
        projected=[sum(component*weight for component,weight in zip(vector,edge)) for vector in first]
        certificates.append({'piece':index,'minimum_dx':horizontal['minimum_dx'],
                             'minimum_bernstein_dy':vertical,'edge_derivative_control_values':projected})
    normal_speed_lower=min(math.sin(math.radians(40)),math.cos(math.radians(40)))-1e-12
    thickness_upper=.02+2e-9
    separation_upper=thickness_upper/normal_speed_lower
    return {'status':'bound_certified','derivative_certificates':certificates,
            'normal_axis':[math.sin(math.radians(40)),math.cos(math.radians(40))],
            'normal_progress_per_arclength_lower':normal_speed_lower,
            'finite_contact_thickness_mm':.02,'guarded_overlap_normal_separation_mm':thickness_upper,
            'possible_overlap_arclength_separation_upper_mm':separation_upper,
            'turn_bound_radians_using_unchanged_curvature_limit':separation_upper/.1125,
            'whole_chain_including_P_Q':True,
            'proof':'dx>0,dy>=0 imply n dot tangent >= min(sin40,cos40). Two translated identical rectangles can overlap only if their n-center projections differ by <= thickness. Integrating the positive normal progress bounds the intervening arclength. This applies to all parameter pairs, not samples.',
            'corner_offset':'Constant negative10% rectangle offset cancels between two footprints; finite .02mm thickness is retained.',
            'meaning':'All overlap beyond the reported derived arclength bound is excluded. The bound is a measurement, not a new locality cutoff or permission for overlap inside it.'}


def run():
    if shutil.disk_usage(BASE).free<5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started=time.monotonic()
    report={'version':VERSION,'status':'stopped','accepted':False,'new_geometries':0,
            'fitting_evaluations':0,'images':0,'physical_runs':0,'mu_started':False}
    def timeout_handler(signum,frame):
        raise TimeoutError('300-second measurement ceiling')
    prior_handler=signal.signal(signal.SIGALRM,timeout_handler)
    signal.alarm(300)
    try:
        with source.evidence.read_only_guard():
            verify()
            document=source.read_json(CANDIDATE)
            saved=source.read_json(previous.frozen.SAVED)
            checks=previous.checks(document,saved)
            old_report=source.read_json(previous.OUTPUT/'report.json')
            if checks!={name:value for name,value in old_report['checks'].items() if name!='finite_contact'}:
                raise ValueError('Unchanged structural measurements differ')
            report.update(approval=approval_record(),code_sha256=actions.digest(Path(__file__)),
                          tests_sha256=actions.digest(ROOT/'tests/test_nu_self_contact_review.py'),
                          unchanged_structural_checks=checks)
            if any(check['status']!='pass' for check in checks.values()):
                raise ValueError('Structural prerequisite failed')
            report['external_contact_recheck']=previous.contacts(document)
            report['self_contact_measurement']=measure(document['boundary'][1]['cubics_mm'])
            report.update(status='unresolved',
                          reason='Stronger separation bound does not authorize residual near-path overlap. No approved quantitative local/nonlocal classification or complete no-reentry proof supplied; acceptance remains gated.')
            for path,pin in {**PINS,**previous.frozen.PINS,**previous.audit.PINS}.items():
                if actions.digest(path)!=pin:
                    raise ValueError('Frozen input changed during measurement')
            report['frozen_inputs_unchanged']=True
    except Exception as error:
        report.update(status='stopped',error=f'{type(error).__name__}: {error}')
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM,prior_handler)
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
