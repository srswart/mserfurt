import copy
import json
import math

import pytest

from scripts import nu_j1_receiving_repair as repair


@pytest.fixture
def synthetic(monkeypatch):
    rows = []
    for letter in range(2):
        for stroke in range(4):
            horizontal = .4 if letter == 0 else 1.8
            rows.append({'occurrence_id': f'{letter}:{stroke}', 'action_profile': 'fixed',
                         'cubics': [[[horizontal, 1.], [horizontal, .7],
                                     [horizontal, .4], [horizontal, 0.]]]})
    model = {'synthetic': True}
    monkeypatch.setattr(repair.prior, 'canonical', lambda model, text: {'text': text, 'strokes': copy.deepcopy(rows)})
    saved = repair.prior.construct(model, 'J1')
    return model, saved, repair.construct(saved)


def test_exact_local_replacement_and_protection(synthetic):
    model, saved, document = synthetic
    repair.validate(document, saved, model)
    assert document['boundary'][:-1] == saved['boundary'][:-1]
    assert document['retained'] == saved['retained']
    assert len(document['boundary'][-1]['cubics_mm']) == 2
    assert len(saved['boundary'][-1]['cubics_mm']) == 1
    assert document['boundary'][-1]['replacement_source_span'] == saved['boundary'][-1]['replacement_source_span']


@pytest.mark.parametrize('mutation', ['second', 'body', 'action', 'source', 'reset', 'port', 'tangent'])
def test_mutations_fail_identity(synthetic, mutation):
    model, saved, document = synthetic
    if mutation == 'second':
        document['boundary'][-1]['cubics_mm'][1][1][0] += .001
    elif mutation == 'body':
        document['retained'][0]['cubics_mm'][0][0][0] += .001
    elif mutation == 'action':
        document['profiles']['receiving'] = document['profiles']['core']
    elif mutation == 'source':
        document['boundary'][-1]['replacement_source_span']['interval'][1] = '.4'
    elif mutation == 'reset':
        document['receiving_revision']['action_domain'] = 'per-cubic'
    elif mutation == 'port':
        document['ports_mm']['E'] = [0., 0.]
    else:
        document['boundary'][-1]['cubics_mm'][1][1] = document['boundary'][-1]['cubics_mm'][1][0]
    with pytest.raises(ValueError):
        repair.validate(document, saved, model)


def test_full_domain_locality_and_canonical_tangent():
    direction = [-.03, -math.sqrt(1-.03**2)]
    document = {'ports_mm': {'K': [0., 1.], 'C': [.3, .2]}, 'directions': {'C': direction}}
    curves = repair.controls(document)
    assert repair.local_tail_check(curves, document['ports_mm']['C'])['status'] == 'pass'
    assert repair.join_check(*curves)['status'] == 'pass'
    assert repair.prior.clearance.attachment.tangent(curves[-1], 1) == pytest.approx(direction)
    curves[-1][1][0] += .2
    assert repair.local_tail_check(curves, document['ports_mm']['C'])['status'] == 'fail'


def test_all_curvatures_and_shared_length_checked(synthetic, monkeypatch):
    model, saved, document = synthetic
    seen = []
    original = repair.prior.bounds.original.curvature_check
    def capture(cubic, *args):
        seen.append(cubic)
        return original(cubic, *args)
    monkeypatch.setattr(repair.prior.bounds.original, 'curvature_check', capture)
    checks = repair.structural_checks(document, saved, model)
    curves = document['boundary'][-1]['cubics_mm']
    assert all(curve in seen for curve in curves)
    assert checks['receiving_aggregate_length']['limit_mm'] == pytest.approx(1.25*math.dist(curves[0][0], curves[-1][-1]))
    assert 'K-C_excursion' not in checks and 'E-C_curvature' in checks
    assert checks['E_join']['status'] == checks['C_join']['status'] == 'pass'


def test_short_tail_curvature_and_cusp_rejected():
    curve = [[0., 0.], [0., .001], [.001, .001], [.001, 0.]]
    assert repair.prior.bounds.original.curvature_check(curve)['status'] == 'fail'
    curve[1] = curve[0]
    assert repair.prior.bounds.original.curvature_check(curve)['status'] == 'fail'


def test_aggregate_length_not_per_cubic_allowance():
    curves = [[[0., 0.], [0., .3], [0., .6], [0., 1.]],
              [[0., 1.], [0., .8], [0., .5], [0., .1]]]
    assert all(repair.prior.length_check([curve])['status'] == 'pass' for curve in curves)
    assert repair.prior.length_check(curves)['status'] == 'fail'


