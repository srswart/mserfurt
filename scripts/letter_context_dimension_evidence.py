"""Versioned read-only dimension correction; frozen physical evidence is never rewritten."""

import argparse
from contextlib import contextmanager, ExitStack
import gzip
import json
import math
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

from scripts import letter_context_physical as physical
from scripts import letter_context_physical_evidence as reader
from scripts import letter_context_recovery as recovery
from scripts import letter_context_recovery_evidence as previous
from scribesim.handvalidate import bridge
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


runner = physical
measurement = reader.measurement
case_measurements = reader.case_measurements
case_pass = reader.case_pass
controls = reader.controls
verify_original_budgets = previous.verify_original_budgets
verify_receipt = previous.verify_receipt
BASE = recovery.BASE/'dimension-check-v1'
PREPARED = BASE/'prepared-001'
OUTPUT = BASE/'inspection-001'
RECOVERY_CONTRACT_SHA256 = '1b454630045689f257ac322f1334cebf614c106d748ca00301f5edfcde01b405'
RECOVERY_REPORT_SHA256 = 'e294db3edc76d2d22f28548e8a5f54834c61e9c3d543b6102410a274ce20dc98'
BLOCKED_SHA256 = '90d6287394d1feec8cdf40a141a5678dc602c77eba382a5d5fee070d8d947463'
RENDERER_SHA256 = '703008736483b2c4ef0feef7f6133f8fde0544774d6103661f1901e6c9574e64'


def renderer_size(frame, dpi):
    if (len(frame) != 4 or not all(math.isfinite(value) for value in (*frame, dpi))
            or dpi <= 0 or frame[1] <= frame[0] or frame[3] <= frame[2]):
        raise ValueError('Invalid finite frame or DPI')
    pixels = dpi*3/25.4
    size = (max(3, math.ceil((frame[1]-frame[0])*pixels)),
            max(3, math.ceil((frame[3]-frame[2])*pixels)))
    if size[0]*size[1] > 30000000:
        raise ValueError('Bridge canvas exceeds pixel budget')
    return size[0]//3, size[1]//3


def verify_presentation(file, frame, dpi):
    with Image.open(file) as image:
        if image.size != renderer_size(frame, dpi):
            raise ValueError('Incomplete presentation frame')
        image.load()


def forbidden_execution(*args, **kwargs):
    raise RuntimeError('Physical execution or rasterization forbidden in read-only inspection')


@contextmanager
def read_only_guard():
    with ExitStack() as stack:
        for module, name in [(physical, 'execute_raw'), (physical.ActionController, 'follow_plan'),
                             (reader, 'paint'), (reader, 'paint_trajectory'),
                             (measurement, 'overlap_masks'), (bridge, 'paint_trajectory')]:
            stack.enter_context(patch.object(module, name, forbidden_execution))
        yield


def contract_record():
    recovery.load_contract(RECOVERY_CONTRACT_SHA256)
    if digest(recovery.OUTPUT/'report.json') != RECOVERY_REPORT_SHA256:
        raise ValueError('Changed recovery report')
    if digest(recovery.BASE/'recovery-inspection-blocked-001.json') != BLOCKED_SHA256:
        raise ValueError('Changed failed inspection evidence')
    if digest(ROOT/'scribesim/handvalidate/bridge.py') != RENDERER_SHA256:
        raise ValueError('Changed frozen renderer')
    return {'version': 'letter-context-dimension-check-v1',
        'owner_request': 'Yes please correct measurement-only checker and reinspect the saved files',
        'original_contract_sha256': recovery.CONTRACT_SHA256,
        'recovery_contract_sha256': RECOVERY_CONTRACT_SHA256,
        'recovery_report_sha256': RECOVERY_REPORT_SHA256,
        'previous_inspection_failure_sha256': BLOCKED_SHA256, 'renderer_sha256': RENDERER_SHA256,
        'code_sha256': {str(file.relative_to(ROOT)): digest(file) for file in
            (Path(__file__), ROOT/'tests/test_letter_context_dimension_evidence.py')},
        'change': 'Only presentation dimensions use exact frozen supersample-ceil then integer-downsize formula',
        'unchanged': ['raw containment', 'metric images', 'targets', 'frames', 'thresholds', 'candidate',
                      'controls', 'budgets', 'all frozen sources', 'all saved evidence'],
        'inspection_cases': 1464, 'presentation_images': 324, 'physical_executions_allowed': 0,
        'raster_renders_allowed': 0, 'sealed_holdout_access': False, **physical.FLAGS}


