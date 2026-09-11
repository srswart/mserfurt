"""Render the single admitted nm geometry as ten nominal comparisons only."""

import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import signal
import time

from PIL import Image, ImageChops

from scripts import stroke_nm_envelope as evaluation
from scripts import stroke_context_nominal as renderer


ROOT = evaluation.ROOT
BASE = evaluation.BASE
OUTPUT = BASE/'nominal-001'
TEMPLATE = ROOT/'scripts/templates/stroke_nm_review.html'
REPORT_PIN = 'd997defea86e87537e3f9d8b7aafc288c8eaffd53fa33f8d56cbb85376d8fabf'
RENDERER_PIN = '737075c2239d29b844555e91c8bc4c0ba6d9b61c77923c6a43835d8dddd4abdf'
TEXTS = ('n', 'm', 'nm', 'nn', 'mm')
MODES = ('B0', 'B3')


def approval_record():
    return {'owner_quote': "Okay let's generate the conditional nominal comparison for your visual review.",
            'version': 'nm-nominal-comparison-v1', 'evaluation_report_sha256': REPORT_PIN,
            'candidate_sha256': evaluation.SAVED_PIN, 'revision_sha256': evaluation.REVISION_PIN,
            'renderer_sha256': RENDERER_PIN, 'texts': list(TEXTS), 'modes': list(MODES),
            'png_count': 10, 'review_pages': 1, 'seconds': 300, 'max_combined_bytes': 100*1024**2,
            'minimum_free_bytes': 5*1024**3, 'retries': 0, 'new_geometry': False,
            'physical_runs': 0, 'fitting': False}


def verify(approval):
    if approval != approval_record():
        raise ValueError('Exact nominal approval required')
    if evaluation.original.digest(evaluation.OUTPUT/'report.json') != REPORT_PIN:
        raise ValueError('Changed passing report')
    report = evaluation.original.attachment.source.read_json(evaluation.OUTPUT/'report.json')
    if report['status'] != 'geometry_pass' or any(check['status'] != 'pass' for check in report['checks'].values()):
        raise ValueError('Every geometry/finite-nib gate must pass')
    for filename, expected in ((Path(evaluation.__file__), report['checker_sha256']),
                               (ROOT/'tests/test_stroke_nm_envelope.py', report['tests_sha256']),
                               (BASE/'envelope-approval.json', report['approval_sha256']),
                               (Path(renderer.__file__), RENDERER_PIN)):
        if evaluation.original.digest(filename) != expected:
            raise ValueError(f'Changed evaluation or renderer identity: {filename}')
    evaluation.verify(evaluation.original.attachment.source.read_json(BASE/'envelope-approval.json'))


def document(text, mode, saved, canonical):
    if text not in TEXTS or mode not in MODES:
        raise ValueError('Outside approved text/mode inventory')
    if text != 'nm' or mode == 'B0':
        return {'compiled': evaluation.original.attachment.canonical(canonical, text)}
    strokes = [copy.deepcopy(piece['stroke']) for piece in saved['pieces'][:10]]
    for piece in saved['pieces'][-2:]:
        strokes.append({'cubics': [[[value/3.5 for value in control] for control in cubic]
                                   for cubic in piece['cubics_mm']],
                        'nominal_owner': piece['owner'], 'contributors': piece['contributors'],
                        'contact': piece['contact'], 'kind': piece['kind']})
    return {'compiled': {'strokes': strokes}, 'saved_candidate_sha256': evaluation.SAVED_PIN}


def inspect_png(payload):
    with Image.open(io.BytesIO(payload)) as image:
        image.load()
        if image.size != (1169, 390) or image.mode != 'L':
            raise ValueError('Incorrect full comparison frame')
        bounds = ImageChops.invert(image).getbbox()
        if not bounds or min(bounds[:2]) <= 0 or bounds[2] >= image.width or bounds[3] >= image.height:
            raise ValueError('Blank or clipped comparison')
        return {'pixel_sha256': hashlib.sha256(image.tobytes()).hexdigest(), 'ink_bbox_pixels': list(bounds)}


def run():
    if shutil.disk_usage(BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    report = {'status': 'stopped', 'accepted': False, 'physical_runs': 0, 'fitting_evaluations': 0,
              'new_geometries': 0, 'images': [], 'frame_mm': [-3, 30, 2, 13], 'dpi': 900,
              'pixel_size': [1169, 390], 'label': 'NOMINAL CONSTRUCTION — NOT ACTUAL INK'}
    def timeout_handler(signum, frame):
        raise TimeoutError('300-second nominal budget exhausted')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    def write(name, payload):
        used = sum(filename.stat().st_size for filename in BASE.rglob('*') if filename.is_file())
        if used+len(payload) > 100*1024**2-65536 or shutil.disk_usage(BASE).free < 5*1024**3:
            raise ValueError('Combined output/free-space guard')
        with (OUTPUT/name).open('xb') as handle:
            handle.write(payload)
    try:
        with evaluation.original.attachment.source.evidence.read_only_guard():
            approval = evaluation.original.attachment.source.read_json(BASE/'nominal-approval.json')
            verify(approval)
            report.update(approval=approval, approval_sha256=evaluation.original.digest(BASE/'nominal-approval.json'),
                          code_sha256=evaluation.original.digest(Path(__file__)),
                          tests_sha256=evaluation.original.digest(ROOT/'tests/test_stroke_nm_nominal.py'),
                          template_sha256=evaluation.original.digest(TEMPLATE))
            source = evaluation.original.attachment.source
            saved = source.read_json(BASE/'attempt-001/candidate.json')
            canonical = source.read_json(source.CANDIDATE)
            payloads = {}
            for text in TEXTS:
                for mode in MODES:
                    compiled = document(text, mode, saved, canonical)
                    payload, segments = renderer.render(compiled)
                    filename = f'{text}-{mode}.png'
                    write(filename, payload)
                    row = {'text': text, 'mode': mode, 'src': filename, 'segments': segments,
                           'sha256': hashlib.sha256(payload).hexdigest(), **inspect_png(payload)}
                    report['images'].append(row)
                    payloads[text, mode] = payload
            for text in TEXTS:
                equal = payloads[text, 'B0'] == payloads[text, 'B3']
                if equal != (text != 'nm'):
                    raise ValueError('Changed control or indistinguishable nm')
            with Image.open(io.BytesIO(payloads['nm', 'B0'])) as before, Image.open(io.BytesIO(payloads['nm', 'B3'])) as after:
                difference = ImageChops.difference(before, after)
                report['nm_difference_bbox_pixels'] = list(difference.getbbox())
                report['nm_changed_pixels'] = sum(value != 0 for value in difference.getdata())
            page = TEMPLATE.read_text().replace('__MANIFEST__', json.dumps(report['images']))
            write('index.html', page.encode())
            report.update(status='nominal_packet_pass_owner_review_pending', raster_renders=10,
                          controls_pixel_identical=True, page_sha256=evaluation.original.digest(OUTPUT/'index.html'))
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report['elapsed_seconds'] = time.monotonic()-started
        evaluation.original.save(OUTPUT, 'report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['generate'])
    parser.parse_args()
    print(json.dumps(run(), indent=2))
