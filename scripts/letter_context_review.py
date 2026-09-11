"""Prepare training-only owner comparisons from pinned saved pixels; never fit."""

import argparse
import json
import os
from pathlib import Path
import time

from scripts import letter_context_dimension_evidence as evidence
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = evidence.recovery.BASE.parent/'owner-review-v1'
OUTPUT = BASE/'packet-001'
TEMPLATE = ROOT/'scripts/templates/letter_context_review.html'
INSPECTION_SHA256 = '251d4fd3ff6a9c11ea0162b2b73108d679e22fa6ea7fd2a82756e103fdaddb5b'
DIMENSION_SHA256 = '56e3ed722e086ec1415ea54c179070985c8d4841c19368a7c666db56d4f31f11'
REVIEW_VERSION = 'letter-context-owner-rankings-v1'
TRAINING_PAIRS = ['nn', 'nm', 'un', 'um', 'mn', 'mm']


def manifest_record():
    evidence.load_contract(DIMENSION_SHA256)
    if digest(evidence.OUTPUT/'report.json') != INSPECTION_SHA256:
        raise ValueError('Changed independent inspection report')
    inspection = evidence.physical.preflight.foundation.read_json(evidence.OUTPUT/'report.json')
    if inspection['status'] != 'pass' or inspection['cases_verified'] != 1464:
        raise ValueError('Incomplete mechanical clearance')
    contract = evidence.physical.load_contract(evidence.recovery.CONTRACT_SHA256)
    rows = []
    for text in TRAINING_PAIRS:
        cases = [case for case in contract['cases'] if case['presentation'] and case['fixture']['text'] == text
                 and case['fixture']['role'] == 'train_pairs' and case['refinement'] == 'base']
        cases.sort(key=lambda case: (case['program']['rules'][0]['width_scale'], case['program']['rules'][0]['advance_delta']))
        if len(cases) != 9:
            raise ValueError('Incomplete training grid')
        for index, case in enumerate(cases, 1):
            rule = case['program']['rules'][0]
            source = evidence.recovery.ORIGINAL/'seed-7/first'/case['id']
            image = source/'actual-full.png'
            rows.append({'id': f'{text}-{index}', 'text': text, 'case_id': case['id'], 'rule_id': rule['id'],
                'width_scale': rule['width_scale'], 'advance_delta': rule['advance_delta'],
                'identity': rule['width_scale'] == 1 and rule['advance_delta'] == 0,
                'spacing_only': rule['width_scale'] == 1, 'image_path': str(image.relative_to(ROOT)),
                'src': os.path.relpath(image, OUTPUT), 'image_sha256': digest(image),
                'document_path': str((source/'document.json').relative_to(ROOT)),
                'document_sha256': digest(source/'document.json'), 'image_size': [1169, 390],
                'frame_mm': [-3, 30, 2, 13], 'seed': 7, 'refinement': 'base', 'presentation_dpi': 900})
    ledger = evidence.physical.preflight.foundation.read_json(evidence.recovery.ORIGINAL/'execution.json')['ledger']
    budgets = []
    for seed in (7, 19, 41):
        entry = inspection['seed_41_cumulative_ledger'] if seed == 41 else next(
            row for row in ledger if row['seed'] == seed and row['process'] == 'replay')
        budgets.append({'seed': seed, 'spent_seconds': entry['cumulative_seconds'], 'spent_renders': entry['cumulative_renders'],
            'remaining_seconds': 2700-entry['cumulative_seconds'], 'remaining_renders': 5000-entry['cumulative_renders']})
    return {'version': 'letter-context-owner-review-packet-v1',
        'owner_request': 'Prepare clear visual comparisons, collect owner preferences, and define objective and remaining budget before fitting',
        'independent_inspection_sha256': INSPECTION_SHA256, 'dimension_contract_sha256': DIMENSION_SHA256,
        'training_pairs': TRAINING_PAIRS, 'rows': rows, 'preferences': 'not_collected',
        'objective': {'status': 'proposed_requires_owner_approval', 'rank_semantics': '1 best; ties allowed; 1 through 9; rank gaps have no meaning',
            'cell_loss': 'Number of admissible alternatives ranked strictly better than the candidate / max(1, admissible alternatives - 1)',
            'table_loss': 'Unweighted mean of the six cell losses',
            'exclusions': 'Owner appearance exclusions forbid selection; not reclassified as mechanical failures',
            'ties': ['Fewest nonidentity width/advance parameters', 'Smallest sum(abs(width-1)/0.03 + abs(advance)/0.05)', 'Lexical stable row IDs'],
            'arms': ['Identity context off', 'Best spacing-only with width=1', 'Joint stroke-context width and advance'],
            'matched_advance_control': 'For selected stroke-context widths, also compare width=1 at those exact advances',
            'incomplete_labels': 'No selection if any row is unreviewed, any cell has no admissible row, or owner has not approved the objective',
            'identity': 'May win; ties do not force deformation; an owner-excluded identity blocks a three-arm preference claim pending review'},
        'budget': {'seeds': budgets, 'combined_seconds_per_seed': 2700, 'combined_renders_per_seed': 5000,
            'p3_new_physical_runs_authorized': 0, 'p3_new_renders_authorized': 0,
            'p3_packaging': 'Read-only saved-file indexing and browser layout; no simulation/raster generation; wall time journaled separately',
            'future_budget_status': 'Exact selected-program inventory and time feasibility still require owner approval; no reset or increase',
            'future_conservative_inventory': {'arms': 4, 'development_texts': 6, 'previous_pair_probes': 3,
                'sealed_texts': 6, 'isolated_controls': 3, 'known_base_regressions': 4, 'refinements': 4, 'processes': 2,
                'controller_runs_per_seed_without_reuse': 536, 'render_calls_per_seed_without_reuse': 1744,
                'scope': 'Proposal only, staged development then sealed evaluation; no sealed pixels are accessed by this packet',
                'planning_seconds_per_seed': [1876, 2320],
                'estimate_limit': 'Rough extrapolation from prior completed process averages, not a runtime guarantee; no safety margin included',
                'time_feasible_under_current_remaining_caps': False}},
        'code_sha256': {str(file.relative_to(ROOT)): digest(file) for file in
            (Path(__file__), TEMPLATE, ROOT/'tests/test_letter_context_review.py')},
        'sealed_holdout_access': False, 'owner_labels_frozen': False, 'budget_ready_for_fitting': False, **evidence.physical.FLAGS}


