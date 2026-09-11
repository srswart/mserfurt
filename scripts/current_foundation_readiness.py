"""Pinned current-foundation baseline reuse, never context-fitting permission."""

import argparse
from collections import Counter
import gzip
import json
import math
from pathlib import Path

from scripts import upright_placement_validation as placement, upright_placement_evidence as physical_reader
from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


VERSION = 'current-connected-foundation-baseline-v1'
BASE = ROOT/'shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/readiness-v1'
SOURCE = placement.BASE/'run-001'
PINS = {'report.json': '25b0e886ab643ff5dee969d1393b1f3f1e235e75f945e3c94025aedcfffe36b4',
        'inspection.json': 'bda0a94c03a4d8a870cf398137e29c1e093349c0b8f1345a71a4da0caa3c499d',
        'actual-review.json': 'cf890ca88e8295c1a3e66a7ae71545ba7806e3159600b13274f241d1ce06a076'}
PURPOSE = 'frozen-baseline-reuse'
AUTHORIZATION = 'Owner authorizes CURRICULUM-006 P1 current-foundation readiness implementation only; no simulation, fitting or new admission'
GAPS = [
    {'id': 'transformed-occurrences', 'required': 'Approved opt-in derivation/lineage contract, null replay and nonidentity mechanical envelope; H024 covers unchanged recipes only'},
    {'id': 'new-context-coverage', 'required': 'New pair/triple and frame/local-window coverage; no inference from current ten fixed placements'},
    {'id': 'preferences-objective', 'required': 'Owner training labels, exact objective and immutable train/development/test protocol'},
    {'id': 'execution-authorization', 'required': 'Explicit context experiment/fitting clearance and combined budget; no permission inherited from baseline reuse'},
    {'id': 'broader-layer-admission', 'required': 'Independent reusable S1/S2 or historical-hand scope needs its own matching-source quality contract; legacy readers remain unchanged'}]


def read_json(path):
    value = json.loads(Path(path).read_text())
    json.dumps(value, allow_nan=False)
    return value


def identities():
    return {**placement.identities(), str(Path(__file__).relative_to(ROOT)): digest(Path(__file__))}


def verify_inventory(directory, artifacts, excluded):
    directory = Path(directory).resolve()
    inventory = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()}-set(excluded)
    if inventory != set(artifacts):
        raise ValueError('Incomplete artifact inventory')
    for name, checksum in artifacts.items():
        path = (directory/name).resolve()
        if not path.is_relative_to(directory) or digest(path) != checksum:
            raise ValueError('Changed or escaped pinned artifact')


