import copy
import gzip
import json
import subprocess
from types import SimpleNamespace

import numpy as np
from PIL import Image

import pytest

from scripts import letter_context_physical as physical
from scripts import letter_context_physical_evidence as reader
from scribesim.handvalidate.specimen import digest, object_digest


def test_contract_freezes_approved_inventory_without_execution():
    contract = physical.contract_record()
    assert len(contract['cases']) == 244
    assert len({row['id'] for row in contract['cases']}) == 244
    assert contract['budget']['seconds_per_seed'] == 2700
    assert contract['budget']['renders_per_seed'] == 5000
    assert contract['budget']['seeds'] == [7, 19, 41]
    assert contract['renders_per_seed_upper_bound'] == 1588
    assert contract['physical_runs_per_seed'] == 488
    assert contract['fitting_authorized'] is False
    assert {row['fixture']['role'] for row in contract['cases']} == {'train_pairs', 'controls', 'known_regression'}
    assert sum(row['presentation'] for row in contract['cases']) == 54
    assert len(physical.render_schedule(contract))*2 == 1574 <= contract['renders_per_seed_upper_bound']


def test_frozen_preflight_and_approval_cannot_be_repinned(monkeypatch):
    monkeypatch.setattr(physical, 'APPROVAL_SHA256', '0'*64)
    with pytest.raises(ValueError, match='approval'):
        physical.contract_record()


def test_ledger_reserves_failed_render_and_cannot_reset(tmp_path):
    instant = [10.0]
    ledger = physical.Ledger(tmp_path/'execution.json', 2, 5, clock=lambda: instant[0])
    def fail():
        instant[0] += 1
        raise RuntimeError('renderer failed')
    with pytest.raises(RuntimeError):
        ledger.render(fail)
    assert ledger.used == 1
    assert json.loads((tmp_path/'execution.json').read_text())['renders'] == 1
    with pytest.raises(FileExistsError):
        physical.Ledger(tmp_path/'execution.json', 2, 5)
    ledger.render(lambda: None)
    with pytest.raises(RuntimeError, match='render budget'):
        ledger.render(lambda: pytest.fail('Unreserved render'))


def test_ledger_accounts_for_compute_timeout_and_nonfinite_clock(tmp_path):
    instant = [10.0]
    ledger = physical.Ledger(tmp_path/'execution.json', 5, 1, clock=lambda: instant[0])
    instant[0] += 1.1
    with pytest.raises(RuntimeError, match='time budget'):
        ledger.check()
    instant[0] = float('nan')
    with pytest.raises(RuntimeError, match='clock'):
        ledger.check()


@pytest.mark.parametrize('seconds,renders', [(2701, 5000), (2700, 5001), (float('nan'), 5), (0, 5), (1, True)])
def test_worker_budget_rejects_invalid_allowances(tmp_path, seconds, renders):
    with pytest.raises(ValueError):
        physical.Ledger(tmp_path/'execution.json', renders, seconds)


@pytest.fixture
def archived_case():
    contract = physical.contract_record()
    case = next(row for row in contract['cases'] if row['fixture']['id'] == 'letter-m' and row['refinement'] == 'base')
    directory = physical.preflight.foundation.SOURCE/'seed-7/first'
    with gzip.open(directory/'letter-m-traces.json.gz', 'rt') as stream:
        run = json.load(stream)['base']
    document = physical.document_for(contract, case)
    run['document_sha256'] = object_digest(document)
    return contract, case, document, run


def test_independent_derived_audit_preserves_archived_null_proof(archived_case):
    contract, case, document, run = archived_case
    proof = reader.audit_document(contract, case, document, run)
    assert reader.measurement.motion_pass(proof, contract['criteria'])
    assert proof['contained']
    model = physical.preflight.variants.source_model(contract['candidate'], case['fixture'], case['refinement'])
    assert proof == reader.measurement.audit(model, case['fixture'], run, physical.preflight.foundation.placement.evaluation.SPEC)


