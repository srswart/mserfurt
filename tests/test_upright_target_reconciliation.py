import json

import pytest

from scripts import handvalidate_upright_targets as reconciliation
from scribesim.handvalidate import upright_letters as evaluation
from scribesim.handvalidate.specimen import digest


def test_reconciliation_is_read_only_deterministic_and_not_admission(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Reconciliation attempted execution or rendering')
    monkeypatch.setattr(evaluation, 'paint', forbidden)
    monkeypatch.setattr(evaluation.runtime, 'execute', forbidden)
    first = reconciliation.reconcile()
    assert first == reconciliation.reconcile()
    assert first['source_numeric_pass'] is False
    assert first['appearance'] == 'approved_actual_ink'
    assert first['S2_accepted'] is False
    assert first['context_training_allowed'] is False
    assert first['new_target'] is False
    assert first['budgets'] == {'controller_executions': 0, 'raster_renders': 0, 'optimization_evaluations': 0}
    assert len(first['fixtures']) == 10
    for row in first['fixtures']:
        assert set(row['actual']) == {'base', 'arc', 'time', 'subdivision'}
        if row['id'] in {'letter-n', 'letter-u', 'letter-m'}:
            assert row['target_to_nominal']['global'] > .05
            assert row['actual']['base']['nominal_to_actual'] < .01
            assert row['actual']['base']['target_to_actual']['global'] > .05
    assert first['letter_entry_exit_span_mm']['n']['approved'] > first['letter_entry_exit_span_mm']['n']['analytic']


def test_pins_reject_corruption_and_path_escape(tmp_path):
    path = tmp_path/'sample.json'
    path.write_text('{}')
    pins = {'sample.json': digest(path)}
    reconciliation.verify_pins(tmp_path, pins)
    path.write_text('{"changed":true}')
    with pytest.raises(ValueError, match='pin'):
        reconciliation.verify_pins(tmp_path, pins)
    with pytest.raises(ValueError, match='path'):
        reconciliation.verify_pins(tmp_path, {'../outside': '0'*64})


def test_primitive_diagnostics_preserve_asymmetric_ports():
    candidate = json.loads((evaluation.SOURCE/'candidate.json').read_text())
    result = reconciliation.primitive_ports(candidate, evaluation.SPEC)
    assert result['rise']['approved_exit_mm'][0] == pytest.approx(.28)
    assert result['rise']['analytic_exit_mm'] == pytest.approx([0, 2.8])
    assert result['upper-return']['approved_entry_mm'][1] != result['upper-return']['approved_exit_mm'][1]
    assert result['upper-return']['analytic_entry_mm'][1] == pytest.approx(result['upper-return']['analytic_exit_mm'][1])


def test_report_writer_never_overwrites_prior_diagnostics(tmp_path):
    path = tmp_path/'report.json'
    path.write_text('preserved')
    with pytest.raises(ValueError, match='exists'):
        reconciliation.write_report(path, {})
    assert path.read_text() == 'preserved'
