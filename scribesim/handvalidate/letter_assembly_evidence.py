"""Read-only archived level-assembly proofs with saved measurement-pixel hydration."""

import argparse
import gzip
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

from scribesim.handvalidate import letter_assembly as validation
from scribesim.handvalidate.letter_assembly import probe, compile_gestures, levels, target, actual_levels, refinements, image_losses, control_proofs
from scribesim.handvalidate.specimen import digest


foundation = validation.foundation
physical = validation.physical


def verify_record(source, record, directory):
    if json.loads((directory / 'candidate.json').read_text()) != source['candidate']:
        raise ValueError('Changed frozen validation candidate')
    for row in record['fixtures']:
        fixture = row['fixture']
        model = probe(source['candidate'], fixture)
        if (row != json.loads((directory / (fixture['id']+'.json')).read_text())
                or row['compiled'] != compile_gestures(fixture['text'], model) or row['levels'] != levels(model, fixture)
                or row['regions'] != target(fixture)[1]):
            raise ValueError('Changed source, level or target-region proof')
        runs = json.loads(gzip.decompress((directory / f"{fixture['id']}-traces.json.gz").read_bytes()))
        if set(runs) != set(refinements(fixture)):
            raise ValueError('Missing refinement trace')
        for label, run in runs.items():
            variant = foundation.primitives.subdivide(model) if label == 'subdivision' and fixture['text'] != 'i' else model
            if (row['motion'][label]['audit'] != foundation.audit_trace(variant, fixture['text'], run, subdivision=label == 'subdivision' and fixture['text'] == 'i')
                    or row['motion'][label]['metrics'] != run['metrics'] or row['motion'][label]['boundaries'] != foundation.boundaries(run)
                    or row['actual_levels_mm'][label] != actual_levels(run, fixture) or row['tool'][label] != physical.tool_proof(run)):
                raise ValueError('Changed actual physical proof')
        images = {label: np.array(Image.open(directory / f"{fixture['id']}-{label}-metric.png")) for label in ['nominal', *refinements(fixture)]}
        target_pixels = np.array(Image.open(directory / f"{fixture['id']}-target-metric.png"))
        if row['losses'] != image_losses(target_pixels, images, row['regions']):
            raise ValueError('Numeric image proof differs from saved measurement pixels')
        if fixture['kind'] == 'letter':
            before = float(foundation.stroke_loss(target_pixels, np.array(Image.open(directory / f"{fixture['id']}-prior-metric.png"))))
            if row['benefit'] != {'before': before, 'ratio': row['losses']['global']['nominal']/before if before > 0 else None}:
                raise ValueError('Changed benefit measurement')
        for label, run in runs.items():
            run['images'] = {'actual': images[label]}
        if row['comparisons'] != {label: foundation.primitives.motion.compare(runs['base'], run) for label, run in runs.items() if label != 'base'}:
            raise ValueError('Changed convergence proof')
    expected = control_proofs(source['candidate'], fixture, runs['base'])
    loss = float(foundation.stroke_loss(target_pixels, np.array(Image.open(directory / 'visible-shift-metric.png'))))
    expected['visible-shift'] = {'detected': math.isfinite(loss) and loss > .05, 'loss': loss, 'gate': 'rendered-image'}
    if record['controls'] != expected or expected != json.loads((directory / 'controls.json').read_text()):
        raise ValueError('Changed independent control proof')


def inspect_run(directory, *, expected_report_sha256):
    adapter = SimpleNamespace(SPEC=validation.SPEC, identities=validation.identities,
        load_inputs=validation.load_inputs, verify_record=verify_record, passed=validation.passed)
    result = validation.protocol.inspect(adapter, directory, expected_report_sha256)
    return {**result, 'reader_sha256': digest(Path(__file__)),
            'mechanical_validation_pass': result['status'] == 'pass',
            'appearance_review': 'pending', 'context_training_allowed': False,
            'scope': validation.SPEC['scope'],
            'archive_note': 'Convergence reads original saved metric pixels; compact traces omit images. No rerendering, changed decisions or source edits.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path, default=validation.BASE / 'run-001')
    parser.add_argument('--report-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_run(args.directory, expected_report_sha256=args.report_sha256), indent=2))


if __name__ == '__main__':
    main()
