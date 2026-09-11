"""Reconstruct null context lineage and bind exact planning inputs to archived output."""

import argparse
from dataclasses import asdict, replace
import gzip
import json
from pathlib import Path

import numpy as np
from PIL import Image

from scripts import current_foundation_readiness as foundation, letter_context_contract as context
from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handflow.curve_tangents import retime_curve_tangents
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json
from scribesim.pathguide.gesture_actions import action_bundle


BASE = foundation.BASE.parent/'null-contract-v1'
READINESS = foundation.BASE/'snapshot-001'
READINESS_SHA256 = 'af4e70fc3c1b61c4e69ff46f0a9a3e70ecf5d737659901d0d5730edb976181aa'
AUTHORIZATION = 'Owner authorizes CURRICULUM-006 P2 context/lineage contract and exact unchanged-output checks; identity-only planning and archived bindings, no new physical execution, transforms or fitting; leave changes uncommitted'


def identities():
    return {**foundation.identities(), **{str(path.relative_to(ROOT)): digest(path)
            for path in (Path(__file__), Path(context.__file__))}}


def verify_document(document, candidate, fixture, refinement):
    try:
        program = context.validate_program(document['program'])
        if object_digest(candidate) != context.CANDIDATE_SHA256 or refinement not in foundation.placement.SPEC['refinements']:
            raise ValueError('Unfrozen candidate/refinement')
        model = foundation.placement.model_for_fixture(candidate, fixture)
        if refinement == 'subdivision':
            model = foundation.placement.evaluation.subdivide(model)
        baseline = compile_gestures(fixture['text'], model)
        expected_occurrences = []
        for stroke in baseline['strokes']:
            following = fixture['text'][stroke['letter']+1:stroke['letter']+2]
            entry = 'rise-entry' if following == 'm' else 'stem-entry' if following in ('n', 'u') else None
            matches = [rule for rule in program['rules'] if rule['current_letter'] == stroke['recipe']
                       and rule['following_entry_class'] == entry]
            expected_occurrences.append({'owner': {key: value for key, value in stroke.items() if key != 'cubics'},
                'canonical_primitive_sha256': object_digest(candidate['primitives'][stroke['primitive']]),
                'execution_primitive_sha256': object_digest(model['primitives'][stroke['primitive']]),
                'canonical_gesture_sha256': object_digest(candidate['gestures'][stroke['gesture']]),
                'canonical_action_sha256': object_digest(candidate['actions'][stroke['action_profile']]),
                'canonical_recipe_sha256': object_digest(candidate['recipes'][stroke['recipe']]),
                'placed_recipe_sha256': object_digest(model['recipes'][stroke['recipe']]),
                'following_entry_class': entry, 'rule_id': matches[0]['id'] if matches else None,
                'transform': {'kind': 'identity-short-circuit', 'width_scale': 1.0, 'advance_delta': 0.0},
                'source_geometry_sha256': object_digest(stroke['cubics']),
                'derived_geometry_sha256': object_digest(stroke['cubics'])})
        expected_lineage = {'version': context.VERSION, 'canonical_candidate_sha256': context.CANDIDATE_SHA256,
            'execution_model_sha256': object_digest(model), 'fixture': fixture, 'refinement': refinement,
            'geometry_derivation': 'exact-internal-subdivision' if refinement == 'subdivision' else 'canonical-geometry',
            'context_program_sha256': object_digest(program), 'compiled_sha256': object_digest(baseline),
            'occurrences': expected_occurrences, 'context_training_allowed': False, 'execution_authorized': False,
            'nonidentity_authorized': False, 'S2_accepted': False, 'real_accepted': False}
        expected = {'version': context.VERSION, 'program': program, 'compiled': baseline, 'lineage': expected_lineage}
        if object_digest(document) != object_digest(expected):
            raise ValueError('Context geometry or lineage differs from independently reconstructed null contract')
        return model
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('Incomplete null context lineage') from error