@pytest.mark.parametrize('change', ['owner', 'lift', 'clock', 'tool', 'desired_as_actual', 'plan', 'document', 'truncated'])
def test_reader_rejects_forged_raw_evidence(archived_case, change):
    contract, case, document, run = copy.deepcopy(archived_case)
    selected = next(row for row in run['trace'] if row['contact'] and row['dt_s'] > 0)
    if change == 'owner':
        selected['owner']['occurrence_id'] = 'invented'
    elif change == 'lift':
        selected['contact'] = False
    elif change == 'clock':
        selected['dt_s'] += .001
    elif change == 'tool':
        selected['width_mm'] = .46
    elif change == 'desired_as_actual':
        for row in run['trace']:
            row['to_mm'] = row['desired_mm'][:]
    elif change == 'plan':
        run['plan']['samples'][0]['x_mm'] += .01
    elif change == 'document':
        document['compiled']['strokes'][0]['cubics'][0][1][0] += .01
    else:
        run['trace'].pop()
    try:
        proof = reader.audit_document(contract, case, document, run)
    except ValueError:
        return
    assert not reader.measurement.motion_pass(proof, contract['criteria'])


def test_preparation_is_immutable_and_does_not_run_controller(tmp_path, monkeypatch):
    monkeypatch.setattr(physical, 'BASE', tmp_path)
    monkeypatch.setattr(physical.preflight, 'load_inputs', lambda: None)
    monkeypatch.setattr(physical, 'execute_raw', lambda *args: pytest.fail('Preparation executed controller'))
    physical.prepare()
    checksum = digest(tmp_path/'prepared-001/contract.json')
    assert physical.load_contract(checksum)['physical_runs_per_seed'] == 488
    with pytest.raises(FileExistsError):
        physical.prepare()
    with pytest.raises(ValueError, match='contract pin'):
        physical.load_contract('0'*64)


def test_derived_plan_reaches_controller_without_canonical_fallback(monkeypatch):
    contract = physical.contract_record()
    case = next(row for row in contract['cases'] if row['id'] == contract['control_case_id'])
    document = physical.document_for(contract, case)
    expected, _ = physical.preflight.variants.prepare_plan(document, contract['candidate'], case['fixture'], case['refinement'])
    class Capture:
        def __init__(self, model, execution_version):
            assert execution_version == 'event-time-v2'
        def step(self, *args, **kwargs):
            pytest.fail('No physical step is authorized by this routing test')
        def follow_plan(self, plan, dt, settle_time_s):
            assert plan == expected.plan
            assert dt == .002 and settle_time_s == 0
            raise RuntimeError('Captured only; not executed')
    monkeypatch.setattr(physical, 'ActionController', Capture)
    with pytest.raises(RuntimeError, match='Captured only'):
        physical.execute_raw(contract, case, document, SimpleNamespace(check=lambda: None))


def test_execution_adapter_serializes_recorded_events_without_running_physics(archived_case, monkeypatch):
    contract, case, document, archived = archived_case
    class RecordedController:
        def __init__(self, model, execution_version):
            self.dyn = SimpleNamespace(max_speed=1000)
            self.event = None
        def step(self, state, desired, *, dt):
            event = self.event
            state.acc_x_mm_s2, state.acc_y_mm_s2 = [
                (after-before)/dt if dt else 0 for before, after in
                zip(event['velocity_before_mm_s'], event['velocity_mm_s'])]
            state.vel_x_mm_s, state.vel_y_mm_s = event['velocity_mm_s']
            state.pos_x_mm, state.pos_y_mm = event['to_mm']
            return 0
        def follow_plan(self, plan, dt, settle_time_s):
            for event in archived['trace']:
                self.event = event
                state = SimpleNamespace(pos_x_mm=event['from_mm'][0], pos_y_mm=event['from_mm'][1],
                    vel_x_mm_s=event['velocity_before_mm_s'][0], vel_y_mm_s=event['velocity_before_mm_s'][1])
                self.step(state, None, dt=event['dt_s'])
            return SimpleNamespace(trajectory=[None]*len(archived['trace']),
                trajectory_plan_indices=[event['plan_index'] for event in archived['trace']],
                final_state=SimpleNamespace(execution_trace=archived['trace']))
    monkeypatch.setattr(physical, 'ActionController', RecordedController)
    run = physical.execute_raw(contract, case, document, SimpleNamespace(check=lambda: None))
    assert len(run['trace']) == len(archived['trace'])
    assert reader.measurement.motion_pass(reader.audit_document(contract, case, document, run), contract['criteria'])


