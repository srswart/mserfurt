import copy
from dataclasses import replace
import json
import math

import numpy as np
import pytest

from scribesim.handvalidate import foundation_primitives as evaluation
from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide
from scribesim.handflow.planning import build_track_plan, retime_curve_timing


def source(model, step=.025, text='i'):
    bundle = gesture_guide(text, model, step_mm=step, include_curve_positions=True)
    return build_track_plan(bundle.guide, base_speed_mm_s=12), bundle.metadata['owners'], compile_gestures(text, model)['strokes']


def frozen():
    return json.loads((evaluation.BASE / 'run-001/seed-7/first/candidate.json').read_text())


def test_actual_failed_seam_is_repaired_without_moving_samples_or_changing_clock():
    from scribesim.handflow.curve_tangents import retime_curve_tangents, VERSION

    model = evaluation.subdivide(evaluation.probe(frozen(), evaluation.FIXTURES[-1]))
    original, owners, strokes = source(model)
    old = retime_curve_timing(original, owners, strokes)
    assert evaluation.motion.desired_motion_metrics(old.plan)['desired_acceleration_mm_s2'] > 402
    repaired = retime_curve_tangents(original, owners, strokes)
    assert repaired.version == VERSION == 'curve-tangent-v1'
    assert evaluation.motion.desired_pass(evaluation.motion.desired_motion_metrics(repaired.plan))
    assert repaired.source_indices == old.source_indices
    assert [row.t_s for row in repaired.plan.samples] == [row.t_s for row in old.plan.samples]
    for before, after in zip(old.plan.samples, repaired.plan.samples):
        assert replace(after, vx_mm_s=before.vx_mm_s, vy_mm_s=before.vy_mm_s) == before
    assert retime_curve_timing(original, owners, strokes) == old


@pytest.mark.parametrize('family', ['stem', 'rise', 'bowl', 'turn', 'loop', 'exit', 'lower-return', 'upper-return'])
def test_all_eight_families_preserve_geometry_and_subdivision_timing(family):
    from scribesim.handflow.curve_tangents import retime_curve_tangents

    model = evaluation.probe(frozen(), {'topology': [family], 'scale': .9})
    variants = [(model, .025), (model, .0125), (evaluation.subdivide(model), .025)]
    results = [retime_curve_tangents(*source(variant, step)) for variant, step in variants]
    for result in results:
        assert evaluation.motion.desired_pass(evaluation.motion.desired_motion_metrics(result.plan))
        assert result.plan.total_time_s == pytest.approx(results[0].plan.total_time_s, abs=1e-10)


def test_curve_direction_is_analytic_and_rejects_stationary_or_nonfinite_geometry():
    from scribesim.handflow.curve_tangents import cubic_direction

    cubic = [[0, 0], [0, 1], [1, 1], [1, 0]]
    assert np.allclose(cubic_direction(cubic, .5), [1, 0])
    assert np.allclose(cubic_direction(cubic, 0), [0, 1])
    for broken in ([[0, 0]] * 4, [[float('nan'), 0]] * 4, [[0, 0]] * 3):
        with pytest.raises(ValueError):
            cubic_direction(broken, .5)
    for parameter in (-.1, 1.1, float('nan'), True):
        with pytest.raises(ValueError):
            cubic_direction(cubic, parameter)


def test_repaired_tangents_fail_closed_on_fabricated_source_or_owner():
    from scribesim.handflow.curve_tangents import retime_curve_tangents

    model = evaluation.probe(frozen(), evaluation.FIXTURES[-1])
    plan, owners, strokes = source(model)
    for mutation in ('missing', 'owner', 'position'):
        changed = copy.deepcopy(owners)
        altered = plan
        if mutation == 'missing':
            changed[5].pop('curve_position')
        elif mutation == 'owner':
            changed[5]['primitive_sha256'] = 'fabricated'
        else:
            samples = list(plan.samples)
            samples[5] = replace(samples[5], x_mm=samples[5].x_mm + .01)
            altered = replace(plan, samples=tuple(samples))
        with pytest.raises(ValueError):
            retime_curve_tangents(altered, changed, strokes)


def test_corners_and_lifted_reentry_keep_explicit_contact_ownership():
    from scribesim.handflow.curve_tangents import retime_curve_tangents

    for label, text, model in evaluation.motion.fixtures():
        model['sampling'] = 'gesture-arc-v3'
        plan, owners, strokes = source(model, text=text)
        result = retime_curve_tangents(plan, owners, strokes)
        assert evaluation.motion.desired_pass(evaluation.motion.desired_motion_metrics(result.plan)), label
        assert [index for sample, index in zip(result.plan.samples, result.source_indices) if sample.contact] == [index for index, sample in enumerate(plan.samples) if sample.contact]
        for corner in result.corners:
            sample = result.plan.samples[corner['plan_index']]
            assert sample.contact and sample.speed_mm_s == sample.vx_mm_s == sample.vy_mm_s == 0
        assert all(row.pressure == 0 for row in result.plan.samples if not row.contact)


