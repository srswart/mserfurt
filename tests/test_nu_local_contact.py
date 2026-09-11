import copy
import math

import pytest

from scripts import nu_local_contact as local


def piece(curves):
    return {'piece_id':'R','contact_profile':'core','contact':'pen-down',
            'contact_run_ref':'proposed-boundary-run','cubics_mm':curves}


def straight():
    return [[[offset+fraction,0] for fraction in (0,1/3,2/3,1)] for offset in (0,1,2)]


def test_adjacent_sweeps_across_joins_pass():
    result=local.classify(piece(straight()),local.actions.PROFILES)
    assert result['status']=='pass'
    assert result['classification']=='ordinary_neighboring_path_coverage'
    assert result['turning']['includes_all_join_turns']


def test_edge_projection_change_is_not_automatically_return_contact():
    curves=[[[0,0],[1,0],[2,1],[3,1]],[[3,1],[4,1],[4.1,3],[5,3]],[[5,3],[6,3],[7,4],[8,4]]]
    result=local.classify(piece(curves),local.actions.PROFILES)
    assert result['status']=='pass'
    values=result['measurement']['derivative_certificates'][1]['edge_derivative_control_values']
    assert min(values)<0<max(values)


@pytest.mark.parametrize('key,value',[('piece_id','T'),('contact','pen-up'),('contact_profile','receiving'),('contact_run_ref','another-run')])
def test_permission_cannot_expand_to_other_spans(key,value):
    candidate=piece(straight())
    candidate[key]=value
    with pytest.raises(ValueError):
        local.classify(candidate,local.actions.PROFILES)


def test_mutated_action_rejected():
    profiles=copy.deepcopy(local.actions.PROFILES)
    profiles['core']=profiles['full']
    with pytest.raises(ValueError):
        local.classify(piece(straight()),profiles)


def test_hidden_corner_not_ignored():
    curves=straight()
    curves[1]=[[1,0],[1,.1],[1.9,0],[2,0]]
    assert local.classify(piece(curves),local.actions.PROFILES)['status']=='unresolved'


def test_reversal_and_disconnected_runs_not_admitted():
    curves=straight()
    curves[1]=[[1,0],[2,0],[0,0],[2,0]]
    assert local.classify(piece(curves),local.actions.PROFILES)['status']=='unresolved'
    curves=straight()
    curves[1][0]=[1.1,0]
    with pytest.raises(ValueError):
        local.classify(piece(curves),local.actions.PROFILES)


def test_right_angle_boundary_unresolved():
    assert local.turning_gate(.1125*math.pi/2,0)['status']=='unresolved'
    assert local.turning_gate(.03,0)['status']=='pass'
    assert local.turning_gate(.03,math.pi)['status']=='unresolved'


def test_frozen_input_change_stops_verification(monkeypatch,tmp_path):
    approval=tmp_path/'approval.json'
    approval.write_text(local.json.dumps(local.approval_record()))
    monkeypatch.setattr(local,'APPROVAL',approval)
    monkeypatch.setattr(local.actions,'digest',lambda path:'changed')
    with pytest.raises(ValueError,match='Frozen input'):
        local.verify()


def test_no_constructor_or_retry_and_external_gate(monkeypatch,tmp_path):
    monkeypatch.setattr(local,'OUTPUT',tmp_path/'review')
    approval=tmp_path/'approval.json'
    approval.write_text(local.json.dumps(local.approval_record()))
    monkeypatch.setattr(local,'APPROVAL',approval)
    monkeypatch.setattr(local,'verify',lambda:None)
    baseline=local.source.read_json(local.measurement.OUTPUT/'report.json')
    monkeypatch.setattr(local.previous,'checks',lambda *args:baseline['unchanged_structural_checks'])
    def forbidden(*args,**kwargs):
        raise AssertionError('Constructor/classification must not run')
    monkeypatch.setattr(local.previous,'construct',forbidden)
    monkeypatch.setattr(local,'classify',forbidden)
    monkeypatch.setattr(local,'external_contacts',lambda *args:{'status':'unresolved'})
    result=local.run()
    assert result['local_contact']['status']=='not_evaluated'
    assert not result['accepted'] and not result['revised_geometry_contact_pass']
    with pytest.raises(FileExistsError):
        local.run()
