"""Frozen analytic contact diagnostics, not learned-action acceptance."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageDraw

from scribesim.evo.nib_contact import ContactSample, VERSION
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate import tool_contract as oracle
from scribesim.handvalidate.specimen import ROOT, digest, write_json


BASE = ROOT / 'shared/training/konrad_hand_recovery/stroke_gestures_v2'


def fixture_samples(fixture):
    rows = []
    for run in fixture['runs']:
        if rows:
            rows.append(replace(rows[-1], contact=False, pressure=0))
        rows.extend(ContactSample(*pose['center'], width_mm=.45, pressure=.5, nib_angle_deg=pose['angle'],
                                  edge_start=pose['edge'][0], edge_end=pose['edge'][1]) for pose in run)
    return rows


def build(output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    output.mkdir(parents=True, exist_ok=True)
    budget = oracle.ProbeBudget()
    fixtures = oracle.tool_fixtures()
    panel = Image.new('RGB', (864, 8 * 310), 'white')
    draw = ImageDraw.Draw(panel)
    measurements = []
    for index, fixture in enumerate(fixtures):
        expected = oracle._oracle(fixture, budget)
        samples = fixture_samples(fixture)
        refined = []
        for first, second in zip(samples, samples[1:]):
            refined.append(first)
            if first.contact and second.contact:
                refined.append(replace(first, x_mm=(first.x_mm + second.x_mm) / 2,
                    y_mm=(first.y_mm + second.y_mm) / 2, nib_angle_deg=(first.nib_angle_deg + second.nib_angle_deg) / 2,
                    edge_start=(first.edge_start + second.edge_start) / 2, edge_end=(first.edge_end + second.edge_end) / 2))
        refined.append(samples[-1])
        images = []
        for trajectory in (samples, refined):
            budget.consume()
            images.append(paint_trajectory(trajectory, [0, 3, 0, 3], dpi=oracle.PPMM * 25.4, contact_version=VERSION))
        masks = [image.mean(axis=2) < 180 for image in images]
        error = oracle._disagreement(expected, masks[0])
        convergence = oracle._disagreement(masks[0], masks[1])
        measurements.append({'fixture': fixture['id'], 'oracle_disagreement': error, 'refinement_disagreement': convergence,
                             'pass': error <= .05 and convergence <= .03})
        tiles = [np.repeat(np.where(expected, 0, 255).astype('uint8')[:, :, None], 3, axis=2), *images]
        for column, (label, tile) in enumerate(zip(('independent oracle', 'physical canonical sweep', 'refined sampling'), tiles)):
            draw.text((column * 288 + 4, index * 310 + 4), fixture['id'] + ' | ' + label, fill='black')
            panel.paste(Image.fromarray(tile), (column * 288, index * 310 + 22))
    budget.consume()
    panel.save(output / 'contact-comparison.png')
    report = {'scope': 'analytic synthetic physical geometry only; not learned actions or historical calibration',
              'contact_version': VERSION, 'geometry_checks_pass': all(row['pass'] for row in measurements),
              'S1_action_accepted': False, 'promoted': False, 'measurements': measurements,
              'renders': budget.renders, 'max_renders': 100, 'max_seconds': 900, 'optimization_evaluations': 0,
              'revision': 0, 'criteria_sha256': digest(oracle.SPEC),
              'code_sha256': {name: digest(ROOT / name) for name in ('scribesim/evo/nib_contact.py',
                'scribesim/evo/renderer.py', 'scribesim/handvalidate/bridge.py', 'scribesim/handvalidate/nib_contact.py')},
              'artifacts': {'contact-comparison.png': digest(output / 'contact-comparison.png')},
              'legacy': 'old call path and pixels unchanged; whole-file code-bound older gates are stale and must not authorize new fitting'}
    budget.check_time()
    write_json(output / 'report.json', report)
    write_json(output / 'execution.json', {'elapsed_seconds': time.monotonic() - budget.started, 'renders': budget.renders})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output)['measurements']))


if __name__ == '__main__':
    main()
