import copy
import gzip
import json

import pytest

from scripts import current_foundation_readiness as readiness
from scripts import upright_placement_validation as placement
from scribesim.handvalidate.specimen import digest


@pytest.fixture(scope='module')
def evidence():
    return readiness.summarize()


def sample_run():
    fixture = placement.SPEC['fixtures'][0]
    candidate = json.loads((placement.evaluation.SOURCE/'candidate.json').read_text())
    model = placement.model_for_fixture(candidate, fixture)
    run = json.loads(gzip.decompress((placement.BASE/'run-001/seed-7/first/letter-n-traces.json.gz').read_bytes()))['base']
    return fixture, model, run


def test_complete_current_coverage_is_not_training_clearance(evidence):
    assert evidence['baseline_readiness'] == 'pass'
    assert evidence['source_artifacts_verified'] == 1808
    assert len(evidence['coverage']) == 240
    assert set(evidence['catalog']['primitives']) == {'stem', 'rise', 'upper-return', 'lower-return'}
    assert set(evidence['catalog']['gestures']) == {'stem', 'overturn', 'underturn'}
    assert set(evidence['catalog']['actions']) == {'fixed'}
    assert evidence['missing_baseline_inventory'] == []
    assert evidence['context_training_allowed'] is evidence['S2_accepted'] is evidence['real_accepted'] is False
    assert evidence['context_readiness'] == 'blocked'
    assert evidence['context_gaps']
    assert evidence['new_controller_executions'] == evidence['new_renders'] == 0


@pytest.mark.parametrize('mutation', ['owner', 'primitive', 'gesture', 'action', 'offset', 'missing_occurrence',
                                      'tool', 'pressure', 'angle', 'fatigue', 'boundary', 'nonfinite', 'refinement'])
def test_raw_occurrence_audit_fails_closed(mutation):
    fixture, model, run = sample_run()
    row = next(row for row in run['trace'] if row['contact'])
    if mutation == 'owner':
        row['owner']['occurrence_id'] = 'invented'
    elif mutation in ('primitive', 'gesture', 'action'):
        row['owner'][mutation+'_sha256'] = '0'*64
    elif mutation == 'offset':
        row['owner']['offset'][0] += .1
    elif mutation == 'missing_occurrence':
        run['trace'] = [event for event in run['trace'] if not event['contact'] or event['owner']['occurrence_id'] != '0:0']
    elif mutation == 'tool':
        run['tool'] = 'legacy-full-edge'
    elif mutation == 'pressure':
        row['pressure'] = .4
    elif mutation == 'angle':
        row['angle_deg'] += .001
    elif mutation == 'fatigue':
        row['fatigue'] = .1
    elif mutation == 'boundary':
        boundary = next(event for event in run['trace'] if event['contact'] and event['owner']['boundary_contributors'])
        boundary['owner']['boundary_contributors'][0]['action_sha256'] = 'forged'
    elif mutation == 'refinement':
        run['dt_s'] *= 2
    else:
        row['to_mm'][0] = float('nan')
    with pytest.raises(ValueError):
        readiness.audit_run(model, fixture, 'base', run)


def test_subdivision_coverage_is_derived_not_a_new_primitive():
    fixture, model, _ = sample_run()
    run = json.loads(gzip.decompress((placement.BASE/'run-001/seed-7/first/letter-n-traces.json.gz').read_bytes()))['subdivision']
    result = readiness.audit_run(model, fixture, 'subdivision', run)
    assert result['primitive_counts'] == {'stem': 2, 'rise': 1, 'upper-return': 1}
    assert result['derivation'] == 'exact-internal-subdivision'


def test_external_pin_read_only_inspection_and_immutable_snapshot(tmp_path, monkeypatch, evidence):
    def forbidden(*args, **kwargs):
        pytest.fail('Readiness attempted execution or rendering')
    monkeypatch.setattr(placement.evaluation.runtime, 'execute', forbidden)
    monkeypatch.setattr(placement.evaluation, 'paint', forbidden)
    snapshot = tmp_path/'snapshot'
    monkeypatch.setattr(readiness, 'summarize', lambda: copy.deepcopy(evidence))
    readiness.build(snapshot)
    with pytest.raises(ValueError, match='pin'):
        readiness.inspect(snapshot, None)
    checksum = digest(snapshot/'report.json')
    assert readiness.inspect(snapshot, checksum)['baseline_readiness'] == 'pass'
    with pytest.raises(ValueError, match='exist'):
        readiness.build(snapshot)
    report = json.loads((snapshot/'report.json').read_text())
    report['context_training_allowed'] = True
    (snapshot/'report.json').write_text(json.dumps(report))
    with pytest.raises(ValueError):
        readiness.inspect(snapshot, digest(snapshot/'report.json'))


