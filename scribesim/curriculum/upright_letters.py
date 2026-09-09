"""Deterministic shared upright nominal preview; no fitting or admission."""

import argparse
import copy
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.evofit.connected_contract import SCHEMA
from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide, validate_gestures
from scribesim.evo.nib_contact import ContactSample, VERSION, contact_corners
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = ROOT / 'shared/training/konrad_hand_recovery/stroke_gestures_v2/letters'
SOURCE = BASE / 'validation/run-001/seed-7/first/candidate.json'
SOURCE_SHA256 = 'e3c6e0a41374ada0ac15085df7100a8fbbc2ee855cddc71c9c2df93a84a74ff9'
SOURCE_OBJECT_SHA256 = '73c17320af9b418bb148abe22a105fa030c35d36a605da12504bb20e441cd863'
REPORT_SHA256 = 'bd3def56ffb24c9541815d3234cceddb31d21453331f2a6764f95c009026b28e'
FRAME = [-3, 20, 2, 13]
COLORS = {'stem': '#2768bd', 'rise': '#c05d00', 'upper-return': '#913f9e', 'lower-return': '#008375'}


def load_source():
    if digest(SOURCE) != SOURCE_SHA256 or digest(BASE / 'validation/run-001/report.json') != REPORT_SHA256:
        raise ValueError('Changed archived source; no implicit admission refresh')
    return json.loads(SOURCE.read_text())


def extrema(curves, axis):
    values = []
    for points in np.asarray(curves)[:, :, axis]:
        polynomial = [-points[0]+3*points[1]-3*points[2]+points[3],
                      3*points[0]-6*points[1]+3*points[2], -3*points[0]+3*points[1], points[0]]
        parameters = [0, 1] + [float(root.real) for root in np.roots(np.polyder(polynomial))
                              if abs(root.imag) < 1e-12 and 0 < root.real < 1]
        values.extend(np.polyval(polynomial, parameters))
    return float(min(values)), float(max(values))


def primitive(cubic, provenance):
    cubic = np.asarray(cubic, dtype=float)
    directions = [cubic[1]-cubic[0], cubic[-1]-cubic[-2]]
    return {'cubics': [cubic.tolist()], 'entry': (directions[0]/np.linalg.norm(directions[0])).tolist(),
            'exit': (directions[1]/np.linalg.norm(directions[1])).tolist(), 'closed': False, 'provenance': provenance}


def stroke(name, offset=(0, 0), scale=1, transition='smooth'):
    return {'primitive': name, 'offset': list(offset), 'scale': float(scale), 'rotation_deg': 0, 'transition': transition}


