"""Level open-letter assemblies using bounded whole-gesture transforms only."""

import argparse
import copy
import gzip
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scribesim.curriculum import letter_recipes as prior, gesture_targets
from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures
from scribesim.handvalidate import standalone_stem as stem, frozen_replay as protocol
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


foundation = stem.foundation
BASE = prior.BASE / 'alignment'
SPEC_PATH = BASE / 'spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())


def identities():
    return {**prior.identities(), **stem.identities(), **{str(path.relative_to(ROOT)): digest(path)
            for path in [Path(__file__), SPEC_PATH]}}


def load_inputs():
    admitted = stem.require_readiness(stem.BASE / 'run-001', expected_report_sha256=SPEC['stem_report_sha256'], required_gestures=['stem'])
    directory = prior.BASE / 'run-001'
    if digest(directory / 'report.json') != SPEC['prior_report_sha256']:
        raise ValueError('Changed prior assembly report')
    report = json.loads((directory / 'report.json').read_text())
    frozen = json.loads((directory / 'freeze.json').read_text())
    if frozen['code_sha256'] != prior.identities() or report['status'] != 'pass' or report['S2_accepted'] is not False:
        raise ValueError('Stale or overstated prior assembly evidence')
    foundation.primitives.verify_artifacts(directory, report['artifacts'])
    path = directory / 'seed-7/shared/first/candidate.json'
    if digest(path) != SPEC['prior_candidate_sha256']:
        raise ValueError('Changed prior assembly candidate')
    old = json.loads(path.read_text())
    path = stem.prior.BASE / 'run-001/seed-7/first/candidate.json'
    candidate = json.loads(path.read_text())
    stem.require_candidate(candidate)
    if any(old[key] != candidate[key] for key in candidate if key != 'recipes'):
        raise ValueError('Detached prior lower layers')
    return {'candidate': candidate, 'prior': old, 'stem_admission': admitted}


def extrema(curves, axis):
    values = []
    for curve in np.asarray(curves, dtype=float):
        points = curve[:, axis]
        polynomial = [-points[0]+3*points[1]-3*points[2]+points[3],
                      3*points[0]-6*points[1]+3*points[2], -3*points[0]+3*points[1], points[0]]
        roots = np.roots(np.polyder(polynomial))
        parameters = [0, 1] + [float(root.real) for root in roots if abs(root.imag) < 1e-12 and 0 < root.real < 1]
        values.extend(np.polyval(polynomial, parameters).tolist())
    return min(values), max(values)


def rotation(delta):
    if not np.isfinite(delta).all() or np.linalg.norm(delta) < 1e-12:
        raise ValueError('Nondegenerate finite open-gesture chord required')
    angle = -math.atan2(delta[1], delta[0])
    degrees = math.degrees(angle)
    if not -20 <= degrees <= 20:
        raise ValueError('Chord rotation outside existing instance envelope')
    return degrees, np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])


def normalization(curves):
    curves = np.asarray(curves, dtype=float)
    if curves.ndim != 3 or curves.shape[1:] != (4, 2) or not np.isfinite(curves).all():
        raise ValueError('Finite cubic program required')
    degrees, matrix = rotation(curves[-1, -1] - curves[0, 0])
    rotated = curves @ matrix.T
    low, high = extrema(rotated, 1)
    if high - low <= 1e-12 or not .5 <= 1 / (high - low) <= 1.5:
        raise ValueError('Uniform scale outside existing instance envelope')
    scale = 1 / (high - low)
    offset = [-float(rotated[0, 0, 0]) * scale, -low * scale]
    width = float((rotated[-1, -1, 0] - rotated[0, 0, 0]) * scale)
    return {'rotation_deg': degrees, 'scale': scale, 'offset': offset, 'width': width}


