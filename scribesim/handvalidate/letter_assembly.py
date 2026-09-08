"""Independent frozen level-assembly mechanics, with human appearance kept separate."""

import argparse
import copy
from dataclasses import replace
import gzip
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image

from scribesim.curriculum import letter_alignment as alignment, letter_alignment_evidence as source_reader
from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures
from scribesim.handvalidate import frozen_replay as protocol
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


foundation = alignment.foundation
physical = alignment.stem.prior.physical
BASE = alignment.BASE.parent / 'validation'
SPEC_PATH = BASE / 'spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())


def identities():
    return {**alignment.identities(), **{str(path.relative_to(ROOT)): digest(path)
            for path in (Path(__file__), Path(source_reader.__file__), SPEC_PATH)}}


def require_candidate(candidate):
    if object_digest(candidate) != SPEC['candidate_object_sha256']:
        raise ValueError('Exact frozen level-assembly candidate required')
    validate_gestures(candidate)


def load_inputs():
    lower = alignment.load_inputs()
    directory = alignment.BASE / 'run-001'
    if (digest(directory / 'report.json') != SPEC['source_report_sha256']
            or digest(alignment.BASE / 'adjudication.json') != SPEC['source_adjudication_sha256']):
        raise ValueError('Changed source report or explicit numeric adjudication')
    frozen = json.loads((directory / 'freeze.json').read_text())
    if frozen != {'spec': alignment.SPEC, 'code_sha256': alignment.identities(), 'source': lower}:
        raise ValueError('Changed source freeze or live lower-layer admission')
    report = json.loads((directory / 'report.json').read_text())
    inventory = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()} - {'report.json'}
    if set(report['artifacts']) != inventory:
        raise ValueError('Incomplete source inventory')
    foundation.primitives.verify_artifacts(directory, report['artifacts'])
    adjudication = json.loads((alignment.BASE / 'adjudication.json').read_text())
    if (adjudication['reader_sha256'] != digest(Path(source_reader.__file__)) or adjudication['status'] != 'pass'
            or adjudication['source_report_sha256'] != SPEC['source_report_sha256']
            or any(adjudication[key] is not False for key in ('S2_accepted', 'real_accepted', 'context_training_allowed'))
            or SPEC['criteria'] != alignment.SPEC['criteria'] or SPEC['target_version'] != alignment.SPEC['target_version']):
        raise ValueError('Stale source adjudication, criteria or target version')
    for seed in SPEC['seeds']:
        for label in ('first', 'replay'):
            path = directory / f'seed-{seed}/{label}/candidate.json'
            if digest(path) != SPEC['candidate_file_sha256']:
                raise ValueError('Changed source candidate file')
    candidate = json.loads(path.read_text())
    require_candidate(candidate)
    if any(candidate[key] != lower['candidate'][key] for key in candidate if key != 'recipes'):
        raise ValueError('Detached lower layers')
    return {'candidate': candidate, 'prior': lower['prior'], 'stem_admission': lower['stem_admission'],
            'source_adjudication_sha256': SPEC['source_adjudication_sha256']}


