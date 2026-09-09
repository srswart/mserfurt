"""One authorized frozen placement experiment; no fitting or layer admission."""

import argparse
import copy
from dataclasses import asdict, replace
from itertools import groupby
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

from scripts import upright_reference_contract as contract
from scripts.handvalidate_upright_events import restore_owner_aliases
from scribesim.handvalidate import upright_letters as evaluation, upright_measurement as measurement
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = evaluation.BASE/'placement-validation-v1'
AUTH_PATH = BASE/'authorization.json'
AUTH = json.loads(AUTH_PATH.read_text())
PREPARED = contract.BASE/'snapshot-001'
UNREVIEWED = {'status': 'not_applicable', 'owner_appearance': 'not_reviewed',
              'quality_pass': None, 'generalization_proven': False}


def prepared_protocol():
    for name, key in [('report.json', 'prepared_report_sha256'), ('protocol.json', 'prepared_protocol_sha256'),
                      ('registry.json', 'registry_sha256')]:
        if digest(PREPARED/name) != AUTH[key]:
            raise ValueError('Changed prepared contract pin')
    if (AUTH['approved'] is not True or AUTH['optimization_evaluations'] != 0
            or AUTH['budget_per_seed_including_replay'] != {'renders': 5000, 'seconds': 1800, 'automatic_retries': 0}
            or AUTH['visible_shift_detection_loss'] != .05):
        raise ValueError('Unapproved execution allowance')
    return json.loads((PREPARED/'protocol.json').read_text())


PREPARATION = prepared_protocol()
SPEC = {key: PREPARATION[key] for key in ('version', 'known_regressions', 'held_out_placements', 'held_out_policy',
        'frame_mm', 'local_padding_mm', 'metric_dpi', 'presentation_dpi', 'refinements', 'mechanical_criteria',
        'regression_mode', 'regression_variant_tolerance', 'held_out_nominal_actual_loss', 'style_reference',
        'physical_controls', 'seeds', 'fresh_process_replays_per_seed', 'optimization_evaluations')}
SPEC.update({'stage': 'held-out-approved-style-mechanics-v1', 'authorization': AUTH,
        'execution_authorized': True, 'budget_authorized': True,
        'fixtures': [*PREPARATION['known_regressions'], *[
            {key: row[key] for key in ('id', 'text', 'shift')} | {'kind': 'letter'}
            for row in PREPARATION['held_out_placements']]]})


def identities():
    paths = [Path(__file__), ROOT/'scripts/upright_placement_evidence.py', AUTH_PATH,
             ROOT/'scripts/upright_reference_contract.py', ROOT/'scripts/handvalidate_upright_events.py',
             ROOT/'scripts/handvalidate_upright_targets.py']
    return {**contract.reconciliation.replay.identities(),
            **{str(path.relative_to(ROOT)): digest(path) for path in paths}}


def model_for_fixture(candidate, fixture):
    if fixture not in SPEC['fixtures']:
        raise ValueError('Unfrozen fixture')
    model = copy.deepcopy(candidate)
    for recipe in model['recipes'].values():
        for instance in recipe['gestures']:
            instance['offset'] = [value+shift for value, shift in zip(instance['offset'], fixture['shift'])]
    evaluation.validate_gestures(model)
    return model


def load_inputs():
    if prepared_protocol() != PREPARATION:
        raise ValueError('Changed preparation')
    contract.inspect(PREPARED, AUTH['prepared_report_sha256'])
    registry = json.loads((PREPARED/'registry.json').read_text())
    source = contract.reconciliation.replay.load_inputs()
    derived = {}
    for fixture in SPEC['fixtures']:
        model = model_for_fixture(source['candidate'], fixture)
        target, regions = evaluation.target(fixture, evaluation.SPEC)
        paths = {'target': target, 'nominal': evaluation.nominal(model, fixture['text']),
                 'prior': evaluation.nominal(model_for_fixture(source['prior'], fixture), fixture['text'])}
        if not all(measurement.contained(path, SPEC['frame_mm']) for path in paths.values()):
            raise ValueError('Incomplete reference frame')
        groups = [list(points) for contact, points in groupby(paths['nominal'], key=lambda point: point.contact) if contact]
        if len(groups) != len(fixture['text']) or any(not measurement.contained(points, regions[str(index)])
                                                    for index, points in enumerate(groups)):
            raise ValueError('Incomplete per-letter nominal reference window')
        derived[fixture['id']] = {'paths': {name: [asdict(point) for point in path] for name, path in paths.items()},
            'regions': regions, 'nominal_provenance': 'candidate-derived; not independent style truth',
            'style_provenance': registry['style_reference'], 'candidate_sha256': evaluation.SPEC['candidate_file_sha256']}
    return {**source, 'registry': registry, 'derived_references': derived,
            'core_identities': contract.reconciliation.replay.identities()}


def reference_result(source, fixture, pixels):
    reference = source['registry']['references'].get('actual:'+fixture['id'])
    if reference is None:
        return UNREVIEWED.copy()
    context = {'candidate_sha256': digest(evaluation.SOURCE/'candidate.json'),
        'source_code_sha256': object_digest(source['core_identities']), 'fixture': fixture,
        'frame_mm': SPEC['frame_mm'], 'dpi': SPEC['metric_dpi'], 'tool_version': 'physical-edge-v1',
        'fixed_tool_sha256': object_digest({key: source['candidate'][key] for key in
            ('nib_width_mm', 'nib_angle_deg', 'x_height_mm', 'actions')}),
        'refinement': dict(zip(('step_mm', 'dt_s'), SPEC['refinements']['base']))}
    return contract.compare_reference(reference, pixels, context)