def make_model(source):
    stem.require_candidate(source)
    model, transforms = copy.deepcopy(source), {}
    for name in ('underturn', 'overturn'):
        probe = copy.deepcopy(source)
        probe['recipes']['i']['gestures'][0]['gesture'] = name
        curves = [curve for row in compile_gestures('i', probe)['strokes'] for curve in row['cubics']]
        transforms[name] = normalization(curves)
    model['recipes'] = {}
    for char, definition in SPEC['recipes'].items():
        instances, horizontal = [], SPEC['origin_x']
        for index, name in enumerate(definition['gestures']):
            transform = transforms.get(name, {'scale': 1, 'rotation_deg': 0, 'offset': [0, 0], 'width': 0})
            instances.append({'gesture': name, 'scale': transform['scale'], 'rotation_deg': transform['rotation_deg'],
                'offset': [horizontal + transform['offset'][0], transform['offset'][1]],
                'transition': 'start' if index == 0 else 'lift', 'overlap_with': []})
            horizontal += transform['width']
        model['recipes'][char] = {'logical': char, 'visible': char, 'advance': definition['advance'], 'gestures': instances}
    validate_gestures(model)
    return model, transforms


def require_lineage(model, source):
    if model != make_model(source)[0]:
        raise ValueError('Only deterministic shared whole-gesture transforms are permitted')
    validate_gestures(model)


def landmarks(model):
    result = {}
    levels = {'stem': [1, 0], 'overturn': [0, 0], 'underturn': [1, 1]}
    for char in SPEC['inventory']:
        rows = compile_gestures(char, model)['strokes']
        curves = [curve for row in rows for curve in row['cubics']]
        low, high = extrema(curves, 1)
        groups, residuals = [], [abs(low), abs(high-1)]
        for index in (0, 1):
            group = [row for row in rows if row['gesture_index'] == index]
            start, end = group[0]['cubics'][0][0], group[-1]['cubics'][-1][-1]
            name = group[0]['gesture']
            residuals.extend([abs(start[1]-levels[name][0]), abs(end[1]-levels[name][1])])
            groups.append({'gesture': name, 'entry': start, 'exit': end})
        gap = math.dist(groups[0]['exit'], groups[1]['entry'])
        residuals.append(gap)
        result[char] = {'ymin': low, 'ymax': high, 'groups': groups, 'attachment_gap': gap,
                       'expanded': len(rows), 'residual': max(residuals)}
    return result


def target_shapes():
    result = {}
    for name in ('stem', 'underturn', 'overturn'):
        parts = gesture_targets.parts(foundation.SPEC['targets'], {'instances': [{'gesture': name, 'offset': [0, 0], 'scale': 1}]})
        curves = [row['points'].copy() for row in parts]
        width = 0
        if name != 'stem':
            _, matrix = rotation(curves[-1][-1] - curves[0][0])
            curves = [points @ matrix.T for points in curves]
            all_points = np.concatenate(curves)
            low, high = all_points[:, 1].min(), all_points[:, 1].max()
            scale = 1 / (high-low)
            if not .5 <= scale <= 1.5:
                raise ValueError('Independent target normalization exceeds frozen scale bounds')
            offset = [curves[0][0, 0], low]
            curves = [(points-offset) * scale for points in curves]
            width = float(curves[-1][-1, 0])
        result[name] = {'parts': curves, 'width': width}
    return result


def target(fixture):
    shapes, parts, horizontal = target_shapes(), [], 0.0
    for letter, char in enumerate(fixture['text']):
        local = horizontal + SPEC['origin_x'] + fixture['shift'][0]
        for index, name in enumerate(SPEC['recipes'][char]['gestures']):
            parts.extend((f'{letter}:{index}', points + [local, fixture['shift'][1]]) for points in shapes[name]['parts'])
            local += shapes[name]['width']
        horizontal += SPEC['recipes'][char]['advance'] + .15
    return foundation.contact_trajectory(parts)


