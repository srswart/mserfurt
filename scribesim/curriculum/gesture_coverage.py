"""Bounded, fail-closed coverage investigation of the frozen v3 non-test corpus."""

import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scribesim.evofit.reference_dataset import _exclusions
from scribesim.evofit.reference_repair import verify_review_lineage
from scribesim.handvalidate.specimen import ROOT, digest, evaluate_benchmark, object_digest, write_json


INPUTS = {
    'manifest.json': 'cb35c78ce0daa6992743c13c30675ae4d3ae0ff05340f192f6684c20df987c36',
    'review.json': '3649753d87cc7116de03a82b622cd43e5c4bc1a61965098fab1a392e883f4608',
    'approvals.json': 'ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356',
    'calibration.json': '0483b14d6b011626d82a330be360cc2db6a4dbef14165ae3931a32528cd139f0',
}


def synthetic_fixtures():
    def line(start, end):
        return [start, [start[axis] + (end[axis] - start[axis]) / 3 for axis in (0, 1)],
                [start[axis] + 2 * (end[axis] - start[axis]) / 3 for axis in (0, 1)], end]

    shapes = [
        ('stem', ['descend'], [line([0, 1], [0, 0])], 'i: stem plus unresolved exit'),
        ('rise', ['rise'], [line([0, 0], [.55, 1])], 'u: entry approach, not a complete letter'),
        ('underturn', ['descend', 'lower_turn', 'rise'],
         [line([0, 1], [0, .25]), [[0, .25], [0, -1 / 12], [.5, -1 / 12], [.5, .25]],
          line([.5, .25], [.5, 1])], 'u: underturn plus stem (4 primitive occurrences)'),
        ('overturn', ['rise', 'upper_turn', 'descend'],
         [line([0, 0], [0, .75]), [[0, .75], [0, 13 / 12], [.5, 13 / 12], [.5, .75]],
          line([.5, .75], [.5, 0])], 'n: overturn plus stem (4 primitive occurrences)'),
        ('compound_curve', ['upper_turn', 'lower_turn'],
         [[[0, 0], [0, 1], [.5, 1], [.5, .5]], [[.5, .5], [.5, 0], [1, 0], [1, 1]]],
         'm: alternative compound construction hypothesis, not an accepted recipe'),
        ('left_bowl', ['left_bowl'], [[[.7, 1], [-.1, 1], [-.1, 0], [.7, 0]]],
         'c: open bowl construction hypothesis'),
        ('upper_loop', ['upper_loop'], [[[0, 0], [-.4, 1.4], [.6, 1.4], [0, 0]]],
         'l: loop plus stem construction hypothesis'),
        ('lower_loop', ['lower_loop'], [[[0, 0], [.6, -1.4], [-.4, -1.4], [0, 0]]],
         'g: descender only; bowl/attachment unresolved'),
    ]
    return [{'id': name, 'primitive_roles': roles, 'segments': segments,
             'contact': 'continuous', 'construction_hypothesis': use,
             'closed': name.endswith('loop'), 'action': 'fixed-full-edge-baseline',
             'provenance': 'project-authored analytic hypothesis; not a learned or historical stroke',
             'practice': {'scale': 1.0, 'composition': 'single', 'offset': [0, 0]},
             'transfer': {'scale': .8, 'composition': 'two occurrences separated by explicit lift',
                          'offsets': [[0, 0], [1.1, 0]], 'split': 'synthetic-held-out'}}
            for name, roles, segments, use in shapes]


