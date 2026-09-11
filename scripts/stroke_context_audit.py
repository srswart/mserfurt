"""Read-only canonical span and saved-contact investigation; never executes a model."""

import argparse
import gzip
import json
import math
from pathlib import Path
import re

from scripts import letter_context_contract as context
from scripts import letter_context_dimension_evidence as evidence
from scripts import letter_context_physical as physical
from scripts import letter_context_recovery as recovery
from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = ROOT/'shared/training/konrad_hand_recovery/stroke_gestures_v2'
CANDIDATE = BASE/'letters/upright/run-001/candidate.json'
OUTPUT = BASE/'stroke_context_v1/investigation/snapshot-001'
PAIRS = ('nn', 'nm', 'un', 'um', 'mn', 'mm', 'nu', 'uu', 'mu')
PROBES = ('n', 'u', 'm', *PAIRS)
PROPOSED = ('nuu', 'uuu', 'muu')
SEALED = ('num', 'mun', 'umn', 'nmn', 'umu', 'mum')
DIMENSION_CONTRACT = '56e3ed722e086ec1415ea54c179070985c8d4841c19368a7c666db56d4f31f11'
DIMENSION_REPORT = '251d4fd3ff6a9c11ea0162b2b73108d679e22fa6ea7fd2a82756e103fdaddb5b'
CANDIDATE_FILE = '01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd'


def read_json(path):
    return json.loads(path.read_text())


def require_probe(text):
    if text not in PROBES:
        raise ValueError('Text not admitted to read-only geometry/trace inventory')


def direction(start, end):
    vector = [end[index]-start[index] for index in range(2)]
    length = math.hypot(*vector)
    if not math.isfinite(length) or length <= 1e-12:
        raise ValueError('Degenerate directed port')
    return [value/length for value in vector]


def port(stroke, entry):
    cubic = stroke['cubics'][0 if entry else -1]
    return {'position_local': cubic[0 if entry else 3],
            'tangent_local_y_up': direction(cubic[0], cubic[1]) if entry else direction(cubic[2], cubic[3]),
            'contact_intent': 'down', 'action_sha256': stroke['action_sha256'],
            'occurrence_id': stroke['occurrence_id']}


def geometry(candidate):
    if object_digest(candidate) != context.CANDIDATE_SHA256:
        raise ValueError('Changed canonical candidate')
    letters = {}
    for letter in 'num':
        compiled = compile_gestures(letter, candidate)
        strokes = compiled['strokes']
        spans = []
        for index, stroke in enumerate(strokes):
            roles = ['body'] + (['entry'] if index == 0 else []) + (['exit'] if index == len(strokes)-1 else [])
            spans.append({'owner': {key: value for key, value in stroke.items() if key != 'cubics'},
                          'roles': roles, 'editable': False,
                          'cubics': [{'canonical_cubic': number, 'parameter_range': [0, 1],
                                      'control_points_local': cubic} for number, cubic in enumerate(stroke['cubics'])],
                          'entry_port': port(stroke, True), 'exit_port': port(stroke, False)})
        letters[letter] = {'compiled_sha256': object_digest(compiled), 'spans': spans,
                           'contact_runs': sorted({stroke['contact_run_id'] for stroke in strokes}),
                           'entry': port(strokes[0], True), 'exit': port(strokes[-1], False)}
    boundaries = []
    for text in PAIRS:
        rows = compile_gestures(text, candidate)['strokes']
        previous = [row for row in rows if row['letter'] == 0][-1]
        following = next(row for row in rows if row['letter'] == 1)
        exit_port, entry_port = port(previous, False), port(following, True)
        boundaries.append({'example': text, 'previous_exit_class': 'stem-down-baseline',
            'following_entry_class': context.ENTRY_CLASSES[text[1]],
            'exit': exit_port, 'entry': entry_port,
            'endpoint_gap_mm': math.dist(exit_port['position_local'], entry_port['position_local'])*candidate['x_height_mm'],
            'baseline': 'pen_up_transfer', 'contact_runs': [previous['contact_run_id'], following['contact_run_id']],
            'direct_join_supported': False, 'cross_letter_retrace_supported': False,
            'reason': 'Separated endpoints and separate contact runs; no declared cross-letter path or overlap owners'})
    return {'coordinate_frame': 'canonical local x-height y-up; physical y is inverted',
            'role_policy': 'First and last whole canonical occurrences overlap protected body; roles do not grant edits',
            'body_policy': 'All control points, endpoints, advances, action state and internal joins frozen',
            'letters': letters, 'boundaries': boundaries,
            'selectors': ['current_recipe', 'previous_exit_class_or_BOS', 'following_entry_class_or_EOS', 'transition_intent'],
            'previous_classes': ['BOS', 'stem-down-baseline'],
            'following_classes': ['EOS', 'stem-entry', 'rise-entry'],
            'limitation': 'All three previous letters share directed exit class; distinguishing them needs reviewed state beyond class alone',
            'unsupported': ['unknown recipe', 'word boundary', 'line boundary', 'cross-letter join', 'cross-letter retrace']}


