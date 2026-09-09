"""Diagnose approved appearance versus analytic targets from pinned saved evidence."""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handvalidate import upright_event_replay as replay, upright_letters as evaluation
from scribesim.handvalidate import upright_measurement as measurement, upright_targets
from scribesim.handvalidate.specimen import ROOT, digest


BASE = evaluation.BASE/'reconciliation-001'
PROTOCOL_PATH = BASE/'protocol.json'


def verify_pins(base, pins):
    base = Path(base).resolve()
    for name, checksum in pins.items():
        path = (base/name).resolve()
        if not path.is_relative_to(base):
            raise ValueError('Source path escapes evidence root')
        if not path.is_file() or digest(path) != checksum:
            raise ValueError('Changed source pin: '+name)


def primitive_ports(candidate, spec):
    families = upright_targets.shapes(spec)
    scale = spec['target']['x_height_mm']
    result = {}
    for name, primitive in candidate['primitives'].items():
        entry, end = np.array(primitive['cubics'][0][0])*scale, np.array(primitive['cubics'][-1][-1])*scale
        target_entry, target_end = families[name][0][0]*scale, families[name][-1][-1]*scale
        result[name] = {'approved_entry_mm': entry.tolist(), 'approved_exit_mm': end.tolist(),
            'analytic_entry_mm': target_entry.tolist(), 'analytic_exit_mm': target_end.tolist(),
            'entry_difference_mm': float(np.linalg.norm(entry-target_entry)),
            'exit_difference_mm': float(np.linalg.norm(end-target_end))}
    return result


def reconcile():
    protocol = json.loads(PROTOCOL_PATH.read_text())
    verify_pins(evaluation.BASE, protocol['source_pins'])
    source = replay.load_inputs()
    directory = replay.BASE/'run-001'
    frozen = json.loads((directory/'freeze.json').read_text())
    if frozen != {'spec': replay.SPEC, 'code_sha256': replay.identities(), 'source': source}:
        raise ValueError('Frozen source identities changed')
    report = json.loads((directory/'report.json').read_text())
    inventory = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()}-{'report.json'}
    if inventory != set(report['artifacts']):
        raise ValueError('Changed artifact inventory')
    verify_pins(directory, report['artifacts'])
    receipt = json.loads((replay.BASE/'inspection.json').read_text())
    review = json.loads((replay.BASE/'actual-review.json').read_text())
    if (receipt['report_sha256'] != digest(directory/'report.json') or receipt['numeric_pass'] is not False
            or receipt['evaluation_complete'] is not True or report['status'] != 'fail'
            or receipt['reader_sha256'] != digest(ROOT/'scripts/handvalidate_upright_events.py')
            or review['candidate_sha256'] != digest(evaluation.SOURCE/'candidate.json')
            or review['report_sha256'] != receipt['report_sha256'] or review['status'] != 'approved_actual_ink'
            or any(row['verdict'] != 'keep' for row in review['letters'].values())
            or review['placement_probes']['placed-mu']['verdict'] != 'keep'):
        raise ValueError('Unverified source decision or owner approval')
    worker = directory/protocol['worker']
    record = json.loads((worker/'report.json').read_text())
    rows, spans = [], {}
    for row in record['fixtures']:
        fixture = row['fixture']
        name = fixture['id']
        def pixels(label):
            return np.array(Image.open(worker/f'{name}-{label}-metric.png'))
        target, nominal = pixels('target'), pixels('nominal')
        nominal_loss = measurement.losses(target, nominal, row['regions'], evaluation.SPEC)
        if nominal_loss != row['losses']['nominal']:
            raise ValueError('Saved nominal loss differs')
        actual = {}
        for label in evaluation.SPEC['refinements']:
            rendered, desired = pixels(label), pixels(label+'-desired')
            losses = measurement.losses(target, rendered, row['regions'], evaluation.SPEC)
            tracking = float(measurement.stroke_loss(desired, rendered))
            if losses != row['losses'][label] or tracking != row['tracking_losses'][label]:
                raise ValueError('Saved actual loss differs')
            actual[label] = {'target_to_actual': losses,
                'nominal_to_actual': float(measurement.stroke_loss(nominal, rendered)),
                'desired_to_actual': tracking}
        rows.append({'id': name, 'target_to_nominal': nominal_loss, 'actual': actual})
        if name in {'letter-n', 'letter-u', 'letter-m'}:
            compiled = compile_gestures(fixture['text'], source['candidate'])['strokes']
            horizontal = [curve[index][0] for stroke in compiled for curve in stroke['cubics'] for index in (0, -1)]
            reference, _ = upright_targets.target(fixture, evaluation.SPEC)
            spans[fixture['text']] = {
                'approved': (max(horizontal)-min(horizontal))*evaluation.SPEC['target']['x_height_mm'],
                'analytic': max(point.x_mm for point in reference)-min(point.x_mm for point in reference)}
    return {'version': protocol['version'], 'protocol_sha256': digest(PROTOCOL_PATH),
        'diagnostic_code_sha256': digest(Path(__file__)), 'source_pins': protocol['source_pins'],
        'artifacts_verified': len(inventory), 'source_numeric_pass': False,
        'appearance': review['status'], 'fixtures': rows,
        'primitive_ports_local_y_up_mm': primitive_ports(source['candidate'], evaluation.SPEC),
        'letter_entry_exit_span_mm': spans, 'budgets': protocol['budgets'],
        'new_target': False, 'new_thresholds': False, 'S2_accepted': False, 'real_accepted': False,
        'context_training_allowed': False,
        'interpretation': 'Diagnostic comparisons are not additive loss attribution or new gates. Candidate-derived anchors are regression references, not independent style truth. Existing verified receipt supplies motion/replay evidence; this script does not reexecute those checks.'}


def write_report(path, result):
    path = Path(path)
    if path.exists():
        raise ValueError('Diagnostic report already exists; preserve evidence')
    with path.open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = reconcile()
    if args.output:
        write_report(args.output, result)
    else:
        print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