def prepare():
    if PREPARED.exists() or OUTPUT.exists():
        raise FileExistsError('Immutable dimension-check preparation or inspection exists')
    recovery.verify_original()
    record = contract_record()
    PREPARED.mkdir(parents=True, exist_ok=False)
    write_json(PREPARED/'contract.json', record)
    return {'status': 'prepared_not_inspected', 'contract_sha256': digest(PREPARED/'contract.json'),
            'controller_executions': 0, 'raster_renders': 0, **physical.FLAGS}


def load_contract(checksum):
    file = PREPARED/'contract.json'
    if not checksum or digest(file) != checksum:
        raise ValueError('External dimension-check contract pin required')
    record = physical.preflight.foundation.read_json(file)
    if record != contract_record():
        raise ValueError('Changed dimension-check source or contract')
    return record


def verify_worker(contract, directory, seed):
    record = runner.preflight.foundation.read_json(directory/'report.json')
    if (record['status'] != 'pass' or record['seed'] != seed
            or not runner.scope_matches(record)
            or type(record['controller_executions']) is not int or record['controller_executions'] != len(contract['cases'])
            or [row['id'] for row in record['cases']] != [row['id'] for row in contract['cases']]):
        raise ValueError('Incomplete worker case inventory or scope')
    comparisons, reconstructed = {}, []
    for case in contract['cases']:
        case_dir = directory/case['id']
        if runner.preflight.foundation.read_json(case_dir/'attempt.json') != {'case_id': case['id'], 'controller': 'complete'}:
            raise ValueError('Missing or incomplete controller reservation')
        with gzip.open(case_dir/'trace.json.gz', 'rt') as stream:
            run = json.load(stream)
        document = runner.preflight.foundation.read_json(case_dir/'document.json')
        actual = np.asarray(Image.open(case_dir/'actual.png'))
        desired = np.asarray(Image.open(case_dir/'desired.png'))
        masks = {owner: np.asarray(Image.open(case_dir/f"owner-{owner.replace(':', '_')}.png"), dtype=bool)
            for owner in dict.fromkeys(row['gesture_occurrence_id'] for row in document['compiled']['strokes'])}
        expected = case_measurements(contract, case, document, run, actual, desired, masks)
        group = (case['fixture']['id'], object_digest(case['program']))
        if case['refinement'] == 'base':
            comparisons[group] = run, actual
        else:
            baseline, baseline_pixels = comparisons[group]
            expected['comparison'] = measurement.comparison(baseline, run, baseline_pixels, actual)
            if case['refinement'] == list(contract['refinements'])[-1]:
                del comparisons[group]
        expected['passed'] = case_pass(expected, contract)
        if expected != runner.preflight.foundation.read_json(case_dir/'measurement.json') or not expected['passed']:
            raise ValueError('Stored verdict differs from independent raw measurement')
        if case['presentation']:
            verify_presentation(case_dir/'actual-full.png', document['frame_mm'], contract['presentation_dpi'])
        reconstructed.append({'id': case['id'], 'passed': True})
        if case['id'] == contract['control_case_id']:
            control_result = controls(contract, case, document, run, actual, directory=directory)
            if (control_result != record['controls'] or set(control_result) != set(contract['controls'])
                    or control_result != runner.preflight.foundation.read_json(directory/'controls.json')
                    or not all(control_result.values())):
                raise ValueError('Negative controls differ or do not detect corruption')
    if reconstructed != record['cases']:
        raise ValueError('Worker decisions differ')
    return record