def test_archived_pixels_and_owner_masks_pass_new_reader_without_rerendering(archived_case):
    contract, case, document, run = archived_case
    directory = physical.preflight.foundation.SOURCE/'seed-7/first'
    actual = np.asarray(Image.open(directory/'letter-m-base-metric.png'))
    desired = np.asarray(Image.open(directory/'letter-m-base-desired-metric.png'))
    masks = {owner: np.asarray(Image.open(directory/f"letter-m-base-owner-{owner.replace(':', '_')}.png"), dtype=bool)
        for owner in dict.fromkeys(row['gesture_occurrence_id'] for row in document['compiled']['strokes'])}
    result = reader.case_measurements(contract, case, document, run, actual, desired, masks)
    assert reader.case_pass(result, contract)
    assert result['known_reference']['status'] == 'match'
    result['context_training_allowed'] = 0
    assert not reader.case_pass(result, contract)
    with pytest.raises(ValueError, match='frame or DPI'):
        reader.case_measurements(contract, case, document, run, actual[:, 1:], desired, masks)


@pytest.mark.parametrize('failure', ['exit', 'timeout'])
def test_supervisor_retains_failed_attempt_and_debits_without_retry(tmp_path, monkeypatch, failure):
    contract = physical.contract_record()
    monkeypatch.setattr(physical, 'BASE', tmp_path)
    monkeypatch.setattr(physical, 'load_contract', lambda checksum: contract)
    calls = []
    def failed_worker(command, **kwargs):
        calls.append(command)
        directory = tmp_path/'run-001/seed-7/first'
        directory.mkdir()
        physical.write_json(directory/'execution.json', {'renders': 2})
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(command, kwargs['timeout'])
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(physical.subprocess, 'run', failed_worker)
    report = physical.run('test-pin')
    assert report['status'] == 'blocked'
    assert report['ledger'][0]['cumulative_renders'] == 2
    assert len(calls) == 1 and not report['seeds']
    with pytest.raises(FileExistsError):
        physical.run('test-pin')
    assert len(calls) == 1


def test_boolean_and_integer_admission_flags_are_not_interchangeable():
    assert physical.scope_matches(physical.FLAGS)
    for key in physical.FLAGS:
        changed = dict(physical.FLAGS)
        changed[key] = False if key == 'optimization_evaluations' else 0
        assert not physical.scope_matches(changed)


@pytest.mark.parametrize('width,advance,label', [(1, 0, 'identity'), (1, .05, 'spacing-only'),
    (.97, 0, 'stroke-only'), (.97, .05, 'stroke-and-spacing')])
def test_stroke_change_classification_excludes_translation(width, advance, label):
    contract = physical.contract_record()
    case = next(row for row in contract['cases'] if row['fixture']['id'] == 'train_pairs-nn'
        and row['refinement'] == 'base' and row['program']['rules'][0]['width_scale'] == width
        and row['program']['rules'][0]['advance_delta'] == advance)
    document = physical.document_for(contract, case)
    assert reader.change_kind(document) == label
    reader.require_change_kind(document, label)
    with pytest.raises(ValueError):
        reader.require_change_kind(document, 'invented-stroke-improvement')


def test_ineffective_image_control_is_rejected_without_rendering(archived_case, tmp_path):
    contract, case, document, run = archived_case
    directory = physical.preflight.foundation.SOURCE/'seed-7/first'
    actual = np.asarray(Image.open(directory/'letter-m-base-metric.png'))
    Image.fromarray(actual).save(tmp_path/'visible-shift.png')
    controls = reader.controls(contract, case, document, run, actual, directory=tmp_path)
    assert set(controls) == set(contract['controls'])
    assert controls['visible-shift'] is False
    assert all(value for key, value in controls.items() if key != 'visible-shift')


def test_saved_case_round_trip_reconstructs_measurements_without_controller_or_raster(archived_case, tmp_path, monkeypatch):
    contract, case, document, run = archived_case
    contract = {**contract, 'cases': [case]}
    directory = physical.preflight.foundation.SOURCE/'seed-7/first'
    actual = np.asarray(Image.open(directory/'letter-m-base-metric.png'))
    desired = np.asarray(Image.open(directory/'letter-m-base-desired-metric.png'))
    masks = {owner: np.asarray(Image.open(directory/f"letter-m-base-owner-{owner.replace(':', '_')}.png"), dtype=bool)
        for owner in dict.fromkeys(row['gesture_occurrence_id'] for row in document['compiled']['strokes'])}
    rendered = iter([actual, desired, masks])
    budget = SimpleNamespace(render=lambda *args, **kwargs: next(rendered))
    case_dir = tmp_path/case['id']
    case_dir.mkdir()
    physical.write_json(case_dir/'document.json', document)
    physical.write_json(case_dir/'attempt.json', {'case_id': case['id'], 'controller': 'complete'})
    physical.preflight.foundation.placement.evaluation.compressed(case_dir/'trace.json.gz', run)
    result, _ = reader.measure_case(contract, case, document, run, budget, case_dir)
    result['passed'] = reader.case_pass(result, contract)
    physical.write_json(case_dir/'measurement.json', result)
    record = {'status': 'pass', 'seed': 7, 'controller_executions': 1,
        'cases': [{'id': case['id'], 'passed': True}], **physical.FLAGS}
    physical.write_json(tmp_path/'report.json', record)
    monkeypatch.setattr(reader, 'paint', lambda *args: pytest.fail('Reader rerendered'))
    monkeypatch.setattr(physical, 'execute_raw', lambda *args: pytest.fail('Reader reran controller'))
    assert reader.verify_worker(contract, tmp_path, 7) == record
    result['tracking_loss'] = .123
    physical.write_json(case_dir/'measurement.json', result)
    with pytest.raises(ValueError, match='Stored verdict differs'):
        reader.verify_worker(contract, tmp_path, 7)


