"""Read-only raw-evidence verification for the authorized placement experiment."""

import argparse
import gzip
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

from scripts import upright_placement_validation as runner
from scripts.handvalidate_upright_events import restore_owner_aliases
from scribesim.handvalidate import upright_evidence as historical
from scribesim.handvalidate import upright_letters as evaluation, upright_measurement as measurement
from scribesim.handvalidate.specimen import digest


def decision(record):
    failures, style = [], []
    spec, criteria = runner.SPEC, runner.SPEC['mechanical_criteria']
    refinements = set(spec['refinements'])
    try:
        json.dumps(record, allow_nan=False)
        if ([row['fixture'] for row in record['fixtures']] != spec['fixtures']
                or record['optimization_evaluations'] != 0 or record['actual_ink_review'] != 'held_out_pending'
                or record['decision_scope'] != spec['stage'] or any(record[key] is not False for key in
                    ('S2_accepted', 'real_accepted', 'context_training_allowed'))):
            raise ValueError('inventory or acceptance boundary')
        if set(record['controls']) != set(spec['physical_controls']) or any(control['detected'] is not True for control in record['controls'].values()):
            failures.append('negative-controls')
        for row in record['fixtures']:
            name = row['fixture']['id']
            local = {str(index) for index in range(len(row['fixture']['text']))}
            if set(row['regions']) != local or set(row['nominal_levels']) != local:
                raise ValueError('local inventory')
            for key in ('motion', 'overlap', 'tracking_losses', 'actual_levels', 'actual_port_errors_mm', 'nominal_actual_losses'):
                if set(row[key]) != refinements:
                    raise ValueError('refinement inventory')
            if (set(row['comparisons']) != refinements-{'base'} or set(row['losses']) != {'nominal', *refinements}
                    or set(row['ratios']) != set(row['losses'])):
                raise ValueError('measurement inventory')
            for losses in [*row['losses'].values(), *row['nominal_actual_losses'].values(), row['prior_losses']]:
                if set(losses['local']) != local or any(value < 0 for value in [losses['global'], *losses['local'].values()]):
                    raise ValueError('incomplete local loss')
            reference = row['approved_reference']
            if row['fixture'] in spec['known_regressions']:
                if reference != {'status': 'match', 'quality_pass': None, 'generalization_proven': False, 'scope': 'Exact scoped replay identity only'}:
                    failures.append(name+':known-reference')
            elif reference != runner.UNREVIEWED:
                raise ValueError('unreviewed placement inherited approval')
            for label, proof in row['motion'].items():
                if not measurement.motion_pass(proof, criteria):
                    failures.append(name+':'+label+':actual-motion')
                if row['overlap'][label]['undeclared_pairs']:
                    failures.append(name+':'+label+':overlap-attribution')
                if not 0 <= row['tracking_losses'][label] <= criteria['actual_tracking_loss']:
                    failures.append(name+':'+label+':tracking-image')
                ports = {f'{letter}:{part}' for letter in range(len(row['fixture']['text'])) for part in range(2)}
                if set(row['actual_levels'][label]) != local or set(row['actual_port_errors_mm'][label]) != ports:
                    raise ValueError('missing landmarks or ports')
                if any(not 0 <= value <= criteria['actual_landmark_mm_max'] for value in
                       [*row['actual_levels'][label].values(), *row['actual_port_errors_mm'][label].values()]):
                    failures.append(name+':'+label+':actual-landmarks')
            if any(not 0 <= value <= criteria['nominal_landmark_max'] for value in row['nominal_levels'].values()):
                failures.append(name+':nominal-levels')
            for label, loss in row['losses'].items():
                if not historical.image_pass(loss, row['ratios'][label]):
                    style.append(name+':'+label+':target-image')
            for label, proof in row['comparisons'].items():
                if proof['owner_match'] is not True or any(not 0 <= proof[key] <= criteria[gate] for key, gate in
                        [('endpoint_mm', 'endpoint_mm'), ('event_time_s', 'event_time_s'), ('image_loss', 'convergence_loss')]):
                    failures.append(name+':'+label+':convergence')
    except (ValueError, TypeError, KeyError, IndexError, OverflowError):
        failures.append('malformed-or-nonfinite-evidence')
    return {'execution_protocol_pass': not failures, 'failures': failures,
            'style_target': {'status': 'fail' if style else 'pass' if not failures else 'invalid', 'failures': style, 'role': 'diagnostic'},
            'held_out_nominal_actual_loss': 'report_only; no transferred 0.05 threshold',
            'historical_H021_numeric_pass': False, 'overall_admission': 'withheld', 'actual_ink_review': 'held_out_pending',
            'S2_accepted': False, 'real_accepted': False, 'context_training_allowed': False}


