import copy
import json

import numpy as np
from PIL import Image
import pytest

from scripts import upright_reference_contract as contract
from scribesim.handvalidate import upright_letters as evaluation
from scribesim.handvalidate.specimen import ROOT, digest


@pytest.fixture(scope='module')
def registry():
    return contract.make_registry()


def image_for(reference):
    return np.array(Image.open(ROOT/reference['image_path']))


def test_registry_separates_derived_appearance_from_independent_style(registry):
    assert set(registry['references']) == {'actual:letter-n', 'actual:letter-u', 'actual:letter-m', 'actual:placed-mu'}
    for reference in registry['references'].values():
        assert reference['role'] == 'approved_appearance_regression'
        assert reference['candidate_independent'] is False
        assert reference['owner_approved'] is True
    assert registry['style_reference']['candidate_independent'] is True
    assert registry['style_reference']['owner_approved'] is False
    assert registry['regression_policy']['mode'] == 'exact_replay_identity'
    assert registry['regression_policy']['variant_tolerance'] is None


def test_exact_replay_is_identity_not_generalization(registry):
    reference = registry['references']['actual:letter-n']
    result = contract.compare_reference(reference, image_for(reference), reference['context'])
    assert result['status'] == 'match'
    assert result['quality_pass'] is None
    assert result['generalization_proven'] is False
    changed = image_for(reference)
    changed[0, 0, 0] ^= 1
    assert contract.compare_reference(reference, changed, reference['context'])['status'] == 'mismatch'


@pytest.mark.parametrize('key,value', [('candidate_sha256','0'*64), ('dpi',900), ('tool_version','wrong'),
    ('frame_mm',[0,20,2,13]), ('fixture',{'id':'unseen'}), ('refinement',{'step_mm':.0125,'dt_s':.002})])
def test_scope_mismatch_cannot_inherit_approval(registry, key, value):
    reference = registry['references']['actual:letter-n']
    context = copy.deepcopy(reference['context'])
    context[key] = value
    assert contract.compare_reference(reference, image_for(reference), context)['status'] == 'incompatible'


def test_crop_dtype_and_independence_laundering_fail_closed(registry):
    reference = registry['references']['actual:letter-u']
    pixels = image_for(reference)
    assert contract.compare_reference(reference, pixels[:-1], reference['context'])['status'] == 'incompatible'
    assert contract.compare_reference(reference, pixels.astype(float), reference['context'])['status'] == 'incompatible'
    changed = copy.deepcopy(reference)
    changed['candidate_independent'] = True
    with pytest.raises(ValueError, match='provenance'):
        contract.compare_reference(changed, pixels, reference['context'])


def saved_record():
    return json.loads((contract.SOURCE/'seed-7/first/report.json').read_text())


def test_channel_split_preserves_style_failure_and_mechanical_success():
    result = contract.classify_record(saved_record())
    assert result['construction']['status'] == 'pass'
    assert result['physical_motion']['status'] == 'pass'
    assert result['style_target']['status'] == 'fail'
    assert result['historical_numeric_pass'] is False
    changed = saved_record()
    changed['fixtures'][0]['motion']['base']['errors']['contact'] = 1
    assert contract.classify_record(changed)['physical_motion']['status'] == 'fail'


@pytest.mark.parametrize('kind', ['missing_fixture','missing_control','nonfinite','missing_refinement'])
def test_incomplete_or_nonfinite_evidence_never_passes_channels(kind):
    changed = saved_record()
    if kind == 'missing_fixture':
        changed['fixtures'].pop()
    elif kind == 'missing_control':
        changed['controls'].pop('trace-owner')
    elif kind == 'missing_refinement':
        changed['fixtures'][0]['motion'].pop('arc')
    else:
        changed['fixtures'][0]['tracking_losses']['base'] = float('nan')
    result = contract.classify_record(changed)
    assert result['construction']['status'] == 'invalid'
    assert result['physical_motion']['status'] == 'invalid'
    assert result['historical_numeric_pass'] is False


def test_registry_requires_external_pin_and_exact_source_roles(tmp_path, registry):
    path = tmp_path/'registry.json'
    path.write_text(json.dumps(registry))
    with pytest.raises(ValueError, match='pin'):
        contract.load_registry(path, None)
    assert contract.load_registry(path, digest(path)) == registry
    changed = copy.deepcopy(registry)
    changed['references']['actual:letter-n']['candidate_independent'] = True
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='registry'):
        contract.load_registry(path, digest(path))


def test_read_only_build_inspect_and_protocol_boundary(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Contract validation attempted physical execution or rendering')
    monkeypatch.setattr(evaluation, 'paint', forbidden)
    monkeypatch.setattr(evaluation.runtime, 'execute', forbidden)
    output = tmp_path/'snapshot'
    result = contract.build(output)
    assert result['status'] == 'complete'
    assert result['overall_admission'] == 'withheld'
    assert len(result['workers']) == 6
    assert all(control['detected'] for control in result['controls'].values())
    assert contract.inspect(output, digest(output/'report.json'))['artifacts_verified'] == 3
    protocol = json.loads((output/'protocol.json').read_text())
    assert protocol['execution_authorized'] is False
    assert protocol['optimization_evaluations'] == 0
    assert {row['text'] for row in protocol['held_out_placements']} == {'un','nu','um','nn','uu','mm'}
    assert all(row['plan_preflight_pass'] for row in protocol['held_out_placements'])
    assert protocol['regression_variant_tolerance'] is None
    with pytest.raises(ValueError, match='exists'):
        contract.build(output)
    protocol['execution_authorized'] = True
    (output/'protocol.json').write_text(json.dumps(protocol))
    with pytest.raises(ValueError):
        contract.inspect(output, digest(output/'report.json'))