def load_source():
    for name, checksum in PINS.items():
        path = SOURCE/name if name == 'report.json' else placement.BASE/name
        if digest(path) != checksum:
            raise ValueError('Changed source pin: '+name)
    report = read_json(SOURCE/'report.json')
    verify_inventory(SOURCE, report['artifacts'], ['report.json'])
    frozen = read_json(SOURCE/'freeze.json')
    if frozen['code_sha256'] != placement.identities() or frozen['spec'] != placement.SPEC:
        raise ValueError('Changed current foundation source identities')
    candidate = read_json(placement.evaluation.SOURCE/'candidate.json')
    if (digest(placement.evaluation.SOURCE/'candidate.json') != placement.evaluation.SPEC['candidate_file_sha256']
            or candidate != frozen['source']['candidate']):
        raise ValueError('Changed approved candidate')
    validate_gestures(candidate)
    inspection = read_json(placement.BASE/'inspection.json')
    if (inspection['report_sha256'] != PINS['report.json'] or inspection['status'] != 'pass'
            or inspection['reader_sha256'] != digest(Path(physical_reader.__file__))
            or inspection['artifacts_verified'] != len(report['artifacts'])
            or inspection['read_only'] is not True or inspection['rerenders'] != 0
            or inspection['controller_executions'] != 0 or report['evaluation_complete'] is not True):
        raise ValueError('Incomplete pinned independent inspection')
    decisions = []
    for seed in placement.SPEC['seeds']:
        for process in ('first', 'replay'):
            record = read_json(SOURCE/f'seed-{seed}/{process}/report.json')
            decision = physical_reader.decision(record)
            if record['status'] != 'complete' or decision['execution_protocol_pass'] is not True:
                raise ValueError('Unverified physical baseline')
            decisions.append({'seed': seed, 'process': process, **decision})
    if decisions != inspection['decisions']:
        raise ValueError('Pinned inspection differs from current physical decisions')
    review = read_json(placement.BASE/'actual-review.json')
    if (review['candidate_sha256'] != placement.evaluation.SPEC['candidate_file_sha256']
            or review['report_sha256'] != PINS['report.json'] or review['status'] != 'approved_held_out_actual_appearance'
            or set(review['placements']) != {'un','nu','um','nn','uu','mm'}
            or any(row['verdict'] != 'keep' for row in review['placements'].values())
            or any(review[key] is not False for key in ('S2_accepted', 'real_accepted', 'context_training_allowed'))):
        raise ValueError('Missing scoped owner review')
    original_review = placement.evaluation.BASE/'continuation-002/actual-review.json'
    if digest(original_review) != review['known_regressions']['original_review_sha256']:
        raise ValueError('Changed known-letter owner review')
    return {'candidate': candidate, 'review': review, 'report': report, 'inspection': inspection,
            'core_identities': frozen['source']['core_identities']}


def audit_run(model, fixture, refinement, run):
    try:
        variant = placement.evaluation.subdivide(model) if refinement == 'subdivision' else model
        step, dt = placement.SPEC['refinements'][refinement]
        if (run['text'] != fixture['text'] or run['model_sha256'] != object_digest(variant)
                or run['tool'] != 'physical-edge-v1' or run['version'] != 'curve-tangent-v1'
                or run['step_mm'] != step or run['dt_s'] != dt):
            raise ValueError('Unmatched candidate/refinement/tool')
        compiled = compile_gestures(fixture['text'], variant)
        indexed = {row['occurrence_id']: row for row in compiled['strokes']}
        if len(indexed) != len(compiled['strokes']) or not indexed:
            raise ValueError('Duplicate or missing compiled occurrences')
        samples = Counter()
        for event in run['trace']:
            if event['contact'] is not True and event['contact'] is not False:
                raise ValueError('Invalid contact flag')
            if any(not math.isfinite(value) for value in [*event['to_mm'], event['time_s'], event['dt_s'], event['angle_deg']]):
                raise ValueError('Nonfinite trace')
            if (event['fatigue'] != 0 or event['consumed'] != 0 or event['ink_before'] != 1 or event['ink_after'] != 1
                    or abs(event['angle_deg']-40) > 1e-10 or event['realized_edge'] != [0, 1]
                    or event['execution_version'] != 'event-time-v2'):
                raise ValueError('Changed fixed action or session state')
            if not event['contact']:
                if event['pressure'] != 0:
                    raise ValueError('Ink during air movement')
                continue
            owner = event['owner']
            expected = indexed.get(owner['occurrence_id'])
            if (expected is None or owner['kind'] != 'stroke' or event['pressure'] != .5 or event['width_mm'] != .45
                    or any(owner[key] != value for key, value in expected.items() if key != 'cubics')):
                raise ValueError('Changed primitive/gesture/action/recipe owner lineage')
            position = owner['curve_position']
            if (type(position['cubic_index']) is not int or not 0 <= position['cubic_index'] < len(expected['cubics'])
                    or not 0 <= position['parameter'] <= 1 or not 0 <= owner['gesture_progress'] <= 1):
                raise ValueError('Unbound curve coverage')
            for boundary in owner['boundary_contributors']:
                previous = indexed.get(boundary['occurrence_id'])
                if (previous is None or any(boundary[key] != previous[key] for key in
                        ('gesture_occurrence_id', 'action_profile', 'action_sha256'))
                        or boundary['gesture_progress'] not in (0, 1)):
                    raise ValueError('Changed boundary contributor')
            samples[owner['occurrence_id']] += 1
        if set(samples) != set(indexed):
            raise ValueError('Missing actual occurrence coverage')
        contact_runs = list(dict.fromkeys(row['contact_run_id'] for row in compiled['strokes']))
        if len(contact_runs) != len(fixture['text']):
            raise ValueError('Changed letter contact topology')
        gestures = {row['gesture_occurrence_id']: row['gesture'] for row in compiled['strokes']}
        return {'fixture': fixture['id'], 'refinement': refinement,
                'derivation': 'exact-internal-subdivision' if refinement == 'subdivision' else 'canonical-geometry',
                'model_sha256': object_digest(variant), 'compiled_sha256': object_digest(compiled),
                'primitive_counts': dict(Counter(row['primitive'] for row in compiled['strokes'])),
                'gesture_counts': dict(Counter(gestures.values())), 'letter_counts': dict(Counter(fixture['text'])),
                'action_occurrences': dict(Counter(row['action_profile'] for row in compiled['strokes'])),
                'contact_samples_per_occurrence': dict(sorted(samples.items())), 'contact_runs': contact_runs,
                'primitive_bindings': {name: object_digest(variant['primitives'][name]) for name in sorted({row['primitive'] for row in indexed.values()})}}
    except (KeyError, TypeError, IndexError, OverflowError) as error:
        raise ValueError('Incomplete raw lineage evidence') from error