def make_model(source):
    if object_digest(source) != SOURCE_OBJECT_SHA256:
        raise ValueError('Changed pinned source candidate')
    model = copy.deepcopy(source)
    model.update(schema_version=SCHEMA, scope='upright-shared-preview-v1; unaccepted synthetic nominal construction',
                 migration_source_sha256=object_digest(source))
    stem = copy.deepcopy(source['primitives']['stem'])
    stem.update({key: value for key, value in primitive(stem['cubics'][0], stem['provenance']).items() if key in {'entry', 'exit'}})
    old_rows = {letter: compile_gestures(letter, source)['strokes'] for letter in 'nu'}
    upper = np.array(next(row['cubics'][0] for row in old_rows['n'] if row['primitive'] == 'upper-return'))
    lower = np.array(next(row['cubics'][0] for row in old_rows['u'] if row['primitive'] == 'lower-return'))
    upper[:, 0] -= upper[0, 0]
    lower[:, 0] -= lower[0, 0]
    entry = upper[1]-upper[0]
    rise_end = np.array([.08, upper[0, 1]])
    rise = np.array([[0, 0], [-.008, .216], rise_end-entry/np.linalg.norm(entry)*.06, rise_end])
    upper[2, 0] = upper[-1, 0] - stem['entry'][0]/stem['entry'][1]*(upper[-1, 1]-upper[2, 1])
    lower[1, 0] = stem['exit'][0]/stem['exit'][1]*(lower[1, 1]-lower[0, 1])
    lower[2, 0] = lower[-1, 0] - rise[1, 0]/rise[1, 1]*(lower[-1, 1]-lower[2, 1])
    note = 'deterministic upright preview v1; no fitting or historical/physical admission'
    model['primitives'] = {'stem': stem, 'rise': primitive(rise, note),
                           'upper-return': primitive(upper, note), 'lower-return': primitive(lower, note)}
    width = float(.08+upper[-1, 0])
    rise_scale = float((1-lower[-1, 1])/rise[-1, 1])
    under_width = float(lower[-1, 0]+.08*rise_scale)
    model['gestures'] = {
        'stem': {'action': 'fixed', 'strokes': [stroke('stem', transition='start')]},
        'overturn': {'action': 'fixed', 'strokes': [stroke('rise', transition='start'),
            stroke('upper-return', (.08, 0)), stroke('stem', (width, 0), upper[-1, 1])]},
        'underturn': {'action': 'fixed', 'strokes': [stroke('stem', (0, lower[0, 1]), 1-lower[0, 1], 'start'),
            stroke('lower-return'), stroke('rise', (lower[-1, 0], lower[-1, 1]), rise_scale)]}}
    for letter, recipe in model['recipes'].items():
        names = {'n': ['stem', 'overturn'], 'u': ['underturn', 'stem'], 'm': ['overturn', 'overturn']}[letter]
        second = {'n': 0, 'u': under_width, 'm': width}[letter]
        recipe['gestures'] = [{'gesture': name, 'scale': 1, 'rotation_deg': 0,
            'offset': [-.2+(second if index else 0), 0], 'transition': 'corner' if index else 'start',
            'overlap_with': [0] if index else []} for index, name in enumerate(names)]
    validate_gestures(model)
    return model


def points(cubic, count=257):
    parameter = np.linspace(0, 1, count)[:, None]
    controls = np.asarray(cubic)
    return ((1-parameter)**3*controls[0] + 3*(1-parameter)**2*parameter*controls[1]
            + 3*(1-parameter)*parameter**2*controls[2] + parameter**3*controls[3])


def measure(model):
    measurements = {}
    for letter in 'num':
        rows = compile_gestures(letter, model)['strokes']
        values, distances = [], []
        for index, row in enumerate(rows):
            cubic = np.asarray(row['cubics'][0])
            chord = cubic[-1]-cubic[0]
            parameter = np.linspace(0, 1, 257)[:, None]
            differences = np.diff(cubic, axis=0)
            tangents = 3*((1-parameter)**2*differences[0] + 2*(1-parameter)*parameter*differences[1] + parameter**2*differences[2])
            angles = np.degrees(np.arctan2(tangents[:, 0], np.abs(tangents[:, 1])))
            values.append({'primitive': row['primitive'], 'occurrence_id': row['occurrence_id'],
                'primitive_sha256': row['primitive_sha256'], 'chord_deg_from_vertical': math.degrees(math.atan2(chord[0], abs(chord[1]))),
                'sampled_tangent_deg_min': float(angles.min()), 'sampled_tangent_deg_max': float(angles.max())})
            if row['primitive'] == 'rise':
                neighbors = [rows[neighbor] for neighbor in (index-1, index+1) if 0 <= neighbor < len(rows)
                             and rows[neighbor]['primitive'] == 'stem']
                for neighbor in neighbors:
                    upward, downward = points(cubic), points(neighbor['cubics'][0])[::-1]
                    heights = np.linspace(.2, .7, 101)
                    distances.append(float(np.max(np.abs(np.interp(heights, upward[:, 1], upward[:, 0])
                        - np.interp(heights, downward[:, 1], downward[:, 0])))*model['x_height_mm']))
        bounds = extrema([curve for row in rows for curve in row['cubics']], 1)
        measurements[letter] = {'strokes': values, 'baseline': bounds[0], 'x_height': bounds[1],
            'body_stem_rise_max_horizontal_separation_mm': max(distances, default=0),
            'paired_rise_count': len(distances), 'clearance_scope': 'Adjacent stem/rise only, y=0.2..0.7 xheight; initial m rise has no adjacent stem. Horizontal centerline separation, not blank ink clearance.',
            'contact_runs': len({row['contact_run_id'] for row in rows}) if model['schema_version'] == SCHEMA else None}
    return measurements