@pytest.fixture
def ledger_evidence(tmp_path, monkeypatch):
    contract = physical.contract_record()
    monkeypatch.setattr(physical, 'load_contract', lambda checksum: contract)
    monkeypatch.setattr(reader, 'verify_worker', lambda contract, directory, seed: json.loads((directory/'report.json').read_text()))
    physical.write_json(tmp_path/'contract.json', contract)
    checksum = digest(tmp_path/'contract.json')
    ledger = []
    count = 3*len(contract['cases'])+54+1
    for seed in (7, 19, 41):
        for offset, label in enumerate(('first', 'replay')):
            directory = tmp_path/f'seed-{seed}'/label
            directory.mkdir(parents=True)
            permit = {'seed': seed, 'label': label, 'maximum': 5000-count*offset,
                'seconds': 2700-10*offset, 'contract_sha256': checksum}
            physical.write_json(directory.parent/f'{label}-permit.json', permit)
            physical.write_json(directory/'execution.json', {'renders': count, 'maximum_renders': permit['maximum'],
                'maximum_seconds': permit['seconds'], 'elapsed_seconds': 1,
                'events': [{'ordinal': index, 'status': 'complete', 'operation': operation}
                    for index, operation in enumerate(physical.render_schedule(contract), 1)]})
            physical.write_json(directory/'report.json', {'renders': count, 'seed': seed, **physical.FLAGS})
            ledger.append({'seed': seed, 'process': label, 'renders': count, 'cumulative_renders': count*(offset+1),
                'cumulative_seconds': 10*(offset+1)})
    physical.write_json(tmp_path/'execution.json', {'ledger': ledger})
    report = {'status': 'pass', 'ledger': ledger, 'seeds': [{'seed': seed, 'replay_match': True} for seed in (7, 19, 41)],
        'artifacts': physical.artifact_map(tmp_path), **physical.FLAGS}
    physical.write_json(tmp_path/'report.json', report)
    return tmp_path, checksum


def test_readonly_ledger_verification_binds_all_six_processes(ledger_evidence):
    directory, checksum = ledger_evidence
    report = reader.inspect(directory, digest(directory/'report.json'), checksum)
    assert report['cases_verified'] == 1464 and report['read_only']


@pytest.mark.parametrize('change', ['time', 'renders', 'reserved', 'allowance', 'missing_process', 'permission'])
def test_ledger_reader_rejects_repinned_budget_or_scope_forgery(ledger_evidence, change):
    directory, checksum = ledger_evidence
    report = json.loads((directory/'report.json').read_text())
    if change in ('time', 'missing_process'):
        if change == 'time':
            report['ledger'][-1]['cumulative_seconds'] = 2701
        else:
            report['ledger'].pop()
        physical.write_json(directory/'execution.json', {'ledger': report['ledger']})
    elif change == 'permission':
        report['context_training_allowed'] = 0
    else:
        file = directory/'seed-7/first/execution.json'
        receipt = json.loads(file.read_text())
        if change == 'renders':
            receipt['renders'] -= 1
        elif change == 'reserved':
            receipt['events'][-1]['status'] = 'reserved'
        else:
            receipt['maximum_renders'] = 5001
        physical.write_json(file, receipt)
    report['artifacts'] = physical.artifact_map(directory, {'report.json'})
    physical.write_json(directory/'report.json', report)
    with pytest.raises(ValueError):
        reader.inspect(directory, digest(directory/'report.json'), checksum)
