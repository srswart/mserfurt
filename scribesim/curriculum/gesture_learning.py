"""Bounded construction fitting on frozen learned primitives; broad coverage stays blocked."""

import argparse
import copy
import gzip
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scribesim.curriculum.stroke_learning import stroke_loss
from scribesim.evofit.stroke_gestures import execute_gestures, migrate_v1, render_gestures, validate_gestures
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = ROOT / 'shared/training/konrad_hand_recovery/stroke_gestures_v2'
SPEC_PATH = BASE / 'gestures/spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
LOWER = ROOT / 'shared/training/konrad_hand_recovery/stroke_language_v1/strokes/synthetic'
LOWER_HASHES = {'candidate.json': 'c86db60ebbc2d1ad4fbb82a03afec360ec079873522af165b9dbca2043d5603f',
                'S1.json': '9214d6124fca1002d40c6225457136081f6f4f64cf310e93fa5128e95847247f',
                'freeze.json': 'd96023de1d985c680c746f43c14eac16ff5516924bbfe5f6313b72cae9f5f18b',
                'report.json': 'a0d3c9e24d2a84b6a226d9d387dfc31a460978ef30aa5d924eb3b480286b22ee'}


def verify_lower():
    for name, checksum in LOWER_HASHES.items():
        if digest(LOWER / name) != checksum:
            raise ValueError('Frozen accepted primitive checkpoint identity changed')
    freeze = json.loads((LOWER / 'freeze.json').read_text())
    report = json.loads((LOWER / 'report.json').read_text())
    for name, checksum in freeze['code_sha256'].items():
        if digest(ROOT / name) != checksum:
            raise ValueError('Primitive acceptance code identity changed')
    for name, checksum in report['artifacts'].items():
        path = (LOWER / name).resolve()
        if not path.is_relative_to(LOWER.resolve()) or digest(path) != checksum:
            raise ValueError('Primitive acceptance evidence changed')
    if json.loads((LOWER / 'S1.json').read_text())['status'] != 'pass':
        raise ValueError('Accepted synthetic primitive S1 required')
    return json.loads((LOWER / 'candidate.json').read_text())


def exercise_model(model, sample):
    changed = copy.deepcopy(model)
    changed['x_height_mm'] *= sample['scale']
    for recipe in changed['recipes'].values():
        for instance in recipe['gestures']:
            instance['offset'] = [value + delta for value, delta in zip(instance['offset'], sample['offset'])]
    return changed


def render_exercise(model, sample, *, step_mm=.05):
    return render_gestures(sample['text'], exercise_model(model, sample), dpi=SPEC['dpi'],
                           frame=SPEC['frame_mm'], step_mm=step_mm)


def experiment():
    initial = migrate_v1(verify_lower())
    initial['sampling'] = 'gesture-arc-v2'
    target = copy.deepcopy(initial)
    initial['gestures']['gesture-0']['strokes'][1]['primitive'] = 'rise'
    target['gestures']['gesture-0']['strokes'][1].update(scale=1.2, rotation_deg=12)
    validate_gestures(initial)
    validate_gestures(target)
    samples = []
    for identifier, split, text, scale, offset in (
            ('single', 'train', 'i', 1, [0, 0]), ('small', 'train', 'i', .85, [.1, .1]),
            ('development', 'development', 'i', 1.1, [0, 0]),
            ('unseen-scale', 'test', 'i', .7, [.25, 0]), ('unseen-pair', 'test', 'u', 1, [0, 0])):
        sample = {'id': identifier, 'split': split, 'text': text, 'scale': scale, 'offset': offset}
        samples.append({**sample, 'raw': render_exercise(target, sample)})
    return initial, target, samples


class Budget:
    def __init__(self, maximum, seconds):
        if (type(maximum) is not int or not 1 <= maximum <= 5000
                or not isinstance(seconds, (int, float)) or not np.isfinite(seconds) or not 0 < seconds <= 1800):
            raise ValueError('Invalid render/time budget')
        self.maximum, self.seconds = maximum, seconds
        self.used, self.started = 0, time.monotonic()

    def render(self, model, sample):
        if self.used >= self.maximum or time.monotonic() - self.started >= self.seconds:
            raise StopIteration
        self.used += 1
        return render_exercise(model, sample)