def bind_archived_run(run, bundle, timed, refinement):
    try:
        step, dt = foundation.placement.SPEC['refinements'][refinement]
        if (run['model_sha256'] != bundle.model_sha256 or run['text'] != bundle.text
                or run['tool'] != 'physical-edge-v1' or run['version'] != timed.version
                or run['step_mm'] != step or run['dt_s'] != dt
                or object_digest(run['plan']) != object_digest(asdict(bundle.plan))
                or object_digest(run['corners']) != object_digest(timed.corners)
                or object_digest(run['arrivals']) != object_digest(timed.arrivals)):
            raise ValueError('Archived plan, exact event timing or execution identity changed')
        if not run['trace']:
            raise ValueError('Missing archived actual trace')
        for event in run['trace']:
            index = event['plan_index']
            if (type(index) is not int or not 0 <= index < len(bundle.owners)
                    or event['owner'] != bundle.owners[index] or event['contact'] != bundle.plan.samples[index].contact):
                raise ValueError('Archived owner or contact differs from null plan')
        return {'exact_input_match': True, 'archived_trace_sha256': object_digest(run['trace']),
                'plan_sha256': object_digest(run['plan']), 'corners_sha256': object_digest(run['corners']),
                'arrivals_sha256': object_digest(run['arrivals'])}
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('Incomplete archived null binding') from error


def summarize():
    placement = foundation.placement
    candidate = foundation.read_json(placement.evaluation.SOURCE/'candidate.json')
    clearance = foundation.require_readiness(READINESS, expected_report_sha256=READINESS_SHA256,
        candidate=candidate, required_letters=['n', 'u', 'm'], tool='physical-edge-v1', purpose=foundation.PURPOSE)
    programs = {name: context.null_program(candidate, enabled=enabled) for name, enabled in [('off', False), ('six-identity', True)]}
    prepared, cases = {}, []
    for fixture in placement.SPEC['fixtures']:
        for refinement, (step, _) in placement.SPEC['refinements'].items():
            model = placement.model_for_fixture(candidate, fixture)
            if refinement == 'subdivision':
                model = placement.evaluation.subdivide(model)
            compiled = compile_gestures(fixture['text'], model)
            original = action_bundle(fixture['text'], model, step_mm=step, include_curve_positions=True)
            timed = retime_curve_tangents(original.plan, original.owners, compiled['strokes'])
            baseline = replace(original, plan=timed.plan, owners=[original.owners[index] for index in timed.source_indices])
            for name, program in programs.items():
                document = context.compile_context(candidate, fixture, program, refinement)
                bundle, derived_timed = context.prepare_null_plan(document, candidate, fixture, refinement)
                if (object_digest(document['compiled']) != object_digest(compiled)
                        or asdict(bundle) != asdict(baseline) or asdict(derived_timed) != asdict(timed)):
                    raise ValueError('Null context changes canonical geometry, ownership or timing')
                cases.append({'fixture': fixture['id'], 'refinement': refinement, 'mode': name,
                    'program_sha256': object_digest(program), 'lineage': document['lineage'],
                    'compiled_sha256': object_digest(compiled), 'bundle_sha256': object_digest(asdict(bundle)),
                    'timing_sha256': object_digest(asdict(timed)), 'exact_null_match': True})
            prepared[fixture['id'], refinement] = baseline, timed
    registry = foundation.read_json(placement.PREPARED/'registry.json')
    source = {'candidate': candidate, 'registry': registry,
              'core_identities': placement.contract.reconciliation.replay.identities()}
    records, first_hashes, known_matches = [], {}, 0
    for seed in placement.SPEC['seeds']:
        for process in ('first', 'replay'):
            directory = foundation.SOURCE/f'seed-{seed}/{process}'
            for fixture in placement.SPEC['fixtures']:
                trace_path = directory/f"{fixture['id']}-traces.json.gz"
                runs = json.loads(gzip.decompress(trace_path.read_bytes()))
                for refinement in placement.SPEC['refinements']:
                    binding = bind_archived_run(runs[refinement], *prepared[fixture['id'], refinement], refinement)
                    pixels = {}
                    for role in (refinement, refinement+'-desired'):
                        image_path = directory/f"{fixture['id']}-{role}-metric.png"
                        with Image.open(image_path) as image:
                            array = np.array(image)
                        pixels[role] = {'source_file': str(image_path.relative_to(ROOT)), 'file_sha256': digest(image_path),
                            'pixel_sha256': placement.contract.pixel_digest(array)}
                        if role == 'base' and fixture in placement.SPEC['known_regressions']:
                            result = placement.reference_result(source, fixture, array)
                            if result['status'] != 'match':
                                raise ValueError('Known-base approved pixel reference differs')
                            known_matches += 1
                    signatures = {'trace': binding['archived_trace_sha256'],
                                  'pixels': {key: value['pixel_sha256'] for key, value in pixels.items()}}
                    key = seed, fixture['id'], refinement
                    if process == 'first':
                        first_hashes[key] = signatures
                    elif signatures != first_hashes[key]:
                        raise ValueError('Archived first/replay output differs')
                    records.append({'seed': seed, 'process': process, 'fixture': fixture['id'], 'refinement': refinement,
                        **binding, 'trace_source': str(trace_path.relative_to(ROOT)), 'trace_file_sha256': digest(trace_path),
                        'archived_pixels': pixels})
    return {'version': context.VERSION, 'status': 'pass', 'readiness_report_sha256': READINESS_SHA256,
        'programs': programs, 'cases': cases, 'archived_bindings': records, 'compilation_plan_cases': len(cases),
        'archived_runs_bound': len(records), 'archived_images_bound': 2*len(records), 'known_base_reference_matches': known_matches,
        'proof_kind': 'exact-null-input-equivalence-and-archived-output-binding',
        'physical_evidence': 'Pinned H024 evidence reused; no new controller or renderer replay',
        'fresh_physical_null_replay': False, 'source_artifacts_verified': 1808,
        'context_gaps': clearance['context_gaps'], 'nonidentity_authorized': False, 'execution_authorized': False,
        'context_training_allowed': False, 'S2_accepted': False, 'real_accepted': False,
        'new_controller_executions': 0, 'new_renders': 0, 'optimization_evaluations': 0}


