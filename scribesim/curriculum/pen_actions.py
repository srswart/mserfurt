"""Isolated action proposals and admission-first bounded fitting."""

import argparse
import copy
import gzip
import json
from pathlib import Path
import random
import time

import numpy as np
from PIL import Image

from scribesim.curriculum.gesture_learning import exercise_model
from scribesim.curriculum.stroke_learning import stroke_loss
from scribesim.evofit.stroke_gestures import validate_gestures
from scribesim.handvalidate.nib_contact import BASE
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json
from scribesim.pathguide.gesture_actions import code_identities, execute_actions


SPEC_PATH = BASE / 'actions/spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())


def prerequisites(*, real=False):
    reasons, identities, reports = [], {}, {}
    if digest(BASE / 'tool_contract/spec-v1.json') != SPEC['tool_sha256']:
        reasons.append('tool_identity_stale')
    for relative, expected in SPEC['upstream'].items():
        path = BASE / relative
        try:
            identities[relative] = digest(path)
            if identities[relative] != expected:
                raise ValueError('Unregistered upstream identity')
            report = json.loads(path.read_text())
            reports[relative] = report
            for name, checksum in report['artifacts'].items():
                artifact = (path.parent / name).resolve()
                if not artifact.is_relative_to(path.parent.resolve()) or digest(artifact) != checksum:
                    raise ValueError('Upstream artifact identity mismatch')
            freeze = json.loads((path.parent / 'freeze.json').read_text())
            if any(digest(ROOT / name) != checksum for name, checksum in freeze['code_sha256'].items()):
                reasons.append('gesture_code_identity_stale' if 'gesture_evaluation' in relative else 'bridge_code_identity_stale')
            if 'gesture_evaluation' in relative:
                if report['status'] != 'pass':
                    reasons.append('gesture_gate_not_passed')
                if report.get('coverage_debt'):
                    reasons.append('required_gesture_coverage_missing')
            elif not report['bridge_checks_pass']:
                reasons.append('bridge_convergence_not_passed')
        except (OSError, ValueError, KeyError, TypeError) as error:
            reasons.append('prerequisite_integrity_failed:' + relative + ':' + str(error))
    try:
        checkpoint = json.loads((BASE / 'gestures/run-002/candidate.json').read_text())
        gesture = reports['gesture_evaluation/run-001/S1-gesture.json']
        if not gesture['subset_results'] or any(row['model_sha256'] != object_digest(checkpoint) for row in gesture['subset_results']):
            reasons.append('gesture_candidate_identity_mismatch')
    except (OSError, ValueError, KeyError, TypeError):
        reasons.append('gesture_candidate_identity_unverified')
    if real:
        reasons.append('live_real_G0_and_real_lower_layers_required')
    return {'status': 'blocked' if reasons else 'pass', 'reasons': sorted(set(reasons)),
            'identities': identities, 'renders': 0, 'real': real}


def foundation_prerequisites(manifest, *, expected_report_sha256, required_gestures, real=False):
    from scribesim.handvalidate.pen_actions import foundation_prerequisites as check_foundation

    return check_foundation(manifest, expected_report_sha256=expected_report_sha256,
                            required_gestures=required_gestures, real=real)


def candidate_models(model, ablation):
    if ablation not in SPEC['ablations']:
        raise ValueError('Unfrozen action ablation')
    validate_gestures(model)
    for profile in model['actions'].values():
        if (any(knot[1] != profile['orientation'][0][1] for knot in profile['orientation'])
                or profile['edge'] != [[0, 0, 1], [1, 0, 1]]):
            raise ValueError('A fixed full-edge baseline is required')
    proposals = [copy.deepcopy(model)]
    if ablation in ('rotation', 'edge'):
        for name, profile in model['actions'].items():
            changes = ([{'orientation': [[0, profile['orientation'][0][1]], [1, profile['orientation'][0][1] + delta]]}
                        for delta in SPEC['rotation_endpoint_deltas_deg']] if ablation == 'rotation' else
                       [{'edge': [[0, 0, 1], [1, fraction if positive else 0, 1 if positive else 1 - fraction]]}
                        for fraction in SPEC['edge_release_fractions'] for positive in (False, True)])
            for change in changes:
                candidate = copy.deepcopy(model)
                candidate['actions'][name].update(change)
                proposals.append(candidate)
    else:
        contract = SPEC['finishing']
        recipe = model['recipes'].get(contract['recipe'])
        if recipe is None or contract['gesture'] not in model['gestures']:
            return proposals
        for offset in contract['offsets']:
            candidate = copy.deepcopy(model)
            instances = candidate['recipes'][contract['recipe']]['gestures']
            instances.append({'gesture': contract['gesture'], 'offset': offset, 'scale': 1,
                              'rotation_deg': 0, 'transition': 'lift', 'overlap_with': list(range(len(instances)))})
            proposals.append(candidate)
    valid = []
    for proposal in proposals:
        try:
            validate_gestures(proposal)
            valid.append(proposal)
        except ValueError:
            continue
    return valid


