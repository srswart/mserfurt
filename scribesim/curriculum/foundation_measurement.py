"""Full-frame measurement of pinned return candidates without fitting or execution."""

import argparse
import copy
import gzip
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image

from scribesim.curriculum import foundation_primitives as learning
from scribesim.curriculum.stroke_learning import stroke_loss
from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handvalidate import foundation_motion as motion
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.model import TrajectorySample
from scribesim.handvalidate.specimen import digest, object_digest, write_json


SPEC_PATH = learning.BASE / 'measurement-spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())


def identities():
    return {**learning.identities(), 'scribesim/curriculum/foundation_measurement.py': digest(Path(__file__)),
            str(SPEC_PATH.relative_to(learning.ROOT)): digest(SPEC_PATH)}


def load_source(root=None):
    root = learning.BASE / SPEC['source'] if root is None else Path(root)
    try:
        if digest(root / 'report.json') != SPEC['source_report_sha256']:
            raise ValueError('Unfrozen learning source')
        report = json.loads((root / 'report.json').read_text())
        if report['code_sha256'] != learning.identities():
            raise ValueError('Stale learning, motion or target identities')
        for name, checksum in report['artifacts'].items():
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()) or digest(path) != checksum:
                raise ValueError('Learning source artifact mismatch')
        freeze = json.loads((root / 'freeze.json').read_text())
        if freeze['spec'] != learning.SPEC or freeze['initial'] != learning.initial_model():
            raise ValueError('Changed learning initialization or protocol')
        admission = learning.verify_admission(root / 'baseline')
        if [row['seed'] for row in report['seeds']] != SPEC['seeds']:
            raise ValueError('All frozen seeds are required')
        seeds = {}
        for row in report['seeds']:
            directory = root / f"seed-{row['seed']}"
            candidate = json.loads((directory / 'candidate.json').read_text())
            learning.require_lineage(candidate, freeze['initial'])
            checksum = object_digest(candidate)
            if checksum != row['candidate_sha256']:
                raise ValueError('Candidate identity mismatch')
            selection = json.loads((directory / 'selection.json').read_text())
            if selection['candidate_sha256'] != checksum or selection['selection_split'] != 'development' or selection['held_out_accessed']:
                raise ValueError('Invalid frozen selection')
            traces = json.loads(gzip.decompress((directory / 'traces.json.gz').read_bytes()))
            if set(traces) != {fixture['id'] for fixture in learning.SPEC['splits']['held_out']}:
                raise ValueError('Incomplete frozen attachment traces')
            for fixture in learning.SPEC['splits']['held_out']:
                runs = traces[fixture['id']]
                if set(runs) != {refinement['id'] for refinement in learning.SPEC['refinements']}:
                    raise ValueError('Incomplete frozen refinements')
                probe_sha = object_digest(learning.probe_model(candidate, fixture))
                if any(result['foundation_source_sha256'] != checksum or result['probe_sha256'] != probe_sha for result in runs.values()):
                    raise ValueError('Trace/candidate lineage mismatch')
            seeds[row['seed']] = {'candidate': candidate, 'traces': traces, 'directory': directory}
    except (OSError, KeyError, TypeError) as error:
        raise ValueError('Incomplete frozen measurement source') from error
    return {'seeds': seeds, 'admission': admission, 'initial': freeze['initial']}


def segment_trajectory(segments):
    return [TrajectorySample(float(point[0] * 3.5), float(10 - point[1] * 3.5), True, .45, .5, 40)
            for segment in segments for point in segment]


def require_containment(trajectory, *, frame=None):
    left, right, top, bottom = SPEC['frame_mm'] if frame is None else frame
    if not all(math.isfinite(value) for value in (left, right, top, bottom)) or left >= right or top >= bottom:
        raise ValueError('Invalid measurement frame')
    for point in trajectory:
        if not all(math.isfinite(value) for value in (point.x_mm, point.y_mm)):
            raise ValueError('Nonfinite frame geometry')
        if not point.contact:
            continue
        if point.width_mm is None or not math.isfinite(point.width_mm) or point.width_mm < 0:
            raise ValueError('Invalid contact footprint')
        margin = point.width_mm / 2 + 2 * 25.4 / SPEC['dpi']
        if not (left <= point.x_mm - margin and point.x_mm + margin <= right
                and top <= point.y_mm - margin and point.y_mm + margin <= bottom):
            raise ValueError('Contact footprint lies outside the measurement frame')


