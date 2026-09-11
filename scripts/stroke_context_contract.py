"""Opt-in bounded occurrence geometry; non-null documents cannot enter execution."""

import copy
import argparse
from dataclasses import asdict, replace
import gzip
import json
import math
from pathlib import Path

from scripts import letter_context_contract as legacy
from scripts import stroke_context_audit as audit
from scribesim.evofit.connected_contract import require_joins
from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handflow.curve_tangents import retime_curve_tangents
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json
from scribesim.pathguide.gesture_actions import action_bundle


VERSION = 'stroke-context-spans-v1'
CONTRACT = audit.BASE/'stroke_context_v1/contract/contract.json'
CONTRACT_SHA256 = 'f438dc9f8d4e9c8464dfe183346117b21c3a5f97da60e34fe5539d402b25fd3b'
INVESTIGATION = 'd7eb422948f7de6696221d2f026559ca603fb84a95e713e9e6cdce5aa95a6b75'
PROPOSAL = '9f0076010c4fdf9d539527e0333bb0d8c36982a458bb493391645201592dad87'


def contract_pin():
    return digest(CONTRACT)


def load_contract(checksum):
    if checksum != CONTRACT_SHA256 or contract_pin() != checksum:
        raise ValueError('External owner contract pin required')
    contract = audit.read_json(CONTRACT)
    expected = {'version': VERSION, 'candidate_sha256': legacy.CANDIDATE_SHA256,
                'investigation_sha256': INVESTIGATION, 'proposal_sha256': PROPOSAL,
                'hypotheses': ['H0', 'H1', 'H2', 'H3'], 'previous_gap_bin_xheight': 1.2,
                'angles_deg': [-1, 0, 1], 'maximum_handle_displacement_mm': .04,
                'admitted_transition': 'pen_up_transfer', 'triple_admission': False,
                'execution_authorized': False, 'fitting_authorized': False}
    if any(object_digest(contract.get(key)) != object_digest(value) for key, value in expected.items()):
        raise ValueError('Changed reviewed scope or bounds')
    if (digest(audit.OUTPUT/'report.json') != INVESTIGATION
            or digest(audit.OUTPUT.parent/'README.md') != PROPOSAL):
        raise ValueError('Changed externally pinned investigation or proposal')
    return contract


def request(hypothesis='H0'):
    return {'version': VERSION, 'hypothesis': hypothesis, 'transition_intent': 'pen_up_transfer'}


def validate_request(value):
    if (type(value) is not dict or set(value) != {'version', 'hypothesis', 'transition_intent'}
            or value['version'] != VERSION or value['hypothesis'] not in ('H0', 'H1', 'H2', 'H3')
            or value['transition_intent'] != 'pen_up_transfer'):
        raise ValueError('Unsupported request, selector keys or transition intent')


def split_cubic(cubic):
    levels = [copy.deepcopy(cubic)]
    while len(levels[-1]) > 1:
        levels.append([[(before[axis]+after[axis])/2 for axis in range(2)]
                       for before, after in zip(levels[-1], levels[-1][1:])])
    return [[level[0] for level in levels], [level[-1] for level in reversed(levels)]]


def rotate_handle(cubic, control_point, angle):
    anchor = cubic[0 if control_point == 1 else 3]
    before = cubic[control_point]
    horizontal, vertical = [before[axis]-anchor[axis] for axis in range(2)]
    radians = math.radians(angle)
    after = [anchor[0]+horizontal*math.cos(radians)-vertical*math.sin(radians),
             anchor[1]+horizontal*math.sin(radians)+vertical*math.cos(radians)]
    displacement = math.dist(before, after)*3.5
    if displacement > .04 or not math.isfinite(displacement):
        raise ValueError('Body exception exceeds reviewed displacement cap')
    cubic[control_point] = after
    return displacement