def actual_landmarks(run, fixture):
    errors = {}
    for letter in range(len(fixture['text'])):
        values = [(10-row['to_mm'][1])/3.5-fixture['shift'][1] for row in run['trace']
                  if row['contact'] and row['owner']['letter'] == letter]
        if not values:
            raise ValueError('Missing actual letter occurrence')
        errors[str(letter)] = max(abs(min(values)), abs(max(values)-1)) * 3.5
    return errors


def paint(path, *, dpi=180):
    return foundation.paint(path, frame=SPEC['frame_mm'], dpi=dpi)


def local_crops(pixels, fixture):
    left, right, top, bottom = SPEC['frame_mm']
    width = pixels.shape[1]
    result, horizontal = {}, 0.0
    for index, char in enumerate(fixture['text']):
        origin = horizontal + SPEC['origin_x'] + fixture['shift'][0]
        low = (origin - SPEC['local_window_padding_xheight'][0]) * 3.5
        high = (origin + SPEC['recipes'][char]['advance'] + SPEC['local_window_padding_xheight'][1]) * 3.5
        if not left <= low < high <= right:
            raise ValueError('Local letter window outside full frame')
        result[str(index)] = pixels[:, math.floor((low-left)/(right-left)*width):math.ceil((high-left)/(right-left)*width)]
        horizontal += SPEC['recipes'][char]['advance'] + .15
    return result


def measure(model, old, fixture, budget, directory):
    variant = prior.placed(model, fixture)
    paths = [prior.nominal(old, fixture), target(fixture), prior.nominal(model, fixture)]
    pixels = [budget.render(paint, path) for path in paths]
    before, after = [foundation.stroke_loss(pixels[1], image) for image in [pixels[0], pixels[2]]]
    row = {'fixture': fixture, 'before': before, 'after': after, 'ratio': after/before if before else None,
        'compiled': compile_gestures(fixture['text'], variant), 'landmarks': landmarks(model),
        'motion': {}, 'actual_target': {}, 'local_actual_target': {}, 'actual_landmarks_mm': {}, 'tool': {}}
    local_target = local_crops(pixels[1], fixture)
    local_nominal = local_crops(pixels[2], fixture)
    row['local_nominal_target'] = {key: foundation.stroke_loss(value, local_nominal[key]) for key, value in local_target.items()}
    runs = {}
    for label, step, dt in [('base', .025, .002), ('arc', .0125, .002), ('time', .025, .001)]:
        run = foundation.runtime.execute(variant, fixture['text'], step=step, dt=dt, budget=budget, frame=SPEC['frame_mm'])
        for kind in ('desired', 'actual'):
            foundation.measurement.require_containment(foundation.primitives.learning._trajectory(run, kind), frame=SPEC['frame_mm'])
        contacts = list(dict.fromkeys(stroke['gesture_occurrence_id'] for stroke in row['compiled']['strokes']))
        audit, boundaries = foundation.audit_trace(variant, fixture['text'], run), foundation.boundaries(run)
        row['motion'][label] = {'metrics': run['metrics'], 'audit': audit, 'boundaries': boundaries,
            'pass': foundation.runtime.passes(run) and audit['errors'] == 0 and foundation.boundaries_pass(boundaries, contacts)}
        row['actual_target'][label] = foundation.stroke_loss(pixels[1], run['images']['actual'])
        local_actual = local_crops(run['images']['actual'], fixture)
        for key, value in local_target.items():
            row['local_actual_target'].setdefault(key, {})[label] = foundation.stroke_loss(value, local_actual[key])
        row['actual_landmarks_mm'][label] = actual_landmarks(run, fixture)
        row['tool'][label] = stem.prior.physical.tool_proof(run)
        runs[label] = run
    row['comparisons'] = {label: foundation.primitives.motion.compare(runs['base'], runs[label]) for label in ('arc', 'time')}
    foundation.primitives.compressed(directory / f"{fixture['id']}-traces.json.gz", {label: {key: value for key, value in run.items() if key != 'images'} for label, run in runs.items()})
    paths.extend(foundation.primitives.learning._trajectory(runs['base'], kind) for kind in ('desired', 'actual'))
    for label, path in zip(('initial', 'target', 'nominal', 'desired', 'actual'), paths):
        Image.fromarray(budget.render(paint, path, dpi=900)).save(directory / f"{fixture['id']}-{label}.png")
    write_json(directory / (fixture['id'] + '.json'), row)
    return row