def fit_gestures(initial, samples, *, ablation, seed, max_evaluations=5000, seconds=1800):
    if ablation not in SPEC['ablations'] or seed not in SPEC['seeds']:
        raise ValueError('Unfrozen ablation/seed')
    if (not samples or len({sample['id'] for sample in samples}) != len(samples)
            or any(sample['split'] not in {'train', 'development', 'test'} for sample in samples)):
        raise ValueError('Invalid exercise splits/identities')
    validate_gestures(initial)
    training = [sample for sample in samples if sample['split'] == 'train']
    development = [sample for sample in samples if sample['split'] == 'development']
    if not training or not development:
        raise ValueError('Disjoint training and development are required')
    budget = Budget(max_evaluations, seconds)
    best = copy.deepcopy(initial)
    ledger, metrics, before, after = [], {}, {}, {}

    def score(model, rows):
        return float(np.mean([stroke_loss(sample['raw'], budget.render(model, sample)) for sample in rows]))

    status = 'complete'
    try:
        train_best, dev_best = score(best, training), score(best, development)
        if ablation != 'fixed':
            alternatives = SPEC['freedoms']['primitive_choices'] if ablation == 'composition' else ['rise']
            proposals = [(primitive, scale, rotation) for primitive in alternatives
                         for scale in SPEC['freedoms']['scales'] for rotation in SPEC['freedoms']['rotations_deg']]
            random.Random(seed).shuffle(proposals)
            for primitive, scale, rotation in proposals:
                candidate = copy.deepcopy(initial)
                candidate['gestures']['gesture-0']['strokes'][1].update(primitive=primitive, scale=scale, rotation_deg=rotation)
                try:
                    validate_gestures(candidate)
                except ValueError:
                    continue
                loss = score(candidate, training)
                if loss < train_best:
                    train_best = loss
                    dev_loss = score(candidate, development)
                    ledger.append({'primitive': primitive, 'scale': scale, 'rotation_deg': rotation,
                                   'train_loss': loss, 'development_loss': dev_loss})
                    if dev_loss < dev_best:
                        best, dev_best = candidate, dev_loss
        for sample in samples:
            before[sample['id']] = score(initial, [sample])
            after[sample['id']] = score(best, [sample])
        for split in ('train', 'development', 'test'):
            identifiers = [sample['id'] for sample in samples if sample['split'] == split]
            if identifiers:
                metrics[split] = {'before': float(np.mean([before[identifier] for identifier in identifiers])),
                                  'after': float(np.mean([after[identifier] for identifier in identifiers]))}
    except StopIteration:
        status = 'blocked'
    return {'status': status, 'ablation': ablation, 'seed': seed, 'renders': budget.used,
            'selection_split': 'development', 'model': best, 'model_sha256': object_digest(best),
            'metrics': metrics, 'ledger': ledger, 'promoted': False,
            'coverage': 'stem-terminal only; broader family coverage blocked'}


def code_identities():
    names = ('scribesim/evofit/stroke_gestures.py', 'scribesim/curriculum/gesture_learning.py',
             'scribesim/curriculum/stroke_learning.py', 'scribesim/evofit/stroke_language.py',
             'scribesim/handflow/controller.py', 'scribesim/handflow/planning.py', 'scribesim/handflow/model.py',
             'scribesim/handflow/controls.py', 'scribesim/handvalidate/bridge.py', 'scribesim/evo/renderer.py',
             'scribesim/pathguide/repertoire.py', 'scribesim/pathguide/model.py', 'scribesim/handvalidate/model.py')
    return {name: digest(ROOT / name) for name in names}


def _practice(output, initial, target, chosen, samples):
    selected = [samples[0], samples[-2], samples[-1]]
    panel = Image.new('RGB', (1320, 950), 'white')
    draw = ImageDraw.Draw(panel)
    font = ImageFont.load_default(size=17)
    draw.text((15, 12), 'Shared stem-terminal CONSTRUCTION learning; primitives frozen; NOT underturn or historical learning', fill='black', font=font)
    labels = ['Initial: stem + rise', 'Synthetic target', 'Fitted nominal (.01mm)', 'Sampled desired', 'Actual neutral']
    for index, label in enumerate(labels):
        draw.text((10 + index * 264, 48), label, fill='black', font=font)
    traces = {}
    for index, sample in enumerate(selected):
        result = execute_gestures(sample['text'], exercise_model(chosen, sample), dpi=SPEC['dpi'], frame=SPEC['frame_mm'])
        images = [render_exercise(initial, sample), sample['raw'], render_exercise(chosen, sample, step_mm=.01),
                  result['images']['desired'], result['images']['actual']]
        draw.text((15, 83 + index * 280), sample['id'] + ' - supplied text ' + sample['text'], fill='black', font=font)
        for column, image in enumerate(images):
            tile = Image.fromarray(image).resize((248, 248), Image.Resampling.NEAREST)
            panel.paste(tile, (8 + column * 264, 112 + index * 280))
        traces[sample['id']] = {key: value for key, value in result.items() if key != 'images'}
    panel.save(output / 'practice-sheet.png')
    (output / 'actual-traces.json.gz').write_bytes(gzip.compress(json.dumps(traces, sort_keys=True).encode(), mtime=0))
    return {identifier: record['metrics'] for identifier, record in traces.items()}