def _derive(candidate, text, program, refinement, checksum):
    load_contract(checksum)
    audit.require_probe(text)
    validate_request(program)
    if object_digest(candidate) != legacy.CANDIDATE_SHA256:
        raise ValueError('Changed canonical candidate')
    if refinement not in legacy.foundation.placement.SPEC['refinements']:
        raise ValueError('Unsupported refinement')
    baseline = compile_gestures(text, candidate)
    derived = copy.deepcopy(baseline)
    source_rows = baseline['strokes']
    rows = derived['strokes']
    contexts, edits, boundaries = [], [], []
    for letter_index, recipe in enumerate(text):
        indices = [index for index, row in enumerate(source_rows) if row['letter'] == letter_index]
        if len(indices) > 6:
            raise ValueError('Canonical expansion cap exceeded')
        first, last = indices[0], indices[-1]
        entry, exit_port = audit.port(source_rows[first], True), audit.port(source_rows[last], False)
        previous = audit.port(source_rows[first-1], False) if first else None
        following = audit.port(source_rows[last+1], True) if last+1 < len(rows) else None
        gap = entry['position_local'][0]-previous['position_local'][0] if previous else None
        previous_bin = 'BOS' if previous is None else 'near' if gap <= 1.2 else 'far'
        following_class = 'EOS' if following is None else legacy.ENTRY_CLASSES[text[letter_index+1]]
        contexts.append({'current_recipe': recipe, 'letter_owner': letter_index,
            'previous_class': 'BOS' if previous is None else 'stem-down-baseline',
            'previous_bin': previous_bin, 'previous_horizontal_gap_xheight': gap,
            'following_class': following_class, 'entry': entry, 'exit': exit_port,
            'previous_exit': previous, 'following_entry': following,
            'transition_intent': 'pen_up_transfer', 'state_basis': 'canonical-before-any-derivation'})
        entry_angle = 0 if previous is None or program['hypothesis'] not in ('H1', 'H3') else 1 if previous_bin == 'near' else -1
        exit_angle = 0 if following is None or program['hypothesis'] not in ('H2', 'H3') else 1 if following_class == 'stem-entry' else -1
        for index, control_point, angle, role in ((first, 1, entry_angle, 'entry'), (last, 2, exit_angle, 'exit')):
            if angle:
                if len(rows[index]['cubics']) != 1:
                    raise ValueError('Unreviewed canonical cubic span')
                displacement = rotate_handle(rows[index]['cubics'][0], control_point, angle)
                edits.append({'occurrence_id': rows[index]['occurrence_id'], 'canonical_cubic': 0,
                    'parameter_range': [0, 1], 'body_exception_role': role, 'control_point': control_point,
                    'angle_deg': angle, 'displacement_mm': displacement})
        if following is not None:
            next_row = source_rows[last+1]
            boundaries.append({'kind': 'pen_up_transfer', 'departure_gesture_owner': rows[last]['gesture_occurrence_id'],
                'landing_gesture_owner': next_row['gesture_occurrence_id'],
                'departure_letter_owner': letter_index, 'landing_letter_owner': letter_index+1,
                'departure_contact_run': rows[last]['contact_run_id'], 'landing_contact_run': next_row['contact_run_id'],
                'events_required': ['lift', 'air', 'landing'], 'ink_owners': [], 'overlap_allowance': 'none',
                'new_ink_segments': [], 'physical_event_evidence': 'not_generated'})
    require_joins(rows)
    lineage = []
    for source, changed in zip(source_rows, rows):
        lineage.append({'owner': {key: value for key, value in source.items() if key != 'cubics'},
            'source_sha256': object_digest(source['cubics']), 'derived_canonical_sha256': object_digest(changed['cubics']),
            'canonical_spans': [{'cubic': 0, 'parameter_range': [0, 1]}],
            'entry_port': audit.port(changed, True), 'exit_port': audit.port(changed, False),
            'body_policy': 'all control points fixed except declared first-C1/last-C2',
            'output_parameter_ranges': [[0, .5], [.5, 1]] if refinement == 'subdivision' else [[0, 1]]})
    if program['hypothesis'] == 'H0':
        model = legacy.foundation.placement.evaluation.subdivide(candidate) if refinement == 'subdivision' else candidate
        derived = compile_gestures(text, model)
    else:
        derived['schema_version'] = VERSION+'-geometry-only'
        derived['canonical_model_sha256'] = derived.pop('model_sha256')
        if refinement == 'subdivision':
            for row in rows:
                row['cubics'] = split_cubic(row['cubics'][0])
    for provenance, row in zip(lineage, derived['strokes']):
        provenance['output_geometry_sha256'] = object_digest(row['cubics'])
    return {'version': VERSION, 'contract_sha256': checksum, 'request': copy.deepcopy(program),
            'text': text, 'refinement': refinement, 'placement': 'canonical-origin',
            'compiled': derived, 'contexts': contexts, 'edits': edits, 'boundaries': boundaries,
            'lineage': lineage, 'execution_authorized': False, 'physical_accepted': False,
            'finite_nib_overlap_evaluated': False, 'context_training_allowed': False,
            'fitting_authorized': False, 'S2_accepted': False, 'real_accepted': False}