def freeze_record():
    return {'version': context.VERSION, 'code_sha256': identities(), 'readiness_report_sha256': READINESS_SHA256,
            'authorization': AUTHORIZATION, 'inventory': {'fixtures': foundation.placement.SPEC['fixtures'],
                'refinements': foundation.placement.SPEC['refinements'], 'modes': ['off', 'six-identity']}}


def build(directory):
    directory = Path(directory)
    if directory.exists():
        raise ValueError('Immutable null snapshot already exists')
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory/'freeze.json', freeze_record())
    report = summarize()
    if foundation.read_json(directory/'freeze.json') != freeze_record():
        raise ValueError('Source changed during null audit')
    report['artifacts'] = {'freeze.json': digest(directory/'freeze.json')}
    write_json(directory/'report.json', report)
    return report


def inspect(directory, expected_report_sha256):
    directory = Path(directory)
    try:
        if not expected_report_sha256 or digest(directory/'report.json') != expected_report_sha256:
            raise ValueError('External null report pin required')
        report = foundation.read_json(directory/'report.json')
        foundation.verify_inventory(directory, report['artifacts'], ['report.json'])
        if foundation.read_json(directory/'freeze.json') != freeze_record():
            raise ValueError('Changed null contract source or authorization')
        expected = summarize()
        if report != {**expected, 'artifacts': {'freeze.json': digest(directory/'freeze.json')}}:
            raise ValueError('Null report differs from reconstructed evidence')
        return {**expected, 'report_sha256': expected_report_sha256, 'read_only': True}
    except (OSError, KeyError, TypeError) as error:
        raise ValueError('Incomplete null contract evidence') from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path)
    parser.add_argument('--inspect', type=Path)
    parser.add_argument('--report-sha256')
    args = parser.parse_args()
    if bool(args.build) == bool(args.inspect):
        parser.error('Choose exactly one of --build or --inspect')
    report = build(args.build) if args.build else inspect(args.inspect, args.report_sha256)
    print(json.dumps({key: value for key, value in report.items()
                      if key not in {'cases', 'archived_bindings', 'programs', 'artifacts'}}, indent=2))


if __name__ == '__main__':
    main()
