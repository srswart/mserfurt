"""Prepare bounded nominal comparisons; image and physical execution gates stay closed."""

import argparse
import copy
import json
import math
from pathlib import Path

from scripts import stroke_context_contract as context
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = context.CONTRACT.parent.parent/'demonstrator'
OUTPUT = BASE/'prepared-001'
HYPOTHESES = ('H0', 'H1', 'H2', 'H3')
FRAME = [-3, 30, 2, 13]
CONTRACT_REPORT = '8af42ea3bcec6ac97546856798f1aec970dd96a6cd59a01a1822ef45761f42e4'


def documents(candidate):
    return {text+':'+hypothesis: context.compile_context(candidate, text, context.request(hypothesis),
            'base', context.CONTRACT_SHA256) for text in context.audit.PROBES for hypothesis in HYPOTHESES}


def points(document):
    return [point for row in document['compiled']['strokes'] for cubic in row['cubics'] for point in cubic]


def deltas(document, baseline, letter):
    result = []
    for row, source in zip(document['compiled']['strokes'], baseline['compiled']['strokes']):
        if row['letter'] == letter:
            result.extend([[after[axis]-before[axis] for axis in range(2)]
                for cubic, original in zip(row['cubics'], source['cubics'])
                for after, before in zip(cubic, original)])
    return result


def equal_deltas(first, second):
    return len(first) == len(second) and all(math.dist(before, after) <= 1e-12 for before, after in zip(first, second))


def analyze(inventory, frame=FRAME):
    expected_keys = {text+':'+hypothesis for text in context.audit.PROBES for hypothesis in HYPOTHESES}
    if set(inventory) != expected_keys:
        raise ValueError('Changed diagnostic inventory')
    candidate = context.audit.read_json(context.audit.CANDIDATE)
    maximum, changed_handles = 0.0, 0
    for text in context.audit.PROBES:
        baseline = inventory[text+':H0']
        for hypothesis in HYPOTHESES:
            document = inventory[text+':'+hypothesis]
            context.verify_document(document, candidate, context.CONTRACT_SHA256)
            if document['text'] != text or document['request']['hypothesis'] != hypothesis:
                raise ValueError('Swapped diagnostic identity')
            if document['compiled']['lines'] != baseline['compiled']['lines']:
                raise ValueError('Changed advance in matched-advance comparison')
            allowed = {(change['occurrence_id'], change['control_point']) for change in document['edits']}
            for row, original in zip(document['compiled']['strokes'], baseline['compiled']['strokes']):
                if {key: value for key, value in row.items() if key != 'cubics'} != {
                        key: value for key, value in original.items() if key != 'cubics'}:
                    raise ValueError('Changed ownership or contact state')
                for index, (after, before) in enumerate(zip(row['cubics'][0], original['cubics'][0])):
                    delta = math.dist(after, before)*3.5
                    if after != before and (row['occurrence_id'], index) not in allowed:
                        raise ValueError('Undeclared body or anchor change')
                    if delta > .04:
                        raise ValueError('Changed handle bound')
                    changed_handles += int(delta > 0)
                    maximum = max(maximum, delta)
            for point in points(document):
                horizontal, vertical = point[0]*3.5, 10-point[1]*3.5
                margin = .225+.001
                if not (frame[0]+margin <= horizontal <= frame[1]-margin
                        and frame[2]+margin <= vertical <= frame[3]-margin):
                    raise ValueError('Incomplete nominal finite-nib control-hull frame')
    def delta(text, hypothesis, letter):
        return deltas(inventory[text+':'+hypothesis], inventory[text+':H0'], letter)
    previous = not equal_deltas(delta('nn', 'H1', 1), delta('mn', 'H1', 1))
    following = not equal_deltas(delta('un', 'H2', 0), delta('um', 'H2', 0))
    same_bin = equal_deltas(delta('nn', 'H1', 1), delta('un', 'H1', 1))
    if not all((previous, following, same_bin)):
        raise ValueError('Expected shared causal controls failed')
    for text in context.audit.PROBES:
        baseline = inventory[text+':H0']
        for letter in range(len(text)):
            entry = deltas(inventory[text+':H1'], baseline, letter)
            exit_delta = deltas(inventory[text+':H2'], baseline, letter)
            combined = deltas(inventory[text+':H3'], baseline, letter)
            expected = [[before[axis]+after[axis] for axis in range(2)] for before, after in zip(entry, exit_delta)]
            if not equal_deltas(combined, expected):
                raise ValueError('Unexpected interaction beyond independent entry/exit edits')
        if len(text) == 1 and any(points(inventory[text+':'+hypothesis]) != points(baseline) for hypothesis in HYPOTHESES):
            raise ValueError('Isolated BOS/EOS control changed')
    return {'previous_near_far_distinct': previous, 'following_stem_rise_distinct': following,
        'same_previous_bin_same_effect': same_bin, 'all_anchors_and_advances_exact': True,
        'independent_entry_exit_composition': True, 'maximum_control_delta_mm': maximum,
        'changed_handles_across_documents': changed_handles, 'delta_comparison_tolerance_local': 1e-12,
        'frame_size_pixels': list(context.audit.evidence.renderer_size(frame, 900)),
        'nominal_finite_nib_control_hulls_contained': True,
        'containment_scope': 'Bezier convex hull plus 0.225-mm nib radius and 0.001-mm nominal flattening margin; not actual ink',
        'physical_containment_measured': False, 'owner_usefulness_measured': False}


