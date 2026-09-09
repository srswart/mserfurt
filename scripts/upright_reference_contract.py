"""Versioned approved-appearance references; no aggregate acceptance or fitting."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from scripts import handvalidate_upright_targets as reconciliation
from scribesim.handvalidate import upright_evidence as historical, upright_letters as evaluation
from scribesim.handvalidate import upright_measurement as measurement
from scribesim.handvalidate.specimen import ROOT, digest, object_digest


VERSION = 'reviewed-synthetic-appearance-contract-v1'
BASE = evaluation.BASE/'reference-contract-v1'
SOURCE = evaluation.BASE/'continuation-002/run-001'
REVIEW = evaluation.BASE/'reconciliation-001/contract-review.json'
REVIEW_SHA256 = '704dadc883d53fd1440f501cd83ccbbeb4f7b51d9991e20d9c586a44d561fe5b'
DIAGNOSTIC_SHA256 = 'f56d560e345b686e8dc06d2a5cef55ea4a8956d7b3f608e0069c330462ce3eae'


def pixel_digest(pixels):
    if not isinstance(pixels, np.ndarray) or pixels.dtype != np.uint8 or pixels.ndim != 3 or pixels.shape[-1] != 3:
        raise ValueError('Full RGB uint8 pixels required')
    return hashlib.sha256(json.dumps(list(pixels.shape)).encode()+b'\0'+pixels.tobytes()).hexdigest()


def make_registry():
    if digest(REVIEW) != REVIEW_SHA256:
        raise ValueError('Changed contract approval')
    approved = json.loads(REVIEW.read_text())
    if approved['contract_version'] != VERSION or approved['status'] != 'approved_design_pending_implementation':
        raise ValueError('Owner-approved design required')
    diagnostic_path = reconciliation.BASE/'report.json'
    if digest(diagnostic_path) != DIAGNOSTIC_SHA256 or reconciliation.reconcile() != json.loads(diagnostic_path.read_text()):
        raise ValueError('Changed verified reconciliation')
    source = reconciliation.replay.load_inputs()
    references = {}
    for fixture in evaluation.SPEC['fixtures']:
        if fixture['id'] not in {'letter-n', 'letter-u', 'letter-m', 'placed-mu'}:
            continue
        path = SOURCE/f"seed-7/first/{fixture['id']}-base-metric.png"
        pixels = np.array(Image.open(path))
        references['actual:'+fixture['id']] = {
            'role': 'approved_appearance_regression', 'candidate_independent': False, 'owner_approved': True,
            'image_path': str(path.relative_to(ROOT)), 'image_sha256': digest(path),
            'pixel_sha256': pixel_digest(pixels), 'pixel_shape': list(pixels.shape),
            'review_sha256': digest(evaluation.BASE/'continuation-002/actual-review.json'),
            'context': {'candidate_sha256': digest(evaluation.SOURCE/'candidate.json'),
                'source_code_sha256': object_digest(reconciliation.replay.identities()),
                'fixture': fixture, 'frame_mm': evaluation.SPEC['frame_mm'], 'dpi': evaluation.SPEC['metric_dpi'],
                'tool_version': 'physical-edge-v1', 'fixed_tool_sha256': object_digest({
                    key: source['candidate'][key] for key in ('nib_width_mm', 'nib_angle_deg', 'x_height_mm', 'actions')}),
                'refinement': {'step_mm': .025, 'dt_s': .002}},
            'provenance': 'Saved actual output from the owner-approved frozen candidate. Derived regression anchor, not independent style truth.'}
    return {'version': VERSION, 'contract_review_sha256': REVIEW_SHA256,
        'historical_report_sha256': digest(SOURCE/'report.json'), 'diagnostic_sha256': DIAGNOSTIC_SHA256,
        'references': references,
        'regression_policy': {'mode': 'exact_replay_identity', 'variant_tolerance': None,
            'quality_gate': False, 'generalization_claim': False},
        'style_reference': {'version': evaluation.SPEC['target_version'], 'role': 'independent_style_comparator',
            'candidate_independent': True, 'owner_approved': False, 'historical_hand_validated': False,
            'spec_sha256': digest(evaluation.SPEC_PATH), 'definition': evaluation.SPEC['target'],
            'historical_required_gate': True, 'prospective_preservation_role': 'diagnostic',
            'absolute_local_limit': .05, 'relative_limit': .75,
            'provenance': evaluation.SPEC['target_provenance']},
        'permission_policy': {'S2_accepted': False, 'real_accepted': False, 'context_training_allowed': False}}


def load_registry(path, expected_sha256):
    path = Path(path)
    if not expected_sha256 or digest(path) != expected_sha256:
        raise ValueError('Consumer-pinned registry hash required')
    registry = json.loads(path.read_text())
    if registry != make_registry():
        raise ValueError('Changed registry role, scope or source binding')
    return registry


def compare_reference(reference, pixels, context):
    if (reference['role'] != 'approved_appearance_regression' or reference['candidate_independent'] is not False
            or reference['owner_approved'] is not True):
        raise ValueError('Invalid regression reference provenance')
    result = {'quality_pass': None, 'generalization_proven': False, 'scope': 'Exact scoped replay identity only'}
    if context != reference['context']:
        return {**result, 'status': 'incompatible', 'reason': 'candidate/fixture/frame/tool/refinement binding'}
    try:
        checksum = pixel_digest(pixels)
    except ValueError:
        return {**result, 'status': 'incompatible', 'reason': 'pixel representation'}
    if list(pixels.shape) != reference['pixel_shape']:
        return {**result, 'status': 'incompatible', 'reason': 'full frame required'}
    return {**result, 'status': 'match' if checksum == reference['pixel_sha256'] else 'mismatch'}


def classify_record(record):
    physical_kinds = {'actual-motion', 'overlap-attribution', 'tracking-image', 'actual-levels', 'actual-ports', 'convergence'}
    groups = {'construction': [], 'physical_motion': [], 'style_target': []}
    try:
        decision = historical.decision(record)
        invalid = []
        for failure in decision['failures']:
            kind = failure.rsplit(':', 1)[-1]
            if kind == 'nominal-levels':
                groups['construction'].append(failure)
            elif kind in physical_kinds:
                groups['physical_motion'].append(failure)
            elif kind == 'target-image':
                groups['style_target'].append(failure)
            else:
                invalid.append(failure)
    except (KeyError, ValueError, TypeError, IndexError):
        invalid = ['malformed-evidence']
        decision = {'numeric_pass': False}
    if invalid:
        return {**{name: {'status': 'invalid', 'failures': invalid} for name in groups}, 'historical_numeric_pass': False}
    return {**{name: {'status': 'fail' if failures else 'pass', 'failures': failures} for name, failures in groups.items()},
        'historical_numeric_pass': decision['numeric_pass']}


def make_protocol(registry):
    source = reconciliation.replay.load_inputs()['candidate']
    held_out = []
    for text in ('un', 'nu', 'um', 'nn', 'uu', 'mm'):
        model = copy.deepcopy(source)
        shift = [.017, -.011]
        for recipe in model['recipes'].values():
            for instance in recipe['gestures']:
                instance['offset'] = [value+delta for value, delta in zip(instance['offset'], shift)]
        if not measurement.contained(evaluation.nominal(model, text), evaluation.SPEC['frame_mm']):
            raise ValueError('Held-out placement is outside full frame')
        counts = {}
        for label, (step, _) in evaluation.SPEC['refinements'].items():
            variant = evaluation.subdivide(model) if label == 'subdivision' else model
            compiled = measurement.compile_gestures(text, variant)['strokes']
            if len({stroke['contact_run_id'] for stroke in compiled}) != len(text):
                raise ValueError('Held-out interletter contact topology changed')
            bundle = measurement.action_bundle(text, variant, step_mm=step, include_curve_positions=True)
            timed = measurement.retime_curve_tangents(bundle.plan, bundle.owners, compiled)
            counts[label] = len(timed.plan.samples)
        held_out.append({'id': 'placement-'+text, 'text': text, 'shift': shift, 'plan_preflight_pass': True,
            'plan_sample_counts': counts, 'owner_appearance': 'not_reviewed', 'reference_provenance': 'candidate-derived nominal; not independently validated'})
    return {'version': VERSION+'-placement-protocol-v1', 'registry_digest': object_digest(registry),
        'status': 'prepared_not_executed', 'execution_authorized': False,
        'known_regressions': [reference['context']['fixture'] for reference in registry['references'].values()],
        'held_out_placements': held_out, 'held_out_policy': 'Text-disjoint from n/u/m/mu; no context overlays or fitting. Preflight is not actual motion or transfer evidence.',
        'frame_mm': evaluation.SPEC['frame_mm'], 'local_padding_mm': evaluation.SPEC['local_padding_mm'],
        'metric_dpi': 180, 'presentation_dpi': 900, 'refinements': evaluation.SPEC['refinements'],
        'mechanical_criteria': {key: value for key, value in evaluation.SPEC['criteria'].items()
            if key not in {'absolute_loss_max', 'relative_loss_max'}},
        'regression_mode': 'exact_replay_identity_for_known_base_fixtures', 'regression_variant_tolerance': None,
        'held_out_nominal_actual_loss': 'report_only; no transferred 0.05 threshold',
        'style_reference': registry['style_reference'], 'physical_controls': evaluation.SPEC['controls'],
        'seeds': [7, 19, 41], 'fresh_process_replays_per_seed': 1,
        'proposed_budget_per_seed_including_replay': {'renders': 5000, 'seconds': 1800, 'automatic_retries': 0},
        'budget_authorized': False, 'optimization_evaluations': 0,
        'execution_requirements': ['New owner-bound execution authorization for this protocol and budget',
            'Freeze execution code, candidate, derived reference artifacts and independent reader before any scoring'],
        'acceptance_debt': ['Held-out actual motion/replay and adversarial evidence absent',
            'Held-out actual appearance not reviewed', 'No S2/real/context admission authorized'],
        'implementation_validation_budget': {'controller_executions': 0, 'raster_renders': 0, 'optimization_evaluations': 0}}


def mutation_controls(registry):
    reference = registry['references']['actual:letter-n']
    pixels = np.array(Image.open(ROOT/reference['image_path']))
    result = {}
    for name in ('single_pixel', 'shift', 'crop', 'tool', 'frame', 'candidate', 'fixture', 'independence'):
        changed, context, anchor = pixels.copy(), copy.deepcopy(reference['context']), copy.deepcopy(reference)
        if name == 'single_pixel':
            changed[0, 0, 0] ^= 1
        elif name == 'shift':
            changed = np.roll(changed, 1, axis=1)
        elif name == 'crop':
            changed = changed[:-1]
        elif name == 'independence':
            anchor['candidate_independent'] = True
        else:
            key = {'tool': 'tool_version', 'frame': 'frame_mm', 'candidate': 'candidate_sha256', 'fixture': 'fixture'}[name]
            context[key] = 'altered'
        try:
            verdict = compare_reference(anchor, changed, context)
            result[name] = {'detected': verdict['status'] != 'match', 'status': verdict['status']}
        except ValueError:
            result[name] = {'detected': True, 'status': 'rejected-provenance'}
    return result


def snapshot(registry):
    workers = []
    for seed in (7, 19, 41):
        for process in ('first', 'replay'):
            directory = SOURCE/f'seed-{seed}/{process}'
            record = json.loads((directory/'report.json').read_text())
            regression = {}
            for name, reference in registry['references'].items():
                fixture = reference['context']['fixture']['id']
                pixels = np.array(Image.open(directory/f'{fixture}-base-metric.png'))
                regression[name] = compare_reference(reference, pixels, reference['context'])
            workers.append({'seed': seed, 'process': process, **classify_record(record),
                'appearance': {'status': 'approved_saved_fixtures', 'references': list(regression),
                    'unreviewed_scope': 'Isolated primitives and gestures have no separate owner verdict; unseen combinations inherit none.'},
                'regression': regression})
    return {'version': VERSION, 'status': 'complete', 'overall_admission': 'withheld',
        'historical_numeric_pass': False, 'workers': workers, 'controls': mutation_controls(registry),
        'evidence_basis': 'Current source/artifact hashes and pinned independent H021 receipt. Stored motion gates are reclassified, not newly executed or independently reconstructed here.',
        'control_scope': 'In-memory pixel/metadata mutations, not new physical-controller runs',
        'validation_budget': {'controller_executions': 0, 'raster_renders': 0, 'optimization_evaluations': 0},
        **registry['permission_policy']}


def write_json(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False)+'\n')


def build(directory):
    directory = Path(directory)
    if directory.exists():
        raise ValueError('Contract snapshot already exists')
    registry = make_registry()
    protocol = make_protocol(registry)
    directory.mkdir(parents=True)
    write_json(directory/'registry.json', registry)
    write_json(directory/'protocol.json', protocol)
    write_json(directory/'freeze.json', {'contract_code_sha256': digest(Path(__file__)),
        'source_code_sha256': reconciliation.replay.identities(), 'registry_sha256': digest(directory/'registry.json'),
        'protocol_sha256': digest(directory/'protocol.json')})
    report = snapshot(registry)
    report['artifacts'] = {path.name: digest(path) for path in sorted(directory.iterdir())}
    write_json(directory/'report.json', report)
    return report


def inspect(directory, expected_report_sha256):
    directory = Path(directory)
    if not expected_report_sha256 or digest(directory/'report.json') != expected_report_sha256:
        raise ValueError('Consumer-pinned report hash required')
    report = json.loads((directory/'report.json').read_text())
    if {path.name for path in directory.iterdir()} != {'registry.json', 'protocol.json', 'freeze.json', 'report.json'}:
        raise ValueError('Changed snapshot inventory')
    if set(report['artifacts']) != {'registry.json', 'protocol.json', 'freeze.json'}:
        raise ValueError('Changed artifact list')
    reconciliation.verify_pins(directory, report['artifacts'])
    registry = load_registry(directory/'registry.json', report['artifacts']['registry.json'])
    if json.loads((directory/'protocol.json').read_text()) != make_protocol(registry):
        raise ValueError('Changed prepared protocol')
    frozen = json.loads((directory/'freeze.json').read_text())
    if frozen != {'contract_code_sha256': digest(Path(__file__)), 'source_code_sha256': reconciliation.replay.identities(),
            'registry_sha256': digest(directory/'registry.json'), 'protocol_sha256': digest(directory/'protocol.json')}:
        raise ValueError('Changed frozen contract source')
    if report != {**snapshot(registry), 'artifacts': report['artifacts']}:
        raise ValueError('Changed contract decisions')
    return {'status': 'verified', 'report_sha256': expected_report_sha256, 'artifacts_verified': 3,
        'original_artifacts_verified': 1256, 'read_only': True, 'rerenders': 0,
        'overall_admission': 'withheld', **registry['permission_policy']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--build', type=Path)
    actions.add_argument('--inspect', type=Path)
    parser.add_argument('--report-sha256')
    args = parser.parse_args()
    result = build(args.build) if args.build else inspect(args.inspect, args.report_sha256)
    print(json.dumps({key: value for key, value in result.items() if key != 'workers'}, indent=2))


if __name__ == '__main__':
    main()
