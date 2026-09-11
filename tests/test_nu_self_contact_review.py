import pytest

from scripts import nu_self_contact_review as review


def test_all_pairs_bound_retains_thickness():
    result=review.measure([[[0,0],[1,0],[2,1],[3,1]]])
    assert result['status']=='bound_certified'
    assert .0311<result['possible_overlap_arclength_separation_upper_mm']<.0312
    assert result['finite_contact_thickness_mm']==.02
    assert 'not a new locality cutoff' in result['meaning']


def test_axis_turn_does_not_require_both_projections_monotone():
    result=review.measure([[[0,0],[1,0],[1.01,1],[2,1]]])
    assert result['status']=='bound_certified'
    values=result['derivative_certificates'][0]['edge_derivative_control_values']
    assert min(values)<0<max(values)


@pytest.mark.parametrize('curve',[[[0,0],[1,0],[-1,1],[0,1]],[[0,0],[1,1],[2,-1],[3,0]],[[0,0]]*4])
def test_reversal_or_zero_progress_not_certified(curve):
    assert review.measure([curve])['status']=='unresolved'


def test_discontinuous_chain_rejected():
    with pytest.raises(ValueError,match='Continuous'):
        review.measure([[[0,0],[1,0],[2,0],[3,0]],[[4,0],[5,0],[6,0],[7,0]]])


def test_no_reconstruction_or_retry(monkeypatch,tmp_path):
    monkeypatch.setattr(review,'OUTPUT',tmp_path/'review')
    monkeypatch.setattr(review,'verify',lambda:None)
    def forbidden(*args,**kwargs):
        raise AssertionError('Constructor must not run')
    monkeypatch.setattr(review.previous,'construct',forbidden)
    old=review.source.read_json(review.previous.OUTPUT/'report.json')
    monkeypatch.setattr(review.previous,'checks',lambda *args:{name:value for name,value in old['checks'].items() if name!='finite_contact'})
    monkeypatch.setattr(review.previous,'contacts',lambda *args:{'status':'unresolved','reason':'fixture'})
    report=review.run()
    assert report['status']=='unresolved' and report['new_geometries']==0
    assert not report['accepted']
    with pytest.raises(FileExistsError):
        review.run()