def passed(record):
    try:
        labels = {'base', 'arc', 'time'}
        if [row['fixture'] for row in record['fixtures']] != SPEC['fixtures']:
            return False
        for row in record['fixtures']:
            if (set(row['landmarks']) != set(SPEC['inventory']) or any(value['residual'] > 1e-8 or value['expanded'] > 6 for value in row['landmarks'].values())
                    or set(row['motion']) != labels or not all(value['pass'] is True for value in row['motion'].values())
                    or set(row['comparisons']) != {'arc', 'time'} or not all(value['pass'] is True for value in row['comparisons'].values())
                    or set(row['actual_target']) != labels or set(row['tool']) != labels
                    or not all(stem.prior.physical.tool_pass(value) for value in row['tool'].values())
                    or type(row['ratio']) not in (int, float) or not math.isfinite(row['ratio']) or not 0 <= row['ratio'] < .75):
                return False
            expected = {str(index) for index in range(len(row['fixture']['text']))}
            if set(row['local_actual_target']) != expected or set(row['local_nominal_target']) != expected or set(row['actual_landmarks_mm']) != labels:
                return False
            losses = [row['after'], *row['actual_target'].values(), *row['local_nominal_target'].values()]
            for values in row['local_actual_target'].values():
                if set(values) != labels:
                    return False
                losses.extend(values.values())
            if not stem.prior.physical.finite(losses) or max(losses) > .05:
                return False
            for values in row['actual_landmarks_mm'].values():
                if set(values) != expected or not stem.prior.physical.finite(list(values.values())) or max(values.values()) > .05:
                    return False
        return True
    except (KeyError, ValueError, TypeError):
        return False


def workbook(directory, model, budget):
    fixtures = [row for row in SPEC['fixtures'] if row['split'] != 'regression_pair']
    tiles = [[Image.open(directory / f"{row['id']}-{label}.png").convert('RGB') for label in ('initial', 'target', 'nominal', 'desired', 'actual')] for row in fixtures]
    width, height = tiles[0][0].size
    budget.charge(2)
    sheet = Image.new('RGB', (width*5, 90+len(fixtures)*(height+45)), 'white')
    draw, font = ImageDraw.Draw(sheet), ImageFont.load_default(size=20)
    for index, label in enumerate(('Prior assembly', 'New independent target', 'Level nominal', 'Sampled desired', 'Actual neutral')):
        draw.text((index*width+10, 20), label, font=font, fill='black')
    for index, (fixture, images) in enumerate(zip(fixtures, tiles)):
        top = 90+index*(height+45)
        draw.text((10, top), fixture['id']+' / '+fixture['split']+' / synthetic, no reading acceptance', font=font, fill='black')
        for column, image in enumerate(images):
            sheet.paste(image, (column*width, top+40))
    sheet.save(directory / 'workbook.png')
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="940"><rect width="100%" height="100%" fill="white"/>',
           '<text x="20" y="28" font-size="22" font-family="sans-serif">Level n / u / m: fixed shared primitives; baseline 0 and x-height 1 are centerline guides</text>']
    colors = ['#2864b4', '#a33f34', '#248250', '#9654ae', '#bc741a', '#258b9c']
    for letter, char in enumerate(SPEC['inventory']):
        rows = compile_gestures(char, model)['strokes']
        for stage in (0, 1, 2):
            svg.append(f'<g transform="translate({stage*480+20},{letter*300+65})"><text y="0" font-family="sans-serif" font-size="20">{char}: {["first gesture", "both gestures", "numbered primitives"][stage]}</text>')
            for level, label in [(1, 'x-height 1'), (0, 'baseline 0')]:
                vertical = 215-level*155
                svg.append(f'<path d="M 10 {vertical} H 450" stroke="#999" stroke-dasharray="5 5"/><text x="320" y="{vertical-6}" font-size="14">{label}</text>')
            for index, row in enumerate(rows):
                if stage == 0 and row['gesture_index'] != 0:
                    continue
                color = colors[index if stage == 2 else row['gesture_index']]
                for cubic in row['cubics']:
                    points = [[point[0]*165+45, 215-point[1]*155] for point in cubic]
                    path = 'M '+' '.join(map(str, points[0]))+' C '+' '.join(str(value) for point in points[1:] for value in point)
                    svg.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3"/>')
                    if stage == 2:
                        svg.append(f'<text x="{points[0][0]+4}" y="{points[0][1]-5}" fill="{color}" font-size="15">{index+1}</text>')
            svg.append('</g>')
    svg.append('</svg>')
    (directory / 'construction.svg').write_text('\n'.join(svg))


