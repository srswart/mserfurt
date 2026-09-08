import copy
import inspect
import json

import pytest

from scribesim.handvalidate import foundation_actions as evaluation


def test_new_holdouts_do_not_repeat_learning_transforms():
    old = {evaluation.object_digest(row['instances']) for row in evaluation.learning.SPEC['fixtures']}
    assert len(evaluation.SPEC['fixtures']) == 9
    assert all(evaluation.object_digest(row['instances']) not in old for row in evaluation.SPEC['fixtures'])
    assert 'candidate' not in inspect.signature(evaluation.target).parameters
    assert evaluation.SPEC['criteria']['absolute_loss_max'] == .05


def test_admission_does_not_fit_or_require_positive_learning_null(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Independent evaluation cannot optimize or read learning pass flags')

    monkeypatch.setattr(evaluation.learning, 'measure', forbidden)
    source = evaluation.load_inputs()
    assert set(source['candidates']) == {7, 19, 41}
    assert not source['selected']['null_hypothesis_supported']


@pytest.mark.parametrize('inventory,tool,real', [([], 'legacy-full-edge', False),
    (['oval'], 'legacy-full-edge', False), (['underturn'], 'physical-edge-v1', False),
    (['underturn'], 'legacy-full-edge', True)])
def test_scope_rejects_missing_unknown_cross_tool_and_real(inventory, tool, real):
    with pytest.raises(ValueError):
        evaluation.require_scope(inventory, tool, real)


def test_quality_requires_every_actual_refinement_and_local_occurrence():
    row = {'fixture': evaluation.SPEC['fixtures'][0],
           'actual_target': {label: .04 for label in evaluation.REFINEMENTS},
           'local_actual_target': {'0': {label: .04 for label in evaluation.REFINEMENTS}},
           'passed': True, 'nominal_target': .01}
    assert evaluation.quality(row)
    row['actual_target']['time'] = .051
    assert not evaluation.quality(row)
    row['actual_target']['time'] = .04
    row['local_actual_target']['0']['subdivision'] = float('nan')
    assert not evaluation.quality(row)
    del row['local_actual_target']['0']['subdivision']
    assert not evaluation.quality(row)


def test_missing_control_or_forged_detection_does_not_pass():
    assert not evaluation.controls_pass({})
    assert not evaluation.controls_pass({name: {'detected': True} for name in evaluation.SPEC['controls']})


def test_closed_counter_is_not_an_open_blank_pocket():
    import numpy as np

    pixels = np.full((156, 85, 3), 245, dtype=np.uint8)
    assert not evaluation.enclosed_blank(pixels, [1.6, 1.8, 5.6, 5.9])
    pixels[30:60, 20] = 0
    pixels[30:60, 35] = 0
    pixels[30, 20:36] = 0
    pixels[59, 20:36] = 0
    assert evaluation.enclosed_blank(pixels, [1.6, 1.8, 5.6, 5.9])
    pixels[30, 25:30] = 245
    assert not evaluation.enclosed_blank(pixels, [1.6, 1.8, 5.6, 5.9])


def test_asymmetric_physical_edge_control_is_not_a_dynamic_candidate():
    assert evaluation.SPEC['edge_control']['expected'] == [0, .45]
    assert evaluation.SPEC['edge_control']['swapped'] == [.55, 1]
    assert evaluation.SPEC['edge_control']['candidate_action_activation'] is False
    assert evaluation.SPEC['tool'] == 'legacy-full-edge'


def test_missing_source_stops_before_rendering(tmp_path, monkeypatch):
    def missing():
        raise ValueError('Missing pinned selected evidence')

    monkeypatch.setattr(evaluation, 'load_inputs', missing)
    report = evaluation.worker(tmp_path / 'seed', 7, 5000, 1800)
    assert report['status'] == 'blocked'
    assert report['renders'] == 0
    assert not (tmp_path / 'seed/candidate.json').exists()


def test_forged_manifest_cannot_admit_letters(tmp_path):
    evaluation.write_json(tmp_path / 'S1-actions.json', {'status': 'pass', 'S1_action_accepted': True})
    with pytest.raises(ValueError):
        evaluation.require_readiness(tmp_path, expected_report_sha256=evaluation.digest(tmp_path / 'S1-actions.json'),
                                     required_gestures=['underturn'])


def test_no_optimistic_completion_for_empty_numeric_proof():
    assert not evaluation.complete({'status': 'complete', 'fixtures': [], 'controls': {}, 'optimization_evaluations': 0})


def test_existing_output_is_immutable(tmp_path):
    with pytest.raises(ValueError, match='immutable'):
        evaluation.build(tmp_path)


def test_every_frozen_probe_respects_unchanged_grammar_before_rendering():
    candidate = json.loads((evaluation.learning.BASE / 'run-001/seed-7/first/candidate.json').read_text())
    for fixture in [*evaluation.SPEC['fixtures'], evaluation.SPEC['counter_fixture']]:
        model = evaluation.foundation.probe(candidate, fixture)
        assert 1 <= len(evaluation.compile_gestures('i', model)['strokes']) <= 6


def test_continuation_preserves_failed_attempt_costs():
    usage = evaluation.prior_usage()
    assert set(usage) == {7, 19, 41}
    assert all(row['renders'] == 550 and row['seconds'] > 140 for row in usage.values())


def test_support_terminal_is_not_missing_required_null_inventory():
    fixture = {'instances': [{'gesture': 'compound_curve'}, {'gesture': 'terminal'}]}
    row = {'fixture': fixture, 'actual_target': {label: .04 for label in evaluation.REFINEMENTS},
           'local_actual_target': {'0': {label: .04 for label in evaluation.REFINEMENTS}}}
    assert evaluation.quality(row)
    assert not evaluation.quality(row, 'terminal')


def test_live_numpy_scalars_are_normalized_without_changing_physical_values():
    import numpy as np
    from scribesim.evo.nib_contact import contact_corners

    row = {'to_mm': [np.float64(1.25), np.float64(3.5)], 'contact': True,
           'pressure': np.float64(.5), 'angle_deg': np.float64(40)}
    sample = evaluation.physical_samples({'trace': [row]}, [0, .45])[0]
    contact_corners(sample)
    assert type(sample.x_mm) is float and type(sample.y_mm) is float
    assert [sample.x_mm, sample.y_mm] == row['to_mm']
    assert sample.pressure == row['pressure'] and sample.nib_angle_deg == row['angle_deg']
    assert [sample.edge_start, sample.edge_end] == [0, .45]


def test_fixed_angle_roundoff_retains_raw_rate_without_failing_sample_contract():
    row = {'contact': True, 'pressure': .5, 'width_mm': .45, 'angle_deg': 40., 'time_s': 0.}
    run = {'tool': 'legacy-full-edge', 'trace': [row, {**row, 'angle_deg': 40.00000000000001, 'time_s': .001}]}
    proof = evaluation.tool_proof(run)
    assert proof['angle_rate_deg_s'] > 0
    assert evaluation.tool_pass(proof)
    run['trace'][1]['angle_deg'] = 40.000001
    assert not evaluation.tool_pass(evaluation.tool_proof(run))


def test_nonfinite_rate_or_changed_tool_cannot_pass():
    proof = evaluation.tool_proof({'tool': 'legacy-full-edge', 'trace': [
        {'contact': True, 'pressure': .5, 'width_mm': .45, 'angle_deg': 40., 'time_s': 0.}]})
    assert evaluation.tool_pass(proof)
    proof['angle_rate_deg_s'] = float('nan')
    assert not evaluation.tool_pass(proof)
    proof['angle_rate_deg_s'] = 0
    proof['mode'] = 'physical-edge-v1'
    assert not evaluation.tool_pass(proof)


def test_partial_control_evidence_is_saved_before_next_control(tmp_path):
    import gzip

    records = {'wrong-angle': {'detected': True, 'errors': 10}}
    evidence = {'wrong-angle': {'trace': [{'angle_deg': 55}]}}
    evaluation.checkpoint_controls(tmp_path, records, evidence)
    assert json.loads((tmp_path / 'controls.json').read_text()) == records
    assert json.loads(gzip.decompress((tmp_path / 'control-evidence.json.gz').read_bytes())) == evidence


def test_approved_rerun_keeps_fixture_target_and_limit_spec_identical():
    old_freeze = json.loads((evaluation.BASE / 'run-002/freeze.json').read_text())
    assert evaluation.SPEC == old_freeze['spec']


def test_completed_independent_reader_admits_only_measured_underturn_scope():
    root = evaluation.BASE / 'run-003'
    pinned = evaluation.digest(root / 'S1-actions.json')
    result = evaluation.require_readiness(root, expected_report_sha256=pinned, required_gestures=['underturn'])
    assert result['S1_action_accepted'] and result['kind'] == 'scoped-fixed-null'
    assert not result['letter_training_allowed'] and not result['real_accepted']
    with pytest.raises(ValueError, match='Unresolved'):
        evaluation.require_readiness(root, expected_report_sha256=pinned, required_gestures=evaluation.SPEC['required_gestures'])


def test_whole_inventory_pass_flag_cannot_override_actual_target_failures(tmp_path):
    import shutil

    root = tmp_path / 'forged'
    shutil.copytree(evaluation.BASE / 'run-003', root)
    report = json.loads((root / 'S1-actions.json').read_text())
    report.update(status='pass', S1_action_accepted=True, accepted_gestures=evaluation.SPEC['required_gestures'])
    evaluation.write_json(root / 'S1-actions.json', report)
    with pytest.raises(ValueError, match='flags disagree'):
        evaluation.require_readiness(root, expected_report_sha256=evaluation.digest(root / 'S1-actions.json'),
                                     required_gestures=evaluation.SPEC['required_gestures'])


def test_repaired_measurement_keeps_saved_actual_paths_and_pixels_identical():
    for seed in evaluation.SPEC['seeds']:
        old = evaluation.BASE / f'run-002/seed-{seed}/first'
        new = evaluation.BASE / f'run-003/seed-{seed}/first'
        for path in old.iterdir():
            if path.suffix in ('.png', '.gz') or path.name == 'candidate.json':
                assert path.read_bytes() == (new / path.name).read_bytes()
