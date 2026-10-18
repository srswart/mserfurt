"""Resume the unchanged two-candidate study after dual-source readiness."""

import argparse
import html
import json
import math
from pathlib import Path
import shutil
import signal
import subprocess
import time

from scripts import nu_merge_readiness as readiness
from scripts import nu_mutual_construction as program


OUTPUT = program.BASE/'continuation-001'
VERSION = 'nu-mutual-continuation-v1'


def write(name, payload, replace=False):
    if not isinstance(payload, bytes):
        payload = payload.encode()
    destination = OUTPUT/name
    total = sum(path.stat().st_size for path in program.BASE.rglob('*') if path.is_file() and path != destination)
    if total+len(payload) > program.MAX_BYTES-65536:
        raise ValueError('Combined study evidence ceiling reached')
    if not replace:
        with destination.open('xb') as stream:
            stream.write(payload)
    else:
        temporary = OUTPUT/'.report.tmp'
        with temporary.open('wb') as stream:
            stream.write(payload)
            stream.flush()
        temporary.replace(destination)


def save(report):
    write('report.json', json.dumps(report, indent=2, allow_nan=False)+'\n', replace=True)


def candidate_drawing(document, owner=None):
    renderer = program.history.renderer
    pieces = [piece for piece in document['retained'] if owner is None or ('n' if piece['canonical_owner']['letter'] == 0 else 'u') == owner]
    pieces += [piece for piece in document['boundary'] if owner is None or piece['owner'] == owner]
    return [{'profile': piece['contact_profile'],
             'polygons': renderer.polygons(piece['cubics_mm'], piece['contact_profile'], document['profiles'])}
            for piece in pieces]


def svg_board(rows, frame):
    renderer = program.history.renderer
    left, top, right, bottom = frame
    output = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="{380*len(rows)}"><rect width="100%" height="100%" fill="#fffdf8"/>']
    for index, row in enumerate(rows):
        offset = 380*index
        output.append(f'<text x="30" y="{offset+32}" font-family="sans-serif" font-size="23" fill="#26322e">{html.escape(row["label"])}</text>')
        if row.get('status'):
            output.append(f'<text x="50" y="{offset+100}" font-family="sans-serif" font-size="21">{html.escape(row["status"])} — not rendered</text>')
            continue
        output.append(f'<svg x="25" y="{offset+45}" width="1450" height="320" viewBox="{left} {top} {right-left} {bottom-top}">')
        for vertical in (0., -program.HEIGHT):
            output.append(f'<path d="M{left},{vertical} H{right}" stroke="#cfc8bb" stroke-width=".012" stroke-dasharray=".08 .08"/>')
        if row.get('ghost'):
            output.append('<g opacity=".22">'+renderer.paths(row['ghost'])+'</g>')
        output.append(renderer.paths(row['drawing'], colored=row.get('colored', False)))
        output.append(row.get('sequence', ''))
        output.append('</svg>')
    return ''.join(output)+'</svg>'


def sequence(document):
    output = []
    for number, piece in enumerate(document['boundary'], 1):
        segments = [segment for cubic in piece['cubics_mm'] for segment in program.clearance.flatten(cubic)]
        lengths = [math.dist(*segment) for segment in segments]
        target, traveled = sum(lengths)/2, 0.
        for (start, end), length in zip(segments, lengths):
            if traveled+length >= target:
                ratio = (target-traveled)/length
                position = [start[axis]+ratio*(end[axis]-start[axis]) for axis in (0, 1)]
                angle = math.degrees(math.atan2(-(end[1]-start[1]), end[0]-start[0]))
                output.append(f'<path d="M-.08,-.04 L.08,0 L-.08,.04 Z" fill="#b22c3d" transform="translate({position[0]},{-position[1]}) rotate({angle})"/>')
                output.append(f'<text x="{position[0]+.08}" y="{-position[1]-.06}" font-size=".13" fill="#b22c3d">{number}</text>')
                break
            traveled += length
    return ''.join(output)