def probe(candidate, fixture):
    require_candidate(candidate)
    if fixture not in SPEC['fixtures']:
        raise ValueError('Unfrozen observation')
    result = copy.deepcopy(candidate)
    if fixture['kind'] == 'gesture':
        instance = copy.deepcopy(candidate['recipes'][fixture['from_letter']]['gestures'][0])
        result['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 2, 'gestures': [instance]}}
    for recipe in result['recipes'].values():
        for instance in recipe['gestures']:
            instance['offset'] = [value + shift for value, shift in zip(instance['offset'], fixture['shift'])]
    validate_gestures(result)
    return result


def extrema(curves):
    values = []
    for curve in curves:
        start, first, second, end = np.asarray(curve, dtype=float)[:, 1]
        polynomial = np.polynomial.Polynomial([start, 3*(first-start), 3*(second-2*first+start), end-3*second+3*first-start])
        roots = [float(root.real) for root in polynomial.deriv().roots() if abs(root.imag) < 1e-12 and 0 < root.real < 1]
        values.extend(float(polynomial(parameter)) for parameter in [0, 1, *roots])
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError('Finite complete centerline required')
    return min(values), max(values)


def levels(model, fixture):
    return level_rows(compile_gestures(fixture['text'], model)['strokes'], fixture)


def level_rows(rows, fixture):
    result, vertical = {}, fixture['shift'][1]
    for letter in range(len(fixture['text'])):
        selected = [row for row in rows if row['letter'] == letter]
        low, high = extrema([curve for row in selected for curve in row['cubics']])
        errors, previous = [abs(low-vertical), abs(high-vertical-1)], None
        for index in sorted({row['gesture_index'] for row in selected}):
            group = [row for row in selected if row['gesture_index'] == index]
            start, end = group[0]['cubics'][0][0], group[-1]['cubics'][-1][-1]
            expected = {'stem': (1, 0), 'underturn': (1, 1), 'overturn': (0, 0)}[group[0]['gesture']]
            errors.extend([abs(start[1]-vertical-expected[0]), abs(end[1]-vertical-expected[1])])
            if previous is not None:
                errors.append(math.dist(previous, start))
            previous = end
        result[str(letter)] = max(errors)
    return result


def target(fixture):
    shapes, parts, regions, horizontal = alignment.target_shapes(), [], {}, 0.0
    for letter, char in enumerate(fixture['text']):
        names = ([alignment.SPEC['recipes'][fixture['from_letter']]['gestures'][0]] if fixture['kind'] == 'gesture'
                 else alignment.SPEC['recipes'][char]['gestures'])
        local, points = horizontal + alignment.SPEC['origin_x'] + fixture['shift'][0], []
        for index, name in enumerate(names):
            for shape in shapes[name]['parts']:
                placed = shape + [local, fixture['shift'][1]]
                points.append(placed)
                parts.append((f'{letter}:{index}', placed))
            local += shapes[name]['width']
        physical_points = np.concatenate(points) * [3.5, -3.5] + [0, 10]
        low, high = physical_points.min(axis=0)-SPEC['local_target_padding_mm'], physical_points.max(axis=0)+SPEC['local_target_padding_mm']
        regions[str(letter)] = [float(low[0]), float(high[0]), float(low[1]), float(high[1])]
        horizontal += (2 if fixture['kind'] == 'gesture' else alignment.SPEC['recipes'][char]['advance']) + .15
    return foundation.contact_trajectory(parts), regions


def crop(pixels, bounds):
    left, right, top, bottom = SPEC['frame_mm']
    xmin, xmax, ymin, ymax = bounds
    if not left <= xmin < xmax <= right or not top <= ymin < ymax <= bottom:
        raise ValueError('Incomplete local comparison frame')
    height, width = pixels.shape[:2]
    return pixels[math.floor((ymin-top)/(bottom-top)*height):math.ceil((ymax-top)/(bottom-top)*height),
                  math.floor((xmin-left)/(right-left)*width):math.ceil((xmax-left)/(right-left)*width)]


def paint(path, *, dpi=180):
    return foundation.paint(path, frame=SPEC['frame_mm'], dpi=dpi)


def actual_levels(run, fixture):
    result = {}
    for letter in range(len(fixture['text'])):
        points = [row['to_mm'][1] for row in run['trace'] if row['contact'] and row['owner']['letter'] == letter]
        baseline = 10-3.5*fixture['shift'][1]
        result[str(letter)] = max(abs(max(points)-baseline), abs(min(points)-(baseline-3.5)))
    return result


def image_losses(target_pixels, images, regions):
    return {'global': {label: float(foundation.stroke_loss(target_pixels, pixels)) for label, pixels in images.items()},
            'local': {owner: {label: float(foundation.stroke_loss(crop(target_pixels, bounds), crop(pixels, bounds)))
                            for label, pixels in images.items()} for owner, bounds in regions.items()}}


def refinements(fixture):
    return SPEC['refinements'][fixture['kind']]


def execute(model, fixture, budget):
    if fixture['kind'] == 'gesture':
        return foundation.execute_refinements(model, fixture['text'], budget, SPEC['frame_mm'])
    runs, motion = {}, {}
    required = list(dict.fromkeys(row['gesture_occurrence_id'] for row in compile_gestures(fixture['text'], model)['strokes']))
    for label, step, dt in [('base', .025, .002), ('arc', .0125, .002), ('time', .025, .001)]:
        run = foundation.runtime.execute(model, fixture['text'], step=step, dt=dt, budget=budget, frame=SPEC['frame_mm'])
        for kind in ('desired', 'actual'):
            foundation.measurement.require_containment(foundation.primitives.learning._trajectory(run, kind), frame=SPEC['frame_mm'])
        motion[label] = {'metrics': run['metrics'], 'version': run['version'],
            'audit': foundation.audit_trace(model, fixture['text'], run), 'boundaries': foundation.boundaries(run),
            'required_contacts': required, 'contained': True}
        runs[label] = run
    return runs, motion, {label: foundation.primitives.motion.compare(runs['base'], run) for label, run in runs.items() if label != 'base'}


def motion_pass(row):
    labels = set(refinements(row['fixture']))
    return (set(row['motion']) == labels and foundation.admission.comparisons_pass(row['comparisons'], sorted(labels-{'base'}))
        and all(proof['version'] == foundation.runtime.VERSION and foundation.runtime.passes(proof)
                and proof['audit']['errors'] == 0 and proof['contained'] is True
                and foundation.boundaries_pass(proof['boundaries'], proof['required_contacts']) for proof in row['motion'].values()))


def measure(candidate, prior, fixture, budget, directory):
    model = probe(candidate, fixture)
    target_path, regions = target(fixture)
    nominal_path = foundation.nominal(model, fixture['text'])
    target_pixels, nominal_pixels = [budget.render(paint, path) for path in (target_path, nominal_path)]
    runs, motion, comparisons = execute(model, fixture, budget)
    images = {'nominal': nominal_pixels, **{label: run['images']['actual'] for label, run in runs.items()}}
    row = {'fixture': fixture, 'compiled': compile_gestures(fixture['text'], model), 'levels': levels(model, fixture),
           'regions': regions, 'motion': motion, 'comparisons': comparisons,
           'contacts': [foundation.contact_runs(path) for path in (target_path, nominal_path)],
           'actual_levels_mm': {label: actual_levels(run, fixture) for label, run in runs.items()},
           'tool': {label: physical.tool_proof(run) for label, run in runs.items()},
           'losses': image_losses(target_pixels, images, regions), 'benefit': None}
    paths = {'target': target_path, 'nominal': nominal_path,
             'actual': foundation.primitives.learning._trajectory(runs['base'], 'actual')}
    if fixture['kind'] == 'letter':
        prior_path = alignment.prior.nominal(prior, fixture)
        prior_pixels = budget.render(paint, prior_path)
        before = float(foundation.stroke_loss(target_pixels, prior_pixels))
        row['benefit'] = {'before': before, 'ratio': row['losses']['global']['nominal']/before if before > 0 else None}
        images['prior'], paths['prior'] = prior_pixels, prior_path
    for label, pixels in {'target': target_pixels, **images}.items():
        Image.fromarray(pixels).save(directory / f"{fixture['id']}-{label}-metric.png")
    for label, path in paths.items():
        Image.fromarray(budget.render(paint, path, dpi=900)).save(directory / f"{fixture['id']}-{label}.png")
    foundation.primitives.compressed(directory / f"{fixture['id']}-traces.json.gz",
        {label: {key: value for key, value in run.items() if key != 'images'} for label, run in runs.items()})
    write_json(directory / (fixture['id'] + '.json'), row)
    return row, runs


def below(values, maximum):
    return bool(values) and all(type(value) in (int, float, np.float64) and math.isfinite(value) and 0 <= value <= maximum for value in values)


def fixture_pass(row):
    try:
        fixture, labels = row['fixture'], set(refinements(row['fixture']))
        owners = {str(index) for index in range(len(fixture['text']))}
        contacts = 1 if fixture['kind'] == 'gesture' else 2*len(fixture['text'])
        if (not motion_pass(row) or row['contacts'] != [contacts, contacts]
                or set(row['levels']) != owners or not below(list(row['levels'].values()), SPEC['criteria']['nominal_landmark_max'])
                or set(row['actual_levels_mm']) != labels or set(row['tool']) != labels
                or not all(physical.tool_pass(value) for value in row['tool'].values())):
            return False
        if any(set(values) != owners or not below(list(values.values()), .05) for values in row['actual_levels_mm'].values()):
            return False
        if set(row['losses']['local']) != owners or set(row['losses']['global']) != labels | {'nominal'}:
            return False
        if any(set(values) != labels | {'nominal'} or not below(list(values.values()), .05)
               for values in [row['losses']['global'], *row['losses']['local'].values()]):
            return False
        benefit = row['benefit']
        if fixture['kind'] == 'gesture':
            return benefit is None
        return (below([benefit['before']], float('inf')) and benefit['before'] > 0
                and below([benefit['ratio']], .75) and benefit['ratio'] < .75)
    except (KeyError, TypeError, ValueError):
        return False


def control_proofs(candidate, fixture, run):
    result = {}
    for name in ('primitive-drift', 'action-drift'):
        changed = copy.deepcopy(candidate)
        if name == 'primitive-drift':
            changed['primitives']['stem']['cubics'][0][1][0] += .01
        else:
            changed['actions']['fixed']['orientation'][1][1] += 5
        try:
            require_candidate(changed)
            detected = False
        except ValueError:
            detected = True
        result[name] = {'detected': detected, 'mutant_sha256': object_digest(changed), 'gate': 'exact-lineage'}
    model = probe(candidate, fixture)
    changed = compile_gestures(fixture['text'], model)['strokes']
    for row in changed:
        if row['letter'] == 0 and row['gesture_index'] == 1:
            for curve in row['cubics']:
                for point in curve:
                    point[1] += .08
    residuals = level_rows(changed, fixture)
    result['climbing-assembly'] = {'detected': not below(list(residuals.values()), 1e-8),
                                 'residuals': residuals, 'gate': 'independent-levels'}
    for name in ('owner', 'painted-air', 'desired-as-actual'):
        changed = copy.deepcopy(run)
        if name == 'owner':
            next(row for row in changed['trace'] if row['contact'])['owner']['primitive'] = 'invented'
        elif name == 'painted-air':
            next(row for row in changed['trace'] if not row['contact'])['pressure'] = .5
        else:
            for row in changed['trace']:
                row['to_mm'] = row['desired_mm'][:]
        audit = foundation.audit_trace(model, fixture['text'], changed)
        result[name] = {'detected': audit['errors'] > 0, 'audit': audit, 'gate': 'actual-trace'}
    return result


def controls(candidate, fixture, run, budget, directory):
    result = control_proofs(candidate, fixture, run)
    path = foundation.primitives.learning._trajectory(run, 'actual')
    shifted = [replace(point, x_mm=point.x_mm+SPEC['visible_shift_mm']) for point in path]
    pixels = budget.render(paint, shifted)
    Image.fromarray(pixels).save(directory / 'visible-shift-metric.png')
    target_pixels = np.array(Image.open(directory / f"{fixture['id']}-target-metric.png"))
    loss = float(foundation.stroke_loss(target_pixels, pixels))
    result['visible-shift'] = {'detected': math.isfinite(loss) and loss > .05, 'loss': loss, 'gate': 'rendered-image'}
    write_json(directory / 'controls.json', result)
    return result


def evaluate(source, budget, directory):
    write_json(directory / 'candidate.json', source['candidate'])
    rows = []
    for fixture in SPEC['fixtures']:
        row, runs = measure(source['candidate'], source['prior'], fixture, budget, directory)
        rows.append(row)
    return {'fixtures': rows, 'controls': controls(source['candidate'], fixture, runs['base'], budget, directory),
            'appearance_review': 'pending', 'S2_accepted': False}


def passed(record):
    try:
        return ([row['fixture'] for row in record['fixtures']] == SPEC['fixtures']
                and all(fixture_pass(row) for row in record['fixtures'])
                and set(record['controls']) == set(SPEC['controls'])
                and all(value['detected'] is True for value in record['controls'].values())
                and record['appearance_review'] == 'pending' and record['S2_accepted'] is False)
    except (KeyError, TypeError, ValueError):
        return False


def verify_record(source, record, directory):
    if json.loads((directory / 'candidate.json').read_text()) != source['candidate']:
        raise ValueError('Changed frozen validation candidate')
    for row in record['fixtures']:
        fixture = row['fixture']
        model = probe(source['candidate'], fixture)
        if (row != json.loads((directory / (fixture['id']+'.json')).read_text())
                or row['compiled'] != compile_gestures(fixture['text'], model) or row['levels'] != levels(model, fixture)
                or row['regions'] != target(fixture)[1]):
            raise ValueError('Changed source, level or target-region proof')
        runs = json.loads(gzip.decompress((directory / f"{fixture['id']}-traces.json.gz").read_bytes()))
        if set(runs) != set(refinements(fixture)):
            raise ValueError('Missing refinement trace')
        for label, run in runs.items():
            variant = foundation.primitives.subdivide(model) if label == 'subdivision' and fixture['text'] != 'i' else model
            if (row['motion'][label]['audit'] != foundation.audit_trace(variant, fixture['text'], run, subdivision=label == 'subdivision' and fixture['text'] == 'i')
                    or row['motion'][label]['metrics'] != run['metrics'] or row['motion'][label]['boundaries'] != foundation.boundaries(run)
                    or row['actual_levels_mm'][label] != actual_levels(run, fixture) or row['tool'][label] != physical.tool_proof(run)):
                raise ValueError('Changed actual physical proof')
        images = {label: np.array(Image.open(directory / f"{fixture['id']}-{label}-metric.png")) for label in ['nominal', *refinements(fixture)]}
        target_pixels = np.array(Image.open(directory / f"{fixture['id']}-target-metric.png"))
        if row['losses'] != image_losses(target_pixels, images, row['regions']):
            raise ValueError('Numeric image proof differs from saved measurement pixels')
        if fixture['kind'] == 'letter':
            before = float(foundation.stroke_loss(target_pixels, np.array(Image.open(directory / f"{fixture['id']}-prior-metric.png"))))
            if row['benefit'] != {'before': before, 'ratio': row['losses']['global']['nominal']/before if before > 0 else None}:
                raise ValueError('Changed benefit measurement')
        if row['comparisons'] != {label: foundation.primitives.motion.compare(runs['base'], run) for label, run in runs.items() if label != 'base'}:
            raise ValueError('Changed convergence proof')
    expected = control_proofs(source['candidate'], fixture, runs['base'])
    loss = float(foundation.stroke_loss(target_pixels, np.array(Image.open(directory / 'visible-shift-metric.png'))))
    expected['visible-shift'] = {'detected': math.isfinite(loss) and loss > .05, 'loss': loss, 'gate': 'rendered-image'}
    if record['controls'] != expected or expected != json.loads((directory / 'controls.json').read_text()):
        raise ValueError('Changed independent control proof')


def inspect_run(directory, *, expected_report_sha256):
    result = protocol.inspect(sys.modules[__name__], directory, expected_report_sha256)
    return {**result, 'mechanical_validation_pass': result['status'] == 'pass',
            'appearance_review': 'pending', 'context_training_allowed': False, 'scope': SPEC['scope']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    parser.add_argument('--inspect-sha256')
    args = parser.parse_args()
    import importlib
    module = importlib.import_module('scribesim.handvalidate.letter_assembly')
    if args.inspect_sha256:
        print(json.dumps(module.inspect_run(BASE / 'run-001', expected_report_sha256=args.inspect_sha256), indent=2))
        return 0
    result = protocol.worker(module, args.worker, args.seed, args.maximum, args.seconds) if args.worker else protocol.build(module)
    print(json.dumps({key: value for key, value in result.items() if key in ('status', 'reason', 'renders')}))
    return int(result['status'] == 'blocked')


if __name__ == '__main__':
    raise SystemExit(main())