def _fixture_panel(fixtures, output):
    image = Image.new('RGB', (1120, 1190), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=16)
    draw.text((18, 12), 'Synthetic centerline specifications - NOT trained strokes or actual pen output',
              fill='black', font=font)
    draw.text((18, 40), 'One contact gesture can have multiple colored segments. Scale: 64 px / x-height.',
              fill='black', font=font)
    draw.text((300, 70), 'Practice: one gesture', fill='black', font=font)
    draw.text((660, 70), 'Held-out: smaller pair, explicit lift', fill='black', font=font)
    colors = ['#2457a6', '#d46c17', '#208456', '#873db1']
    for index, fixture in enumerate(fixtures):
        top = 110 + index * 132
        draw.text((18, top), fixture['id'], fill='black', font=font)
        draw.text((18, top + 26), f"{len(fixture['segments'])} segment(s), one contact", fill='black', font=font)
        for origin, scale in [(350, 1.0), (690, .8), (810, .8)]:
            baseline = top + (8 if fixture['id'] == 'lower_loop' else 92)
            draw.line((origin - 30, baseline, origin + 95, baseline), fill='#ddd')
            for segment_index, cubic in enumerate(fixture['segments']):
                points = []
                for step in range(65):
                    progress = step / 64
                    weights = [(1 - progress) ** 3, 3 * (1 - progress) ** 2 * progress,
                               3 * (1 - progress) * progress ** 2, progress ** 3]
                    point = [sum(weight * control[axis] for weight, control in zip(weights, cubic))
                             for axis in (0, 1)]
                    points.append((origin + point[0] * 64 * scale, baseline - point[1] * 64 * scale))
                draw.line(points, fill=colors[segment_index], width=3)
                draw.ellipse((points[0][0] - 3, points[0][1] - 3, points[0][0] + 3, points[0][1] + 3),
                             fill=colors[segment_index])
    image.save(output)