def compile_context(candidate, text, program, refinement, contract_sha256):
    return _derive(candidate, text, program, refinement, contract_sha256)


def verify_document(document, candidate, contract_sha256):
    try:
        expected = _derive(candidate, document['text'], document['request'], document['refinement'], contract_sha256)
        if object_digest(expected) != object_digest(document):
            raise ValueError('Changed geometry, ports, ownership, selectors or lineage')
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('Malformed contextual document') from error
    return True


def prepare_null_plan(document, candidate, contract_sha256):
    verify_document(document, candidate, contract_sha256)
    if document['request']['hypothesis'] != 'H0':
        raise ValueError('Only exact H0 has a planner; nonidentity requires a later reviewed consumer')
    refinement = document['refinement']
    model = legacy.foundation.placement.evaluation.subdivide(candidate) if refinement == 'subdivision' else candidate
    bundle = action_bundle(document['text'], model,
        step_mm=legacy.foundation.placement.SPEC['refinements'][refinement][0], include_curve_positions=True)
    timed = retime_curve_tangents(bundle.plan, bundle.owners, document['compiled']['strokes'])
    return replace(bundle, plan=timed.plan, owners=[bundle.owners[index] for index in timed.source_indices]), timed


def snapshot(contract_sha256):
    from scripts import letter_context_evidence as archived
    destination = CONTRACT.parent/'snapshot-001'
    if destination.exists():
        raise FileExistsError('Immutable contract evidence already exists')
    load_contract(contract_sha256)
    with audit.evidence.read_only_guard():
        sources = audit.verify_sources()
        candidate = audit.read_json(audit.CANDIDATE)
        physical_contract = audit.read_json(audit.physical.BASE/'prepared-001/contract.json')
        cases, bindings = [], []
        for text in audit.PROBES:
            for refinement in legacy.foundation.placement.SPEC['refinements']:
                for hypothesis in ('H0', 'H1', 'H2', 'H3'):
                    document = compile_context(candidate, text, request(hypothesis), refinement, contract_sha256)
                    verify_document(document, candidate, contract_sha256)
                    result = {'text': text, 'refinement': refinement, 'hypothesis': hypothesis,
                              'document_sha256': object_digest(document), 'edits': document['edits']}
                    if hypothesis == 'H0':
                        model = legacy.foundation.placement.evaluation.subdivide(candidate) if refinement == 'subdivision' else candidate
                        if document['compiled'] != compile_gestures(text, model):
                            raise ValueError('Null compilation differs from frozen baseline')
                        bundle, timed = prepare_null_plan(document, candidate, contract_sha256)
                        result['bundle_sha256'] = object_digest(asdict(bundle))
                        result['timing_sha256'] = object_digest(asdict(timed))
                        matching = [case for case in physical_contract['cases']
                            if case['fixture']['text'] == text and case['refinement'] == refinement
                            and case['fixture']['shift'] == [0, 0]
                            and all(rule['width_scale'] == 1 and rule['advance_delta'] == 0 for rule in case['program']['rules'])]
                        if matching:
                            path = audit.recovery.ORIGINAL/'seed-7/first'/matching[0]['id']/'trace.json.gz'
                            with gzip.open(path, 'rt') as stream:
                                raw = json.load(stream)
                            bindings.append({'text': text, 'refinement': refinement,
                                'path': str(path.relative_to(ROOT)), 'file_sha256': digest(path),
                                **archived.bind_archived_run(raw, bundle, timed, refinement)})
                    cases.append(result)
        report = {'version': VERSION, 'status': 'structural_contract_pass', 'contract_sha256': contract_sha256,
            'sources': sources, 'cases': cases, 'archived_null_bindings': bindings,
            'archive_scope': 'Existing origin-aligned identity seed-7 cases only; no substituted placed mu or missing nu/uu traces',
            'code_sha256': digest(Path(__file__)), 'tests_sha256': digest(ROOT/'tests/test_stroke_context_contract.py'),
            'read_only': True, 'controller_executions': 0, 'raster_renders': 0, 'optimization_evaluations': 0,
            'execution_authorized': False, 'physical_accepted': False, 'S2_accepted': False,
            'real_accepted': False, 'fitting_authorized': False, 'finite_nib_overlap_evaluated': False}
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/'report.json', report)
    return {'report_sha256': digest(destination/'report.json'), 'cases': len(cases), 'archived_bindings': len(bindings)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot'])
    parser.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(snapshot(args.contract_sha256), indent=2))


if __name__ == '__main__':
    main()
