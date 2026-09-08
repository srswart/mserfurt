"""Read-only reconstruction of CURRICULUM-005 receipts, not independent S2 admission."""

import argparse
import itertools
import json
import math
from pathlib import Path
import random

from scribesim.curriculum import letter_recipes as experiment
from scribesim.handvalidate.specimen import digest, object_digest


def verify_selection(selected, *, seed, ablation):
    try:
        if (selected['seed'] != seed or selected['ablation'] != ablation
                or selected['selection_split'] != 'development' or selected['held_out_accessed'] is not False
                or set(selected['records']) != set(experiment.INVENTORY)
                or set(selected['parameters']) != set(experiment.INVENTORY)):
            raise ValueError('Changed selection scope or split isolation')
        generator = random.Random(seed)
        for char in experiment.INVENTORY:
            proposals = list(itertools.product(experiment.SPEC['search']['dx'], experiment.SPEC['search']['dy'])) if ablation == 'shared' else [(0, 0)]
            generator.shuffle(proposals)
            training, development = [selected['records'][char][split] for split in ('training', 'development')]
            if ([row['parameters'] for row in training] != [list(values) for values in proposals]
                    or any(type(row['loss']) not in (int, float) or not math.isfinite(row['loss']) or row['loss'] < 0
                        for row in training + development)):
                raise ValueError('Incomplete seeded grid or nonfinite score')
            rank = lambda row: (row['loss'], row['parameters'])
            shortlist = {tuple(row['parameters']) for row in sorted(training, key=rank)[:experiment.SPEC['search']['shortlist']]}
            shortlist.add((0, 0))
            if ([row['parameters'] for row in development] != [list(values) for values in sorted(shortlist)]
                    or selected['parameters'][char] != min(development, key=rank)['parameters']):
                raise ValueError('Changed development shortlist or minimum')
        return True
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('Malformed saved selection') from error


def inspect_run(directory):
    directory = Path(directory).resolve()
    try:
        report = json.loads((directory / 'report.json').read_text())
        frozen = json.loads((directory / 'freeze.json').read_text())
        if (report['stage'] != experiment.SPEC['stage'] or report['measurement_complete'] is not True
                or frozen['spec'] != experiment.SPEC or frozen['code_sha256'] != experiment.identities()
                or frozen['fixtures'] != experiment.fixtures() or frozen['target_pixels_accessed'] is not False
                or any(report[key] is not False for key in ('S2_accepted', 'real_accepted', 'context_training_allowed', 'promoted'))):
            raise ValueError('Incomplete, stale or overstated experiment')
        actual_files = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()} - {'report.json'}
        if actual_files != set(report['artifacts']):
            raise ValueError('Incomplete artifact inventory')
        experiment.foundation.primitives.verify_artifacts(directory, report['artifacts'])
        source = experiment.load_inputs()
        if source != frozen['inputs'] or frozen['legacy'] != experiment.word_recovery.seed_hand(experiment.INVENTORY):
            raise ValueError('Changed input or legacy lineage')
        ledger = json.loads((directory / 'execution.json').read_text())['ledger']
        expected_ledger = [(seed, arm, label) for seed in experiment.SPEC['seeds']
            for arm in experiment.SPEC['ablations'] for label in ('first', 'replay')]
        if [(row['seed'], row['ablation'], row['process']) for row in ledger] != expected_ledger:
            raise ValueError('Incomplete execution ledger')
        summaries, artifacts, used = [], {}, 0
        for seed in experiment.SPEC['seeds']:
            for arm in experiment.SPEC['ablations']:
                root = directory / f'seed-{seed}/{arm}'
                first = experiment.foundation.primitives.manifest(root / 'first')
                if first != experiment.foundation.primitives.manifest(root / 'replay'):
                    raise ValueError('Non-clock replay differs')
                artifacts[f'{seed}/{arm}'] = len(first)
                counts = []
                for label in ('first', 'replay'):
                    worker = root / label
                    record = json.loads((worker / 'report.json').read_text())
                    candidate = json.loads((worker / 'candidate.json').read_text())
                    receipt = json.loads((worker / 'execution.json').read_text())
                    if (record['status'] != 'complete' or record['seed'] != seed or record['ablation'] != arm
                            or record['S2_accepted'] is not False or record['real_accepted'] is not False
                            or receipt['renders'] != record['renders']
                            or [row['fixture'] for row in record['fixtures']] != experiment.fixtures()):
                        raise ValueError('Incomplete worker receipt')
                    counts.append(receipt['renders'])
                    if arm != 'legacy':
                        selected = json.loads((worker / 'selection.json').read_text())
                        verify_selection(selected, seed=seed, ablation=arm)
                        if (selected != record['selection'] or candidate != experiment.with_parameters(source['candidate'], selected['parameters'])
                                or selected['candidate_sha256'] != object_digest(candidate)
                                or json.loads((worker / 'reuse.json').read_text()) != experiment.reuse_proof(candidate, source['candidate'])):
                            raise ValueError('Changed candidate, selection or shared-parameter proof')
                        experiment.require_lineage(candidate, source['candidate'])
                        for row in record['fixtures']:
                            compiled = experiment.stroke_gestures.compile_gestures(row['fixture']['text'], experiment.placed(candidate, row['fixture']))
                            if row['compiled'] != compiled or row['ports'] != experiment.ports(candidate):
                                raise ValueError('Changed compiled occurrence or port identity')
                    elif candidate != frozen['legacy']:
                        raise ValueError('Legacy diagnostic candidate changed')
                    if json.loads((worker / 'evaluation-freeze.json').read_text()) != {
                            'candidate_sha256': object_digest(candidate), 'selection_complete': True, 'held_out_accessed': False}:
                        raise ValueError('Changed pre-heldout checkpoint')
                    if record['synthetic_learning_pass'] is not experiment.evaluation_pass(record['fixtures']):
                        raise ValueError('Worker decision differs from numeric evidence')
                receipts = [row for row in ledger if row['seed'] == seed and row['ablation'] == arm]
                if ([row['renders'] for row in receipts] != counts
                        or [row['cumulative_renders'] for row in receipts] != [counts[0], sum(counts)]
                        or sum(counts) > 5000 or not 0 <= receipts[0]['cumulative_seconds'] <= receipts[1]['cumulative_seconds'] <= 1800):
                    raise ValueError('Combined render/time budget differs')
                used += sum(counts)
                summaries.append({'seed': seed, 'ablation': arm, 'replay_match': True, 'renders': sum(counts),
                                  'synthetic_learning_pass': record['synthetic_learning_pass']})
        status = 'pass' if all(row['synthetic_learning_pass'] for row in summaries if row['ablation'] == 'shared') else 'fail'
        if report['seeds'] != summaries or report['renders'] != used or report['status'] != status:
            raise ValueError('Root decision differs from verified worker evidence')
        return {'report_sha256': digest(directory / 'report.json'), 'artifacts_verified': len(report['artifacts']),
            'nonclock_artifacts_per_worker': artifacts, 'renders': used, 'status': status,
            'S2_accepted': False, 'real_accepted': False, 'context_training_allowed': False,
            'scope': 'Read-only provenance reconstruction, not independent letter appearance/reading or S2 acceptance'}
    except (OSError, KeyError, TypeError, IndexError) as error:
        raise ValueError('Incomplete letter experiment evidence') from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, nargs='?', default=experiment.BASE / 'run-001')
    print(json.dumps(inspect_run(parser.parse_args().directory), indent=2))


if __name__ == '__main__':
    main()