def protocol():
    physical_contract = context.audit.read_json(context.audit.physical.BASE/'prepared-001/contract.json')
    return {'version': 'stroke-context-demonstrator-preflight-v1',
        'contract_sha256': context.CONTRACT_SHA256, 'contract_report_sha256': CONTRACT_REPORT,
        'texts': list(context.audit.PROBES), 'hypotheses': list(HYPOTHESES), 'refinement': 'base',
        'nominal_rendering': {'approved': False, 'image_count': 48, 'frame_mm': FRAME, 'dpi': 900,
            'size_pixels': list(context.audit.evidence.renderer_size(FRAME, 900)),
            'representation': 'nominal fixed-edge swept geometry only; neither desired timed motion nor actual ink',
            'maximum_flattening_error_mm': .001, 'tool': {'full_edge_mm': .45, 'angle_deg': 40},
            'wall_time_limit_seconds': 300, 'output_limit_bytes': 100*1024**2,
            'minimum_free_bytes': 5*1024**3, 'automatic_retries': 0,
            'extra_zoom_or_diff_rasters': 0, 'html_review_pages': 1,
            'limits_are': 'Prospective hard stop limits, not measured runtime estimates or physical budget resets'},
        'comparisons': [
            {'name': 'previous-only', 'texts': ['nn', 'mn'], 'focus': 'second n', 'arms': ['H0', 'H1'], 'fixed': 'following EOS'},
            {'name': 'same-bin control', 'texts': ['nn', 'un'], 'focus': 'second n', 'arms': ['H0', 'H1'], 'expected': 'same local delta'},
            {'name': 'following-only', 'texts': ['un', 'um'], 'focus': 'first u', 'arms': ['H0', 'H2'], 'fixed': 'previous BOS'},
            {'name': 'combined entry-exit', 'texts': list(context.audit.PAIRS), 'arms': list(HYPOTHESES),
             'limitation': 'Pairs have no middle letter with both neighbors; no two-sided within-letter interaction claim'}],
        'unsupported_arms': {'transition-only': 'join/retrace unadmitted; unchanged lift arm duplicates H0',
            'form-plus-new-transition': 'no new transition admitted',
            'spacing-only': 'not generated; all advances exact, old affine grid remains paused'},
        'view_specification': {'full_frame': 'Show complete untouched fixed-scale image for each arm',
            'diagnostics': 'Synchronized zoom/blink reuse same images; canonical span/port and control-delta annotations toggle separately',
            'contact': 'Semantic pen-down/corner and lift-air-landing schematic only; no invented seconds or physical timeline',
            'labels': ['NOMINAL GEOMETRY — NOT ACTUAL INK', 'Diagnostic magnification is not acceptance evidence'],
            'actual_desired_panels': 'Absent until separately authorized physical execution; never substitute nominal as actual'},
        'owner_feedback': [], 'owner_questions': ['Can you identify the changed stroke at normal scale?',
            'Does it help the lettering or is it unnecessary?', 'Would you prefer unchanged separate lettering?'],
        'allowed_judgments': ['useful', 'indistinguishable', 'unnecessary', 'less readable', 'separate lettering preferred', 'unsupported'],
        'physical': {'approved': False, 'texts': list(context.audit.PROBES), 'hypotheses': list(HYPOTHESES),
            'refinements': list(physical_contract['refinements']), 'seeds': [7, 19, 41], 'processes': ['first', 'replay'],
            'executions': 12*4*4*3*2, 'metric_images_per_execution': 3,
            'base_presentation_images': 12*4*3*2*2, 'adverse_control_render_reserve_per_seed': 24,
            'render_calls_upper_bound': 12*4*4*3*2*3+12*4*3*2*2+24*3,
            'frame_mm': FRAME, 'metric_dpi': 180, 'presentation_dpi': 900,
            'unchanged_mechanical_criteria': copy.deepcopy(physical_contract['criteria']),
            'proposed_additional_checks': {'undeclared_canonical_control_point_changes': 0,
                'anchor_or_advance_changes': 0, 'maximum_handle_delta_mm': .04,
                'directed_port_unit_vector_error_max': 1e-8, 'handle_length_error_mm_max': 1e-12,
                'missing_or_duplicate_boundary_events': 0, 'unowned_new_ink_segments': 0},
            'remaining_seconds': {'7': 582.1848200419918, '19': 988.4159828750417, '41': 579.0667824570555},
            'remaining_renders': {'7': 3426, '19': 3426, '41': 3259},
            'time_feasibility': 'Unmeasured; do not assume residual time suffices. No fresh allowance or automatic retry.',
            'blocking_work': ['owner nominal usefulness review', 'reviewed non-null planner',
                'independent measurement reader', 'freeze local finite-nib windows and full adverse-control schedule',
                'time/storage estimate and explicit cumulative execution budget approval'],
            'inventory_status': 'Concrete upper-bound proposal, not execution-ready protocol'},
        'controller_executions_allowed_now': 0, 'raster_renders_allowed_now': 0, 'fitting_authorized': False}