def summarize():
    source = load_source()
    candidate, coverage = source['candidate'], []
    for seed in placement.SPEC['seeds']:
        for process in ('first', 'replay'):
            directory = SOURCE/f'seed-{seed}/{process}'
            for fixture in placement.SPEC['fixtures']:
                runs = json.loads(gzip.decompress((directory/f"{fixture['id']}-traces.json.gz").read_bytes()))
                if set(runs) != set(placement.SPEC['refinements']):
                    raise ValueError('Incomplete refinement coverage')
                model = placement.model_for_fixture(candidate, fixture)
                for refinement in placement.SPEC['refinements']:
                    coverage.append({'seed': seed, 'process': process, **audit_run(model, fixture, refinement, runs[refinement])})
    catalog = {key: {name: object_digest(value) for name, value in candidate[key].items()}
               for key in ('primitives', 'gestures', 'actions', 'recipes')}
    missing = []
    for seed in placement.SPEC['seeds']:
        for process in ('first', 'replay'):
            for refinement in placement.SPEC['refinements']:
                rows = [row for row in coverage if (row['seed'], row['process'], row['refinement']) == (seed, process, refinement)]
                for kind, field in [('primitives','primitive_counts'), ('gestures','gesture_counts'),
                                    ('actions','action_occurrences'), ('recipes','letter_counts')]:
                    observed = {name for row in rows for name in row[field]}
                    if observed != set(catalog[kind]):
                        missing.append(f'{seed}/{process}/{refinement}/{kind}')
    return {'version': VERSION, 'status': 'complete', 'source_pins': dict(PINS),
            'candidate_file_sha256': placement.evaluation.SPEC['candidate_file_sha256'],
            'candidate_object_sha256': object_digest(candidate), 'source_artifacts_verified': len(source['report']['artifacts']),
            'core_identity_count': len(source['core_identities']), 'core_identity_sha256': object_digest(source['core_identities']),
            'catalog': catalog, 'coverage': coverage, 'missing_baseline_inventory': missing,
            'baseline_readiness': 'fail' if missing else 'pass', 'purpose': PURPOSE,
            'baseline_scope': {'fixtures': placement.SPEC['fixtures'], 'frame_mm': placement.SPEC['frame_mm'],
                'tool': 'physical-edge-v1', 'refinements': placement.SPEC['refinements'],
                'limitation': 'Observed canonical occurrences inside these letters only, not arbitrary transformed or isolated-use admission'},
            'physical_evidence': 'Reused consumer-pinned H024 independent raw inspection; new coverage/lineage scan only',
            'appearance': 'Approved exact n/u/m and listed placement samples, not new geometry',
            'historical_style_target': 'fail, unchanged; diagnostic under the approved preservation contract',
            'context_readiness': 'blocked', 'context_gaps': GAPS, 'S2_accepted': False, 'real_accepted': False,
            'context_training_allowed': False, 'new_controller_executions': 0, 'new_renders': 0, 'optimization_evaluations': 0}