def verify_record(source, record, directory):
    if json.loads((directory/'candidate.json').read_text()) != source['candidate']:
        raise ValueError('Changed candidate')
    if [row['fixture'] for row in record['fixtures']] != runner.SPEC['fixtures']:
        raise ValueError('Incomplete fixture inventory')
    for row in record['fixtures']:
        fixture = row['fixture']
        model = runner.model_for_fixture(source['candidate'], fixture)
        runs = json.loads(gzip.decompress((directory/f"{fixture['id']}-traces.json.gz").read_bytes()))
        if set(runs) != set(runner.SPEC['refinements']):
            raise ValueError('Incomplete saved refinements')
        labels = ['target', 'nominal', 'prior', *runs, *[label+'-desired' for label in runs]]
        images = {label: np.array(Image.open(directory/f"{fixture['id']}-{label}-metric.png")) for label in labels}
        proofs, overlaps = {}, {}
        for label, run in runs.items():
            step, dt = runner.SPEC['refinements'][label]
            if run['step_mm'] != step or run['dt_s'] != dt:
                raise ValueError('Unfrozen refinement')
            variant = evaluation.subdivide(model) if label == 'subdivision' else model
            proofs[label] = measurement.audit(variant, fixture, run, evaluation.SPEC)
            masks = {name: np.array(Image.open(directory/f"{fixture['id']}-{label}-owner-{name.replace(':', '_')}.png"), dtype=bool)
                     for name in dict.fromkeys(event['owner']['gesture_occurrence_id'] for event in run['trace'] if event['contact'])}
            overlaps[label] = measurement.overlap_proof(masks, variant, fixture['text'])
        expected = evaluation.record_fixture(model, fixture, runs, images, proofs, overlaps,
                                              source['derived_references'][fixture['id']]['regions'])
        runner.require_local_frames(runs, expected['regions'])
        expected['approved_reference'] = runner.reference_result(source, fixture, images['base'])
        expected['nominal_actual_losses'] = {label: measurement.losses(images['nominal'], images[label], expected['regions'], evaluation.SPEC)
                                              for label in runs}
        if row != expected or row != json.loads((directory/f"{fixture['id']}.json").read_text()):
            raise ValueError('Saved metrics differ from independent raw evidence')
    controls = {**evaluation.model_controls(source['candidate']),
                **evaluation.trace_controls(model, fixture, restore_owner_aliases(model, fixture, runs['base']))}
    shifted = np.array(Image.open(directory/'visible-shift-metric.png'))
    loss = float(measurement.stroke_loss(images['base'], shifted))
    controls['visible-shift'] = {'detected': loss > runner.AUTH['visible_shift_detection_loss'], 'loss': loss,
                                'gate': 'image', 'reference': 'same-run-unshifted-actual'}
    if controls != record['controls'] or controls != json.loads((directory/'controls.json').read_text()):
        raise ValueError('Changed negative control evidence')


def inspect_run(directory, expected_report_sha256):
    directory = Path(directory)
    if not expected_report_sha256:
        raise ValueError('Consumer-pinned report hash required')
    adapter = SimpleNamespace(SPEC=runner.SPEC, identities=runner.identities, load_inputs=runner.load_inputs,
                              verify_record=verify_record, passed=lambda record: decision(record)['execution_protocol_pass'])
    result = evaluation.protocol.inspect(adapter, directory, expected_report_sha256)
    summaries = []
    for seed in runner.SPEC['seeds']:
        for label in ('first', 'replay'):
            record = json.loads((directory/f'seed-{seed}/{label}/report.json').read_text())
            summaries.append({'seed': seed, 'process': label, **decision(record)})
    return {**result, 'decisions': summaries, 'reader_sha256': digest(Path(__file__)),
            'read_only': True, 'rerenders': 0, 'controller_executions': 0,
            'scope': runner.SPEC['stage'], 'overall_admission': 'withheld', 'context_training_allowed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path, default=runner.BASE/'run-001')
    parser.add_argument('--report-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_run(args.directory, args.report_sha256), indent=2))


if __name__ == '__main__':
    main()
