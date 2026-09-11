"""Frozen canonical/old-bridge/derived-entry nominal comparison only."""

import argparse
import html
import json
from pathlib import Path
import shutil
import signal
import subprocess
import time

from scripts import nu_local_contact as gate
from scripts import nu_nominal_review as renderer


ROOT=gate.ROOT
BASE=gate.BASE
OUTPUT=BASE/'nominal-001'
VERSION='nu-three-way-nominal-v1'
REPORT_PIN='2531730f4839d2f9c6fce32484406f6e5d858ad4a4af80da3f77143b851ede3b'
RENDERER_PIN='f10d6c4bc5f9efa054bce561bb4eeb6bd65ff4e0ef71e36d393b131505ff081e'
LABELS=('1 · Canonical — unconnected n + u','2 · Old bridge — frozen thin connector','3 · Derived entry — recovery, rise and crown approach')


def approval_record():
    return {'version':VERSION,'owner_quote':'Please generate the **canonical / old-bridge / derived-entry visual comparison** for your review.',
            'classification_report_sha256':REPORT_PIN,'renderer_sha256':RENDERER_PIN,
            'seconds':300,'max_output_bytes':25*1024**2,'minimum_free_bytes':5*1024**3,
            'svg_count':2,'png_count':2,'html_count':1,'retries':0,'new_geometry':False,
            'fitting':False,'physical_runs':0,'mu':False}


def verify():
    if gate.source.read_json(BASE/'nominal-approval.json')!=approval_record():
        raise ValueError('Exact three-way nominal approval required')
    if gate.actions.digest(gate.OUTPUT/'report.json')!=REPORT_PIN or gate.actions.digest(Path(renderer.__file__))!=RENDERER_PIN:
        raise ValueError('Frozen report/renderer changed')
    report=gate.source.read_json(gate.OUTPUT/'report.json')
    if not report['revised_geometry_contact_pass'] or report['external_contact']['status']!='pass' or report['local_contact']['status']!='pass':
        raise ValueError('Complete geometry/contact admission required')
    for path,key in ((Path(gate.__file__),'code_sha256'),(ROOT/'tests/test_nu_local_contact.py','tests_sha256')):
        if gate.actions.digest(path)!=report[key]:
            raise ValueError('Frozen classifier implementation changed')
    gate.verify()


def drawings():
    saved=gate.source.read_json(gate.previous.frozen.SAVED)
    derived=gate.source.read_json(gate.measurement.CANDIDATE)
    canonical,old=renderer.drawings(saved,gate.source.read_json(gate.source.CANDIDATE))
    new=[{'profile':piece['contact_profile'],'polygons':renderer.polygons(piece['cubics_mm'],piece['contact_profile'],derived['profiles'])}
         for piece in derived['retained']+derived['boundary']]
    if renderer.paths(old)==renderer.paths(new):
        raise ValueError('Derived comparison indistinguishable in vector geometry')
    if old[:-2]!=new[:-2] or old[-1]!=new[-1]:
        raise ValueError('Retained bodies or T/S drawing changed')
    return [canonical,old,new],derived


def board(drawings,labels,colors=False):
    left,top,right,bottom=renderer.frame(drawings)
    height=380*len(drawings)
    output=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="{height}" viewBox="0 0 1500 {height}"><rect width="100%" height="100%" fill="#fffdf8"/>']
    for index,(drawing,label) in enumerate(zip(drawings,labels)):
        offset=380*index
        output.append(f'<text x="30" y="{offset+32}" font-family="sans-serif" font-size="24" fill="#252c35">{html.escape(label)}</text>')
        output.append(f'<svg x="25" y="{offset+45}" width="1450" height="320" viewBox="{left} {top} {right-left} {bottom-top}">')
        for vertical in (0,-3.5):
            output.append(f'<path d="M{left},{vertical} H{right}" stroke="#cec8bb" stroke-width=".012" stroke-dasharray=".08 .08"/>')
        output.append(renderer.paths(drawing,colors))
        output.append('</svg>')
    return ''.join(output)+'</svg>'


