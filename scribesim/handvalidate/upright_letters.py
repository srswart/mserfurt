"""Opt-in immutable actual-contact evaluation of the reviewed upright candidate."""

import argparse
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

from scribesim.evo.nib_contact import ContactSample, VERSION
from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide, validate_gestures
from scribesim.handvalidate import frozen_replay as protocol, tangent_motion as runtime
from scribesim.handvalidate import upright_measurement as measurement
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.foundation_primitives import compressed
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json
from scribesim.handvalidate.upright_targets import target


BASE = ROOT / 'shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/upright/validation'
SPEC_PATH = BASE / 'spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
SOURCE = BASE.parent / 'run-001'
PRIOR = BASE.parents[1] / 'validation/run-001/seed-7/first/candidate.json'


def identities():
    paths = list((ROOT/'scribesim').rglob('*.py')) + [SPEC_PATH]
    paths += list((ROOT/'shared/training/konrad_hand_recovery/stroke_gestures_v2').rglob('spec-*.json'))
    return {str(path.relative_to(ROOT)): digest(path) for path in sorted(set(paths))}


def require_candidate(candidate):
    if digest(SOURCE/'candidate.json') != SPEC['candidate_file_sha256'] or candidate != json.loads((SOURCE/'candidate.json').read_text()):
        raise ValueError('Exact reviewed candidate required')
    validate_gestures(candidate)


