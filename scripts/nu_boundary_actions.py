"""Opt-in boundary-local action contract and exact edge validation; no path consumer."""

import argparse
import copy
from dataclasses import dataclass
from fractions import Fraction
import json
import math
from pathlib import Path
import re
import shutil
import signal
import time

from scripts import nu_corner_contact as capability
from scribesim.handvalidate.specimen import ROOT, digest, object_digest


VERSION = 'nu-boundary-actions-v1'
CONTACT_VERSION = 'boundary-contact-decimal-v1'
OUTPUT = capability.BASE/'boundary-action-001'
CAPABILITY_PIN = 'b42bf1a70a0d52d4fde0a19a4fb7a52aab9ec81da342fbb959f59a796da231d6'
FULL = [['0', '0', '1'], ['1', '0', '1']]
PROFILES = {'full': FULL, 'departure': [['0', '0', '1'], ['1', '0', '0.1']],
            'core': [['0', '0', '0.1'], ['1', '0', '0.1']],
            'receiving': [['0', '0', '0.1'], ['1', '0', '1']]}


def exact(value):
    if isinstance(value, Fraction):
        return value
    if type(value) is not str or len(value) > 64 or not re.fullmatch(r'(?:0|1)(?:\.[0-9]+)?', value):
        raise ValueError('Exact decimal string or Fraction required; floats are not edge authority')
    return Fraction(value)


def edge_interval(start, end):
    lower, upper = exact(start), exact(end)
    if not 0 <= lower < upper <= 1 or upper-lower < Fraction(1, 10):
        raise ValueError('Contact interval must lie in [0,1] and span at least exactly 0.1')
    return lower, upper


def validate_track(track):
    if type(track) is not list or not 2 <= len(track) <= 4:
        raise ValueError('Two to four arc-progress knots required')
    result = []
    previous = Fraction(-1)
    for knot in track:
        if type(knot) is not list or len(knot) != 3:
            raise ValueError('Progress/start/end knot required')
        progress = exact(knot[0])
        lower, upper = edge_interval(*knot[1:])
        if not previous < progress <= 1:
            raise ValueError('Strictly increasing progress required')
        previous = progress
        result.append((progress, lower, upper))
    if result[0][0] != 0 or result[-1][0] != 1:
        raise ValueError('Track must cover the entire [0,1] domain')
    return result


def interpolate(track, progress):
    knots = validate_track(track)
    progress = exact(progress)
    if not 0 <= progress <= 1:
        raise ValueError('Progress outside [0,1]')
    for before, after in zip(knots, knots[1:]):
        if before[0] <= progress <= after[0]:
            ratio = (progress-before[0])/(after[0]-before[0])
            interval = tuple(before[axis]+ratio*(after[axis]-before[axis]) for axis in (1, 2))
            return edge_interval(*interval)
    raise ValueError('Missing interpolation segment')


@dataclass(frozen=True)
class BoundaryContact:
    center: tuple
    interval: tuple
    frame: str = 'physical-y-down'
    version: str = CONTACT_VERSION

    def __post_init__(self):
        if (self.version != CONTACT_VERSION or self.frame not in ('physical-y-down', 'physical-y-up')
                or type(self.center) is not tuple or len(self.center) != 2
                or any(type(value) not in (int, float) or not math.isfinite(value) for value in self.center)
                or type(self.interval) is not tuple or len(self.interval) != 2):
            raise ValueError('Explicit fixed-tool boundary contact required')
        object.__setattr__(self, 'interval', edge_interval(*self.interval))

    def corners(self):
        angle = math.radians(40 if self.frame == 'physical-y-down' else -40)
        direction = (math.cos(angle), math.sin(angle))
        normal = (-direction[1], direction[0])
        return [(self.center[0]+float(endpoint-Fraction(1, 2))*.45*direction[0]+side*.01*normal[0],
                 self.center[1]+float(endpoint-Fraction(1, 2))*.45*direction[1]+side*.01*normal[1])
                for endpoint in self.interval for side in (-1, 1)]

    def reflected(self):
        frame = 'physical-y-up' if self.frame == 'physical-y-down' else 'physical-y-down'
        return BoundaryContact((self.center[0], -self.center[1]), self.interval, frame)