def prepare(destination=OUTPUT):
    if destination.exists():
        raise FileExistsError('Immutable demonstrator preparation exists')
    with context.audit.evidence.read_only_guard():
        context.load_contract(context.CONTRACT_SHA256)
        file = context.CONTRACT.parent/'snapshot-001/report.json'
        if digest(file) != CONTRACT_REPORT:
            raise ValueError('Changed contract report')
        prior = context.audit.read_json(file)
        if prior['code_sha256'] != digest(Path(context.__file__)) or prior['tests_sha256'] != digest(ROOT/'tests/test_stroke_context_contract.py'):
            raise ValueError('Changed frozen contract source')
        sources = context.audit.verify_sources()
        inventory = documents(context.audit.read_json(context.audit.CANDIDATE))
        analysis = analyze(inventory)
        proposed = protocol()
        report = {'status': 'prepared_nominal_render_approval_pending', 'sources': sources, 'analysis': analysis,
            'documents': {key: object_digest(value) for key, value in inventory.items()},
            'protocol_object_sha256': object_digest(proposed), 'code_sha256': digest(Path(__file__)),
            'tests_sha256': digest(ROOT/'tests/test_stroke_context_preview.py'), 'read_only': True,
            'controller_executions': 0, 'raster_renders': 0, 'optimization_evaluations': 0,
            'owner_feedback_collected': False, 'physical_accepted': False, 'S2_accepted': False, 'real_accepted': False}
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/'documents.json', inventory)
    write_json(destination/'protocol.json', proposed)
    report['files'] = {name: digest(destination/name) for name in ('documents.json', 'protocol.json')}
    write_json(destination/'report.json', report)
    return {'report_sha256': digest(destination/'report.json'), 'protocol_sha256': digest(destination/'protocol.json'),
            'status': report['status']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare'])
    parser.parse_args()
    print(json.dumps(prepare(), indent=2))


if __name__ == '__main__':
    main()
