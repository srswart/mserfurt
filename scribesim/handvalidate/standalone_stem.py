"""Independent unchanged standalone-stem fixed-null admission; not letter acceptance."""

import argparse
import copy
import gzip
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

from scribesim.curriculum import gesture_targets
from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures
from scribesim.handvalidate import finer_scales as prior, frozen_replay as protocol
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


foundation = prior.foundation
BASE = prior.BASE.parent / 'stem_evaluation'
SPEC_PATH = BASE / 'spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())


def identities():
    return {**prior.identities(), **{str(path.relative_to(ROOT)): digest(path)
            for path in [Path(__file__), Path(protocol.__file__), SPEC_PATH]}}


def require_candidate(candidate):
    if object_digest(candidate) != prior.SPEC['candidate_object_sha256']:
        raise ValueError('Exact frozen lower-layer candidate required')
    validate_gestures(candidate)


def load_inputs():
    admitted = prior.require_readiness(prior.BASE / 'run-001',
        expected_report_sha256=SPEC['source_report_sha256'], required_gestures=['underturn', 'overturn'])
    path = prior.BASE / 'run-001/seed-7/first/candidate.json'
    if digest(path) != SPEC['candidate_file_sha256']:
        raise ValueError('Changed source candidate bytes')
    candidate = json.loads(path.read_text())
    require_candidate(candidate)
    return {'candidate': candidate, 'prior_admission': admitted}


