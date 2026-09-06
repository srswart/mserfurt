"""Independent early-stop S1-action decision; no failed prerequisite can become GO."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from scribesim.handvalidate.nib_contact import BASE
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


SPEC_PATH = BASE / 'action_evaluation/spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
LEARNING = BASE / 'actions/run-002'


def _verify_artifacts(root, report):
    for name, checksum in report['artifacts'].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path) != checksum:
            raise ValueError('Artifact identity mismatch: ' + name)


def _current_code(identities):
    return all((ROOT / name).resolve().is_relative_to(ROOT.resolve())
               and digest(ROOT / name) == checksum for name, checksum in identities.items())


def evaluate_seed(seed, *, learning_root=LEARNING):
    if seed not in SPEC['seeds']:
        raise ValueError('Unfrozen seed')
    root = Path(learning_root)
    reasons, identities = [], {}
    controls = {}
    try:
        identities['learning_report_sha256'] = digest(root / 'report.json')
        if identities['learning_report_sha256'] != SPEC['learning_report_sha256']:
            raise ValueError('Learning report identity mismatch')
        learning = json.loads((root / 'report.json').read_text())
        if not _current_code(learning['code_sha256']):
            reasons.append('learning_code_identity_stale')
        if learning['spec_sha256'] != digest(BASE / 'actions/spec-v1.json'):
            reasons.append('learning_spec_identity_stale')
        _verify_artifacts(root, learning)
        if learning['spec']['tool_sha256'] != digest(BASE / 'tool_contract/spec-v1.json'):
            reasons.append('tool_identity_stale')
        upstream = {}
        for relative, expected in learning['spec']['upstream'].items():
            path = BASE / relative
            if digest(path) != expected:
                raise ValueError('Upstream identity mismatch: ' + relative)
            identities[relative] = expected
            report = json.loads(path.read_text())
            upstream[relative] = report
            _verify_artifacts(path.parent, report)
            freeze = json.loads((path.parent / 'freeze.json').read_text())
            if not _current_code(freeze['code_sha256']):
                reasons.append('current_code_invalidates:' + relative)
            if 'gesture_evaluation' in relative:
                if report['status'] != 'pass' or report.get('coverage_debt'):
                    reasons.append('matching_covered_S1_gesture_not_passed')
                if any(row['subset_status'] != 'pass' or not all(row['checks'].values()) for row in report['subset_results']):
                    reasons.append('gesture_actual_execution_failed')
            elif not report['bridge_checks_pass'] or any(
                    not row['tracking_pass'] or not all(value['pass'] for value in row['convergence'].values()) for row in report['rows']):
                reasons.append('bridge_actual_convergence_failed')
        model = json.loads((BASE / 'gestures/run-002/candidate.json').read_text())
        identities['model_sha256'] = object_digest(model)
        if any(row['model_sha256'] != identities['model_sha256'] for row in
               upstream['gesture_evaluation/run-001/S1-gesture.json']['subset_results']):
            reasons.append('selected_model_identity_mismatch')
        if learning['status'] != 'complete' or not learning['candidates']:
            reasons.append('no_admitted_fitted_or_justified_null_actions')
        if learning['renders'] != 0 or learning['candidates']:
            reasons.append('new_selected_candidates_require_new_frozen_evaluation')
        control_path = BASE / 'tool_contract/run-001/report.json'
        if digest(control_path) != SPEC['original_control_report_sha256']:
            raise ValueError('Original failed-control identity mismatch')
        controls = json.loads(control_path.read_text())['negative_controls']
    except (OSError, KeyError, TypeError, ValueError) as error:
        reasons.append('integrity_failure:' + str(error))
    if not reasons:
        reasons.append('candidate_metrics_not_evaluated_in_this_early_stop_scope')
    return {'seed': seed, 'status': 'blocked', 'reasons': sorted(set(reasons)), 'identities': identities,
            'renders': 0, 'optimization_evaluations': 0, 'candidate_evaluation': 'not_run_prerequisites_failed',
            'letter_training_allowed': False, 'real_letter_training_allowed': False,
            'original_global_controls': controls,
            'new_negative_controls': {name: 'not_run_prerequisites_failed' for name in SPEC['negative_controls_required_after_admission']},
            'action_outcomes': {name: 'unresolved_no_admitted_candidates' for name in ('rotation', 'edge', 'finishing')},
            'real_requirements': SPEC['real_policy'], 'owner_review': 'not performed', 'promoted': False}


def build(output, *, learning_root=LEARNING):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty output directory')
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    write_json(output / 'freeze.json', {'spec': SPEC, 'spec_sha256': digest(SPEC_PATH),
                                      'code_sha256': {'scribesim/handvalidate/pen_actions.py': digest(Path(__file__))}})
    rows, receipts = [], []
    for seed in SPEC['seeds']:
        seed_started = time.monotonic()
        for label, hash_seed in (('first', '7'), ('replay', '839')):
            subprocess.run([sys.executable, '-m', 'scribesim.handvalidate.pen_actions', 'worker',
                            '--output', str(output / f'{seed}-{label}.json'), '--seed', str(seed),
                            '--learning-root', str(learning_root)], check=True, timeout=850,
                           env={**os.environ, 'PYTHONHASHSEED': hash_seed})
        if (output / f'{seed}-first.json').read_bytes() != (output / f'{seed}-replay.json').read_bytes():
            raise ValueError('Fresh-process admission replay mismatch')
        elapsed = time.monotonic() - seed_started
        row = json.loads((output / f'{seed}-first.json').read_text())
        if elapsed > 1800 or row['renders'] * 2 > 5000:
            raise ValueError('Combined per-seed evaluation budget exhausted')
        rows.append(row)
        receipts.append({'seed': seed, 'elapsed_seconds_including_replay': elapsed, 'renders_including_replay': row['renders'] * 2})
    report = {'stage': 'S1-action', 'status': 'blocked', 'decision': 'STOP / REVISE fixed-tool foundations before fitted actions or letters',
              'scope': SPEC['scope'], 'seeds': rows, 'replay': True, 'renders': 0, 'optimization_evaluations': 0,
              'revision': 0, 'letter_training_allowed': False, 'real_letter_training_allowed': False,
              'owner_review': 'not performed', 'promoted': False,
              'remaining_evaluation': 'Selected-candidate actual tracking/benefit, six negative controls, counters and convergence remain unexecuted; freeze a new evaluation after valid prerequisites.',
              'artifacts': {path.name: digest(path) for path in sorted(output.iterdir())}}
    write_json(output / 'S1-action.json', report)
    write_json(output / 'execution.json', {'elapsed_seconds': time.monotonic() - started, 'seeds': receipts})
    return report


def require_letter_readiness(root):
    root = Path(root)
    report = json.loads((root / 'S1-action.json').read_text())
    _verify_artifacts(root, report)
    freeze = json.loads((root / 'freeze.json').read_text())
    if not _current_code(freeze['code_sha256']) or freeze['spec_sha256'] != digest(SPEC_PATH):
        raise ValueError('Stale readiness identity')
    if (report['stage'] != 'S1-action' or report['status'] != 'pass' or report['letter_training_allowed'] is not True
            or any(evaluate_seed(seed)['status'] != 'pass' for seed in SPEC['seeds'])):
        raise ValueError('Matching accepted action and gesture evidence required before letters')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'worker'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--learning-root', type=Path, default=LEARNING)
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    if args.command == 'worker':
        write_json(args.output, evaluate_seed(args.seed, learning_root=args.learning_root))
    else:
        report = build(args.output, learning_root=args.learning_root)
        print(json.dumps({key: report[key] for key in ('status', 'decision', 'renders')}))


if __name__ == '__main__':
    main()