def trace_summary(raw, owners):
    result = {'events': len(raw['trace']), 'pen_down_upward_events': 0, 'lift_events': 0,
              'landing_events': 0, 'air_events': 0, 'air_transfers': []}
    for event in raw['trace']:
        owner = event['owner']
        if type(event['contact']) is not bool or type(event['previous_contact']) is not bool:
            raise ValueError('Invalid explicit contact state')
        if owner['kind'] == 'air':
            if event['contact']:
                raise ValueError('Air owner cannot claim contact')
            result['air_events'] += 1
            transfer = {'from': owner['from'], 'to': owner['to']}
            if transfer not in result['air_transfers']:
                result['air_transfers'].append(transfer)
        elif owner['kind'] == 'stroke':
            if owners.get(owner['occurrence_id']) != owner['contact_run_id']:
                raise ValueError('Changed stroke contact-run owner')
            if not event['contact']:
                raise ValueError('Stroke owner without contact')
        else:
            raise ValueError('Unknown trace owner')
        result['lift_events'] += int(event['previous_contact'] and not event['contact'])
        result['landing_events'] += int(not event['previous_contact'] and event['contact'])
        result['pen_down_upward_events'] += int(event['contact'] and event['to_mm'][1] < event['from_mm'][1])
    return result


def verify_sources():
    if digest(CANDIDATE) != CANDIDATE_FILE:
        raise ValueError('Changed candidate file')
    manifest = recovery.verify_original()
    evidence.load_contract(DIMENSION_CONTRACT)
    report = read_json(recovery.OUTPUT/'report.json')
    if physical.artifact_map(recovery.OUTPUT, {'report.json'}) != report['artifacts']:
        raise ValueError('Changed recovery artifacts')
    if digest(evidence.OUTPUT/'report.json') != DIMENSION_REPORT:
        raise ValueError('Changed independent inspection pin')
    inspection = read_json(evidence.OUTPUT/'report.json')
    if inspection['status'] != 'pass' or not inspection['read_only']:
        raise ValueError('Independent inspection not cleared')
    return {'candidate_file_sha256': CANDIDATE_FILE, 'candidate_object_sha256': context.CANDIDATE_SHA256,
            'original_manifest_sha256': recovery.FAILURE_SHA256,
            'original_artifacts_verified': len(manifest['artifacts']),
            'recovery_contract_sha256': evidence.RECOVERY_CONTRACT_SHA256,
            'recovery_report_sha256': evidence.RECOVERY_REPORT_SHA256,
            'recovery_artifacts_verified': len(report['artifacts']),
            'dimension_contract_sha256': DIMENSION_CONTRACT, 'dimension_report_sha256': DIMENSION_REPORT,
            'scope': 'Verify saved artifact bytes and frozen source contracts; reuse full independent measurement, do not rerun it'}