def manifest(candidate, text, prior):
    if text not in ('nu', 'mu'):
        raise ValueError('Only exposed nu/mu contracts; no um/num admission')
    compiled = capability.investigation.canonical(candidate, text)
    cases = [case for case in prior['investigation']['cases'] if case['text'] == text
             and abs(case['receiving']['canonical_parameter']-.25) < 1e-12]
    case = max(cases, key=lambda item: item['departure']['height_mm'])
    departure = case['departure']['owner']['occurrence_id']
    receiving = case['receiving']['owner']['occurrence_id']
    departure_parameter = str(case['departure']['canonical_parameter'])
    intervals = {departure: ['0', departure_parameter], receiving: ['0.25', '1']}
    retained = []
    for row in compiled['strokes']:
        owner = {key: value for key, value in row.items() if key != 'cubics'}
        retained.append({'piece_id': 'retained:'+row['occurrence_id'], 'canonical_owner': owner,
                         'canonical_geometry_sha256': object_digest(row['cubics']),
                         'source_interval': intervals.get(row['occurrence_id'], ['0', '1']),
                         'canonical_action': copy.deepcopy(candidate['actions'][row['action_profile']]),
                         'boundary_override': None, 'contact_profile': 'full', 'contact': 'pen-down'})
    removed = {departure: [departure_parameter, '1'], receiving: ['0', '0.25']}
    boundary = [
        {'piece_id': 'T', 'role': 'derived_departure', 'source_owner': departure,
         'removed_interval': removed[departure], 'contributors': [departure], 'contact_profile': 'departure'},
        {'piece_id': 'R', 'role': 'boundary', 'source_owner': None,
         'removed_interval': None, 'contributors': [departure, receiving], 'contact_profile': 'core'},
        {'piece_id': 'S', 'role': 'derived_receiving', 'source_owner': receiving,
         'removed_interval': removed[receiving], 'contributors': [departure, receiving], 'contact_profile': 'receiving'}]
    for slot in boundary:
        slot['contact'] = 'pen-down'
        slot['contact_run_ref'] = 'proposed-boundary-run'
    return {'version': VERSION, 'contact_version': CONTACT_VERSION, 'exposed_fixture': text,
            'candidate_sha256': object_digest(candidate), 'canonical_compilation_sha256': object_digest(compiled),
            'proposal_sha256': capability.PROPOSAL_PIN,
            'selection': {'departure_role': 'final_descending_stem', 'receiving_role': 'first_u_descending_stem',
                          'policy': 'explicit_connection_permitted', 'layout_sha256': object_digest(compiled)},
            'tool': {'width_mm': .45, 'thickness_mm': .02, 'physical_y_down_angle_deg': 40,
                     'pressure': .5, 'speed_cap_mm_s': 12, 'edge_endpoint_rate_per_s': 3},
            'profiles': copy.deepcopy(PROFILES), 'retained': retained, 'boundary_slots': boundary,
            'joins': [{'name': name, 'pieces': [before, after], 'edge_state': edge,
                       'geometric_continuity': 'not_evaluated_no_geometry'}
                      for name, before, after, edge in (
                          ('A', 'retained:'+departure, 'T', ['0', '1']),
                          ('B', 'T', 'R', ['0', '0.1']), ('D', 'R', 'S', ['0', '0.1']),
                          ('C', 'S', 'retained:'+receiving, ['0', '1']))],
            'shared_contact_run': {'id': 'proposed-boundary-run', 'does_not_replace_canonical_owner': True},
            'piece_cap': 13, 'geometry_present': False, 'geometry_approved': False,
            'nominal_execution_approved': False, 'physical_execution_approved': False}


def validate_manifest(document, candidate, prior):
    if type(document) is not dict or document.get('exposed_fixture') not in ('nu', 'mu'):
        raise ValueError('Unsupported boundary contract')
    expected = manifest(candidate, document['exposed_fixture'], prior)
    if object_digest(document) != object_digest(expected):
        raise ValueError('Changed source, ownership, body action, contact scope or execution permission')
    for track in document['profiles'].values():
        validate_track(track)
    if len(document['retained'])+len(document['boundary_slots']) > document['piece_cap']:
        raise ValueError('Boundary piece cap')
    for before, after in zip(('full', 'departure', 'core', 'receiving'), ('departure', 'core', 'receiving', 'full')):
        if interpolate(document['profiles'][before], '1') != interpolate(document['profiles'][after], '0'):
            raise ValueError('Contact-state discontinuity')