def paint(trajectory, *, dpi=180):
    require_containment(trajectory)
    return paint_trajectory(trajectory, SPEC['frame_mm'], dpi=dpi)


def crop(image, bounds):
    left, right, top, bottom = SPEC['frame_mm']
    xmin, xmax, ymin, ymax = bounds
    if not (all(math.isfinite(value) for value in bounds) and left <= xmin < xmax <= right and top <= ymin < ymax <= bottom):
        raise ValueError('Local region extends outside the measurement frame')
    xstart = math.floor((xmin - left) / (right - left) * image.shape[1])
    xend = math.ceil((xmax - left) / (right - left) * image.shape[1])
    ystart = math.floor((ymin - top) / (bottom - top) * image.shape[0])
    yend = math.ceil((ymax - top) / (bottom - top) * image.shape[0])
    if xend <= xstart or yend <= ystart:
        raise ValueError('Empty measurement region')
    return image[ystart:yend, xstart:xend]


def _nominal(model, fixture):
    rows = compile_gestures('i', learning.probe_model(model, fixture))['strokes']
    return segment_trajectory([learning._curve(cubic) for row in rows for cubic in row['cubics']])


def measure_fixture(candidate, fixture, saved_runs, budget):
    initial_path = _nominal(learning.initial_model(), fixture)
    target_path = segment_trajectory(learning.target_segments(fixture))
    learned_path = _nominal(candidate, fixture)
    before, target, after, null = [budget.render(paint, path) for path in (initial_path, target_path, learned_path, [])]
    runs = copy.deepcopy(saved_runs)
    for result in runs.values():
        result['images'] = {kind: budget.render(paint, learning._trajectory(result, kind)) for kind in ('desired', 'actual')}
        metrics = result['metrics']
        metrics['image_loss'] = stroke_loss(result['images']['desired'], result['images']['actual'])
        metrics['corridor_mm'] = max(math.dist(row['to_mm'], row['desired_mm']) for row in result['trace'] if row['contact'])
        result['passed'] = (metrics['image_loss'] <= .35 and metrics['corridor_mm'] <= .25 and metrics['owner_errors'] == 0
                            and metrics['time_error_s'] <= motion.SPEC['criteria']['duration_s']
                            and metrics['max_projection_mm'] <= 1e-12 and motion.entry_pass(metrics)
                            and motion.mechanics_pass(metrics) and motion.desired_pass(metrics) and motion.corners_pass(metrics))
    comparisons = {label: motion.compare(runs['base'], runs[label]) for label in ('arc', 'time', 'subdivision')}
    families = {}
    for name, bounds in learning._regions(fixture).items():
        prior = stroke_loss(crop(target, bounds['loss']), crop(before, bounds['loss']))
        learned = stroke_loss(crop(target, bounds['loss']), crop(after, bounds['loss']))
        fractions = {label: float(np.mean(np.asarray(Image.fromarray(crop(pixels, bounds['blank'])).convert('L')) < 180))
                     for label, pixels in [('target', target), ('nominal', after),
                                           *[(label, result['images']['actual']) for label, result in runs.items()]]}
        families[name] = {'before': prior, 'after': learned, 'ratio': learned / prior if prior > 0 else None,
                          'benefit_pass': learning.benefit_pass(prior, learned), 'regions_mm': bounds,
                          'blank_fractions': fractions, 'blank_pass': all(value <= .01 for value in fractions.values()),
                          'motion': {label: result['metrics'] for label, result in runs.items()}}
    prior, learned = stroke_loss(target, before), stroke_loss(target, after)
    record = {'fixture': fixture, 'frame_mm': SPEC['frame_mm'], 'footprint_contained': True,
              'before': prior, 'after': learned, 'ratio': learned / prior if prior > 0 else None,
              'benefit_pass': learning.benefit_pass(prior, learned), 'families': families,
              'fixed_null': {'loss': prior, 'ratio': 1.0}, 'empty_control_loss': stroke_loss(target, null),
              'comparisons': comparisons,
              'motion_pass': all(result['passed'] for result in runs.values()) and all(row['pass'] for row in comparisons.values()),
              'candidate_sha256': object_digest(candidate), 'mechanics_source': 'Pinned unchanged run-002 traces and scalar metrics; image losses and corridor remeasured'}
    record['passed'] = (record['benefit_pass'] and record['motion_pass'] and record['empty_control_loss'] >= .1
                        and all(row['benefit_pass'] and row['blank_pass'] for row in families.values()))
    paths = [initial_path, target_path, learned_path, *[learning._trajectory(runs['base'], kind) for kind in ('desired', 'actual')]]
    tiles = [budget.render(paint, path, dpi=SPEC['presentation_dpi']) for path in paths]
    return record, tiles


