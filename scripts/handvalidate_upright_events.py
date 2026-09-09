"""Read-only H021 replay verification with original in-memory control aliasing."""

import argparse
import copy
import gzip
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

from scribesim.handvalidate import upright_event_replay as replay, upright_letters as evaluation
from scribesim.handvalidate import upright_measurement as measurement, upright_evidence as reader
from scribesim.handvalidate.specimen import digest


def restore_owner_aliases(model, fixture, run):
    bundle = measurement.action_bundle(fixture['text'], model, step_mm=run['step_mm'], include_curve_positions=True)
    compiled = measurement.compile_gestures(fixture['text'], model)['strokes']
    timed = measurement.retime_curve_tangents(bundle.plan, bundle.owners, compiled)
    owners = [bundle.owners[index] for index in timed.source_indices]
    restored = copy.deepcopy(run)
    for row in restored['trace']:
        index = row['plan_index']
        if type(index) is not int or not 0 <= index < len(owners) or row['owner'] != owners[index]:
            raise ValueError('Saved owner differs from original mapped owner')
        row['owner'] = owners[index]
    if restored != run:
        raise ValueError('Owner alias restoration changed saved values')
    return restored


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
    controls = {**evaluation.model_controls(source['candidate']),
                **evaluation.trace_controls(model, fixture, restore_owner_aliases(model, fixture, runs['base']))}
    loss = float(measurement.stroke_loss(images['target'], np.array(Image.open(directory/'visible-shift-metric.png'))))
    controls['visible-shift'] = {'detected': loss > .05, 'loss': loss, 'gate': 'image'}
    if controls != record['controls'] or controls != json.loads((directory/'controls.json').read_text()):
        raise ValueError('Changed negative control evidence')


def inspect_run(directory, expected_report_sha256):
    directory = Path(directory)
    if not expected_report_sha256 or digest(directory/'report.json') != expected_report_sha256:
        raise ValueError('Consumer-pinned report hash required')
    adapter = SimpleNamespace(SPEC=replay.SPEC, identities=replay.identities, load_inputs=replay.load_inputs,
                              verify_record=verify_record, passed=replay.passed)
    result = evaluation.protocol.inspect(adapter, directory, expected_report_sha256)
    source = replay.load_inputs()
    report = json.loads((directory/'report.json').read_text())
    combined = replay.check_combined(json.loads((directory/'execution.json').read_text())['ledger'], source['prior_attempt']['debits'])
    if report['prior_attempt'] != source['prior_attempt'] or report['combined_renders'] != combined:
        raise ValueError('Changed combined debit')
    record = json.loads((directory/'seed-7/first/report.json').read_text())
    return {**result, **reader.decision(record), 'combined_renders': combined,
        'reader_sha256': digest(Path(__file__)), 'decision_reader_sha256': digest(Path(reader.__file__)),
        'evaluation_complete': report['evaluation_complete'], 'seeds': report['seeds'],
        'control_aliasing': 'original-mapped-owner-v1', 'scope': replay.SPEC['scope'],
        'read_only': True, 'rerenders': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path, default=replay.BASE/'run-001')
    parser.add_argument('--report-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_run(args.directory, args.report_sha256), indent=2))


if __name__ == '__main__':
    main()
