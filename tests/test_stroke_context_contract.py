import copy
from dataclasses import asdict, replace
import json

import pytest

from scripts import stroke_context_contract as context
from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handflow.curve_tangents import retime_curve_tangents
from scribesim.pathguide.gesture_actions import action_bundle


@pytest.fixture
def candidate():
    return json.loads(context.audit.CANDIDATE.read_text())


def compile_document(candidate, text='un', hypothesis='H3', refinement='base'):
    return context.compile_context(candidate, text, context.request(hypothesis), refinement,
                                   context.contract_pin())


@pytest.mark.parametrize('text', context.audit.PROBES)
@pytest.mark.parametrize('refinement', ['base', 'arc', 'time', 'subdivision'])
def test_exact_null_geometry_plan_action_and_timing(candidate, text, refinement):
    document = compile_document(candidate, text, 'H0', refinement)
    model = context.legacy.foundation.placement.evaluation.subdivide(candidate) if refinement == 'subdivision' else candidate
    compiled = compile_gestures(text, model)
    assert document['compiled'] == compiled
    actual = context.prepare_null_plan(document, candidate, context.contract_pin())
    bundle = action_bundle(text, model, step_mm=context.legacy.foundation.placement.SPEC['refinements'][refinement][0], include_curve_positions=True)
    timed = retime_curve_tangents(bundle.plan, bundle.owners, compiled['strokes'])
    expected = (replace(bundle, plan=timed.plan, owners=[bundle.owners[index] for index in timed.source_indices]), timed)
    assert [asdict(value) for value in actual] == [asdict(value) for value in expected]


@pytest.mark.parametrize('text', context.audit.PROBES)
@pytest.mark.parametrize('hypothesis', ['H0', 'H1', 'H2', 'H3'])
def test_bounded_lineage_and_no_source_mutation(candidate, text, hypothesis):
    before = copy.deepcopy(candidate)
    document = compile_document(candidate, text, hypothesis)
    context.verify_document(document, candidate, context.contract_pin())
    assert candidate == before
    assert document['execution_authorized'] is False
    for change in document['edits']:
        assert change['displacement_mm'] <= .04
        assert change['control_point'] in (1, 2)
        assert change['angle_deg'] in (-1, 1)
    assert len(document['boundaries']) == len(text)-1
    assert all(row['ink_owners'] == [] for row in document['boundaries'])


def test_two_sided_selectors_and_sentinels(candidate):
    near = compile_document(candidate, 'nn')['contexts'][1]
    far = compile_document(candidate, 'mn')['contexts'][1]
    assert near['previous_bin'] == 'near'
    assert far['previous_bin'] == 'far'
    assert near['following_class'] == 'EOS'
    assert compile_document(candidate, 'un')['contexts'][0]['following_class'] == 'stem-entry'
    assert compile_document(candidate, 'um')['contexts'][0]['following_class'] == 'rise-entry'
    assert compile_document(candidate, 'u')['edits'] == []


@pytest.mark.parametrize('field', ['word', 'fixture', 'seed', 'ports', 'bounds', 'execution_authorized'])
def test_no_unreviewed_request_fields(candidate, field):
    request = context.request('H3')
    request[field] = True
    with pytest.raises(ValueError):
        context.compile_context(candidate, 'un', request, 'base', context.contract_pin())


@pytest.mark.parametrize('intent', ['pen_down_join', 'pen_down_retrace', 'smooth', 'implicit_lift'])
def test_unsupported_contact_intents_reject(candidate, intent):
    request = context.request('H3')
    request['transition_intent'] = intent
    with pytest.raises(ValueError):
        context.compile_context(candidate, 'un', request, 'base', context.contract_pin())


@pytest.mark.parametrize('text', ['a', 'nuu', 'num', 'n u', 'n\nu', ''])
def test_unsupported_inventory_rejects(candidate, text):
    with pytest.raises(ValueError):
        compile_document(candidate, text)


@pytest.mark.parametrize('mutation', ['body', 'port', 'owner', 'lift', 'smooth', 'lineage', 'permission', 'selector'])
def test_rehashed_forgery_rejects(candidate, mutation):
    document = compile_document(candidate)
    if mutation == 'body':
        document['compiled']['strokes'][1]['cubics'][0][1][0] += .001
    elif mutation == 'port':
        document['contexts'][0]['entry']['tangent_local_y_up'] = [0, 0]
    elif mutation == 'owner':
        document['boundaries'][0]['ink_owners'] = ['0:0']
    elif mutation == 'lift':
        document['boundaries'][0]['kind'] = 'pen_down_join'
    elif mutation == 'smooth':
        document['compiled']['strokes'][3]['transition'] = 'smooth'
    elif mutation == 'lineage':
        document['lineage'][0]['source_sha256'] = '0'*64
    elif mutation == 'permission':
        document['execution_authorized'] = True
    else:
        document['contexts'][0]['following_class'] = 'rise-entry'
    with pytest.raises(ValueError):
        context.verify_document(document, candidate, context.contract_pin())


def test_nonidentity_never_enters_legacy_planner(candidate):
    with pytest.raises(ValueError, match='H0'):
        context.prepare_null_plan(compile_document(candidate), candidate, context.contract_pin())


def test_external_pin_required(candidate):
    with pytest.raises(ValueError, match='pin'):
        context.compile_context(candidate, 'un', context.request('H3'), 'base', '')


def test_verifier_does_not_trust_public_compiler(candidate, monkeypatch):
    document = compile_document(candidate)
    monkeypatch.setattr(context, 'compile_context', lambda *args: pytest.fail('Trusted compiler'))
    context.verify_document(document, candidate, context.contract_pin())


@pytest.mark.parametrize('refinement', ['arc', 'time', 'subdivision'])
def test_nonidentity_refinements_preserve_internal_ports(candidate, refinement):
    document = compile_document(candidate, 'mn', 'H3', refinement)
    context.verify_document(document, candidate, context.contract_pin())
    context.require_joins(document['compiled']['strokes'])
    assert document['compiled']['schema_version'].endswith('geometry-only')
    if refinement == 'subdivision':
        assert all(len(row['cubics']) == 2 for row in document['compiled']['strokes'])


def test_rehashed_owner_contract_is_not_new_authorization(tmp_path, monkeypatch):
    path = tmp_path/'contract.json'
    contract = json.loads(context.CONTRACT.read_text())
    contract['maximum_handle_displacement_mm'] = 4
    path.write_text(json.dumps(contract))
    monkeypatch.setattr(context, 'CONTRACT', path)
    with pytest.raises(ValueError, match='pin'):
        context.load_contract(context.contract_pin())


def test_handle_cap_rejects_without_clipping():
    cubic = [[0, 0], [10, 0], [0, 1], [0, 2]]
    before = copy.deepcopy(cubic)
    with pytest.raises(ValueError, match='cap'):
        context.rotate_handle(cubic, 1, 1)
    assert cubic == before