def select_by_development(rows):
    if not rows or any(not np.isfinite(row['development']) or row['development'] < 0 for row in rows):
        raise ValueError('Finite development evidence required')
    return min(rows, key=lambda row: (row['development'], row['candidate']))


def _fit_lesson(model, samples, ablation, seed):
    started, renders = time.monotonic(), 0
    candidates = candidate_models(model, ablation)
    order = list(range(1, len(candidates)))
    random.Random(seed).shuffle(order)
    ledger, scores = [], []

    def evaluate(candidate, selected):
        nonlocal renders
        losses, results = [], []
        for sample in selected:
            if renders + 2 > 5000 or time.monotonic() - started > 1800:
                raise StopIteration('Frozen action budget exhausted')
            renders += 2
            result = execute_actions(sample['text'], exercise_model(candidate, sample), dpi=SPEC['dpi'], frame=SPEC['frame_mm'])
            if not result['tracking_pass']:
                raise ValueError('Actual tracking failure')
            losses.append(stroke_loss(sample['raw'], result['images']['actual']))
            results.append(result)
        return float(np.mean(losses)), results

    training = [sample for sample in samples if sample['split'] == 'train']
    development = [sample for sample in samples if sample['split'] == 'development']
    heldout = [sample for sample in samples if sample['split'] == 'test']
    try:
        best_train, _ = evaluate(model, training)
        dev, _ = evaluate(model, development)
        scores.append({'candidate': 0, 'development': dev})
        for index in order:
            try:
                train, _ = evaluate(candidates[index], training)
                if train < best_train:
                    best_train = train
                    dev, _ = evaluate(candidates[index], development)
                    scores.append({'candidate': index, 'development': dev})
                ledger.append({'candidate': index, 'train': train, 'status': 'measured'})
            except ValueError as error:
                ledger.append({'candidate': index, 'status': 'rejected', 'reason': str(error)})
        chosen = select_by_development(scores)
        before, baseline = evaluate(model, heldout)
        after, fitted = evaluate(candidates[chosen['candidate']], heldout)
        sensitivity = float(np.mean([stroke_loss(first['images']['actual'], second['images']['actual'])
                                     for first, second in zip(baseline, fitted)]))
        activation = SPEC['activation']
        if chosen['candidate'] == 0:
            status = 'null' if before <= activation['null_actual_loss_max'] else 'unresolved'
        else:
            status = ('supported' if after <= activation['heldout_ratio_max'] * before
                      and sensitivity >= activation['actual_sensitivity_min'] else 'rejected')
        return {'status': status, 'model': candidates[chosen['candidate']], 'selected': chosen, 'ledger': ledger,
                'heldout': {'before': before, 'after': after, 'sensitivity': sensitivity}, 'renders': renders,
                'heldout_proofs': [{'sample': {key: value for key, value in sample.items() if key != 'raw'},
                                    'baseline': first, 'fitted': second} for sample, first, second in zip(heldout, baseline, fitted)]}
    except (StopIteration, ValueError) as error:
        return {'status': 'blocked', 'reason': str(error), 'renders': renders, 'ledger': ledger}