def verify_images(packet):
    for row in packet['rows']:
        image, document = ROOT/row['image_path'], ROOT/row['document_path']
        if digest(image) != row['image_sha256'] or digest(document) != row['document_sha256']:
            raise ValueError('Changed review image or document')
        saved = evidence.physical.preflight.foundation.read_json(document)
        if saved['frame_mm'] != row['frame_mm'] or saved['fixture']['role'] != 'train_pairs' or saved['fixture']['text'] != row['text']:
            raise ValueError('Wrong review frame or training partition')
        evidence.verify_presentation(image, row['frame_mm'], row['presentation_dpi'])


def validate_review(response, packet):
    required = {'version', 'packet_sha256', 'author', 'objective_approved', 'reviews'}
    if (set(response) != required or response['version'] != REVIEW_VERSION
            or response['packet_sha256'] != object_digest(packet) or not isinstance(response['author'], str)
            or type(response['objective_approved']) is not bool or type(response['reviews']) is not dict
            or set(response['reviews']) != {row['id'] for row in packet['rows']}):
        raise ValueError('Wrong review schema, packet or inventory')
    pending, admissible = [], {text: 0 for text in TRAINING_PAIRS}
    for row in packet['rows']:
        label = response['reviews'][row['id']]
        if (type(label) is not dict or set(label) != {'rank', 'excluded', 'note'} or type(label['excluded']) is not bool
                or not isinstance(label['note'], str) or (label['excluded'] and label['rank'] is not None)
                or (label['rank'] is not None and (type(label['rank']) is not int or not 1 <= label['rank'] <= 9))):
            raise ValueError('Malformed rank or exclusion')
        if not label['excluded'] and label['rank'] is None:
            pending.append(row['id'])
        elif not label['excluded']:
            admissible[row['text']] += 1
    empty = [text for text, count in admissible.items() if not count]
    return {'labels_complete': not pending and not empty and bool(response['author'].strip()),
        'pending_rows': pending, 'cells_without_admissible_variant': empty,
        'objective_approved': response['objective_approved'], 'owner_labels_frozen': False,
        'budget_ready_for_fitting': False, 'authority': 'Claimed owner review; explicit repository confirmation required before freezing',
        **evidence.physical.FLAGS}


def prepare():
    if OUTPUT.exists():
        raise FileExistsError('Immutable owner review packet already exists')
    started = time.monotonic()
    with evidence.read_only_guard():
        evidence.recovery.verify_original()
        recovery_report = evidence.physical.preflight.foundation.read_json(evidence.recovery.OUTPUT/'report.json')
        if recovery_report['artifacts'] != evidence.physical.artifact_map(evidence.recovery.OUTPUT, {'report.json'}):
            raise ValueError('Changed recovery artifacts')
        packet = manifest_record()
        verify_images(packet)
        OUTPUT.mkdir(parents=True, exist_ok=False)
        write_json(OUTPUT/'manifest.json', packet)
        html = TEMPLATE.read_text().replace('__PACKET_JSON__', json.dumps(packet).replace('<', '\\u003c'))
        html = html.replace('__PACKET_SHA__', object_digest(packet))
        (OUTPUT/'index.html').write_text(html)
        receipt = {'status': 'prepared_waiting_for_owner', 'packet_sha256': object_digest(packet),
            'manifest_file_sha256': digest(OUTPUT/'manifest.json'), 'index_sha256': digest(OUTPUT/'index.html'),
            'rows': len(packet['rows']), 'controller_executions': 0, 'raster_renders': 0,
            'packaging_seconds': time.monotonic()-started, 'preferences_collected': False,
            'objective_status': packet['objective']['status'], 'budget_ready_for_fitting': False, **evidence.physical.FLAGS}
        write_json(OUTPUT/'preparation.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--validate-review', type=Path)
    args = parser.parse_args()
    if args.prepare:
        result = prepare()
    else:
        packet = evidence.physical.preflight.foundation.read_json(OUTPUT/'manifest.json')
        if packet != manifest_record():
            raise ValueError('Changed packet or source')
        result = validate_review(json.loads(args.validate_review.read_text()), packet)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
