"""Read-only independent decisions from pinned traces and saved measurement pixels."""

import argparse
import gzip
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

from scribesim.handvalidate import upright_letters as evaluation, upright_measurement as measurement
from scribesim.handvalidate.specimen import digest


def image_pass(losses, ratio):
    values = [losses['global'], *losses['local'].values()]
    return (bool(losses['local']) and all(math.isfinite(value) and value <= .05 for value in values)
            and ratio is not None and math.isfinite(ratio) and 0 <= ratio <= .75)


def decision(record):
    spec, failures = evaluation.SPEC, []
    try:
        json.dumps(record, allow_nan=False)
    except ValueError:
        return {'numeric_pass': False, 'failures': ['nonfinite-record'], 'actual_ink_review': 'pending',
                'S2_accepted': False, 'real_accepted': False, 'context_training_allowed': False}
    if [row['fixture'] for row in record['fixtures']] != spec['fixtures']:
        failures.append('fixture-inventory')
    if set(record['controls']) != set(spec['controls']) or not all(row['detected'] for row in record['controls'].values()):
        failures.append('negative-controls')
    for row in record['fixtures']:
        name = row['fixture']['id']
        if set(row['motion']) != set(spec['refinements']):
            failures.append(name+':refinement-inventory')
        if (set(row['comparisons']) != set(spec['refinements'])-{'base'}
                or set(row['losses']) != {'nominal', *spec['refinements']}):
            failures.append(name+':measurement-inventory')
        for label, proof in row['motion'].items():
            if not measurement.motion_pass(proof, spec['criteria']):
                failures.append(name+':'+label+':actual-motion')
            if row['overlap'][label]['undeclared_pairs']:
                failures.append(name+':'+label+':overlap-attribution')
            if row['tracking_losses'][label] > spec['criteria']['actual_tracking_loss']:
                failures.append(name+':'+label+':tracking-image')
            if any(value > .05 for value in row['actual_levels'][label].values()):
                failures.append(name+':'+label+':actual-levels')
            if any(value > .05 for value in row['actual_port_errors_mm'][label].values()):
                failures.append(name+':'+label+':actual-ports')
        if any(value > 1e-8 for value in row['nominal_levels'].values()):
            failures.append(name+':nominal-levels')
        for label, loss in row['losses'].items():
            ratio = row['ratios'][label] if row['fixture']['kind'] == 'letter' else 0
            if not image_pass(loss, ratio):
                failures.append(name+':'+label+':target-image')
        for label, proof in row['comparisons'].items():
            if not proof['owner_match'] or any(not math.isfinite(proof[key]) or proof[key] > spec['criteria'][gate]
                    for key, gate in [('endpoint_mm', 'endpoint_mm'), ('event_time_s', 'event_time_s'), ('image_loss', 'convergence_loss')]):
                failures.append(name+':'+label+':convergence')
    return {'numeric_pass': not failures, 'failures': failures, 'actual_ink_review': 'pending',
            'S2_accepted': False, 'real_accepted': False, 'context_training_allowed': False}


def verify_record(source, record, directory):
    if (json.loads((directory/'candidate.json').read_text()) != source['candidate'] or record['optimization_evaluations'] != 0
            or record['actual_ink_review'] != 'pending' or any(record[key] is not False for key in ('S2_accepted', 'real_accepted', 'context_training_allowed'))):
        raise ValueError('Changed candidate or acceptance boundary')
    for row in record['fixtures']:
        fixture = row['fixture']
        model = evaluation.probe(source['candidate'], fixture)
        runs = json.loads(gzip.decompress((directory/f"{fixture['id']}-traces.json.gz").read_bytes()))
        if set(runs) != set(evaluation.SPEC['refinements']):
            raise ValueError('Incomplete saved refinements')
        labels = ['target', 'nominal', *runs, *[label+'-desired' for label in runs]]
        if fixture['kind'] == 'letter':
            labels.append('prior')
        images = {name: np.array(Image.open(directory/f"{fixture['id']}-{name}-metric.png")) for name in labels}
        proofs, overlaps = {}, {}
        for label, run in runs.items():
            step, dt = evaluation.SPEC['refinements'][label]
            if run['step_mm'] != step or run['dt_s'] != dt:
                raise ValueError('Unfrozen refinement')
            variant = evaluation.subdivide(model) if label == 'subdivision' else model
            proofs[label] = measurement.audit(variant, fixture, run, evaluation.SPEC)
            masks = {name: np.array(Image.open(directory/f"{fixture['id']}-{label}-owner-{name.replace(':', '_')}.png"), dtype=bool)
                     for name in dict.fromkeys(event['owner']['gesture_occurrence_id'] for event in run['trace'] if event['contact'])}
            overlaps[label] = measurement.overlap_proof(masks, variant, fixture['text'])
        expected = evaluation.record_fixture(model, fixture, runs, images, proofs, overlaps, evaluation.target(fixture, evaluation.SPEC)[1])
        if row != expected or row != json.loads((directory/f"{fixture['id']}.json").read_text()):
            raise ValueError('Saved metrics differ from independent raw evidence')
    controls = {**evaluation.model_controls(source['candidate']), **evaluation.trace_controls(model, fixture, runs['base'])}
    loss = float(measurement.stroke_loss(images['target'], np.array(Image.open(directory/'visible-shift-metric.png'))))
    controls['visible-shift'] = {'detected': loss > .05, 'loss': loss, 'gate': 'image'}
    if controls != record['controls'] or controls != json.loads((directory/'controls.json').read_text()):
        raise ValueError('Changed negative control evidence')


def inspect_run(directory, expected_report_sha256):
    directory = Path(directory)
    if not expected_report_sha256 or digest(directory/'report.json') != expected_report_sha256:
        raise ValueError('Consumer-pinned report hash required')
    adapter = SimpleNamespace(SPEC=evaluation.SPEC, identities=evaluation.identities, load_inputs=evaluation.load_inputs,
                              verify_record=verify_record, passed=evaluation.passed)
    result = evaluation.protocol.inspect(adapter, directory, expected_report_sha256)
    record = json.loads((directory/'seed-7/first/report.json').read_text())
    return {**result, **decision(record), 'reader_sha256': digest(Path(__file__)),
            'scope': evaluation.SPEC['scope'], 'read_only': True, 'rerenders': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path, default=evaluation.BASE/'run-001')
    parser.add_argument('--report-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_run(args.directory, args.report_sha256), indent=2))


if __name__ == '__main__':
    main()
