"""Opt-in bounded synthetic letter assembly; never an S2 or real-hand admission."""

import argparse
import copy
import itertools
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scribesim.curriculum import gesture_targets
from scribesim.evofit import foundation_contract as contract, stroke_gestures, stroke_language, word_recovery
from scribesim.handvalidate import finer_scales as admission
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


foundation = admission.foundation
BASE = contract.BASE / 'letters'
SPEC_PATH = BASE / 'spec-v1.json'
SPEC = json.loads(SPEC_PATH.read_text())
INVENTORY = SPEC['inventory']


def identities():
    paths = [Path(__file__), SPEC_PATH, Path(word_recovery.__file__), ROOT / 'scribesim/glyphs/catalog.py']
    return {**admission.identities(), **{str(path.relative_to(ROOT)): digest(path) for path in paths}}


def load_inputs(*, real=False):
    if real is not False:
        raise ValueError('Real-reference fitting requires live G0, real lower layers and letter allocations; none supplied')
    admitted = admission.require_readiness(admission.BASE / 'run-001',
        expected_report_sha256=SPEC['source_report_sha256'], required_gestures=SPEC['required_gestures'])
    path = admission.BASE / 'run-001/seed-7/first/candidate.json'
    if digest(path) != SPEC['candidate_file_sha256']:
        raise ValueError('Frozen lower-layer file identity mismatch')
    return {'candidate': json.loads(path.read_text()), 'admission': admitted,
            'unresolved_gestures': SPEC['unresolved_gestures'], 'S2_accepted': False, 'real_accepted': False}


def initial_model(source):
    result = copy.deepcopy(source)
    templates = contract.initial_model()['recipes']
    result['recipes'] = {name: templates[name] for name in INVENTORY}
    for recipe in result['recipes'].values():
        for instance in recipe['gestures']:
            instance['offset'][0] += SPEC['letter_origin_x']
    stroke_gestures.validate_gestures(result)
    return result


def with_parameters(source, parameters):
    if set(parameters) != set(INVENTORY):
        raise ValueError('Complete frozen letter inventory required')
    result = initial_model(source)
    for character, values in parameters.items():
        if (not isinstance(values, (list, tuple)) or len(values) != 2 or any(
                type(value) not in (int, float) or not math.isfinite(value) or value not in SPEC['search'][axis]
                for value, axis in zip(values, ('dx', 'dy')))):
            raise ValueError('Only the frozen bounded attachment grid is permitted')
        instance = result['recipes'][character]['gestures'][1]
        instance['offset'] = [round(origin + value, 10) for origin, value in zip(instance['offset'], values)]
    stroke_gestures.validate_gestures(result)
    return result


def require_lineage(model, source):
    try:
        initial = initial_model(source)
        parameters = {name: [round(value - origin, 10) for value, origin in zip(
            model['recipes'][name]['gestures'][1]['offset'], initial['recipes'][name]['gestures'][1]['offset'])]
            for name in INVENTORY}
        if model != with_parameters(source, parameters):
            raise ValueError('Only frozen second-gesture placement may change; no detached geometry or aliases')
        for character in INVENTORY:
            rows = stroke_gestures.compile_gestures(character, model)['strokes']
            points = np.array([point for row in rows for cubic in row['cubics'] for point in cubic])
            if (len(rows) > SPEC['expanded_cap'] or len({row['gesture_occurrence_id'] for row in rows}) != 2
                    or any(points[:, axis].min() < bounds[0] or points[:, axis].max() > bounds[1]
                        for axis, bounds in enumerate([SPEC['constraints']['local_x_bounds'], SPEC['constraints']['local_y_bounds']]))):
                raise ValueError('Audited expansion, contact or proportion bounds exceeded')
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError('Malformed bounded letter recipe') from error


def compile_recipe(text, model, source):
    require_lineage(model, source)
    if not isinstance(text, str) or not text or any(char not in INVENTORY for char in text):
        raise ValueError('Unsupported exact letter inventory; no fallback or text alias')
    return stroke_gestures.compile_gestures(text, model)


def fixtures():
    rows = []
    for split, shift in [('train', [0, 0]), ('development', [.03, .02]), ('repeat', [-.02, .04])]:
        rows.extend({'id': f'{split}-{char}', 'split': split, 'text': char, 'shift': shift} for char in INVENTORY)
    rows.extend({'id': f'unseen-{text}', 'split': 'unseen', 'text': text, 'shift': [.04, -.02]} for text in ('nu', 'um', 'mn'))
    return rows


