"""Read-only verification of saved H021 fixtures; incomplete evidence never admits."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.handvalidate import upright_continuation as continuation, upright_letters as evaluation
from scribesim.handvalidate import upright_measurement as measurement, upright_evidence as reader
from scribesim.handvalidate.specimen import digest


REPORT_SHA256 = 'cc4a202e570d292ad899493e5ca53e7cad7b4f796f5e87349af5274d9e587b5c'


def inspect_partial(directory, expected_report_sha256):
    directory = Path(directory)
    if not expected_report_sha256 or digest(directory/'report.json') != expected_report_sha256:
        raise ValueError('Consumer-pinned report hash required')
    report = json.loads((directory/'report.json').read_text())
    source = continuation.load_inputs()
    frozen = json.loads((directory/'freeze.json').read_text())
    if frozen != {'spec': continuation.SPEC, 'code_sha256': continuation.identities(), 'source': source}:
        raise ValueError('Changed frozen continuation identities')
    if report['status'] != 'blocked' or report['evaluation_complete'] is not False or report['seeds']:
        raise ValueError('This partial inspector cannot admit a completed evaluation')
    if report['optimization_evaluations'] != 0 or any(report[key] is not False for key in ('S2_accepted', 'real_accepted', 'context_training_allowed')):
        raise ValueError('Overstated incomplete evidence')
    inventory = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()}-{'report.json'}
    if inventory != set(report['artifacts']):
        raise ValueError('Incomplete artifact inventory')
    evaluation.protocol.foundation.primitives.verify_artifacts(directory, report['artifacts'])
    ledger = json.loads((directory/'execution.json').read_text())['ledger']
    if len(ledger) != 1 or ledger[0]['seed'] != 7 or ledger[0]['process'] != 'first':
        raise ValueError('Unsupported partial ledger')
    worker = directory/'seed-7/first'
    record = json.loads((worker/'report.json').read_text())
    receipt = json.loads((worker/'execution.json').read_text())
    debit = source['prior_attempt']['debits']['7']
    entry = ledger[0]
    if (record['status'] != 'blocked' or record['renders'] != receipt['renders'] or report['renders'] != receipt['renders']
            or entry['renders'] != receipt['renders'] or entry['cumulative_renders'] != receipt['renders']
            or entry['combined_renders'] != receipt['renders']+debit['renders'] or entry['combined_renders'] > 5000
            or entry['combined_seconds'] != entry['cumulative_seconds']+debit['seconds']
            or not receipt['elapsed_seconds'] <= entry['cumulative_seconds'] or entry['combined_seconds'] > 1800):
        raise ValueError('Changed partial budget debit')
    if json.loads((worker/'candidate.json').read_text()) != source['candidate']:
        raise ValueError('Changed candidate')
    rows = []
    for fixture in evaluation.SPEC['fixtures']:
        path = worker/(fixture['id']+'.json')
        if not path.exists():
            continue
        row = json.loads(path.read_text())
        model = evaluation.probe(source['candidate'], fixture)
        runs = json.loads(gzip.decompress((worker/(fixture['id']+'-traces.json.gz')).read_bytes()))
        if set(runs) != set(evaluation.SPEC['refinements']):
            raise ValueError('Incomplete saved fixture refinements')
        labels = ['target', 'nominal', *runs, *[name+'-desired' for name in runs]]
        if fixture['kind'] == 'letter':
            labels.append('prior')
        images = {name: np.array(Image.open(worker/f"{fixture['id']}-{name}-metric.png")) for name in labels}
        proofs, overlaps = {}, {}
        for label, run in runs.items():
            step, dt = evaluation.SPEC['refinements'][label]
            if run['step_mm'] != step or run['dt_s'] != dt:
                raise ValueError('Changed refinement')
            variant = evaluation.subdivide(model) if label == 'subdivision' else model
            proofs[label] = measurement.audit(variant, fixture, run, evaluation.SPEC)
            masks = {name: np.array(Image.open(worker/f"{fixture['id']}-{label}-owner-{name.replace(':', '_')}.png"), dtype=bool)
                     for name in dict.fromkeys(event['owner']['gesture_occurrence_id'] for event in run['trace'] if event['contact'])}
            overlaps[label] = measurement.overlap_proof(masks, variant, fixture['text'])
        expected = evaluation.record_fixture(model, fixture, runs, images, proofs, overlaps, evaluation.target(fixture, evaluation.SPEC)[1])
        if row != expected:
            raise ValueError('Saved partial fixture differs from independent raw evidence: '+fixture['id'])
        rows.append(row)
    completed = [row['fixture']['id'] for row in rows]
    outcome = reader.decision({'fixtures': rows, 'controls': {}})
    letters = {}
    for row in rows:
        if row['fixture']['kind'] != 'letter':
            continue
        letters[row['fixture']['text']] = {
            'per_run_motion_pass': all(measurement.motion_pass(proof, evaluation.SPEC['criteria']) for proof in row['motion'].values()),
            'contact_runs': row['motion']['base']['contact_runs'],
            'max_corridor_mm': max(proof['metrics']['corridor_mm'] for proof in row['motion'].values()),
            'max_clock_error_s': max(proof['metrics']['clock_error_s'] for proof in row['motion'].values()),
            'max_port_error_mm': max(value for values in row['actual_port_errors_mm'].values() for value in values.values()),
            'max_level_error_mm': max(value for values in row['actual_levels'].values() for value in values.values()),
            'undeclared_overlap_pairs': sum(proof['undeclared_pairs'] for proof in row['overlap'].values()),
            'base_target_loss': row['losses']['base'], 'base_relative_loss': row['ratios']['base'],
            'comparisons': row['comparisons']}
    return {**outcome, 'status': 'incomplete', 'numeric_pass': False, 'evaluation_complete': False,
            'report_sha256': expected_report_sha256, 'reader_sha256': digest(Path(__file__)),
            'artifacts_verified': len(inventory), 'completed_fixtures': completed,
            'missing_fixtures': [fixture['id'] for fixture in evaluation.SPEC['fixtures'] if fixture['id'] not in completed],
            'controls_executed': False, 'replay_complete': False, 'seeds_completed': [], 'letters': letters,
            'combined_renders': entry['combined_renders'], 'combined_seconds': entry['combined_seconds'],
            'rerenders': 0, 'scope': 'Partial saved seed-7 evidence only. No replay, full protocol pass or acceptance. No candidate or archive modification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path, default=continuation.BASE/'run-001')
    parser.add_argument('--report-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_partial(args.directory, args.report_sha256), indent=2))


if __name__ == '__main__':
    main()