def evaluate(source, budget, directory):
    model, transforms = make_model(source['candidate'])
    require_lineage(model, source['candidate'])
    write_json(directory / 'candidate.json', model)
    write_json(directory / 'evaluation-freeze.json', {'candidate_sha256': object_digest(model), 'transforms': transforms, 'targets_opened': False, 'optimization_evaluations': 0})
    rows = [measure(model, source['prior'], fixture, budget, directory) for fixture in SPEC['fixtures']]
    workbook(directory, model, budget)
    reuse = prior.reuse_proof(model, source['candidate'])
    write_json(directory / 'reuse.json', reuse)
    return {'fixtures': rows, 'candidate_sha256': object_digest(model), 'transforms': transforms, 'reuse': reuse}


def verify_record(source, record, directory):
    model, transforms = make_model(source['candidate'])
    if (json.loads((directory / 'candidate.json').read_text()) != model or record['candidate_sha256'] != object_digest(model)
            or record['transforms'] != transforms or record['reuse'] != prior.reuse_proof(model, source['candidate'])
            or json.loads((directory / 'evaluation-freeze.json').read_text()) != {
                'candidate_sha256': object_digest(model), 'transforms': transforms, 'targets_opened': False, 'optimization_evaluations': 0}):
        raise ValueError('Changed derived model or evaluation freeze')
    for row in record['fixtures']:
        variant = prior.placed(model, row['fixture'])
        if row['compiled'] != compile_gestures(row['fixture']['text'], variant) or row['landmarks'] != landmarks(model):
            raise ValueError('Changed letter lineage or exact landmarks')
        runs = json.loads(gzip.decompress((directory / f"{row['fixture']['id']}-traces.json.gz").read_bytes()))
        for label, run in runs.items():
            if (row['motion'][label]['audit'] != foundation.audit_trace(variant, row['fixture']['text'], run)
                    or row['motion'][label]['metrics'] != run['metrics'] or row['motion'][label]['boundaries'] != foundation.boundaries(run)
                    or row['actual_landmarks_mm'][label] != actual_landmarks(run, row['fixture'])
                    or row['tool'][label] != stem.prior.physical.tool_proof(run)):
                raise ValueError('Changed actual letter proof')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args()
    import importlib
    module = importlib.import_module('scribesim.curriculum.letter_alignment')
    result = protocol.worker(module, args.worker, args.seed, args.maximum, args.seconds) if args.worker else protocol.build(module)
    print(json.dumps({key: value for key, value in result.items() if key in ('status', 'reason', 'renders')}))
    return int(result['status'] == 'blocked')


if __name__ == '__main__':
    raise SystemExit(main())