def test_cross_cubic_return_not_certified():
    outward = [[0., 0.], [1., 0.], [2., 0.], [3., 0.]]
    returning = list(reversed(outward))
    result = repair.ramp_self_contact([outward, returning], 'receiving')
    assert result['status'] == 'unresolved'


def test_contacts_inspect_both_receiving_cubics_no_E_permission(synthetic, monkeypatch):
    document = synthetic[2]
    tail = document['boundary'][-1]['cubics_mm'][1]
    calls = []
    def pair(first, profile, second, other, join):
        calls.append((first, second, join))
        return first != tail and second != tail
    monkeypatch.setattr(repair.prior.original, 'contact_pair', pair)
    result = repair.contacts(document)
    assert result['status'] == 'unresolved'
    assert any(first == tail or second == tail for first, second, _ in calls)
    assert all(entry['splice_port'] != 'E' for entry in result['pairs'])
    assert 'receiving' in result['ramp_self_contact']


def test_renderer_uses_one_aggregate_action(synthetic, monkeypatch):
    document = synthetic[2]
    calls = []
    monkeypatch.setattr(repair.prior.history.renderer, 'polygons',
                        lambda curves, profile, profiles: calls.append((curves, profile)) or [])
    repair.nominal.candidate_drawing(document)
    receiving = [curves for curves, profile in calls if profile == 'receiving']
    assert receiving == [document['boundary'][-1]['cubics_mm']]


@pytest.mark.parametrize('text', ['n', 'u', 'nu', 'mu', 'num'])
def test_context_off_exact(text, monkeypatch):
    from scribesim.evofit import stroke_gestures
    expected = {'text': text, 'canonical': True}
    monkeypatch.setattr(stroke_gestures, 'compile_gestures', lambda text, model: expected)
    assert repair.context_program({}, text) is expected
    if text != 'nu':
        assert repair.context_program({}, text, enabled=True) is expected


def test_failed_candidate_never_drawn(tmp_path, monkeypatch):
    monkeypatch.setattr(repair, 'OUTPUT', tmp_path)
    monkeypatch.setattr(repair.nominal, 'candidate_drawing', lambda *args: pytest.fail('Rendered failure'))
    repair.render({'candidates': [{'brief': 'J1-R1', 'status': 'unresolved'}], 'new_candidates': 1})
    assert not list(tmp_path.glob('*.svg'))


def test_saved_before_check_and_no_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(repair, 'OUTPUT', tmp_path/'run')
    fingerprints = {'n': 'n', 'u': 'u', 'nu': 'nu'}
    monkeypatch.setattr(repair, 'verify', lambda: {'historical': {'canonical_compiled_sha256': fingerprints}})
    monkeypatch.setattr(repair.readiness, 'digest', lambda path: 'synthetic')
    monkeypatch.setattr(repair.readiness, 'dependencies', lambda: {})
    monkeypatch.setattr(repair.readiness, 'invoke_worker', lambda *args: {'canonical_compiled_sha256': fingerprints})
    monkeypatch.setattr(repair, 'context_program', lambda model, text: text)
    monkeypatch.setattr(repair.prior.actions, 'object_digest', lambda value: value if isinstance(value, str) else 'candidate')
    monkeypatch.setattr(repair, 'frozen_candidate', lambda: {})
    calls = []
    monkeypatch.setattr(repair, 'construct', lambda saved: calls.append('one') or {'synthetic': True})
    def fail(document, saved, model):
        stored = json.loads((repair.OUTPUT/'report.json').read_text())
        assert stored['candidates'][0]['candidate'] == document
        raise ValueError('Synthetic stopped checker')
    monkeypatch.setattr(repair, 'inspect', fail)
    result = repair.run()
    assert result['status'] == 'stopped' and result['new_candidates'] == 1
    assert result['renders'] == 0 and calls == ['one']
    assert 'No study candidate was constructed' not in (repair.OUTPUT/'index.html').read_text()
    with pytest.raises(FileExistsError):
        repair.run()


def test_output_budget_and_exclusive_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(repair, 'OUTPUT', tmp_path)
    repair.write('once', 'saved')
    with pytest.raises(FileExistsError):
        repair.write('once', 'overwrite')
    with pytest.raises(ValueError, match='budget'):
        repair.write('large', b'0'*(25*1024**2))