def load_inputs():
    for path, key in [(SOURCE/'candidate.json', 'candidate_file_sha256'), (SOURCE/'report.json', 'source_report_sha256'),
                      (SOURCE/'owner-review.json', 'source_owner_review_sha256'), (PRIOR, 'prior_file_sha256')]:
        if digest(path) != SPEC[key]:
            raise ValueError('Changed pinned source: '+path.name)
    report = json.loads((SOURCE/'report.json').read_text())
    inventory = {path.name for path in SOURCE.iterdir() if path.is_file()} - {'report.json', 'owner-review.json'}
    if inventory != set(report['artifacts']):
        raise ValueError('Incomplete nominal archive')
    for name, checksum in report['artifacts'].items():
        if Path(name).name != name or digest(SOURCE/name) != checksum:
            raise ValueError('Changed nominal artifact')
    for name, checksum in report['source_identities'].items():
        path = (ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != checksum:
            raise ValueError('Changed nominal source identity')
    review = json.loads((SOURCE/'owner-review.json').read_text())
    if review['candidate_sha256'] != SPEC['candidate_file_sha256'] or review['status'] != 'approved_nominal_preview' or any(
            review['letters'][letter]['verdict'] != 'keep' for letter in 'num'):
        raise ValueError('Exact candidate-bound nominal review required')
    candidate = json.loads((SOURCE/'candidate.json').read_text())
    require_candidate(candidate)
    return {'candidate': candidate, 'prior': json.loads(PRIOR.read_text()),
            'nominal_review_sha256': SPEC['source_owner_review_sha256']}


def probe(candidate, fixture):
    if fixture not in SPEC['fixtures']:
        raise ValueError('Unfrozen fixture')
    model = copy.deepcopy(candidate)
    if fixture['kind'] != 'letter':
        name = fixture['name']
        if fixture['kind'] == 'primitive':
            model['gestures'] = {'probe': {'action': 'fixed', 'strokes': [{'primitive': name,
                'offset': [0, 0], 'scale': 1, 'rotation_deg': 0, 'transition': 'start'}]}}
            name = 'probe'
        model['recipes'] = {'i': {'logical': 'i', 'visible': 'i', 'advance': 2, 'gestures': [{
            'gesture': name, 'offset': [-.2, 0], 'scale': 1, 'rotation_deg': 0, 'transition': 'start', 'overlap_with': []}]}}
    for recipe in model['recipes'].values():
        for instance in recipe['gestures']:
            instance['offset'] = [value+shift for value, shift in zip(instance['offset'], fixture['shift'])]
    validate_gestures(model)
    return model


def subdivide(model):
    result = copy.deepcopy(model)
    for primitive in result['primitives'].values():
        divided = []
        for cubic in primitive['cubics']:
            controls = np.asarray(cubic)
            edges = (controls[:-1]+controls[1:])/2
            inner = (edges[:-1]+edges[1:])/2
            midpoint = (inner[0]+inner[1])/2
            divided.extend([[controls[0].tolist(), edges[0].tolist(), inner[0].tolist(), midpoint.tolist()],
                            [midpoint.tolist(), inner[1].tolist(), edges[2].tolist(), controls[3].tolist()]])
        primitive['cubics'] = divided
    validate_gestures(result)
    return result


def nominal(model, text):
    guide = gesture_guide(text, model, step_mm=.005).guide
    return [ContactSample(point.x_mm, point.y_mm, point.contact, .45, .5 if point.contact else 0, 40) for point in guide.samples]


def paint(path, dpi=180):
    if not measurement.contained(path, SPEC['frame_mm']):
        raise ValueError('Incomplete finite-ink frame')
    return paint_trajectory(path, SPEC['frame_mm'], dpi=dpi, contact_version=VERSION)


def model_controls(candidate):
    controls = {}
    for name in ('inserted-lift', 'gap', 'false-smooth-reversal', 'overlap-owner', 'geometry', 'tool', 'climbing'):
        changed = copy.deepcopy(candidate)
        instance = changed['recipes']['n']['gestures'][1]
        if name == 'inserted-lift':
            instance['transition'] = 'lift'
        elif name == 'gap':
            instance['offset'][0] += .1
        elif name == 'false-smooth-reversal':
            instance['transition'] = 'smooth'
        elif name == 'overlap-owner':
            instance['overlap_with'] = []
        elif name == 'geometry':
            changed['primitives']['rise']['cubics'][0][1][0] += .001
        elif name == 'tool':
            changed['nib_width_mm'] = .46
        else:
            for recipe in changed['recipes'].values():
                for part in recipe['gestures']:
                    part['offset'][1] += .1
        reason = None
        try:
            validate_gestures(changed)
            compiled = compile_gestures('n', changed)['strokes']
            if len({row['contact_run_id'] for row in compiled}) != 1:
                raise ValueError('Continuous contact run changed')
            fixture = next(row for row in SPEC['fixtures'] if row['id'] == 'letter-n')
            if any(value > SPEC['criteria']['nominal_landmark_max'] for value in measurement.levels(changed, fixture).values()):
                raise ValueError('Climbing nominal landmarks')
            require_candidate(changed)
        except ValueError as error:
            reason = str(error)
        controls[name] = {'detected': reason is not None, 'reason': reason}
    return controls


def trace_controls(model, fixture, run):
    result = {}
    for name in ('trace-owner', 'trace-lift', 'desired-as-actual'):
        changed = copy.deepcopy(run)
        contact = [row for row in changed['trace'] if row['contact']]
        selected = contact[len(contact)//2]
        if name == 'trace-owner':
            selected['owner']['overlap_contributors'] = ['invented']
        elif name == 'trace-lift':
            selected['contact'], selected['pressure'] = False, 0
        else:
            for row in changed['trace']:
                row['to_mm'] = row['desired_mm'][:]
        proof = measurement.audit(model, fixture, changed, SPEC)
        intended = {'trace-owner': 'owner', 'trace-lift': 'contact', 'desired-as-actual': 'dynamics'}[name]
        result[name] = {'detected': proof['errors'][intended] > 0, 'gate': intended, 'errors': proof['errors']}
    return result


def measure(source, fixture, budget, directory):
    model = probe(source['candidate'], fixture)
    target_path, regions = target(fixture, SPEC)
    paths = {'target': target_path, 'nominal': nominal(model, fixture['text'])}
    if fixture['kind'] == 'letter':
        paths['prior'] = nominal(probe(source['prior'], fixture), fixture['text'])
    images = {name: budget.render(paint, path) for name, path in paths.items()}
    runs, proofs, overlaps = {}, {}, {}
    for label, (step, dt) in SPEC['refinements'].items():
        variant = subdivide(model) if label == 'subdivision' else model
        run = runtime.execute(variant, fixture['text'], step=step, dt=dt, budget=budget, physical=True, frame=SPEC['frame_mm'])
        runs[label] = {key: value for key, value in run.items() if key != 'images'}
        images[label] = run['images']['actual']
        images[label+'-desired'] = run['images']['desired']
        proofs[label] = measurement.audit(variant, fixture, runs[label], SPEC)
        masks = budget.render(measurement.overlap_masks, run, SPEC)
        overlaps[label] = measurement.overlap_proof(masks, variant, fixture['text'])
        for owner, mask in masks.items():
            Image.fromarray(mask).save(directory/f"{fixture['id']}-{label}-owner-{owner.replace(':', '_')}.png")
    for name, pixels in images.items():
        Image.fromarray(pixels).save(directory/f"{fixture['id']}-{name}-metric.png")
    paths['actual'] = measurement.trajectory(runs['base'])
    if fixture['id'] in {'letter-n', 'letter-u', 'letter-m', 'placed-mu'}:
        for name, path in paths.items():
            Image.fromarray(budget.render(paint, path, SPEC['presentation_dpi'])).save(directory/f"{fixture['id']}-{name}-full.png")
    row = record_fixture(model, fixture, runs, images, proofs, overlaps, regions)
    compressed(directory/f"{fixture['id']}-traces.json.gz", runs)
    write_json(directory/f"{fixture['id']}.json", row)
    return row, runs


def record_fixture(model, fixture, runs, images, proofs, overlaps, regions):
    losses = {label: measurement.losses(images['target'], images[label], regions, SPEC) for label in ['nominal', *SPEC['refinements']]}
    before = measurement.losses(images['target'], images['prior'], regions, SPEC) if 'prior' in images else None
    ratios = {label: losses[label]['global']/before['global'] if before and before['global'] > 0 else None for label in losses}
    return {'fixture': fixture, 'model_sha256': object_digest(model), 'regions': regions,
        'nominal_levels': measurement.levels(model, fixture), 'actual_levels': {label: measurement.actual_levels(run, fixture) for label, run in runs.items()},
        'actual_port_errors_mm': {label: measurement.port_errors(model, fixture, run) for label, run in runs.items()},
        'slant_diagnostics': measurement.slant_diagnostics(runs['base']),
        'motion': proofs, 'overlap': overlaps, 'losses': losses, 'prior_losses': before, 'ratios': ratios,
        'tracking_losses': {label: float(measurement.stroke_loss(images[label+'-desired'], images[label])) for label in runs},
        'comparisons': {label: measurement.comparison(runs['base'], run, images['base'], images[label]) for label, run in runs.items() if label != 'base'}}


def evaluate(source, budget, directory):
    rows = []
    write_json(directory/'candidate.json', source['candidate'])
    for fixture in SPEC['fixtures']:
        row, runs = measure(source, fixture, budget, directory)
        rows.append(row)
    model = probe(source['candidate'], fixture)
    controls = {**model_controls(source['candidate']), **trace_controls(model, fixture, runs['base'])}
    shifted = [replace(point, x_mm=point.x_mm+SPEC['visible_shift_mm']) for point in measurement.trajectory(runs['base'])]
    pixels = budget.render(paint, shifted)
    Image.fromarray(pixels).save(directory/'visible-shift-metric.png')
    target_pixels = np.array(Image.open(directory/f"{fixture['id']}-target-metric.png"))
    loss = float(measurement.stroke_loss(target_pixels, pixels))
    controls['visible-shift'] = {'detected': loss > SPEC['criteria']['absolute_loss_max'], 'loss': loss, 'gate': 'image'}
    write_json(directory/'controls.json', controls)
    return {'fixtures': rows, 'controls': controls, 'optimization_evaluations': 0,
            'actual_ink_review': 'pending', 'S2_accepted': False, 'real_accepted': False, 'context_training_allowed': False}


def passed(record):
    from scribesim.handvalidate.upright_evidence import decision
    return decision(record)['numeric_pass']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--maximum', type=int)
    parser.add_argument('--seconds', type=float)
    args = parser.parse_args()
    module = sys.modules[__name__]
    module.__name__ = 'scribesim.handvalidate.upright_letters'
    report = protocol.worker(module, args.worker, args.seed, args.maximum, args.seconds) if args.worker else protocol.build(module)
    print(json.dumps({key: value for key, value in report.items() if key not in {'artifacts', 'fixtures'}}, indent=2))


if __name__ == '__main__':
    main()
