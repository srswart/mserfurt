import copy
import json

import numpy as np
import pytest


def test_frozen_frame_covers_compound_and_old_frame_is_rejected():
    from scribesim.curriculum import foundation_measurement as measurement
    from scribesim.curriculum import foundation_primitives as learning

    fixture = learning.SPEC['splits']['held_out'][-1]
    points = measurement.segment_trajectory(learning.target_segments(fixture))
    measurement.require_containment(points)
    with pytest.raises(ValueError, match='frame'):
        measurement.require_containment(points, frame=learning.SPEC['frame_mm'])
    assert measurement.SPEC['frame_mm'] == [-2, 9, 3, 16]
    assert measurement.SPEC['max_renders'] == 500


def test_crop_rejects_outside_regions_instead_of_hiding_missing_strokes():
    from scribesim.curriculum.foundation_measurement import crop

    pixels = np.zeros((130, 110, 3), dtype=np.uint8)
    assert crop(pixels, [0, 1, 13, 15]).size > 0
    with pytest.raises(ValueError, match='region'):
        crop(pixels, [0, 1, 15, 17])


def test_source_admission_rejects_fabricated_status_before_render(tmp_path, monkeypatch):
    from scribesim.curriculum import foundation_measurement as measurement

    (tmp_path / 'report.json').write_text(json.dumps({'status': 'pass'}))
    with pytest.raises(ValueError):
        measurement.load_source(tmp_path)
    monkeypatch.setattr(measurement, 'load_source', lambda: (_ for _ in ()).throw(ValueError('Changed source')))
    monkeypatch.setattr(measurement, 'paint', lambda *args, **kwargs: pytest.fail('Rendered before admission'))
    report = measurement.build(tmp_path / 'output')
    assert report['status'] == 'blocked' and report['renders'] == 0
    assert report['optimization_evaluations'] == report['execution_calls'] == 0


def test_compound_remeasurement_uses_saved_candidate_and_traces_without_refit(tmp_path, monkeypatch):
    from scribesim.curriculum import foundation_measurement as measurement
    from scribesim.curriculum import foundation_primitives as learning

    source = measurement.load_source()
    row = source['seeds'][7]
    before = copy.deepcopy(row['candidate'])
    fixture = learning.SPEC['splits']['held_out'][-1]
    monkeypatch.setattr(learning, 'search_handles', lambda *args, **kwargs: pytest.fail('Optimizer called'))
    monkeypatch.setattr(learning, 'execute_fixture', lambda *args, **kwargs: pytest.fail('New trajectory created'))
    record, tiles = measurement.measure_fixture(row['candidate'], fixture, row['traces'][fixture['id']], learning.Budget(500, 900))
    assert before == row['candidate']
    assert set(record['families']) == {'lower-return', 'upper-return'}
    assert all(family['before'] > 0 for family in record['families'].values())
    assert len(tiles) == 5
    assert record['footprint_contained']


def test_every_seed_and_fixture_is_required_for_completion():
    from scribesim.curriculum.foundation_measurement import complete

    rows = [{'seed': seed, 'fixtures': [{'passed': True} for index in range(5)]} for seed in (7, 19, 41)]
    assert complete(rows)
    rows[1]['fixtures'][-1]['passed'] = False
    assert not complete(rows)
    assert not complete(rows[:1])
