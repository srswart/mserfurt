import copy
import json
import gzip

import numpy as np
import pytest
from PIL import Image

from scripts import upright_placement_validation as runner
from scripts import upright_placement_evidence as reader
from scripts import upright_reference_contract as contract


def saved_record():
    original = json.loads((contract.SOURCE/'seed-7/first/report.json').read_text())
    known = {row['fixture']['id']: row for row in original['fixtures']}
    rows = []
    for fixture in runner.SPEC['fixtures']:
        row = copy.deepcopy(known.get(fixture['id'], known['placed-mu']))
        row['fixture'] = fixture
        row['approved_reference'] = {'status': 'match', 'quality_pass': None, 'generalization_proven': False,
                                     'scope': 'Exact scoped replay identity only'} if fixture['id'] in known else runner.UNREVIEWED.copy()
        row['nominal_actual_losses'] = copy.deepcopy(row['losses'])
        row['nominal_actual_losses'].pop('nominal')
        rows.append(row)
    return {**original, 'fixtures': rows, 'actual_ink_review': 'held_out_pending', 'decision_scope': runner.SPEC['stage']}


def test_authorized_protocol_is_exact_and_does_not_rewrite_prepared_snapshot():
    prepared = runner.prepared_protocol()
    assert prepared['execution_authorized'] is False
    assert runner.SPEC['seeds'] == [7, 19, 41]
    assert [row['text'] for row in runner.SPEC['fixtures']] == ['n','u','m','mu','un','nu','um','nn','uu','mm']
    assert runner.AUTH['budget_per_seed_including_replay'] == {'renders': 5000, 'seconds': 1800, 'automatic_retries': 0}
    assert runner.SPEC['mechanical_criteria'] == prepared['mechanical_criteria']
    assert runner.SPEC['refinements'] == prepared['refinements']


def test_decisions_separate_mechanics_from_style_and_withhold_admission():
    result = reader.decision(saved_record())
    assert result['execution_protocol_pass'] is True
    assert result['style_target']['status'] == 'fail'
    assert result['overall_admission'] == 'withheld'
    assert result['actual_ink_review'] == 'held_out_pending'
    assert result['S2_accepted'] is result['real_accepted'] is result['context_training_allowed'] is False


@pytest.mark.parametrize('mutation', ['fixture', 'refinement', 'control', 'nan', 'regression', 'approval', 'ports', 'motion', 'convergence', 'local', 'permissions'])
def test_incomplete_or_failed_evidence_fails_closed(mutation):
    record = saved_record()
    row = record['fixtures'][0]
    if mutation == 'fixture':
        record['fixtures'].pop()
    elif mutation == 'refinement':
        row['motion'].pop('arc')
    elif mutation == 'control':
        record['controls']['visible-shift']['detected'] = False
    elif mutation == 'nan':
        row['tracking_losses']['base'] = float('nan')
    elif mutation == 'regression':
        row['approved_reference']['status'] = 'mismatch'
    elif mutation == 'approval':
        record['fixtures'][-1]['approved_reference']['status'] = 'match'
    elif mutation == 'ports':
        row['actual_port_errors_mm']['base'] = {}
    elif mutation == 'motion':
        row['motion']['base']['errors']['contact'] = 1
    elif mutation == 'convergence':
        row['comparisons']['time']['event_time_s'] = 1
    elif mutation == 'local':
        row['nominal_actual_losses']['base']['local'] = {}
    else:
        record['context_training_allowed'] = True
    assert reader.decision(record)['execution_protocol_pass'] is False


def test_visible_shift_control_uses_actual_not_failed_style_comparator():
    base = np.full((20, 20, 3), 255, dtype=np.uint8)
    base[2:18, 2:4] = 0
    shifted = np.roll(base, 8, axis=1)
    assert runner.shift_control(base, base)['detected'] is False
    assert runner.shift_control(base, shifted)['detected'] is True


def test_frozen_source_preflight_has_no_controller_or_raster_calls(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Unbudgeted controller or raster call')
    monkeypatch.setattr(runner.evaluation.runtime, 'execute', forbidden)
    monkeypatch.setattr(runner.evaluation, 'paint', forbidden)
    source = runner.load_inputs()
    assert len(source['derived_references']) == 10
    assert len(source['core_identities']) == 206
    for fixture in runner.SPEC['fixtures']:
        frozen = source['derived_references'][fixture['id']]
        assert set(frozen['paths']) == {'target', 'nominal', 'prior'}
        assert frozen['nominal_provenance'] == 'candidate-derived; not independent style truth'
        model = runner.model_for_fixture(source['candidate'], fixture)
        assert model != source['candidate'] or fixture['shift'] == [0, 0]


def test_no_automatic_retry_or_missing_consumer_pin(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'BASE', tmp_path)
    (tmp_path/'run-001').mkdir()
    with pytest.raises(ValueError, match='immutable'):
        runner.evaluation.protocol.build(runner)
    with pytest.raises(ValueError, match='pin'):
        reader.inspect_run(tmp_path/'run-001', None)


def test_reader_recomputes_saved_raw_evidence_without_rendering(tmp_path, monkeypatch):
    source = runner.load_inputs()
    fixture = runner.SPEC['fixtures'][0]
    monkeypatch.setitem(runner.SPEC, 'fixtures', [fixture])
    original = contract.SOURCE/'seed-7/first'
    for path in original.glob('letter-n-*'):
        (tmp_path/path.name).symlink_to(path)
    model = runner.model_for_fixture(source['candidate'], fixture)
    runs = json.loads(gzip.decompress((tmp_path/'letter-n-traces.json.gz').read_bytes()))
    row = json.loads((original/'letter-n.json').read_text())
    images = {label: np.array(Image.open(tmp_path/f'letter-n-{label}-metric.png'))
              for label in ('target', 'nominal', 'prior', *runner.SPEC['refinements'])}
    row['approved_reference'] = runner.reference_result(source, fixture, images['base'])
    row['nominal_actual_losses'] = {label: runner.measurement.losses(images['nominal'], images[label], row['regions'], runner.evaluation.SPEC)
                                  for label in runs}
    shifted = np.roll(images['base'], 10, axis=1)
    Image.fromarray(shifted).save(tmp_path/'visible-shift-metric.png')
    controls = {**runner.evaluation.model_controls(source['candidate']),
                **runner.evaluation.trace_controls(model, fixture, runner.restore_owner_aliases(model, fixture, runs['base'])),
                'visible-shift': runner.shift_control(images['base'], shifted)}
    record = {'fixtures': [row], 'controls': controls}
    for name, value in [('candidate', source['candidate']), ('letter-n', row), ('controls', controls)]:
        (tmp_path/f'{name}.json').write_text(json.dumps(value))
    def forbidden(*args, **kwargs):
        pytest.fail('Read-only verification attempted execution or rendering')
    monkeypatch.setattr(runner.evaluation.runtime, 'execute', forbidden)
    monkeypatch.setattr(runner.evaluation, 'paint', forbidden)
    reader.verify_record(source, record, tmp_path)
    row['tracking_losses']['base'] += .001
    with pytest.raises(ValueError, match='raw evidence'):
        reader.verify_record(source, record, tmp_path)
    row['tracking_losses']['base'] -= .001
    path = tmp_path/'letter-n-traces.json.gz'
    path.unlink()
    runs['base']['trace'][10]['to_mm'][0] += 1
    path.write_bytes(gzip.compress(json.dumps(runs).encode()))
    with pytest.raises(ValueError):
        reader.verify_record(source, record, tmp_path)