def run_learning(output, *, real=False, revision=0):
    if type(revision) is not int or revision not in (0, 1):
        raise ValueError('Only one diagnosed experiment revision is allowed')
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty output directory')
    output.mkdir(parents=True, exist_ok=True)
    if real:
        report = {'status': 'blocked', 'scope': 'real-reference', 'renders': 0, 'promoted': False,
                  'reasons': ['live reviewed G0 and real lower-layer gesture/primitive evidence unavailable',
                              'real native gesture assignments and supported starter inventory missing'],
                  'G0': 'not promoted; no source pixels opened or old blocked summary used as a pass'}
        write_json(output / 'report.json', report)
        return report
    started = time.monotonic()
    initial, target, samples = experiment()
    for sample in samples:
        Image.fromarray(sample['raw']).save(output / (sample['id'] + '-target.png'))
    freeze = {'spec_sha256': digest(SPEC_PATH), 'spec': SPEC, 'lower_checkpoint': LOWER_HASHES,
              'coverage_sha256': digest(BASE / 'coverage/run-001/report.json'), 'code_sha256': code_identities(),
              'environment': {'python': sys.version, 'numpy': np.__version__, 'pillow': Image.__version__},
              'initial': initial, 'target': target,
              'samples': [{key: value for key, value in sample.items() if key != 'raw'} for sample in samples],
              'targets': {sample['id']: digest(output / (sample['id'] + '-target.png')) for sample in samples}}
    write_json(output / 'freeze.json', freeze)
    records, selected = [], []
    for seed in SPEC['seeds']:
        for ablation in SPEC['ablations']:
            for label, hash_seed in (('first', '7'), ('replay', '839')):
                subprocess.run([sys.executable, '-m', 'scribesim.curriculum.gesture_learning', 'worker',
                                '--output', str(output / f'{seed}-{ablation}-{label}.json'),
                                '--seed', str(seed), '--ablation', ablation],
                               check=True, env={**os.environ, 'PYTHONHASHSEED': hash_seed})
            first = output / f'{seed}-{ablation}-first.json'
            if first.read_bytes() != (output / f'{seed}-{ablation}-replay.json').read_bytes():
                raise ValueError('Fresh-process learning replay differs')
            records.append(json.loads(first.read_text()))
        eligible = [record for record in records if record['seed'] == seed and record['status'] == 'complete']
        if not eligible:
            raise ValueError('No complete development-selected candidate')
        selected.append(min(eligible, key=lambda record: (record['metrics']['development']['after'], record['ablation'])))
    chosen = min(selected, key=lambda record: (record['metrics']['development']['after'], record['seed']))
    write_json(output / 'candidate.json', chosen['model'])
    actual = _practice(output, initial, target, chosen['model'], samples)
    presentation_renders = 5 + 3 * 4 + 1
    fixed_first = next(record for record in records if record['seed'] == 7 and record['ablation'] == 'fixed')
    if fixed_first['renders'] + 5 + presentation_renders > 5000 or time.monotonic() - started > 1800:
        raise ValueError('Charged presentation/setup budget exceeded')
    report = {'status': 'complete', 'scope': SPEC['scope'], 'freeze_sha256': object_digest(freeze),
              'selected_seed': chosen['seed'], 'selection_split': 'development',
              'selected': [{'seed': record['seed'], 'ablation': record['ablation'], 'model_sha256': record['model_sha256']}
                           for record in selected],
              'rows': [{key: record[key] for key in ('seed', 'ablation', 'renders', 'status', 'metrics')} for record in records],
              'actual': actual, 'replay': True, 'promoted': False, 'broad_S1_gesture': 'blocked-coverage',
              'real_fitting_evaluations': 0,
              'budget': {'worker_target_renders_per_attempt': 5, 'main_setup_and_presentation_renders': presentation_renders,
                         'main_charge': 'seed 7 fixed ablation; all worker counts plus five setup renders per attempt',
                         'first_attempt_renders': sum(record['renders'] + 5 for record in records) + presentation_renders,
                         'verification_replay_renders': sum(record['renders'] + 5 for record in records),
                         'max_per_ablation_seed': 5000, 'max_seconds_per_ablation_seed': 1800, 'revision': revision},
              'coverage_debt': ['No new primitive geometry fitted; only existing stem plus rise/exit choices.',
                                'Underturn, overturn, compound return, lower-loop and directional bowl coverage unresolved.',
                                'Scope a primitive extension and revalidate S1 before broad gesture acceptance.']}
    report['artifacts'] = {file.name: digest(file) for file in sorted(output.iterdir()) if file.name != 'freeze.json'}
    write_json(output / 'report.json', report)
    write_json(output / 'execution.json', {'elapsed_seconds': time.monotonic() - started})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'worker'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--ablation', default='composition')
    parser.add_argument('--real', action='store_true')
    parser.add_argument('--revision', type=int, choices=(0, 1), default=0)
    args = parser.parse_args()
    if args.command == 'worker':
        initial, _, samples = experiment()
        result = fit_gestures(initial, samples, ablation=args.ablation, seed=args.seed, max_evaluations=4995)
        write_json(args.output, result)
    else:
        result = run_learning(args.output, real=args.real, revision=args.revision)
        print(json.dumps({key: result[key] for key in ('status', 'scope')}))


if __name__ == '__main__':
    main()