def test_repinning_forged_authority_does_not_change_clearance(tmp_path, monkeypatch, evidence):
    monkeypatch.setattr(readiness, 'summarize', lambda: copy.deepcopy(evidence))
    snapshot = tmp_path/'snapshot'
    readiness.build(snapshot)
    frozen = json.loads((snapshot/'freeze.json').read_text())
    frozen['authorization'] = 'context fitting approved'
    (snapshot/'freeze.json').write_text(json.dumps(frozen))
    report = json.loads((snapshot/'report.json').read_text())
    report['artifacts']['freeze.json'] = digest(snapshot/'freeze.json')
    (snapshot/'report.json').write_text(json.dumps(report))
    with pytest.raises(ValueError, match='identities'):
        readiness.inspect(snapshot, digest(snapshot/'report.json'))


@pytest.mark.parametrize('field,value', [('purpose','context-fitting'), ('purpose','nonidentity-geometry'),
    ('tool','legacy-full-edge'), ('required_letters',[]), ('required_letters',['a']), ('required_letters',['n','n'])])
def test_consumers_cannot_expand_scope(tmp_path, monkeypatch, evidence, field, value):
    monkeypatch.setattr(readiness, 'inspect', lambda *args: copy.deepcopy(evidence))
    arguments = {'expected_report_sha256': '1'*64, 'candidate': json.loads((placement.evaluation.SOURCE/'candidate.json').read_text()),
                 'required_letters': ['n','u','m'], 'tool': 'physical-edge-v1', 'purpose': 'frozen-baseline-reuse'}
    arguments[field] = value
    with pytest.raises(ValueError):
        readiness.require_readiness(tmp_path, **arguments)


def test_exact_consumer_candidate_and_scope(monkeypatch, tmp_path, evidence):
    monkeypatch.setattr(readiness, 'inspect', lambda *args: copy.deepcopy(evidence))
    candidate = json.loads((placement.evaluation.SOURCE/'candidate.json').read_text())
    args = {'expected_report_sha256': '1'*64, 'candidate': candidate, 'required_letters':['n','u','m'],
            'tool':'physical-edge-v1', 'purpose':'frozen-baseline-reuse'}
    result = readiness.require_readiness(tmp_path, **args)
    assert result['baseline_ready'] is True
    assert result['context_training_allowed'] is False
    candidate['primitives']['rise']['cubics'][0][1][0] += .001
    with pytest.raises(ValueError, match='candidate'):
        readiness.require_readiness(tmp_path, **args)


def test_source_loader_requires_original_pins_and_readiness_permissions(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Source verification attempted execution or rendering')
    monkeypatch.setattr(placement.evaluation.runtime, 'execute', forbidden)
    monkeypatch.setattr(placement.evaluation, 'paint', forbidden)
    source = readiness.load_source()
    assert source['review']['status'] == 'approved_held_out_actual_appearance'
    monkeypatch.setitem(readiness.PINS, 'report.json', '0'*64)
    with pytest.raises(ValueError, match='pin'):
        readiness.load_source()


def test_missing_changed_or_escaped_artifacts_fail_closed(tmp_path):
    directory = tmp_path/'archive'
    directory.mkdir()
    path = directory/'trace.json'
    path.write_text('{}')
    artifacts = {'trace.json': digest(path)}
    readiness.verify_inventory(directory, artifacts, [])
    path.write_text('{"changed":true}')
    with pytest.raises(ValueError, match='artifact'):
        readiness.verify_inventory(directory, artifacts, [])
    path.unlink()
    with pytest.raises(ValueError, match='inventory'):
        readiness.verify_inventory(directory, artifacts, [])
    outside = tmp_path/'outside.json'
    outside.write_text('{}')
    path.symlink_to(outside)
    with pytest.raises(ValueError, match='escaped'):
        readiness.verify_inventory(directory, {'trace.json':digest(outside)}, [])


def test_legacy_readiness_rejections_are_not_repaired():
    from scribesim.handvalidate import finer_scales, standalone_stem
    for module, filename, names in [(finer_scales, 'S1-actions.json', ['underturn','overturn']),
                                    (standalone_stem, 'report.json', ['stem'])]:
        directory = module.BASE/'run-001'
        with pytest.raises(ValueError, match='Stale'):
            module.require_readiness(directory, expected_report_sha256=digest(directory/filename),
                                     required_gestures=names, tool=module.SPEC['tool'])
