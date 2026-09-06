"""Actual action-state diagnostics with frozen failure and convergence bounds."""

import argparse
from dataclasses import asdict
import gzip
import json
from pathlib import Path
import time

from PIL import Image, ImageDraw

from scribesim.evofit.stroke_language import seed_language
from scribesim.evofit.stroke_gestures import migrate_v1
from scribesim.handvalidate.gestures import _endpoint_difference
from scribesim.handvalidate.nib_contact import BASE
from scribesim.handvalidate.specimen import ROOT, digest, write_json
from scribesim.handvalidate.tool_contract import ProbeBudget
from scribesim.pathguide.gesture_actions import action_bundle, code_identities, execute_actions
from scribesim.curriculum.stroke_learning import stroke_loss


SPEC_PATH = BASE / 'action_bridge/spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())


def fixture_models():
    models = {}
    for name in SPEC['profiles']:
        model = migrate_v1(seed_language())
        model['sampling'] = 'gesture-arc-v2'
        profile = model['actions']['fixed']
        if name == 'rotation':
            profile['orientation'] = [[0, 40], [1, 60]]
        elif name == 'negative_edge':
            profile['edge'] = [[0, 0, 1], [1, 0, .5]]
        elif name == 'positive_edge':
            profile['edge'] = [[0, 0, 1], [1, .5, 1]]
        elif name == 'wrap':
            profile['orientation'] = [[0, 179], [1, 181]]
        models[name] = model
    return models


def build(output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    output.mkdir(parents=True, exist_ok=True)
    budget = ProbeBudget()
    models = fixture_models()
    write_json(output / 'freeze.json', {'spec': SPEC, 'spec_sha256': digest(SPEC_PATH), 'models': models,
        'code_sha256': {**code_identities(), **{name: digest(ROOT / name) for name in
            ('scribesim/handvalidate/action_bridge.py', 'scribesim/handvalidate/gestures.py')}}})
    panel = Image.new('RGB', (1200, 5 * 260), 'white')
    draw = ImageDraw.Draw(panel)
    traces, rows = {}, []
    for row_index, (name, model) in enumerate(models.items()):
        runs = {}
        for label, step, timestep, angular_rate, edge_rate in (
                ('baseline', .025, .002, 180, 3), ('dense', .01, .002, 180, 3),
                ('step', .0125, .002, 180, 3), ('time', .025, .001, 180, 3),
                ('forced', .025, .002, 1, .01)):
            budget.consume()
            budget.consume()
            runs[label] = execute_actions(SPEC['text'], model, step_mm=step, dt=timestep, dpi=SPEC['dpi'],
                                          frame=SPEC['frame_mm'], angular_rate=angular_rate, edge_rate=edge_rate)
        write_json(output / (name + '-bundle.json'), {'payload': asdict(action_bundle(SPEC['text'], model)),
            'note': 'diagnostic plan; use the strict payload hash envelope when importing'})
        baseline = runs['baseline']
        comparisons = {}
        for label in ('step', 'time'):
            error = _endpoint_difference(baseline, runs[label])
            loss = stroke_loss(baseline['images']['actual'], runs[label]['images']['actual'])
            comparisons[label] = {'endpoint_error_mm': error, 'image_loss': loss, 'pass': error <= .01 and loss <= .03}
        rows.append({'profile': name, 'tracking_pass': baseline['tracking_pass'], 'metrics': baseline['metrics'],
                     'convergence': comparisons, 'forced_metrics': runs['forced']['metrics'],
                     'forced_tracking_pass': runs['forced']['tracking_pass']})
        traces[name] = {label: {key: value for key, value in result.items() if key != 'images'} for label, result in runs.items()}
        panels = [('Dense desired', runs['dense']['images']['desired']), ('Sampled desired', baseline['images']['desired']),
                  ('Actual bounded', baseline['images']['actual']), ('Forced-lag actual', runs['forced']['images']['actual'])]
        for column, (label, array) in enumerate(panels):
            draw.text((column * 300 + 6, row_index * 260 + 6), name + ' | ' + label, fill='black')
            image = Image.fromarray(array)
            image.thumbnail((294, 228))
            panel.paste(image, (column * 300 + 3, row_index * 260 + 30))
    budget.consume()
    panel.save(output / 'action-comparison.png')
    (output / 'actual-traces.json.gz').write_bytes(gzip.compress(json.dumps(traces, sort_keys=True).encode(), mtime=0))
    report = {'scope': SPEC['scope'], 'rows': rows, 'S1_action_accepted': False, 'promoted': False,
              'forced_lag_detected': all(not row['forced_tracking_pass'] for row in rows
                                         if row['profile'] in ('rotation', 'negative_edge', 'positive_edge')),
              'bridge_checks_pass': all(row['tracking_pass'] and all(check['pass'] for check in row['convergence'].values()) for row in rows),
              'renders': budget.renders, 'max_renders': 100, 'max_seconds': 900, 'optimization_evaluations': 0, 'revision': 0,
              'artifacts': {path.name: digest(path) for path in sorted(output.iterdir())},
              'decision': 'infrastructure diagnostics only; S1-gesture and action fitting remain blocked'}
    budget.check_time()
    write_json(output / 'report.json', report)
    write_json(output / 'execution.json', {'elapsed_seconds': time.monotonic() - budget.started, 'renders': budget.renders})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build(args.output)
    print(json.dumps({key: report[key] for key in ('bridge_checks_pass', 'forced_lag_detected', 'renders')}))


if __name__ == '__main__':
    main()