def complete(rows):
    return (len(rows) == 3 and {row['seed'] for row in rows} == set(SPEC['seeds'])
            and all(len(row['fixtures']) == 5 and all(fixture['passed'] is True for fixture in row['fixtures']) for row in rows))


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError('Use a new immutable measurement output directory')
    budget = learning.Budget(SPEC['max_renders'], SPEC['max_seconds'])
    write_json(output / 'freeze.json', {'spec': SPEC, 'code_sha256': identities(), 'spec_sha256': digest(SPEC_PATH)})
    report = {'status': 'blocked', 'scope': SPEC['scope'], 'code_sha256': identities(), 'seeds': [],
              'source_report_sha256': SPEC['source_report_sha256'], 'optimization_evaluations': 0, 'execution_calls': 0,
              'S1_accepted': False, 'gesture_training_permitted': False, 'revision': 0}
    try:
        source = load_source()
        report['admission'] = source['admission']
        for seed in SPEC['seeds']:
            budget.check()
            row = source['seeds'][seed]
            directory = output / f'seed-{seed}'
            directory.mkdir()
            fixtures, sheet_rows = [], []
            for fixture in learning.SPEC['splits']['held_out']:
                record, tiles = measure_fixture(row['candidate'], fixture, row['traces'][fixture['id']], budget)
                fixtures.append(record)
                write_json(directory / (fixture['id'] + '-metrics.json'), record)
                sheet_rows.append((fixture['id'] + (' | PASS' if record['passed'] else ' | FAIL'), tiles))
                for label, pixels in zip(('initial', 'target', 'learned', 'desired', 'actual'), tiles):
                    Image.fromarray(pixels).save(directory / (fixture['id'] + '-' + label + '-900dpi.png'))
            budget.render(learning._sheet, directory / 'practice-sheet.png', sheet_rows)
            (directory / 'candidate.json').write_bytes((row['directory'] / 'candidate.json').read_bytes())
            (directory / 'ports.svg').write_bytes((row['directory'] / 'ports.svg').read_bytes())
            result = {'seed': seed, 'fixtures': fixtures, 'candidate_sha256': object_digest(row['candidate']),
                      'source_trace_sha256': digest(row['directory'] / 'traces.json.gz')}
            report['seeds'].append(result)
            write_json(directory / 'report.json', result)
        report['status'] = 'pass' if complete(report['seeds']) else 'fail'
        budget.check()
    except (ValueError, RuntimeError) as error:
        report['status'] = 'blocked'
        report['reason'] = str(error)
    report.update(renders=budget.used, max_renders=SPEC['max_renders'], max_seconds=SPEC['max_seconds'],
                  artifacts={str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()})
    write_json(output / 'report.json', report)
    write_json(output / 'execution.json', {'renders': budget.used, 'elapsed_seconds': time.monotonic() - budget.started})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({key: result[key] for key in ('status', 'renders', 'optimization_evaluations', 'execution_calls')}, indent=2))


if __name__ == '__main__':
    main()