def probe(candidate, fixture):
    require_candidate(candidate)
    result = copy.deepcopy(candidate)
    instances = [{'gesture': 'stem', 'offset': offset, 'scale': 1, 'rotation_deg': 0,
                  'transition': 'start' if index == 0 else 'lift', 'overlap_with': []}
                 for index, offset in enumerate(fixture['offsets'])]
    result['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 2, 'gestures': instances}}
    validate_gestures(result)
    return result


def target(fixture):
    parts = gesture_targets.parts(foundation.SPEC['targets'], {'instances': [
        {'gesture': 'stem', 'offset': offset, 'scale': 1} for offset in fixture['offsets']]})
    return foundation.contact_trajectory((row['occurrence'], row['points']) for row in parts)


def crop(pixels, bounds):
    left, right, top, bottom = SPEC['frame_mm']
    xmin, xmax, ymin, ymax = bounds
    if not left <= xmin < xmax <= right or not top <= ymin < ymax <= bottom:
        raise ValueError('Local measurement outside full frame')
    height, width = pixels.shape[:2]
    return pixels[int((ymin-top)/(bottom-top)*height):int(np.ceil((ymax-top)/(bottom-top)*height)),
                  int((xmin-left)/(right-left)*width):int(np.ceil((xmax-left)/(right-left)*width))]


def regions(fixture):
    return {str(index): [horizontal*3.5-.6, horizontal*3.5+.6, 10-(vertical+1)*3.5-.6, 10-vertical*3.5+.6]
            for index, (horizontal, vertical) in enumerate(fixture['offsets'])}


def measure(candidate, fixture, budget, directory):
    model = probe(candidate, fixture)
    paths = [target(fixture), foundation.nominal(model)]
    pixels = [budget.render(foundation.paint, path, frame=SPEC['frame_mm']) for path in paths]
    runs, motion, comparisons = foundation.execute_refinements(model, 'i', budget, SPEC['frame_mm'])
    row = {'fixture': fixture, 'compiled': compile_gestures('i', model), 'motion': motion, 'comparisons': comparisons,
        'contact_runs': [foundation.contact_runs(path) for path in paths],
        'nominal_target': foundation.stroke_loss(*pixels),
        'actual_target': {name: foundation.stroke_loss(pixels[0], run['images']['actual']) for name, run in runs.items()},
        'tool': {name: prior.physical.tool_proof(run) for name, run in runs.items()}, 'local_actual_target': {}, 'blank': {}}
    for occurrence, bounds in regions(fixture).items():
        row['local_actual_target'][occurrence] = {name: foundation.stroke_loss(crop(pixels[0], bounds), crop(run['images']['actual'], bounds)) for name, run in runs.items()}
    for name, image in [('target', pixels[0]), ('nominal', pixels[1]), *[(name, run['images']['actual']) for name, run in runs.items()]]:
        row['blank'][name] = float(np.mean(np.asarray(Image.fromarray(crop(image, [4.5, 5.5, 6, 11])).convert('L')) < 180))
    for label, path in [('target', paths[0]), ('nominal', paths[1]), ('actual', foundation.primitives.learning._trajectory(runs['base'], 'actual'))]:
        Image.fromarray(budget.render(foundation.paint, path, frame=SPEC['frame_mm'], dpi=900)).save(directory / f"{fixture['id']}-{label}.png")
    foundation.primitives.compressed(directory / f"{fixture['id']}-traces.json.gz", {name: {key: value for key, value in run.items() if key != 'images'} for name, run in runs.items()})
    write_json(directory / (fixture['id'] + '.json'), row)
    return row, runs['base']


def fixture_pass(row):
    try:
        labels = {'base', 'arc', 'time', 'subdivision'}
        return (foundation.motion_pass(row) and row['contact_runs'] == [len(row['fixture']['offsets'])]*2
            and set(row['actual_target']) == labels and set(row['local_actual_target']) == set(regions(row['fixture']))
            and all(prior.physical.finite(values) and max(values) <= .05 for values in
                [[row['nominal_target']], list(row['actual_target'].values()), *[list(values.values()) for values in row['local_actual_target'].values()]] )
            and all(set(values) == labels for values in row['local_actual_target'].values())
            and set(row['tool']) == labels and all(value['errors'] == 0 for value in row['tool'].values())
            and set(row['blank']) == labels | {'target', 'nominal'} and prior.physical.finite(list(row['blank'].values()))
            and max(row['blank'].values()) <= .01)
    except (KeyError, TypeError, ValueError):
        return False


def controls(candidate, fixture, run, directory):
    result, mutations = {}, {}
    for name in ('geometry', 'action'):
        changed = copy.deepcopy(candidate)
        if name == 'geometry':
            changed['primitives']['stem']['cubics'][0][1][0] += .01
        else:
            changed['actions']['fixed']['orientation'][1][1] += 5
        try:
            require_candidate(changed)
        except ValueError:
            result[name] = True
        else:
            result[name] = False
        mutations[name] = changed
    model = probe(candidate, fixture)
    for name in ('owner', 'painted-air', 'desired-as-actual'):
        changed = copy.deepcopy(run)
        if name == 'owner':
            next(row for row in changed['trace'] if row['contact'])['owner']['primitive'] = 'invented'
        elif name == 'painted-air':
            next(row for row in changed['trace'] if not row['contact'])['pressure'] = .5
        else:
            for row in changed['trace']:
                row['to_mm'] = row['desired_mm'][:]
        result[name] = foundation.audit_trace(model, 'i', changed)['errors'] > 0
        mutations[name] = {key: value for key, value in changed.items() if key != 'images'}
    foundation.primitives.compressed(directory / 'controls.json.gz', mutations)
    return result


def evaluate(source, budget, directory):
    rows, run = [], None
    for fixture in SPEC['fixtures']:
        row, run = measure(source['candidate'], fixture, budget, directory)
        rows.append(row)
    return {'fixtures': rows, 'controls': controls(source['candidate'], SPEC['fixtures'][-1], run, directory)}


def passed(record):
    try:
        return ([row['fixture'] for row in record['fixtures']] == SPEC['fixtures']
            and all(fixture_pass(row) for row in record['fixtures']) and set(record['controls']) == set(SPEC['controls'])
            and all(value is True for value in record['controls'].values()))
    except (KeyError, TypeError, ValueError):
        return False


def verify_record(source, record, directory):
    for row in record['fixtures']:
        model = probe(source['candidate'], row['fixture'])
        if row['compiled'] != compile_gestures('i', model):
            raise ValueError('Compiled stem lineage differs')
        runs = json.loads(gzip.decompress((directory / f"{row['fixture']['id']}-traces.json.gz").read_bytes()))
        for label, run in runs.items():
            if (row['motion'][label]['audit'] != foundation.audit_trace(model, 'i', run, subdivision=label == 'subdivision')
                    or row['motion'][label]['metrics'] != run['metrics'] or row['motion'][label]['boundaries'] != foundation.boundaries(run)
                    or row['tool'][label] != prior.physical.tool_proof(run)):
                raise ValueError('Saved physical stem proof differs')
    mutations = json.loads(gzip.decompress((directory / 'controls.json.gz').read_bytes()))
    for name, changed in mutations.items():
        if name in ('geometry', 'action'):
            try:
                require_candidate(changed)
                detected = False
            except ValueError:
                detected = True
        else:
            detected = foundation.audit_trace(probe(source['candidate'], SPEC['fixtures'][-1]), 'i', changed)['errors'] > 0
        if record['controls'][name] is not detected:
            raise ValueError('Adversarial stem detection differs')


def require_readiness(directory, *, expected_report_sha256, required_gestures, tool='legacy-full-edge', real=False):
    if required_gestures != ['stem'] or tool != SPEC['tool'] or real is not False:
        raise ValueError('Explicit synthetic standalone-stem fixed-tool scope required')
    evidence = protocol.inspect(sys.modules[__name__], directory, expected_report_sha256)
    if evidence['status'] != 'pass':
        raise ValueError('Standalone stem is not accepted')
    return {**evidence, 'accepted_gestures': ['stem'], 'S1_action_accepted': True,
            'candidate_file_sha256': SPEC['candidate_file_sha256'], 'scope': SPEC['scope']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args()
    module = sys.modules[__name__]
    if __name__ == '__main__':
        import importlib
        module = importlib.import_module('scribesim.handvalidate.standalone_stem')
    result = protocol.worker(module, args.worker, args.seed, args.maximum, args.seconds) if args.worker else protocol.build(module)
    print(json.dumps({key: value for key, value in result.items() if key in ('status', 'reason', 'renders')}))
    return int(result['status'] == 'blocked')


if __name__ == '__main__':
    raise SystemExit(main())
