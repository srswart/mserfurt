import json
from pathlib import Path
import shutil

import pytest
from PIL import Image

from scribesim.curriculum.gesture_coverage import investigate, synthetic_fixtures


SOURCE = Path('reference/konrad_hand_recovery_v3')


def test_investigation_keeps_locked_pixels_sealed_and_real_scope_blocked(tmp_path, monkeypatch):
    dataset = json.loads((SOURCE / 'manifest.json').read_text())
    sealed = {(SOURCE / sample[kind + '_path']).resolve()
              for sample in dataset['samples'] if sample['split'] == 'test'
              for kind in ('raw', 'mask', 'cleaned')}
    sealed.update((SOURCE / source['path']).resolve() for source in dataset['sources'])
    original = Image.open

    def guarded_open(path, *args, **kwargs):
        assert Path(path).resolve() not in sealed
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Image, 'open', guarded_open)
    report = investigate(SOURCE, tmp_path / 'audit')
    assert report['audited_non_test'] == 52
    assert report['admitted_non_test'] == 0
    assert report['real_starter_characters'] == []
    assert report['real_fitting_evaluations'] == 0
    assert report['G0']['status'] == 'blocked'
    assert 'dataset_integrity_unverified' in report['G0']['reasons']
    assert report['scope_decision'] == {'synthetic': 'proceed-fixtures-only', 'real': 'blocked'}
    assert all(row['split'] != 'test' for row in report['observations'])
    assert all(row['independent_admitted_support'] == 0 for row in report['vocabulary'])


def test_fixtures_have_disjoint_transfer_and_bounded_expansion():
    fixtures = synthetic_fixtures()
    assert len(fixtures) == 8
    assert len({row['id'] for row in fixtures}) == 8
    for fixture in fixtures:
        assert 1 <= len(fixture['segments']) <= 4
        assert fixture['contact'] == 'continuous'
        assert fixture['provenance'] == 'project-authored analytic hypothesis; not a learned or historical stroke'
        assert fixture['transfer']['scale'] != fixture['practice']['scale']
        assert fixture['transfer']['composition'] != fixture['practice']['composition']
    assert len(next(row for row in fixtures if row['id'] == 'underturn')['segments']) == 3


def test_investigation_is_reproducible_and_refuses_overwrite(tmp_path):
    first, second = tmp_path / 'first', tmp_path / 'second'
    assert investigate(SOURCE, first) == investigate(SOURCE, second)
    for file in first.iterdir():
        assert file.read_bytes() == (second / file.name).read_bytes()
    with pytest.raises(ValueError, match='empty'):
        investigate(SOURCE, first)


@pytest.mark.parametrize('filename', ['manifest.json', 'review.json', 'approvals.json'])
def test_changed_source_or_review_requires_new_audit_scope(tmp_path, filename):
    copied = tmp_path / 'source'
    shutil.copytree(SOURCE, copied)
    with (copied / filename).open('a') as stream:
        stream.write(' ')
    with pytest.raises(ValueError, match='Frozen input'):
        investigate(copied, tmp_path / 'audit')


def test_changed_non_test_pixels_are_rejected(tmp_path):
    copied = tmp_path / 'source'
    shutil.copytree(SOURCE, copied)
    dataset = json.loads((copied / 'manifest.json').read_text())
    sample = next(row for row in dataset['samples'] if row['split'] != 'test')
    (copied / sample['mask_path']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='Artifact hash'):
        investigate(copied, tmp_path / 'audit')