def placed(model, fixture):
    result = copy.deepcopy(model)
    for recipe in result['recipes'].values():
        for instance in recipe['gestures']:
            instance['offset'] = [value + shift for value, shift in zip(instance['offset'], fixture['shift'])]
    stroke_gestures.validate_gestures(result)
    return result


def target(fixture):
    templates = contract.initial_model()['recipes']
    instances, horizontal = [], 0.0
    for char in fixture['text']:
        recipe = templates[char]
        for index, instance in enumerate(recipe['gestures']):
            offset = SPEC['target_second_offsets'][char] if index == 1 else instance['offset']
            instances.append({'gesture': instance['gesture'], 'scale': 1,
                'offset': [offset[0] + horizontal + fixture['shift'][0] + SPEC['letter_origin_x'], offset[1] + fixture['shift'][1]]})
        horizontal += recipe['advance'] + contract.SPEC['baseline']['letter_gap']
    parts = gesture_targets.parts(foundation.SPEC['targets'], {'instances': instances})
    return foundation.contact_trajectory((part['occurrence'], part['points']) for part in parts)


def nominal(model, fixture):
    return foundation.nominal(placed(model, fixture), fixture['text'])


def paint(path, *, dpi=180):
    return foundation.paint(path, frame=SPEC['frame_mm'], dpi=dpi)


def legacy_path(hand, fixture):
    parts, horizontal = [], 0.0
    templates = contract.initial_model()['recipes']
    for letter, char in enumerate(fixture['text']):
        for index, segment in enumerate(hand['glyphs'][char]['segments']):
            points = foundation.primitives.curve([segment[key] for key in ('p0', 'p1', 'p2', 'p3')])
            parts.append((f'{letter}:{index}', points + [horizontal + fixture['shift'][0] + SPEC['letter_origin_x'], fixture['shift'][1]]))
        horizontal += templates[char]['advance'] + contract.SPEC['baseline']['letter_gap']
    return foundation.contact_trajectory(parts)


def select(score, *, seed, ablation):
    if seed not in SPEC['seeds'] or ablation not in ('shared', 'prior'):
        raise ValueError('Unfrozen seed or fitting arm')
    generator = random.Random(seed)
    selected, records = {}, {}
    for character in INVENTORY:
        proposals = list(itertools.product(SPEC['search']['dx'], SPEC['search']['dy'])) if ablation == 'shared' else [(0, 0)]
        generator.shuffle(proposals)
        def evaluate(values, split):
            loss = score(character, list(values), split)
            if type(loss) not in (int, float) or not math.isfinite(loss) or loss < 0:
                raise ValueError('Finite nonnegative loss required')
            return {'parameters': list(values), 'loss': loss}
        training = [evaluate(values, 'train') for values in proposals]
        shortlist = {tuple(row['parameters']) for row in sorted(training, key=lambda row: (row['loss'], row['parameters']))[:SPEC['search']['shortlist']]}
        shortlist.add((0, 0))
        development = [evaluate(values, 'development') for values in sorted(shortlist)]
        selected[character] = min(development, key=lambda row: (row['loss'], row['parameters']))['parameters']
        records[character] = {'training': training, 'development': development}
    return {'parameters': selected, 'records': records, 'seed': seed, 'ablation': ablation,
            'selection_split': 'development', 'held_out_accessed': False}


def fit(source, seed, ablation, budget, directory):
    lessons = [row for row in fixtures() if row['split'] in ('train', 'development')]
    targets = {row['id']: budget.render(paint, target(row)) for row in lessons}
    journal = []
    def score(character, values, split):
        parameters = dict.fromkeys(INVENTORY, [0, 0])
        parameters[character] = values
        fixture = next(row for row in lessons if row['split'] == split and row['text'] == character)
        try:
            model = with_parameters(source, parameters)
            require_lineage(model, source)
        except ValueError as error:
            journal.append({'character': character, 'parameters': values, 'split': split, 'invalid': str(error)})
            write_json(directory / 'search-journal.json', journal)
            return 1000.0
        loss = foundation.stroke_loss(targets[fixture['id']], budget.render(paint, nominal(model, fixture)))
        journal.append({'character': character, 'parameters': values, 'split': split, 'loss': loss})
        write_json(directory / 'search-journal.json', journal)
        return loss
    selected = select(score, seed=seed, ablation=ablation)
    candidate = with_parameters(source, selected['parameters'])
    require_lineage(candidate, source)
    selected['candidate_sha256'] = object_digest(candidate)
    write_json(directory / 'selection.json', selected)
    write_json(directory / 'candidate.json', candidate)
    return candidate, selected


