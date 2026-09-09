import copy
import gzip
import json
import math

import numpy as np
from PIL import Image
import pytest

from scribesim.evofit import stroke_gestures as gestures
from scribesim.handflow.curve_tangents import retime_curve_tangents
from scribesim.handvalidate import upright_letters as evaluation, upright_measurement as measurement
from scribesim.handvalidate.specimen import digest
from scribesim.pathguide.gesture_actions import action_bundle


def candidate():
    path = evaluation.SOURCE/'candidate.json'
    assert digest(path) == evaluation.SPEC['candidate_file_sha256']
    return json.loads(path.read_text())


def test_roundoff_grid_shadow_is_removed_but_distinct_geometry_is_not():
    boundary = 7.0
    targets = np.array([0, math.nextafter(boundary, 0), boundary+1e-9, 14])
    result = gestures._boundary_targets(targets, np.array([boundary, 14]))
    assert result.tolist() == [0, boundary, boundary+1e-9, 14]


@pytest.mark.parametrize('fixture', evaluation.SPEC['fixtures'], ids=lambda row: row['id'])
def test_all_frozen_plans_have_unique_provenance_bound_corners_without_execution(fixture):
    original = candidate()
    model = evaluation.probe(original, fixture)
    for label, (step, _) in evaluation.SPEC['refinements'].items():
        variant = evaluation.subdivide(model) if label == 'subdivision' else model
        bundle = action_bundle(fixture['text'], variant, step_mm=step, include_curve_positions=True)
        compiled = gestures.compile_gestures(fixture['text'], variant)['strokes']
        timed = retime_curve_tangents(bundle.plan, bundle.owners, compiled)
        assert len(timed.corners) == sum(row['transition'] == 'corner' for row in compiled)
        for corner in timed.corners:
            index = corner['source_index']
            owner = bundle.owners[index]
            assert owner['occurrence_id'] == corner['occurrence_id']
            assert owner['curve_position']['parameter'] == 0
            assert [row['gesture_progress'] for row in owner['boundary_contributors']] == [1, 0]
    assert candidate() == original


@pytest.mark.parametrize('letter', ['n', 'u', 'm'])
def test_saved_actual_events_are_resolution_independent_without_rerender(letter):
    root = evaluation.BASE/'continuation-001/run-001/seed-7/first'
    runs = json.loads(gzip.decompress((root/f'letter-{letter}-traces.json.gz').read_bytes()))
    pixels = {label: np.array(Image.open(root/f'letter-{letter}-{label}-metric.png')) for label in runs}
    for label in ('arc', 'time', 'subdivision'):
        result = measurement.comparison(runs['base'], runs[label], pixels['base'], pixels[label])
        assert result['owner_match']
        assert result['event_version'] == 'declared-contact-events-v1'
        assert result['event_time_s'] <= 1e-10
        assert result['endpoint_mm'] <= .01
    events = measurement.exact_events(runs['base'])
    assert [event['kind'] for event in events] == ['entry', 'corner', 'end']
    broken = copy.deepcopy(runs['base'])
    corner = broken['corners'][0]
    selected = next(row for row in broken['trace'] if row['plan_index'] == corner['plan_index']
                    and abs(row['time_s']-corner['time_s']) <= 1e-12)
    broken['trace'].remove(selected)
    assert not measurement.comparison(runs['base'], broken, pixels['base'], pixels['base'])['owner_match']
    broken = copy.deepcopy(runs['base'])
    broken['corners'] = []
    assert not measurement.comparison(runs['base'], broken, pixels['base'], pixels['base'])['owner_match']