def record_fixture(source, fixture, runs, images, proofs, overlaps):
    frozen = source['derived_references'][fixture['id']]
    require_local_frames(runs, frozen['regions'])
    row = evaluation.record_fixture(model_for_fixture(source['candidate'], fixture), fixture, runs, images,
                                    proofs, overlaps, frozen['regions'])
    return {**row, 'approved_reference': reference_result(source, fixture, images['base']),
            'nominal_actual_losses': {label: measurement.losses(images['nominal'], images[label], frozen['regions'], evaluation.SPEC)
                                      for label in SPEC['refinements']}}


def require_local_frames(runs, regions):
    for run in runs.values():
        for letter, bounds in regions.items():
            selected = {'trace': [row for row in run['trace'] if row['contact'] and row['owner']['letter'] == int(letter)]}
            if not measurement.contained(measurement.trajectory(selected), bounds):
                raise ValueError('Incomplete per-letter actual ink frame')


def measure(source, fixture, budget, directory):
    model = model_for_fixture(source['candidate'], fixture)
    paths = {name: [evaluation.ContactSample(**point) for point in path]
             for name, path in source['derived_references'][fixture['id']]['paths'].items()}
    images = {name: budget.render(evaluation.paint, path) for name, path in paths.items()}
    runs, proofs, overlaps = {}, {}, {}
    for label, (step, dt) in SPEC['refinements'].items():
        variant = evaluation.subdivide(model) if label == 'subdivision' else model
        run = evaluation.runtime.execute(variant, fixture['text'], step=step, dt=dt, budget=budget, physical=True, frame=SPEC['frame_mm'])
        runs[label] = {key: value for key, value in run.items() if key != 'images'}
        images[label], images[label+'-desired'] = run['images']['actual'], run['images']['desired']
        proofs[label] = measurement.audit(variant, fixture, runs[label], evaluation.SPEC)
        masks = budget.render(measurement.overlap_masks, run, evaluation.SPEC)
        overlaps[label] = measurement.overlap_proof(masks, variant, fixture['text'])
        for owner, mask in masks.items():
            Image.fromarray(mask).save(directory/f"{fixture['id']}-{label}-owner-{owner.replace(':', '_')}.png")
    for name, pixels in images.items():
        Image.fromarray(pixels).save(directory/f"{fixture['id']}-{name}-metric.png")
    paths['actual'] = measurement.trajectory(runs['base'])
    for name in ('target', 'nominal', 'actual'):
        Image.fromarray(budget.render(evaluation.paint, paths[name], SPEC['presentation_dpi'])).save(directory/f"{fixture['id']}-{name}-full.png")
    row = record_fixture(source, fixture, runs, images, proofs, overlaps)
    evaluation.compressed(directory/f"{fixture['id']}-traces.json.gz", runs)
    write_json(directory/f"{fixture['id']}.json", row)
    return row, runs, images['base']


def shift_control(base, shifted):
    loss = float(measurement.stroke_loss(base, shifted))
    return {'detected': loss > AUTH['visible_shift_detection_loss'], 'loss': loss,
            'gate': 'image', 'reference': 'same-run-unshifted-actual'}


def evaluate(source, budget, directory):
    rows = []
    write_json(directory/'candidate.json', source['candidate'])
    for fixture in SPEC['fixtures']:
        row, runs, pixels = measure(source, fixture, budget, directory)
        rows.append(row)
    model = model_for_fixture(source['candidate'], fixture)
    controls = {**evaluation.model_controls(source['candidate']),
                **evaluation.trace_controls(model, fixture, restore_owner_aliases(model, fixture, runs['base']))}
    shifted = [replace(point, x_mm=point.x_mm+evaluation.SPEC['visible_shift_mm']) for point in measurement.trajectory(runs['base'])]
    shifted_pixels = budget.render(evaluation.paint, shifted)
    Image.fromarray(shifted_pixels).save(directory/'visible-shift-metric.png')
    controls['visible-shift'] = shift_control(pixels, shifted_pixels)
    write_json(directory/'controls.json', controls)
    return {'fixtures': rows, 'controls': controls, 'optimization_evaluations': 0, 'decision_scope': SPEC['stage'],
            'actual_ink_review': 'held_out_pending', 'S2_accepted': False, 'real_accepted': False, 'context_training_allowed': False}


def passed(record):
    from scripts.upright_placement_evidence import decision
    return decision(record)['execution_protocol_pass']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--maximum', type=int)
    parser.add_argument('--seconds', type=float)
    args = parser.parse_args()
    module = sys.modules[__name__]
    module.__name__ = 'scripts.upright_placement_validation'
    report = evaluation.protocol.worker(module, args.worker, args.seed, args.maximum, args.seconds) if args.worker else evaluation.protocol.build(module)
    print(json.dumps({key: value for key, value in report.items() if key not in {'artifacts', 'fixtures'}}, indent=2))


if __name__ == '__main__':
    main()