def nominal(text, model, frame, *, dpi):
    bundle = gesture_guide(text, model, step_mm=.005)
    trajectory = [ContactSample(float(sample.x_mm), float(sample.y_mm), sample.contact, .45,
                               .5 if sample.contact else 0, 40) for sample in bundle.guide.samples]
    left, right, top, bottom = frame
    corners = [point for sample in trajectory if sample.contact for point in contact_corners(sample)]
    if not all(left <= point[0] <= right and top <= point[1] <= bottom for point in corners):
        raise ValueError('Nominal ink outside measurement frame')
    return paint_trajectory(trajectory, frame, dpi=dpi, contact_version=VERSION)


def path_svg(rows, frame, *, title):
    left, right, top, bottom = frame
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{left} {top} {right-left} {bottom-top}" role="img" aria-label="{title}">',
             '<defs><marker id="arrow" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5" fill="context-stroke"/></marker></defs>',
             f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="#faf7ed"/>']
    for height in (6.5, 10):
        parts.append(f'<path d="M {left} {height} H {right}" stroke="#b9b2a1" stroke-width=".015" stroke-dasharray=".12 .08"/>')
    for index, row in enumerate(rows):
        for cubic in row['cubics']:
            physical = np.asarray(cubic)*[3.5, -3.5]+[0, 10]
            coordinates = [' '.join(map(str, point)) for point in physical]
            color = COLORS[row['primitive']]
            parts.append(f'<path d="M {coordinates[0]} C {coordinates[1]} {coordinates[2]} {coordinates[3]}" fill="none" stroke="{color}" stroke-width=".028"/>')
            samples = points(physical, 21)
            before, after = samples[9], samples[11]
            parts.append(f'<path d="M {before[0]} {before[1]} L {after[0]} {after[1]}" stroke="{color}" stroke-width=".028" marker-end="url(#arrow)"/>')
            parts.append(f'<text x="{samples[7,0]+.06}" y="{samples[7,1]}" font-size=".19" fill="{color}">{index+1}</text>')
    return '\n'.join(parts+['</svg>'])


