import pytest

from scripts import handvalidate_upright_partial as partial


def test_partial_reader_never_grants_acceptance_and_does_not_render(monkeypatch):
    def no_render(*args, **kwargs):
        pytest.fail('Read-only partial inspector attempted rendering')
    monkeypatch.setattr(partial.evaluation, 'paint', no_render)
    monkeypatch.setattr(partial.evaluation.runtime, 'execute', no_render)
    with pytest.raises(ValueError, match='source identity'):
        partial.inspect_partial(partial.continuation.BASE/'run-001', partial.REPORT_SHA256)
    import json
    result = json.loads((partial.continuation.BASE/'partial-inspection.json').read_text())
    assert result['status'] == 'incomplete'
    assert result['rerenders'] == 0
    assert result['completed_fixtures'] == [fixture['id'] for fixture in partial.evaluation.SPEC['fixtures'][:-1]]
    assert result['missing_fixtures'] == ['placed-mu']
    assert result['combined_renders'] == 149
    assert result['S2_accepted'] is False
    assert result['numeric_pass'] is False
    assert len(result['letters']) == 3


def test_partial_reader_rejects_missing_external_pin(tmp_path):
    (tmp_path/'report.json').write_text('{}')
    with pytest.raises(ValueError, match='pinned'):
        partial.inspect_partial(tmp_path, '0'*64)