def exposure():
    paths = sorted((ROOT/'shared/training').rglob('spec-*.json'))
    paths += [ROOT/'scripts/letter_context_variants.py',
              ROOT/'docs/tech-direction/TD-018-addendum-c-letter-context.md']
    paths = [path for path in paths if path.exists()]
    hits = {text: [] for text in (*PROBES, *PROPOSED, *SEALED)}
    for path in paths:
        contents = path.read_text()
        for text in hits:
            if re.search(r'(?<![A-Za-z])'+re.escape(text)+r'(?![A-Za-z])', contents):
                hits[text].append(str(path.relative_to(ROOT)))
    return {'metadata_sources': {str(path.relative_to(ROOT)): digest(path) for path in paths},
            'token_mentions_not_proof_of_execution': hits, 'existing_design_probes': list(PROBES),
            'proposed_triples': {text: {'status': 'not_admitted',
                'reason': 'Bounded metadata audit cannot prove complete historical exposure or absence of other reservations; owner must freeze as design-only before use'} for text in PROPOSED},
            'reserved': list(SEALED), 'sealed_pixels_or_traces_opened': [],
            'coverage_limit': 'spec-*.json registries and named context metadata only; no global absence or unseen-transfer claim'}


def saved_traces(contract):
    results = []
    for text in PROBES:
        require_probe(text)
        cases = [case for case in contract['cases'] if case['fixture']['text'] == text
                 and case['refinement'] == 'base'
                 and all(rule['width_scale'] == 1 and rule['advance_delta'] == 0 for rule in case['program']['rules'])]
        if not cases:
            results.append({'text': text, 'status': 'no_identity_case_in_C006_physical_contract',
                            'scope': 'Canonical geometry only; no new trace generated'})
            continue
        case = cases[0]
        directory = recovery.ORIGINAL/'seed-7/first'/case['id']
        file = directory/'trace.json.gz'
        document = read_json(directory/'document.json')
        with gzip.open(file, 'rt') as stream:
            raw = json.load(stream)
        rows = document['compiled']['strokes']
        summary = trace_summary(raw, {row['occurrence_id']: row['contact_run_id'] for row in rows})
        if summary['lift_events'] != len(text)-1 or summary['landing_events'] != len(text)-1:
            raise ValueError('Unexpected baseline boundary contact transitions')
        results.append({'text': text, 'status': 'saved_trace_audited', 'fixture': case['fixture'],
                        'trace_path': str(file.relative_to(ROOT)), 'trace_sha256': digest(file),
                        'document_sha256': digest(directory/'document.json'), **summary})
    return results


def build_report():
    with evidence.read_only_guard():
        sources = verify_sources()
        contract = read_json(physical.BASE/'prepared-001/contract.json')
        return {'version': 'stroke-context-investigation-v1', 'status': 'audit_complete_owner_review_pending',
                'sources': sources, 'geometry': geometry(contract['candidate']), 'exposure': exposure(),
                'saved_trace_audit': saved_traces(contract),
                'adapter_sha256': digest(Path(__file__)),
                'tests_sha256': digest(ROOT/'tests/test_stroke_context_audit.py'),
                'controller_executions': 0, 'raster_renders': 0, 'read_only': True,
                'owner_scope_approved': False, 'GESTURE_005_authorized': False, **physical.FLAGS}


def snapshot(destination=OUTPUT):
    if destination.exists():
        raise FileExistsError('Immutable audit snapshot already exists')
    result = build_report()
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/'report.json', result)
    return {'report_sha256': digest(destination/'report.json'), 'status': result['status']}


def inspect(destination, checksum):
    if not checksum or digest(destination/'report.json') != checksum:
        raise ValueError('Exact external report pin required')
    if read_json(destination/'report.json') != build_report():
        raise ValueError('Changed derived audit or source inventory')
    return {'status': 'exact_read_only_reinspection_pass', 'report_sha256': checksum}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot', 'inspect'])
    parser.add_argument('--report-sha256')
    args = parser.parse_args()
    print(json.dumps(snapshot() if args.command == 'snapshot' else inspect(OUTPUT, args.report_sha256), indent=2))


if __name__ == '__main__':
    main()
