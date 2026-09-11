"""Owner-approved frozen-nu vector comparison; no motion, fitting or ink physics."""

import argparse
from fractions import Fraction
import html
import json
import math
from pathlib import Path
import shutil
import signal
import subprocess
import time

from scripts import nu_receiving_envelope as evaluation


actions = evaluation.actions
source = evaluation.source
BASE = evaluation.BASE
OUTPUT = BASE/'nominal-001'
REPORT_PIN = '053aff33d2b767c622ea63614fd4727a394c1c6bce365740d007915c7e163b8f'
VERSION = 'nu-nominal-vector-review-v1'
MAX_BYTES = 25*1024**2
COLORS = {'full': '#252c35', 'departure': '#b85420', 'core': '#147b77', 'receiving': '#7051b5'}


def approval_record():
    return {'version': VERSION, 'owner_quote': 'yes',
            'approved_offer': 'Generate standalone n/u beside connected nu, plus an enlarged connection detail, using frozen geometry without refitting.',
            'report_sha256': REPORT_PIN, 'candidate_sha256': evaluation.PINS[evaluation.SAVED],
            'seconds': 300, 'max_output_bytes': MAX_BYTES, 'minimum_free_bytes': 5*1024**3,
            'svg_count': 2, 'png_count': 1, 'html_count': 1, 'retries': 0,
            'new_geometry': False, 'fitting': False, 'physical_runs': 0, 'mu': False}


def verify():
    approval = source.read_json(BASE/'nominal-approval.json')
    if approval != approval_record():
        raise ValueError('Exact nominal approval required')
    if actions.digest(evaluation.OUTPUT/'report.json') != REPORT_PIN:
        raise ValueError('Passing report changed')
    report = source.read_json(evaluation.OUTPUT/'report.json')
    if not report['revised_geometry_pass'] or any(check['status'] != 'pass' for check in report['checks'].values()):
        raise ValueError('Every structural/contact gate must pass')
    for path, pin in ((Path(evaluation.__file__), report['code_sha256']),
                      (evaluation.ROOT/'tests/test_nu_receiving_envelope.py', report['tests_sha256'])):
        if actions.digest(path) != pin:
            raise ValueError('Frozen evaluation implementation changed')
    evaluation.verify(source.read_json(evaluation.APPROVAL))


def hull(points):
    unique = sorted(set(tuple(point) for point in points))
    def half(sequence):
        result = []
        for point in sequence:
            while len(result) >= 2 and evaluation.original.capability.clearance.cross(result[-2], result[-1], point) <= 0:
                result.pop()
            result.append(point)
        return result
    return half(unique)[:-1]+half(reversed(unique))[:-1]


def polygons(cubics, profile, profiles):
    segments = [segment for cubic in cubics for segment in evaluation.original.capability.clearance.flatten(cubic)]
    lengths = [math.dist(*segment) for segment in segments]
    total = sum(lengths)
    if total <= 0:
        raise ValueError('Zero-length nominal path')
    traveled = 0.0
    result = []
    for index, ((start, end), length) in enumerate(zip(segments, lengths)):
        lower = traveled/total
        traveled += length
        upper = 1.0 if index == len(segments)-1 else traveled/total
        corners = []
        for point, progress in ((start, lower), (end, upper)):
            interval = actions.interpolate(profiles[profile], Fraction(str(progress)))
            corners.extend(actions.BoundaryContact(tuple(point), interval, 'physical-y-up').corners())
        result.append(hull(corners))
    return result


def drawings(saved, canonical):
    if actions.object_digest(saved) != actions.object_digest(source.read_json(evaluation.SAVED)):
        raise ValueError('Frozen candidate identity changed')
    rows = evaluation.original.capability.investigation.canonical(canonical, 'nu')['strokes']
    before = [{'profile': 'full', 'polygons': polygons([[[value*3.5 for value in point] for point in cubic]
               for cubic in row['cubics']], 'full', saved['profiles'])} for row in rows]
    after = [{'profile': piece['contact_profile'], 'polygons': polygons(piece['cubics_mm'], piece['contact_profile'], saved['profiles'])}
             for piece in saved['retained']+saved['boundary']]
    return before, after


def frame(drawings):
    points = [point for drawing in drawings for piece in drawing for polygon in piece['polygons'] for point in polygon]
    return [min(point[0] for point in points)-.5, -max(point[1] for point in points)-.5,
            max(point[0] for point in points)+.5, -min(point[1] for point in points)+.5]


def paths(drawing, colored=False):
    output = []
    for piece in drawing:
        commands = []
        for polygon in piece['polygons']:
            commands.append('M'+' L'.join(f'{horizontal:.8f},{-vertical:.8f}' for horizontal, vertical in polygon)+' Z')
        color = COLORS[piece['profile']] if colored else COLORS['full']
        output.append(f'<path fill="{color}" d="{" ".join(commands)}"/>')
    return ''.join(output)


def svg(before, after, colored=False):
    left, top, right, bottom = frame([before, after])
    width, height = right-left, bottom-top
    panel_height = 360 if not colored else 600
    panels = [('Unconnected n + u — canonical forms and placement', before),
              ('Connected nu — frozen candidate, thin corner-contact core', after)] if not colored else [
                  ('Connection detail — colored contact spans, same frozen geometry', after)]
    output = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="{len(panels)*(panel_height+65)}" viewBox="0 0 1500 {len(panels)*(panel_height+65)}">',
              '<rect width="100%" height="100%" fill="#fffdf8"/>']
    for index, (title, drawing) in enumerate(panels):
        offset = index*(panel_height+65)
        output.append(f'<text x="36" y="{offset+34}" font-family="sans-serif" font-size="23" fill="#252c35">{html.escape(title)}</text>')
        output.append(f'<svg x="30" y="{offset+50}" width="1440" height="{panel_height}" viewBox="{left} {top} {width} {height}">')
        for vertical in (0, -3.5):
            output.append(f'<path d="M{left},{vertical} H{right}" fill="none" stroke="#c9c5ba" stroke-width=".012" stroke-dasharray=".08 .08"/>')
        output.append(paths(drawing, colored))
        output.append('</svg>')
    return ''.join(output)+'</svg>'


PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Frozen nu — visual review</title><style>
body{margin:0;background:#f2efe7;color:#252c35;font:18px/1.55 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:32px 20px}h1{font-size:clamp(28px,5vw,48px);line-height:1.1}h2{margin-top:42px}.tag{font-size:13px;letter-spacing:.12em;color:#7051b5;font-weight:700}img{display:block;width:100%;background:#fffdf8;border:1px solid #d9d4c9;border-radius:12px}a{color:#176762}.note{padding:18px 22px;background:#fffdf8;border-left:4px solid #147b77}.legend{display:flex;flex-wrap:wrap;gap:22px;font-weight:650}.departure{color:#b85420}.core{color:#147b77}.receiving{color:#7051b5}li{margin:9px 0}</style>
<main><div class="tag">NOMINAL CONTACT DRAWING · NOT SIMULATED INK</div><h1>Does this thin connection feel natural?</h1>
<p>The top row shows unconnected canonical n and u. The bottom row uses the saved connected nu. Both use the same scale, placement and complete frame. No fitting, letter-body redesign or physical run.</p>
<a href="comparison.svg" target="_blank"><img src="comparison.svg" alt="Same-scale unconnected n and u above the frozen connected nu"></a>
<p><a href="comparison.svg" target="_blank">Open sharp vector comparison ↗</a> · <a href="comparison.png" target="_blank">Open PNG</a></p>
<h2>Enlarged connection detail</h2><p>Open this vector drawing in a new tab and zoom freely. Color shows contact spans, not different ink or a different candidate.</p>
<div class="legend"><span>Dark: retained bodies</span><span class="departure">Orange: departure taper (T)</span><span class="core">Teal: thin rising connection (R)</span><span class="receiving">Purple: receiving transition (S)</span></div>
<a href="detail.svg" target="_blank"><img src="detail.svg" alt="Enlarged nu with orange departure taper, teal thin core and purple receiving transition"></a>
<p><a href="detail.svg" target="_blank">Open enlarged vector detail ↗</a></p>
<h2>What to judge</h2><ol><li>Does the thin rising connection look like a plausible continuation of n into u?</li><li>Are the departure taper and receiving transition natural, or do they form awkward bulges?</li><li>Does u still read clearly as u, and does the pair feel connected rather than bridged?</li></ol>
<div class="note"><strong>This is a visual proposal, not accepted handwriting.</strong> The core uses the actual negative 10% nib interval; the departure and receiving spans taper between full and corner contact. The 0.45 × 0.02 mm rectangular footprint retains its offset and orientation. Nominal tessellation approximates arc-progress ramps; it does not model motion timing, pressure response, ink accumulation or fatigue. The tiny receiving overshoot is not exaggerated.</div>
<p><a href="report.json">Rendering evidence</a> · <a href="../receiving-envelope-review-001/README.md">Geometric-check summary</a></p><p>Mu remains unstarted. Your visual feedback comes before the next construction.</p></main></html>'''


def run():
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    report = {'version': VERSION, 'status': 'stopped', 'accepted': False, 'physical_runs': 0,
              'fitting_evaluations': 0, 'new_geometries': 0, 'mu_started': False, 'files': {}}
    def timeout_handler(signum, context):
        raise TimeoutError('300-second nominal ceiling')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    def write(name, payload):
        used = sum(path.stat().st_size for path in OUTPUT.iterdir() if path.is_file())
        if used+len(payload) > MAX_BYTES-65536:
            raise ValueError('Nominal output ceiling')
        with (OUTPUT/name).open('xb') as stream:
            stream.write(payload)
    try:
        with source.evidence.read_only_guard():
            verify()
            report.update(approval=approval_record(), code_sha256=actions.digest(Path(__file__)),
                          tests_sha256=actions.digest(evaluation.ROOT/'tests/test_nu_nominal_review.py'))
            before, after = drawings(source.read_json(evaluation.SAVED), source.read_json(source.CANDIDATE))
            report.update(common_full_frame_mm_y_down=frame([before, after]),
                          flattening_error_mm=evaluation.original.capability.clearance.ERROR,
                          arc_progress='Nominal cumulative flattened chord length; not physical timing',
                          contact='Finite rectangular full/corner/full profile, physical-y-up; reflected only for SVG',
                          polygon_counts=[sum(len(piece['polygons']) for piece in drawing) for drawing in (before, after)])
            write('comparison.svg', svg(before, after).encode())
            write('detail.svg', svg(before, after, True).encode())
            write('index.html', PAGE.encode())
            result = subprocess.run(['rsvg-convert', str(OUTPUT/'comparison.svg'), '-w', '2400'], capture_output=True, check=True, timeout=60)
            write('comparison.png', result.stdout)
            for name in ('comparison.svg', 'detail.svg', 'index.html', 'comparison.png'):
                report['files'][name] = actions.digest(OUTPUT/name)
            for path, pin in evaluation.PINS.items():
                if actions.digest(path) != pin:
                    raise ValueError('Frozen evidence changed during rendering')
            report.update(status='nominal_packet_ready_owner_review_pending', frozen_inputs_unchanged=True)
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report['elapsed_seconds'] = time.monotonic()-started
        write('report.json', (json.dumps(report, indent=2, allow_nan=False)+'\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['generate'])
    parser.parse_args()
    print(json.dumps(run(), indent=2))
