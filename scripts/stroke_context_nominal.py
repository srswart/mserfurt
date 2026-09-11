"""One approved nominal fixed-edge packet; never simulates motion or ink physics."""

import argparse
import io
import json
import math
from pathlib import Path
import shutil
import signal
import time

from PIL import Image, ImageChops, ImageDraw

from scripts import stroke_context_preview as preview
from scribesim.handvalidate.specimen import ROOT, digest, object_digest, write_json


BASE = preview.BASE
OUTPUT = BASE/'nominal-001'
TEMPLATE = ROOT/'scripts/templates/stroke_context_nominal.html'
APPROVAL = BASE/'nominal-approval-001.json'
APPROVAL_SHA256 = '8ca9757e8946b35b3b0198f93231204d64a27d9352fe2e2a4b7d0334bbef86e3'
PROTOCOL_SHA256 = '66a9984b2584c2278b11aa5e36675ba6d51a658a522fb2c9a5174ee3cea17274'
REPORT_SHA256 = '8e25b685591f3cb9c52f05bcd1220f5f8ddb62038b9c2119078e3c9158ba8329'
PIXELS = 900*3/25.4
SUPER_SIZE = (math.ceil(33*PIXELS), math.ceil(11*PIXELS))
SIZE = (SUPER_SIZE[0]//3, SUPER_SIZE[1]//3)


def chord_error(cubic):
    return max(math.dist(cubic[index], [(1-index/3)*cubic[0][axis]+index/3*cubic[3][axis]
                                      for axis in range(2)]) for index in (1, 2))


def flatten(cubic, depth=0):
    if len(cubic) != 4 or any(len(point) != 2 or not all(math.isfinite(value) for value in point) for point in cubic):
        raise ValueError('Finite cubic required')
    if chord_error(cubic) <= .001:
        return [cubic]
    if depth >= 20:
        raise ValueError('Nominal flattening depth exhausted')
    before, after = preview.context.split_cubic(cubic)
    return flatten(before, depth+1)+flatten(after, depth+1)


def sweep(start, end):
    offset = [.225*math.cos(math.radians(40)), .225*math.sin(math.radians(40))]
    return [[point[axis]+sign*offset[axis] for axis in range(2)]
            for point, sign in ((start, -1), (start, 1), (end, 1), (end, -1))]


def physical(point):
    return [point[0]*3.5, 10-point[1]*3.5]


def screen(point):
    horizontal, vertical = physical(point)
    return [(horizontal+3)*PIXELS*SIZE[0]/SUPER_SIZE[0], (vertical-2)*PIXELS*SIZE[1]/SUPER_SIZE[1]]


def render(document):
    image = Image.new('L', SUPER_SIZE, 255)
    painter = ImageDraw.Draw(image)
    segments = 0
    for row in document['compiled']['strokes']:
        for cubic in row['cubics']:
            for part in flatten([physical(point) for point in cubic]):
                polygon = sweep(part[0], part[3])
                painter.polygon([((point[0]+3)*PIXELS, (point[1]-2)*PIXELS) for point in polygon], fill=0)
                segments += 1
    output = image.resize(SIZE, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    output.save(buffer, format='PNG')
    return buffer.getvalue(), segments


class Budget:
    def __init__(self, directory):
        self.directory = directory
        self.started = time.monotonic()
        self.used = 0

    def check(self, extra=0):
        if time.monotonic()-self.started >= 300:
            raise RuntimeError('Nominal wall-time limit reached')
        if self.used+extra > 100*1024**2-65536:
            raise RuntimeError('Nominal output size limit reached')
        if shutil.disk_usage(self.directory).free < 5*1024**3:
            raise RuntimeError('Nominal free-space guard reached')

    def write(self, name, contents):
        self.check(len(contents))
        with (self.directory/name).open('xb') as stream:
            stream.write(contents)
        self.used += len(contents)


def verify_inputs(checksum):
    if checksum != APPROVAL_SHA256 or digest(APPROVAL) != checksum:
        raise ValueError('Exact external nominal approval pin required')
    if digest(preview.OUTPUT/'protocol.json') != PROTOCOL_SHA256 or digest(preview.OUTPUT/'report.json') != REPORT_SHA256:
        raise ValueError('Changed nominal preparation')
    report = preview.context.audit.read_json(preview.OUTPUT/'report.json')
    if report['code_sha256'] != digest(Path(preview.__file__)) or report['tests_sha256'] != digest(ROOT/'tests/test_stroke_context_preview.py'):
        raise ValueError('Changed frozen preparation source')
    for name, expected in report['files'].items():
        if digest(preview.OUTPUT/name) != expected:
            raise ValueError('Changed prepared documents or protocol')
    prior = preview.context.audit.read_json(preview.context.CONTRACT.parent/'snapshot-001/report.json')
    if (digest(preview.context.CONTRACT.parent/'snapshot-001/report.json') != preview.CONTRACT_REPORT
            or prior['code_sha256'] != digest(Path(preview.context.__file__))
            or prior['tests_sha256'] != digest(ROOT/'tests/test_stroke_context_contract.py')):
        raise ValueError('Changed frozen contextual contract')
    inventory = preview.context.audit.read_json(preview.OUTPUT/'documents.json')
    if {key: object_digest(value) for key, value in inventory.items()} != report['documents']:
        raise ValueError('Changed prepared document identities')
    preview.analyze(inventory)
    return inventory


def annotations(document):
    return {'strokes': [{'owner': row['occurrence_id'], 'letter': row['letter'], 'primitive': row['primitive'],
        'transition': row['transition'], 'contact_run': row['contact_run_id'],
        'cubics': [[screen(point) for point in cubic] for cubic in row['cubics']]} for row in document['compiled']['strokes']],
        'edits': document['edits'], 'boundaries': document['boundaries']}


def inspect_images(directory, rows):
    results = []
    for row in rows:
        path = directory/row['src']
        if digest(path) != row['sha256']:
            raise ValueError('Changed nominal image')
        with Image.open(path) as image:
            image.load()
            if image.size != SIZE or image.mode != 'L':
                raise ValueError('Changed nominal frame or mode')
            bounds = ImageChops.invert(image).getbbox()
            if not bounds or min(bounds[:2]) <= 0 or bounds[2] >= SIZE[0] or bounds[3] >= SIZE[1]:
                raise ValueError('Blank or edge-clipped nominal image')
        results.append({'id': row['id'], 'nonwhite_bbox_pixels': list(bounds)})
    hashes = {row['id']: row['sha256'] for row in rows}
    for text in 'num':
        if len({hashes[text+':'+hypothesis] for hypothesis in preview.HYPOTHESES}) != 1:
            raise ValueError('Isolated null PNGs changed')
    return results


def generate(checksum, destination=OUTPUT):
    if destination.exists():
        raise FileExistsError('Immutable nominal attempt exists; no automatic retries')
    if checksum != APPROVAL_SHA256:
        raise ValueError('Exact nominal approval required')
    destination.mkdir(parents=True, exist_ok=False)
    budget = Budget(destination)
    old_handler = signal.getsignal(signal.SIGALRM)
    def timeout(signum, frame):
        raise RuntimeError('Nominal wall-time limit reached')
    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, 300)
    rows = []
    try:
        budget.check()
        with preview.context.audit.evidence.read_only_guard():
            inventory = verify_inputs(checksum)
            sources = preview.context.audit.verify_sources()
            for identifier, document in inventory.items():
                budget.check()
                contents, segments = render(document)
                name = identifier.replace(':', '-')+'.png'
                budget.write(name, contents)
                rows.append({'id': identifier, 'text': document['text'], 'hypothesis': document['request']['hypothesis'],
                    'src': name, 'sha256': digest(destination/name), 'document_sha256': object_digest(document),
                    'segments': segments, **annotations(document)})
            if len(rows) != 48:
                raise ValueError('Unexpected nominal image inventory')
            checks = inspect_images(destination, rows)
            manifest = {'version': 'stroke-context-nominal-packet-v1', 'approval_sha256': checksum,
                'protocol_sha256': PROTOCOL_SHA256, 'preparation_sha256': REPORT_SHA256,
                'size': list(SIZE), 'rows': rows, 'owner_feedback': [], 'physical_execution_authorized': False}
            encoded = json.dumps(manifest, ensure_ascii=False).replace('<', '\\u003c')
            page = TEMPLATE.read_text().replace('__PACKET_JSON__', encoded)
            budget.write('index.html', page.encode())
            budget.write('manifest.json', (json.dumps(manifest, indent=2)+'\n').encode())
            record = {'status': 'nominal_packet_complete_owner_review_pending', 'approval_sha256': checksum,
                'sources': sources, 'image_checks': checks, 'nominal_raster_renders': 48,
                'extra_raster_renders': 0, 'controller_executions': 0, 'optimization_evaluations': 0,
                'seconds_before_report': time.monotonic()-budget.started, 'bytes_before_report': budget.used,
                'code_sha256': digest(Path(__file__)), 'tests_sha256': digest(ROOT/'tests/test_stroke_context_nominal.py'),
                'template_sha256': digest(TEMPLATE), 'manifest_sha256': digest(destination/'manifest.json'),
                'html_sha256': digest(destination/'index.html'), 'physical_accepted': False,
                'owner_usefulness_review': 'pending', 'S2_accepted': False, 'real_accepted': False}
            budget.write('report.json', (json.dumps(record, indent=2)+'\n').encode())
        return {'status': record['status'], 'report_sha256': digest(destination/'report.json'),
                'seconds': time.monotonic()-budget.started, 'bytes': budget.used, 'images': len(rows)}
    except Exception as error:
        write_json(destination/'failure.json', {'status': 'failed_preserved_no_retry', 'error': str(error),
            'images_finished': len(rows), 'seconds': time.monotonic()-budget.started, 'bytes': budget.used})
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['generate', 'inspect'])
    parser.add_argument('--approval-sha256')
    parser.add_argument('--report-sha256')
    args = parser.parse_args()
    if args.command == 'generate':
        result = generate(args.approval_sha256)
    else:
        if not args.report_sha256 or digest(OUTPUT/'report.json') != args.report_sha256:
            raise ValueError('External nominal report pin required')
        report = preview.context.audit.read_json(OUTPUT/'report.json')
        for name, key in [('manifest.json', 'manifest_sha256'), ('index.html', 'html_sha256')]:
            if digest(OUTPUT/name) != report[key]:
                raise ValueError('Changed nominal packet')
        manifest = preview.context.audit.read_json(OUTPUT/'manifest.json')
        result = {'images_verified': len(inspect_images(OUTPUT, manifest['rows'])), 'raster_renders': 0}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