def test_no_refit_compatibility_and_invalid_source_stop(tmp_path, monkeypatch):
    from scribesim.handvalidate import tangent_evaluation

    source_inputs = tangent_evaluation.load_inputs()
    assert set(source_inputs['seeds']) == {7, 19, 41}
    assert source_inputs['seeds'][7]['candidate'] == frozen()
    monkeypatch.setattr(tangent_evaluation, 'load_inputs', lambda: (_ for _ in ()).throw(ValueError('Changed source')))
    report = tangent_evaluation.build(tmp_path / 'run')
    assert report['status'] == 'blocked' and report['renders'] == report['optimization_evaluations'] == 0
    assert not report['gesture_training_permitted']


def test_tangent_reader_rejects_old_or_fabricated_pass(tmp_path):
    from scribesim.handvalidate.tangent_evaluation import require_readiness

    (tmp_path / 'S1-primitives.json').write_text(json.dumps({'status': 'pass', 'gesture_training_permitted': True}))
    with pytest.raises(ValueError):
        require_readiness(tmp_path, expected_report_sha256='0' * 64, required_families=['lower-return'])


def test_new_execution_and_controls_use_existing_controller_without_fitting(tmp_path, monkeypatch):
    from scribesim.handvalidate import tangent_motion

    forbidden = lambda *args, **kwargs: pytest.fail('Training helper called')
    for name in ('execute_fixture', 'search_handles', 'build'):
        monkeypatch.setattr(evaluation.learning, name, forbidden)
    model = evaluation.contract.initial_model()
    budget = evaluation.learning.Budget()
    record, runs, tiles = evaluation.evaluate_fixture(model, evaluation.FIXTURES[-1], budget, tmp_path, version=tangent_motion.VERSION)
    assert record['full']['ratio'] == 1 and not record['passed']
    assert all(run['passed'] and run['version'] == tangent_motion.VERSION for run in runs.values())
    controls = evaluation.controls(model, budget, tmp_path, version=tangent_motion.VERSION)
    assert all(row['detected'] for row in controls.values())
    assert not controls['extra-contributor']['global_meets_minimum']
    assert len(tiles) == 5


def test_unknown_execution_mode_cannot_fall_back_to_legacy():
    model = evaluation.probe(evaluation.contract.initial_model(), evaluation.FIXTURES[0])
    with pytest.raises(ValueError, match='Unsupported'):
        evaluation.execute(model, step=.025, dt=.002, budget=evaluation.learning.Budget(), version='unknown')


@pytest.mark.parametrize('family', ['stem', 'rise', 'bowl', 'turn', 'loop', 'exit'])
def test_baseline_probe_proves_single_occurrence_geometry_without_relaxing_migration(family):
    from scribesim.handvalidate.tangent_evaluation import baseline_probe
    from scribesim.evofit.stroke_gestures import migrate_v1

    original = evaluation.motion.load_historical_baseline()
    sample = next(row for row in original['freeze']['samples'] if row['id'] == family + '-base')
    language, text = evaluation.motion.strokes.exercise_model(original['candidate'], sample)
    before = copy.deepcopy(language)
    with pytest.raises(ValueError, match='crossings'):
        migrate_v1(language)
    model = baseline_probe(family, language, sample)
    assert language == before and language['recipes']['exercise']['allow_crossings']
    prior = evaluation.motion.compile_text(text, language)['strokes']
    current = compile_gestures(text, model)['strokes']
    assert len(prior) == len(current) == 1
    assert prior[0]['cubics'] == current[0]['cubics'] and prior[0]['span'] == current[0]['span']
    assert model['primitives'][family] == language['primitives'][family]
    changed = copy.deepcopy(language)
    changed['recipes']['exercise']['strokes'][0]['offset'][0] += .1
    with pytest.raises(ValueError):
        baseline_probe(family, changed, sample)


def test_diagnosed_retry_charges_the_retained_first_attempt():
    from scribesim.handvalidate.tangent_evaluation import prior_usage

    usage = prior_usage()
    assert set(usage) == {7, 19, 41}
    assert all(row['renders'] == 324 and row['seconds'] > 0 for row in usage.values())


def test_worker_allowance_includes_prior_attempt_and_cannot_create_a_pass(tmp_path, monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace
    from scribesim.handvalidate import tangent_evaluation

    calls = []

    def fake_worker(command, **kwargs):
        directory = Path(command[command.index('--output') + 1])
        seed = int(command[command.index('--worker-seed') + 1])
        maximum = int(command[command.index('--maximum') + 1])
        seconds = float(command[command.index('--seconds') + 1])
        assert maximum == 4676 and 0 < seconds < 1800
        calls.append(seed)
        evaluation.write_json(directory / 'report.json', {'status': 'blocked', 'renders': 0, 'seed': seed})
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(tangent_evaluation.subprocess, 'run', fake_worker)
    report = tangent_evaluation.build(tmp_path / 'mocked')
    assert calls == [7, 7, 19, 19, 41, 41]
    assert report['renders'] == 0 and report['cumulative_renders'] == 972
    assert report['status'] == 'fail' and not report['gesture_training_permitted']