def render(report):
    admitted = [entry for entry in report['candidates'] if entry['status'] == 'admitted']
    if not admitted:
        write('index.html', program.status_page(report))
        report['render_status'] = 'not_applicable_no_admitted_candidates'
        return
    renderer = program.history.renderer
    saved = program.source.read_json(program.frozen.SAVED)
    canonical_model = program.source.read_json(program.source.CANDIDATE)
    canonical, old = renderer.drawings(saved, canonical_model)
    rows = [{'label': 'Canonical — unconnected control', 'drawing': canonical},
            {'label': 'Old bridge — owner-rejected relative reference, not target', 'drawing': old}]
    drawings = [canonical, old]
    for entry in report['candidates']:
        if entry['status'] != 'admitted':
            rows.append({'label': entry['brief'], 'status': entry['status']})
            continue
        if program.actions.object_digest(entry['candidate']) != entry['candidate_sha256']:
            raise ValueError('Saved candidate changed before rendering')
        drawing = candidate_drawing(entry['candidate'])
        drawings.append(drawing)
        rows.append({'label': entry['brief']+' — nominal geometry, not physical ink', 'drawing': drawing})
    frame = renderer.frame(drawings)
    overlay_rows, sequence_rows = [], []
    for entry in admitted:
        for owner, canonical_owner in [('n', canonical[:4]), ('u', canonical[4:])]:
            overlay_rows.append({'label': entry['brief']+' '+owner+' — faint canonical / contextual stroke colors',
                                 'ghost': canonical_owner, 'drawing': candidate_drawing(entry['candidate'], owner), 'colored': True})
        sequence_rows.append({'label': entry['brief']+' — pen-down sequence; arrows at half segment arc, NOT physical timing',
                              'drawing': candidate_drawing(entry['candidate']), 'colored': True,
                              'sequence': sequence(entry['candidate'])})
    converter = shutil.which('rsvg-convert')
    if not converter:
        raise ValueError('PNG converter unavailable; no alternate rendering retry')
    for name, selected in [('comparison', rows), ('overlays', overlay_rows), ('sequence', sequence_rows)]:
        write(name+'.svg', svg_board(selected, frame))
        raster = subprocess.run([converter, str(OUTPUT/(name+'.svg'))], capture_output=True, check=True, timeout=300)
        write(name+'.png', raster.stdout)
        report['renders'] += 1
    report['comparison_frame_mm_y_down'] = frame
    report['render_status'] = 'nominal_review_ready'
    page = program.status_page(report)
    figures = ''.join(f'<h2>{name.title()}</h2><a href="{name}.svg"><img style="width:100%" src="{name}.svg" alt="{name}"></a>' for name in ('comparison', 'overlays', 'sequence'))
    page = page.replace('This is a technical status board, not a visual comparison or owner acceptance.',
                        'Only admitted candidates are drawn; owner preference and physical acceptance remain open.')
    page = page.replace('</html>', figures+'<h2>Review</h2><p>Assess n identity, u identity, flow, entry/downstroke relation, thinness, shelves/bulges and whether both letters respond. Neither and indistinguishable are valid outcomes.</p></html>')
    write('index.html', page)


def run(receipt_sha256):
    if shutil.disk_usage(program.BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    readiness.verify_receipt(receipt_sha256)
    OUTPUT.mkdir(exist_ok=False)
    report = {'version': VERSION, 'status': 'stopped', 'readiness_report_sha256': receipt_sha256,
              'continuation_approval_sha256': readiness.digest(readiness.APPROVAL),
              'stopped_report_sha256': readiness.STOP_PIN, 'candidates': [], 'new_candidates': 0,
              'renders': 0, 'fitting_evaluations': 0, 'physical_runs': 0, 'mu_started': False,
              'nib_rotation': False, 'automatic_retries': 0, 'code_sha256': readiness.digest(Path(__file__)),
              'tests_sha256': readiness.digest(program.ROOT/'tests/test_nu_mutual_resume.py'),
              'original_constructor_sha256': readiness.read(readiness.STOP)['code_sha256']}
    def timeout_handler(signum, frame):
        raise TimeoutError('Approved phase wall-time ceiling reached')
    previous_handler = signal.signal(signal.SIGALRM, timeout_handler)
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        save(report)
        model = program.source.read_json(program.source.CANDIDATE)
        before = program.actions.object_digest(model)
        for name in ('J1', 'J2'):
            entry = {'brief': name, 'status': 'construction_started'}
            report['candidates'].append(entry)
            save(report)
            candidate = program.construct(model, name)
            entry.update(candidate=candidate, candidate_sha256=program.actions.object_digest(candidate), status='constructed')
            report['new_candidates'] += 1
            save(report)
            evaluation = program.inspect(candidate, model)
            entry.update(evaluation=evaluation, status=evaluation['status'])
            save(report)
        if program.actions.object_digest(model) != before:
            raise ValueError('Canonical source mutated')
        readiness.verify_receipt(receipt_sha256)
        report.update(status='geometry_checked', source_and_authority_verified_after=True)
    except (ValueError, OSError, TimeoutError, program.bounds.Unresolved) as error:
        report.update(status='stopped', error=str(error))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        report['construction_check_seconds'] = time.monotonic()-started
        save(report)
    render_started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        if report['status'] == 'geometry_checked':
            render(report)
            report['status'] = 'nominal_review_ready' if any(entry['status'] == 'admitted' for entry in report['candidates']) else 'no_candidate_admitted'
        else:
            write('index.html', program.status_page(report))
        readiness.verify_receipt(receipt_sha256)
    except (ValueError, OSError, TimeoutError, subprocess.SubprocessError) as error:
        report.update(status='stopped', error=str(error))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        report['render_phase_seconds'] = time.monotonic()-render_started
        report['artifacts'] = {path.name: readiness.digest(path) for path in OUTPUT.iterdir() if path.is_file() and path.name != 'report.json'}
        save(report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--readiness-sha256', required=True)
    options = parser.parse_args()
    result = run(options.readiness_sha256)
    print(json.dumps({'status': result['status'], 'new_candidates': result['new_candidates'],
                      'construction_check_seconds': result['construction_check_seconds'],
                      'render_phase_seconds': result['render_phase_seconds']}))