def build(directory):
    directory = Path(directory)
    if directory.exists():
        raise ValueError('Readiness snapshot already exists; no overwrite')
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory/'freeze.json', freeze_record())
    report = summarize()
    if read_json(directory/'freeze.json')['code_sha256'] != identities():
        raise ValueError('Source changed during readiness audit')
    report['artifacts'] = {'freeze.json': digest(directory/'freeze.json')}
    write_json(directory/'report.json', report)
    return report


def freeze_record():
    return {'version': VERSION, 'code_sha256': identities(), 'source_pins': dict(PINS), 'authorization': AUTHORIZATION}


def inspect(directory, expected_report_sha256):
    directory = Path(directory)
    try:
        if not expected_report_sha256 or digest(directory/'report.json') != expected_report_sha256:
            raise ValueError('Consumer-pinned readiness report required')
        report = read_json(directory/'report.json')
        verify_inventory(directory, report['artifacts'], ['report.json'])
        frozen = read_json(directory/'freeze.json')
        if frozen != freeze_record():
            raise ValueError('Stale readiness identities')
        expected = summarize()
        if report != {**expected, 'artifacts': {'freeze.json': digest(directory/'freeze.json')}}:
            raise ValueError('Readiness differs from current pinned evidence')
        return {**expected, 'report_sha256': expected_report_sha256, 'read_only': True}
    except (OSError, KeyError, TypeError, IndexError) as error:
        raise ValueError('Incomplete readiness evidence') from error


def require_readiness(directory, *, expected_report_sha256, candidate, required_letters, tool, purpose):
    if (purpose != PURPOSE or tool != 'physical-edge-v1' or not isinstance(required_letters, (list, tuple))
            or not required_letters or any(not isinstance(letter, str) for letter in required_letters)
            or len(set(required_letters)) != len(required_letters) or not set(required_letters) <= {'n','u','m'}):
        raise ValueError('Explicit frozen-baseline letter/tool/purpose scope required; context fitting is not cleared')
    report = inspect(directory, expected_report_sha256)
    if object_digest(candidate) != report['candidate_object_sha256']:
        raise ValueError('Exact approved candidate required')
    if report['baseline_readiness'] != 'pass' or report['missing_baseline_inventory']:
        raise ValueError('Unresolved baseline coverage')
    return {'version': VERSION, 'baseline_ready': True, 'report_sha256': expected_report_sha256,
            'candidate_file_sha256': report['candidate_file_sha256'], 'required_letters': sorted(required_letters),
            'purpose': purpose, 'scope': report['baseline_scope'], 'context_gaps': report['context_gaps'],
            'S2_accepted': False, 'real_accepted': False, 'context_training_allowed': False,
            'execution_authorized': False, 'geometry_changes_authorized': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path)
    parser.add_argument('--inspect', type=Path)
    parser.add_argument('--report-sha256')
    args = parser.parse_args()
    if bool(args.build) == bool(args.inspect):
        parser.error('Choose exactly one of --build or --inspect')
    report = build(args.build) if args.build else inspect(args.inspect, args.report_sha256)
    print(json.dumps({key: value for key, value in report.items() if key not in ('coverage', 'catalog', 'artifacts')}, indent=2))


if __name__ == '__main__':
    main()
