import copy
from fractions import Fraction

import pytest

from scripts import nu_entry_port_audit as audit


@pytest.mark.parametrize('scale,rotation,kind', [(-1,0,'similarity'),(1.6,0,'similarity'),(.49,0,'similarity'),(1,21,'similarity'),(1,0,'shear'),(1,0,'reflection'),(float('nan'),0,'similarity')])
def test_forbidden_transforms(scale, rotation, kind):
    with pytest.raises(ValueError):
        audit.placement(scale, rotation, kind)


def test_rotation_preserves_directed_not_unsigned_ports():
    assert abs(audit.difference(audit.angle([0,1]),audit.angle([0,-1]))) == 180
    with pytest.raises(ValueError):
        audit.angle([0,0])


def test_extrema_encloses_interior_minimum():
    result = audit.extrema(list(map(Fraction,[1,-2,2,0])))
    assert result['root_intervals'][0][0] < .5 < result['root_intervals'][0][1]
    assert result['minimum_lower'] < .5


def test_repeated_root_is_unresolved():
    with pytest.raises(audit.frozen.bounds.Unresolved):
        audit.extrema([Fraction(0),Fraction(1,4),Fraction(-1,2),Fraction(1,3)])


def test_changed_pin_rejected(monkeypatch):
    monkeypatch.setattr(audit.actions,'digest',lambda path:'changed')
    with pytest.raises(ValueError,match='Frozen audit input'):
        audit.verify(audit.approval_record())


@pytest.mark.parametrize('mutation', ['duplicate','action','interval'])
def test_source_coverage_and_actions_frozen(mutation):
    document = audit.source.read_json(audit.frozen.SAVED)
    if mutation == 'duplicate':
        document['retained'].append(copy.deepcopy(document['retained'][0]))
    elif mutation == 'action':
        document['profiles']['core'] = audit.actions.PROFILES['full']
    else:
        document['retained'][0]['source_interval'] = ['0','0.5']
    with pytest.raises(ValueError,match='identity'):
        audit.validate_contract(document,{}, {})


@pytest.mark.parametrize('field', ['core','length','names'])
def test_semantic_relabeling_cannot_reset_gates(field):
    core = audit.actions.PROFILES['full' if field=='core' else 'core']
    lengths = ['A-P','P-Q','Q-C'] if field=='length' else ['A-B','B-D','D-C']
    names = ['T','R','S'] if field=='names' else list(audit.INVENTORY)
    with pytest.raises(ValueError):
        audit.require_partition(core,lengths,names)


def test_source_inventory_has_real_shared_ports():
    model=audit.source.read_json(audit.source.CANDIDATE)
    for before,after in zip(audit.INVENTORY,audit.INVENTORY[1:]):
        assert audit.math.dist(model['primitives'][before]['exit'],model['primitives'][after]['entry']) < 1e-8


def test_no_retry_or_candidate_generation(monkeypatch,tmp_path):
    monkeypatch.setattr(audit,'BASE',tmp_path)
    monkeypatch.setattr(audit,'OUTPUT',tmp_path/'audit')
    (tmp_path/'approval.json').write_text('{}')
    monkeypatch.setattr(audit,'verify',lambda approval:None)
    def forbidden(*args,**kwargs):
        raise AssertionError('No construction permitted')
    monkeypatch.setattr(audit.frozen.original,'construct',forbidden)
    monkeypatch.setattr(audit,'analyze',lambda *args:{'status':'incompatible'})
    report=audit.run()
    assert report['status']=='incompatible'
    assert report['new_geometries']==report['renders']==report['fitting_evaluations']==0
    assert sorted(path.name for path in audit.OUTPUT.iterdir())==['report.json']
    with pytest.raises(FileExistsError):
        audit.run()
