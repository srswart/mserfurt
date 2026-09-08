import json

import numpy as np
from PIL import Image
import pytest

from scribesim.handvalidate import letter_assembly_evidence as evidence


def test_archived_convergence_uses_saved_pixels_without_rerendering(tmp_path, monkeypatch):
    validation = evidence.validation
    candidate = json.loads((validation.alignment.BASE / 'run-001/seed-7/first/candidate.json').read_text())
    prior = json.loads((validation.alignment.prior.BASE / 'run-001/seed-7/shared/first/candidate.json').read_text())
    fixture = validation.SPEC['fixtures'][-1]
    budget = validation.foundation.JournalBudget(tmp_path, 100, 120)
    row, runs = validation.measure(candidate, prior, fixture, budget, tmp_path)
    controls = validation.controls(candidate, fixture, runs['base'], budget, tmp_path)
    validation.write_json(tmp_path / 'candidate.json', candidate)
    record = {'fixtures': [row], 'controls': controls}
    source = {'candidate': candidate, 'prior': prior}
    with pytest.raises(KeyError, match='images'):
        validation.verify_record(source, record, tmp_path)
    original = {path: path.read_bytes() for path in tmp_path.rglob('*') if path.is_file()}
    def forbidden(*args, **kwargs):
        pytest.fail('Archived proof verification must not rerender or refit')
    monkeypatch.setattr(validation, 'paint', forbidden)
    monkeypatch.setattr(validation, 'execute', forbidden)
    evidence.verify_record(source, record, tmp_path)
    assert {path: path.read_bytes() for path in original} == original
    metric = tmp_path / f"{fixture['id']}-time-metric.png"
    Image.fromarray(np.zeros_like(np.array(Image.open(metric)))).save(metric)
    with pytest.raises(ValueError, match='image'):
        evidence.verify_record(source, record, tmp_path)


def test_reader_keeps_frozen_execution_identity_and_pending_appearance(monkeypatch):
    def verified(adapter, directory, pinned):
        assert adapter.identities() == evidence.validation.identities()
        assert adapter.verify_record is evidence.verify_record
        assert pinned == 'consumer-pin'
        return {'status': 'pass', 'S2_accepted': False, 'real_accepted': False}
    monkeypatch.setattr(evidence.validation.protocol, 'inspect', verified)
    result = evidence.inspect_run('unused', expected_report_sha256='consumer-pin')
    assert result['mechanical_validation_pass'] is True
    assert result['appearance_review'] == 'pending'
    assert result['S2_accepted'] is result['context_training_allowed'] is False


def test_unpinned_archives_fail_closed(tmp_path):
    (tmp_path / 'report.json').write_text('{}')
    with pytest.raises(ValueError):
        evidence.inspect_run(tmp_path, expected_report_sha256='wrong')