def build(output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty preview directory')
    source = load_source()
    model = make_model(source)
    all_controls = np.array([point for program in (source, model) for letter in 'num'
        for row in compile_gestures(letter, program)['strokes'] for cubic in row['cubics'] for point in cubic])*[3.5, -3.5]+[0, 10]
    detail = [float(all_controls[:,0].min()-.6), float(all_controls[:,0].max()+.6),
              float(all_controls[:,1].min()-.6), float(all_controls[:,1].max()+.6)]
    output.mkdir(parents=True, exist_ok=True)
    write_json(output/'candidate.json', model)
    containment, timeline = [], {}
    for letter in 'num':
        timeline[letter] = {}
        for arm, program in [('prior', source), ('proposed', model)]:
            for view, frame, dpi in [('full', FRAME, 900), ('detail', detail, 1800)]:
                pixels = nominal(letter, program, frame, dpi=dpi)
                Image.fromarray(pixels).save(output/f'{letter}-{arm}-{view}.png')
                containment.append({'letter': letter, 'arm': arm, 'view': view, 'frame_mm': frame, 'dpi': dpi, 'contained': True})
            bundle = gesture_guide(letter, program, step_mm=.005)
            runs = []
            for sample in bundle.guide.samples:
                state = 'pen down' if sample.contact else 'pen up'
                if not runs or runs[-1] != state:
                    runs.append(state)
            timeline[letter][arm] = runs
        rows = compile_gestures(letter, model)['strokes']
        (output/f'{letter}-paths.svg').write_text(path_svg(rows, detail, title=f'{letter}: proposed shared stroke paths and direction'))
    isolated = []
    for index, (name, definition) in enumerate(model['primitives'].items()):
        isolated.append({'primitive': name, 'cubics': (np.array(definition['cubics'])+[index*1.1, 0]).tolist()})
    (output/'strokes.svg').write_text(path_svg(isolated, [-1, 15, 5.7, 10.7], title='Shared primitives: stem, rise, upper return, lower return'))
    isolated_trajectory = []
    for row in isolated:
        isolated_trajectory.append(ContactSample(0, 0, False, .45, 0, 40))
        for cubic in row['cubics']:
            isolated_trajectory.extend(ContactSample(float(point[0]*3.5), float(10-point[1]*3.5), True, .45, .5, 40)
                                       for point in points(cubic, 1025))
    isolated_frame = [-1, 15, 5.7, 10.7]
    if not all(-1 <= horizontal <= 15 and 5.7 <= vertical <= 10.7 for sample in isolated_trajectory if sample.contact
               for horizontal, vertical in contact_corners(sample)):
        raise ValueError('Isolated primitive ink outside frame')
    Image.fromarray(paint_trajectory(isolated_trajectory, isolated_frame, dpi=1800, contact_version=VERSION)).save(output/'strokes-ink.png')
    containment.append({'letter': 'isolated primitives, not a recipe', 'arm': 'proposed', 'view': 'ink',
                        'frame_mm': isolated_frame, 'dpi': 1800, 'contained': True})
    report = {'version': 'upright-shared-preview-v1', 'source_file_sha256': SOURCE_SHA256,
        'source_report_sha256': REPORT_SHA256, 'candidate_sha256': digest(output/'candidate.json'),
        'candidate_object_sha256': object_digest(model), 'proposed_parameters': {'rise_dx_xheight': .08, 'rise_entry_handle': [-.008, .216], 'rise_exit_handle_length_xheight': .06},
        'parameter_status': 'deterministic design proposal, not owner-approved tolerances',
        'source_identities': {str(path.relative_to(ROOT)): digest(path) for path in [Path(__file__),
            ROOT/'scribesim/evofit/stroke_gestures.py', ROOT/'scribesim/evofit/stroke_language.py',
            ROOT/'scribesim/evofit/connected_contract.py', ROOT/'scribesim/handvalidate/bridge.py',
            ROOT/'scribesim/evo/nib_contact.py', ROOT/'scribesim/evo/renderer.py']},
        'measurements': measure(model), 'prior_measurements': measure(source), 'containment': containment,
        'contact_timeline': timeline, 'timeline_scope': 'Ordered nominal contact states, not measured durations or actual motion',
        'stem_geometry_unchanged': model['primitives']['stem']['cubics'] == source['primitives']['stem']['cubics'],
        'turn_tradeoff': 'Upper return retains all y controls, endpoint width and first handle; exit-handle x changes for the unrotated stem tangent. Lower return retains y controls and width; both handle x values change. Upper return curvature is not identical.',
        'optimization_evaluations': 0, 'physical_executions': 0, 'targets_created': 0,
        'owner_review': 'pending', 'S2_accepted': False, 'real_accepted': False, 'context_training_allowed': False}
    write_json(output/'owner-review.json', {'status': 'pending', 'candidate_sha256': report['candidate_sha256'],
        'letters': {letter: {'verdict': 'pending', 'notes': None} for letter in 'num'}, 'reviewer': None,
        'questions': ['Are upstrokes upright and close enough to stems?', 'Are descents and the u underturn upright enough?',
                      'Is the adjusted n overturn acceptable?', 'Are width and fixed-tool overlap acceptable?'],
        'S2_accepted': False, 'context_training_allowed': False})
    sections = []
    for letter in 'num':
        states = timeline[letter]
        sections.append(f'''<section><h2>{letter}</h2><div class="pair">
<figure><img class="ink" data-prefix="{letter}-prior" src="{letter}-prior-detail.png" alt="Archived {letter}, nominal ink"/><figcaption>Archived construction — nominal ink</figcaption></figure>
<figure><img class="ink" data-prefix="{letter}-proposed" src="{letter}-proposed-detail.png" alt="Proposed {letter}, nominal ink"/><figcaption>Proposed construction — nominal ink</figcaption></figure></div>
<p class="timeline">Old: {' → '.join(states['prior'])}<br/>Proposed: {' → '.join(states['proposed'])} throughout the letter.</p>
<details><summary>Shared stroke paths, order and direction</summary><img src="{letter}-paths.svg" alt="{letter} shared stroke decomposition"/></details></section>''')
    (output/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Upright shared strokes — CURRICULUM-015</title><style>
body{font:17px/1.5 system-ui;background:#faf7ef;color:#282d31;max-width:1180px;margin:auto;padding:24px}h1{line-height:1.15}h2{font-size:30px}
.notice{background:#fff0d1;padding:18px;border-left:5px solid #c05d00}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0}img{width:100%;height:auto}figcaption{font-weight:600}section{border-top:1px solid #cabfae;margin-top:28px;padding-top:8px}
button{font:inherit;padding:10px 16px;cursor:pointer}.timeline{font-family:monospace;background:#e8f2ed;padding:12px}summary{cursor:pointer}a{color:#185b9d}@media(max-width:650px){.pair{grid-template-columns:1fr}body{padding:15px}}
</style><h1>Upright strokes. Pen stays down.</h1><p>CURRICULUM-015 · shared vocabulary → n / u / m</p>
<p class="notice"><strong>Nominal design preview — awaiting your review.</strong> No fitting, actual hand simulation or acceptance run. Old and proposed ink use the same fixed nib, pressure and physical scale. These are construction comparisons, not independent targets.</p>
<p>Stem cubic geometry is unchanged. Upstroke bodies are more upright; the final rise still turns toward the arch. The n cap keeps its height profile and width, but its exit handle changes to meet the upright stem. Letter widths narrow; advance spacing is unchanged. Fixed-tool retracing may remain visually heavy.</p>
<p><button id="view" type="button">Show full physical frame</button> Detail uses a shared, uncropped ink-containing frame at 1800 DPI; full views use 900 DPI. No per-letter stretching.</p>
'''+'\n'.join(sections)+'''
<section><h2>The four shared primitives</h2><p>Stem · rise · upper return · lower return. Isolated nominal ink, then vector centerlines at the same physical scale. These tiles are diagnostics, not an extra letter recipe.</p><img src="strokes-ink.png" alt="Nominal ink of four isolated shared primitives"/><p>Blue: stem · orange: rise · purple: upper return · teal: lower return. Arrows show writing direction; vector line width does not represent ink thickness.</p><img src="strokes.svg" alt="Four isolated shared stroke primitives"/></section>
<section><h2>Your review is the next gate</h2><p>For each n/u/m, say keep or repair: upstroke angle and stem proximity, descending slant, turn shape, width and overlap. Is the adjusted n cap still acceptable? We will not fit or run scored physical validation before this review.</p><p><a href="candidate.json">Frozen candidate</a> · <a href="report.json">Measurements and provenance</a> · <a href="owner-review.json">Pending owner review</a></p></section>
<script>let full=false;document.getElementById('view').onclick=()=>{full=!full;document.querySelectorAll('.ink').forEach(image=>image.src=image.dataset.prefix+'-'+(full?'full':'detail')+'.png');document.getElementById('view').textContent=full?'Show enlarged detail':'Show full physical frame';};</script></html>''')
    report['artifacts'] = {path.name: digest(path) for path in sorted(output.iterdir()) if path.name not in {'report.json', 'owner-review.json'}}
    write_json(output/'report.json', report)
    return report


def verify_preview(directory):
    directory = Path(directory)
    report = json.loads((directory/'report.json').read_text())
    actual = {path.name for path in directory.iterdir()} - {'report.json', 'owner-review.json'}
    if actual != set(report['artifacts']):
        raise ValueError('Incomplete preview artifact inventory')
    for name, checksum in report['artifacts'].items():
        if Path(name).name != name or digest(directory/name) != checksum:
            raise ValueError('Changed preview artifact')
    if digest(directory/'candidate.json') != report['candidate_sha256']:
        raise ValueError('Changed preview candidate')
    for name, checksum in report['source_identities'].items():
        path = (ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != checksum:
            raise ValueError('Stale preview source identity')
    if any(report[key] != 0 for key in ('optimization_evaluations', 'physical_executions', 'targets_created')) or any(
            report[key] is not False for key in ('S2_accepted', 'real_accepted', 'context_training_allowed')):
        raise ValueError('Overstated preview scope')
    review = json.loads((directory/'owner-review.json').read_text())
    if review['candidate_sha256'] != report['candidate_sha256']:
        raise ValueError('Stale owner review binding')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.output)


if __name__ == '__main__':
    main()
