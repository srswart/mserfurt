import copy
import pytest

from scripts import nu_derived_entry as entry


def test_height_root_unique_and_bracketed():
    cubic=[[0,0],[1,0],[2,3],[3,3]]
    point,proof=entry.height_port(cubic,1.5)
    assert point==pytest.approx([1.5,1.5])
    assert entry.Fraction(proof['bracket_exact'][0])<entry.Fraction(1,2)<=entry.Fraction(proof['bracket_exact'][1])


def test_outside_or_reversing_scaffold_rejected():
    with pytest.raises(ValueError):
        entry.height_port([[0,0],[1,0],[2,3],[3,3]],4)
    with pytest.raises(entry.bounds.Unresolved):
        entry.height_port([[0,0],[1,4],[2,-4],[3,3]],1)


def test_handle_rule_is_not_arbitrary_bridge():
    source=[[0,0],[0,.2],[.8,1],[1,1]]
    ratios=entry.proportions(source)
    curve=entry.derive([0,0],[2,0],[1,0],[1,0],ratios)
    assert curve[1][0]==pytest.approx(2*.2/entry.math.sqrt(2))
    assert curve[2][0]==pytest.approx(2-2*.2/entry.math.sqrt(2))


def test_zero_chord_or_nonunit_ports_rejected():
    with pytest.raises(ValueError):
        entry.proportions([[0,0]]*4)
    with pytest.raises(ValueError):
        entry.derive([0,0],[1,1],[0,0],[1,0],[.3,.3])


@pytest.mark.parametrize('mutation',['body','action','number'])
def test_frozen_identity_and_contact(mutation):
    saved=entry.source.read_json(entry.frozen.SAVED)
    document=copy.deepcopy(saved)
    document['derivation']={}
    document['boundary'][1]['cubics_mm']*=3
    if mutation=='body':
        document['retained'][0]['source_interval']=['0','.5']
    elif mutation=='action':
        document['profiles']['core']=entry.actions.PROFILES['full']
    else:
        document['boundary'][1]['cubics_mm'].pop()
    with pytest.raises(ValueError,match='identity'):
        entry.unchanged(document,saved)


def test_false_primitive_relabeling_rejected():
    saved=entry.source.read_json(entry.frozen.SAVED)
    document=copy.deepcopy(saved)
    document['boundary'][1]['cubics_mm']*=3
    document['derivation']={'theta_deg':0,'contact_partition':['A-P','P-Q','Q-C']}
    with pytest.raises(ValueError,match='partition'):
        entry.checks(document,saved)


def test_approval_is_bounded():
    approval=entry.approval_record()
    assert approval['candidate_count']==1 and approval['retries']==0
    assert not approval['fitting'] and not approval['mu']


def test_curvature_not_relaxed():
    assert entry.bounds.original.curvature_check([[0,0],[.01,0],[.01,.01],[.01,.02]])['status']=='fail'


def test_run_preserves_failure_and_never_retries(monkeypatch,tmp_path):
    monkeypatch.setattr(entry,'OUTPUT',tmp_path/'run')
    monkeypatch.setattr(entry,'verify',lambda:None)
    calls=[]
    def stopped(*args):
        calls.append(1)
        raise ValueError('Synthetic root ambiguity')
    monkeypatch.setattr(entry,'construct',stopped)
    report=entry.run()
    assert report['status']=='stopped' and calls==[1]
    assert (entry.OUTPUT/'report.json').exists()
    with pytest.raises(FileExistsError):
        entry.run()