def investigate(source, output):
    source, output = Path(source), Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty output directory')
    for name, expected in INPUTS.items():
        if digest(source / name) != expected:
            raise ValueError(f'Frozen input changed: {name}; reviewed derivatives require a new audit scope')
    dataset = json.loads((source / 'manifest.json').read_text())
    verify_review_lineage(dataset)
    samples = [sample for sample in dataset['samples'] if sample['split'] != 'test']
    if len(samples) != 52 or any(sample['admission'] != 'quarantined' for sample in samples):
        raise ValueError('Unexpected frozen non-test scope')
    observations = []
    for sample in samples:
        for kind in ('raw', 'mask', 'cleaned'):
            if digest(source / sample[kind + '_path']) != sample[kind + '_sha256']:
                raise ValueError(f'Artifact hash mismatch: {sample["id"]}/{kind}')
        with Image.open(source / sample['mask_path']) as image:
            exclusions = _exclusions(sample, np.asarray(image))
        if exclusions != sample['exclusions']:
            raise ValueError('Non-test exclusion mismatch')
        observations.append({key: sample[key] for key in
                             ('id', 'source_id', 'line_index', 'bbox', 'source_to_crop', 'split', 'text',
                              'label_status', 'mapping_status', 'raw_path', 'raw_sha256', 'exclusions')})
    benchmark = ROOT / 'shared/training/konrad_hand_recovery/benchmark_v1'
    gate = evaluate_benchmark(dataset['contract'], json.loads((benchmark / 'baseline_manifest.json').read_text()),
                              benchmark, dataset=dataset, dataset_root=None, review=None)
    if gate['status'] == 'pass':
        raise ValueError('A sealed metadata audit cannot confer G0 acceptance')
    fixtures = synthetic_fixtures()
    vocabulary = [{**fixture, 'status': 'unresolved', 'synthetic_status': 'fixture-only',
                   'independent_admitted_support': 0,
                   'possible_observation_ids': [sample['id'] for sample in samples
                                                if fixture['construction_hypothesis'][0] in sample['text']],
                   'observation_link_basis': 'unverified text hypothesis only; not stroke support',
                   'alternatives': ['continuous single pass', 'separate lifted passes',
                                    'different path or nib angle; static pixels do not decide'],
                   'v1_compatibility': 'unproven; primitive roles are not automatically existing v1 IDs'}
                  for fixture in fixtures]
    report = {
        'schema_version': 'gesture-coverage-investigation-v1', 'inputs': INPUTS,
        'code_sha256': {name: digest(ROOT / name) for name in
                       ('scribesim/curriculum/gesture_coverage.py', 'scribesim/evofit/reference_dataset.py',
                        'scribesim/evofit/reference_repair.py', 'scribesim/handvalidate/specimen.py')},
        'audited_non_test': len(observations), 'admitted_non_test': 0,
        'audit_method': 'metadata plus non-test mask/exclusion integrity; no new visual reading or annotation',
        'locked_test_policy': 'no test/source-image decoding or test-image statistics; manifest identity only',
        'full_dataset_integrity': 'not executed: existing validator decodes sealed test/source pixels',
        'scope_decision': {'synthetic': 'proceed-fixtures-only', 'real': 'blocked'},
        'real_starter_characters': [], 'real_fitting_evaluations': 0, 'G0': gate,
        'review': '52 pending entries; no genuine external approvals supplied; no annotations changed',
        'calibration': 'blocked: zero admitted independent non-test repeats',
        'observations': observations, 'vocabulary': vocabulary,
        'exclusion_counts': dict(Counter(reason for sample in observations for reason in sample['exclusions'])),
        'coverage_debt': [
            'No accepted real starter letters or historical gesture assignments.',
            'Right bowls, closed ovals, entry/exit terminals and stem-length variants remain unresolved.',
            'Cross-strokes, hooks, diamonds and built terminals need verified named constructions.',
            'Two 3-segment overturns for m expand to 6 primitives and exceed the 4-per-letter cap.',
            'New primitive geometry cannot be fitted in CURRICULUM-008; scope primitive S1 extensions first.',
            'Stationary dabs, capitals, flourishes and abbreviations excluded from this initial scope.'],
        'follow_up_request': {
            'authorization': 'proposed only; requires separately authorized follow-up',
            'annotation': 'One qualified reading/mapping review of up to 52 non-test entries, one adjudication pass; exact source-bound identity/date and separate trusted attestations.',
            'target': 'One owner target/rubric review bound to the frozen benchmark contract.',
            'calibration': 'Only after genuine support: admitted train/development independent repeats and negative controls.',
            'source_acquisition': 'If review cannot meet unchanged G0 coverage, scope up to two additional rights-cleared folios before download; preserve old test reservations and freeze new source-line splits.'},
        'budget': {'non_test_audit_passes': 1, 'annotations_changed': 0, 'extraction_revisions': 0,
                   'synthetic_panel_renders': 1, 'fitting_evaluations': 0},
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / 'report.json', report)
    write_json(output / 'G0.json', gate)
    write_json(output / 'fixtures.json', fixtures)
    _fixture_panel(fixtures, output / 'synthetic-fixtures.png')
    rows = '\n'.join(f"| {row['id']} | {row['construction_hypothesis']} | unresolved / 0 |"
                     for row in vocabulary)
    (output / 'README.md').write_text(
        '# Gesture coverage investigation\n\n'
        '**Decision: proceed with synthetic fixtures only; real G0 remains blocked.**\n\n'
        'Audited 52 non-test records and mask exclusions; no new visual readings, source acquisition or label changes. '
        'All source/test pixels remain sealed from decoding. Zero admitted real starter characters.\n\n'
        '[Synthetic centerline specifications](synthetic-fixtures.png) are independently authored hypotheses, '
        'not learned strokes, nib renders or actual execution. [Fixtures](fixtures.json) freeze single-gesture '
        'practice and different-scale lifted-pair transfer. Primitive roles still need v1 compatibility investigation.\n\n'
        '| Candidate | Construction hypothesis | Real status / independent support |\n|---|---|---|\n' + rows +
        '\n\n[Workbook/report](report.json) records native coordinates, source IDs, uncertain mappings, competing hypotheses, '
        'budget, coverage debt and a separately authorized review/acquisition request. Possible observation links use '
        'unverified text, not evidence of ductus. No candidate is historical-support accepted.\n\n'
        '[G0](G0.json) is recomputed by the benchmark evaluator with dataset_root=None: known blockers suffice to stop. '
        'Full dataset integrity is explicitly unverified because that validator decodes locked pixels. This is not '
        'a substitute G0 pass or permission to train. No repeat calibration is possible without admitted observations.\n\n'
        'Replay from repository root into a fresh directory:\n\n'
        '```sh\n.venv/bin/python -m scribesim.curriculum.gesture_coverage --output /tmp/td018-coverage-replay\n```\n'
        '\nNo optimizer, controller, primitive checkpoint or production default was changed.\n')
    write_json(output / 'freeze.json', {'report_sha256': object_digest(report),
                                       'artifacts': {file.name: digest(file) for file in sorted(output.iterdir())}})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'reference/konrad_hand_recovery_v3')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = investigate(args.source, args.output)
    print(json.dumps({'audited': report['audited_non_test'], 'decision': report['scope_decision'],
                      'G0': report['G0']['status']}))


if __name__ == '__main__':
    main()
