import copy
import json

import numpy as np
import pytest

from scribesim.handvalidate import upright_letters as evaluation
from scribesim.handvalidate import upright_evidence as reader
from scribesim.handvalidate import upright_event_replay as current
from scribesim.handvalidate.specimen import digest


def test_reviewed_source_is_pinned_and_not_rebuilt():
    source = current.load_inputs()
    assert source['candidate']['schema_version'] == 'shared-stroke-gestures-connected-v1'
    changed = copy.deepcopy(source['candidate'])
    changed['primitives']['rise']['cubics'][0][1][0] += .001
    with pytest.raises(ValueError, match='candidate'):
        evaluation.require_candidate(changed)


def test_analytic_target_needs_no_candidate(monkeypatch):
    monkeypatch.setattr(evaluation, 'load_inputs', lambda: pytest.fail('Target reads candidate'))
    from scribesim.handvalidate.upright_targets import target
    for fixture in evaluation.SPEC['fixtures']:
        path, regions = target(fixture, evaluation.SPEC)
        assert path and regions
        assert all(point.pressure == (.5 if point.contact else 0) for point in path)
    fixture = next(row for row in evaluation.SPEC['fixtures'] if row['id'] == 'letter-n')
    path, _ = target(fixture, evaluation.SPEC)
    assert min(point.y_mm for point in path) == pytest.approx(6.5)
    assert max(point.y_mm for point in path) == pytest.approx(10)


def test_nominal_adapter_emits_supported_physical_scalars_without_rendering():
    from scribesim.evo.nib_contact import contact_corners
    candidate = current.load_inputs()['candidate']
    for fixture in evaluation.SPEC['fixtures']:
        model = evaluation.probe(candidate, fixture)
        for sample in evaluation.nominal(model, fixture['text']):
            assert type(sample.x_mm) is float
            assert type(sample.y_mm) is float
            contact_corners(sample)


def test_probes_and_exact_subdivision_preserve_caps_and_source():
    from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures
    source = current.load_inputs()['candidate']
    before = copy.deepcopy(source)
    for fixture in evaluation.SPEC['fixtures']:
        model = evaluation.probe(source, fixture)
        divided = evaluation.subdivide(model)
        validate_gestures(divided)
        rows = compile_gestures(fixture['text'], model)['strokes']
        halves = compile_gestures(fixture['text'], divided)['strokes']
        assert len(rows) == len(halves)
        assert max(sum(row['letter'] == letter for row in halves) for letter in range(len(fixture['text']))) <= 6
        for original, divided_row in zip(rows, halves):
            assert np.allclose(original['cubics'][0][0], divided_row['cubics'][0][0])
            assert np.allclose(original['cubics'][-1][-1], divided_row['cubics'][-1][-1])
    assert source == before


def test_existing_image_gates_are_local_and_ratio_is_defined():
    assert reader.image_pass({'global': .04, 'local': {'0': .03}}, .7)
    assert not reader.image_pass({'global': .001, 'local': {'0': .051}}, .7)
    assert not reader.image_pass({'global': .001, 'local': {'0': .001}}, None)
    assert not reader.image_pass({'global': float('nan'), 'local': {'0': .001}}, .1)
    assert not reader.image_pass({'global': .01, 'local': {'0': .01}}, .751)


def test_archive_reader_requires_external_pin_before_loading(tmp_path):
    (tmp_path / 'report.json').write_text(json.dumps({'status': 'pass'}))
    with pytest.raises(ValueError):
        reader.inspect_run(tmp_path, '0' * 64)
    assert digest(tmp_path / 'report.json') != '0' * 64


def test_source_controls_have_specific_rejection_reasons():
    controls = evaluation.model_controls(current.load_inputs()['candidate'])
    assert set(controls) == {'inserted-lift', 'gap', 'false-smooth-reversal', 'overlap-owner', 'geometry', 'tool', 'climbing'}
    assert all(row['detected'] and row['reason'] for row in controls.values())


def test_synthetic_contact_audit_survives_json_and_detects_substitution():
    from tests.test_connected_gestures import connected_model
    from scribesim.handvalidate.foundation_motion import Budget
    from scribesim.handvalidate import upright_measurement as measurement
    model = connected_model()
    fixture = {'text': 'ii', 'kind': 'primitive', 'shift': [0, 0]}
    run = evaluation.runtime.execute(model, 'ii', step=.025, dt=.002, budget=Budget(), physical=True,
                                     frame=evaluation.SPEC['frame_mm'])
    compact = {key: value for key, value in run.items() if key != 'images'}
    saved = json.loads(json.dumps(compact))
    proof = measurement.audit(model, fixture, saved, evaluation.SPEC)
    assert not any(proof['errors'].values()), proof
    assert len(proof['contact_runs']) == 2
    assert proof == measurement.audit(model, fixture, compact, evaluation.SPEC)
    controls = evaluation.trace_controls(model, fixture, saved)
    assert all(row['detected'] for row in controls.values()), controls
    masks = measurement.overlap_masks(saved, evaluation.SPEC)
    overlaps = measurement.overlap_proof(masks, model, 'ii')
    assert overlaps['repeated_pixels'] > 0
    assert overlaps['undeclared_pairs'] == 0
    saved['trace'][5]['to_mm'][0] = float('nan')
    with pytest.raises(ValueError, match='finite'):
        measurement.audit(model, fixture, saved, evaluation.SPEC)