PAGE='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nu — three-way visual review</title>
<style>body{background:#f1eee7;color:#252c35;font:18px/1.6 system-ui;margin:0}main{max-width:1200px;margin:auto;padding:30px 20px}h1{line-height:1.15;font-size:clamp(28px,4vw,44px)}img{display:block;width:100%;background:#fffdf8;border:1px solid #d5d0c4;border-radius:12px}a{color:#166e68}.note{background:#fffdf8;padding:18px;border-left:4px solid #147b77}.tag{color:#7051b5;font-size:13px;letter-spacing:.12em;font-weight:bold}</style>
<main><div class="tag">NOMINAL CONTACT GEOMETRY · NOT SIMULATED INK</div><h1>Canonical / old bridge / derived entry</h1>
<p>All three rows share scale, letter placement and a complete frame. Only the thin entry changes between rows 2 and 3; letter bodies and broad departure/receiving spans stay fixed.</p>
<a href="comparison.svg" target="_blank"><img src="comparison.svg" alt="Canonical unconnected nu, old bridge and derived entry at identical scale"></a>
<p><a href="comparison.svg" target="_blank">Open scalable comparison ↗</a> · <a href="comparison.png" target="_blank">PNG</a></p>
<h2>Contact spans: old versus derived</h2><p>Dark: retained bodies. Orange: unchanged departure taper. Teal: thin entry. Purple: unchanged receiving transition. Colors are explanatory, not a different ink treatment.</p>
<a href="detail.svg" target="_blank"><img src="detail.svg" alt="Color-keyed old and derived contact constructions"></a>
<p><a href="detail.svg" target="_blank">Open scalable detail ↗</a></p>
<h2>Review questions</h2><ol><li>Does the new upward recovery follow naturally from n?</li><li>Does its rise read as entering u, rather than an added bridge?</li><li>Is the change of direction near the lower part too abrupt, despite geometric tangent continuity?</li></ol>
<div class="note">Both candidates are frozen. The same finite 0.45 × 0.02 mm nib and full/corner/full contact renderer are used throughout. This nominal sweep does not model pressure response, ink accumulation, physical timing or fatigue. Passing geometry/contact checks does not establish visual quality.</div>
<p><a href="review.md">Assistant visual review</a> · <a href="report.json">Rendering evidence</a> · <a href="../local-contact-review-001/README.md">Classification evidence</a></p><p>Owner preference remains open; mu and physical runs are not started.</p></main></html>'''


def run():
    if shutil.disk_usage(BASE).free<5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started=time.monotonic()
    report={'version':VERSION,'status':'stopped','accepted':False,'new_geometries':0,'fitting_evaluations':0,'physical_runs':0,'mu_started':False,'files':{}}
    def timeout_handler(signum,frame):
        raise TimeoutError('300-second nominal ceiling')
    handler=signal.signal(signal.SIGALRM,timeout_handler)
    signal.alarm(300)
    def write(name,payload):
        if sum(path.stat().st_size for path in OUTPUT.iterdir())+len(payload)>25*1024**2-65536:
            raise ValueError('Output ceiling')
        with (OUTPUT/name).open('xb') as stream:
            stream.write(payload)
    try:
        with gate.source.evidence.read_only_guard():
            verify()
            rows,document=drawings()
            report.update(approval=approval_record(),code_sha256=gate.actions.digest(Path(__file__)),tests_sha256=gate.actions.digest(ROOT/'tests/test_nu_three_way_review.py'),
                          frame_mm=renderer.frame(rows),retained_and_T_S_identical=True,
                          candidate_sha256=gate.actions.digest(gate.measurement.CANDIDATE),old_candidate_sha256=gate.actions.digest(gate.previous.frozen.SAVED),
                          labels=LABELS,derivation=document['derivation'])
            write('comparison.svg',board(rows,LABELS).encode())
            write('detail.svg',board(rows[1:],LABELS[1:],True).encode())
            write('index.html',PAGE.encode())
            for name in ('comparison','detail'):
                converted=subprocess.run(['rsvg-convert',str(OUTPUT/(name+'.svg')),'-w','2100'],capture_output=True,check=True,timeout=60)
                write(name+'.png',converted.stdout)
            for path in OUTPUT.iterdir():
                report['files'][path.name]=gate.actions.digest(path)
            for path,pin in {**gate.PINS,**gate.previous.frozen.PINS,**gate.previous.audit.PINS}.items():
                if gate.actions.digest(path)!=pin:
                    raise ValueError('Frozen input changed during render')
            report.update(status='nominal_packet_ready_for_review',frozen_inputs_unchanged=True)
    except Exception as error:
        report.update(error=f'{type(error).__name__}: {error}')
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM,handler)
        report['elapsed_seconds']=time.monotonic()-started
        write('report.json',(json.dumps(report,indent=2,allow_nan=False)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['generate'])
    parser.parse_args()
    print(json.dumps(run(),indent=2))