def reuse_proof(model, source):
    before, bindings = stroke_gestures._lower(model)
    changed = copy.deepcopy(model)
    changed['primitives']['stem']['cubics'][0][1][0] += .01
    after, _ = stroke_gestures._lower(changed)
    affected, identities_seen = [], []
    for char in INVENTORY:
        original = stroke_language._recipe_strokes(before['recipes'][char], before)
        replaced = stroke_language._recipe_strokes(after['recipes'][char], after)
        if original != replaced:
            affected.append(char)
        identities_seen.extend(object_digest(changed['primitives'][row['primitive']]) for row in replaced if row['primitive'] == 'stem')
    try:
        require_lineage(changed, source)
    except ValueError:
        rejected = True
    else:
        rejected = False
    return {'changed_letters': affected, 'all_changed_rows_share_identity': len(set(identities_seen)) == 1,
            'substitution_admitted': not rejected, 'bindings': bindings,
            'scope': 'Negative structural expansion probe only; mutated primitive is never rendered or admitted'}


def measure(model, initial, fixture, budget, directory, *, legacy=None):
    paths = [target(fixture), nominal(initial, fixture), legacy_path(legacy, fixture) if legacy else nominal(model, fixture)]
    pixels = [budget.render(paint, path) for path in paths]
    before, after = [foundation.stroke_loss(pixels[0], image) for image in pixels[1:]]
    row = {'fixture': fixture, 'before': before, 'after': after, 'ratio': after / before if before else None,
           'motion': {}, 'actual_target': {}, 'contained': True, 'physical_evaluated': legacy is None}
    runs = {}
    if legacy is None:
        variant = placed(model, fixture)
        row['compiled'] = stroke_gestures.compile_gestures(fixture['text'], variant)
        for label, step, dt in [('base', .025, .002), ('arc', .0125, .002), ('time', .025, .001)]:
            run = foundation.runtime.execute(variant, fixture['text'], step=step, dt=dt, budget=budget, frame=SPEC['frame_mm'])
            for kind in ('desired', 'actual'):
                foundation.measurement.require_containment(foundation.primitives.learning._trajectory(run, kind), frame=SPEC['frame_mm'])
            contacts = list(dict.fromkeys(stroke['gesture_occurrence_id'] for stroke in row['compiled']['strokes']))
            audit = foundation.audit_trace(variant, fixture['text'], run)
            boundaries = foundation.boundaries(run)
            row['motion'][label] = {'metrics': run['metrics'], 'audit': audit, 'boundaries': boundaries,
                'pass': foundation.runtime.passes(run) and audit['errors'] == 0 and foundation.boundaries_pass(boundaries, contacts)}
            row['actual_target'][label] = foundation.stroke_loss(pixels[0], run['images']['actual'])
            runs[label] = run
        row['comparisons'] = {label: foundation.primitives.motion.compare(runs['base'], runs[label]) for label in ('arc', 'time')}
        row['mechanical_pass'] = all(item['pass'] for item in row['motion'].values()) and all(item['pass'] for item in row['comparisons'].values())
        foundation.primitives.compressed(directory / (fixture['id'] + '-traces.json.gz'),
            {label: {key: value for key, value in run.items() if key != 'images'} for label, run in runs.items()})
    if fixture['split'] in ('repeat', 'unseen'):
        labels = ['target', 'initial', 'nominal']
        if runs:
            paths.extend(foundation.primitives.learning._trajectory(runs['base'], kind) for kind in ('desired', 'actual'))
            labels.extend(['desired', 'actual'])
        for label, path in zip(labels, paths):
            Image.fromarray(budget.render(paint, path, dpi=SPEC['workbook_dpi'])).save(directory / f"{fixture['id']}-{label}.png")
    write_json(directory / (fixture['id'] + '.json'), row)
    return row


def evaluation_pass(rows):
    try:
        return ([row['fixture'] for row in rows] == fixtures() and all(
            row['contained'] is True and row['physical_evaluated'] is True and row['mechanical_pass'] is True
            and set(row['actual_target']) == {'base', 'arc', 'time'}
            and all(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= SPEC['criteria']['absolute_loss_max']
                for value in [row['after'], *row['actual_target'].values()])
            and (row['fixture']['split'] not in ('repeat', 'unseen') or
                type(row['ratio']) in (int, float) and math.isfinite(row['ratio']) and 0 <= row['ratio'] < SPEC['criteria']['heldout_ratio_max'])
            for row in rows))
    except (KeyError, TypeError, ValueError):
        return False