def _load_lessons(path, model):
    path = Path(path)
    document = json.loads(path.read_text())
    if (document.get('scope') != 'project-authored-synthetic' or document.get('model_sha256') != object_digest(model)
            or document.get('spec_sha256') != digest(SPEC_PATH) or set(document.get('lessons', {})) != set(SPEC['ablations'])):
        raise ValueError('Matching frozen synthetic lesson manifest required')
    lessons = {}
    for ablation, lesson in document['lessons'].items():
        samples = lesson['samples']
        if (not lesson.get('named_failure') or not 3 <= len(samples) <= 12
                or len({sample['id'] for sample in samples}) != len(samples)
                or {sample['split'] for sample in samples} != {'train', 'development', 'test'}):
            raise ValueError('Disjoint bounded train/development/held-out lesson required')
        rows = []
        for sample in samples:
            target = (path.parent / sample['target']).resolve()
            if (not target.is_relative_to(path.parent.resolve()) or digest(target) != sample['target_sha256']
                    or not .5 <= sample['scale'] <= 1.5 or len(sample['offset']) != 2
                    or any(not np.isfinite(value) or abs(value) > .5 for value in sample['offset'])):
                raise ValueError('Invalid frozen target/transform')
            rows.append({**sample, 'raw': np.asarray(Image.open(target).convert('RGB'))})
        lessons[ablation] = rows
    return document, lessons


def run_actions(output, *, real=False, lesson_path=None, revision=0):
    if type(revision) is not int or revision not in (0, 1):
        raise ValueError('Only one diagnosed revision allowed')
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty output directory')
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    prerequisite = prerequisites(real=real)
    report = {'status': 'blocked', 'scope': 'real' if real else 'synthetic', 'reasons': prerequisite['reasons'],
              'prerequisite': prerequisite, 'spec_sha256': digest(SPEC_PATH), 'spec': SPEC,
              'code_sha256': {**code_identities(), 'scribesim/curriculum/pen_actions.py': digest(Path(__file__))},
              'renders': 0, 'optimization_evaluations': 0, 'candidates': [], 'revision': revision,
              'S1_action_accepted': False, 'promoted': False, 'target_pixels_opened': False}
    if prerequisite['status'] == 'pass':
        if lesson_path is None:
            report['reasons'].append('frozen_named_failure_lesson_missing')
        else:
            model = json.loads((BASE / 'gestures/run-002/candidate.json').read_text())
            try:
                manifest, lessons = _load_lessons(lesson_path, model)
                report['target_pixels_opened'] = True
                write_json(output / 'lesson-freeze.json', manifest)
                records = []
                for seed in SPEC['seeds']:
                    for ablation in SPEC['ablations']:
                        result = _fit_lesson(model, lessons[ablation], ablation, seed)
                        proofs = result.pop('heldout_proofs', [])
                        traces = []
                        for index, proof in enumerate(proofs):
                            for label in ('baseline', 'fitted'):
                                images = proof[label].pop('images')
                                for kind, image in images.items():
                                    Image.fromarray(image).save(output / f'{seed}-{ablation}-{index}-{label}-{kind}.png')
                            traces.append(proof)
                        trace_path = output / f'{seed}-{ablation}-traces.json.gz'
                        trace_path.write_bytes(gzip.compress(json.dumps(traces, sort_keys=True).encode(), mtime=0))
                        record = {**result, 'seed': seed, 'ablation': ablation, 'traces_sha256': digest(trace_path)}
                        write_json(output / f'{seed}-{ablation}.json', record)
                        records.append(record)
                report.update(status='complete', candidates=records, renders=sum(row['renders'] for row in records),
                              optimization_evaluations=sum(len(row['ledger']) for row in records))
            except (ValueError, OSError, KeyError, TypeError) as error:
                report['reasons'].append(str(error))
    report['artifacts'] = {path.name: digest(path) for path in sorted(output.iterdir())}
    write_json(output / 'report.json', report)
    write_json(output / 'execution.json', {'elapsed_seconds': time.monotonic() - started, 'renders': report['renders']})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--real', action='store_true')
    parser.add_argument('--lesson', type=Path)
    parser.add_argument('--revision', type=int, choices=(0, 1), default=0)
    parser.add_argument('--foundation-manifest', type=Path)
    parser.add_argument('--foundation-sha256')
    parser.add_argument('--required-gesture', action='append')
    args = parser.parse_args()
    if args.foundation_manifest is not None:
        if args.lesson is not None or args.output.exists():
            parser.error('Foundation eligibility cannot run a legacy lesson or overwrite evidence')
        report = foundation_prerequisites(args.foundation_manifest, expected_report_sha256=args.foundation_sha256,
                                          required_gestures=args.required_gesture, real=args.real)
        write_json(args.output / 'foundation-eligibility.json', report)
    else:
        report = run_actions(args.output, real=args.real, lesson_path=args.lesson, revision=args.revision)
    print(json.dumps({key: report[key] for key in ('status', 'reasons', 'renders')}))


if __name__ == '__main__':
    main()
