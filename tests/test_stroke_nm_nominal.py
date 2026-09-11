import pytest

from scripts import stroke_nm_nominal as nominal


def test_forged_nominal_approval():
    approval = nominal.approval_record()
    approval['png_count'] = 48
    with pytest.raises(ValueError, match='approval'):
        nominal.verify(approval)


def test_changed_passing_report(monkeypatch):
    monkeypatch.setattr(nominal.evaluation.original, 'digest', lambda filename: 'wrong')
    with pytest.raises(ValueError, match='Changed passing report'):
        nominal.verify(nominal.approval_record())


@pytest.mark.parametrize('text,mode', [('um', 'B3'), ('nm', 'B1'), ('nm', 'B2'), ('new', 'B0')])
def test_unapproved_inventory(text, mode):
    with pytest.raises(ValueError, match='inventory'):
        nominal.document(text, mode, {}, {})


@pytest.mark.parametrize('text', ['n', 'm', 'nn', 'mm'])
def test_controls_exact(text):
    source = nominal.evaluation.original.attachment.source
    canonical = source.read_json(source.CANDIDATE)
    assert nominal.document(text, 'B0', {}, canonical) == nominal.document(text, 'B3', {}, canonical)


def test_saved_pieces_are_rendered_once():
    source = nominal.evaluation.original.attachment.source
    saved = source.read_json(nominal.BASE/'attempt-001/candidate.json')
    rows = nominal.document('nm', 'B3', saved, {})['compiled']['strokes']
    assert len(rows) == 12
    assert rows[:10] == [piece['stroke'] for piece in saved['pieces'][:10]]
    assert rows[-1]['nominal_owner'] == saved['pieces'][-1]['owner']
    assert len(rows[-1]['contributors']) == 2
    for row, piece in zip(rows[-2:], saved['pieces'][-2:]):
        assert row['cubics'] == [[[value/3.5 for value in control] for control in cubic] for cubic in piece['cubics_mm']]


def test_review_starts_without_owner_preference():
    template = nominal.TEMPLATE.read_text()
    assert '<option value="">Not reviewed</option>' in template
    assert 'NOMINAL CONSTRUCTION — NOT ACTUAL INK' in template
    assert '__MANIFEST__' in template