def require_geometry_consumer(document):
    raise ValueError('Contract-only artifact: no geometry, raster or controller consumer is admitted')


def snapshot():
    if shutil.disk_usage(capability.BASE).free < 5*1024**3:
        raise ValueError('At least 5 GiB free required')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    def timeout_handler(signum, frame):
        raise TimeoutError('300-second local contract-check ceiling')
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    report = {'version': VERSION, 'status': 'stopped', 'accepted': False,
              'connector_geometries': 0, 'raster_renders': 0, 'controller_executions': 0, 'fitting_evaluations': 0,
              'owner_scope': 'Address boundary-local contract and numeric handling; no geometry activation'}
    try:
        with capability.source.evidence.read_only_guard():
            if digest(capability.OUTPUT/'report.json') != CAPABILITY_PIN:
                raise ValueError('Frozen capability report changed')
            frozen = capability.source.read_json(capability.OUTPUT/'report.json')
            if (digest(Path(capability.__file__)) != frozen['code_sha256'] or
                    digest(ROOT/'tests/test_nu_corner_contact.py') != frozen['tests_sha256']):
                raise ValueError('Frozen capability checker changed')
            prior = capability.verify(capability.source.read_json(capability.BASE/'capability-approval.json'))
            candidate = capability.source.read_json(capability.source.CANDIDATE)
            before = object_digest(candidate)
            documents = {text: manifest(candidate, text, prior) for text in ('nu', 'mu')}
            for document in documents.values():
                validate_manifest(document, candidate, prior)
            if object_digest(candidate) != before:
                raise ValueError('Canonical mutation')
            contacts = {}
            for name, interval in (('negative', ('0', '0.1')), ('positive', ('0.9', '1')), ('full', ('0', '1'))):
                contact = BoundaryContact((0, 0), interval)
                reflected = contact.reflected()
                error = max(math.dist(actual, expected) for actual, expected in zip(
                    sorted(reflected.corners()), sorted((horizontal, -vertical) for horizontal, vertical in contact.corners())))
                contacts[name] = {'accepted': True, 'exact_interval': [str(value) for value in contact.interval],
                                  'reflection_error_mm': error, 'corners_mm_y_down': contact.corners()}
                if error > 1e-12:
                    raise ValueError('Contact reflection mismatch')
            report.update(status='contract_and_numeric_checks_pass_geometry_gated', contacts=contacts,
                          capability_report_sha256=CAPABILITY_PIN, canonical_sha256=before,
                          code_sha256=digest(Path(__file__)), tests_sha256=digest(ROOT/'tests/test_nu_boundary_actions.py'),
                          manifests_sha256={text: object_digest(document) for text, document in documents.items()},
                          retained_piece_counts={text: len(document['retained']) for text, document in documents.items()},
                          whole_track_interval_proof='Affine interpolation of valid endpoint intervals preserves bounds and minimum span by convexity; exact rational interpolation, no epsilon.',
                          legacy_behavior='Unmodified: connected-v1 remains fixed-action only and legacy positive-corner rejection remains preserved.')
            payload = (json.dumps(documents, indent=2, allow_nan=False)+'\n').encode()
            if len(payload) > 10*1024**2-65536:
                raise ValueError('10MiB local output cap')
            with (OUTPUT/'contracts.json').open('xb') as handle:
                handle.write(payload)
            report['contracts_file_sha256'] = digest(OUTPUT/'contracts.json')
    except Exception as error:
        report.update(status='stopped', error=f'{type(error).__name__}: {error}')
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    report['elapsed_seconds'] = time.monotonic()-started
    with (OUTPUT/'report.json').open('x') as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write('\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot'])
    parser.parse_args()
    print(json.dumps(snapshot(), indent=2))