def workbook(directory, model, budget):
    colors = ['#2864b4', '#a33f34', '#248250', '#9654ae', '#bc741a', '#258b9c']
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1050" viewBox="0 0 1500 1050">',
        '<rect width="1500" height="1050" fill="white"/>',
        '<text x="20" y="30" font-family="sans-serif" font-size="22">Synthetic n / u / m: frozen strokes, fitted assembly; NOT historical reading</text>']
    for letter, char in enumerate(INVENTORY):
        rows = stroke_gestures.compile_gestures(char, model)['strokes']
        top = 90 + letter * 310
        svg.append(f'<text x="20" y="{top}" font-family="sans-serif" font-size="22">{char}: {len(rows)} shared primitives; 2 lifted gestures</text>')
        for stage in (1, 2, 3):
            svg.append(f'<g transform="translate({20 + (stage - 1) * 485},{top + 40})">')
            svg.append(f'<text y="0" font-family="sans-serif" font-size="16">{["Gesture 1", "Both gestures", "Numbered constituent strokes"][stage - 1]}</text>')
            for index, row in enumerate(rows):
                if stage == 1 and row['gesture_index'] > 0:
                    continue
                color = colors[index] if stage == 3 else colors[row['gesture_index']]
                for cubic in row['cubics']:
                    points = [[point[0] * 150 + 20, 230 - point[1] * 120] for point in cubic]
                    command = 'M ' + ' '.join(map(str, points[0])) + ' C ' + ' '.join(str(value) for point in points[1:] for value in point)
                    svg.append(f'<path d="{command}" fill="none" stroke="{color}" stroke-width="3"/>')
                    if stage == 3:
                        svg.append(f'<text x="{points[0][0] + 4}" y="{points[0][1] - 5}" font-family="sans-serif" font-size="14" fill="{color}">{index + 1}</text>')
            svg.append('</g>')
    svg.append('</svg>')
    budget.charge(1)
    (directory / 'construction.svg').write_text('\n'.join(svg))
    samples = [row for row in fixtures() if row['split'] in ('repeat', 'unseen')]
    tiles = [[Image.open(directory / f"{row['id']}-{label}.png").convert('RGB') for label in ('initial', 'target', 'nominal', 'desired', 'actual')] for row in samples]
    width, height = tiles[0][0].size
    budget.charge(1)
    sheet = Image.new('RGB', (width * 5, 90 + len(samples) * (height + 45)), 'white')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=20)
    for column, label in enumerate(('Frozen prior', 'Synthetic target', 'Fitted recipe nominal', 'Sampled desired', 'Actual neutral')):
        draw.text((column * width + 10, 20), label, font=font, fill='black')
    for index, (row, images) in enumerate(zip(samples, tiles)):
        top = 90 + index * (height + 45)
        draw.text((10, top), row['id'] + ' | supplied label, not validated reading | native 900 DPI', font=font, fill='black')
        for column, tile in enumerate(images):
            sheet.paste(tile, (column * width, top + 40))
    sheet.save(directory / 'workbook.png')


def worker(directory, seed, ablation, maximum, seconds):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    budget = foundation.JournalBudget(directory, maximum, seconds)
    report = {'seed': seed, 'ablation': ablation, 'status': 'blocked', 'fixtures': [], 'S2_accepted': False, 'real_accepted': False}
    try:
        inputs = load_inputs()
        frozen = json.loads((directory.parents[2] / 'freeze.json').read_text())
        if frozen['spec'] != SPEC or frozen['code_sha256'] != identities():
            raise ValueError('Changed pre-render freeze')
        source, legacy = inputs['candidate'], None
        initial = initial_model(source)
        if ablation == 'legacy':
            legacy = frozen['legacy']
            candidate = initial
            write_json(directory / 'candidate.json', legacy)
        else:
            candidate, selected = fit(source, seed, ablation, budget, directory)
            report['selection'] = selected
            write_json(directory / 'reuse.json', reuse_proof(candidate, source))
        write_json(directory / 'evaluation-freeze.json', {'candidate_sha256': object_digest(legacy or candidate),
            'selection_complete': True, 'held_out_accessed': False})
        for fixture in fixtures():
            report['fixtures'].append(measure(candidate, initial, fixture, budget, directory, legacy=legacy))
            write_json(directory / 'progress.json', report)
        if ablation == 'shared':
            workbook(directory, candidate, budget)
        if frozen['code_sha256'] != identities():
            raise ValueError('Execution source changed during run')
        report['synthetic_learning_pass'] = evaluation_pass(report['fixtures']) if ablation != 'legacy' else False
        report['status'] = 'complete'
        budget.check()
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        report['reason'] = str(error)
    report['renders'] = budget.used
    write_json(directory / 'report.json', report)
    budget.receipt()
    return report