def inspect_composite(directory, report_sha256, contract_sha256):
    directory = Path(directory).resolve()
    if directory != recovery.OUTPUT.resolve() or digest(directory/'report.json') != report_sha256:
        raise ValueError('External recovery report pin and fixed directory required')
    frozen = recovery.load_contract(contract_sha256)
    manifest = recovery.verify_original()
    contract = physical.load_contract(recovery.CONTRACT_SHA256)
    report = physical.preflight.foundation.read_json(directory/'report.json')
    if (report['status'] != 'pass' or not physical.scope_matches(report) or report.get('replay_match') is not True
            or report.get('worker_exit_code') != 0 or report['recovery_contract_sha256'] != contract_sha256
            or report['original_contract_sha256'] != recovery.CONTRACT_SHA256
            or report['failure_manifest_sha256'] != recovery.FAILURE_SHA256
            or digest(directory/'contract.json') != contract_sha256
            or report['artifacts'] != physical.artifact_map(directory, {'report.json'})):
        raise ValueError('Incomplete recovery report, scope or artifact inventory')
    verify_original_budgets(contract, manifest)
    ledger = physical.preflight.foundation.read_json(directory/'execution.json')
    if (ledger != report['ledger'] or ledger['prior_seconds'] != frozen['prior_seconds']
            or ledger['prior_renders'] != frozen['prior_renders']
            or not math.isfinite(ledger['recovery_seconds']) or not 0 <= ledger['recovery_seconds'] <= frozen['remaining_seconds']
            or ledger['recovery_renders'] != frozen['scheduled_renders']
            or ledger['cumulative_seconds'] != ledger['prior_seconds']+ledger['recovery_seconds']
            or ledger['cumulative_renders'] != ledger['prior_renders']+ledger['recovery_renders']
            or ledger['cumulative_seconds'] > 2700 or ledger['cumulative_renders'] > 5000):
        raise ValueError('Recovery resets or exceeds cumulative seed budget')
    permit = physical.preflight.foundation.read_json(directory/'permit.json')
    if (permit['contract_sha256'] != contract_sha256 or permit['maximum'] != frozen['remaining_renders']
            or not 0 < permit['seconds'] <= frozen['remaining_seconds']):
        raise ValueError('Changed recovery allowance')
    receipt = physical.preflight.foundation.read_json(directory/'replay/execution.json')
    verify_receipt(receipt, physical.render_schedule(contract), permit['maximum'], permit['seconds'], ledger['recovery_seconds'])
    summaries = []
    for seed in (7, 19, 41):
        first = recovery.ORIGINAL/f'seed-{seed}/first'
        replay = directory/'replay' if seed == 41 else recovery.ORIGINAL/f'seed-{seed}/replay'
        if physical.artifact_map(first, {'execution.json'}) != physical.artifact_map(replay, {'execution.json'}):
            raise ValueError('Fresh-process replay differs')
        for label, worker_dir in [('first', first), ('replay', replay)]:
            record = verify_worker(contract, worker_dir, seed)
            if record['renders'] != frozen['scheduled_renders']:
                raise ValueError('Worker render count differs')
            print(f'Independently verified seed {seed} {label}: {len(record["cases"])} cases', flush=True)
        summaries.append({'seed': seed, 'replay_match': True})
    recovery.verify_original()
    recovery.load_contract(contract_sha256)
    if digest(directory/'report.json') != report_sha256 or report['artifacts'] != physical.artifact_map(directory, {'report.json'}):
        raise ValueError('Recovery changed during inspection')
    return {'status': 'pass', 'read_only': True, 'report_sha256': report_sha256,
        'recovery_contract_sha256': contract_sha256, 'original_contract_sha256': recovery.CONTRACT_SHA256,
        'failure_manifest_sha256': recovery.FAILURE_SHA256, 'cases_verified': len(contract['cases'])*6,
        'seeds': summaries, 'seed_41_cumulative_ledger': ledger, 'raster_renders': 0, 'controller_executions': 0,
        'historical_style_numeric_pass': False, 'appearance_review': 'pending', **physical.FLAGS}


def inspect(checksum):
    if OUTPUT.exists():
        raise FileExistsError('Immutable inspection already exists')
    load_contract(checksum)
    OUTPUT.mkdir(parents=True, exist_ok=False)
    result = {'status': 'blocked', 'dimension_contract_sha256': checksum,
              'controller_executions': 0, 'raster_renders': 0, **physical.FLAGS}
    try:
        with read_only_guard():
            result.update(inspect_composite(recovery.OUTPUT, RECOVERY_REPORT_SHA256, RECOVERY_CONTRACT_SHA256))
            load_contract(checksum)
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, IndexError) as error:
        result.update(status='blocked', reason=str(error))
    write_json(OUTPUT/'report.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--inspect', action='store_true')
    parser.add_argument('--contract-sha256')
    args = parser.parse_args()
    print(json.dumps(prepare() if args.prepare else inspect(args.contract_sha256), indent=2), flush=True)


if __name__ == '__main__':
    main()

