import json

import pytest

from scripts import nu_mutual_resume as resume


@pytest.fixture
def synthetic(monkeypatch, tmp_path):
    monkeypatch.setattr(resume, 'OUTPUT', tmp_path/'continuation')
    monkeypatch.setattr(resume.program, 'BASE', tmp_path)
    monkeypatch.setattr(resume.readiness, 'verify_receipt', lambda checksum: {'status': 'pass'})
    return tmp_path


def test_first_two_constructions_rejected_without_retry_or_render(synthetic, monkeypatch):
    calls = []
    def construct(model, name):
        calls.append(name)
        return {'synthetic': name}
    monkeypatch.setattr(resume.program, 'construct', construct)
    monkeypatch.setattr(resume.program, 'inspect', lambda document, model: {'status': 'rejected', 'checks': {}, 'render_eligible': False})
    report = resume.run('synthetic-receipt')
    assert calls == ['J1', 'J2'] and report['new_candidates'] == 2
    assert report['status'] == 'no_candidate_admitted'
    assert report['renders'] == 0 and (resume.OUTPUT/'index.html').exists()
    with pytest.raises(FileExistsError):
        resume.run('synthetic-receipt')


def test_constructed_candidate_is_saved_before_checker_failure(synthetic, monkeypatch):
    calls = []
    monkeypatch.setattr(resume.program, 'construct', lambda model, name: {'synthetic': name})
    def stopped(document, model):
        report = json.loads((resume.OUTPUT/'report.json').read_text())
        assert report['candidates'][0]['candidate'] == document
        calls.append('checked')
        raise ValueError('Synthetic technical failure')
    monkeypatch.setattr(resume.program, 'inspect', stopped)
    result = resume.run('synthetic-receipt')
    assert result['status'] == 'stopped' and result['new_candidates'] == 1
    assert calls == ['checked'] and result['renders'] == 0


def test_unverified_receipt_prevents_candidate_creation(synthetic, monkeypatch):
    def denied(checksum):
        raise ValueError('Unverified historical evidence')
    monkeypatch.setattr(resume.readiness, 'verify_receipt', denied)
    with pytest.raises(ValueError):
        resume.run('wrong')
    assert not resume.OUTPUT.exists()


def test_evidence_budget_counts_other_attempts(synthetic, monkeypatch):
    resume.OUTPUT.mkdir()
    (synthetic/'prior-evidence.bin').write_bytes(b'0'*200)
    monkeypatch.setattr(resume.program, 'MAX_BYTES', 65536+210)
    with pytest.raises(ValueError, match='Combined study'):
        resume.write('new.txt', '1'*11)


def test_failed_geometry_gets_text_not_ink_panel():
    board = resume.svg_board([{'label': 'J1', 'status': 'rejected'}], [-1, -4, 6, 1])
    assert 'not rendered' in board
    assert '<path' not in board


def test_no_admission_does_not_call_polygon_renderer(synthetic, monkeypatch):
    resume.OUTPUT.mkdir()
    def forbidden(*args):
        raise AssertionError('Rejected geometry rendered')
    monkeypatch.setattr(resume.program.history.renderer, 'polygons', forbidden)
    report = {'candidates': [{'brief': 'J1', 'status': 'unresolved'}]}
    resume.render(report)
    assert report['render_status'] == 'not_applicable_no_admitted_candidates'