def build(output=None, *, real=False):
    output = Path(output) if output else BASE / 'run-001'
    if output.exists():
        raise ValueError('Use an immutable new experiment; no overwrite or automatic retry')
    inputs = load_inputs(real=real)
    write_json(output / 'freeze.json', {'spec': SPEC, 'code_sha256': identities(), 'inputs': inputs,
        'legacy': word_recovery.seed_hand(INVENTORY), 'fixtures': fixtures(), 'target_pixels_accessed': False,
        'environment': {'python': sys.version, 'numpy': np.__version__, 'pillow': Image.__version__}})
    report = {'stage': SPEC['stage'], 'status': 'blocked', 'seeds': [], 'S2_accepted': False,
        'real_accepted': False, 'context_training_allowed': False, 'promoted': False, 'renders': 0}
    ledger = []
    try:
        for seed in SPEC['seeds']:
            for ablation in SPEC['ablations']:
                started, used = time.monotonic(), 0
                for label, hashseed in [('first', '7'), ('replay', '839')]:
                    remaining = 1800 - (time.monotonic() - started)
                    directory = output / f'seed-{seed}/{ablation}/{label}'
                    try:
                        process = subprocess.run([sys.executable, '-m', 'scribesim.curriculum.letter_recipes',
                            '--worker', str(directory), '--seed', str(seed), '--ablation', ablation,
                            '--maximum', str(5000 - used), '--seconds', str(remaining)], cwd=ROOT,
                            env={**os.environ, 'PYTHONHASHSEED': hashseed}, capture_output=True, text=True, timeout=remaining)
                    finally:
                        receipt = directory / 'execution.json'
                        if receipt.exists():
                            count = json.loads(receipt.read_text())['renders']
                            used += count
                            report['renders'] += count
                            ledger.append({'seed': seed, 'ablation': ablation, 'process': label, 'renders': count,
                                'cumulative_renders': used, 'cumulative_seconds': time.monotonic() - started})
                            write_json(output / 'execution.json', {'ledger': ledger})
                    if process.returncode or not receipt.exists():
                        raise ValueError('Worker failed: ' + process.stdout[-1000:] + process.stderr[-1000:])
                    result = json.loads((directory / 'report.json').read_text())
                    if result['status'] != 'complete':
                        raise ValueError('Worker incomplete: ' + result.get('reason', 'unknown'))
                root = output / f'seed-{seed}/{ablation}'
                matching = foundation.primitives.manifest(root / 'first') == foundation.primitives.manifest(root / 'replay')
                if not matching or used > 5000 or time.monotonic() - started > 1800:
                    raise ValueError('Replay or cumulative budget failure')
                report['seeds'].append({'seed': seed, 'ablation': ablation, 'replay_match': matching,
                    'renders': used, 'synthetic_learning_pass': result['synthetic_learning_pass']})
        shared = [row for row in report['seeds'] if row['ablation'] == 'shared']
        report['status'] = 'pass' if len(shared) == 3 and all(row['synthetic_learning_pass'] for row in shared) else 'fail'
        report['measurement_complete'] = True
        report['next_step'] = 'Review letter shape/attachment residuals and unresolved standalone stem admission before independent S2 evaluation; no context fitting yet'
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        report['reason'] = str(error)
        report['next_step'] = 'Preserve attempt; diagnose before the one separately frozen revision'
    report['artifacts'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
    write_json(output / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--seed', type=int, choices=SPEC['seeds'])
    parser.add_argument('--ablation', choices=SPEC['ablations'])
    parser.add_argument('--maximum', type=int, default=5000)
    parser.add_argument('--seconds', type=float, default=1800)
    parser.add_argument('--real', action='store_true')
    args = parser.parse_args()
    result = worker(args.worker, args.seed, args.ablation, args.maximum, args.seconds) if args.worker else build(real=args.real)
    print(json.dumps({key: value for key, value in result.items() if key in ('status', 'reason', 'renders', 'next_step')}))
    return int(result['status'] == 'blocked')


if __name__ == '__main__':
    raise SystemExit(main())
